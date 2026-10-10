"""
Progress bar untuk modul evaluasi, yang tetap jalan tanpa tqdm.

Gunanya:
    Progress bar ditampilkan lewat `zul.adapters.tqdm` jika extra evaluation
    ter-install. Tanpa extra itu, item dikembalikan apa adanya, jadi modul
    evaluasi yang tidak butuh ragas tetap jalan dengan library standar.

Cara pakai:
    from zul.evaluation._progress import progress

    for row in progress(rows, "Embedding", enabled=True):
        ...
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def progress(items: Iterable[T], description: str, enabled: bool) -> Iterable[T]:
    """`items` dengan progress bar jika tqdm ada dan `enabled` True."""
    if not enabled:
        return items
    try:
        from zul.adapters import tqdm as tqdm_adapter
    except ModuleNotFoundError:
        return items
    return tqdm_adapter.progress(items, description=description)
