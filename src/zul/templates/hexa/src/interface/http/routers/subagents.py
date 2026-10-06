"""
Endpoint supervisor + subagents: `POST /subagents/chat`.

Contoh:
    curl -X POST http://localhost:8000/subagents/chat \
         -H "Content-Type: application/json" \
         -d '{"message": "cek cuaca di sf lalu email ke alice@example.com"}'

Memakai model request/response dan handler yang sama dengan `POST /chat`;
yang berbeda hanya use case yang disediakan `get_subagents_chat_usecase`.
"""

from fastapi import APIRouter, Depends

from src.application.usecases.chat import ChatUseCase
from src.interface.http.controllers import chat_controller, subagents_controller
from src.interface.http.controllers.chat_controller import ChatRequest, ChatResponse

router = APIRouter(prefix="/subagents", tags=["subagents"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    usecase: ChatUseCase = Depends(subagents_controller.get_subagents_chat_usecase),
) -> ChatResponse:
    """Kirim pesan ke supervisor, yang mendelegasikan pekerjaan ke subagent."""
    return chat_controller.chat(request, usecase)
