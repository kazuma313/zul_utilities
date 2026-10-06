"""Parse and repair deck specs written by LLMs for the pptx-research template.

Python standard library only.

    slides, meta      = parse_slides(raw)             # str | list | dict -> list
    slides, warnings  = normalize_spec(slides, meta, keep_order=False, auto_agenda=True)

What it guarantees for the builder:
    - every slide is a dict with a valid "layout" and clean field types
    - SECTIONS ARE IN THE STANDARD ORDER (cover, intro, agenda, background,
      problem, framework, methodology, data, timeline, analysis, gallery,
      testimonials, closing) unless keep_order=True
    - the agenda lists the real section titles, numbered in that order
    - list sizes fit the template (extra items are dropped with a warning)
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
        for key in ("slides", "deck", "presentation", "pages", "slide_list", "data", "sections"):
            inner = data.get(key)
            if isinstance(inner, dict) and isinstance(inner.get("slides"), list):
                data = dict(inner)
                inner = data.get("slides")
            if isinstance(inner, list):
                for mk in ("theme", "filename", "organization", "tagline"):
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
    text = str(v).strip()
    if re.match(r"[A-Za-z]:\\|\\\\", text) or re.search(r"\.(?:png|jpe?g|gif|svg|webp|bmp)$", text, re.I):
        return text                             # a Windows path keeps its backslashes
    # a model that escapes twice leaves the two characters "\n" in the text, and the slide shows them
    text = re.sub(r"\\[nrt]", "\n", text)
    # gemma3:4b sometimes closes a string too late, so pieces of the JSON end up in the text: `... e-commerce.”},{`
    text = re.sub(r"[\s\"“”,\[\]]*[{}][\s\"“”,{}\[\]]*$", "", text)
    return re.sub(r"\s+[“\"]$", "", text).strip()


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
# Layouts of this template
# ---------------------------------------------------------------------------

# layout -> rank in the standard section order
ORDER = {
    "cover": 0, "intro": 1, "agenda": 2, "section": 3, "three_cards": 4, "team": 5,
    "two_cards": 6, "people": 7, "chart": 8, "timeline": 9, "analysis": 10,
    "stat_chart": 11, "gallery": 12, "testimonials": 13, "closing": 99,
}
LAYOUTS = tuple(ORDER)

LAYOUT_ALIASES = {
    # generic names
    "title": "cover", "title_slide": "cover", "cover_slide": "cover", "opening": "cover",
    "hello": "intro", "introduction": "intro", "welcome": "intro", "about": "intro", "overview": "intro",
    "summary": "intro", "abstract": "intro", "executive_summary": "intro",
    "agenda_overview": "agenda", "toc": "agenda", "table_of_contents": "agenda", "contents": "agenda",
    "outline": "agenda",
    "section_divider": "section", "divider": "section", "section_header": "section", "chapter": "section",
    "content": "section", "text": "section",
    "cards3": "three_cards", "3_cards": "three_cards", "cards": "three_cards", "three_card": "three_cards",
    "bullets": "three_cards", "key_points": "three_cards",
    "cards2": "two_cards", "2_cards": "two_cards", "two_column": "two_cards", "two_columns": "two_cards",
    "comparison": "two_cards", "two_card": "two_cards",
    "people4": "people", "participants": "people", "respondents": "people", "profiles": "people",
    "members": "team", "theorists": "team", "experts": "team", "researchers": "team",
    "bar_chart": "chart", "graph": "chart", "data": "chart", "line_chart": "analysis",
    "roadmap": "timeline", "schedule": "timeline", "plan": "timeline", "milestones": "timeline",
    "gantt": "timeline",
    "stat": "stat_chart", "stats": "stat_chart", "stat_callout": "stat_chart", "key_finding": "stat_chart",
    "radar": "stat_chart", "findings": "stat_chart", "results": "stat_chart",
    "images": "gallery", "photos": "gallery", "image": "gallery",
    "testimonial": "testimonials", "quotes": "testimonials", "quote": "testimonials", "reviews": "testimonials",
    "feedback": "testimonials",
    "thank_you": "closing", "thanks": "closing", "end": "closing", "conclusion": "closing",
    "conclusion_cta": "closing", "final": "closing",
    # research-proposal section names (English + Indonesian)
    "background": "section", "background_of_the_study": "section", "latar_belakang": "section",
    "pendahuluan": "intro",
    "problem": "three_cards", "problem_statement": "three_cards", "rumusan_masalah": "three_cards",
    "objectives": "three_cards", "tujuan": "three_cards", "tujuan_penelitian": "three_cards",
    "research_questions": "three_cards",
    "framework": "team", "theoretical_framework": "team", "kerangka_teori": "team",
    "literature_review": "team", "tinjauan_pustaka": "team",
    "methodology": "two_cards", "methods": "two_cards", "method": "two_cards", "metodologi": "two_cards",
    "metode": "two_cards", "metode_penelitian": "two_cards",
    "qualitative": "people", "qualitative_data": "people", "kualitatif": "people",
    "quantitative": "chart", "quantitative_data": "chart", "kuantitatif": "chart",
    "proposed_timeline": "timeline", "jadwal": "timeline", "jadwal_penelitian": "timeline",
    "analysis_chart": "analysis", "analisis": "analysis", "data_analysis": "analysis",
    "portfolio": "gallery", "our_portfolio": "gallery", "portofolio": "gallery",
    "penutup": "closing", "terima_kasih": "closing",
}

CHART_TYPES = ("bar", "column", "line", "pie", "doughnut", "radar", "area")
CHART_TYPE_ALIASES = {
    "col": "column", "columns": "column", "vertical_bar": "column", "histogram": "column",
    "bars": "bar", "horizontal_bar": "bar", "hbar": "bar", "barh": "bar",
    "lines": "line", "trend": "line", "spline": "line", "donut": "doughnut", "ring": "doughnut",
    "spider": "radar", "web": "radar", "areas": "area",
}


def _canon_layout(raw):
    key = re.sub(r"[\s\-]+", "_", str(raw or "").strip().lower())
    key = re.sub(r"_?(slide|layout)$", "", key) or key
    if key in LAYOUTS:
        return key, (None if key == raw else f"layout {raw!r} -> {key!r}")
    if key in LAYOUT_ALIASES:
        return LAYOUT_ALIASES[key], f"layout {raw!r} -> {LAYOUT_ALIASES[key]!r}"
    close = difflib.get_close_matches(key, list(LAYOUTS) + list(LAYOUT_ALIASES), n=1, cutoff=0.8)
    if close:
        target = close[0] if close[0] in LAYOUTS else LAYOUT_ALIASES[close[0]]
        return target, f"layout {raw!r} -> {target!r}"
    return None, None


def _infer_layout(s: dict, index: int, total: int) -> str:
    has = lambda *ks: any(s.get(k) not in (None, "", [], {}) for k in ks)  # noqa: E731
    if has("columns", "months", "phases", "steps", "milestones"):
        return "timeline"
    if has("stat", "value", "percentage"):
        return "stat_chart"
    if has("chart", "chart_data", "series", "datasets"):
        return "chart"
    if has("testimonials", "quotes", "reviews"):
        return "testimonials"
    if has("people", "members", "participants"):
        return "team" if has("overview", "overview_items") else "people"
    if has("cards"):
        n = len(_as_list(s.get("cards")))
        return "two_cards" if n == 2 else "three_cards"
    if has("images"):
        return "gallery"
    if has("paragraphs", "lead"):
        return "intro"
    if index == 0:
        return "cover"
    if index == total - 1 and not has("text", "content", "body"):
        return "closing"
    return "section"


def _title_guess(s: dict) -> str:
    return _s(_first(s, "title", "heading", "headline", "name", "slide_title"))


def _cards(v, n: int, w) -> list[dict]:
    cards = _obj_list(v, "header", {
        "header": ("title", "name", "label", "heading"),
        "body": ("text", "description", "desc", "content", "detail"),
    }, split_key="body")
    if len(cards) > n:
        w(f"{len(cards)} cards given, this slide has {n} -> extra cards dropped")
    return cards[:n]


def _people(v, n: int, w, with_note=False) -> list[dict]:
    mapping = {
        "name": ("full_name", "person", "title"),
        "role": ("position", "job", "occupation", "subtitle", "theory", "label", "affiliation"),
        "image": ("photo", "image_url", "picture", "avatar", "image_path"),
    }
    if with_note:
        mapping["note"] = ("caption", "tag", "description", "desc")
    people = _obj_list(v, "name", mapping, split_key="role")
    if len(people) > n:
        w(f"{len(people)} people given, this slide has {n} photo slots -> extra people dropped")
    return people[:n]


def _chart(s: dict, w, key="chart"):
    """Return {"type", "categories", "series":[{"name","values"}]} or None."""
    c = s.get(key)
    if c in (None, "", [], {}):
        if key != "chart":
            return None
        c = {k: s[k] for k in ("chart_type", "chart_data", "categories", "labels", "series", "datasets", "values")
             if k in s}
        if not c:
            return None
    if isinstance(c, list):
        c = {"series": c}
    if not isinstance(c, dict):
        return None
    raw_type = re.sub(r"[\s\-]+", "_", _s(_first(c, "type", "chart_type", "kind")).lower())
    raw_type = re.sub(r"_?chart$", "", raw_type)
    ctype = raw_type if raw_type in CHART_TYPES else CHART_TYPE_ALIASES.get(raw_type)
    if raw_type and not ctype:
        w(f"chart type {raw_type!r} unknown -> default used")

    cats = _first(c, "categories", "labels", "x")
    data = _first(c, "series", "chart_data", "datasets", "data")
    if isinstance(data, dict):
        if isinstance(data.get("datasets"), list):
            cats = cats or data.get("labels")
            data = data["datasets"]
        elif isinstance(data.get("series"), list):
            cats = cats or _first(data, "categories", "labels")
            data = data["series"]
        elif any(k in data for k in ("values", "data", "y")):
            data = [data]
        else:
            cats, data = list(data.keys()), [{"name": "Series 1", "values": list(data.values())}]
    if data is None and c.get("values") is not None:
        data = [{"name": _s(c.get("name")) or "Series 1", "values": c["values"]}]
    if isinstance(data, list) and data and all(isinstance(x, (int, float, str)) for x in data):
        data = [{"name": "Series 1", "values": data}]
    series = []
    for i, ser in enumerate(data if isinstance(data, list) else []):
        if not isinstance(ser, dict):
            continue
        cats = cats or _first(ser, "labels", "categories", "x")
        vals = [_to_number(v) for v in _as_list(_first(ser, "values", "data", "y", "numbers"))]
        if any(v is None for v in vals):
            w("chart: non-numeric values replaced by 0")
            vals = [0.0 if v is None else v for v in vals]
        if vals:
            series.append({"name": _s(_first(ser, "name", "label", "title")) or f"Series {i + 1}", "values": vals})
    if not series:
        w("chart had no usable numbers -> chart left out")
        return None
    n = min(len(x["values"]) for x in series)
    cats = [_s(x) for x in _as_list(cats)] or [str(i + 1) for i in range(n)]
    n = min(n, len(cats), 12)
    if any(len(x["values"]) != n for x in series) or len(cats) != n:
        w(f"chart: categories and values trimmed to {n} points")
    for x in series:
        x["values"] = x["values"][:n]
    if len(series) > 3:
        w("chart: more than 3 series -> kept the first 3")
    return {"type": ctype, "categories": cats[:n], "series": series[:3]}


def _text(s: dict, *extra) -> str:
    return _s(_first(s, "text", "content", "body", "description", "paragraph", *extra))


def _image(s: dict) -> str:
    return _s(_first(s, "image", "image_url", "image_path", "photo", "picture"))


def _normalise_slide(layout: str, s: dict, w) -> dict:
    out: dict = {}
    if layout == "cover":
        out.update(subtitle=_s(_first(s, "subtitle", "sub_title", "tagline2")),
                   organization=_s(_first(s, "organization", "organisation", "company", "institution", "university")),
                   presenter=_s(_first(s, "presenter", "author", "presented_by", "by", "name", "authors")),
                   presenter_label=_s(s.get("presenter_label")),
                   tagline=_s(_first(s, "tagline", "description", "topic", "text")))
    elif layout == "intro":
        paras = _as_list(_first(s, "paragraphs", "text", "content", "body"))
        paras = [_s(p) for p in paras if _s(p)]
        if len(paras) > 2:
            w(f"{len(paras)} paragraphs given, the slide has 2 -> merged")
            paras = [paras[0], " ".join(paras[1:])]
        out.update(lead=_s(_first(s, "lead", "subtitle", "summary", "intro")), paragraphs=paras, image=_image(s))
    elif layout == "agenda":
        items = [_s(x) for x in _as_list(_first(s, "items", "agenda", "topics", "sections", "bullets"))]
        out.update(items=[re.sub(r"^\d{1,2}[.):\s-]+", "", x) for x in items if x], image=_image(s),
                   auto=s.get("auto", True) is not False)
    elif layout == "section":
        out.update(text=_text(s, "subtitle"), image=_image(s))
    elif layout in ("three_cards", "two_cards"):
        n = 3 if layout == "three_cards" else 2
        out.update(text=_text(s), image=_image(s),
                   cards=_cards(_first(s, "cards", "items", "points", "bullets", "columns"), n, w))
        if layout == "two_cards" and not out["cards"]:
            pair = [{"header": _s(s.get(f"{k}_header")), "body": _s(s.get(k))} for k in ("left", "right")]
            out["cards"] = [c for c in pair if c["header"] or c["body"]]
    elif layout == "team":
        out.update(text=_text(s), image=_image(s),
                   overview_title=_s(_first(s, "overview_title", "list_title")),
                   overview_items=[_s(x) for x in _as_list(_first(s, "overview_items", "overview", "bullets",
                                                                  "theories", "items")) if _s(x)][:4],
                   people=_people(_first(s, "people", "members", "team", "theorists", "experts"), 3, w, True))
    elif layout == "people":
        texts = [_s(x) for x in _as_list(_first(s, "text", "content", "body", "paragraphs")) if _s(x)]
        out.update(text=texts[0] if texts else "",
                   text2=_s(s.get("text2")) or (" ".join(texts[1:]) if len(texts) > 1 else ""),
                   people=_people(_first(s, "people", "participants", "respondents", "members", "profiles"), 4, w))
    elif layout == "chart":
        out.update(text=_text(s), chart=_chart(s, w))
        st = s.get("stat")
        if isinstance(st, dict):
            out["stat"] = {"value": _s(_first(st, "value", "number")), "label": _s(_first(st, "label", "text"))}
    elif layout == "timeline":
        cols = []
        for c in _as_list(_first(s, "columns", "months", "phases", "steps", "milestones", "items")):
            if isinstance(c, dict):
                header = _s(_first(c, "header", "title", "month", "phase", "label", "name", "period"))
                items = [_s(x) for x in _as_list(_first(c, "items", "tasks", "activities", "description", "text"))]
            else:
                m = re.match(r"^(.{2,24}?)\s*:\s*(.+)$", _s(c), flags=re.S)
                header, items = (m.group(1), [m.group(2)]) if m else (_s(c), [])
            items = [x for x in items if x]
            if len(items) > 2:
                w(f"timeline column {header!r}: {len(items)} items, 2 fit -> merged")
                items = [items[0], "; ".join(items[1:])]
            if header or items:
                cols.append({"header": header, "items": items})
        if len(cols) > 4:
            w(f"timeline has {len(cols)} columns, 4 fit -> extra columns dropped")
        out.update(columns=cols[:4], text=_text(s))
    elif layout == "analysis":
        out.update(text=_text(s), chart=_chart(s, w), chart2=_chart(s, w, key="chart2"))
    elif layout == "stat_chart":
        st = s.get("stat") if isinstance(s.get("stat"), dict) else {}
        out.update(text=_text(s), chart=_chart(s, w),
                   stat=_s(_first(st, "value", "number") or _first(s, "stat", "value", "percentage", "number")
                           if not isinstance(s.get("stat"), dict) else _first(st, "value", "number")),
                   stat_text=_s(_first(st, "label", "text") or _first(s, "stat_text", "stat_label", "label", "caption")))
    elif layout == "gallery":
        imgs = [_s(x) for x in _as_list(_first(s, "images", "photos", "pictures")) if _s(x)]
        out.update(text=_text(s), images=imgs[:3])
    elif layout == "testimonials":
        items = _obj_list(_first(s, "items", "testimonials", "quotes", "reviews", "people"), "text", {
            "name": ("author", "person", "by", "source"),
            "text": ("quote", "comment", "review", "body", "content"),
            "rating": ("stars", "score"),
            "image": ("photo", "image_url", "picture", "avatar"),
        })
        if len(items) > 4:
            w(f"{len(items)} testimonials given, 4 fit -> extra dropped")
        for it in items:
            r = _to_number(it.get("rating")) if it.get("rating") else None
            it["rating"] = int(max(1, min(5, round(r)))) if r is not None else 5
        out.update(lead=_s(_first(s, "lead", "text", "subtitle")), items=items[:4])
    elif layout == "closing":
        out.update(subtitle=_s(_first(s, "subtitle", "text", "message", "contact")),
                   organization=_s(_first(s, "organization", "organisation", "company", "institution")),
                   tagline=_s(_first(s, "tagline", "description", "topic")))
    return out


CONTENT_RANKS = (3, 98)  # ranks that count as agenda sections


def _agenda_label(s: dict, limit: int = 34) -> str:
    """Agenda rows are one line: use agenda_label, or the title cut at a word boundary."""
    t = re.sub(r"\s+", " ", s.get("agenda_label") or s["title"]).strip()
    if len(t) <= limit:
        return t
    cut = t[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return (cut or t[:limit]) + "..."


def normalize_spec(slides: list, meta: dict | None = None, keep_order: bool = False,
                   auto_agenda: bool = True) -> tuple[list, list[str]]:
    meta = meta or {}
    warnings: list[str] = []
    clean: list[dict] = []
    total = len(slides)

    for idx, raw in enumerate(slides):
        tag = f"slide {idx + 1}"
        if isinstance(raw, str) and raw.strip():
            raw = {"layout": "section", "title": raw.strip()[:60], "text": raw.strip()}
            warnings.append(f"{tag}: was plain text -> 'section' slide")
        if not isinstance(raw, dict):
            warnings.append(f"{tag}: not an object -> skipped")
            continue
        s = dict(raw)

        def w(msg, _tag=tag):
            warnings.append(f"{_tag}: {msg}")

        raw_layout = _first(s, "layout", "slide_type", "layout_type", "kind", "template")
        if raw_layout is None and isinstance(s.get("type"), str) and _canon_layout(s["type"])[0]:
            raw_layout = s["type"]
        if raw_layout is None and isinstance(s.get("section"), str) and _canon_layout(s["section"])[0]:
            raw_layout = s["section"]
        layout, note = _canon_layout(raw_layout) if raw_layout else (None, None)
        if note:
            w(note)
        if layout is None:
            layout = _infer_layout(s, idx, total)
            w(f"layout {raw_layout!r} unknown -> guessed {layout!r}" if raw_layout
              else f"no layout given -> guessed {layout!r}")
        try:
            fields = _normalise_slide(layout, s, w)
        except Exception as e:
            w(f"could not read fields ({type(e).__name__}: {e}) -> kept title only")
            fields = {}
        item = {"layout": layout, "title": _title_guess(s)}
        if layout == "section":
            probe = f"{raw_layout or ''} {item['title']}".lower().replace("_", " ")
            if re.search(r"background|latar belakang|pendahuluan|introduction|context", probe):
                item["_role"] = "background"
        if _s(_first(s, "agenda_label", "short_title")):
            item["agenda_label"] = _s(_first(s, "agenda_label", "short_title"))
        item.update({k: v for k, v in fields.items() if v not in (None, "", [], {})})
        if _s(_first(s, "notes", "speaker_notes")):
            item["notes"] = _s(_first(s, "notes", "speaker_notes"))
        clean.append(item)

    if not clean:
        return [], warnings

    # ---- one cover, one closing, shared organisation / tagline ----------------
    covers = [s for s in clean if s["layout"] == "cover"]
    for extra in covers[1:]:
        extra["layout"] = "section"
        warnings.append(f"second cover {extra['title']!r} -> 'section' slide")
    if not covers:
        warnings.append("deck has no 'cover' slide -> start the deck with {\"layout\":\"cover\",\"title\":...}")
    closings = [s for s in clean if s["layout"] == "closing"]
    for extra in closings[:-1]:
        extra["layout"] = "section"
    if not closings:
        clean.append({"layout": "closing", "title": "Thank You"})
        warnings.append("no 'closing' slide -> a 'Thank You' slide was added")
    cover = covers[0] if covers else {}
    closing = [s for s in clean if s["layout"] == "closing"][-1]
    for key in ("organization", "tagline"):
        shared = cover.get(key) or _s(meta.get(key))
        if shared and cover and not cover.get(key):
            cover[key] = shared
        if shared and not closing.get(key):
            closing[key] = shared

    # ---- standard section order -------------------------------------------------
    if not keep_order:
        ranks = []
        for i, s in enumerate(clean):
            r = float(ORDER[s["layout"]])
            if s["layout"] == "section" and s.get("_role") != "background":
                # a generic section header travels with the slide that follows it;
                # with nothing after it, it stays behind the slide before it
                nxt = next((t for t in clean[i + 1:] if t["layout"] != "section"), None)
                prev = next((t for t in reversed(clean[:i]) if t["layout"] != "section"), None)
                if nxt and CONTENT_RANKS[0] < ORDER[nxt["layout"]] < CONTENT_RANKS[1]:
                    r = ORDER[nxt["layout"]] - 0.5
                elif prev and CONTENT_RANKS[0] <= ORDER[prev["layout"]] < CONTENT_RANKS[1]:
                    r = ORDER[prev["layout"]] + 0.25
            ranks.append(r)
        order = sorted(range(len(clean)), key=lambda i: (ranks[i], i))
        if order != list(range(len(clean))):
            warnings.append("slides were re-ordered to the standard section order: "
                            + " > ".join(clean[i]["layout"] for i in order))
        clean = [clean[i] for i in order]

    # ---- agenda follows the real sections ----------------------------------------
    sections, seen = [], set()
    for s in clean:
        if CONTENT_RANKS[0] <= ORDER[s["layout"]] <= CONTENT_RANKS[1] and s["title"]:
            t = _agenda_label(s)
            if t.lower() not in seen:
                seen.add(t.lower())
                sections.append(t)
    agendas = [s for s in clean if s["layout"] == "agenda"]
    if not agendas and auto_agenda and len(sections) >= 4:
        pos = max((i for i, s in enumerate(clean) if s["layout"] in ("cover", "intro")), default=-1) + 1
        agenda = {"layout": "agenda", "title": "Agenda", "auto": True}
        clean.insert(pos, agenda)
        agendas = [agenda]
        warnings.append("no 'agenda' slide -> one was added from the section titles")
    for a in agendas:
        if a.pop("auto", True) and sections:
            if a.get("items") and [x.lower() for x in a["items"]] != [x.lower() for x in sections[:8]]:
                warnings.append("agenda items replaced by the real section titles so the numbering matches the slides")
            a["items"] = list(sections)
        if len(a.get("items", [])) > 8:
            warnings.append(f"agenda has {len(a['items'])} items, 8 fit -> only the first 8 are listed")
            a["items"] = a["items"][:8]
        if not a.get("title"):
            a["title"] = "Agenda"
    for s in clean:
        s.pop("_role", None)
        s.pop("agenda_label", None)
    return clean, warnings
