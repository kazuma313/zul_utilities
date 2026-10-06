"""
Template human-in-the-loop.

Agent berhenti meminta persetujuan sebelum tool tertentu jalan.
"""

import pytest
from langchain.messages import ToolMessage
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from tests.fake_llm import calls, scripted_model, tool_call

THREAD = "thread-1"
EMAIL_ARGS = {"to": "alice@example.com", "subject": "Rapat", "body": "Rapat jam 10."}
APPROVE = {"type": "approve"}


def email_call(call_id: str = "email_1"):
    return tool_call("send_email", EMAIL_ARGS, call_id)


def weather_call(call_id: str = "weather_1"):
    return tool_call("get_weather", {"location": "sf"}, call_id)


def tool_messages(messages) -> list[ToolMessage]:
    return [message for message in messages if isinstance(message, ToolMessage)]


@pytest.fixture
def sent_emails():
    return []


@pytest.fixture
def reviewed_chat_with(hexa_project, sent_emails):
    """
    Factory: ReviewedChatUseCase dengan LLM palsu. `send_email` (wajib disetujui)
    mencatat pemanggilannya ke `sent_emails`; `get_weather` berjalan tanpa review.
    """
    from src.application.AI.agents.human_in_the_loop.human_in_the_loop import (
        build_human_in_the_loop_agent,
    )
    from src.application.usecases.reviewed_chat import ReviewedChatUseCase
    from src.infrastructure.AI.tools.weather_tool import get_weather

    @tool
    def send_email(to: str, subject: str, body: str) -> str:
        """Send an email to a recipient."""
        sent_emails.append({"to": to, "subject": subject, "body": body})
        return f"Email sent to {to}"

    def build(llm, **usecase_options):
        agent = build_human_in_the_loop_agent(
            llm=llm,
            tools=[get_weather, send_email],
            tools_requiring_approval={"send_email"},
            checkpointer=InMemorySaver(),
        )
        return ReviewedChatUseCase(agent, **usecase_options)

    return build


# --------------------------------------------------------------------------
# Berhenti untuk review
# --------------------------------------------------------------------------


def test_agent_pauses_for_review_before_running_a_tool_that_needs_approval(
    reviewed_chat_with, sent_emails
):
    usecase = reviewed_chat_with(scripted_model(calls(email_call()), "Terkirim."))

    turn = usecase.send_message("kirim email ke alice", THREAD)

    assert turn.answer is None
    assert turn.pending_review["action_requests"][0]["name"] == "send_email"
    assert turn.pending_review["action_requests"][0]["args"] == EMAIL_ARGS
    assert turn.pending_review["review_configs"][0]["allowed_decisions"] == [
        "approve",
        "edit",
        "reject",
    ]
    assert sent_emails == []


def test_tool_that_does_not_need_approval_runs_without_pausing(reviewed_chat_with):
    usecase = reviewed_chat_with(scripted_model(calls(weather_call()), "Cerah."))

    turn = usecase.send_message("cuaca di sf?", THREAD)

    assert turn.answer == "Cerah."
    assert turn.pending_review is None


# --------------------------------------------------------------------------
# Keputusan: approve / edit / reject
# --------------------------------------------------------------------------


def test_approved_tool_runs_with_original_arguments(reviewed_chat_with, sent_emails):
    usecase = reviewed_chat_with(scripted_model(calls(email_call()), "Terkirim."))
    usecase.send_message("kirim email ke alice", THREAD)

    turn = usecase.submit_review([APPROVE], THREAD)

    assert turn.answer == "Terkirim."
    assert sent_emails == [EMAIL_ARGS]


def test_edited_tool_runs_with_the_human_edited_arguments(
    reviewed_chat_with, sent_emails
):
    usecase = reviewed_chat_with(
        scripted_model(calls(email_call()), "Terkirim ke Bob.")
    )
    usecase.send_message("kirim email ke alice", THREAD)
    edited_args = {**EMAIL_ARGS, "to": "bob@example.com"}

    turn = usecase.submit_review(
        [
            {
                "type": "edit",
                "edited_action": {"name": "send_email", "args": edited_args},
            }
        ],
        THREAD,
    )

    assert turn.answer == "Terkirim ke Bob."
    assert sent_emails == [edited_args]


def test_rejected_tool_is_not_run_and_llm_is_told_why(reviewed_chat_with, sent_emails):
    llm = scripted_model(calls(email_call()), "Baik, email tidak saya kirim.")
    usecase = reviewed_chat_with(llm)
    usecase.send_message("kirim email ke alice", THREAD)

    turn = usecase.submit_review(
        [{"type": "reject", "message": "Alamatnya salah"}], THREAD
    )

    assert turn.answer == "Baik, email tidak saya kirim."
    assert sent_emails == []
    rejection = tool_messages(llm.received[1])[0]
    assert (rejection.content, rejection.status) == ("Alamatnya salah", "error")


def test_only_tools_needing_approval_are_reviewed_and_the_rest_still_run(
    reviewed_chat_with, sent_emails
):
    llm = scripted_model(
        calls(weather_call(), email_call()), "Cuaca cerah, email dibatalkan."
    )
    usecase = reviewed_chat_with(llm)

    pending = usecase.send_message("cek cuaca lalu email alice", THREAD).pending_review
    usecase.submit_review([{"type": "reject"}], THREAD)

    assert [action["name"] for action in pending["action_requests"]] == ["send_email"]
    assert sent_emails == []
    results = {
        message.name: message.status for message in tool_messages(llm.received[1])
    }
    assert results == {"send_email": "error", "get_weather": "success"}


def test_each_reviewed_tool_gets_its_own_decision_in_order(
    reviewed_chat_with, sent_emails
):
    second_email = tool_call(
        "send_email", {**EMAIL_ARGS, "to": "bob@example.com"}, "email_2"
    )
    usecase = reviewed_chat_with(
        scripted_model(calls(email_call(), second_email), "Selesai.")
    )
    usecase.send_message("email alice dan bob", THREAD)

    usecase.submit_review([{"type": "reject"}, APPROVE], THREAD)

    assert [email["to"] for email in sent_emails] == ["bob@example.com"]


def test_conversation_continues_normally_after_a_review(reviewed_chat_with):
    llm = scripted_model(calls(email_call()), "Terkirim.", "Sama-sama.")
    usecase = reviewed_chat_with(llm)
    usecase.send_message("kirim email ke alice", THREAD)
    usecase.submit_review([APPROVE], THREAD)

    turn = usecase.send_message("terima kasih", THREAD)

    assert turn.answer == "Sama-sama."


# --------------------------------------------------------------------------
# Penjagaan alur review
# --------------------------------------------------------------------------


def test_reviewed_action_without_a_decision_is_not_run(hexa_project, sent_emails):
    from langgraph.types import Command

    from src.application.AI.agents.human_in_the_loop.human_in_the_loop import (
        build_human_in_the_loop_agent,
    )

    @tool
    def send_email(to: str, subject: str, body: str) -> str:
        """Send an email to a recipient."""
        sent_emails.append(to)
        return f"Email sent to {to}"

    two_emails = calls(email_call("email_1"), email_call("email_2"))
    agent = build_human_in_the_loop_agent(
        llm=scripted_model(two_emails, "Satu email terkirim."),
        tools=[send_email],
        tools_requiring_approval={"send_email"},
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": THREAD}}
    agent.invoke({"messages": [{"role": "user", "content": "kirim dua email"}]}, config)

    result = agent.invoke(Command(resume={"decisions": [APPROVE]}), config)

    undecided = [m for m in tool_messages(result["messages"]) if m.status == "error"]
    assert sent_emails == ["alice@example.com"]
    assert len(undecided) == 1
    assert "No decision was given" in undecided[0].content


def test_edited_arguments_that_do_not_fit_the_tool_are_reported_to_the_model(
    reviewed_chat_with, sent_emails
):
    llm = scripted_model(calls(email_call()), "Argumennya belum lengkap.")
    usecase = reviewed_chat_with(llm)
    usecase.send_message("kirim email ke alice", THREAD)
    incomplete_args = {"to": "alice@example.com"}

    turn = usecase.submit_review(
        [
            {
                "type": "edit",
                "edited_action": {"name": "send_email", "args": incomplete_args},
            }
        ],
        THREAD,
    )

    tool_result = tool_messages(llm.received[1])[-1]
    assert turn.answer == "Argumennya belum lengkap."
    assert sent_emails == []
    assert tool_result.status == "error"
    assert "subject" in tool_result.content and "body" in tool_result.content


def test_model_arguments_that_do_not_fit_the_tool_are_reported_to_the_model(
    reviewed_chat_with,
):
    weather_without_location = tool_call("get_weather", {}, "weather_1")
    llm = scripted_model(calls(weather_without_location), "Lokasinya di mana?")
    usecase = reviewed_chat_with(llm)

    turn = usecase.send_message("cuaca?", THREAD)

    tool_result = tool_messages(llm.received[1])[-1]
    assert turn.answer == "Lokasinya di mana?"
    assert tool_result.status == "error"
    assert "location" in tool_result.content


def test_conversation_continues_after_arguments_were_refused(reviewed_chat_with):
    llm = scripted_model(calls(email_call()), "Argumennya belum lengkap.", "Baik.")
    usecase = reviewed_chat_with(llm)
    usecase.send_message("kirim email ke alice", THREAD)
    decision = {"type": "edit", "edited_action": {"name": "send_email", "args": {}}}
    usecase.submit_review([decision], THREAD)

    turn = usecase.send_message("lupakan saja", THREAD)

    assert turn.answer == "Baik."
    assert turn.pending_review is None


def test_new_message_is_refused_while_a_review_is_pending(reviewed_chat_with):
    from src.domain.exceptions import ReviewPendingError

    usecase = reviewed_chat_with(scripted_model(calls(email_call()), "Terkirim."))
    usecase.send_message("kirim email ke alice", THREAD)

    with pytest.raises(ReviewPendingError):
        usecase.send_message("eh, satu lagi", THREAD)
    assert usecase.submit_review([APPROVE], THREAD).answer == "Terkirim."


def test_review_without_anything_pending_is_refused(reviewed_chat_with):
    from src.domain.exceptions import NoPendingReviewError

    usecase = reviewed_chat_with(scripted_model("Halo"))
    usecase.send_message("halo", THREAD)

    with pytest.raises(NoPendingReviewError):
        usecase.submit_review([APPROVE], THREAD)


@pytest.mark.parametrize(
    "bad_decisions",
    [
        [],
        [APPROVE, APPROVE],
        [{"type": "postpone"}],
        [{"type": "edit"}],
    ],
)
def test_invalid_decisions_are_refused_and_review_can_still_be_completed(
    reviewed_chat_with, sent_emails, bad_decisions
):
    from src.domain.exceptions import InvalidReviewDecisionError

    usecase = reviewed_chat_with(scripted_model(calls(email_call()), "Terkirim."))
    usecase.send_message("kirim email ke alice", THREAD)

    with pytest.raises(InvalidReviewDecisionError):
        usecase.submit_review(bad_decisions, THREAD)

    assert usecase.submit_review([APPROVE], THREAD).answer == "Terkirim."
    assert sent_emails == [EMAIL_ARGS]


@pytest.mark.parametrize("max_agent_steps", [7, 8, 9, 25])
def test_agent_that_keeps_calling_tools_stops_with_an_answer_instead_of_an_error(
    reviewed_chat_with, max_agent_steps
):
    from src.application.AI.agents.react.nodes.react_nodes import STEP_LIMIT_MESSAGE

    endless_weather_calls = [calls(weather_call(f"w{i}")) for i in range(50)]
    usecase = reviewed_chat_with(
        scripted_model(*endless_weather_calls), max_agent_steps=max_agent_steps
    )

    assert usecase.send_message("cuaca di sf?", THREAD).answer == STEP_LIMIT_MESSAGE


def test_unknown_tool_in_approval_list_is_reported_when_building(hexa_project):
    from src.application.AI.agents.human_in_the_loop.human_in_the_loop import (
        build_human_in_the_loop_agent,
    )
    from src.infrastructure.AI.tools.weather_tool import get_weather

    with pytest.raises(ValueError, match="delete_database"):
        build_human_in_the_loop_agent(
            llm=scripted_model(),
            tools=[get_weather],
            tools_requiring_approval={"delete_database"},
            checkpointer=InMemorySaver(),
        )


# --------------------------------------------------------------------------
# HTTP interface
# --------------------------------------------------------------------------


@pytest.fixture
def http_client(http_app, reviewed_chat_with):
    from fastapi.testclient import TestClient

    from src.interface.http.controllers.hitl_controller import get_reviewed_chat_usecase

    def build(llm):
        usecase = reviewed_chat_with(llm)
        http_app.dependency_overrides[get_reviewed_chat_usecase] = lambda: usecase
        return TestClient(http_app)

    return build


def test_hitl_chat_endpoint_returns_pending_review_instead_of_answer(http_client):
    client = http_client(scripted_model(calls(email_call()), "Terkirim."))

    body = client.post("/hitl/chat", json={"message": "kirim email ke alice"}).json()

    assert body["answer"] is None
    assert body["thread_id"]
    assert body["pending_review"]["action_requests"][0]["name"] == "send_email"


def test_hitl_review_endpoint_resumes_the_agent(http_client, sent_emails):
    client = http_client(scripted_model(calls(email_call()), "Terkirim."))
    thread_id = client.post(
        "/hitl/chat", json={"message": "kirim email ke alice"}
    ).json()["thread_id"]

    response = client.post(
        "/hitl/review",
        json={"thread_id": thread_id, "decisions": [{"type": "approve"}]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "thread_id": thread_id,
        "answer": "Terkirim.",
        "pending_review": None,
    }
    assert sent_emails == [EMAIL_ARGS]


def test_hitl_review_endpoint_passes_edited_arguments(http_client, sent_emails):
    client = http_client(scripted_model(calls(email_call()), "Terkirim."))
    thread_id = client.post(
        "/hitl/chat", json={"message": "kirim email ke alice"}
    ).json()["thread_id"]
    edited_args = {**EMAIL_ARGS, "subject": "Rapat diundur"}

    client.post(
        "/hitl/review",
        json={
            "thread_id": thread_id,
            "decisions": [
                {
                    "type": "edit",
                    "edited_action": {"name": "send_email", "args": edited_args},
                }
            ],
        },
    )

    assert sent_emails == [edited_args]


def test_hitl_review_endpoint_reports_review_flow_errors_as_client_errors(http_client):
    client = http_client(scripted_model("Halo"))
    thread_id = client.post("/hitl/chat", json={"message": "halo"}).json()["thread_id"]

    response = client.post(
        "/hitl/review",
        json={"thread_id": thread_id, "decisions": [{"type": "approve"}]},
    )

    assert response.status_code == 400
    assert "Tidak ada aksi" in response.json()["detail"]
