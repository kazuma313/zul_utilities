---
name: pptx-claude
description: Create PowerPoint (.pptx) decks from a JSON list of slides. Use for any request to make a presentation, slide deck or pitch deck as a .pptx file. 20 layouts (title, bullets, two_column, table, chart, stat_callout, quote, timeline, icon_grid and more), 6 colour themes, native editable charts, icons. Input is forgiving - wrong field names, extra text around the JSON and oversized lists are repaired automatically. Needs Python 3.9+ and Node.js with the npm package pptxgenjs.
---

# pptx-claude

Turn a JSON list of slides into a polished `.pptx` file.

You write JSON. The script does all the design work (positions, colours, fonts,
icons, charts). Never write pptxgenjs or python-pptx code yourself.

## Steps

1. Plan the deck: 5 to 12 slides, one message per slide.
2. Write the slides as a JSON array and save it, for example `slides.json`.
3. Run:
   ```
   python scripts/create_pptx.py slides.json -o deck.pptx --theme ocean
   ```
4. Read the output.
   - `OK: created <path>` means success. Tell the user the path.
   - `AUTO-FIXED / WARNINGS` lists what the script repaired. The deck is still valid.
   - `ERROR:` means no file was made. Follow the `HINT`, fix the JSON, run again (one retry).

If you have a tool named `create_pptx_js` instead of a shell, call
`create_pptx_js(slides="<JSON array as a string>", filename="deck.pptx", theme="ocean")`.
The rules below are the same.

## Core layouts (use these first)

Copy the field names exactly. Every slide needs `"layout"`.

```json
[
  {"layout": "title", "title": "Deck title", "subtitle": "One line"},
  {"layout": "bullets", "title": "Slide title", "bullets": ["Point one", "Point two", "Point three"]},
  {"layout": "two_column", "title": "Slide title", "left_header": "Before", "left": "Short text.", "right_header": "After", "right": "Short text."},
  {"layout": "table", "title": "Slide title", "headers": ["Item", "Cost"], "rows": [["Rent", "1200"], ["Staff", "3000"]]},
  {"layout": "stat_callout", "title": "Slide title", "stats": [{"value": "42%", "label": "Growth"}, {"value": "3x", "label": "Faster"}]},
  {"layout": "chart", "title": "Slide title", "chart_type": "bar", "chart_data": [{"name": "Sales", "labels": ["Jan", "Feb", "Mar"], "values": [10, 20, 15]}]},
  {"layout": "quote", "quote": "The quoted sentence.", "attribution": "Name, Role"},
  {"layout": "conclusion_cta", "title": "Next steps", "points": ["Do this", "Then this"], "cta": "Approve the plan"}
]
```

## More layouts

Field details for all 20 layouts: `references/layouts.md`.

| Layout | Use for | Main fields |
|---|---|---|
| `agenda` | table of contents | `items: [{number, label, duration}]` |
| `section_divider` | start of a new part | `section_number`, `title`, `subtitle` |
| `content` | one short paragraph | `content`, optional `icon` |
| `two_column_bullets` | compare two lists | `left_header`, `left_bullets`, `right_header`, `right_bullets` |
| `icon_grid` | 3 to 6 features or pillars | `cards: [{icon, header, body}]` |
| `definition` | explain a concept | `definition`, `cards: [{icon, header, body}]` |
| `features_stats` | features plus numbers | `features: [{title, subtitle, description}]`, `stats` |
| `timeline` | roadmap, process | `steps: [{phase, label, description}]` |
| `numbered_list` | ordered steps, principles | `items: [{number, title, description}]` |
| `challenges` | risks, problems | `items: [{title, description}]`, `tip` |
| `image` | one picture or chart image | `image_url` (local file path), `caption` |
| `image_bullets` | picture plus takeaways | `image_url`, `bullets` |

## Rules

1. First slide: `title`. Last slide: `conclusion_cta`.
2. Do not use the same layout twice in a row. Use at least 4 different layouts.
3. Limits per slide: bullets 6, stats 4, table 6 columns and 8 rows, cards 6, timeline steps 5, numbered items 6, challenges 4, points 5. Extra bullets and table rows continue on a new slide; other extra items are dropped.
4. Keep text short: titles under 8 words, bullets under 12 words, stat values under 8 characters.
5. Chart `values` are numbers. `labels` and `values` have the same length. `chart_type`: `bar`, `line`, `pie`, `doughnut`, `area`, `radar`, `scatter`.
6. Plain text only. No `**bold**`, no bullet characters, no HTML.
7. Use only facts and numbers the user gave you. Do not invent statistics.
8. Use image layouts only when you have a real local image file.

## Themes

`midnight` corporate (default) - `coral` marketing - `forest` environment - `ocean` tech and finance - `charcoal` minimal - `cherry` bold.

## Icons

Optional. Use a react-icons name such as `FaRocket`, `FaUsers`, `FaChartLine`,
`FaShieldAlt`, `FaLightbulb`, `FaCheckCircle`. Verified list by topic:
`references/icons.md`. A wrong name becomes a check mark, it never breaks the deck.
`icon_grid`, `definition` and `two_column` get icons automatically when you leave them out.

## Files in this skill

| Path | Purpose |
|---|---|
| `scripts/create_pptx.py` | JSON -> .pptx. Command line and Python function `create_pptx()` |
| `scripts/spec_normalizer.py` | Repairs imperfect JSON (used automatically) |
| `scripts/generate_deck.py` | Topic -> deck with a local model (Ollama, LM Studio, llama.cpp, vLLM) |
| `scripts/check_env.py` | Checks Node.js and npm packages, prints the fix |
| `scripts/render_preview.py` | Optional: .pptx -> PNG images for visual checking |
| `scripts/langchain_tool.py` | Optional LangChain tool `create_pptx_js` |
| `references/layouts.md` | Every layout, every field, limits |
| `references/icons.md` | Verified icon names by topic |
| `references/design_guide.md` | Deck patterns and how to pick layouts |
| `references/small_models.md` | Running this skill with small local models (Qwen etc.) |
| `references/integration.md` | Python API, LangChain, uploads, environment variables |
| `references/troubleshooting.md` | Errors and fixes |
| `assets/examples/` | `minimal_deck.json`, `all_layouts.json`, `sample_chart.png` |
| `assets/slide_spec.lite.schema.json` | JSON Schema, 8 core layouts, for constrained decoding |
| `assets/slide_spec.schema.json` | JSON Schema, all 20 layouts |
| `assets/prompts/` | Ready-to-paste system prompts (lite and full) |
| `package.json` | npm dependencies. Run `npm install` in this folder once |

## Setup (once)

```
cd <this folder>
npm install
python scripts/check_env.py --build
```

Only `pptxgenjs` is required. `react`, `react-dom`, `react-icons` and `sharp` are
optional; without them decks build without icons.
