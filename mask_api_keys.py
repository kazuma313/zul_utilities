"""
mask_api_keys.py — Samarkan API key yang tak sengaja tertulis di repo.

Cara pakai:
    python mask_api_keys.py            # samarkan (buat backup .bak dulu)
    python mask_api_keys.py --dry-run  # hanya tampilkan yang akan diubah

Menyasar file .py, .ipynb, .md, .json, .yaml, .yml (kecuali .venv/.git).
Pola yang disamarkan: OpenAI-style key (sk-...), Google (AIza...),
GitHub (ghp_/gho_...), HuggingFace (hf_...), Tavily (tvly-...).
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

# (pola, pengganti)
PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"sk-[A-Za-z0-9_-]{15,}"), "sk-xxxxxxxxxxxxxxxxxxxxxx"),
    (re.compile(r"AIza[A-Za-z0-9_-]{20,}"), "AIzaxxxxxxxxxxxxxxxxxxxxxx"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "ghp_xxxxxxxxxxxxxxxxxxxx"),
    (re.compile(r"hf_[A-Za-z0-9]{20,}"), "hf_xxxxxxxxxxxxxxxxxxxx"),
    (re.compile(r"tvly-[A-Za-z0-9]{15,}"), "tvly-xxxxxxxxxxxxxxxx"),
]

EXTS = {".py", ".ipynb", ".md", ".json", ".yaml", ".yml", ".txt", ".env"}
SKIP_DIRS = {".venv", "venv", ".git", "__pycache__", "node_modules", ".mypy_cache"}


def iter_files(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in EXTS:
            if not any(part in SKIP_DIRS for part in p.parts):
                yield p


def mask_text(text: str) -> tuple[str, int]:
    total = 0
    for pattern, repl in PATTERNS:
        text, n = pattern.subn(repl, text)
        total += n
    return text, total


def main() -> None:
    parser = argparse.ArgumentParser(description="Samarkan API key di repo.")
    parser.add_argument("--root", default=".", help="folder root (default: .)")
    parser.add_argument("--dry-run", action="store_true", help="hanya laporkan")
    parser.add_argument("--no-backup", action="store_true", help="jangan buat .bak")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    changed_files = 0
    changed_keys = 0

    for path in iter_files(root):
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        masked, n = mask_text(original)
        if n == 0:
            continue
        changed_files += 1
        changed_keys += n
        rel = path.relative_to(root)
        print(f"{'[dry-run] ' if args.dry_run else ''}{rel}  ->  {n} key disamarkan")
        if not args.dry_run:
            if not args.no_backup:
                shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
            path.write_text(masked, encoding="utf-8")

    print("-" * 48)
    print(f"Total: {changed_keys} key di {changed_files} file"
          f"{' (dry-run, tidak ada perubahan ditulis)' if args.dry_run else ' disamarkan'}.")
    if changed_keys and not args.dry_run:
        print("Backup asli disimpan sebagai *.bak — hapus setelah diverifikasi.")
    print("⚠️  Ingat: key yang pernah ter-commit tetap harus DI-ROTATE/dicabut.")


if __name__ == "__main__":
    main()
