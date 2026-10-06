"""
Controller playground: menjalankan fitur dan mengembalikan jejak langkahnya.

Gunanya:
    Menerjemahkan request dari halaman dokumentasi menjadi pemanggilan
    `runner`, lalu mengubah hasilnya menjadi JSON yang mudah ditampilkan:
    jawaban, aksi yang menunggu keputusan, error, dan daftar langkah.

Contoh request:
    POST /playground/messages
    {"feature": "ReAct", "message": "What is the weather in sf?"}

Contoh respons:
    {
        "thread_id": "playground-3f9a1c2e",
        "answer": "It's sunny in San Francisco.",
        "pending_review": null,
        "error": null,
        "seconds": 1.2,
        "steps": [
            {"node": "llm_call", "depth": 0, "events": [
                {"type": "tool_call", "name": "get_weather",
                 "args": {"location": "sf"}}
            ]},
            {"node": "tool_node", "depth": 0, "events": [
                {"type": "tool_result", "name": "get_weather",
                 "content": "It's sunny in San Francisco."}
            ]},
            {"node": "llm_call", "depth": 0, "events": [
                {"type": "text", "content": "It's sunny in San Francisco."}
            ]}
        ]
    }

Melanjutkan agent yang menunggu keputusan:
    POST /playground/resume
    {"feature": "Human-in-the-loop", "thread_id": "playground-3f9a1c2e",
     "value": {"decisions": [{"type": "approve"}]}}
"""

from typing import Any, Literal
from uuid import uuid4

from fastapi import HTTPException
from langchain.messages import AIMessage, AnyMessage, ToolMessage
from pydantic import BaseModel, Field

from src.application.usecases.chat import MAX_AGENT_STEPS
from src.application.usecases.reviewed_chat import validate_decisions
from src.domain.exceptions import (
    EmptyMessageError,
    NoPendingReviewError,
    ReviewPendingError,
)
from src.interface.playground import runner
from src.interface.playground.features import FEATURES, Feature, find_feature

MOST_STEPS_ALLOWED = 200

# --------------------------------------------------------------------------
# Bentuk Request
# --------------------------------------------------------------------------


class MessageRequest(BaseModel):
    feature: str = Field(description="Nama fitur, lihat GET /playground/features")
    message: str = Field(min_length=1, description="Pesan dari user")
    thread_id: str | None = Field(
        default=None,
        description="ID percakapan. Kosongkan untuk memulai percakapan baru.",
    )
    max_steps: int = Field(default=MAX_AGENT_STEPS, ge=1, le=MOST_STEPS_ALLOWED)


class ResumeRequest(BaseModel):
    feature: str = Field(description="Nama fitur yang sedang menunggu")
    thread_id: str = Field(description="thread_id dari giliran yang menunggu")
    value: Any = Field(
        description='Nilai untuk interrupt(). Untuk review: {"decisions": [...]}'
    )
    max_steps: int = Field(default=MAX_AGENT_STEPS, ge=1, le=MOST_STEPS_ALLOWED)


# --------------------------------------------------------------------------
# Bentuk Respons
# --------------------------------------------------------------------------
#
# Pesan LangChain tidak dikirim mentah ke browser. Setiap pesan diubah
# menjadi satu atau lebih kejadian yang sederhana, supaya halaman
# dokumentasi tidak perlu mengenal kelas pesan milik LangChain.
#


class FeatureInfo(BaseModel):
    name: str
    description: str
    examples: list[str]


class TraceEvent(BaseModel):
    type: Literal["tool_call", "tool_result", "text"]
    name: str | None = Field(default=None, description="Nama tool")
    args: dict[str, Any] | None = Field(default=None, description="Argumen tool")
    content: str | None = Field(default=None, description="Teks atau hasil tool")
    failed: bool = Field(default=False, description="True jika tool gagal/ditolak")


class TraceStep(BaseModel):
    node: str
    depth: int = Field(description="0 = graph utama, 1+ = graph di dalam tool")
    events: list[TraceEvent]


class TurnError(BaseModel):
    type: str
    message: str


class PlaygroundTurn(BaseModel):
    thread_id: str
    answer: str | None = None
    pending_review: Any = None
    error: TurnError | None = None
    seconds: float
    steps: list[TraceStep]


# --------------------------------------------------------------------------
# Handler
# --------------------------------------------------------------------------


def list_features() -> list[FeatureInfo]:
    return [
        FeatureInfo(
            name=feature.name,
            description=feature.description,
            examples=list(feature.examples),
        )
        for feature in FEATURES
    ]


def send_message(request: MessageRequest) -> PlaygroundTurn:
    if not request.message.strip():
        raise EmptyMessageError()

    agent = _build_agent(request.feature)
    thread_id = request.thread_id or f"playground-{uuid4().hex[:8]}"

    # Pesan baru di thread yang sedang menunggu keputusan akan meninggalkan
    # tool call tanpa jawaban di riwayat. Thread baru belum punya state
    # apa pun, jadi pemeriksaan ini hanya perlu untuk thread lama.
    if request.thread_id and runner.pending_review_of(agent, thread_id) is not None:
        raise ReviewPendingError()

    turn = runner.send_message(agent, request.message, thread_id, request.max_steps)

    return _to_response(turn, thread_id)


def resume(request: ResumeRequest) -> PlaygroundTurn:
    agent = _build_agent(request.feature)
    pending_review = runner.pending_review_of(agent, request.thread_id)

    if pending_review is None:
        raise NoPendingReviewError()

    if _is_action_review(pending_review):
        decisions = _decisions_in(request.value)
        validate_decisions(decisions, pending_review)

    turn = runner.resume(agent, request.value, request.thread_id, request.max_steps)

    return _to_response(turn, request.thread_id)


# --------------------------------------------------------------------------
# Pembantu
# --------------------------------------------------------------------------


def _build_agent(feature_name: str) -> Any:
    try:
        feature: Feature = find_feature(feature_name)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=error.args[0]) from None

    # Fitur yang sedang dikerjakan wajar kalau belum bisa dirakit, misalnya
    # karena API key belum diisi. Alasannya dikirim apa adanya ke halaman
    # playground supaya langsung terlihat apa yang harus diperbaiki.
    try:
        return feature.build_agent()
    except Exception as error:
        detail = f"Fitur '{feature.name}' belum bisa dirakit: {error}"

        raise HTTPException(status_code=503, detail=detail) from error


def _is_action_review(pending_review: Any) -> bool:
    return isinstance(pending_review, dict) and "action_requests" in pending_review


def _decisions_in(value: Any) -> list[Any]:
    decisions = value.get("decisions") if isinstance(value, dict) else None

    return decisions if isinstance(decisions, list) else []


def _to_response(turn: runner.Turn, thread_id: str) -> PlaygroundTurn:
    error = None
    if turn.error is not None:
        error = TurnError(type=type(turn.error).__name__, message=str(turn.error))

    return PlaygroundTurn(
        thread_id=thread_id,
        answer=turn.answer,
        pending_review=turn.pending_review,
        error=error,
        seconds=round(turn.seconds, 3),
        steps=[
            TraceStep(
                node=step.node,
                depth=step.depth,
                events=[
                    event for message in step.messages for event in _to_events(message)
                ],
            )
            for step in turn.steps
        ],
    )


def _to_events(message: AnyMessage) -> list[TraceEvent]:
    """Ubah satu pesan LangChain menjadi kejadian yang ditampilkan playground."""
    if isinstance(message, ToolMessage):
        return [
            TraceEvent(
                type="tool_result",
                name=message.name,
                content=str(message.text),
                failed=message.status == "error",
            )
        ]

    events = []
    text = str(message.text)

    if text:
        events.append(TraceEvent(type="text", content=text))

    if isinstance(message, AIMessage):
        events.extend(
            TraceEvent(type="tool_call", name=tool_call["name"], args=tool_call["args"])
            for tool_call in message.tool_calls
        )

    return events
