"""Tests without a model server or network for the contextual retrieval skill.

    python -m pytest research/agentic/algorithms/skills/contextual_retrieval/tests -q -p no:cacheprovider
"""

import argparse
import json
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(SKILL / "evals"))
sys.path.insert(0, str(SKILL.parent.parent))
import chunker  # noqa: E402
import contextualize as cx  # noqa: E402
import retrieval_eval as ev  # noqa: E402

TRANSCRIPT = """---
name: trader-sejati
title: "Trader Sejati = Berani CUTLOSS"
channel: "Theresa Learns"
video_id: "Qft-J2LG0NM"
upload_date: "2026-10-04"
duration: "44:10"
transcript_language: "id"
description: "Transcript of the YouTube video \\"Trader Sejati\\" by Theresa Learns (44:10; language id). Video summary: Ngobrol bareng KJo soal trading crypto."
---

## Video description

Gabung komunitas: https://example.org

## Transcript

### 00:00:00 Intro dan Teaser

Ketika aku analisa di technical, kita tuh harus punya parameter. Aku lebih cenderung lihat risk.

### 00:01:30 Awal Mula Masuk Crypto

Aku programmer web developer 2016. Bitcoin dari Rp50 juta satu koinnya sampai jadi Rp300 juta.
"""

MARKDOWN = """# Menyimpan vektor di Milvus

Halaman ini menunjukkan cara membuat collection.

## Menyiapkan helper

1. Pasang Zul:

    ```shell
    pip install "zul[milvus]"

    # bukan judul, ini komentar di dalam kode
    ```

2. Buat helper dari file config.
"""


# ---------------------------------------------------------------------------
# Chunks
# ---------------------------------------------------------------------------

def test_a_transcript_keeps_its_metadata_and_chapters_and_drops_the_video_description():
    doc = chunker.parse_document(TRANSCRIPT)
    assert doc.doc_id == "Qft-J2LG0NM" and doc.title == "Trader Sejati = Berani CUTLOSS"
    chunks = chunker.chunk_document(doc)
    assert [c.section[-1] for c in chunks] == ["00:00:00 Intro dan Teaser", "00:01:30 Awal Mula Masuk Crypto"]
    assert all("example.org" not in c.text for c in chunks)
    assert all(doc.body[c.start:c.end] == c.text for c in chunks)


def test_code_blocks_stay_whole_and_hashes_inside_them_are_not_headings():
    doc = chunker.parse_document(MARKDOWN, source="memakai-milvus.md")
    chunks = chunker.chunk_document(doc, target=60, limit=400, minimum=10)
    sections = {tuple(c.section) for c in chunks}
    assert sections == {("Menyimpan vektor di Milvus",), ("Menyimpan vektor di Milvus", "Menyiapkan helper")}
    code = next(c for c in chunks if "pip install" in c.text)
    assert "# bukan judul" in code.text and code.text.count("```") == 2


def test_long_paragraphs_are_cut_between_sentences_within_the_limit():
    body = "# Judul\n\n" + " ".join(f"Kalimat nomor {i} berisi beberapa kata." for i in range(80))
    doc = chunker.parse_document(body)
    chunks = chunker.chunk_document(doc, target=300, limit=400, minimum=50)
    assert len(chunks) > 5 and all(len(c.text) <= 400 for c in chunks)
    assert all(c.text.endswith(".") for c in chunks)
    assert all(doc.body[c.start:c.end] == c.text for c in chunks)


# ---------------------------------------------------------------------------
# Header, brief and the document a request sees
# ---------------------------------------------------------------------------

def test_the_header_is_written_by_code_in_the_documents_language():
    doc = chunker.parse_document(TRANSCRIPT)
    chunks = chunker.chunk_document(doc)
    assert cx.language_of(doc) == "Indonesian"
    assert cx.header_of(doc, chunks[1], "Indonesian") == (
        "Dokumen: Trader Sejati = Berani CUTLOSS. Sumber: video YouTube Theresa Learns, 2026-10-04, 44:10. "
        "Bagian: 00:01:30 Awal Mula Masuk Crypto.")
    english = cx.header_of(doc, chunks[1], "English")
    assert english.startswith("Document: Trader Sejati") and "YouTube video by Theresa Learns" in english
    brief = cx.brief_of(doc, chunks)
    assert "Summary: Ngobrol bareng KJo soal trading crypto." in brief and "Transcript of the YouTube" not in brief


def test_a_short_document_goes_whole_and_a_long_one_as_the_text_around_the_chunk(monkeypatch):
    doc = chunker.parse_document(TRANSCRIPT)
    chunk = chunker.chunk_document(doc)[1]
    assert cx.document_view(doc, chunk) == ("document", doc.body.strip())
    monkeypatch.setattr(cx, "WHOLE_DOC_CHARS", 100)
    monkeypatch.setattr(cx, "WINDOW_CHARS", 50)
    tag, view = cx.document_view(doc, chunk)
    assert tag == "document_excerpt" and chunk.text in view and len(view) < len(doc.body)


# ---------------------------------------------------------------------------
# What a model answers, and what the checks let through
# ---------------------------------------------------------------------------

KNOWN = TRANSCRIPT + "\nTitle: Trader Sejati\nSource: video YouTube Theresa Learns"


def test_tidy_removes_form_and_keeps_identifiers():
    assert cx.tidy('Berikut adalah konteksnya: **KJo** memakai `build_mindmap.py`') == "KJo memakai build_mindmap.py"
    assert cx.tidy("Konteks: chunk ini dari video KJo.") == "Chunk ini dari video KJo."
    # found by the judge: a sentence that starts with "Konteks ini" lost its first word, *x* kept its asterisks
    assert cx.tidy("Konteks ini berada di bagian Memeriksa hasilnya.") == "Konteks ini berada di bagian Memeriksa hasilnya."
    assert cx.tidy("KJo fokus pada *price action* dan *cut loss*.") == "KJo fokus pada price action dan cut loss."
    assert cx.tidy("build_mindmap.py membuat peta.") == "build_mindmap.py membuat peta."
    long = " ".join(["Kalimat pertama yang cukup panjang."] * 10) + " " + " ".join(["kata"] * 80)
    assert len(cx.tidy(long).split()) <= cx.MAX_WORDS


def test_the_context_is_read_also_from_broken_json():
    assert cx.context_from('{"context": "KJo bercerita."}') == "KJo bercerita."
    assert cx.context_from('{"context": "Bagian ini dari video KJo.”}​ 45 words. Total: 68 words.') == "Bagian ini dari video KJo."
    assert cx.context_from("tanpa JSON") == "tanpa JSON"


@pytest.mark.parametrize("context, problem", [
    ("Dalam podcast Theresa Learns, KJo bercerita bahwa Bitcoin naik dari Rp50 juta.", None),
    ("Dalam podcast Theresa Learns, KJo bercerita bahwa Bitcoin naik ke Rp900 juta.", "numbers not in the document: 900"),
    ("Dalam podcast Theresa Learns, Elon Musk bercerita tentang trading crypto.", "names not in the document: Elon, Musk"),
    ("This chunk is from a Theresa Learns podcast where the guest explains trading.", "not written in Indonesian"),
    ("Aku programmer web developer 2016 dan Bitcoin dari Rp50 juta satu koinnya.", "copies the chunk instead of situating it"),
    ("Podcast trading.", "too short"),
])
def test_checks(context, problem):
    chunk = "Aku programmer web developer 2016. Bitcoin dari Rp50 juta satu koinnya sampai jadi Rp300 juta."
    problems = cx.check_context(context, chunk, KNOWN, "Indonesian")
    assert problems == ([] if problem is None else [problem])


def test_a_possessive_is_not_an_unknown_name():
    assert cx.check_context("Bagian ini dari video Theresa's Learns tentang trading crypto dan risk.", "x", KNOWN, "Indonesian") == []
    # qwen3:4b, chunk 34 of the trading podcast: "pengalaman AI-nya" was rejected as an unknown name
    known = KNOWN + " Aku belajar AI sejak lama."
    assert cx.check_context("KJo menjelaskan sistem kerja trading lalu pengalaman AI-nya sebagai programmer.", "x", known, "Indonesian") == []


def test_a_corrected_spelling_of_a_caption_word_is_not_an_unknown_name():
    known = KNOWN + "\nAku average Etherium aku ngambil di 1000."
    ok = "Dalam podcast Theresa Learns, KJo bercerita cara average posisi Ethereum miliknya."
    assert cx.check_context(ok, "x", known, "Indonesian") == []
    invented = "Dalam podcast Theresa Learns, KJo bercerita cara average posisi Solana miliknya."
    assert cx.check_context(invented, "x", known, "Indonesian") == ["names not in the document: Solana"]


def scripted(*answers):
    """A fake ask_model: the context of each answer in turn (ask_model has already taken it out of the JSON)."""
    calls = []

    def ask(args, prompt):
        calls.append(prompt)
        return answers[min(len(calls), len(answers)) - 1]       # the last answer again once they run out
    return ask, calls


def options(**changes):
    values = dict(model="test-model", no_llm=False, retries=1, verbose=False, target=1000, limit=1500, language="auto")
    values.update(changes)
    return argparse.Namespace(**values)


def test_a_rejected_context_is_asked_again_with_the_reason(monkeypatch):
    ask, calls = scripted("This chunk is from the Theresa Learns podcast about trading and the guest.",
                          "Dalam podcast Theresa Learns, KJo bercerita awal mula masuk crypto sebagai programmer.")
    monkeypatch.setattr(cx, "ask_model", ask)
    doc = chunker.parse_document(TRANSCRIPT)
    records = cx.contextualize_document(options(), doc)
    assert records[0]["context_source"] == "model" and records[0]["attempts"] == 2
    assert "not written in Indonesian" in calls[1] and "Tulis konteksnya dalam bahasa Indonesia" in calls[1]
    assert records[0]["contextualized_text"] == (records[0]["header"] + "\n" + records[0]["context"] + "\n\n" + records[0]["text"])


def test_a_context_that_fails_twice_never_reaches_the_index(monkeypatch):
    bad = "Dalam podcast Theresa Learns, Elon Musk membahas Bitcoin di Rp900 juta."
    ask, calls = scripted(bad, bad, bad, bad)
    monkeypatch.setattr(cx, "ask_model", ask)
    records = cx.contextualize_document(options(), chunker.parse_document(TRANSCRIPT))
    first = records[0]
    assert first["context"] == "" and first["context_source"] == "none" and first["model"] == ""
    assert first["contextualized_text"] == first["header"] + "\n\n" + first["text"]
    assert any(p.startswith("names not in the document") for p in first["checks"])
    assert "Elon" in first["rejected_context"] and len(calls) == 4


def test_without_a_model_every_chunk_gets_the_header_only(monkeypatch):
    monkeypatch.setattr(cx, "ask_model", lambda args, prompt: pytest.fail("no model may be asked"))
    records = cx.contextualize_document(options(no_llm=True, model=""), chunker.parse_document(TRANSCRIPT))
    assert len(records) == 2 and all(r["context"] == "" and r["checks"] == [] for r in records)
    assert {"id", "doc_id", "section", "start", "end", "header", "contextualized_text", "metadata"} <= set(records[0])
    assert records[0]["metadata"]["channel"] == "Theresa Learns"


def test_the_skill_works_without_a_model_server():
    from skills.contextual_retrieval import contextual_retrieval_skill as skill

    records = skill.contextualize_text(MARKDOWN, title="Milvus", use_model=False)
    assert records and records[0]["header"].startswith("Dokumen: Menyimpan vektor di Milvus.")
    assert skill.contextualize_document is not None and skill.contextualize_document.name == "contextualize_document"


# ---------------------------------------------------------------------------
# Retrieval scores
# ---------------------------------------------------------------------------

def test_bm25_fusion_and_recall():
    texts = ["kerokan dan arteri karotis di leher", "harga bitcoin naik", "cara memasang milvus"]
    bm25 = ev.BM25(texts)
    assert ev.ranking(bm25.scores("arteri karotis"))[0] == 0
    assert ev.fuse([2, 1, 0], [1, 2, 0])[:2] in ([2, 1], [1, 2])
    m = ev.metrics([0, 2, None, 5])
    assert m["recall@1"] == 0.25 and m["recall@3"] == 0.5 and m["recall@10"] == 0.75
    assert m["mrr@10"] == pytest.approx((1 + 1 / 3 + 1 / 6) / 4)


def test_the_questions_have_one_answer_chunk_each_in_their_own_file():
    data = json.loads((SKILL / "evals" / "queries.json").read_text(encoding="utf-8"))
    kinds = {q["type"] for q in data["queries"]}
    assert len(data["queries"]) >= 80 and kinds == {"situated", "content", "paraphrase"}
    assert all(q["q"].strip() and q["evidence"].strip() for q in data["queries"])
