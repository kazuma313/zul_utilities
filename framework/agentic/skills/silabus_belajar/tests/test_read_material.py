"""Tests without a model or a network for read_material.py (the learner's own files and links).

    python -m pytest research/agentic/algorithms/skills/silabus_belajar/tests -q -p no:cacheprovider
"""

import io
import json
import sys
import zipfile
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
import generate_silabus as gs  # noqa: E402
import read_material as rm  # noqa: E402

REFERENCE = json.loads((SKILL / "tests" / "fixtures" / "silabus-reksa-dana.json").read_text(encoding="utf-8"))


class FakeVision:
    """Stands in for the vision model: records what it was given and answers with a fixed text."""

    model = "fake-vision"

    def __init__(self, answer="Teks dari gambar: NAB per unit Rp1.250"):
        self.answer, self.seen = answer, []

    def __call__(self, image, name):
        self.seen.append((name, image[:8]))
        return self.answer


def zip_bytes(files: dict) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for name, text in files.items():
            z.writestr(name, text)
    return buffer.getvalue()


def pdf_bytes(*pages: str) -> bytes:
    """A small valid PDF; an empty string makes a page without text, like a scan."""
    objects = ["<< /Type /Catalog /Pages 2 0 R >>",
               "<< /Type /Pages /Kids [" + " ".join(f"{3 + 2 * i} 0 R" for i in range(len(pages)))
               + f"] /Count {len(pages)} >>"]
    font = 3 + 2 * len(pages)
    for i, text in enumerate(pages):
        stream = f"BT /F1 14 Tf 20 100 Td ({text}) Tj ET" if text else ""
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Contents {4 + 2 * i} 0 R "
                       f"/Resources << /Font << /F1 {font} 0 R >> >> >>")
        objects.append(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out, offsets = b"%PDF-1.4\n", []
    for number, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n{body}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets).encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


# ---------------------------------------------------------------------------
# Files the standard library reads
# ---------------------------------------------------------------------------

def test_text_files_and_html_are_read_with_their_names(tmp_path):
    (tmp_path / "catatan.md").write_text("# NAB\nNilai aktiva bersih.", encoding="utf-8")
    (tmp_path / "artikel.html").write_text("<script>x()</script><h2>Biaya</h2><p>Fee <b>beli</b> 1%</p>",
                                           encoding="utf-8")

    text, notes = rm.read_material([str(tmp_path / "catatan.md"), str(tmp_path / "artikel.html")], FakeVision())

    assert text.startswith("# catatan.md\n# NAB\nNilai aktiva bersih.")
    assert "# artikel.html" in text and "## Biaya" in text and "Fee beli 1%" in text and "x()" not in text
    assert notes == []


def test_docx_keeps_headings_and_lists(tmp_path):
    body = ('<w:body><w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Reksa dana</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>Uang dikelola manajer investasi.</w:t></w:r></w:p>'
            '<w:p><w:pPr><w:pStyle w:val="ListParagraph"/></w:pPr><w:r><w:t>Saham</w:t></w:r></w:p></w:body>')
    path = tmp_path / "bab.docx"
    path.write_bytes(zip_bytes({"word/document.xml": body}))

    text, _ = rm.read_material(str(path), FakeVision())

    assert text == "# bab.docx\n# Reksa dana\nUang dikelola manajer investasi.\n- Saham"


def test_pptx_slides_come_in_number_order(tmp_path):
    slide = '<p:sld><a:p><a:r><a:t>{}</a:t></a:r></a:p><a:p><a:r><a:t>poin {}</a:t></a:r></a:p></p:sld>'
    path = tmp_path / "kuliah.pptx"
    path.write_bytes(zip_bytes({f"ppt/slides/slide{n}.xml": slide.format(f"Judul {n}", n) for n in (10, 2, 1)}))

    text, _ = rm.read_material(str(path), FakeVision())

    assert text.index("Judul 1") < text.index("Judul 2") < text.index("Judul 10")
    assert "## Slide 3\nJudul 10\npoin 10" in text


def test_xlsx_rows_use_shared_strings_and_sheet_names(tmp_path):
    path = tmp_path / "penjualan.xlsx"
    path.write_bytes(zip_bytes({
        "xl/workbook.xml": '<workbook><sheets><sheet name="Mei" sheetId="1"/></sheets></workbook>',
        "xl/sharedStrings.xml": "<sst><si><t>menu</t></si><si><t>jumlah</t></si><si><t>kopi</t></si></sst>",
        "xl/worksheets/sheet1.xml": ('<worksheet><sheetData>'
                                     '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
                                     '<row r="2"><c r="A2" t="s"><v>2</v></c><c r="B2"><v>12</v></c></row>'
                                     '</sheetData></worksheet>'),
    }))

    text, _ = rm.read_material(str(path), FakeVision())

    assert text == "# penjualan.xlsx\n## Mei\nmenu | jumlah\nkopi | 12"


def test_a_folder_is_read_file_by_file(tmp_path):
    (tmp_path / "b.txt").write_text("dua", encoding="utf-8")
    (tmp_path / "a.txt").write_text("satu", encoding="utf-8")
    (tmp_path / "skip.exe").write_bytes(b"MZ")

    text, _ = rm.read_material(str(tmp_path), FakeVision())

    assert text == "# a.txt\nsatu\n\n# b.txt\ndua"


# ---------------------------------------------------------------------------
# PDF and pictures
# ---------------------------------------------------------------------------

def test_pdf_text_is_read_page_by_page(tmp_path):
    path = tmp_path / "modul.pdf"
    path.write_bytes(pdf_bytes("Halaman satu tentang NAB per unit", "Halaman dua tentang biaya pembelian"))

    text, notes = rm.read_material(str(path), FakeVision())

    assert "[halaman 1]" in text and "NAB per unit" in text and "[halaman 2]" in text and "biaya pembelian" in text
    assert notes == []


def test_a_pdf_page_without_text_goes_to_the_vision_model(tmp_path):
    pytest.importorskip("pypdfium2")
    path = tmp_path / "scan.pdf"
    path.write_bytes(pdf_bytes("Halaman satu tentang NAB per unit", ""))
    vision = FakeVision()

    text, notes = rm.read_material(str(path), vision)

    assert vision.seen == [("scan.pdf halaman 2", b"\x89PNG\r\n\x1a\n")]
    assert "[halaman 2]\nTeks dari gambar: NAB per unit Rp1.250" in text
    assert notes == ["scan.pdf: 1 page(s) without text read by fake-vision; check names and numbers from those pages"]


def test_an_image_is_read_by_the_vision_model_and_noted(tmp_path):
    path = tmp_path / "papan-tulis.png"
    path.write_bytes(PNG)
    vision = FakeVision("Rumus: unit = uang / NAB per unit")

    text, notes = rm.read_material(str(path), vision)

    assert text == "# papan-tulis.png\nRumus: unit = uang / NAB per unit"
    assert notes == ["papan-tulis.png: read by fake-vision from the image; check names and numbers"]


def test_the_vision_reader_sends_the_image_to_the_model(monkeypatch):
    sent = {}

    def fake_ask(settings, system, user, schema, images=None):
        sent.update(model=settings.model, images=images, user=user)
        return "  teks  ", {"seconds": 1}

    monkeypatch.setattr(rm, "ask_model", fake_ask)

    assert rm.VisionReader(model="gemma3:4b")(PNG, "foto.png") == "teks"
    assert sent["model"] == "gemma3:4b" and sent["images"] == [PNG] and "Salin semua teks" in sent["user"]


def test_the_vision_reader_drops_the_models_opening_line(monkeypatch):
    answer = "Berikut adalah teks yang terbaca dari gambar, dalam urutan baca:\n\nSurvei dalam angka\n350 | 72%"
    monkeypatch.setattr(rm, "ask_model", lambda *a, **k: (answer, {}))

    assert rm.VisionReader(model="gemma3:4b")(PNG, "slide.png") == "Survei dalam angka\n350 | 72%"


def test_a_text_model_is_never_chosen_to_read_pictures(monkeypatch):
    monkeypatch.delenv("VISION_MODEL_ID", raising=False)
    monkeypatch.setattr(rm, "choose_model", lambda *a, **k: "qwen3:8b")

    assert rm.VisionReader().model == "gemma3:4b"


# ---------------------------------------------------------------------------
# Links and errors
# ---------------------------------------------------------------------------

class FakeResponse:
    def __init__(self, data, kind):
        self.data, self.headers = data, {"Content-Type": kind}

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_a_link_is_read_by_its_content_type(monkeypatch):
    pages = {"https://contoh.id/artikel": FakeResponse(b"<h1>Reksa dana</h1><p>Isi artikel</p>", "text/html"),
             "https://contoh.id/unduh?id=7": FakeResponse(pdf_bytes("Isi PDF dari link"), "application/pdf")}
    monkeypatch.setattr(rm.urllib.request, "urlopen", lambda request, timeout: pages[request.full_url])

    text, _ = rm.read_material(list(pages), FakeVision())

    assert "# https://contoh.id/artikel\n# Reksa dana" in text and "Isi artikel" in text
    assert "Isi PDF dari link" in text


@pytest.mark.parametrize("name, message", [("catatan.doc", "save as .docx"), ("tidak-ada.pdf", "file not found")])
def test_files_that_cannot_be_read_say_why(tmp_path, name, message):
    if name.endswith(".doc"):
        (tmp_path / name).write_bytes(b"\xd0\xcf\x11\xe0")

    with pytest.raises(rm.MaterialError, match=message):
        rm.read_material(str(tmp_path / name), FakeVision())


# ---------------------------------------------------------------------------
# The generator uses the material
# ---------------------------------------------------------------------------

def test_the_generator_sends_the_material_and_reports_what_was_cut(tmp_path, monkeypatch):
    material = tmp_path / "buku.txt"
    material.write_text("Reksa dana adalah wadah. " * 700, encoding="utf-8")
    sent = []

    def fake_ask(settings, system, user, schema):
        sent.append(user)
        return json.dumps(REFERENCE), {"seconds": 1.0, "tokens": 100}

    monkeypatch.setattr(gs, "ask_model", fake_ask)
    res = gs.generate("", str(tmp_path / "s.html"), settings=gs.Settings(model="fake"), files=[str(material)])

    assert res["ok"]
    assert "Topik: tentukan dari bahan di bawah" in sent[0] and "# buku.txt\nReksa dana adalah wadah." in sent[0]
    assert res["warnings"][0] == "the material has 17,510 characters; the model got the first 12,000"


def test_the_generator_reports_a_file_it_cannot_read(tmp_path):
    res = gs.generate("Reksa dana", str(tmp_path / "s.html"), settings=gs.Settings(model="fake"),
                      files=[str(tmp_path / "hilang.pdf")])

    assert not res["ok"] and "hilang.pdf: file not found" in res["error"]
