"""
Contoh paling kecil sebuah graph LangGraph: satu node, satu state.

Gunanya:
    Titik awal untuk memahami StateGraph sebelum membaca agent yang lebih
    lengkap di template hexa (`zul build hexa`). Graph disusun lewat
    zul.adapters.langgraph, satu-satunya file Zul yang mengimpor
    langgraph.

Cara pakai (`pip install "zul[llm]"`):
    from zul.utilities.react_graph import graph

    graph.invoke({"a": "hello"})      # {'a': 'goodbye'}

Pola yang dipakai:
    1. Definisikan state (di sini model Pydantic `OverallState`).
    2. Tulis node: fungsi `(state) -> dict` berisi perubahan state.
    3. Sambungkan START -> node -> END dengan `chain`, lalu `compile_graph`.

`builder` adalah StateGraph dan `graph` adalah graph ter-compile milik
LangGraph. Keduanya sengaja dibiarkan sebagai objek LangGraph, supaya
contoh ini tetap bisa dipakai dengan method LangGraph seperti invoke.
"""

from pydantic import BaseModel

from zul.adapters import langgraph as langgraph_adapter

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
# Fungsi chain memakai nama fungsi sebagai nama node, lalu menyambung
# START ke node itu dan node itu ke END. Sesudah itu compile_graph
# mengubah rancangan ini menjadi graph yang bisa dijalankan.
#

builder = langgraph_adapter.chain(OverallState, [node])
graph = langgraph_adapter.compile_graph(builder)


if __name__ == "__main__":
    print(langgraph_adapter.invoke(graph, {"a": "hello"}))
