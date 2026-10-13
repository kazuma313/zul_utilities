"""
Endpoint agent human-in-the-loop: `POST /hitl/chat` dan `POST /hitl/review`.

Contoh:
    curl -X POST http://localhost:8000/hitl/chat \
         -H "Content-Type: application/json" \
         -d '{"message": "email alice@example.com: rapat jam 10"}'

    curl -X POST http://localhost:8000/hitl/review \
         -H "Content-Type: application/json" \
         -d '{"thread_id": "THREAD_ID", "decisions": [{"type": "approve"}]}'

Ganti `THREAD_ID` dengan nilai `thread_id` dari respons pertama.
"""

from fastapi import APIRouter, Depends

from src.application.usecases.reviewed_chat import ReviewedChatUseCase
from src.interface.http.controllers import hitl_controller
from src.interface.http.controllers.hitl_controller import (
    ReviewedChatRequest,
    ReviewedChatResponse,
    ReviewRequest,
)

router = APIRouter(prefix="/hitl", tags=["human-in-the-loop"])


@router.post("/chat", response_model=ReviewedChatResponse)
def chat(
    request: ReviewedChatRequest,
    usecase: ReviewedChatUseCase = Depends(hitl_controller.get_reviewed_chat_usecase),
) -> ReviewedChatResponse:
    """
    Kirim pesan ke agent.

    Respons berisi `answer`, atau `pending_review` jika agent berhenti
    menunggu persetujuan.
    """
    return hitl_controller.chat(request, usecase)


@router.post("/review", response_model=ReviewedChatResponse)
def review(
    request: ReviewRequest,
    usecase: ReviewedChatUseCase = Depends(hitl_controller.get_reviewed_chat_usecase),
) -> ReviewedChatResponse:
    """
    Kirim keputusan untuk aksi yang menunggu, lalu agent melanjutkan.

    Jenis keputusan: `approve`, `edit`, atau `reject`.
    """
    return hitl_controller.review(request, usecase)
