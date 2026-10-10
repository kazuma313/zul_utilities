"""
Laporan skor evaluasi: disimpan ke file dan dibandingkan antar percobaan.

Gunanya:
    `EvalReport` berisi ringkasan skor (rata-rata setiap metrik), skor per
    baris, dan keterangan percobaan. `save_report` menulis
    `<nama>.scores.json` untuk ringkasan dan `<nama>.rows.csv` untuk skor
    per baris. `compare_reports` menyusun beberapa ringkasan menjadi satu
    tabel, satu baris per percobaan. Hanya butuh library standar.

Cara pakai:
    from zul.evaluation.reports import compare_reports, save_report

    save_report(report, "outputs")             # outputs/redis-rrf.scores.json
    table = compare_reports("outputs/redis-rrf.scores.json",
                            "outputs/milvus-hybrid.scores.json")
    # [{"name": "redis-rrf", "context_recall": 0.41, "n": 120}, ...]
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .dataset import save_results


@dataclass
class EvalReport:
    """Hasil satu evaluasi: ringkasan, skor per baris, dan keterangannya."""

    name: str
    metrics: list[str]
    summary: dict[str, float | None]
    rows: list[dict[str, Any]]
    meta: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        scores = ", ".join(
            f"{name}={'-' if value is None else f'{value:.4f}'}"
            for name, value in self.summary.items()
        )
        return f"EvalReport({self.name}: {scores}; n={len(self.rows)})"


def summarize_scores(
    rows: list[dict[str, Any]], metrics: list[str]
) -> dict[str, float | None]:
    """Rata-rata setiap metrik; skor None dilewati, dan None jika semuanya None."""
    summary: dict[str, float | None] = {}
    for metric in metrics:
        values = [row[metric] for row in rows if row.get(metric) is not None]
        summary[metric] = round(sum(values) / len(values), 4) if values else None
    return summary


def save_report(
    report: EvalReport, out_dir: str | Path, name: str | None = None
) -> tuple[Path, Path]:
    """Tulis `<nama>.scores.json` dan `<nama>.rows.csv`; path keduanya."""
    folder = Path(out_dir)
    folder.mkdir(parents=True, exist_ok=True)
    label = name or report.name
    json_path = folder / f"{label}.scores.json"
    content = {
        "name": label,
        "summary": report.summary,
        "metrics": report.metrics,
        "meta": report.meta,
    }
    json_path.write_text(
        json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    csv_path = save_results(report.rows, folder / f"{label}.rows.csv")
    return json_path, csv_path


def load_report(path: str | Path) -> dict[str, Any]:
    """Isi file `.scores.json`: name, summary, metrics, dan meta."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compare_reports(*paths: str | Path) -> list[dict[str, Any]]:
    """Satu baris per percobaan: nama, skor setiap metrik, dan jumlah baris `n`.

    Untuk ditampilkan sebagai tabel:
    `pandas.DataFrame(compare_reports(...)).set_index("name")`.
    """
    table = []
    for path in paths:
        report = load_report(path)
        meta = report.get("meta") or {}
        # Laporan lama dari research/ menyimpan
        # jumlah baris sebagai jumlah_baris.
        count = meta.get("n", meta.get("jumlah_baris"))
        table.append({"name": report["name"], **report["summary"], "n": count})
    return table
