# Troubleshooting

Run `python scripts/check_env.py --build` first.

| Message | Cause | Fix |
|---|---|---|
| `python-pptx is not installed` | package missing | `pip install python-pptx` |
| `Template not found` | `assets/template.pptx` missing | `python scripts/prepare_template.py "<original .pptx>"`, see `template_setup.md` |
| `template shape 'X' not found` | the template was edited (shape renamed, deleted, regrouped) | rebuild `assets/template.pptx` from the original file |
| `Template has N slides, 15 expected` | wrong or edited template | use the original 15-slide file |
| `Invalid JSON` | no parsable JSON in the input | return only JSON; use the JSON Schema with local models (`small_models.md`) |
| `JSON was cut off` | model hit its token limit | raise `max_tokens` / `num_predict` and the context window, or ask for fewer slides |
| `title ... is too long` | title does not fit even at the smallest size | at most 4 words |
| `text has N characters, about M fit` | text too long | shorten to the limit in `layouts.md` |
| `agenda has N items, 8 fit` | more than 8 content sections | merge sections, or accept that the agenda lists the first 8 |
| `image ... not found` | file does not exist | absolute path, or put the file next to the JSON, or set `PPTX_IMAGE_DIRS` |
| `no chart data - the ... card is empty` | `chart` missing or without numbers | add a `chart`, or use a layout without a chart (`section`, `three_cards`) |
| `Cannot write ... (is the file open in PowerPoint?)` | output file is open | close it or choose another name |
| Titles wrap differently on Mac / Google Slides / LibreOffice | embedded fonts are ignored there | install the fonts, see `template_setup.md` |
| PowerPoint asks to repair the file | should not happen | run with `--json`, keep the JSON and the message, and check the template was not edited |

## Flags

```
python scripts/build_deck.py deck.json -o out.pptx --json         # machine-readable result
python scripts/build_deck.py deck.json -o out.pptx --strict       # fail instead of repairing
python scripts/build_deck.py deck.json -o out.pptx --keep-order   # do not sort the sections
python scripts/build_deck.py deck.json -o out.pptx --no-agenda    # do not insert an agenda
python scripts/render_preview.py out.pptx --grid                  # PNG per slide + overview (needs LibreOffice)
```
