# Using this skill with small local models

For models of about 4B to 14B parameters (for example an 8B Qwen) on Ollama, LM Studio, llama.cpp or vLLM.

## Why it works

The model writes only the content: eight short titles, a few paragraphs, some numbers. The script draws the poster, orders the sections, chooses icons, draws the charts, writes the chart takeaway and shrinks text that is too long. Wrong type names, wrong field names, text around the JSON and cut-off JSON are repaired and reported. The model cannot break the layout; it can only write weak content.

## Bare minimum

1. Python 3.9+ (Pillow optional). Microsoft Edge or Chrome for PDF/PNG; without a browser you still get the HTML.
2. A model server with JSON Schema constrained output (Ollama `format`, or `response_format: json_schema`).
3. `assets/prompts/system_prompt_lite.txt` with `assets/poster.lite.schema.json`.
4. Context window 8192+ tokens and 4096+ tokens for the answer (set Ollama's `num_ctx` yourself).
5. Temperature 0.2 to 0.4. Quantisation Q4_K_M or better.
6. **Your numbers in the prompt** (`--context notes.txt`). Without material the prompt tells the model to leave the stats and chart sections out, and the poster has no analytics.

## One command

```
python scripts/generate_poster.py "Consumer behaviour of urban shoppers in Medan" ^
    --context survey_summary.txt --organization "Universitas X" ^
    --contact "hello@example.org | www.example.org" --language "Bahasa Indonesia" -o poster.pdf --png
```

The model is chosen for you: the first of `qwen3:8b`, `gemma3:4b`, `qwen3:4b` that the server has (`--model` or the `SKILL_MODEL` environment variable chooses another). The script prints the model it uses.

OpenAI-compatible servers: `--api openai --base-url http://localhost:1234/v1 --model <id>`.
`--schema full` adds the `list` type, icons and images (14B+ models). `--save-json poster.json` keeps the answer so you can edit it and rebuild with `build_poster.py`.

## Thinking mode

Prefer instruct variants; add `--qwen-no-think` for hybrid Qwen3 models. On Ollama `--think off` sends `think: false`, but some Ollama versions then ignore the schema, so the default leaves the parameter out. `<think>` blocks in the answer are removed by the parser.

## Better posters

- Put the numbers in the context as a short table (label, value). Small models copy tables well and invent less.
- Ask for 6 sections when the material is thin; 8 sections make the text small.
- Two calls: first an outline (8 titles + one line each), then the JSON from the outline.
- Read the warnings. "will be shrunk" means a text is over the limit: cut it and rebuild.
