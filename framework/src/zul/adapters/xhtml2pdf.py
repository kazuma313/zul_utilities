"""
Adapter xhtml2pdf: mencetak dokumen HTML menjadi PDF.

Gunanya:
    Satu-satunya file Zul yang mengimpor xhtml2pdf. Dokumen HTML lengkap,
    termasuk CSS di tag <style>, dicetak ke file atau ke bytes. Jika
    xhtml2pdf melaporkan error, adapter ini melempar PdfRenderError.
    Butuh extra converter: `pip install "zul[converter]"`.

Cara pakai:
    from zul.adapters import xhtml2pdf as xhtml2pdf_adapter

    pdf_bytes = xhtml2pdf_adapter.render_pdf("<html><body><h1>Judul</h1></body></html>")
    xhtml2pdf_adapter.write_pdf(html_document, "output/laporan.pdf")
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from xhtml2pdf import pisa


class PdfRenderError(RuntimeError):
    """xhtml2pdf melaporkan error saat mencetak HTML; `errors` adalah jumlahnya."""

    def __init__(self, errors: int) -> None:
        super().__init__(f"xhtml2pdf melaporkan {errors} error saat membuat PDF")
        self.errors = errors


def _create_pdf(html: str, destination: BinaryIO) -> None:
    status = pisa.CreatePDF(html, dest=destination)
    if status.err:
        raise PdfRenderError(int(status.err))


def render_pdf(html: str) -> bytes:
    """Isi file PDF hasil cetak dokumen HTML, dibuat di memori.

    Raises:
        PdfRenderError: xhtml2pdf melaporkan error.
    """
    buffer = BytesIO()
    _create_pdf(html, buffer)
    return buffer.getvalue()


def write_pdf(html: str, path: str | Path) -> None:
    """Cetak dokumen HTML ke file PDF; file yang sudah ada ditimpa.

    Raises:
        OSError: file tidak bisa ditulis.
        PdfRenderError: xhtml2pdf melaporkan error. File-nya tetap
            tertulis, tetapi isinya bisa tidak lengkap.
    """
    with open(path, "wb") as file:
        _create_pdf(html, file)
