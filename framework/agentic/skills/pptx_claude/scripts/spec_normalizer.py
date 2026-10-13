"""Parse and repair slide specs produced by LLMs (especially small local ones).

Nothing here needs third-party packages.

    slides, meta            = parse_slides(raw)          # str | list | dict -> list
    slides, theme, warnings = normalize_spec(slides, theme, valid_themes)

Design rule: never crash, never drop content silently.  Every repair is
reported in `warnings` so the caller (or the model) can see what was changed.

Typical small-model mistakes handled:
    - <think>...</think> blocks, prose or ``` fences around the JSON
    - trailing commas, smart quotes, Python literals (True/None, single quotes)
    - output cut off by the token limit (complete slides are kept)
    - {"slides": [...]} wrapper or a single slide object instead of an array
    - wrong layout names ("bullet_points", "two-column", "cta", "stats" ...)
    - wrong field names ("points", "items", "text", "body", "heading" ...)
    - wrong types (string instead of list, list of strings instead of objects,
      numbers as strings, Chart.js-style chart data ...)
    - too many items for one slide (bullets / table rows are split over
      continuation slides, other lists are trimmed with a warning)
"""

from __future__ import annotations

import ast
import difflib
import json
import math
import re

LAYOUTS = (
    "title", "bullets", "content", "two_column", "two_column_bullets", "table",
    "image", "image_bullets", "stat_callout", "section_divider", "quote",
    "agenda", "timeline", "icon_grid", "features_stats", "definition",
    "numbered_list", "conclusion_cta", "challenges", "chart",
)

LAYOUT_ALIASES = {
    "title_slide": "title", "cover": "title", "cover_slide": "title", "intro": "title",
    "opening": "title", "hero": "title",
    "bullet": "bullets", "bullet_points": "bullets", "bullet_list": "bullets",
    "bulleted_list": "bullets", "list": "bullets", "points": "bullets", "key_points": "bullets",
    "text": "content", "paragraph": "content", "body": "content", "text_slide": "content",
    "summary": "content", "overview": "content",
    "two_columns": "two_column", "twocolumn": "two_column", "2_column": "two_column",
    "2_columns": "two_column", "comparison": "two_column", "compare": "two_column",
    "versus": "two_column", "vs": "two_column", "columns": "two_column",
    "two_column_bullet": "two_column_bullets", "two_columns_bullets": "two_column_bullets",
    "comparison_bullets": "two_column_bullets", "pros_cons": "two_column_bullets",
    "pros_and_cons": "two_column_bullets",
    "tables": "table", "data_table": "table", "grid": "table", "matrix": "table",
    "picture": "image", "img": "image", "photo": "image", "figure": "image",
    "image_text": "image_bullets", "image_and_bullets": "image_bullets",
    "image_with_bullets": "image_bullets", "picture_bullets": "image_bullets",
    "stat": "stat_callout", "stats": "stat_callout", "statistics": "stat_callout",
    "metrics": "stat_callout", "kpi": "stat_callout", "kpis": "stat_callout",
    "numbers": "stat_callout", "big_number": "stat_callout", "big_numbers": "stat_callout",
    "stat_callouts": "stat_callout", "callout": "stat_callout",
    "section": "section_divider", "divider": "section_divider", "section_header": "section_divider",
    "section_title": "section_divider", "section_break": "section_divider", "chapter": "section_divider",
    "quotes": "quote", "quotation": "quote", "testimonial": "quote",
    "outline": "agenda", "toc": "agenda", "table_of_contents": "agenda", "contents": "agenda",
    "roadmap": "timeline", "process": "timeline", "steps": "timeline", "milestones": "timeline",
    "phases": "timeline", "journey": "timeline",
    "icons": "icon_grid", "icon_cards": "icon_grid", "cards": "icon_grid", "card_grid": "icon_grid",
    "features": "icon_grid", "feature_grid": "icon_grid", "benefits": "icon_grid", "pillars": "icon_grid",
    "feature_stats": "features_stats", "features_and_stats": "features_stats",
    "features_with_stats": "features_stats",
    "definitions": "definition", "concept": "definition", "what_is": "definition", "glossary": "definition",
    "numbered": "numbered_list", "numbered_steps": "numbered_list", "ordered_list": "numbered_list",
    "step_list": "numbered_list", "how_to": "numbered_list", "recommendations": "numbered_list",
    "conclusion": "conclusion_cta", "cta": "conclusion_cta", "call_to_action": "conclusion_cta",
    "closing": "conclusion_cta", "thank_you": "conclusion_cta", "thanks": "conclusion_cta",
    "next_steps": "conclusion_cta", "end": "conclusion_cta", "final": "conclusion_cta",
    "takeaways": "conclusion_cta", "key_takeaways": "conclusion_cta",
    "challenge": "challenges", "risks": "challenges", "risk": "challenges", "problems": "challenges",
    "issues": "challenges", "pain_points": "challenges", "obstacles": "challenges",
    "charts": "chart", "graph": "chart", "bar_chart": "chart", "line_chart": "chart",
    "pie_chart": "chart", "plot": "chart", "data_chart": "chart",
}

# layout implied by an alias such as "pie_chart"
_CHART_TYPE_FROM_LAYOUT = {"bar_chart": "bar", "line_chart": "line", "pie_chart": "pie"}

CHART_TYPES = ("bar", "line", "pie", "doughnut", "radar", "scatter", "area")
CHART_TYPE_ALIASES = {
    "column": "bar", "columns": "bar", "col": "bar", "bars": "bar", "histogram": "bar",
    "stacked_bar": "bar", "horizontal_bar": "bar", "hbar": "bar", "barh": "bar",
    "lines": "line", "trend": "line", "spline": "line",
    "donut": "doughnut", "ring": "doughnut", "circle": "pie", "pies": "pie",
    "spider": "radar", "web": "radar", "points": "scatter", "xy": "scatter",
    "areas": "area", "stacked_area": "area",
}
_HORIZONTAL_BAR = {"horizontal_bar", "hbar", "barh"}

# Max items that fit one slide.  bullets / table rows are split, others trimmed.
MAX_BULLETS = 6
MAX_TABLE_ROWS = 8
MAX_TABLE_COLS = 6
LIMITS = {
    ("stat_callout", "stats"): 4, ("agenda", "items"): 7, ("timeline", "steps"): 5,
    ("icon_grid", "cards"): 6, ("features_stats", "features"): 4, ("features_stats", "stats"): 3,
    ("definition", "cards"): 4, ("numbered_list", "items"): 6, ("conclusion_cta", "points"): 5,
    ("challenges", "items"): 4, ("two_column_bullets", "left_bullets"): 6,
    ("two_column_bullets", "right_bullets"): 6, ("image_bullets", "bullets"): 6,
    ("image", "bullets"): 5,
}

_TOP_LEVEL_ALIASES = {
    "layout": ("type", "slide_type", "layout_type", "slide_layout", "kind", "template"),
    "title": ("heading", "headline", "slide_title", "name"),
    "subtitle": ("sub_title", "subheading", "sub_heading", "tagline", "subheader"),
    "notes": ("speaker_notes", "note", "speakernotes", "presenter_notes"),
}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _strip_wrappers(text: str) -> str:
    text = text.lstrip("\ufeff").strip()
    # reasoning blocks from Qwen / DeepSeek style models
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S | re.I)
    text = re.sub(r"^.*?</think>", "", text, flags=re.S | re.I)  # unopened block
    fence = re.search(r"```(?:json|javascript|js|python)?\s*(.*?)```", text, flags=re.S | re.I)
    if fence:
        text = fence.group(1)
    else:
        text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.I)  # unclosed fence
    return text.strip()


def _outer_json(text: str) -> str:
    """Cut away prose before the first bracket and after the last one."""
    starts = [i for i in (text.find("["), text.find("{")) if i >= 0]
    if not starts:
        return text
    start = min(starts)
    end = max(text.rfind("]"), text.rfind("}"))
    return text[start:end + 1] if end > start else text[start:]


def _light_repairs(text: str) -> str:
    text = (text.replace("“", '"').replace("”", '"')
                .replace("‘", "'").replace("’", "'"))
    text = re.sub(r",\s*([\]}])", r"\1", text)          # trailing commas
    text = re.sub(r"^\s*//[^\n]*$", "", text, flags=re.M)  # // comments on own line
    return text


def _complete_objects(text: str) -> list:
    """Salvage the complete slide objects from JSON that was cut off.

    Works for a bare array and for a {"slides": [...]} wrapper: every closed
    {...} is recorded with its brace depth and the shallowest complete ones
    are the slides (their unfinished parents/siblings never close).
    """
    found: list[tuple[int, int, int]] = []  # (depth, start, end)
    stack: list[int] = []
    in_str = esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            stack.append(i)
        elif ch == "}" and stack:
            start = stack.pop()
            found.append((len(stack) + 1, start, i + 1))
    if not found:
        return []
    top = min(d for d, _, _ in found)
    out = []
    for depth, start, end in sorted(found, key=lambda x: x[1]):
        if depth != top:
            continue
        chunk = text[start:end]
        for cand in (chunk, _light_repairs(chunk)):
            try:
                obj = json.loads(cand)
                if isinstance(obj, dict):
                    out.append(obj)
                break
            except Exception:
                continue
    return out


def _loads_lenient(text: str):
    text = _strip_wrappers(text)
    if not text:
        raise ValueError("empty input")
    candidates = [text, _outer_json(text)]
    candidates += [_light_repairs(c) for c in list(candidates)]
    last_err = None
    for cand in candidates:
        try:
            return json.loads(cand)
        except Exception as e:  # noqa: PERF203
            last_err = e
    for cand in candidates:  # Python-literal style: single quotes, True/False/None
        try:
            return ast.literal_eval(cand)
        except Exception:
            pass
        try:
            py = re.sub(r"\btrue\b", "True", cand)
            py = re.sub(r"\bfalse\b", "False", py)
            py = re.sub(r"\bnull\b", "None", py)
            return ast.literal_eval(py)
        except Exception:
            pass
    # Output cut off by the token limit: keep the slides that are complete
    body = _outer_json(text)
    objs = _complete_objects(body)
    if objs:
        salvaged = {"slides": objs, "_truncated": True}
        head = body[:body.find("{", 1)] if body.startswith("{") else ""
        m = re.search(r'"theme"\s*:\s*"([^"]+)"', head)
        if m:
            salvaged["theme"] = m.group(1)
        return salvaged
    raise ValueError(f"could not parse JSON ({last_err})")


def parse_slides(raw) -> tuple[list, dict]:
    """Return (slides_list, meta).  meta may contain theme / filename / truncated."""
    meta: dict = {}
    data = raw
    for _ in range(3):  # strings may be double-encoded
        if isinstance(data, (bytes, bytearray)):
            data = data.decode("utf-8", errors="replace")
        if isinstance(data, str):
            data = _loads_lenient(data)
        else:
            break
    if isinstance(data, dict):
        if data.get("_truncated"):
            meta["truncated"] = True
        for key in ("slides", "deck", "presentation", "pages", "slide_list", "data"):
            inner = data.get(key)
            if isinstance(inner, dict) and isinstance(inner.get("slides"), list):
                data = dict(inner)
                inner = data.get("slides")
            if isinstance(inner, list):
                for mk in ("theme", "filename"):
                    if isinstance(data.get(mk), str):
                        meta[mk] = data[mk]
                data = inner
                break
        else:
            data = [data]  # a single slide object
    if not isinstance(data, list):
        raise ValueError("expected a JSON array of slide objects")
    return data, meta


# ---------------------------------------------------------------------------
# Small coercion helpers
# ---------------------------------------------------------------------------

def _s(v) -> str:
    """Anything -> clean string."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, (list, tuple)):
        return "\n".join(_s(x) for x in v if _s(x))
    if isinstance(v, dict):
        for k in ("text", "title", "label", "header", "name", "value", "content"):
            if v.get(k):
                rest = [_s(v[x]) for x in ("description", "body", "desc", "detail") if v.get(x)]
                return _s(v[k]) + (": " + rest[0] if rest else "")
        return "; ".join(f"{k}: {_s(x)}" for k, x in v.items() if _s(x))
    return str(v).strip()


def _first(d: dict, *keys, default=None):
    for k in keys:
        if k in d and d[k] not in (None, "", [], {}):
            return d[k]
    return default


def _as_list(v) -> list:
    if v is None or v == "":
        return []
    if isinstance(v, (list, tuple)):
        return list(v)
    if isinstance(v, str):
        parts = [p for p in re.split(r"\s*\n+\s*", v.strip()) if p]
        if len(parts) == 1 and v.count(";") >= 2:
            parts = [p.strip() for p in v.split(";") if p.strip()]
        return [re.sub(r"^\s*(?:[-*•·]|\d+[.)])\s+", "", p) for p in parts]
    if isinstance(v, dict):
        # {"1": "...", "2": "..."} or {"Point": "detail"}
        return [x if isinstance(x, (dict, list)) else f"{k}: {_s(x)}" if not str(k).isdigit() else _s(x)
                for k, x in v.items()]
    return [v]


def _to_number(v):
    if isinstance(v, bool):
        return float(v)
    if isinstance(v, (int, float)):
        return float(v) if math.isfinite(float(v)) else None
    if isinstance(v, str):
        t = v.strip().replace(",", "") if re.fullmatch(r"[-+]?[\d,]+(\.\d+)?\s*%?", v.strip()) else v.strip()
        m = re.search(r"[-+]?\d+(?:\.\d+)?", t.replace(" ", ""))
        if m:
            num = float(m.group(0))
            low = t.lower()
            for suffix, mult in (("k", 1e3), ("m", 1e6), ("b", 1e9)):
                if re.search(r"\d\s*" + suffix + r"\b", low):
                    num *= mult
                    break
            return num
    return None


def _chunks_balanced(items: list, size: int) -> list[list]:
    n = math.ceil(len(items) / size)
    per = math.ceil(len(items) / n)
    return [items[i:i + per] for i in range(0, len(items), per)]


def _bullet(v):
    """A bullet is a string, or {"text","icon","color"} when it has an icon."""
    if isinstance(v, dict):
        icon = _s(_first(v, "icon", "emoji"))
        text = _s({k: x for k, x in v.items() if k not in ("icon", "emoji", "color")})
        if "text" in v and not isinstance(v["text"], (dict, list)):
            text = _s(v["text"])
            extra = _s(_first(v, "description", "detail", "body"))
            if extra:
                text = f"{text}: {extra}"
        if icon:
            out = {"icon": icon, "text": text}
            if v.get("color"):
                out["color"] = _s(v["color"])
            return out
        return text
    return _s(v)


def _bullets(v) -> list:
    out = []
    for b in _as_list(v):
        if isinstance(b, (list, tuple)):  # nested bullets -> flatten
            out += [_bullet(x) for x in b]
        else:
            out.append(_bullet(b))
    return [b for b in out if (b.get("text") if isinstance(b, dict) else b)]


def _obj_list(v, str_key: str, mapping: dict, split_key: str | None = None) -> list[dict]:
    """List of dicts with canonical keys.

    mapping = {canonical_key: (alias, alias, ...)}; a plain string item becomes
    {str_key: item}.  "Header: body" strings are split into str_key/split_key
    when split_key is given.
    """
    out = []
    for item in _as_list(v):
        if isinstance(item, dict):
            d = {}
            for canon, aliases in mapping.items():
                val = _first(item, canon, *aliases)
                if val is not None:
                    d[canon] = _s(val)
            if d:
                out.append(d)
        else:
            text = _s(item)
            if not text:
                continue
            second = split_key
            m = re.match(r"^(.{2,60}?)\s*(?::| - | – | — )\s*(.+)$", text, flags=re.S)
            if m and second:
                out.append({str_key: m.group(1).strip(), second: m.group(2).strip()})
            else:
                out.append({str_key: text})
    return out


_CARD_MAP = {
    "icon": ("emoji", "icon_name"),
    "header": ("title", "name", "label", "heading"),
    "body": ("description", "text", "desc", "content", "detail", "subtitle"),
    "color": ("colour", "icon_color"),
}
_STAT_KEYS_VALUE = ("value", "number", "stat", "metric", "figure", "amount", "val")
_STAT_KEYS_LABEL = ("label", "name", "description", "text", "title", "caption", "desc")


def _stats(v) -> list[dict]:
    out = []
    if isinstance(v, dict) and not any(k in v for k in _STAT_KEYS_VALUE):
        v = [{"label": k, "value": x} for k, x in v.items()]  # {"Growth": "42%"}
    for item in _as_list(v):
        if isinstance(item, dict):
            value = _s(_first(item, *_STAT_KEYS_VALUE))
            label = _s(_first(item, *_STAT_KEYS_LABEL))
            if value or label:
                out.append({"value": value or "-", "label": label})
        else:
            text = _s(item)
            # "42% Growth" / "Growth: 42%"
            m = re.match(r"^([-+~<>$€£Rp.\s]*\d[\d.,]*\s*[%xXkKmMbB+]*\S*)\s+(.+)$", text)
            m2 = re.match(r"^(.+?)\s*[:=]\s*(\S.*)$", text)
            if m2 and re.search(r"\d", m2.group(2)) and len(m2.group(2)) <= 14:
                out.append({"value": m2.group(2).strip(), "label": m2.group(1).strip()})
            elif m:
                out.append({"value": m.group(1).strip(), "label": m.group(2).strip()})
            elif text:
                out.append({"value": text[:10], "label": text[10:].strip()})
    return out


# ---------------------------------------------------------------------------
# Layout detection
# ---------------------------------------------------------------------------

def _canon_layout(raw: str) -> tuple[str | None, str | None]:
    """(layout, note) - note explains a repair, None when the name was exact."""
    key = re.sub(r"[\s\-]+", "_", str(raw or "").strip().lower())
    key = re.sub(r"_?(slide|layout)$", "", key) or key
    if key in LAYOUTS:
        return key, (None if key == raw else f"layout {raw!r} -> {key!r}")
    if key in LAYOUT_ALIASES:
        return LAYOUT_ALIASES[key], f"layout {raw!r} -> {LAYOUT_ALIASES[key]!r}"
    close = difflib.get_close_matches(key, list(LAYOUTS) + list(LAYOUT_ALIASES), n=1, cutoff=0.78)
    if close:
        target = close[0] if close[0] in LAYOUTS else LAYOUT_ALIASES[close[0]]
        return target, f"layout {raw!r} -> {target!r}"
    return None, None


def _infer_layout(s: dict, index: int) -> str:
    has = lambda *ks: any(s.get(k) not in (None, "", [], {}) for k in ks)  # noqa: E731
    if has("chart_data", "chart_type", "datasets", "series"):
        return "chart"
    if has("headers", "rows", "columns"):
        return "table"
    if has("stats", "metrics", "kpis"):
        return "features_stats" if has("features") else "stat_callout"
    if has("quote"):
        return "quote"
    if has("steps", "milestones", "phases"):
        return "timeline"
    if has("definition"):
        return "definition"
    if has("cards"):
        return "icon_grid"
    if has("cta", "call_to_action"):
        return "conclusion_cta"
    if has("left_bullets", "right_bullets"):
        return "two_column_bullets"
    if has("left", "right"):
        return "two_column"
    if has("image_url", "image", "image_path"):
        return "image_bullets" if has("bullets") else "image"
    if has("section_number"):
        return "section_divider"
    if has("bullets", "points", "items"):
        return "bullets"
    if has("content", "text", "body"):
        return "content"
    return "title" if index == 0 else "content"


# ---------------------------------------------------------------------------
# Per-layout normalisers.  Each returns a clean dict (may change the layout).
# ---------------------------------------------------------------------------

def _n_title(s, w):
    return {"subtitle": _s(_first(s, "subtitle", "description", "content", "text", "author")),
            "icon": _s(s.get("icon")), "icon_color": _s(s.get("icon_color"))}


def _n_bullets(s, w):
    return {"bullets": _bullets(_first(s, "bullets", "points", "items", "content", "text",
                                       "body", "list", "key_points"))}


def _n_content(s, w):
    raw = _first(s, "content", "text", "body", "description", "paragraph", "paragraphs", "bullets", "points")
    if isinstance(raw, (list, tuple)) and len(raw) >= 3 and all(len(_s(x)) < 160 for x in raw):
        w("content was a list -> layout 'bullets'")
        return {"layout": "bullets", "bullets": _bullets(raw)}
    return {"content": _s(raw).replace("\n", "\n\n") if isinstance(raw, (list, tuple)) else _s(raw),
            "icon": _s(s.get("icon")), "icon_color": _s(s.get("icon_color"))}


def _side(s, side):
    """Collect one side of a two-column slide from the many shapes models emit."""
    block = s.get(f"{side}_column", s.get(f"{side}_side", s.get(f"column_{side}")))
    header = _first(s, f"{side}_header", f"{side}_title", f"{side}_heading", f"{side}_label")
    body = _first(s, side, f"{side}_content", f"{side}_text", f"{side}_body")
    bullets = _first(s, f"{side}_bullets", f"{side}_points", f"{side}_items")
    if isinstance(block, dict):
        header = header or _first(block, "header", "title", "heading", "label")
        bullets = bullets or _first(block, "bullets", "points", "items")
        body = body or _first(block, "content", "text", "body", "description")
    elif block is not None and body is None:
        body = block
    if isinstance(body, dict):
        header = header or _first(body, "header", "title", "heading", "label")
        bullets = bullets or _first(body, "bullets", "points", "items")
        body = _first(body, "content", "text", "body", "description")
    if isinstance(body, (list, tuple)) and bullets is None:
        bullets, body = body, None
    return _s(header), body, bullets


def _n_two_column(s, w, want_bullets=False):
    out = {}
    sides = {}
    cols = s.get("columns")
    if isinstance(cols, (list, tuple)) and len(cols) >= 2 and "left" not in s:
        s = dict(s, left_column=cols[0], right_column=cols[1])
    for side in ("left", "right"):
        sides[side] = _side(s, side)
        for k in ("icon", "color"):
            if s.get(f"{side}_{k}"):
                out[f"{side}_{k}"] = _s(s[f"{side}_{k}"])
    use_bullets = want_bullets or any(b for _, _, b in sides.values())
    for side, (header, body, bullets) in sides.items():
        out[f"{side}_header"] = header
        if use_bullets:
            out[f"{side}_bullets"] = _bullets(bullets if bullets else body)
        else:
            out[side] = _s(body)
    if use_bullets and not want_bullets:
        w("two_column with lists -> layout 'two_column_bullets'")
    out["layout"] = "two_column_bullets" if use_bullets else "two_column"
    return out


def _n_table(s, w):
    headers = _first(s, "headers", "columns", "header", "cols")
    rows = _first(s, "rows", "data", "body", "values", default=[])
    table = s.get("table")
    if isinstance(table, dict):
        headers = headers or _first(table, "headers", "columns")
        rows = rows or _first(table, "rows", "data", default=[])
    elif isinstance(table, list) and not rows:
        rows = table
    rows = [r for r in _as_list(rows) if r not in (None, "", [])] if not isinstance(rows, dict) else [rows]
    if rows and all(isinstance(r, dict) for r in rows):
        if not headers:
            headers = list(rows[0].keys())
        hdrs = [_s(h) for h in _as_list(headers)]
        rows = [[_s(r.get(h, "")) for h in hdrs] for r in rows]
    headers = [_s(h) for h in _as_list(headers)]
    clean = []
    for r in rows:
        if isinstance(r, str) and ("|" in r or "\t" in r):
            r = [c.strip() for c in re.split(r"\||\t", r.strip("| "))]
        clean.append([_s(c) for c in (r if isinstance(r, (list, tuple)) else [r])])
    rows = [r for r in clean if not all(re.fullmatch(r"[-: ]*", c) for c in r)]
    if not headers and rows:
        headers, rows = rows[0], rows[1:]
        w("table had no headers -> first row used as headers")
    if len(headers) > MAX_TABLE_COLS:
        w(f"table has {len(headers)} columns -> kept first {MAX_TABLE_COLS}")
        headers = headers[:MAX_TABLE_COLS]
    n = len(headers)
    rows = [(r + [""] * n)[:n] for r in rows]
    return {"headers": headers, "rows": rows}


def _n_image(s, w):
    return {"image_url": _s(_first(s, "image_url", "image", "image_path", "path", "src", "url", "chart_url")),
            "caption": _s(_first(s, "caption", "description", "subtitle")),
            "bullets": [b if isinstance(b, str) else b.get("text", "") for b in
                        _bullets(_first(s, "bullets", "points", "insights", "items"))]}


def _n_image_bullets(s, w):
    return {"image_url": _s(_first(s, "image_url", "image", "image_path", "path", "src", "url", "chart_url")),
            "bullets": _bullets(_first(s, "bullets", "points", "insights", "items", "content", "text"))}


def _n_stat_callout(s, w):
    return {"stats": _stats(_first(s, "stats", "metrics", "kpis", "statistics", "numbers", "items", "data"))}


def _n_section_divider(s, w):
    return {"section_number": _s(_first(s, "section_number", "number", "section", "index")),
            "subtitle": _s(_first(s, "subtitle", "description", "content", "text"))}


def _n_quote(s, w):
    q = _first(s, "quote", "text", "content", "body")
    attr = _first(s, "attribution", "author", "by", "source", "speaker", "name")
    if isinstance(q, dict):
        attr = attr or _first(q, "attribution", "author", "by", "source")
        q = _first(q, "quote", "text", "content")
    q = _s(q).strip().strip('"“”')
    return {"quote": q, "attribution": _s(attr), "context": _s(_first(s, "context", "role", "position"))}


def _n_agenda(s, w):
    items = _obj_list(_first(s, "items", "agenda", "topics", "sections", "bullets", "points"), "label", {
        "number": ("no", "index", "num"),
        "label": ("title", "name", "text", "topic", "header"),
        "duration": ("time", "minutes", "length"),
    })
    hi = s.get("highlight", -1)
    try:
        hi = int(hi)
    except Exception:
        hi = -1
    return {"items": items, "highlight": hi if 0 <= hi < len(items) else -1}


def _n_timeline(s, w):
    return {"steps": _obj_list(_first(s, "steps", "milestones", "phases", "events", "items", "timeline", "stages"),
                               "label", {
        "phase": ("date", "year", "time", "period", "quarter", "when", "stage"),
        "label": ("title", "name", "header", "step", "milestone"),
        "description": ("desc", "text", "body", "detail", "details", "content"),
    }, split_key="description")}


def _n_icon_grid(s, w):
    return {"cards": _obj_list(_first(s, "cards", "items", "features", "benefits", "pillars", "points", "bullets"),
                               "header", _CARD_MAP, split_key="body")}


def _n_features_stats(s, w):
    return {"features": _obj_list(_first(s, "features", "items", "cards", "points", "bullets"), "title", {
                "title": ("header", "name", "label", "feature"),
                "subtitle": ("tagline", "subheader"),
                "description": ("desc", "text", "body", "detail"),
            }, split_key="description"),
            "stats": _stats(_first(s, "stats", "metrics", "kpis", "statistics", "numbers"))}


def _n_definition(s, w):
    return {"definition": _s(_first(s, "definition", "text", "content", "description", "body")),
            "cards": _obj_list(_first(s, "cards", "items", "points", "features", "aspects"), "header", _CARD_MAP, split_key="body")}


def _n_numbered_list(s, w):
    return {"items": _obj_list(_first(s, "items", "steps", "points", "bullets", "list", "recommendations"), "title", {
        "number": ("no", "index", "num", "step"),
        "title": ("header", "label", "name", "heading", "text"),
        "description": ("desc", "body", "detail", "details", "content"),
    }, split_key="description")}


def _n_conclusion_cta(s, w):
    pts = [b if isinstance(b, str) else b.get("text", "") for b in
           _bullets(_first(s, "points", "bullets", "items", "takeaways", "key_points", "summary", "content"))]
    return {"points": pts, "cta": _s(_first(s, "cta", "call_to_action", "action", "next_step", "button"))}


def _n_challenges(s, w):
    return {"items": _obj_list(_first(s, "items", "challenges", "risks", "problems", "issues", "cards", "points",
                                      "bullets"), "title", {
                "title": ("header", "name", "label", "challenge", "risk"),
                "description": ("desc", "text", "body", "detail", "impact"),
                "color": ("colour",),
            }, split_key="description"),
            "tip": _s(_first(s, "tip", "solution", "mitigation", "note", "recommendation"))}


def _n_chart(s, w):
    raw_type = re.sub(r"[\s\-]+", "_", _s(_first(s, "chart_type", "type_of_chart", "kind", "chartType")).lower())
    raw_type = re.sub(r"_?chart$", "", raw_type)
    opts = dict(s.get("chart_options") or s.get("options") or {}) if isinstance(
        s.get("chart_options") or s.get("options") or {}, dict) else {}
    ctype = raw_type if raw_type in CHART_TYPES else CHART_TYPE_ALIASES.get(raw_type)
    if raw_type in _HORIZONTAL_BAR:
        opts.setdefault("bar_dir", "bar")
    if not ctype:
        if raw_type:
            w(f"chart_type {raw_type!r} unknown -> 'bar'")
        ctype = "bar"

    data = _first(s, "chart_data", "data", "series", "datasets")
    labels_top = _first(s, "labels", "categories", "x")
    if isinstance(data, dict):
        if isinstance(data.get("datasets"), list):            # Chart.js shape
            labels_top = labels_top or data.get("labels")
            data = data["datasets"]
        elif isinstance(data.get("series"), list):
            labels_top = labels_top or _first(data, "labels", "categories")
            data = data["series"]
        elif any(k in data for k in ("values", "data", "y")):
            data = [data]
        else:                                                   # {"Jan": 10, "Feb": 20}
            data = [{"name": _s(s.get("title")) or "Series 1",
                     "labels": list(data.keys()), "values": list(data.values())}]
    if data is None and s.get("values") is not None:
        data = [{"name": _s(s.get("title")) or "Series 1", "values": s["values"]}]
    if isinstance(data, list) and data and all(isinstance(x, dict) and ("label" in x or "name" in x)
                                               and not any(k in x for k in ("values", "data", "y"))
                                               and any(k in x for k in ("value", "count", "amount"))
                                               for x in data):
        # [{"label":"Jan","value":10}, ...]
        data = [{"name": _s(s.get("title")) or "Series 1",
                 "labels": [_s(_first(x, "label", "name")) for x in data],
                 "values": [_first(x, "value", "count", "amount") for x in data]}]

    series = []
    for i, ser in enumerate(data if isinstance(data, list) else []):
        if not isinstance(ser, dict):
            continue
        labels = _as_list(_first(ser, "labels", "categories", "x") or labels_top)
        values = [_to_number(v) for v in _as_list(_first(ser, "values", "data", "y", "numbers"))]
        if any(v is None for v in values):
            w("chart: non-numeric values replaced by 0")
            values = [0.0 if v is None else v for v in values]
        if not values:
            continue
        if not labels:
            labels = [str(n + 1) for n in range(len(values))]
        n = min(len(labels), len(values))
        if len(labels) != len(values):
            w(f"chart: {len(labels)} labels vs {len(values)} values -> trimmed to {n}")
        series.append({"name": _s(_first(ser, "name", "label", "title", "series")) or f"Series {i + 1}",
                       "labels": [_s(x) for x in labels[:n]], "values": values[:n]})
    if ctype in ("pie", "doughnut") and len(series) > 1:
        w(f"{ctype} chart takes one series -> kept the first")
        series = series[:1]
    if not series:
        w("chart had no usable chart_data -> layout 'content'")
        return {"layout": "content",
                "content": _s(_first(s, "content", "description", "caption")) or "Chart data was not provided."}
    return {"chart_type": ctype, "chart_data": series, "chart_options": opts}


_NORMALISERS = {
    "title": _n_title, "bullets": _n_bullets, "content": _n_content,
    "two_column": _n_two_column,
    "two_column_bullets": lambda s, w: _n_two_column(s, w, want_bullets=True),
    "table": _n_table, "image": _n_image, "image_bullets": _n_image_bullets,
    "stat_callout": _n_stat_callout, "section_divider": _n_section_divider, "quote": _n_quote,
    "agenda": _n_agenda, "timeline": _n_timeline, "icon_grid": _n_icon_grid,
    "features_stats": _n_features_stats, "definition": _n_definition,
    "numbered_list": _n_numbered_list, "conclusion_cta": _n_conclusion_cta,
    "challenges": _n_challenges, "chart": _n_chart,
}


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def normalize_theme(theme, valid: list[str], warnings: list[str]) -> str:
    key = re.sub(r"[^a-z]", "", str(theme or "").lower())
    if key in valid:
        return key
    close = difflib.get_close_matches(key, valid, n=1, cutoff=0.6)
    fallback = close[0] if close else valid[0]
    if theme:
        warnings.append(f"theme {theme!r} unknown -> {fallback!r} (valid: {', '.join(valid)})")
    return fallback


def normalize_spec(slides: list, theme: str, valid_themes: list[str]) -> tuple[list, str, list[str]]:
    warnings: list[str] = []
    theme = normalize_theme(theme, list(valid_themes), warnings)
    out: list[dict] = []

    for idx, raw in enumerate(slides):
        tag = f"slide {idx + 1}"
        if isinstance(raw, str) and raw.strip():
            raw = {"layout": "content", "title": raw.strip()[:80], "content": raw.strip()}
            warnings.append(f"{tag}: was plain text -> 'content' slide")
        if not isinstance(raw, dict):
            warnings.append(f"{tag}: not an object -> skipped")
            continue

        s = dict(raw)
        for canon, aliases in _TOP_LEVEL_ALIASES.items():
            if s.get(canon) in (None, ""):
                for a in aliases:
                    # "type" inside a chart slide means chart type, not layout
                    if a in s and isinstance(s[a], str) and s[a].strip():
                        if canon == "layout" and _canon_layout(s[a])[0] is None:
                            continue
                        s[canon] = s[a]
                        break

        def w(msg, _tag=tag):
            warnings.append(f"{_tag}: {msg}")

        raw_layout = s.get("layout")
        layout, note = _canon_layout(raw_layout) if raw_layout else (None, None)
        if note:
            w(note)
        if layout is None:
            layout = _infer_layout(s, idx)
            w(f"layout {raw_layout!r} unknown -> guessed {layout!r} from the fields"
              if raw_layout else f"no layout given -> guessed {layout!r} from the fields")
        raw_key = re.sub(r"[\s\-]+", "_", str(raw_layout or "").lower())
        if layout == "chart" and raw_key in _CHART_TYPE_FROM_LAYOUT and not s.get("chart_type"):
            s["chart_type"] = _CHART_TYPE_FROM_LAYOUT[raw_key]

        try:
            fields = _NORMALISERS[layout](s, w)
        except Exception as e:  # never let one bad slide kill the deck
            w(f"could not read fields ({type(e).__name__}: {e}) -> kept title only")
            fields = {}

        clean = {"layout": fields.pop("layout", layout), "title": _s(s.get("title"))}
        clean.update({k: v for k, v in fields.items() if v not in (None, "")})
        if _s(s.get("notes")):
            clean["notes"] = _s(s["notes"])
        if s.get("bg_override"):
            clean["bg_override"] = _s(s["bg_override"])
        layout = clean["layout"]

        if layout == "quote" and not clean.get("quote") and clean["title"]:
            clean["quote"] = clean["title"]
        if layout == "title" and not clean["title"]:
            clean["title"] = clean.get("subtitle") or "Presentation"

        # trim lists that cannot be split sensibly
        for (lay, field), limit in LIMITS.items():
            if lay == layout and isinstance(clean.get(field), list) and len(clean[field]) > limit:
                w(f"{field} has {len(clean[field])} items, max {limit} fit -> extra items dropped")
                clean[field] = clean[field][:limit]

        # split lists that can continue on the next slide
        if layout == "bullets" and len(clean.get("bullets", [])) > MAX_BULLETS:
            parts = _chunks_balanced(clean["bullets"], MAX_BULLETS)
            w(f"{len(clean['bullets'])} bullets -> split over {len(parts)} slides")
            for n, part in enumerate(parts):
                piece = dict(clean, bullets=part)
                if n:
                    piece["title"] = f"{clean['title']} (cont.)".strip()
                    piece.pop("notes", None)
                out.append(piece)
            continue
        if layout == "table" and len(clean.get("rows", [])) > MAX_TABLE_ROWS:
            parts = _chunks_balanced(clean["rows"], MAX_TABLE_ROWS)
            w(f"{len(clean['rows'])} table rows -> split over {len(parts)} slides")
            for n, part in enumerate(parts):
                piece = dict(clean, rows=part)
                if n:
                    piece["title"] = f"{clean['title']} (cont.)".strip()
                    piece.pop("notes", None)
                out.append(piece)
            continue

        out.append(clean)

    return out, theme, warnings
