"""
Retrieval dan jawaban untuk seluruh dataset, disimpan sambil berjalan.

Gunanya:
    `run_rag` mengambil konteks, dan jika ada generator membuat jawaban,
    untuk setiap pertanyaan. Hasilnya berkolom user_input,
    retrieved_contexts, response, dan reference, persis yang dibutuhkan
    ragas, ditambah retriever, generator, top_k, dataset, dan file_name
    supaya beberapa percobaan bisa digabung dalam satu tabel. Jika
    `out_path` diisi, hasil ditulis setiap kali satu pertanyaan selesai.
    Proses yang terputus dilanjutkan dari pertanyaan yang belum ada di file
    itu. Hanya butuh library standar.

Cara pakai:
    from zul.evaluation.runner import length_summary, run_rag

    results = run_rag(rows, retriever, generator, top_k=5,
                      out_path="outputs/redis-rrf.csv")
    print(length_summary(results))

    contexts_only = run_rag(rows, retriever)      # tanpa jawaban
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._progress import progress
from .dataset import load_results, save_results
from .generation import Generator
from .retrievers import Retriever


def run_rag(
    rows: list[dict[str, Any]],
    retriever: Retriever,
    generator: Generator | None = None,
    *,
    top_k: int = 5,
    out_path: str | Path | None = None,
    resume: bool = True,
    show_progress: bool = True,
) -> list[dict[str, Any]]:
    """
    Ambil konteks, dan buat jawaban, untuk setiap pertanyaan di dataset.

    Args:
        rows: Dataset dari `load_qa_dataset`, berkolom user_input dan
            reference.
        retriever: Objek dengan method `retrieve(query, top_k)`.
        generator: Objek dengan method `answer(question, contexts)`; None
            untuk retrieval saja, sehingga `response` kosong.
        top_k: Jumlah konteks per pertanyaan.
        out_path: File .csv atau .jsonl tempat hasil ditulis setiap kali satu
            pertanyaan selesai.
        resume: Lewati pertanyaan yang sudah ada di `out_path`.
        show_progress: Tampilkan progress bar jika extra evaluation ada.

    Returns:
        Satu dict hasil per pertanyaan, dengan urutan yang sama dengan `rows`.
    """
    done: dict[tuple[str, str], dict[str, Any]] = {}
    if out_path and resume and Path(out_path).exists():
        done = {_key(row): row for row in load_results(out_path)}

    results: list[dict[str, Any]] = []
    for item in progress(rows, f"RAG {retriever.name}", show_progress):
        if _key(item) in done:
            results.append(done[_key(item)])
            continue
        question = str(item["user_input"])
        contexts = retriever.retrieve(question, top_k=top_k)
        results.append(
            {
                "user_input": question,
                "retrieved_contexts": contexts,
                "response": generator.answer(question, contexts) if generator else "",
                "reference": str(item.get("reference") or ""),
                "reference_contexts": item.get("reference_contexts"),
                "file_name": item.get("file_name"),
                "dataset": item.get("dataset"),
                "retriever": retriever.name,
                "generator": generator.name if generator else "",
                "top_k": top_k,
            }
        )
        if out_path:
            save_results(results, out_path)
    if out_path:
        save_results(results, out_path)
    return results


def _key(row: dict[str, Any]) -> tuple[str, str]:
    # Pertanyaan yang sama di dua dataset berbeda tetap dihitung dua.
    return str(row.get("user_input", "")).strip(), str(row.get("dataset") or "")


def length_summary(results: list[dict[str, Any]]) -> dict[str, float]:
    """Rata-rata panjang setiap kolom dan jumlah pertanyaan tanpa konteks.

    Dipakai untuk memeriksa cepat bahwa retriever benar-benar mengembalikan
    konteks sebelum hasilnya dinilai.
    """
    if not results:
        return {"jumlah": 0, "konteks_kosong": 0}
    contexts = [
        sum(len(text) for text in row.get("retrieved_contexts") or [])
        for row in results
    ]

    def mean(values: list[int]) -> float:
        return round(sum(values) / len(values), 1)

    return {
        "jumlah": len(results),
        "user_input": mean([len(str(row.get("user_input") or "")) for row in results]),
        "retrieved_contexts": mean(contexts),
        "response": mean([len(str(row.get("response") or "")) for row in results]),
        "reference": mean([len(str(row.get("reference") or "")) for row in results]),
        "konteks_kosong": sum(1 for length in contexts if length == 0),
    }
