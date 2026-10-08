"""Check every skill in this pool against a small local model (Ollama).

    python evals/small_model_check.py qwen3:8b
    python evals/small_model_check.py qwen3:8b --only calculator,docx --num-ctx 8192
    python evals/small_model_check.py qwen3:8b --skip-runners        # no decks or posters (they take minutes)

Four things are measured, in this order:

  inventory    does the skill import here, which tools it exposes, what METADATA and SKILL.md cost in tokens
  selection    shown every description, does the model name the right skill for a request?
  invocation   given SKILL.md and the tool, does the model call it with arguments that really work?
  runners      generate_deck.py / generate_poster.py end to end (model writes the JSON spec, script builds the file)

The tools are executed for real when that is safe offline (calculator, docx, mind map); for tools that
need the network or an upload (web search, subagents, image) only the arguments are checked.

`app.agent.minio_connection` and `app.config.settings` belong to the application these skills were
written for.  They are replaced by stubs here, so a skill that imports them can still be checked.
Standard library only, plus whatever each skill itself imports.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import types
import urllib.error
import urllib.request
from pathlib import Path

POOL = Path(__file__).resolve().parent.parent
CHARS_PER_TOKEN = 3.6           # mixed Indonesian / English text, same figure as REQUIREMENTS.md

# skill folder -> (module with the tools, request used for the selection test)
SKILLS = {
    "calculator": ("calculator.math_skill", "Berapa 17,5% dari 2.340.000?"),
    "chart": ("chart.chart_skill", "Buatkan grafik batang penjualan per bulan: Jan 12, Feb 18, Mar 9."),
    "docx": ("docx.docx_skill", "Tolong buatkan surat penawaran harga dalam format Word."),
    "image": ("image.image_skill", "Jelaskan isi gambar yang baru saya unggah, file_id t1/abc.png."),
    "mind_map": ("mind_map.mind_map_skill", "Buatkan peta pikiran dari materi fotosintesis ini."),
    "pptx_claude": ("pptx_claude.pptx_claude_skill", "Buatkan pitch deck startup saya, 8 slide, tema gelap."),
    "pptx_research": ("pptx_research.pptx_research_skill", "Saya butuh slide proposal penelitian tesis tentang literasi digital."),
    "resaerch_poster": ("resaerch_poster.research_poster_skill", "Buat poster penelitian satu halaman dari hasil survei konsumen ini."),
    "subagent_research": ("subagent_research.subagent_research_skill", "Riset tiga hal sekaligus: harga, pesaing, dan regulasi mobil listrik di Indonesia."),
    "web_search": ("web_search.web_search", "Berapa kurs dolar ke rupiah hari ini?"),
    "xlsx": ("xlsx.xlsx_skill", "Analisis file penjualan.xlsx yang saya unggah."),
    "youtube_transcript": ("youtube_transcript.youtube_transcript_skill", "Rangkum isi video ini: https://youtu.be/Pc3GWaOWHLk"),
    "contextual_retrieval": ("contextual_retrieval.contextual_retrieval_skill", "Siapkan catatan kuliah.md ini untuk dimasukkan ke vector database supaya bisa dicari AI."),
    "crypto_snapshot": ("crypto_snapshot.crypto_snapshot_skill", "Cek harga BTC sekarang, sama EMA dan stochastic-nya."),
    "crypto_chart": ("crypto_chart.crypto_chart_skill", "Kirimin gambar candlestick chart SOL 4 jam dong."),
}

# tool name -> (skill folder, user request, how to judge the call)
INVOCATIONS = {
    "math_calculator": ("calculator", "Berapa 15% dari 340?", "run:51"),
    "create_docx": ("docx", "Buat memo Word berjudul 'Rapat Mingguan' dengan dua butir: anggaran disetujui, rilis diundur seminggu.", "run:created successfully"),
    "create_mind_map": ("mind_map", "Buat mind map tentang siklus air, simpan sebagai siklus_air.svg.", "run:OK:"),
    "web_search": ("web_search", "Cari berita terbaru tentang harga beras di Indonesia.", "args:query"),
    "view_image": ("image", "Apa isi gambar dengan file_id t1/abc.png?", "args:file_id=t1/abc.png"),
    "dispatch_research_subagents": ("subagent_research", "Bandingkan PostgreSQL dan MongoDB untuk aplikasi kasir: riset keduanya secara paralel.", "args:tasks>=2"),
    "generate_chart": ("chart", "Buat grafik batang dari data ini: [{\"bulan\": \"Jan\", \"jual\": 12}, {\"bulan\": \"Feb\", \"jual\": 18}]", "run:chart_url"),
    "create_xlsx": ("xlsx", "Buat file Excel daftar belanja: beras 2 kg, telur 1 kg, minyak 2 liter.", "run:created successfully"),
    "get_youtube_transcript": ("youtube_transcript", "Ambil transcript video https://youtu.be/Pc3GWaOWHLk?si=Z4W_FHEmJlxeJZWU", "args:url"),
    "contextualize_document": ("contextual_retrieval", "Pecah file catatan/fotosintesis.md jadi chunk untuk vector database.", "args:path"),
    "get_crypto_snapshot": ("crypto_snapshot", "Update market ETH timeframe 4 jam dong.", "args:token"),
    "get_crypto_chart": ("crypto_chart", "Lihat chart BTC harian, candle saja tanpa indikator.", "args:token"),
}

RUNNERS = {
    "pptx_research": ["scripts/generate_deck.py", "Pengaruh literasi digital terhadap prestasi belajar siswa SMA", "-o", "{out}/deck.pptx"],
    "pptx_claude": ["scripts/generate_deck.py", "Pitch deck startup kopi langganan untuk kantor, 8 slide", "-o", "{out}/pitch.pptx"],
    "resaerch_poster": ["scripts/generate_poster.py", "Survei kebiasaan belanja online mahasiswa di Indonesia", "-o", "{out}/poster.html"],
}


# ---------------------------------------------------------------------------
# Stubs for the application these skills came from
# ---------------------------------------------------------------------------

def install_app_stubs() -> None:
    class _Settings:
        def __getattr__(self, name):
            return ""

    stubs = {name: types.ModuleType(name) for name in
             ("app", "app.agent", "app.agent.minio_connection", "app.config", "app.config.settings")}
    stubs["app.agent.minio_connection"].upload_file_to_minio = lambda *a, **k: None
    stubs["app.config.settings"].settings = _Settings()
    sys.modules.update(stubs)


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

def tokens(text: str) -> int:
    return round(len(text) / CHARS_PER_TOKEN)


def front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    fields = {}
    for line in (m.group(1) if m else "").splitlines():
        if re.match(r"^[\w-]+:", line):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def load_tools(module_name: str) -> tuple[dict, str]:
    """Import a skill module; return ({tool name: tool}, error text)."""
    try:
        module = importlib.import_module(f"skills.{module_name}")
    except Exception as e:  # noqa: BLE001 - the error text is the finding
        return {}, f"{type(e).__name__}: {str(e)[:110]}"
    tools = {getattr(v, "name", ""): v for v in vars(module).values()
             if hasattr(v, "args_schema") and hasattr(v, "invoke") and getattr(v, "name", "")}
    return tools, ""


def inventory(names: list[str]) -> dict:
    rows = {}
    for folder in names:
        module_name, _ = SKILLS[folder]
        meta = front_matter(POOL / folder / "METADATA.md") or front_matter(POOL / folder / "SKILL.md")
        skill_md = (POOL / folder / "SKILL.md").read_text(encoding="utf-8", errors="replace")
        tools, error = load_tools(module_name)
        rows[folder] = {"name": meta.get("name", folder), "description": meta.get("description", ""),
                        "skill_md": skill_md, "tools": tools, "error": error}
    return rows


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

def needs_thinking(args) -> bool:
    """True for a model that writes its reasoning into the answer when reasoning is switched off (qwen3:4b).

    Such a model fails every test here with reasoning off: asked for a skill name it answers
    "Okay, let's see. The user is ...".  Allowed to reason, the server keeps the reasoning apart.
    """
    probe = argparse.Namespace(**{**vars(args), "thinking": False})
    reply = chat(probe, [{"role": "system", "content": "Reply with exactly one word."},
                         {"role": "user", "content": "Say: ready"}], max_tokens=30)
    return len((reply.get("content") or "").split()) > 3


def chat(args, messages, tools=None, max_tokens=700, schema=None) -> dict:
    payload = {"model": args.model, "messages": messages, "stream": False, "think": args.thinking,
               "options": {"temperature": 0.2, "num_ctx": max(args.num_ctx, 16384) if args.thinking else args.num_ctx,
                           "num_predict": max_tokens + 6000 if args.thinking else max_tokens}}   # reasoning is counted too
    if tools:
        payload["tools"] = tools
    if schema:
        payload["format"] = schema           # the server only lets the model write JSON of this shape
    req = urllib.request.Request(args.base_url.rstrip("/") + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=args.timeout) as resp:
        return json.loads(resp.read().decode("utf-8")).get("message", {})


def select_skill(args, rows: dict, request: str) -> str:
    listing = "\n".join(f"- {r['name']}: {r['description']}" for r in rows.values())
    system = ("You are an assistant that has these skills:\n" + listing +
              "\n\nPick the ONE skill that fits the user's request. Reply with its name only, exactly as written in the list.")
    reply = chat(args, [{"role": "system", "content": system}, {"role": "user", "content": request}], max_tokens=40)
    return re.sub(r"<think>.*?</think>", "", reply.get("content") or "", flags=re.S).strip().strip("`*\"' .").lower()


def judge(rule: str, tool, call_args: dict, out_dir: Path) -> tuple[bool, str]:
    kind, _, expect = rule.partition(":")
    if kind == "args":
        key, op, value = re.match(r"(\w+)(>=|=)?(.*)", expect).groups()
        got = call_args.get(key)
        if op == ">=":
            ok = isinstance(got, list) and len(got) >= int(value) and all(isinstance(t, dict) and t.get("topic") for t in got)
        elif op == "=":
            ok = str(got) == value
        else:
            ok = bool(str(got or "").strip())
        return ok, f"{key}={json.dumps(got, ensure_ascii=False)[:90]}"
    namespace = tool.func.__globals__ if getattr(tool, "func", None) else {}
    for attr in ("DOWNLOADS_DIR", "CHARTS_DIR"):                 # keep generated files out of the repo
        if attr in namespace:
            namespace[attr] = out_dir
    try:
        result = str(tool.invoke(call_args))
    except Exception as e:  # noqa: BLE001
        return False, f"tool raised {type(e).__name__}: {str(e)[:90]}"
    return expect.lower() in result.lower(), " ".join(result.split())[:110]


def invoke_tool(args, rows: dict, tool_name: str, out_dir: Path) -> tuple[str, str, float]:
    from langchain_core.utils.function_calling import convert_to_openai_tool

    folder, request, rule = INVOCATIONS[tool_name]
    row = rows[folder]
    tool = row["tools"].get(tool_name)
    if tool is None:
        return "SKIP", row["error"] or "tool not found in the module", 0.0
    body = row["skill_md"].split("---", 2)[-1].strip()
    spec = convert_to_openai_tool(tool)
    user = {"role": "user", "content": request}
    started = time.perf_counter()
    if args.calls == "native":
        reply = chat(args, [{"role": "system", "content": "You have one skill. Use its tool to do what the user asks.\n\n" + body}, user],
                     tools=[spec], max_tokens=args.max_tokens)
        calls = reply.get("tool_calls") or []
        if not calls:
            return "FAIL", "no tool call; answered: " + " ".join((reply.get("content") or "").split())[:80], time.perf_counter() - started
        function = calls[0].get("function", {})
        call_args = function.get("arguments") or {}
        if function.get("name") != tool_name:
            return "FAIL", f"called {function.get('name')!r} instead", time.perf_counter() - started
    else:
        # No tool calling in the model (gemma3 on Ollama): the same call as plain JSON.  The server holds
        # the answer to the tool's own argument schema, so the JSON cannot be malformed.
        system = (f"You have one skill. Do what the user asks by calling its tool `{tool_name}`.\n"
                  f"Reply with the arguments of that call as one JSON object, nothing else.\n\n{body}\n\n"
                  f"Tool `{tool_name}`:\n{spec['function'].get('description', '')}")
        reply = chat(args, [{"role": "system", "content": system}, user], max_tokens=args.max_tokens,
                     schema=spec["function"]["parameters"])
        call_args = reply.get("content") or ""
    seconds = time.perf_counter() - started
    if isinstance(call_args, str):
        try:
            call_args = json.loads(call_args)
        except json.JSONDecodeError:
            return "FAIL", "arguments are not JSON", seconds
    ok, detail = judge(rule, tool, call_args, out_dir)
    if not ok:                                                   # keep the call, to see what the model got wrong
        (out_dir / f"{tool_name}.failed_call.json").write_text(json.dumps(call_args, ensure_ascii=False, indent=1), encoding="utf-8")
    return ("ok" if ok else "FAIL"), detail, seconds


def run_runner(args, folder: str, out_dir: Path) -> tuple[str, str, float]:
    script, *rest = RUNNERS[folder]
    command = [sys.executable, str(POOL / folder / script), *[a.format(out=out_dir) for a in rest],
               "--model", args.model, "--base-url", args.base_url, "--think", "on" if args.thinking else "off",
               "--num-ctx", str(args.num_ctx)]
    if args.thinking:
        command += ["--max-tokens", "8000"]                      # the reasoning is counted too
    started = time.perf_counter()
    done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    seconds = time.perf_counter() - started
    lines = [ln for ln in (done.stdout + done.stderr).splitlines() if ln.strip()]
    head = next((ln for ln in lines if ln.startswith(("OK", "ERROR"))), lines[-1] if lines else "")
    fixed = next((ln for ln in lines if "AUTO-FIXED" in ln), "")
    return ("ok" if done.returncode == 0 else "FAIL"), f"{head[:100]} {fixed[:40]}".strip(), seconds


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model", nargs="?", help="for example qwen3:8b; omit for the inventory only")
    ap.add_argument("--base-url", default="http://localhost:11434")
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--max-tokens", type=int, default=900, help="room for one tool call")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--only", default="", help="skill folders, comma separated")
    ap.add_argument("--skip-runners", action="store_true")
    ap.add_argument("--skip-selection", action="store_true")
    ap.add_argument("--calls", choices=["detect", "native", "schema"], default="detect",
                    help="how the model calls a tool: its own tool calling, or JSON held to the tool's schema "
                         "(for models without tool calling). detect (default) tries native first")
    ap.add_argument("--think", choices=["detect", "on", "off"], default="detect",
                    help="detect (default): reasoning is left on only for a model that cannot answer without it")
    ap.add_argument("--out", help="folder for the files the skills write (default: a temporary folder)")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:  # noqa: BLE001
        pass

    names = [n for n in (args.only.split(",") if args.only else SKILLS) if n in SKILLS]
    sys.path.insert(0, str(POOL.parent))
    install_app_stubs()
    rows = inventory(names)
    out_dir = Path(args.out or tempfile.mkdtemp(prefix="skill-check-"))
    out_dir.mkdir(parents=True, exist_ok=True)
    os.environ["PPTX_OUTPUT_DIR"] = str(out_dir)                 # where the spec skills write relative file names

    print(f"{'skill':<18} {'name':<18} {'description':>11} {'SKILL.md':>9}  tools / problem")
    for folder, r in rows.items():
        what = ", ".join(r["tools"]) if r["tools"] else ("IMPORT FAILS: " + r["error"] if r["error"] else "no tool exported")
        print(f"{folder:<18} {r['name']:<18} {tokens(r['description']):>7} tok {tokens(r['skill_md']):>5} tok  {what}")
    total = sum(tokens(r["description"]) for r in rows.values())
    print(f"\nAll descriptions together: about {total} tokens (this much is in the prompt before any skill is opened).")
    if not args.model:
        return 0

    try:
        args.thinking = args.think == "on" or (args.think == "detect" and needs_thinking(args))
    except (urllib.error.URLError, OSError) as e:
        print(f"ERROR: cannot use {args.model} at {args.base_url}: {e}")
        return 2
    print(f"\n{args.model}: reasoning {'on (the model cannot answer without it)' if args.thinking else 'off'}")
    if args.calls == "detect":
        try:
            chat(args, [{"role": "user", "content": "Say: ready"}], tools=[{"type": "function", "function": {
                "name": "noop", "description": "Does nothing.", "parameters": {"type": "object", "properties": {}}}}], max_tokens=20)
            args.calls = "native"
        except urllib.error.HTTPError:
            args.calls = "schema"
    print(f"{args.model}: tool calls {'by the model itself' if args.calls == 'native' else 'as JSON held to the tool schema (no tool calling in this model)'}")

    failures = 0
    if not args.skip_selection:
        print(f"\nselection ({args.model}): which skill for which request")
    for folder, r in ({} if args.skip_selection else rows).items():
        started = time.perf_counter()
        try:
            picked = select_skill(args, rows, SKILLS[folder][1])
        except (urllib.error.URLError, OSError) as e:
            print(f"ERROR: cannot reach {args.base_url}: {e}")
            return 2
        ok = picked == r["name"].lower()
        failures += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {r['name']:<18} picked {picked[:28]!r:<30} {time.perf_counter() - started:5.0f}s")

    print(f"\ninvocation ({args.model}): one real tool call per tool")
    for tool_name, (folder, _, _) in INVOCATIONS.items():
        if folder not in rows:
            continue
        try:
            state, detail, seconds = invoke_tool(args, rows, tool_name, out_dir)
        except urllib.error.HTTPError as e:                      # for example: the model does not support tools
            state, detail, seconds = "FAIL", f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:90]}", 0.0
        failures += state == "FAIL"
        print(f"  {state:<4} {tool_name:<28} {seconds:5.0f}s  {detail}")

    if not args.skip_runners:
        print(f"\nrunners ({args.model}): the model writes the spec, the script builds the file")
        for folder in RUNNERS:
            if folder not in rows:
                continue
            state, detail, seconds = run_runner(args, folder, out_dir)
            failures += state == "FAIL"
            print(f"  {state:<4} {folder:<28} {seconds:5.0f}s  {detail}")

    print(f"\nFiles written by the skills: {out_dir}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
