"""
Use case: chat dengan agent yang meminta persetujuan manusia untuk aksi tertentu.

Gunanya:
    Menjaga alur review tetap benar: pesan baru ditolak selama masih ada
    aksi yang menunggu keputusan, dan keputusan divalidasi sebelum agent
    dilanjutkan.

Cara pakai:
    usecase = ReviewedChatUseCase(agent)   # agent wajib punya checkpointer

    turn = usecase.send_message("email alice: rapat jam 10", thread_id="t1")
    if turn.pending_review:                 # agent menunggu keputusan
        print(turn.pending_review["action_requests"])
        turn = usecase.submit_review([{"type": "approve"}], thread_id="t1")
    print(turn.answer)

Bentuk keputusan (satu per aksi, urutan sama dengan `action_requests`):
    {"type": "approve"}
    {"type": "edit", "edited_action": {"name": "send_email", "args": {...}}}
    {"type": "reject", "message": "alasan penolakan"}
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from langchain.messages import HumanMessage
from langgraph.types import Command

from src.application.AI.agents.human_in_the_loop.nodes.human_in_the_loop_nodes import (
    ALLOWED_DECISIONS,
)
from src.application.usecases.chat import MAX_AGENT_STEPS
from src.domain.exceptions import (
    EmptyMessageError,
    InvalidReviewDecisionError,
    NoPendingReviewError,
    ReviewPendingError,
)

INTERRUPT_KEY = "__interrupt__"

# --------------------------------------------------------------------------
# Port
# --------------------------------------------------------------------------


class ReviewableAgent(Protocol):
    """Port: graph LangGraph ter-compile dengan checkpointer."""

    def invoke(
        self, input: Any, config: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...

    def get_state(self, config: dict[str, Any]) -> Any: ...


# --------------------------------------------------------------------------
# Hasil Satu Giliran
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ChatTurn:
    """
    Hasil satu giliran percakapan.

    Tepat satu yang terisi: `answer` jika agent selesai menjawab, atau
    `pending_review` jika agent berhenti menunggu keputusan manusia.
    """

    answer: str | None = None
    pending_review: dict[str, Any] | None = None


# --------------------------------------------------------------------------
# Validasi Keputusan
# --------------------------------------------------------------------------
#
# Fungsi ini berdiri di luar use case karena dipakai juga oleh playground.
# Siapa pun yang melanjutkan agent harus memeriksa keputusannya lebih
# dulu, sebab keputusan yang salah bentuk membuat node review gagal.
#


def validate_decisions(
    decisions: Sequence[dict[str, Any]], pending_review: dict[str, Any]
) -> None:
    """
    Pastikan keputusan cocok dengan aksi yang menunggu review.

    Raises:
        InvalidReviewDecisionError: Jika jumlah, jenis, atau isi keputusan
            tidak sesuai.
    """
    action_count = len(pending_review["action_requests"])

    if len(decisions) != action_count:
        raise InvalidReviewDecisionError(
            f"Butuh {action_count} keputusan (satu per aksi), "
            f"diterima {len(decisions)}"
        )

    for decision in decisions:
        decision_type = decision.get("type") if isinstance(decision, dict) else None

        if decision_type not in ALLOWED_DECISIONS:
            raise InvalidReviewDecisionError(
                f"Jenis keputusan '{decision_type}' tidak dikenal. "
                f"Pilihan: {ALLOWED_DECISIONS}"
            )

        if decision_type == "edit":
            _validate_edited_action(decision.get("edited_action"))


def _validate_edited_action(edited_action: Any) -> None:
    if edited_action is None:
        raise InvalidReviewDecisionError(
            "Keputusan 'edit' wajib menyertakan 'edited_action'"
        )

    is_complete = (
        isinstance(edited_action, dict)
        and isinstance(edited_action.get("name"), str)
        and isinstance(edited_action.get("args"), dict)
    )

    if not is_complete:
        raise InvalidReviewDecisionError(
            "'edited_action' harus berisi 'name' (teks) dan 'args' (objek)"
        )


# --------------------------------------------------------------------------
# Use Case
# --------------------------------------------------------------------------


class ReviewedChatUseCase:
    """Menjalankan percakapan yang bisa berhenti menunggu keputusan manusia."""

    def __init__(
        self, agent: ReviewableAgent, max_agent_steps: int = MAX_AGENT_STEPS
    ) -> None:
        self._agent = agent
        self._max_agent_steps = max_agent_steps

    def send_message(self, message: str, thread_id: str) -> ChatTurn:
        """
        Kirim pesan user ke agent.

        Raises:
            EmptyMessageError: Jika message kosong.
            ReviewPendingError: Jika thread ini masih menunggu keputusan review.
        """
        if not message.strip():
            raise EmptyMessageError()

        config = self._config(thread_id)

        # Pesan baru di thread yang sedang berhenti akan meninggalkan tool
        # call tanpa jawaban di riwayat percakapan, dan riwayat seperti
        # itu ditolak provider LLM. Jadi pesannya ditolak lebih dulu.
        if self._pending_review(config) is not None:
            raise ReviewPendingError()

        result = self._agent.invoke(
            {"messages": [HumanMessage(content=message)]}, config
        )

        return self._to_chat_turn(result)

    def submit_review(
        self, decisions: Sequence[dict[str, Any]], thread_id: str
    ) -> ChatTurn:
        """
        Lanjutkan agent dengan keputusan manusia, satu keputusan per aksi yang
        direview dan dalam urutan yang sama.

        Raises:
            NoPendingReviewError: Jika thread ini tidak sedang menunggu review.
            InvalidReviewDecisionError: Jika keputusan tidak cocok dengan aksi
                yang menunggu.
        """
        config = self._config(thread_id)
        pending_review = self._pending_review(config)

        if pending_review is None:
            raise NoPendingReviewError()

        # Nilai resume ikut tersimpan di checkpoint. Karena itu keputusan
        # harus diperiksa sebelum agent dilanjutkan, sebab error yang
        # muncul sesudah interrupt() akan terulang di setiap resume.
        validate_decisions(decisions, pending_review)

        result = self._agent.invoke(
            Command(resume={"decisions": list(decisions)}), config
        )

        return self._to_chat_turn(result)

    def _config(self, thread_id: str) -> dict[str, Any]:
        return {
            "recursion_limit": self._max_agent_steps,
            "configurable": {"thread_id": thread_id},
        }

    def _pending_review(self, config: dict[str, Any]) -> dict[str, Any] | None:
        """Payload interrupt yang sedang menunggu di thread ini, atau None."""
        interrupts = self._agent.get_state(config).interrupts

        return interrupts[0].value if interrupts else None

    @staticmethod
    def _to_chat_turn(result: dict[str, Any]) -> ChatTurn:
        interrupts = result.get(INTERRUPT_KEY)

        if interrupts:
            return ChatTurn(pending_review=interrupts[0].value)

        return ChatTurn(answer=str(result["messages"][-1].text))
