"""OPTIONAL LangChain / LangGraph tool for the mind-map engine (needs `pip install langchain-core`).

    from langchain_tool import create_mind_map
    tools = [create_mind_map]

Environment: PPTX_OUTPUT_DIR (default ./output), POSTER_BROWSER (browser for PNG/PDF), PPTX_PUBLIC_URL.
Upload hook (MinIO, S3 ...):  langchain_tool.UPLOAD_HOOK = lambda path, filename, config: url
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from langchain_core.runnables import RunnableConfig  # noqa: E402
from langchain_core.tools import tool  # noqa: E402

from build_mindmap import build_mindmap, format_result  # noqa: E402

UPLOAD_HOOK: Optional[Callable] = None


@tool
def create_mind_map(outline: str, filename: str = "mindmap.png", theme: str = "rainbow",
                    config: RunnableConfig = None) -> str:
    """Draw a mind map (PNG, SVG, PDF or HTML) from an outline of a lesson, article or topic.

    `outline` is Markdown: first line "# Root topic", then "- " bullets for the main
    branches (3-8), indented by two spaces per level for sub points (max 6 per parent,
    3 levels). Every line is a short phrase (max 8 words), never a sentence. Example:
      # Fotosintesis
      - Bahan
        - Cahaya matahari
        - Air dan CO2
      - Tahapan
        - Reaksi terang
        - Reaksi gelap
    JSON {"root": "...", "nodes": [{"text": "...", "children": [...]}]} is accepted too.

    Args:
        outline:  The outline text described above.
        filename: Output name; the extension picks the format (.png .svg .pdf .html .md).
        theme:    rainbow | blue | pastel | dark | mono.
    """
    safe = Path(str(filename or "mindmap.png")).name
    res = build_mindmap(outline, filename=f"{uuid.uuid4().hex[:8]}_{safe}", theme=theme, also=["svg"])
    if not res.get("ok"):
        return format_result(res)
    path, url = Path(res["path"]), None
    if UPLOAD_HOOK is not None:
        try:
            url = UPLOAD_HOOK(path, safe, config)
        except Exception as e:
            res["warnings"].append(f"upload failed ({e}) - file kept locally")
    if not url and os.environ.get("PPTX_PUBLIC_URL"):
        url = os.environ["PPTX_PUBLIC_URL"].rstrip("/") + "/" + path.name
    text = format_result(res)
    return f"file_url:{url}\n{text}" if url else text
