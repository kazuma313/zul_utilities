"""
Controller chat human-in-the-loop: kirim pesan, lalu setujui, ubah, atau tolak
aksi agent.

Gunanya:
    Composition root agent human-in-the-loop dan model request/response
    untuk dua endpoint: `POST /hitl/chat` dan `POST /hitl/review`.

Cara mewajibkan persetujuan untuk tool lain:
    Tambahkan tool ke daftar `TOOLS` dan namanya ke `TOOLS_REQUIRING_APPROVAL`.

Contoh alur:
    POST /hitl/chat    {"message": "email alice@example.com: rapat jam 10"}
    -> {"thread_id": "abc", "answer": null, "pending_review": {...}}

    POST /hitl/review  {"thread_id": "abc", "decisions": [{"type": "approve"}]}
    -> {"thread_id": "abc", "answer": "Email terkirim.", "pending_review": null}
"""

from functools import lru_cache
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from src.application.AI.agents.human_in_the_loop.human_in_the_loop import (
    build_human_in_the_loop_agent,
)
from src.application.usecases.reviewed_chat import ChatTurn, ReviewedChatUseCase
from src.infrastructure.AI.llm.openai import get_llm_model
from src.infrastructure.AI.memory.checkpointer import get_checkpointer
from src.infrastructure.AI.tools.email_tool import send_email
from src.infrastructure.AI.tools.weather_tool import get_weather

# --------------------------------------------------------------------------
# Tool dan Persetujuan
# --------------------------------------------------------------------------
#
# Tool yang punya efek ke dunia luar harus disetujui manusia lebih dulu.
# Tool yang hanya membaca data, seperti cuaca, langsung dijalankan
# supaya manusia tidak diminta menyetujui hal yang tak berisiko.
#

TOOLS = [get_weather, send_email]

TOOLS_REQUIRING_APPROVAL = {send_email.name}

# --------------------------------------------------------------------------
# Bentuk Request dan Respons
# --------------------------------------------------------------------------


class ReviewedChatRequest(BaseModel):
    message: str = Field(min_length=1, description="Pesan dari user")
    thread_id: str | None = Field(
        default=None,
        description="ID percakapan. Kosongkan untuk memulai percakapan baru.",
    )


class EditedAction(BaseModel):
    name: str = Field(description="Nama tool yang dijalankan, biasanya tetap")
    args: dict[str, Any] = Field(description="Argumen tool setelah diubah")


class ReviewDecision(BaseModel):
    type: Literal["approve", "edit", "reject"]
    edited_action: EditedAction | None = Field(
        default=None, description="Wajib untuk type=edit"
    )
    message: str | None = Field(
        default=None, description="Alasan penolakan untuk type=reject"
    )


class ReviewRequest(BaseModel):
    thread_id: str = Field(
        description="thread_id dari respons yang berisi pending_review"
    )
    decisions: list[ReviewDecision] = Field(
        min_length=1,
        description=(
            "Satu keputusan per aksi di pending_review.action_requests, urutan sama"
        ),
    )


class ReviewedChatResponse(BaseModel):
    thread_id: str
    answer: str | None = Field(
        default=None, description="Terisi jika agent selesai menjawab"
    )
    pending_review: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Terisi jika agent menunggu keputusan; "
            "kirim keputusannya ke POST /hitl/review"
        ),
    )


# --------------------------------------------------------------------------
# Composition Root
# --------------------------------------------------------------------------


@lru_cache
def get_human_in_the_loop_agent():
    """Agent yang dilayani `POST /hitl/*` dan dicoba di playground."""
    return build_human_in_the_loop_agent(
        llm=get_llm_model(),
        tools=TOOLS,
        tools_requiring_approval=TOOLS_REQUIRING_APPROVAL,
        checkpointer=get_checkpointer(),
    )


@lru_cache
def get_reviewed_chat_usecase() -> ReviewedChatUseCase:
    return ReviewedChatUseCase(get_human_in_the_loop_agent())


# --------------------------------------------------------------------------
# Handler
# --------------------------------------------------------------------------


def chat(
    request: ReviewedChatRequest, usecase: ReviewedChatUseCase
) -> ReviewedChatResponse:
    thread_id = request.thread_id or uuid4().hex
    turn = usecase.send_message(request.message, thread_id)

    return _to_response(turn, thread_id)


def review(
    request: ReviewRequest, usecase: ReviewedChatUseCase
) -> ReviewedChatResponse:
    decisions = [
        decision.model_dump(exclude_none=True) for decision in request.decisions
    ]
    turn = usecase.submit_review(decisions, request.thread_id)

    return _to_response(turn, request.thread_id)


def _to_response(turn: ChatTurn, thread_id: str) -> ReviewedChatResponse:
    return ReviewedChatResponse(
        thread_id=thread_id,
        answer=turn.answer,
        pending_review=turn.pending_review,
    )
