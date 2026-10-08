---
name: silabus-belajar
description: Learning path for one topic as a visual HTML page - final skills, a module map, module cards with a main question, checkable objectives, terms and an exercise, a weekly schedule, a final project and sources, with progress the reader can tick. Use whenever the user wants to learn something step by step or needs a study plan - "buatkan silabus", "kurikulum", "roadmap belajar", "rencana belajar", "learning path", "saya mau belajar X dari nol", "ajari saya X step by step" - even without the words silabus or HTML. Pairs with materi-belajar, which writes each module's lesson from its card. Runs with a local model through Ollama (the model writes JSON, code builds the page) or with any model that writes the JSON itself.
---

# silabus-belajar

Turns "I want to learn X" into a syllabus page. The module cards are the contract for `materi_belajar`: title, main question, objectives, terms and exercise are taken word for word when a module's lesson is written.

The model only writes the content as one JSON object. Code does the rest, so a 4B local model can use this skill:

| Code does | Why it is not left to the model |
|---|---|
| Hours (whole, 1-3 per module), totals and the weekly schedule | small models add up hours wrongly and squeeze the schedule |
| The module map (diagram recipe 9) | SVG coordinates and text widths |
| "Memahami / mengetahui / membahas ..." -> "Menjelaskan ..." | the rule asks for objectives the reader can check |
| Report a term used before the module that teaches it | the rule "bangun bertahap" |
| Report a money topic without a risk or business-model module | the rule for money, product and business topics |
| Remove links that are not in the sources you gave | a local model has no web search and invents URLs |
| Drop a leading "Bisa" from outcomes, write a result that is only a verb from the first objective, remove Markdown | the page already writes "Anda bisa:"; the map needs what the reader can do |

What code cannot check: whether the facts are right, and whether the core concepts of the topic are in a module. In the comparison, NAB was in 2 of 5 gemma3:4b syllabi on mutual funds. Without `--context` or `--sources` the page says that the content comes from the model's general knowledge.

## With a local model (Ollama): the script

```
python scripts/generate_silabus.py "Python untuk analisis data" -o silabus-python.html
python scripts/generate_silabus.py "Reksa dana" --level Pemula --goal "bisa memilih reksa dana sendiri" \
    --hours-per-week 3 --sources sumber.txt --context catatan.md
python scripts/generate_silabus.py "Reksa dana" --from-json jawaban.json       # rebuild without the model
```

`--model auto` (default) takes the first of `RECOMMENDED` in `scripts/generate_silabus.py` that the server has; `--model NAME` or `SKILL_MODEL` chooses another. `--api openai --base-url http://localhost:1234/v1` uses LM Studio or another OpenAI-compatible server. The answer is constrained by `assets/silabus.schema.json`; an answer that cannot be used is sent back with the reason once (`--retries`).

`sumber.txt` holds lines `Judul | URL | dipakai untuk`. `--context` is source text: the model is told to use only its facts.

Output: `silabus-<topic>.html` and `silabus-<topic>.json` (the normalised spec with numbered module cards). The last lines list every repair and every rule the checks found broken; read them before sending the page.

## With a model that writes the JSON itself

Write one object with the fields of `assets/silabus.schema.json` (the rules are in `assets/prompts/system_prompt.txt`), then:

```
python scripts/build_silabus.py spec.json -o silabus-topik.html --hours-per-week 4 [--sources sumber.txt]
```

A strong model with web search and an Artifact tool can instead follow `references/SKILL-claude.md`, the original claude.ai workflow that writes the whole page by hand from `assets/template-silabus.html`.

## From Python, or as a tool

```python
from skills.silabus_belajar.silabus_belajar_skill import generate_silabus, build_silabus
result = generate_silabus("Python untuk analisis data", hours_per_week=4)    # local model
result = build_silabus(spec, "silabus-python.html")                           # JSON written elsewhere
result["path"], result["json"], result["warnings"]
```

`create_silabus(topic, level, goal, hours_per_week)` is the LangChain tool (None without langchain-core); it saves under `$LEARNING_OUTPUT_DIR` or `./belajar` and replies with the paths and the checks.

## After the syllabus

Write module 1 with `materi_belajar`: `python ../materi_belajar/scripts/generate_materi.py --silabus silabus-topik.json --module 1`. The learner came to learn, not only to see a plan.

## Models

See `docs/konsep/model-lokal-untuk-skill-belajar.md` in the repository for the comparison of gemma3:4b, qwen3:4b, qwen3:8b and Claude on these two skills; `RECOMMENDED` follows it.

Tests without a model: `python -m pytest research/agentic/algorithms/skills/silabus_belajar/tests -q -p no:cacheprovider`.
