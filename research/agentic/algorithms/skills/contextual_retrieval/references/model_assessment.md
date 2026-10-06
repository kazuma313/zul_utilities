# Which local model writes the contexts

Measured on 2026-10-06 on a laptop with an RTX 3060 6 GB and Ollama 0.32.6: 102 chunks from 5 documents (three Indonesian YouTube transcripts, two documentation pages). Claude Opus 5.5 judged 34 of them blind. The full report, the documents, every run, and the judge's notes are in the Zul repository under `research/contextual_retrieval_assessment/`.

## Recommendation

| Model | Seconds per chunk | Judged (1-5) | Factual errors | Use |
|---|---|---|---|---|
| `qwen3:8b` | 12.7 | 4.49 | 2 of 34 | Default. Most faithful, cleanest form, shortest contexts (22 words). |
| `gemma3:4b` | 4.9 | 4.22 | 0 of 34 | Large batches. Almost twice as fast; 8 of 34 contexts are generic. |
| `qwen3:4b` | 7.2 | 4.32 | 4 of 33 | Not as default. Most specific, but the most factual errors. |

`RECOMMENDED` in `scripts/contextualize.py` follows this order. `qwen3:8b` does not fit in 6 GB of video memory and runs partly on the CPU, which is why it is the slowest here.

## What to keep in mind

- **The checks stop invented names and numbers, not every wrong sentence.** A sentence built from words that are all in the document passes, for example a year attached to the wrong event or "Rp" before a number that is in dollars. Tell the AI that reads the chunks to treat `context` as a search aid and to quote from `text`. The `header` is written by code and is always correct.
- **On the test documents, contexts did not measurably improve search.** BM25 alone found 95% of the answers in the top five results, because the five documents are about very different subjects. Contexts help most when many chunks look alike. Measure your own collection with `evals/retrieval_eval.py` and your own `queries.json`.
- **`nomic-embed-text` is weak on Indonesian:** 67% in the top five, where BM25 found 95%. Compare a multilingual embedding model such as `bge-m3` with the same script.
