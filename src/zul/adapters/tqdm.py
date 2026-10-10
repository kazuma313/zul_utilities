"""
Adapter tqdm: progress bar untuk perulangan yang lama.

Gunanya:
    Satu-satunya file Zul yang mengimpor tqdm. Modul lain memanggil
    `progress`, sehingga progress bar bisa dimatikan atau diganti di satu
    tempat. Butuh extra evaluation: `pip install "zul[evaluation]"`.

Cara pakai:
    from zul.adapters import tqdm as tqdm_adapter

    for row in tqdm_adapter.progress(rows, description="Embedding"):
        ...
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import TypeVar

from tqdm import tqdm

T = TypeVar("T")


def progress(
    items: Iterable[T], description: str = "", enabled: bool = True
) -> Iterator[T]:
    """Iterasi `items` sambil menampilkan progress bar, kecuali `enabled` False."""
    return iter(tqdm(items, desc=description, disable=not enabled))
