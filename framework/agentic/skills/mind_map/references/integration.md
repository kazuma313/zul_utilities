# Integration: Python API, LangChain, environment

## Python

```python
import sys
sys.path.insert(0, "skills/mind_map/scripts")          # or import via skills.mind_map.mind_map_skill
from build_mindmap import build_mindmap, format_result

res = build_mindmap(
    "# Fotosintesis\n- Bahan\n  - Cahaya\n  - Air\n- Hasil\n  - Glukosa\n  - Oksigen",
    filename="fotosintesis.png",      # extension picks the format: svg html png pdf md mmd json
    output_dir="output",              # default: $PPTX_OUTPUT_DIR or ./output; absolute filenames ignore it
    theme="rainbow",                  # rainbow | blue | pastel | dark | mono
    layout="radial",                  # radial | right
    title="Biologi kelas 8",          # small caption
    font_scale=1.0,                   # 0.6 - 2.0
    also=["svg", "md"],               # extra files next to the main one
    scale=2,                          # PNG pixel density
)
print(format_result(res))
# res = {"ok": True, "path": ".../fotosintesis.png", "files": {...}, "stats": {...}, "warnings": [...]}
```

`source` may be the outline text, a JSON string, a dict (already parsed JSON), or a Mermaid block. The function never raises; check `res["ok"]`.

Helpers:

```python
from extract_text import read_source              # .txt .md .docx .pdf .html or a folder -> text
from outline_from_text import outline_from_text   # text -> rule-based outline (no model)
from outline_parser import parse_mindmap, to_outline, to_mermaid
from render_svg import render, layout, THEMES     # lower level: tree dict -> SVG string

text = read_source("bab3.pdf")
outline = outline_from_text(text, max_branches=6, max_leaves=4)
root, meta, warnings = parse_mindmap(outline)
svg = render(root, theme="blue", layout_mode="right")
```

The entry shim `mind_map_skill.py` re-exports `build_mindmap`, `format_result`, `read_source`, `outline_from_text` and (when langchain-core is installed) the tool `create_mind_map`:

```python
from skills.mind_map.mind_map_skill import build_mindmap, create_mind_map
```

## LangChain / LangGraph

`scripts/langchain_tool.py` defines one tool:

```python
from langchain_tool import create_mind_map
agent = create_agent(model, tools=[create_mind_map], system_prompt=open("SKILL.md").read())
```

`create_mind_map(outline: str, filename: str = "mindmap.png", theme: str = "rainbow") -> str` builds the map (plus an SVG) and returns the `OK:` / `ERROR:` text the agent should relay. The docstring already teaches the outline format, so the tool works even when SKILL.md is not in the system prompt. Filenames get a random 8-character prefix so parallel calls never overwrite each other.

Uploading the file somewhere (MinIO, S3, a static folder served by FastAPI):

```python
import langchain_tool
langchain_tool.UPLOAD_HOOK = lambda path, filename, config: my_upload(path)   # return the public URL
```

The tool's reply then starts with `file_url:<url>`. Without a hook, `PPTX_PUBLIC_URL=https://host/files` is prefixed to the file name.

Recommended agent flow for "buatkan mind map dari materi ini": the agent (or a small model) writes the outline itself following SKILL.md, then calls `create_mind_map`. For long PDFs let a separate step call `read_source` and hand the text (or `outline_from_text`'s draft) to the model first.

## Command line

```
python scripts/build_mindmap.py map.md -o map.png --also svg,md --theme blue --layout right --title "Bab 3"
python scripts/build_mindmap.py - -o map.svg < outline.txt
python scripts/build_mindmap.py map.json -o map.html --json        # result as JSON on stdout
python scripts/generate_mindmap.py lesson.pdf -o lesson.png                 # model chosen automatically
python scripts/generate_mindmap.py lesson.pdf --no-llm -o lesson.svg --save-outline lesson.md
python scripts/extract_text.py lesson.docx > lesson.txt
python scripts/outline_from_text.py lesson.txt > outline.md
python scripts/check_env.py --build
```

Exit code 0 = file written, 1 = build failed, 2 = bad input / server unreachable.

## Environment variables

| Variable | Meaning | Default |
|---|---|---|
| `PPTX_OUTPUT_DIR` | folder for relative output names (shared with the other skills) | `./output` |
| `POSTER_BROWSER` | path to `msedge.exe` / `chrome.exe` / `chromium` used for PNG and PDF (shared with research_poster) | auto-detected |
| `PPTX_PUBLIC_URL` | base URL prefixed to the file name in the LangChain tool's reply | none |

Browser auto-detection order: `POSTER_BROWSER`, Edge and Chrome in the usual Windows locations, `chromium`, `chromium-browser`, `google-chrome`, `chrome`, `msedge` on PATH, Playwright's Chromium. Without any browser: `pip install cairosvg` (needs the cairo library) or use `.svg` / `.html` output and press Save PNG in the page.
