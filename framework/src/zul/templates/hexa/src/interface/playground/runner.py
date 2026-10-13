"""
Mesin playground: menjalankan agent dan mencatat setiap langkahnya.

Gunanya:
    Bagian playground yang tidak bergantung pada HTTP. Karena itu ia bisa
    diuji dengan LLM palsu, dan bisa dipakai dari skrip atau notebook saat
    kamu ingin melihat jejak agent tanpa membuka browser.

Cara pakai:
    from src.interface.playground.runner import send_message, submit_review

    turn = send_message(agent, "cuaca di sf?", thread_id="coba-1")

    for step in turn.steps:
        print("  " * step.depth, step.node, step.messages)
    print(turn.answer)

Saat agent berhenti menunggu keputusan manusia:
    if turn.pending_review:
        turn = submit_review(agent, [{"type": "approve"}], thread_id="coba-1")

Saat agent gagal di tengah jalan:
    if turn.error:
        print(turn.error)        # langkah sebelum gagal tetap ada di turn.steps
"""

import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from langchain.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.types import Command

from src.application.usecases.chat import MAX_AGENT_STEPS

INTERRUPT_KEY = "__interrupt__"

# --------------------------------------------------------------------------
# Jejak Satu Giliran
# --------------------------------------------------------------------------
#
# Satu giliran dimulai saat pesan atau keputusan dikirim ke agent, dan
# selesai saat agent menjawab, berhenti menunggu keputusan, atau
# gagal. Setiap node yang selesai dicatat sebagai satu langkah.
#


@dataclass(frozen=True)
class Step:
    """
    Satu node yang selesai dijalankan.

    `depth` adalah kedalaman graph tempat node itu berada: 0 untuk graph
    utama, 1 untuk graph yang dipanggil dari dalam tool (subagent).
    """

    node: str
    messages: tuple[AnyMessage, ...] = ()
    depth: int = 0


@dataclass(frozen=True)
class Turn:
    """Hasil satu giliran: langkah-langkahnya dan cara giliran itu berakhir."""

    steps: tuple[Step, ...] = ()
    pending_review: Any = None
    error: Exception | None = None
    seconds: float = 0.0

    @property
    def answer(self) -> str | None:
        """Teks jawaban agent, atau None jika giliran ini belum selesai."""
        if self.pending_review is not None or self.error is not None:
            return None

        for step in reversed(self.steps):
            if step.depth == 0 and step.messages:
                last_message = step.messages[-1]
                is_answer = isinstance(last_message, AIMessage)

                return str(last_message.text) if is_answer else None

        return None


# --------------------------------------------------------------------------
# Menjalankan Agent
# --------------------------------------------------------------------------


def send_message(
    agent: Any, message: str, thread_id: str, max_steps: int = MAX_AGENT_STEPS
) -> Turn:
    """Kirim pesan user ke agent dan catat langkah yang diambilnya."""
    payload = {"messages": [HumanMessage(content=message)]}

    return _run(agent, payload, thread_id, max_steps)


def submit_review(
    agent: Any,
    decisions: Sequence[dict[str, Any]],
    thread_id: str,
    max_steps: int = MAX_AGENT_STEPS,
) -> Turn:
    """Lanjutkan agent yang menunggu review dengan keputusan manusia."""
    return resume(agent, {"decisions": list(decisions)}, thread_id, max_steps)


def resume(
    agent: Any, value: Any, thread_id: str, max_steps: int = MAX_AGENT_STEPS
) -> Turn:
    """Lanjutkan agent yang berhenti di `interrupt()` dengan nilai apa pun."""
    return _run(agent, Command(resume=value), thread_id, max_steps)


def pending_review_of(agent: Any, thread_id: str) -> Any:
    """Payload interrupt yang sedang menunggu di sebuah thread, atau None."""
    config = {"configurable": {"thread_id": thread_id}}
    interrupts = agent.get_state(config).interrupts

    return interrupts[0].value if interrupts else None


def _run(agent: Any, payload: Any, thread_id: str, max_steps: int) -> Turn:
    config = {
        "recursion_limit": max_steps,
        "configurable": {"thread_id": thread_id},
    }
    steps: list[Step] = []
    pending_review = None
    error = None
    started_at = time.perf_counter()

    # Dengan subgraphs=True, graph yang dipanggil dari dalam sebuah tool
    # ikut melaporkan langkahnya. Setiap laporan membawa namespace, dan
    # panjang namespace itu menunjukkan kedalaman graph pelapornya.
    stream = agent.stream(payload, config, stream_mode="updates", subgraphs=True)

    # Playground adalah alat bantu melihat apa yang terjadi, jadi error
    # apa pun tidak diteruskan ke atas. Error itu disimpan bersama
    # langkah yang sudah sempat berjalan sebelum agent gagal.
    try:
        for namespace, update in stream:
            if INTERRUPT_KEY in update:
                pending_review = update[INTERRUPT_KEY][0].value
                continue

            steps.extend(_to_steps(update, depth=len(namespace)))
    except Exception as caught:
        error = caught

    return Turn(
        steps=tuple(steps),
        pending_review=pending_review,
        error=error,
        seconds=time.perf_counter() - started_at,
    )


def _to_steps(update: dict[str, Any], depth: int) -> list[Step]:
    """Ubah satu laporan graph menjadi langkah, satu per node di dalamnya."""
    steps = []

    for node, changes in update.items():
        messages = changes.get("messages", []) if isinstance(changes, dict) else []
        steps.append(Step(node=node, messages=tuple(messages), depth=depth))

    return steps
