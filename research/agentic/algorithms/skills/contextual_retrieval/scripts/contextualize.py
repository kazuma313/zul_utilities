#!/usr/bin/env python3
"""Documents -> contextualized chunks (JSONL) for a vector database: Anthropic's contextual retrieval with a local model.

    python scripts/contextualize.py notes.md transcript.txt -o chunks.jsonl
    python scripts/contextualize.py docs/*.md -o chunks.jsonl --embed nomic-embed-text
    python scripts/contextualize.py notes.md -o chunks.jsonl --no-llm          # header only, no model

Every chunk gets two things in front of it before it is embedded and indexed for BM25:
  header   written by code from the document: title, source, section.  Always right.
  context  one or two sentences from the model that situate the chunk in the document (the method of
           https://www.anthropic.com/engineering/contextual-retrieval).  Checked by code: a sentence with
           a number or a name that is not in the document, a preamble, a copy of the chunk or the wrong
           language is asked again once, and then left out.  A bad sentence never reaches the index.

A document that fits the model's context (up to WHOLE_DOC_CHARS) is sent whole, as in the article; a longer
one is represented by its metadata brief and the text around the chunk, because a 4-8B model on a laptop has
an 8k-token window.  Output: one JSON object per line; `contextualized_text` is what to embed.
Python standard library only; the model runs in Ollama (or any OpenAI-compatible server).
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chunker import LIMIT_CHARS, TARGET_CHARS, Chunk, Document, chunk_document, read_document  # noqa: E402

# Models for writing chunk contexts, best first; set from evals/ (see references/model_assessment.md).
RECOMMENDED = ("qwen3:8b", "gemma3:4b", "qwen3:4b")
USE_CASE = "chunk contexts"

WHOLE_DOC_CHARS = 14000     # documents up to this size go into every request whole, like the article does
WINDOW_CHARS = 1500         # longer documents: this much text before and after the chunk
MAX_WORDS = 60              # a context longer than this is cut to its first sentences
MIN_WORDS = 6
CONTEXT_SCHEMA = {"type": "object", "properties": {"context": {"type": "string"}}, "required": ["context"]}

SYSTEM = ("You help a search engine find passages of documents. For one chunk of a document you write a short "
          "context that says where the chunk belongs: what the document is, which part or speaker the chunk "
          "comes from, and what the chunk is about. You only use facts that are in the document.")

PROMPT = """<document_info>
{brief}
</document_info>
<{doc_tag}>
{document}
</{doc_tag}>
Here is the chunk we want to situate within the whole document. It is from the section: {section}
<chunk>
{chunk}
</chunk>
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk.
Rules: one or two sentences, at most 50 words, written in {language}. Name the document or its speaker and say what this chunk is about. Do not repeat the chunk. Do not add names or numbers that are not in the document. Answer as JSON: {{"context": "..."}}
{language_line}"""

# Said in the language itself: with the rules in English, gemma3:4b answered in English for 2 of 7 Indonesian chunks.
LANGUAGE_LINE = {"Indonesian": "Tulis konteksnya dalam bahasa Indonesia, bukan bahasa Inggris.", "English": "Write the context in English."}

RETRY = ("\n\nYour previous answer could not be used: {problems}. Write the context again, following every rule. {language_line}")

ID_WORDS = {"yang", "dan", "di", "ini", "itu", "dengan", "untuk", "dari", "tidak", "adalah", "pada", "ke", "dalam", "juga",
            "akan", "bisa", "karena", "atau", "membahas", "tentang", "menjelaskan", "bagian", "sebagai", "oleh"}
EN_WORDS = {"the", "and", "of", "to", "is", "in", "that", "this", "it", "for", "with", "as", "on", "are", "about",
            "discusses", "explains", "from", "by", "be", "which"}
# A bare "Konteks" or "Context" is a preamble only before a colon: "Konteks ini berada di ..." is a sentence
# (qwen3:4b wrote 11 of them, and cutting the word left "ini berada di ...").
PREAMBLE_RE = re.compile(r"^\s*(?:(?:(?:here is|here's)(?: the)?(?: succinct)?(?: context)?|sure|certainly|"
                         r"berikut(?: ini)?(?: adalah)?(?: konteks(?:nya)?)?|tentu|baik)\b\s*[:,]?|"
                         r"(?:(?:the |succinct )?context|konteks(?:nya)?)\s*:)\s*", re.I)
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")
# A capitalised word of letters (Rp900 is a number, not a name), not at the start of a sentence.
NAME_RE = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z](?:[^\W\d_]|['’-]){2,}")


# ---------------------------------------------------------------------------
# The document around a chunk
# ---------------------------------------------------------------------------

def language_of(doc: Document) -> str:
    """'Indonesian' or 'English': the metadata's language, else the share of common words in the body."""
    code = str(doc.metadata.get("transcript_language") or doc.metadata.get("spoken_language") or doc.metadata.get("language") or "")
    if code[:2] in ("id", "en"):
        return "Indonesian" if code.startswith("id") else "English"
    words = re.findall(r"[a-z]+", doc.body[:20000].lower())
    return "Indonesian" if sum(w in ID_WORDS for w in words) >= sum(w in EN_WORDS for w in words) else "English"


def source_of(doc: Document, language: str = "English") -> str:
    meta = doc.metadata
    if meta.get("video_id"):
        if language == "Indonesian":
            kind = "siaran langsung YouTube" if meta.get("live_recording") else "video YouTube"
            parts = [f"{kind} {meta.get('channel')}" if meta.get("channel") else kind]
        else:
            kind = "YouTube live stream" if meta.get("live_recording") else "YouTube video"
            parts = [f"{kind} by {meta.get('channel')}" if meta.get("channel") else kind]
        parts += [str(meta[k]) for k in ("upload_date", "duration") if meta.get(k)]
        return ", ".join(parts)
    return Path(doc.source).name if doc.source else ""


def section_of(doc: Document, chunk: Chunk) -> str:
    """The heading path without the parts every chunk shares (the page title, the transcript's "Transcript" heading)."""
    path = [s for s in chunk.section if s and s != doc.title and s.lower() != "transcript"]
    return " > ".join(path)


def header_of(doc: Document, chunk: Chunk, language: str) -> str:
    """The code-written first line of a contextualized chunk."""
    words = ("Dokumen", "Sumber", "Bagian") if language == "Indonesian" else ("Document", "Source", "Section")
    parts = [f"{words[0]}: {doc.title}."]
    source = source_of(doc, language)
    if source:
        parts.append(f"{words[1]}: {source}.")
    section = section_of(doc, chunk)
    if section:
        parts.append(f"{words[2]}: {section}.")
    return " ".join(parts)


def brief_of(doc: Document, chunks: list[Chunk]) -> str:
    """What every request knows about the document: title, source, the uploader's summary, the section names."""
    lines = [f"Title: {doc.title}"]
    source = source_of(doc)
    if source:
        lines.append(f"Source: {source}")
    summary = str(doc.metadata.get("description") or "")
    summary = re.sub(r"^Transcript of the YouTube video .*?\)\.\s*(Video summary:\s*)?", "", summary)
    if summary.strip():
        lines.append(f"Summary: {' '.join(summary.split())[:500]}")
    sections = list(dict.fromkeys(section_of(doc, c) for c in chunks if section_of(doc, c)))
    if sections:
        lines.append("Sections: " + "; ".join(sections[:25]))
    return "\n".join(lines)


def document_view(doc: Document, chunk: Chunk) -> tuple[str, str]:
    """('document', the whole body) when it fits, else ('document_excerpt', the text around the chunk)."""
    if len(doc.body) <= WHOLE_DOC_CHARS:
        return "document", doc.body.strip()
    start, end = max(0, chunk.start - WINDOW_CHARS), min(len(doc.body), chunk.end + WINDOW_CHARS)
    return "document_excerpt", ("..." if start else "") + doc.body[start:end].strip() + ("..." if end < len(doc.body) else "")


# ---------------------------------------------------------------------------
# Checks: what makes a model's sentence unusable
# ---------------------------------------------------------------------------

def tidy(context: str) -> str:
    """Remove what is form, not content: a preamble, quotes, Markdown, line breaks; cut a long answer at a sentence."""
    text = PREAMBLE_RE.sub("", " ".join(str(context or "").split())).replace('\\"', '"')
    # Markdown emphasis and code marks go (gemma3:4b writes *price action*), single underscores stay:
    # build_mindmap.py is a word BM25 should find.
    text = re.sub(r"\*+|__|`", "", text)
    text = re.sub(r"^[#>\s]+", "", text).strip(" \"'“”‘’-")
    if re.match(r"[a-z]+\b(?![._])", text):              # "berikut adalah: ini ..." -> "Ini ...", but not build_mindmap.py
        text = text[0].upper() + text[1:]
    words = text.split()
    if len(words) > MAX_WORDS:
        sentences, kept = re.split(r"(?<=[.!?])\s+", text), []
        for sentence in sentences:
            if kept and len(" ".join(kept + [sentence]).split()) > MAX_WORDS:
                break
            kept.append(sentence)
        text = " ".join(kept)
        if len(text.split()) > MAX_WORDS:
            text = " ".join(text.split()[:MAX_WORDS]).rstrip(",;:") + "…"
    return text


def numbers_in(text: str) -> set[str]:
    """Numbers without their separators: 57.000, 57,000 and 57000 are the same."""
    return {re.sub(r"[.,]", "", n) for n in NUMBER_RE.findall(text)}


def check_context(context: str, chunk: str, known: str, language: str) -> list[str]:
    """Problems that make a context unusable; [] when it may be indexed.  `known` is all the text the model was given."""
    if not context:
        return ["empty"]
    words = context.split()
    problems = []
    if len(words) < MIN_WORDS:
        problems.append("too short")
    unknown_numbers = sorted(numbers_in(context) - numbers_in(known))
    if unknown_numbers:
        problems.append("numbers not in the document: " + ", ".join(unknown_numbers[:3]))
    known_lower = known.lower()
    # Laksana's -> Laksana, AI-nya -> AI (Indonesian -nya, -ku, -mu attach to names too)
    names = [re.sub(r"['’]s$|-(?:nya|ku|mu)$", "", n) for n in NAME_RE.findall(context)]
    names = [n for n in names if n.lower().strip("'’-") not in known_lower]
    if names:
        # Automatic captions misspell names; a model that writes "Ethereum" for the caption's "Etherium" has not
        # invented anything.  A name within a few letters of a word of the document passes.
        vocabulary = {w for w in re.findall(r"[^\W\d_]{4,}", known_lower)}
        names = [n for n in names if not difflib.get_close_matches(n.lower(), vocabulary, n=1, cutoff=0.8)]
    if names:
        problems.append("names not in the document: " + ", ".join(dict.fromkeys(names[:3])))
    if copied(context, chunk):
        problems.append("copies the chunk instead of situating it")
    lower = re.findall(r"[a-z]+", context.lower())
    id_hits, en_hits = sum(w in ID_WORDS for w in lower), sum(w in EN_WORDS for w in lower)
    if language == "Indonesian" and en_hits > id_hits + 1 or language == "English" and id_hits > en_hits + 1:
        problems.append(f"not written in {language}")
    return problems


def copied(context: str, chunk: str, n: int = 4) -> bool:
    """True when most of the context is word-for-word from the chunk (it adds nothing the chunk does not say)."""
    words = re.findall(r"\w+", context.lower())
    if len(words) < n + 3:
        return False
    chunk_text = " ".join(re.findall(r"\w+", chunk.lower()))
    grams = [" ".join(words[i:i + n]) for i in range(len(words) - n + 1)]
    return sum(g in chunk_text for g in grams) / len(grams) > 0.5


# ---------------------------------------------------------------------------
# The model
# ---------------------------------------------------------------------------

def _same_model(installed: str, wanted: str) -> bool:
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())  # noqa: E731
    return norm(installed.split("/")[-1]).startswith(norm(wanted))


def choose_model(args) -> str:
    """The first of RECOMMENDED that the server has (SKILL_MODEL overrides); see the generators of the other skills."""
    if os.environ.get("SKILL_MODEL"):
        return os.environ["SKILL_MODEL"]
    base = (args.base_url or ("http://localhost:11434" if args.api == "ollama" else "http://localhost:1234/v1")).rstrip("/")
    try:
        with urllib.request.urlopen(base + ("/api/tags" if args.api == "ollama" else "/models"), timeout=10) as resp:
            listing = json.loads(resp.read().decode("utf-8"))
    except (OSError, ValueError):
        return RECOMMENDED[0]
    names = [m.get("name") or m.get("id") or "" for m in listing.get("models") or listing.get("data") or []]
    names = [n for n in names if n and "embed" not in n.lower()]
    return next((n for want in RECOMMENDED for n in names if _same_model(n, want)), names[0] if names else RECOMMENDED[0])


def _post(url: str, payload: dict, timeout: int, api_key: str = "local") -> dict:
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def ask_model(args, prompt: str) -> str:
    """The model's context for one prompt.  JSON held to a schema, reasoning off: the answer is the sentence and nothing else."""
    # Ollama cuts a prompt longer than num_ctx from the front, silently; 2.5 characters per token leaves room for
    # Indonesian, which takes more tokens per character than English.
    num_ctx = args.num_ctx or min(16384, max(4096, ((len(SYSTEM) + len(prompt)) * 2 // 5 + 400) // 2048 * 2048 + 2048))
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    if args.api == "ollama":
        base = (args.base_url or "http://localhost:11434").rstrip("/")
        payload = {"model": args.model, "stream": False, "messages": messages, "format": CONTEXT_SCHEMA, "think": False,
                   "options": {"temperature": args.temperature, "seed": 7, "num_ctx": num_ctx, "num_predict": 300}}
        try:
            data = _post(base + "/api/chat", payload, args.timeout)
        except urllib.error.HTTPError as error:
            if error.code != 400:
                raise
            payload.pop("think")                 # a model without a reasoning switch (gemma3) rejects it
            data = _post(base + "/api/chat", payload, args.timeout)
        content = data.get("message", {}).get("content", "")
    else:
        base = (args.base_url or "http://localhost:1234/v1").rstrip("/")
        payload = {"model": args.model, "messages": messages, "temperature": args.temperature, "max_tokens": 300,
                   "response_format": {"type": "json_schema", "json_schema": {"name": "context", "strict": True, "schema": CONTEXT_SCHEMA}}}
        content = _post(base + "/chat/completions", payload, args.timeout, args.api_key)["choices"][0]["message"].get("content") or ""
    return context_from(content)


def context_from(content: str) -> str:
    """The "context" value of the answer, also from broken JSON.

    Seen with gemma3:4b despite the schema: '{"context": "...”}​ 45 words. Total: 68 words.' - the string closed
    with a curly quote and a remark after it.  The text up to that quote is the context.
    """
    try:
        data = json.loads(content)
        return str(data.get("context") or "") if isinstance(data, dict) else str(data)
    except ValueError:
        match = re.search(r'"context"\s*:\s*"(.*?)(?:["”]\s*\}|["”]\s*$)', content, re.S)
        return match.group(1) if match else content  # no JSON at all: the checks decide


def contextualize_chunk(args, doc: Document, chunks: list[Chunk], chunk: Chunk, brief: str, language: str) -> dict:
    """The model's context for one chunk, checked; at most 1 + args.retries requests."""
    doc_tag, view = document_view(doc, chunk)
    language_line = LANGUAGE_LINE.get(language, f"Write the context in {language}.")
    prompt = PROMPT.format(brief=brief, doc_tag=doc_tag, document=view, section=section_of(doc, chunk) or "(start of the document)",
                           chunk=chunk.text, language=language, language_line=language_line)
    known = f"{brief}\n{view}\n{chunk.text}"
    context, problems, attempts = "", ["not asked"], 0
    for attempts in range(1, args.retries + 2):
        try:
            retry = RETRY.format(problems="; ".join(problems), language_line=language_line) if attempts > 1 else ""
            context = tidy(ask_model(args, prompt + retry))
        except (OSError, ValueError, KeyError) as error:
            context, problems = "", [f"model request failed: {error}"]
            continue
        problems = check_context(context, chunk.text, known, language)
        if not problems:
            break
        if args.verbose:
            print(f"   chunk {chunk.index}: {problems} <- {context!r}", file=sys.stderr)
    return {"context": context if not problems else "", "problems": problems, "attempts": attempts,
            "rejected": context if problems else ""}


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

KEEP_METADATA = ("url", "video_id", "channel", "upload_date", "duration", "category", "transcript_language", "captions")


def record_of(doc: Document, chunk: Chunk, n_chunks: int, header: str, outcome: dict, model: str, seconds: float) -> dict:
    context = outcome["context"]
    return {
        "id": f"{doc.doc_id}#{chunk.index}",
        "doc_id": doc.doc_id, "chunk_index": chunk.index, "n_chunks": n_chunks,
        "title": doc.title, "source": doc.source, "section": chunk.section, "start": chunk.start, "end": chunk.end,
        "text": chunk.text,
        "header": header,
        "context": context,
        "context_source": "model" if context else "none",
        "contextualized_text": "\n".join(filter(None, [header, context])) + "\n\n" + chunk.text,
        "model": model if context else "",
        "checks": outcome["problems"] if not context else [],
        "rejected_context": outcome["rejected"],
        "attempts": outcome["attempts"],
        "seconds": round(seconds, 2),
        "metadata": {k: doc.metadata[k] for k in KEEP_METADATA if doc.metadata.get(k)},
    }


def contextualize_document(args, doc: Document, progress=None) -> list[dict]:
    chunks = chunk_document(doc, target=args.target, limit=args.limit)
    language = args.language if args.language != "auto" else language_of(doc)
    brief = brief_of(doc, chunks)
    records = []
    for chunk in chunks:
        started = time.perf_counter()
        if args.no_llm:
            outcome = {"context": "", "problems": [], "attempts": 0, "rejected": ""}
        else:
            outcome = contextualize_chunk(args, doc, chunks, chunk, brief, language)
        records.append(record_of(doc, chunk, len(chunks), header_of(doc, chunk, language), outcome,
                                 args.model, time.perf_counter() - started))
        if progress:
            progress(records[-1])
    return records


def embed(args, records: list[dict], batch: int = 16) -> None:
    """Add an "embedding" to every record: the contextualized text, through Ollama's /api/embed."""
    prefix = "search_document: " if "nomic" in args.embed else ""
    base = (args.base_url or "http://localhost:11434").rstrip("/")
    for i in range(0, len(records), batch):
        group = records[i:i + batch]
        data = _post(base + "/api/embed", {"model": args.embed, "input": [prefix + r["contextualized_text"] for r in group]}, args.timeout)
        for record, vector in zip(group, data["embeddings"]):
            record["embedding"] = vector
            record["embedding_model"] = args.embed


def summary(records: list[dict], seconds: float) -> str:
    with_context = sum(r["context_source"] == "model" for r in records)
    problems: dict[str, int] = {}
    for r in records:
        for p in r["checks"]:
            key = p.split(":")[0]
            problems[key] = problems.get(key, 0) + 1
    lines = [f"OK: {len(records)} chunks from {len({r['doc_id'] for r in records})} documents in {seconds:.0f} s; "
             f"{with_context} with a model context, {len(records) - with_context} with the header only"]
    lines += [f"- {count} rejected: {name}" for name, count in sorted(problems.items(), key=lambda x: -x[1])]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="Markdown or text files; a YAML front matter becomes metadata")
    ap.add_argument("-o", "--output", default="chunks.jsonl")
    ap.add_argument("--model", default="auto", help=f"auto (default): the first of {', '.join(RECOMMENDED)} that the server has")
    ap.add_argument("--no-llm", action="store_true", help="no model: every chunk gets the code-written header only")
    ap.add_argument("--embed", default="", help="also store embeddings, e.g. nomic-embed-text (Ollama)")
    ap.add_argument("--api", choices=["ollama", "openai"], default="ollama")
    ap.add_argument("--base-url")
    ap.add_argument("--api-key", default="local")
    ap.add_argument("--language", default="auto", help="language of the contexts; auto = the document's")
    ap.add_argument("--target", type=int, default=TARGET_CHARS, help="chunk size in characters")
    ap.add_argument("--limit", type=int, default=LIMIT_CHARS, help="largest chunk in characters")
    ap.add_argument("--retries", type=int, default=1, help="extra requests for a context that fails the checks")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--num-ctx", type=int, default=0, help="Ollama context window; 0 = sized to each request")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--verbose", action="store_true", help="print every rejected context")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if args.model == "auto" and not args.no_llm:
        args.model = choose_model(args)
        print(f"model: {args.model} (recommended for {USE_CASE}; --model or SKILL_MODEL chooses another)", file=sys.stderr)
    if args.no_llm:
        args.model = ""
    started, records = time.perf_counter(), []
    try:
        for path in args.files:
            doc = read_document(path)
            print(f"{Path(path).name}: ", end="", file=sys.stderr, flush=True)
            records += contextualize_document(args, doc, progress=lambda r: print("." if r["context"] or args.no_llm else "x",
                                                                                   end="", file=sys.stderr, flush=True))
            print(file=sys.stderr)
        if args.embed:
            embed(args, records)
    except urllib.error.URLError as error:
        print(f"ERROR: cannot reach the model server: {error}\nHINT: start Ollama (`ollama serve`), or use --no-llm")
        return 2
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(summary(records, time.perf_counter() - started))
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
