"""
Pemeriksa gaya komentar untuk repository ini: pembungkus zul.assistant.comment_style.

Gunanya:
    Logikanya tinggal di paket Zul, supaya MCP server Zul juga bisa memakainya.
    Tanpa argumen, file ini memeriksa semua folder yang mengikuti gaya kode
    Zul, jadi daftar foldernya tidak perlu diingat.

Cara pakai:
    uv run python framework/scripts/comment_style.py           # periksa semua
    uv run python framework/scripts/comment_style.py --fix     # lipat ulang
    uv run python framework/scripts/comment_style.py framework/src/zul/cli.py
"""

import sys
from pathlib import Path

from zul.assistant.comment_style import main

ROOT = Path(__file__).resolve().parents[2]
STYLED_FOLDERS = (
    "framework/src",
    "framework/tests",
    "framework/project",
    "framework/scripts",
    "docs/tools",
)


def run(argv: list[str]) -> int:
    """`main` dengan folder standar jika tidak ada file atau folder yang disebut."""
    if not [arg for arg in argv if not arg.startswith("-")]:
        argv = [str(ROOT / folder) for folder in STYLED_FOLDERS] + argv
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
