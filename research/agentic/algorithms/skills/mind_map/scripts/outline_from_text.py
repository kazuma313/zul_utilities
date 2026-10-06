"""Make a mind-map outline from raw text WITHOUT a language model (rule based).

    python scripts/outline_from_text.py lesson.txt > outline.md
    from outline_from_text import outline_from_text
    md = outline_from_text(text, max_branches=7, max_leaves=4)

How it works: headings, numbered titles and short stand-alone lines become the
branches; the sentences under each one are ranked by the words that are frequent
in the text but rare in general (no stop words), and the best ones become leaves,
shortened to their core clause.  Without any headings the text is split into
paragraphs and each paragraph becomes a branch named after its key words.
Quality is modest - it is a fallback and a starting point for a model to refine.
English and Indonesian stop words are built in.
"""

from __future__ import annotations

import math
import re
import sys
from collections import Counter

STOP = set("""
a an the and or but if of to in on at by for from with as is are was were be been being this that these those it its
into than then so such not no nor do does did done have has had having can could may might will would shall should
we you they he she i me my our your their them his her who whom which what when where why how all any each both few
more most other some very s t just also about over under out up down off again further once here there
yang dan di ke dari untuk pada dengan adalah ini itu atau juga tidak akan telah sudah dapat bisa karena sebagai oleh
para agar serta bahwa maka jika kami kita mereka dia ia saya anda nya lebih sangat hanya masih sudah namun tetapi
seperti antara secara dalam tentang terhadap bagi merupakan menjadi yaitu yakni ada suatu sebuah beberapa setiap
""".split())

_HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
_NUMBERED_TITLE = re.compile(r"^(?:[IVX]+[.)]|\d+(?:\.\d+)*[.)]?|[A-Z][.)])\s+([A-ZÀ-Þ][^.!?]{2,70})$")
_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+(.+)$")


def _words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-zA-ZÀ-ɏ][a-zA-ZÀ-ɏ'-]{2,}", text.lower()) if w not in STOP]


def _sentences(par: str) -> list[str]:
    par = re.sub(r"\s+", " ", par).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Þ0-9\"'(])", par)
    return [p.strip() for p in parts if len(p.strip()) > 15]


def _shorten(sentence: str, max_words: int = 7) -> str:
    s = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", sentence).strip()
    s = re.sub(r"\s*\([^)]{25,}\)", "", s)                       # long parentheses
    s = re.split(r"[;:]|\s[-–—]\s", s)[0]              # first clause
    s = re.sub(r"^(?:namun|tetapi|selain itu|oleh karena itu|dengan demikian|however|moreover|therefore|in addition|"
               r"for example|misalnya|contohnya)[, ]+", "", s, flags=re.I)
    words = s.split()
    if len(words) > max_words:
        cut = " ".join(words[:max_words])
        # prefer to end before a conjunction
        m = re.search(r"^(.*?)\s(?:yang|dan|atau|karena|sehingga|and|or|because|which|that|so)\s[^\s]*$", cut)
        s = (m.group(1) if m and len(m.group(1).split()) >= 4 else cut)
        ws = s.split()
        while len(ws) > 3 and ws[-1].lower().strip(",.") in STOP:   # never end on "bagi", "dari", "the" ...
            ws.pop()
        s = " ".join(ws)
    return s.rstrip(" .,;:").strip()


def _is_title_line(line: str, next_line: str) -> bool:
    t = line.strip()
    if not t or len(t) > 70 or t.endswith((".", ",", ";")):
        return False
    if _NUMBERED_TITLE.match(t):
        return True
    words = t.split()
    caps = sum(1 for w in words if w[:1].isupper())
    if len(words) <= 8 and (t.isupper() or t.endswith(":") or caps >= max(1, len(words) - 2)) and next_line.strip():
        return True
    return False


def _sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    """(title, [(heading, body)]) from headings / title lines; body = text until next heading."""
    lines = text.splitlines()
    title = ""
    sections: list[tuple[str, list[str]]] = []
    cur_head, cur = None, []
    first = next((ln.strip() for ln in lines if ln.strip()), "")
    if first and len(first.split()) <= 10 and not first.endswith((".", ",", ";", ":")) and not _BULLET.match(first) \
            and not _HEADING.match(first):
        title = first
        lines = lines[lines.index(next(ln for ln in lines if ln.strip())) + 1:]
    for i, ln in enumerate(lines):
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        hm = _HEADING.match(ln.strip())
        head = None
        if hm:
            head = hm.group(2).strip()
            if hm.group(1) == "#" and not title and not sections:
                title = head
                continue
        elif _is_title_line(ln, nxt) and (not _BULLET.match(ln) or _NUMBERED_TITLE.match(ln.strip())):
            head = re.sub(r"^(?:[IVX]+[.)]|\d+(?:\.\d+)*[.)]?|[A-Z][.)])\s+", "", ln.strip()).rstrip(":")
            if not title and not sections and not cur:
                title = head
                continue
        if head is not None:
            if cur_head is not None or cur:
                sections.append((cur_head or "", cur))
            cur_head, cur = head, []
        else:
            cur.append(ln)
    if cur_head is not None or cur:
        sections.append((cur_head or "", cur))
    return title, [(h, "\n".join(b)) for h, b in sections]


def _keywords(text: str, n: int = 3) -> list[str]:
    c = Counter(_words(text))
    return [w for w, _ in c.most_common(n)]


def outline_from_text(text: str, max_branches: int = 7, max_leaves: int = 4, root: str | None = None) -> str:
    text = text.strip()
    if not text:
        return "# Mind map\n"
    doc_freq = Counter(_words(text))
    title, secs = _sections(text)
    if len([s for s in secs if s[0]]) < 2:
        # no usable headings: paragraphs become branches
        pars = [p for p in re.split(r"\n\s*\n", text) if len(p.split()) >= 12]
        secs = []
        for p in pars:
            kws = _keywords(p, 3)
            head = " ".join(w.capitalize() for w in kws[:2]) or _shorten(_sentences(p)[0] if _sentences(p) else p, 5)
            secs.append((head, p))
    secs = [(h, b) for h, b in secs if b.strip() or h]
    # rank sections by amount of content, keep order of the strongest ones
    scored = sorted(range(len(secs)), key=lambda i: -len(secs[i][1]))[:max_branches]
    keep = sorted(scored)
    root_text = root or title or " ".join(w.capitalize() for w in _keywords(text, 2)) or "Mind map"
    out = [f"# {root_text}"]
    for i in keep:
        head, body = secs[i]
        out.append(f"- {head or _shorten(_sentences(body)[0], 6) if body else head}")
        bullets = [_BULLET.match(ln).group(1) for ln in body.splitlines() if _BULLET.match(ln)]
        if bullets:
            leaves = [_shorten(b) for b in bullets[:max_leaves]]
        else:
            sents = [s for par in re.split(r"\n\s*\n", body) for s in _sentences(par)]
            head_words = set(_words(head))

            def score(s):
                ws = _words(s)
                if not ws:
                    return 0
                sc = sum(math.log(1 + doc_freq[w]) for w in ws) / math.sqrt(len(ws))
                sc += 0.6 * len(head_words & set(ws))
                return sc
            ranked = sorted(range(len(sents)), key=lambda k: -score(sents[k]))[:max_leaves]
            leaves = [_shorten(sents[k]) for k in sorted(ranked)]
        seen = set()
        for lf in leaves:
            key = lf.lower()
            if lf and key not in seen and key != head.lower():
                seen.add(key)
                out.append(f"  - {lf}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    from extract_text import read_source
    # usage: outline_from_text.py SOURCE [-o OUTLINE.md]   (other options are ignored: an agent often guesses some)
    argv, target = sys.argv[1:], None
    if "-o" in argv[:-1] or "--output" in argv[:-1]:
        at = argv.index("-o") if "-o" in argv else argv.index("--output")
        target = argv[at + 1]
        del argv[at:at + 2]
    sources = [a for a in argv if not a.startswith("-")]
    if not sources:
        print(__doc__)
        sys.exit(2)
    sys.stdout.reconfigure(encoding="utf-8")
    outline = outline_from_text(read_source(sources[0]))
    if target:
        with open(target, "w", encoding="utf-8") as f:
            f.write(outline)
        print(f"OK: outline written to {target}")
    else:
        print(outline)
