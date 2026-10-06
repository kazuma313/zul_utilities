# Using this skill with small local models

Written for models in the 4B to 14B range (for example an 8B Qwen) running on a
PC through Ollama, LM Studio, llama.cpp or vLLM.

## What a small model can and cannot do here

| Task | ~8B model | Notes |
|---|---|---|
| Fill a fixed JSON shape with slide text | reliable with a schema | this is all the skill asks of the model |
| Choose sensible layouts from 8 options | good | use the lite prompt and lite schema |
| Choose from all 20 layouts, nested fields, icons | fair | field-name mistakes are common; the normaliser repairs most |
| Read SKILL.md, write a file, run a shell command, read the result (agent mode) | unreliable | works with 14B+ tool-tuned models and a good agent harness |
| Write pptxgenjs or python-pptx code directly | poor | never ask for this; it is the reason the engine exists |
| Accurate facts and numbers from memory | poor | always pass source text with `--context` |

So: **do not run a small model as a free agent that reads this skill.**
Let your program call the model once for JSON and then call the engine.
`scripts/generate_deck.py` does exactly that.

## Bare minimum

1. Python 3.9+ and Node.js 18+.
2. `npm install pptxgenjs` in the skill folder. Nothing else is required. Icons are optional.
3. A model server that supports **JSON Schema constrained output**
   (Ollama `format`, LM Studio / llama.cpp / vLLM `response_format: json_schema`).
4. The **lite** prompt and schema: `assets/prompts/system_prompt_lite.txt` and `assets/slide_spec.lite.schema.json` (8 layouts).
5. Context window of 8192 tokens or more, and at least 4096 tokens for the answer.
   Ollama's default context is small; set `num_ctx` explicitly or the prompt is silently cut.
6. Low temperature (0.2 to 0.4).
7. Quantisation Q4_K_M or better. Below 4 bits, JSON discipline drops quickly.

With these seven points an 8B model produces a valid deck almost every time, because
the grammar makes invalid JSON impossible and the engine repairs the rest.

## One command

```
ollama pull qwen3:8b
python scripts/generate_deck.py "Onboarding plan for new sales staff" --slides 8 -o onboarding.pptx
```

The model is chosen for you: the first of `qwen3:8b`, `gemma3:4b`, `qwen3:4b` that the server has (`--model` or the `SKILL_MODEL` environment variable chooses another). The script prints the model it uses.

LM Studio, llama.cpp server or vLLM:

```
python scripts/generate_deck.py "Onboarding plan" --api openai --base-url http://localhost:1234/v1 --model <model-id> -o onboarding.pptx
```

With source material, in Indonesian, forcing a theme:

```
python scripts/generate_deck.py "Ringkasan laporan tahunan" --context laporan.txt --language "Bahasa Indonesia" --theme forest -o laporan.pptx
```

## Thinking mode (Qwen3 and similar)

Reasoning tokens make deck JSON slower, not better.

- Instruct / non-thinking variants are the best fit.
- Hybrid Qwen3 models: add `--qwen-no-think` (appends `/no_think`).
- Ollama: `--think off` sends `think: false`. Some Ollama versions stop applying the
  JSON schema in that combination (ollama issue 15260), so the default is `--think auto`,
  which leaves the parameter out. If you use `--think off`, check that the output is still valid JSON.
- If the model still thinks, the `<think>...</think>` block is removed by the parser. Give it enough `--max-tokens`.

## Calling the model yourself

Ollama:

```python
import json, urllib.request, sys
sys.path.insert(0, "scripts")
from create_pptx import create_pptx, format_result

schema = json.load(open("assets/slide_spec.lite.schema.json"))
system = open("assets/prompts/system_prompt_lite.txt", encoding="utf-8").read()
body = {"model": "qwen3:8b", "stream": False, "format": schema,
        "options": {"temperature": 0.3, "num_ctx": 16384, "num_predict": 8192},
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": "Topic: Remote work policy\nNumber of slides: 7"}]}
req = urllib.request.Request("http://localhost:11434/api/chat", json.dumps(body).encode(),
                             {"Content-Type": "application/json"})
answer = json.load(urllib.request.urlopen(req, timeout=900))["message"]["content"]
print(format_result(create_pptx(answer, "remote_work.pptx")))
```

OpenAI-compatible servers: send
`"response_format": {"type": "json_schema", "json_schema": {"name": "deck", "strict": true, "schema": schema}}`.

`create_pptx()` accepts the wrapper object `{"theme": ..., "slides": [...]}` directly and
takes the theme from it.

## Tool calling instead of structured output

If your agent framework registers `create_pptx_js` as a tool (see `references/integration.md`):

- Put `system_prompt_lite.txt` in the system prompt. The tool description alone is not enough for an 8B model.
- The `slides` argument is a JSON array inside a JSON string. Small models often break the
  escaping. The engine accepts a real list as well, so if your framework allows it, declare `slides` as an array.
- Return the tool result text unchanged. It starts with `OK:` or `ERROR:` and lists repairs,
  which lets the model retry once with a fix.
- Cap retries at 1 or 2. A small model that fails twice will not succeed the third time.

## Better decks from small models

- **Two calls instead of one.** First: "List 8 slide titles with one key message each." Second: "Turn this outline into the JSON." Each step is easier than both together.
- **Give the facts.** `--context file.txt`. Without source text the prompt forbids invented numbers, so you get text-only slides.
- **Ask for fewer slides.** 6 to 8 good slides beat 15 thin ones, and the answer fits the token budget.
- **Use the full schema only with 14B+ models.** `--schema full` adds 12 layouts and icons; the grammar is larger and slower, and small models choose layouts less sensibly.
- **Check the result.** `python scripts/render_preview.py deck.pptx --grid` writes one overview image.

## What the engine repairs on its own

See "Accepted alternatives" in `references/layouts.md`. In short: text around the JSON,
think blocks, code fences, trailing commas, cut-off output, wrong layout names, wrong
field names, strings instead of lists, too many items, invalid colours and icon names,
chart numbers given as strings, control characters that would corrupt the file.

## Limits you cannot fix with code

- Content quality. An 8B model writes generic text unless you give it material.
- Long inputs. A 30-page report does not fit; summarise it in chunks first.
- Language. Quality in Indonesian is lower than in English for most small models; keep sentences short.
