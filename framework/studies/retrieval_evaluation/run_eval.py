"""
CLI studi evaluasi retrieval, di atas `zul.evaluation`.

    uv run python run_eval.py dataset data/qa.xlsx data/qa2.xlsx
    uv run python run_eval.py rag data/qa.xlsx --index recursive_qwen \\
        --prefix recursive --dims 2560 --mode rrf --top-k 5 --out outputs/redis-rrf.csv
    uv run python run_eval.py hits outputs/redis-rrf.csv
    uv run python run_eval.py ragas outputs/redis-rrf.csv \\
        --metrics context_precision,context_recall
    uv run python run_eval.py compare outputs/*.scores.json

Jalankan dari folder ini (framework/studies/retrieval_evaluation) dengan .env di akar
repo sudah terisi. Perintah `rag` memakai Redis; untuk Milvus atau retriever
lain, pakai `zul.evaluation` langsung dari Python (lihat README.md).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import typer
from dotenv import load_dotenv

from zul.evaluation.config import RedisSettings
from zul.evaluation.dataset import describe_dataset, load_qa_dataset, load_results
from zul.evaluation.generation import ChatGenerator
from zul.evaluation.hits import retrieval_hit_stats
from zul.evaluation.indexing import redis_schema
from zul.evaluation.reports import compare_reports, save_report
from zul.evaluation.retrievers import RedisRetriever
from zul.evaluation.runner import length_summary, run_rag

DEFAULT_METRICS = "context_precision,context_recall,faithfulness,answer_relevancy"

app = typer.Typer(help="Evaluasi retrieval dan RAG dengan ragas.", no_args_is_help=True)


@app.callback()
def _load_env() -> None:
    # .env dicari ke atas dari folder kerja; akar repo zul_utilites punya satu.
    load_dotenv(override=False)


@app.command()
def dataset(paths: list[Path]) -> None:
    """Ringkas dataset: jumlah, panjang teks, ada tidaknya reference_contexts."""
    rows = load_qa_dataset(*paths)
    typer.echo(json.dumps(describe_dataset(rows), indent=2, ensure_ascii=False))


@app.command()
def rag(
    paths: list[Path],
    index: str = typer.Option(..., help="Nama index RedisVL yang sudah terisi."),
    prefix: str = typer.Option(..., help="Prefix kunci index itu."),
    dims: int = typer.Option(..., help="Dimensi vektor embedding."),
    mode: str = typer.Option("rrf", help="vector | text | hybrid | rrf"),
    top_k: int = typer.Option(5),
    out: Path = typer.Option(Path("outputs/rag.csv")),
    generate: bool = typer.Option(True, help="--no-generate untuk retrieval saja."),
    resume: bool = typer.Option(True),
) -> None:
    """Jalankan retrieval (dan jawaban) untuk seluruh dataset, simpan CSV."""
    from zul.utilities.embedding_service import AIService

    ai = AIService.from_env()
    db = RedisSettings.from_env().connect()
    db.create_index(redis_schema(index, prefix=prefix, dims=dims), overwrite=False)
    retriever = RedisRetriever(db, ai, mode=mode)  # type: ignore[arg-type]
    generator = ChatGenerator(ai) if generate else None
    rows = load_qa_dataset(*paths)
    results = run_rag(
        rows, retriever, generator, top_k=top_k, out_path=out, resume=resume
    )
    typer.echo(json.dumps(length_summary(results), indent=2))
    typer.echo(f"tersimpan: {out}")


@app.command()
def ragas(
    csv: Path,
    metrics: str = typer.Option(DEFAULT_METRICS, help="Dipisah koma."),
    name: str = typer.Option("", help="Label percobaan; bawaannya nama file CSV."),
    out_dir: Path = typer.Option(Path("outputs")),
    backend: str = typer.Option("instructor", help="instructor | langchain"),
    timeout: int = typer.Option(180),
    workers: int = typer.Option(8),
) -> None:
    """Nilai CSV hasil `rag` dengan ragas; tulis .scores.json dan .rows.csv."""
    from zul.evaluation.judge import evaluate_rag

    report = evaluate_rag(
        csv,
        metrics=[m.strip() for m in metrics.split(",") if m.strip()],
        name=name or csv.stem,
        judge_backend=backend,  # type: ignore[arg-type]
        timeout=timeout,
        max_workers=workers,
    )
    json_path, _ = save_report(report, out_dir)
    typer.echo(repr(report))
    typer.echo(f"tersimpan: {json_path}")


@app.command()
def hits(csv: Path, threshold: float = typer.Option(0.6)) -> None:
    """Hit rate dan MRR tanpa LLM, pemeriksaan cepat sebelum membayar penilai."""
    stats = retrieval_hit_stats(load_results(csv), threshold=threshold)
    typer.echo(json.dumps(stats, indent=2))


@app.command()
def compare(scores: list[Path]) -> None:
    """Tabel perbandingan beberapa .scores.json."""
    typer.echo(pd.DataFrame(compare_reports(*scores)).set_index("name").to_string())


if __name__ == "__main__":
    app()
