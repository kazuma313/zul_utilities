"""Repairs for outlines written by small local models.  Python standard library only.

Every function here fixes a failure that was seen while running the skill against live
models (qwen3:8b, qwen3:4b, gemma3:4b through Ollama) - see references/small_models.md:

    last_outline_block(raw)      the reply "thinks aloud": rules repeated, a draft, then the real outline
    outline_problem(root)        the reply was drawn although it was prose, or one branch held everything
    group_branches(root, ask)    13 main branches: the model sorts them into groups, the script rebuilds the tree
    shorten_texts(root, ask)     sentences copied from the source: the model shortens them, matched by number
    take_notes(text, ask)        the source is longer than one request: notes on each part instead of a cut-off
    stepwise_outline(...)        a 4B model cannot structure a document in one answer: branch names first,
                                 then the key points of each branch, and the script puts the outline together

`ask(system, user, max_tokens) -> str` is all they need from the caller.  The model is only
asked for short, easy answers (a list of numbers, a few keywords); the tree is rebuilt in Python.
"""

from __future__ import annotations

import re

if __package__:
    from .outline_parser import _BULLET, _HEADING, MAX_BRANCHES, _clean_text
else:
    from outline_parser import _BULLET, _HEADING, MAX_BRANCHES, _clean_text

_THINK = re.compile(r"<think>.*?</think>", re.S | re.I)
_FENCE = re.compile(r"^\s*(?:```|~~~)")
_GROUP_LINE = re.compile(r"^\s*(?:[-*]\s*)?(.+?)\s*:\s*((?:\d+\s*,?\s*)+)$")
_GROUP_WORD = re.compile(r"^(?:group(?:\s+name)?|kelompok|grup)\s*\d*\s*[:.-]\s*", re.I)

GROUP_PROMPT = """Sort the numbered topics into 3 to 6 groups of related topics.
Reply with one line per group: a name of 1 to 4 words, a colon, then the numbers of its topics. For example:

Coffee beans: 1, 3, 4
Brewing methods: 2, 5, 6

Write the names in the language of the topics. Use every number exactly once. Reply with those lines only."""

SHORTEN_PROMPT = """Shorten each line to a keyword phrase of at most 6 words.
Keep the language and the key terms of the line. Drop markdown, links and code.
Reply with one line per item, in the same order, as "number. short phrase". Reply with those lines only."""

NOTES_PROMPT = """You take notes on one part of a longer text.
Reply with the 2 to 4 topics of this part. Under each topic, list 2 to 4 keywords: names, numbers and terms taken from the text.
Use exactly this format, with a real topic name of 1 to 4 words:

- Coffee beans
  - arabica
  - robusta

Write in the language of the text. Reply with the list only."""

BRANCHES_PROMPT = """You name the main branches of a mind map.
Reply with one branch name per line, 1 to 4 words each. No numbering, no explanation, nothing else."""

POINTS_PROMPT = """You list the key points of ONE branch of a mind map.
Reply with 2 to 4 lines. Each line is a keyword phrase of at most 6 words: a name, a number, a step, a cause, an example.
Never a sentence, no numbering, no explanation, nothing else.

Example for the branch "Bahan" of a mind map about photosynthesis:
Cahaya matahari
Air dari akar
CO2 dari stomata"""


def _in(language: str) -> str:
    """A first line for a request that names the language; small models otherwise drift to English."""
    return f"Write in {language}.\n\n" if language else ""


def _all_nodes(root: dict) -> list[dict]:
    found, todo = [], list(root.get("children") or [])
    while todo:
        node = todo.pop()
        found.append(node)
        todo += node.get("children") or []
    return found


def _is_sentence(text: str) -> bool:
    return len(text.split()) > 8 or len(text) > 70


def outline_problem(root: dict) -> str:
    """'' when the tree looks like a mind map, else what is wrong with it.

    The parser turns any text into a tree, so "a file was written" says nothing about the map.  Seen
    with 4B models: the model's reasoning drawn as 60 nodes, and a document drawn as eight bare
    sentences plus one branch that held everything else.
    """
    nodes, kids = _all_nodes(root), root.get("children") or []
    if len(nodes) < 3:
        return "fewer than 4 nodes"
    if _is_sentence(root.get("text", "")):
        return "the central topic is a sentence"
    sentences = sum(_is_sentence(n.get("text", "")) for n in nodes)
    if sentences * 4 > len(nodes):
        return f"{sentences} of {len(nodes)} lines are sentences, not keyword phrases"
    if len(kids) < 2:
        return "fewer than 2 main branches"
    bare = sum(not k.get("children") for k in kids)
    if len(nodes) >= 8 and bare * 2 > len(kids):
        return f"{bare} of {len(kids)} main branches have no sub points"
    return ""


def last_outline_block(raw: str) -> str:
    """The last '# title' that is followed by at least two bullets, up to the first line that is not outline.

    Some small models write their reasoning into the answer (no <think> tags): the rules again, the
    example, one or two drafts, then the outline, then a remark.  A reply without such a block, and
    JSON, is returned unchanged.
    """
    text = _THINK.sub("", raw)
    if not text.strip() or text.lstrip().startswith(("{", "[")):
        return raw
    lines = text.splitlines()

    def level(line: str) -> int:
        m = _HEADING.match(line.strip())
        return len(m.group(1)) if m else 0

    for start in reversed(range(len(lines))):
        if level(lines[start]) != 1:
            continue
        block, bullets = [lines[start].strip()], 0
        indent = len(lines[start]) - len(lines[start].lstrip())
        for line in lines[start + 1:]:
            if _BULLET.match(line.replace("\t", "    ")) or level(line) > 1:
                bullets += 1
            elif line.strip() and not _FENCE.match(line) and bullets:
                break
            block.append(line[indent:] if line[:indent].strip() == "" else line)
        if bullets >= 2:
            return "\n".join(block)
    return raw


def group_branches(node: dict, ask, limit: int = MAX_BRANCHES, language: str = "") -> bool:
    """Ask the model to sort the children of `node` into groups; rebuild the tree from its answer.

    Returns False and leaves the tree alone when there is nothing to group or the answer is unusable.
    A group with one member is not created: the member keeps its place.
    """
    kids = node.get("children") or []
    if len(kids) <= limit:
        return False
    listing = "\n".join(f"{i}. {k['text']}" for i, k in enumerate(kids, 1))
    reply = _THINK.sub("", ask(GROUP_PROMPT, _in(language) + listing, 400))
    grouped, placed = [], set()
    for line in reply.splitlines():
        m = _GROUP_LINE.match(re.sub(r"[*`]+", "", line))
        if not m:
            continue
        numbers = [int(n) for n in re.findall(r"\d+", m.group(2))]
        numbers = list(dict.fromkeys(n for n in numbers if 1 <= n <= len(kids) and n not in placed))
        placed.update(numbers)
        members = [kids[n - 1] for n in numbers]
        if len(members) == 1:
            grouped.append(members[0])
        elif members:
            name = _clean_text(_GROUP_WORD.sub("", m.group(1).strip()))
            grouped.append({"text": name or members[0]["text"], "children": members})
    grouped += [k for i, k in enumerate(kids, 1) if i not in placed]
    if not 2 <= len(grouped) <= limit:
        return False
    node["children"] = grouped
    return True


def shorten_texts(root: dict, ask, max_chars: int = 60, max_words: int = 8, language: str = "") -> int:
    """Ask the model to turn sentence-long node texts into keyword phrases; returns how many were changed.

    A small model given a source text copies sentences into the map (seen with qwen3:8b: 7 of 30 nodes).
    The texts go out as a numbered list and come back by number, so one bad line cannot damage the tree.
    A text the model does not answer, or answers no shorter, is left for the parser to cut.
    """
    long_nodes = []

    def walk(node):
        text = node.get("text", "")
        if len(text) > max_chars or len(text.split()) > max_words:
            long_nodes.append(node)
        for kid in node.get("children") or []:
            walk(kid)
    walk(root)
    long_nodes = long_nodes[:40]
    if not long_nodes:
        return 0
    listing = "\n".join(f"{i}. {n['text']}" for i, n in enumerate(long_nodes, 1))
    reply = _THINK.sub("", ask(SHORTEN_PROMPT, _in(language) + listing, 900))
    changed = 0
    for line in reply.splitlines():
        m = re.match(r"^\s*(\d+)[.)]\s*(.+?)\s*$", line)
        if not m or not 1 <= int(m.group(1)) <= len(long_nodes):
            continue
        node, text = long_nodes[int(m.group(1)) - 1], _clean_text(m.group(2))
        if text and len(text) < len(node["text"]) and len(text) <= max_chars:
            node["text"] = text
            changed += 1
    return changed


def split_text(text: str, limit: int) -> list[str]:
    """Cut a long text at paragraph breaks into parts of at most `limit` characters."""
    parts, current = [], ""
    for para in re.split(r"\n\s*\n", text.strip()):
        while len(para) > limit:
            parts.append(para[:limit])
            para = para[limit:]
        if current and len(current) + len(para) + 2 > limit:
            parts.append(current)
            current = ""
        current = f"{current}\n\n{para}" if current else para
    if current:
        parts.append(current)
    return parts


def take_notes(text: str, ask, part_chars: int, progress=None) -> str:
    """Notes on every part of a long text ('- topic' with indented keywords), joined into one list."""
    parts = split_text(text, part_chars)
    notes = []
    for i, part in enumerate(parts, 1):
        if progress:
            progress(f"reading part {i} of {len(parts)}")
        notes.append(_THINK.sub("", ask(NOTES_PROMPT, part, 500)).strip())
    return "\n".join(notes)


_PROSE_START = re.compile(r"^(okay|ok|oke|wait|hmm|let me|let's|lets|the user|sure)\b|^(here|berikut)\s+(is|are|adalah)\b", re.I)


def short_lines(reply: str, limit: int, max_words: int = 6) -> list[str]:
    """The usable lines of a reply that should be a few short phrases.

    List markers are stripped; headings ("Main branches:"), prose, questions and repeats are dropped.
    """
    lines, seen = [], set()
    for raw in _THINK.sub("", reply).splitlines():
        if raw.strip().endswith((":", "?")) or _FENCE.match(raw):
            continue
        text = _clean_text(raw.strip().lstrip("#").strip()).rstrip(".")
        if not text or len(text.split()) > max_words or _PROSE_START.match(text) or text.casefold() in seen:
            continue
        seen.add(text.casefold())
        lines.append(text)
    return lines[:limit]


def stepwise_outline(title: str, material: str, ask, branches: int = 6, language: str = "", sections=(),
                     progress=None) -> str:
    """Build the outline from several small answers: the branch names, then the key points of each branch.

    One answer per question is short enough for a 4B model, and the shape of the tree no longer depends
    on the model: every branch gets its own 2-4 points.  The material is the first thing in every
    request, so the server can reuse its work on it.  Returns '' when the model names no branches.
    """
    context = f"MATERIAL:\n<<<\n{material}\n>>>\n\n" if material else ""
    wish = f"Language: {language}\n" if language else ""
    hint = f"Sections of the material: {'; '.join(sections)}\n" if sections else ""
    source = "taken from the material" if material else "about the topic"

    def lines_for(system, user, limit, max_words):
        found = short_lines(ask(system, user, 300), limit, max_words)
        if len(found) < 2:                   # a model that can only answer after thinking: let it think
            found = short_lines(ask(system, user, 1500, think="auto"), limit, max_words)
        return found

    names = lines_for(BRANCHES_PROMPT, f"{context}Central topic: {title}\n{hint}{wish}"
                      f"Name {max(3, branches - 2)} to {branches} main branches that cover the whole of it.", branches, 5)
    if len(names) < 2:
        return ""
    outline = [f"# {title}"]
    for i, name in enumerate(names, 1):
        if progress:
            progress(f"branch {i} of {len(names)}: {name}")
        # Sentences are kept here (up to 20 words): the caller shortens them, which loses less than
        # dropping them.  gemma3:4b answers this question in sentences more often than not.
        points = lines_for(POINTS_PROMPT, f"{context}Central topic: {title}\nBranch: {name}\n{wish}"
                           f"List 2 to 4 key points of this branch, {source}.", 4, 20)
        outline.append(f"- {name}")
        outline += [f"  - {p}" for p in points if p.casefold() != name.casefold()]
    return "\n".join(outline) + "\n"
