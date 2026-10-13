"""
Endpoint playground: `GET /playground/features`, `POST /playground/messages`,
dan `POST /playground/resume`.

Gunanya:
    Dipanggil oleh halaman Playground di dokumentasi Zul. Router ini hanya
    didaftarkan jika `PLAYGROUND_ENABLED=true`; lihat `main.py`.

Contoh:
    curl http://localhost:8000/playground/features

    curl -X POST http://localhost:8000/playground/messages \
         -H "Content-Type: application/json" \
         -d '{"feature": "ReAct", "message": "What is the weather in sf?"}'

    curl -X POST http://localhost:8000/playground/resume \
         -H "Content-Type: application/json" \
         -d '{"feature": "Human-in-the-loop", "thread_id": "THREAD_ID",
              "value": {"decisions": [{"type": "approve"}]}}'

Ganti `THREAD_ID` dengan nilai `thread_id` dari respons sebelumnya.
"""

from fastapi import APIRouter

from src.interface.http.controllers import playground_controller
from src.interface.http.controllers.playground_controller import (
    FeatureInfo,
    MessageRequest,
    PlaygroundTurn,
    ResumeRequest,
)

router = APIRouter(prefix="/playground", tags=["playground"])


@router.get("/features", response_model=list[FeatureInfo])
def features() -> list[FeatureInfo]:
    """Daftar fitur yang bisa dicoba, sesuai urutan di `features.py`."""
    return playground_controller.list_features()


@router.post("/messages", response_model=PlaygroundTurn)
def messages(request: MessageRequest) -> PlaygroundTurn:
    """
    Kirim pesan ke sebuah fitur.

    Respons berisi `answer`, `pending_review`, atau `error`, beserta setiap
    langkah yang diambil agent.
    """
    return playground_controller.send_message(request)


@router.post("/resume", response_model=PlaygroundTurn)
def resume(request: ResumeRequest) -> PlaygroundTurn:
    """Lanjutkan fitur yang berhenti menunggu keputusan."""
    return playground_controller.resume(request)
