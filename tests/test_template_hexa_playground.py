"""Template playground: mencoba agent sambil melihat setiap langkahnya."""

import pytest
from langchain.messages import AIMessage, ToolMessage
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from tests.fake_llm import calls, scripted_model, tool_call

THREAD = "thread-1"
EMAIL_ARGS = {"to": "alice@example.com", "subject": "Rapat", "body": "Rapat jam 10."}


def weather_call(call_id: str = "weather_1"):
    return tool_call("get_weather", {"location": "sf"}, call_id)


def email_call(call_id: str = "email_1"):
    return tool_call("send_email", EMAIL_ARGS, call_id)


def nodes(turn) -> list[str]:
    return [step.node for step in turn.steps]


@pytest.fixture
def runner(hexa_project):
    from src.interface.playground import runner

    return runner


@pytest.fixture
def react_agent_with(hexa_project):
    """Factory: agent ReAct dengan LLM palsu dan tool cuaca."""
    from src.application.AI.agents.react.react import build_react_agent
    from src.infrastructure.AI.tools.weather_tool import get_weather

    def build(llm, tools=(get_weather,)):
        return build_react_agent(llm=llm, tools=tools, checkpointer=InMemorySaver())

    return build


@pytest.fixture
def hitl_agent_with(hexa_project):
    """Factory: agent human-in-the-loop; `send_email` wajib disetujui."""
    from src.application.AI.agents.human_in_the_loop.human_in_the_loop import (
        build_human_in_the_loop_agent,
    )
    from src.infrastructure.AI.tools.email_tool import send_email
    from src.infrastructure.AI.tools.weather_tool import get_weather

    def build(llm):
        return build_human_in_the_loop_agent(
            llm=llm,
            tools=[get_weather, send_email],
            tools_requiring_approval={"send_email"},
            checkpointer=InMemorySaver(),
        )

    return build


# --------------------------------------------------------------------------
# Runner: Jejak Langkah
# --------------------------------------------------------------------------


def test_turn_records_every_node_the_agent_ran(runner, react_agent_with):
    agent = react_agent_with(scripted_model(calls(weather_call()), "Cerah."))

    turn = runner.send_message(agent, "cuaca di sf?", THREAD)

    assert nodes(turn) == ["llm_call", "tool_node", "llm_call"]
    assert turn.answer == "Cerah."
    assert turn.pending_review is None
    assert turn.error is None


def test_turn_keeps_the_messages_each_node_produced(runner, react_agent_with):
    agent = react_agent_with(scripted_model(calls(weather_call()), "Cerah."))

    turn = runner.send_message(agent, "cuaca di sf?", THREAD)

    tool_request, tool_result, answer = (step.messages[0] for step in turn.steps)
    assert tool_request.tool_calls[0]["name"] == "get_weather"
    assert isinstance(tool_result, ToolMessage)
    assert "sunny in San Francisco" in tool_result.content
    assert isinstance(answer, AIMessage)


def test_steps_inside_a_subagent_are_one_level_deeper(runner, hexa_project):
    from src.application.AI.agents.subagents.subagents import (
        SubagentSpec,
        build_supervisor_agent,
    )
    from src.infrastructure.AI.tools.weather_tool import get_weather

    supervisor_llm = scripted_model(
        calls(tool_call("weather_agent", {"query": "cuaca di sf"})), "Cerah."
    )
    subagent_llm = scripted_model(calls(weather_call()), "Cerah di SF.")
    supervisor = build_supervisor_agent(
        llm=supervisor_llm,
        subagents=[
            SubagentSpec(
                name="weather_agent",
                description="Look up the weather.",
                system_prompt="You are a weather specialist.",
                tools=[get_weather],
                llm=subagent_llm,
            )
        ],
        checkpointer=InMemorySaver(),
    )

    turn = runner.send_message(supervisor, "cuaca di sf?", THREAD)

    assert [(step.depth, step.node) for step in turn.steps] == [
        (0, "llm_call"),
        (1, "llm_call"),
        (1, "tool_node"),
        (1, "llm_call"),
        (0, "tool_node"),
        (0, "llm_call"),
    ]
    assert turn.answer == "Cerah."


def test_same_thread_continues_the_conversation(runner, react_agent_with):
    llm = scripted_model("Halo Bob", "Namamu Bob")
    agent = react_agent_with(llm)

    runner.send_message(agent, "Saya Bob", THREAD)
    runner.send_message(agent, "Siapa nama saya?", THREAD)

    second_call = [message.content for message in llm.received[1]]
    assert second_call[1:] == ["Saya Bob", "Halo Bob", "Siapa nama saya?"]


# --------------------------------------------------------------------------
# Runner: Review dan Error
# --------------------------------------------------------------------------


def test_turn_stops_with_the_pending_review(runner, hitl_agent_with):
    agent = hitl_agent_with(scripted_model(calls(email_call()), "Terkirim."))

    turn = runner.send_message(agent, "email alice", THREAD)

    assert turn.pending_review["action_requests"][0]["name"] == "send_email"
    assert turn.pending_review["action_requests"][0]["args"] == EMAIL_ARGS
    assert turn.answer is None
    assert nodes(turn) == ["llm_call"]


def test_submitting_the_review_continues_the_agent(runner, hitl_agent_with):
    agent = hitl_agent_with(scripted_model(calls(email_call()), "Terkirim."))
    runner.send_message(agent, "email alice", THREAD)

    turn = runner.submit_review(agent, [{"type": "approve"}], THREAD)

    assert nodes(turn) == ["human_review", "tool_node", "llm_call"]
    assert turn.answer == "Terkirim."
    assert turn.pending_review is None


def test_error_is_kept_with_the_steps_that_ran_before_it(runner, react_agent_with):
    @tool
    def broken_tool(query: str) -> str:
        """Always fails."""
        raise RuntimeError("layanan tidak tersedia")

    llm = scripted_model(
        calls(tool_call("broken_tool", {"query": "x"})), "tidak sampai"
    )
    agent = react_agent_with(llm, tools=[broken_tool])

    turn = runner.send_message(agent, "coba", THREAD)

    assert isinstance(turn.error, RuntimeError)
    assert str(turn.error) == "layanan tidak tersedia"
    assert nodes(turn) == ["llm_call"]
    assert turn.answer is None


def test_step_limit_applies_to_the_playground_too(runner, react_agent_with):
    endless_calls = [calls(weather_call(f"call_{index}")) for index in range(10)]
    agent = react_agent_with(scripted_model(*endless_calls))

    turn = runner.send_message(agent, "cuaca?", THREAD, max_steps=5)

    assert turn.error is None
    assert turn.answer.startswith("Maaf, saya butuh lebih banyak langkah")


# --------------------------------------------------------------------------
# Daftar Fitur
# --------------------------------------------------------------------------


def test_built_in_features_cover_every_agent_in_the_template(hexa_project):
    from src.interface.playground.features import FEATURES

    names = [feature.name for feature in FEATURES]

    assert names == ["ReAct", "Human-in-the-loop", "Subagents"]


def test_playground_tries_the_same_agent_the_api_serves(hexa_project, monkeypatch):
    from src.interface.http.controllers import chat_controller
    from src.interface.playground.features import find_feature

    monkeypatch.setattr(chat_controller, "get_llm_model", lambda: scripted_model())

    agent = find_feature("ReAct").build_agent()

    assert agent is chat_controller.get_react_agent()


def test_unknown_feature_names_the_available_ones(hexa_project):
    from src.interface.playground.features import find_feature

    with pytest.raises(KeyError, match="ReAct, Human-in-the-loop, Subagents"):
        find_feature("Tidak ada")


# --------------------------------------------------------------------------
# Endpoint: Menyala dan Mati
# --------------------------------------------------------------------------


@pytest.fixture
def client_with(hexa_project, monkeypatch):
    """Factory: client HTTP untuk aplikasi dengan environment tertentu."""
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    def build(**environment):
        for name in ("PLAYGROUND_ENABLED", "PLAYGROUND_ORIGINS"):
            monkeypatch.delenv(name, raising=False)
        for name, value in environment.items():
            monkeypatch.setenv(name, value)

        from src.interface.http.main import app

        return TestClient(app)

    return build


@pytest.fixture
def client(client_with):
    """Client HTTP dengan playground menyala."""
    return client_with(PLAYGROUND_ENABLED="true")


def use_llm(monkeypatch, controller_name: str, llm) -> None:
    """Ganti LLM yang dipakai satu controller dengan model palsu."""
    from src.interface.http import controllers

    controller = getattr(controllers, controller_name)
    monkeypatch.setattr(controller, "get_llm_model", lambda: llm)


def test_playground_is_off_unless_it_is_enabled(client_with):
    client = client_with()

    assert client.get("/playground/features").status_code == 404
    assert client.get("/health").status_code == 200


def test_features_endpoint_lists_what_can_be_tried(client):
    response = client.get("/playground/features")

    assert response.status_code == 200
    assert [feature["name"] for feature in response.json()] == [
        "ReAct",
        "Human-in-the-loop",
        "Subagents",
    ]
    assert response.json()[0]["examples"] == ["What is the weather in sf?"]


# --------------------------------------------------------------------------
# Endpoint: Mengirim Pesan
# --------------------------------------------------------------------------


def test_message_returns_the_answer_and_every_step(client, monkeypatch):
    llm = scripted_model(calls(weather_call()), "Cerah di San Francisco.")
    use_llm(monkeypatch, "chat_controller", llm)

    response = client.post(
        "/playground/messages", json={"feature": "ReAct", "message": "cuaca di sf?"}
    )

    turn = response.json()
    assert response.status_code == 200
    assert turn["answer"] == "Cerah di San Francisco."
    assert turn["thread_id"].startswith("playground-")
    assert [(step["node"], step["depth"]) for step in turn["steps"]] == [
        ("llm_call", 0),
        ("tool_node", 0),
        ("llm_call", 0),
    ]
    tool_call_event = turn["steps"][0]["events"][0]
    assert tool_call_event["type"] == "tool_call"
    assert tool_call_event["name"] == "get_weather"
    assert tool_call_event["args"] == {"location": "sf"}
    tool_result_event = turn["steps"][1]["events"][0]
    assert tool_result_event["type"] == "tool_result"
    assert "sunny in San Francisco" in tool_result_event["content"]
    assert turn["steps"][2]["events"] == [
        {
            "type": "text",
            "name": None,
            "args": None,
            "content": "Cerah di San Francisco.",
            "failed": False,
        }
    ]


def test_same_thread_id_continues_the_conversation_over_http(client, monkeypatch):
    llm = scripted_model("Halo Bob", "Namamu Bob")
    use_llm(monkeypatch, "chat_controller", llm)

    first = client.post(
        "/playground/messages", json={"feature": "ReAct", "message": "Saya Bob"}
    ).json()
    second = client.post(
        "/playground/messages",
        json={
            "feature": "ReAct",
            "message": "Siapa nama saya?",
            "thread_id": first["thread_id"],
        },
    ).json()

    assert second["answer"] == "Namamu Bob"
    assert second["thread_id"] == first["thread_id"]
    assert [message.content for message in llm.received[1]][1:] == [
        "Saya Bob",
        "Halo Bob",
        "Siapa nama saya?",
    ]


def test_tool_failure_is_reported_with_the_steps_before_it(client, monkeypatch):
    from src.interface.http.controllers import chat_controller

    @tool
    def get_weather(location: str) -> str:
        """Always fails."""
        raise RuntimeError("layanan cuaca mati")

    llm = scripted_model(calls(weather_call()), "tidak sampai")
    use_llm(monkeypatch, "chat_controller", llm)
    monkeypatch.setattr(chat_controller, "tools", [get_weather])

    response = client.post(
        "/playground/messages", json={"feature": "ReAct", "message": "cuaca?"}
    )

    turn = response.json()
    assert response.status_code == 200
    assert turn["error"] == {"type": "RuntimeError", "message": "layanan cuaca mati"}
    assert turn["answer"] is None
    assert [step["node"] for step in turn["steps"]] == ["llm_call"]


def test_blank_message_is_rejected(client, monkeypatch):
    use_llm(monkeypatch, "chat_controller", scripted_model())

    response = client.post(
        "/playground/messages", json={"feature": "ReAct", "message": "   "}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Message tidak boleh kosong"


def test_unknown_feature_is_not_found(client):
    response = client.post(
        "/playground/messages", json={"feature": "Tidak ada", "message": "halo"}
    )

    assert response.status_code == 404
    assert "ReAct, Human-in-the-loop, Subagents" in response.json()["detail"]


def test_feature_that_cannot_be_built_explains_why(client_with, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: False)
    client = client_with(PLAYGROUND_ENABLED="true")

    response = client.post(
        "/playground/messages", json={"feature": "ReAct", "message": "halo"}
    )

    assert response.status_code == 503
    assert "Fitur 'ReAct' belum bisa dirakit" in response.json()["detail"]
    assert "OPENAI_API_KEY" in response.json()["detail"]


# --------------------------------------------------------------------------
# Endpoint: Review
# --------------------------------------------------------------------------

HITL = "Human-in-the-loop"


def start_email_review(client) -> dict:
    """Kirim pesan yang membuat agent berhenti menunggu persetujuan email."""
    return client.post(
        "/playground/messages", json={"feature": HITL, "message": "email alice"}
    ).json()


def resume_with(client, thread_id: str, value):
    return client.post(
        "/playground/resume",
        json={"feature": HITL, "thread_id": thread_id, "value": value},
    )


def test_agent_stops_with_the_actions_waiting_for_a_decision(client, monkeypatch):
    llm = scripted_model(calls(email_call()), "Email terkirim.")
    use_llm(monkeypatch, "hitl_controller", llm)

    turn = start_email_review(client)

    assert turn["answer"] is None
    assert turn["pending_review"]["action_requests"][0]["name"] == "send_email"
    assert turn["pending_review"]["action_requests"][0]["args"] == EMAIL_ARGS


def test_approving_the_review_lets_the_agent_finish(client, monkeypatch):
    llm = scripted_model(calls(email_call()), "Email terkirim.")
    use_llm(monkeypatch, "hitl_controller", llm)
    waiting = start_email_review(client)

    response = resume_with(
        client, waiting["thread_id"], {"decisions": [{"type": "approve"}]}
    )

    turn = response.json()
    assert response.status_code == 200
    assert turn["answer"] == "Email terkirim."
    assert turn["pending_review"] is None
    assert [step["node"] for step in turn["steps"]] == [
        "human_review",
        "tool_node",
        "llm_call",
    ]


def test_rejected_action_shows_up_as_a_failed_tool_result(client, monkeypatch):
    llm = scripted_model(calls(email_call()), "Baik, email tidak dikirim.")
    use_llm(monkeypatch, "hitl_controller", llm)
    waiting = start_email_review(client)

    decision = {"type": "reject", "message": "alamatnya salah"}
    turn = resume_with(client, waiting["thread_id"], {"decisions": [decision]}).json()

    rejection = turn["steps"][0]["events"][-1]
    assert rejection["type"] == "tool_result"
    assert rejection["content"] == "alamatnya salah"
    assert rejection["failed"] is True
    assert turn["answer"] == "Baik, email tidak dikirim."


def test_new_message_is_refused_while_a_review_is_waiting(client, monkeypatch):
    llm = scripted_model(calls(email_call()), "Email terkirim.")
    use_llm(monkeypatch, "hitl_controller", llm)
    waiting = start_email_review(client)

    response = client.post(
        "/playground/messages",
        json={"feature": HITL, "message": "halo?", "thread_id": waiting["thread_id"]},
    )

    assert response.status_code == 400
    assert "menunggu persetujuan" in response.json()["detail"]


@pytest.mark.parametrize(
    "value",
    [
        {"decisions": []},
        {"decisions": [{"type": "skip"}]},
        {"decisions": [{"type": "edit"}]},
        {"decisions": [{"type": "edit", "edited_action": {"name": "send_email"}}]},
        {"decisions": ["approve"]},
        "approve",
    ],
)
def test_malformed_decision_is_refused_and_the_review_stays_open(
    client, monkeypatch, value
):
    llm = scripted_model(calls(email_call()), "Email terkirim.")
    use_llm(monkeypatch, "hitl_controller", llm)
    waiting = start_email_review(client)

    refused = resume_with(client, waiting["thread_id"], value)
    approved = resume_with(
        client, waiting["thread_id"], {"decisions": [{"type": "approve"}]}
    )

    assert refused.status_code == 400
    assert approved.json()["answer"] == "Email terkirim."


def test_resume_without_a_waiting_review_is_refused(client, monkeypatch):
    use_llm(monkeypatch, "hitl_controller", scripted_model("Halo."))
    finished = client.post(
        "/playground/messages", json={"feature": HITL, "message": "halo"}
    ).json()

    response = resume_with(
        client, finished["thread_id"], {"decisions": [{"type": "approve"}]}
    )

    assert response.status_code == 400
    assert "Tidak ada aksi yang menunggu" in response.json()["detail"]


# --------------------------------------------------------------------------
# Endpoint: Siapa yang Boleh Memanggil dari Browser
# --------------------------------------------------------------------------

DOCS_ORIGIN = "http://127.0.0.1:8001"
OTHER_ORIGIN = "https://situs-lain.example"


def test_documentation_site_may_call_the_playground(client):
    response = client.get("/playground/features", headers={"Origin": DOCS_ORIGIN})

    assert response.headers["access-control-allow-origin"] == DOCS_ORIGIN


def test_published_documentation_site_may_call_the_playground(client):
    origin = "https://zulkit.my.id"
    response = client.get("/playground/features", headers={"Origin": origin})

    assert response.headers["access-control-allow-origin"] == origin


def test_other_sites_may_not_call_the_playground(client):
    response = client.get("/playground/features", headers={"Origin": OTHER_ORIGIN})

    assert "access-control-allow-origin" not in response.headers


def test_browser_preflight_is_answered_for_the_documentation_site(client):
    response = client.options(
        "/playground/messages",
        headers={
            "Origin": DOCS_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == DOCS_ORIGIN


def test_allowed_sites_can_be_configured(client_with):
    client = client_with(
        PLAYGROUND_ENABLED="true",
        PLAYGROUND_ORIGINS="https://docs.example.com/, http://localhost:9000",
    )

    allowed = client.get(
        "/playground/features", headers={"Origin": "https://docs.example.com"}
    )
    default = client.get("/playground/features", headers={"Origin": DOCS_ORIGIN})

    assert allowed.headers["access-control-allow-origin"] == "https://docs.example.com"
    assert "access-control-allow-origin" not in default.headers
