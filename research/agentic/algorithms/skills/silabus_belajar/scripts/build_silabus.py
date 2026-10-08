"""Silabus spec (JSON) -> one self-contained HTML page built on assets/template-silabus.html.

The template's CSS and progress script are used unchanged; this script writes the page body: hero,
module map (diagram recipe 9), module cards, schedule, final project and sources.  It also checks the
spec against the skill's rules and repairs what code can repair, so a 4B model's answer still becomes
a page that follows them:

- objectives that start with "memahami" / "mengetahui" become "menjelaskan" (the reader must be able
  to check them),
- hours are whole numbers from 1 to 3; the totals and the weekly schedule are computed here,
- links that are not in the sources the user gave are removed (a local model has no web search),
- a term that an earlier module already uses but a later module teaches is reported,
- money topics without a module on risk or the business model are reported.

    python scripts/build_silabus.py spec.json -o silabus-python.html --hours-per-week 4

The normalised spec is written next to the page (silabus-python.json); materi_belajar takes a module
card from it as the contract for that module's lesson.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "template-silabus.html"

VAGUE_VERBS = ("memahami", "mengetahui", "mengerti", "mengenal", "paham", "tahu", "membahas", "mempelajari", "mendalami")
MONEY_WORDS = ("investasi", "saham", "kripto", "crypto", "bitcoin", "reksa dana", "reksadana", "keuangan", "trading",
               "forex", "obligasi", "deposito", "asuransi", "pinjaman", "uang", "emas", "bisnis", "startup", "pajak")
URL = re.compile(r"https?://[^\s)\"'<>]+|www\.[^\s)\"'<>]+", re.I)


class SpecError(ValueError):
    """The spec cannot become a page; the message says why (it is sent back to the model)."""


# ---------------------------------------------------------------------------
# Reading and repairing the spec
# ---------------------------------------------------------------------------

# *kata*, **kata** and `kode` from a model used to Markdown: the page shows text, not Markdown.  An
# asterisk between numbers or after a space ("400 * 1.300", "2*3*4") is multiplication and stays.
_EMPHASIS = re.compile(r"(?<![\w*])(\*{1,2})(?=\S)(.+?)(?<=\S)\1(?![\w*])")


def _plain(text: str) -> str:
    return re.sub(r"`([^`]+)`", r"\1", _EMPHASIS.sub(r"\2", text))


def _text(value, limit: int = 600) -> str:
    """One clean line of text from whatever the model wrote."""
    if isinstance(value, (list, tuple)):
        value = " ".join(str(v) for v in value)
    text = _plain(" ".join(str(value or "").split()))
    return text[:limit].rstrip()


def _list(value, limit: int, item_limit: int = 220) -> list[str]:
    items = value if isinstance(value, list) else [value] if value else []
    out = []
    for item in items:
        text = _text(item, item_limit)
        if text and text.lower() not in (o.lower() for o in out):
            out.append(text)
    return out[:limit]


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")[:50] or "topik"


def checkable(objective: str) -> tuple[str, bool]:
    """("Menjelaskan ...", True) when a vague verb such as "memahami" was replaced.

    A leading "Bisa"/"Mampu"/"Dapat" is dropped first: the page already writes "Anda bisa:".
    """
    objective = re.sub(r"^(anda\s+)?(bisa|mampu|dapat)\s+", "", objective.strip(), flags=re.I)
    words = objective.split()
    if words and words[0].lower().strip(",.") in VAGUE_VERBS:
        rest = " ".join(words[1:])
        return f"Menjelaskan {rest}".strip(), True
    return objective[:1].upper() + objective[1:], False


def strip_links(text: str, allowed: set) -> tuple[str, list]:
    removed = [u for u in URL.findall(text) if u.rstrip(".,") not in allowed]
    for url in removed:
        text = text.replace(url, "").replace("()", "")
    return " ".join(text.split()), removed


def is_money_topic(spec: dict) -> bool:
    text = " ".join([spec.get("topic", ""), spec.get("title", "")]).lower()
    return any(word in text for word in MONEY_WORDS)


def normalize(raw: dict, sources: list | None = None) -> tuple[dict, list]:
    """(spec ready to render, warnings).  Raises SpecError when there is too little to build a page."""
    if not isinstance(raw, dict):
        raise SpecError("the answer is not a JSON object")
    warnings: list[str] = []
    allowed = {s["url"] for s in sources or [] if s.get("url")}
    removed_links: list[str] = []

    def clean(value, limit=600):
        text, removed = strip_links(_text(value, limit), allowed)
        removed_links.extend(removed)
        return text

    topic = clean(raw.get("topic") or raw.get("title") or "", 80)
    if not topic:
        raise SpecError("'topic' is empty")
    spec = {
        "topic": topic,
        "title": clean(raw.get("title"), 90) or f"Belajar {topic} dari nol",
        "lead": clean(raw.get("lead"), 500),
        "level": clean(raw.get("level"), 40) or "Pemula",
        "assumptions": clean(raw.get("assumptions"), 500),
        "map_note": clean(raw.get("map_note"), 300),
        "running_example": clean(raw.get("running_example"), 300),
    }

    outcomes = []
    for item in _list(raw.get("outcomes"), 6):
        text, changed = checkable(clean(item, 220))
        outcomes.append(text)
        if changed:
            warnings.append(f"outcome changed to a checkable verb: {text!r}")
    if len(outcomes) < 3:
        raise SpecError(f"'outcomes' needs 4-6 items, got {len(outcomes)}")
    spec["outcomes"] = outcomes

    stages, number = [], 0
    for stage in raw.get("stages") or []:
        if not isinstance(stage, dict):
            continue
        modules = []
        for module in stage.get("modules") or []:
            if not isinstance(module, dict) or not _text(module.get("title")):
                continue
            number += 1
            objectives = []
            for item in _list(module.get("objectives"), 4):
                text, changed = checkable(clean(item, 220))
                objectives.append(text)
                if changed:
                    warnings.append(f"module {number}: objective changed to a checkable verb: {text!r}")
            try:
                hours = int(round(float(module.get("hours") or 2)))
            except (TypeError, ValueError):
                hours = 2
            if not 1 <= hours <= 3:
                warnings.append(f"module {number}: {hours} hours -> {min(3, max(1, hours))} (modules are 1-3 hours)")
            question = clean(module.get("question"), 200)
            if question and not question.endswith("?"):
                question += "?"
            result = clean(module.get("result"), 120)
            if len(result.split()) <= 2 and objectives:
                # "Bisa Menjelaskan" says nothing on the map; the first objective says what
                result = "Bisa " + objectives[0][:1].lower() + objectives[0][1:].rstrip(".")
                warnings.append(f"module {number}: result too short; written from the first objective")
            modules.append({
                "number": number,
                "title": clean(module.get("title"), 90),
                "question": question,
                "objectives": objectives,
                "terms": _list(module.get("terms"), 6, 40),
                "exercise": clean(module.get("exercise"), 400),
                "result": result,
                "hours": min(3, max(1, hours)),
                "source": clean(module.get("source"), 120),
            })
            if len(objectives) < 2:
                warnings.append(f"module {number}: {len(objectives)} objective(s); the rule asks for 2-4")
            if not modules[-1]["exercise"]:
                warnings.append(f"module {number}: no exercise")
        if modules:
            stages.append({"name": clean(stage.get("name"), 30) or f"Tahap {len(stages) + 1}", "modules": modules})
    if number < 3:
        raise SpecError(f"the syllabus needs 4-8 modules in 2-3 stages, got {number}")
    if number > 8:
        warnings.append(f"{number} modules; the rule asks for at most 8 (split the topic into phases)")
    spec["stages"] = stages

    project = raw.get("project") if isinstance(raw.get("project"), dict) else {}
    spec["project"] = {
        "title": clean(project.get("title"), 80) or "Proyek akhir",
        "task": clean(project.get("task"), 600),
        "criteria": _list([clean(c, 220) for c in project.get("criteria") or []], 5),
        "hours": min(8, max(1, int(project.get("hours") or 3))) if str(project.get("hours") or "3").isdigit() else 3,
    }
    if not spec["project"]["task"]:
        warnings.append("no final project task")

    # A term taught in module k must not be used in the cards of modules before k.
    modules = [m for s in stages for m in s["modules"]]
    for later in modules:
        for term in later["terms"]:
            pattern = re.compile(rf"(?<!\w){re.escape(term.lower())}(?!\w)")
            for earlier in modules[: later["number"] - 1]:
                card = " ".join([earlier["title"], earlier["question"], *earlier["objectives"], earlier["exercise"]])
                if pattern.search(card.lower()) and term.lower() not in (t.lower() for t in earlier["terms"]):
                    warnings.append(f"term {term!r} is taught in module {later['number']} "
                                    f"but already used in module {earlier['number']}")
                    break

    spec["money_topic"] = is_money_topic(spec)
    if spec["money_topic"]:
        all_text = " ".join(" ".join([m["title"], m["question"], *m["objectives"]]) for m in modules).lower()
        if "risiko" not in all_text:
            warnings.append("money topic without a module that covers risk")
        # "keuntungan" alone is not enough: "keuntungan investasi" let a syllabus without the module through
        if not any(w in all_text for w in ("model bisnis", "insentif", "siapa mendapat", "siapa membayar",
                                           "dibayar oleh", "pendapatan manajer", "imbalan")):
            warnings.append("money topic without a module on the business model or incentives")
    if removed_links:
        warnings.append(f"{len(removed_links)} link(s) not in the given sources were removed: "
                        + ", ".join(sorted(set(removed_links))[:5]))
    spec["sources"] = sources or []
    return spec, warnings


# ---------------------------------------------------------------------------
# Schedule and module map
# ---------------------------------------------------------------------------

def make_schedule(spec: dict, hours_per_week: int) -> list[dict]:
    """Weeks of whole modules, at most `hours_per_week` each (a longer module gets its own week),
    then the final project.  Every week names what is done by its end."""
    weeks, current, used = [], [], 0
    for module in (m for s in spec["stages"] for m in s["modules"]):
        if current and used + module["hours"] > hours_per_week:
            weeks.append(current)
            current, used = [], 0
        current.append(module)
        used += module["hours"]
    if current:
        weeks.append(current)
    rows = []
    for i, week in enumerate(weeks, 1):
        numbers = [m["number"] for m in week]
        label = f"Modul {numbers[0]}" if len(numbers) == 1 else f"Modul {numbers[0]}-{numbers[-1]}"
        result = week[-1]["result"] or f"Latihan modul {numbers[-1]} selesai"
        rows.append({"week": i, "modules": label, "hours": sum(m["hours"] for m in week), "result": result})
    project = spec["project"]
    for extra in range(math.ceil(project["hours"] / max(1, hours_per_week))):
        hours = min(hours_per_week, project["hours"] - extra * hours_per_week)
        rows.append({"week": len(rows) + 1, "modules": "Proyek akhir", "hours": hours,
                     "result": project["title"] if extra else f"{project['title']} dimulai"})
    if len(rows) > 1 and rows[-1]["modules"] == "Proyek akhir":
        rows[-1]["result"] = f"{project['title']} selesai"
    return rows


def _fit(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def module_map(spec: dict) -> str:
    """Recipe 9: one 320x48 box per module, stage names between groups, the project box in teal."""
    parts, y, prev_bottom = [], 34, None
    for stage in spec["stages"]:
        if prev_bottom is not None:
            y += 24                                   # recipe: first box of a new stage = previous + 86
        parts.append(f'<text class="to" x="20" y="{y - 12}">{html.escape(stage["name"].upper())}</text>')
        for module in stage["modules"]:
            if prev_bottom is not None:
                parts.append(f'<line class="ln" x1="180" y1="{prev_bottom}" x2="180" y2="{y - 4}" marker-end="url(#ah)"/>')
            title = _fit(f"{module['number']} · {module['title']}", 40)
            result = _fit(module["result"] or (module["objectives"][0] if module["objectives"] else ""), 45)
            parts.append(f'<rect class="bx" x="20" y="{y}" width="320" height="48" rx="8"/>'
                         f'<text class="tx" x="36" y="{y + 20}">{html.escape(title)}</text>'
                         f'<text class="ts" x="36" y="{y + 37}">{html.escape(result)}</text>')
            prev_bottom = y + 48
            y += 62
    y += 24
    project = spec["project"]
    parts.append(f'<text class="to" x="20" y="{y - 12}">PROYEK AKHIR</text>')
    parts.append(f'<line class="ln" x1="180" y1="{prev_bottom}" x2="180" y2="{y - 4}" marker-end="url(#ah)"/>')
    parts.append(f'<rect class="bt" x="20" y="{y}" width="320" height="48" rx="8"/>'
                 f'<text class="tx" x="36" y="{y + 20}">{html.escape(_fit(project["title"], 40))}</text>'
                 f'<text class="ts" x="36" y="{y + 37}">{html.escape(_fit(project["criteria"][0] if project["criteria"] else project["task"], 45))}</text>')
    count = sum(len(s["modules"]) for s in spec["stages"])
    label = f"Peta belajar {spec['topic']}: {count} modul dalam {len(spec['stages'])} tahap, lalu proyek akhir"
    return (f'<svg viewBox="0 0 360 {y + 68}" role="img" aria-label="{html.escape(label)}">'
            + "".join(parts) + "</svg>")


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _template_parts() -> tuple[str, str, str]:
    """(head up to <main>, the progress script, closing tags) from the original template."""
    template = TEMPLATE.read_text(encoding="utf-8")
    head = template[: template.index("<main>")]
    script = template[template.index("<script>"): template.index("</script>") + len("</script>")]
    return head, script, "\n</body>\n</html>\n"


def render(spec: dict, hours_per_week: int, model: str = "") -> str:
    esc = html.escape
    modules = [m for s in spec["stages"] for m in s["modules"]]
    schedule = make_schedule(spec, hours_per_week)
    total = sum(m["hours"] for m in modules) + spec["project"]["hours"]
    weeks = len(schedule)
    head, script, tail = _template_parts()
    head = head.replace("{{JUDUL}}", esc(spec["title"]))
    script = script.replace("{{SLUG}}", slugify(spec["topic"]))

    lead = spec["lead"] or f"Rencana belajar {spec['topic']} bertahap, dari dasar sampai bisa dipakai."
    assumptions = spec["assumptions"] or (f"level awal {spec['level'].lower()}, sekitar {hours_per_week} jam per minggu, "
                                          "tujuan paham cara kerja dan bisa memakainya")
    out = [head, "<main>\n<header class=\"hero\">", '<p class="eyebrow">Silabus belajar</p>',
           f"<h1>{esc(spec['title'])}</h1>", f'<p class="lead">{esc(lead)}</p>',
           f'<ul class="chips"><li>{esc(spec["level"])}</li><li>{len(modules)} modul</li><li>± {total} jam total</li>'
           f'<li>{weeks} minggu, {hours_per_week} jam per minggu</li></ul>',
           '<div class="goals"><strong>Setelah selesai, Anda bisa:</strong><ul>'
           + "".join(f"<li>{esc(o)}</li>" for o in spec["outcomes"]) + "</ul></div>",
           f'<div class="howto"><strong>Silabus ini dibuat dengan asumsi:</strong> {esc(assumptions)} '
           "Kalau ada yang tidak cocok, minta disesuaikan.</div>",
           '<div class="howto">Cara memakai: kerjakan modul berurutan, karena setiap modul memakai istilah dari modul '
           "sebelumnya. Di setiap modul: baca materi, kerjakan latihan, lalu jawab kuis. Centang <strong>Selesai</strong> "
           "kalau kuisnya sudah benar semua.</div>"]
    if spec["running_example"]:
        out.append(f'<div class="howto"><strong>Contoh yang dipakai di semua modul:</strong> {esc(spec["running_example"])}</div>')
    out.append('<ol class="toc"><li><a href="#peta">Peta belajar</a></li><li><a href="#modul">Modul</a></li>'
               '<li><a href="#jadwal">Jadwal</a></li><li><a href="#proyek">Proyek akhir</a></li>'
               '<li><a href="#sumber">Sumber belajar</a></li></ol>\n</header>')

    stage_names = " → ".join(s["name"] for s in spec["stages"])
    out.append('<section id="peta"><div class="chapter"><span class="num">1</span><h2>Peta belajar</h2></div>'
               f'<p>{esc(spec["map_note"] or f"Urutannya {stage_names}, lalu proyek akhir. Setiap modul memakai hasil modul sebelumnya.")}</p>'
               f'<figure class="fig">{module_map(spec)}<figcaption>Baca dari atas ke bawah: setiap kotak satu modul '
               "dengan hasilnya, kotak teal adalah proyek akhir.</figcaption></figure></section>")

    out.append('<section id="modul"><div class="chapter"><span class="num">2</span><h2>Modul</h2></div>'
               '<div class="progress"><div class="track"><div class="fill" id="pfill"></div></div><p class="lab" id="ptext"></p></div>')
    for stage in spec["stages"]:
        out.append(f'<p class="stage">{esc(stage["name"])}</p>')
        for m in stage["modules"]:
            mid = f"m{m['number']}"
            source = esc(m["source"]) if m["source"] else "Sumber: belum ditentukan"
            out.append(
                f'<article class="mod" id="{mid}"><div class="top"><span class="num">Modul {m["number"]}</span>'
                f'<h3>{esc(m["title"])}</h3></div>'
                + (f'<p class="ask">{esc(m["question"])}</p>' if m["question"] else "")
                + '<p class="sub">Setelah modul ini, Anda bisa</p><ul>'
                + "".join(f"<li>{esc(o)}</li>" for o in m["objectives"]) + "</ul>"
                + ('<p class="sub">Istilah yang dipelajari</p><ul class="chips">'
                   + "".join(f"<li>{esc(t)}</li>" for t in m["terms"]) + "</ul>" if m["terms"] else "")
                + (f'<p class="sub">Latihan</p><p>{esc(m["exercise"])}</p>' if m["exercise"] else "")
                + f'<div class="foot"><span>± {m["hours"]} jam</span><span>{source}</span>'
                '<span class="soon">Materi belum dibuat</span>'
                f'<label class="check"><input type="checkbox" data-mod="{mid}"> Selesai</label></div></article>')
    out.append("</section>")

    rows = "".join(f'<tr><td>{r["week"]}</td><td>{esc(r["modules"])}</td><td>{r["hours"]} jam</td><td>{esc(r["result"])}</td></tr>'
                   for r in schedule)
    out.append('<section id="jadwal"><div class="chapter"><span class="num">3</span><h2>Jadwal</h2></div>'
               f"<p>Sekitar {hours_per_week} jam per minggu, satu atau dua modul utuh per minggu, lalu proyek akhir. "
               "Kalau satu minggu terlewat, lanjutkan dari modul terakhir yang selesai.</p>"
               '<div class="tablewrap"><table><thead><tr><th>Minggu</th><th>Modul</th><th>Waktu</th><th>Hasil nyata</th></tr></thead>'
               f"<tbody>{rows}</tbody></table></div></section>")

    project = spec["project"]
    out.append('<section id="proyek"><div class="chapter"><span class="num">4</span><h2>Proyek akhir</h2></div>'
               f'<p><strong>{esc(project["title"])}.</strong> {esc(project["task"])}</p>'
               + ("<h3>Dianggap selesai kalau</h3><ul>" + "".join(f"<li>{esc(c)}</li>" for c in project["criteria"]) + "</ul>"
                  if project["criteria"] else "") + "</section>")

    if spec["sources"]:
        source_rows = "".join(
            f'<tr><td><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a></td>'
            f'<td>{esc(s.get("used_for") or "Semua modul")}</td></tr>' for s in spec["sources"])
        sources = ('<div class="tablewrap"><table><thead><tr><th>Sumber</th><th>Dipakai untuk</th></tr></thead>'
                   f"<tbody>{source_rows}</tbody></table></div>")
    else:
        sources = ('<div class="note">Belum ada sumber yang diberikan. Silabus ini disusun dari pengetahuan umum '
                   + (f"model {esc(model)}" if model else "model bahasa")
                   + ", jadi periksa angka dan nama penting ke sumber resmi sebelum materinya dibuat.</div>")
    money = ('<div class="note">Silabus ini mengajarkan cara kerja, bukan menyarankan untuk membeli atau menjual apa pun. '
             "Halaman ini bukan saran keuangan.</div>") if spec["money_topic"] else ""
    out.append('<section id="sumber"><div class="chapter"><span class="num">5</span><h2>Sumber belajar</h2></div>'
               f"{sources}{money}</section>\n</main>")
    made_by = f" Isi silabus ditulis oleh {esc(model)} dan disusun oleh skill silabus_belajar." if model else ""
    out.append(f"<footer>Silabus ini disusun untuk belajar mandiri. Materi setiap modul dibuat terpisah dan "
               f"ditautkan dari kartu modulnya.{made_by}</footer>\n{script}{tail}")
    return "\n".join(out)


def read_sources(path: str | None) -> list:
    """Lines "Judul | URL | dipakai untuk" (the third part is optional); blank lines and # lines are ignored."""
    if not path:
        return []
    sources = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        url = next((p for p in parts if URL.match(p)), "")
        title = next((p for p in parts if p and p != url), url)
        rest = [p for p in parts if p not in (url, title)]
        sources.append({"title": title, "url": url, "used_for": rest[0] if rest else ""})
    return sources


def build_silabus(raw, filename: str, sources: list | None = None, hours_per_week: int = 4, model: str = "") -> dict:
    """Spec (dict or JSON text) -> HTML page and normalised JSON.  Returns {"ok", "path", "json", "warnings", ...}."""
    try:
        data = raw if isinstance(raw, dict) else json.loads(raw)
        spec, warnings = normalize(data, sources)
    except (ValueError, SpecError) as error:
        return {"ok": False, "error": str(error)}
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(spec, hours_per_week, model), encoding="utf-8")
    spec["hours_per_week"] = hours_per_week
    spec["model"] = model
    json_path = path.with_suffix(".json")
    json_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    modules = [m for s in spec["stages"] for m in s["modules"]]
    return {"ok": True, "path": str(path), "json": str(json_path), "warnings": warnings,
            "modules": len(modules), "stages": len(spec["stages"]),
            "hours": sum(m["hours"] for m in modules) + spec["project"]["hours"],
            "weeks": len(make_schedule(spec, hours_per_week))}


def format_result(res: dict) -> str:
    if not res.get("ok"):
        return f"GAGAL: {res.get('error')}"
    lines = [f"OK: {res['path']} ({res['modules']} modul, {res['stages']} tahap, ± {res['hours']} jam, {res['weeks']} minggu)",
             f"     kontrak modul untuk materi_belajar: {res['json']}"]
    lines += [f"     peringatan: {w}" for w in res.get("warnings", [])]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Silabus spec (JSON) -> HTML page.")
    ap.add_argument("spec", help="JSON file written by a model or by hand")
    ap.add_argument("-o", "--output", help="HTML file (default: silabus-<topic>.html)")
    ap.add_argument("--sources", help='file with lines "Judul | URL | dipakai untuk"')
    ap.add_argument("--hours-per-week", type=int, default=4)
    ap.add_argument("--model", default="", help="name of the model that wrote the spec, shown in the footer")
    args = ap.parse_args()
    raw = Path(args.spec).read_text(encoding="utf-8")
    try:
        topic = json.loads(raw).get("topic", "topik")
    except ValueError:
        topic = "topik"
    output = args.output or f"silabus-{slugify(topic)}.html"
    res = build_silabus(raw, output, read_sources(args.sources), args.hours_per_week, args.model)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    print(format_result(res))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
