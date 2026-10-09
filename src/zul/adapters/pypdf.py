"""
Adapter pypdf: membaca teks setiap halaman file PDF.

Gunanya:
    Satu-satunya file Zul yang mengimpor pypdf. Jika pypdf belum ter-install,
    adapter ini memakai PyPDF2, nama lama pypdf yang API-nya sama. Hasilnya
    berupa list string biasa, satu string untuk satu halaman.
    Butuh extra pdf: `pip install "zul[pdf]"`.

Cara pakai:
    from zul.adapters import pypdf as pypdf_adapter

    pages = pypdf_adapter.read_pages("dokumen.pdf")
    pages = pypdf_adapter.read_pages(
        "dokumen.pdf", on_page_error=lambda number, message: print(number, message)
    )

Halaman yang teksnya gagal diekstrak menjadi string kosong, sehingga satu
halaman yang rusak tidak membatalkan pembacaan halaman lainnya.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:  # PyPDF2 adalah nama lama pypdf
    from PyPDF2 import PdfReader

PageErrorHandler = Callable[[int, str], None]


class PdfError(ValueError):
    """File yang bukan PDF yang valid, atau daftar halamannya tidak bisa dibaca.

    Pesan error-nya sama dengan pesan dari pypdf.
    """


def read_pages(
    path: str | Path,
    strict: bool = False,
    on_page_error: PageErrorHandler | None = None,
) -> list[str]:
    """Teks setiap halaman PDF, dengan spasi di awal dan akhir dibuang.

    Args:
        path: Path ke file PDF.
        strict: Mode strict pypdf; jika True, kesalahan kecil di file
            menjadi error.
        on_page_error: Dipanggil dengan nomor halaman (mulai dari 1) dan
            pesan error-nya setiap kali teks satu halaman gagal diekstrak.

    Raises:
        OSError: file tidak bisa dibuka, misalnya karena tidak ada.
        PdfError: isi file bukan PDF yang valid.
    """
    with open(path, "rb") as file:
        try:
            pages = list(PdfReader(file, strict=strict).pages)
        except Exception as error:
            raise PdfError(str(error)) from error

        texts = []
        for number, page in enumerate(pages, start=1):
            try:
                text = page.extract_text()
            except Exception as error:
                if on_page_error is not None:
                    on_page_error(number, str(error))
                text = ""
            texts.append(text.strip() if text else "")
        return texts
