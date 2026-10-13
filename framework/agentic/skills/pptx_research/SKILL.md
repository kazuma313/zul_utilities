---
name: pptx-research
description: Create a research-proposal PowerPoint (.pptx) in the black-and-white "Modern Research Proposal" template. Use when the user wants a research proposal, thesis proposal, study plan or research presentation as slides. You write a JSON list of slides; the script fills the template, puts the sections in the standard order (cover, intro, agenda, background, problem, framework, methodology, data, timeline, analysis, closing), builds the agenda automatically, and adds editable charts. Needs Python 3.9+ and python-pptx.
---

# pptx-research

Fill the research-proposal template from JSON. The design is already in
`assets/template.pptx`. You only write the content. Never write python-pptx code yourself.

## Steps

1. Collect the material: topic, organization, presenter, facts, numbers, image files.
2. Write the deck as JSON (format below) and save it, for example `deck.json`.
3. Run:
   ```
   python scripts/build_deck.py deck.json -o proposal.pptx
   ```
4. Read the output.
   - `OK: created <path>` means success. `ORDER:` shows the final slide order. Tell the user the path.
   - `AUTO-FIXED / WARNINGS` lists repairs and texts that are too long. Shorten those texts and run again if needed.
   - `ERROR:` means no file was made. Follow the `HINT`, fix the JSON, run again (one retry).

If you have a tool named `create_research_pptx`, call it with the same JSON:
`create_research_pptx(deck="<JSON object as a string>", filename="proposal.pptx")`.

## Format

```json
{
  "organization": "Universitas Nusantara",
  "tagline": "Research Proposal - Faculty of Economics 2026",
  "slides": [
    {"layout": "cover", "title": "Digital Cooperatives", "subtitle": "Research Proposal", "presenter": "Your Name"},
    {"layout": "intro", "title": "Hello !", "lead": "One or two sentences.", "paragraphs": ["First paragraph.", "Second paragraph."]},
    {"layout": "section", "title": "Background of the Study", "text": "One paragraph."},
    {"layout": "three_cards", "title": "Problem Statement", "text": "One paragraph.", "cards": [
      {"header": "Scope of the Study", "body": "..."},
      {"header": "Relevance of the Study", "body": "..."},
      {"header": "Research Question", "body": "..."}]},
    {"layout": "two_cards", "title": "Methodology", "text": "One paragraph.", "cards": [
      {"header": "Qualitative Methods", "body": "..."},
      {"header": "Quantitative Methods", "body": "..."}]},
    {"layout": "chart", "title": "Quantitative Data", "text": "One paragraph.",
     "chart": {"type": "column", "categories": ["A", "B", "C"], "series": [{"name": "2026", "values": [10, 20, 15]}]}},
    {"layout": "timeline", "title": "Proposed Timeline", "text": "One sentence.", "columns": [
      {"header": "Jan - Mar", "items": ["First task", "Second task"]},
      {"header": "Apr - Jun", "items": ["First task", "Second task"]}]},
    {"layout": "stat_chart", "title": "Expected Findings", "text": "One paragraph.", "stat": "65%", "stat_text": "One sentence about the number.",
     "chart": {"type": "radar", "categories": ["A", "B", "C"], "series": [{"name": "Group", "values": [5, 7, 3]}]}},
    {"layout": "closing", "title": "Thank You", "subtitle": "Contact or closing line"}
  ]
}
```

## Section order (automatic)

The script sorts the slides into this order, whatever order you wrote them in:

| # | Layout | Research section | Main fields |
|---|---|---|---|
| 1 | `cover` | Title | `title`, `subtitle`, `presenter` |
| 2 | `intro` | Hello / summary | `lead`, `paragraphs` (max 2), `image` |
| 3 | `agenda` | Agenda | **do not write it** - built from the slide titles, numbered 01 to 08 |
| 4 | `section` | Background of the study | `text`, `image` |
| 5 | `three_cards` | Problem statement | `text`, `cards` (max 3: `header`, `body`), `image` |
| 6 | `team` | Framework, theorists | `text`, `overview_items` (max 4), `people` (max 3: `name`, `role`, `note`, `image`) |
| 7 | `two_cards` | Methodology | `text`, `cards` (max 2), `image` |
| 8 | `people` | Qualitative data, participants | `text`, `text2`, `people` (max 4: `name`, `role`, `image`) |
| 9 | `chart` | Quantitative data | `text`, `chart`, optional `stat: {value, label}` |
| 10 | `timeline` | Proposed timeline | `columns` (max 4: `header`, `items` max 2), `text` |
| 11 | `analysis` | Analysis | `text`, `chart`, optional `chart2` |
| 12 | `stat_chart` | Findings with one key number | `text`, `stat`, `stat_text`, `chart` |
| 13 | `gallery` | Portfolio, photos | `text`, `images` (max 3) |
| 14 | `testimonials` | Testimonials | `lead`, `items` (max 4: `name`, `rating` 1-5, `text`, `image`) |
| 15 | `closing` | Thank you | `title`, `subtitle` |

An extra `section` slide may open another part: write it directly before the slide it introduces and it stays there.
A missing `closing` is added. `--keep-order` turns sorting off. `--no-agenda` turns the automatic agenda off.
All fields and limits: `references/layouts.md`.

## Rules

1. Do not write the agenda. Do not number the titles. The script does both.
2. Titles: at most 4 words. Cover title: at most 30 characters. Long titles shrink and then overflow.
3. `text`, paragraphs: under 450 characters. Card `body`: under 200. Timeline item: under 80. Testimonial text: under 170.
4. Chart `values` are numbers. `categories` and every `values` list have the same length (2 to 8). Types: `column`, `bar`, `line`, `pie`, `doughnut`, `radar`, `area`.
5. Use only facts, numbers, names and quotes the user gave you. No material for a slide: leave the slide out. Never invent people, testimonials or statistics.
6. `image` is a local file the user gave you. Without a file, people get a neutral avatar and other slots keep the template photo.
7. Plain text only. No `**bold**`, no bullet characters, no line breaks inside a string.
8. Write the text in the user's language. Keep the field names in English.

## Files

| Path | Purpose |
|---|---|
| `scripts/build_deck.py` | JSON -> .pptx. Command line and Python function `build_deck()` |
| `scripts/spec_normalizer.py` | Repairs JSON, orders sections, builds the agenda (used automatically) |
| `scripts/font_metrics.py` | Glyph widths used to fit titles (used automatically) |
| `scripts/generate_deck.py` | Topic -> deck with a local model (Ollama, LM Studio, llama.cpp, vLLM) |
| `scripts/prepare_template.py` | Makes `assets/template.pptx` from the original template file |
| `scripts/check_env.py` | Checks Python packages and the template |
| `scripts/render_preview.py` | Optional: .pptx -> PNG images for checking |
| `scripts/langchain_tool.py` | Optional LangChain tool `create_research_pptx` |
| `references/layouts.md` | Every layout, every field, limits |
| `references/section_order.md` | How ordering and the agenda work |
| `references/small_models.md` | Using this skill with small local models |
| `references/template_setup.md` | The template file: source, fonts, replacing it |
| `references/troubleshooting.md` | Errors and fixes |
| `assets/template.pptx` | The template (size-reduced copy of your original file) |
| `assets/examples/` | `research_proposal.json`, `all_layouts.json`, `sample_photo.jpg` |
| `assets/deck_spec.lite.schema.json`, `assets/deck_spec.schema.json` | JSON Schemas for constrained decoding |
| `assets/prompts/` | System prompts (lite and full) |

## Setup (once)

```
pip install python-pptx
python scripts/check_env.py --build
```
