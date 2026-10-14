"""Read the learner's own material as plain text: files, folders and links.

Shared by silabus_belajar and materi_belajar (each skill keeps its own copy, the pool loads skills
in isolation).

    python scripts/read_material.py buku.pdf foto-papan-tulis.jpg https://example.com/artikel
    from read_material import read_material
    text, notes = read_material(["buku.pdf", "slide.pptx"])

.txt .md .csv .json .html .docx .pptx .xlsx need only the standard library.  .pdf uses `pdftotext`
(poppler) when it is installed, else `pypdf`.  Images (.png .jpg .jpeg .webp .gif .bmp) and PDF pages
without text (a scan) are read by a vision or OCR model: gemma3:4b through Ollama unless READER_MODEL,
READER_API (ollama or openai), READER_BASE_URL and READER_API_KEY name another, in the environment or
the nearest .env.  Reading a scanned page needs `pypdfium2`; .webp .gif .bmp need Pillow.  `notes`
says what a model read, so names and numbers from pictures get checked.
"""

from __future__ import annotations

import base64
import html
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from local_model import Settings, ask_model, choose_model  # noqa: E402

TEXT_EXT = {".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".rst", ".log"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
SUPPORTED = TEXT_EXT | IMAGE_EXT | {".html", ".htm", ".docx", ".pptx", ".xlsx", ".pdf"}
VISION_RECOMMENDED = ("gemma3:4b", "qwen3-vl", "glm-ocr", "gemma3", "qwen2.5vl", "llama3.2-vision", "minicpm-v")
SEEING_MODELS = ("gemma3", "gemma4", "vl", "vision", "ocr", "llava", "minicpm")      # parts of names that can see
MAX_SCANNED_PAGES = 10          # a vision model reads one page in 10-60 s
VISION_PROMPT = ("Salin semua teks yang terbaca di gambar ini apa adanya, dalam urutan baca. Tabel ditulis "
                 "per baris dengan pemisah |. Diagram, grafik, atau foto tanpa teks dijelaskan isinya dalam "
                 "2-4 kalimat. Jangan menambah apa pun yang tidak ada di gambar.")
# Dedicated OCR models answer only their own task prompt (from each model card); the first part of the
# model's name that matches wins, and every other model gets VISION_PROMPT.  READER_PROMPT overrides both.
READER_PROMPTS = (("glm-ocr", "Text Recognition:"), ("paddleocr-vl", "OCR:"), ("deepseek-ocr", "Free OCR."))


class MaterialError(ValueError):
    """A file or link that cannot be read; the message says why and what to install or change."""


# ---------------------------------------------------------------------------
# Office files: the XML inside the zip
# ---------------------------------------------------------------------------

def _xml_text(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def _docx(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    xml = xml.replace("<w:tab/>", "\t")
    paragraphs = []
    for part in re.split(r"<w:p[ >]", xml)[1:]:
        text = _xml_text(part)
        if not text:
            continue
        style = (re.search(r'<w:pStyle w:val="([^"]+)"', part) or [None, ""])[1].lower()
        level = re.match(r"(?:heading|judul)\s*(\d)", style)
        if level:
            text = "#" * int(level.group(1)) + " " + text
        elif "title" in style:
            text = "# " + text
        elif "list" in style:
            text = "- " + text
        paragraphs.append(text)
    return "\n".join(paragraphs)


def _pptx(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        slides = sorted((n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                        key=lambda n: int(re.search(r"(\d+)\.xml$", n).group(1)))
        out = []
        for number, name in enumerate(slides, 1):
            xml = z.read(name).decode("utf-8", errors="replace")
            lines = [_xml_text(p) for p in re.split(r"</a:p>", xml)]
            out.append(f"## Slide {number}\n" + "\n".join(line for line in lines if line))
    return "\n\n".join(out)


def _xlsx(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        shared = []
        if "xl/sharedStrings.xml" in names:
            xml = z.read("xl/sharedStrings.xml").decode("utf-8", errors="replace")
            shared = [_xml_text(si) for si in re.findall(r"<si>(.*?)</si>", xml, re.S)]
        workbook = z.read("xl/workbook.xml").decode("utf-8", errors="replace") if "xl/workbook.xml" in names else ""
        titles = [html.unescape(t) for t in re.findall(r'<sheet [^>]*name="([^"]+)"', workbook)]
        sheets = sorted((n for n in names if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)),
                        key=lambda n: int(re.search(r"(\d+)\.xml$", n).group(1)))
        out = []
        for i, name in enumerate(sheets):
            xml = z.read(name).decode("utf-8", errors="replace")
            rows = []
            for row in re.findall(r"<row[^>]*>(.*?)</row>", xml, re.S):
                cells = []
                for attrs, body in re.findall(r"<c([^>]*?)(?:/>|>(.*?)</c>)", row, re.S):
                    value = re.search(r"<v>(.*?)</v>", body or "", re.S)
                    if 't="s"' in attrs and value:
                        cells.append(shared[int(value.group(1))] if int(value.group(1)) < len(shared) else "")
                    elif 't="inlineStr"' in attrs:
                        cells.append(_xml_text(body))
                    else:
                        cells.append(html.unescape(value.group(1)) if value else "")
                if any(cells):
                    rows.append(" | ".join(cells))
            title = titles[i] if i < len(titles) else f"Sheet {i + 1}"
            out.append(f"## {title}\n" + "\n".join(rows))
    return "\n\n".join(out)


def _html(text: str) -> str:
    text = re.sub(r"(?is)<(script|style|nav|footer|header|noscript)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?is)<h([1-6])[^>]*>(.*?)</h\1>",
                  lambda m: "\n" + "#" * int(m.group(1)) + " " + re.sub(r"<[^>]+>", "", m.group(2)) + "\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "\n- ", text)
    text = re.sub(r"(?i)</(p|div|tr|h\d|li)[^>]*>|<br\s*/?>", "\n", text)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"[ \t]+", " ", text)


# ---------------------------------------------------------------------------
# Pictures: a vision or OCR model reads them
# ---------------------------------------------------------------------------
# Which model reads is configuration, not code, so the same skill reads with gemma3:4b on a laptop
# today and with a model deployed behind vLLM tomorrow.  Arguments win over the environment, the
# environment over the nearest .env (the folder the command runs in, or one of the six above it).

def _env_with_source(name: str) -> tuple[str | None, str]:
    """The value and where it came from: "environment", or the path of the .env that holds it."""
    if os.environ.get(name):
        return os.environ[name], "environment"
    folder = Path.cwd()
    for _ in range(7):
        env = folder / ".env"
        if env.is_file():
            for line in env.read_text(encoding="utf-8-sig", errors="replace").splitlines():
                key, _, value = line.partition("=")
                if key.strip() == name and value.strip():
                    return value.strip().strip("'\""), str(env)
            return None, ""                     # only the nearest .env counts
        folder = folder.parent
    return None, ""


def _env(name: str) -> str | None:
    return _env_with_source(name)[0]


class VisionReader:
    """Image bytes -> the text a vision or OCR model reads in them.  The model is chosen on first use."""

    def __init__(self, api: str | None = None, base_url: str | None = None, model: str | None = None,
                 api_key: str | None = None, prompt: str | None = None):
        self.api = api or _env("READER_API") or "ollama"
        self.base_url, url_source = (base_url, "argument") if base_url else _env_with_source("READER_BASE_URL")
        self.api_key, key_source = (api_key, "argument") if api_key else _env_with_source("READER_API_KEY")
        # The key goes to whatever address is configured, and .env is searched upward from the folder the
        # command runs in.  A .env found in some other folder must not be able to point the address at
        # its own server while the key comes from somewhere else, so the two must come from one source.
        # An argument is the caller's own choice and is trusted.
        if self.api_key and self.base_url and "argument" not in (url_source, key_source) and url_source != key_source:
            raise MaterialError(
                f"READER_BASE_URL comes from {url_source} but READER_API_KEY from {key_source}.  "
                "The key is sent to that address, so set both in the same .env, or both in the environment.")
        self.api_key = self.api_key or "local"
        self._model = model or _env("READER_MODEL") or _env("VISION_MODEL_ID")
        self._prompt = prompt or _env("READER_PROMPT")

    @property
    def model(self) -> str:
        if not self._model:
            self._model = choose_model(self.api, self.base_url, VISION_RECOMMENDED, self.api_key)
            if not any(part in self._model.lower() for part in SEEING_MODELS):
                self._model = VISION_RECOMMENDED[0]      # a text model cannot see; the request names what to pull
        return self._model

    @property
    def prompt(self) -> str:
        name = self.model.lower()
        return self._prompt or next((p for part, p in READER_PROMPTS if part in name), VISION_PROMPT)

    def __call__(self, image: bytes, name: str) -> str:
        # think off: qwen3-vl otherwise spends all 2048 tokens reasoning and returns no text
        settings = Settings(model=self.model, api=self.api, base_url=self.base_url, api_key=self.api_key,
                            temperature=0.1, max_tokens=2048, num_ctx=4096, think="off")
        try:
            text, _ = ask_model(settings, "", self.prompt, None, images=[_as_png_or_jpeg(image, name)])
        except OSError as error:
            hint = (f"Is Ollama running and {self.model} downloaded (ollama pull {self.model})?" if self.api == "ollama"
                    else "Check READER_BASE_URL, READER_API_KEY and READER_MODEL.")
            raise MaterialError(f"{name}: the vision model {self.model} could not read it ({error}). {hint}") from error
        return _tidy(text)


def _tidy(text: str) -> str:
    """What a reading model wrote, without its extras: an opening line, special tokens, a table written twice."""
    # gemma3:4b opens with "Berikut adalah teks yang terbaca dari gambar ...:" although the prompt says not to
    text = re.sub(r"^\s*(berikut|ini adalah|here is|here are)[^\n]*:\s*\n", "", text, flags=re.I)
    text = re.sub(r"<\|[^|>]{1,40}\|>|<(?:start|end)_of_image>", "", text)

    def rows(table):
        cells = [[_xml_text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
                 for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", table.group(0), re.S | re.I)]
        return "\n".join(" | ".join(row) for row in cells if row)

    text = re.sub(r"<table.*?</table>", rows, text, flags=re.S | re.I)
    # glm-ocr writes a table as plain lines and again as <table>; the version with cells stays
    in_table = {" ".join(line.replace("|", " ").split()) for line in text.splitlines() if " | " in line}
    lines = [line for line in text.splitlines() if " | " in line or " ".join(line.split()) not in in_table]
    return "\n".join(lines).strip()


def _as_png_or_jpeg(image: bytes, name: str) -> bytes:
    if image[:8] == b"\x89PNG\r\n\x1a\n" or image[:3] == b"\xff\xd8\xff":
        return image
    try:
        from PIL import Image
    except ImportError as error:
        raise MaterialError(f"{name}: only PNG and JPEG are read without Pillow; save it as PNG or JPEG, "
                            "or install Pillow") from error
    buffer = io.BytesIO()
    Image.open(io.BytesIO(image)).convert("RGB").save(buffer, "PNG")
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# PDF: text first, a vision model for pages without text
# ---------------------------------------------------------------------------

def _pdf_pages(path: Path) -> list[str]:
    if shutil.which("pdftotext"):
        done = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"], capture_output=True,
                              timeout=180)
        if done.returncode == 0:
            pages = done.stdout.decode("utf-8", errors="replace").split("\f")    # one form feed after each page
            return pages[:-1] if len(pages) > 1 and not pages[-1].strip() else pages
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise MaterialError(f"{path.name}: cannot read PDF; install poppler (pdftotext) or pypdf") from error
    return [page.extract_text() or "" for page in PdfReader(str(path)).pages]


def _pdf(path: Path, label: str, vision: VisionReader, notes: list) -> str:
    pages = _pdf_pages(path)
    blank = [i for i, page in enumerate(pages) if not re.search(r"[^\W\d_]{3}", page)]    # no word: a scan
    if blank:
        try:
            import pypdfium2
        except ImportError:
            pypdfium2 = None
        if pypdfium2 is None:
            notes.append(f"{label}: {len(blank)} page(s) without text (a scan?) skipped; install pypdfium2 "
                         "so a vision model reads them")
        else:
            document = pypdfium2.PdfDocument(str(path))
            try:
                for i in blank[:MAX_SCANNED_PAGES]:
                    buffer = io.BytesIO()
                    document[i].render(scale=2).to_pil().save(buffer, "PNG")
                    pages[i] = vision(buffer.getvalue(), f"{label} halaman {i + 1}")
            finally:
                document.close()        # Windows keeps an open PDF locked
            notes.append(f"{label}: {min(len(blank), MAX_SCANNED_PAGES)} page(s) without text read by "
                         f"{vision.model}; check names and numbers from those pages")
            if len(blank) > MAX_SCANNED_PAGES:
                notes.append(f"{label}: only the first {MAX_SCANNED_PAGES} of {len(blank)} pages without "
                             "text were read")
    return "\n\n".join(f"[halaman {i}]\n{page.strip()}" for i, page in enumerate(pages, 1) if page.strip())


# ---------------------------------------------------------------------------
# One entry point for files, folders and links
# ---------------------------------------------------------------------------

def _read_bytes(data: bytes, name: str, ext: str, vision: VisionReader, notes: list, path: Path | None = None) -> str:
    if ext in TEXT_EXT:
        return data.decode("utf-8-sig", errors="replace")
    if ext in (".html", ".htm"):
        return _html(data.decode("utf-8", errors="replace"))
    if ext == ".docx":
        return _docx(data)
    if ext == ".pptx":
        return _pptx(data)
    if ext == ".xlsx":
        return _xlsx(data)
    if ext in IMAGE_EXT:
        text = vision(data, name)
        notes.append(f"{name}: read by {vision.model} from the image; check names and numbers")
        return text
    if ext == ".pdf":
        if path is not None:
            return _pdf(path, name, vision, notes)
        with tempfile.TemporaryDirectory() as folder:      # a PDF from a link
            temporary = Path(folder) / "material.pdf"
            temporary.write_bytes(data)
            return _pdf(temporary, name, vision, notes)
    raise MaterialError(f"{name}: {ext or 'this file type'} is not read; use PDF, an image, docx, pptx, xlsx, "
                        "html, or a text file (.doc and .ppt: save as .docx or .pptx first)")


def _read_link(url: str, vision: VisionReader, notes: list) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (zul learning skills)"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data, kind = response.read(), response.headers.get("Content-Type", "").lower()
    except OSError as error:
        raise MaterialError(f"{url}: cannot open the link ({error})") from error
    ext = Path(url.split("?")[0]).suffix.lower()
    if "pdf" in kind:
        ext = ".pdf"
    elif kind.startswith("image/"):
        ext = ".png" if "png" in kind else ".jpg"
    elif "html" in kind or ext not in SUPPORTED:
        ext = ".html"
    return _read_bytes(data, url, ext, vision, notes)


def read_material(items: list[str] | str, vision: VisionReader | None = None, max_chars: int = 60000) -> tuple[str, list]:
    """(text, notes) for files, folders or links; each part starts with "# <name>".  Raises MaterialError."""
    items = [items] if isinstance(items, str) else list(items or [])
    vision = vision or VisionReader()
    parts, notes = [], []
    for item in items:
        item = str(item).strip()
        if re.match(r"https?://", item, re.I):
            parts.append((item, _read_link(item, vision, notes)))
            continue
        path = Path(item)
        if not path.exists():
            raise MaterialError(f"{item}: file not found")
        files = sorted(f for f in path.rglob("*") if f.suffix.lower() in SUPPORTED) if path.is_dir() else [path]
        if path.is_dir() and not files:
            raise MaterialError(f"{item}: no file in this folder that can be read")
        for file in files:
            parts.append((file.name, _read_bytes(file.read_bytes(), file.name, file.suffix.lower(), vision, notes, file)))
    parts = [(name, body.replace("\r\n", "\n").replace("\r", "\n")) for name, body in parts]
    sections =[f"# {name}\n" + re.sub(r"\n{3,}", "\n\n", body.strip()) for name, body in parts if body.strip()]
    text = "\n\n".join(sections)
    empty = [name for name, body in parts if not body.strip()]
    if empty:
        notes.append("no text found in " + ", ".join(empty))
    return text[:max_chars], notes


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    try:
        text, notes = read_material(sys.argv[1:])
    except MaterialError as error:
        print(f"GAGAL: {error}")
        return 1
    print(text)
    for note in notes:
        print(f"catatan: {note}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
