"""pptx-claude skill — PowerPoint creation via pptxgenjs (Node.js).

Generates visually polished presentations using pptxgenjs as the rendering
engine, with crisp react-icons (SVG→PNG via sharp), card shadows, decorative
ovals, and native pptxgenjs charts.

Supported layouts (20):
    title, bullets, content, two_column, two_column_bullets, table, image,
    image_bullets, stat_callout, section_divider, quote, agenda, timeline,
    icon_grid, features_stats, definition, numbered_list, conclusion_cta,
    challenges, chart.

Icons can be either:
    - react-icons name (e.g. "FaRocket", "MdSecurity") — rendered as crisp PNG
    - emoji or any character (e.g. "🎓") — rendered as text (fallback)
"""

import json
import logging
import os
import re
import subprocess
import tempfile
import uuid
from pathlib import Path

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.agent.minio_connection import upload_file_to_minio

logger = logging.getLogger(__name__)

PROJECT_ROOT  = Path(__file__).parent.parent.parent
DOWNLOADS_DIR = PROJECT_ROOT / "app" / "static" / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
CHARTS_DIR = PROJECT_ROOT / "app" / "static" / "charts"

# Color themes.
#   dark      — slide bg for dark layouts
#   light     — slide bg for non-dark layouts
#   mid       — card bg on dark slides
#   accent    — primary accent color
#   white     — pure white (for text on dark)
#   text      — body text on dark bg
#   text_dark — body text on light bg
#   muted     — secondary / caption text
THEMES: dict[str, dict[str, str]] = {
    "midnight": {
        "dark":      "0A1628",
        "light":     "F0F4F8",
        "mid":       "1A3A6E",
        "accent":    "06B6D4",
        "white":     "FFFFFF",
        "text":      "F0F4F8",
        "text_dark": "0F172A",
        "muted":     "94A3B8",
    },
    "coral": {
        "dark":      "2F3C7E",
        "light":     "FFFFFF",
        "mid":       "F8F8F8",
        "accent":    "F96167",
        "white":     "FFFFFF",
        "text":      "FCF6F5",
        "text_dark": "2F3C7E",
        "muted":     "6B7280",
    },
    "forest": {
        "dark":      "2C5F2D",
        "light":     "F5F5F5",
        "mid":       "E8F5E9",
        "accent":    "97BC62",
        "white":     "FFFFFF",
        "text":      "F5F5F5",
        "text_dark": "1F2937",
        "muted":     "6B7280",
    },
    "ocean": {
        "dark":      "065A82",
        "light":     "F0F7FF",
        "mid":       "1C7293",
        "accent":    "06B6D4",
        "white":     "FFFFFF",
        "text":      "F0F7FF",
        "text_dark": "0F172A",
        "muted":     "6B7280",
    },
    "charcoal": {
        "dark":      "1E293B",
        "light":     "F2F2F2",
        "mid":       "334155",
        "accent":    "02C39A",
        "white":     "FFFFFF",
        "text":      "F2F2F2",
        "text_dark": "212121",
        "muted":     "6B7280",
    },
    "cherry": {
        "dark":      "990011",
        "light":     "FCF6F5",
        "mid":       "B91C1C",
        "accent":    "FCD34D",
        "white":     "FCF6F5",
        "text":      "FCF6F5",
        "text_dark": "2F3C7E",
        "muted":     "6B7280",
    },
}

_DARK_LAYOUTS = {
    "title", "stat_callout", "quote", "section_divider",
    "icon_grid", "features_stats", "definition",
    "conclusion_cta", "numbered_list",
}

# react-icons packages we support
_REACT_ICON_PREFIXES = ("Fa", "Md", "Hi", "Bi", "Ri", "Io")
_PKG_BY_PREFIX = {
    "Fa": "fa", "Md": "md", "Hi": "hi", "Bi": "bi", "Ri": "ri", "Io": "io5",
}

# native chart type mapping (slide-spec name → pptxgenjs constant)
_CHART_TYPES = {
    "bar": "BAR", "line": "LINE", "pie": "PIE",
    "doughnut": "DOUGHNUT", "radar": "RADAR",
    "scatter": "SCATTER", "area": "AREA",
}

# snake_case → camelCase for chart options
_CHART_OPTION_MAP = {
    "bar_dir": "barDir", "show_legend": "showLegend", "legend_pos": "legendPos",
    "show_title": "showTitle", "title_font_size": "titleFontSize",
    "show_value": "showValue", "data_label_position": "dataLabelPosition",
    "data_label_color": "dataLabelColor", "chart_colors": "chartColors",
    "line_size": "lineSize", "line_smooth": "lineSmooth",
    "hole_size": "holeSize", "show_percent": "showPercent",
    "cat_axis_label_color": "catAxisLabelColor",
    "val_axis_label_color": "valAxisLabelColor",
    "legend_font_color": "legendFontColor",
    "legend_font_size": "legendFontSize",
}

# Layouts whose cards/items MUST have icons — Python fills a default if missing
_ICON_MANDATORY_LAYOUTS = {
    "icon_grid": "cards",
    "definition": "cards",
}

# Default fallback icons by header keyword (lowercase substring → react-icon name).
# Order matters: more specific terms first to avoid false matches.
_DEFAULT_ICON_HINTS = (
    # Education / learning
    ("eduk",       "FaGraduationCap"),
    ("educat",     "FaGraduationCap"),
    ("learn",      "FaGraduationCap"),
    ("belajar",    "FaGraduationCap"),
    ("literasi",   "FaBookOpen"),
    ("study",      "FaBookOpen"),
    # Decisions / insights (before "data" so "Keputusan ..." → bulb, not DB)
    ("keputusan",  "FaLightbulb"),
    ("decision",   "FaLightbulb"),
    ("implic",     "FaLightbulb"),
    ("insight",    "FaLightbulb"),
    ("idea",       "FaLightbulb"),
    # Observations / findings / search
    ("observ",     "FaSearch"),
    ("finding",    "FaSearch"),
    ("temuan",     "FaSearch"),
    # Results / outcomes
    ("result",     "FaChartLine"),
    ("hasil",      "FaChartLine"),
    ("outcome",    "FaChartLine"),
    # Pattern / trend (covered "tren" elsewhere; add "pattern")
    ("pattern",    "MdShowChart"),
    ("pola",       "MdShowChart"),
    # Security / privacy
    ("keaman",     "FaShieldAlt"),
    ("secur",      "FaShieldAlt"),
    ("aman",       "FaShieldAlt"),
    ("proteksi",   "FaShieldAlt"),
    ("priva",      "FaUserShield"),
    # Data / database
    ("database",   "FaDatabase"),
    ("data",       "FaDatabase"),
    # Mobile / access
    ("mobile",     "FaMobileAlt"),
    ("akses",      "FaMobileAlt"),
    ("access",     "FaMobileAlt"),
    ("app",        "FaMobileAlt"),
    # Tracking / monitoring / analytics
    ("track",      "FaChartLine"),
    ("monitor",    "FaChartLine"),
    ("analy",      "FaChartLine"),
    ("analisis",   "FaChartLine"),
    ("kinerja",    "FaChartLine"),
    # People / inclusion / community (must come before "keuangan" so "Inklusi Keuangan" → users)
    ("inklusi",    "FaUsers"),
    ("inclusion",  "FaUsers"),
    ("pengguna",   "FaUsers"),
    ("masyarakat", "FaUsers"),
    ("commun",     "FaUsers"),
    ("user",       "FaUsers"),
    # Money / finance
    ("invest",     "FaChartLine"),
    ("money",      "FaMoneyBillWave"),
    ("uang",       "FaMoneyBillWave"),
    ("budget",     "FaWallet"),
    ("anggaran",   "FaWallet"),
    ("tabung",     "FaPiggyBank"),
    ("save",       "FaPiggyBank"),
    ("portofolio", "FaChartPie"),
    ("keuangan",   "FaMoneyBillWave"),
    # Charts / trends
    ("growth",     "MdTrendingUp"),
    ("tren",       "MdTrendingUp"),
    ("chart",      "FaChartBar"),
    # (decisions/insights moved up to take priority over "data")
    ("baik",       "FaLightbulb"),
    # Speed / performance
    ("speed",      "FaBolt"),
    ("fast",       "FaBolt"),
    ("cepat",      "FaBolt"),
    # AI / brain / smart
    ("ai",         "FaBrain"),
    ("smart",      "FaBrain"),
    ("cerdas",     "FaBrain"),
    ("predict",    "FaBrain"),
    ("robot",      "FaRobot"),
    # Automation / process
    ("otomatis",   "FaCog"),
    ("auto",       "FaCog"),
    # Goals / targets / planning
    ("goal",       "FaBullseye"),
    ("tujuan",     "FaBullseye"),
    ("target",     "FaBullseye"),
    ("perencan",   "FaBalanceScale"),
    ("plan",       "FaBalanceScale"),
    # Risk / warning
    ("risiko",     "FaExclamationTriangle"),
    ("risk",       "FaExclamationTriangle"),
    ("warn",       "FaExclamationTriangle"),
    # Misc visual cues
    ("global",     "FaGlobe"),
    ("cloud",      "FaCloud"),
    ("rocket",     "FaRocket"),
    ("launch",     "FaRocket"),
    ("time",       "FaStopwatch"),
    ("waktu",      "FaStopwatch"),
)


def _pick_default_icon(text: str) -> str:
    """Pick a sensible react-icon based on header/body keywords."""
    if not text:
        return "FaCheckCircle"
    low = text.lower()
    for keyword, icon in _DEFAULT_ICON_HINTS:
        if keyword in low:
            return icon
    return "FaCheckCircle"


def _normalize_slides(slides: list) -> list:
    """In-place safety net:

    1. Strip any ``bg_override`` set by the planner — theme bgs are chosen for
       contrast; override produces off-brand colors (purple/pink etc).
    2. Fill missing icons on cards/items in icon-mandatory layouts.
    3. Auto-fill ``two_column`` / ``two_column_bullets`` side icons from
       header (preferred) or body text (fallback).
    4. Log warnings for image layouts with unresolved ``image_url``.
    """
    for s in slides:
        if not isinstance(s, dict):
            continue

        # (1) Strip bg_override
        if "bg_override" in s:
            s.pop("bg_override", None)

        layout = s.get("layout", "")

        # (2) Card/item-based layouts
        field = _ICON_MANDATORY_LAYOUTS.get(layout)
        if field:
            for item in s.get(field, []) or []:
                if isinstance(item, dict) and not item.get("icon"):
                    item["icon"] = _pick_default_icon(str(item.get("header", "")))

        # (3) two_column / two_column_bullets — fill side icons.
        # Prefer header keywords; fall back to first line of body so icons
        # appear even when planner omits headers entirely.
        if layout in ("two_column", "two_column_bullets"):
            lh = str(s.get("left_header", ""))
            rh = str(s.get("right_header", ""))
            l_body_hint = str(s.get("left", "")).split("\n", 1)[0]
            r_body_hint = str(s.get("right", "")).split("\n", 1)[0]
            if not s.get("left_icon"):
                hint = lh or l_body_hint
                if hint:
                    s["left_icon"] = _pick_default_icon(hint)
            if not s.get("right_icon"):
                hint = rh or r_body_hint
                if hint:
                    s["right_icon"] = _pick_default_icon(hint)

        # (4) Warn on broken image refs (renderer handles gracefully)
        if layout in ("image", "image_bullets"):
            raw = s.get("image_url", "")
            if raw and not _resolve_chart_path(raw):
                logger.warning(
                    "[pptx_claude] %s slide %r references unresolved image_url=%r",
                    layout, s.get("title", "")[:60], raw,
                )

    # (5) Empty-slide protection — demote slides that have only a title
    # to a `content` layout with a placeholder so we never ship blank slides.
    for s in slides:
        if not isinstance(s, dict):
            continue
        if _slide_has_content(s):
            continue
        title = s.get("title", "")
        logger.warning(
            "[pptx_claude] slide %r (layout=%s) has no body content — demoting to placeholder content slide",
            title[:60], s.get("layout", "?"),
        )
        s.clear()
        s["layout"] = "content"
        s["title"] = title or "Untitled"
        s["content"] = (
            "Content unavailable for this section. The planner did not "
            "produce body content — please regenerate this slide."
        )
    return slides


def _slide_has_content(s: dict) -> bool:
    """True if a slide has the body content fields required by its layout."""
    layout = s.get("layout", "")

    def _has(field: str) -> bool:
        v = s.get(field)
        if v is None:
            return False
        if isinstance(v, str):
            return bool(v.strip())
        if isinstance(v, (list, tuple, dict)):
            return len(v) > 0
        return bool(v)

    # Layouts that need at least one of these content fields:
    requirements = {
        "title":              ("title", "subtitle", "icon"),
        "bullets":            ("bullets",),
        "content":            ("content",),
        "two_column":         ("left", "right", "left_header", "right_header", "left_icon", "right_icon"),
        "two_column_bullets": ("left_bullets", "right_bullets", "left_header", "right_header"),
        "table":              ("headers", "rows"),
        "image":              ("image_url", "bullets"),
        "image_bullets":      ("image_url", "bullets"),
        "stat_callout":       ("stats",),
        "section_divider":    ("title", "subtitle", "section_number"),
        "quote":              ("quote",),
        "agenda":             ("items",),
        "timeline":           ("steps",),
        "icon_grid":          ("cards",),
        "features_stats":     ("features", "stats"),
        "definition":         ("definition", "cards"),
        "numbered_list":      ("items",),
        "conclusion_cta":     ("title", "points", "cta"),
        "challenges":         ("items",),
        "chart":              ("chart_data",),
    }
    fields = requirements.get(layout, ("title",))
    return any(_has(f) for f in fields)


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

_INLINE_MD_RE = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")


def _strip_inline_md(text: str) -> str:
    """Remove `**bold**` and `__bold__` markdown wrappers, keeping the inner text.

    pptxgenjs renders text verbatim — markdown markers display as literal characters.
    The planner LLM frequently emits these markers for emphasis; this helper neutralizes
    them so the rendered slide is clean. Single-asterisk italic is intentionally left
    alone to avoid eating legitimate asterisks (e.g. "5*4=20", footnote markers).
    """
    if not isinstance(text, str) or not text:
        return text
    return _INLINE_MD_RE.sub(lambda m: m.group(1) or m.group(2) or "", text)


def _esc(value: object) -> str:
    """Escape a value for use inside a JS single-quoted string.

    Also strips inline markdown bold markers (`**...**`, `__...__`) since
    pptxgenjs does not parse markdown.
    """
    s = _strip_inline_md(str(value))
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")


def _bg_is_dark(hex_color: str) -> bool:
    """Perceived brightness < 128 = dark bg (use light text).

    Used to pick contrasting text color regardless of layout class —
    important when `bg_override` is applied.
    """
    h = (hex_color or "").strip().lstrip("#")
    if len(h) != 6:
        return True  # safe default: assume dark
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return True
    return (r * 299 + g * 587 + b * 114) / 1000 < 128


_BULLET_PREFIXES = ("•", "·", "▪", "►", "▶", "★", "◦", "‣", "*", "-", "–", "—")


def _strip_bullet_prefix(text: str) -> str:
    """Remove leading bullet glyphs + whitespace.

    Prevents double bullets when the planner inserts "•" into bullet text
    AND the renderer also applies pptxgenjs ``bullet:true``.
    """
    if not isinstance(text, str):
        return text
    s = text.lstrip()
    while s and s[0] in _BULLET_PREFIXES:
        s = s[1:].lstrip()
    return s


def _node_ok() -> bool:
    try:
        subprocess.run(["node", "--version"], capture_output=True, timeout=5, check=True)
        return True
    except Exception:
        return False


def _pptxgenjs_ok() -> bool:
    """Check pptxgenjs + react-icons + sharp are all available."""
    try:
        r = subprocess.run(
            ["node", "-e",
             "require('pptxgenjs');require('react-icons/fa');require('sharp');"
             "require('react');require('react-dom/server');process.exit(0)"],
            capture_output=True, timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        return r.returncode == 0
    except Exception:
        return False


def _resolve_chart_path(src: str) -> str | None:
    """Resolve a chart_url token or /static/charts/ path to an absolute path."""
    if not src:
        return None
    if src.startswith("chart_url:"):
        src = src[len("chart_url:"):]
    if src.startswith("/static/charts/"):
        src = src[len("/static/charts/"):]
    p = CHARTS_DIR / src
    return str(p) if p.exists() else None


# ---------------------------------------------------------------------------
# Icon system (react-icons → PNG via sharp)
# ---------------------------------------------------------------------------

# Strict react-icon pattern: prefix + capital + at least 2 lowercase chars,
# optionally followed by more PascalCase words. Rejects truncations like
# "Fa", "FaCl", "MdX" that previously slipped through.
_REACT_ICON_RE = re.compile(r"^(Fa|Md|Hi|Bi|Ri|Io)[A-Z][a-z]{2,}([A-Z][a-z0-9]*)*\d*$")


def _is_react_icon(name: str) -> bool:
    """Strict match for a real react-icon name (e.g. 'FaRocket', 'MdSecurity').

    Rejects truncations the planner LLM sometimes emits — 'FaCl', 'Fa',
    'Fa Cl' — that would otherwise render as literal text in the slide.
    """
    return isinstance(name, str) and bool(_REACT_ICON_RE.match(name))


def _is_emoji_like(name: str) -> bool:
    """True for emoji or 1-3 char fallback text (rendered as text, not icon)."""
    if not isinstance(name, str) or not name:
        return False
    # Non-ASCII chars (emoji) or very short string
    return len(name) <= 3 or any(ord(c) > 127 for c in name)


# Substituted when the planner emits a non-emoji, non-valid icon name.
# This icon is always pre-rendered for `conclusion_cta` / `features_stats`,
# so it's safe to reference from any slide.
_ICON_FALLBACK = "FaCheckCircle"


def _norm_color(c: str | None, fallback: str) -> str:
    """Return color without leading '#'."""
    c = (c or fallback).strip().lstrip("#")
    return c if len(c) == 6 else fallback.lstrip("#")


def _icon_key(name: str, color_no_hash: str) -> str:
    return f"{name}__{color_no_hash}"


def _walk_slide_icons(s: dict, accent: str):
    """Yield (name, color_no_hash) for every icon reference in a slide.

    Names that fail strict validation are yielded as the fallback react-icon
    so the prelude pre-renders it; this keeps the ICONS map in sync with
    what ``_emit_icon`` will reference at render time.
    """
    layout = s.get("layout", "")

    def _emit(name: str, color: str):
        resolved = _resolve_icon_name(name)
        if resolved:
            yield (resolved, color)

    if isinstance(s.get("icon"), str):
        yield from _emit(s["icon"], _norm_color(s.get("icon_color"), accent))

    # two_column side icons
    if isinstance(s.get("left_icon"), str):
        yield from _emit(s["left_icon"], _norm_color(s.get("left_color"), accent))
    if isinstance(s.get("right_icon"), str):
        yield from _emit(s["right_icon"], _norm_color(s.get("right_color"), accent))

    for field in ("cards", "features", "items", "benefits"):
        for it in s.get(field, []) or []:
            ic = it.get("icon") if isinstance(it, dict) else None
            if isinstance(ic, str):
                yield from _emit(ic, _norm_color(it.get("color"), accent))

    # bullets with icon (dict-form bullets) — flat + two-column variants
    for field in ("bullets", "left_bullets", "right_bullets"):
        for b in s.get(field, []) or []:
            if isinstance(b, dict):
                ic = b.get("icon")
                if isinstance(ic, str):
                    yield from _emit(ic, _norm_color(b.get("color"), accent))

    # auto-icons used by specific layouts
    if layout == "conclusion_cta":
        yield (_ICON_FALLBACK, accent)
    if layout == "features_stats":
        yield (_ICON_FALLBACK, accent)
    if layout == "challenges":
        for it in s.get("items", []) or []:
            color = _norm_color(it.get("color"), "DC2626")
            yield ("FaExclamationTriangle", color)


def _collect_icons(slides: list, accent: str) -> dict[str, tuple[str, str]]:
    """Return {key: (name, color_no_hash)} for every unique react-icon needed."""
    out: dict[str, tuple[str, str]] = {}
    for s in slides:
        for name, color in _walk_slide_icons(s, accent):
            if _is_react_icon(name):
                key = _icon_key(name, color)
                out.setdefault(key, (name, color))
    return out


def _build_icon_prelude(icon_map: dict[str, tuple[str, str]]) -> tuple[str, str]:
    """Returns (require_lines, render_lines) — JS code blocks for the IIFE."""
    if not icon_map:
        return ("", "  const ICONS = {};")

    by_pkg: dict[str, set[str]] = {}
    for _, (name, _) in icon_map.items():
        pkg = _PKG_BY_PREFIX.get(name[:2], name[:2].lower())
        by_pkg.setdefault(pkg, set()).add(name)

    require_lines = []
    for pkg, names in sorted(by_pkg.items()):
        names_str = ", ".join(sorted(names))
        require_lines.append(f"const {{ {names_str} }} = require('react-icons/{pkg}');")

    render_lines = ["  const ICONS = {};"]
    for key, (name, color) in icon_map.items():
        render_lines.append(
            f"  ICONS['{key}'] = await iconToBase64Png({name}, '#{color}');"
        )

    return ("\n".join(require_lines), "\n".join(render_lines))


def _resolve_icon_name(name: str) -> str:
    """Normalize a user-provided icon name.

    - Valid react-icon → returned unchanged
    - Emoji / very short / non-ASCII → returned unchanged (rendered as text)
    - Anything else (e.g. "FaCl", "Fa", "Bitcoin") → substituted with the
      fallback react-icon and a warning is logged
    """
    if not name:
        return ""
    if _is_react_icon(name) or _is_emoji_like(name):
        return name
    logger.warning(
        "[pptx_claude] icon name %r is not a valid react-icon or emoji — substituting %s",
        name, _ICON_FALLBACK,
    )
    return _ICON_FALLBACK


def _emit_icon(name: str, color_no_hash: str, x: float, y: float, w: float, h: float, fontsize: int = 28) -> str:
    """Emit JS to place an icon at (x,y,w,h). Auto-detects react-icon vs emoji.

    Wraps the JS ``addImage`` call in an ``if (ICONS[key])`` guard so that
    when the icon failed to pre-render (returned null in the prelude), the
    slide simply omits the icon instead of crashing pptxgenjs.
    """
    name = _resolve_icon_name(name)
    if not name:
        return ""

    if _is_react_icon(name):
        key = _icon_key(name, color_no_hash)
        return (
            f"    if (ICONS['{key}']) {{ "
            f"sl.addImage({{data: ICONS['{key}'], "
            f"x:{x:.3f}, y:{y:.3f}, w:{w:.3f}, h:{h:.3f}}}); }}"
        )
    # emoji / arbitrary short text fallback
    return (
        f"    sl.addText('{_esc(name)}', "
        f"{{x:{x:.3f},y:{y:.3f},w:{w:.3f},h:{h:.3f},"
        f"fontSize:{fontsize},align:'center',valign:'middle',"
        f"color:'{color_no_hash}',fontFace:'Calibri',margin:0}});"
    )


# ---------------------------------------------------------------------------
# Per-layout JS generators
# ---------------------------------------------------------------------------

def _slide_title(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    sub = _esc(s.get("subtitle", ""))
    icon_name = s.get("icon")
    icon_color = _norm_color(s.get("icon_color"), t["accent"])
    lines = [
        # Decorative ovals
        f"    sl.addShape(pres.shapes.OVAL, {{x:-1.5,y:-1.5,w:5,h:5,fill:{{color:'{t['mid']}',transparency:70}},line:{{type:'none'}}}});",
        f"    sl.addShape(pres.shapes.OVAL, {{x:7.5,y:2.5,w:4,h:4,fill:{{color:'{t['accent']}',transparency:75}},line:{{type:'none'}}}});",
        f"    sl.addShape(pres.shapes.OVAL, {{x:8.5,y:-0.5,w:2.5,h:2.5,fill:{{color:'{t['accent']}',transparency:80}},line:{{type:'none'}}}});",
        # Accent bar
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.5,y:1.4,w:0.08,h:2.6,fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});",
        # Title with charSpacing
        f"    sl.addText('{title}', {{x:0.75,y:1.4,w:8.5,h:0.95,fontSize:38,bold:true,color:'{t['white']}',fontFace:'Calibri',align:'left',charSpacing:2,margin:0}});",
    ]
    if sub:
        lines.append(
            f"    sl.addText('{sub}', {{x:0.75,y:2.35,w:8.0,h:0.7,fontSize:22,color:'{t['accent']}',fontFace:'Calibri',align:'left',margin:0}});"
        )
    # Optional icon
    if icon_name:
        lines.append(_emit_icon(icon_name, icon_color, 7.7, 0.9, 1.6, 1.6, fontsize=72))
    return lines


def _slide_section_divider(s: dict, t: dict) -> list[str]:
    num = _esc(s.get("section_number", ""))
    title = _esc(s.get("title", ""))
    sub = _esc(s.get("subtitle", ""))
    lines = [
        f"    sl.addShape(pres.shapes.OVAL, {{x:8,y:-1,w:4,h:4,fill:{{color:'{t['accent']}',transparency:75}},line:{{type:'none'}}}});",
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:0.08,h:5.625,fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});",
    ]
    if num:
        lines.append(
            f"    sl.addText('{num}', {{x:0.6,y:0.6,w:2.0,h:1.6,fontSize:80,bold:true,color:'{t['accent']}',fontFace:'Calibri',margin:0}});"
        )
    lines.append(
        f"    sl.addText('{title}', {{x:0.6,y:2.4,w:8.8,h:1.2,fontSize:32,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});"
    )
    if sub:
        lines.append(
            f"    sl.addText('{sub}', {{x:0.6,y:3.7,w:8.8,h:0.8,fontSize:18,color:'{t['accent']}',fontFace:'Calibri',margin:0}});"
        )
    return lines


def _slide_bullets(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    bullets = s.get("bullets", []) or []
    lines = [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['dark']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:24,bold:true,color:'{t['white']}',fontFace:'Calibri',align:'left',margin:0}});",
    ]
    if not bullets:
        return lines

    # Decide rendering mode: all strings → classic bullets; any dict → icon rows
    has_dict = any(isinstance(b, dict) for b in bullets)

    if not has_dict:
        items = (
            "[" +
            ", ".join(
                f"{{text:'{_esc(_strip_bullet_prefix(str(b)))}',options:{{bullet:true,breakLine:{'false' if i == len(bullets)-1 else 'true'},paraSpaceAfter:6}}}}"
                for i, b in enumerate(bullets)
            ) +
            "]"
        )
        lines.append(
            f"    sl.addText({items}, {{x:0.6,y:1.3,w:8.8,h:4.1,fontSize:16,color:'{t['text']}',fontFace:'Calibri'}});"
        )
        return lines

    # Icon-row mode
    body_top, body_h = 1.3, 4.1
    n = len(bullets)
    row_h = body_h / n
    icon_size = min(0.42, row_h * 0.7)
    for i, b in enumerate(bullets):
        if isinstance(b, dict):
            text = _esc(_strip_bullet_prefix(str(b.get("text", ""))))
            icon = b.get("icon", "")
            icon_color = _norm_color(b.get("color"), t["accent"])
        else:
            text = _esc(_strip_bullet_prefix(str(b)))
            icon = ""
            icon_color = t["accent"]
        ry = body_top + i * row_h
        if icon:
            iy = ry + (row_h - icon_size) / 2
            lines.append(_emit_icon(icon, icon_color, 0.6, iy, icon_size, icon_size, fontsize=20))
            text_x = 1.2
        else:
            # Use a small dot when no icon
            dot_d = 0.12
            dy = ry + (row_h - dot_d) / 2
            lines.append(
                f"    sl.addShape(pres.shapes.OVAL, {{x:0.75,y:{dy:.3f},w:{dot_d},h:{dot_d},fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});"
            )
            text_x = 1.2
        if text:
            lines.append(
                f"    sl.addText('{text}', {{x:{text_x},y:{ry:.3f},w:{9.8 - text_x:.2f},h:{row_h:.3f},fontSize:15,color:'{t['text']}',valign:'middle',fontFace:'Calibri',margin:0}});"
            )
    return lines


def _slide_content(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    content = _esc(s.get("content", ""))
    icon = s.get("icon", "")
    icon_color = _norm_color(s.get("icon_color"), t["accent"])
    lines = [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['dark']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:24,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:1.3,w:9.2,h:4.1,fill:{{color:'{t['white']}'}},line:{{type:'none'}},shadow:mkShadow(0.10)}});",
    ]
    if icon:
        # Split layout: content left ~6.0, icon decoration right
        lines.append(
            f"    sl.addText('{content}', {{x:0.6,y:1.55,w:5.8,h:3.6,fontSize:15,color:'{t['text_dark']}',valign:'middle',fontFace:'Calibri'}});"
        )
        icon_size = 2.0
        icon_x = 6.7 + (2.7 - icon_size) / 2
        icon_y = 1.3 + (4.1 - icon_size) / 2
        lines.append(_emit_icon(icon, icon_color, icon_x, icon_y, icon_size, icon_size, fontsize=110))
    else:
        lines.append(
            f"    sl.addText('{content}', {{x:0.6,y:1.45,w:8.8,h:3.8,fontSize:15,color:'{t['text_dark']}',fontFace:'Calibri'}});"
        )
    return lines


def _slide_two_column(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    left_body = _esc(s.get("left", ""))
    right_body = _esc(s.get("right", ""))
    left_icon = s.get("left_icon", "")
    right_icon = s.get("right_icon", "")
    left_header = _esc(s.get("left_header", ""))
    right_header = _esc(s.get("right_header", ""))
    left_color = _norm_color(s.get("left_color"), t["accent"])
    right_color = _norm_color(s.get("right_color"), t["accent"])

    lines = [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['dark']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:24,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
    ]

    for side, x_card, body, icon, header, accent in (
        ("left",  0.4, left_body,  left_icon,  left_header,  left_color),
        ("right", 5.2, right_body, right_icon, right_header, right_color),
    ):
        # Card + top accent bar
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:{x_card},y:1.3,w:4.4,h:4.0,fill:{{color:'{t['white']}'}},line:{{type:'none'}},shadow:mkShadow(0.10)}});"
        )
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:{x_card},y:1.3,w:4.4,h:0.07,fill:{{color:'{accent}'}},line:{{type:'none'}}}});"
        )

        # Compute content layout based on which optional fields are set
        cur_y = 1.55
        if icon:
            icon_size = 0.95
            icon_x = x_card + (4.4 - icon_size) / 2
            lines.append(_emit_icon(icon, accent, icon_x, cur_y, icon_size, icon_size, fontsize=56))
            cur_y = 1.55 + icon_size + 0.15  # 2.65
        if header:
            lines.append(
                f"    sl.addText('{header}', {{x:{x_card + 0.2:.2f},y:{cur_y:.2f},w:4.0,h:0.55,fontSize:18,bold:true,color:'{accent}',align:'center',fontFace:'Calibri',margin:0}});"
            )
            cur_y += 0.6
        if body:
            body_h = 5.3 - cur_y  # card bottom is 1.3+4.0=5.3
            # Use top valign only when BOTH icon and header are set (so the body
            # sits naturally below the header). Otherwise vertically center the
            # body so it fills the card instead of crowding the top.
            valign = "top" if (icon and header) else "middle"
            lines.append(
                f"    sl.addText('{body}', {{x:{x_card + 0.25:.2f},y:{cur_y:.2f},w:3.9,h:{body_h:.2f},fontSize:14,color:'{t['text_dark']}',align:'left',valign:'{valign}',fontFace:'Calibri',paraSpaceAfter:4}});"
            )
    return lines


def _slide_two_column_bullets(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    left_header = _esc(s.get("left_header", ""))
    right_header = _esc(s.get("right_header", ""))
    left_bullets = s.get("left_bullets", []) or []
    right_bullets = s.get("right_bullets", []) or []
    left_icon = s.get("left_icon", "")
    right_icon = s.get("right_icon", "")
    left_color = _norm_color(s.get("left_color"), t["accent"])
    right_color = _norm_color(s.get("right_color"), t["accent"])

    lines = [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['dark']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:24,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
    ]

    for x_card, header, icon, bullets, accent in (
        (0.4, left_header,  left_icon,  left_bullets,  left_color),
        (5.2, right_header, right_icon, right_bullets, right_color),
    ):
        # Card + top accent bar
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:{x_card},y:1.3,w:4.4,h:4.0,fill:{{color:'{t['white']}'}},line:{{type:'none'}},shadow:mkShadow(0.10)}});"
        )
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:{x_card},y:1.3,w:4.4,h:0.07,fill:{{color:'{accent}'}},line:{{type:'none'}}}});"
        )

        cur_y = 1.55
        if icon:
            icon_size = 0.55
            icon_x = x_card + (4.4 - icon_size) / 2
            lines.append(_emit_icon(icon, accent, icon_x, cur_y, icon_size, icon_size, fontsize=36))
            cur_y = 2.20
        if header:
            lines.append(
                f"    sl.addText('{header}', {{x:{x_card + 0.2:.2f},y:{cur_y:.2f},w:4.0,h:0.45,fontSize:16,bold:true,color:'{accent}',align:'center',fontFace:'Calibri',margin:0}});"
            )
            cur_y += 0.55
        if bullets:
            bullet_h = 5.3 - cur_y - 0.1
            has_dict = any(isinstance(b, dict) for b in bullets)

            if not has_dict:
                # Classic bullets
                items = "[" + ", ".join(
                    f"{{text:'{_esc(_strip_bullet_prefix(str(b)))}',options:{{bullet:true,breakLine:{'false' if i==len(bullets)-1 else 'true'},paraSpaceAfter:4}}}}"
                    for i, b in enumerate(bullets)
                ) + "]"
                lines.append(
                    f"    sl.addText({items}, {{x:{x_card + 0.2:.2f},y:{cur_y:.2f},w:4.0,h:{bullet_h:.2f},fontSize:13,color:'{t['text_dark']}',fontFace:'Calibri'}});"
                )
            else:
                # Icon-row mode — each bullet renders as icon + text on its own row
                n_b = max(1, len(bullets))
                row_h = bullet_h / n_b
                icon_size = min(0.32, row_h * 0.65)
                for i, b in enumerate(bullets):
                    if isinstance(b, dict):
                        text = _strip_bullet_prefix(str(b.get("text", "")))
                        row_icon = b.get("icon", "")
                        row_color = _norm_color(b.get("color"), accent)
                    else:
                        text = _strip_bullet_prefix(str(b))
                        row_icon = ""
                        row_color = accent
                    ry = cur_y + i * row_h
                    if row_icon:
                        iy = ry + (row_h - icon_size) / 2
                        lines.append(_emit_icon(row_icon, row_color, x_card + 0.25, iy, icon_size, icon_size, fontsize=16))
                        text_x = x_card + 0.65
                    else:
                        dot = 0.10
                        dy = ry + (row_h - dot) / 2
                        lines.append(
                            f"    sl.addShape(pres.shapes.OVAL, {{x:{x_card + 0.32:.2f},y:{dy:.3f},w:{dot},h:{dot},fill:{{color:'{accent}'}},line:{{type:'none'}}}});"
                        )
                        text_x = x_card + 0.55
                    if text:
                        text_w = (x_card + 4.2) - text_x
                        lines.append(
                            f"    sl.addText('{_esc(text)}', {{x:{text_x:.2f},y:{ry:.3f},w:{text_w:.2f},h:{row_h:.3f},fontSize:12,color:'{t['text_dark']}',valign:'middle',fontFace:'Calibri',margin:0}});"
                        )
    return lines


def _stat_value_fontsize(value: str) -> int:
    """Pick a font size that fits a stat value into one column without wrapping.

    A 4-stat callout has ~2.05" columns. At 54pt one digit takes ~0.45",
    so a 4-char value barely fits. Step down by length.
    """
    n = len(value or "")
    if n <= 4:  return 54
    if n <= 6:  return 44
    if n <= 8:  return 34
    if n <= 10: return 26
    return 20


def _slide_stat_callout(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    stats = s.get("stats", [])[:4]
    lines = [
        f"    sl.addShape(pres.shapes.OVAL, {{x:8,y:-1,w:4,h:4,fill:{{color:'{t['accent']}',transparency:80}},line:{{type:'none'}}}});",
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:0.07,fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.6,y:0.3,w:8.8,h:0.7,fontSize:22,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
    ]
    n = len(stats) or 1
    col_w = 9.0 / n
    for i, stat in enumerate(stats):
        x = 0.5 + i * col_w
        raw_val = stat.get("value", "")
        val = _esc(raw_val)
        lbl = _esc(stat.get("label", ""))
        fs = _stat_value_fontsize(str(raw_val))
        lines += [
            f"    sl.addText('{val}', {{x:{x:.2f},y:1.9,w:{col_w-0.2:.2f},h:1.8,fontSize:{fs},bold:true,color:'{t['accent']}',align:'center',valign:'middle',fontFace:'Calibri',charSpacing:2,margin:0}});",
            f"    sl.addText('{lbl}', {{x:{x:.2f},y:3.85,w:{col_w-0.2:.2f},h:0.7,fontSize:14,color:'{t['white']}',align:'center',valign:'middle',fontFace:'Calibri',margin:0}});",
            # Thin accent underline anchors the bottom space
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:{x + 0.3:.2f},y:4.85,w:{col_w-0.8:.2f},h:0.04,fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});",
        ]
        # Vertical divider between stats
        if i < len(stats) - 1:
            dx = 0.5 + (i + 1) * col_w - 0.05
            lines.append(
                f"    sl.addShape(pres.shapes.RECTANGLE, {{x:{dx:.2f},y:2.0,w:0.02,h:2.6,fill:{{color:'{t['accent']}',transparency:50}},line:{{type:'none'}}}});"
            )
    return lines


def _slide_quote(s: dict, t: dict) -> list[str]:
    quote = _esc(s.get("quote", ""))
    attr = _esc(s.get("attribution", ""))
    ctx = _esc(s.get("context", ""))
    lines = [
        # decorative oval
        f"    sl.addShape(pres.shapes.OVAL, {{x:-1.5,y:-1.5,w:4,h:4,fill:{{color:'{t['accent']}',transparency:80}},line:{{type:'none'}}}});",
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:0.08,h:5.625,fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});",
        # huge quotation mark
        f"    sl.addText('“', {{x:0.5,y:0.4,w:1.5,h:1.4,fontSize:120,bold:true,color:'{t['accent']}',fontFace:'Georgia',margin:0}});",
        f"    sl.addText('{quote}', {{x:1.4,y:1.4,w:7.6,h:2.4,fontSize:24,italic:true,color:'{t['white']}',align:'left',fontFace:'Georgia',margin:0}});",
        f"    sl.addText('{attr}', {{x:1.4,y:4.0,w:7.6,h:0.5,fontSize:14,bold:true,color:'{t['accent']}',align:'left',fontFace:'Calibri',margin:0}});",
    ]
    if ctx:
        lines.append(
            f"    sl.addText('{ctx}', {{x:1.4,y:4.5,w:7.6,h:0.4,fontSize:12,color:'{t['muted']}',align:'left',fontFace:'Calibri',margin:0}});"
        )
    return lines


def _slide_image(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    raw_url = s.get("image_url", "")
    img_path = _resolve_chart_path(raw_url)
    caption = _esc(s.get("caption", ""))
    insights = [b for b in (s.get("bullets") or []) if b]

    if raw_url and not img_path:
        logger.warning(
            "[pptx_claude] image: image_url %r did not resolve — falling back",
            raw_url,
        )

    # If no image but we have bullets, render as a bullets-only card (no blank image box)
    if not img_path and insights:
        lines = [
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['dark']}'}},line:{{type:'none'}}}});",
            f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:24,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:1.3,w:9.2,h:4.2,fill:{{color:'{t['white']}'}},line:{{type:'none'}},shadow:mkShadow(0.12)}});",
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:1.3,w:9.2,h:0.07,fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});",
        ]
        items = (
            "[" +
            ",".join(
                f"{{text:'{_esc(_strip_bullet_prefix(str(b)))}',options:{{bullet:true,breakLine:{'false' if i == len(insights)-1 else 'true'},paraSpaceAfter:6}}}}"
                for i, b in enumerate(insights)
            ) +
            "]"
        )
        lines.append(
            f"    sl.addText({items}, {{x:0.6,y:1.5,w:8.8,h:3.9,fontSize:15,color:'{t['text_dark']}',fontFace:'Calibri'}});"
        )
        return lines

    lines = [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['dark']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:24,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
    ]

    if insights:
        # Enhanced mode: image top ~60%, insights row below
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:1.3,w:9.2,h:3.0,fill:{{color:'{t['white']}'}},line:{{type:'none'}},shadow:mkShadow(0.10)}});"
        )
        if img_path:
            img_esc = img_path.replace("\\", "\\\\")
            lines.append(f"    sl.addImage({{path:'{img_esc}',x:0.55,y:1.42,w:8.9,h:2.75}});")
        else:
            lines.append(
                f"    sl.addText('[image not found]', {{x:0.4,y:2.5,w:9.2,h:0.6,fontSize:14,color:'{t['muted']}',align:'center',fontFace:'Calibri'}});"
            )
        # Insights band at y=4.4, h=1.05 (bottom edge 5.45)
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:4.4,w:9.2,h:1.05,fill:{{color:'{t['white']}'}},line:{{type:'none'}},shadow:mkShadow(0.10)}});"
        )
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:4.4,w:9.2,h:0.06,fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});"
        )
        # Insights as one-line items in a row (max 3) — or stacked if 4-5
        n = min(len(insights), 5)
        items = insights[:n]
        if n <= 3:
            # Row layout
            col_w = 9.0 / n
            for i, ins in enumerate(items):
                text = _esc(_strip_bullet_prefix(str(ins)))
                x = 0.5 + i * col_w
                lines.append(_emit_icon("FaCheckCircle", t["accent"], x + 0.05, 4.65, 0.3, 0.3))
                lines.append(
                    f"    sl.addText('{text}', {{x:{x + 0.4:.2f},y:4.55,w:{col_w - 0.5:.2f},h:0.75,fontSize:12,color:'{t['text_dark']}',valign:'middle',fontFace:'Calibri',margin:0}});"
                )
        else:
            # Stacked bullets
            bullet_items = "[" + ", ".join(
                f"{{text:'{_esc(_strip_bullet_prefix(str(ins)))}',options:{{bullet:true,breakLine:{'false' if i==n-1 else 'true'}}}}}"
                for i, ins in enumerate(items)
            ) + "]"
            lines.append(
                f"    sl.addText({bullet_items}, {{x:0.6,y:4.5,w:8.8,h:0.9,fontSize:11,color:'{t['text_dark']}',fontFace:'Calibri'}});"
            )
        if caption:
            lines.append(
                f"    sl.addText('{caption}', {{x:0.4,y:5.5,w:9.2,h:0.12,fontSize:9,color:'{t['muted']}',align:'center',italic:true,fontFace:'Calibri',margin:0}});"
            )
    else:
        # Default mode: large chart card only
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:1.3,w:9.2,h:4.0,fill:{{color:'{t['white']}'}},line:{{type:'none'}},shadow:mkShadow(0.12)}});"
        )
        if img_path:
            img_esc = img_path.replace("\\", "\\\\")
            lines.append(f"    sl.addImage({{path:'{img_esc}',x:0.55,y:1.45,w:8.9,h:3.7}});")
        else:
            lines.append(
                f"    sl.addText('[image not found]', {{x:0.4,y:3.0,w:9.2,h:1.0,fontSize:14,color:'{t['muted']}',align:'center',fontFace:'Calibri'}});"
            )
        if caption:
            lines.append(
                f"    sl.addText('{caption}', {{x:0.4,y:5.4,w:9.2,h:0.2,fontSize:12,color:'{t['muted']}',align:'center',italic:true,fontFace:'Calibri',margin:0}});"
            )
    return lines


def _slide_image_bullets(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    raw_url = s.get("image_url", "")
    img_path = _resolve_chart_path(raw_url)
    bullets = s.get("bullets", []) or []

    if raw_url and not img_path:
        logger.warning(
            "[pptx_claude] image_bullets: image_url %r did not resolve — expanding bullets to full width",
            raw_url,
        )

    lines = [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['dark']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:24,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
    ]

    has_dict = any(isinstance(b, dict) for b in bullets)
    accent = t["accent"]

    if img_path:
        # Standard split layout: image left, bullets right
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:1.3,w:5.0,h:4.2,fill:{{color:'{t['white']}'}},line:{{type:'none'}},shadow:mkShadow(0.12)}});"
        )
        img_esc = img_path.replace("\\", "\\\\")
        lines.append(f"    sl.addImage({{path:'{img_esc}',x:0.55,y:1.45,w:4.7,h:3.9}});")
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:5.65,y:1.3,w:0.06,h:4.2,fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});"
        )
        if bullets:
            # Right-side bullets region: x=5.85, y=1.3, w=3.7, h=4.2
            lines += _render_bullet_region(bullets, has_dict, t, accent,
                                          region_x=5.85, region_y=1.3,
                                          region_w=3.7, region_h=4.2,
                                          fontsize=14)
    else:
        # No image — full-width bullet card
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:1.3,w:9.2,h:4.2,fill:{{color:'{t['white']}'}},line:{{type:'none'}},shadow:mkShadow(0.12)}});"
        )
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:1.3,w:9.2,h:0.07,fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});"
        )
        if bullets:
            lines += _render_bullet_region(bullets, has_dict, t, accent,
                                          region_x=0.6, region_y=1.5,
                                          region_w=8.8, region_h=3.9,
                                          fontsize=15)
    return lines


def _render_bullet_region(
    bullets: list, has_dict: bool, t: dict, accent: str,
    region_x: float, region_y: float, region_w: float, region_h: float,
    fontsize: int = 14,
) -> list[str]:
    """Emit JS for a bullets list (classic OR icon-row when any item is dict)."""
    lines: list[str] = []

    if not has_dict:
        items = (
            "[" +
            ",".join(
                f"{{text:'{_esc(_strip_bullet_prefix(str(b)))}',options:{{bullet:true,breakLine:{'false' if i == len(bullets)-1 else 'true'},paraSpaceAfter:6}}}}"
                for i, b in enumerate(bullets)
            ) +
            "]"
        )
        lines.append(
            f"    sl.addText({items}, {{x:{region_x},y:{region_y},w:{region_w},h:{region_h},fontSize:{fontsize},color:'{t['text_dark']}',fontFace:'Calibri'}});"
        )
        return lines

    # Icon-row mode
    n_b = max(1, len(bullets))
    row_h = region_h / n_b
    icon_size = min(0.36, row_h * 0.65)
    for i, b in enumerate(bullets):
        if isinstance(b, dict):
            text = _strip_bullet_prefix(str(b.get("text", "")))
            row_icon = b.get("icon", "")
            row_color = _norm_color(b.get("color"), accent)
        else:
            text = _strip_bullet_prefix(str(b))
            row_icon = ""
            row_color = accent
        ry = region_y + i * row_h
        if row_icon:
            iy = ry + (row_h - icon_size) / 2
            lines.append(_emit_icon(row_icon, row_color, region_x, iy, icon_size, icon_size, fontsize=16))
            text_x = region_x + icon_size + 0.12
        else:
            dot = 0.10
            dy = ry + (row_h - dot) / 2
            lines.append(
                f"    sl.addShape(pres.shapes.OVAL, {{x:{region_x + 0.07:.2f},y:{dy:.3f},w:{dot},h:{dot},fill:{{color:'{accent}'}},line:{{type:'none'}}}});"
            )
            text_x = region_x + 0.27
        if text:
            text_w = (region_x + region_w) - text_x
            lines.append(
                f"    sl.addText('{_esc(text)}', {{x:{text_x:.2f},y:{ry:.3f},w:{text_w:.2f},h:{row_h:.3f},fontSize:{fontsize - 1},color:'{t['text_dark']}',valign:'middle',fontFace:'Calibri',margin:0}});"
            )
    return lines


def _slide_table(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    headers = s.get("headers", [])
    rows = s.get("rows", [])
    if not headers:
        return _slide_fallback(s, t)
    n_cols = len(headers)
    col_w = round(9.2 / n_cols, 2)
    col_w_arr = ",".join(str(col_w) for _ in headers)
    header_cells = ",".join(
        f"{{text:'{_esc(h)}',options:{{bold:true,color:'{t['white']}',fill:{{color:'{t['dark']}'}},align:'center',valign:'middle'}}}}"
        for h in headers
    )
    all_rows_js = [f"[{header_cells}]"]
    for r_idx, row in enumerate(rows):
        row_fill = "FFFFFF" if r_idx % 2 == 0 else "F8FAFC"
        cells = ",".join(
            f"{{text:'{_esc(str(v) if v is not None else '')}',options:{{color:'{t['text_dark']}',fill:{{color:'{row_fill}'}},valign:'middle'}}}}"
            for v in row[:n_cols]
        )
        all_rows_js.append(f"[{cells}]")
    return [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['dark']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:24,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
        f"    sl.addTable([{','.join(all_rows_js)}], {{x:0.4,y:1.3,w:9.2,colW:[{col_w_arr}],border:{{pt:0.5,color:'CBD5E1'}},fontSize:13,fontFace:'Calibri',rowH:0.45}});",
    ]


def _slide_timeline(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    steps = s.get("steps", [])[:5]
    n = len(steps)
    lines = [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['dark']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:24,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
    ]
    if not steps:
        return lines
    # Layout: title bar 0–1.05; label 1.20; phase 1.70; line 2.75; card 3.15 (h=2.30); end 5.45
    line_y, line_left, line_right = 2.75, 0.7, 9.3
    line_w = line_right - line_left
    lines.append(
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:{line_left},y:{line_y - 0.03:.2f},w:{line_w},h:0.06,fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});"
    )
    positions = (
        [line_left + i * (line_w / (n - 1)) for i in range(n)] if n > 1
        else [line_left + line_w / 2]
    )
    circle_r = 0.28
    for i, (step, cx) in enumerate(zip(steps, positions)):
        phase = _esc(step.get("phase", ""))
        label = _esc(step.get("label", ""))
        desc = _esc(step.get("description", ""))
        lx = cx - 0.85
        if label:
            lines.append(
                f"    sl.addText('{label}', {{x:{lx:.2f},y:1.20,w:1.7,h:0.45,fontSize:13,bold:true,color:'{t['text_dark']}',align:'center',fontFace:'Calibri',margin:0}});"
            )
        if phase:
            lines.append(
                f"    sl.addText('{phase}', {{x:{lx:.2f},y:1.70,w:1.7,h:0.4,fontSize:11,color:'{t['muted']}',align:'center',fontFace:'Calibri',margin:0}});"
            )
        lines.append(
            f"    sl.addShape(pres.shapes.OVAL, {{x:{cx - circle_r:.2f},y:{line_y - circle_r:.2f},w:{circle_r * 2},h:{circle_r * 2},fill:{{color:'{t['dark']}'}},line:{{type:'none'}}}});"
        )
        lines.append(
            f"    sl.addText('{i + 1}', {{x:{cx - circle_r:.2f},y:{line_y - circle_r:.2f},w:{circle_r * 2},h:{circle_r * 2},fontSize:12,bold:true,color:'{t['white']}',align:'center',valign:'middle',fontFace:'Calibri',margin:0}});"
        )
        if desc:
            card_x, card_y, card_h = cx - 0.85, 3.15, 2.30
            lines.append(
                f"    sl.addShape(pres.shapes.RECTANGLE, {{x:{card_x:.2f},y:{card_y},w:1.7,h:{card_h},fill:{{color:'{t['white']}'}},line:{{type:'none'}},shadow:mkShadow(0.10)}});"
            )
            lines.append(
                f"    sl.addShape(pres.shapes.RECTANGLE, {{x:{card_x:.2f},y:{card_y},w:1.7,h:0.06,fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});"
            )
            lines.append(
                f"    sl.addText('{desc}', {{x:{card_x + 0.1:.2f},y:{card_y + 0.15},w:1.5,h:{card_h - 0.25:.2f},fontSize:10.5,color:'{t['text_dark']}',align:'center',valign:'middle',fontFace:'Calibri'}});"
            )
    return lines


def _slide_agenda(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", "Agenda"))
    items = s.get("items", [])
    highlight = s.get("highlight", -1)
    lines = [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['dark']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:24,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
    ]
    if not items:
        return lines
    body_top, body_h = 1.3, 5.8
    item_h = body_h / len(items)
    circle_d = min(0.38, item_h * 0.7)
    for i, item in enumerate(items):
        row_top = body_top + i * item_h
        row_mid_y = row_top + item_h / 2
        is_hi = (i == highlight)
        num = _esc(str(item.get("number", str(i + 1).zfill(2))))
        label = _esc(str(item.get("label", "")))
        duration = _esc(str(item.get("duration", "")))
        circ_color = t["accent"] if is_hi else t["dark"]
        num_color = t["dark"] if is_hi else t["white"]
        label_color = t["white"] if is_hi else t["text_dark"]
        if is_hi:
            lines.append(
                f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.35,y:{row_top + 0.04:.2f},w:9.3,h:{item_h - 0.08:.2f},fill:{{color:'{t['dark']}'}},line:{{type:'none'}},shadow:mkShadow(0.12)}});"
            )
        lines.append(
            f"    sl.addShape(pres.shapes.OVAL, {{x:0.5,y:{row_mid_y - circle_d / 2:.2f},w:{circle_d},h:{circle_d},fill:{{color:'{circ_color}'}},line:{{type:'none'}}}});"
        )
        lines.append(
            f"    sl.addText('{num}', {{x:0.5,y:{row_mid_y - circle_d / 2:.2f},w:{circle_d},h:{circle_d},fontSize:13,bold:true,color:'{num_color}',align:'center',valign:'middle',fontFace:'Calibri',margin:0}});"
        )
        lines.append(
            f"    sl.addText('{label}', {{x:1.1,y:{row_mid_y - 0.22:.2f},w:7.2,h:0.45,fontSize:18,bold:{str(is_hi).lower()},color:'{label_color}',fontFace:'Calibri',margin:0}});"
        )
        if duration:
            lines.append(
                f"    sl.addText('{duration}', {{x:8.3,y:{row_mid_y - 0.2:.2f},w:1.35,h:0.42,fontSize:14,color:'{label_color}',align:'right',fontFace:'Calibri',margin:0}});"
            )
    return lines


def _slide_icon_grid(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    cards = s.get("cards", [])[:6]
    n = len(cards)
    lines = [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:0.07,fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.4,y:0.15,w:9.2,h:0.8,fontSize:22,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
    ]
    if not cards:
        return lines
    if n <= 2:
        cols, rows_count = n, 1
    elif n == 3:
        cols, rows_count = 3, 1
    elif n == 4:
        cols, rows_count = 2, 2
    else:
        cols, rows_count = 3, 2
    gap = 0.22
    content_top = 1.15
    avail_h = 5.625 - content_top - 0.2
    card_w = round((9.2 - gap * (cols - 1)) / cols, 3)
    card_h = round((avail_h - gap * (rows_count - 1)) / rows_count, 3)
    for i, card_data in enumerate(cards):
        col, row = i % cols, i // cols
        cx = round(0.4 + col * (card_w + gap), 3)
        cy = round(content_top + row * (card_h + gap), 3)
        icon = card_data.get("icon", "")
        icon_color = _norm_color(card_data.get("color"), t["accent"])
        header = _esc(str(card_data.get("header", "")))
        body = _esc(str(card_data.get("body", "")))
        # Card bg + accent border + shadow
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:{cx},y:{cy},w:{card_w},h:{card_h},fill:{{color:'{t['mid']}',transparency:25}},line:{{color:'{icon_color}',width:1}},shadow:mkShadow(0.20)}});"
        )
        # Icon centered horizontally near top
        icon_size = 0.7
        icon_x = round(cx + (card_w - icon_size) / 2, 3)
        icon_y = round(cy + 0.2, 3)
        if icon:
            lines.append(_emit_icon(icon, icon_color, icon_x, icon_y, icon_size, icon_size, fontsize=32))
        # Header
        hdr_y = round(cy + icon_size + 0.3, 3)
        if header:
            lines.append(
                f"    sl.addText('{header}', {{x:{cx + 0.1:.2f},y:{hdr_y},w:{card_w - 0.2:.2f},h:0.45,fontSize:13.5,bold:true,color:'{icon_color}',align:'center',fontFace:'Calibri',margin:0}});"
            )
        # Body
        body_y = round(cy + icon_size + 0.8, 3)
        body_h = round(card_h - (icon_size + 0.95), 3)
        if body and body_h > 0.2:
            lines.append(
                f"    sl.addText('{body}', {{x:{cx + 0.15:.2f},y:{body_y},w:{card_w - 0.3:.2f},h:{body_h},fontSize:11,color:'{t['text']}',align:'center',fontFace:'Calibri'}});"
            )
    return lines


def _slide_features_stats(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    features = s.get("features", [])[:4]
    stats = s.get("stats", [])[:3]
    accent_no_hash = t["accent"]
    lines = [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['mid']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:22,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
    ]
    # Left panel — feature list
    if features:
        feat_top = 1.3
        feat_h = (5.625 - feat_top - 0.2) / len(features)
        for i, feat in enumerate(features):
            fy = feat_top + i * feat_h
            ft = _esc(str(feat.get("title", "")))
            fsub = _esc(str(feat.get("subtitle", "")))
            fdesc = _esc(str(feat.get("description", "")))
            # card
            lines.append(
                f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:{fy + 0.04:.2f},w:5.8,h:{feat_h - 0.08:.2f},fill:{{color:'{t['mid']}',transparency:30}},line:{{type:'none'}},shadow:mkShadow(0.15)}});"
            )
            lines.append(
                f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:{fy + 0.04:.2f},w:0.06,h:{feat_h - 0.08:.2f},fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});"
            )
            # checkmark icon (react-icon)
            icon_size = min(0.35, feat_h * 0.35)
            lines.append(_emit_icon("FaCheckCircle", accent_no_hash, 0.55, fy + (feat_h - icon_size) / 2, icon_size, icon_size))
            # title + subtitle + desc
            if ft:
                lines.append(
                    f"    sl.addText('{ft}', {{x:1.0,y:{fy + 0.12:.2f},w:5.0,h:0.32,fontSize:13,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});"
                )
            if fsub:
                lines.append(
                    f"    sl.addText('{fsub}', {{x:1.0,y:{fy + 0.42:.2f},w:5.0,h:0.28,fontSize:10,italic:true,color:'{t['accent']}',fontFace:'Calibri',margin:0}});"
                )
            if fdesc:
                lines.append(
                    f"    sl.addText('{fdesc}', {{x:1.0,y:{fy + 0.7:.2f},w:5.0,h:{feat_h - 0.78:.2f},fontSize:10,color:'{t['text']}',fontFace:'Calibri',margin:0}});"
                )
    # Right panel — stat boxes
    if stats:
        stat_top = 1.3
        stat_gap = 0.18
        stat_h = (5.625 - stat_top - 0.2 - stat_gap * (len(stats) - 1)) / len(stats)
        for i, stat in enumerate(stats):
            sy = stat_top + i * (stat_h + stat_gap)
            val = _esc(stat.get("value", ""))
            lbl = _esc(stat.get("label", ""))
            lines.append(
                f"    sl.addShape(pres.shapes.RECTANGLE, {{x:6.4,y:{sy:.2f},w:3.2,h:{stat_h:.2f},fill:{{color:'{t['dark']}'}},line:{{color:'{t['accent']}',width:1.2}},shadow:mkShadow(0.20)}});"
            )
            lines.append(
                f"    sl.addText('{val}', {{x:6.4,y:{sy + stat_h * 0.1:.2f},w:3.2,h:{stat_h * 0.55:.2f},fontSize:38,bold:true,color:'{t['accent']}',align:'center',valign:'middle',fontFace:'Calibri',charSpacing:2,margin:0}});"
            )
            if lbl:
                lines.append(
                    f"    sl.addText('{lbl}', {{x:6.5,y:{sy + stat_h * 0.65:.2f},w:3.0,h:{stat_h * 0.3:.2f},fontSize:10,color:'{t['text']}',align:'center',fontFace:'Calibri',margin:0}});"
                )
    return lines


def _slide_definition(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    definition = _esc(s.get("definition", ""))
    cards = s.get("cards", [])[:4]
    n = len(cards)
    lines = [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['mid']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:22,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
    ]
    if definition:
        lines += [
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:1.3,w:9.2,h:1.4,fill:{{color:'{t['mid']}',transparency:25}},line:{{color:'{t['accent']}',width:2}},shadow:mkShadow(0.15)}});",
            f"    sl.addText('{definition}', {{x:0.6,y:1.35,w:8.8,h:1.3,fontSize:15,color:'{t['white']}',align:'center',valign:'middle',fontFace:'Calibri'}});",
        ]
    if cards:
        card_top = 2.9
        avail_h = round(5.625 - card_top - 0.2, 3)
        gap = 0.2
        card_w = round((9.2 - gap * (n - 1)) / n, 3)
        for i, card_data in enumerate(cards):
            cx = round(0.4 + i * (card_w + gap), 3)
            icon = card_data.get("icon", "")
            icon_color = _norm_color(card_data.get("color"), t["accent"])
            header = _esc(str(card_data.get("header", "")))
            body = _esc(str(card_data.get("body", "")))
            lines.append(
                f"    sl.addShape(pres.shapes.RECTANGLE, {{x:{cx},y:{card_top},w:{card_w},h:{avail_h},fill:{{color:'{t['mid']}',transparency:25}},line:{{type:'none'}},shadow:mkShadow(0.18)}});"
            )
            lines.append(
                f"    sl.addShape(pres.shapes.RECTANGLE, {{x:{cx},y:{card_top},w:{card_w},h:0.08,fill:{{color:'{icon_color}'}},line:{{type:'none'}}}});"
            )
            icon_size = 0.55
            icon_x = round(cx + (card_w - icon_size) / 2, 3)
            if icon:
                lines.append(_emit_icon(icon, icon_color, icon_x, card_top + 0.25, icon_size, icon_size, fontsize=24))
            if header:
                lines.append(
                    f"    sl.addText('{header}', {{x:{cx + 0.05:.2f},y:{card_top + 0.95:.2f},w:{card_w - 0.1:.2f},h:0.35,fontSize:12,bold:true,color:'{t['white']}',align:'center',fontFace:'Calibri',margin:0}});"
                )
            body_y = round(card_top + 1.35, 3)
            body_h_v = round(avail_h - 1.4, 3)
            if body and body_h_v > 0.2:
                lines.append(
                    f"    sl.addText('{body}', {{x:{cx + 0.1:.2f},y:{body_y},w:{card_w - 0.2:.2f},h:{body_h_v},fontSize:10,color:'{t['text']}',align:'center',fontFace:'Calibri'}});"
                )
    return lines


def _slide_numbered_list(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    items = s.get("items", [])[:6]
    lines = [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['accent']}',transparency:20}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:22,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
    ]
    if not items:
        return lines
    top = 1.25
    avail = 5.625 - top - 0.2
    gap = 0.06
    item_h = (avail - gap * (len(items) - 1)) / len(items)
    for i, item in enumerate(items):
        y = top + i * (item_h + gap)
        num = _esc(str(item.get("number", str(i + 1).zfill(2))))
        i_title = _esc(_strip_bullet_prefix(str(item.get("title", ""))))
        i_desc = _esc(_strip_bullet_prefix(str(item.get("description", ""))))
        # Row card
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:{y:.3f},w:9.2,h:{item_h:.3f},fill:{{color:'{t['mid']}',transparency:35}},line:{{type:'none'}}}});"
        )
        # Number badge
        badge_w = 0.85
        lines.append(
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:{y:.3f},w:{badge_w},h:{item_h:.3f},fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});"
        )
        lines.append(
            f"    sl.addText('{num}', {{x:0.4,y:{y:.3f},w:{badge_w},h:{item_h:.3f},fontSize:18,bold:true,color:'{t['dark']}',align:'center',valign:'middle',fontFace:'Calibri',margin:0}});"
        )
        # Title
        if i_title:
            lines.append(
                f"    sl.addText('{i_title}', {{x:1.4,y:{y + 0.06:.3f},w:8.1,h:{max(0.3, item_h * 0.4):.3f},fontSize:13,bold:true,color:'{t['accent']}',fontFace:'Calibri',margin:0}});"
            )
        # Description
        if i_desc:
            desc_y = y + max(0.3, item_h * 0.4) + 0.04
            desc_h = max(0.2, item_h - (max(0.3, item_h * 0.4) + 0.1))
            lines.append(
                f"    sl.addText('{i_desc}', {{x:1.4,y:{desc_y:.3f},w:8.1,h:{desc_h:.3f},fontSize:11,color:'{t['text']}',fontFace:'Calibri',margin:0}});"
            )
    return lines


def _slide_conclusion_cta(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", "Kesimpulan"))
    points = s.get("points", [])[:5]
    cta = _esc(s.get("cta", ""))
    accent_no_hash = t["accent"]
    lines = [
        f"    sl.addShape(pres.shapes.OVAL, {{x:8,y:-1,w:4,h:4,fill:{{color:'{t['mid']}',transparency:75}},line:{{type:'none'}}}});",
        f"    sl.addShape(pres.shapes.OVAL, {{x:-1,y:3,w:3,h:3,fill:{{color:'{t['accent']}',transparency:82}},line:{{type:'none'}}}});",
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.5,y:0.8,w:0.08,h:1.0,fill:{{color:'{t['accent']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.75,y:0.75,w:8.5,h:0.8,fontSize:30,bold:true,color:'{t['white']}',fontFace:'Calibri',charSpacing:2,margin:0}});",
    ]
    if points:
        ptop = 1.85
        avail = 3.1
        item_h = avail / len(points)
        for i, p in enumerate(points):
            py = ptop + i * item_h
            icon_size = min(0.35, item_h * 0.55)
            icon_y = py + (item_h - icon_size) / 2
            lines.append(_emit_icon("FaCheckCircle", accent_no_hash, 0.55, icon_y, icon_size, icon_size))
            lines.append(
                f"    sl.addText('{_esc(_strip_bullet_prefix(str(p)))}', {{x:1.05,y:{py:.3f},w:8.4,h:{item_h:.3f},fontSize:13,color:'{t['text']}',valign:'middle',fontFace:'Calibri',margin:0}});"
            )
    if cta:
        lines += [
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:2.5,y:5.0,w:5,h:0.55,fill:{{color:'{t['accent']}'}},line:{{type:'none'}},shadow:mkShadow(0.30)}});",
            f"    sl.addText('{cta}', {{x:2.5,y:5.0,w:5,h:0.55,fontSize:13,bold:true,color:'{t['dark']}',align:'center',valign:'middle',fontFace:'Calibri',margin:0}});",
        ]
    return lines


def _slide_challenges(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    items = s.get("items", [])[:4]
    tip = _esc(s.get("tip", ""))
    lines = [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['dark']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:22,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
    ]
    if items:
        positions = [(0.4, 1.3), (5.2, 1.3), (0.4, 2.95), (5.2, 2.95)]
        card_w, card_h = 4.4, 1.55
        for i, item in enumerate(items[:4]):
            x, y = positions[i]
            i_title = _esc(str(item.get("title", "")))
            i_desc = _esc(str(item.get("description", "")))
            i_color = _norm_color(item.get("color"), "DC2626")
            lines.append(
                f"    sl.addShape(pres.shapes.RECTANGLE, {{x:{x},y:{y},w:{card_w},h:{card_h},fill:{{color:'{t['white']}'}},line:{{type:'none'}},shadow:mkShadow(0.12)}});"
            )
            lines.append(
                f"    sl.addShape(pres.shapes.RECTANGLE, {{x:{x},y:{y},w:{card_w},h:0.08,fill:{{color:'{i_color}'}},line:{{type:'none'}}}});"
            )
            # warning icon (react-icon)
            lines.append(_emit_icon("FaExclamationTriangle", i_color, x + 0.18, y + 0.22, 0.42, 0.42))
            if i_title:
                lines.append(
                    f"    sl.addText('{i_title}', {{x:{x + 0.75:.2f},y:{y + 0.18:.2f},w:{card_w - 0.85:.2f},h:0.35,fontSize:13,bold:true,color:'{t['text_dark']}',fontFace:'Calibri',margin:0}});"
                )
            if i_desc:
                lines.append(
                    f"    sl.addText('{i_desc}', {{x:{x + 0.18:.2f},y:{y + 0.7:.2f},w:{card_w - 0.3:.2f},h:0.8,fontSize:10.5,color:'{t['muted']}',fontFace:'Calibri'}});"
                )
    if tip:
        lines += [
            f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:4.7,w:9.2,h:0.7,fill:{{color:'{t['accent']}',transparency:15}},line:{{color:'{t['accent']}',width:1}},shadow:mkShadow(0.10)}});",
            f"    sl.addText('💡  {tip}', {{x:0.5,y:4.75,w:9.0,h:0.6,fontSize:11,color:'{t['text_dark']}',valign:'middle',fontFace:'Calibri'}});",
        ]
    return lines


def _to_camel(snake: str) -> str:
    """Convert snake_case to camelCase, using map first then generic fallback."""
    if snake in _CHART_OPTION_MAP:
        return _CHART_OPTION_MAP[snake]
    parts = snake.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def _slide_chart(s: dict, t: dict) -> list[str]:
    title = _esc(s.get("title", ""))
    ct = str(s.get("chart_type", "bar")).lower()
    chart_const = _CHART_TYPES.get(ct, "BAR")
    chart_data = s.get("chart_data", [])
    user_opts = s.get("chart_options", {}) or {}

    # Default theme-aware options
    default_opts = {
        "chartColors": [t["accent"], t["mid"], "F59E0B", "10B981", "EF4444"],
        "showLegend": True,
        "legendPos": "b",
        "legendFontColor": t["text_dark"],
        "catAxisLabelColor": t["text_dark"],
        "valAxisLabelColor": t["text_dark"],
        "chartArea": {"fill": {"color": t["white"]}},
    }
    if ct == "bar":
        default_opts["barDir"] = "col"
    if ct in ("pie", "doughnut"):
        default_opts["showPercent"] = True
        default_opts.pop("catAxisLabelColor", None)
        default_opts.pop("valAxisLabelColor", None)

    # Apply user overrides (snake_case → camelCase)
    for k, v in user_opts.items():
        default_opts[_to_camel(k)] = v

    opts_json = json.dumps(default_opts)
    data_json = json.dumps(chart_data)
    return [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['dark']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:24,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0.4,y:1.3,w:9.2,h:4.1,fill:{{color:'{t['white']}'}},line:{{type:'none'}},shadow:mkShadow(0.12)}});",
        f"    sl.addChart(pres.charts.{chart_const}, {data_json}, Object.assign({{x:0.55,y:1.45,w:8.9,h:3.85}}, {opts_json}));",
    ]


def _slide_fallback(s: dict, t: dict) -> list[str]:
    layout = _esc(s.get("layout", "?"))
    title = _esc(s.get("title", layout))
    return [
        f"    sl.addShape(pres.shapes.RECTANGLE, {{x:0,y:0,w:10,h:1.05,fill:{{color:'{t['dark']}'}},line:{{type:'none'}}}});",
        f"    sl.addText('{title}', {{x:0.5,y:0.15,w:9.0,h:0.8,fontSize:24,bold:true,color:'{t['white']}',fontFace:'Calibri',margin:0}});",
        f"    sl.addText('[Unknown layout: {layout}]', {{x:0.5,y:1.5,w:9.0,h:0.6,fontSize:14,color:'{t['muted']}',fontFace:'Calibri',margin:0}});",
    ]


_LAYOUT_FN = {
    "title":               _slide_title,
    "bullets":             _slide_bullets,
    "content":             _slide_content,
    "two_column":          _slide_two_column,
    "two_column_bullets":  _slide_two_column_bullets,
    "table":               _slide_table,
    "image":               _slide_image,
    "image_bullets":       _slide_image_bullets,
    "stat_callout":        _slide_stat_callout,
    "section_divider":     _slide_section_divider,
    "quote":               _slide_quote,
    "agenda":              _slide_agenda,
    "timeline":            _slide_timeline,
    "icon_grid":           _slide_icon_grid,
    "features_stats":      _slide_features_stats,
    "definition":          _slide_definition,
    "numbered_list":       _slide_numbered_list,
    "conclusion_cta":      _slide_conclusion_cta,
    "challenges":          _slide_challenges,
    "chart":               _slide_chart,
}


# ---------------------------------------------------------------------------
# JS builder
# ---------------------------------------------------------------------------

_ICON_HELPER_JS = """\
async function iconToBase64Png(IconComponent, color, size) {
  size = size || 256;
  if (!IconComponent) return null;
  try {
    const svg = ReactDOMServer.renderToStaticMarkup(
      React.createElement(IconComponent, { color: color, size: String(size) })
    );
    const buf = await sharp(Buffer.from(svg)).png().toBuffer();
    return 'image/png;base64,' + buf.toString('base64');
  } catch (e) {
    console.warn('[pptx_claude] icon render failed:', e && e.message);
    return null;
  }
}
const mkShadow = (opacity) => ({
  type: 'outer', color: '000000', blur: 8, offset: 3, angle: 135,
  opacity: (opacity === undefined ? 0.14 : opacity)
});
"""


def _build_js(slides: list, out_path: str, theme_name: str) -> str:
    base_t = THEMES.get(theme_name.lower(), THEMES["midnight"])
    out_escaped = out_path.replace("\\", "\\\\")

    # Collect icons
    accent_no_hash = base_t["accent"]
    icon_map = _collect_icons(slides, accent_no_hash)
    icon_imports, icon_renders = _build_icon_prelude(icon_map)

    # Per-slide bodies
    slide_blocks = []
    for spec in slides:
        layout = spec.get("layout", "bullets")
        is_dark = layout in _DARK_LAYOUTS
        bg = base_t["dark"] if is_dark else base_t["light"]

        bg_override = str(spec.get("bg_override", "")).strip().lstrip("#")
        if len(bg_override) == 6:
            try:
                int(bg_override, 16)
                bg = bg_override
            except ValueError:
                pass

        # Per-slide theme: pick text color from the FINAL bg's luminance
        # (handles bg_override correctly — layout class alone is insufficient)
        t_slide = dict(base_t)
        t_slide["text"] = base_t["text"] if _bg_is_dark(bg) else base_t["text_dark"]

        fn = _LAYOUT_FN.get(layout, _slide_fallback)
        body = fn(spec, t_slide)

        notes = str(spec.get("notes", "")).strip()
        notes_line = f"\n    sl.addNotes('{_esc(notes)}');" if notes else ""

        slide_blocks.append(
            "  { let sl = pres.addSlide();\n"
            f"    sl.background = {{color:'{bg}'}};\n"
            + "\n".join(body)
            + notes_line
            + "\n  }"
        )

    parts = [
        "const pptxgen = require('pptxgenjs');",
        "const React = require('react');",
        "const ReactDOMServer = require('react-dom/server');",
        "const sharp = require('sharp');",
    ]
    if icon_imports:
        parts.append(icon_imports)
    parts.append("")
    parts.append(_ICON_HELPER_JS)
    parts.append("(async () => {")
    parts.append(icon_renders)
    parts.append("  const pres = new pptxgen();")
    parts.append("  pres.layout = 'LAYOUT_16x9';")
    parts.extend(slide_blocks)
    parts.append(
        f"  await pres.writeFile({{fileName: '{out_escaped}'}});"
    )
    parts.append("  console.log('done');")
    parts.append("})().catch(e => { console.error(e); process.exit(1); });")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

@tool
def create_pptx_js(slides: str, filename: str, theme: str = "midnight", config: RunnableConfig = None) -> str:
    """Create a visually polished PowerPoint presentation using pptxgenjs (Node.js).

    Uses react-icons + sharp for crisp PNG icon rendering, card shadows,
    decorative transparent ovals, and native pptxgenjs charts.

    Supports all 20 layouts: title, bullets, content, two_column,
    two_column_bullets, table, image, image_bullets, stat_callout,
    section_divider, quote, agenda, timeline, icon_grid, features_stats,
    definition, numbered_list, conclusion_cta, challenges, chart.

    Icons can be either:
        - react-icons names: "FaRocket", "MdSecurity", "HiUsers" etc.
          Renders as crisp colored PNG. Browse at react-icons.github.io
        - emoji or text: "🎓", "★", etc. Renders as text (fallback)

    Each slide also accepts optional cross-layout fields:
        "notes"       — speaker notes text
        "bg_override" — hex color string (e.g. "1A1A2E") to override slide background

    Args:
        slides:   JSON array of slide objects.
        filename: Output filename (e.g. "report.pptx"; .pptx appended if missing).
        theme:    Color theme — midnight | coral | forest | ocean | charcoal | cherry.
    """
    logger.info("[TOOL] create_pptx_js | filename=%s theme=%s", filename, theme)

    if not filename.endswith(".pptx"):
        filename += ".pptx"

    try:
        slides_list = json.loads(slides)
    except Exception as e:
        return f"Invalid slides JSON: {e}"

    # Safety-net: fill default icons on icon-mandatory cards when planner forgot
    _normalize_slides(slides_list)

    if not _node_ok():
        return (
            "Node.js is not installed on this server.\n"
            "To enable this skill: install Node.js, then run:\n"
            "  npm install pptxgenjs react react-dom react-icons sharp\n\n"
            "Alternative: use the standard `pptx` skill — call create_pptx() with the same slide spec."
        )

    if not _pptxgenjs_ok():
        return (
            "Required npm packages are missing. Run:\n"
            "  npm install pptxgenjs react react-dom react-icons sharp\n\n"
            "Alternative: use the standard `pptx` skill — call create_pptx() with the same slide spec."
        )

    out_name = f"{uuid.uuid4().hex}_{filename}"
    out_path = DOWNLOADS_DIR / out_name
    js_code = _build_js(slides_list, str(out_path), theme)

    tmp_js = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, encoding="utf-8",
            dir=str(PROJECT_ROOT),
        ) as f:
            f.write(js_code)
            tmp_js = f.name

        result = subprocess.run(
            ["node", tmp_js],
            capture_output=True, text=True, timeout=90,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode != 0:
            logger.error("[TOOL] create_pptx_js node error: %s", result.stderr[:800])
            return f"pptxgenjs execution failed: {result.stderr[:800]}"

        if not out_path.exists():
            return "pptxgenjs ran but output file was not created."

        thread_id = (config or {}).get("configurable", {}).get("thread_id", "")
        username = thread_id.split("__")[0] if "__" in thread_id else "anonymous"
        minio_name = upload_file_to_minio(
            out_path.read_bytes(), username, filename,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            folder="pptx",
        )
        if minio_name:
            url = f"/api/files/{minio_name}"
            suffix = ""
        else:
            url = f"/static/downloads/{out_name}"
            suffix = " WARNING: MinIO upload failed — file served from local storage and may disappear on server restart"
        logger.info(
            "[TOOL] create_pptx_js saved | url=%s | slides=%d", url, len(slides_list)
        )
        return f"file_url:{url}{suffix}"

    except subprocess.TimeoutExpired:
        return "pptxgenjs timed out after 90 seconds."
    except Exception as e:
        logger.error("[TOOL] create_pptx_js error: %s", e)
        return f"Failed to create presentation: {e}"
    finally:
        if tmp_js:
            try:
                os.unlink(tmp_js)
            except Exception:
                pass
