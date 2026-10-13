"""Text / file / topic -> mind map with a LOCAL model (Ollama, LM Studio, llama.cpp server, vLLM ...).

The model writes a Markdown OUTLINE (headings + indented bullets) - the format
small models produce most reliably - and build_mindmap.py draws it.  With
--no-llm the rule-based outline_from_text.py is used instead (no model at all).

    python scripts/generate_mindmap.py lesson.pdf -o lesson.png --also svg,md
    python scripts/generate_mindmap.py "Sistem pencernaan manusia" -o pencernaan.svg
    python scripts/generate_mindmap.py article.txt --api openai --base-url http://localhost:1234/v1 --model <id>
    python scripts/generate_mindmap.py notes.docx --no-llm -o notes.svg

Input may be a file (.txt .md .pdf .docx .html), a folder of such files, or a
topic / pasted text.  A source longer than --max-chars is read in parts: the model
takes notes on each part and the map is built from the notes, so the end of a long
text is not lost (--long-source cut restores the old cut-off).

How the outline is obtained (scripts/outline_repair.py has the details):

  1. one answer    the model writes the whole outline; the last outline of a reply that thinks
                   aloud is taken, too many branches are grouped, sentence-long lines are shortened
  2. again         if that is not a usable map (prose, one branch holding everything), once more
  3. step by step  still not usable: the model names the branches, then the key points of each
                   branch, and the script puts the outline together (--steps always | auto | never)
  4. rule based    a source file still gets a map from outline_from_text.py, with a warning

--verbose prints every model reply.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_mindmap import SKILL_DIR, build_mindmap, format_result  # noqa: E402
from extract_text import read_source  # noqa: E402
from outline_from_text import outline_from_text  # noqa: E402
from outline_parser import _merge_repeats, _strip_wrappers, parse_outline, to_outline  # noqa: E402
from outline_repair import (  # noqa: E402
    group_branches, last_outline_block, outline_problem, shorten_texts, stepwise_outline, take_notes)

PROMPT_DIR = SKILL_DIR / "assets" / "prompts"
LONGEST_SOURCE = 400_000     # characters; a longer source is cut here even in notes mode
DEFAULT_LANGUAGE = "the same language as the source"
REMINDER = ("\n\nThe previous answer was not a usable outline. Return ONLY the outline: '# root' then '- ' bullets "
            "indented by two spaces, every line a short keyword phrase.")


def _post(url, payload, api_key, timeout):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# Models for mind maps, best first, from the skill pool's comparison (REQUIREMENTS.md, evals/compare_models.py):
# gemma3:4b drew 16 of 16 test maps in 8-98 s and kept the detail of a document; qwen3:8b left
# details out; qwen3:4b needs the schema path.
RECOMMENDED = ("gemma3:4b", "qwen3:8b", "qwen3:4b")
USE_CASE = "mind maps"

def _same_model(installed: str, wanted: str) -> bool:
    """qwen3:8b is qwen3:8b, qwen3:8b-q4_K_M, library/qwen3:8b and LM Studio's qwen/qwen3-8b."""
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())  # noqa: E731
    return norm(installed.split("/")[-1]).startswith(norm(wanted))


def choose_model(args) -> str:
    """The model to use when --model is auto: the first of RECOMMENDED that the server has.

    SKILL_MODEL in the environment names one model for every skill.  Without the recommended models the
    first installed chat model is used, and without a server the first recommended name is returned, so
    the request that follows reports what is missing.
    """
    if os.environ.get("SKILL_MODEL"):
        return os.environ["SKILL_MODEL"]
    base = (args.base_url or ("http://localhost:11434" if args.api == "ollama" else "http://localhost:1234/v1")).rstrip("/")
    req = urllib.request.Request(base + ("/api/tags" if args.api == "ollama" else "/models"),
                                 headers={"Authorization": f"Bearer {args.api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            listing = json.loads(resp.read().decode("utf-8"))
    except (OSError, ValueError):
        return RECOMMENDED[0]
    names = [m.get("name") or m.get("id") or "" for m in listing.get("models") or listing.get("data") or []]
    names = [n for n in names if n and "embed" not in n.lower()]
    return next((n for want in RECOMMENDED for n in names if _same_model(n, want)), names[0] if names else RECOMMENDED[0])


def detect_think(args) -> str:
    """'off' when the model answers plainly with reasoning switched off, else 'on'.

    Some models can only answer after reasoning (qwen3:4b).  Told not to think, they write the
    reasoning into the answer itself: "Okay, let's see. The user wants ...".  One tiny question
    shows which kind of model this is; a model that needs to think is then allowed to, and the
    server keeps its reasoning out of the answer.
    """
    probe = argparse.Namespace(**{**vars(args), "think": "off", "verbose": False})
    reply = ask_model(probe, "Reply with exactly one word.", "Say: ready", 30)
    return "off" if len(reply.split()) <= 3 else "on"


OUTLINE_SCHEMA = {
    "type": "object",
    "properties": {
        "root": {"type": "string"},
        "nodes": {"type": "array", "minItems": 3, "maxItems": 8, "items": {
            "type": "object",
            "properties": {"text": {"type": "string"},
                           "children": {"type": "array", "minItems": 2, "maxItems": 6, "items": {
                               "type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
            "required": ["text", "children"]}},
    },
    "required": ["root", "nodes"],
}
JSON_SYSTEM = ("You turn a topic or a source text into a mind map outline, written as JSON.\n"
               "root: the central topic, 2 to 6 words. nodes: the 3 to 8 main branches. children: 2 to 6 points of that branch.\n"
               "Every text is a keyword phrase of at most 8 words, never a sentence. Keep the numbers and names of the source.\n"
               "Use only facts from the source, and write in the language that is asked for.")


def outline_from_json(reply: str) -> str:
    """The schema answer {"root", "nodes": [{"text", "children": [{"text"}]}]} as a Markdown outline ('' if unusable)."""
    try:
        data = json.loads(_strip_wrappers(reply))
    except ValueError:
        return ""
    if not isinstance(data, dict):
        return ""
    lines = [f"# {str(data.get('root') or '').strip() or 'Mind map'}"]
    for node in data.get("nodes") or []:
        if isinstance(node, dict) and str(node.get("text") or "").strip():
            lines.append(f"- {str(node['text']).strip()}")
            lines += [f"  - {str(c['text']).strip()}" for c in node.get("children") or []
                      if isinstance(c, dict) and str(c.get("text") or "").strip()]
    return "\n".join(lines) if len(lines) > 1 else ""


def ask_model(args, system, user, max_tokens=None, think=None, schema=None) -> str:
    """One request to the model.  `think` overrides --think for this request ("auto" = the model decides).

    With `schema` the server only lets the model write JSON of that shape, and reasoning is switched off.
    """
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    limit, think, num_ctx = max_tokens or args.max_tokens, "off" if schema else think or args.think, args.num_ctx
    if think != "off":
        # The reasoning is counted too: it needs room in the answer and in the context window.  Without
        # it qwen3:4b reasoned until the window was full and returned an empty answer.
        limit, num_ctx = limit * 3, max(num_ctx, 16384)
    if args.api == "ollama":
        payload = {"model": args.model, "stream": False, "messages": msgs,
                   "options": {"temperature": args.temperature, "num_ctx": num_ctx, "num_predict": limit}}
        if schema:
            payload["format"] = schema
        if think != "auto":
            payload["think"] = think == "on"
        base = args.base_url or "http://localhost:11434"
        try:
            data = _post(base.rstrip("/") + "/api/chat", payload, args.api_key, args.timeout)
        except urllib.error.HTTPError as e:
            if e.code != 400:
                raise
            payload.pop("think", None)       # a model without a thinking mode rejects the switch
            data = _post(base.rstrip("/") + "/api/chat", payload, args.api_key, args.timeout)
        reply = data.get("message", {}).get("content", "")
    else:
        payload = {"model": args.model, "temperature": args.temperature, "max_tokens": limit, "messages": msgs}
        if think == "off":
            payload["reasoning_effort"] = "none"
        if schema:
            payload["response_format"] = {"type": "json_schema", "json_schema": {"name": "outline", "strict": True, "schema": schema}}
        base = args.base_url or "http://localhost:1234/v1"
        try:
            data = _post(base.rstrip("/") + "/chat/completions", payload, args.api_key, args.timeout)
        except urllib.error.HTTPError as e:
            if e.code not in (400, 422) or not {"reasoning_effort", "response_format"} & set(payload):
                raise
            payload.pop("reasoning_effort", None)   # a server that does not know a switch rejects it
            payload.pop("response_format", None)
            data = _post(base.rstrip("/") + "/chat/completions", payload, args.api_key, args.timeout)
        reply = data["choices"][0]["message"].get("content") or ""
    if args.verbose:
        print("--- model reply ---", reply.strip(), "---", sep="\n", file=sys.stderr)
    return reply


def problem_of(outline: str) -> str:
    """'' when the outline is worth drawing, else what is wrong with it (JSON is left to the parser)."""
    text = _strip_wrappers(outline)
    if not text:
        return "the model answered nothing"
    if text.startswith(("{", "[")):
        return ""
    return outline_problem(parse_outline(text)["root"])


def repair(raw: str, ask, notes: list[str], language: str = "") -> str:
    """The model's reply -> the outline to draw.  Every change is added to `notes`."""
    outline = last_outline_block(raw)
    text = _strip_wrappers(outline)
    if not text or text.startswith(("{", "[")):          # nothing, or JSON: the parser handles it
        return raw
    root = parse_outline(text)["root"]
    if not root.get("children"):
        return outline
    _merge_repeats(root, notes.append)
    branches = len(root["children"])
    changed = len(notes) > 0
    if outline_problem(root).startswith("the central topic"):
        return outline                       # the root itself is prose: nothing here is worth repairing
    if group_branches(root, ask, language=language):
        notes.append(f"{branches} main branches -> grouped into {len(root['children'])} by the model")
        changed = True
    shortened = shorten_texts(root, ask, language=language)
    if shortened:
        notes.append(f"{shortened} sentence-long lines -> shortened by the model")
        changed = True
    if not changed:
        return outline
    root["text"] = root.get("text") or "Mind map"
    return to_outline(root)


def source_title(text: str, draft: str, source: str) -> str:
    """The central topic of a source: its first heading, else the file name, else the root of the rule-based draft."""
    for line in text.splitlines()[:40]:
        if line.startswith("#") and line.lstrip("#").strip():
            return line.lstrip("#").strip(" *_`")
    if len(source) < 300 and "\n" not in source and Path(source).suffix:
        return Path(source).stem.replace("_", " ").replace("-", " ")
    return draft.splitlines()[0].lstrip("# ").strip() if draft.strip() else "Mind map"


_ID_WORDS = set("yang dan di dengan untuk ini itu tidak adalah dari pada juga atau akan karena jika sudah lebih".split())
_EN_WORDS = set("the and of to is that with for are this it not from which can will because if more".split())
_CODE = re.compile(r"```.*?```|~~~.*?~~~", re.S)


def guess_language(text: str) -> str | None:
    """'Indonesian' or 'English' when the source is clearly one of them.

    Named explicitly in the request, the language is kept; left to "the language of the source",
    qwen3:8b drifts to English for Indonesian material that is full of English identifiers.
    """
    words = re.findall(r"[a-z]+", text[:20000].lower())
    indonesian, english = sum(w in _ID_WORDS for w in words), sum(w in _EN_WORDS for w in words)
    if indonesian > 2 * english and indonesian >= 5:
        return "Indonesian"
    if english > 2 * indonesian and english >= 5:
        return "English"
    return None


def source_plan(args, text: str, ask) -> dict:
    """What to ask about a source text.

    `user` is the request for the whole outline in one answer.  `title`, `material`, `sections` and
    `language` are the same things in pieces, for the step-by-step path.  `material` is the text
    itself, or notes on its parts when the text is longer than one request.
    """
    language = args.language
    if language == DEFAULT_LANGUAGE:
        language = guess_language(text) or language
    text = _CODE.sub("", text)               # code and diagrams are noise in a mind map (and in the draft)
    draft = outline_from_text(text, max_branches=args.branches)
    sections = [ln[2:].strip() for ln in draft.splitlines() if ln.startswith("- ")]
    sections = [s for s in sections if re.search(r"[^\W\d_]{3}", s) and not re.search(r"[|<>{}=`]|-->", s)]
    sections = sections if len(sections) >= 2 else []
    title = source_title(text, draft, args.source)
    head = (f"Central topic: {title}\nNumber of main branches: {args.branches}\n"
            f"Levels below the root: {args.depth}\nLanguage: {language}\n")
    tail = "Return only the outline. Every line is a keyword phrase of at most 8 words, never a sentence copied from the source."
    if len(text) > args.max_chars and args.long_source == "notes":
        material = take_notes(text, ask, args.max_chars, progress=lambda m: print(m, file=sys.stderr))
        user = (f"{head}\nThe source is long, so it was read in parts. NOTES ON EACH PART:\n<<<\n{material}\n>>>\n\n"
                f"Group the notes into the main branches and merge notes about the same topic. {tail}")
    else:
        # Only the section names of the rule-based draft are passed on.  Given the whole draft, an 8B model
        # copies its sentences (and its table rows and code fences) into the map instead of summarising.
        material = text[:args.max_chars]
        hint = f"Sections found in the source: {'; '.join(sections)}\n" if sections else ""
        user = f"{head}{hint}\nSOURCE TEXT:\n<<<\n{material}\n>>>\n\n{tail}"
    return {"user": user, "title": title, "material": material, "sections": sections, "language": language}


def source_request(args, text: str, ask) -> str:
    return source_plan(args, text, ask)["user"]


def write_outline(args, system: str, plan: dict, ask) -> tuple[str, list[str], str]:
    """Get an outline from the model.  Returns (outline, notes, problem); problem is '' when it is usable."""
    outline, notes, problem = "", [], "the model was not asked"
    if getattr(args, "schema_first", False):
        # A model that only answers after reasoning needs minutes for a topic, and on a document qwen3:4b
        # reasoned until no room was left for the answer.  Held to a JSON schema it writes the outline
        # at once; the stages below remain for an answer that is not usable.
        outline = outline_from_json(ask(JSON_SYSTEM, plan["user"], None, "off", OUTLINE_SCHEMA))
        problem = problem_of(outline) if outline else "the model answered nothing"
        if not problem:
            return outline, ["outline written as JSON held to a schema (this model answers plain text only after long reasoning)"], ""
        print(f"schema outline: {problem}", file=sys.stderr)
    if args.steps != "always":
        for attempt in range(args.retries + 1):
            # A model that can only answer after thinking writes its reasoning into the answer when
            # thinking is switched off (seen with qwen3:4b).  So the second attempt lets the model decide.
            think = "auto" if attempt and args.think == "off" else None
            notes = []
            reply = ask(system, plan["user"] + (REMINDER if attempt else ""), None, think)
            outline = repair(reply, ask, notes, plan["language"])
            problem = problem_of(outline)
            if not problem:
                return outline, notes, ""
            print(f"attempt {attempt + 1}: {problem}", file=sys.stderr)
    if args.steps != "never":
        print("building the outline step by step", file=sys.stderr)
        stepped = stepwise_outline(plan["title"], plan["material"], ask, branches=args.branches,
                                   language=plan["language"], sections=plan["sections"],
                                   progress=lambda m: print(m, file=sys.stderr))
        step_notes = [f"outline built step by step ({problem})" if args.steps == "auto" else "outline built step by step"]
        stepped = repair(stepped, ask, step_notes, plan["language"]) if stepped else ""
        if stepped and not problem_of(stepped):
            return stepped, step_notes, ""
        if stepped and not outline:
            outline, problem = stepped, problem_of(stepped)
    return outline, notes, problem


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="file, folder, topic or pasted text")
    ap.add_argument("-o", "--output", default="mindmap.svg", help=".svg .png .pdf .html .md .mmd")
    ap.add_argument("--also", default="", help="extra formats, comma separated")
    ap.add_argument("--api", choices=["ollama", "openai"], default="ollama")
    ap.add_argument("--base-url")
    ap.add_argument("--model", default="auto",
                    help="auto (default): the first of gemma3:4b, qwen3:8b, qwen3:4b that the server has")
    ap.add_argument("--api-key", default="local")
    ap.add_argument("--no-llm", action="store_true", help="rule-based outline only (no model)")
    ap.add_argument("--branches", type=int, default=6, help="target number of main branches (3-8)")
    ap.add_argument("--depth", type=int, default=3, help="levels below the root (2-4)")
    ap.add_argument("--language", default=DEFAULT_LANGUAGE,
                    help="for example Indonesian; by default Indonesian and English sources are recognised")
    ap.add_argument("--theme", help="rainbow | blue | pastel | dark | mono")
    ap.add_argument("--layout", help="radial | right")
    ap.add_argument("--title", help="caption in the corner")
    ap.add_argument("--max-chars", type=int, default=12000, help="source characters per request")
    ap.add_argument("--long-source", choices=["notes", "cut"], default="notes",
                    help="a source longer than --max-chars: notes on each part (default) or cut it off")
    ap.add_argument("--steps", choices=["auto", "always", "never"], default="auto",
                    help="build the outline step by step: when one answer is not usable (default), always, or never")
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--num-ctx", type=int, default=8192, help="Ollama context window")
    ap.add_argument("--think", choices=["detect", "auto", "on", "off"], default="detect",
                    help="reasoning mode of the model. detect (default): off when the model can answer without "
                         "reasoning, which is about ten times faster, and on when it cannot")
    ap.add_argument("--qwen-no-think", action="store_true")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--retries", type=int, default=1, help="extra attempts for the one-answer outline")
    ap.add_argument("--save-outline", help="write the model's outline to this file")
    ap.add_argument("--verbose", action="store_true", help="print every model reply")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if args.model == "auto" and not args.no_llm:
        args.model = choose_model(args)
        print(f"model: {args.model} (recommended for {USE_CASE}; --model or SKILL_MODEL chooses another)", file=sys.stderr)

    if not Path(args.source).exists() and re.fullmatch(r"[\w.-]+\.(md|txt|pdf|docx|html?)", args.source):
        # An agent asked for a topic often passes a file name it made up ("bills-to-law.md"): read it as the topic.
        args.source = re.sub(r"[-_.]+", " ", Path(args.source).stem).strip()
    try:
        text = read_source(args.source, max_chars=LONGEST_SOURCE)
    except Exception as e:
        print(f"ERROR: cannot read {args.source}: {e}")
        return 2
    is_source = (Path(args.source).exists() and len(args.source) < 1000) or len(text) > 200
    also = [x for x in args.also.split(",") if x]
    out = Path(args.output)
    out_name = str(out if out.is_absolute() else Path.cwd() / out)

    def draw(outline):
        return build_mindmap(outline, out_name, theme=args.theme, layout=args.layout, title=args.title, also=also)

    if args.no_llm:
        text = text[:args.max_chars]
        outline = outline_from_text(text, max_branches=args.branches) if is_source else f"# {text}\n"
        if args.save_outline:
            Path(args.save_outline).write_text(outline, encoding="utf-8")
        res = draw(outline)
        print(format_result(res))
        return 0 if res["ok"] else 1

    def ask(system, user, max_tokens=None, think=None, schema=None):
        return ask_model(args, system, user, max_tokens, think, schema)

    system = (PROMPT_DIR / "system_prompt_outline.txt").read_text(encoding="utf-8")
    try:
        if args.think == "detect":
            args.think = detect_think(args)
            args.schema_first = args.think == "on"       # found to need reasoning: try the schema before paying for it
            print(f"reasoning mode: {args.think}" + (" (the outline is asked as schema-held JSON first)" if args.schema_first else ""),
                  file=sys.stderr)
        if is_source:
            plan = source_plan(args, text, ask)
        else:
            plan = {"user": (f"Topic: {text}\nNumber of main branches: {args.branches}\nLevels below the root: {args.depth}\n"
                             f"Language: {args.language}\nReturn only the outline."),
                    "title": text.strip(), "material": "", "sections": [],
                    "language": "" if args.language == DEFAULT_LANGUAGE else args.language}
        if args.qwen_no_think:
            plan["user"] += " /no_think"
        outline, notes, problem = write_outline(args, system, plan, ask)
    except urllib.error.HTTPError as e:
        print(f"ERROR: model server answered HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}\n"
              f"HINT: check --model ({args.model!r}) and --api / --base-url.")
        return 2
    except urllib.error.URLError as e:
        print(f"ERROR: cannot reach the model server: {e}\nHINT: is it running? `ollama serve`, LM Studio local server; "
              "or use --no-llm for the rule-based outline.")
        return 2

    if problem and is_source:
        # last resort: the rule-based outline, so a file is always produced
        outline = outline_from_text(_CODE.sub("", text)[:args.max_chars], max_branches=args.branches)
        notes = [f"the model gave no usable outline ({problem}) -> rule-based outline used instead (edit the .md and rebuild)"]
    elif problem:
        notes = [f"LOW QUALITY: {problem}; the model is too small for this topic or needs --think on"] + notes
    if args.save_outline:
        Path(args.save_outline).write_text(outline, encoding="utf-8")
    res = draw(outline)
    if res.get("ok"):
        res["warnings"] = notes + res.get("warnings", [])
    print(format_result(res))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
