"""
State yang mengalir di graph agent.

Gunanya:
    `AgentState` adalah "ingatan kerja" agent selama satu kali jalan. Setiap
    node menerima state ini dan mengembalikan perubahan untuknya.

Field:
    messages          riwayat percakapan. Reducer `add_messages` membuat
                      pesan baru DITAMBAHKAN ke daftar; pesan dengan id yang
                      sama menggantikan versi lamanya.
    remaining_steps   diisi otomatis oleh LangGraph: sisa langkah sebelum
                      `recursion_limit` tercapai. Dipakai `llm_call` untuk
                      menutup percakapan dengan jawaban, bukan error.

Contoh node yang memakai state:
    def llm_call(state: AgentState) -> dict:
        response = model.invoke(state["messages"])
        return {"messages": [response]}      # ditambahkan, bukan menimpa

Contoh memperluas state untuk agent lain:
    class RagState(AgentState):
        documents: list[str]
"""

from typing import Annotated

from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages
from langgraph.managed import RemainingSteps
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """Data yang dibawa graph dari satu node ke node berikutnya."""

    # Anotasi add_messages adalah reducer untuk field ini. Pesan yang
    # dikembalikan sebuah node ditambahkan ke daftar, bukan menimpa
    # isinya, dan pesan ber-id sama menggantikan versi lamanya.
    messages: Annotated[list[AnyMessage], add_messages]

    # Field ini diisi sendiri oleh LangGraph, bukan oleh node. Isinya
    # adalah sisa langkah sebelum recursion_limit tercapai, dan node
    # LLM membacanya untuk menutup percakapan sebelum terlambat.
    remaining_steps: RemainingSteps
