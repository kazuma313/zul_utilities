---
name: contextual-retrieval
description: Prepare documents for a vector database or RAG with Anthropic's contextual retrieval - split a document into chunks and put a short context in front of each one (which document, source and section it is from, and what it is about) so that embeddings and BM25 find the right chunk. Runs on a local model (Ollama); every context is checked by code and dropped if it adds names or numbers that are not in the document. Use when the user wants notes, Markdown, documentation or YouTube transcripts chunked, contextualized, embedded or loaded into a knowledge base. Output is JSONL, one chunk per line.
---

# contextual-retrieval

Splits documents into chunks and gives every chunk the context it lacks on its own, the method of [Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval): the context is put in front of the chunk before it is embedded and indexed for BM25. The output is meant to be read by other AI systems, so reliability comes first:

| Part | Written by | Why |
|---|---|---|
| Chunks | code | Cut between paragraphs inside one section (Markdown heading or transcript chapter), about 1 000 characters, never more than 1 500. A code block is never cut at a blank line. Every chunk is an exact slice of the document. |
| `header` | code | `Dokumen: <title>. Sumber: <source>. Bagian: <section>.` Always correct, even without a model. |
| `context` | the local model | One or two sentences that situate the chunk. Accepted only if it passes the checks below; otherwise asked once more, and then left out. |

A context is rejected when it has a number or a capitalised name that is not in the text the model was given, copies the chunk, is in the wrong language, or is too short. Preambles ("Berikut adalah konteksnya:"), Markdown and over-long answers are cleaned instead of rejected. So a chunk in the index has either a checked context or none, never an invented one.

## Steps

1. Put the documents in files: Markdown, plain text, or transcripts from the `youtube_transcript` skill (their YAML header becomes metadata, their chapters become sections, and the uploader's description is left out of the chunks).
2. Make sure Ollama runs with a model (see *Models*), then run:

    ```
    python scripts/contextualize.py notes.md transcript.txt -o chunks.jsonl
    python scripts/contextualize.py docs/*.md -o chunks.jsonl --embed nomic-embed-text   # also store vectors
    python scripts/contextualize.py notes.md -o chunks.jsonl --no-llm                    # header only, no model
    ```

3. Read the summary it prints, for example `OK: 102 chunks from 5 documents in 1296 s; 101 with a model context, 1 with the header only`, followed by the reasons contexts were rejected.
4. Load `chunks.jsonl` into the vector database: embed `contextualized_text`, keep `text` for showing the passage, and store the rest as metadata.

From Python:

```python
from skills.contextual_retrieval.contextual_retrieval_skill import contextualize_file, write_jsonl
records = contextualize_file("notes.md")                   # model chosen automatically
write_jsonl(records, "chunks.jsonl")
```

For an agent, `contextualize_document(path, output="")` is the same as a LangChain tool.

## One record

| Field | Content |
|---|---|
| `id` | `<doc_id>#<chunk_index>`; `doc_id` is the YouTube video ID, the front matter `id`, or a hash of the text |
| `text` | the chunk, an exact slice of the document (`start`, `end` are its character span) |
| `header` | code-written: title, source, section |
| `context` | the model's checked sentence, or `""` |
| `contextualized_text` | `header`, `context` and `text`: **what to embed and index** |
| `context_source` | `model` or `none` |
| `checks` | why the model's context was rejected (empty when accepted) |
| `rejected_context` | the rejected sentence, for review; never indexed |
| `section`, `title`, `source`, `metadata` | the heading path; the document's title and file; URL, channel, date, duration, category, language from a transcript header |
| `model`, `attempts`, `seconds` | which model wrote the context and how long it took |
| `embedding`, `embedding_model` | only with `--embed` |

## Models

`--model auto` (the default) takes the first of `RECOMMENDED` in `scripts/contextualize.py` that Ollama has; `--model NAME` or the `SKILL_MODEL` environment variable chooses another. Which model to use, and why, is measured in `references/model_assessment.md`. In short, measured on an RTX 3060 6 GB:

| Model | Seconds per chunk | Judged (1-5) | Use |
|---|---|---|---|
| `qwen3:8b` | 12.7 | 4.49 | the default: most faithful, best form, shortest contexts |
| `gemma3:4b` | 4.9 | 4.22 | many documents: almost twice as fast, more often generic |
| `qwen3:4b` | 7.2 | 4.32 | not as default: most specific, but the most factual errors |

Tell the AI that reads the chunks to treat `context` as a search aid and to quote from `text`: the checks stop invented names and numbers, not every wrong sentence. Reasoning is switched off and the answer is JSON held to a schema, so models that "think" first (qwen3) answer at once.

A document up to 14 000 characters is sent whole with every chunk, as in the article. A longer one is represented by a brief (title, source, the uploader's summary, the section names) and 1 500 characters on each side of the chunk, because a 4-8B model on a laptop has an 8k-token window. Ollama reuses the cached start of the prompt, so the whole-document requests stay fast.

## Options

| Option | Use |
|---|---|
| `--no-llm` | No model: every chunk gets the header only. Seconds for any amount of text. |
| `--embed MODEL` | Also store an embedding of `contextualized_text` (Ollama `/api/embed`; `nomic-embed-text` gets its `search_document:` prefix). |
| `--language Indonesian` | Language of the contexts; by default the document's (from a transcript header, else guessed from common words). |
| `--target`, `--limit` | Chunk size and largest chunk in characters (1 000 and 1 500). |
| `--retries N` | Extra requests for a rejected context (default 1). |
| `--api openai --base-url URL` | LM Studio, llama.cpp or vLLM instead of Ollama. |
| `--verbose` | Print every rejected context with its reason. |

## Measuring

`evals/retrieval_eval.py` scores how often the right chunk is found with embeddings, BM25 and both (rank fusion), for raw chunks, header only, and each model's contexts. `evals/queries.json` holds 83 questions with the evidence that marks their answer. `evals/judge_sheet.py` hides which model wrote which context so a judge can score them blind. The results are summed up in `references/model_assessment.md`.

## Files

| File | Purpose |
|---|---|
| `scripts/chunker.py` | Documents -> chunks with heading path and character span |
| `scripts/contextualize.py` | Chunks -> checked contexts -> JSONL; the CLI |
| `contextual_retrieval_skill.py` | `contextualize_file`, `contextualize_text`, `write_jsonl`, and the LangChain tool `contextualize_document` |
| `evals/retrieval_eval.py`, `evals/queries.json` | Retrieval scores |
| `evals/judge_sheet.py` | A blind judging sheet for several models' contexts, and the summary of the scores |
| `references/model_assessment.md` | Which local model, measured and judged |
| `tests/` | `pytest` tests without a model server |
