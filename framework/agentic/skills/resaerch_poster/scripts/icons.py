"""Small inline-SVG icon set for the poster (stroke icons, drawn here, no external files).

    svg = icon("target", size_css="4em", color="#0C3F83")
    name = pick_icon("Research methods")      # keyword -> icon name

Names: overview, target, people, monitor, chart, cart, tag, trust, quality, phone,
leaf, clipboard, star, money, globe, bulb, shield, book, clock, check, search,
document, message, trend, list, location, calendar, heart, tools, flag.
"""

from __future__ import annotations

import re

_VB = 'viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"'

ICONS: dict[str, str] = {
    "overview": '<circle cx="20" cy="20" r="11"/><path d="M28 28l11 11"/><path d="M20 13v3M20 24v3M13 20h3M24 20h3"/><circle cx="20" cy="20" r="3.5"/>',
    "search": '<circle cx="21" cy="21" r="12"/><path d="M30 30l10 10"/>',
    "target": '<circle cx="24" cy="24" r="16"/><circle cx="24" cy="24" r="9.5"/><circle cx="24" cy="24" r="3"/><path d="M24 8V4M24 44v-4M8 24H4M44 24h-4"/>',
    "people": '<circle cx="16" cy="18" r="6"/><circle cx="32" cy="18" r="6"/><path d="M4 40c0-7 5-11 12-11s12 4 12 11"/><path d="M28 29c7 0 12 4 12 11"/>',
    "monitor": '<rect x="5" y="8" width="38" height="26" rx="3"/><path d="M18 42h12M24 34v8"/><path d="M12 27l7-8 6 5 9-10"/>',
    "chart": '<path d="M6 42h36"/><rect x="10" y="26" width="7" height="12"/><rect x="20.5" y="16" width="7" height="22"/><rect x="31" y="9" width="7" height="29"/>',
    "trend": '<path d="M6 40h36"/><path d="M8 32l10-10 8 6 14-16"/><path d="M32 12h8v8"/>',
    "cart": '<path d="M4 8h6l5 22h22l4-15H13"/><circle cx="18" cy="38" r="3"/><circle cx="34" cy="38" r="3"/>',
    "tag": '<path d="M6 24V8h16l20 20-16 16z"/><circle cx="15" cy="17" r="3"/>',
    "trust": '<path d="M10 22l5-1V38h-5z"/><path d="M15 22l7-14c3 0 5 2 4 6l-1 6h11c2 0 4 2 3 5l-3 10c-1 2-2 3-4 3H15"/>',
    "quality": '<circle cx="24" cy="20" r="12"/><path d="M24 12l2.5 5 5.5.8-4 3.9.9 5.5-4.9-2.6-4.9 2.6.9-5.5-4-3.9 5.5-.8z"/><path d="M17 30l-3 14 10-5 10 5-3-14"/>',
    "phone": '<rect x="14" y="4" width="20" height="40" rx="4"/><path d="M21 38h6"/>',
    "leaf": '<path d="M8 40C8 20 20 8 42 8c0 22-12 34-32 34"/><path d="M8 40l18-18"/>',
    "clipboard": '<rect x="10" y="8" width="28" height="36" rx="3"/><path d="M18 8h12v6H18z"/><path d="M17 24h14M17 32h10"/>',
    "star": '<path d="M24 6l5.5 11.5 12.5 1.7-9 8.8 2.2 12.5L24 34.6l-11.2 5.9L15 28l-9-8.8 12.5-1.7z"/>',
    "money": '<rect x="4" y="12" width="40" height="24" rx="3"/><circle cx="24" cy="24" r="6"/><path d="M10 18h2M36 30h2"/>',
    "globe": '<circle cx="24" cy="24" r="18"/><path d="M6 24h36M24 6c6 6 6 30 0 36M24 6c-6 6-6 30 0 36"/>',
    "bulb": '<path d="M16 32c-4-3-6-7-6-12a14 14 0 0128 0c0 5-2 9-6 12v5H16z"/><path d="M18 43h12"/><path d="M24 20v6"/>',
    "shield": '<path d="M24 4l16 6v14c0 10-7 17-16 20-9-3-16-10-16-20V10z"/><path d="M17 24l5 5 9-10"/>',
    "book": '<path d="M8 8h13a4 4 0 014 4v28a4 4 0 00-4-4H8z"/><path d="M40 8H27a4 4 0 00-4 4v28a4 4 0 014-4h13z"/>',
    "clock": '<circle cx="24" cy="24" r="18"/><path d="M24 12v12l8 5"/>',
    "check": '<circle cx="24" cy="24" r="18"/><path d="M15 25l6 6 12-13"/>',
    "document": '<path d="M12 4h16l10 10v30H12z"/><path d="M28 4v10h10"/><path d="M18 26h14M18 34h10"/>',
    "message": '<path d="M6 10h36v22H20l-8 8v-8H6z"/><path d="M14 18h20M14 25h12"/>',
    "list": '<path d="M16 12h26M16 24h26M16 36h26"/><circle cx="8" cy="12" r="2.2"/><circle cx="8" cy="24" r="2.2"/><circle cx="8" cy="36" r="2.2"/>',
    "location": '<path d="M24 44s-14-13-14-24a14 14 0 0128 0c0 11-14 24-14 24z"/><circle cx="24" cy="20" r="5"/>',
    "calendar": '<rect x="6" y="10" width="36" height="32" rx="3"/><path d="M6 20h36M16 6v8M32 6v8"/>',
    "heart": '<path d="M24 42S6 30 6 17a9 9 0 0118-4 9 9 0 0118 4c0 13-18 25-18 25z"/>',
    "tools": '<path d="M30 8l10 10-14 14-10-10z"/><path d="M8 40l10-10"/><path d="M34 6l8 8"/>',
    "flag": '<path d="M10 44V6"/><path d="M10 8h28l-6 8 6 8H10"/>',
}

_HINTS = (
    ("overview", "overview"), ("background", "overview"), ("introduction", "overview"), ("pendahuluan", "overview"),
    ("latar", "overview"), ("summary", "overview"), ("ringkasan", "overview"),
    ("objective", "target"), ("goal", "target"), ("tujuan", "target"), ("aim", "target"), ("purpose", "target"),
    ("audience", "people"), ("respondent", "people"), ("participant", "people"), ("sample", "people"),
    ("customer", "people"), ("responden", "people"), ("demograf", "people"), ("user", "people"), ("segment", "people"),
    ("method", "monitor"), ("metode", "monitor"), ("survey", "monitor"), ("data collection", "monitor"),
    ("finding", "quality"), ("temuan", "quality"), ("result", "chart"), ("hasil", "chart"),
    ("insight", "chart"), ("wawasan", "chart"), ("analysis", "chart"), ("analisis", "chart"), ("statistic", "chart"),
    ("trend", "trend"), ("tren", "trend"), ("growth", "trend"), ("market", "trend"), ("pasar", "trend"),
    ("recommend", "clipboard"), ("rekomendasi", "clipboard"), ("action", "clipboard"), ("next step", "clipboard"),
    ("conclusion", "check"), ("kesimpulan", "check"),
    ("shop", "cart"), ("belanja", "cart"), ("e-commerce", "cart"), ("ecommerce", "cart"), ("purchase", "cart"),
    ("price", "tag"), ("harga", "tag"), ("cost", "tag"), ("pricing", "tag"),
    ("brand", "trust"), ("merek", "trust"), ("trust", "trust"), ("loyal", "heart"), ("satisf", "heart"),
    ("quality", "quality"), ("kualitas", "quality"),
    ("mobile", "phone"), ("app", "phone"), ("digital", "phone"),
    ("sustain", "leaf"), ("green", "leaf"), ("environment", "leaf"), ("lingkungan", "leaf"),
    ("money", "money"), ("income", "money"), ("revenue", "money"), ("budget", "money"), ("pendapatan", "money"),
    ("global", "globe"), ("online", "globe"), ("internet", "globe"),
    ("idea", "bulb"), ("innovat", "bulb"), ("inovasi", "bulb"),
    ("risk", "shield"), ("secur", "shield"), ("safe", "shield"), ("risiko", "shield"),
    ("literature", "book"), ("theory", "book"), ("teori", "book"), ("pustaka", "book"),
    ("time", "clock"), ("duration", "clock"), ("waktu", "clock"), ("schedule", "calendar"), ("jadwal", "calendar"),
    ("timeline", "calendar"), ("interview", "message"), ("wawancara", "message"), ("focus group", "message"),
    ("feedback", "message"), ("review", "star"), ("rating", "star"),
    ("location", "location"), ("region", "location"), ("lokasi", "location"), ("area", "location"),
    ("document", "document"), ("report", "document"), ("laporan", "document"),
    ("tool", "tools"), ("process", "tools"), ("implementation", "tools"),
    ("milestone", "flag"), ("target", "target"),
)


def pick_icon(text: str, default: str = "list") -> str:
    """Icon name for a header or item label (English + Indonesian keywords)."""
    low = (text or "").lower()
    for key, name in _HINTS:
        if key in low:
            return name
    return default


def icon(name: str, size_css: str = "1em", color: str = "currentColor", cls: str = "") -> str:
    body = ICONS.get(name) or ICONS.get(pick_icon(name)) or ICONS["list"]
    return (f'<svg class="ico {cls}" style="width:{size_css};height:{size_css};color:{color}" {_VB} '
            f'aria-hidden="true">{body}</svg>')


def resolve(name: str | None, fallback_text: str = "", default: str = "list") -> str:
    """Accept an icon name, an emoji, or nothing (-> keyword guess)."""
    if name and name in ICONS:
        return name
    if name:
        key = re.sub(r"[^a-z]", "", name.lower())
        if key in ICONS:
            return key
        guess = pick_icon(name, default="")
        if guess:
            return guess
    return pick_icon(fallback_text, default)
