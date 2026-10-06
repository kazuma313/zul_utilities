"""
Kumpulan template agent. Satu subfolder = satu agent.

Template yang tersedia:
    react/              satu agent dengan beberapa tool
    human_in_the_loop/  agent yang menunggu persetujuan manusia sebelum
                        menjalankan tool tertentu
    subagents/          supervisor yang mendelegasikan ke agent spesialis

Cara menambah agent baru (misal `rag`):
    1. Buat folder `rag/` berisi `rag.py` (fungsi `build_rag_agent(...)`)
       dan `nodes/rag_nodes.py` (fungsi node dan routing).
    2. Taruh state-nya di `src/domain/entities/agents/rag/` dan prompt-nya
       di `src/domain/templates/prompt/rag/`.
    3. Rakit di controller: `src/interface/http/controllers/`.

Contoh pemakaian agent yang sudah ada:
    from src.application.AI.agents.react.react import build_react_agent

    agent = build_react_agent(llm=llm, tools=[get_weather])
    result = agent.invoke({"messages": [{"role": "user", "content": "halo"}]})
    print(result["messages"][-1].text)
"""
