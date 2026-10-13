"""DOCX skill — read uploaded Word documents and create new .docx files."""

import json
import logging
import re
import uuid
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, RGBColor, Inches
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.agent.minio_connection import upload_file_to_minio

logger = logging.getLogger(__name__)


def _loads_lenient(text: str):
    """json.loads that forgives what a small model adds around the JSON it passes as a string.

    Seen with qwen3:4b and qwen3:8b calling these tools: a stray quote or a remark after the closing
    brace, a code fence around the JSON, a comma before a closing bracket.  The first complete JSON
    value is taken and the rest is ignored.
    """
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=0)
    text = text[start:]
    error = None
    no_trailing = re.sub(r",\s*([\]}])", r"\1", text)
    for candidate in (text, no_trailing, _closed(no_trailing)):
        try:
            return json.JSONDecoder().raw_decode(candidate)[0]
        except json.JSONDecodeError as e:
            error = error or e
    raise error


def _closed(text: str) -> str:
    """The text plus the brackets it opened and never closed.

    Seen with qwen3:8b: a long document that ends in "]}]" where "]}]}" was needed.
    """
    stack, in_string, escaped = [], False, False
    for ch in text:
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]" and stack:
            stack.pop()
    return text + ('"' if in_string else "") + "".join(reversed(stack))


def _spec_from_markdown(text: str) -> dict:
    """Document spec from Markdown or plain text.

    Seen with gemma3:4b: asked for a longer document, it writes the document itself into `content`
    (a title line, paragraphs, "**Heading:**", "* " bullets, a "|" table) instead of the JSON that
    create_docx describes.  The text carries everything the document needs, so it is read, not refused.
    """
    def plain(s: str) -> str:
        return re.sub(r"\*\*(.+?)\*\*|__(.+?)__|`(.+?)`", lambda m: next(g for g in m.groups() if g), s).strip()

    special = re.compile(r"#{1,6}\s|\||[*\-+•]\s|\d+[.)]\s|\*\*[^*]+\*\*:?$")
    spec, lines, i = {"title": "", "sections": []}, text.replace("\r", "").split("\n"), 0
    sections = spec["sections"]
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        heading = re.match(r"(#{1,6})\s+(.*)", line)
        bold_line = re.fullmatch(r"\*\*(.+?)\*\*:?", line)
        item = re.match(r"(?:[*\-+•]|(\d+[.)]))\s+(.*)", line)
        if heading or bold_line:
            words = plain(heading.group(2) if heading else bold_line.group(1)).rstrip(":").strip()
            if heading and len(heading.group(1)) == 1 and not spec["title"] and not sections:
                spec["title"] = words
            else:
                sections.append({"type": "heading2" if heading and len(heading.group(1)) > 2 else "heading1", "text": words})
        elif line.startswith("|"):
            rows = [line]
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            cells = [[plain(c) for c in r.strip("|").split("|")] for r in rows if not re.fullmatch(r"[\s|:\-]+", r)]
            if cells:
                sections.append({"type": "table", "headers": cells[0], "rows": cells[1:]})
        elif item:
            kind = "numbered" if item.group(1) else "bullet"
            if not sections or sections[-1]["type"] != kind:
                sections.append({"type": kind, "items": []})
            sections[-1]["items"].append(plain(item.group(2)))
        else:
            while i < len(lines) and lines[i].strip() and not special.match(lines[i].strip()):
                line += " " + lines[i].strip()
                i += 1
            if not spec["title"] and not sections and len(line) <= 90 and not line.endswith("."):
                spec["title"] = plain(line)
            else:
                sections.append({"type": "paragraph", "text": plain(line)})
    return spec


UPLOADS_DIR   = Path(__file__).parent.parent.parent / "app" / "uploads"
DOWNLOADS_DIR = Path(__file__).parent.parent.parent / "app" / "static" / "downloads"
CHARTS_DIR    = Path(__file__).parent.parent.parent / "app" / "static" / "charts"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_image_path(src: str) -> Path | None:
    """Resolve a chart_url token or bare filename to an absolute Path."""
    if not src:
        return None
    # chart_url:/static/charts/abc123.png  →  CHARTS_DIR/abc123.png
    if src.startswith("chart_url:"):
        src = src[len("chart_url:"):]
    if src.startswith("/static/charts/"):
        return CHARTS_DIR / src[len("/static/charts/"):]
    p = CHARTS_DIR / src
    if p.exists():
        return p
    return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_upload(file_id: str) -> Path:
    return UPLOADS_DIR / file_id


def _set_cell_bg(cell, hex_color: str) -> None:
    """Set table cell background colour."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _add_styled_table(doc: Document, headers: list, rows: list) -> None:
    """Add a table with a styled header row."""
    col_count = len(headers)
    table = doc.add_table(rows=1 + len(rows), cols=col_count)
    table.style = "Table Grid"

    # Header
    hdr_row = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.text = str(h)
        cell.paragraphs[0].runs[0].bold = True
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        _set_cell_bg(cell, "366092")

    # Data rows
    for r_idx, row in enumerate(rows):
        tbl_row = table.rows[r_idx + 1]
        for c_idx, val in enumerate(row[:col_count]):
            tbl_row.cells[c_idx].text = str(val) if val is not None else ""


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def read_docx(file_id: str) -> str:
    """Read and extract the content of an uploaded Word (.docx) document.

    Use this when the user uploads a .docx file and asks to read, summarize,
    or analyze its content.

    Args:
        file_id: The file identifier from the upload (format: 'thread_id/uuid.docx').
    """
    logger.info("[TOOL] read_docx called | file_id=%s", file_id)

    path = _resolve_upload(file_id)
    if not path.exists():
        return f"File not found for file_id '{file_id}'. Make sure the file was uploaded."

    if path.suffix.lower() not in {".docx", ".doc"}:
        return f"Unsupported file type '{path.suffix}'. Only .docx is supported."

    try:
        doc = Document(str(path))
        parts: list[str] = []

        for element in doc.element.body:
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

            if tag == "p":
                # Find matching paragraph in doc.paragraphs by element identity
                para = next((p for p in doc.paragraphs if p._element is element), None)
                if para is None:
                    continue
                text = para.text.strip()
                if not text:
                    continue
                style = para.style.name if para.style else ""
                if style.startswith("Heading 1"):
                    parts.append(f"# {text}")
                elif style.startswith("Heading 2"):
                    parts.append(f"## {text}")
                elif style.startswith("Heading 3"):
                    parts.append(f"### {text}")
                elif style.startswith("List"):
                    parts.append(f"- {text}")
                else:
                    parts.append(text)

            elif tag == "tbl":
                tbl = next((t for t in doc.tables if t._element is element), None)
                if tbl is None:
                    continue
                table_lines: list[str] = []
                for r_idx, row in enumerate(tbl.rows):
                    cells = [c.text.replace("\n", " ").strip() for c in row.cells]
                    table_lines.append("| " + " | ".join(cells) + " |")
                    if r_idx == 0:
                        table_lines.append("| " + " | ".join(["---"] * len(cells)) + " |")
                parts.append("\n".join(table_lines))

        logger.info("[TOOL] read_docx done | paragraphs=%d", len(parts))
        return "\n\n".join(parts) if parts else "(Document appears to be empty)"

    except Exception as e:
        logger.error("[TOOL] read_docx error: %s", e)
        return f"Failed to read document: {e}"


@tool
def create_docx(content: str, filename: str, config: RunnableConfig = None) -> str:
    """Create a formatted Word (.docx) document from structured JSON content.

    Use this when the user wants a Word document, report, memo, or letter.

    Args:
        content:  JSON string describing the document. Format:
                  {
                    "title": "Document Title",
                    "author": "Author Name",
                    "sections": [
                      {"type": "heading1", "text": "Section Name"},
                      {"type": "heading2", "text": "Subsection"},
                      {"type": "paragraph", "text": "Body text here.", "bold": false},
                      {"type": "bullet", "items": ["A", "B", "C"]},
                      {"type": "numbered", "items": ["Step 1", "Step 2"]},
                      {"type": "table", "headers": ["Col1","Col2"], "rows":[["a","b"]]},
                      {"type": "image", "image_url": "chart_url:/static/charts/abc123.png", "caption": "Figure 1", "width_inches": 6.0},
                      {"type": "page_break"}
                    ]
                  }
                  For image_url use the exact chart_url: token returned by analyze_data or generate_chart.
        filename: Output filename (should end in .docx).
    """
    logger.info("[TOOL] create_docx called | filename=%s", filename)

    if not filename.endswith(".docx"):
        filename += ".docx"

    try:
        spec = _loads_lenient(content)
        if not isinstance(spec, dict):
            raise ValueError("content must be a JSON object")
    except Exception as e:
        if content.lstrip().startswith(("{", "[", "```")):
            return f"Invalid JSON content: {e}"
        spec = _spec_from_markdown(content)      # the model wrote the document itself, not its JSON description

    try:
        doc = Document()

        # Document title
        title_text = spec.get("title", "")
        if title_text:
            title_para = doc.add_heading(title_text, level=0)
            title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Author line
        author = spec.get("author", "")
        if author:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(author)
            run.italic = True
            run.font.color.rgb = RGBColor(0x60, 0x60, 0x60)

        if title_text or author:
            doc.add_paragraph()  # spacer

        for section in spec.get("sections", []):
            stype = section.get("type", "paragraph")

            if stype == "heading1":
                doc.add_heading(section.get("text", ""), level=1)

            elif stype == "heading2":
                doc.add_heading(section.get("text", ""), level=2)

            elif stype == "heading3":
                doc.add_heading(section.get("text", ""), level=3)

            elif stype == "paragraph":
                p = doc.add_paragraph()
                run = p.add_run(section.get("text", ""))
                if section.get("bold"):
                    run.bold = True

            elif stype == "bullet":
                for item in section.get("items", []):
                    doc.add_paragraph(str(item), style="List Bullet")

            elif stype == "numbered":
                for item in section.get("items", []):
                    doc.add_paragraph(str(item), style="List Number")

            elif stype == "table":
                headers = section.get("headers", [])
                rows = section.get("rows", [])
                if headers:
                    _add_styled_table(doc, headers, rows)
                    doc.add_paragraph()  # spacer after table

            elif stype == "image":
                img_path = _resolve_image_path(section.get("image_url", ""))
                if img_path and img_path.exists():
                    width_inches = section.get("width_inches", 6.0)
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = p.add_run()
                    run.add_picture(str(img_path), width=Inches(width_inches))
                    caption = section.get("caption", "")
                    if caption:
                        cap_p = doc.add_paragraph(caption)
                        cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        cap_p.runs[0].italic = True
                        cap_p.runs[0].font.size = Pt(10)
                        cap_p.runs[0].font.color.rgb = RGBColor(0x60, 0x60, 0x60)
                    doc.add_paragraph()  # spacer
                else:
                    doc.add_paragraph(f"[Image not found: {section.get('image_url', '')}]")

            elif stype == "page_break":
                doc.add_page_break()

        out_name = f"{uuid.uuid4().hex}_{filename}"
        out_path = DOWNLOADS_DIR / out_name
        doc.save(str(out_path))

        thread_id = (config or {}).get("configurable", {}).get("thread_id", "")
        username = thread_id.split("__")[0] if "__" in thread_id else "anonymous"
        minio_name = upload_file_to_minio(
            out_path.read_bytes(), username, filename,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            folder="docx",
        )
        if minio_name:
            url = f"/api/files/{minio_name}"
            suffix = ""
        else:
            url = f"/static/downloads/{out_name}"
            suffix = " (WARNING: MinIO upload failed — file may disappear on server restart)"
        logger.info("[TOOL] create_docx saved | url=%s", url)
        return f"Word document created successfully. file_url:{url}{suffix}"

    except Exception as e:
        logger.error("[TOOL] create_docx error: %s", e)
        return f"Failed to create document: {e}"
