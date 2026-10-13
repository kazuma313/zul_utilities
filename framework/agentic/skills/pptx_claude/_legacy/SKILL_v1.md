---
name: pptx-claude
description: PRIMARY skill for creating ALL PowerPoint presentations. Produces visually polished decks via pptxgenjs with crisp react-icons (SVG→PNG), card shadows, decorative ovals, and native charts. Supports all 20 layouts: title, bullets, content, two_column, two_column_bullets, table, image/image_bullets (chart embedding), stat_callout, section_divider, quote, agenda, timeline, icon_grid, features_stats, definition, numbered_list, conclusion_cta, challenges, chart. Falls back to the pptx skill only if Node.js is unavailable.
---

# pptx-claude

## Overview

**PRIMARY skill for all presentation creation.** Creates visually polished `.pptx` files via
**pptxgenjs** (Node.js) with **react-icons** for crisp PNG icons, **card shadows**, **decorative
transparent ovals**, and **native pptxgenjs charts**.

One tool: **`create_pptx_js`** — supports **20 layouts**

## Prerequisites

Node.js must be installed with these npm packages (one-time setup, project root):

```
npm install pptxgenjs react react-dom react-icons sharp
```

## When to use

- **Always** — this is the default tool for any presentation creation request
- Falls back to `pptx` skill only when Node.js / npm deps are unavailable

## How to invoke

```
create_pptx_js(slides='[...]', filename="deck.pptx", theme="midnight")
```

| Parameter | Required | Default      | Description |
|-----------|----------|--------------|-------------|
| `slides`  | Yes      | —            | JSON array of slide objects |
| `filename`| Yes      | —            | Output filename (`.pptx` appended if missing) |
| `theme`   | No       | `"midnight"` | Color theme: midnight, coral, forest, ocean, charcoal, cherry |

## Icon Reference

Two icon styles are supported. **Prefer react-icons for production decks.**

### react-icons (crisp PNG, recommended)

Pass any name from these packages (no quotes/underscores; case matters):

| Prefix | Package        | Examples |
|--------|----------------|----------|
| `Fa`   | Font Awesome   | `FaRocket`, `FaCheckCircle`, `FaShieldAlt`, `FaChartLine`, `FaMoneyBillWave`, `FaUsers`, `FaGraduationCap`, `FaMobileAlt`, `FaLightbulb`, `FaBrain`, `FaSearch`, `FaBalanceScale` |
| `Md`   | Material Design| `MdSecurity`, `MdTrendingUp`, `MdAccountBalance`, `MdDashboard` |
| `Hi`   | Heroicons      | `HiUsers`, `HiChartBar`, `HiLightBulb` |
| `Bi`   | Bootstrap      | `BiBarChart`, `BiCog` |
| `Ri`   | Remix          | `RiRocketLine`, `RiUserLine` |
| `Io`   | Ionicons       | `IoStatsChartOutline` |

Browse all icons: **https://react-icons.github.io/react-icons/**

Optional `"color"` field on a card sets the icon's color (hex without `#`).

### Emoji fallback

Any emoji or character renders as text: `"🎓"`, `"★"`, `"💡"`.

## Slide Spec (JSON array)

Each slide requires a `"layout"` key. All slides also accept:
- `"notes"` — speaker notes text
- `"bg_override"` — hex color string (e.g. `"1A1A2E"`) to override slide background

```json
[
  { "layout": "title",              "title": "...", "subtitle": "...", "icon": "FaRocket" },
  { "layout": "bullets",            "title": "...", "bullets": ["plain string", {"icon": "FaCheckCircle", "text": "with icon", "color": "06B6D4"}] },
  { "layout": "content",            "title": "...", "content": "...", "icon": "FaRocket" },
  { "layout": "two_column",         "title": "...", "left_icon": "FaCog", "left_header": "Traditional", "left": "Body text...", "right_icon": "FaBrain", "right_header": "AI-Enhanced", "right": "Body text..." },
  { "layout": "two_column_bullets", "title": "...", "left_header": "...", "left_bullets": [], "right_header": "...", "right_bullets": [] },
  { "layout": "table",              "title": "...", "headers": ["A","B"], "rows": [["1","2"]] },
  { "layout": "image",              "title": "...", "image_url": "chart_url:/static/charts/abc.png", "caption": "..." },
  { "layout": "image_bullets",      "title": "...", "image_url": "chart_url:...", "bullets": ["..."] },
  { "layout": "stat_callout",       "title": "...", "stats": [{"value": "42%", "label": "Growth"}] },
  { "layout": "section_divider",    "section_number": "01", "title": "...", "subtitle": "..." },
  { "layout": "quote",              "quote": "...", "attribution": "— Name", "context": "Role" },
  { "layout": "agenda",             "title": "...", "highlight": 0, "items": [{"number":"01","label":"...","duration":"10 min"}] },
  { "layout": "timeline",           "title": "...", "steps": [{"phase":"Q1","label":"Discovery","description":"..."}] },
  { "layout": "icon_grid",          "title": "...", "cards": [{"icon":"FaRocket","header":"Fast","body":"Sub-100ms","color":"06B6D4"}] },
  { "layout": "features_stats",     "title": "...", "features": [{"title":"...","subtitle":"...","description":"..."}], "stats": [{"value":"78%","label":"..."}] },
  { "layout": "definition",         "title": "...", "definition": "Long definition...", "cards": [{"icon":"FaMoneyBillWave","header":"...","body":"...","color":"06B6D4"}] },
  { "layout": "numbered_list",      "title": "...", "items": [{"number":"01","title":"...","description":"..."}] },
  { "layout": "conclusion_cta",     "title": "...", "points": ["Point 1", "Point 2"], "cta": "Call to action!" },
  { "layout": "challenges",         "title": "...", "items": [{"title":"...","description":"...","color":"DC2626"}], "tip": "Optional solution tip" },
  { "layout": "chart",              "title": "...", "chart_type": "bar", "chart_data": [{"name":"Revenue","labels":["Jan","Feb"],"values":[420,580]}], "chart_options": {"show_legend": false} }
]
```

## Native chart layout

`chart_type` options: `bar`, `line`, `pie`, `doughnut`, `radar`, `scatter`, `area`.

`chart_options` accepts snake_case keys auto-converted to pptxgenjs camelCase:
- `bar_dir` (`col` for vertical, `bar` for horizontal)
- `show_legend`, `legend_pos` (`b`, `t`, `l`, `r`, `tr`)
- `show_value`, `data_label_position`, `data_label_color`
- `chart_colors` (array of hex without `#`)
- `line_size`, `line_smooth`
- `hole_size` (doughnut), `show_percent` (pie/doughnut)
- `show_title`, `title_font_size`

Charts produced this way are **editable in PowerPoint** (right-click → Edit Data).

## Expected output

Success: `file_url:/static/downloads/filename.pptx`

Missing deps: clear error message with install instructions and guidance to use `pptx` skill.

## Themes

| Theme      | Primary      | Accent      | Best for |
|------------|-------------|-------------|----------|
| `midnight` | Navy        | Cyan        | Corporate, executive |
| `coral`    | Navy        | Coral red   | Marketing, startup |
| `forest`   | Forest green| Moss green  | Sustainability |
| `ocean`    | Deep blue   | Teal        | Tech, finance |
| `charcoal` | Charcoal    | Mint green  | Minimal, modern |
| `cherry`   | Cherry red  | Gold        | Bold, high-impact |

## Design Guide

### Deck Structure Rules

1. **Always start with `title`** (gets decorative ovals + accent bar)
2. **Use `section_divider` between major sections**
3. **Never repeat the same layout twice in a row**
4. **Every deck needs at least one visual-primary slide** (`stat_callout`, `quote`, `icon_grid`)
5. **End strong** — close with `conclusion_cta` (with checkmark points + CTA button)

### Recommended deck patterns

| Use case | Suggested layouts |
|----------|-------------------|
| Investor pitch | title → stat_callout → icon_grid → chart → conclusion_cta |
| Educational | title → definition → icon_grid → features_stats → numbered_list → conclusion_cta |
| Project review | title → section_divider → timeline → challenges → chart → quote |
| Team update | title → agenda → bullets → table → conclusion_cta |

### Avoid

- **Don't** use `bullets` for every slide — vary with `stat_callout`, `quote`, `icon_grid`, `numbered_list`
- **Don't** put more than 6 cards/items per slide — split it
- **Don't** mix react-icons with emoji in the same card grid — looks inconsistent
- **Don't** use light themes for `_DARK_LAYOUTS` (title, stat_callout, etc.) — they're designed for dark bg

## Implementation

See `pptx_claude_skill.py` in this folder.
