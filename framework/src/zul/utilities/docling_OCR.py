"""Dipindahkan ke `zul.utilities.OCR.docling_OCR`.

File ini dipertahankan supaya import lama tetap jalan:
    from zul.utilities.docling_OCR import DoclingVLMConverter
"""

from .OCR.docling_OCR import DoclingVLMConverter

__all__ = ["DoclingVLMConverter"]
