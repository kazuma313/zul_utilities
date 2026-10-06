"""
Agent human-in-the-loop: ReAct agent yang berhenti meminta persetujuan manusia
sebelum menjalankan tool tertentu.

    START -> llm_call -> (ada tool call?) -> human_review -> tool_node -> llm_call
                                                  |
                                                  +-- semua ditolak --> llm_call

Gunanya:
    Mencegah agent menjalankan aksi berisiko (kirim email, hapus data,
    bayar) tanpa dilihat manusia. `human_review` memanggil `interrupt()`
    dari LangGraph: graph berhenti, state disimpan checkpointer, dan
    payload review dikembalikan ke pemanggil di `result["__interrupt__"]`.

Cara pakai:
    agent = build_human_in_the_loop_agent(
        llm=llm,
        tools=[get_weather, send_email],
        tools_requiring_approval={"send_email"},
        checkpointer=InMemorySaver(),          # wajib
    )
    config = {"configurable": {"thread_id": "t1"}}   # wajib

    result = agent.invoke({"messages": [HumanMessage(content="email alice")]}, config)
    if "__interrupt__" in result:
        print(result["__interrupt__"][0].value)      # aksi yang menunggu
        result = agent.invoke(
            Command(resume={"decisions": [{"type": "approve"}]}), config
        )

Di aplikasi, jangan panggil agent ini langsung. Pakai `ReviewedChatUseCase`
(`src/application/usecases/reviewed_chat.py`) yang menjaga alur review.

Jika agent dirakit dengan `langchain.agents.create_agent`, perilaku yang
sama tersedia lewat `HumanInTheLoopMiddleware`.
"""

from collections.abc import Collection, Sequence

from langchain.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from src.application.AI.agents.human_in_the_loop.nodes.human_in_the_loop_nodes import (
    make_human_review,
    make_tool_node,
    should_continue,
)
from src.application.AI.agents.react.nodes.react_nodes import make_llm_call
from src.domain.entities.agents.react.react import AgentState
from src.domain.templates.prompt.human_in_the_loop import (
    human_in_the_loop_prompt_templates as prompts,
)

# --------------------------------------------------------------------------
# Batas Langkah
# --------------------------------------------------------------------------
#
# Satu putaran tool di graph ini melewati tiga node: "human_review", lalu
# "tool_node", lalu "llm_call". Angkanya lebih besar daripada di graph
# ReAct sebab ada node tambahan yang jalan sebelum tool dijalankan.
#

STEPS_PER_TOOL_ROUND = 3


def build_human_in_the_loop_agent(
    llm: BaseChatModel,
    tools: Sequence[BaseTool],
    tools_requiring_approval: Collection[str],
    checkpointer: BaseCheckpointSaver,
    system_prompt: str = prompts.HUMAN_IN_THE_LOOP_SYSTEM_PROMPT,
):
    """
    Rakit graph agent dengan langkah persetujuan manusia.

    Args:
        llm: Chat model yang mendukung tool calling.
        tools: Semua tool yang boleh dipanggil agent.
        tools_requiring_approval: Nama tool yang harus disetujui manusia dulu.
        checkpointer: Penyimpan state per thread; interrupt tidak bisa jalan
            tanpanya.
        system_prompt: Instruksi sistem untuk agent.

    Returns:
        Graph ter-compile. Setiap invoke wajib menyertakan
        config {"configurable": {"thread_id": ...}}.
    """
    tools = list(tools)
    unknown_tools = set(tools_requiring_approval) - {tool.name for tool in tools}

    if unknown_tools:
        raise ValueError(
            f"tools_requiring_approval berisi tool tak dikenal: {sorted(unknown_tools)}"
        )

    llm_call = make_llm_call(
        llm.bind_tools(tools),
        system_prompt,
        steps_per_tool_round=STEPS_PER_TOOL_ROUND,
    )

    agent_builder = StateGraph(AgentState)

    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("human_review", make_human_review(tools_requiring_approval))
    agent_builder.add_node("tool_node", make_tool_node(tools))

    # Node "human_review" tidak punya edge keluar yang ditulis di sini. Ia
    # memilih tujuannya sendiri lewat Command(goto=...): ke "tool_node"
    # kalau masih ada aksi yang jalan, atau kembali ke "llm_call".
    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges(
        "llm_call", should_continue, ["human_review", END]
    )
    agent_builder.add_edge("tool_node", "llm_call")

    return agent_builder.compile(checkpointer=checkpointer)
