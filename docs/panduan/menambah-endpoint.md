# Menambah endpoint

Halaman ini menunjukkan cara menyediakan fitur baru lewat REST API. Contohnya menambah `POST /summaries` yang merangkum teks. Langkahnya mengikuti jalur yang sama dengan endpoint bawaan: use case, controller, router, lalu pendaftaran.

**Sebelum mulai:** kamu mengenal pembagian layer di proyek. Lihat [Perjalanan sebuah request](../konsep/alur-request.md) jika belum.

## Langkah-langkah

1. Tulis use case di layer application. Use case memuat aturan fiturnya dan menerima dependensinya lewat konstruktor:

    ```python title="src/application/usecases/summarize.py"
    from langchain.messages import HumanMessage

    from src.domain.exceptions import EmptyMessageError


    class SummarizeUseCase:
        def __init__(self, llm) -> None:
            self._llm = llm

        def execute(self, text: str) -> str:
            if not text.strip():
                raise EmptyMessageError()

            prompt = f"Summarize in one paragraph:\n\n{text}"
            reply = self._llm.invoke([HumanMessage(content=prompt)])

            return str(reply.text)
    ```

2. Tulis controller. Controller memuat model request dan respons, fungsi yang merakit use case, dan handler:

    ```python title="src/interface/http/controllers/summary_controller.py"
    from functools import lru_cache

    from pydantic import BaseModel, Field

    from src.application.usecases.summarize import SummarizeUseCase
    from src.infrastructure.AI.llm.openai import get_llm_model


    class SummaryRequest(BaseModel):
        text: str = Field(min_length=1)


    class SummaryResponse(BaseModel):
        summary: str


    @lru_cache
    def get_summarize_usecase() -> SummarizeUseCase:
        return SummarizeUseCase(get_llm_model())


    def create(request: SummaryRequest, usecase: SummarizeUseCase) -> SummaryResponse:
        return SummaryResponse(summary=usecase.execute(request.text))
    ```

3. Tulis router. Router menghubungkan path ke handler dan meminta FastAPI menyediakan use case-nya:

    ```python title="src/interface/http/routers/summaries.py"
    from fastapi import APIRouter, Depends

    from src.application.usecases.summarize import SummarizeUseCase
    from src.interface.http.controllers import summary_controller
    from src.interface.http.controllers.summary_controller import (
        SummaryRequest,
        SummaryResponse,
    )

    router = APIRouter(prefix="/summaries", tags=["summaries"])


    @router.post("", response_model=SummaryResponse)
    def create(
        request: SummaryRequest,
        usecase: SummarizeUseCase = Depends(summary_controller.get_summarize_usecase),
    ) -> SummaryResponse:
        return summary_controller.create(request, usecase)
    ```

4. Daftarkan router di entry point aplikasi. Tambahkan `summaries` ke baris impor router, lalu daftarkan router-nya:

    ```python title="src/interface/http/main.py"
    from src.interface.http.routers import chat, hitl, playground, subagents, summaries

    app.include_router(summaries.router)
    ```

5. Mulai ulang server.

## Melaporkan pelanggaran aturan bisnis

Controller tidak perlu `try/except`. Lempar turunan `DomainError` dari use case, dan aplikasi mengubahnya menjadi HTTP 400 dengan body `{"detail": "pesan"}`. Untuk aturan baru, tambahkan kelas exception di `src/domain/exceptions/__init__.py`:

```python title="src/domain/exceptions/__init__.py"
class TextTooLongError(DomainError):
    """Teks yang akan dirangkum melebihi batas."""

    def __init__(self, limit: int) -> None:
        super().__init__(f"Teks tidak boleh lebih dari {limit} karakter")
```

## Memeriksa hasilnya

Panggil endpoint barumu:

```shell
curl -X POST http://localhost:8000/summaries \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"TEKS_YANG_DIRANGKUM\"}"
```

Ganti `TEKS_YANG_DIRANGKUM` dengan teksmu. Respons berisi field `summary`. Endpoint baru juga muncul di dokumentasi interaktif, di `http://localhost:8000/docs`.

## Lihat juga

- [Menguji agent](menguji-agent.md) untuk menguji endpoint dengan model palsu.
- [HTTP API](../referensi/http-api.md) untuk kode status yang dipakai endpoint bawaan.
- [Perjalanan sebuah request](../konsep/alur-request.md) untuk alasan perakitan dependensi ditaruh di controller.
