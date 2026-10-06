"""
State agent: bentuk data yang mengalir antar node di graph LangGraph.

Gunanya:
    Satu subfolder per agent. State dipakai bersama oleh node, routing,
    dan perakit graph, jadi diletakkan di domain agar semua bisa
    mengimpornya tanpa saling bergantung.

Contoh menambah field ke state:
    class RagState(AgentState):
        documents: list[str]
"""
