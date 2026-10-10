"""
Dokumen PDF menjadi potongan (chunk) yang siap di-embed dan dimasukkan ke index.

Gunanya:
    Dua cara memotong yang sering dibandingkan dalam evaluasi retrieval:
    satu potongan per halaman, atau teks seluruh PDF dipotong rekursif
    dengan ukuran dan tumpang tindih tertentu. Hasilnya berupa `Chunk`,
    lalu `chunks_to_records` mengubahnya menjadi dict datar untuk index.
    PDF dibaca lewat `zul.adapters.pypdf` dan dipotong lewat
    `zul.adapters.langchain_text_splitters`. Butuh extra pdf:
    `pip install "zul[pdf]"`.

Cara pakai:
    from zul.evaluation.documents import chunk_folder, chunks_to_records

    chunks = chunk_folder("data/pdf", strategy="recursive", chunk_size=4000)
    records = chunks_to_records(chunks)
    # [{"content": "...", "source": "a.pdf", "chunk_index": 0, ...}, ...]
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from zul.adapters import langchain_text_splitters as splitter_adapter
from zul.adapters import pypdf as pypdf_adapter

Strategy = Literal["per_page", "recursive"]


@dataclass(frozen=True)
class Chunk:
    """Satu potongan teks beserta asalnya. `page` hanya terisi untuk per_page."""

    content: str
    source: str
    chunk_index: int
    page: int | None = None
    strategy: str = ""


def find_pdfs(folder: str | Path) -> list[Path]:
    """Semua file .pdf di dalam folder dan subfoldernya, terurut.

    Raises:
        FileNotFoundError: folder tidak ada.
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Folder tidak ada: {folder}")
    return sorted(path for path in folder.rglob("*") if path.suffix.lower() == ".pdf")


def read_pdf_pages(path: str | Path) -> list[str]:
    """Teks setiap halaman PDF. Halaman yang gagal dibaca menjadi teks kosong."""
    return pypdf_adapter.read_pages(path)


def chunk_per_page(path: str | Path) -> list[Chunk]:
    """Satu potongan per halaman PDF; halaman kosong dilewati."""
    source = Path(path).name
    return [
        Chunk(
            content=text, source=source, chunk_index=i, page=i + 1, strategy="per_page"
        )
        for i, text in enumerate(read_pdf_pages(path))
        if text.strip()
    ]


def chunk_recursive(
    path: str | Path,
    chunk_size: int = 4000,
    overlap: int = 450,
    separators: list[str] | None = None,
) -> list[Chunk]:
    """Teks seluruh PDF digabung, lalu dipotong per paragraf, baris, dan spasi."""
    text = "\n".join(read_pdf_pages(path)).strip()
    if not text:
        return []
    split = splitter_adapter.recursive_character_splitter(
        chunk_size=chunk_size, overlap=overlap, separators=separators
    )
    source = Path(path).name
    return [
        Chunk(content=piece, source=source, chunk_index=i, strategy="recursive")
        for i, piece in enumerate(split(text))
        if piece.strip()
    ]


def chunk_folder(
    folder: str | Path, strategy: Strategy = "recursive", **options: Any
) -> list[Chunk]:
    """Potong semua PDF di folder dengan satu cara.

    `options` diteruskan ke `chunk_recursive`, misalnya `chunk_size` dan
    `overlap`.

    Raises:
        ValueError: `strategy` bukan "per_page" atau "recursive".
    """
    if strategy not in ("per_page", "recursive"):
        raise ValueError(
            f"Strategi {strategy!r} tidak dikenal: per_page atau recursive."
        )
    chunks: list[Chunk] = []
    for pdf in find_pdfs(folder):
        if strategy == "per_page":
            chunks.extend(chunk_per_page(pdf))
        else:
            chunks.extend(chunk_recursive(pdf, **options))
    return chunks


def chunks_to_records(
    chunks: Iterable[Chunk], text_field: str = "content"
) -> list[dict[str, Any]]:
    """Dict datar untuk setiap potongan; teksnya disimpan di kolom `text_field`."""
    records = []
    for chunk in chunks:
        row = asdict(chunk)
        row[text_field] = row.pop("content")
        records.append(row)
    return records


def length_stats(chunks: Iterable[Chunk]) -> dict[str, float]:
    """Jumlah potongan serta panjang terpendek, terpanjang, dan rata-ratanya."""
    lengths = [len(chunk.content) for chunk in chunks]
    if not lengths:
        return {"jumlah": 0, "min": 0, "max": 0, "rata": 0.0}
    return {
        "jumlah": len(lengths),
        "min": min(lengths),
        "max": max(lengths),
        "rata": round(sum(lengths) / len(lengths), 1),
    }
