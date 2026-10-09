"""
Menulis catatan hasil ke CSV, satu baris per kejadian.

Gunanya:
    Catatan dari zul.computer_vision.analytics, misalnya Attention atau
    Visit, ditulis ke CSV saat kejadiannya selesai. File di-flush setiap
    baris, jadi run yang terputus tetap meninggalkan data yang bisa dipakai.

Cara pakai:
    from zul.computer_vision.analytics import Attention
    from zul.computer_vision.report import RecordWriter

    columns = ["attention_id", "track_id", "zone_name", "start_time_s",
               "end_time_s", "looking_s", "span_s"]
    with RecordWriter("outputs/interior_attention.csv", columns) as writer:
        writer.write(tracker.update(...))     # boleh list kosong

Kolom boleh berupa field dataclass maupun property, misalnya `span_s`.
Angka desimal dibulatkan ke 3 angka di belakang koma.
"""

from __future__ import annotations

import csv
import dataclasses
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# Penulis CSV
# --------------------------------------------------------------------------
#
# Header ditulis saat file dibuka, bahkan jika tidak ada satu baris pun
# yang masuk. CSV kosong dengan header ialah jawaban yang benar untuk
# video tanpa kejadian, dan berbeda dari file yang gagal ditulis.
#


class RecordWriter:
    """CSV untuk satu jenis catatan, ditulis dan di-flush per baris."""

    def __init__(self, path: str | Path, columns: Sequence[str] | type) -> None:
        self.path = Path(path)
        if isinstance(columns, type) and dataclasses.is_dataclass(columns):
            columns = [item.name for item in dataclasses.fields(columns)]
        self.columns = list(columns)
        self.rows = 0
        self._file = None
        self._writer = None

    def __enter__(self) -> RecordWriter:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(self.columns)
        self._file.flush()
        return self

    def __exit__(self, *exc_info) -> bool:
        if self._file is not None:
            self._file.close()
        return False

    def write(self, records: Iterable[Any]) -> None:
        """Tulis setiap catatan sebagai satu baris; nilai None menjadi sel kosong."""
        if self._writer is None:
            raise RuntimeError("RecordWriter harus dipakai dengan `with`")
        wrote = False
        for record in records:
            self._writer.writerow(
                [_cell(getattr(record, name, None)) for name in self.columns]
            )
            self.rows += 1
            wrote = True
        if wrote:
            self._file.flush()


def _cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        return round(value, 3)
    return value
