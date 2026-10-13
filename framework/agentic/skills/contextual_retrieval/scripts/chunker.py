"""Documents -> chunks that keep their place in the document: heading path, character span, metadata.

    from chunker import read_document, chunk_document
    doc = read_document("transcript.txt")          # YAML front matter (if any) + body
    chunks = chunk_document(doc)

Markdown headings (# ... ######) open sections; a chunk never crosses a section boundary.  Transcripts from
the youtube_transcript skill fit this as they are: their chapters are "### HH:MM:SS title" headings.
Inside a section, paragraphs are packed up to `target` characters; a paragraph longer than `limit` is cut
between sentences, and a fenced code block is never cut at a blank line.  Every chunk is an exact slice of
the document body (chunk.text == body[chunk.start:chunk.end]).  Standard library only (PyYAML, when
installed, reads the front matter).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

TARGET_CHARS = 1000     # a few hundred tokens, as in Anthropic's contextual retrieval
LIMIT_CHARS = 1500      # no chunk is longer than this
MIN_CHARS = 250         # a smaller last piece of a section joins the piece before it
SKIP_SECTIONS = ("Video description",)   # the uploader's text in transcript files: links and promotion, not content

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
FENCE_RE = re.compile(r"^[ \t]*(```|~~~)")
SENTENCE_END_RE = re.compile(r"(?<=[.!?…])\s+")
FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.S)


@dataclass
class Document:
    doc_id: str
    title: str
    body: str
    metadata: dict = field(default_factory=dict)
    source: str = ""


@dataclass
class Chunk:
    index: int
    text: str
    section: list[str]        # heading path, outermost first
    start: int                # character span in Document.body
    end: int


def read_document(path: str | Path) -> Document:
    """A text or Markdown file as a Document; a YAML front matter becomes its metadata."""
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    return parse_document(text, source=str(path), fallback_title=path.stem)


def parse_document(text: str, source: str = "", fallback_title: str = "") -> Document:
    metadata, body = {}, text.replace("\r\n", "\n")
    match = FRONT_MATTER_RE.match(body)
    if match:
        metadata = parse_front_matter(match.group(1))
        body = body[match.end():]
    first_heading = next((m.group(2) for m in map(HEADING_RE.match, body.splitlines()) if m and len(m.group(1)) == 1), "")
    title = clean(str(metadata.get("title") or first_heading or fallback_title or "Document"))
    doc_id = str(metadata.get("video_id") or metadata.get("id") or "") or hashlib.sha1(body.encode("utf-8")).hexdigest()[:12]
    return Document(doc_id=doc_id, title=title, body=body, metadata=metadata, source=source or str(metadata.get("url") or ""))


def parse_front_matter(text: str) -> dict:
    try:
        import yaml
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001 - no PyYAML, or a header that is not YAML: read key: value lines
        data = {}
        for line in text.splitlines():
            key, sep, value = line.partition(":")
            if sep and re.fullmatch(r"[A-Za-z_][\w-]*", key.strip()):
                value = value.strip()
                try:
                    data[key.strip()] = json.loads(value)
                except ValueError:
                    data[key.strip()] = value.strip("\"'")
        return data


def clean(text: str) -> str:
    return " ".join(text.replace("**", "").replace("`", "").split())


def sections_of(body: str, skip: tuple[str, ...] = SKIP_SECTIONS) -> list[tuple[list[str], int, int]]:
    """[(heading path, start, end)] of the text under each heading, in document order (skipped headings left out).

    A "#" line inside a fenced code block is code, not a heading.
    """
    skip_lower = {s.lower() for s in skip}
    path: list[tuple[int, str]] = []
    out: list[tuple[list[str], int, int]] = []
    start, offset, in_fence, skipping = 0, 0, False, False
    for line in body.splitlines(keepends=True):
        if FENCE_RE.match(line):
            in_fence = not in_fence
        match = None if in_fence else HEADING_RE.match(line.rstrip("\n"))
        if match:
            if body[start:offset].strip() and not skipping:
                out.append(([title for _, title in path], start, offset))
            level, title = len(match.group(1)), clean(match.group(2))
            path = [(lvl, t) for lvl, t in path if lvl < level] + [(level, title)]
            skipping = any(t.lower() in skip_lower for _, t in path)
            start = offset + len(line)
        offset += len(line)
    if body[start:offset].strip() and not skipping:
        out.append(([title for _, title in path], start, offset))
    return out


def blocks(body: str, start: int, end: int) -> list[tuple[int, int]]:
    """Spans of the paragraphs between `start` and `end`; a fenced code block is one block, blank lines and all."""
    spans, block_start, in_fence, offset = [], None, False, start
    for line in body[start:end].splitlines(keepends=True):
        blank = not line.strip()
        if FENCE_RE.match(line):
            in_fence = not in_fence
            block_start = offset if block_start is None else block_start
        elif blank and not in_fence:
            if block_start is not None:
                spans.append((block_start, offset))
                block_start = None
        elif block_start is None:
            block_start = offset
        offset += len(line)
    if block_start is not None:
        spans.append((block_start, end))
    return [trim(body, s, e) for s, e in spans if body[s:e].strip()]


def trim(body: str, start: int, end: int) -> tuple[int, int]:
    while start < end and body[start].isspace():
        start += 1
    while end > start and body[end - 1].isspace():
        end -= 1
    return start, end


def split_long(body: str, start: int, end: int, limit: int) -> list[tuple[int, int]]:
    """A block longer than `limit`, as spans cut after a sentence end, else at a line break or space, else hard."""
    spans, code = [], bool(FENCE_RE.match(body[start:end]))
    while end - start > limit:
        window = body[start:start + limit]
        lines = [i + 1 for i, ch in enumerate(window) if ch == "\n"]
        sentences = [] if code else [m.end() for m in SENTENCE_END_RE.finditer(window)]   # code is cut at line ends
        cuts = sentences or lines or [i + 1 for i, ch in enumerate(window) if ch == " "]
        cut = max((c for c in cuts if c > limit // 3), default=limit)
        spans.append(trim(body, start, start + cut))
        start, _ = trim(body, start + cut, end)
    if end > start:
        spans.append((start, end))
    return [s for s in spans if s[1] > s[0]]


def chunk_document(doc: Document, target: int = TARGET_CHARS, limit: int = LIMIT_CHARS, minimum: int = MIN_CHARS,
                   skip: tuple[str, ...] = SKIP_SECTIONS) -> list[Chunk]:
    """Chunks of about `target` characters (never more than `limit`) that stay inside one section."""
    body, chunks = doc.body, []
    for section, start, end in sections_of(body, skip):
        spans = [piece for s, e in blocks(body, start, end) for piece in split_long(body, s, e, limit)]
        packed: list[list[int]] = []
        for s, e in spans:
            if packed and e - packed[-1][0] <= target:
                packed[-1][1] = e
            else:
                packed.append([s, e])
        if len(packed) > 1 and packed[-1][1] - packed[-1][0] < minimum and packed[-1][1] - packed[-2][0] <= limit:
            packed[-2:] = [[packed[-2][0], packed[-1][1]]]
        for s, e in packed:
            chunks.append(Chunk(index=len(chunks), text=body[s:e], section=section, start=s, end=e))
    return chunks
