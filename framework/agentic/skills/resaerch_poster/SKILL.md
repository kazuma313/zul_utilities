---
name: research-poster
description: Create a one-page research poster (PDF, PNG or HTML) in a modern infographic style - big title, hero picture, cards of different widths in a flowing 12-column layout (blue "consumer research" preset or purple "technology" preset), with overview, objectives, audience, methods, key findings (big numbers), insights (donut/bar/line chart with an automatic takeaway), trends and recommendations. Use when the user wants a research poster, infographic summary, one-page research summary or academic poster. You write a JSON object; the script draws everything, orders the sections, fits the text on one page. Needs Python 3.9+; PDF/PNG need Edge, Chrome or Chromium (HTML needs nothing).
---

# research-poster

One page, compact, analytic. You write the content as JSON, the script builds the poster.
Never write HTML, CSS or chart code yourself.

## Steps

1. Collect the material: topic, numbers, sample, methods, findings, contact line, optional photo file.
2. Write the poster as JSON (format below) and save it, for example `poster.json`.
3. Run:
   ```
   python scripts/build_poster.py poster.json -o poster.pdf
   ```
   `-o poster.png` gives an image, `-o poster.html` needs no browser, `--png` adds a preview next to the PDF.
4. Read the output.
   - `OK: created <path>` means success. `ORDER:` shows the final section order. Tell the user the path.
   - `AUTO-FIXED / WARNINGS` lists repairs and texts that are too long. Shorten those and run again if needed.
   - `ERROR:` means nothing was made. Follow the `HINT`, fix the JSON, run again (one retry).

If you have a tool named `create_research_poster`, call it with the same JSON:
`create_research_poster(poster="<JSON object as a string>", filename="poster.pdf")`.

## Format

```json
{
  "tag": "Research Project",
  "title": "Consumer Behavior Research",
  "highlight": "Behavior",
  "subtitle": "Understanding customers, shaping better strategies",
  "lead": "Optional one or two sentences under the title.",
  "theme": "blue",
  "footer": {"slogan": "Technology today, a better tomorrow.", "text": "Faculty of Economics | hello@example.org | www.example.org"},
  "hero_image": "photo.jpg",
  "size": "A2",
  "sections": [
    {"type": "text",    "title": "Research Overview", "text": "Two or three sentences."},
    {"type": "bullets", "title": "Objectives", "items": ["First objective", "Second objective"]},
    {"type": "facts",   "title": "Target Audience", "items": [{"label": "Age range", "value": "18 - 45"}, {"label": "Sample size", "value": "350 respondents"}],
                        "pictograph": {"value": 350, "total": 500, "label": "350 of 500 invited took part"}},
    {"type": "list",    "title": "Research Methods", "items": [{"title": "Online survey", "text": "350 respondents, 24 questions", "icon": "monitor"}]},
    {"type": "stats",   "title": "Key Findings", "items": [{"label": "Quality is the top priority", "value": "72%", "text": "rank quality first", "icon": "quality"}]},
    {"type": "chart",   "title": "Customer Insights", "chart": {"type": "donut", "categories": ["Quality", "Price", "Brand"], "series": [{"name": "Main reason", "values": [54, 31, 15]}]},
                        "text": "One or two sentences.", "quote": "One-sentence takeaway (automatic when left out)."},
    {"type": "list",    "title": "Market Trends", "items": [{"title": "Rise of e-commerce", "text": "Online purchases grew 18%", "icon": "cart"}]},
    {"type": "columns", "title": "Recommendations", "items": [
      {"title": "For students", "text": "Weekly guided practice", "icon": "book"},
      {"title": "For educators", "text": "Peer communities and training", "icon": "people"},
      {"title": "For government", "text": "Fund technical support staff", "icon": "flag"}]}
  ]
}
```

`footer` may also be a plain string (one contact line). `theme` is `"blue"` (numbered bar headers, like the consumer poster) or `"purple"` (rounded pill headers, wave lines, slogan banner, like the technology poster); a dict with `preset` plus colour overrides also works (`references/design.md`).

## Section types

| Type | Shows | Fields | Limits |
|---|---|---|---|
| `text` | paragraph + big icon | `text`, `icon` | 350 characters |
| `bullets` | bullet list + big icon | `items` (string or `{title, text}`), `text`, `icon` | 2 to 5 items |
| `list` | items with small icons | `items` `{title, text, icon}` | 2 to 4 items |
| `facts` | label / value rows + people pictograph | `items` `{label, value}`, `pictograph {value, total, label}`, `icon` | 2 to 6 rows |
| `stats` | rows of big numbers | `items` `{label, value, text, icon}` | 2 to 5 rows, value is one number, at most 14 characters (`72%`, `Rp 310.000`) |
| `chart` | donut, pie, column, bar or line chart, legend, takeaway | `chart`, `text`, `quote`, `insight` | 2 to 6 categories, up to 3 series |
| `columns` | 2 to 4 groups side by side, each with icon, title, text (full width) | `items` `{title, text, icon}`, `text` | 2 to 4 columns |

Every section may have `text`, `quote`, `icon`, `image` (a local illustration shown beside the content) and `width`. Icon names: `references/sections.md`.

## Layout (not a fixed grid)

Sections are placed in rows of a 12-column grid and each row is as tall as its content, so the page looks like a designed poster rather than equal boxes. `width` picks the column span: `narrow` (4), `half` (6), `wide` (8), `full` (12). Without it, the span comes from the amount of content: short sections get 4 columns, long ones 8. Rows are filled left to right and stretched to the full width; a half-width card never sits alone. Mix widths on purpose: `narrow + wide`, `half + half`, `narrow + narrow + narrow`, and a `columns` section across the bottom. After layout, the text is scaled so the rows fill the page exactly, and cards shorter than their row enlarge their own text. `"layout": "grid"` gives the old equal-card grid instead.

## Rules

1. 6 to 8 sections. The script sorts them into the research order: overview, objectives, audience, methods, findings, insights, trends, recommendations, conclusion (by title keywords, English or Indonesian). `--keep-order` turns this off.
2. Section titles: at most 3 words. Poster title: at most 6 words (longer titles shrink; over 12 words they overflow).
3. Keep text short: `text` under 350 characters, item texts under 90, item titles under 40. Text that does not fit is shrunk, then reported.
4. Chart `values` are numbers. `categories` and every `values` list have the same length. A chart card without a `quote` gets an automatic sentence from the data (largest share, or first-to-last change).
5. Use only facts and numbers the user gave. No numbers: leave out `stats`, `chart` and `pictograph`. Never invent an institution, an e-mail address or a website for the footer. A donut or pie shows parts of one whole: give every part, so percentages add up to 100.
6. Plain text only. No `**bold**`, no bullet characters, no line breaks inside a string.
7. Write in the user's language; keep field names in English. The automatic chart sentence follows the language (`"language": "id"` forces Indonesian).

## Files

| Path | Purpose |
|---|---|
| `scripts/build_poster.py` | JSON -> HTML/PDF/PNG. Command line and Python function `build_poster()` |
| `scripts/spec_normalizer.py` | Repairs JSON, orders sections, trims lists (used automatically) |
| `scripts/charts.py`, `scripts/icons.py` | SVG charts and icons (used automatically) |
| `scripts/generate_poster.py` | Topic -> poster with a local model (Ollama, LM Studio, llama.cpp, vLLM) |
| `scripts/check_env.py` | Checks Python, fonts and the browser |
| `scripts/langchain_tool.py` | Optional LangChain tool `create_research_poster` |
| `references/sections.md` | Every section type, field, icon name, size |
| `references/design.md` | How the layout works, colours, theme overrides |
| `references/small_models.md` | Using this skill with small local models |
| `references/integration.md` | Python API, LangChain, environment variables |
| `references/troubleshooting.md` | Errors and fixes |
| `assets/examples/` | `consumer_research.json` (the reference poster as JSON), `sample_hero.jpg` |
| `assets/poster.lite.schema.json`, `assets/poster.schema.json` | JSON Schemas for constrained decoding |
| `assets/prompts/` | System prompts (lite and full) |
| `assets/fonts/` | Poppins (OFL licence), embedded in every poster |
| `assets/original/` | The reference PDF the design was taken from |

## Setup

```
python scripts/check_env.py --build
```

PDF and PNG use Microsoft Edge (already on Windows), Google Chrome or Chromium. Without one, the HTML is still written: open it in any browser and print to PDF.
