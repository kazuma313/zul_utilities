"""Contextual retrieval skill: documents -> chunks with a context in front, ready for a vector database.

    from skills.contextual_retrieval.contextual_retrieval_skill import contextualize_file
    records = contextualize_file("notes.md")                 # local model through Ollama
    records = contextualize_file("notes.md", use_model=False) # code-written header only, no model
    records[0]["contextualized_text"]                         # what to embed and index for BM25

Each record is one chunk (see SKILL.md for every field).  The header (title, source, section) is written by
code; the context sentence by a local model, and only when it passes the checks in scripts/contextualize.py.
`contextualize_document` is the same as a LangChain tool; it is None without langchain-core.
"""

import argparse
import importlib
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent / "scripts"


def _load(required, optional=()):
    """Import this skill's scripts without leaving their names behind (the other skills share module names)."""
    own = {p.stem for p in _SCRIPTS.glob("*.py")}
    aside = {name: sys.modules.pop(name) for name in own if name in sys.modules}
    sys.path.insert(0, str(_SCRIPTS))
    loaded = {}
    try:
        for name in required:
            loaded[name] = importlib.import_module(name)
        for name in optional:
            try:
                loaded[name] = importlib.import_module(name)
            except ImportError:
                loaded[name] = None
    finally:
        for name in own:
            sys.modules.pop(name, None)
        sys.modules.update(aside)
        while str(_SCRIPTS) in sys.path:
            sys.path.remove(str(_SCRIPTS))
    return loaded


_m = _load(["chunker", "contextualize"])
_chunker, _cx = _m["chunker"], _m["contextualize"]


def _options(model: str, use_model: bool, base_url: str, embed: str, language: str) -> argparse.Namespace:
    args = argparse.Namespace(model=model, no_llm=not use_model, api="ollama", base_url=base_url or None, api_key="local",
                              language=language or "auto", target=_chunker.TARGET_CHARS, limit=_chunker.LIMIT_CHARS,
                              retries=1, temperature=0.0, num_ctx=0, timeout=600, verbose=False, embed=embed)
    if use_model and model in ("", "auto"):
        args.model = _cx.choose_model(args)
    if not use_model:
        args.model = ""
    return args


def contextualize_text(text: str, title: str = "", source: str = "", model: str = "auto", use_model: bool = True,
                       base_url: str = "", embed: str = "", language: str = "") -> list[dict]:
    """Chunks of one document given as text (Markdown, plain text, or a transcript file with a YAML header)."""
    doc = _chunker.parse_document(text, source=source, fallback_title=title)
    args = _options(model, use_model, base_url, embed, language)
    records = _cx.contextualize_document(args, doc)
    if embed:
        _cx.embed(args, records)
    return records


def contextualize_file(path: str, model: str = "auto", use_model: bool = True, base_url: str = "", embed: str = "",
                       language: str = "") -> list[dict]:
    """Chunks of one file, with its YAML front matter (if any) as metadata."""
    doc = _chunker.read_document(path)
    args = _options(model, use_model, base_url, embed, language)
    records = _cx.contextualize_document(args, doc)
    if embed:
        _cx.embed(args, records)
    return records


def write_jsonl(records: list[dict], path: str) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    return out


def _contextualize_document(path: str, output: str = "") -> str:
    """Split a document into chunks for a vector database and give every chunk a context, with a local model.

    Use it when the user wants a document (Markdown, text, or a YouTube transcript file) prepared for
    retrieval, RAG, a knowledge base or a vector database. Writes one JSON line per chunk; the field
    "contextualized_text" is what to embed. Returns where the file is and how many chunks got a context.

    Args:
        path: The document file on disk.
        output: Where to write the JSONL file; empty: next to the document, ending in .chunks.jsonl.
    """
    try:
        records = contextualize_file(path)
    except FileNotFoundError:
        return f"File not found: {path}"
    except OSError as error:
        return f"Could not prepare {path}: {error}. Is the model server (Ollama) running?"
    out = write_jsonl(records, output or str(Path(path).with_suffix(".chunks.jsonl")))
    return _cx.summary(records, sum(r["seconds"] for r in records)) + f"\nwritten: {out}"


try:
    from langchain_core.tools import StructuredTool
except ImportError:  # pragma: no cover - the plain functions above work without LangChain
    contextualize_document = None
else:
    contextualize_document = StructuredTool.from_function(_contextualize_document, name="contextualize_document")


__all__ = ["contextualize_text", "contextualize_file", "write_jsonl", "contextualize_document"]
