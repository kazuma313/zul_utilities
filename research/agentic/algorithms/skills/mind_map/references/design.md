# Design: layout, node styles, themes

Everything here is done by `scripts/render_svg.py`; you only choose `theme`, `layout`, `title` and `font_scale`.

## Layout

- **radial** (default): the root sits in the centre, the main branches are split into a right and a left group (the first half right, top to bottom; the second half left). Best for concept maps and material without a strict order.
- **right**: everything grows to the right of the root, top to bottom, like a tree. Best for step-by-step material (processes, timelines, chapters in order) because reading order = branch order.

Each subtree is measured first (text is wrapped with real Poppins glyph widths from `scripts/font_metrics.py`), then stacked vertically with gaps of 22 px between main branches, 12 px between level-2 siblings, 8 px deeper; children are centred on their parent. Horizontal distance parent -> child: 70 px from the root, 48 px from a branch, 36 px and 30 px deeper. Connectors are cubic curves from the parent's edge to the child's edge in the branch colour. The image is as big as the tree needs (typical 900-1600 px wide, 500-1100 px high) plus a 40 px margin; PNG uses `--scale 2` for crisp text.

## Node styles by level

| Level | Style | Font |
|---|---|---|
| 0 root | dark filled pill, white text, wraps at 260 px | Poppins Bold 24 |
| 1 main branch | filled pill in the branch colour, white text, wraps at 220 px | Poppins SemiBold 17 |
| 2 sub point | text sitting on a coloured line (classic mind-map look), wraps at 210 px | Poppins Regular 14 |
| 3 detail | text on a thinner line, wraps at 200 px | Poppins Regular 13 |
| 4 | text on a line, wraps at 190 px | Poppins Regular 12 |

A `note` is drawn under the node's text in 11 px italic grey. `font_scale` (0.6-2.0) multiplies every size and the gaps; use 1.3-1.5 for a map with few nodes that will be projected, 0.8 for a dense one.

## Themes

| Theme | Background | Root | Branch colours |
|---|---|---|---|
| `rainbow` (default) | white | charcoal | one distinct colour per branch: blue, green, orange, purple, pink, cyan, amber, red |
| `blue` | very light blue | navy | shades of blue and teal |
| `pastel` | warm off-white | dark grey | soft pastel tones (coral, orange, yellow, mint, sky, lilac) |
| `dark` | navy-black | white pill with dark text | bright saturated colours, light text |
| `mono` | white | black | greys only, for printing in black and white |

Branch `i` gets colour `palette[i % len(palette)]`; all descendants of a branch use the branch's colour, so a reader can follow a branch by colour. A node with `"color": "#RRGGBB"` (JSON only) overrides the colour for its whole subtree.

## Title

`--title "..."` (or `"title"` in JSON) draws a small grey caption at the top-left corner, for a class name, source or date. It does not change the root text.

## Sizes for common uses

| Use | Suggestion |
|---|---|
| slide / projector | `--font-scale 1.4`, 4-6 branches, depth 2 |
| A4 print | default scale, `-o map.pdf` |
| chat / WhatsApp | `-o map.png` (scale 2), `--theme rainbow` |
| notes app (Notion, Obsidian) | `-o map.mmd` (Mermaid) or `.svg` |
| interactive exploration | `-o map.html` (pan, zoom, Fit, Save PNG) |
