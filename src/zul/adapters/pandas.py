"""
Adapter pandas: membaca dan menulis file CSV sebagai kolom berisi list.

Gunanya:
    Satu-satunya file Zul yang mengimpor pandas. Isi CSV keluar sebagai
    dict nama kolom ke list nilai, dan dict seperti itu bisa ditulis lagi
    menjadi CSV, jadi modul lain tidak perlu memegang DataFrame.
    Butuh extra analysis: `pip install "zul[analysis]"`.

Cara pakai:
    from zul.adapters import pandas as pandas_adapter

    columns = pandas_adapter.read_csv_columns("hasil.csv", ["query", "milvus_ms"])
    pandas_adapter.write_csv("data/latency.csv", {"short": [0.11, 0.12]})

Error dari pandas diteruskan apa adanya. File CSV kosong, misalnya, tetap
memunculkan pandas.errors.EmptyDataError, turunan dari ValueError.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import IO, Any

import pandas as pd

# --------------------------------------------------------------------------
# File CSV
# --------------------------------------------------------------------------


def read_csv_columns(
    source: str | Path | IO[str], names: Iterable[str]
) -> dict[str, list[Any]]:
    """Kolom `names` dari file CSV, masing-masing sebagai list nilai Python.

    Nama yang tidak ada di file dilewati tanpa error. `source` boleh path,
    URL, atau objek file, sama seperti yang diterima pandas.read_csv.
    """
    frame = pd.read_csv(source)
    return {name: frame[name].tolist() for name in names if name in frame.columns}


def write_csv(path: str | Path, columns: Mapping[str, Any]) -> None:
    """Simpan dict nama kolom ke list nilai sebagai CSV, tanpa kolom index.

    Raises:
        ValueError: panjang list antar kolom tidak sama.
    """
    pd.DataFrame(columns).to_csv(path, index=False)
