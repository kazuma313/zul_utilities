"""
Pemeriksa dan perapi gaya komentar: paragraf komentar berbentuk anak tangga.

Gunanya:
    Komentar di repository ini mengikuti gaya komentar Laravel: setiap baris
    sedikit lebih pendek dari baris sebelumnya, sehingga tepi kanannya turun
    seperti anak tangga. Skrip ini mencari paragraf komentar yang belum
    berbentuk begitu, lalu melipat ulang barisnya jika memungkinkan.

Cara pakai:
    python scripts/comment_style.py src tests           # periksa saja
    python scripts/comment_style.py src tests --fix     # lipat ulang barisnya

Contoh hasil:
    # Nilai resume ikut tersimpan di checkpoint. Karena itu keputusan harus
    # diperiksa sebelum agent dilanjutkan, sebab error yang muncul sesudah
    # titik interrupt akan terulang di setiap percobaan berikutnya.

Yang tidak disentuh:
    Baris pembatas (`# -----`), judul bagian, komentar satu baris, daftar
    (`# - butir`), contoh kode yang menjorok, dan komentar di akhir baris
    kode. Paragraf yang tidak bisa dilipat menjadi anak tangga dilaporkan
    supaya kalimatnya bisa kamu ubah sedikit.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import textwrap
import tokenize
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

# --------------------------------------------------------------------------
# Aturan Bentuk
# --------------------------------------------------------------------------
#
# Lebar baris pembatas adalah 76 karakter, sama dengan komentar blok di
# Laravel. Paragraf di bawahnya tidak boleh lebih lebar dari pembatas,
# dan setiap baris harus lebih pendek 1 sampai 6 karakter dari baris
# sebelumnya. Selisih yang dikejar adalah 3 karakter per baris.
#

MAX_LINE_WIDTH = 76
SHORTEST_STEP = 1
LONGEST_STEP = 6
IDEAL_STEP = 3

RULE_LINE = re.compile(r"^#\s?[-=─]{8,}\s*$")
PROSE_LINE = re.compile(r"^# \S")
LIST_ITEM = re.compile(r"^# (?:[-*•]|\d+[.)])\s")
DIRECTIVE = re.compile(r"^#\s*(?:noqa|type:|pragma|fmt:|pylint|ruff:|mypy:|!)")
METADATA_FENCE = re.compile(r"^# ///")
CODE_LINE = re.compile(
    r"^# (?:#"
    r"|import [\w.]+(?: as \w+)?\s*$"
    r"|from [\w.]+ import "
    r"|(?:def|class) \w+[(:]"
    r"|(?:return|raise|assert|print)\b.*[)\]\w\"']\s*$"
    r"|(?:if|elif|for|while|with|try|else|except|finally)\b.*:\s*$"
    r"|[\w.\[\]\"']+ = "
    r"|[\w.]+\(.*\)\s*$"
    r"|[)\]}]+,?\s*$)"
)

SKIPPED_DIRECTORIES = {".venv", "__pycache__", ".git", "site", "node_modules"}


@dataclass(frozen=True)
class Paragraph:
    """Satu paragraf komentar: baris pertamanya, indentasinya, dan isinya."""

    first_line: int
    indent: int
    lines: tuple[str, ...]

    @property
    def words(self) -> list[str]:
        return " ".join(self.lines).split()

    @property
    def max_text_width(self) -> int:
        return MAX_LINE_WIDTH - self.indent - len("# ")


# --------------------------------------------------------------------------
# Mencari Paragraf Komentar
# --------------------------------------------------------------------------


def find_paragraphs(source: str) -> list[Paragraph]:
    """Kembalikan paragraf komentar yang berdiri di barisnya sendiri."""
    paragraphs: list[Paragraph] = []
    current: list[tuple[int, int, str]] = []

    def close_paragraph() -> None:
        if current:
            first_line, indent, _ = current[0]
            texts = tuple(text for _, _, text in current)
            paragraphs.append(Paragraph(first_line, indent, texts))
            current.clear()

    # Blok metadata skrip (PEP 723) diapit baris `# ///`. Isinya dibaca
    # program lain baris demi baris, jadi tidak boleh ikut dilipat.
    inside_metadata = False

    for line_number, indent, comment in _own_line_comments(source):
        if METADATA_FENCE.match(comment):
            inside_metadata = not inside_metadata
            close_paragraph()
            continue

        if inside_metadata:
            continue

        continues = (
            current and current[-1][0] == line_number - 1 and current[-1][1] == indent
        )
        if not continues:
            close_paragraph()

        if _is_prose(comment):
            current.append((line_number, indent, comment[2:].strip()))
        else:
            close_paragraph()

    close_paragraph()

    return paragraphs


def _own_line_comments(source: str) -> list[tuple[int, int, str]]:
    """Komentar yang tidak berbagi baris dengan kode: (baris, kolom, teks)."""
    source_lines = source.splitlines()
    comments = []

    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue

        line_number, column = token.start
        if source_lines[line_number - 1][:column].strip() == "":
            comments.append((line_number, column, token.string))

    return comments


def _is_prose(comment: str) -> bool:
    return bool(
        PROSE_LINE.match(comment)
        and not RULE_LINE.match(comment)
        and not LIST_ITEM.match(comment)
        and not DIRECTIVE.match(comment)
        and not CODE_LINE.match(comment)
    )


# --------------------------------------------------------------------------
# Melipat Paragraf Menjadi Anak Tangga
# --------------------------------------------------------------------------


def is_staircase(lines: tuple[str, ...] | list[str], max_width: int) -> bool:
    """True jika setiap baris lebih pendek dari sebelumnya, dalam batas."""
    lengths = [len(line) for line in lines]
    steps = [upper - lower for upper, lower in pairwise(lengths)]
    even_steps = all(SHORTEST_STEP <= step <= LONGEST_STEP for step in steps)

    return lengths[0] <= max_width and even_steps and _is_wide_enough(lines, max_width)


def _is_wide_enough(lines: tuple[str, ...] | list[str], max_width: int) -> bool:
    """False untuk anak tangga yang sempit dan tinggi: sah, tapi sulit dibaca."""
    return len(lines) < 3 or len(lines[0]) >= max_width * 4 // 5


def fold_into_staircase(words: list[str], max_width: int) -> list[str] | None:
    """
    Cari pelipatan baris terbaik untuk sederet kata.

    Returns:
        Daftar baris berbentuk anak tangga, atau None jika kata-katanya
        tidak bisa dilipat begitu tanpa mengubah kalimat.
    """
    best: tuple[float, list[str]] | None = None

    # Jumlah baris dibatasi paling banyak satu di atas pelipatan biasa,
    # supaya paragraf tidak berubah menjadi anak tangga yang sempit
    # dan tinggi hanya demi memenuhi aturan selisih panjangnya.
    most_lines = len(textwrap.wrap(" ".join(words), max_width)) + 1

    def place(start: int, previous_length: int | None, lines: list[str]) -> None:
        nonlocal best

        if len(lines) >= most_lines:
            return

        for end in range(start + 1, len(words) + 1):
            line = " ".join(words[start:end])

            if previous_length is None:
                if len(line) > max_width:
                    break
            else:
                if len(line) > previous_length - SHORTEST_STEP:
                    break
                if len(line) < previous_length - LONGEST_STEP:
                    continue

            if end < len(words):
                place(end, len(line), [*lines, line])
                continue

            candidate = [*lines, line]
            if not _is_wide_enough(candidate, max_width):
                continue

            cost = _cost(candidate, max_width)
            if best is None or cost < best[0]:
                best = (cost, candidate)

    place(0, None, [])

    return best[1] if best else None


def _cost(lines: list[str], max_width: int) -> float:
    """Makin kecil makin rapi: selisih dekat 3, baris sedikit, lebar terpakai."""
    lengths = [len(line) for line in lines]
    uneven_steps = sum(
        abs((upper - lower) - IDEAL_STEP) for upper, lower in pairwise(lengths)
    )
    unused_width = (max_width - lengths[0]) / 4

    return uneven_steps + unused_width + 3 * len(lines)


# --------------------------------------------------------------------------
# Memeriksa dan Memperbaiki File
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """Paragraf yang belum berbentuk anak tangga, beserta usulan barisnya."""

    path: Path
    paragraph: Paragraph
    folded: list[str] | None


def check_file(path: Path) -> list[Finding]:
    source = path.read_text(encoding="utf-8")
    findings = []

    for paragraph in find_paragraphs(source):
        fits = len(paragraph.lines[0]) <= paragraph.max_text_width
        if len(paragraph.lines) == 1 and fits:
            continue
        if is_staircase(paragraph.lines, paragraph.max_text_width):
            continue

        folded = fold_into_staircase(paragraph.words, paragraph.max_text_width)
        findings.append(Finding(path, paragraph, folded))

    return findings


def fix_file(path: Path, findings: list[Finding]) -> int:
    """Tulis ulang paragraf yang punya usulan. Mengembalikan jumlahnya."""
    lines = path.read_text(encoding="utf-8").split("\n")
    fixable = [finding for finding in findings if finding.folded]

    # Paragraf diganti dari bawah ke atas supaya nomor baris paragraf yang
    # belum diganti tidak bergeser saat jumlah barisnya ikut berubah.
    for finding in sorted(fixable, key=lambda f: -f.paragraph.first_line):
        paragraph = finding.paragraph
        start = paragraph.first_line - 1
        prefix = " " * paragraph.indent + "# "
        replacement = [prefix + line for line in finding.folded]
        lines[start : start + len(paragraph.lines)] = replacement

    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    return len(fixable)


def python_files(targets: list[str]) -> list[Path]:
    files: list[Path] = []

    for target in map(Path, targets):
        if target.is_file():
            files.append(target)
            continue

        files.extend(
            path
            for path in sorted(target.rglob("*.py"))
            if not SKIPPED_DIRECTORIES.intersection(path.parts)
        )

    return files


# --------------------------------------------------------------------------
# Perintah
# --------------------------------------------------------------------------


def describe(finding: Finding) -> str:
    paragraph = finding.paragraph
    header = f"{finding.path}:{paragraph.first_line}"
    current = "\n".join(f"    {len(line):>3} | {line}" for line in paragraph.lines)

    if finding.folded:
        return f"{header}  bisa dilipat ulang dengan --fix\n{current}"

    return (
        f"{header}  ubah kalimatnya: tidak ada pelipatan yang berbentuk"
        f" anak tangga (lebar maksimum {paragraph.max_text_width})\n{current}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("targets", nargs="+", help="File atau folder Python.")
    parser.add_argument("--fix", action="store_true", help="Lipat ulang barisnya.")
    options = parser.parse_args(argv)

    remaining = 0
    for path in python_files(options.targets):
        findings = check_file(path)

        if options.fix and findings:
            fixed = fix_file(path, findings)
            print(f"{path}: {fixed} paragraf dilipat ulang")
            findings = check_file(path)

        for finding in findings:
            print(describe(finding))
            remaining += 1

    if remaining:
        print(f"\n{remaining} paragraf komentar belum berbentuk anak tangga.")
        return 1

    print("Semua paragraf komentar berbentuk anak tangga.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
