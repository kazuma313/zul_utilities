# Troubleshooting

Run `python scripts/check_env.py --build` first; it names the missing piece.

| Message / symptom | Cause | Fix |
|---|---|---|
| `ERROR: Could not read the mind map` | the text has no `#` root and no `- ` bullets, or the JSON has no recognisable node keys | Start with `# Topic`, then `- ` lines indented by two spaces. JSON: use `root` + `nodes` / `text` + `children` (see `references/formats.md`) |
| `WARNING: 'X': 9 branches -> 8` / `7 children -> 6` | more than the limits | merge or drop items, or move some into a deeper level |
| `text too long -> note` | a node over 90 characters | write a phrase, put the explanation in `(parentheses)` so it becomes a note on purpose |
| `deeper than 4 levels -> children folded into a note` | more than 3 levels below the root | flatten: promote a sub point to a branch |
| all sub points nested under the wrong branch | inconsistent indentation (3 spaces, mixed tabs) | use exactly two spaces per level; tabs are converted to four spaces |
| root is "Here is the mind map" or similar | the model wrote a preamble sentence and then several top-level bullets | remove the sentence, or make the topic a `#` line; a preamble with a single top-level item is repaired automatically |
| map is empty except the root | outline is a single paragraph, or every line ends with `.` and is over 140 characters | give real bullets; for raw text use `generate_mindmap.py` (with or without `--no-llm`) |
| `no browser found for PNG` | no Edge / Chrome / Chromium and no cairosvg | Windows: Edge is at `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`, set `POSTER_BROWSER` if elsewhere. Linux: `apt install chromium` or `pip install cairosvg`. Or open the `.html` and press Save PNG |
| PNG has a white strip at the bottom / right | Pillow missing, so the screenshot was not cropped | `pip install pillow` |
| PNG text looks different from SVG | the browser had no Poppins | fonts are embedded in the SVG; for PNG the same embedded CSS is used - this only happens with cairosvg, which ignores `@font-face`: install the Poppins font locally or use a browser |
| text overlaps between two branches | very long wrapped nodes next to each other | shorten those nodes, `--font-scale 0.9`, or `--layout right` |
| Indonesian words split at strange places | the wrapper breaks on spaces only; a single 30-letter token is wider than the box | add a space or hyphen, or lower `--font-scale` |
| `cannot read PDF` | no `pdftotext` and no `pypdf` | `pip install pypdf` (or install poppler and put `pdftotext` on PATH) |
| PDF text is garbage / empty | scanned PDF (images only) | OCR first (e.g. `ocrmypdf`), or paste the text |
| `cannot reach the model server` | Ollama / LM Studio not running or wrong port | `ollama serve`; LM Studio: start the local server and use `--api openai --base-url http://localhost:1234/v1`; or `--no-llm` |
| `model server answered HTTP 404` | the server has no model yet, or `--model` names one it does not have | `ollama pull gemma3:4b`, or leave `--model` out so an installed model is chosen |
| model answer contains `<think>` only, or nothing | the reasoning used up `--max-tokens` | leave `--think detect` (default), or raise `--max-tokens` |
| model writes sentences, map looks heavy | prompt rule 4 ignored (common on 4B models) | `--depth 2`, ask for "maksimal 6 kata per baris", or edit the saved outline (`--save-outline`) and rebuild |
| the `.md` output differs from my input | that is the cleaned tree after limits and repairs | intended; edit the `.md` and rebuild if a repair was wrong |
| `UnicodeEncodeError` on Windows console | code page 1252 | `set PYTHONIOENCODING=utf-8` or `chcp 65001`; the scripts already reconfigure stdout when possible |
| Mermaid `.mmd` does not render in Notion | node text contains `(`, `)`, `[` or `]` | the exporter already replaces brackets with spaces; check for very long lines and shorten them |

## Checks done for you

The parser strips `<think>...</think>`, code fences, ``` ```markdown ``` labels, `**bold**`, backticks and trailing colons; repairs JSON with trailing commas, single quotes and truncation; promotes the single child of an empty or prose root; enforces 8 branches, 6 children, depth 3, 90 characters. The renderer wraps text with real glyph widths so nodes never overflow their pills; siblings never overlap because subtrees are stacked by their measured height. PNG/PDF fall back to SVG when no renderer exists, and the function never raises.
