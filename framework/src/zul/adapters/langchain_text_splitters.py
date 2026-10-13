"""
Adapter langchain-text-splitters: memotong teks panjang menjadi chunk.

Gunanya:
    Satu-satunya file Zul yang mengimpor langchain_text_splitters dan
    langchain_core. Pemotong teks dikembalikan sebagai fungsi Python biasa
    yang menerima string dan mengembalikan list string, jadi modul lain
    tidak perlu tahu kelas RecursiveCharacterTextSplitter.
    Butuh extra pdf: `pip install "zul[pdf]"`.

Cara pakai:
    from zul.adapters import langchain_text_splitters as text_splitters

    split = text_splitters.recursive_character_splitter(chunk_size=1000, overlap=200)
    chunks = split(text)                                    # list string
    documents = text_splitters.to_documents(chunks)         # list Document LangChain

Document LangChain dibuat di sini karena pipeline RAG Zul mengembalikan
Document kepada pemakainya. Isinya hanya teks, tanpa metadata.
"""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def recursive_character_splitter(
    chunk_size: int = 4000,
    overlap: int = 200,
    separators: list[str] | None = None,
    length_function: Callable[[str], int] | None = len,
    is_separator_regex: bool = False,
) -> Callable[[str], list[str]]:
    """Fungsi pemotong teks: chunk sepanjang `chunk_size`, tumpang tindih `overlap`.

    Pemisah dicoba berurutan, dari paragraf, baris, spasi, lalu karakter,
    kecuali `separators` diisi.

    Raises:
        ValueError: `chunk_size` kurang dari 1, `overlap` negatif, atau
            `overlap` lebih besar dari `chunk_size`. Diperiksa saat fungsi
            pemotongnya dibuat, bukan saat dipanggil.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=length_function,
        is_separator_regex=is_separator_regex,
        separators=separators,
    )
    return splitter.split_text


def to_documents(texts: list[str]) -> list[Document]:
    """Satu Document LangChain untuk setiap teks, dengan metadata kosong."""
    return [Document(page_content=text) for text in texts]
