"""
Contoh paling kecil sebuah graph LangGraph: satu node, satu state.

Gunanya:
    Titik awal untuk memahami StateGraph sebelum membaca agent yang lebih
    lengkap di template hexa (`zul build hexa`).

Cara pakai:
    from zul.utilities.react_graph import graph

    graph.invoke({"a": "hello"})      # {'a': 'goodbye'}

Pola yang dipakai:
    1. Definisikan state (di sini model Pydantic `OverallState`).
    2. Tulis node: fungsi `(state) -> dict` berisi perubahan state.
    3. Sambungkan START -> node -> END lalu `compile()`.
"""

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

# --------------------------------------------------------------------------
# State
# --------------------------------------------------------------------------
#
# State adalah data yang dibagikan ke semua node. Setiap node menerima state
# ini dan mengembalikan dict yang berisi field yang ingin diubahnya saja.
#


class OverallState(BaseModel):
    a: str


# --------------------------------------------------------------------------
# Node
# --------------------------------------------------------------------------


def node(state: OverallState):
    return {"a": "goodbye"}


# --------------------------------------------------------------------------
# Menyusun Graph
# --------------------------------------------------------------------------
#
# add_node mengambil nama fungsi sebagai nama node, karena itu
# edge di bawah menyebutnya dengan teks "node". compile()
# menjadikan rancangan ini graph yang bisa dijalankan.
#

builder = StateGraph(OverallState)
builder.add_node(node)
builder.add_edge(START, "node")
builder.add_edge("node", END)
graph = builder.compile()


if __name__ == "__main__":
    print(graph.invoke({"a": "hello"}))
