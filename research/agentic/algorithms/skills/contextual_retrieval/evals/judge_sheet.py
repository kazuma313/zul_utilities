"""A blind judging sheet for the contexts of several models, and the summary of the judge's scores.

    python evals/judge_sheet.py make --run gemma3-4b=runs/gemma3-4b.jsonl --run qwen3-8b=runs/qwen3-8b.jsonl \
        --every 3 --out runs/judge
    (the judge writes runs/judge/scores.json, see below)
    python evals/judge_sheet.py score --out runs/judge

`make` writes sheet.md: for every sampled chunk its section and text, then the contexts of all runs under
shuffled labels A, B, C ... so the judge cannot tell which model wrote which; key.json holds the labels.
A context the checks rejected is shown as "(no context: <reason>)" and is not scored.

scores.json, written by the judge: {"<chunk id>": {"A": [faithful, situates, specific, form, "note"], ...}}
with every score from 1 (bad) to 5 (good):
  faithful   every statement is supported by the document (1: invents a fact)
  situates   says which document, speaker or section the chunk is from (1: says nothing about it)
  specific   says what this chunk is about, so it can be told apart from its neighbours (1: generic)
  form       right language, one or two sentences, no filler (1: unusable as written)
`score` turns them into one row per model.  Standard library only.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

CRITERIA = ("faithful", "situates", "specific", "form")


def load(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def make(args) -> int:
    runs = {}
    for item in args.run:
        name, _, path = item.partition("=")
        runs[name] = {r["id"]: r for r in load(path)}
    ids = list(next(iter(runs.values())))
    sample = ids[::args.every]
    rng = random.Random(args.seed)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    key, lines = {}, [f"# Judging sheet: {len(sample)} chunks x {len(runs)} contexts, labels shuffled per chunk\n",
                     "Score every context 1-5 on: " + ", ".join(CRITERIA) + " (see judge_sheet.py).\n"]
    for chunk_id in sample:
        names = list(runs)
        rng.shuffle(names)
        key[chunk_id] = {chr(65 + i): name for i, name in enumerate(names)}
        first = runs[names[0]][chunk_id]
        lines.append(f"## {chunk_id}  ({first['title'][:70]})")
        lines.append(f"Section: {' > '.join(first['section'])}\n")
        lines.append("```text\n" + first["text"].strip() + "\n```\n")
        for label, name in key[chunk_id].items():
            record = runs[name][chunk_id]
            shown = record["context"] or f"(no context: {'; '.join(record['checks'])})"
            lines.append(f"- **{label}**: {shown}")
        lines.append("")
    (out / "sheet.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"sheet: {out / 'sheet.md'} ({len(sample)} chunks); key: {out / 'key.json'}")
    return 0


def score(args) -> int:
    out = Path(args.out)
    key = json.loads((out / "key.json").read_text(encoding="utf-8"))
    scores = json.loads((out / "scores.json").read_text(encoding="utf-8"))
    table: dict[str, dict] = {}
    for chunk_id, labels in key.items():
        for label, name in labels.items():
            row = table.setdefault(name, {"scored": 0, "no_context": 0, "low_faithful": [], **{c: 0.0 for c in CRITERIA}})
            given = scores.get(chunk_id, {}).get(label)
            if not given:
                row["no_context"] += 1
                continue
            row["scored"] += 1
            for criterion, value in zip(CRITERIA, given):
                row[criterion] += value
            if given[0] <= 3:
                row["low_faithful"].append(f"{chunk_id}: {given[4] if len(given) > 4 else ''}")
    print(f"{'model':<12} {'scored':>6} {'none':>5} " + " ".join(f"{c:>9}" for c in CRITERIA) + f" {'mean':>6}")
    for name, row in table.items():
        n = max(1, row["scored"])
        means = [row[c] / n for c in CRITERIA]
        row.update({c: round(m, 2) for c, m in zip(CRITERIA, means)}, mean=round(sum(means) / len(means), 2))
        print(f"{name:<12} {row['scored']:>6} {row['no_context']:>5} " + " ".join(f"{m:>9.2f}" for m in means) + f" {row['mean']:>6.2f}")
    (out / "summary.json").write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="command", required=True)
    m = sub.add_parser("make")
    m.add_argument("--run", action="append", required=True, metavar="NAME=FILE")
    m.add_argument("--every", type=int, default=3, help="judge every n-th chunk")
    m.add_argument("--seed", type=int, default=11)
    m.add_argument("--out", default="judge")
    s = sub.add_parser("score")
    s.add_argument("--out", default="judge")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    return make(args) if args.command == "make" else score(args)


if __name__ == "__main__":
    sys.exit(main())
