"""Parse a mind map written as JSON *or* as an indented outline, and clean it.

Python standard library only.

    tree, meta, warnings = parse_mindmap(raw)

Accepted input
--------------
JSON:   {"title": "...", "root": "...", "theme": "...", "nodes": [{"text": "...", "children": [...]}]}
        also {"root": {"text": "...", "children": [...]}}, {"name","children"}, {"label","items"},
        {"topic","subtopics"}, a bare list of nodes, plain strings as leaves ...
Outline (what small models write best):
        # Photosynthesis            <- root (first heading, or first line)
        ## Definition               <- level-1 branch (headings)
        - converts light to sugar   <- deeper levels by indentation (2 spaces or a tab)
          - happens in chloroplasts
        1. Stages                   <- numbered lists work too
Mermaid `mindmap` blocks are also accepted (indentation based).

Guarantees: one root, 1-8 branches, at most 6 children per node, depth at most 4,
node texts at most 90 characters (the rest becomes a note).  Every repair is
listed in `warnings`.
"""

from __future__ import annotations

import ast
import json
import re

MAX_BRANCHES = 8
MAX_CHILDREN = 6
MAX_DEPTH = 4          # root = 0
MAX_TEXT = 90

_BULLET = re.compile(r"^(\s*)(?:[-*+•◦–—>]|\d+[.)]|[a-zA-Z][.)]|\(\d+\))\s+(.*)$")
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


# ---------------------------------------------------------------------------
# Lenient JSON
# ---------------------------------------------------------------------------

def _strip_wrappers(text: str) -> str:
    text = text.lstrip("\ufeff").strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S | re.I)
    text = re.sub(r"^.*?</think>", "", text, flags=re.S | re.I)
    m = re.search(r"```(?:json|markdown|md|mermaid|text)?\s*\n(.*?)```", text, flags=re.S | re.I)
    if m:
        text = m.group(1)
    else:
        text = re.sub(r"^```\w*\s*", "", text)
    return text.strip()


def _loads_lenient(text: str):
    cands = [text]
    start = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=-1)
    if start >= 0:
        end = max(text.rfind("}"), text.rfind("]"))
        cands.append(text[start:end + 1] if end > start else text[start:])
    fixed = []
    for c in cands:
        c2 = (c.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'"))
        c2 = re.sub(r",\s*([\]}])", r"\1", c2)
        fixed.append(c2)
    for c in cands + fixed:
        try:
            return json.loads(c)
        except Exception:
            pass
    for c in cands + fixed:
        try:
            return ast.literal_eval(re.sub(r"\b(true|false|null)\b", lambda m: {"true": "True", "false": "False", "null": "None"}[m.group(1)], c))
        except Exception:
            pass
    return None


# ---------------------------------------------------------------------------
# Outline text -> tree
# ---------------------------------------------------------------------------

def _clean_text(t: str) -> str:
    t = re.sub(r"\*\*(.+?)\*\*|__(.+?)__|`(.+?)`", lambda m: m.group(1) or m.group(2) or m.group(3), t)
    t = re.sub(r"^\s*(?:[-*+•]|\d+[.)])\s+", "", t)
    t = re.sub(r"\s+", " ", t).strip(" \t:;")
    return t


_PROSE = re.compile(r"^(here|below|the following|this is|berikut|ini adalah|inilah|peta pikiran|mind ?map)\b", re.I)


_NOTE = re.compile(r"^(.*?\S)\s*(?:\(([^()]{8,}?)\)|\s[-\u2013\u2014]\s+(.{3,}))$")


def _split_note(txt: str) -> tuple[str, str]:
    """'Reaksi terang (di tilakoid)' / 'Reaksi terang - di tilakoid' -> ('Reaksi terang', 'di tilakoid')."""
    m = _NOTE.match(txt)
    if m and len(m.group(1)) >= 2:
        return m.group(1).strip(), (m.group(2) or m.group(3) or "").strip()
    return txt, ""


def _node(txt: str) -> dict:
    txt, note = _split_note(txt)
    node = {"text": txt, "children": []}
    if note:
        node["note"] = note
    return node


def parse_outline(text: str) -> dict:
    """Indented bullets / headings -> nested dict tree (root at top).

    Headings nest by their number of #, bullets by indentation; bullets always
    belong to the nearest heading above them."""
    lines = [ln.rstrip() for ln in text.replace("\t", "    ").splitlines()]
    if any(re.match(r"^\s*mindmap\s*$", ln) for ln in lines[:3]):        # mermaid
        lines = [ln for ln in lines if not re.match(r"^\s*mindmap\s*$", ln)]
        lines = [re.sub(r"\)\)|\(\(|\]\]|\[\[|\{\{|\}\}|[()\[\]]", " ", ln).rstrip() for ln in lines]
        lines = [re.sub(r"^(\s*)root\s+", r"\1", ln) for ln in lines]
    root = {"text": "", "children": []}
    stack: list[tuple[float, dict]] = [(-1000, root)]      # (level, node); headings < 0 <= bullets
    for raw in lines:
        if not raw.strip():
            continue
        hm = _HEADING.match(raw)
        if hm:
            level = -100 + len(hm.group(1))
            txt = _clean_text(hm.group(2))
            if not txt:
                continue
            if not root["text"] and not root["children"]:
                root["text"] = txt
                continue
            node = _node(txt)
            while len(stack) > 1 and stack[-1][0] >= level:
                stack.pop()
            stack[-1][1]["children"].append(node)
            stack.append((level, node))
            continue
        bm = _BULLET.match(raw)
        if bm:
            indent, txt = len(bm.group(1)), _clean_text(bm.group(2))
        else:
            indent, txt = len(raw) - len(raw.lstrip()), _clean_text(raw.strip())
            if not root["text"] and not root["children"]:
                root["text"] = txt              # first plain line is the root
                continue
            if len(txt) > 140 and indent == 0:  # a paragraph, not an outline line
                continue
        if not txt:
            continue
        node = _node(txt)
        while len(stack) > 1 and stack[-1][0] >= 0 and stack[-1][0] >= indent:
            stack.pop()
        stack[-1][1]["children"].append(node)
        stack.append((float(indent), node))
    # "Here is the mind map:" followed by one top-level item -> that item is the root
    if root["text"] and (root["text"].endswith(":") or _PROSE.match(root["text"])):
        if len(root["children"]) == 1:
            root = root["children"][0]
        else:
            root["text"] = ""
    if not root["text"] and len(root["children"]) == 1:
        root = root["children"][0]
    return {"title": "", "root": root}


# ---------------------------------------------------------------------------
# JSON shapes -> tree
# ---------------------------------------------------------------------------

_TEXT_KEYS = ("text", "name", "label", "title", "topic", "node", "value", "key")
_CHILD_KEYS = ("children", "nodes", "items", "subtopics", "branches", "sub", "kids", "points", "leaves")


def _to_node(obj, warn) -> dict | None:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float)):
        t = _clean_text(str(obj))
        return {"text": t, "children": []} if t else None
    if isinstance(obj, list):
        kids = [n for n in (_to_node(x, warn) for x in obj) if n]
        return {"text": "", "children": kids}
    if isinstance(obj, dict):
        text = ""
        for k in _TEXT_KEYS:
            if isinstance(obj.get(k), (str, int, float)) and str(obj[k]).strip():
                text = _clean_text(str(obj[k]))
                break
        kids_raw = None
        for k in _CHILD_KEYS:
            if k in obj and obj[k] not in (None, ""):
                kids_raw = obj[k]
                break
        if kids_raw is None and not text and len(obj) >= 1:
            # {"Topic": ["a", "b"], "Other": {...}} style
            kids = []
            for k, v in obj.items():
                sub = _to_node(v, warn)
                node = {"text": _clean_text(str(k)), "children": sub["children"] if sub and not sub["text"] else ([sub] if sub else [])}
                kids.append(node)
            return {"text": "", "children": kids}
        kids: list[dict] = []
        if isinstance(kids_raw, dict):
            sub = _to_node(kids_raw, warn)
            kids = sub["children"] if sub and not sub["text"] else ([sub] if sub else [])
        elif isinstance(kids_raw, list):
            for x in kids_raw:
                n = _to_node(x, warn)
                if n and n["text"]:
                    kids.append(n)
                elif n:
                    kids.extend(n["children"])
        elif isinstance(kids_raw, str):
            kids = [{"text": _clean_text(x), "children": []} for x in re.split(r"[\n;]+", kids_raw) if _clean_text(x)]
        node = {"text": text, "children": kids}
        for extra in ("note", "icon", "color", "url"):
            if isinstance(obj.get(extra), str) and obj[extra].strip():
                node[extra] = obj[extra].strip()
        return node
    return None


# ---------------------------------------------------------------------------
# Public
# ---------------------------------------------------------------------------

def _merge_repeats(node: dict, warn) -> None:
    """Siblings with the same text become one node that keeps the children of both.

    A small model that runs out of ideas repeats branches it already wrote (seen with qwen3:4b:
    26 main branches, most of them the same five again)."""
    first: dict[str, dict] = {}
    for kid in node.get("children") or []:
        seen = first.setdefault(kid["text"].casefold(), kid)
        if seen is not kid:
            seen.setdefault("children", []).extend(kid.get("children") or [])
            warn(f"{kid['text']!r} written twice under {node.get('text') or 'root'!r} -> merged")
    node["children"] = list(first.values())
    for kid in node["children"]:
        _merge_repeats(kid, warn)


def _limit(node: dict, depth: int, warn) -> None:
    kids = node.get("children") or []
    cap = MAX_BRANCHES if depth == 0 else MAX_CHILDREN
    if len(kids) > cap:
        warn(f"{node['text'] or 'root'!r}: {len(kids)} children, {cap} fit -> extra merged into the last one")
        keep, extra = kids[:cap - 1], kids[cap - 1:]
        merged = {"text": extra[0]["text"], "children": []}
        for e in extra:
            merged["children"].extend([e] if e is not extra[0] else e["children"])
        kids = keep + [merged]
    if depth >= MAX_DEPTH:
        if kids:
            warn(f"{node['text']!r}: deeper than {MAX_DEPTH} levels -> children folded into a note")
            node["note"] = (node.get("note", "") + " " + "; ".join(k["text"] for k in kids)).strip()
            kids = []
    node["children"] = kids
    t = node.get("text", "")
    if len(t) > MAX_TEXT:
        cut = t[:MAX_TEXT].rsplit(" ", 1)[0]
        if len(cut) < 20:
            cut = t[:MAX_TEXT]
        rest = t[len(cut):].strip(" ,;:-")
        node["text"] = cut.rstrip(" ,;:-")
        if rest and not node.get("note"):
            node["note"] = rest
        elif rest:
            node["note"] = rest + " " + node["note"]
        warn(f"text shortened: {t[:40]!r}...")
    for k in kids:
        _limit(k, depth + 1, warn)


def _count(node: dict) -> int:
    return 1 + sum(_count(k) for k in node.get("children", []))


def parse_mindmap(raw) -> tuple[dict, dict, list[str]]:
    """Return (root_node, meta, warnings).  meta: title, theme, language, layout, notes."""
    warnings: list[str] = []
    warn = lambda m: warnings.append(m) if m not in warnings else None  # noqa: E731
    meta: dict = {}
    data = raw
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="replace")
    if isinstance(raw, str):
        text = _strip_wrappers(raw)
        data = _loads_lenient(text) if text[:1] in "{[" else None
        if isinstance(data, str):
            data = None
        if data is None:
            tree = parse_outline(text)
            root = tree["root"]
            if not root["text"] and not root["children"]:
                raise ValueError("no outline found - give an indented list, headings, or JSON")
            if not root["text"]:
                root["text"] = "Mind map"
                warn("no root line -> 'Mind map' used as the centre")
            meta["source"] = "outline"
            _merge_repeats(root, warn)
            _limit(root, 0, warn)
            return root, meta, warnings

    if isinstance(data, dict):
        for k in ("title", "theme", "language", "lang", "layout", "subtitle", "font_scale"):
            if k in data and isinstance(data[k], (str, int, float)):
                meta["language" if k == "lang" else k] = data[k]
        body = data
        for key in ("mindmap", "mind_map", "map", "data", "tree"):
            if isinstance(data.get(key), (dict, list)):
                body = data[key]
                break
        root = None
        if isinstance(body, dict):
            r = body.get("root")
            if isinstance(r, dict):
                root = _to_node(r, warn)
                if root and not root["children"]:
                    for k in _CHILD_KEYS:
                        if isinstance(body.get(k), list):
                            root["children"] = _to_node(body[k], warn)["children"]
                            break
            elif isinstance(r, str) or any(k in body for k in _CHILD_KEYS) or any(k in body for k in _TEXT_KEYS):
                root = _to_node(body, warn)
                if isinstance(r, str) and root is not None:
                    root["text"] = _clean_text(r)
            else:
                root = _to_node({k: v for k, v in body.items() if k not in meta}, warn)
        elif isinstance(body, list):
            root = _to_node(body, warn)
    elif isinstance(data, list):
        root = _to_node(data, warn)
    else:
        raise ValueError("unsupported input type")
    if not root:
        raise ValueError("no nodes found")
    if not root["text"]:
        if len(root["children"]) == 1:
            root = root["children"][0]
        else:
            root["text"] = _clean_text(str(meta.get("title") or "Mind map"))
            if not meta.get("title"):
                warn("no root text -> 'Mind map' used as the centre")
    meta["source"] = "json"
    _merge_repeats(root, warn)
    _limit(root, 0, warn)
    if _count(root) < 4:
        warn("very small map (fewer than 4 nodes)")
    return root, meta, warnings


def to_outline(root: dict) -> str:
    """Tree -> Markdown outline (round-trips through parse_outline)."""
    lines = [f"# {root['text']}"]

    def walk(node, depth):
        for k in node.get("children", []):
            note = f"  ({k['note']})" if k.get("note") else ""
            lines.append("  " * (depth - 1) + f"- {k['text']}{note}")
            walk(k, depth + 1)
    walk(root, 1)
    return "\n".join(lines) + "\n"


def to_mermaid(root: dict) -> str:
    def esc(t):
        return re.sub(r"[()\[\]{}]", " ", t).strip()
    lines = ["mindmap", f"  root(({esc(root['text'])}))"]

    def walk(node, depth):
        for k in node.get("children", []):
            lines.append("  " * (depth + 1) + esc(k["text"]))
            walk(k, depth + 1)
    walk(root, 1)
    return "\n".join(lines) + "\n"
