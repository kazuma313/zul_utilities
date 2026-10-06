"""Read the user's source material as plain text: .txt .md .html .docx .pdf (or a folder).

    python scripts/extract_text.py lesson.pdf            # prints the text
    from extract_text import read_source
    text = read_source("article.docx")

.docx needs nothing (the XML is unzipped directly).  .pdf uses `pdftotext`
(poppler) when installed, else the Python package `pypdf` or `pdfminer.six`.
.html is stripped of tags and scripts.  Anything else is read as UTF-8 text.
"""

from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def _docx(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    xml = re.sub(r"<w:tab/>", "\t", xml)
    xml = re.sub(r"</w:p>", "\n", xml)
    # keep heading style names as markdown headings so the outline parser can use them
    paras = []
    for p in re.split(r"<w:p[ >]", xml)[1:]:
        m = re.search(r'<w:pStyle w:val="([^"]+)"', p)
        style = (m.group(1) if m else "").lower()
        text = html.unescape(re.sub(r"<[^>]+>", "", p)).strip()
        if not text:
            continue
        hm = re.match(r"(?:heading|judul)\s*(\d)", style)
        if hm:
            text = "#" * int(hm.group(1)) + " " + text
        elif "title" in style:
            text = "# " + text
        elif "list" in style:
            text = "- " + text
        paras.append(text)
    return "\n".join(paras)


def _pdf(path: Path) -> str:
    if shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"], capture_output=True, timeout=120)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.decode("utf-8", errors="replace")
    try:
        from pypdf import PdfReader
        return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(path)).pages)
    except ImportError:
        pass
    try:
        from pdfminer.high_level import extract_text
        return extract_text(str(path))
    except ImportError:
        raise RuntimeError("cannot read PDF: install poppler (pdftotext) or `pip install pypdf`")


def _html(text: str) -> str:
    text = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?i)<h([1-6])[^>]*>(.*?)</h\1>", lambda m: "\n" + "#" * int(m.group(1)) + " " + re.sub(r"<[^>]+>", "", m.group(2)) + "\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "\n- ", text)
    text = re.sub(r"(?i)</(p|div|br|tr|h\d|li)[^>]*>|<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"[ \t]+", " ", text)


def read_source(path_or_text: str, max_chars: int = 40000) -> str:
    """Return plain text.  A string that is not an existing file is returned as-is."""
    p = Path(str(path_or_text))
    if len(str(path_or_text)) < 1000 and p.exists():
        if p.is_dir():
            parts = []
            for f in sorted(p.iterdir()):
                if f.suffix.lower() in (".txt", ".md", ".docx", ".pdf", ".html", ".htm"):
                    parts.append(f"# {f.stem}\n" + read_source(str(f), max_chars))
            text = "\n\n".join(parts)
        else:
            ext = p.suffix.lower()
            if ext == ".docx":
                text = _docx(p)
            elif ext == ".pdf":
                text = _pdf(p)
            elif ext in (".html", ".htm"):
                text = _html(p.read_text(encoding="utf-8", errors="replace"))
            else:
                text = p.read_text(encoding="utf-8-sig", errors="replace")
    else:
        text = str(path_or_text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:max_chars]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.stdout.reconfigure(encoding="utf-8")
    print(read_source(sys.argv[1]))
