"""
Menggabungkan beberapa daftar peringkat menjadi satu peringkat.

Gunanya:
    Dua cara pencarian, misalnya pencarian vektor dan full-text search,
    mengembalikan urutan hasil yang berbeda. Reciprocal Rank Fusion (RRF)
    memberi setiap hasil skor 1 / (peringkat + K) di setiap daftar, lalu
    menjumlahkannya. Hasil yang muncul tinggi di beberapa daftar naik ke
    atas, tanpa perlu menyamakan skala skor masing-masing pencarian. Hanya
    butuh library standar.

Cara pakai:
    from zul.utilities.ranking import reciprocal_rank_fusion

    scored, ranked = reciprocal_rank_fusion(["a", "b", "c"], ["b", "d"], K=60)
    print(ranked)        # ['b', 'a', 'd', 'c']
"""

from collections import defaultdict
from typing import Any


def reciprocal_rank_fusion(
    *ranked_lists: list[Any], K: int = 100
) -> tuple[list[tuple[Any, float]], list[Any]]:
    """
    Gabungkan beberapa daftar peringkat dengan Reciprocal Rank Fusion.

    Args:
        *ranked_lists: Daftar hasil, masing-masing terurut dari yang terbaik.
        K: Konstanta di rumus RRF. Makin besar, makin kecil beda skor antara
            peringkat atas dan bawah.

    Returns:
        Pasangan (hasil, skor) terurut dari skor tertinggi, dan daftar hasilnya
        saja dengan urutan yang sama.
    """
    rrf_scores: dict[Any, float] = defaultdict(float)
    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            rrf_scores[item] += 1 / (rank + K)

    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_items, [item for item, _score in sorted_items]
