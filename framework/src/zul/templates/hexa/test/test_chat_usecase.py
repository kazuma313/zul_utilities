"""
Contoh test untuk use case chat.

Menjalankan dari root proyek:
    pip install -r requirements-dev.txt
    pytest

Pola yang dipakai:
    1. Rakit agent dengan LLM palsu (`scripted_model` dari conftest.py).
    2. Jalankan use case.
    3. Periksa jawaban dan pesan yang diterima LLM.

Salin file ini sebagai titik awal saat menguji use case baru.
"""

import pytest
from langchain.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from src.application.AI.agents.react.react import build_react_agent
from src.application.usecases.chat import ChatUseCase
from src.domain.exceptions import EmptyMessageError
from src.infrastructure.AI.tools.weather_tool import get_weather


def weather_tool_call() -> AIMessage:
    """Respons LLM yang meminta tool `get_weather` dijalankan."""
    return AIMessage(
        content="",
        tool_calls=[
            {"name": "get_weather", "args": {"location": "sf"}, "id": "call_1"}
        ],
    )


def build_usecase(llm, checkpointer=None) -> ChatUseCase:
    agent = build_react_agent(llm=llm, tools=[get_weather], checkpointer=checkpointer)
    return ChatUseCase(agent)


def test_agent_answers_directly_when_no_tool_is_needed(scripted_model):
    usecase = build_usecase(scripted_model("Halo juga!"))

    assert usecase.execute("halo", thread_id="t1") == "Halo juga!"


def test_agent_runs_the_tool_and_answers_with_its_result(scripted_model):
    llm = scripted_model(weather_tool_call(), "Cerah di San Francisco.")

    answer = build_usecase(llm).execute("cuaca di sf?", thread_id="t1")

    assert answer == "Cerah di San Francisco."
    tool_results = [m for m in llm.received[1] if isinstance(m, ToolMessage)]
    assert "sunny in San Francisco" in tool_results[0].content


def test_same_thread_continues_the_conversation(scripted_model):
    llm = scripted_model("Halo Bob", "Namamu Bob")
    usecase = build_usecase(llm, checkpointer=InMemorySaver())

    usecase.execute("Saya Bob", thread_id="t1")
    usecase.execute("Siapa nama saya?", thread_id="t1")

    second_call = [message.content for message in llm.received[1]]
    assert second_call[1:] == ["Saya Bob", "Halo Bob", "Siapa nama saya?"]


def test_empty_message_is_rejected(scripted_model):
    with pytest.raises(EmptyMessageError):
        build_usecase(scripted_model()).execute("   ", thread_id="t1")
