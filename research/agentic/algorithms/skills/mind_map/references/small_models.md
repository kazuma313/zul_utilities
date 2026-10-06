# Using this skill with small local models

Short answer: **use a 4B model.** `gemma3:4b` writes a mind map in 8-20 seconds on a 6 GB laptop GPU and passed every test below. The model only has to write an indented outline, or answer a few short questions; everything visual is deterministic Python. What decides the result is not the size of the model but three settings that are easy to get wrong: the reasoning mode, the context window, and which GPU the server uses.

Everything on this page was measured, not estimated: Ollama 0.32.6, Ryzen 7 5800HS, 23 GB RAM, RTX 3060 Laptop 6 GB, 2026-10-03. Run `evals/local_models.py` and `evals/agent_loop.py` to get the same tables for your own model.

## What was measured

`python scripts/generate_mindmap.py <topic or file> --model <model>`, default options:

| Model | Reasoning | Topic | Document, 5 000 characters | Document, 13 700 characters |
|---|---|---|---|---|
| `gemma3:4b` | none | 8-10 s, 8 of 8 | 10-24 s, 4 of 4 | 16-98 s, 4 of 4 (one built step by step) |
| `qwen3:4b` | always on | 159-224 s, 2 of 2 | rule-based fallback after 942 s | not run (see the 5 000 one) |
| `qwen3:8b` | off | 87 s | 181 s | 389 s |

The `qwen3:8b` row was measured on the CPU only (the GPU was not available during that run, about 4 tokens per second), so its times are not comparable; on the GPU the same model generates about 15 tokens per second.

The `qwen3:4b` row was measured before the schema path existed. A model found to need reasoning is now asked for the outline as JSON held to a schema, with reasoning off. Measured that way, `qwen3:4b` mapped a 770 character document in 72 s on the integrated GPU (about 5 tokens per second), with correct numbers. The 5 000 and 13 700 character documents and the topics were not measured again.

As an agent (`evals/agent_loop.py`: SKILL.md in the system prompt, three tools, two tasks):

| Model | How it calls tools | Result |
|---|---|---|
| `gemma3:4b` | one JSON object per turn, held to a schema by the server | 6 of 6, 15-17 s, 2 turns |
| `qwen3:4b` | its own tool calling, reasoning on, 16k context | 3 of 4, 109-355 s per task; the failure claimed the map was done without running anything |
| `qwen3:8b` | its own tool calling, reasoning off | 1 of 2, on the CPU, before the one-command shortcut was added to SKILL.md |

## What goes wrong, and what the scripts do about it

Each line is a failure that was seen with a live model. The repair is in `scripts/outline_repair.py` and `scripts/generate_mindmap.py`.

| Seen | With | What happens now |
|---|---|---|
| The reasoning is written into the answer: "Okay, let's see. The user wants ..." | `qwen3:4b` with reasoning switched off | `--think detect` (default) asks one tiny question first. A model that cannot answer it plainly is allowed to reason, and the server keeps the reasoning out of the answer. |
| Reasoning fills the context window; the answer is empty | `qwen3:4b`, 8 192 context | With reasoning on, the request gets three times the answer room and a context of at least 16 384. An empty answer counts as a problem, not as an outline. It still makes `qwen3:4b` the wrong model for documents: with the larger context it no longer fits the 6 GB GPU, every attempt reasons for minutes, and the 5 000 character document ended in the rule-based fallback after 942 s. |
| Reasoning takes all the time: 26 minutes for one answer to a 770 character document, and the answer was still not finished | `qwen3:4b`, reasoning on, 5 tokens per second | A model that `--think detect` finds to need reasoning is first asked for the outline as JSON held to a schema (`OUTLINE_SCHEMA`), with reasoning off: the server only lets it write the outline. 72 s for the same document. An answer that fails the quality check falls back to the stages below. |
| Rules repeated, a draft, then the outline, then a remark | `qwen3:4b` | Only the last `# title` that is followed by bullets is read (`last_outline_block`). |
| 26 main branches, most of them the same five again | `qwen3:4b` | Siblings with the same text are merged, with their children (parser, every input). |
| 10-13 main branches from a long document | `qwen3:8b` | The model sorts the branch numbers into groups; the script rebuilds the tree (`group_branches`). |
| Sentences, table rows and code copied from the source into the map | `qwen3:8b` given the rule-based draft | Only the section names of the draft are passed on. Code blocks are removed from the source. Sentence-long lines are sent back as a numbered list to be shortened (`shorten_texts`). |
| English branches for an Indonesian document | `qwen3:8b`, `gemma3:4b` | Indonesian and English sources are recognised and the language is named in every request. `--language` sets it by hand. |
| The end of a long document is missing | every model, 12 000 character cut | A source longer than `--max-chars` is read in parts, and the map is built from notes on each part (`take_notes`). `--long-source cut` restores the cut. |
| A file is written although it is not a mind map: the reasoning as 60 nodes, or eight bare sentences and one branch holding everything | `qwen3:4b`, `gemma3:4b` | `outline_problem` checks the tree before it is drawn. If it fails: one more attempt, then the outline is built step by step (branch names first, then 2-4 points per branch), then the rule-based outline with a warning. |

## Options that matter

| Option | Default | Note |
|---|---|---|
| `--model` | `auto` | The first of `gemma3:4b`, `qwen3:8b`, `qwen3:4b` that the server has, else any installed chat model. `SKILL_MODEL` in the environment overrides it. |
| `--think` | `detect` | `off` is about ten times faster (`qwen3:8b`: 47 s instead of 500 s for one topic). `detect` chooses `off` when the model can answer without reasoning and `on` when it cannot. |
| `--steps` | `auto` | `always` builds every outline step by step: slower (about 45 s with `gemma3:4b`), but the tree is balanced by construction. `never` keeps the one-answer outline. |
| `--num-ctx` | 8192 | Ollama context window. The source text, the prompt and the answer must fit. |
| `--max-chars` | 12000 | Source characters per request. A longer source is read in parts. |
| `--language` | the language of the source | Name it (`--language Indonesian`) when the map comes out in the wrong language. |
| `--max-tokens` | 2048 | Enough for 40-60 nodes. |
| `--verbose` | off | Prints every model reply, to see what the model really wrote. |

## The server matters more than the model

- **Check which GPU is used.** On a laptop with an integrated GPU and an NVIDIA GPU, Ollama picked the integrated one (through Vulkan, because it reports more memory): about 6 tokens per second for an 8B model. Started with `OLLAMA_VULKAN=0`, it uses the NVIDIA GPU: 15 tokens per second for `qwen3:8b`, about 75 for a 4B model. `ollama ps` shows the processor in use.
- **A model that fits the GPU is several times faster than one that almost fits.** `qwen3:8b` (6.0 GB with a 4 096 context) is split 30% CPU / 70% GPU on a 6 GB card. `gemma3:4b` (2.9 GB) and `qwen3:4b` (3.9 GB) run entirely on it.
- **Tool calling is not needed.** Ollama refuses tools for `gemma3` ("does not support tools"). A tool call is only a JSON object: send the tool's argument schema as `format`, and the server holds the model's answer to it. That is how `gemma3:4b` made 6 of 6 correct tool calls in 3-8 seconds each (`../evals/small_model_check.py`).

## When you are the model (agent loop)

- For a file from the user, run the one-command shortcut at the top of SKILL.md. It is the path a 4B model completes every time.
- For a topic or pasted text, write the outline: `# root`, `- ` branches, two-space indents. Give 3-8 branches and 2-6 short lines under each.
- Save the outline as a new file ending in `-mindmap.md`. Never write it over the user's file.
- Read the `AUTO-FIXED / WARNINGS` list. `text shortened` means a line was a sentence: shorten it and rebuild.

## Without any model

`python scripts/generate_mindmap.py lesson.txt --no-llm -o lesson.svg` builds an outline by rules (`scripts/outline_from_text.py`): headings, numbered titles and title-case lines become branches, and the sentences under them are ranked by keyword frequency and cut to their first clause. It is rough (leaves are clipped sentences, not summaries), but it is deterministic and instant. It is also the last resort of the model path, so a source file always gets a map.
