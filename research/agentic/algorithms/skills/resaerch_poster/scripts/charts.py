"""Inline-SVG charts for the poster.  Pure Python, no matplotlib.

    chart_svg({"type": "donut", "categories": [...], "series": [{"name":..., "values": [...]}]}, palette)

Types: donut, pie, bar (horizontal), column (vertical), line, pictograph, progress.
All charts are drawn in a 100 x 100-ish viewBox and scale with their box.
"""

from __future__ import annotations

import math
from html import escape

PALETTE = ["#0C3F83", "#60A6F7", "#F5B453", "#C9A7F5", "#EF737C", "#3CC8A4", "#F9D34E", "#8FA3C7"]
INK = "#1B2A41"
MUTED = "#5B6B85"


def _fmt(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        return f"{int(round(v)):,}".replace(",", ".") if abs(v) >= 10000 else str(int(round(v)))
    return f"{v:.1f}".rstrip("0").rstrip(".")


def _pct(values):
    total = sum(values) or 1
    return [v / total * 100 for v in values]


def _polar(cx, cy, r, ang):
    a = math.radians(ang - 90)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def _arc_path(cx, cy, r_out, r_in, a0, a1):
    a1 = min(a1, a0 + 359.999)
    x0, y0 = _polar(cx, cy, r_out, a0)
    x1, y1 = _polar(cx, cy, r_out, a1)
    xi0, yi0 = _polar(cx, cy, r_in, a1)
    xi1, yi1 = _polar(cx, cy, r_in, a0)
    large = 1 if a1 - a0 > 180 else 0
    return (f"M{x0:.2f},{y0:.2f} A{r_out},{r_out} 0 {large} 1 {x1:.2f},{y1:.2f} "
            f"L{xi0:.2f},{yi0:.2f} A{r_in},{r_in} 0 {large} 0 {xi1:.2f},{yi1:.2f} Z")


def donut(categories, values, palette, hole=0.52, labels=True, unit="%"):
    pct = _pct(values)
    cx = cy = 50
    r = 40
    parts = []
    ang = 0.0
    for i, (cat, p) in enumerate(zip(categories, pct)):
        if p <= 0:
            continue
        sweep = p / 100 * 360
        parts.append(f'<path d="{_arc_path(cx, cy, r, r * hole, ang, ang + sweep)}" fill="{palette[i % len(palette)]}"/>')
        if labels and p >= 6:
            lx, ly = _polar(cx, cy, r * (1 + hole) / 2, ang + sweep / 2)
            fill = "#fff" if i % len(palette) in (0, 4) else INK
            parts.append(f'<text x="{lx:.1f}" y="{ly + 1.4:.1f}" font-size="5.2" font-weight="700" fill="{fill}" '
                         f'text-anchor="middle">{_fmt(p)}{unit}</text>')
        ang += sweep
    return f'<svg viewBox="0 0 100 100" class="chart chart-donut">{"".join(parts)}</svg>'


def pie(categories, values, palette, **kw):
    return donut(categories, values, palette, hole=0.0, **kw).replace("chart-donut", "chart-pie")


def column(categories, series, palette, value_labels=True):
    n_cat, n_ser = len(categories), len(series)
    vmax = max((max(s["values"]) for s in series), default=1) or 1
    w, h, left, bottom, top = 100, 48, 3, 8, 6
    plot_w, plot_h = w - left - 2, h - bottom - top
    group_w = plot_w / max(n_cat, 1)
    bar_w = group_w * 0.72 / max(n_ser, 1)
    parts = [f'<line x1="{left}" y1="{h - bottom}" x2="{w - 2}" y2="{h - bottom}" stroke="#C7CFDD" stroke-width="0.6"/>']
    for gi in range(1, 4):  # light grid
        y = h - bottom - plot_h * gi / 4
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{w - 2}" y2="{y:.1f}" stroke="#E6EAF2" stroke-width="0.4"/>')
    for ci, cat in enumerate(categories):
        gx = left + ci * group_w + group_w * 0.14
        for si, s in enumerate(series):
            v = s["values"][ci] if ci < len(s["values"]) else 0
            bh = plot_h * v / vmax
            x = gx + si * bar_w
            y = h - bottom - bh
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w * 0.9:.2f}" height="{bh:.2f}" rx="1" '
                         f'fill="{palette[si % len(palette)]}"/>')
            if value_labels:
                parts.append(f'<text x="{x + bar_w * 0.45:.2f}" y="{y - 1.2:.2f}" font-size="3.2" font-weight="700" '
                             f'fill="{INK}" text-anchor="middle">{_fmt(v)}</text>')
        parts.append(f'<text x="{gx + group_w * 0.36:.2f}" y="{h - bottom + 4.5}" font-size="3.4" fill="{MUTED}" '
                     f'text-anchor="middle">{escape(str(cat))[:14]}</text>')
    return f'<svg viewBox="0 0 {w} {h}" class="chart chart-column">{"".join(parts)}</svg>'


def bar(categories, series, palette, value_labels=True):
    """Horizontal bars (first series; more series stacked side by side per category)."""
    n_cat, n_ser = len(categories), len(series)
    vmax = max((max(s["values"]) for s in series), default=1) or 1
    w = 100
    row_h = 9 if n_ser == 1 else 6 * n_ser + 3
    h = n_cat * row_h + 4
    label_w = 30
    plot_w = w - label_w - 12
    parts = []
    for ci, cat in enumerate(categories):
        y0 = 2 + ci * row_h
        parts.append(f'<text x="{label_w - 2}" y="{y0 + row_h / 2 + 1.5:.1f}" font-size="4.2" fill="{INK}" '
                     f'text-anchor="end">{escape(str(cat))[:22]}</text>')
        bh = (row_h - 3) / n_ser
        for si, s in enumerate(series):
            v = s["values"][ci] if ci < len(s["values"]) else 0
            bw = plot_w * v / vmax
            y = y0 + 1.5 + si * bh
            parts.append(f'<rect x="{label_w}" y="{y:.2f}" width="{bw:.2f}" height="{bh * 0.85:.2f}" rx="1.2" '
                         f'fill="{palette[si % len(palette)]}"/>')
            if value_labels:
                parts.append(f'<text x="{label_w + bw + 1.5:.2f}" y="{y + bh * 0.62:.2f}" font-size="4" '
                             f'font-weight="700" fill="{INK}">{_fmt(v)}</text>')
    return f'<svg viewBox="0 0 {w} {h}" class="chart chart-bar">{"".join(parts)}</svg>'


def line(categories, series, palette):
    n = len(categories)
    vmax = max((max(s["values"]) for s in series), default=1) or 1
    vmin = min((min(s["values"]) for s in series), default=0)
    vmin = min(vmin, 0)
    w, h, left, bottom, top = 100, 46, 4, 7, 5
    plot_w, plot_h = w - left - 4, h - bottom - top
    parts = [f'<line x1="{left}" y1="{h - bottom}" x2="{w - 2}" y2="{h - bottom}" stroke="#C7CFDD" stroke-width="0.6"/>']
    for gi in range(1, 4):
        y = h - bottom - plot_h * gi / 4
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{w - 2}" y2="{y:.1f}" stroke="#E6EAF2" stroke-width="0.4"/>')
    xs = [left + plot_w * (i / max(n - 1, 1)) for i in range(n)]
    for si, s in enumerate(series):
        pts = []
        for i, v in enumerate(s["values"][:n]):
            y = h - bottom - plot_h * (v - vmin) / (vmax - vmin or 1)
            pts.append((xs[i], y))
        d = " ".join(f"{'M' if i == 0 else 'L'}{x:.2f},{y:.2f}" for i, (x, y) in enumerate(pts))
        color = palette[si % len(palette)]
        parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.4" stroke-linejoin="round"/>')
        for x, y in pts:
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.3" fill="#fff" stroke="{color}" stroke-width="1"/>')
        if len(series) == 1:
            for (x, y), v in zip(pts, s["values"]):
                parts.append(f'<text x="{x:.2f}" y="{y - 2.6:.2f}" font-size="3.2" font-weight="700" fill="{INK}" '
                             f'text-anchor="middle">{_fmt(v)}</text>')
    for x, cat in zip(xs, categories):
        parts.append(f'<text x="{x:.2f}" y="{h - bottom + 4.5}" font-size="3.4" fill="{MUTED}" '
                     f'text-anchor="middle">{escape(str(cat))[:10]}</text>')
    return f'<svg viewBox="0 0 {w} {h}" class="chart chart-line">{"".join(parts)}</svg>'


_PERSON = ('<path d="M5 0a2.2 2.2 0 110 4.4A2.2 2.2 0 015 0zm-2 5h4c1.2 0 2 .8 2 2v4H7v5H3v-5H1V7c0-1.2.8-2 2-2z"/>')


def pictograph(value: float, total: float = 100, count: int = 10, color: str = "#0C3F83", faded: str = "#BFD4F2"):
    """Row of people icons, `value/total` of them filled."""
    filled = round(count * (value / (total or 1)))
    parts = []
    for i in range(count):
        parts.append(f'<g transform="translate({i * 11.5},0)" fill="{color if i < filled else faded}">{_PERSON}</g>')
    w = count * 11.5
    return f'<svg viewBox="-0.5 -0.5 {w} 17" class="chart chart-pictograph">{"".join(parts)}</svg>'


def progress(value: float, total: float = 100, color: str = "#0C3F83", track: str = "#DCE6F5"):
    p = max(0.0, min(1.0, value / (total or 1)))
    return (f'<svg viewBox="0 0 100 6" preserveAspectRatio="none" class="chart chart-progress">'
            f'<rect x="0" y="0" width="100" height="6" rx="3" fill="{track}"/>'
            f'<rect x="0" y="0" width="{p * 100:.1f}" height="6" rx="3" fill="{color}"/></svg>')


def legend(categories, series, palette, show_pct=True):
    if len(series) == 1:
        pct = _pct(series[0]["values"])
        items = []
        for i, (c, p, v) in enumerate(zip(categories, pct, series[0]["values"])):
            val = f"{_fmt(p)}%" if show_pct else _fmt(v)
            items.append(f'<li><i style="background:{palette[i % len(palette)]}"></i><b>{val}</b>'
                         f'<span>{escape(str(c))}</span></li>')
        cls = "legend legend-2col" if len(items) > 4 else "legend"
        return f'<ul class="{cls}">{"".join(items)}</ul>'
    items = [f'<li><i style="background:{palette[i % len(palette)]}"></i><span>{escape(str(s["name"]))}</span></li>'
             for i, s in enumerate(series)]
    return f'<ul class="legend legend-series">{"".join(items)}</ul>'


_T = {
    "en": {"rose": "rose", "fell": "fell", "stayed": "stayed at", "from_to": "From {a} to {b}, ", "while": " while ",
           "leads": "{c} leads with {p}% of the total.", "change": "{s} {v} {p}% from {a} to {b}.",
           "hilo": "{hi} scores highest ({hv}); {lo} lowest ({lv})."},
    "id": {"rose": "naik", "fell": "turun", "stayed": "tetap", "from_to": "Dari {a} ke {b}, ", "while": " sementara ",
           "leads": "{c} terbesar dengan {p}% dari total.", "change": "{s} {v} {p}% dari {a} ke {b}.",
           "hilo": "{hi} tertinggi ({hv}); {lo} terendah ({lv})."},
}


def insight_sentence(chart: dict, lang: str = "en") -> str:
    """One automatic analytic sentence from the data (used when the spec gives none)."""
    t = _T.get(lang, _T["en"])
    cats, series = chart.get("categories") or [], chart.get("series") or []
    if not cats or not series:
        return ""
    kind = chart.get("type", "donut")
    s0 = series[0]
    vals = s0["values"]
    if len(series) >= 2 and len(cats) >= 2 and kind in ("line", "column", "bar"):
        bits = []
        for s in series[:2]:
            a, b = s["values"][0], s["values"][-1]
            verb = t["rose"] if b > a else t["fell"] if b < a else t["stayed"]
            bits.append(f"{s['name']} {verb} {_fmt(a)} -> {_fmt(b)}")
        return t["from_to"].format(a=cats[0], b=cats[-1]) + t["while"].join(bits) + "."
    if kind in ("donut", "pie"):
        pct = _pct(vals)
        i = max(range(len(pct)), key=lambda k: pct[k])
        return t["leads"].format(c=cats[i], p=_fmt(pct[i]))
    if kind == "line" and len(vals) >= 2:
        first, last = vals[0], vals[-1]
        if first:
            ch = (last - first) / abs(first) * 100
            verb = t["rose"] if ch > 0 else t["fell"] if ch < 0 else t["stayed"]
            return t["change"].format(s=s0["name"], v=verb, p=_fmt(abs(ch)), a=cats[0], b=cats[-1])
    i = max(range(len(vals)), key=lambda k: vals[k])
    j = min(range(len(vals)), key=lambda k: vals[k])
    return t["hilo"].format(hi=cats[i], hv=_fmt(vals[i]), lo=cats[j], lv=_fmt(vals[j]))


def chart_svg(chart: dict, palette=None) -> str:
    palette = palette or PALETTE
    kind = chart.get("type", "donut")
    cats, series = chart["categories"], chart["series"]
    if kind == "pie":
        return pie(cats, series[0]["values"], palette)
    if kind == "column":
        return column(cats, series, palette)
    if kind == "bar":
        return bar(cats, series, palette)
    if kind == "line":
        return line(cats, series, palette)
    return donut(cats, series[0]["values"], palette)
