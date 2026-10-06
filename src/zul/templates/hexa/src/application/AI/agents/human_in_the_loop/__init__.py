"""
Agent human-in-the-loop: ReAct yang berhenti dan menunggu keputusan manusia
(approve / edit / reject) sebelum menjalankan tool tertentu.

File:
    human_in_the_loop.py              `build_human_in_the_loop_agent(...)`
    nodes/human_in_the_loop_nodes.py  node `human_review`, `tool_node`

Contoh:
    agent = build_human_in_the_loop_agent(
        llm=llm,
        tools=[get_weather, send_email],
        tools_requiring_approval={"send_email"},
        checkpointer=checkpointer,
    )
"""
