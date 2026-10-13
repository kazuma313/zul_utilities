"""
Node dan routing untuk graph ReAct agent.

Gunanya:
    `make_llm_call`     membuat node yang memanggil LLM dengan system prompt
    `should_continue`   memilih langkah berikutnya: `tool_node` atau selesai

Cara pakai (dilakukan oleh `build_react_agent`):
    builder.add_node("llm_call", make_llm_call(llm.bind_tools(tools), prompt))
    builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])

Cara menambah node sendiri:
    Node adalah fungsi `(state) -> dict`. Nilai yang dikembalikan digabung
    ke state; untuk `messages`, pesan baru ditambahkan ke daftar.

    def summarize(state: AgentState) -> dict:
        summary = llm.invoke(state["messages"])

        return {"messages": [summary]}
"""

from typing import Literal

from langchain.messages import AIMessage, SystemMessage
from langgraph.graph import END

from src.domain.entities.agents.react.react import AgentState

# --------------------------------------------------------------------------
# Batas Langkah
# --------------------------------------------------------------------------
#
# Satu putaran tool di graph ReAct melewati dua node: "tool_node" lalu
# "llm_call". Node LLM memakai angka ini untuk tahu kapan ia harus
# berhenti meminta tool, agar masih ada langkah untuk menjawab.
#

STEPS_PER_TOOL_ROUND = 2

STEP_LIMIT_MESSAGE = (
    "Maaf, saya butuh lebih banyak langkah untuk menyelesaikan permintaan ini."
)

# --------------------------------------------------------------------------
# Node
# --------------------------------------------------------------------------


def make_llm_call(
    model_with_tools,
    system_prompt: str,
    steps_per_tool_round: int = STEPS_PER_TOOL_ROUND,
):
    """
    Buat node yang memanggil LLM.

    Args:
        model_with_tools: Chat model yang sudah di-bind dengan tools.
        system_prompt: Instruksi sistem yang selalu ditaruh di awal percakapan.
        steps_per_tool_round: Jumlah langkah graph dari llm_call ini sampai
            llm_call berikutnya ketika ada tool call.
    """

    def llm_call(state: AgentState) -> dict:
        """Panggil LLM: ia memilih antara meminta tool atau menjawab."""
        messages = [SystemMessage(content=system_prompt), *state["messages"]]
        response = model_with_tools.invoke(messages)

        # Pemanggilan LLM berikutnya butuh sedikitnya satu langkah tersisa.
        # Kalau putaran tool ini akan menghabiskannya, percakapan ditutup
        # dengan jawaban sekarang, bukan dengan GraphRecursionError.
        out_of_steps = state["remaining_steps"] <= steps_per_tool_round
        if response.tool_calls and out_of_steps:
            response = AIMessage(id=response.id, content=STEP_LIMIT_MESSAGE)

        return {"messages": [response]}

    return llm_call


# --------------------------------------------------------------------------
# Routing
# --------------------------------------------------------------------------


def should_continue(state: AgentState) -> Literal["tool_node", END]:
    """Pilih langkah berikutnya: jalankan tool, atau selesai dan jawab user."""
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tool_node"

    return END
