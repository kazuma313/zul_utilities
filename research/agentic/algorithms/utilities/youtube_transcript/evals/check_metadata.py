"""Check transcript files written by scripts/yt_transcripts.py: enough metadata, a complete transcript, a valid header.

    python evals/check_metadata.py transcripts
    python evals/check_metadata.py transcripts --min-coverage 0.95

One row per file.  A file passes when its header is valid YAML with every field in REQUIRED, the
captions reach at least --min-coverage of the video, the transcript has words, and no sound markers
such as [musik] are left.  Exit code 1 when a file fails.  Standard library only (PyYAML, when
installed, also checks that the header is valid YAML).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED = ("name", "description", "title", "channel", "url", "video_id", "upload_date", "duration", "category",
            "transcript_language", "captions", "caption_coverage", "words")


def read_header(text: str) -> tuple[dict, str]:
    """(header fields, body) of one file."""
    match = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not match:
        raise ValueError("no header between --- lines")
    header, body = match.groups()
    try:
        import yaml
    except ImportError:
        yaml = None
    if yaml is not None:
        return yaml.safe_load(header), body
    fields = {}
    for line in header.splitlines():
        key, _, value = line.partition(": ")
        try:
            fields[key] = json.loads(value)
        except ValueError:
            fields[key] = value
    return fields, body


def check(path: Path, min_coverage: float) -> tuple[dict, list[str]]:
    fields, body = read_header(path.read_text(encoding="utf-8"))
    problems = [f"no {key}" for key in REQUIRED if fields.get(key) in (None, "", [])]
    if len(str(fields.get("name", ""))) > 64 or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(fields.get("name", ""))):
        problems.append("name is not a slug of at most 64 characters")
    if len(str(fields.get("description", ""))) > 1024:
        problems.append("description longer than 1024 characters")
    coverage = fields.get("caption_coverage")
    if isinstance(coverage, (int, float)) and coverage < min_coverage:
        problems.append(f"captions reach only {coverage:.0%} of the video")
    if "## Transcript" not in body or (fields.get("words") or 0) < 50:
        problems.append("no transcript text")
    leftovers = re.findall(r"\[(?:musik|music|tertawa|laughter|applause|tepuk tangan)\]", body, re.I)
    if leftovers:
        problems.append(f"{len(leftovers)} sound markers left, e.g. {leftovers[0]}")
    if fields.get("metadata_source") != "yt-dlp":
        problems.append(f"metadata from {fields.get('metadata_source')}: no duration, category or chapters")
    return fields, problems


def minutes(fields: dict) -> float:
    return (fields.get("duration_seconds") or 0) / 60


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("folder", help="output folder of yt_transcripts.py")
    ap.add_argument("--min-coverage", type=float, default=0.9)
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    files = sorted(Path(args.folder).glob("*.txt"))
    files = [f for f in files if f.name != "failed_urls.txt"]
    if not files:
        print(f"no transcript files in {args.folder}")
        return 1
    failed = 0
    print(f"{'video':<12} {'ok':<4} {'duration':>8} {'words':>6} {'wpm':>4} {'cover':>5} {'chap':>4} {'tags':>4}  category / captions / title")
    for path in files:
        try:
            fields, problems = check(path, args.min_coverage)
        except Exception as error:  # noqa: BLE001 - a broken file is a finding
            fields, problems = {}, [f"unreadable: {error}"]
        failed += bool(problems)
        wpm = round(fields.get("words", 0) / minutes(fields)) if minutes(fields) else 0
        print(f"{str(fields.get('video_id', path.stem[-11:])):<12} {'yes' if not problems else 'NO':<4} {str(fields.get('duration', '')):>8} "
              f"{fields.get('words', 0):>6} {wpm:>4} {str(fields.get('caption_coverage', '')):>5} {len(fields.get('chapters') or []):>4} "
              f"{len(fields.get('tags') or []):>4}  {fields.get('category', '')} / {fields.get('captions', '')} "
              f"{fields.get('transcript_language', '')} / {str(fields.get('title', ''))[:60]}")
        for problem in problems:
            print(f"{'':<12} - {problem}")
    print(f"\n{len(files) - failed} of {len(files)} files have enough metadata and a complete transcript")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
