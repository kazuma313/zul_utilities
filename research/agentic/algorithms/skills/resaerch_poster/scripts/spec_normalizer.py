"""Parse and repair poster specs written by LLMs (small local models included).

Python standard library only.

    poster, meta      = parse_spec(raw)                   # str | dict | list -> dict
    poster, warnings  = normalize(poster, meta, keep_order=False)

Guarantees for the builder:
    - 4 to 8 sections, each with a valid "type", a title and clean field types
    - sections in the standard research order (overview, objectives, audience,
      methods, findings, insights, trends, recommendations, conclusion)
      unless keep_order=True; unknown sections keep their relative place
    - list sizes fit one poster page (extra items dropped with a warning)
Every repair is reported in `warnings`.
"""

from __future__ import annotations

import ast
import difflib
import json
import math
import re

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
        salvaged = {"sections": objs, "_truncated": True}
        head = body[:body.find("{", 1)] if body.startswith("{") else ""
        for key in ("tag", "title", "highlight", "subtitle", "footer", "hero_image", "size", "language"):
            m = re.search(r'"%s"\s*:\s*"((?:[^"\\]|\\.)*)"' % key, head)
            if m:
                salvaged[key] = m.group(1)
        return salvaged
    raise ValueError(f"could not parse JSON ({last_err})")


def parse_spec(raw) -> tuple[dict, dict]:
    """Return (poster_dict, meta).  meta may contain truncated."""
    meta: dict = {}
    data = raw
    for _ in range(3):  # strings may be double-encoded
        if isinstance(data, (bytes, bytearray)):
            data = data.decode("utf-8", errors="replace")
        if isinstance(data, str):
            data = _loads_lenient(data)
        else:
            break
    if isinstance(data, list):
        data = {"sections": data}
    if isinstance(data, dict):
        if data.pop("_truncated", False):
            meta["truncated"] = True
        if "sections" not in data and "slides" in data:
            data["sections"] = data.pop("slides")
        if "sections" not in data:
            for key in ("cards", "blocks", "panels", "items", "content"):
                if isinstance(data.get(key), list):
                    data["sections"] = data.pop(key)
                    break
    if not isinstance(data, dict):
        raise ValueError("expected a JSON object with a \"sections\" list")
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




# ---------------------------------------------------------------------------
# Poster sections
# ---------------------------------------------------------------------------

TYPES = ("text", "bullets", "list", "facts", "stats", "chart", "columns")
TYPE_ALIASES = {
    "paragraph": "text", "overview": "text", "summary": "text", "description": "text", "content": "text",
    "body": "text", "intro": "text",
    "bullet": "bullets", "bullet_points": "bullets", "points": "bullets", "objectives": "bullets",
    "recommendations": "bullets", "checklist": "bullets",
    "items": "list", "methods": "list", "steps": "list", "trends": "list", "icon_list": "list", "features": "list",
    "fact": "facts", "keyvalue": "facts", "key_value": "facts", "kv": "facts", "profile": "facts",
    "audience": "facts", "demographics": "facts", "table": "facts", "details": "facts",
    "stat": "stats", "findings": "stats", "numbers": "stats", "kpi": "stats", "kpis": "stats",
    "metrics": "stats", "results": "stats", "statistics": "stats",
    "charts": "chart", "graph": "chart", "insights": "chart", "analysis": "chart", "donut": "chart",
    "pie": "chart", "bar": "chart", "column": "chart", "line": "chart", "data": "chart",
    "groups": "columns", "categories": "columns", "audiences": "columns", "cards": "columns", "grid": "columns",
    "for_each": "columns", "stakeholders": "columns",
}

# role (from the title) -> rank in the standard poster order
ROLE_RANK = {
    "overview": 0, "objectives": 1, "audience": 2, "methods": 3, "findings": 4, "insights": 5,
    "trends": 6, "conclusion": 7, "recommendations": 8,
}
_ROLE_HINTS = (
    ("overview", "overview"), ("background", "overview"), ("introduction", "overview"), ("pendahuluan", "overview"),
    ("latar belakang", "overview"), ("abstract", "overview"), ("summary", "overview"), ("ringkasan", "overview"),
    ("objective", "objectives"), ("goal", "objectives"), ("tujuan", "objectives"), ("aim", "objectives"),
    ("research question", "objectives"), ("hypothes", "objectives"),
    ("audience", "audience"), ("respondent", "audience"), ("participant", "audience"), ("sample", "audience"),
    ("responden", "audience"), ("demograf", "audience"), ("population", "audience"), ("populasi", "audience"),
    ("profile", "audience"),
    ("method", "methods"), ("metode", "methods"), ("approach", "methods"), ("data collection", "methods"),
    ("design", "methods"), ("procedure", "methods"),
    ("finding", "findings"), ("temuan", "findings"), ("result", "findings"), ("hasil", "findings"),
    ("key number", "findings"),
    ("insight", "insights"), ("wawasan", "insights"), ("analysis", "insights"), ("analisis", "insights"), ("discussion", "insights"),
    ("pembahasan", "insights"), ("statistic", "insights"), ("distribution", "insights"),
    ("trend", "trends"), ("tren", "trends"), ("market", "trends"), ("pasar", "trends"), ("outlook", "trends"),
    ("implication", "trends"),
    ("recommend", "recommendations"), ("rekomendasi", "recommendations"), ("action", "recommendations"),
    ("next step", "recommendations"), ("strategy", "recommendations"), ("saran", "recommendations"),
    ("conclusion", "conclusion"), ("kesimpulan", "conclusion"), ("limitation", "conclusion"),
    ("keterbatasan", "conclusion"), ("future", "conclusion"), ("acknowledg", "conclusion"),
    ("reference", "conclusion"), ("contact", "conclusion"),
)

CHART_TYPES = ("donut", "pie", "bar", "column", "line")
CHART_ALIASES = {"doughnut": "donut", "ring": "donut", "circle": "pie", "hbar": "bar", "horizontal_bar": "bar",
                 "barh": "bar", "bars": "bar", "col": "column", "columns": "column", "vertical_bar": "column",
                 "histogram": "column", "lines": "line", "trend": "line", "area": "line", "radar": "donut",
                 "scatter": "line"}

MIN_SECTIONS, MAX_SECTIONS = 4, 8
LIMITS = {"bullets": 5, "list": 4, "facts": 6, "stats": 5, "categories": 6, "series": 3, "columns": 4}
TEXT_LIMIT = 380


def _role(title: str, explicit: str | None = None) -> str | None:
    if explicit and explicit in ROLE_RANK:
        return explicit
    low = (title or "").lower()
    for key, role in _ROLE_HINTS:
        if key in low:
            return role
    return None


def _canon_type(raw) -> tuple[str | None, str | None]:
    key = re.sub(r"[\s\-]+", "_", str(raw or "").strip().lower())
    if key in TYPES:
        return key, None
    if key in TYPE_ALIASES:
        return TYPE_ALIASES[key], f"type {raw!r} -> {TYPE_ALIASES[key]!r}"
    close = difflib.get_close_matches(key, list(TYPES) + list(TYPE_ALIASES), n=1, cutoff=0.8)
    if close:
        t = close[0] if close[0] in TYPES else TYPE_ALIASES[close[0]]
        return t, f"type {raw!r} -> {t!r}"
    return None, None


def _infer_type(s: dict) -> str:
    has = lambda *ks: any(s.get(k) not in (None, "", [], {}) for k in ks)  # noqa: E731
    if has("chart", "categories", "series", "datasets", "values"):
        return "chart"
    if has("stats", "kpis", "metrics", "numbers"):
        return "stats"
    if has("facts", "fields", "pairs", "profile", "details"):
        return "facts"
    items = s.get("items") or s.get("points") or s.get("bullets") or s.get("list")
    if isinstance(items, list) and items:
        first = items[0]
        if isinstance(first, dict):
            if "value" in first and ("label" in first or "text" in first or "title" in first):
                return "stats" if any(re.search(r"\d", _s(x.get("value"))) and len(_s(x.get("value"))) <= 8
                                      for x in items if isinstance(x, dict)) else "facts"
            if "label" in first and "value" in first:
                return "facts"
            if "title" in first or "name" in first:
                return "list"
        if isinstance(first, str) and ":" in first and len(first) < 60 and all(
                isinstance(x, str) and ":" in x for x in items):
            return "facts"
        return "bullets"
    if has("text", "content", "body", "description"):
        return "text"
    return "text"


def _text_of(s: dict, *extra) -> str:
    return _s(_first(s, "text", "content", "body", "description", "paragraph", "summary", *extra))


def _titled_items(v, limit: int, w, what: str) -> list[dict]:
    items = _obj_list(v, "title", {
        "title": ("name", "label", "header", "heading", "point"),
        "text": ("description", "desc", "detail", "body", "content", "subtitle"),
        "icon": ("emoji",),
    }, split_key="text")
    if len(items) > limit:
        w(f"{len(items)} {what}, {limit} fit -> extra dropped")
    return items[:limit]


def _facts(v, limit: int, w) -> list[dict]:
    if isinstance(v, dict) and not any(k in v for k in ("label", "value")):
        v = [{"label": k, "value": x} for k, x in v.items()]
    items = _obj_list(v, "label", {
        "label": ("name", "key", "field", "title"),
        "value": ("text", "val", "content", "detail"),
    }, split_key="value")
    items = [x for x in items if x.get("label") or x.get("value")]
    if len(items) > limit:
        w(f"{len(items)} facts, {limit} fit -> extra dropped")
    return items[:limit]


_NUM_RE = re.compile(r"[-+]?\d[\d.,]*\s*(?:%|x|k|K|M|B|jt|rb)?", re.I)


def _stats(v, limit: int, w) -> list[dict]:
    items = _obj_list(v, "label", {
        "label": ("title", "name", "headline", "finding", "point"),
        "value": ("number", "stat", "metric", "figure", "percent", "percentage", "val"),
        "text": ("description", "desc", "detail", "note", "caption", "body"),
        "icon": ("emoji",),
    })
    out = []
    for it in items:
        if not it.get("value"):
            # "72% of respondents ..." inside label / text
            for key in ("label", "text"):
                m = _NUM_RE.search(it.get(key, ""))
                if m and len(m.group(0).strip()) <= 8:
                    it["value"] = m.group(0).strip()
                    it[key] = (it[key][:m.start()] + it[key][m.end():]).strip(" ,;:-")
                    break
        if not it.get("value") and not it.get("label"):
            continue
        value, words = "", _s(it.get("value")).split()
        for word in words:                  # whole words only: "Rp 310.000" cut to "Rp 310.00" is a different number
            if value and len(value) + 1 + len(word) > 14:
                w(f"stat value {' '.join(words)!r} is long -> {value!r}")
                break
            value = f"{value} {word}".strip()
        out.append({"label": it.get("label", ""), "value": value, "text": it.get("text", ""),
                    **({"icon": it["icon"]} if it.get("icon") else {})})
    if len(out) > limit:
        w(f"{len(out)} stats, {limit} fit -> extra dropped")
    return out[:limit]


def _chart(s: dict, w):
    c = s.get("chart")
    if c in (None, "", [], {}):
        c = {k: s[k] for k in ("chart_type", "categories", "labels", "series", "datasets", "values", "data")
             if k in s}
        if not c:
            return None
    if isinstance(c, list):
        c = {"series": c}
    if not isinstance(c, dict):
        return None
    raw_type = re.sub(r"[\s\-]+", "_", _s(_first(c, "type", "chart_type", "kind")).lower())
    raw_type = re.sub(r"_?chart$", "", raw_type)
    ctype = raw_type if raw_type in CHART_TYPES else CHART_ALIASES.get(raw_type)
    if raw_type and not ctype:
        w(f"chart type {raw_type!r} unknown -> 'donut'")
    cats = _first(c, "categories", "labels", "x")
    data = _first(c, "series", "datasets", "data", "values")
    if isinstance(data, dict):
        if isinstance(data.get("datasets"), list):
            cats = cats or data.get("labels")
            data = data["datasets"]
        elif any(k in data for k in ("values", "data", "y")):
            data = [data]
        else:
            cats, data = list(data.keys()), [{"name": "Share", "values": list(data.values())}]
    if isinstance(data, list) and data and all(isinstance(x, (int, float, str)) for x in data):
        data = [{"name": _s(c.get("name")) or "Share", "values": data}]
    if isinstance(data, list) and data and all(isinstance(x, dict) and "value" in x and not any(
            k in x for k in ("values", "data")) for x in data):
        cats = [_s(_first(x, "label", "name", "category")) for x in data]
        data = [{"name": "Share", "values": [x["value"] for x in data]}]
    series = []
    for i, ser in enumerate(data if isinstance(data, list) else []):
        if not isinstance(ser, dict):
            continue
        cats = cats or _first(ser, "labels", "categories")
        vals = [_to_number(v) for v in _as_list(_first(ser, "values", "data", "y"))]
        if any(v is None for v in vals):
            w("chart: non-numeric values replaced by 0")
            vals = [0.0 if v is None else v for v in vals]
        if vals:
            series.append({"name": _s(_first(ser, "name", "label", "title")) or f"Series {i + 1}", "values": vals})
    if not series:
        w("chart has no usable numbers -> chart left out")
        return None
    n = min(len(x["values"]) for x in series)
    cats = [_s(x) for x in _as_list(cats)] or [f"Item {k + 1}" for k in range(n)]
    n = min(n, len(cats), LIMITS["categories"])
    if any(len(x["values"]) != n for x in series) or len(cats) != n:
        w(f"chart trimmed to {n} categories")
    for x in series:
        x["values"] = x["values"][:n]
    ctype = ctype or ("line" if n >= 5 and len(series) <= 2 else "donut")
    if ctype in ("donut", "pie") and len(series) > 1:
        w(f"{ctype} chart uses one series -> kept the first")
        series = series[:1]
    cats, rest = cats[:n], False
    if ctype in ("donut", "pie"):
        vals = series[0]["values"]
        total = sum(vals)
        if all(0 <= v <= 100 for v in vals) and 60 <= total < 99.5 and n < LIMITS["categories"]:
            # 54 + 31 = 85: these are percentages and one share is missing.  Drawn as they are, the
            # chart scales them to 100 and prints 63.5% and 36.5%, numbers that are in no source.
            w(f"{ctype} values add up to {total:g}, not 100 -> read as percentages, the rest added as 'Others'")
            cats, rest = cats + ["Others"], True
            vals.append(round(100 - total, 1))
    return {"type": ctype, "categories": cats, "series": series[:LIMITS["series"]],
            "unit": _s(c.get("unit")), "rest": rest}


def _pictograph(s: dict, w):
    p = s.get("pictograph") or s.get("people")
    if isinstance(p, dict):
        v, t = _to_number(_first(p, "value", "count", "filled")), _to_number(_first(p, "total", "of", "max"))
        if v is not None:
            return {"value": v, "total": t or 100, "label": _s(_first(p, "label", "text"))}
    if isinstance(p, (int, float, str)):
        v = _to_number(p)
        if v is not None:
            return {"value": v, "total": 100, "label": ""}
    return None


def _normalise_section(kind: str, s: dict, w) -> dict:
    out = {"text": _text_of(s)}
    items_raw = _first(s, "items", "points", "bullets", "list", "steps", "methods", "entries")
    if kind == "bullets":
        out["items"] = _titled_items(items_raw, LIMITS["bullets"], w, "bullets")
    elif kind == "list":
        out["items"] = _titled_items(items_raw, LIMITS["list"], w, "items")
    elif kind == "facts":
        out["items"] = _facts(_first(s, "facts", "fields", "pairs", "profile", "details", "items", "data"),
                              LIMITS["facts"], w)
        out["pictograph"] = _pictograph(s, w)
    elif kind == "stats":
        out["items"] = _stats(_first(s, "stats", "kpis", "metrics", "numbers", "items", "findings"),
                              LIMITS["stats"], w)
    elif kind == "columns":
        out["items"] = _titled_items(_first(s, "columns", "groups", "items", "cards", "entries"), LIMITS["columns"], w, "columns")
    elif kind == "chart":
        out["chart"] = _chart(s, w)
        if not out["chart"]:
            items = _titled_items(items_raw, LIMITS["bullets"], w, "bullets")
            if items:
                w("chart without data -> shown as bullets")
                return {"type": "bullets", "text": out["text"], "items": items}
            return {"type": "text", "text": out["text"] or "Chart data was not provided."}
        out["legend"] = s.get("legend", True) is not False
        out["insight"] = _s(_first(s, "insight", "takeaway", "caption"))
    out["quote"] = _s(_first(s, "quote", "highlight_text", "callout"))
    out["icon"] = _s(_first(s, "icon", "emoji"))
    out["image"] = _s(_first(s, "image", "illustration", "picture", "photo"))
    width = _first(s, "width", "span", "size")
    if isinstance(width, (int, float)) or (isinstance(width, str) and width.strip()):
        out["width"] = width if isinstance(width, (int, float)) else width.strip().lower()
    if s.get("numbered") is True or (isinstance(s.get("style"), str) and "number" in s["style"].lower()):
        out["numbered"] = True
    for key in ("text", "quote"):
        if len(out.get(key, "")) > TEXT_LIMIT * (1.0 if key == "text" else 0.5):
            lim = TEXT_LIMIT if key == "text" else TEXT_LIMIT // 2
            w(f"{key} has {len(out[key])} characters, about {lim} fit - it will be shrunk")
    return out


def normalize(poster: dict, meta: dict | None = None, keep_order: bool = False) -> tuple[dict, list[str]]:
    meta = meta or {}
    warnings: list[str] = []
    p: dict = {}
    p["tag"] = _s(_first(poster, "tag", "label", "kicker", "eyebrow", "category")) or "Research Project"
    p["title"] = _s(_first(poster, "title", "heading", "headline", "name"))
    p["highlight"] = _s(_first(poster, "highlight", "accent_word", "title_accent"))
    p["subtitle"] = _s(_first(poster, "subtitle", "tagline", "sub_title", "description"))
    p["hero_image"] = _s(_first(poster, "hero_image", "image", "photo", "picture", "cover_image"))
    footer = _first(poster, "footer", "contact", "contacts", "authors", "affiliation")
    if isinstance(footer, dict) and any(k in footer for k in ("slogan", "tagline", "text", "message")):
        p["footer"] = {"slogan": _s(_first(footer, "slogan", "tagline", "title", "headline")),
                       "text": _s(_first(footer, "text", "message", "contact", "note")),
                       "icon": _s(footer.get("icon"))}
    else:
        if isinstance(footer, dict):
            footer = [_s(v) for v in footer.values() if _s(v)]
        if isinstance(footer, (list, tuple)):
            footer = "  |  ".join(_s(x) for x in footer if _s(x))
        p["footer"] = _s(footer)
    slogan = _s(_first(poster, "slogan", "footer_slogan", "closing_line"))
    if slogan and not isinstance(p["footer"], dict):
        p["footer"] = {"slogan": slogan, "text": p["footer"], "icon": ""}
    p["lead"] = _s(_first(poster, "lead", "intro", "summary", "abstract_short"))
    p["hero_style"] = _s(poster.get("hero_style")).lower()
    layout = _s(_first(poster, "layout", "grid")).lower()
    p["layout"] = "grid" if layout in ("grid", "rigid", "equal", "fixed") else "flow"
    theme = poster.get("theme")
    p["theme"] = theme if isinstance(theme, (dict, str)) else {}
    p["size"] = _s(_first(poster, "size", "paper", "page_size")).upper().replace(" ", "") or "A2"
    lang = _s(_first(poster, "language", "lang")).lower()[:2]
    if lang in ("en", "id"):
        p["language"] = lang
    if not p["title"]:
        warnings.append("no title -> 'Research Poster' used")
        p["title"] = "Research Poster"

    raw_sections = poster.get("sections") or []
    if isinstance(raw_sections, dict):
        raw_sections = [dict(v, title=k) if isinstance(v, dict) else {"title": k, "text": v}
                        for k, v in raw_sections.items()]
    sections: list[dict] = []
    for idx, raw in enumerate(raw_sections):
        tag = f"section {idx + 1}"
        if isinstance(raw, str) and raw.strip():
            raw = {"type": "text", "title": raw.strip()[:40], "text": raw.strip()}
            warnings.append(f"{tag}: was plain text -> 'text' section")
        if not isinstance(raw, dict):
            warnings.append(f"{tag}: not an object -> skipped")
            continue
        s = dict(raw)

        def w(msg, _tag=tag):
            warnings.append(f"{_tag}: {msg}")

        title = _s(_first(s, "title", "heading", "header", "name", "label"))
        raw_type = _first(s, "type", "kind", "layout", "section_type")
        kind, note = _canon_type(raw_type) if raw_type else (None, None)
        if note:
            w(note)
        if kind is None:
            kind = _infer_type(s)
            if raw_type:
                w(f"type {raw_type!r} unknown -> guessed {kind!r}")
        try:
            fields = _normalise_section(kind, s, w)
        except Exception as e:
            w(f"could not read fields ({type(e).__name__}: {e}) -> text only")
            fields = {"type": "text", "text": _text_of(s)}
        kind = fields.pop("type", kind)
        sec = {"type": kind, "title": title or kind.title(), "role": _role(title, _s(s.get("role")) or None)}
        sec.update({k: v for k, v in fields.items() if v not in (None, "", [], {})})
        if kind in ("bullets", "list", "facts", "stats", "columns") and not sec.get("items"):
            if sec.get("text"):
                w(f"{kind} without items -> 'text' section")
                sec["type"] = "text"
            else:
                w("empty section skipped")
                continue
        sections.append(sec)

    if len(sections) > MAX_SECTIONS:
        warnings.append(f"{len(sections)} sections, {MAX_SECTIONS} fit on one page -> extra sections dropped")
        sections = sections[:MAX_SECTIONS]
    if len(sections) < MIN_SECTIONS:
        warnings.append(f"only {len(sections)} sections - the poster looks best with 6 to 8")

    if not keep_order and sections:
        ranks, last = [], -0.5
        for s in sections:
            if s["role"] in ROLE_RANK:
                last = float(ROLE_RANK[s["role"]])
                ranks.append(last)
            else:
                ranks.append(last + 0.25)
        order = sorted(range(len(sections)), key=lambda i: (ranks[i], i))
        if order != list(range(len(sections))):
            warnings.append("sections re-ordered to the standard research order: "
                            + " > ".join(sections[i]["title"] for i in order))
        sections = [sections[i] for i in order]
    for s in sections:
        s.pop("role", None)
    p["sections"] = sections
    return p, warnings
