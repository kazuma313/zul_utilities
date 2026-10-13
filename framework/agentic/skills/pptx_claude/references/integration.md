# Integration

## Python

```python
import sys
sys.path.insert(0, "<skill folder>/scripts")
from create_pptx import create_pptx, format_result

result = create_pptx(
    slides,                       # JSON string, list of dicts, or {"theme":..., "slides":[...]}
    filename="report.pptx",       # relative names go to output_dir
    theme="ocean",
    output_dir="C:/decks",        # default: $PPTX_OUTPUT_DIR, else ./output
    image_dirs=["C:/charts"],     # extra folders searched for image_url
    strict=False,                 # True: any repair becomes an error
    allow_bg_override=False,
    keep_js=False,
)
# {"ok": True, "path": "...", "slides": 8, "theme": "ocean", "warnings": [...]}
# {"ok": False, "error": "...", "hint": "...", "warnings": [...]}
print(format_result(result))      # short text, suitable as a tool result for an LLM
```

`create_pptx()` never raises. Importing the module has no side effects (no folders are created).

Old import path still works: `from pptx_claude_skill import create_pptx, create_pptx_js`.

## Command line

```
python scripts/create_pptx.py slides.json -o deck.pptx --theme ocean [--json] [--strict] [--keep-js] [--allow-bg-override]
type slides.json | python scripts/create_pptx.py - -o deck.pptx        (stdin)
```

Exit code 0 = file created, 1 = error, 2 = spec file not found.

## Environment variables

| Variable | Meaning |
|---|---|
| `PPTX_NODE_DIR` | folder that contains `node_modules/pptxgenjs`. Default: searched in the skill folder, `scripts/`, the current folder and up to five parent folders of each |
| `PPTX_OUTPUT_DIR` | folder for relative output names. Default `./output` |
| `PPTX_IMAGE_DIRS` | extra image folders, separated by `;` on Windows and `:` elsewhere |
| `PPTX_PUBLIC_URL` | LangChain tool only: answer `file_url:<PPTX_PUBLIC_URL>/<file>` instead of a local path |

## LangChain / LangGraph

`scripts/langchain_tool.py` needs `pip install langchain-core`. The engine does not.

```python
from langchain_tool import create_pptx_js     # @tool with args: slides, filename, theme
tools = [create_pptx_js]
```

### Uploading the file (MinIO, S3 ...)

Version 1 of this skill uploaded to MinIO inside the tool through `app.agent.minio_connection`.
That import tied the skill to one application, so it was replaced by a hook:

```python
import langchain_tool
from app.agent.minio_connection import upload_file_to_minio

def upload(path, filename, config):
    thread_id = (config or {}).get("configurable", {}).get("thread_id", "")
    username = thread_id.split("__")[0] if "__" in thread_id else "anonymous"
    name = upload_file_to_minio(
        path.read_bytes(), username, filename,
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        folder="pptx",
    )
    return f"/api/files/{name}" if name else None

langchain_tool.UPLOAD_HOOK = upload
```

When the hook returns a URL the tool result starts with `file_url:<url>`, as before.
To serve files from a static folder instead, set `PPTX_OUTPUT_DIR=<app>/static/downloads`
and `PPTX_PUBLIC_URL=/static/downloads`.

## Other agent frameworks

Register one function with three string parameters (`slides`, `filename`, `theme`) that calls
`create_pptx()` and returns `format_result(...)`. Use the docstring of `create_pptx_js`
as the tool description. For small models read `references/small_models.md` first.

## Changes from version 1

| Area | Version 1 | Now |
|---|---|---|
| Dependencies | LangChain, MinIO client, the host app's folders | Python standard library + Node with pptxgenjs |
| Import side effects | created `app/static/downloads` three folders above the file | none |
| Icon packages | required; one bad icon name could drop icons | optional; unknown names fall back to a check mark |
| Input checking | `json.loads` only; wrong types crashed the layout code | lenient parser + normaliser, every repair reported |
| `bg_override` | documented, but always removed | off by default, `--allow-bg-override` to enable |
| `agenda` | rows ran off the bottom of the slide | fits the slide |
| `timeline` | first and last cards hung off the slide edges | inside the margins |
| `coral`, `forest` | near-white cards under near-white text on dark layouts; invisible second chart colour | readable card colour |
| Accent text on white cards | low contrast in `forest` and `cherry` | darker `accent_text` colour per theme |
| Colours | `"purple"` passed the 6-character check and corrupted the file | hex validated |
| `**bold**` bullets | rendered as `bold**` | markers removed |
| `image` slides | check icons never rendered; pictures stretched; only `/static/charts` | icons render; aspect ratio kept; any local path |
| Long titles and text | overflowed | font size steps down |
| Paths with `'` | broke the generated script | escaped with JSON |
| Result | `file_url:` string or free-text error | `{"ok", "path", "slides", "warnings"}` and `OK:` / `ERROR:` text |
