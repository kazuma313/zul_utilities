from types import SimpleNamespace

import pytest

# --------------------------------------------------------------------------
# PDF Kecil Untuk Test
# --------------------------------------------------------------------------
#
# PDF ini ditulis langsung sebagai bytes: satu halaman per teks, font
# Helvetica standar, dan tabel xref yang offset-nya dihitung. Jadi
# test tidak butuh library pembuat PDF selain yang sedang diuji.
#


def tiny_pdf(texts: list[str]) -> bytes:
    page_ids = [4 + 2 * index for index in range(len(texts))]
    kids = " ".join(f"{number} 0 R" for number in page_ids)
    bodies = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {len(texts)} >>".encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for page_id, text in zip(page_ids, texts, strict=True):
        bodies.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> "
            f"/Contents {page_id + 1} 0 R >>".encode()
        )
        stream = f"BT /F1 24 Tf 72 720 Td ({text}) Tj ET".encode()
        bodies.append(
            b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream)
        )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(bodies, start=1):
        offsets.append(len(pdf))
        pdf += b"%d 0 obj\n%s\nendobj\n" % (number, body)
    xref = len(pdf)
    pdf += b"xref\n0 %d\n0000000000 65535 f \n" % (len(bodies) + 1)
    pdf += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    pdf += b"trailer\n<< /Size %d /Root 1 0 R >>\n" % (len(bodies) + 1)
    pdf += b"startxref\n%d\n%%%%EOF\n" % xref
    return bytes(pdf)


@pytest.fixture
def pdf_folder(tmp_path):
    (tmp_path / "laporan.pdf").write_bytes(tiny_pdf(["Halaman satu", "Halaman dua"]))
    (tmp_path / "rusak.pdf").write_bytes(b"bukan pdf")
    return tmp_path


@pytest.fixture
def pypdf_adapter():
    return pytest.importorskip("zul.adapters.pypdf")


@pytest.fixture
def text_splitters():
    return pytest.importorskip("zul.adapters.langchain_text_splitters")


@pytest.fixture
def pdf_processor():
    read_pdf2 = pytest.importorskip("zul.utilities.script_helper.read_pdf2")
    return read_pdf2.PDFProcessor(read_pdf2.PDFConfig(verbose=False))


@pytest.fixture
def broken_first_page(monkeypatch):
    """Ekstraksi teks halaman pertama gagal; halaman lain tetap terbaca."""
    page_class = pytest.importorskip("pypdf").PageObject
    original = page_class.extract_text
    calls = []

    def extract_text(self, *args, **kwargs):
        calls.append(self)
        if len(calls) == 1:
            raise ValueError("font rusak")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(page_class, "extract_text", extract_text)


# --------------------------------------------------------------------------
# Adapter pypdf
# --------------------------------------------------------------------------


def test_read_pages_returns_stripped_text_per_page(pypdf_adapter, pdf_folder):
    pages = pypdf_adapter.read_pages(pdf_folder / "laporan.pdf")

    assert pages == ["Halaman satu", "Halaman dua"]


def test_page_that_fails_becomes_empty_and_is_reported(
    pypdf_adapter, pdf_folder, broken_first_page
):
    errors = []

    pages = pypdf_adapter.read_pages(
        pdf_folder / "laporan.pdf",
        on_page_error=lambda number, message: errors.append((number, message)),
    )

    assert pages == ["", "Halaman dua"]
    assert errors == [(1, "font rusak")]


def test_file_that_is_not_a_pdf_raises_pdf_error(pypdf_adapter, pdf_folder):
    with pytest.raises(pypdf_adapter.PdfError) as raised:
        pypdf_adapter.read_pages(pdf_folder / "rusak.pdf")

    assert isinstance(raised.value, ValueError)
    assert str(raised.value) == str(raised.value.__cause__)


def test_missing_pdf_raises_os_error(pypdf_adapter, tmp_path):
    with pytest.raises(OSError):
        pypdf_adapter.read_pages(tmp_path / "tidak-ada.pdf")


# --------------------------------------------------------------------------
# Adapter langchain-text-splitters
# --------------------------------------------------------------------------


def test_splitter_cuts_at_paragraphs_before_words(text_splitters):
    text = "paragraf satu\n\nparagraf dua"
    by_paragraph = text_splitters.recursive_character_splitter(chunk_size=13, overlap=0)
    by_word = text_splitters.recursive_character_splitter(chunk_size=12, overlap=0)

    assert by_paragraph(text) == ["paragraf satu", "paragraf dua"]
    assert by_word(text) == ["paragraf", "satu", "paragraf", "dua"]


def test_splitter_checks_overlap_when_created(text_splitters):
    with pytest.raises(ValueError):
        text_splitters.recursive_character_splitter(chunk_size=10, overlap=20)


def test_documents_carry_text_without_metadata(text_splitters):
    documents = text_splitters.to_documents(["satu", "dua"])

    assert [document.page_content for document in documents] == ["satu", "dua"]
    assert all(document.metadata == {} for document in documents)


# --------------------------------------------------------------------------
# PDFProcessor Lewat Adapter
# --------------------------------------------------------------------------


def test_processor_reads_pages_and_single_text(pdf_processor, pdf_folder):
    path = pdf_folder / "laporan.pdf"

    assert pdf_processor.read_pdf_pages(path) == ["Halaman satu", "Halaman dua"]
    assert pdf_processor.read_pdf_as_single_text(path) == "Halaman satu\nHalaman dua"


def test_chunk_per_page_returns_one_langchain_document_per_page(
    pdf_processor, pdf_folder
):
    from langchain_core.documents import Document

    documents = pdf_processor.chunk_per_page(pdf_folder / "laporan.pdf")

    assert all(isinstance(document, Document) for document in documents)
    assert [document.page_content for document in documents] == [
        "Halaman satu",
        "Halaman dua",
    ]


def test_recursive_chunks_are_langchain_documents_within_chunk_size(
    pdf_processor, pdf_folder
):
    from langchain_core.documents import Document

    chunks = pdf_processor.chunk_recursive_character_splitter(
        pdf_folder / "laporan.pdf", chunk_size=12, overlap=0
    )

    assert [chunk.page_content for chunk in chunks] == ["Halaman satu", "Halaman dua"]
    assert all(isinstance(chunk, Document) and chunk.metadata == {} for chunk in chunks)


def test_invalid_overlap_raises_even_if_pdf_is_missing(pdf_processor, tmp_path):
    with pytest.raises(ValueError):
        pdf_processor.chunk_recursive_character_splitter(
            tmp_path / "tidak-ada.pdf", chunk_size=10, overlap=20
        )


def test_unreadable_pdf_gives_none_and_keeps_the_error(pdf_processor, pdf_folder):
    path = pdf_folder / "rusak.pdf"

    assert pdf_processor.read_pdf_pages(path) is None
    assert pdf_processor.last_error.startswith(f"Error reading PDF {path}: ")
    assert pdf_processor.chunk_per_page(path) == []
    assert pdf_processor.chunk_recursive_character_splitter(path) == []


def test_page_error_is_kept_as_last_error(pdf_processor, pdf_folder, broken_first_page):
    pages = pdf_processor.read_pdf_pages(pdf_folder / "laporan.pdf")

    assert pages == ["", "Halaman dua"]
    assert pdf_processor.last_error == "Error reading page 1: font rusak"


def test_missing_pdf_is_reported(pdf_processor, tmp_path):
    path = tmp_path / "tidak-ada.pdf"

    assert pdf_processor.read_pdf_pages(path) is None
    assert pdf_processor.last_error == f"PDF file does not exist: {path}"


def test_process_folder_counts_readable_and_broken_files(pdf_processor, pdf_folder):
    stats = pdf_processor.process_folder(pdf_folder)

    assert stats["total_files"] == 2
    assert stats["processed_files"] == 1
    assert stats["failed_files"] == 1
    assert stats["total_pages"] == 2
    (file_data,) = stats["files_data"]
    assert file_data["min_max_page_length"] == (11, 12)


# --------------------------------------------------------------------------
# Adapter Markdown Dan xhtml2pdf
# --------------------------------------------------------------------------


def test_markdown_table_extension_gives_html_table():
    markdown_adapter = pytest.importorskip("zul.adapters.markdown")

    html = markdown_adapter.to_html("| A | B |\n|---|---|\n| 1 | 2 |", ["tables"])

    assert "<table>" in html
    assert "<table>" not in markdown_adapter.to_html("| A | B |\n|---|---|\n| 1 | 2 |")


def test_unknown_markdown_extension_raises_import_error():
    markdown_adapter = pytest.importorskip("zul.adapters.markdown")

    with pytest.raises(ImportError):
        markdown_adapter.to_html("# Judul", ["bukan_extension_markdown"])


def test_render_pdf_returns_pdf_bytes_and_write_pdf_writes_them(tmp_path):
    xhtml2pdf_adapter = pytest.importorskip("zul.adapters.xhtml2pdf")
    html = "<html><body><h1>Judul</h1></body></html>"

    xhtml2pdf_adapter.write_pdf(html, tmp_path / "judul.pdf")

    assert xhtml2pdf_adapter.render_pdf(html).startswith(b"%PDF")
    assert (tmp_path / "judul.pdf").read_bytes().startswith(b"%PDF")


def test_errors_reported_by_xhtml2pdf_raise_pdf_render_error(monkeypatch):
    xhtml2pdf_adapter = pytest.importorskip("zul.adapters.xhtml2pdf")
    monkeypatch.setattr(
        xhtml2pdf_adapter.pisa, "CreatePDF", lambda html, dest: SimpleNamespace(err=2)
    )

    with pytest.raises(xhtml2pdf_adapter.PdfRenderError) as raised:
        xhtml2pdf_adapter.render_pdf("<p>isi</p>")

    assert raised.value.errors == 2


# --------------------------------------------------------------------------
# Adapter python-pptx
# --------------------------------------------------------------------------


@pytest.fixture
def pptx_adapter():
    return pytest.importorskip("zul.adapters.pptx")


def test_color_accepts_tuple_hex_and_rgbcolor(pptx_adapter):
    from pptx.dml.color import RGBColor

    expected = RGBColor(26, 54, 93)

    assert pptx_adapter.color((26, 54, 93)) == expected
    assert pptx_adapter.color("#1A365D") == expected
    assert pptx_adapter.color(expected) is expected
    assert isinstance(pptx_adapter.color((26, 54, 93)), RGBColor)


@pytest.mark.parametrize("value", [(1, 2), (0, 0, 300), "#XYZXYZ", None])
def test_invalid_color_raises_value_error(pptx_adapter, value):
    with pytest.raises(ValueError):
        pptx_adapter.color(value)


def test_inches_box_matches_inches(pptx_adapter):
    box = pptx_adapter.inches_box(0.5, 1, 9, 0.8)

    assert box == tuple(pptx_adapter.inches(value) for value in (0.5, 1, 9, 0.8))
    assert box[0] == 457200


def test_show_bullet_adds_one_bullet_even_when_called_twice(pptx_adapter):
    prs = pptx_adapter.new_presentation(width_inches=10, height_inches=5.625)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    textbox = slide.shapes.add_textbox(*pptx_adapter.inches_box(1, 1, 8, 1))
    paragraph = textbox.text_frame.paragraphs[0]

    pptx_adapter.show_bullet(paragraph)
    pptx_adapter.show_bullet(paragraph)

    bullets = paragraph._element.pPr.findall(
        f"{{{pptx_adapter.DRAWINGML_NAMESPACE}}}buChar"
    )
    assert [bullet.get("char") for bullet in bullets] == ["•"]
    assert prs.slide_width == pptx_adapter.inches(10)


def test_unknown_alignment_raises_value_error(pptx_adapter):
    with pytest.raises(ValueError):
        pptx_adapter.align(SimpleNamespace(alignment=None), "tengah")
