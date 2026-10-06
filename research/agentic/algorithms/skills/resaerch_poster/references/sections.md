# Section reference

Top-level fields: **title** (required), `tag` (default "Research Project"), `highlight` (a word of the title shown in the accent colour; without it the middle word of a 3-4 word title is used), `subtitle`, `lead` (one or two sentences under the title), `footer` (a contact string, a list joined with " | ", or `{"slogan": "...", "text": "..."}` for the banner footer), `hero_image` (local file; without one a decorative panel is drawn; `"hero_style": "plain"` shows a cut-out illustration without the rounded frame), `size` (A0, A1, A2 default, A3, A4, LETTER, TABLOID, 24X36, 36X48), `language` (`en` or `id`, auto-detected otherwise), `theme` (`"blue"`, `"purple"` or a dict, see design.md), `layout` (`flow` default, or `grid`), `sections`.

4 to 8 sections (a `columns` section counts as a full row). Sections are numbered in their final order when the theme is numbered.

Every section: **type**, **title** (max 3 words), optional `text`, `quote`, `icon`, `image` (local illustration beside the content), `width` (`narrow`, `half`, `wide`, `full` or a number 3-12), `role`
(`role` forces the ordering slot: overview, objectives, audience, methods, findings, insights, trends, conclusion, recommendations).

| Type | Fields | Notes |
|---|---|---|
| `text` | `text` (350 chars), `icon` | one paragraph next to a big icon |
| `bullets` | `items`: strings or `{title, text}` (2-5), `text` (lead), `icon` | dot bullets, bold title + grey text |
| `list` | `items`: `{title, text, icon}` (2-4) | each item has a small icon disc (auto-chosen from the title when missing) |
| `facts` | `items`: `{label, value}` (2-6), `pictograph`: `{value, total, label}`, `text`, `icon` | label/value table; `{"Age": "18-45"}` maps also work; strings "Age: 18-45" are split |
| `stats` | `items`: `{label, value, text, icon}` (2-5) | big number rows; a number inside a plain string ("72% prefer online") is extracted |
| `chart` | `chart`, `text`, `quote`, `insight`, `legend` (false hides it) | see below |
| `columns` | `items`: `{title, text, icon}` (2-4), `text` | groups side by side, always full width; good for recommendations per audience |

`bullets` with `"numbered": true` shows numbered circles instead of check marks (research questions).

## Chart object

```json
{"type": "donut", "categories": ["Quality", "Price", "Brand"], "series": [{"name": "Main reason", "values": [54, 31, 15]}], "unit": "%"}
```

- `type`: `donut`, `pie` (shares, one series, percentages computed from the values), `column` (vertical bars), `bar` (horizontal bars), `line` (trend). Up to 3 series for column, bar and line.
- 2 to 6 categories. Chart.js style `{"labels": [...], "datasets": [{"label", "data"}]}`, a map `{"Yes": 65, "No": 35}` and numbers as strings ("65%") are accepted.
- Automatic takeaway (`quote` when none is given): largest share for donut/pie; change from first to last category for line and multi-series charts; highest and lowest otherwise. Set `"insight": "..."` or `"quote": "..."` to write your own.

## Icons

Use these names in `icon` fields: `overview` `search` `target` `people` `monitor` `chart` `trend` `cart` `tag` `trust` `quality` `phone` `leaf` `clipboard` `star` `money` `globe` `bulb` `shield` `book` `clock` `check` `document` `message` `list` `location` `calendar` `heart` `tools` `flag`.
Unknown names fall back to a keyword guess from the title (English and Indonesian), then to a generic icon.

## Standard order

Sections are sorted by the role found in their title (keywords, English and Indonesian):

| Rank | Role | Title keywords |
|---|---|---|
| 0 | overview | overview, background, introduction, summary, latar belakang, pendahuluan, ringkasan |
| 1 | objectives | objective, goal, aim, research question, hypothesis, tujuan |
| 2 | audience | audience, respondent, participant, sample, population, profile, responden, populasi |
| 3 | methods | method, approach, design, procedure, data collection, metode |
| 4 | findings | finding, result, temuan, hasil |
| 5 | insights | insight, analysis, discussion, statistic, distribution, wawasan, analisis, pembahasan |
| 6 | trends | trend, market, outlook, implication, tren, pasar |
| 7 | conclusion | conclusion, limitation, future, reference, contact, kesimpulan, keterbatasan |
| 8 | recommendations | recommend, action, next step, strategy, rekomendasi, saran |

A section whose title matches none of these keeps its position relative to the previous section. `--keep-order` (or `keep_order=True`) disables sorting. The re-ordering is always reported in the warnings.

## Accepted alternatives

Text around the JSON, code fences, `<think>` blocks, trailing commas, cut-off JSON (complete sections kept); a bare array of sections; `slides`/`cards`/`blocks` instead of `sections`; `type` aliases such as `paragraph`, `kpi`, `metrics`, `keyvalue`, `demographics`, `pie`, `graph`; `points`/`bullets`/`list` instead of `items`; `content`/`body` instead of `text`; missing `type` (guessed from the fields).
