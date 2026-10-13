"""OPTIONAL LangChain / LangGraph adapter for the pptx-claude engine.

Only import this file when `langchain-core` is installed.  The engine itself
(create_pptx.py) has no LangChain dependency.

    from langchain_tool import create_pptx_js        # a LangChain @tool
    agent = create_agent(model, tools=[create_pptx_js])

Environment variables (all optional):
    PPTX_OUTPUT_DIR   folder for generated decks          (default ./output)
    PPTX_IMAGE_DIRS   folders searched for image_url files (os.pathsep separated)
    PPTX_PUBLIC_URL   if set, the tool answers "file_url:<PPTX_PUBLIC_URL>/<file>"
                      instead of a local path (for web apps that serve the folder)

Upload hook: web apps can register a callable that stores the finished file
(S3, MinIO ...) and returns its URL:

    import langchain_tool
    langchain_tool.UPLOAD_HOOK = lambda path, filename, config: my_upload(path)
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

from create_pptx import create_pptx, format_result  # noqa: E402

# (path: Path, filename: str, config: dict | None) -> url or None
UPLOAD_HOOK: Optional[Callable] = None


@tool
def create_pptx_js(slides: str, filename: str, theme: str = "midnight",
                   config: RunnableConfig = None) -> str:
    """Create a PowerPoint (.pptx) file from a JSON array of slides.

    Every slide is an object with a "layout" and a "title". Core layouts:
      {"layout":"title","title":"...","subtitle":"..."}
      {"layout":"bullets","title":"...","bullets":["...","..."]}            (max 6)
      {"layout":"two_column","title":"...","left_header":"...","left":"...","right_header":"...","right":"..."}
      {"layout":"stat_callout","title":"...","stats":[{"value":"42%","label":"Growth"}]}  (max 4)
      {"layout":"table","title":"...","headers":["A","B"],"rows":[["1","2"]]}
      {"layout":"chart","title":"...","chart_type":"bar","chart_data":[{"name":"Sales","labels":["Jan","Feb"],"values":[10,20]}]}
      {"layout":"quote","quote":"...","attribution":"Name"}
      {"layout":"conclusion_cta","title":"...","points":["...","..."],"cta":"..."}
    More layouts: content, two_column_bullets, image, image_bullets, section_divider,
    agenda, timeline, icon_grid, features_stats, definition, numbered_list, challenges.

    Rules: start with "title", end with "conclusion_cta", do not use the same layout
    twice in a row, keep text short. Plain text only - no markdown.

    Args:
        slides:   JSON array of slide objects (a string).
        filename: Output file name, e.g. "report.pptx".
        theme:    midnight | coral | forest | ocean | charcoal | cherry.
    """
    safe = Path(str(filename or "presentation.pptx")).name
    unique = f"{uuid.uuid4().hex[:8]}_{safe}"
    res = create_pptx(slides, filename=unique, theme=theme)
    if not res.get("ok"):
        return format_result(res)

    path = Path(res["path"])
    url = None
    if UPLOAD_HOOK is not None:
        try:
            url = UPLOAD_HOOK(path, safe, config)
        except Exception as e:  # keep the local file if the upload fails
            res["warnings"].append(f"upload failed ({e}) - file kept locally")
    if not url and os.environ.get("PPTX_PUBLIC_URL"):
        url = os.environ["PPTX_PUBLIC_URL"].rstrip("/") + "/" + path.name

    text = format_result(res)
    return f"file_url:{url}\n{text}" if url else text
