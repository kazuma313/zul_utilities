"""OPTIONAL LangChain / LangGraph tool for the research-poster engine.

Needs `pip install langchain-core`.  The engine (build_poster.py) does not.

    from langchain_tool import create_research_poster
    tools = [create_research_poster]

Environment: PPTX_OUTPUT_DIR (default ./output), PPTX_IMAGE_DIRS, PPTX_PUBLIC_URL, POSTER_BROWSER.
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

from build_poster import build_poster, format_result  # noqa: E402

UPLOAD_HOOK: Optional[Callable] = None


@tool
def create_research_poster(poster: str, filename: str = "poster.pdf", config: RunnableConfig = None) -> str:
    """Create a one-page research poster (PDF) in the blue-and-white research style.

    `poster` is a JSON object:
    {"tag":"Research Project","title":"...","highlight":"one title word","subtitle":"...","footer":"email | site",
     "sections":[ ... 6 to 8 sections in this order ... ]}
    Section shapes:
      {"type":"text","title":"Research Overview","text":"..."}
      {"type":"bullets","title":"Objectives","items":[{"title":"...","text":"..."}]}          (2-5)
      {"type":"facts","title":"Target Audience","items":[{"label":"Age","value":"18-45"}]}   (2-6)
      {"type":"stats","title":"Key Findings","items":[{"label":"...","value":"72%","text":"..."}]}   (2-5)
      {"type":"chart","title":"Insights","chart":{"type":"donut","categories":["A","B"],"series":[{"name":"S","values":[60,40]}]},"text":"...","quote":"..."}
      {"type":"list","title":"Methods","items":[{"title":"...","text":"...","icon":"monitor"}]}   (2-4)
    Keep titles under 4 words, texts under 350 characters. Plain text only. Never invent numbers.

    Args:
        poster:   The JSON object above, as a string.
        filename: Output name, e.g. "poster.pdf" (.png or .html also work).
    """
    safe = Path(str(filename or "poster.pdf")).name
    res = build_poster(poster, filename=f"{uuid.uuid4().hex[:8]}_{safe}")
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
