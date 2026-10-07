# Menguji agent

Test untuk agent, tool, dan endpoint bisa ditulis tanpa memanggil LLM asli. Test seperti ini berjalan dalam hitungan detik, tidak butuh API key, dan hasilnya selalu sama.

**Sebelum mulai:** dependency pengembangan sudah di-install dengan `pip install -r requirements-dev.txt`.

## Menjalankan test

Dari root proyek, jalankan semua test:

```shell
pytest
```

Untuk menjalankan satu file atau satu test:

```shell
pytest test/test_chat_usecase.py
pytest test/test_chat_usecase.py::test_empty_message_is_rejected
```

## Menyiapkan model palsu

Fixture `scripted_model` di `test/conftest.py` membuat model palsu. Kamu memberinya naskah: satu respons untuk setiap pemanggilan model, berurutan.

Respons berupa teks menjadi jawaban biasa:

```python
def test_contoh(scripted_model):
    llm = scripted_model("Jawaban pertama", "Jawaban kedua")
```

Untuk membuat model "meminta" sebuah tool, berikan `AIMessage` berisi `tool_calls`:

```python
from langchain.messages import AIMessage

llm = scripted_model(
    AIMessage(
        content="",
        tool_calls=[{"name": "get_weather", "args": {"location": "sf"}, "id": "call_1"}],
    ),
    "Cerah di San Francisco.",
)
```

> [!NOTE]
> Jumlah respons di naskah harus sama dengan jumlah pemanggilan model. Agent yang memakai satu tool memanggil model dua kali: sekali untuk meminta tool, sekali untuk menjawab. Jika naskah habis, test gagal dengan `RuntimeError: generator raised StopIteration`.

## Menguji use case

1. Rakit agent dengan model palsu, lalu bungkus dengan use case:

    ```python title="test/test_chat_usecase.py"
    from src.application.AI.agents.react.react import build_react_agent
    from src.application.usecases.chat import ChatUseCase
    from src.infrastructure.AI.tools.weather_tool import get_weather


    def build_usecase(llm, checkpointer=None) -> ChatUseCase:
        agent = build_react_agent(llm=llm, tools=[get_weather], checkpointer=checkpointer)
        return ChatUseCase(agent)
    ```

2. Jalankan use case dan periksa hasilnya:

    ```python title="test/test_chat_usecase.py"
    def test_agent_answers_directly_when_no_tool_is_needed(scripted_model):
        usecase = build_usecase(scripted_model("Halo juga!"))

        assert usecase.execute("halo", thread_id="t1") == "Halo juga!"
    ```

3. Untuk aturan bisnis, periksa exception-nya:

    ```python title="test/test_chat_usecase.py"
    import pytest

    from src.domain.exceptions import EmptyMessageError


    def test_empty_message_is_rejected(scripted_model):
        with pytest.raises(EmptyMessageError):
            build_usecase(scripted_model()).execute("   ", thread_id="t1")
    ```

## Menguji bahwa agent memakai tool

Tulis naskah berisi permintaan tool, lalu periksa pesan yang diterima model pada pemanggilan kedua. Atribut `llm.received` mencatat pesan di setiap pemanggilan:

```python
from langchain.messages import AIMessage, ToolMessage


def test_agent_runs_the_tool_and_answers_with_its_result(scripted_model):
    llm = scripted_model(
        AIMessage(
            content="",
            tool_calls=[{"name": "get_weather", "args": {"location": "sf"}, "id": "call_1"}],
        ),
        "Cerah di San Francisco.",
    )

    answer = build_usecase(llm).execute("cuaca di sf?", thread_id="t1")

    assert answer == "Cerah di San Francisco."
    tool_results = [m for m in llm.received[1] if isinstance(m, ToolMessage)]
    assert "sunny in San Francisco" in tool_results[0].content
```

## Menguji sebuah tool sendirian

Tool bisa dipanggil langsung dengan `invoke`, tanpa agent dan tanpa model:

```python
from src.infrastructure.AI.tools.weather_tool import get_weather


def test_weather_tool_knows_san_francisco():
    result = get_weather.invoke({"location": "sf"})

    assert "sunny" in result
```

## Menguji memory

Berikan `InMemorySaver` baru, lalu panggil use case dua kali dengan `thread_id` yang sama:

```python
from langgraph.checkpoint.memory import InMemorySaver


def test_same_thread_continues_the_conversation(scripted_model):
    llm = scripted_model("Halo Bob", "Namamu Bob")
    usecase = build_usecase(llm, checkpointer=InMemorySaver())

    usecase.execute("Saya Bob", thread_id="t1")
    usecase.execute("Siapa nama saya?", thread_id="t1")

    second_call = [message.content for message in llm.received[1]]
    assert second_call[1:] == ["Saya Bob", "Halo Bob", "Siapa nama saya?"]
```

Indeks `[1:]` melewati system prompt, yang selalu berada di posisi pertama. Buat `InMemorySaver` baru di setiap test supaya percakapan tidak bocor antar test.

## Menguji persetujuan manusia

Pakai tool tiruan yang mencatat pemanggilannya, sehingga kamu bisa memeriksa kapan tool sungguh dijalankan:

```python
from langchain.messages import AIMessage
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from src.application.AI.agents.human_in_the_loop.human_in_the_loop import (
    build_human_in_the_loop_agent,
)
from src.application.usecases.reviewed_chat import ReviewedChatUseCase

EMAIL_ARGS = {"to": "alice@example.com", "subject": "Rapat", "body": "Rapat jam 10."}


def test_email_is_sent_only_after_approval(scripted_model):
    sent_emails = []

    @tool
    def send_email(to: str, subject: str, body: str) -> str:
        """Send an email to a recipient."""
        sent_emails.append(to)
        return f"Email sent to {to}"

    llm = scripted_model(
        AIMessage(
            content="",
            tool_calls=[{"name": "send_email", "args": EMAIL_ARGS, "id": "call_1"}],
        ),
        "Email terkirim.",
    )
    agent = build_human_in_the_loop_agent(
        llm=llm,
        tools=[send_email],
        tools_requiring_approval={"send_email"},
        checkpointer=InMemorySaver(),
    )
    usecase = ReviewedChatUseCase(agent)

    turn = usecase.send_message("email alice", thread_id="t1")

    assert turn.pending_review["action_requests"][0]["name"] == "send_email"
    assert sent_emails == []

    turn = usecase.submit_review([{"type": "approve"}], thread_id="t1")

    assert turn.answer == "Email terkirim."
    assert sent_emails == ["alice@example.com"]
```

## Menguji endpoint

Ganti perakit use case lewat `app.dependency_overrides`, lalu kirim request dengan `TestClient`:

```python
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver

from src.interface.http.controllers.chat_controller import get_chat_usecase
from src.interface.http.main import app


def test_chat_endpoint_returns_the_agent_answer(scripted_model):
    usecase = build_usecase(scripted_model("Halo juga!"), checkpointer=InMemorySaver())
    app.dependency_overrides[get_chat_usecase] = lambda: usecase

    try:
        response = TestClient(app).post("/chat", json={"message": "halo"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["answer"] == "Halo juga!"
```

Blok `finally` membersihkan pengganti itu supaya test lain tidak memakai use case ini.

## Halaman terkait

- [Menguji tanpa LLM asli](../konsep/pengujian.md) untuk apa yang dibuktikan test seperti ini, dan apa yang tidak.
- [Mencoba fitur di playground](mencoba-di-playground.md) untuk mencoba agent dengan model sungguhan.
- [API agent](../referensi/agent.md) untuk exception yang bisa kamu periksa di test.
