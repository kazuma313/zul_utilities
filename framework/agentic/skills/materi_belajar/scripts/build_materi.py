"""Materi spec (JSON) -> one self-contained lesson page built on assets/template-materi.html.

The template's CSS and quiz script are used unchanged; this script writes the page: hero, chapters
(Apa / Bagaimana / Mengapa penting) with a term box at each term's first appearance and a step diagram
(diagram recipe 1), an interactive step-by-step demo, summary, quiz, exercises, "next" box and glossary.
It checks the spec against the skill's rules and repairs what code can repair:

- with a module card from a silabus (the contract), title, question, objectives and terms are the
  card's, word for word,
- quiz answers are moved so the right one is not always in the same place, and every explanation
  names the chapter to read again,
- objectives that start with "memahami" / "mengetahui" become "menjelaskan",
- an objective that no chapter teaches, or that no question or exercise tests, is reported,
- links that are not in the sources the user gave are removed.

    python scripts/build_materi.py spec.json -o materi-reksa-dana.html
    python scripts/build_materi.py spec.json --silabus silabus-reksa-dana.json --module 2 -o reksa-dana-modul-2.html
"""

from __future__ import annotations

import argparse
import ast
import html
import json
import operator
import re
import sys
import unicodedata
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "template-materi.html"

VAGUE_VERBS = ("memahami", "mengetahui", "mengerti", "mengenal", "paham", "tahu", "membahas", "mempelajari", "mendalami")
MONEY_WORDS = ("investasi", "saham", "kripto", "crypto", "bitcoin", "reksa dana", "reksadana", "keuangan", "trading",
               "forex", "obligasi", "deposito", "asuransi", "pinjaman", "emas", "pajak")
URL = re.compile(r"https?://[^\s)\"'<>]+|www\.[^\s)\"'<>]+", re.I)
TARGET_POSITIONS = (1, 0, 2, 2, 0, 1)        # where the right answer goes, question by question


class SpecError(ValueError):
    """The spec cannot become a page; the message says why (it is sent back to the model)."""


# ---------------------------------------------------------------------------
# Checking written arithmetic
# ---------------------------------------------------------------------------
# Small models write "500 unit x Rp1.300 = Rp520.000" correctly in one sentence and "Rp90.000" for
# 300 x 100 in the next.  Every calculation that is written out (a chain of sides joined by "=", in
# either order, or a number followed by the expression in brackets) is computed again here, and each
# pair of neighbouring sides that does not match is reported.

_NUM = r"(?:Rp\s?)?\d+(?:[.,]\d+)*\s?%?"
_TERM = rf"\(?\s*{_NUM}(?:\s+(?![xX]\b)[A-Za-z]{{1,8}})?\s*\)?"
_OP = r"\s*[x×*/+\-−]\s*|\s+:\s+|(?<=\d):(?=\d)"        # "10 : 4" divides, "Langkah 1: ..." does not
_SIDE = rf"[-−]?\s*{_TERM}(?:(?:{_OP}){_TERM})*"
_CHAIN = re.compile(rf"(?<![\w.,])({_SIDE})(?:\s*=\s*{_SIDE})+")
_VALUE_THEN_BRACKET = re.compile(rf"(?<![\w.,])({_NUM})\s*(\((?:[^()]|\([^()]*\))*\)(?:(?:{_OP}){_NUM})*)")


def _number(token: str) -> float:
    percent = "%" in token
    token = re.sub(r"Rp\s?|%|\s", "", token)
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", token):          # 1.250.000 or 1.250,5
        value = float(token.replace(".", "").replace(",", "."))
    elif re.fullmatch(r"\d+,\d{1,2}", token):                         # 0,5
        value = float(token.replace(",", "."))
    else:
        value = float(token.replace(",", ""))
    return value / 100 if percent else value


def _evaluate(expression: str) -> float | None:
    """The value of an expression of numbers, + - x / : and brackets; None when it is something else."""
    text = re.sub(r"(?<=\d)\s+(?![xX]\b)[A-Za-z]{1,8}", "", expression)   # "400 unit" -> "400"; "x" stays
    text = re.sub(_NUM, lambda m: repr(_number(m.group(0))), text)
    text = text.replace("×", "*").replace("x", "*").replace(":", "/").replace("−", "-")
    if not re.fullmatch(r"[\d.\s()+\-*/]+", text) or not re.search(r"[+\-*/]", text):
        return None
    try:
        return _arithmetic(ast.parse(text.strip(), mode="eval").body)
    except (SyntaxError, ZeroDivisionError, TypeError, ValueError):
        return None


_OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def _arithmetic(node) -> float:
    """Numbers and + - * / only: anything else in the tree raises ValueError (no code is ever run)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_arithmetic(node.left), _arithmetic(node.right))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_arithmetic(node.operand)
    raise ValueError("not plain arithmetic")


def _differs(value: float, expected: float) -> bool:
    return abs(value - expected) > max(0.5, abs(expected) * 0.005)


def _value(side: str) -> float | None:
    """A side of "=": a calculation, or one number such as "Rp20.000" or "400 unit"."""
    computed = _evaluate(side)
    if computed is not None:
        return computed
    token = re.sub(r"(?<=\d)\s+[A-Za-z]{1,8}$", "", side.strip()).strip("() ")
    return _number(token) if re.fullmatch(_NUM, token) else None


def arithmetic_errors(text: str) -> list[str]:
    """Written calculations in `text` whose result is wrong, as "<what is written> (hasilnya N)"."""
    errors = []
    for match in _CHAIN.finditer(text):
        sides = [s.strip() for s in re.split(r"\s*=\s*", match.group(0))]
        for left, right in zip(sides, sides[1:]):
            if any(s.count("(") != s.count(")") for s in (left, right)):   # "(NAB Rp1.600) = ..." is a label
                continue
            calculation = next((s for s in (left, right) if _evaluate(s) is not None), None)
            values = _value(left), _value(right)
            if calculation is None or None in values:      # "Rp500.000 = Rp500.000" checks nothing
                continue
            if _differs(*values):
                errors.append(f"{left} = {right} (hasilnya {_evaluate(calculation):,.10g})")
    for match in _VALUE_THEN_BRACKET.finditer(text):
        computed = _evaluate(match.group(2))
        if computed is not None and _differs(_number(match.group(1)), computed):
            errors.append(f"{match.group(0).strip()} (hasilnya {computed:,.10g})")
    return errors


# ---------------------------------------------------------------------------
# Reading and repairing the spec
# ---------------------------------------------------------------------------

# *kata*, **kata** and `kode` from a model used to Markdown: the page shows text, not Markdown.  An
# asterisk between numbers or after a space ("400 * 1.300", "2*3*4") is multiplication and stays.
_EMPHASIS = re.compile(r"(?<![\w*])(\*{1,2})(?=\S)(.+?)(?<=\S)\1(?![\w*])")


def _plain(text: str) -> str:
    return re.sub(r"`([^`]+)`", r"\1", _EMPHASIS.sub(r"\2", text))


def _text(value, limit: int = 900) -> str:
    if isinstance(value, (list, tuple)):
        value = " ".join(str(v) for v in value)
    return _plain(" ".join(str(value or "").split()))[:limit].rstrip()


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")[:50] or "materi"


def checkable(objective: str) -> tuple[str, bool]:
    objective = re.sub(r"^(anda\s+)?(bisa|mampu|dapat)\s+", "", objective.strip(), flags=re.I)
    words = objective.split()
    if words and words[0].lower().strip(",.") in VAGUE_VERBS:
        return f"Menjelaskan {' '.join(words[1:])}".strip(), True
    return objective[:1].upper() + objective[1:], False


def _index(value, size: int, default: int = 0) -> int:
    """A 1-based number from the model -> a 0-based index inside 0..size-1."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return min(size - 1, max(0, number - 1))


def load_contract(silabus_json: str | None, module: int | None) -> dict | None:
    """The module card from a silabus written by silabus_belajar, with its neighbours."""
    if not silabus_json:
        return None
    spec = json.loads(Path(silabus_json).read_text(encoding="utf-8"))
    modules = [m for s in spec.get("stages", []) for m in s.get("modules", [])]
    if not module or not 1 <= module <= len(modules):
        raise SpecError(f"module {module} is not in {silabus_json} ({len(modules)} modules)")
    card = modules[module - 1]
    return {"topic": spec.get("topic", ""), "silabus_title": spec.get("title", ""),
            "silabus_file": Path(silabus_json).with_suffix(".html").name, "number": module, "total": len(modules),
            "title": card.get("title", ""), "question": card.get("question", ""),
            "objectives": card.get("objectives", []), "terms": card.get("terms", []),
            "exercise": card.get("exercise", ""), "hours": card.get("hours", 2), "source": card.get("source", ""),
            "previous": modules[module - 2] if module > 1 else None,
            "next": modules[module] if module < len(modules) else None,
            "project": spec.get("project", {}), "running_example": spec.get("running_example", ""),
            "money_topic": spec.get("money_topic", False)}


def normalize(raw: dict, contract: dict | None = None, sources: list | None = None) -> tuple[dict, list]:
    if not isinstance(raw, dict):
        raise SpecError("the answer is not a JSON object")
    warnings: list[str] = []
    allowed = {s["url"] for s in sources or [] if s.get("url")}
    removed_links: list[str] = []

    def clean(value, limit=900):
        text = _text(value, limit)
        for url in URL.findall(text):
            if url.rstrip(".,") not in allowed:
                removed_links.append(url)
                text = text.replace(url, "")
        return " ".join(text.split())

    if contract:
        objectives = [_text(o, 220) for o in contract["objectives"]]
        title, lead_question = contract["title"], contract["question"]
    else:
        objectives = []
        for item in raw.get("objectives") or []:
            text, changed = checkable(clean(item, 220))
            if text:
                objectives.append(text)
            if changed:
                warnings.append(f"objective changed to a checkable verb: {text!r}")
        objectives = objectives[:4]
        title, lead_question = clean(raw.get("title"), 90), ""
    if len(objectives) < 2:
        raise SpecError(f"'objectives' needs 2-4 items, got {len(objectives)}")
    if not title:
        raise SpecError("'title' is empty")

    chapters, seen_terms = [], set()
    for item in raw.get("chapters") or []:
        if not isinstance(item, dict) or not _text(item.get("title")):
            continue
        terms = []
        for term in item.get("terms") or []:
            if isinstance(term, dict):
                name, meaning = clean(term.get("term"), 50), clean(term.get("meaning"), 300)
            else:
                name, meaning = clean(term, 50), ""
            if name and meaning and name.lower() not in seen_terms:
                seen_terms.add(name.lower())
                terms.append({"term": name, "meaning": meaning})
        steps = [clean(s.get("label") if isinstance(s, dict) else s, 60) for s in item.get("steps") or []]
        # "1. ..." or "Bab 1: ..." -> "...": the page shows the number already
        heading = re.sub(r"^(bab\s*\d+\s*[.):-]?|\d+\s*[.):-])\s*", "", clean(item.get("title"), 90), flags=re.I)
        chapters.append({
            "title": heading, "what": clean(item.get("what")), "how": clean(item.get("how")),
            "why": clean(item.get("why")), "terms": terms, "steps": [s for s in steps if s][:5],
            "objective": _index(item.get("objective"), len(objectives)),
        })
    if len(chapters) < 3:
        raise SpecError(f"the lesson needs 3-6 chapters, got {len(chapters)}")
    chapters = chapters[:6]
    for number, chapter in enumerate(chapters, 1):
        for part in ("what", "how", "why"):
            if not chapter[part]:
                warnings.append(f"chapter {number}: '{part}' is empty")

    quiz = []
    for item in raw.get("quiz") or []:
        if not isinstance(item, dict):
            continue
        question = clean(item.get("question"), 300)
        # The model writes the right answer and two wrong ones as text ("right", "wrong"), so it never has
        # to count positions; "options" + "answer" (a 0-based index) is read too, for hand-written specs.
        right = clean(item.get("right"), 200)
        wrong = [w for w in (clean(x, 200) for x in item.get("wrong") or []) if w and w.lower() != right.lower()]
        if not right:
            options = [clean(o, 200) for o in item.get("options") or [] if clean(o, 200)]
            answer = item.get("answer")
            if options and isinstance(answer, int) and 0 <= answer < len(options):
                right, wrong = options[answer], [o for i, o in enumerate(options) if i != answer]
        wrong = list(dict.fromkeys(wrong))[:2]
        if not question or not right or len(wrong) < 2:
            warnings.append(f"quiz question dropped (needs a question, the right answer and 2 wrong ones): {question[:60]!r}")
            continue
        objective = _index(item.get("objective"), len(objectives))
        target = TARGET_POSITIONS[len(quiz) % len(TARGET_POSITIONS)]
        placed = wrong[:]
        placed.insert(target, right)
        why = clean(item.get("why"), 400)
        if not re.search(r"\bbab\s*\d", why, re.I):
            serving = next((i for i, c in enumerate(chapters, 1) if c["objective"] == objective), 1)
            why = f"{why.rstrip('.')}. Lihat bab {serving}.".lstrip(". ")
        quiz.append({"q": question, "opts": placed, "a": target, "why": why, "objective": objective})
    if len(quiz) < 3:
        raise SpecError(f"the quiz needs 4-6 questions with 3 options each, got {len(quiz)} usable")
    quiz = quiz[:6]

    exercises = []
    for item in raw.get("exercises") or []:
        if isinstance(item, dict) and _text(item.get("task")):
            exercises.append({"title": clean(item.get("title"), 90) or "Latihan", "task": clean(item.get("task")),
                              "expected": clean(item.get("expected"), 400), "objective": _index(item.get("objective"), len(objectives), -1)})
    if contract and contract.get("exercise"):
        # The card's exercise comes first, in the card's words.  Its expected result is taken from the
        # model's exercise that is the same task (most words shared), never from a different task.
        card = _text(contract["exercise"])
        card_words = set(re.findall(r"\w+", card.lower()))
        same = next((e for e in exercises
                     if len(card_words & set(re.findall(r"\w+", e["task"].lower()))) >= 0.5 * len(card_words)), None)
        if same:
            exercises.remove(same)
        exercises.insert(0, {"title": "Latihan dari silabus", "task": card,
                             "expected": same["expected"] if same else "", "objective": same["objective"] if same else -1})
    exercises = exercises[:3]
    for exercise in exercises:
        if not exercise["expected"]:
            warnings.append(f"exercise {exercise['title']!r} has no expected result")

    for i, objective in enumerate(objectives):
        if not any(c["objective"] == i for c in chapters):
            warnings.append(f"objective {i + 1} is taught by no chapter: {objective!r}")
        if not any(q["objective"] == i for q in quiz) and not any(e["objective"] == i for e in exercises):
            warnings.append(f"objective {i + 1} is tested by no question or exercise: {objective!r}")
    if contract:
        missing = [t for t in contract["terms"] if t.lower() not in seen_terms]
        if missing:
            warnings.append("terms from the module card without a term box: " + ", ".join(missing))

    demo = raw.get("demo") if isinstance(raw.get("demo"), dict) else {}
    demo_steps = [{"label": clean(s.get("label"), 60), "detail": clean(s.get("detail"), 300)}
                  for s in demo.get("steps") or [] if isinstance(s, dict) and _text(s.get("label"))][:6]
    if len(demo_steps) < 3:
        warnings.append("demo has fewer than 3 steps; the page has no interactive demo")

    lead = clean(raw.get("lead"), 500)
    spec = {
        "title": title, "lead": lead, "question": lead_question, "objectives": objectives,
        "prior": clean(raw.get("prior"), 500), "chapters": chapters,
        "demo": {"title": clean(demo.get("title"), 90) or "Coba sendiri", "instruction": clean(demo.get("instruction"), 300),
                 "steps": demo_steps},
        "summary": [clean(s, 300) for s in raw.get("summary") or [] if clean(s, 300)][:6],
        "quiz": quiz, "exercises": exercises, "next": clean(raw.get("next"), 400),
        "money_topic": bool(contract and contract.get("money_topic"))
        or any(w in (title + " " + lead).lower() for w in MONEY_WORDS),
        "sources": sources or [],
    }
    previous = (contract or {}).get("previous")
    if not spec["prior"] and previous:
        # the reader still gets the link back to what they learned; the card says what it was
        terms = ", ".join(previous.get("terms", [])[:4])
        spec["prior"] = f"Modul sebelumnya, {previous.get('title')}, mengajarkan {terms}." if terms else \
            f"Modul ini melanjutkan {previous.get('title')}."
        warnings.append("prior was empty; written from the previous module card")
    if len(spec["summary"]) < 3:
        warnings.append(f"summary has {len(spec['summary'])} point(s); the rule asks for 4-6")
    if removed_links:
        warnings.append(f"{len(removed_links)} link(s) not in the given sources were removed")

    places = [(f"bab {i}", " ".join([c["what"], c["how"], c["why"]])) for i, c in enumerate(chapters, 1)]
    places += [("demo", " ".join(s["detail"] for s in demo_steps)), ("rangkuman", " ".join(spec["summary"]))]
    places += [(f"soal {i}", " ".join([q["q"], q["opts"][q["a"]], q["why"]])) for i, q in enumerate(quiz, 1)]
    places += [(f"latihan {e['title']!r}", " ".join([e["task"], e["expected"]])) for e in exercises]
    for place, text in places:
        for error in arithmetic_errors(text):
            warnings.append(f"arithmetic in {place} does not add up: {error}")
    return spec, warnings


# ---------------------------------------------------------------------------
# Diagrams and the demo
# ---------------------------------------------------------------------------

def _fit(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _lines(text: str, width: int = 41, count: int = 2) -> list[str]:
    """Word-wrap `text` into at most `count` lines of `width` characters; the last line is cut with "…"."""
    words, lines = text.split(), [""]
    for word in words:
        if len(lines[-1]) + len(word) + (1 if lines[-1] else 0) <= width:
            lines[-1] = f"{lines[-1]} {word}".strip()
        elif len(lines) < count:
            lines.append(word[:width])
        else:
            lines[-1] = _fit(lines[-1] + " " + word, width)
            break
    return lines


def _step_boxes(labels: list[str], css_of) -> tuple[list[str], int]:
    """SVG parts of a vertical flow (recipe 1): a 40-high box per one-line step, 56 for two lines."""
    parts, y = [], 20
    for i, label in enumerate(labels):
        if i:
            parts.append(f'<line class="ln" x1="180" y1="{y - 20}" x2="180" y2="{y - 4}" marker-end="url(#ah)"/>')
        lines = _lines(f"{i + 1}. {label}")
        height = 40 if len(lines) == 1 else 56
        text = "".join(f'<tspan x="36" dy="{0 if j == 0 else 16}">{html.escape(line)}</tspan>' for j, line in enumerate(lines))
        parts.append(f'<rect class="{css_of(i)}" x="20" y="{y}" width="320" height="{height}" rx="8"/>'
                     f'<text class="tx" x="36" y="{y + (25 if height == 40 else 24)}">{text}</text>')
        y += height + 20
    return parts, y


def step_diagram(steps: list[str], label: str) -> str:
    """Recipe 1: boxes top to bottom with arrows; the last step, the result, in teal."""
    parts, y = _step_boxes(steps, lambda i: "bt" if i == len(steps) - 1 else "bx")
    return f'<svg viewBox="0 0 360 {y}" role="img" aria-label="{html.escape(label)}">{"".join(parts)}</svg>'


DEMO_SCRIPT = """
<script>
(function(){
  /* Demo langkah demi langkah: kotak yang sedang dibahas disorot, yang sudah lewat jadi teal. */
  var STEPS = %s;
  var boxes = document.querySelectorAll('#demo rect'), text = document.getElementById('demotext');
  var label = document.getElementById('demostep'), current = 0;
  function show(){
    Array.prototype.forEach.call(boxes, function(box, i){
      box.setAttribute('class', i < current ? 'bt' : (i === current ? 'bo' : 'bx'));
    });
    label.textContent = 'Langkah ' + (current + 1) + ' dari ' + STEPS.length;
    text.textContent = STEPS[current].detail || STEPS[current].label;
    document.getElementById('demoprev').disabled = current === 0;
    document.getElementById('demonext').disabled = current === STEPS.length - 1;
  }
  document.getElementById('demoprev').addEventListener('click', function(){ if (current > 0) { current--; show(); } });
  document.getElementById('demonext').addEventListener('click', function(){ if (current < STEPS.length - 1) { current++; show(); } });
  document.getElementById('demoreset').addEventListener('click', function(){ current = 0; show(); });
  show();
})();
</script>"""


def demo_block(demo: dict) -> tuple[str, str]:
    """(HTML of the demo, its script); empty when there are fewer than 3 steps."""
    steps = demo["steps"]
    if len(steps) < 3:
        return "", ""
    parts, y = _step_boxes([s["label"] for s in steps], lambda i: "bx")
    title = html.escape(demo["title"])
    svg = f'<svg viewBox="0 0 360 {y}" role="img" aria-label="{title}">' + "".join(parts) + "</svg>"
    instruction = demo["instruction"] or "Klik Berikutnya untuk melihat setiap langkah, lalu perhatikan kotak yang berubah warna."
    block = (f'<section id="demo-sec"><div class="chapter"><span class="num">▶</span><h2>{html.escape(demo["title"])}</h2></div>'
             f'<div class="fig" id="demo">{svg}<p class="lab" id="demostep"></p>'
             '<div id="demotext" class="status no" style="display:block"></div>'
             '<div class="btns"><button type="button" id="demoprev">Sebelumnya</button>'
             '<button type="button" class="primary" id="demonext">Berikutnya</button>'
             '<button type="button" id="demoreset">Ulangi</button></div>'
             f'<p class="lab">{html.escape(instruction)}</p></div></section>')
    payload = json.dumps(steps, ensure_ascii=False).replace("</", "<\\/")
    return block, DEMO_SCRIPT % payload


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _template_parts() -> tuple[str, str]:
    template = TEMPLATE.read_text(encoding="utf-8")
    head = template[: template.index("<main>")]
    script = template[template.index("<script>"): template.index("</script>") + len("</script>")]
    return head, script


def render(spec: dict, contract: dict | None = None, model: str = "", hours: int = 2) -> str:
    esc = html.escape
    head, quiz_script = _template_parts()
    head = head.replace("{{JUDUL}}", esc(spec["title"]))
    quiz_json = json.dumps([{k: q[k] for k in ("q", "opts", "a", "why")} for q in spec["quiz"]],
                           ensure_ascii=False).replace("</", "<\\/")
    quiz_script = re.sub(r"var QUIZ = \[.*?\n  \];", lambda _m: f"var QUIZ = {quiz_json};", quiz_script, count=1, flags=re.S)
    chapters = spec["chapters"]
    all_terms = [t for c in chapters for t in c["terms"]]

    if contract:
        eyebrow = (f'<a href="{esc(contract["silabus_file"])}">Silabus {esc(contract["topic"])}</a> · '
                   f'Modul {contract["number"]} dari {contract["total"]}')
    else:
        eyebrow = "Materi belajar"
    # The lead starts with the main question; the card's question is added only when the lead asks none.
    lead = spec["lead"] if "?" in spec["lead"] or not spec["question"] else f'{spec["question"]} {spec["lead"]}'
    lead = lead.strip() or spec["title"]
    out = [head, "<main>\n<header class=\"hero\">", f'<p class="eyebrow">{eyebrow}</p>', f"<h1>{esc(spec['title'])}</h1>",
           f'<p class="lead">{esc(lead)}</p>',
           f'<ul class="chips"><li>± {hours} jam</li><li>{len(chapters)} bab</li><li>{len(spec["quiz"])} soal kuis</li></ul>',
           '<div class="goals"><strong>Setelah modul ini, Anda bisa:</strong><ul>'
           + "".join(f"<li>{esc(o)}</li>" for o in spec["objectives"]) + "</ul></div>"]
    if spec["prior"] and contract and contract["number"] > 1:
        out.append(f'<div class="howto"><strong>Bekal dari modul sebelumnya:</strong> {esc(spec["prior"])}</div>')
    main_terms = ", ".join(t["term"] for t in all_terms[:4])
    out.append('<div class="howto">Setiap bab dibagi menjadi tiga bagian: <strong>apa</strong> (pengertiannya), '
               '<strong>bagaimana</strong> (cara kerjanya), dan <strong>mengapa penting</strong>.'
               + (f" Istilah seperti {esc(main_terms)} sengaja tidak diterjemahkan karena memang itu yang dipakai "
                  "sehari-hari. Artinya dijelaskan di kotak istilah saat pertama muncul." if main_terms else "")
               + " Di akhir ada kuis dan latihan.</div>")
    toc = "".join(f'<li><a href="#bab{i}">{esc(c["title"])}</a></li>' for i, c in enumerate(chapters, 1))
    demo_html, demo_script = demo_block(spec["demo"])
    out.append(f'<ol class="toc">{toc}' + ('<li><a href="#demo-sec">Coba sendiri</a></li>' if demo_html else "")
               + '<li><a href="#rangkuman">Rangkuman</a></li><li><a href="#kuis">Cek pemahaman</a></li>'
               '<li><a href="#latihan">Latihan</a></li><li><a href="#kamus">Kamus istilah</a></li></ol>\n</header>')

    source_label = (contract or {}).get("source") or (
        f"Ditulis oleh {model} dari pengetahuan umum; periksa angka penting ke sumber resmi" if model else "")
    for i, c in enumerate(chapters, 1):
        terms = "".join(f'<div class="term"><b>{esc(t["term"])}</b>{esc(t["meaning"])}</div>' for t in c["terms"])
        figure = ""
        if len(c["steps"]) >= 2:
            figure = (f'<figure class="fig">{step_diagram(c["steps"], "Langkah: " + c["title"])}'
                      f"<figcaption>Urutan dari atas ke bawah; kotak teal adalah hasil akhirnya.</figcaption></figure>")
        out.append(f'<section id="bab{i}"><div class="chapter"><span class="num">{i}</span><h2>{esc(c["title"])}</h2></div>'
                   + (f'<p class="src">{esc(source_label)}</p>' if source_label else "")
                   + f'<h3>Apa</h3><p>{esc(c["what"])}</p>{terms}'
                   f'<h3>Bagaimana</h3><p>{esc(c["how"])}</p>{figure}'
                   f'<h3>Mengapa penting</h3><p>{esc(c["why"])}</p></section>')
    out.append(demo_html)

    n = len(chapters) + 1
    out.append(f'<section id="rangkuman"><div class="chapter"><span class="num">{n}</span><h2>Rangkuman</h2></div>'
               "<p>Kalau modul ini diringkas menjadi satu cerita:</p><ol>"
               + "".join(f"<li>{esc(s)}</li>" for s in spec["summary"]) + "</ol></section>")
    out.append(f'<section id="kuis"><div class="chapter"><span class="num">{n + 1}</span><h2>Cek pemahaman</h2></div>'
               "<p>Jawab tanpa melihat ke atas dulu. Kalau salah, penjelasannya menunjukkan bab mana yang perlu dibaca ulang.</p>"
               '<div class="quiz" id="quiz"></div><div id="quizscore" class="status no"></div>'
               '<div class="btns"><button type="button" id="quizretry" hidden>Ulangi kuis</button></div></section>')

    tasks = "".join(f'<div class="task"><b>{esc(e["title"])}</b>{esc(e["task"])}'
                    + (f'<p class="out">Hasil yang diharapkan: {esc(e["expected"])}</p>' if e["expected"] else "") + "</div>"
                    for e in spec["exercises"])
    if contract and contract.get("next"):
        nxt = contract["next"]
        next_box = (f'<div class="next"><strong>Berikutnya: Modul {contract["number"] + 1}, {esc(nxt.get("title", ""))}</strong>'
                    f'{esc(spec["next"] or nxt.get("question", ""))}</div>')
    elif contract:
        project = contract.get("project") or {}
        next_box = (f'<div class="next"><strong>Berikutnya: {esc(project.get("title") or "Proyek akhir")}</strong>'
                    f'{esc(project.get("task", ""))}</div>')
    else:
        next_box = f'<div class="next"><strong>Berikutnya</strong>{esc(spec["next"])}</div>' if spec["next"] else ""
    out.append(f'<section id="latihan"><div class="chapter"><span class="num">{n + 2}</span><h2>Latihan</h2></div>'
               f"{tasks}{next_box}</section>")

    gloss = "".join(f"<dt>{esc(t['term'])}</dt><dd>{esc(t['meaning'])}</dd>" for t in all_terms)
    money = ('<div class="note">Modul ini membahas cara kerja, bukan saran investasi. Halaman ini bukan saran keuangan.</div>'
             if spec["money_topic"] else "")
    out.append(f'<section id="kamus"><div class="chapter"><span class="num">{n + 3}</span><h2>Kamus istilah</h2></div>'
               f'<dl class="gloss">{gloss}</dl>{money}</section>\n</main>')
    if spec["sources"]:
        links = ", ".join(f'<a href="{esc(s["url"])}">{esc(s["title"])}</a>' for s in spec["sources"])
        footer = f"Sumber: {links}. Penjelasan ini disederhanakan untuk pembaca umum."
    else:
        footer = ("Penjelasan ini disederhanakan untuk pembaca umum."
                  + (f" Isi ditulis oleh {esc(model)} tanpa sumber tertulis; periksa angka dan nama penting." if model else ""))
    out.append(f"<footer>{footer}</footer>\n{quiz_script}{demo_script}\n</body>\n</html>\n")
    return "\n".join(out)


def build_materi(raw, filename: str, contract: dict | None = None, sources: list | None = None, model: str = "") -> dict:
    """Spec (dict or JSON text) -> lesson page.  Returns {"ok", "path", "warnings", "chapters", "questions", ...}."""
    try:
        data = raw if isinstance(raw, dict) else json.loads(raw)
        spec, warnings = normalize(data, contract, sources)
    except (ValueError, SpecError) as error:
        return {"ok": False, "error": str(error)}
    hours = int((contract or {}).get("hours") or 2)
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(spec, contract, model, hours), encoding="utf-8")
    return {"ok": True, "path": str(path), "warnings": warnings, "chapters": len(spec["chapters"]),
            "questions": len(spec["quiz"]), "exercises": len(spec["exercises"]),
            "terms": sum(len(c["terms"]) for c in spec["chapters"]),
            "diagrams": sum(1 for c in spec["chapters"] if len(c["steps"]) >= 2), "demo": len(spec["demo"]["steps"]) >= 3}


def format_result(res: dict) -> str:
    if not res.get("ok"):
        return f"GAGAL: {res.get('error')}"
    lines = [f"OK: {res['path']} ({res['chapters']} bab, {res['diagrams']} diagram, "
             f"{'1 demo' if res['demo'] else 'tanpa demo'}, {res['questions']} soal, {res['exercises']} latihan, "
             f"{res['terms']} istilah)"]
    lines += [f"     peringatan: {w}" for w in res.get("warnings", [])]
    return "\n".join(lines)


def read_sources(path: str | None) -> list:
    """Lines "Judul | URL"; blank lines and # lines are ignored."""
    if not path:
        return []
    sources = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        parts = [p.strip() for p in line.strip().split("|")]
        if not parts[0] or parts[0].startswith("#"):
            continue
        url = next((p for p in parts if URL.match(p)), "")
        sources.append({"title": next((p for p in parts if p and p != url), url), "url": url})
    return sources


def main() -> int:
    ap = argparse.ArgumentParser(description="Materi spec (JSON) -> lesson page.")
    ap.add_argument("spec")
    ap.add_argument("-o", "--output")
    ap.add_argument("--silabus", help="silabus JSON written by silabus_belajar (the module card is the contract)")
    ap.add_argument("--module", type=int, help="module number in the silabus")
    ap.add_argument("--sources", help='file with lines "Judul | URL"')
    ap.add_argument("--model", default="")
    args = ap.parse_args()
    raw = Path(args.spec).read_text(encoding="utf-8")
    try:
        contract = load_contract(args.silabus, args.module)
    except SpecError as error:
        print(f"GAGAL: {error}")
        return 2
    default = (f"{slugify(contract['topic'])}-modul-{contract['number']}.html" if contract
               else f"materi-{slugify(json.loads(raw).get('title', 'materi'))}.html")
    res = build_materi(raw, args.output or default, contract, read_sources(args.sources), args.model)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    print(format_result(res))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
