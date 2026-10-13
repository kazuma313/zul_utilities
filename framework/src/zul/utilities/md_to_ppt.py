"""Dipindahkan ke `zul.utilities.markdown_converter.md_to_ppt`.

File ini dipertahankan supaya import lama tetap jalan:
    from zul.utilities.md_to_ppt import DynamicMarkdownToPPTXService
"""

from .markdown_converter.md_to_ppt import DynamicMarkdownToPPTXService

__all__ = ["DynamicMarkdownToPPTXService"]
