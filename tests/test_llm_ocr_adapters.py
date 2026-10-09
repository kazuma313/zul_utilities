"""Adapter LLM dan OCR, diuji dengan model dan client palsu.

Tidak ada test di sini yang menghubungi server, butuh API key, atau
mengunduh model. Objek library sungguhan hanya dibuat, tidak dipanggil.
"""

import logging
import os
from types import SimpleNamespace

import pytest

# --------------------------------------------------------------------------
# Model Dan Client Palsu
# --------------------------------------------------------------------------


class FakeChatModel:
    """Pengganti ChatOpenAI: mencatat prompt dan mengembalikan pesan tetap."""

    def __init__(self, content="Jakarta", metadata=None, error=None):
        self.content = content
        self.metadata = metadata if metadata is not None else {}
        self.error = error
        self.prompts = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(content=self.content, response_metadata=self.metadata)


class FakeEmbeddings:
    """Pengganti OpenAIEmbeddings: vektor tetap untuk setiap teks."""

    def __init__(self, vector=(0.25, -0.5, 1.0), error=None):
        self.vector = list(vector)
        self.error = error

    def embed_query(self, text):
        if self.error is not None:
            raise self.error
        return list(self.vector)


OPENAI_METADATA = {
    "model_name": "qwen-server",
    "finish_reason": "stop",
    "token_usage": {
        "prompt_tokens": 5,
        "completion_tokens": 2,
        "total_tokens": 7,
        "completion_tokens_details": None,
        "prompt_tokens_details": {"cached_tokens": 0},
    },
}


@pytest.fixture
def openai_adapter():
    pytest.importorskip("langchain_openai")
    from zul.adapters import langchain_openai

    return langchain_openai


@pytest.fixture
def no_ai_env(monkeypatch):
    """Hapus environment variable AI supaya config hanya berisi nilai di test."""
    for name in list(os.environ):
        if name.startswith(("LLM_", "EMBEDDING_", "SERVICE_")):
            monkeypatch.delenv(name)


# --------------------------------------------------------------------------
# Adapter langchain_openai
# --------------------------------------------------------------------------


def test_chat_returns_text_model_and_flat_token_counts(openai_adapter):
    model = FakeChatModel(content="Jakarta", metadata=OPENAI_METADATA)

    reply = openai_adapter.chat(model, "Apa ibu kota Indonesia?")

    assert model.prompts == ["Apa ibu kota Indonesia?"]
    assert reply == openai_adapter.ChatReply(
        content="Jakarta",
        model_name="qwen-server",
        finish_reason="stop",
        token_usage={"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
    )


def test_chat_without_metadata_leaves_fields_empty(openai_adapter):
    reply = openai_adapter.chat(FakeChatModel(content="halo"), "hai")

    assert reply == openai_adapter.ChatReply(content="halo")


def test_chat_passes_model_errors_through(openai_adapter):
    model = FakeChatModel(error=ConnectionError("server mati"))

    with pytest.raises(ConnectionError, match="server mati"):
        openai_adapter.chat(model, "hai")


def test_create_chat_model_uses_the_config_values(openai_adapter):
    model = openai_adapter.create_chat_model(
        base_url="http://127.0.0.1:9/v1",
        api_key="test-key",
        model="qwen-kecil",
        temperature=0.3,
        max_tokens=64,
        timeout=7,
    )

    assert model.model_name == "qwen-kecil"
    assert model.temperature == 0.3
    assert model.max_tokens == 64
    assert model.request_timeout == 7
    assert model.openai_api_base == "http://127.0.0.1:9/v1"


def test_create_chat_model_leaves_unset_options_to_langchain(openai_adapter):
    model = openai_adapter.create_chat_model(
        base_url="http://127.0.0.1:9/v1",
        api_key="test-key",
        model="qwen-kecil",
        temperature=0.1,
    )

    assert model.max_tokens is None
    assert model.request_timeout is None


def test_create_embeddings_and_embed_query(openai_adapter):
    embeddings = openai_adapter.create_embeddings(
        base_url="http://127.0.0.1:9/v1",
        api_key="test-key",
        model="embed-kecil",
        timeout=3,
    )

    assert embeddings.model == "embed-kecil"
    assert embeddings.request_timeout == 3
    assert openai_adapter.embed_query(FakeEmbeddings(), "teks") == [0.25, -0.5, 1.0]


# --------------------------------------------------------------------------
# AIService Dari embedding_service
# --------------------------------------------------------------------------


@pytest.fixture
def full_service(openai_adapter, no_ai_env, monkeypatch):
    """AIService lengkap dengan chat model dan embedding palsu dari adapter."""
    from zul.utilities.embedding_service import (
        AIConfig,
        AIService,
        EmbeddingConfig,
        LLMConfig,
    )

    created = {}

    def fake_chat_model(**options):
        created["chat"] = options
        return created.setdefault("chat_model", FakeChatModel())

    def fake_embeddings(**options):
        created["embeddings"] = options
        return FakeEmbeddings()

    monkeypatch.setattr(openai_adapter, "create_chat_model", fake_chat_model)
    monkeypatch.setattr(openai_adapter, "create_embeddings", fake_embeddings)
    config = AIConfig(
        llm=LLMConfig(api_key="llm-key", model="qwen-config"),
        embedding=EmbeddingConfig(api_key="embed-key", model="embed-config"),
    )
    service = AIService(config)
    service.created = created
    return service


def test_ai_service_chat_returns_chat_response(full_service):
    full_service.created["chat_model"] = FakeChatModel(
        content="Jakarta", metadata=OPENAI_METADATA
    )

    response = full_service.chat("Apa ibu kota Indonesia?")

    assert response.content == "Jakarta"
    assert response.model == "qwen-server"
    assert response.finish_reason == "stop"
    assert response.usage == {
        "prompt_tokens": 5,
        "completion_tokens": 2,
        "total_tokens": 7,
    }
    assert full_service.created["chat"] == {
        "base_url": "https://llmservice.air.id",
        "api_key": "llm-key",
        "model": "qwen-config",
        "temperature": 0.1,
        "max_tokens": 2048,
        "timeout": 30,
    }


def test_ai_service_chat_falls_back_to_the_config_model_name(full_service):
    response = full_service.chat("hai")

    assert response.model == "qwen-config"
    assert response.usage is None


def test_ai_service_chat_wraps_errors_in_runtime_error(full_service):
    full_service.created["chat_model"] = FakeChatModel(error=TimeoutError("lambat"))

    with pytest.raises(RuntimeError, match="Chat request failed: lambat"):
        full_service.chat("hai")


def test_ai_service_embed_returns_embed_response(full_service):
    response = full_service.embed("Paris")

    assert response.vector == [0.25, -0.5, 1.0]
    assert response.dimensions == 3
    assert response.model == "embed-config"
    assert full_service.created["embeddings"] == {
        "base_url": "",
        "api_key": "embed-key",
        "model": "embed-config",
        "timeout": 30,
    }


def test_ai_service_embed_is_unavailable_without_embedding_config(
    openai_adapter, no_ai_env
):
    from zul.utilities.embedding_service import AIConfig, AIService, LLMConfig

    service = AIService(AIConfig(llm=LLMConfig(api_key="llm-key")))

    assert not service.is_embedding_enabled()
    with pytest.raises(ValueError, match="Embedding is not available"):
        service.embed("Paris")


# --------------------------------------------------------------------------
# AIService Ringkas Dari ai_models
# --------------------------------------------------------------------------


@pytest.fixture
def ai_models(openai_adapter, monkeypatch):
    from zul.utilities.script_helper import ai_models

    monkeypatch.setattr(
        openai_adapter, "create_chat_model", lambda **options: FakeChatModel()
    )
    monkeypatch.setattr(
        openai_adapter, "create_embeddings", lambda **options: FakeEmbeddings()
    )
    return ai_models


def test_short_ai_service_chat_and_embed(ai_models):
    config = ai_models.AIConfig(
        llm_config=ai_models.LLMConfig(api_key="llm-key"),
        embedding_config=ai_models.EmbeddingConfig(api_key="embed-key"),
    )
    service = ai_models.AIService(config)

    assert service.chat("Apa ibu kota Indonesia?") == "Jakarta"
    assert service.embed("Paris") == [0.25, -0.5, 1.0]
    assert service.is_embedding_enabled()


def test_short_ai_service_errors(ai_models):
    config = ai_models.AIConfig(
        llm_config=ai_models.LLMConfig(api_key="llm-key"), embedding_config=None
    )
    service = ai_models.AIService(config)
    service.llm = FakeChatModel(error=TimeoutError("lambat"))

    with pytest.raises(RuntimeError, match="Chat failed: lambat"):
        service.chat("hai")
    with pytest.raises(ValueError, match="Embedding not enabled"):
        service.embed("Paris")


# --------------------------------------------------------------------------
# Adapter langgraph Dan react_graph
# --------------------------------------------------------------------------


@pytest.fixture
def langgraph_adapter():
    pytest.importorskip("langgraph")
    from zul.adapters import langgraph

    return langgraph


def test_chain_runs_nodes_in_order(langgraph_adapter):
    from pydantic import BaseModel

    class State(BaseModel):
        a: str

    def first(state):
        return {"a": state.a + "1"}

    def second(state):
        return {"a": state.a + "2"}

    graph = langgraph_adapter.compile_graph(
        langgraph_adapter.chain(State, [first, second])
    )

    assert langgraph_adapter.invoke(graph, {"a": "x"}) == {"a": "x12"}


def test_chain_needs_at_least_one_node(langgraph_adapter):
    from pydantic import BaseModel

    class State(BaseModel):
        a: str

    with pytest.raises(ValueError, match="minimal satu"):
        langgraph_adapter.chain(State, [])


def test_react_graph_still_works_as_a_langgraph_graph(langgraph_adapter):
    from zul.utilities import react_graph

    assert react_graph.graph.invoke({"a": "hello"}) == {"a": "goodbye"}
    assert langgraph_adapter.invoke(react_graph.graph, {"a": "hello"}) == {
        "a": "goodbye"
    }
    assert react_graph.node(react_graph.OverallState(a="hello")) == {"a": "goodbye"}
    assert "node" in react_graph.builder.nodes


# --------------------------------------------------------------------------
# Adapter docling Dan DoclingVLMConverter
# --------------------------------------------------------------------------


@pytest.fixture
def docling_adapter():
    pytest.importorskip("docling")
    from zul.adapters import docling

    return docling


class FakeDocument:
    def export_to_markdown(self):
        return "# Judul"

    def export_to_text(self):
        return "Judul"

    def export_to_dict(self):
        return {"name": "dokumen"}


def test_converter_rejects_an_unknown_response_format(docling_adapter):
    from zul.utilities.OCR.docling_OCR import DoclingVLMConverter

    with pytest.raises(ValueError, match="Invalid response_format 'json'"):
        DoclingVLMConverter(
            model="vlm", hostname_and_port="http://x", response_format="json"
        )


def test_converter_keeps_docling_response_format(docling_adapter):
    from zul.utilities.OCR.docling_OCR import RESPONSE_FORMATS, DoclingVLMConverter

    converter = DoclingVLMConverter(
        model="vlm", hostname_and_port="http://x", response_format="Markdown"
    )

    assert converter.response_format is RESPONSE_FORMATS["markdown"]
    assert converter.response_format == "markdown"
    assert type(converter.response_format).__name__ == "ResponseFormat"


def test_converter_builds_once_and_exports_through_the_adapter(
    docling_adapter, monkeypatch
):
    from zul.utilities.OCR.docling_OCR import DoclingVLMConverter

    created, converted = [], []
    monkeypatch.setattr(
        docling_adapter,
        "create_converter",
        lambda **options: created.append(options) or "converter-handle",
    )
    monkeypatch.setattr(
        docling_adapter,
        "convert",
        lambda converter, path: converted.append((converter, path))
        or SimpleNamespace(document=FakeDocument()),
    )
    converter = DoclingVLMConverter(
        model="vlm",
        hostname_and_port="http://127.0.0.1:9/v1/chat/completions",
        api_key="key",
        prompt="Convert this page to markdown.",
        response_format="markdown",
    )

    assert converter.convert_to_markdown("a.pdf") == "# Judul"
    assert converter.convert_to_text("b.pdf") == "Judul"
    assert converter.convert_to_dict("c.pdf") == {"name": "dokumen"}
    assert converted == [
        ("converter-handle", "a.pdf"),
        ("converter-handle", "b.pdf"),
        ("converter-handle", "c.pdf"),
    ]
    assert len(created) == 1
    assert created[0]["url"] == "http://127.0.0.1:9/v1/chat/completions"
    assert created[0]["response_format"] == "markdown"
    assert created[0]["picture_prompt"] == (
        "Convert this page to markdown. "
        "Describe diagrams, flowcharts, and shapes concisely."
    )


def test_create_converter_builds_vlm_options(docling_adapter):
    from docling.datamodel.base_models import InputFormat

    converter = docling_adapter.create_converter(
        url="http://127.0.0.1:9/v1/chat/completions",
        model="vlm",
        prompt="Convert this page to markdown.",
        response_format="deepseek_markdown",
        api_key="key",
        enable_picture_description=True,
        picture_prompt="Describe the flowchart.",
    )

    options = converter.format_to_options[InputFormat.PDF].pipeline_options
    assert options.vlm_options.response_format == "deepseekocr_markdown"
    assert options.vlm_options.headers == {"Authorization": "Bearer key"}
    assert options.vlm_options.params == {
        "model": "vlm",
        "max_tokens": 4096,
        "skip_special_tokens": False,
    }
    assert options.do_picture_description
    assert options.picture_description_options.prompt == "Describe the flowchart."


def test_create_converter_without_api_key_sends_no_authorization(docling_adapter):
    from docling.datamodel.base_models import InputFormat

    converter = docling_adapter.create_converter(
        url="http://127.0.0.1:9/v1/chat/completions",
        model="vlm",
        prompt="p",
        response_format="doctags",
    )

    options = converter.format_to_options[InputFormat.IMAGE].pipeline_options
    assert options.vlm_options.headers == {}
    assert not options.do_picture_description


def test_old_docling_import_path_still_works(docling_adapter):
    from zul.utilities.docling_OCR import DoclingVLMConverter as OldPath
    from zul.utilities.OCR.docling_OCR import DoclingVLMConverter

    assert OldPath is DoclingVLMConverter


# --------------------------------------------------------------------------
# Adapter gemini Dan gemini_ocr
# --------------------------------------------------------------------------


class FakeGeminiClient:
    """Pengganti genai.Client dengan bagian files dan models yang dipakai Zul."""

    def __init__(self, error=None):
        self.error = error
        self.uploaded, self.deleted, self.requests = [], [], []
        self.files = SimpleNamespace(upload=self._upload, delete=self._delete)
        self.models = SimpleNamespace(generate_content=self._generate)

    def _upload(self, file):
        self.uploaded.append(file)
        return SimpleNamespace(
            name="files/abc",
            uri="https://gemini/files/abc",
            mime_type="application/pdf",
        )

    def _delete(self, name):
        self.deleted.append(name)

    def _generate(self, model, contents):
        self.requests.append((model, contents))
        if self.error is not None:
            raise self.error
        return SimpleNamespace(text="# Isi PDF")


@pytest.fixture
def gemini_ocr():
    pytest.importorskip("google.genai")
    from zul.utilities.OCR import gemini_ocr

    return gemini_ocr


@pytest.fixture
def pdf_file(tmp_path):
    path = tmp_path / "dokumen.pdf"
    path.write_bytes(b"%PDF-1.4\n")
    return str(path)


def test_process_pdf_uploads_asks_and_deletes(gemini_ocr, pdf_file):
    client = FakeGeminiClient()

    text = gemini_ocr.process_pdf_with_gemini(
        client, pdf_file, "Extract as markdown.", logging.getLogger("test")
    )

    assert text == "# Isi PDF"
    assert client.uploaded == [pdf_file]
    assert client.deleted == ["files/abc"]
    model, (prompt, part) = client.requests[0]
    assert model == "gemini-2.5-pro"
    assert prompt == "Extract as markdown."
    assert part.file_data.file_uri == "https://gemini/files/abc"
    assert part.file_data.mime_type == "application/pdf"


def test_process_pdf_returns_none_on_error_and_still_deletes(gemini_ocr, pdf_file):
    client = FakeGeminiClient(error=RuntimeError("kuota habis"))

    text = gemini_ocr.process_pdf_with_gemini(
        client, pdf_file, "p", logging.getLogger("test")
    )

    assert text is None
    assert client.deleted == ["files/abc"]


def test_process_pdf_returns_none_for_a_missing_file(gemini_ocr, tmp_path):
    client = FakeGeminiClient()

    text = gemini_ocr.process_pdf_with_gemini(
        client, str(tmp_path / "tidak-ada.pdf"), "p", logging.getLogger("test")
    )

    assert text is None
    assert client.uploaded == []


def test_create_gemini_client(gemini_ocr, monkeypatch):
    from zul.adapters import gemini as gemini_adapter

    logger = logging.getLogger("test")
    assert gemini_ocr.create_gemini_client("", logger) is None

    monkeypatch.setattr(gemini_adapter, "create_client", lambda api_key: "client")
    assert gemini_ocr.create_gemini_client("key", logger) == "client"

    def broken(api_key):
        raise ValueError("key ditolak")

    monkeypatch.setattr(gemini_adapter, "create_client", broken)
    assert gemini_ocr.create_gemini_client("key", logger) is None


def test_gemini_adapter_creates_a_client_without_network(gemini_ocr):
    from zul.adapters import gemini as gemini_adapter

    client = gemini_adapter.create_client("test-key")

    assert type(client).__name__ == "Client"


def test_generate_text_needs_uri_and_mime_type(gemini_ocr):
    from zul.adapters import gemini as gemini_adapter

    file = gemini_adapter.UploadedFile(name="files/abc", uri=None, mime_type=None)

    with pytest.raises(ValueError, match="uri and mime_type"):
        gemini_adapter.generate_text(FakeGeminiClient(), "m", "p", file)
