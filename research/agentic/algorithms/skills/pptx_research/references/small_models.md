# Using this skill with small local models

For models of about 4B to 14B parameters (for example an 8B Qwen) on Ollama, LM Studio, llama.cpp or vLLM.

## Why this skill suits small models

The model never designs anything and never writes code. It fills a fixed JSON shape:
titles, paragraphs, card texts, a few numbers. The builder does the rest:

- sorts the sections into the standard order,
- writes the agenda from the slide titles,
- adds the closing slide, the organization and the tagline,
- shrinks or enlarges text to fit, removes unused cards, people and columns,
- repairs wrong layout names, wrong field names and broken JSON.

So a small model cannot produce an unordered or visually broken deck. What it can still get wrong is the content.

## Bare minimum

1. Python 3.9+, `pip install python-pptx`. No Node.js.
2. A server with JSON Schema constrained output (Ollama `format`, or `response_format: json_schema` on LM Studio, llama.cpp, vLLM).
3. `assets/prompts/system_prompt_lite.txt` with `assets/deck_spec.lite.schema.json` (9 layouts).
4. Context window 8192+ tokens and 4096+ tokens for the answer. Set Ollama's `num_ctx` yourself; the default is small and cuts the prompt silently.
5. Temperature 0.2 to 0.4. Quantisation Q4_K_M or better.
6. **Your material in the prompt** (`--context notes.txt`). A small model has no reliable facts about your study. Without material the prompt tells it to leave the chart slides out.

## One command

```
python scripts/generate_deck.py "Adoption of mobile services in village cooperatives" ^
    --context notes.txt --organization "Universitas X" --presenter "Kurnia" ^
    --language "Bahasa Indonesia" -o proposal.pptx
```

The model is chosen for you: the first of `qwen3:8b`, `gemma3:4b`, `qwen3:4b` that the server has (`--model` or the `SKILL_MODEL` environment variable chooses another). The script prints the model it uses.

OpenAI-compatible servers: add `--api openai --base-url http://localhost:1234/v1 --model <id>`.
`--schema full` uses all 15 layouts (14B+ models). `--save-json deck.json` keeps the model's answer so you can edit it and rebuild with `build_deck.py`.

## Thinking mode

Reasoning tokens make the JSON slower, not better. Prefer instruct variants. For hybrid Qwen3 models add `--qwen-no-think`.
On Ollama `--think off` sends `think: false`; some Ollama versions then stop applying the schema, so the default leaves the parameter out. `<think>` blocks in the answer are removed by the parser.

## Better content

- Two calls: first ask for an outline (section title + key message), check it, then ask for the JSON from that outline.
- Put numbers in the context as a small table. The model copies tables well and invents less.
- Ask for 8 to 10 slides. The answer fits the token budget and the agenda fits its 8 rows.
- Review `AUTO-FIXED / WARNINGS`. "too long" warnings mean the model ignored a length rule; shorten and rebuild.

## Limits code cannot fix

- Generic or wrong statements when no material is given.
- Weaker writing in Indonesian than in English with most small models; short sentences help.
- Long source documents do not fit the context; summarise them in parts first.
