"""
Agent ReAct (Reason + Act): LLM berpikir, memanggil tool, membaca hasilnya,
lalu mengulang sampai bisa menjawab.

File:
    react.py              `build_react_agent(...)`, perakit graph
    nodes/react_nodes.py  node `llm_call` dan routing `should_continue`

Contoh:
    from src.application.AI.agents.react.react import build_react_agent

    agent = build_react_agent(llm=llm, tools=tools, checkpointer=checkpointer)
"""
