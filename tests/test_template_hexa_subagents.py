"""
Template subagents.

Supervisor mendelegasikan pekerjaan ke subagent yang dibungkus sebagai tool.
"""

import pytest
from langchain.messages import ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from tests.fake_llm import calls, contents, scripted_model, tool_call

THREAD = "thread-1"
WEATHER_PROMPT = "You are a weather specialist."


def delegate(agent_name: str, query: str, call_id: str = "task_1"):
    """Respons supervisor yang mendelegasikan satu tugas ke subagent."""
    return calls(tool_call(agent_name, {"query": query}, call_id))


@pytest.fixture
def weather_spec(hexa_project):
    """Factory: SubagentSpec spesialis cuaca dengan LLM palsunya sendiri."""
    from src.application.AI.agents.subagents.subagents import SubagentSpec
    from src.infrastructure.AI.tools.weather_tool import get_weather

    def build(llm=None, name="weather_agent"):
        return SubagentSpec(
            name=name,
            description="Look up the weather for a location.",
            system_prompt=WEATHER_PROMPT,
            tools=[get_weather],
            llm=llm,
        )

    return build


@pytest.fixture
def supervisor_chat_with(hexa_project):
    """Factory: ChatUseCase di atas supervisor dengan LLM palsu."""
    from src.application.AI.agents.subagents.subagents import build_supervisor_agent
    from src.application.usecases.chat import ChatUseCase

    def build(llm, subagents, checkpointer=None):
        supervisor = build_supervisor_agent(
            llm=llm, subagents=subagents, checkpointer=checkpointer
        )
        return ChatUseCase(supervisor)

    return build


# --------------------------------------------------------------------------
# Delegasi
# --------------------------------------------------------------------------


def test_supervisor_answers_using_the_result_returned_by_a_subagent(
    supervisor_chat_with, weather_spec
):
    supervisor_llm = scripted_model(
        delegate("weather_agent", "weather in sf"), "Di SF cerah."
    )
    subagent_llm = scripted_model("It is sunny in San Francisco.")
    usecase = supervisor_chat_with(supervisor_llm, [weather_spec(subagent_llm)])

    answer = usecase.execute("cuaca di sf?", THREAD)

    assert answer == "Di SF cerah."
    subagent_result = [
        m for m in supervisor_llm.received[1] if isinstance(m, ToolMessage)
    ][0]
    assert subagent_result.content == "It is sunny in San Francisco."


def test_supervisor_sees_each_subagent_as_a_tool_with_its_name_and_description(
    supervisor_chat_with, weather_spec
):
    supervisor_llm = scripted_model("ok")
    usecase = supervisor_chat_with(supervisor_llm, [weather_spec(scripted_model())])

    usecase.execute("halo", THREAD)

    subagent_tool = supervisor_llm.bound_tools[0]
    assert subagent_tool.name == "weather_agent"
    assert subagent_tool.description == "Look up the weather for a location."


def test_subagent_only_sees_its_own_prompt_and_the_delegated_query(
    supervisor_chat_with, weather_spec
):
    supervisor_llm = scripted_model(
        delegate("weather_agent", "weather in sf"), "Di SF cerah."
    )
    subagent_llm = scripted_model("Sunny.")
    usecase = supervisor_chat_with(supervisor_llm, [weather_spec(subagent_llm)])

    usecase.execute("Nama saya Bob. Cuaca di sf?", THREAD)

    assert contents(subagent_llm.received[0]) == [WEATHER_PROMPT, "weather in sf"]


def test_subagent_does_its_work_with_its_own_tools(supervisor_chat_with, weather_spec):
    supervisor_llm = scripted_model(
        delegate("weather_agent", "weather in sf"), "Di SF cerah."
    )
    subagent_llm = scripted_model(
        calls(tool_call("get_weather", {"location": "sf"}, "weather_1")), "Sunny in SF."
    )
    usecase = supervisor_chat_with(supervisor_llm, [weather_spec(subagent_llm)])

    usecase.execute("cuaca di sf?", THREAD)

    weather_result = [
        m for m in subagent_llm.received[1] if isinstance(m, ToolMessage)
    ][0]
    assert "sunny in San Francisco" in weather_result.content
    assert [tool.name for tool in subagent_llm.bound_tools] == ["get_weather"]


def test_supervisor_can_delegate_to_several_subagents_in_one_turn(
    supervisor_chat_with, weather_spec
):
    supervisor_llm = scripted_model(
        calls(
            tool_call("weather_agent", {"query": "weather in sf"}, "task_1"),
            tool_call("forecast_agent", {"query": "forecast in sf"}, "task_2"),
        ),
        "Cerah hari ini dan besok.",
    )
    weather_llm, forecast_llm = scripted_model("Sunny today."), scripted_model(
        "Sunny tomorrow."
    )
    subagents = [
        weather_spec(weather_llm),
        weather_spec(forecast_llm, name="forecast_agent"),
    ]

    answer = supervisor_chat_with(supervisor_llm, subagents).execute(
        "cuaca sf?", THREAD
    )

    assert answer == "Cerah hari ini dan besok."
    results = {
        m.name: m.content
        for m in supervisor_llm.received[1]
        if isinstance(m, ToolMessage)
    }
    assert results == {
        "weather_agent": "Sunny today.",
        "forecast_agent": "Sunny tomorrow.",
    }


def test_subagent_without_its_own_model_uses_the_supervisor_model(
    supervisor_chat_with, weather_spec
):
    shared_llm = scripted_model(
        delegate("weather_agent", "weather in sf"), "Sunny.", "Di SF cerah."
    )
    usecase = supervisor_chat_with(shared_llm, [weather_spec(llm=None)])

    assert usecase.execute("cuaca di sf?", THREAD) == "Di SF cerah."
    assert contents(shared_llm.received[1]) == [WEATHER_PROMPT, "weather in sf"]


# --------------------------------------------------------------------------
# Memory
# --------------------------------------------------------------------------


def test_supervisor_remembers_the_conversation_but_subagents_start_fresh(
    supervisor_chat_with, weather_spec
):
    supervisor_llm = scripted_model(
        delegate("weather_agent", "weather in sf", "task_1"),
        "Di SF cerah.",
        delegate("weather_agent", "weather in nyc", "task_2"),
        "Di NYC tidak diketahui.",
    )
    subagent_llm = scripted_model("Sunny in SF.", "Unknown for NYC.")
    usecase = supervisor_chat_with(
        supervisor_llm, [weather_spec(subagent_llm)], checkpointer=InMemorySaver()
    )

    usecase.execute("cuaca di sf?", THREAD)
    usecase.execute("kalau nyc?", THREAD)

    assert "cuaca di sf?" in contents(supervisor_llm.received[2])
    assert contents(subagent_llm.received[1]) == [WEATHER_PROMPT, "weather in nyc"]


# --------------------------------------------------------------------------
# Validasi
# --------------------------------------------------------------------------


def test_duplicate_subagent_names_are_reported_when_building(
    hexa_project, weather_spec
):
    from src.application.AI.agents.subagents.subagents import build_supervisor_agent

    with pytest.raises(ValueError, match="weather_agent"):
        build_supervisor_agent(
            llm=scripted_model(), subagents=[weather_spec(), weather_spec()]
        )


def test_template_ships_weather_and_email_subagents(hexa_project):
    from src.interface.http.controllers.subagents_controller import SUBAGENTS

    assert {spec.name: [tool.name for tool in spec.tools] for spec in SUBAGENTS} == {
        "weather_agent": ["get_weather"],
        "email_agent": ["send_email"],
    }


# --------------------------------------------------------------------------
# HTTP interface
# --------------------------------------------------------------------------


def test_subagents_chat_endpoint_returns_supervisor_answer(
    http_app, supervisor_chat_with, weather_spec
):
    from fastapi.testclient import TestClient

    from src.interface.http.controllers.subagents_controller import (
        get_subagents_chat_usecase,
    )

    supervisor_llm = scripted_model(
        delegate("weather_agent", "weather in sf"), "Di SF cerah."
    )
    usecase = supervisor_chat_with(
        supervisor_llm,
        [weather_spec(scripted_model("Sunny."))],
        checkpointer=InMemorySaver(),
    )
    http_app.dependency_overrides[get_subagents_chat_usecase] = lambda: usecase

    response = TestClient(http_app).post(
        "/subagents/chat", json={"message": "cuaca di sf?"}
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Di SF cerah."
    assert response.json()["thread_id"]
