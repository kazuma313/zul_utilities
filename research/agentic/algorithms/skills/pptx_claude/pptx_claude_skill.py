"""Backward-compatible entry point.

The implementation moved to `scripts/`:
    scripts/create_pptx.py      engine + CLI (no LangChain needed)
    scripts/langchain_tool.py   optional LangChain tool `create_pptx_js`

Old imports keep working:
    from skills.pptx_claude.pptx_claude_skill import create_pptx_js
"""

import importlib
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent / "scripts"


def _load(required, optional=()):
    """Import this skill's scripts without leaving their generic names behind.

    Every skill in this folder has scripts called langchain_tool, font_metrics, spec_normalizer ...
    Imported the plain way, the second skill loaded in a process gets the first skill's module:
    it fails, or its LangChain tool silently becomes None.  So same-named modules of other skills
    are set aside, ours are imported, and then ours leave sys.modules and sys.path again.  They
    stay alive through the names bound below.
    """
    own = {p.stem for p in _SCRIPTS.glob("*.py")}
    aside = {name: sys.modules.pop(name) for name in own if name in sys.modules}
    sys.path.insert(0, str(_SCRIPTS))
    loaded = {}
    try:
        for name in required:
            loaded[name] = importlib.import_module(name)
        for name in optional:
            try:
                loaded[name] = importlib.import_module(name)
            except ImportError:  # pragma: no cover - langchain-core is not installed
                loaded[name] = None
    finally:
        for name in own:
            sys.modules.pop(name, None)
        sys.modules.update(aside)
        while str(_SCRIPTS) in sys.path:
            sys.path.remove(str(_SCRIPTS))
    return loaded


_m = _load(["create_pptx"], ["langchain_tool"])

THEMES = _m["create_pptx"].THEMES
create_pptx = _m["create_pptx"].create_pptx
format_result = _m["create_pptx"].format_result
create_pptx_js = getattr(_m["langchain_tool"], "create_pptx_js", None)

__all__ = ["create_pptx", "format_result", "create_pptx_js", "THEMES"]
