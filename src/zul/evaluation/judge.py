"""
Skor hasil RAG dengan ragas dan model penilai.

Gunanya:
    `evaluate_rag` menilai hasil `run_rag` dengan metrik ragas yang dipilih
    lewat nama pendek, lalu mengembalikan `EvalReport`. Metrik yang butuh
    `response` dilewati otomatis jika hasilnya tanpa jawaban, jadi retrieval
    saja juga bisa dinilai. Model penilai dibaca dari `JudgeConfig`, bukan
    model yang sedang dinilai. Semua pemanggilan ragas lewat
    `zul.adapters.ragas`. Butuh extra evaluation:
    `pip install "zul[evaluation]"`.

Metrik:
    context_precision         konteks relevan di peringkat atas LLM, reference
    context_recall            semua yang dibutuhkan terambil    LLM, reference
    faithfulness              jawaban setia pada konteks        LLM, response
    answer_relevancy          jawaban menjawab pertanyaan       LLM, embedding, response
    context_precision_nonllm  context_precision tanpa LLM       reference_contexts
    context_recall_nonllm     context_recall tanpa LLM          reference_contexts

Cara pakai:
    from zul.evaluation.judge import RETRIEVAL_METRICS, evaluate_rag
    from zul.evaluation.reports import save_report

    report = evaluate_rag(results, metrics=RETRIEVAL_METRICS, name="redis-rrf")
    print(report.summary)        # {"context_precision": 0.41, "context_recall": 0.38}
    save_report(report, "outputs")
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from zul.adapters import ragas as ragas_adapter

from .config import OPENAI_BASE_URL, JudgeConfig
from .dataset import load_results
from .reports import EvalReport, summarize_scores

RETRIEVAL_METRICS: tuple[str, ...] = ("context_precision", "context_recall")
GENERATION_METRICS: tuple[str, ...] = ("faithfulness", "answer_relevancy")
DEFAULT_METRICS: tuple[str, ...] = RETRIEVAL_METRICS + GENERATION_METRICS
NONLLM_METRICS: tuple[str, ...] = ("context_precision_nonllm", "context_recall_nonllm")
KNOWN_METRICS: tuple[str, ...] = DEFAULT_METRICS + NONLLM_METRICS

NEEDS_RESPONSE = set(GENERATION_METRICS)
NEEDS_EMBEDDINGS = {"answer_relevancy"}
NEEDS_REFERENCE_CONTEXTS = set(NONLLM_METRICS)

Backend = Literal["instructor", "langchain"]

# --------------------------------------------------------------------------
# Model Penilai
# --------------------------------------------------------------------------
#
# Di backend instructor, penilai mengirim jawabannya berbentuk JSON lewat
# client OpenAI. Backend langchain, dengan chat model LangChain biasa,
# dipakai untuk endpoint yang menolak mode JSON atau tool calling.
#


def make_judge(
    config: JudgeConfig | None = None, backend: Backend = "instructor"
) -> Any:
    """LLM penilai dari pengaturan; bawaannya `JudgeConfig.from_env()`.

    Raises:
        ValueError: kunci penilai kosong, atau `backend` tidak dikenal.
    """
    config = (config or JudgeConfig.from_env()).validate()
    if backend == "instructor":
        return ragas_adapter.judge_llm(config.model, config.api_key, config.base_url)
    if backend == "langchain":
        from zul.adapters import langchain_openai

        chat_model = langchain_openai.create_chat_model(
            base_url=config.base_url or OPENAI_BASE_URL,
            api_key=config.api_key,
            model=config.model,
            temperature=0,
        )
        return ragas_adapter.wrap_chat_model(chat_model)
    raise ValueError(f"Backend {backend!r} tidak dikenal: instructor atau langchain.")


def make_judge_embeddings(config: JudgeConfig | None = None) -> Any:
    """Embedding penilai untuk `answer_relevancy`, dari pengaturan yang sama.

    Raises:
        ValueError: kunci embedding penilai kosong.
    """
    from zul.adapters import langchain_openai

    config = config or JudgeConfig.from_env()
    if not config.embedding_api_key:
        raise ValueError(
            "Kunci embedding penilai kosong. Isi RAGAS_EMBEDDING_API_KEY, "
            "RAGAS_JUDGE_API_KEY, atau OPENAI_API_KEY di environment."
        )
    embeddings = langchain_openai.create_embeddings(
        base_url=config.embedding_base_url or OPENAI_BASE_URL,
        api_key=config.embedding_api_key,
        model=config.embedding_model,
    )
    return ragas_adapter.wrap_embeddings(embeddings)


# --------------------------------------------------------------------------
# Memilih Metrik Dan Menyusun Sampel
# --------------------------------------------------------------------------


def select_metrics(
    results: list[dict[str, Any]], metrics: Sequence[str]
) -> tuple[list[str], list[str]]:
    """Metrik yang bisa dijalankan, dan metrik yang dilewati karena tanpa jawaban.

    Raises:
        ValueError: ada nama metrik yang tidak dikenal, atau tidak ada metrik
            yang bisa dijalankan.
    """
    unknown = [name for name in metrics if name not in KNOWN_METRICS]
    if unknown:
        known = ", ".join(KNOWN_METRICS)
        raise ValueError(f"Metrik {unknown} tidak dikenal. Pilihan: {known}.")
    has_response = any(str(row.get("response") or "").strip() for row in results)
    chosen = [name for name in metrics if has_response or name not in NEEDS_RESPONSE]
    skipped = [name for name in metrics if name not in chosen]
    if not chosen:
        raise ValueError(
            "Tidak ada metrik yang bisa dijalankan: kolom response kosong dan "
            "tidak ada metrik retrieval yang dipilih."
        )
    return chosen, skipped


def to_samples(
    results: list[dict[str, Any]], need_reference_contexts: bool = False
) -> list[dict[str, Any]]:
    """Kolom ragas dari setiap hasil; `response` hanya ikut jika tidak kosong.

    Raises:
        ValueError: `need_reference_contexts` True, tetapi ada baris tanpa
            `reference_contexts`.
    """
    samples = []
    for row in results:
        sample: dict[str, Any] = {
            "user_input": str(row["user_input"]),
            "retrieved_contexts": [str(c) for c in row.get("retrieved_contexts") or []],
            "reference": str(row.get("reference") or ""),
        }
        response = str(row.get("response") or "").strip()
        if response:
            sample["response"] = response
        references = row.get("reference_contexts") or []
        if references:
            sample["reference_contexts"] = [str(c) for c in references]
        elif need_reference_contexts:
            raise ValueError(
                "Metrik *_nonllm butuh reference_contexts di setiap baris. Baris "
                f"tanpa reference_contexts: {sample['user_input'][:60]!r}"
            )
        samples.append(sample)
    return samples


# --------------------------------------------------------------------------
# Evaluasi
# --------------------------------------------------------------------------


def evaluate_rag(
    results: list[dict[str, Any]] | str | Path,
    metrics: Sequence[str] = DEFAULT_METRICS,
    *,
    name: str = "",
    judge: Any = None,
    judge_embeddings: Any = None,
    judge_config: JudgeConfig | None = None,
    judge_backend: Backend = "instructor",
    timeout: int = 180,
    max_workers: int = 8,
    batch_size: int | None = None,
    raise_exceptions: bool = False,
    show_progress: bool = True,
) -> EvalReport:
    """
    Nilai hasil `run_rag` dengan ragas.

    Args:
        results: Hasil `run_rag`, atau path file .csv/.jsonl-nya.
        metrics: Nama metrik dari `KNOWN_METRICS`.
        name: Label percobaan; bawaannya nama retriever di hasil.
        judge: LLM penilai; jika None dibuat dengan `make_judge`.
        judge_embeddings: Embedding penilai untuk answer_relevancy; jika None
            dibuat dengan `make_judge_embeddings`.
        judge_config: Pengaturan penilai; bawaannya `JudgeConfig.from_env()`.
        judge_backend: "instructor" atau "langchain", lihat `make_judge`.
        timeout: Batas detik setiap panggilan penilai. Endpoint lokal yang
            lambat butuh nilai lebih besar.
        max_workers: Jumlah panggilan penilai yang berjalan bersamaan.
        batch_size: Jumlah baris per batch ragas; None berarti sekaligus.
        raise_exceptions: True untuk berhenti di error pertama. Jika False,
            skor yang gagal bernilai None.
        show_progress: Tampilkan progress bar ragas.

    Raises:
        ValueError: hasil kosong, atau metrik tidak bisa dijalankan.
    """
    rows = load_results(results) if isinstance(results, str | Path) else list(results)
    if not rows:
        raise ValueError("Hasil RAG kosong; tidak ada yang bisa dinilai.")
    chosen, skipped = select_metrics(rows, metrics)

    need_llm = any(metric not in NEEDS_REFERENCE_CONTEXTS for metric in chosen)
    need_embeddings = any(metric in NEEDS_EMBEDDINGS for metric in chosen)
    config = None
    if (need_llm and judge is None) or (need_embeddings and judge_embeddings is None):
        config = judge_config or JudgeConfig.from_env()
    if need_llm and judge is None:
        judge = make_judge(config, backend=judge_backend)
    if need_embeddings and judge_embeddings is None:
        judge_embeddings = make_judge_embeddings(config)

    needs_references = any(metric in NEEDS_REFERENCE_CONTEXTS for metric in chosen)
    samples = to_samples(rows, need_reference_contexts=needs_references)
    scores = ragas_adapter.evaluate(
        samples,
        chosen,
        llm=judge if need_llm else None,
        embeddings=judge_embeddings if need_embeddings else None,
        timeout=timeout,
        max_workers=max_workers,
        batch_size=batch_size,
        raise_exceptions=raise_exceptions,
        show_progress=show_progress,
    )
    score_rows = [
        {**sample, **score} for sample, score in zip(samples, scores, strict=True)
    ]
    return EvalReport(
        name=name or _first(rows, "retriever") or "rag",
        metrics=chosen,
        summary=summarize_scores(score_rows, chosen),
        rows=score_rows,
        meta={
            "n": len(rows),
            "metrik_dilewati": skipped,
            "judge": config.safe_summary() if config else None,
            "retriever": _first(rows, "retriever"),
            "generator": _first(rows, "generator"),
            "top_k": _first(rows, "top_k"),
            "waktu": datetime.now(UTC).isoformat(timespec="seconds"),
        },
    )


def _first(rows: list[dict[str, Any]], column: str) -> Any:
    value = rows[0].get(column)
    return value if value not in ("", None) else None
