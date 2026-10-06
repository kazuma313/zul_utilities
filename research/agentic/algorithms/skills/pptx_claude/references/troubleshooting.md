# Troubleshooting

Run `python scripts/check_env.py --build` first. It tests everything below.

| Message | Cause | Fix |
|---|---|---|
| `Node.js is not installed or not on PATH` | Node missing, or the terminal was opened before installing | Install Node 18+ from https://nodejs.org, open a new terminal |
| `npm package pptxgenjs was not found` | `npm install` not run, or run in another folder | `cd` to the skill folder (where `package.json` is) and run `npm install`. Or set `PPTX_NODE_DIR` to a folder that contains `node_modules/pptxgenjs` |
| `icons disabled (optional packages ...)` | react / react-dom / react-icons / sharp missing | `npm install` in the skill folder. On Windows `sharp` needs a 64-bit Node |
| `icon "X" not found ... used FaCheckCircle` | the model invented an icon name | use names from `references/icons.md` |
| `Invalid slides JSON` | the text contains no parsable JSON | make the model return only JSON; use the JSON Schema (see `references/small_models.md`) |
| `JSON was cut off (token limit?)` | model stopped mid-answer | raise `max_tokens` / `num_predict` (4096+) and the context window (8192+), or ask for fewer slides |
| `No usable slides in the spec` | empty array, or items are not objects | every slide is `{"layout": "...", ...}` |
| `image not found: ...` | `image_url` is not an existing local file | use an absolute path, put the file next to the spec, or set `PPTX_IMAGE_DIRS` |
| `pptxgenjs failed: ...` | bug or unexpected value | run with `--keep-js`; the generated script is saved as `<output>.build.js`; run `node` on it to see the line |
| PowerPoint says the file needs repair | should not happen: control characters and bad colours are removed | run with `--keep-js` and report the spec |
| Text overflows a box | too much text for the layout | shorten the text or split the slide; limits are in `references/layouts.md` |
| `UnicodeEncodeError` in a Windows terminal | console code page | `set PYTHONIOENCODING=utf-8`, or use `--json` |
| LibreOffice not found (`render_preview.py`) | optional tool missing | install LibreOffice, or open the .pptx by hand |

## Debug flags

```
python scripts/create_pptx.py slides.json -o deck.pptx --json      # machine-readable result
python scripts/create_pptx.py slides.json -o deck.pptx --strict    # fail instead of repairing
python scripts/create_pptx.py slides.json -o deck.pptx --keep-js   # keep the generated Node script
python scripts/render_preview.py deck.pptx --grid                  # PNG per slide + overview
```
