# Which local model should write chunk contexts?

The `contextual_retrieval` skill splits a document into chunks and puts a short context in front of each chunk before it goes into a vector database. Code writes a `header` (title, source, section), and a local model writes one or two sentences about the chunk. Other AI systems will read the result, so the question is: **which local model writes contexts that can be trusted, at a usable speed, on an RTX 3060 6 GB laptop?**

## Answer

- **Use `qwen3:8b` by default.** It made the best contexts overall, but it is the slowest.
- **Use `gemma3:4b` for large batches.** It is almost twice as fast and made no factual errors in the sample, but its sentences are more often generic.
- **Avoid `qwen3:4b` as the default.** It made the most factual errors.
- **Whatever the model:** keep the code-written `header`, and tell the AI that reads the chunks to quote from `text`, not from `context`.

The skill already uses this order: `RECOMMENDED = ("qwen3:8b", "gemma3:4b", "qwen3:4b")` in `scripts/contextualize.py`.

## Results

102 chunks from 5 documents. Claude Opus 5.5 judged 34 of them without knowing which model wrote which sentence.

| | `qwen3:8b` | `gemma3:4b` | `qwen3:4b` |
|---|---|---|---|
| Verdict | default | large batches | not as default |
| Seconds per chunk (median) | 12.7 | 4.9 | 7.2 |
| Time for all 102 chunks | 21.6 min | 11.5 min | 12.1 min |
| Chunks with an accepted context | 101 of 102 | 102 of 102 | 101 of 102 |
| Judge score, 1 to 5 (mean of 4 criteria) | **4.49** | 4.22 | 4.32 |
| Sentences with a factual error | 2 of 34 | **0 of 34** | 4 of 33 |
| Generic sentences (don't say what the chunk is about) | 2 of 34 | 8 of 34 | **1 of 33** |
| Sentences that name no source | 0 of 34 | 0 of 34 | 4 of 33 |

`qwen3:8b` is slow here because it is 6.3 GB and doesn't fit in 6 GB of video memory: Ollama ran it 32% on the CPU. On a GPU with 8 GB or more it is faster.

## Each model in short

**`qwen3:8b`**
- Good: most faithful to the document, cleanest form, and the shortest sentences (22 words). The checks caught it twice adding something from outside the text it was given. It added "Fibonacci", which was outside its window, and the retry fixed that. It added "Musk" when the transcript only says "si Elon", and it repeated the name on the retry, so that chunk kept only its header.
- Bad: about 3.5 hours for 1 000 chunks. Two errors that the checks can't catch: it dated a market crash to 2021 when the speaker says it was the Terra Luna crash, and it reversed one statement.
- Use it for up to a few hundred chunks, or run it overnight.

**`gemma3:4b`**
- Good: fastest, never failed to give an acceptable context, no factual error in the sample, and always names the source.
- Bad: 8 of 34 sentences repeat the section title or the story of the whole video instead of saying what this chunk is about. It also wrote Markdown such as `*price action*`, which the cleaner now removes.
- Use it when there are many documents, or when the GPU is needed for other work.

**`qwen3:4b`**
- Good: the most specific sentences.
- Bad: 4 factual errors in 33. It wrote "Rp1.000" for an account of 1 000 dollars, and it called the guest the host. It presented a doctor's "possible in the future" as a fact, and it gave smoking and coffee as causes of high blood pressure, which the chunk does not say. 4 of its sentences name no source at all.
- If you use it, check a sample of its output by hand.

## Three things to know

1. **The checks stop invented names and numbers, not every wrong sentence.** A sentence built from words that are all in the document still passes, for example a year attached to the wrong event or "Rp" put before a number that is in dollars. That is why the reading AI should quote from `text`.
2. **On these five documents, the contexts did not measurably improve search.** BM25 alone already finds 95% of the answers in the top five results, because the documents are about very different subjects. Against the raw chunks, every model's contexts won a few questions and lost about as many. Contexts help most in a large collection where many chunks look alike, so measure your own collection before you count on a gain.
3. **The embedding model is the weaker part.** `nomic-embed-text` finds only 67% of the answers in the top five where BM25 finds 95%, because it is weak on Indonesian. A multilingual model such as `bge-m3` is worth testing with the same script.

Recall@5 (share of the 83 questions whose chunk is in the top five results):

| What was indexed | Embeddings | BM25 | Both (hybrid) |
|---|---|---|---|
| raw chunks | 0.67 | 0.95 | 0.89 |
| header + chunk | 0.66 | 0.94 | 0.87 |
| `qwen3:8b` context | 0.70 | 0.93 | 0.88 |
| `gemma3:4b` context | 0.65 | 0.95 | 0.84 |
| `qwen3:4b` context | 0.66 | 0.95 | 0.84 |

One question is 0.012, so these differences are a few questions either way.

## How it was tested

- **Documents** (`corpus/`): three Indonesian YouTube transcripts from the `youtube_transcript` skill (a crypto-trading podcast, a health Q&A, a talk on uncertainty) and two pages of the Zul docs (Milvus, mind maps). The two long transcripts were too big to send whole, so their chunks got a summary of the video and the text around the chunk.
- **Same settings for every model:** temperature 0, seed 7, reasoning off, answer forced to JSON, one retry after a rejected sentence.
- **Judging** (`judge/`): every third chunk, with the three sentences under shuffled labels A, B, C, scored 1 to 5 on four criteria:
    - *faithful*: everything is in the document
    - *situates*: names the document, speaker or section
    - *specific*: says what this chunk is about
    - *form*: right language, short, no filler

  Every claim not in the chunk was looked up in the document. `judge/scores.json` has a note for every score below 5, and `judge/key.json` reveals the labels.
- **Search** (`results/`): 83 questions in `queries.json` (written by Claude Fable 5.1 before any context existed), searched with embeddings, BM25, and both combined.

Judge scores per criterion:

| | `qwen3:8b` | `gemma3:4b` | `qwen3:4b` |
|---|---|---|---|
| faithful | 4.74 | 4.59 | 4.45 |
| situates | 4.03 | 4.21 | 4.09 |
| specific | 4.47 | 3.97 | 4.61 |
| form | 4.71 | 4.12 | 4.12 |

## Limits

- The sample is small: 5 documents, 102 chunks, 34 judged. One error more or less moves a model's error rate by about 3 points.
- There was one judge. The notes in `judge/scores.json` let someone else check every low score.
- The speeds hold for this laptop only.

## Fixed after the run

The judging found three problems in the cleaning code, not in the models. They are fixed in the skill and covered by tests. The recorded contexts were not generated again, so the numbers in this report still include these three problems.

- `qwen3:4b` wrote 11 sentences starting with "Konteks ini ...", and the cleaner cut the first word, leaving "ini ...".
- Single asterisks (`*price action*`) were not removed.
- "AI-nya" was rejected as an unknown name; Indonesian suffixes are now ignored.

## What's in this folder

| Path | Content |
|---|---|
| `corpus/` | the 5 documents |
| `queries.json` | the 83 search questions, each with the text that marks its answer |
| `runs/` | one JSONL file per variant: `header.jsonl` (no model) and one per model, with every chunk, header, context and check result |
| `logs/` | what each model run printed, including every rejected sentence and why |
| `judge/` | `sheet.md` (what the judge saw), `key.json` (which label is which model), `scores.json` (scores and notes), `summary.json` (totals) |
| `results/retrieval.json` | search scores per variant, method and question type, with the rank of every question |
| `archive/` | earlier `gemma3:4b` runs: a 16-chunk first trial, a full run with older checks (it rejected "Ethereum" because the captions spell "Etherium", which led to the fuzzy name match), and a 9-chunk check after the fixes |
| `run_models.sh` | runs everything again into `rerun/` |

## Run it again

You need Ollama running with `gemma3:4b`, `qwen3:4b`, `qwen3:8b` and `nomic-embed-text`. From this folder, run:

```bash
bash run_models.sh
```

The script writes into `rerun/` and leaves the recorded results alone. It takes about 50 minutes on an RTX 3060 6 GB. To judge the new sheet, score `rerun/judge/sheet.md` into `rerun/judge/scores.json`, then run:

```bash
uv run python ../agentic/algorithms/skills/contextual_retrieval/evals/judge_sheet.py score --out rerun/judge
```
