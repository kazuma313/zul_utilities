"""Automatic measures of every answer in this folder (the reference and the three local models).

    uv run python research/learning_skills_comparison/score_outputs.py      # writes metrics.json, prints a table
    uv run python research/learning_skills_comparison/score_outputs.py run1 # the first run, before the schema limits

What a script can count without judging content: shape (modules, chapters, questions), how many
repairs the builders made, which rules their checks found broken, quiz questions that ask for a
definition, "Lihat bab N" that points to a chapter teaching another objective, written arithmetic
that does not add up.  Whether facts are right is judged by reading (review.json).
"""

from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent / "agentic" / "algorithms" / "skills"
SOURCES = {"claude": "claude", "gemma3:4b": "gemma3-4b", "qwen3:4b": "qwen3-4b", "qwen3:8b": "qwen3-8b"}
DEFINITION = re.compile(r"^(apa itu|apa yang dimaksud|apa arti|apa fungsi|apa definisi|apa pengertian|apakah yang dimaksud)",
                        re.I)


def load(skill: str, module: str):
    scripts = str(SKILLS / skill / "scripts")
    for name in ("local_model", "build_silabus", "build_materi"):
        sys.modules.pop(name, None)
    sys.path.insert(0, scripts)
    try:
        return importlib.import_module(module)
    finally:
        sys.path.remove(scripts)


def answer_path(source: str, task: str, run: Path) -> Path:
    if source == "claude":
        return HERE / "claude" / f"{task}.json"
    return run / SOURCES[source] / f"{task}.answer.json"


def silabus_metrics(raw: dict) -> dict:
    bs = load("silabus_belajar", "build_silabus")
    spec, warnings = bs.normalize(raw)
    modules = [m for s in spec["stages"] for m in s["modules"]]
    raw_modules = [m for s in raw.get("stages", []) for m in s.get("modules", [])]
    hours = [m.get("hours") for m in raw_modules]
    return {
        "modules": len(modules), "stages": len(spec["stages"]), "outcomes": len(spec["outcomes"]),
        "hours_written": hours, "all_one_hour": all(h == 1 for h in hours),
        "verb_repairs": sum("checkable verb" in w for w in warnings),
        "order_warnings": sum("is taught in module" in w for w in warnings),
        "money_rule_warnings": sum(w.startswith("money topic") for w in warnings),
        "other_warnings": [w for w in warnings if not ("checkable verb" in w or "is taught in module" in w
                                                        or w.startswith("money topic"))],
        "result_over_45": sum(len(m.get("result", "")) > 45 for m in raw_modules),
        "questions_without_mark": sum(not str(m.get("question", "")).strip().endswith("?") for m in raw_modules),
    }


def materi_metrics(raw: dict, contract: dict) -> dict:
    bm = load("materi_belajar", "build_materi")
    spec, warnings = bm.normalize(raw, contract)
    chapters = spec["chapters"]
    wrong_refs = 0
    for item, built in zip([q for q in raw.get("quiz", []) if isinstance(q, dict)], spec["quiz"]):
        found = re.search(r"\bbab\s*(\d+)", str(item.get("why", "")), re.I)
        if found and "modul" not in str(item.get("why", "")).lower():
            number = int(found.group(1))
            if not 1 <= number <= len(chapters) or chapters[number - 1]["objective"] != built["objective"]:
                wrong_refs += 1
    long_steps = sum(len(s) > 38 for c in raw.get("chapters", []) for s in c.get("steps", []))
    return {
        "chapters": len(chapters), "questions": len(spec["quiz"]), "exercises": len(spec["exercises"]),
        "terms": sum(len(c["terms"]) for c in chapters), "demo_steps": len(spec["demo"]["steps"]),
        "definition_questions": sum(bool(DEFINITION.match(q["q"])) for q in spec["quiz"]),
        "why_points_elsewhere": wrong_refs,
        "first_question_reviews_previous": bool(re.search(r"modul (sebelumnya|1|2)\b",
                                                          spec["quiz"][0]["why"].lower())) if spec["quiz"] else False,
        "prior_written": bool(str(raw.get("prior") or "").strip()),     # the model's, not the builder's fallback
        "steps_over_38_characters": long_steps,
        "arithmetic_warnings": [w for w in warnings if w.startswith("arithmetic")],
        "coverage_warnings": [w for w in warnings if "objective" in w and ("taught" in w or "tested" in w)],
        "other_warnings": [w for w in warnings if not w.startswith("arithmetic")
                           and not ("objective" in w and ("taught" in w or "tested" in w))],
    }


def main() -> int:
    bm = load("materi_belajar", "build_materi")
    contracts = {
        "materi-reksa-dana-modul-2": bm.load_contract(str(HERE / "claude" / "silabus-reksa-dana.json"), 2),
        "materi-python-analisis-data-modul-3": bm.load_contract(str(HERE / "claude" / "silabus-python-analisis-data.json"), 3),
    }
    run = HERE / sys.argv[1] if len(sys.argv) > 1 else HERE
    results = json.loads((run / "results.json").read_text(encoding="utf-8")) if (run / "results.json").exists() else {}
    metrics = {}
    for source in SOURCES:
        for task in ["silabus-reksa-dana", "silabus-python-analisis-data", *contracts]:
            path = answer_path(source, task, run)
            if not path.exists():
                continue
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except ValueError:                      # the answer that never closed its JSON
                metrics[f"{source}/{task}"] = {"not_json": True}
                continue
            if task.startswith("silabus"):
                # the Claude references were written without module numbers; normalize adds them
                row = silabus_metrics(raw)
            else:
                row = materi_metrics(raw, contracts[task])
            record = results.get(f"{source}/{task}", {})
            stats = (record.get("stats") or [{}])[-1]
            row.update({"seconds": record.get("wall_seconds"), "tokens": stats.get("tokens"),
                        "attempts": record.get("attempts"),
                        "indonesian_share": record.get("indonesian_share")})
            metrics[f"{source}/{task}"] = row
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    for key, row in metrics.items():
        short = {k: v for k, v in row.items() if not isinstance(v, list) or k == "hours_written"}
        print(key, short)
        for k in ("other_warnings", "arithmetic_warnings", "coverage_warnings"):
            for w in row.get(k, []):
                print("    -", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
