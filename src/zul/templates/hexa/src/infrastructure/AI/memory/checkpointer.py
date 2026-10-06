"""
Short-term memory: state percakapan disimpan per thread_id oleh checkpointer.

Gunanya:
    Tanpa checkpointer, agent lupa semuanya setelah satu kali jalan. Dengan
    checkpointer, pemanggilan berikutnya dengan `thread_id` yang sama
    melanjutkan percakapan. Human-in-the-loop juga bergantung padanya untuk
    menyimpan state saat menunggu keputusan.

Cara pakai:
    agent = build_react_agent(llm=llm, tools=tools, checkpointer=get_checkpointer())
    agent.invoke(
        {"messages": [...]},
        {"configurable": {"thread_id": "user-42"}},
    )

Contoh memakai PostgreSQL untuk produksi, seperti di dokumentasi LangGraph
(`pip install -U "psycopg[binary,pool]" langgraph-checkpoint-postgres`):
    from langgraph.checkpoint.postgres import PostgresSaver

    DB_URI = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=disable"

    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup()      # cukup sekali, membuat tabel checkpoint
        agent = build_react_agent(llm=llm, tools=tools, checkpointer=checkpointer)
        ...                       # checkpointer hanya hidup di dalam blok `with`
"""

from langgraph.checkpoint.memory import InMemorySaver


def get_checkpointer() -> InMemorySaver:
    """
    Checkpointer untuk development.

    InMemorySaver menyimpan percakapan di memori proses, jadi hilang saat
    aplikasi restart dan tidak terbagi antar worker. Untuk produksi ganti
    dengan checkpointer berbasis database, misalnya PostgresSaver dari
    package `langgraph-checkpoint-postgres`.
    """
    return InMemorySaver()
