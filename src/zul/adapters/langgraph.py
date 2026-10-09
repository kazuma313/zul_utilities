"""
Adapter LangGraph: menyusun graph dari fungsi node biasa, lalu menjalankannya.

Gunanya:
    Satu-satunya file Zul yang mengimpor langgraph. Node ditulis sebagai
    fungsi Python biasa `(state) -> dict`, lalu `chain` menyambungnya
    berurutan dari START sampai END. State masuk dan keluar sebagai dict
    biasa lewat `invoke`. Butuh extra llm: `pip install "zul[llm]"`.

Cara pakai:
    from zul.adapters import langgraph as langgraph_adapter

    builder = langgraph_adapter.chain(OverallState, [first_node, second_node])
    graph = langgraph_adapter.compile_graph(builder)
    state = langgraph_adapter.invoke(graph, {"a": "hello"})    # dict

`chain` mengembalikan StateGraph milik LangGraph, dan `compile_graph`
mengembalikan graph ter-compile. Keduanya objek LangGraph yang dipakai
sebagai handle, jadi cukup diteruskan ke fungsi di file ini.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from langgraph.graph import END, START, StateGraph

# --------------------------------------------------------------------------
# Menyusun Graph
# --------------------------------------------------------------------------
#
# Nama setiap node diambil dari nama fungsinya, sama seperti add_node
# milik LangGraph. Karena itu dua fungsi node dalam satu chain harus
# punya nama berbeda, sebab node dengan nama sama akan ditolak.
#


def chain(state_schema: type, nodes: Sequence[Callable[..., Any]]) -> Any:
    """StateGraph START -> node pertama -> ... -> node terakhir -> END.

    `state_schema` adalah kelas state, misalnya model Pydantic. Graph yang
    dikembalikan belum di-compile; teruskan ke `compile_graph`.

    Raises:
        ValueError: `nodes` kosong.
    """
    if not nodes:
        raise ValueError("chain butuh minimal satu fungsi node")
    builder = StateGraph(state_schema)
    previous = START
    for node in nodes:
        builder.add_node(node.__name__, node)
        builder.add_edge(previous, node.__name__)
        previous = node.__name__
    builder.add_edge(previous, END)
    return builder


def compile_graph(builder: Any) -> Any:
    """Graph dari `chain` yang sudah di-compile dan siap dijalankan."""
    return builder.compile()


# --------------------------------------------------------------------------
# Menjalankan Graph
# --------------------------------------------------------------------------


def invoke(graph: Any, state: dict[str, Any]) -> dict[str, Any]:
    """Jalankan graph dari `compile_graph` sampai END; hasilnya state akhir."""
    return dict(graph.invoke(state))
