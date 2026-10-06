"""
Endpoint agent ReAct: `POST /chat`.

Contoh:
    curl -X POST http://localhost:8000/chat \
         -H "Content-Type: application/json" \
         -d '{"message": "cuaca di sf?"}'

`Depends(get_chat_usecase)` membuat FastAPI menyediakan use case untuk
tiap request. Di test, dependensi ini diganti lewat
`app.dependency_overrides` supaya tidak memanggil LLM asli.
"""

from fastapi import APIRouter, Depends

from src.application.usecases.chat import ChatUseCase
from src.interface.http.controllers import chat_controller
from src.interface.http.controllers.chat_controller import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    usecase: ChatUseCase = Depends(chat_controller.get_chat_usecase),
) -> ChatResponse:
    """Kirim pesan ke ReAct agent."""
    return chat_controller.chat(request, usecase)
