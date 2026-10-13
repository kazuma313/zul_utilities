# Integration

## Python

```python
import sys
sys.path.insert(0, "<skill folder>/scripts")
from build_poster import build_poster, format_result

res = build_poster(spec, filename="poster.pdf", output_dir="C:/posters", image_dirs=["C:/photos"],
                   keep_order=False, strict=False, png=True)
# {"ok": True, "path": ".../poster.pdf", "files": {"html": ..., "pdf": ..., "png": ...}, "size": "A2",
#  "sections": 8, "order": [titles...], "warnings": [...]}
# {"ok": False, "error": "...", "hint": "...", "warnings": [...]}
print(format_result(res))       # short text, suitable as a tool result for an LLM
```

`spec` is a JSON string, a dict, or a list of sections. `build_poster()` never raises.
Old-style import: `from research_poster_skill import build_poster, create_research_poster`.

## Command line

```
python scripts/build_poster.py poster.json -o poster.pdf [--png] [--keep-order] [--strict] [--json]
type poster.json | python scripts/build_poster.py - -o poster.pdf
```

Exit code 0 = created (at least the HTML), 1 = error, 2 = spec file not found.

## Environment variables

| Variable | Meaning |
|---|---|
| `POSTER_BROWSER` | path to a Chromium browser executable (msedge.exe, chrome.exe, chromium) |
| `PPTX_OUTPUT_DIR` | folder for relative output names, default `./output` |
| `PPTX_IMAGE_DIRS` | extra image folders, `;`-separated on Windows |
| `PPTX_PUBLIC_URL` | LangChain tool only: answer `file_url:<PPTX_PUBLIC_URL>/<file>` |

## LangChain / LangGraph

`scripts/langchain_tool.py` needs `pip install langchain-core`; the engine does not.

```python
from langchain_tool import create_research_poster      # @tool with args: poster, filename
```

Upload hook (MinIO, S3 ...): `langchain_tool.UPLOAD_HOOK = lambda path, filename, config: url`.
The tool then returns `file_url:<url>` on the first line, as the other skills in this folder do.

## Other frameworks

Register a function with two string parameters (`poster`, `filename`) that calls `build_poster()` and returns `format_result(...)`. Use the docstring of `create_research_poster` as the tool description. For small models read small_models.md first.
