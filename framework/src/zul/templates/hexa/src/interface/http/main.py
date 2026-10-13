"""
Entry point FastAPI.

Menjalankan dari root proyek:
    uvicorn src.interface.http.main:app --reload

Gunanya:
    Membuat aplikasi, mendaftarkan router, dan memasang handler error.

Cara menambah kelompok endpoint baru:
    1. Buat `routers/orders.py` berisi `router = APIRouter(prefix="/orders")`.
    2. Daftarkan di sini: `app.include_router(orders.router)`.

Penanganan error:
    Semua `DomainError` menjadi HTTP 400 dengan `{"detail": "..."}`.
    Input yang tidak lolos validasi Pydantic menjadi HTTP 422 (bawaan FastAPI).
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.domain.exceptions import DomainError
from src.infrastructure.logging_config import setup_logging
from src.interface.http.routers import chat, hitl, playground, subagents
from src.interface.playground.settings import playground_enabled, playground_origins

setup_logging()

# --------------------------------------------------------------------------
# Aplikasi dan Router
# --------------------------------------------------------------------------
#
# Setiap kelompok endpoint tinggal di router-nya sendiri dan didaftarkan
# di sini. File ini sengaja dibuat tipis: ia hanya merangkai aplikasi,
# sedangkan logika tiap endpoint ada di controller dan use case.
#

app = FastAPI(title="Hexa AI Service")

app.include_router(chat.router)
app.include_router(hitl.router)
app.include_router(subagents.router)

# --------------------------------------------------------------------------
# Playground
# --------------------------------------------------------------------------
#
# Playground hanya menyala kalau PLAYGROUND_ENABLED diisi true, sebab ia
# menampilkan argumen dan hasil setiap tool. Aturan CORS di bawah ini
# membatasi siapa yang boleh memanggil API ini dari browser: hanya
# halaman dari alamat yang diizinkan, yaitu situs dokumentasi.
#

if playground_enabled():
    app.include_router(playground.router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=playground_origins(),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

# --------------------------------------------------------------------------
# Penanganan Error
# --------------------------------------------------------------------------
#
# Pelanggaran aturan bisnis adalah kesalahan pada request, bukan error
# server. Semua turunan DomainError diubah menjadi HTTP 400 di sini,
# jadi controller tidak perlu menulis try/except sendiri-sendiri.
#


@app.exception_handler(DomainError)
def handle_domain_error(_request: Request, error: DomainError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(error)})


# --------------------------------------------------------------------------
# Health Check
# --------------------------------------------------------------------------


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
