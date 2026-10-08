"""Topic -> silabus page with a LOCAL model (Ollama, LM Studio, llama.cpp server, vLLM ...).

The model only writes the content as JSON, constrained by assets/silabus.schema.json; build_silabus.py
checks it against the skill's rules, repairs what code can repair, computes hours and the schedule,
draws the module map and writes the HTML page.  Standard library only.

    python scripts/generate_silabus.py "Python untuk analisis data" -o silabus-python.html
    python scripts/generate_silabus.py "Reksa dana" --level Pemula --goal "bisa memilih reksa dana" \
        --hours-per-week 3 --sources sumber.txt --context catatan.md
    python scripts/generate_silabus.py "..." --from-json jawaban.json        # build again without the model

--model auto (default) takes the first of RECOMMENDED that the server has; SKILL_MODEL overrides it.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_silabus import SKILL_DIR, build_silabus, format_result, is_money_topic, read_sources, slugify  # noqa: E402
from local_model import Settings, ask_model, choose_model, cut_fields, parse_json, server_error_hint  # noqa: E402

SCHEMA = SKILL_DIR / "assets" / "silabus.schema.json"
PROMPT = SKILL_DIR / "assets" / "prompts" / "system_prompt.txt"

# Best first, from the comparison in docs/konsep/model-lokal-untuk-skill-belajar.md: no model covered the core
# concepts every time (NAB was in 2 of 5 gemma3:4b syllabi, 0 of 2 qwen3:8b), and gemma3:4b took 30-40 s
# where qwen3:8b took 140-250 s.
RECOMMENDED = ("gemma3:4b", "qwen3:8b", "qwen3:4b")
CONTEXT_LIMIT = 12000


def request_text(topic: str, level: str, goal: str, hours_per_week: int, sources: list, context: str) -> str:
    lines = [f"Topik: {topic}", f"Level awal pelajar: {level}",
             f"Tujuan pelajar: {goal or 'paham cara kerjanya dan bisa memakainya'}",
             f"Waktu belajar: sekitar {hours_per_week} jam per minggu",
             "Bahasa: Bahasa Indonesia. Semua teks di JSON ditulis dalam Bahasa Indonesia."]
    if is_money_topic({"topic": topic}):
        # only here: given to every topic, the rule added a business-model module to a Python course
        lines.append("Ini topik tentang uang: wajib ada satu modul tentang model bisnis atau insentif (siapa memberi "
                     "apa, siapa mendapat apa, kenapa tiap pihak mau ikut), dan wajib ada modul yang membahas risiko.")
    if sources:
        lines.append("Sumber yang boleh disebut (tanpa menulis URL-nya): "
                     + "; ".join(s["title"] for s in sources))
    if context:
        lines.append("Pakai HANYA fakta dari bahan berikut:\n<<<\n" + context[:CONTEXT_LIMIT] + "\n>>>")
    lines.append("Kembalikan hanya objek JSON.")
    return "\n".join(lines)


def generate(topic: str, output: str | None = None, level: str = "Pemula", goal: str = "", hours_per_week: int = 4,
             sources: list | None = None, context: str = "", settings: Settings | None = None, retries: int = 1,
             from_json: str | None = None, save_json: str | None = None) -> dict:
    """Write the silabus page; returns build_silabus's result plus "model", "attempts" and "stats"."""
    sources = sources or []
    settings = settings or Settings(model=choose_model("ollama", None, RECOMMENDED))
    output = output or f"silabus-{slugify(topic)}.html"
    system = PROMPT.read_text(encoding="utf-8")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    user = request_text(topic, level, goal, hours_per_week, sources, context)
    res, stats_all = {"ok": False, "error": "model was not called"}, []
    for attempt in range(1, retries + 2):
        if from_json:
            raw, stats = Path(from_json).read_text(encoding="utf-8"), {"seconds": 0}
        else:
            try:
                raw, stats = ask_model(settings, system, user, schema)
            except (urllib.error.URLError, OSError) as error:
                return {"ok": False, "error": server_error_hint(error, settings.model), "model": settings.model}
            if save_json:
                Path(save_json).write_text(raw, encoding="utf-8")
        stats_all.append(stats)
        try:
            spec = parse_json(raw)
        except ValueError as error:
            if (stats.get("tokens") or 0) >= settings.max_tokens:
                res = {"ok": False, "error": f"the answer stopped at the token limit ({settings.max_tokens}) before "
                                             "the JSON was closed; write every field shorter"}
            else:
                res = {"ok": False, "error": f"the answer is not JSON ({error})"}
        else:
            if isinstance(spec, dict) and not spec.get("topic"):
                spec["topic"] = topic
            res = build_silabus(spec, output, sources, hours_per_week, settings.model)
            if res.get("ok"):
                res["warnings"] += [f"{p} reached its length limit and may be cut off" for p in cut_fields(spec, schema)]
        if res.get("ok") or from_json:
            break
        user += f"\n\nJawaban sebelumnya tidak bisa dipakai ({res.get('error')}). Kembalikan JSON yang lengkap."
    res.update({"model": settings.model, "attempts": attempt, "stats": stats_all})
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("topic", help="what the learner wants to learn")
    ap.add_argument("-o", "--output", help="HTML file (default: silabus-<topic>.html)")
    ap.add_argument("--level", default="Pemula")
    ap.add_argument("--goal", default="", help="what the learner wants to be able to do")
    ap.add_argument("--hours-per-week", type=int, default=4)
    ap.add_argument("--sources", help='file with lines "Judul | URL | dipakai untuk"')
    ap.add_argument("--context", help="text file with source material; the model uses only its facts")
    ap.add_argument("--api", choices=["ollama", "openai"], default="ollama")
    ap.add_argument("--base-url")
    ap.add_argument("--model", default="auto", help=f"auto (default): the first of {', '.join(RECOMMENDED)} on the server")
    ap.add_argument("--api-key", default="local")
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--num-ctx", type=int, default=0, help="0 (default): just enough for the request")
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--think", choices=["auto", "on", "off"], default="auto")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--retries", type=int, default=1, help="extra attempts when the answer cannot be used")
    ap.add_argument("--save-json", help="write the model's raw answer to this file")
    ap.add_argument("--from-json", help="do not call the model: build from an answer saved with --save-json")
    args = ap.parse_args()

    model = args.model
    if model == "auto" and not args.from_json:
        model = choose_model(args.api, args.base_url, RECOMMENDED, args.api_key)
        print(f"model: {model} (--model or SKILL_MODEL chooses another)", file=sys.stderr)
    settings = Settings(model=model, api=args.api, base_url=args.base_url, api_key=args.api_key,
                        temperature=args.temperature, num_ctx=args.num_ctx, max_tokens=args.max_tokens,
                        think=args.think, timeout=args.timeout)
    context = Path(args.context).read_text(encoding="utf-8", errors="replace") if args.context else ""
    res = generate(args.topic, args.output, args.level, args.goal, args.hours_per_week, read_sources(args.sources),
                   context, settings, args.retries, args.from_json, args.save_json)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    print(format_result(res))
    if res.get("stats") and res["stats"][-1].get("tokens"):
        s = res["stats"][-1]
        print(f"     model {res['model']}: {s['tokens']} token, {s['seconds']} detik, percobaan ke-{res['attempts']}")
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
