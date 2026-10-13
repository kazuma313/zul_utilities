"""Research topic -> one-page poster with a LOCAL model (Ollama, LM Studio, llama.cpp server, vLLM ...).

The model only writes JSON (constrained by assets/poster.lite.schema.json);
build_poster.py orders the sections, draws the charts and fits everything on
one page.  Python standard library (+ a Chromium browser for PDF/PNG).

    python scripts/generate_poster.py "Consumer behaviour of urban shoppers" \
        --context survey_summary.txt --organization "Universitas X" -o poster.pdf

    python scripts/generate_poster.py "..." --api openai --base-url http://localhost:1234/v1 --model <id>

Give the model your numbers with --context: without facts it must leave the chart and stats sections out.
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
from build_poster import SKILL_DIR, build_poster, format_result  # noqa: E402

ASSETS = SKILL_DIR / "assets"
SCHEMAS = {"lite": ASSETS / "poster.lite.schema.json", "full": ASSETS / "poster.schema.json"}
PROMPTS = {"lite": ASSETS / "prompts" / "system_prompt_lite.txt", "full": ASSETS / "prompts" / "system_prompt_full.txt"}

CONTACT = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+|(?:https?://|www\.)\S+|\b[\w-]+(?:\.[\w-]+)*\.(?:id|com|org|net|edu|io)\b(?:/\S*)?", re.I)


ID_WORDS = {"dan", "yang", "untuk", "dengan", "dari", "pada", "ini", "adalah", "tidak", "hasil", "dalam", "atau",
            "penelitian", "mahasiswa", "terhadap", "tentang", "kebiasaan", "pengaruh", "survei", "presentasi"}


def language_of(args) -> str:
    """The language to name in the request.

    "The same language as the topic" is too vague for a small model: qwen3:4b wrote an English deck
    for an Indonesian topic.  An Indonesian topic is therefore named as such.
    """
    words = re.findall(r"[a-z]+", args.topic.lower())
    indonesian = words and sum(w in ID_WORDS for w in words) / len(words) > 0.15
    if args.language == "the same language as the topic" and indonesian:
        return "Bahasa Indonesia. Every title, header and sentence is in Bahasa Indonesia"
    return args.language


# Models for research posters, best first, from the skill pool's comparison (REQUIREMENTS.md, evals/compare_models.py):
# qwen3:8b wrote all sections in the right language with correct numbers; gemma3:4b is several
# times faster and fits a smaller GPU; qwen3:4b works only because the schema switches its reasoning off.
RECOMMENDED = ("qwen3:8b", "gemma3:4b", "qwen3:4b")
USE_CASE = "research posters"

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


def drop_invented_contacts(raw: str, known: str) -> tuple[str, list[str]]:
    """Take e-mail addresses and websites out of the footer when they are in no text the user gave.

    The schema makes the footer required, so a model without a contact to print invents one
    ("survei@kampus.ac.id").  Returns the answer and the parts that were removed.
    """
    try:
        spec = json.loads(raw)
    except ValueError:
        return raw, []
    footer = spec.get("footer") if isinstance(spec, dict) else None
    parts = [p.strip() for p in footer.split("|")] if isinstance(footer, str) else footer if isinstance(footer, list) else None
    if not parts:
        return raw, []
    known = known.lower()
    dropped = [p for p in parts if isinstance(p, str) and any(m.group(0).lower() not in known for m in CONTACT.finditer(p))]
    if not dropped:
        return raw, []
    spec["footer"] = [p for p in parts if p not in dropped]
    return json.dumps(spec, ensure_ascii=False), dropped


def drop_invented_charts(raw: str, known: str) -> tuple[str, list[str]]:
    """Leave out the chart sections whose numbers are in no text the user gave."""
    try:
        spec = json.loads(raw)
    except ValueError:
        return raw, []
    sections = spec.get("sections") if isinstance(spec, dict) else None
    if not isinstance(sections, list):
        return raw, []
    numbers, kept, removed = source_numbers(known), [], []
    for section in sections:
        chart = section.get("chart") if isinstance(section, dict) else None
        values = [v for s in chart.get("series") or [] if isinstance(s, dict) for v in s.get("values") or []] \
            if isinstance(chart, dict) else None
        if values is not None and not from_source(values, numbers):
            removed.append(f"section {section.get('title', '')!r} (chart of {', '.join(str(v) for v in values)})")
        else:
            kept.append(section)
    sections[:] = kept
    return (json.dumps(spec, ensure_ascii=False), removed) if removed else (raw, [])


def source_numbers(text: str) -> set:
    """Every number in the user's text; "310.000" and "310,000" count as 310000."""
    found = set()
    for token in re.findall(r"\d+(?:[.,]\d+)*", text):
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", token):
            found.add(float(re.sub(r"[.,]", "", token)))
        else:
            try:
                found.add(float(token.replace(",", ".")))
            except ValueError:
                pass
    return found


def from_source(values: list, numbers: set) -> bool:
    """True when a chart's numbers are the user's own.

    A value counts when it is in the user's text, or is what is left of 100 (72% shop online, so 28%
    do not).  A chart of three or more values may hold one number that is not; a chart of two, none.
    Seen without this check: a radar chart of 5, 7, 3 copied from the prompt, and one of 0, 1, 0.
    """
    values = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    unknown = [v for v in values if v not in numbers and not (0 < v < 100 and 100 - v in numbers)]
    return bool(values) and len(unknown) <= (1 if len(values) >= 3 else 0)


def _post(url: str, payload: dict, api_key: str, timeout: int) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ask_model(args, system: str, user: str, schema: dict | None) -> str:
    if args.api == "ollama":
        payload = {
            "model": args.model, "stream": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": args.temperature, "num_ctx": args.num_ctx, "num_predict": args.max_tokens},
        }
        if schema:
            payload["format"] = schema
        # With a schema the server lets the model write JSON only, so reasoning adds nothing but tokens:
        # qwen3:4b drafted every slide in its reasoning, spent all 8192 tokens there and returned an
        # empty answer, twice, in an hour.  So "auto" asks without reasoning first.  Some Ollama versions
        # drop the schema when think=false is sent (ollama issue #15260); an answer that is not JSON is
        # asked for again with the model's own default.
        fast = args.think == "auto" and bool(schema)
        if args.think != "auto" or fast:
            payload["think"] = args.think == "on"
        base = args.base_url or "http://localhost:11434"
        try:
            data = _post(base.rstrip("/") + "/api/chat", payload, args.api_key, args.timeout)
        except urllib.error.HTTPError as e:
            if e.code != 400:
                raise
            payload.pop("think", None)  # older Ollama / non-thinking model
            data = _post(base.rstrip("/") + "/api/chat", payload, args.api_key, args.timeout)
        content = data.get("message", {}).get("content", "")
        if fast and "think" in payload and not content.lstrip().startswith(("{", "[")):
            payload.pop("think")
            content = _post(base.rstrip("/") + "/api/chat", payload, args.api_key, args.timeout).get("message", {}).get("content", "")
        return content

    payload = {
        "model": args.model, "temperature": args.temperature, "max_tokens": args.max_tokens,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    if schema:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "deck", "strict": True, "schema": schema},
        }
    base = args.base_url or "http://localhost:1234/v1"
    url = base.rstrip("/") + "/chat/completions"
    try:
        data = _post(url, payload, args.api_key, args.timeout)
    except urllib.error.HTTPError as e:
        if e.code not in (400, 422) or not schema:
            raise
        # server does not support json_schema -> plain JSON mode; the engine repairs the rest
        payload["response_format"] = {"type": "json_object"}
        try:
            data = _post(url, payload, args.api_key, args.timeout)
        except urllib.error.HTTPError:
            payload.pop("response_format")
            data = _post(url, payload, args.api_key, args.timeout)
    return data["choices"][0]["message"].get("content") or ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("topic", help="What the deck is about (one or two sentences)")
    ap.add_argument("-o", "--output", default="poster.pdf", help=".pdf, .png or .html")
    ap.add_argument("--api", choices=["ollama", "openai"], default="ollama")
    ap.add_argument("--base-url", help="Default: http://localhost:11434 (ollama) / http://localhost:1234/v1 (openai)")
    ap.add_argument("--model", default="auto",
                    help="auto (default): the first of qwen3:8b, gemma3:4b, qwen3:4b that the server has")
    ap.add_argument("--api-key", default="local")
    ap.add_argument("--schema", choices=["lite", "full", "none"], default="lite")
    ap.add_argument("--slides", "--sections", dest="slides", type=int, default=8, help="Number of sections (4-8)")
    ap.add_argument("--language", default="the same language as the topic")
    ap.add_argument("--images", nargs="*", help="Folders that contain the image files named in the deck")
    ap.add_argument("--organization", help="Institution name for the footer")
    ap.add_argument("--contact", help="Email / website for the footer")
    ap.add_argument("--png", action="store_true", help="Also write a PNG preview")
    ap.add_argument("--context", help="Text file with source material for the deck")
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--max-tokens", type=int, default=8192,
                    help="Room for the answer (thinking models spend part of it on reasoning)")
    ap.add_argument("--num-ctx", type=int, default=16384, help="Ollama context window")
    ap.add_argument("--think", choices=["auto", "on", "off"], default="auto",
                    help="Ollama only. auto = with a schema, ask without reasoning first and fall back to the "
                         "model's default if the answer is not JSON. on = let the model reason (slow, and a "
                         "small model can spend the whole --max-tokens on it)")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--retries", type=int, default=1, help="Extra attempts if the JSON is unusable")
    ap.add_argument("--save-json", help="Write the model's raw answer to this file")
    ap.add_argument("--from-json", help="Do not call the model: build again from an answer saved with --save-json")
    ap.add_argument("--qwen-no-think", action="store_true",
                    help="Append Qwen3's /no_think soft switch to the request (faster, hybrid Qwen3 models only)")
    args = ap.parse_args()
    if args.model == "auto":
        args.model = choose_model(args)
        print(f"model: {args.model} (recommended for {USE_CASE}; --model or SKILL_MODEL chooses another)", file=sys.stderr)

    kind = "lite" if args.schema == "none" else args.schema
    system = PROMPTS[kind].read_text(encoding="utf-8")
    schema = None if args.schema == "none" else json.loads(SCHEMAS[args.schema].read_text(encoding="utf-8"))
    if schema:                              # a small model closes the list as soon as the schema allows it
        bounds = schema["properties"]["sections"]
        bounds["minItems"] = min(max(4, args.slides - 2), bounds.get("maxItems", 8))

    user = f"Research topic: {args.topic}\nNumber of sections: {args.slides}\nLanguage: {language_of(args)}\n"
    known = " ".join(filter(None, [args.topic, args.organization, args.contact]))
    if args.organization:
        user += f"Organization: {args.organization}\n"
    if args.contact:
        user += f"Contact for the footer: {args.contact}\n"
    else:
        user += "Footer: no contact was given. Do not invent an e-mail address or a website.\n"
    if args.context:
        text = Path(args.context).read_text(encoding="utf-8", errors="replace")
        known += " " + text
        limit = 12000
        if len(text) > limit:
            print(f"note: context is long - only the first {limit} characters are sent")
        user += "\nUse ONLY facts from this source material:\n<<<\n" + text[:limit] + "\n>>>\n"
    user += "\nReturn only the JSON object."
    if args.qwen_no_think:
        user += " /no_think"

    res = {"ok": False, "error": "model was not called"}
    for attempt in range(args.retries + 1):
        try:
            raw = Path(args.from_json).read_text(encoding="utf-8") if args.from_json else ask_model(args, system, user, schema)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:400]
            print(f"ERROR: the model server answered HTTP {e.code}: {body}\n"
                  f"HINT: check --model (is {args.model!r} downloaded?) and --api / --base-url.")
            return 2
        except urllib.error.URLError as e:
            print(f"ERROR: cannot reach the model server: {e}\n"
                  f"HINT: is it running? ollama: `ollama serve` + `ollama pull {args.model}`; "
                  "LM Studio: start the local server; check --base-url.")
            return 2
        if args.save_json and not args.from_json:
            Path(args.save_json).write_text(raw, encoding="utf-8")
        raw, invented = drop_invented_contacts(raw, known)
        raw, charts = drop_invented_charts(raw, known)
        out = Path(args.output)
        dirs = [Path(args.context).resolve().parent] if args.context else []
        dirs += [Path(d) for d in (args.images or [])]
        res = build_poster(raw, filename=str(out if out.is_absolute() else Path.cwd() / out), image_dirs=dirs,
                           png=args.png)
        if invented and res.get("ok"):
            res.setdefault("warnings", []).append(
                "footer: " + ", ".join(repr(p) for p in invented) + " is in no text you gave -> removed")
        if charts and res.get("ok"):
            res.setdefault("warnings", []).append("; ".join(charts) + ": numbers that are in no text you gave -> left out")
        if res.get("ok"):
            break
        print(f"attempt {attempt + 1} failed: {res.get('error')}")
        if args.from_json:                  # a saved answer does not change when asked again
            break
        user += f"\n\nYour previous answer could not be used ({res.get('error')}). Return valid JSON only."

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(format_result(res))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
