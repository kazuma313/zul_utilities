# Layout reference

15 layouts, one per template slide. **Bold** fields are required. Every slide also accepts `"notes"` (speaker notes)
and `"agenda_label"` (short name for the agenda).
Top-level `"organization"` and `"tagline"` are shown on the cover and the closing slide.

Character limits are what fits at the designed font size. Longer text is shrunk to 70 % first, then a warning is given.
Text much shorter than the limit is enlarged up to 130 %. Optional fields that you leave out are removed from the slide.

A complete example of every layout: `assets/examples/all_layouts.json`.

| Layout | Field | Type | Limit / notes |
|---|---|---|---|
| **cover** | **title** | string | 30 characters on one line; up to about 60 on two smaller lines |
| | subtitle | string | about 20 characters, e.g. "Research Proposal" |
| | presenter | string | shown under "Presented By:" (`presenter_label` changes that label) |
| | organization, tagline | string | usually given once at the top of the JSON |
| **intro** | title | string | default "Hello !", 1 to 2 words |
| | lead | string | 320 characters, italic, top right |
| | **paragraphs** | list of strings | max 2, 540 characters each (one paragraph: 1100) |
| | image | file | rounded square photo |
| **agenda** | title | string | default "Agenda" |
| | items | list of strings | max 8. Normally created automatically, see `section_order.md` |
| | image | file | photo top right |
| **section** | **title** | string | 2 lines of about 14 characters |
| | text | string | 510 characters |
| | image | file | wide photo across the top |
| **three_cards** | **title** | string | up to 3 short lines, about 10 characters per line |
| | text | string | 540 characters |
| | **cards** | list of `{header, body}` | max 3. header 22 characters, body 240. A string "Header: body" also works |
| | image | file | tall rounded photo |
| **team** | **title** | string | 1 line, about 10 characters |
| | text | string | 320 characters |
| | overview_title | string | default "Overview" |
| | overview_items | list of strings | max 4 short bullets (about 28 characters each) |
| | people | list of `{name, role, note, image}` | max 3. name 14, role 24, note 20 characters |
| | image | file | photo bottom right |
| **two_cards** | **title** | string | 1 line, about 11 characters |
| | text | string | 480 characters |
| | **cards** | list of `{header, body}` | max 2. Left card is dark, right card is white. `left_header` / `left` / `right_header` / `right` also work |
| | image | file | tall photo on the right |
| **people** | **title** | string | 2 to 3 lines of about 10 characters |
| | text, text2 | string | 510 and 320 characters |
| | **people** | list of `{name, role, image}` | max 4, order: top-left, top-right, bottom-left, bottom-right |
| **chart** | **title** | string | 2 lines of about 10 characters |
| | text | string | 510 characters |
| | **chart** | chart object | default type `column`, drawn on the dark card |
| | stat | `{value, label}` | optional big number under the text (value max 8 characters) |
| **timeline** | **title** | string | 1 line, about 17 characters |
| | **columns** | list of `{header, items}` | 2 to 4 columns. header 10 characters. items: max 2, 80 characters each. A string "Jan: task" also works |
| | text | string | 510 characters, under the timeline |
| **analysis** | **title** | string | 1 to 2 lines |
| | text | string | 470 characters with `chart2`, 1000 without |
| | **chart** | chart object | default type `line`, on the white card |
| | chart2 | chart object | optional small chart bottom left, default type `bar` |
| **stat_chart** | **title** | string | 1 to 2 lines |
| | text | string | 510 characters |
| | stat | string | big number, max 5 characters at full size ("65%") |
| | stat_text | string | 270 characters, italic |
| | **chart** | chart object | default type `radar`, on the white card |
| **gallery** | **title** | string | 2 lines of about 9 characters |
| | text | string | 510 characters |
| | images | list of files | max 3: wide header photo, then two rounded squares |
| **testimonials** | title | string | default "Testimonial" |
| | lead | string | 320 characters |
| | **items** | list of `{name, rating, text, image}` | max 4. rating 1 to 5 (default 5). text 175 characters |
| **closing** | title | string | default "Thank You", about 10 characters at full size |
| | subtitle | string | 70 characters, bottom left |

## Chart object

```json
{"type": "column", "categories": ["2024", "2025", "2026"],
 "series": [{"name": "Members", "values": [120, 180, 260]}, {"name": "Active", "values": [60, 110, 200]}]}
```

- `type`: `column` (vertical bars), `bar` (horizontal), `line`, `area`, `pie`, `doughnut`, `radar`.
- `categories`: 2 to 12 labels. `series`: 1 to 3 (`pie` / `doughnut` use the first one). Each `values` list has one number per category.
- Charts are native PowerPoint charts in the template's black, white and grey palette. Right-click > Edit Data works.
- Also accepted: `labels` instead of `categories`; Chart.js style `{"labels": [...], "datasets": [{"label", "data"}]}`; a map `{"Yes": 65, "No": 35}`; numbers as strings (`"65%"`, `"1,200"`).
- Without usable numbers the chart is left out and a warning is given.

## Images

- Local files only: absolute path, or a name that is searched in the folder of the JSON file, in `PPTX_IMAGE_DIRS` and in the current folder.
- Pictures are cropped to fill the slot (never stretched) and reduced to 2000 px.
- People without a photo get a neutral grey avatar. The template's stock portraits are never shown next to a real name.
- Other slots without a file keep the template photo.

## Accepted alternatives

Every repair is listed under `AUTO-FIXED / WARNINGS`.

- Text around the JSON, code fences, `<think>` blocks, trailing commas, single quotes, JSON cut off by the token limit.
- A bare array of slides instead of the wrapper object.
- Layout names by meaning, English or Indonesian: `title`, `hello`, `background`, `latar_belakang`, `problem_statement`, `rumusan_masalah`, `framework`, `kerangka_teori`, `methodology`, `metodologi`, `qualitative`, `quantitative`, `jadwal`, `analisis`, `portfolio`, `testimonial`, `thank_you`, `penutup` and more.
- `type` / `slide_type` instead of `layout`; `heading` instead of `title`; `content` / `body` instead of `text`.
- No layout at all: guessed from the fields.
- Too many cards, people, columns or items: the extra ones are dropped with a warning.
