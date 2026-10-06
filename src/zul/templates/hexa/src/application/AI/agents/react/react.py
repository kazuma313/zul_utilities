"""
ReAct agent (Reason + Act) dengan LangGraph Graph API.

    START -> llm_call -> (ada tool call?) -> tool_node -> llm_call -> ... -> END

Gunanya:
    Merakit agent dasar: LLM memutuskan apakah perlu memanggil tool,
    `ToolNode` menjalankannya, lalu hasilnya dikembalikan ke LLM sampai
    ada jawaban akhir. LLM, tools, dan checkpointer di-inject dari luar,
    jadi layer application tidak tahu provider mana yang dipakai.

Cara pakai:
    agent = build_react_agent(llm=get_llm_model(), tools=[get_weather])
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "cuaca di sf?"}]},
        {"recursion_limit": 25},
    )
    print(result["messages"][-1].text)

Dengan memory (percakapan berlanjut per thread_id):
    agent = build_react_agent(llm=llm, tools=tools, checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "user-42"}}
    agent.invoke({"messages": [{"role": "user", "content": "Saya Bob"}]}, config)
    agent.invoke({"messages": [{"role": "user", "content": "Siapa saya?"}]}, config)

Graph ini sengaja ditulis manual supaya mudah dikustomisasi (node
tambahan, routing khusus). Untuk ReAct standar tanpa kustomisasi,
`langchain.agents.create_agent` merakit loop yang sama.
"""

from collections.abc import Sequence

from langchain.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.application.AI.agents.react.nodes.react_nodes import (
    make_llm_call,
    should_continue,
)
from src.domain.entities.agents.react.react import AgentState
from src.domain.templates.prompt.react.react_prompt_templates import (
    REACT_SYSTEM_PROMPT,
)


def build_react_agent(
    llm: BaseChatModel,
    tools: Sequence[BaseTool],
    system_prompt: str = REACT_SYSTEM_PROMPT,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """
    Rakit graph ReAct agent.

    Args:
        llm: Chat model yang mendukung tool calling.
        tools: Daftar tool yang boleh dipanggil agent.
        system_prompt: Instruksi sistem untuk agent.
        checkpointer: Penyimpan state per thread (short-term memory). Jika
            diisi, setiap invoke wajib menyertakan config
            {"configurable": {"thread_id": ...}}.

    Returns:
        Graph ter-compile; panggil dengan .invoke({"messages": [...]}, config).
    """
    tools = list(tools)
    model_with_tools = llm.bind_tools(tools)

    agent_builder = StateGraph(AgentState)

    # ToolNode menjalankan seluruh tool call di pesan terakhir, paralel jika
    # lebih dari satu, lalu menaruh hasilnya ke state sebagai ToolMessage.
    agent_builder.add_node("llm_call", make_llm_call(model_with_tools, system_prompt))
    agent_builder.add_node("tool_node", ToolNode(tools))

    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
    agent_builder.add_edge("tool_node", "llm_call")

    return agent_builder.compile(checkpointer=checkpointer)
