"""
Dataset tanya-jawab untuk evaluasi, serta hasil evaluasi yang disimpan ke file.

Gunanya:
    Dataset dari .xlsx, .csv, .json, atau .jsonl dengan nama kolom yang
    berbeda-beda diubah menjadi list dict dengan kolom yang dipakai ragas:

        user_input          pertanyaan
        reference           jawaban acuan
        reference_contexts  potongan dokumen acuan (list teks), atau None
        file_name           dokumen asal, atau None
        dataset             nama file sumber, supaya beberapa dataset yang
                            digabung masih bisa dipisah saat dianalisis

    Hasil retrieval disimpan ke CSV atau JSONL dan dibaca lagi utuh,
    termasuk kolom yang berisi list. Membaca .xlsx butuh extra evaluation;
    format lain hanya butuh library standar.

Cara pakai:
    from zul.evaluation.dataset import describe_dataset, load_qa_dataset

    rows = load_qa_dataset("qa.xlsx", "qa_tambahan.csv")
    print(describe_dataset(rows))

    save_results(results, "outputs/redis-rrf.csv")
    results = load_results("outputs/redis-rrf.csv")

    Untuk dianalisis dengan pandas: `pandas.DataFrame(rows)`.
"""

from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# Nama Kolom
# --------------------------------------------------------------------------
#
# Nama kolom asal dicocokkan tanpa membedakan huruf besar dan kecil.
# Pemetaan dari column_map menimpa pemetaan bawaan untuk nama yang
# sama, jadi dataset dengan nama kolom lain tetap bisa dibaca.
#

DEFAULT_COLUMNS: dict[str, str] = {
    "question": "user_input",
    "query": "user_input",
    "pertanyaan": "user_input",
    "answer": "reference",
    "ground_truth": "reference",
    "jawaban": "reference",
    "context": "reference_contexts",
    "contexts": "reference_contexts",
    "konteks": "reference_contexts",
    "law": "file_name",
    "source": "file_name",
    "sumber": "file_name",
}

REQUIRED_COLUMNS = ("user_input", "reference")
DATASET_COLUMNS = (
    "user_input",
    "reference",
    "reference_contexts",
    "file_name",
    "dataset",
)
LIST_COLUMNS = ("retrieved_contexts", "reference_contexts")
INTEGER_COLUMNS = ("top_k",)

# --------------------------------------------------------------------------
# Membaca Tabel
# --------------------------------------------------------------------------


def read_table(path: str | Path) -> list[dict[str, Any]]:
    """Baris file .xlsx, .csv, .json, atau .jsonl sebagai list dict.

    File .json berisi satu list objek, dan setiap baris .jsonl berisi satu
    objek. Membaca .xlsx butuh extra evaluation.

    Raises:
        ValueError: ekstensi file tidak didukung.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        from zul.adapters import openpyxl as excel

        return excel.read_rows(path)
    if suffix == ".csv":
        _allow_large_csv_fields()
        with path.open(encoding="utf-8-sig", newline="") as file:
            return list(csv.DictReader(file))
    if suffix == ".json":
        return list(json.loads(path.read_text(encoding="utf-8")))
    if suffix == ".jsonl":
        lines = path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]
    raise ValueError(
        f"Format {path.name} tidak didukung. Pakai .xlsx, .csv, .json, atau .jsonl."
    )


def _allow_large_csv_fields() -> None:
    # Konteks hasil retrieval bisa lebih panjang dari batas
    # bawaan modul csv, yaitu 131.072 karakter per sel.
    csv.field_size_limit(2**31 - 1)


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and value != value:
        return True
    return isinstance(value, str) and value.strip() in {"", "nan", "None"}


def as_text_list(value: Any) -> list[str] | None:
    """Teks, list, atau list berbentuk JSON menjadi list teks; sel kosong menjadi None.

    List yang ditulis dengan repr Python, seperti `['a', 'b']`, juga dibaca,
    karena CSV lama dari pandas menyimpannya dengan bentuk itu.
    """
    if _is_empty(value):
        return None
    if isinstance(value, list | tuple):
        texts = [str(item) for item in value if not _is_empty(item)]
        return texts or None
    text = str(value).strip()
    if text.startswith("["):
        for parse in (json.loads, ast.literal_eval):
            try:
                parsed = parse(text)
            except (ValueError, SyntaxError):
                continue
            if isinstance(parsed, list):
                return as_text_list(parsed)
    return [text]


# --------------------------------------------------------------------------
# Dataset Tanya-Jawab
# --------------------------------------------------------------------------


def load_qa_dataset(
    *paths: str | Path, column_map: dict[str, str] | None = None
) -> list[dict[str, Any]]:
    """Baca satu atau beberapa file tanya-jawab dan gabungkan menjadi satu dataset.

    Args:
        *paths: File .xlsx, .csv, .json, atau .jsonl.
        column_map: Pemetaan tambahan {nama kolom asal: nama baku}, misalnya
            `{"tanya": "user_input", "jawab": "reference"}`.

    Returns:
        List dict berkolom user_input, reference, reference_contexts,
        file_name, dan dataset. Baris tanpa pertanyaan dilewati.

    Raises:
        ValueError: tidak ada file, atau kolom user_input atau reference
            tidak ditemukan di salah satu file.
    """
    if not paths:
        raise ValueError("Sebutkan minimal satu file dataset.")
    mapping = {
        **DEFAULT_COLUMNS,
        **{k.lower(): v for k, v in (column_map or {}).items()},
    }
    dataset: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path)
        for row in _renamed_rows(path, mapping):
            question = "" if _is_empty(row["user_input"]) else str(row["user_input"])
            if not question.strip():
                continue
            reference = row.get("reference")
            dataset.append(
                {
                    "user_input": question.strip(),
                    "reference": "" if _is_empty(reference) else str(reference).strip(),
                    "reference_contexts": as_text_list(row.get("reference_contexts")),
                    "file_name": (
                        None
                        if _is_empty(row.get("file_name"))
                        else str(row["file_name"])
                    ),
                    "dataset": path.stem,
                }
            )
    return dataset


def _renamed_rows(path: Path, mapping: dict[str, str]) -> list[dict[str, Any]]:
    rows = read_table(path)
    renamed = [
        {mapping.get(str(key).strip().lower(), str(key).strip()): value
         for key, value in row.items()}
        for row in rows
    ]  # fmt: skip
    columns = set().union(*renamed) if renamed else set()
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise ValueError(
            f"{path.name}: kolom {missing} tidak ditemukan. Kolom yang ada: "
            f"{sorted(columns)}. Beri column_map, misalnya "
            "{'nama_kolom_kamu': 'user_input'}."
        )
    return renamed


def describe_dataset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Ringkasan dataset untuk dicetak sebelum evaluasi dijalankan."""
    per_dataset: dict[str, int] = {}
    for row in rows:
        name = str(row.get("dataset") or "-")
        per_dataset[name] = per_dataset.get(name, 0) + 1
    return {
        "jumlah": len(rows),
        "per_dataset": per_dataset,
        "punya_reference_contexts": sum(
            1 for row in rows if row.get("reference_contexts")
        ),
        "rata_panjang_pertanyaan": _mean_length(rows, "user_input"),
        "rata_panjang_reference": _mean_length(rows, "reference"),
    }


def _mean_length(rows: list[dict[str, Any]], column: str) -> float:
    if not rows:
        return 0.0
    return round(sum(len(str(row.get(column) or "")) for row in rows) / len(rows), 1)


# --------------------------------------------------------------------------
# Menyimpan Dan Membaca Hasil
# --------------------------------------------------------------------------
#
# Di file CSV, kolom berisi list ditulis sebagai JSON supaya bisa dibaca
# kembali utuh. Kolom indeks tanpa nama dari CSV lama pandas dibuang
# saat dibaca, dan sel kosong di kolom list dibaca sebagai None.
#


def save_results(rows: list[dict[str, Any]], path: str | Path) -> Path:
    """Simpan baris hasil ke .csv atau .jsonl; folder tujuan dibuat jika belum ada.

    Raises:
        ValueError: ekstensi file bukan .csv atau .jsonl.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in {".csv", ".jsonl"}:
        raise ValueError(f"Simpan hasil sebagai .csv atau .jsonl, bukan {path.name}.")
    path.parent.mkdir(parents=True, exist_ok=True)
    if suffix == ".jsonl":
        lines = [json.dumps(row, ensure_ascii=False, default=str) for row in rows]
        path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
        return path
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _cell(row.get(key)) for key in columns})
    return path


def _cell(value: Any) -> Any:
    if isinstance(value, list | tuple | dict):
        return json.dumps(value, ensure_ascii=False)
    return "" if value is None else value


def load_results(path: str | Path) -> list[dict[str, Any]]:
    """Baca hasil dari `save_results`, atau CSV lama yang ditulis pandas."""
    rows = read_table(path)
    loaded = []
    for row in rows:
        clean = {
            key: value for key, value in row.items() if key not in {"", "Unnamed: 0"}
        }
        for column in LIST_COLUMNS:
            if column in clean:
                clean[column] = as_text_list(clean[column])
        for column in INTEGER_COLUMNS:
            if isinstance(clean.get(column), str) and clean[column].isdigit():
                clean[column] = int(clean[column])
        clean["response"] = (
            "" if _is_empty(clean.get("response")) else clean["response"]
        )
        loaded.append(clean)
    return loaded
