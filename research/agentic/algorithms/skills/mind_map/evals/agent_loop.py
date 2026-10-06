"""Can a model follow this skill as an agent?  (Ollama, tool calling)

    python evals/agent_loop.py qwen3:8b
    python evals/agent_loop.py qwen3:8b qwen3:4b --repeat 3

An agent hands the model SKILL.md and a few tools and expects it to call them in the right
order.  This script is the smallest possible agent: SKILL.md goes into the system prompt and
the model gets three tools (write a file, read a file, run a command).  So the result says
something about the model, not about the size of a particular agent's own prompt.

A run passes when a script of the skill drew the map (build_mindmap.py with the model's own outline,
or generate_mindmap.py), the picture exists, and the user's own file was not overwritten.

A model without tool calling (gemma3 on Ollama) gets the same three tools another way: it answers
with one JSON object per turn, and the server holds that object to a schema (`format`).

Safety: the only commands that are executed are the scripts in this skill's scripts/ folder, and
every file lives in a temporary folder.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ALLOWED = {p.name for p in (SKILL / "scripts").glob("*.py")}
DRAWING = {"build_mindmap.py", "generate_mindmap.py"}
LAUNCHERS = {"python", "python3", "py", "uv", "run"}
MAX_TURNS = 10

TASKS = {
    "topic": "Make a mind map about how a bill becomes a law. Save it as an SVG file.",
    "notes": "Buatkan mind map dari file notes.md, simpan sebagai SVG.",
}

NOTES = """Catatan rapat perencanaan produk

Kita sepakat fokus kuartal ini pada tiga hal. Pertama, onboarding: pengguna baru sering berhenti
di langkah verifikasi email, jadi kita tambahkan login dengan Google dan kurangi isian formulir
menjadi tiga. Kedua, performa: halaman dasbor butuh 6 detik untuk tampil, targetnya di bawah 2
detik dengan cache dan pemuatan bertahap. Ketiga, harga: paket gratis dibatasi 3 proyek, paket
Pro Rp 99.000 per bulan, dan paket Tim dihitung per pengguna.

Risiko yang dicatat: tim hanya punya dua engineer backend, dan migrasi database dijadwalkan di
bulan yang sama. Keputusan: migrasi diundur satu bulan. Tindak lanjut: Rina menyiapkan desain
onboarding, Budi mengukur performa dasbor, dan Sari menulis halaman harga.
"""


def _tool(name, description, **properties):
    return {"type": "function", "function": {"name": name, "description": description, "parameters": {
        "type": "object", "properties": {k: {"type": "string", "description": v} for k, v in properties.items()},
        "required": list(properties)}}}


TOOLS = [
    _tool("write_file", "Write a text file. Overwrites the file if it exists.", path="File name.", content="Full file text."),
    _tool("read_file", "Read a text file.", path="File name."),
    _tool("run_command", "Run one shell command and return what it prints.", command="The command line."),
]


class Sandbox:
    """The model's working folder, and the exit codes of the skill scripts it ran."""

    def __init__(self):
        self.folder = Path(tempfile.mkdtemp(prefix="mindmap-agent-"))
        self.builds: list[int] = []
        self.trace: list[str] = []
        (self.folder / "notes.md").write_text(NOTES, encoding="utf-8")

    def call(self, name: str, a: dict) -> str:
        if name == "write_file":
            path = self.folder / Path(str(a.get("path", ""))).name
            path.write_text(str(a.get("content", "")), encoding="utf-8")
            return f"wrote {path.name}"
        if name == "read_file":
            path = self.folder / Path(str(a.get("path", ""))).name
            return path.read_text(encoding="utf-8") if path.is_file() else f"error: {path.name} does not exist"
        if name == "run_command":
            return self.run(str(a.get("command", "")))
        return f"error: unknown tool {name}"

    def run(self, command: str) -> str:
        try:
            words = shlex.split(command, posix=True)
        except ValueError as e:
            return f"error: cannot parse the command ({e})"
        at = next((i for i, w in enumerate(words) if Path(w).name in ALLOWED), None)
        if at is None or not {w.lower() for w in words[:at]} <= LAUNCHERS:
            return "error: command not allowed. Only the scripts of this skill can be run."
        script = Path(words[at]).name
        rest = [w if w.startswith("-") else Path(w).name for w in words[at + 1:]]
        done = subprocess.run([sys.executable, str(SKILL / "scripts" / script), *rest], cwd=self.folder,
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        if script in DRAWING:
            self.builds.append(done.returncode)
        return (done.stdout + done.stderr).strip().replace(str(self.folder), ".")[:3000]


def needs_thinking(args, model: str) -> bool:
    """True for a model that writes its reasoning into the answer when reasoning is switched off (qwen3:4b)."""
    payload = {"model": model, "stream": False, "think": False, "options": {"num_ctx": args.num_ctx, "num_predict": 30},
               "messages": [{"role": "system", "content": "Reply with exactly one word."}, {"role": "user", "content": "Say: ready"}]}
    req = urllib.request.Request(args.base_url.rstrip("/") + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=args.timeout) as resp:
        return len((json.loads(resp.read().decode("utf-8")).get("message", {}).get("content") or "").split()) > 3


def has_tool_calling(args, model: str) -> bool:
    """False for a model that the server refuses to give tools to (gemma3 on Ollama answers HTTP 400)."""
    payload = {"model": model, "stream": False, "tools": TOOLS[:1], "options": {"num_ctx": args.num_ctx, "num_predict": 20},
               "messages": [{"role": "user", "content": "Say: ready"}]}
    req = urllib.request.Request(args.base_url.rstrip("/") + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=args.timeout).close()
    except urllib.error.HTTPError:
        return False
    return True


# For a model without tool calling: one JSON object per turn, held to this shape by the server (`format`).
STEP_SCHEMA = {"type": "object", "required": ["tool"], "properties": {
    "tool": {"type": "string", "enum": ["read_file", "write_file", "run_command", "answer"]},
    "path": {"type": "string"}, "content": {"type": "string"}, "command": {"type": "string"}, "text": {"type": "string"}}}
STEP_RULES = ("\n\nYou have no tool calling, so every reply is ONE JSON object and nothing else:\n"
              '{"tool": "read_file", "path": "..."}\n{"tool": "write_file", "path": "...", "content": "..."}\n'
              '{"tool": "run_command", "command": "..."}\n{"tool": "answer", "text": "..."}   <- only when the task is done\n'
              "After each object you are shown the result of that tool.")


def run_task(args, model: str, task: str, thinking: bool, native: bool) -> dict:
    box = Sandbox()
    body = (SKILL / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[-1].strip()
    system = ("You are an agent that completes the user's task with the tools you have. Work in the current folder. "
              "When the task is done, answer the user in one or two sentences.\n\n"
              f"You have one skill. Its folder is the current folder's `skill/`, so its scripts are `skill/scripts/...`.\n\n{body}")
    messages = [{"role": "system", "content": system + ("" if native else STEP_RULES)}, {"role": "user", "content": TASKS[task]}]
    started, note, turns, nudged = time.perf_counter(), "ran out of turns", 0, False
    while turns < MAX_TURNS:
        turns += 1
        payload = {"model": model, "messages": messages, "stream": False, "think": thinking,
                   "options": {"temperature": 0.2, "num_ctx": max(args.num_ctx, 16384) if thinking else args.num_ctx,
                               "num_predict": 8000 if thinking else 1200}}      # the reasoning is counted too
        payload.update({"tools": TOOLS} if native else {"format": STEP_SCHEMA})
        req = urllib.request.Request(args.base_url.rstrip("/") + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=args.timeout) as resp:
                reply = json.loads(resp.read().decode("utf-8")).get("message", {})
        except urllib.error.HTTPError as e:
            note = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:110]}"
            break
        messages.append(reply)
        if native:
            calls = [c.get("function", {}) for c in reply.get("tool_calls") or []]
        else:
            try:
                step = json.loads(reply.get("content") or "{}")
            except json.JSONDecodeError:
                step = {}
            if step.get("tool") == "answer":
                reply, calls = {"content": step.get("text", "")}, []
            else:
                calls = [{"name": step.get("tool", ""), "arguments": step}]
        if not calls:
            note = "answered: " + " ".join((reply.get("content") or "").split())[:90]
            if not box.builds and not nudged:
                # The model says the map is done although it never ran a script (seen with qwen3:4b).
                # A real agent would check the same thing; one reminder is allowed.
                nudged = True
                messages.append({"role": "user", "content": "No file was created: no script of the skill has run yet. "
                                 "Use the tools, and answer only after a script printed OK."})
                box.trace.append("(reminded: nothing was created yet)")
                continue
            break
        for fn in calls:
            a = fn.get("arguments") or {}
            if isinstance(a, str):
                try:
                    a = json.loads(a)
                except json.JSONDecodeError:
                    a = {}
            result = box.call(fn.get("name", ""), a if isinstance(a, dict) else {})
            box.trace.append(f"{fn.get('name', '?')}({json.dumps(a, ensure_ascii=False)[:120]}) -> {' '.join(result.split())[:110]}")
            if native:
                messages.append({"role": "tool", "tool_name": fn.get("name", ""), "content": result})
            else:
                messages.append({"role": "user", "content": f"RESULT of {fn.get('name', '')}:\n{result}"})
    drawn = any(p.suffix in (".svg", ".png", ".html", ".pdf") for p in box.folder.iterdir())
    passed = drawn and bool(box.builds) and box.builds[-1] == 0
    if (box.folder / "notes.md").read_text(encoding="utf-8") != NOTES:
        passed, note = False, "OVERWROTE notes.md | " + note
    return {"model": model, "task": task, "passed": passed, "turns": turns, "builds": box.builds,
            "seconds": time.perf_counter() - started, "note": note, "trace": box.trace}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("models", nargs="+", help="for example qwen3:8b")
    ap.add_argument("--base-url", default="http://localhost:11434")
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--think", choices=["detect", "on", "off"], default="detect",
                    help="detect (default): reasoning is left on only for a model that cannot answer without it")
    ap.add_argument("--trace", action="store_true", help="print every tool call, also for runs that pass")
    ap.add_argument("--tasks", nargs="*", default=list(TASKS), choices=list(TASKS))
    ap.add_argument("--timeout", type=int, default=1800)
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    rows = []
    for model in args.models:
        try:
            thinking = args.think == "on" or (args.think == "detect" and needs_thinking(args, model))
        except urllib.error.HTTPError as e:
            print(f"{model:<16} cannot be used: HTTP {e.code} {e.read().decode('utf-8', 'replace')[:100]}", flush=True)
            continue
        native = has_tool_calling(args, model)
        print(f"{model}: reasoning {'on' if thinking else 'off'}, "
              f"{'tool calling' if native else 'no tool calling: one JSON object per turn, held to a schema'}", flush=True)
        for task in args.tasks:
            for _ in range(args.repeat):
                r = run_task(args, model, task, thinking, native)
                rows.append(r)
                print(f"{r['model']:<16} {r['task']:<6} {'ok' if r['passed'] else 'FAIL':<5} turns={r['turns']} "
                      f"build exit codes={r['builds']} {r['seconds']:.0f}s  {r['note']}", flush=True)
                if not r["passed"] or args.trace:
                    for step in r["trace"]:
                        print(f"    {step}", flush=True)
    good = sum(r["passed"] for r in rows)
    print(f"\n{good} of {len(rows)} agent runs drew a mind map.")
    return 0 if good == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
