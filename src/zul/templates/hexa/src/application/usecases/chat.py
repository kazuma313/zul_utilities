"""
Use case: user mengirim pesan, agent menjawab.

Gunanya:
    Satu-satunya pintu dari layer interface ke agent chat. Memvalidasi
    pesan, memasang batas langkah agent, dan meneruskan `thread_id` supaya
    percakapan bisa berlanjut. Dipakai oleh agent ReAct dan supervisor
    subagents, karena keduanya punya bentuk pemanggilan yang sama.

Cara pakai:
    usecase = ChatUseCase(agent)
    answer = usecase.execute("cuaca di sf?", thread_id="user-42")

Contoh pengujian tanpa LLM asli:
    class FakeAgent:
        def invoke(self, input, config=None):
            return {"messages": [AIMessage(content="Halo juga!")]}

    assert ChatUseCase(FakeAgent()).execute("halo", "t1") == "Halo juga!"
"""

from typing import Any, Protocol

from langchain.messages import HumanMessage

from src.domain.exceptions import EmptyMessageError

# --------------------------------------------------------------------------
# Batas Langkah Agent
# --------------------------------------------------------------------------
#
# Jumlah langkah graph paling banyak untuk satu pesan. Bawaan LangGraph
# adalah 1000 langkah, terlalu longgar untuk agent di belakang API.
# Satu putaran tool memakai 2 langkah, sehingga 25 langkah sudah
# cukup untuk 11 putaran tool sebelum agent harus menjawab.
#

MAX_AGENT_STEPS = 25

# --------------------------------------------------------------------------
# Port
# --------------------------------------------------------------------------


class ChatAgent(Protocol):
    """Port: graph LangGraph ter-compile, atau apa pun yang berperilaku sama."""

    def invoke(
        self, input: dict[str, Any], config: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...


# --------------------------------------------------------------------------
# Use Case
# --------------------------------------------------------------------------


class ChatUseCase:
    """Menjalankan satu giliran percakapan dengan agent."""

    def __init__(
        self, agent: ChatAgent, max_agent_steps: int = MAX_AGENT_STEPS
    ) -> None:
        self._agent = agent
        self._max_agent_steps = max_agent_steps

    def execute(self, message: str, thread_id: str) -> str:
        """
        Kirim pesan user ke agent dan kembalikan jawaban akhirnya.

        Args:
            message: Pesan dari user.
            thread_id: ID percakapan. Pesan dengan thread_id yang sama
                melanjutkan percakapan sebelumnya (jika agent memakai
                checkpointer).

        Raises:
            EmptyMessageError: Jika message kosong.
        """
        if not message.strip():
            raise EmptyMessageError()

        config = {
            "recursion_limit": self._max_agent_steps,
            "configurable": {"thread_id": thread_id},
        }
        result = self._agent.invoke(
            {"messages": [HumanMessage(content=message)]}, config
        )

        # Isi pesan bisa berupa teks biasa atau daftar content block,
        # tergantung provider. Properti "text" menggabungkan semua
        # blok teks menjadi satu string, apa pun provider-nya.
        return str(result["messages"][-1].text)
