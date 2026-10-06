"""
Controller chat: menerjemahkan request HTTP menjadi pemanggilan use case.

Gunanya:
    Composition root agent ReAct. Di `get_react_agent` adapter
    infrastructure (LLM, tools, memory) disambungkan ke layer application.

Cara mengganti komponen:
    - Model lain   : ganti `get_llm_model()` (lihat `infrastructure/AI/llm/`)
    - Tool lain    : ubah daftar `tools`
    - Memory lain  : ganti `get_checkpointer()`

Contoh request:
    POST /chat
    {"message": "cuaca di sf?", "thread_id": "opsional"}

Contoh respons:
    {"answer": "Cerah.", "thread_id": "9f1c..."}
"""

from functools import lru_cache
from uuid import uuid4

from pydantic import BaseModel, Field

from src.application.AI.agents.react.react import build_react_agent
from src.application.usecases.chat import ChatUseCase
from src.infrastructure.AI.llm.openai import get_llm_model
from src.infrastructure.AI.memory.checkpointer import get_checkpointer
from src.infrastructure.AI.tools.weather_tool import tools

# --------------------------------------------------------------------------
# Bentuk Request dan Respons
# --------------------------------------------------------------------------
#
# Dua model ini merupakan kontrak antara endpoint dengan client-nya. FastAPI
# memakai keduanya untuk memvalidasi isi request dan menyusun dokumentasi
# OpenAPI, jadi deskripsi setiap field ikut tampil di halaman "/docs".
#


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, description="Pesan dari user")
    thread_id: str | None = Field(
        default=None,
        description="ID percakapan. Kosongkan untuk memulai percakapan baru.",
    )


class ChatResponse(BaseModel):
    answer: str
    thread_id: str = Field(
        description="Kirim lagi di request berikutnya untuk melanjutkan percakapan"
    )


# --------------------------------------------------------------------------
# Composition Root
# --------------------------------------------------------------------------
#
# Di sinilah adapter dari layer infrastructure disambungkan ke layer
# application: model bahasa, daftar tool, dan penyimpan percakapan.
# Keduanya dibuat satu kali, lalu dipakai ulang semua request.
#


@lru_cache
def get_react_agent():
    """Agent ReAct yang dilayani `POST /chat` dan dicoba di playground."""
    return build_react_agent(
        llm=get_llm_model(),
        tools=tools,
        checkpointer=get_checkpointer(),
    )


@lru_cache
def get_chat_usecase() -> ChatUseCase:
    return ChatUseCase(get_react_agent())


# --------------------------------------------------------------------------
# Handler
# --------------------------------------------------------------------------


def chat(request: ChatRequest, usecase: ChatUseCase) -> ChatResponse:
    thread_id = request.thread_id or uuid4().hex
    answer = usecase.execute(request.message, thread_id)

    return ChatResponse(answer=answer, thread_id=thread_id)
