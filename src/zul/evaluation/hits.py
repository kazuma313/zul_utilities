"""
Hit rate dan MRR hasil retrieval, tanpa model penilai.

Gunanya:
    Pemeriksaan cepat dan gratis sebelum membayar model penilai ragas. Sebuah
    konteks dianggap tepat jika mirip dengan acuannya. Acuan yang dipakai
    adalah `reference_contexts` jika ada di dataset; jika tidak, jawaban
    acuan (`reference`) yang termuat di konteks. Cara kedua kasar, tetapi
    cukup untuk melihat tren antar percobaan. Hanya butuh library standar.

Cara pakai:
    from zul.evaluation.hits import retrieval_hit_stats

    print(retrieval_hit_stats(results))
    # {"n": 120, "hit_rate": 0.62, "mrr": 0.48, "threshold": 0.6, ...}
"""

from __future__ import annotations

import difflib
import re
from typing import Any

_SPACES = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _SPACES.sub(" ", str(text).lower()).strip()


def similarity(a: str, b: str) -> float:
    """Kemiripan dua teks, 0 sampai 1; 1 jika salah satunya memuat yang lain.

    Huruf besar dan kecil serta jumlah spasi tidak dibedakan.
    """
    a, b = _normalize(a), _normalize(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def first_hit_rank(
    contexts: list[str], targets: list[str], threshold: float = 0.6
) -> int | None:
    """Peringkat pertama (mulai dari 1) konteks yang cocok dengan salah satu acuan."""
    for rank, context in enumerate(contexts, 1):
        if any(similarity(target, context) >= threshold for target in targets):
            return rank
    return None


def retrieval_hit_stats(
    results: list[dict[str, Any]], *, threshold: float = 0.6
) -> dict[str, Any]:
    """
    Hit rate dan Mean Reciprocal Rank seluruh hasil.

    Baris tanpa konteks atau tanpa acuan tidak dihitung. Kolom `sumber`
    menyebut acuan yang dipakai: "reference_contexts" atau "reference".

    Args:
        results: Hasil `run_rag`.
        threshold: Kemiripan minimum agar sebuah konteks dianggap tepat.
    """
    uses_contexts = any(row.get("reference_contexts") for row in results)
    hits, reciprocal_ranks, counted = 0, 0.0, 0
    for row in results:
        contexts = row.get("retrieved_contexts") or []
        targets = row.get("reference_contexts") or [row.get("reference") or ""]
        if not contexts or not any(str(target).strip() for target in targets):
            continue
        counted += 1
        rank = first_hit_rank(contexts, targets, threshold)
        if rank:
            hits += 1
            reciprocal_ranks += 1 / rank
    return {
        "n": counted,
        "hit_rate": round(hits / counted, 4) if counted else 0.0,
        "mrr": round(reciprocal_ranks / counted, 4) if counted else 0.0,
        "threshold": threshold,
        "sumber": "reference_contexts" if uses_contexts else "reference",
    }
