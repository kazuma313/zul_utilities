"""
Simpan hasil eksperimen ke folder `data/`.

Cara pakai:
    from zul.utilities.script_helper.save_file import (
        save_latency_to_csv,
        save_text_to_md,
    )

    save_text_to_md(markdown, "hasil_ocr")               # data/hasil_ocr.md

    save_latency_to_csv(
        {"short": [0.11, 0.12], "long": [0.31, 0.29]},
        file_name="latency_milvus",
    )                                                    # data/latency_milvus.csv

Folder `data/` dibuat otomatis di direktori kerja saat ini. File CSV
ditulis lewat zul.adapters.pandas, jadi butuh extra analysis.
"""

import os

from zul.adapters import pandas as pandas_adapter

# --------------------------------------------------------------------------
# Menyimpan ke Folder data
# --------------------------------------------------------------------------


def save_text_to_md(text_result: str, filename: str):
    """
    Save the given text to a markdown file with the specified filename.

    :param text_result: The text content to save.
    :param filename: The name of the file (without extension) to save the content to.
    """
    # Ensure the 'data' directory exists
    os.makedirs("data", exist_ok=True)

    # Create the full file path
    file_path = os.path.join("data", rf"{filename}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text_result)


def save_latency_to_csv(
    mapping: dict, file_name: str = "query_latency_recursive_results"
):
    """
    Save latency data to a CSV file inside the 'data' directory.

    :param mapping: Dict of column name -> list of latencies, e.g.
        {"short": [...], "medium": [...], "long": [...], "extra_long": [...]}.
    :param file_name: The name of the file (without extension).
    """
    # Ensure the 'data' directory exists
    os.makedirs("data", exist_ok=True)

    file_path = os.path.join("data", f"{file_name}.csv")
    pandas_adapter.write_csv(file_path, mapping)
