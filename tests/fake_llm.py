"""LLM palsu untuk test agent, mengikuti panduan unit testing LangChain."""

from langchain.messages import AIMessage
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from pydantic import Field


class FakeToolCallingModel(GenericFakeChatModel):
    """GenericFakeChatModel yang bisa di-bind tools dan mencatat pesan masuk."""

    received: list = Field(default_factory=list)
    bound_tools: list = Field(default_factory=list)

    def bind_tools(self, tools, **_kwargs):
        self.bound_tools = list(tools)
        return self

    def _generate(self, messages, *args, **kwargs):
        self.received.append(messages)
        return super()._generate(messages, *args, **kwargs)


def scripted_model(*responses) -> FakeToolCallingModel:
    """Model bernaskah: satu respons (str / AIMessage) untuk tiap pemanggilan."""
    return FakeToolCallingModel(messages=iter(responses))


def tool_call(name: str, args: dict, call_id: str = "call_1") -> dict:
    return {"name": name, "args": args, "id": call_id}


def calls(*tool_calls: dict) -> AIMessage:
    """Respons LLM yang meminta satu atau lebih tool call."""
    return AIMessage(content="", tool_calls=list(tool_calls))


def contents(messages) -> list[str]:
    return [message.content for message in messages]
