# Layout reference

All 20 layouts. **Bold** fields are required, the rest are optional.
Every slide also accepts `"notes"` (speaker notes).
Slide size is 16:9 (10 x 5.625 inches). "Dark" and "light" refer to the slide background the theme picks.

Colours are 6-digit hex without `#`, for example `"06B6D4"`. Invalid colours fall back to the theme accent.

A working example of every layout: `assets/examples/all_layouts.json`.

## Contents

1. title  2. agenda  3. section_divider  4. bullets  5. content  6. two_column
7. two_column_bullets  8. table  9. stat_callout  10. chart  11. quote  12. icon_grid
13. definition  14. features_stats  15. timeline  16. numbered_list  17. challenges
18. image  19. image_bullets  20. conclusion_cta

---

## 1. title (dark)

Opening slide with decorative circles and an accent bar.

| Field | Type | Notes |
|---|---|---|
| **title** | string | under 40 characters looks best; longer titles shrink automatically |
| subtitle | string | one line |
| icon | string | react-icons name, shown large on the right |
| icon_color | hex | default: theme accent |

```json
{"layout": "title", "title": "Koperasi Digital 2026", "subtitle": "Growth plan", "icon": "FaRocket"}
```

## 2. agenda (light)

| Field | Type | Notes |
|---|---|---|
| title | string | default "Agenda" |
| **items** | list of `{number, label, duration}` | max 7. `number` defaults to 01, 02 ... A plain string becomes the `label` |
| highlight | integer | zero-based index of the row to highlight, `-1` for none |

```json
{"layout": "agenda", "title": "Agenda", "highlight": 0,
 "items": [{"number": "01", "label": "Where we are", "duration": "5 min"}, {"label": "Roadmap"}]}
```

## 3. section_divider (dark)

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| section_number | string | `"01"`, shown very large |
| subtitle | string | |

## 4. bullets (light)

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **bullets** | list | max 6 per slide; more are moved to a "(cont.)" slide. Each item is a string, or `{"text", "icon", "color"}` to show an icon instead of a dot |

```json
{"layout": "bullets", "title": "What is working",
 "bullets": ["Onboarding takes 5 minutes", {"icon": "FaUsers", "text": "Referrals bring 1 in 3 members"}]}
```

Do not mix icon bullets and emoji in one slide.

## 5. content (light)

One paragraph on a white card.

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **content** | string | up to about 500 characters (330 with an icon). `\n\n` starts a new paragraph. Longer text shrinks |
| icon | string | large decorative icon on the right |
| icon_color | hex | |

## 6. two_column (light)

Two white cards side by side, each with icon, header and body text.

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **left**, **right** | string | body text, under 200 characters each |
| left_header, right_header | string | |
| left_icon, right_icon | string | chosen automatically from the header when missing |
| left_color, right_color | hex | accent of each card |

If `left` / `right` are lists the slide becomes `two_column_bullets`.

## 7. two_column_bullets (light)

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **left_bullets**, **right_bullets** | list | max 6 each; strings or `{"text","icon","color"}` |
| left_header, right_header | string | |
| left_icon, right_icon, left_color, right_color | | as in `two_column` |

## 8. table (light)

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **headers** | list of strings | max 6 columns |
| **rows** | list of lists | max 8 rows per slide; more rows continue on a "(cont.)" slide. Short rows are padded. A list of objects `[{"Item": "Rent", "Cost": 1200}]` also works |

## 9. stat_callout (dark)

Big numbers.

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **stats** | list of `{value, label}` | 2 to 4. `value` under 8 characters (`"42%"`, `"Rp 4.2M"`); longer values shrink |

## 10. chart (light)

Native PowerPoint chart. The user can right-click and edit the data.

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **chart_type** | string | `bar`, `line`, `pie`, `doughnut`, `area`, `radar`, `scatter` |
| **chart_data** | list of series | each `{"name": "Sales", "labels": ["Jan","Feb"], "values": [10, 20]}`. `labels` and `values` must have the same length. `pie` / `doughnut` use one series |
| chart_options | object | see below |

`chart_options` (snake_case): `bar_dir` (`"col"` vertical, `"bar"` horizontal), `show_legend`, `legend_pos` (`b`, `t`, `l`, `r`, `tr`), `show_value`, `show_percent`, `data_label_position`, `data_label_color`, `chart_colors` (list of hex), `line_size`, `line_smooth`, `hole_size`, `show_title`, `title_font_size`.

Also accepted and converted: Chart.js style `{"labels": [...], "datasets": [{"label", "data"}]}`, a plain map `{"Jan": 10, "Feb": 20}`, numbers as strings (`"60%"`, `"1,200"`).
A chart without usable data becomes a `content` slide with a warning.

## 11. quote (dark)

| Field | Type | Notes |
|---|---|---|
| **quote** | string | under 200 characters, without quotation marks |
| attribution | string | name |
| context | string | role, source |

## 12. icon_grid (dark)

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **cards** | list of `{icon, header, body, color}` | 2 to 6. Grid: 2 -> 1x2, 3 -> 1x3, 4 -> 2x2, 5-6 -> 2x3. `body` under 60 characters. Missing icons are chosen from the header. A string `"Header: body"` also works |

## 13. definition (dark)

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **definition** | string | under 220 characters, shown in a framed box |
| cards | list of `{icon, header, body, color}` | 2 to 4 supporting points |

## 14. features_stats (dark)

Feature list on the left, big numbers on the right.

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **features** | list of `{title, subtitle, description}` | max 4; keep descriptions under 60 characters |
| **stats** | list of `{value, label}` | max 3 |

## 15. timeline (light)

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **steps** | list of `{phase, label, description}` | 2 to 5. `phase` = date or quarter, `label` = name. `description` under 70 characters. A string `"Q1: find location"` also works |

## 16. numbered_list (dark)

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **items** | list of `{number, title, description}` | 2 to 6; `number` defaults to 01, 02 ... |

## 17. challenges (light)

Risk cards with a warning icon, optional tip bar at the bottom.

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **items** | list of `{title, description, color}` | 2 to 4; default colour red `DC2626` |
| tip | string | one line |

## 18. image (light)

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **image_url** | string | path to a local PNG / JPG / GIF. Relative paths are searched in: the folder of the spec file, `PPTX_IMAGE_DIRS`, the current folder. `http(s)` URLs are not downloaded |
| caption | string | |
| bullets | list of strings | up to 5 short insights shown under the image |

The picture keeps its aspect ratio. A missing file gives a warning and the slide is built without the picture.

## 19. image_bullets (light)

Picture on the left, bullets on the right.

| Field | Type | Notes |
|---|---|---|
| **title** | string | |
| **image_url** | string | as in `image` |
| **bullets** | list | max 6 |

## 20. conclusion_cta (dark)

| Field | Type | Notes |
|---|---|---|
| title | string | default "Kesimpulan" - set it in the language of the deck |
| **points** | list of strings | max 5, shown with check marks |
| cta | string | text of the button at the bottom, under 50 characters |

---

## Accepted alternatives

The normaliser maps common mistakes so that decks from small models still build.
Every repair is listed under `AUTO-FIXED / WARNINGS`.

- Wrapper object `{"theme": "...", "slides": [...]}` or a bare array.
- Text around the JSON, code fences, `<think>...</think>` blocks, trailing commas, single quotes.
- JSON cut off by the token limit: complete slides are kept.
- Layout names: `bullet_points`, `two-column`, `stats`, `kpi`, `cards`, `roadmap`, `steps`, `risks`, `cta`, `thank_you`, `pie_chart`, `Title Slide` and similar.
- `type` / `slide_type` instead of `layout`; `heading` instead of `title`; `tagline` instead of `subtitle`; `speaker_notes` instead of `notes`.
- No layout at all: guessed from the fields present.
- `points` / `items` / `text` instead of `bullets`; one string with line breaks instead of a list.
- Lists of strings where objects are expected (`"Header: body"`, `"42% Growth"`, `"Q1: Launch"`).
