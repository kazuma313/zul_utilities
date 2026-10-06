# Input and output formats

`scripts/build_mindmap.py` accepts three input forms. All of them go through `scripts/outline_parser.py`, which repairs and limits the tree and lists every repair in the warnings.

## 1. Markdown outline (recommended)

```
# Sistem Pencernaan            <- root: first "#" heading, or the first line
- Mulut                        <- main branch
  - Gigi mengunyah             <- sub point (two spaces or a tab per level)
  - Enzim amilase (dalam air liur)   <- note in parentheses -> small grey text
    - Memecah amilum           <- detail
- Lambung
  - Asam lambung
  - Pepsin
```

Also understood:

- `## Heading` lines as main branches, `### Heading` as sub points (headings nest by their number of `#`); bullets under a heading nest under it.
- `1.`, `2)`, `a.` numbered lists (same nesting as bullets).
- `*` and `•` bullets; tabs count as one level.
- Prose before the outline ("Here is the mind map:", "Berikut peta pikirannya:"), code fences and `<think>` blocks are stripped.
- A `- text (note)` ending or a ` — note` after a dash becomes the node's `note`.

## 2. JSON

```json
{
  "title": "Biology grade 8",        // optional caption in the corner
  "theme": "blue",                   // optional: rainbow | blue | pastel | dark | mono
  "layout": "right",                 // optional: radial | right
  "language": "id",                  // optional, used as the HTML lang attribute
  "font_scale": 1.0,                 // optional 0.6 - 2.0
  "root": "Sistem Pencernaan",
  "nodes": [
    {"text": "Mulut", "children": [
      {"text": "Gigi mengunyah"},
      {"text": "Enzim amilase", "note": "dalam air liur", "children": [{"text": "Memecah amilum"}]}
    ]},
    {"text": "Lambung", "children": ["Asam lambung", "Pepsin"]}
  ]
}
```

Accepted variations (all mapped to `text` / `children`):

| Meaning | Keys understood |
|---|---|
| node text | `text`, `name`, `label`, `title`, `topic`, `node`, `value`, `key` |
| children | `children`, `nodes`, `items`, `subtopics`, `branches`, `sub`, `kids`, `points`, `leaves` |
| root | `"root": "string"`, `"root": {node}`, a top-level node object, `{"Topic": [children]}` (single-key dict), a bare list (root = title or "Mind map") |
| extras kept | `note`, `icon`, `color`, `url` |

A child may be a plain string (leaf), a node object, or a one-key dict `{"Branch": [...]}`. Trailing commas, single quotes, comments and truncated JSON (cut off by a token limit) are repaired when possible.

## 3. Mermaid mindmap

```
mindmap
  root((Sistem Pencernaan))
    Mulut
      Gigi mengunyah
    Lambung
      Asam lambung
```

Node shapes `((x))`, `(x)`, `[x]`, `{{x}}`, `)x(` and `::icon(...)` decorations are stripped.

## Limits and repairs

| Rule | Limit | Repair |
|---|---|---|
| main branches | 8 | extra branches dropped (warning) |
| children per node | 6 | extra children dropped (warning) |
| depth below root | 3 (root = level 0, deepest = level 4) | deeper children folded into the parent's note |
| node text | 90 characters | the rest after the first clause becomes a note |
| empty root | - | first branch promoted, or "Mind map" |
| single child with no siblings and a preamble root | - | the child becomes the root |

Nodes with more than about 8 words are wrapped over up to three lines (widths: root 260 px, branch 220 px, deeper 190-210 px) and make the map heavier; keep them short.

## Output formats

Pick by the extension of `-o` / `filename`; `--also svg,md,mmd` adds more next to it.

| Extension | Content | Needs |
|---|---|---|
| `.svg` | vector, fonts embedded (base64 Poppins), opens in browsers, Word, Inkscape | nothing |
| `.html` | the SVG in a page with pan/zoom, `+` `-` `Fit` buttons and `Save PNG` | nothing (browser to view) |
| `.png` | bitmap, `--scale 2` = 2x pixel density (default), transparent margins cropped | Edge / Chrome / Chromium, or cairosvg |
| `.pdf` | one page of exactly the map's size | Edge / Chrome / Chromium, or cairosvg |
| `.md` | the cleaned outline (what was actually drawn) | nothing |
| `.mmd` | Mermaid `mindmap` source (paste into Notion, GitHub, Obsidian) | nothing |
| `.json` | the cleaned tree `{"title", "theme", "layout", "root": {...}}` | nothing |

When PNG/PDF cannot be rendered the SVG is written instead and the warning says why.

## Result object (Python / `--json`)

```json
{"ok": true, "path": "output/map.png", "files": {"png": "...", "svg": "..."},
 "stats": {"nodes": 29, "branches": 5, "depth": 3, "leaves": 19},
 "theme": "rainbow", "layout": "radial", "size": [1180, 720],
 "warnings": ["'Tahapan': 7 children -> 6"]}
```

On failure: `{"ok": false, "error": "...", "hint": "...", "warnings": [...]}`. `format_result(res)` turns either into the `OK:` / `ERROR:` text shown in SKILL.md.
