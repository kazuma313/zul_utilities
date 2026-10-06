"""
Fixture bersama untuk semua test.

Gunanya:
    Menyediakan LLM palsu supaya test berjalan cepat, gratis, dan hasilnya
    selalu sama, tanpa API key. Polanya mengikuti panduan unit testing LangChain:
    `GenericFakeChatModel` menjawab sesuai naskah yang kamu berikan.

Cara pakai di test:
    def test_agent_menjawab(scripted_model):
        llm = scripted_model("Halo juga!")      # satu jawaban per pemanggilan LLM
        agent = build_react_agent(llm=llm, tools=[])
        ...

    # Naskah berisi tool call lalu jawaban akhir:
    llm = scripted_model(
        AIMessage(content="", tool_calls=[
            {"name": "get_weather", "args": {"location": "sf"}, "id": "call_1"},
        ]),
        "Cerah di San Francisco.",
    )

    llm.received      # daftar pesan yang diterima LLM di tiap pemanggilan
    llm.bound_tools   # tools yang diberikan agent ke LLM
"""

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from pydantic import Field


class FakeToolCallingModel(GenericFakeChatModel):
    """Model palsu yang bisa di-bind tools dan mencatat pesan yang diterimanya."""

    received: list = Field(default_factory=list)
    bound_tools: list = Field(default_factory=list)

    def bind_tools(self, tools, **_kwargs):
        self.bound_tools = list(tools)
        return self

    def _generate(self, messages, *args, **kwargs):
        self.received.append(messages)
        return super()._generate(messages, *args, **kwargs)


@pytest.fixture
def scripted_model():
    """Factory LLM palsu: `scripted_model("jawaban 1", "jawaban 2", ...)`."""

    def build(*responses) -> FakeToolCallingModel:
        return FakeToolCallingModel(messages=iter(responses))

    return build
