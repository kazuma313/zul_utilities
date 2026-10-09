"""
Adapter python-pptx: presentasi baru, satuan ukuran, warna, bullet, dan simpan.

Gunanya:
    Satu-satunya file Zul yang mengimpor python-pptx. Di sini ada pembuat
    presentasi, konversi inci dan poin, warna, perataan paragraf, bullet,
    dan penyimpanan ke file atau bytes. Bagian yang menyentuh XML slide
    secara langsung juga ada di sini, jadi modul lain tidak perlu tahu
    namespace DrawingML atau lxml.
    Butuh extra converter: `pip install "zul[converter]"`.

Cara pakai:
    from zul.adapters import pptx as pptx_adapter

    prs = pptx_adapter.new_presentation(width_inches=10, height_inches=5.625)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    textbox = slide.shapes.add_textbox(
        pptx_adapter.inches(1), pptx_adapter.inches(1),
        pptx_adapter.inches(8), pptx_adapter.inches(1),
    )
    paragraph = textbox.text_frame.paragraphs[0]
    paragraph.font.color.rgb = pptx_adapter.color((0, 51, 102))
    pptx_adapter.show_bullet(paragraph)
    data = pptx_adapter.to_bytes(prs)

Presentasi, slide, dan paragraf yang dikembalikan adalah objek python-pptx
asli. Modul konversi Markdown mengisi objek itu langsung, karena setiap
langkahnya bekerja dengan slide dan paragraf, bukan dengan data biasa.
"""

from __future__ import annotations

from collections.abc import Sequence
from io import BytesIO
from pathlib import Path
from typing import IO, Any
from xml.sax.saxutils import quoteattr

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml import parse_xml
from pptx.util import Inches, Pt

DRAWINGML_NAMESPACE = "http://schemas.openxmlformats.org/drawingml/2006/main"

ALIGNMENTS = {
    "left": PP_ALIGN.LEFT,
    "center": PP_ALIGN.CENTER,
    "right": PP_ALIGN.RIGHT,
    "justify": PP_ALIGN.JUSTIFY,
}

Color = RGBColor | str | Sequence[int]

# --------------------------------------------------------------------------
# Presentasi
# --------------------------------------------------------------------------


def open_presentation(path: str | Path) -> Any:
    """Presentasi dari file .pptx, misalnya template perusahaan."""
    return Presentation(path)


def new_presentation(
    width_inches: float | None = None, height_inches: float | None = None
) -> Any:
    """Presentasi kosong dengan template bawaan; ukuran slide bisa diubah."""
    prs = Presentation()
    if width_inches is not None:
        prs.slide_width = Inches(width_inches)
    if height_inches is not None:
        prs.slide_height = Inches(height_inches)
    return prs


def save(prs: Any, target: str | Path | IO[bytes]) -> None:
    """Simpan presentasi ke path file atau ke objek file biner."""
    prs.save(target)


def to_bytes(prs: Any) -> bytes:
    """Isi file .pptx dari presentasi, dibuat di memori."""
    buffer = BytesIO()
    prs.save(buffer)
    return buffer.getvalue()


# --------------------------------------------------------------------------
# Ukuran Dan Warna
# --------------------------------------------------------------------------
#
# Ukuran di python-pptx dihitung dalam EMU, satuan bilangan bulat yang
# sangat kecil. Fungsi di bawah mengubah inci dan poin menjadi EMU,
# dan hasilnya bisa dipakai di mana pun python-pptx butuh ukuran.
#


def inches(value: float) -> int:
    """Panjang `value` inci dalam EMU."""
    return Inches(value)


def inches_box(
    left: float, top: float, width: float, height: float
) -> tuple[int, int, int, int]:
    """Posisi dan ukuran dalam inci sebagai empat panjang EMU, urutannya sama."""
    return Inches(left), Inches(top), Inches(width), Inches(height)


def points(value: float) -> int:
    """Ukuran `value` poin dalam EMU, misalnya untuk ukuran font."""
    return Pt(value)


def color(value: Color) -> RGBColor:
    """Warna python-pptx dari "#RRGGBB", tuple (r, g, b), atau RGBColor.

    Raises:
        ValueError: nilai bukan warna yang valid; setiap kanal 0 sampai 255.
    """
    if isinstance(value, RGBColor):
        return value
    if isinstance(value, str):
        return RGBColor.from_string(value.lstrip("#"))
    try:
        red, green, blue = value
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"warna harus '#RRGGBB', tuple (r, g, b), atau RGBColor: {value!r}"
        ) from error
    return RGBColor(red, green, blue)


# --------------------------------------------------------------------------
# Paragraf Dan Slide
# --------------------------------------------------------------------------


def align(paragraph: Any, alignment: str) -> None:
    """Ratakan paragraf: "left", "center", "right", atau "justify"."""
    if alignment not in ALIGNMENTS:
        names = ", ".join(ALIGNMENTS)
        raise ValueError(f"perataan '{alignment}' tidak dikenal; pilih: {names}")
    paragraph.alignment = ALIGNMENTS[alignment]


def show_bullet(paragraph: Any, char: str = "•") -> None:
    """Tampilkan bullet `char` di depan paragraf, walau layout-nya tanpa bullet.

    Penanda tanpa bullet (buNone) dari layout dibuang lebih dulu. Bullet
    yang sudah ada dibiarkan, jadi fungsi ini aman dipanggil dua kali.
    """
    properties = paragraph._element.get_or_add_pPr()

    for no_bullet in properties.findall(f".//{{{DRAWINGML_NAMESPACE}}}buNone"):
        properties.remove(no_bullet)

    if properties.find(f".//{{{DRAWINGML_NAMESPACE}}}buChar") is None:
        bullet = parse_xml(
            f'<a:buChar xmlns:a="{DRAWINGML_NAMESPACE}" char={quoteattr(char)}/>'
        )
        properties.append(bullet)


def remove_shapes(slide: Any) -> None:
    """Hapus semua shape dari slide, termasuk placeholder bawaan layout-nya."""
    for shape in list(slide.shapes):
        element = shape.element
        element.getparent().remove(element)


def fill_solid(fill: Any, value: Color) -> None:
    """Isi `fill` python-pptx, misalnya latar slide atau sel tabel, satu warna."""
    fill.solid()
    fill.fore_color.rgb = color(value)
