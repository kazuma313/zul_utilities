"""Proyek hasil `zul build hexa` harus bisa langsung dijalankan: agent ReAct.

Mengikuti panduan unit testing LangChain: LLM diganti GenericFakeChatModel
(jawaban sesuai naskah) dan memory diuji dengan InMemorySaver.
"""

import pytest
from langchain.messages import ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from tests.fake_llm import calls, contents, scripted_model, tool_call

THREAD = "thread-1"


def weather_call(call_id: str = "call_1"):
    return calls(tool_call("get_weather", {"location": "sf"}, call_id))


@pytest.fixture
def chat_usecase_with(hexa_project):
    """Factory: rakit ChatUseCase proyek dengan LLM palsu dan tools asli template."""
    from src.application.AI.agents.react.react import build_react_agent
    from src.application.usecases.chat import ChatUseCase
    from src.infrastructure.AI.tools.weather_tool import tools

    def build(llm, checkpointer=None, **usecase_options):
        agent = build_react_agent(llm=llm, tools=tools, checkpointer=checkpointer)
        return ChatUseCase(agent, **usecase_options)

    return build


# --------------------------------------------------------------------------
# ReAct loop
# --------------------------------------------------------------------------


def test_agent_answers_directly_when_no_tool_is_needed(chat_usecase_with):
    llm = scripted_model("Halo juga!")

    assert chat_usecase_with(llm).execute("halo", THREAD) == "Halo juga!"


def test_agent_runs_requested_tool_then_answers_with_its_result(chat_usecase_with):
    llm = scripted_model(weather_call(), "Cerah di San Francisco.")

    answer = chat_usecase_with(llm).execute("cuaca di sf?", THREAD)

    assert answer == "Cerah di San Francisco."
    tool_results = [m for m in llm.received[1] if isinstance(m, ToolMessage)]
    assert "sunny in San Francisco" in tool_results[0].content


def test_agent_gives_llm_the_system_prompt_and_tools(chat_usecase_with):
    from src.domain.templates.prompt.react.react_prompt_templates import (
        REACT_SYSTEM_PROMPT,
    )

    llm = scripted_model("ok")

    chat_usecase_with(llm).execute("halo", THREAD)

    assert llm.received[0][0].content == REACT_SYSTEM_PROMPT
    assert [tool.name for tool in llm.bound_tools] == ["get_weather"]


def test_empty_message_is_rejected_before_reaching_the_llm(chat_usecase_with):
    from src.domain.exceptions import EmptyMessageError

    llm = scripted_model()

    with pytest.raises(EmptyMessageError):
        chat_usecase_with(llm).execute("   ", THREAD)
    assert llm.received == []


# --------------------------------------------------------------------------
# Batas langkah (recursion limit)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "max_agent_steps, llm_calls", [(6, 3), (7, 3), (8, 4), (25, 12)]
)
def test_agent_that_keeps_calling_tools_stops_with_an_answer_instead_of_an_error(
    chat_usecase_with, max_agent_steps, llm_calls
):
    from src.application.AI.agents.react.nodes.react_nodes import STEP_LIMIT_MESSAGE

    endless_tool_calls = [weather_call(f"call_{i}") for i in range(50)]
    llm = scripted_model(*endless_tool_calls)
    usecase = chat_usecase_with(llm, max_agent_steps=max_agent_steps)

    answer = usecase.execute("cuaca di sf?", THREAD)

    assert answer == STEP_LIMIT_MESSAGE
    assert (
        len(llm.received) == llm_calls
    )  # satu putaran llm_call -> tool_node = 2 langkah


def test_default_step_limit_ends_a_runaway_agent_gracefully(chat_usecase_with):
    from src.application.AI.agents.react.nodes.react_nodes import STEP_LIMIT_MESSAGE

    llm = scripted_model(*[weather_call(f"call_{i}") for i in range(50)])

    assert chat_usecase_with(llm).execute("cuaca di sf?", THREAD) == STEP_LIMIT_MESSAGE


# --------------------------------------------------------------------------
# Short-term memory (checkpointer + thread_id)
# --------------------------------------------------------------------------


def test_same_thread_continues_the_conversation(chat_usecase_with):
    llm = scripted_model("Halo Bob", "Namamu Bob")
    usecase = chat_usecase_with(llm, checkpointer=InMemorySaver())

    usecase.execute("Saya Bob", THREAD)
    usecase.execute("Siapa nama saya?", THREAD)

    assert contents(llm.received[1])[1:] == ["Saya Bob", "Halo Bob", "Siapa nama saya?"]


def test_different_thread_starts_a_fresh_conversation(chat_usecase_with):
    llm = scripted_model("Halo Bob", "Saya tidak tahu")
    usecase = chat_usecase_with(llm, checkpointer=InMemorySaver())

    usecase.execute("Saya Bob", "thread-bob")
    usecase.execute("Siapa nama saya?", "thread-lain")

    assert contents(llm.received[1])[1:] == ["Siapa nama saya?"]


def test_without_checkpointer_each_message_is_independent(chat_usecase_with):
    llm = scripted_model("Halo Bob", "Saya tidak tahu")
    usecase = chat_usecase_with(llm)

    usecase.execute("Saya Bob", THREAD)
    usecase.execute("Siapa nama saya?", THREAD)

    assert contents(llm.received[1])[1:] == ["Siapa nama saya?"]


# --------------------------------------------------------------------------
# Infrastructure
# --------------------------------------------------------------------------


def test_llm_factory_explains_missing_api_key(hexa_project, monkeypatch):
    from src.infrastructure.AI.llm.openai import get_llm_model

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        get_llm_model()


# --------------------------------------------------------------------------
# HTTP interface
# --------------------------------------------------------------------------


@pytest.fixture
def http_client(http_app, chat_usecase_with):
    """Factory: TestClient FastAPI dengan use case ber-LLM palsu dan memory."""
    from fastapi.testclient import TestClient

    from src.interface.http.controllers.chat_controller import get_chat_usecase

    def build(llm):
        usecase = chat_usecase_with(llm, checkpointer=InMemorySaver())
        http_app.dependency_overrides[get_chat_usecase] = lambda: usecase
        return TestClient(http_app)

    return build


def test_health_endpoint(http_client):
    response = http_client(scripted_model()).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_endpoint_returns_agent_answer_and_a_new_thread_id(http_client):
    client = http_client(scripted_model("Halo juga!"))

    response = client.post("/chat", json={"message": "halo"})

    assert response.status_code == 200
    assert response.json()["answer"] == "Halo juga!"
    assert response.json()["thread_id"]


def test_chat_endpoint_continues_conversation_when_thread_id_is_sent_back(http_client):
    llm = scripted_model("Halo Bob", "Namamu Bob")
    client = http_client(llm)

    first = client.post("/chat", json={"message": "Saya Bob"}).json()
    second = client.post(
        "/chat", json={"message": "Siapa nama saya?", "thread_id": first["thread_id"]}
    ).json()

    assert second["thread_id"] == first["thread_id"]
    assert contents(llm.received[1])[1:] == ["Saya Bob", "Halo Bob", "Siapa nama saya?"]


def test_chat_endpoint_reports_blank_message_as_client_error(http_client):
    response = http_client(scripted_model()).post("/chat", json={"message": "   "})

    assert response.status_code == 400
    assert "kosong" in response.json()["detail"]
