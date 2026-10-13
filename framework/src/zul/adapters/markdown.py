"""
Adapter Python-Markdown: mengubah teks Markdown menjadi potongan HTML.

Gunanya:
    Satu-satunya file Zul yang mengimpor library markdown. Masukan dan
    hasilnya string biasa, jadi modul lain hanya memilih extension.
    Butuh extra converter: `pip install "zul[converter]"`.

Cara pakai:
    from zul.adapters import markdown as markdown_adapter

    html = markdown_adapter.to_html("| A | B |\\n|---|---|\\n| 1 | 2 |", ["tables"])
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import markdown


def to_html(text: str, extensions: Sequence[str | Any] = ()) -> str:
    """Potongan HTML dari teks Markdown, tanpa tag <html> dan <body>.

    `extensions` berisi nama extension Python-Markdown, misalnya "extra",
    "tables", atau "codehilite", atau objek extension-nya.

    Raises:
        ImportError: nama extension tidak dikenal.
    """
    return markdown.markdown(text, extensions=list(extensions))
