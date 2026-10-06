"""Measure how well a local model writes mind maps with this skill.

    python evals/local_models.py qwen3:8b
    python evals/local_models.py qwen3:8b qwen3:4b gemma3:4b --repeat 3
    python evals/local_models.py qwen3:8b --api openai --base-url http://localhost:1234/v1

It answers "how small a model is still good enough?" with numbers instead of a guess.  Every model
runs scripts/generate_mindmap.py on four cases and one line per run is printed:

    topic-en       an English topic, no source text
    topic-id       an Indonesian topic, no source text
    source-short   a document that fits in one request     (evals/files/short.md,  5 000 characters)
    source-long    a document that is read in parts        (evals/files/long.md,  13 700 characters)

result    ok        the model's outline was drawn, written in one answer
          steps     one answer was not usable; the outline was built step by step (branches, then points)
          fallback  the model gave nothing usable, the rule-based outline was drawn instead
          poor      a topic map was drawn although it does not look like a mind map
          FAIL      no file was written
repairs   how many lines the script had to fix (AUTO-FIXED / WARNINGS).  0-2 means the model is
          comfortable; a long list on every run means it is too small for this material.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts" / "generate_mindmap.py"
CASES = {
    "topic-en": ["How a ReAct agent decides which tool to call"],
    "topic-id": ["Arsitektur hexagonal untuk aplikasi AI"],
    "source-short": [str(HERE / "files" / "short.md")],
    "source-long": [str(HERE / "files" / "long.md")],
}
SUMMARY = re.compile(r"\((\d+) nodes, (\d+) branches, depth (\d+)")
REPAIRS = re.compile(r"AUTO-FIXED / WARNINGS \((\d+)\)")


def run_case(model: str, case: str, args, folder: Path) -> dict:
    name = f"{re.sub(r'[^a-z0-9]+', '-', model.lower())}-{case}"
    command = [sys.executable, str(SCRIPT), *CASES[case], "--model", model, "--api", args.api,
               "-o", str(folder / f"{name}.svg"), "--also", "html,md", "--save-outline", str(folder / f"{name}.raw.txt")]
    if args.base_url:
        command += ["--base-url", args.base_url]
    if args.num_ctx:
        command += ["--num-ctx", str(args.num_ctx)]
    started = time.perf_counter()
    done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    seconds = time.perf_counter() - started
    summary, repairs = SUMMARY.search(done.stdout), REPAIRS.search(done.stdout)
    if done.returncode != 0:
        result = "FAIL"
    elif "rule-based outline used instead" in done.stdout:
        result = "fallback"
    elif "LOW QUALITY" in done.stdout:
        result = "poor"
    elif "built step by step" in done.stdout:
        result = "steps"
    else:
        result = "ok"
    return {"model": model, "case": case, "result": result, "seconds": seconds,
            "shape": "/".join(summary.groups()) if summary else "-", "repairs": int(repairs.group(1)) if repairs else 0,
            "detail": "" if result == "ok" else next((ln for ln in done.stdout.splitlines() if ln.startswith(
                ("ERROR", "- the model", "- LOW QUALITY", "- outline built"))), "")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("models", nargs="+", help="for example qwen3:8b")
    ap.add_argument("--api", choices=["ollama", "openai"], default="ollama")
    ap.add_argument("--base-url")
    ap.add_argument("--num-ctx", type=int)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--cases", nargs="*", default=list(CASES), choices=list(CASES))
    ap.add_argument("--out", help="folder for the maps (default: a temporary folder)")
    args = ap.parse_args()

    folder = Path(args.out or tempfile.mkdtemp(prefix="mindmap-eval-"))
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for model in args.models:
        for case in args.cases:
            for _ in range(args.repeat):
                row = run_case(model, case, args, folder)
                rows.append(row)
                print(f"{model} {case}: {row['result']} in {row['seconds']:.0f}s", file=sys.stderr, flush=True)

    print(f"{'model':<16} {'case':<13} {'result':<9} {'seconds':>7} {'nodes/branches/depth':>21} {'repairs':>8}")
    for r in rows:
        print(f"{r['model']:<16} {r['case']:<13} {r['result']:<9} {r['seconds']:>7.0f} {r['shape']:>21} {r['repairs']:>8}")
        if r["detail"]:
            print(f"    {r['detail'][:150]}")
    good = sum(r["result"] in ("ok", "steps") for r in rows)
    print(f"\n{good} of {len(rows)} runs drew an outline written by the model.  Maps and outlines: {folder}")
    return 0 if good == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
