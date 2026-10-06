"""Entry point in the same style as the other skills in this folder.

    from skills.resaerch_poster.research_poster_skill import build_poster, create_research_poster

`create_research_poster` is a LangChain tool and is None when langchain-core is not installed.
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


_m = _load(["build_poster"], ["langchain_tool"])

build_poster = _m["build_poster"].build_poster
format_result = _m["build_poster"].format_result
create_research_poster = getattr(_m["langchain_tool"], "create_research_poster", None)

__all__ = ["build_poster", "format_result", "create_research_poster"]
