"""
Satu aksi spesifik yang dilakukan sistem
Orchestrate domain entities
Koordinasi dengan repositories

🎯 Karakteristik Use Case:

✅ Satu use case = satu aksi bisnis
✅ Orchestrate domain entities
✅ Tidak ada business logic (ada di domain!)
✅ Koordinasi repository dan domain services

Use case yang tersedia:
    chat.py            ChatUseCase: kirim pesan, terima jawaban agent
    reviewed_chat.py   ReviewedChatUseCase: chat dengan persetujuan manusia

Cara membuat use case baru:
    1. Buat class dengan satu method publik (`execute` atau kata kerja yang jelas).
    2. Terima dependensi lewat `__init__`, jangan dibuat di dalam class.
    3. Lempar exception dari `src.domain.exceptions` untuk pelanggaran aturan.

Contoh:
    class SummarizeUseCase:
        def __init__(self, agent) -> None:
            self._agent = agent

        def execute(self, text: str) -> str:
            if not text.strip():
                raise EmptyMessageError()
            result = self._agent.invoke({"messages": [HumanMessage(content=text)]})
            return str(result["messages"][-1].text)
"""
