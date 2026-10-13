"""research-poster engine: JSON spec -> one-page poster (HTML, PDF, PNG).

The poster is an HTML page in the style of the "Blue and White Modern Consumer
Research Poster": tag, big title, subtitle, hero picture, numbered cards in two
columns, footer.  Charts are inline SVG.  The page fits ONE sheet (A2 default):
every card shrinks its text until it fits.

    python scripts/build_poster.py poster.json -o poster.pdf          # PDF (+ .html next to it)
    python scripts/build_poster.py poster.json -o poster.png          # PNG preview
    python scripts/build_poster.py poster.json -o poster.html         # HTML only (no browser needed)

PDF/PNG need a Chromium browser: Edge (already on Windows), Chrome, Chromium,
or the Python package playwright.  HTML needs nothing.

Python:
    from build_poster import build_poster, format_result
    result = build_poster(spec, "poster.pdf")      # never raises
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import charts  # noqa: E402
from icons import icon, resolve as resolve_icon  # noqa: E402
from spec_normalizer import normalize, parse_spec  # noqa: E402

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS_DIR.parent
FONT_DIR = SKILL_DIR / "assets" / "fonts"
OUTPUT_DIR_ENV = "PPTX_OUTPUT_DIR"
IMAGE_DIRS_ENV = "PPTX_IMAGE_DIRS"
BROWSER_ENV = "POSTER_BROWSER"

# paper name -> (width mm, height mm)
SIZES = {
    "A0": (841, 1189), "A1": (594, 841), "A2": (420, 594), "A3": (297, 420), "A4": (210, 297),
    "LETTER": (216, 279), "TABLOID": (279, 432), "24X36": (610, 914), "36X48": (914, 1219),
}



class Ctx:
    def __init__(self, image_dirs):
        self.warnings: list[str] = []
        self.image_dirs = [Path(d) for d in (image_dirs or [])]
        for d in os.environ.get(IMAGE_DIRS_ENV, "").split(os.pathsep):
            if d.strip():
                self.image_dirs.append(Path(d.strip()))
        self.image_dirs.append(Path.cwd())

    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

def _font_css() -> str:
    faces = []
    for weight, style, name in ((400, "normal", "400-normal"), (400, "italic", "400-italic"),
                                (500, "normal", "500-normal"), (600, "normal", "600-normal"),
                                (700, "normal", "700-normal"), (800, "normal", "800-normal")):
        f = FONT_DIR / f"poppins-latin-{name}.woff2"
        if f.is_file():
            b64 = base64.b64encode(f.read_bytes()).decode()
            faces.append(f"@font-face{{font-family:'Poppins';font-weight:{weight};font-style:{style};"
                         f"font-display:block;src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    return "\n".join(faces)


def _image_data_uri(ctx: Ctx, ref: str, label="image") -> str | None:
    if not ref:
        return None
    if re.match(r"^https?://", ref, re.I):
        ctx.warn(f"{label} {ref!r} is a web address - only local files are used")
        return None
    p = Path(ref[7:] if ref.startswith("file://") else ref).expanduser()
    cands = [p] if p.is_absolute() else [d / ref for d in ctx.image_dirs] + [d / Path(ref).name for d in ctx.image_dirs]
    path = next((c for c in cands if c.is_file()), None)
    if not path:
        ctx.warn(f"{label} {ref!r} not found - decorative panel used instead")
        return None
    try:
        from PIL import Image, ImageOps
        import io
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im)
            im.thumbnail((1600, 1600))
            buf = io.BytesIO()
            im.convert("RGB").save(buf, "JPEG", quality=85, optimize=True)
            data, mime = buf.getvalue(), "image/jpeg"
    except Exception:
        data = path.read_bytes()
        mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


# ---------------------------------------------------------------------------
# HTML pieces
# ---------------------------------------------------------------------------

def _e(s) -> str:
    return escape(str(s or ""), quote=True)


def _clean(text) -> str:
    text = "" if text is None else str(text)
    text = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: m.group(1) or m.group(2), text)
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text).strip()


def _title_html(title: str, highlight: str) -> str:
    words = _clean(title)
    if highlight and highlight.lower() in words.lower():
        i = words.lower().index(highlight.lower())
        return (_e(words[:i]) + f'<span class="hl">{_e(words[i:i + len(highlight)])}</span>' + _e(words[i + len(highlight):]))
    parts = words.split()
    if 3 <= len(parts) <= 4:  # no highlight given: accent the middle word like the reference
        mid = len(parts) // 2
        parts[mid] = f'<span class="hl">{_e(parts[mid])}</span>'
        return " ".join(_e(x) if not x.startswith("<span") else x for x in parts)
    return _e(words)


def _items_html(items, kind: str, theme) -> str:
    out = []
    for it in items:
        t, x = _e(_clean(it.get("title", ""))), _e(_clean(it.get("text", "")))
        if kind == "list":
            ic = resolve_icon(it.get("icon"), it.get("title", ""), default="check")
            out.append(f'<li><span class="li-ico">{icon(ic, "100%", theme["primary"])}</span>'
                       f'<div>{f"<b>{t}</b>" if t else ""}{f"<p>{x}</p>" if x else ""}</div></li>')
        else:
            out.append(f'<li><i class="dot"></i><div>{f"<b>{t}</b>" if t else ""}{f"<p>{x}</p>" if x else ""}</div></li>')
    return f'<ul class="items {kind}">{"".join(out)}</ul>'


PRESETS = {
    "blue": {"primary": "#0C3F83", "accent": "#60A6F7", "ink": "#141C2B", "muted": "#4F5D75", "page": "#ECEBF3",
             "card": "#FFFFFF", "soft": "#E3ECF9", "palette": charts.PALETTE, "header_style": "bar", "numbered": True,
             "corner": True},
    "purple": {"primary": "#5B21B6", "accent": "#A855F7", "ink": "#1E1B4B", "muted": "#5B5B7A", "page": "#F3EEFB",
               "card": "#FFFFFF", "soft": "#EDE4FB", "palette": ["#5B21B6", "#A855F7", "#F5B453", "#60A6F7", "#EF737C", "#3CC8A4"],
               "header_style": "pill", "numbered": False, "corner": False},
}
SPAN_NAMES = {"narrow": 4, "third": 4, "half": 6, "wide": 8, "full": 12}


def _weight(s: dict) -> int:
    """Rough amount of content in a section (characters)."""
    n = len(s.get("text", "")) + len(s.get("quote", ""))
    for it in s.get("items", []) or []:
        n += sum(len(str(v)) for v in it.values()) + 25
    if s.get("chart"):
        n += 260
    if s.get("pictograph"):
        n += 60
    return n


def _span(s: dict) -> int:
    w = s.get("width")
    if isinstance(w, (int, float)) and 1 <= int(w) <= 12:
        return int(w)
    if isinstance(w, str) and w.lower() in SPAN_NAMES:
        return SPAN_NAMES[w.lower()]
    if s["type"] == "columns":
        return 12
    wt = _weight(s)
    if s["type"] == "chart":
        return 8 if wt > 420 else 6
    return 4 if wt < 190 else 8 if wt > 460 else 6


def pack_rows(sections: list[dict]) -> list[list[tuple[dict, int]]]:
    """Arrange sections in rows of a 12-column grid; each row is stretched to 12."""
    rows, cur, used = [], [], 0
    for s in sections:
        sp = _span(s)
        if cur and used + sp > 12:
            lonely = len(cur) == 1 and cur[0][1] < 12 and sp < 12
            if not lonely:  # a single half-width card never sits alone in a row
                rows.append(cur)
                cur, used = [], 0
        cur.append((s, sp))
        used += sp
    if cur:
        rows.append(cur)
    # a lone half-width card joins a neighbouring row that has room (max 3 cards per row)
    i = 0
    while i < len(rows):
        row = rows[i]
        if len(row) == 1 and row[0][1] < 12 and row[0][0]["type"] != "columns":
            if i > 0 and len(rows[i - 1]) < 3 and all(sp < 12 for _, sp in rows[i - 1]):
                rows[i - 1].append(row[0]); del rows[i]; continue
            if i + 1 < len(rows) and len(rows[i + 1]) < 3 and all(sp < 12 for _, sp in rows[i + 1]):
                rows[i + 1].insert(0, row[0]); del rows[i]; continue
        i += 1
    out = []
    for row in rows:
        total = sum(sp for _, sp in row)
        spans = [max(4, round(sp * 12 / total)) for _, sp in row]
        while sum(spans) != 12:  # fix rounding
            i = max(range(len(spans)), key=lambda k: spans[k]) if sum(spans) > 12 else min(range(len(spans)), key=lambda k: spans[k])
            spans[i] += -1 if sum(spans) > 12 else 1
        out.append([(sec, sp) for (sec, _), sp in zip(row, spans)])
    return out


def _items_html(items, kind: str, theme) -> str:
    out = []
    for i, it in enumerate(items):
        t, x = _e(_clean(it.get("title", ""))), _e(_clean(it.get("text", "")))
        body = f'<div>{f"<b>{t}</b>" if t else ""}{f"<p>{x}</p>" if x else ""}</div>'
        if kind == "list":
            ic = resolve_icon(it.get("icon"), it.get("title", ""), default="check")
            out.append(f'<li><span class="li-ico">{icon(ic, "100%", theme["primary"])}</span>{body}</li>')
        elif kind == "numbered":
            out.append(f'<li><span class="li-num">{i + 1}</span>{body}</li>')
        else:
            out.append(f'<li><span class="li-check">{icon("check", "100%", theme["primary"])}</span>{body}</li>')
    return f'<ul class="items {kind}">{"".join(out)}</ul>'


def _section_html(ctx: Ctx, n: int, s: dict, theme: dict, span: int) -> str:
    kind, title = s["type"], _clean(s["title"])
    text = _clean(s.get("text", ""))
    body = []
    big_icon = None
    head_icon = resolve_icon(s.get("icon"), title, default="list")

    if kind == "text":
        big_icon = head_icon if span >= 6 else None
        body.append(f'<p class="para">{_e(text)}</p>')
    elif kind in ("bullets", "list"):
        if text:
            body.append(f'<p class="para lead">{_e(text)}</p>')
        style = "numbered" if s.get("numbered") else kind
        body.append(_items_html(s.get("items", []), style, theme))
    elif kind == "facts":
        big_icon = "people" if span >= 6 else None
        rows_html = "".join(f'<tr><th>{_e(_clean(it.get("label", "")))}</th><td>{_e(_clean(it.get("value", "")))}</td></tr>'
                            for it in s.get("items", []))
        body.append(f'<table class="facts">{rows_html}</table>')
        pg = s.get("pictograph")
        if pg:
            pg_label = pg.get("label") or f"{charts._fmt(pg['value'])} of {charts._fmt(pg['total'])}"
            body.append(f'<div class="picto">{charts.pictograph(pg["value"], pg["total"], 10, theme["primary"])}'
                        f'<span>{_e(pg_label)}</span></div>')
        if text:
            body.append(f'<p class="para small">{_e(text)}</p>')
    elif kind == "stats":
        rows_html = []
        for it in s.get("items", []):
            ic = resolve_icon(it.get("icon"), it.get("label", ""), default="check")
            value = str(it.get("value", ""))
            if re.fullmatch(r"\d{5,}", value):                  # "310000" reads better as 310.000 (310,000 in English)
                value = f"{int(value):,}".replace(",", "." if theme.get("lang") == "id" else ",")
            size = " xlong" if len(value) > 8 else " long" if len(value) > 5 else ""   # "Rp 310.000" must fit its column
            rows_html.append(
                f'<div class="stat"><span class="stat-ico">{icon(ic, "100%", theme["primary"])}</span>'
                f'<b class="stat-label">{_e(_clean(it.get("label", "")))}</b>'
                f'<span class="stat-val{size}">{_e(value)}</span>'
                f'<span class="stat-text">{_e(_clean(it.get("text", "")))}</span></div>')
        body.append(f'<div class="stats">{"".join(rows_html)}</div>')
        if text:
            body.append(f'<p class="para small">{_e(text)}</p>')
    elif kind == "chart":
        ch = s["chart"]
        if ch.get("rest") and theme.get("lang") == "id":
            ch["categories"][-1] = "Lainnya"
        palette = theme["palette"]
        svg = charts.chart_svg(ch, palette)
        wide = ch["type"] in ("column", "line", "bar")
        legend = charts.legend(ch["categories"], ch["series"], palette) if s.get("legend", True) and \
            (not wide or len(ch["series"]) > 1) else ""
        insight = _clean(s.get("insight") or charts.insight_sentence(ch, lang=theme.get("lang", "en")))
        body.append(f'<div class="chart-row {"wide" if wide else ""}"><div class="chart-box">{svg}</div>'
                    f'<div class="chart-side">{legend}</div></div>')
        if text:
            body.append(f'<p class="para small">{_e(text)}</p>')
        if insight and not s.get("quote"):
            s["quote"] = insight
    elif kind == "columns":
        cols = []
        for it in s.get("items", []):
            ic = resolve_icon(it.get("icon"), it.get("title", ""), default="star")
            cols.append(f'<div class="col"><span class="col-ico">{icon(ic, "100%", theme["primary"])}</span>'
                        f'<b>{_e(_clean(it.get("title", "")))}</b><p>{_e(_clean(it.get("text", "")))}</p></div>')
        if text:
            body.append(f'<p class="para lead">{_e(text)}</p>')
        body.append(f'<div class="columns" style="--n:{max(1, len(cols))}">{"".join(cols)}</div>')
    if s.get("quote"):
        body.append(f'<div class="quote"><span class="q">&#8220;</span>{_e(_clean(s["quote"]))}<span class="q r">&#8221;</span></div>')

    side = ""
    img = _image_data_uri(ctx, s.get("image", ""), f"image of section {n}") if s.get("image") else None
    if img:
        side = f'<div class="side-img"><img src="{img}" alt=""></div>'
    elif big_icon and theme.get("header_style") == "bar":
        side = f'<div class="big-ico">{icon(big_icon, "100%", theme["ink"])}</div>'
    elif big_icon and span >= 8:
        side = f'<div class="big-ico">{icon(big_icon, "100%", theme["ink"])}</div>'
    num = f'<span class="num">{n:02d}</span>' if theme.get("numbered") else ""
    head_ico = f'<span class="h-ico">{icon(head_icon, "100%", theme["primary"])}</span>' if theme.get("header_style") == "pill" else ""
    return (f'<section class="card {kind}" style="--span:{span}"><header>{num}{head_ico}<h2>{_e(title)}</h2></header>'
            f'<div class="card-body">{side}<div class="content">{"".join(body)}</div></div></section>')


_CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
:root{--pw:__PW__;--ph:__PH__;--u:calc(var(--pw) * 1mm / 100);
 --primary:__PRIMARY__;--accent:__ACCENT__;--ink:__INK__;--muted:__MUTED__;--page:__PAGE__;--card:__CARD__;--soft:__SOFT__;
 --base:__BASE__;--fs:1}
@page{size:calc(var(--pw) * 1mm) calc(var(--ph) * 1mm);margin:0}
html,body{width:calc(var(--pw) * 1mm);height:calc(var(--ph) * 1mm);background:var(--page);color:var(--ink);
 font-family:Poppins,'Segoe UI',Arial,sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact;overflow:hidden}
.page{position:relative;width:100%;height:100%;overflow:hidden;background:var(--page);display:flex;flex-direction:column}
.page::before{content:"";position:absolute;inset:0;pointer-events:none;
 background:linear-gradient(115deg,transparent 0 46%,rgba(255,255,255,.65) 46% 60%,transparent 60% 70%,rgba(255,255,255,.45) 70% 78%,transparent 78%)}
.preset-purple .page::before{background:
 radial-gradient(circle at 8% 22%,rgba(168,85,247,.12) 0 9%,transparent 9.5%),
 radial-gradient(circle at 92% 62%,rgba(168,85,247,.10) 0 12%,transparent 12.5%),
 radial-gradient(circle at 30% 88%,rgba(91,33,182,.07) 0 10%,transparent 10.5%),
 repeating-linear-gradient(0deg,transparent 0 calc(var(--u)*7.6),rgba(91,33,182,.035) calc(var(--u)*7.6) calc(var(--u)*7.75)),
 repeating-linear-gradient(90deg,transparent 0 calc(var(--u)*7.6),rgba(91,33,182,.035) calc(var(--u)*7.6) calc(var(--u)*7.75))}
.corner-shape{position:absolute;right:0;top:0;width:calc(var(--u)*42);height:calc(var(--u)*26);
 background:var(--primary);clip-path:polygon(100% 0,100% 100%,20% 100%,0 0);z-index:0}
.waves{position:absolute;right:0;top:0;width:calc(var(--u)*62);height:calc(var(--u)*34);z-index:0;opacity:.9}
.waves svg{width:100%;height:100%}
.header{position:relative;z-index:2;flex:none;min-height:calc(var(--u)*36);padding:calc(var(--u)*3) calc(var(--u)*3) calc(var(--u)*2)}
.tag{display:inline-flex;align-items:center;gap:calc(var(--u)*1.3);background:var(--primary);color:#fff;
 font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-size:calc(var(--u)*2.1);
 padding:calc(var(--u)*.9) calc(var(--u)*2.4);border-radius:calc(var(--u)*1)}
.preset-purple .tag{border-radius:calc(var(--u)*3);padding:calc(var(--u)*.9) calc(var(--u)*3)}
.tag .ico{width:calc(var(--u)*2.6);height:calc(var(--u)*2.6)}
.title{margin-top:calc(var(--u)*2);width:calc(var(--u)*50);font-weight:800;text-transform:uppercase;line-height:.98;
 font-size:calc(var(--u)*7);letter-spacing:-.01em;overflow-wrap:anywhere}
.title.long{font-size:calc(var(--u)*5.4)}
.title.xlong{font-size:calc(var(--u)*4.2);line-height:1.05}
.title .hl{color:var(--primary)}
.preset-purple .title{color:var(--primary)}
.preset-purple .title .hl{color:var(--accent)}
.subtitle{margin-top:calc(var(--u)*1.4);font-style:italic;font-size:calc(var(--u)*2.2);color:var(--ink);width:calc(var(--u)*50);line-height:1.25}
.subtitle::after{content:"";display:block;width:calc(var(--u)*11);height:calc(var(--u)*.55);background:var(--accent);
 margin-top:calc(var(--u)*1.2);border-radius:1em}
.preset-purple .subtitle{font-style:normal;font-weight:800;text-transform:uppercase;color:var(--accent);font-size:calc(var(--u)*3.2)}
.preset-purple .subtitle::after{display:none}
.lead{margin-top:calc(var(--u)*1.4);font-size:calc(var(--u)*1.7);line-height:1.4;color:var(--ink);width:calc(var(--u)*56)}
.hero{position:absolute;right:calc(var(--u)*11);top:calc(var(--u)*5.5);width:calc(var(--u)*38);height:calc(var(--u)*29);
 border-radius:calc(var(--u)*3.2) calc(var(--u)*.6);overflow:hidden;box-shadow:0 calc(var(--u)*1) calc(var(--u)*3) rgba(0,0,0,.2);
 background:var(--primary);z-index:2}
.preset-purple .hero{right:calc(var(--u)*3);top:calc(var(--u)*3.5);width:calc(var(--u)*34);height:calc(var(--u)*26);
 border-radius:calc(var(--u)*2.4);background:transparent;box-shadow:none}
.hero img{width:100%;height:100%;object-fit:cover;display:block}
.hero.plain{background:transparent;box-shadow:none;border-radius:0}
.hero.plain img{object-fit:contain}
.hero .deco{position:absolute;inset:0;background:
 radial-gradient(circle at 20% 30%,rgba(255,255,255,.18) 0 18%,transparent 19%),
 radial-gradient(circle at 75% 70%,rgba(255,255,255,.28) 0 26%,transparent 27%),
 linear-gradient(135deg,var(--primary),var(--accent))}
.preset-purple .hero .deco{border-radius:calc(var(--u)*2.4)}
.hero .deco .ico{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:26%;height:26%;color:rgba(255,255,255,.85)}
.corner{position:absolute;right:calc(var(--u)*2.5);top:calc(var(--u)*2.2);z-index:3;display:flex;flex-direction:column;gap:calc(var(--u)*1.2);align-items:flex-end}
.corner .ico{width:calc(var(--u)*5.2);height:calc(var(--u)*5.2);color:#fff}
.corner .dots{width:calc(var(--u)*6);height:calc(var(--u)*6);
 background-image:radial-gradient(circle,rgba(255,255,255,.85) 20%,transparent 22%);background-size:20% 20%}
.grid{position:relative;z-index:1;display:grid;grid-template-columns:repeat(12,1fr);grid-auto-rows:max-content;
 align-content:start;gap:calc(var(--u)*1.8) calc(var(--u)*2);padding:0 calc(var(--u)*3) calc(var(--u)*2);flex:1;min-height:0;
 font-size:calc(var(--u)*var(--base) * var(--fs))}
.layout-grid .grid{grid-auto-rows:1fr;align-content:stretch}
.card{grid-column:span var(--span);background:var(--card);border:calc(var(--u)*.32) solid var(--primary);border-radius:calc(var(--u)*1.6);
 overflow:hidden;display:flex;flex-direction:column;min-height:0;box-shadow:0 calc(var(--u)*.5) calc(var(--u)*1.4) rgba(0,0,0,.10)}
.card header{display:flex;align-items:stretch;background:var(--primary);color:#fff;height:calc(var(--u)*5.2);flex:none}
.card header .num{background:var(--accent);font-weight:800;font-size:calc(var(--u)*3.1);display:flex;align-items:center;
 padding:0 calc(var(--u)*3.4) 0 calc(var(--u)*2.6);clip-path:polygon(0 0,100% 0,85% 50%,100% 100%,0 100%)}
.card header h2{font-weight:700;text-transform:uppercase;letter-spacing:.05em;font-size:calc(var(--u)*2.45);
 display:flex;align-items:center;padding:0 calc(var(--u)*1.5) 0 calc(var(--u)*2.4);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.header-pill .card{border-width:calc(var(--u)*.18);border-color:var(--accent);border-radius:calc(var(--u)*2.2);
 box-shadow:0 calc(var(--u)*.6) calc(var(--u)*1.6) rgba(91,33,182,.10)}
.header-pill .card header{background:transparent;color:#fff;height:auto;padding:calc(var(--u)*.9) calc(var(--u)*1.5) 0;align-items:flex-start}
.header-pill .card header .h-ico{width:calc(var(--u)*3.5);height:calc(var(--u)*3.5);border-radius:50%;background:var(--soft);
 padding:calc(var(--u)*.8);flex:none;z-index:1;color:var(--primary);box-shadow:0 0 0 calc(var(--u)*.25) var(--card)}
.header-pill .card header .h-ico .ico{width:100%;height:100%}
.header-pill .card header h2{background:var(--primary);border-radius:0 calc(var(--u)*2.6) calc(var(--u)*2.6) 0;
 height:calc(var(--u)*3.1);margin:calc(var(--u)*.2) 0 0 calc(var(--u)*-1.8);padding:0 calc(var(--u)*2.6) 0 calc(var(--u)*3.2);
 font-size:calc(var(--u)*2.15);--h2:2.15;letter-spacing:.06em;max-width:calc(100% - var(--u)*2.5)}
.header-pill .card header .num{background:var(--accent);border-radius:50%;width:calc(var(--u)*3.6);height:calc(var(--u)*3.6);
 padding:0;clip-path:none;justify-content:center;font-size:calc(var(--u)*1.8);margin:calc(var(--u)*.5) calc(var(--u)*.8) 0 0}
.card-body{flex:1;min-height:0;display:flex;gap:1.1em;padding:calc(var(--u)*1.2) calc(var(--u)*1.8) calc(var(--u)*1.2) calc(var(--u)*1.6);
 line-height:1.35;overflow:hidden;font-size:calc(1em * var(--lfs,1))}
.header-pill .card-body{padding-top:calc(var(--u)*.9)}
.content{flex:1;min-width:0;min-height:0;display:flex;flex-direction:column;gap:.7em;justify-content:safe center}
.layout-flow .content{justify-content:flex-start}
.content>*{flex:none}
.big-ico{flex:none;width:7em;align-self:center;display:flex;justify-content:center}
.big-ico .ico{width:6.2em;height:6.2em;background:var(--soft);border-radius:50%;padding:1.3em}
.side-img{flex:none;width:32%;max-width:12em;align-self:center;display:flex;justify-content:center}
.side-img img{max-width:100%;max-height:11em;object-fit:contain}
.para{color:var(--ink)}
.para.small{font-size:.92em;color:var(--muted)}
.para.lead{font-size:.95em}
ul.items{list-style:none;display:flex;flex-direction:column;gap:.55em}
ul.items li{display:flex;gap:.7em;align-items:flex-start}
ul.items b{display:block;font-weight:700;font-size:1.02em}
ul.items p{color:var(--muted);font-size:.9em;line-height:1.3}
ul.items .li-check{flex:none;width:1.5em;height:1.5em;color:var(--primary);margin-top:.05em}
ul.items .li-ico{flex:none;width:2.4em;height:2.4em;color:var(--primary);background:var(--soft);border-radius:50%;padding:.45em}
ul.items .li-num{flex:none;width:2em;height:2em;border-radius:50%;background:var(--primary);color:#fff;font-weight:800;
 display:flex;align-items:center;justify-content:center;font-size:.95em}
table.facts{border-collapse:collapse;width:100%}
table.facts th{text-align:left;font-weight:700;padding:.2em .7em .2em 0;white-space:nowrap;width:1%;vertical-align:top}
table.facts td{color:var(--primary);font-weight:600;padding:.2em 0;vertical-align:top}
.picto{display:flex;align-items:center;gap:.8em;margin-top:.2em}
.picto svg{width:14em;height:auto}
.picto span{font-size:.85em;color:var(--muted);font-weight:600}
.stats{display:flex;flex-direction:column;gap:.5em}
.card[style*="--span:12"] .stats,.card[style*="--span:10"] .stats{display:grid;grid-template-columns:1fr 1fr;column-gap:2em}
.stat{display:grid;grid-template-columns:2.8em 1fr 4.6em 1.1fr;align-items:center;gap:.7em}
.stat-ico{width:2.8em;height:2.8em;background:var(--soft);border-radius:50%;padding:.55em;color:var(--primary)}
.stat-label{font-weight:700;font-size:1.02em;line-height:1.2}
.stat-val{font-weight:800;font-size:1.65em;color:var(--primary);text-align:center;letter-spacing:-.02em;line-height:1}
.stat-val.long{font-size:1.2em}
.stat-val.xlong{font-size:.98em;line-height:1.1}
.stat-text{font-size:.86em;color:var(--muted);line-height:1.25}
.chart-row{display:flex;gap:1.2em;align-items:center;flex:none;flex-wrap:wrap}
.chart-box{flex:none;width:12em;max-width:100%}
.card[style*="--span:4"] .chart-box{width:9em}
.chart-row.wide{flex-direction:column;align-items:stretch}
.chart-row.wide .chart-box{width:100%;max-width:none}
.chart-box svg{width:100%;height:auto;display:block}
.chart-side{flex:1 1 8.5em;min-width:8.5em;display:flex;flex-direction:column;gap:.6em}
ul.legend{list-style:none;display:flex;flex-direction:column;gap:.3em}
ul.legend li{display:flex;align-items:center;gap:.6em;font-size:.92em;min-width:0}
ul.legend li span{min-width:0;overflow-wrap:anywhere}
ul.legend i{flex:none;width:.7em;height:.7em;border-radius:50%}
ul.legend b{color:var(--primary);font-weight:800;font-size:1.25em;min-width:2.6em}
ul.legend.legend-series{flex-direction:row;flex-wrap:wrap;gap:1em}
ul.legend.legend-2col{display:grid;grid-template-columns:1fr 1fr;column-gap:1em}
.columns{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:1.2em}
.col{display:flex;flex-direction:column;gap:.35em}
.col .col-ico{width:3.2em;height:3.2em;background:var(--soft);border-radius:50%;padding:.7em;color:var(--primary)}
.col b{font-weight:700;font-size:1.05em}
.col p{color:var(--muted);font-size:.9em;line-height:1.3}
.quote{overflow:hidden;background:var(--soft);border-radius:1em;padding:.55em 1.2em;font-size:.92em;text-align:center;color:var(--ink);font-weight:500}
.quote .q{font-size:2.1em;line-height:0;vertical-align:-.3em;color:var(--primary);font-weight:800;margin-right:.15em}
.quote .q.r{margin:0 0 0 .15em;vertical-align:-.55em}
.footer{flex:none;min-height:calc(var(--u)*4.5);background:var(--primary);color:#fff;z-index:2;
 display:flex;align-items:center;justify-content:center;font-size:calc(var(--u)*1.8);font-weight:500;letter-spacing:.02em;
 padding:0 calc(var(--u)*3);white-space:nowrap;overflow:hidden}
.footer.banner{justify-content:space-between;gap:calc(var(--u)*3);padding:calc(var(--u)*1.4) calc(var(--u)*3);white-space:normal;
 background:linear-gradient(90deg,var(--primary),var(--accent))}
.footer.banner .slogan{display:flex;align-items:center;gap:calc(var(--u)*1.5);font-weight:800;text-transform:uppercase;
 font-size:calc(var(--u)*3.2);line-height:1.05;letter-spacing:.01em;flex:none;max-width:52%}
.footer.banner .slogan .ico{width:calc(var(--u)*5);height:calc(var(--u)*5);flex:none}
.footer.banner .ftext{font-size:calc(var(--u)*1.55);line-height:1.35;font-weight:400;text-align:right;max-width:44%}
"""

_JS = r"""
(function(){
  function run(){
  var grid=document.querySelector('.grid');
  var flow=document.documentElement.classList.contains('layout-flow');
  function fits(el){return el.scrollHeight<=el.clientHeight+1&&el.scrollWidth<=el.clientWidth+1}
  if(flow){
    // whole-grid scale: rows keep their natural height, the scale makes them fill the page
    var s=1.0;
    for(var i=0;i<4;i++){
      var avail=grid.clientHeight,need=grid.scrollHeight;
      if(!avail||!need)break;
      var r=avail/need;if(Math.abs(1-r)<0.015)break;
      s=Math.max(0.55,Math.min(1.6,s*Math.pow(r,0.9)));
      grid.style.setProperty('--fs',s.toFixed(3));
    }
    while(grid.scrollHeight>grid.clientHeight+1&&s>0.55){s-=0.02;grid.style.setProperty('--fs',s.toFixed(3));}
    if(grid.scrollHeight>grid.clientHeight+1){grid.setAttribute('data-overflow','1');}
    var cards=grid.querySelectorAll('.card');var last=cards[cards.length-1];
    var used=last?last.getBoundingClientRect().bottom-grid.getBoundingClientRect().top:0;
    if(last&&used<grid.clientHeight-8){ // sparse content: let the rows share the leftover height
      grid.style.gridAutoRows='auto';grid.style.alignContent='stretch';
      grid.querySelectorAll('.content').forEach(function(c){c.style.justifyContent='safe center';});
    }
    // cards shorter than their row grow their own text until the row would grow
    // a growing card takes height from the other rows, so every card is checked, not only the one that grows
    var H=grid.scrollHeight;
    var bodies=grid.querySelectorAll('.card-body');
    function cut(){return Array.prototype.some.call(bodies,function(x){return x.scrollHeight>x.clientHeight+1||x.scrollWidth>x.clientWidth+1})}
    bodies.forEach(function(b){
      var l=1.0;
      for(var k=0;k<8;k++){
        var t=l+0.06;b.style.setProperty('--lfs',t.toFixed(2));
        var wide=Array.prototype.some.call(b.querySelectorAll('li,.stat,.col,.para'),function(k){return k.scrollWidth>k.clientWidth+1});
        if(wide||grid.scrollHeight>H+1||cut()){b.style.setProperty('--lfs',l.toFixed(2));break;}
        l=t;
      }
    });
  }else{
    document.querySelectorAll('.card-body').forEach(function(b){
      var c=b.querySelector('.content');var s=1.0;
      c.style.justifyContent='flex-start';
      function ok(){return fits(b)&&fits(c)&&Array.prototype.every.call(c.children,function(k){return k.classList.contains('quote')||fits(k)})}
      while(!ok()&&s>0.5){s-=0.03;b.style.setProperty('--fs',s.toFixed(2));}
      if(s>=1.0){while(s<1.3){s+=0.05;b.style.setProperty('--fs',s.toFixed(2));if(!ok()){s-=0.05;b.style.setProperty('--fs',s.toFixed(2));break;}}}
      c.style.justifyContent='';
      if(!ok()){b.setAttribute('data-overflow','1');}
    });
  }
  document.querySelectorAll('.card header h2').forEach(function(h){
    var t=1;while(h.scrollWidth>h.clientWidth+1&&t>0.6){t-=0.05;h.style.fontSize='calc(var(--u)*var(--h2,2.45)*'+t.toFixed(2)+')';}
    if(h.scrollWidth>h.clientWidth+1){h.style.whiteSpace='normal';h.style.lineHeight='1.05';} // still too long: two lines instead of a cut title
  });
  var f=document.querySelector('.footer:not(.banner)');
  if(f){var t=1;while(f.scrollWidth>f.clientWidth+1&&t>0.5){t-=0.05;f.style.fontSize='calc(var(--u)*1.8*'+t.toFixed(2)+')';}}
  document.documentElement.setAttribute('data-fit','done');
  }
  if(document.fonts&&document.fonts.ready){document.fonts.ready.then(run);}else{run();}
})();
"""

_WAVES = ('<svg viewBox="0 0 620 340" fill="none" stroke="__C__" stroke-width="2.2" stroke-linecap="round" opacity=".55">'
          + "".join(f'<path d="M-20 {60 + k * 18} C 120 {20 + k * 18}, 200 {120 + k * 18}, 330 {70 + k * 18} S 520 {30 + k * 18}, 640 {90 + k * 18}"/>'
                    for k in range(7)) + "</svg>")

_ID_WORDS = {"dan", "yang", "untuk", "dengan", "dari", "pada", "ini", "adalah", "tidak", "responden", "penelitian",
             "hasil", "dalam", "atau", "lebih", "kami", "tujuan", "metode"}


def _detect_lang(p: dict) -> str:
    text = " ".join(str(v) for v in json.dumps(p, ensure_ascii=False).lower().split())
    words = re.findall(r"[a-z]+", text)
    hits = sum(1 for w in words if w in _ID_WORDS)
    return "id" if words and hits / len(words) > 0.03 else "en"


# The example in the prompt is in English, and a small model copies its headings into an Indonesian poster.
_ID_TEXT = {
    "research project": "Proyek Penelitian", "research overview": "Ringkasan Penelitian", "overview": "Ringkasan",
    "objectives": "Tujuan", "target audience": "Responden", "research methods": "Metode Penelitian",
    "methods": "Metode", "methodology": "Metodologi", "key findings": "Temuan Utama", "findings": "Temuan",
    "customer insights": "Wawasan Konsumen", "insights": "Wawasan", "market trends": "Tren Pasar", "trends": "Tren",
    "recommendations": "Rekomendasi", "conclusion": "Kesimpulan", "conclusions": "Kesimpulan",
    "age range": "Rentang usia", "age": "Usia", "gender": "Jenis kelamin", "location": "Lokasi",
    "income level": "Tingkat pendapatan", "sample size": "Jumlah sampel",
    "online survey": "Survei online", "interviews": "Wawancara", "focus group discussion": "Diskusi kelompok terarah",
    "data analysis": "Analisis data",
}


def _localize(ctx: Ctx, p: dict) -> None:
    """Put the stock English headings of an Indonesian poster into Indonesian."""
    changed = 0

    def swap(holder: dict, key: str) -> None:
        nonlocal changed
        new = _ID_TEXT.get(str(holder.get(key, "")).strip().lower())
        if new:
            holder[key], changed = new, changed + 1

    swap(p, "tag")
    for s in p["sections"]:
        swap(s, "title")
        for it in s.get("items", []):
            if isinstance(it, dict):
                swap(it, "label" if s.get("type") == "facts" else "title")
        pg = s.get("pictograph") or {}
        m = re.fullmatch(r"(\d[\d.,]*) of (\d[\d.,]*) invited took part", str(pg.get("label", "")).strip())
        if m:
            pg["label"], changed = f"{m.group(1)} dari {m.group(2)} yang diundang ikut serta", changed + 1
    if changed:
        ctx.warn(f"{changed} English headings in an Indonesian poster -> translated")


def _theme(ctx: Ctx, p: dict) -> dict:
    raw = p.get("theme") or {}
    if isinstance(raw, str):
        raw = {"preset": raw}
    preset = str(raw.get("preset", "blue")).lower()
    if preset not in PRESETS:
        ctx.warn(f"theme preset {preset!r} unknown -> 'blue' (valid: {', '.join(PRESETS)})")
        preset = "blue"
    theme = dict(PRESETS[preset])
    theme["preset"] = preset
    for k, v in raw.items():
        if k == "palette" and isinstance(v, list) and v:
            theme["palette"] = [str(x) for x in v]
        elif k in ("header_style",) and v in ("bar", "pill"):
            theme[k] = v
        elif k in ("numbered", "corner") and isinstance(v, bool):
            theme[k] = v
        elif k in theme and isinstance(v, str) and re.fullmatch(r"#?[0-9a-fA-F]{6}", v.strip()):
            theme[k] = "#" + v.strip().lstrip("#")
    return theme


def render_html(ctx: Ctx, p: dict) -> str:
    theme = _theme(ctx, p)
    pw, ph = SIZES.get(p.get("size", "A2"), SIZES["A2"])
    if p.get("size") not in SIZES:
        ctx.warn(f"size {p.get('size')!r} unknown -> A2 (valid: {', '.join(SIZES)})")
    theme["lang"] = p.get("language") or _detect_lang(p)
    if theme["lang"] == "id":
        _localize(ctx, p)
    layout = p.get("layout", "flow")
    rows = pack_rows(p["sections"]) if layout == "flow" else [[(s, 6) for s in p["sections"]]]
    if layout != "flow":
        n = len(p["sections"])
        if n % 2:
            rows[0][-1] = (rows[0][-1][0], 12)
    n_rows = len(rows) if layout == "flow" else max(1, (len(p["sections"]) + 1) // 2)

    title = _clean(p["title"])
    title_cls = "xlong" if len(title) > 44 else "long" if len(title) > 26 else ""
    hero = _image_data_uri(ctx, p.get("hero_image", ""), "hero_image")
    plain = "plain" if p.get("hero_style") == "plain" else ""
    hero_html = (f'<div class="hero {plain}"><img src="{hero}" alt=""></div>' if hero
                 else f'<div class="hero"><div class="deco">{icon("chart", "100%", "#fff")}</div></div>')
    sections, i = [], 0
    for row in rows:
        for sec, span in row:
            i += 1
            sections.append(_section_html(ctx, i, sec, theme, span))
    footer = p.get("footer", "")
    if isinstance(footer, dict):
        slogan, ftext = _clean(footer.get("slogan", "")), _clean(footer.get("text", ""))
        f_icon = resolve_icon(footer.get("icon"), slogan, default="globe")
        footer_html = (f'<div class="footer banner"><div class="slogan">{icon(f_icon, "1em", "#fff")}<span>{_e(slogan)}</span></div>'
                       f'<div class="ftext">{_e(ftext)}</div></div>') if (slogan or ftext) else ""
    else:
        footer_html = f'<div class="footer">{_e(_clean(footer))}</div>' if _clean(footer) else ""

    base = {1: 2.0, 2: 1.75, 3: 1.5}.get(n_rows, 1.32) if layout != "flow" else 1.5
    css = (_CSS.replace("__PW__", str(pw)).replace("__PH__", str(ph)).replace("__BASE__", str(base))
           .replace("__PRIMARY__", theme["primary"]).replace("__ACCENT__", theme["accent"])
           .replace("__INK__", theme["ink"]).replace("__MUTED__", theme["muted"]).replace("__PAGE__", theme["page"])
           .replace("__CARD__", theme["card"]).replace("__SOFT__", theme["soft"]))
    deco = ('<div class="corner-shape"></div><div class="corner">' + icon("trend", "1em", "#fff")
            + '<div class="dots"></div>' + icon("people", "1em", "#fff") + '</div>') if theme.get("corner") \
        else f'<div class="waves">{_WAVES.replace("__C__", theme["accent"])}</div>'
    lead = _clean(p.get("lead", ""))
    cls = f"preset-{theme['preset']} header-{theme['header_style']} layout-{layout}"
    return f"""<!DOCTYPE html>
<html lang="{theme['lang']}" class="{cls}"><head><meta charset="utf-8"><title>{_e(title)}</title>
<style>{_font_css()}
{css}</style></head>
<body><div class="page">
{deco}
<div class="header">
  <div class="tag">{icon("chart", "1em", "#fff")}<span>{_e(_clean(p.get("tag", "")))}</span></div>
  <h1 class="title {title_cls}">{_title_html(title, p.get("highlight", ""))}</h1>
  {f'<p class="subtitle">{_e(_clean(p["subtitle"]))}</p>' if p.get("subtitle") else ''}
  {f'<p class="lead">{_e(lead)}</p>' if lead else ''}
</div>
{hero_html}
<div class="grid">{"".join(sections)}</div>
{footer_html}
</div>
<script>{_JS}</script></body></html>"""


# ---------------------------------------------------------------------------
# Rendering with a Chromium browser
# ---------------------------------------------------------------------------

def find_browser() -> str | None:
    env = os.environ.get(BROWSER_ENV)
    if env and Path(env).is_file():
        return env
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome", "msedge",
                 "microsoft-edge"):
        exe = shutil.which(name)
        if exe:
            return exe
    win = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for c in win:
        if Path(c).is_file():
            return c
    try:  # playwright's own chromium, if the package + browser are installed
        from playwright.sync_api import sync_playwright  # noqa: F401
        return "playwright"
    except ImportError:
        return None


def _render_with_playwright(html_path: Path, out: Path, kind: str, pw_mm, ph_mm):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": int(pw_mm / 25.4 * 96), "height": int(ph_mm / 25.4 * 96)})
        page.goto(html_path.as_uri())
        page.wait_for_function("document.documentElement.getAttribute('data-fit')==='done'")
        if kind == "pdf":
            page.pdf(path=str(out), width=f"{pw_mm}mm", height=f"{ph_mm}mm", print_background=True,
                     margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        else:
            page.screenshot(path=str(out), full_page=False)
        b.close()


def render_file(ctx: Ctx, html_path: Path, out: Path, kind: str, pw_mm: int, ph_mm: int) -> bool:
    browser = find_browser()
    if not browser:
        ctx.warn(f"no Chromium browser found - only the HTML was written ({html_path.name}); "
                 "open it in a browser and print to PDF, or install Edge/Chrome, or `pip install playwright && playwright install chromium`")
        return False
    try:
        if browser == "playwright":
            _render_with_playwright(html_path, out, kind, pw_mm, ph_mm)
            return out.is_file()
        with tempfile.TemporaryDirectory() as profile:
            args = [browser, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                    f"--user-data-dir={profile}", "--no-first-run", "--disable-extensions",
                    "--run-all-compositor-stages-before-draw", "--virtual-time-budget=4000"]
            if kind == "pdf":
                args += ["--no-pdf-header-footer", f"--print-to-pdf={out}"]
            else:
                w, h = round(pw_mm / 25.4 * 96), round(ph_mm / 25.4 * 96)
                args += [f"--screenshot={out}", f"--window-size={w},{h}", "--force-device-scale-factor=1"]
            args.append(html_path.as_uri())
            r = subprocess.run(args, capture_output=True, text=True, timeout=180)
            if not out.is_file():
                ctx.warn(f"browser did not write {out.name}: {(r.stderr or '')[-300:].strip()}")
                return False
            return True
    except Exception as e:
        ctx.warn(f"rendering failed ({type(e).__name__}: {e}) - the HTML was written")
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _result(ok, **kw):
    d = {"ok": ok}
    d.update(kw)
    return d


def build_poster(spec, filename: str = "poster.pdf", output_dir=None, image_dirs=None, keep_order: bool = False,
                 strict: bool = False, png: bool = False) -> dict:
    """Build the poster.  Returns a dict and never raises.

    filename ending: .pdf (default) -> PDF + HTML, .png -> PNG + HTML, .html -> HTML only.
    png=True also writes a PNG preview next to a PDF.
    """
    ctx = Ctx(image_dirs)
    try:
        poster, meta = parse_spec(spec)
    except ValueError as e:
        return _result(False, error=f"Invalid JSON: {e}",
                       hint='Send {"title":"...","sections":[{"type":"text","title":"...","text":"..."}, ...]}',
                       warnings=[])
    if meta.get("truncated"):
        ctx.warn("JSON was cut off (token limit?) - only the complete sections were used")
    poster, norm_warnings = normalize(poster, meta, keep_order=keep_order)
    ctx.warnings += norm_warnings
    if not poster["sections"]:
        return _result(False, error="No usable sections in the spec.",
                       hint='Each section is {"type":"text|bullets|list|facts|stats|chart","title":"...", ...}',
                       warnings=ctx.warnings)
    if strict and ctx.warnings:
        return _result(False, error="Spec needed repairs (strict mode).", hint="Fix the listed items.",
                       warnings=ctx.warnings)

    name = str(filename or "poster.pdf")
    ext = Path(name).suffix.lower()
    if ext not in (".pdf", ".png", ".html"):
        name, ext = name + ".pdf", ".pdf"
    out = Path(name).expanduser()
    if not out.is_absolute():
        out = Path(output_dir or os.environ.get(OUTPUT_DIR_ENV) or (Path.cwd() / "output")) / out
    out = out.resolve()
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        html = render_html(ctx, poster)
        html_path = out.with_suffix(".html")
        html_path.write_text(html, encoding="utf-8")
    except Exception as e:
        return _result(False, error=f"Could not write the poster: {type(e).__name__}: {e}", hint="",
                       warnings=ctx.warnings)

    pw, ph = SIZES.get(poster["size"], SIZES["A2"])
    files = {"html": str(html_path)}
    if ext in (".pdf", ".png"):
        if render_file(ctx, html_path, out, "pdf" if ext == ".pdf" else "png", pw, ph):
            files[ext[1:]] = str(out)
    if png and ext == ".pdf" and "pdf" in files:
        png_path = out.with_suffix(".png")
        if render_file(ctx, html_path, png_path, "png", pw, ph):
            files["png"] = str(png_path)
    path = files.get(ext[1:], files["html"])
    return _result(True, path=path, files=files, size=poster["size"], sections=len(poster["sections"]),
                   order=[s["title"] for s in poster["sections"]], warnings=ctx.warnings)


def format_result(res: dict) -> str:
    if res.get("ok"):
        lines = [f"OK: created {res['path']} ({res['sections']} sections, {res['size']})"]
        extra = [f"{k.upper()}: {v}" for k, v in res.get("files", {}).items() if v != res["path"]]
        lines += extra
        lines.append("ORDER: " + " > ".join(res.get("order", [])))
    else:
        lines = [f"ERROR: {res.get('error')}"]
        if res.get("hint"):
            lines.append(f"HINT: {res['hint']}")
    ws = res.get("warnings") or []
    if ws:
        lines.append(f"AUTO-FIXED / WARNINGS ({len(ws)}):")
        lines += [f"- {w}" for w in ws[:14]]
        if len(ws) > 14:
            lines.append(f"- ... and {len(ws) - 14} more")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build a one-page research poster from a JSON spec (see SKILL.md).")
    ap.add_argument("spec", help="JSON file, or '-' for stdin")
    ap.add_argument("-o", "--output", default="poster.pdf", help=".pdf, .png or .html")
    ap.add_argument("--png", action="store_true", help="Also write a PNG preview next to the PDF")
    ap.add_argument("--keep-order", action="store_true", help="Do not sort sections into the standard order")
    ap.add_argument("--strict", action="store_true", help="Fail instead of repairing the spec")
    ap.add_argument("--json", action="store_true", help="Print the result as JSON")
    args = ap.parse_args(argv)
    if args.spec == "-":
        raw, dirs = sys.stdin.read(), []
    else:
        p = Path(args.spec)
        if not p.is_file():
            print(f"ERROR: spec file not found: {p}")
            return 2
        raw, dirs = p.read_text(encoding="utf-8-sig"), [p.resolve().parent]
    out = Path(args.output)
    res = build_poster(raw, filename=str(out if out.is_absolute() else Path.cwd() / out), image_dirs=dirs,
                       keep_order=args.keep_order, strict=args.strict, png=args.png)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else format_result(res))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
