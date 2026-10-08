"""Module card or topic -> lesson page with a LOCAL model (Ollama, LM Studio, llama.cpp server, vLLM ...).

The model only writes the content as JSON, constrained by assets/materi.schema.json; build_materi.py
checks it against the skill's rules, repairs what code can repair, and writes the HTML page with its
diagrams, interactive demo, quiz and glossary.  Standard library only.

    # module 2 of a silabus written by silabus_belajar (its card is the contract)
    python scripts/generate_materi.py --silabus silabus-reksa-dana.json --module 2 -o reksa-dana-modul-2.html
    # a lesson on its own
    python scripts/generate_materi.py "Cara kerja bunga majemuk" -o materi-bunga-majemuk.html
    python scripts/generate_materi.py --silabus s.json --module 1 --from-json jawaban.json   # without the model

--model auto (default) takes the first of RECOMMENDED that the server has; SKILL_MODEL overrides it.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_materi import SKILL_DIR, SpecError, build_materi, format_result, load_contract, read_sources, slugify  # noqa: E402
from local_model import Settings, ask_model, choose_model, cut_fields, parse_json, server_error_hint  # noqa: E402

SCHEMA = SKILL_DIR / "assets" / "materi.schema.json"
PROMPT = SKILL_DIR / "assets" / "prompts" / "system_prompt.txt"

# Best first, from the comparison in docs/konsep/model-lokal-untuk-skill-belajar.md: qwen3:8b got every number
# right in all four lessons; gemma3:4b is five times faster but got 5 numbers wrong over two runs.
RECOMMENDED = ("qwen3:8b", "gemma3:4b", "qwen3:4b")
CONTEXT_LIMIT = 12000
MAX_TOKENS = 4608              # the longest answer in the comparison was 2 800 tokens


def request_text(topic: str, contract: dict | None, sources: list, context: str) -> str:
    if contract:
        lines = [f"Kartu modul dari silabus \"{contract['silabus_title']}\" (Modul {contract['number']} dari {contract['total']}):",
                 f"Judul: {contract['title']}", f"Pertanyaan utama: {contract['question']}", "Tujuan belajar:"]
        lines += [f"{i}. {o}" for i, o in enumerate(contract["objectives"], 1)]
        lines.append("Istilah yang harus dijelaskan di kotak istilah: " + ", ".join(contract["terms"]))
        if contract.get("exercise"):
            lines.append(f"Latihan di kartu modul: {contract['exercise']} Tulis latihan ini sebagai latihan pertama di "
                         "exercises, lengkap dengan expected-nya; latihan lain boleh ditambahkan.")
        if contract.get("running_example"):
            lines.append(f"Contoh berjalan untuk semua modul: {contract['running_example']}")
        previous = contract.get("previous")
        if previous:
            lines.append(f"Modul sebelumnya: {previous.get('title')} (istilahnya: {', '.join(previous.get('terms', []))}). "
                         "Soal kuis pertama mengulang modul sebelumnya.")
        else:
            lines.append("Ini modul pertama: prior diisi string kosong.")
        if contract.get("next"):
            lines.append(f"Modul berikutnya: {contract['next'].get('title')}. Istilah modul berikutnya belum boleh dipakai.")
    else:
        lines = [f"Topik materi lepas: {topic}",
                 "Tidak ada silabus. Tulis sendiri kontraknya: satu pertanyaan utama di lead, 2-4 tujuan belajar di "
                 "objectives, dan 3-6 istilah yang dijelaskan di bab-bab. prior diisi string kosong."]
    if sources:
        lines.append("Sumber yang boleh disebut (tanpa menulis URL-nya): " + "; ".join(s["title"] for s in sources))
    if context:
        lines.append("Pakai HANYA fakta dari bahan berikut:\n<<<\n" + context[:CONTEXT_LIMIT] + "\n>>>")
    lines += ["Bahasa: Bahasa Indonesia. Semua teks di JSON ditulis dalam Bahasa Indonesia.", "Kembalikan hanya objek JSON."]
    return "\n".join(lines)


def generate(topic: str = "", output: str | None = None, contract: dict | None = None, sources: list | None = None,
             context: str = "", settings: Settings | None = None, retries: int = 1, from_json: str | None = None,
             save_json: str | None = None) -> dict:
    """Write the lesson page; returns build_materi's result plus "model", "attempts" and "stats"."""
    if not topic and not contract:
        return {"ok": False, "error": "give a topic, or --silabus with --module"}
    sources = sources or []
    settings = settings or Settings(model=choose_model("ollama", None, RECOMMENDED), max_tokens=MAX_TOKENS)
    output = output or (f"{slugify(contract['topic'])}-modul-{contract['number']}.html" if contract
                        else f"materi-{slugify(topic)}.html")
    system = PROMPT.read_text(encoding="utf-8")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    user = request_text(topic, contract, sources, context)
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
            res = build_materi(spec, output, contract, sources, settings.model)
            if res.get("ok"):
                res["warnings"] += [f"{p} reached its length limit and may be cut off" for p in cut_fields(spec, schema)]
        if res.get("ok") or from_json:
            break
        user += f"\n\nJawaban sebelumnya tidak bisa dipakai ({res.get('error')}). Kembalikan JSON yang lengkap."
    res.update({"model": settings.model, "attempts": attempt, "stats": stats_all})
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("topic", nargs="?", default="", help="topic of a lesson without a silabus")
    ap.add_argument("-o", "--output")
    ap.add_argument("--silabus", help="silabus JSON written by silabus_belajar")
    ap.add_argument("--module", type=int, help="module number in the silabus")
    ap.add_argument("--sources", help='file with lines "Judul | URL"')
    ap.add_argument("--context", help="text file with source material; the model uses only its facts")
    ap.add_argument("--api", choices=["ollama", "openai"], default="ollama")
    ap.add_argument("--base-url")
    ap.add_argument("--model", default="auto", help=f"auto (default): the first of {', '.join(RECOMMENDED)} on the server")
    ap.add_argument("--api-key", default="local")
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--num-ctx", type=int, default=0, help="0 (default): just enough for the request")
    ap.add_argument("--max-tokens", type=int, default=MAX_TOKENS)
    ap.add_argument("--think", choices=["auto", "on", "off"], default="auto")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--retries", type=int, default=1)
    ap.add_argument("--save-json")
    ap.add_argument("--from-json")
    args = ap.parse_args()

    try:
        contract = load_contract(args.silabus, args.module)
    except (SpecError, OSError, ValueError) as error:
        print(f"GAGAL: {error}")
        return 2
    model = args.model
    if model == "auto" and not args.from_json:
        model = choose_model(args.api, args.base_url, RECOMMENDED, args.api_key)
        print(f"model: {model} (--model or SKILL_MODEL chooses another)", file=sys.stderr)
    settings = Settings(model=model, api=args.api, base_url=args.base_url, api_key=args.api_key,
                        temperature=args.temperature, num_ctx=args.num_ctx, max_tokens=args.max_tokens,
                        think=args.think, timeout=args.timeout)
    context = Path(args.context).read_text(encoding="utf-8", errors="replace") if args.context else ""
    res = generate(args.topic, args.output, contract, read_sources(args.sources), context, settings, args.retries,
                   args.from_json, args.save_json)
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
