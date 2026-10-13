"""Entry point in the same style as the other skills in this folder.

    from skills.mind_map.mind_map_skill import build_mindmap, outline_from_text, read_source, create_mind_map

`create_mind_map` is a LangChain tool and is None when langchain-core is not installed.
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


_m = _load(["build_mindmap", "extract_text", "outline_from_text"], ["langchain_tool"])

build_mindmap = _m["build_mindmap"].build_mindmap
format_result = _m["build_mindmap"].format_result
read_source = _m["extract_text"].read_source
outline_from_text = _m["outline_from_text"].outline_from_text
create_mind_map = getattr(_m["langchain_tool"], "create_mind_map", None)

__all__ = ["build_mindmap", "format_result", "read_source", "outline_from_text", "create_mind_map"]
