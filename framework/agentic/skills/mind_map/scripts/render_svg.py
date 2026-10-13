"""Mind map layout + SVG drawing.  Pure Python (font widths from font_metrics).

    svg = render(root, theme="rainbow", title="...", layout="radial"|"right", font_scale=1.0)

Layout:  root in the centre; level-1 branches alternate right / left ("radial",
the classic two-sided mind map) or all grow to the right ("right", a tree).
Each subtree is stacked vertically and its parent sits at its vertical centre.
Nodes wrap their text; connectors are cubic curves in the branch colour.
"""

from __future__ import annotations

import base64
import re
from html import escape
from pathlib import Path

from font_metrics import text_width

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"

THEMES = {
    "rainbow": {"bg": "#FFFFFF", "root": "#1F2937", "root_text": "#FFFFFF", "ink": "#1F2937", "muted": "#6B7280",
                "palette": ["#2563EB", "#16A34A", "#EA580C", "#9333EA", "#DB2777", "#0891B2", "#CA8A04", "#DC2626"]},
    "blue": {"bg": "#F5F8FF", "root": "#0C3F83", "root_text": "#FFFFFF", "ink": "#14213D", "muted": "#5B6B85",
             "palette": ["#0C3F83", "#2563EB", "#0891B2", "#60A6F7", "#1E40AF", "#3B82F6", "#0E7490", "#4F46E5"]},
    "pastel": {"bg": "#FFFDF7", "root": "#374151", "root_text": "#FFFFFF", "ink": "#374151", "muted": "#6B7280",
               "palette": ["#F87171", "#FB923C", "#FACC15", "#4ADE80", "#38BDF8", "#A78BFA", "#F472B6", "#2DD4BF"]},
    "dark": {"bg": "#0F172A", "root": "#F8FAFC", "root_text": "#0F172A", "ink": "#E2E8F0", "muted": "#94A3B8",
             "palette": ["#60A5FA", "#4ADE80", "#FB923C", "#C084FC", "#F472B6", "#22D3EE", "#FACC15", "#F87171"]},
    "mono": {"bg": "#FFFFFF", "root": "#111827", "root_text": "#FFFFFF", "ink": "#111827", "muted": "#6B7280",
             "palette": ["#111827", "#374151", "#4B5563", "#1F2937", "#6B7280", "#374151", "#111827", "#4B5563"]},
}

# per depth: font size, weight, max text width (px), padding
LEVEL = {
    0: {"size": 24, "face": "bold", "max_w": 260, "pad": (18, 12)},
    1: {"size": 17, "face": "semibold", "max_w": 220, "pad": (12, 7)},
    2: {"size": 14, "face": "regular", "max_w": 210, "pad": (8, 4)},
    3: {"size": 13, "face": "regular", "max_w": 200, "pad": (7, 3)},
    4: {"size": 12, "face": "regular", "max_w": 190, "pad": (6, 3)},
}
H_GAP = {0: 70, 1: 48, 2: 36, 3: 30, 4: 26}      # horizontal distance parent -> child
V_GAP = {1: 22, 2: 12, 3: 8, 4: 6}                # vertical distance between siblings' subtrees
NOTE_SIZE = 11


def _wrap(text: str, size: float, face: str, max_w: float) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if text_width(trial, size, face) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


class Box:
    __slots__ = ("node", "depth", "lines", "note_lines", "w", "h", "x", "y", "kids", "color", "side", "ci")

    def __init__(self, node, depth):
        self.node, self.depth = node, depth
        self.kids: list[Box] = []
        self.x = self.y = 0.0
        self.color = "#000"
        self.side = 1
        self.ci = 0


def _measure(box: Box, fs: float):
    lv = LEVEL[min(box.depth, 4)]
    size, face = lv["size"] * fs, lv["face"]
    text = box.node["text"]
    if box.node.get("icon"):
        text = f"{box.node['icon']} {text}"
    box.lines = _wrap(text, size, face, lv["max_w"] * fs)
    box.note_lines = _wrap(box.node["note"], NOTE_SIZE * fs, "regular", lv["max_w"] * fs)[:2] if box.node.get("note") else []
    tw = max(text_width(ln, size, face) for ln in box.lines)
    if box.note_lines:
        tw = max(tw, max(text_width(ln, NOTE_SIZE * fs, "regular") for ln in box.note_lines))
    px, py = lv["pad"]
    box.w = tw + 2 * px * fs
    box.h = len(box.lines) * size * 1.25 + 2 * py * fs + (len(box.note_lines) * NOTE_SIZE * fs * 1.25 + 2 * fs if box.note_lines else 0)
    for k in box.kids:
        _measure(k, fs)


def _build(node, depth) -> Box:
    b = Box(node, depth)
    b.kids = [_build(k, depth + 1) for k in node.get("children", [])]
    return b


def _subtree_h(box: Box, fs: float) -> float:
    if not box.kids:
        return box.h
    gap = V_GAP[min(box.depth + 1, 4)] * fs
    return max(box.h, sum(_subtree_h(k, fs) for k in box.kids) + gap * (len(box.kids) - 1))


def _place(box: Box, x: float, cy: float, side: int, fs: float):
    """x = edge of the box nearest the parent; cy = centre y of the subtree."""
    box.side = side
    box.x = x if side > 0 else x - box.w
    box.y = cy - box.h / 2
    if not box.kids:
        return
    gap = V_GAP[min(box.depth + 1, 4)] * fs
    total = sum(_subtree_h(k, fs) for k in box.kids) + gap * (len(box.kids) - 1)
    top = cy - total / 2
    child_x = (box.x + box.w if side > 0 else box.x) + side * H_GAP[min(box.depth, 4)] * fs
    for k in box.kids:
        sh = _subtree_h(k, fs)
        _place(k, child_x, top + sh / 2, side, fs)
        top += sh + gap


def layout(root_node: dict, mode: str = "radial", font_scale: float = 1.0) -> tuple[Box, list[Box]]:
    fs = font_scale
    root = _build(root_node, 0)
    _measure(root, fs)
    branches = root.kids
    for i, b in enumerate(branches):
        b.ci = i
    if mode == "right" or len(branches) <= 1:
        groups = [(1, branches)]
    else:
        n_right = (len(branches) + 1) // 2
        groups = [(1, branches[:n_right]), (-1, branches[n_right:])]
    root.x, root.y = -root.w / 2, -root.h / 2
    for side, group in groups:
        gap = V_GAP[1] * fs
        total = sum(_subtree_h(b, fs) for b in group) + gap * (len(group) - 1)
        top = -total / 2
        x = (root.w / 2 if side > 0 else -root.w / 2) + side * H_GAP[0] * fs
        for b in group:
            sh = _subtree_h(b, fs)
            _place(b, x, top + sh / 2, side, fs)
            top += sh + gap
    return root, branches


def _font_css() -> str:
    faces = []
    for weight, name in ((400, "400-normal"), (600, "600-normal"), (700, "700-normal")):
        f = FONT_DIR / f"poppins-latin-{name}.woff2"
        if f.is_file():
            b64 = base64.b64encode(f.read_bytes()).decode()
            faces.append(f"@font-face{{font-family:'Poppins';font-weight:{weight};src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    return "\n".join(faces)


def _e(t):
    return escape(str(t), quote=True)


def _iter(box: Box):
    yield box
    for k in box.kids:
        yield from _iter(k)


def render(root_node: dict, theme: str = "rainbow", title: str = "", layout_mode: str = "radial",
           font_scale: float = 1.0, embed_font: bool = True, padding: int = 40) -> str:
    th = THEMES.get(theme, THEMES["rainbow"])
    root, branches = layout(root_node, layout_mode, font_scale)
    fs = font_scale
    pal = th["palette"]
    for b in branches:
        col = b.node.get("color") if re.fullmatch(r"#?[0-9a-fA-F]{6}", b.node.get("color", "") or "") else None
        col = ("#" + col.lstrip("#")) if col else pal[b.ci % len(pal)]
        for box in _iter(b):
            box.color = col
    boxes = list(_iter(root))
    min_x = min(b.x for b in boxes) - padding
    max_x = max(b.x + b.w for b in boxes) + padding
    min_y = min(b.y for b in boxes) - padding - (34 * fs if title else 0)
    max_y = max(b.y + b.h for b in boxes) + padding
    W, H = max_x - min_x, max_y - min_y

    out = []
    if title:
        out.append(f'<text x="{min_x + padding:.1f}" y="{min_y + padding * 0.5 + 16 * fs:.1f}" font-size="{15 * fs:.1f}" '
                   f'font-weight="600" fill="{th["muted"]}">{_e(title)}</text>')
    # connectors first (under the nodes)
    for b in boxes:
        for k in b.kids:
            if b.depth == 0:
                x0, y0 = (b.x + b.w if k.side > 0 else b.x), b.y + b.h / 2
            else:
                x0, y0 = (b.x + b.w if k.side > 0 else b.x), b.y + b.h - (0 if b.depth >= 2 else b.h / 2)
                if b.depth >= 2:
                    y0 = b.y + b.h - 1
            x1 = k.x if k.side > 0 else k.x + k.w
            y1 = k.y + k.h - 1 if k.depth >= 2 else k.y + k.h / 2
            dx = (x1 - x0) * 0.5
            width = max(1.5, (5 - k.depth) * 0.9) * fs
            out.append(f'<path d="M{x0:.1f},{y0:.1f} C{x0 + dx:.1f},{y0:.1f} {x1 - dx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}" '
                       f'fill="none" stroke="{k.color}" stroke-width="{width:.1f}" stroke-linecap="round"/>')
    # nodes
    for b in boxes:
        lv = LEVEL[min(b.depth, 4)]
        size = lv["size"] * fs
        weight = {"bold": 700, "semibold": 600, "regular": 400}[lv["face"]]
        cx = b.x + b.w / 2
        if b.depth == 0:
            out.append(f'<rect x="{b.x:.1f}" y="{b.y:.1f}" width="{b.w:.1f}" height="{b.h:.1f}" rx="{b.h / 2:.1f}" '
                       f'fill="{th["root"]}" stroke="{th["root"]}"/>')
            color = th["root_text"]
        elif b.depth == 1:
            out.append(f'<rect x="{b.x:.1f}" y="{b.y:.1f}" width="{b.w:.1f}" height="{b.h:.1f}" rx="{10 * fs:.1f}" '
                       f'fill="{b.color}"/>')
            color = "#FFFFFF"
        else:
            # text on a line (classic branch look)
            out.append(f'<line x1="{b.x:.1f}" y1="{b.y + b.h - 1:.1f}" x2="{b.x + b.w:.1f}" y2="{b.y + b.h - 1:.1f}" '
                       f'stroke="{b.color}" stroke-width="{max(1.2, (4.5 - b.depth) * 0.8) * fs:.1f}" stroke-linecap="round"/>')
            color = th["ink"]
        n_lines = len(b.lines)
        pad_top = lv["pad"][1] * fs
        y = b.y + pad_top + size * 0.95
        anchor, tx = ("middle", cx) if b.depth <= 1 else ("start" if b.side > 0 else "end", (b.x + lv["pad"][0] * fs) if b.side > 0 else (b.x + b.w - lv["pad"][0] * fs))
        for i, ln in enumerate(b.lines):
            out.append(f'<text x="{tx:.1f}" y="{y + i * size * 1.25:.1f}" font-size="{size:.1f}" font-weight="{weight}" '
                       f'fill="{color}" text-anchor="{anchor}">{_e(ln)}</text>')
        if b.note_lines:
            ny = y + n_lines * size * 1.25 + 1 * fs
            for i, ln in enumerate(b.note_lines):
                out.append(f'<text x="{tx:.1f}" y="{ny + i * NOTE_SIZE * fs * 1.25:.1f}" font-size="{NOTE_SIZE * fs:.1f}" '
                           f'fill="{th["muted"] if b.depth >= 1 else th["root_text"]}" text-anchor="{anchor}" font-style="italic">{_e(ln)}</text>')

    font_css = _font_css() if embed_font else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="{min_x:.1f} {min_y:.1f} {W:.1f} {H:.1f}" '
            f'font-family="Poppins, Segoe UI, Arial, sans-serif">\n<style>{font_css}\ntext{{font-family:Poppins,"Segoe UI",Arial,sans-serif}}</style>\n'
            f'<rect x="{min_x:.1f}" y="{min_y:.1f}" width="{W:.1f}" height="{H:.1f}" fill="{th["bg"]}"/>\n'
            + "\n".join(out) + "\n</svg>\n")


def stats(root_node: dict) -> dict:
    n, depth = 0, 0

    def walk(node, d):
        nonlocal n, depth
        n += 1
        depth = max(depth, d)
        for k in node.get("children", []):
            walk(k, d + 1)
    walk(root_node, 0)
    return {"nodes": n, "branches": len(root_node.get("children", [])), "depth": depth}
