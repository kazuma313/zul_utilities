---
name: mind-map
description: Draw a mind map (PNG, SVG, PDF, interactive HTML, Markdown or Mermaid) from anything the user gives you - a lesson, chapter, article, notes, a PDF/DOCX file or just a topic. Central topic in the middle, coloured main branches, sub points and details on curved lines, five colour themes, radial or left-to-right layout. Use when the user asks for a mind map, peta pikiran, peta konsep, concept map, ringkasan bercabang or a visual summary of study material. You write a short indented outline; the script lays it out and draws it. Needs Python 3.9+ only for SVG/HTML/MD; PNG/PDF need Edge, Chrome or Chromium.
---

# mind-map

You read the material and write an **outline**; the script measures the text, lays out the tree and draws it. Never draw SVG or HTML yourself.

## Steps

Shortcut for a file from the user (`.txt .md .docx .pdf .html`) when a local model server (Ollama) is running: one command reads the file, gets the outline from the local model, repairs it and draws the map. It is the safest path for a small model and for a long file.

```
python scripts/generate_mindmap.py notes.md -o notes-mindmap.svg
```

Then read the output (step 4). If it prints `cannot reach the model server`, or for a topic or pasted text, write the outline yourself:

1. Read what the user gave: pasted text, a topic, or a file. Read a file with `python scripts/extract_text.py <file>`.
2. Write the outline (format below) and save it as a **new** file whose name ends in `-mindmap.md`, for example `lesson-mindmap.md`. The user's own file is the source, not the outline: never overwrite it and never pass it to `build_mindmap.py`. Root = the central topic, 3-8 main branches = the key ideas, under each 2-6 short sub points, optionally one more level of details. Every node is a phrase of at most 8 words, not a sentence.
3. Run:
   ```
   python scripts/build_mindmap.py lesson-mindmap.md -o lesson.png --also svg
   ```
   `-o map.svg` needs no browser, `-o map.html` gives a pan/zoom page with a Save PNG button, `-o map.pdf` prints it, `-o map.mmd` writes Mermaid, `-o map.md` writes the cleaned outline.
4. Read the output.
   - `OK: created <path> (N nodes, B branches, depth D, WxH px, theme=...)` means success. Tell the user the path.
   - `AUTO-FIXED / WARNINGS` lists repairs (branch cut to 8, children cut to 6, long text moved into a note, unknown theme). Fix the outline and run again if the repair changed the meaning.
   - `ERROR:` means nothing was made. Follow the `HINT`, fix the outline, run again (one retry).
5. No model at all? `python scripts/generate_mindmap.py lesson.pdf --no-llm -o lesson.svg` builds a rule-based outline. The local model is chosen for you (`gemma3:4b` if the server has it, else `qwen3:8b`, else `qwen3:4b`); `--model` names another. A source longer than one request is read in parts.

If you have a tool named `create_mind_map`, call it with the outline as a string: `create_mind_map(outline="# Topic\n- Branch\n  - Leaf", filename="map.png", theme="rainbow")`.

## Outline format

```
# Fotosintesis
- Pengertian
  - Tumbuhan membuat makanan sendiri
  - Energi cahaya menjadi energi kimia
- Bahan
  - Cahaya matahari
  - Air dari akar
  - CO2 dari stomata
- Tahapan
  - Reaksi terang
    - Di tilakoid
    - Menghasilkan ATP, NADPH, O2
  - Reaksi gelap
    - Siklus Calvin di stroma
- Hasil
  - Glukosa
  - Oksigen
```

- Line 1: `# ` + the central topic (2-5 words).
- `- ` at the start of a line = main branch. Two more spaces per level = sub point, detail. `##` / `###` headings and `1.` numbered lists work too.
- A note in parentheses at the end of a line, `- Reaksi terang (di tilakoid)`, is drawn small and grey under the node.
- Also accepted: JSON `{"title": "...", "theme": "blue", "root": "Topic", "nodes": [{"text": "Branch", "children": [{"text": "Leaf"}]}]}` (keys `name/label/title` and `children/items/subtopics` are understood) and a Mermaid `mindmap` block. Full spec: `references/formats.md`.

## Rules

1. 3 to 8 main branches, 2 to 6 children per node, at most 3 levels below the root. More is cut (with a warning); fewer than 3 branches looks empty.
2. Node text: keywords, names, numbers, steps, causes, examples; at most 8 words. Sentences become notes or are wrapped over several lines and look heavy.
3. Use only what is in the material. Keep the material's order and grouping; do not add outside facts.
4. Balanced tree: similar numbers of children under each branch. One branch with 6 children and the others with 1 looks lopsided.
5. Write in the user's language. Plain text only: no `**bold**`, no emojis, no numbering inside the text.
6. Options: `--theme rainbow|blue|pastel|dark|mono` (rainbow = a different colour per branch), `--layout radial|right` (radial = branches on both sides, right = tree growing to the right, better for step-by-step material), `--title "..."` (small caption in the corner), `--font-scale 0.6-2.0`.

## Files

| Path | Purpose |
|---|---|
| `scripts/build_mindmap.py` | Outline/JSON/Mermaid -> SVG, HTML, PNG, PDF, MD, MMD, JSON. CLI and Python function `build_mindmap()` |
| `scripts/outline_parser.py` | Reads the three input forms, repairs and limits the tree (used automatically) |
| `scripts/render_svg.py` | Layout and drawing (used automatically) |
| `scripts/font_metrics.py` | Glyph widths of Poppins for text wrapping (used automatically) |
| `scripts/extract_text.py` | `.docx .pdf .html .txt .md` or a folder -> plain text |
| `scripts/outline_from_text.py` | Text -> outline without a model (rule based) |
| `scripts/generate_mindmap.py` | File/topic -> mind map with a local model (Ollama, LM Studio, llama.cpp, vLLM), or `--no-llm` |
| `scripts/outline_repair.py` | Repairs for a small model's answer: last outline of a reply that thinks aloud, grouping, shortening, notes on long sources (used by `generate_mindmap.py`) |
| `scripts/check_env.py` | Checks Python, fonts, browser, PDF reader |
| `scripts/langchain_tool.py` | Optional LangChain tool `create_mind_map` |
| `references/formats.md` | Every accepted input form, the JSON keys, the limits, the output formats |
| `references/design.md` | Layout, node styles, themes, sizes |
| `references/small_models.md` | Using this skill with small local models |
| `references/integration.md` | Python API, LangChain, environment variables |
| `references/troubleshooting.md` | Errors and fixes |
| `assets/examples/` | `fotosintesis.md` (outline), `water_cycle.json` (JSON), `artikel_koperasi.txt` (raw article for `generate_mindmap.py`) |
| `assets/prompts/` | System prompts for a model: outline (recommended) and JSON |
| `assets/mindmap.schema.json` | JSON Schema for constrained decoding |
| `assets/fonts/` | Poppins (OFL licence), embedded in every SVG/HTML |
| `evals/local_models.py`, `evals/agent_loop.py` | Measure a local model with this skill: through `generate_mindmap.py`, and as an agent with tool calls |
| `tests/` | `pytest` tests for the repairs, no model needed |

## Setup

```
python scripts/check_env.py --build
```

SVG, HTML, Markdown and Mermaid need only Python. PNG and PDF use Microsoft Edge (already on Windows), Google Chrome or Chromium (`POSTER_BROWSER=<path>` if it is not found); without one, `pip install cairosvg` also works, or open the HTML and press Save PNG. PDF sources need `pdftotext` (poppler) or `pip install pypdf`.
