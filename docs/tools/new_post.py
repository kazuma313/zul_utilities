"""
Membuat tulisan blog baru dari template, lengkap dengan tanggalnya.

Gunanya:
    Setiap tulisan blog wajib punya tanggal dan ringkasan, kalau tidak build
    dokumentasi gagal. Skrip ini menyalin docs/blog/_template.md ke folder
    tulisan, mengisi tanggal hari ini, judul, dan kategori, lalu membuat
    folder untuk gambar dan file pendukung tulisan itu.

Cara pakai:
    uv run python scripts/new_post.py "Judul tulisan"
    uv run python scripts/new_post.py "Judul tulisan" --kategori RAG --kategori Python
    uv run python scripts/new_post.py "Judul tulisan" --tanggal 2026-10-01

Hasil:
    docs/blog/posts/2026-10-07-judul-tulisan.md      tulisan baru
    docs/blog/resources/2026-10-07-judul-tulisan/    gambar dan file pendukung
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG_DIR = ROOT / "docs" / "blog"
DEFAULT_CATEGORY = "Catatan"
MAX_SLUG_LENGTH = 60

# --------------------------------------------------------------------------
# Nama File dan Isi Tulisan
# --------------------------------------------------------------------------


def slugify(title: str) -> str:
    """Ubah judul menjadi nama file: huruf kecil, tanpa aksen, dipisah tanda hubung."""
    ascii_title = (
        unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    return slug[:MAX_SLUG_LENGTH].rstrip("-")


def render(
    template: str, title: str, day: date, categories: list[str], folder: str
) -> str:
    """Isi penanda {{...}} di template dengan judul, tanggal, kategori, dan folder."""
    # Kategori ditulis sebagai string berkutip supaya nama yang memuat
    # titik dua atau tanda pagar tetap terbaca benar sebagai YAML.
    category_lines = "\n".join(
        f"  - {json.dumps(name, ensure_ascii=False)}" for name in categories
    )
    values = {
        "{{tanggal}}": day.isoformat(),
        "{{judul}}": title,
        "{{kategori}}": category_lines,
        "{{folder}}": folder,
    }
    for marker, value in values.items():
        template = template.replace(marker, value)
    return template


def create_post(
    title: str,
    day: date | None = None,
    categories: list[str] | None = None,
    blog_dir: Path = BLOG_DIR,
) -> tuple[Path, Path]:
    """
    Buat file tulisan dan folder resources-nya.

    Returns:
        Path file tulisan dan path folder resources.

    Raises:
        ValueError: judul tidak menghasilkan nama file, misalnya hanya tanda baca.
        FileExistsError: tulisan dengan tanggal dan judul yang sama sudah ada.
    """
    day = day or date.today()
    slug = slugify(title)
    if not slug:
        raise ValueError(f"Judul {title!r} tidak memuat huruf atau angka.")

    name = f"{day.isoformat()}-{slug}"
    post = blog_dir / "posts" / f"{name}.md"
    resources = blog_dir / "resources" / name
    if post.exists():
        raise FileExistsError(f"Tulisan {post} sudah ada.")

    template = (blog_dir / "_template.md").read_text(encoding="utf-8")
    content = render(
        template, title.strip(), day, categories or [DEFAULT_CATEGORY], name
    )

    post.parent.mkdir(parents=True, exist_ok=True)
    post.write_text(content, encoding="utf-8")
    resources.mkdir(parents=True, exist_ok=True)
    return post, resources


# --------------------------------------------------------------------------
# Command Line
# --------------------------------------------------------------------------


def parse_day(text: str) -> date:
    """Baca tanggal berformat YYYY-MM-DD untuk argumen --tanggal."""
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"tanggal {text!r} harus berformat YYYY-MM-DD, misalnya 2026-10-07"
        ) from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Buat tulisan blog baru dari template."
    )
    parser.add_argument("judul", help="judul tulisan, juga dipakai untuk nama file")
    parser.add_argument(
        "--tanggal",
        type=parse_day,
        default=None,
        help="tanggal tulisan (YYYY-MM-DD); bawaannya hari ini",
    )
    parser.add_argument(
        "--kategori",
        action="append",
        default=None,
        help=f"kategori tulisan, boleh diulang; bawaannya {DEFAULT_CATEGORY!r}",
    )
    args = parser.parse_args(argv)

    try:
        post, resources = create_post(args.judul, args.tanggal, args.kategori)
    except (ValueError, FileExistsError) as error:
        print(f"Gagal: {error}", file=sys.stderr)
        return 1

    print(f"Tulisan baru : {post.relative_to(ROOT).as_posix()}")
    print(f"Folder file  : {resources.relative_to(ROOT).as_posix()}/")
    print("Pratinjau    : uv run mkdocs serve, buka http://127.0.0.1:8001, menu Blog")
    return 0


if __name__ == "__main__":
    sys.exit(main())
