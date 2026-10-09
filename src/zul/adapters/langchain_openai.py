"""
Adapter langchain-openai: chat model dan model embedding lewat endpoint OpenAI.

Gunanya:
    Satu-satunya file Zul yang mengimpor langchain_openai. Chat model dan
    model embedding dibuat dari nilai config biasa, lalu dipakai lewat
    fungsi di sini: jawaban chat keluar sebagai ChatReply berisi teks dan
    jumlah token, dan embedding keluar sebagai list[float]. Butuh extra
    llm: `pip install "zul[llm]"`.

Cara pakai:
    from zul.adapters import langchain_openai as openai_adapter

    model = openai_adapter.create_chat_model(
        base_url="https://HOST/v1", api_key="API_KEY", model="NAMA_MODEL",
        temperature=0.1,
    )
    reply = openai_adapter.chat(model, "Apa ibu kota Indonesia?")
    reply.content, reply.token_usage

    embeddings = openai_adapter.create_embeddings(
        base_url="https://HOST/v1", api_key="API_KEY", model="NAMA_MODEL",
    )
    vector = openai_adapter.embed_query(embeddings, "Jakarta")    # list[float]

Membuat model tidak menghubungi server. Request pertama baru dikirim oleh
`chat` atau `embed_query`, dan error dari endpoint diteruskan apa adanya.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# --------------------------------------------------------------------------
# Chat Model
# --------------------------------------------------------------------------
#
# ChatOpenAI dipakai sebagai handle: objeknya hanya diteruskan ke chat().
# Opsi yang bernilai None tidak dikirim, sehingga nilai bawaan LangChain
# yang berlaku, sama seperti saat opsi itu tidak ditulis sama sekali.
#


@dataclass(frozen=True)
class ChatReply:
    """Satu jawaban chat model sebagai tipe Python biasa.

    `content` biasanya teks. Beberapa model mengembalikan list blok konten,
    dan list itu diteruskan apa adanya. `token_usage` berisi jumlah token
    per jenis, misalnya prompt_tokens; rincian bertingkat seperti
    completion_tokens_details tidak ikut. Field yang tidak dikirim
    endpoint bernilai None.
    """

    content: str | list[Any]
    model_name: str | None = None
    finish_reason: str | None = None
    token_usage: dict[str, int] | None = None


def create_chat_model(
    base_url: str,
    api_key: str,
    model: str,
    temperature: float,
    max_tokens: int | None = None,
    timeout: float | None = None,
) -> Any:
    """Chat model untuk endpoint yang kompatibel dengan OpenAI.

    Objek yang dikembalikan hanya untuk diteruskan ke `chat`.
    """
    options: dict[str, Any] = {}
    if max_tokens is not None:
        options["max_tokens"] = max_tokens
    if timeout is not None:
        options["timeout"] = timeout
    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=temperature,
        **options,
    )


def chat(model: Any, prompt: str) -> ChatReply:
    """Kirim satu prompt ke model dari `create_chat_model`, lalu baca jawabannya."""
    message = model.invoke(prompt)
    metadata = getattr(message, "response_metadata", None) or {}
    return ChatReply(
        content=message.content,
        model_name=metadata.get("model_name"),
        finish_reason=metadata.get("finish_reason"),
        token_usage=token_counts(metadata.get("token_usage")),
    )


def token_counts(usage: dict[str, Any] | None) -> dict[str, int] | None:
    """Hanya jumlah token yang berupa angka bulat dari blok `usage` OpenAI.

    Endpoint OpenAI dan vLLM ikut mengirim rincian seperti
    `prompt_tokens_details`, yang berupa dict atau None. Rincian itu
    dibuang, supaya hasilnya selalu `dict[str, int]`.
    """
    if usage is None:
        return None
    return {
        name: count
        for name, count in usage.items()
        if isinstance(count, int) and not isinstance(count, bool)
    }


# --------------------------------------------------------------------------
# Model Embedding
# --------------------------------------------------------------------------


def create_embeddings(
    base_url: str,
    api_key: str,
    model: str,
    timeout: float | None = None,
) -> Any:
    """Model embedding untuk endpoint yang kompatibel dengan OpenAI.

    Objek yang dikembalikan hanya untuk diteruskan ke `embed_query`.
    """
    options: dict[str, Any] = {}
    if timeout is not None:
        options["timeout"] = timeout
    return OpenAIEmbeddings(base_url=base_url, api_key=api_key, model=model, **options)


def embed_query(embeddings: Any, text: str) -> list[float]:
    """Vektor embedding satu teks, dari model hasil `create_embeddings`."""
    return list(embeddings.embed_query(text))
