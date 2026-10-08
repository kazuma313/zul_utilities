---
name: materi-belajar
description: Lesson for one module as a visual HTML page for a beginner - objectives, 3-6 chapters (Apa / Bagaimana / Mengapa penting) with term boxes and step diagrams, an interactive step-by-step demo, summary, multiple-choice quiz, exercises with expected results, and a glossary. Use whenever the user wants material to study - "buatkan materi modul 2", "lanjut modul berikutnya", "bahan ajar", "modul pembelajaran", "pelajaran tentang X", "ajari saya X lengkap dengan kuis/latihan" - or names a module of a syllabus. Pairs with silabus-belajar: with its JSON, the module card is the contract. Runs with a local model through Ollama (the model writes JSON, code builds the page) or with any model that writes the JSON itself.
---

# materi-belajar

Writes one module's lesson. With a syllabus from `silabus_belajar`, the module card is the contract: the page's title, main question, objectives and terms are the card's, word for word, and the card's exercise is the first exercise.

The model only writes the content as one JSON object; code builds the page, so a 4B local model can use this skill:

| Code does | Why it is not left to the model |
|---|---|
| Step diagram per chapter (recipe 1) from 3-5 short steps | SVG coordinates and text widths |
| Interactive demo: the reader clicks through the hardest concept step by step | small models cannot write working JavaScript demos |
| Quiz: the model writes the right answer and two wrong ones as text; code places them | small models count answer positions wrongly and put the right one first |
| Every explanation ends with "Lihat bab N." | so a wrong answer tells the reader what to read again |
| A term box at each term's first appearance, the glossary in order | the rule "istilah baru diberi kotak saat pertama muncul" |
| Report objectives that no chapter teaches or no question tests | the rule "setiap tujuan diuji" |
| Remove links that are not in the sources you gave | a local model has no web search |
| Compute every written calculation again ("400 x Rp1.300 = Rp520.000", also "a = b = c" and the result first) and report a wrong one with the right result | small models write a correct sum in one sentence and a wrong one in the next |
| Limit every text in the schema (`maxLength`) and report a text that reached its limit | qwen3:4b once repeated one sentence until the token limit |

What code cannot check: whether the facts are right, concepts that are mixed up, and numbers written without their calculation. Read the chapters and the quiz before sending the page; the comparison in the docs found wrong concepts in lessons whose arithmetic was right.

## With a local model (Ollama): the script

```
python scripts/generate_materi.py --silabus silabus-reksa-dana.json --module 2 -o reksa-dana-modul-2.html
python scripts/generate_materi.py "Cara kerja bunga majemuk" -o materi-bunga-majemuk.html
python scripts/generate_materi.py --file bab-3.pdf --file foto-catatan.jpg                 # from the learner's material
python scripts/generate_materi.py --silabus s.json --module 2 --from-json jawaban.json      # rebuild without the model
```

`--model auto` (default) takes the first of `RECOMMENDED` in `scripts/generate_materi.py` that the server has; `--model` or `SKILL_MODEL` chooses another; `--api openai --base-url ...` uses an OpenAI-compatible server. `--sources` (lines `Judul | URL`) works as in silabus_belajar.

`--file` (repeatable) is the learner's own material: PDF, images, docx, pptx, xlsx, html, text files, a folder or a link, read by `scripts/read_material.py`. Office files and text PDFs need only the standard library (`pdftotext` or `pypdf` for PDF); images and scanned pages go to a local vision model through Ollama (gemma3:4b, or `VISION_MODEL_ID`), and every file read that way is reported, because a vision model misreads. The model gets the first 12,000 characters and is told to use only their facts. `python scripts/read_material.py FILE` prints what was read.

The last lines list every repair and every rule the checks found broken.

## With a model that writes the JSON itself

Write one object with the fields of `assets/materi.schema.json` (rules in `assets/prompts/system_prompt.txt`; a quiz item may also use `options` + `answer`, a 0-based index), then:

```
python scripts/build_materi.py spec.json --silabus silabus-topik.json --module 2 -o topik-modul-2.html
```

A strong model with web search and an Artifact tool can instead follow `references/SKILL-claude.md`, the original claude.ai workflow that writes the whole page, including custom demos, from `assets/template-materi.html`.

## From Python, or as a tool

```python
from skills.materi_belajar.materi_belajar_skill import generate_materi, build_materi
result = generate_materi(silabus_json="silabus-python.json", module=1)     # local model
result = generate_materi(files=["bab-3.pdf"])                              # from the learner's material
result = build_materi(spec, "python-modul-1.html", "silabus-python.json", 1)
result["path"], result["warnings"]
```

`create_materi(topic, silabus_json, module)` is the LangChain tool (None without langchain-core); it saves under `$LEARNING_OUTPUT_DIR` or `./belajar`.

## Models

See `docs/konsep/model-lokal-untuk-skill-belajar.md` in the repository for the comparison of gemma3:4b, qwen3:4b, qwen3:8b and Claude; `RECOMMENDED` follows it.

Tests without a model: `python -m pytest research/agentic/algorithms/skills/materi_belajar/tests -q -p no:cacheprovider`.
