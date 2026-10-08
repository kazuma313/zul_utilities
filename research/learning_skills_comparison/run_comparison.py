"""Run silabus_belajar and materi_belajar with each local model on the same four tasks, and record the results.

    uv run python research/learning_skills_comparison/run_comparison.py                 # all models
    uv run python research/learning_skills_comparison/run_comparison.py --models gemma3:4b
    uv run python research/learning_skills_comparison/run_comparison.py --rebuild       # rebuild pages from saved answers

Every model gets the same requests.  The two lessons use the module cards of the Claude reference
syllabi (claude/*.json) as their contract, so all models write against the same objectives.  Raw
answers, pages and results.json go next to this file.  Models run one after another, never in
parallel, so Ollama does not swap them in and out of the GPU.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent / "agentic" / "algorithms" / "skills"


def load(skill: str, module: str):
    """Import one script of a skill (the two skills share module names, so each is loaded on its own)."""
    scripts = str(SKILLS / skill / "scripts")
    for name in ("local_model", "build_silabus", "build_materi", "generate_silabus", "generate_materi"):
        sys.modules.pop(name, None)
    sys.path.insert(0, scripts)
    try:
        return importlib.import_module(module)
    finally:
        sys.path.remove(scripts)


TASKS = [
    {"id": "silabus-reksa-dana", "skill": "silabus", "topic": "Reksa dana", "level": "Pemula",
     "goal": "bisa memilih reksa dana sendiri tanpa ikut-ikutan rekomendasi", "hours_per_week": 3},
    {"id": "silabus-python-analisis-data", "skill": "silabus", "topic": "Python untuk analisis data", "level": "Pemula",
     "goal": "bisa menganalisis data penjualan sendiri tanpa rumus manual", "hours_per_week": 4},
    {"id": "materi-reksa-dana-modul-2", "skill": "materi", "silabus": "claude/silabus-reksa-dana.json", "module": 2},
    {"id": "materi-python-analisis-data-modul-3", "skill": "materi", "silabus": "claude/silabus-python-analisis-data.json",
     "module": 3},
]
MODELS = ["gemma3:4b", "qwen3:4b", "qwen3:8b"]
ID_WORDS = {"dan", "yang", "untuk", "dengan", "dari", "ini", "adalah", "tidak", "anda", "bisa", "akan", "pada", "di",
            "ke", "itu", "atau", "juga", "cara", "jika", "kalau", "setiap", "modul", "membuat", "menjelaskan"}
EN_WORDS = {"the", "and", "of", "to", "is", "in", "that", "for", "with", "this", "you", "are", "can", "how", "what"}


def language_share(spec: dict) -> float:
    """Share of common Indonesian words among common Indonesian + English words in all strings of the answer."""
    text = " ".join(_strings(spec)).lower()
    words = re.findall(r"[a-z]+", text)
    indonesian, english = sum(w in ID_WORDS for w in words), sum(w in EN_WORDS for w in words)
    return round(indonesian / (indonesian + english), 2) if indonesian + english else 0.0


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def run_task(task: dict, model: str, rebuild: bool) -> dict:
    folder = HERE / model.replace(":", "-")
    folder.mkdir(exist_ok=True)
    raw_path, page = folder / f"{task['id']}.answer.json", folder / f"{task['id']}.html"
    started = time.perf_counter()
    if task["skill"] == "silabus":
        gen = load("silabus_belajar", "generate_silabus")
        settings = gen.Settings(model=model)
        res = gen.generate(task["topic"], str(page), task["level"], task["goal"], task["hours_per_week"],
                           settings=settings, retries=1, from_json=str(raw_path) if rebuild else None,
                           save_json=None if rebuild else str(raw_path))
    else:
        gen = load("materi_belajar", "generate_materi")
        contract = gen.load_contract(str(HERE / task["silabus"]), task["module"])
        settings = gen.Settings(model=model, max_tokens=gen.MAX_TOKENS)
        res = gen.generate("", str(page), contract, settings=settings, retries=1,
                           from_json=str(raw_path) if rebuild else None, save_json=None if rebuild else str(raw_path))
    res["wall_seconds"] = round(time.perf_counter() - started, 1)
    try:
        answer = json.loads(raw_path.read_text(encoding="utf-8"))
        res["indonesian_share"] = language_share(answer)
    except (OSError, ValueError):
        res["indonesian_share"] = None
    res.update({"task": task["id"], "skill": task["skill"]})
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--tasks", default="", help="task ids, comma separated (default: all)")
    ap.add_argument("--rebuild", action="store_true", help="build again from saved answers, without calling a model")
    args = ap.parse_args()
    results_path = HERE / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8")) if results_path.exists() else {}
    chosen = [t for t in TASKS if not args.tasks or t["id"] in args.tasks.split(",")]
    for model in args.models.split(","):
        for task in chosen:
            print(f"== {model} / {task['id']}", flush=True)
            res = run_task(task, model, args.rebuild)
            if args.rebuild and f"{model}/{task['id']}" in results:   # keep the timing of the real run
                for key in ("stats", "wall_seconds", "attempts"):
                    res[key] = results[f"{model}/{task['id']}"].get(key, res.get(key))
            results[f"{model}/{task['id']}"] = res
            results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            stats = (res.get("stats") or [{}])[-1]
            print(f"   ok={res.get('ok')} attempts={res.get('attempts')} wall={res.get('wall_seconds')}s "
                  f"tokens={stats.get('tokens')} warnings={len(res.get('warnings', []))} "
                  f"error={res.get('error', '')[:120]}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
