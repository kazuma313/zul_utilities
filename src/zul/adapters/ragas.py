"""
Adapter ragas: metrik, model penilai, dan evaluasi hasil RAG.

Gunanya:
    Satu-satunya file Zul yang mengimpor ragas dan client OpenAI untuk model
    penilainya. Metrik dipilih dengan nama pendek, misalnya
    "context_recall", dan skornya dikembalikan dengan nama yang sama, bukan
    nama kelas ragas. Sampel dan skor berupa list dict biasa. Butuh extra
    evaluation: `pip install "zul[evaluation]"`.

Cara pakai:
    from zul.adapters import ragas as ragas_adapter

    llm = ragas_adapter.judge_llm("gpt-4o-mini", api_key=API_KEY)
    samples = [
        {
            "user_input": "Apa itu mistika?",
            "retrieved_contexts": ["Mistika adalah ajaran kebatinan."],
            "reference": "Mistika adalah ajaran kebatinan.",
        }
    ]
    scores = ragas_adapter.evaluate(samples, ["context_recall"], llm=llm)
    # [{"context_recall": 1.0}]

Penambal impor:
    ragas 0.4.x mengimpor `langchain_community.chat_models.vertexai` di
    `ragas/llms/base.py`, padahal langchain-community 0.4 sudah menghapus
    modul itu. ragas memakainya hanya untuk `isinstance`, jadi sebelum ragas
    diimpor, file ini mendaftarkan modul pengganti berisi kelas kosong. Jika
    modul aslinya ada, tidak ada yang didaftarkan. Versi ragas dikunci ke
    `>=0.4.3,<0.5`; hapus penambal ini setelah ragas berhenti mengimpornya.

API lama ragas:
    `evaluate()` dan metrik dari `ragas.metrics` ditandai usang di ragas 0.4
    dan akan dihapus di ragas 1.0. Versi dikunci ke 0.4.x, jadi peringatan
    usang dari keduanya diredam di file ini.

Embedding untuk answer_relevancy:
    Metrik `ResponseRelevancy` di ragas 0.4 memanggil `embed_query`, yang
    tidak dimiliki objek embedding baru dari `embedding_factory`. Karena itu
    `wrap_embeddings` membungkus model embedding LangChain dengan
    `LangchainEmbeddingsWrapper`, yang punya method itu.
"""

from __future__ import annotations

import importlib
import math
import sys
import types
import warnings
from typing import Any

# --------------------------------------------------------------------------
# Penambal Impor
# --------------------------------------------------------------------------
#
# Modul pengganti harus sudah terdaftar sebelum ragas diimpor, karena ragas
# langsung mengimpor modul yang hilang itu saat paketnya dimuat. Paket
# induknya diimpor lebih dulu supaya `from ... import` tetap jalan.
#

VERTEXAI_MODULE = "langchain_community.chat_models.vertexai"


def _register_missing_vertexai() -> None:
    if VERTEXAI_MODULE in sys.modules:
        return
    # langchain-community mencetak pengumuman usang saat pertama diimpor.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        importlib.import_module("langchain_community.chat_models")
    try:
        importlib.import_module(VERTEXAI_MODULE)
        return
    except ImportError:
        pass
    stub = types.ModuleType(VERTEXAI_MODULE)
    stub.ChatVertexAI = type(  # type: ignore[attr-defined]
        "ChatVertexAI", (), {"__doc__": "Pengganti kelas yang tidak pernah dibuat."}
    )
    sys.modules[VERTEXAI_MODULE] = stub


_register_missing_vertexai()

from openai import AsyncOpenAI  # noqa: E402
from ragas import EvaluationDataset  # noqa: E402
from ragas import evaluate as ragas_evaluate  # noqa: E402
from ragas import metrics as ragas_metrics  # noqa: E402
from ragas.embeddings import LangchainEmbeddingsWrapper  # noqa: E402
from ragas.llms import LangchainLLMWrapper, llm_factory  # noqa: E402
from ragas.run_config import RunConfig  # noqa: E402

# --------------------------------------------------------------------------
# Metrik
# --------------------------------------------------------------------------

METRIC_CLASSES = {
    "context_precision": "LLMContextPrecisionWithReference",
    "context_recall": "LLMContextRecall",
    "faithfulness": "Faithfulness",
    "answer_relevancy": "ResponseRelevancy",
    "context_precision_nonllm": "NonLLMContextPrecisionWithReference",
    "context_recall_nonllm": "NonLLMContextRecall",
}


def metric(name: str) -> Any:
    """Objek metrik ragas dari nama pendeknya, misalnya `"context_recall"`.

    Raises:
        ValueError: nama tidak ada di `METRIC_CLASSES`.
    """
    if name not in METRIC_CLASSES:
        known = ", ".join(METRIC_CLASSES)
        raise ValueError(f"Metrik {name!r} tidak dikenal. Pilihan: {known}.")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return getattr(ragas_metrics, METRIC_CLASSES[name])()


# --------------------------------------------------------------------------
# Model Penilai
# --------------------------------------------------------------------------
#
# Client OpenAI dibuat async supaya ragas bisa menilai beberapa
# baris sekaligus sesuai max_workers. Dengan client sinkron,
# setiap panggilan penilai menunggu panggilan sebelumnya.
#


def judge_llm(model: str, api_key: str, base_url: str | None = None) -> Any:
    """LLM penilai lewat endpoint yang kompatibel dengan OpenAI.

    Endpoint-nya harus mendukung keluaran terstruktur (JSON). Objek yang
    dikembalikan hanya untuk diteruskan ke `evaluate`.
    """
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    return llm_factory(model, client=client)


def wrap_chat_model(chat_model: Any) -> Any:
    """LLM penilai dari chat model LangChain, untuk endpoint tanpa keluaran JSON."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return LangchainLLMWrapper(chat_model)


def wrap_embeddings(embeddings: Any) -> Any:
    """Embedding penilai dari model embedding LangChain, untuk `answer_relevancy`."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return LangchainEmbeddingsWrapper(embeddings)


# --------------------------------------------------------------------------
# Evaluasi
# --------------------------------------------------------------------------


def evaluate(
    samples: list[dict[str, Any]],
    metrics: list[str],
    llm: Any = None,
    embeddings: Any = None,
    *,
    timeout: int = 180,
    max_workers: int = 8,
    batch_size: int | None = None,
    raise_exceptions: bool = False,
    show_progress: bool = True,
) -> list[dict[str, float | None]]:
    """Skor setiap sampel, satu dict {nama metrik: skor} per sampel.

    Setiap sampel berisi kolom ragas: `user_input`, `retrieved_contexts`,
    `reference`, dan bila ada `response` serta `reference_contexts`. Skor
    yang gagal dihitung, misalnya karena penilai melewati `timeout`,
    bernilai None.
    """
    built = {name: metric(name) for name in metrics}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result = ragas_evaluate(
            dataset=EvaluationDataset.from_list(samples),
            metrics=list(built.values()),
            llm=llm,
            embeddings=embeddings,
            run_config=RunConfig(timeout=timeout, max_workers=max_workers),
            batch_size=batch_size,
            raise_exceptions=raise_exceptions,
            show_progress=show_progress,
        )
    return [
        {
            name: _score(row.get(built_metric.name))
            for name, built_metric in built.items()
        }
        for row in result.scores
    ]


def _score(value: Any) -> float | None:
    if value is None:
        return None
    number = float(value)
    return None if math.isnan(number) else number
