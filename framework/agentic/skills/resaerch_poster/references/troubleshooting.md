# Troubleshooting

Run `python scripts/check_env.py --build` first.

| Message | Cause | Fix |
|---|---|---|
| `no Chromium browser found - only the HTML was written` | no Edge / Chrome / Chromium on PATH or in the usual folders | install Edge or Chrome, or `pip install playwright` then `playwright install chromium`, or set `POSTER_BROWSER` to the browser executable |
| `browser did not write poster.pdf` | the browser refused to run headless (old version, sandbox) | update the browser; try `POSTER_BROWSER` pointing to another one; open the HTML and print to PDF manually |
| `Invalid JSON` | no parsable JSON | return only JSON; use the JSON Schema with local models |
| `JSON was cut off` | model hit its token limit | raise `max_tokens` and the context window, or ask for fewer sections |
| `No usable sections` | empty `sections` or wrong shapes | every section is `{"type": "...", "title": "...", ...}` |
| `... has N characters, about M fit - it will be shrunk` | text longer than the card | shorten to the limit in sections.md |
| `N sections, 8 fit on one page -> extra sections dropped` | too many sections | merge sections |
| `only N sections` | fewer than 4 | add sections; the poster works but looks sparse |
| `image ... not found` | file missing | absolute path, or put the file next to the JSON, or set `PPTX_IMAGE_DIRS` |
| `chart has no usable numbers` | values missing or not numeric | give `categories` and numeric `values` |
| Title overlaps the picture | more than 12 words | shorten the title, or put the long part in `subtitle` |
| Card text very small | too much content for 8 sections | shorten texts, drop items, or use 6 sections (3 rows = larger base font) |
| PDF has 2 pages or white margins | printed manually with margins | in the browser's print dialog choose the paper size of the poster and margins "none" |

## Flags

```
python scripts/build_poster.py poster.json -o poster.pdf --png     # PDF + PNG preview
python scripts/build_poster.py poster.json -o poster.html          # HTML only
python scripts/build_poster.py poster.json -o poster.pdf --json    # machine-readable result
python scripts/build_poster.py poster.json -o poster.pdf --strict  # fail instead of repairing
python scripts/build_poster.py poster.json -o poster.pdf --keep-order
```
