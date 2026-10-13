"""OPTIONAL LangChain / LangGraph tool for the pptx-research engine.

Needs `pip install langchain-core`.  The engine (build_deck.py) does not.

    from langchain_tool import create_research_pptx
    tools = [create_research_pptx]

Environment: PPTX_OUTPUT_DIR (default ./output), PPTX_IMAGE_DIRS, PPTX_PUBLIC_URL.
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

from build_deck import build_deck, format_result  # noqa: E402

UPLOAD_HOOK: Optional[Callable] = None


@tool
def create_research_pptx(deck: str, filename: str, config: RunnableConfig = None) -> str:
    """Create a research-proposal PowerPoint (.pptx) in the black-and-white template.

    `deck` is a JSON object: {"organization":"...","tagline":"...","slides":[...]}.
    Slides, in order (skip the ones without material; do NOT write an agenda, it is automatic):
      {"layout":"cover","title":"...","subtitle":"Research Proposal","presenter":"..."}
      {"layout":"intro","title":"Hello !","lead":"...","paragraphs":["...","..."]}
      {"layout":"section","title":"Background of the Study","text":"..."}
      {"layout":"three_cards","title":"Problem Statement","text":"...","cards":[{"header":"...","body":"..."}]}   (3 cards)
      {"layout":"two_cards","title":"Methodology","text":"...","cards":[{"header":"...","body":"..."}]}           (2 cards)
      {"layout":"chart","title":"...","text":"...","chart":{"type":"column","categories":["A","B"],"series":[{"name":"S","values":[1,2]}]}}
      {"layout":"timeline","title":"Proposed Timeline","columns":[{"header":"Jan - Mar","items":["...","..."]}]}  (max 4 columns, 2 items)
      {"layout":"stat_chart","title":"...","text":"...","stat":"65%","stat_text":"...","chart":{...}}
      {"layout":"closing","title":"Thank You","subtitle":"..."}
    More layouts: team, people, analysis, gallery, testimonials.
    Keep titles under 5 words and texts under 450 characters. Plain text only. Never invent numbers.

    Args:
        deck:     The JSON object described above, as a string.
        filename: Output file name, e.g. "proposal.pptx".
    """
    safe = Path(str(filename or "research_deck.pptx")).name
    res = build_deck(deck, filename=f"{uuid.uuid4().hex[:8]}_{safe}")
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
