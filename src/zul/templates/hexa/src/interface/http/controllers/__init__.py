"""
Controller: menyambungkan HTTP ke use case.

Gunanya:
    Tiap controller berisi tiga hal:
    1. model request/response (Pydantic),
    2. composition root: fungsi `get_..._agent` yang merakit LLM, tools,
       dan memory menjadi agent, dan `get_..._usecase` yang membungkus
       agent itu dengan use case,
    3. fungsi handler yang menerjemahkan request menjadi pemanggilan use case.

Controller yang tersedia:
    chat_controller.py         agent ReAct            -> POST /chat
    hitl_controller.py         human-in-the-loop      -> POST /hitl/chat, /hitl/review
    subagents_controller.py    supervisor + subagents -> POST /subagents/chat
    playground_controller.py   jejak langkah agent    -> /playground/*

Kenapa composition root memakai `@lru_cache`:
    Agent dan checkpointer dibuat sekali lalu dipakai ulang oleh semua
    request, sehingga memory percakapan tidak hilang di antara request.

Kenapa agent dan use case dirakit oleh dua fungsi:
    Playground mencoba agent yang sama dengan yang dilayani REST API. Ia
    butuh graph-nya langsung untuk membaca setiap langkah, jadi perakit
    agent dipisah dari perakit use case.
"""
