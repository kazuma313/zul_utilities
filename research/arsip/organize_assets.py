"""
organize_assets.py — Satukan SEMUA aset ke satu folder induk di root proyek:
    ./assets/

Yang dilakukan:
  1. Memindahkan seluruh isi  tutorial/assets/**  ->  assets/**  (struktur dijaga).
  2. Memindahkan aset yang masih tercecer di dalam tutorial/ (mis.
     tutorial/ocr/realism_example.mp4) -> assets/ocr/realism_example.mp4.
  3. Menghapus folder tutorial/assets yang sudah kosong.

Notebook (.ipynb) dan kode (.py) DI LUAR tutorial/assets tidak dipindahkan.
(File .py / .md yang memang berada di dalam tutorial/assets tetap ikut pindah.)

Cara pakai:
    python organize_assets.py --dry-run   # lihat rencana pemindahan
    python organize_assets.py             # jalankan pemindahan
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

# Ekstensi yang dianggap "aset" untuk file yang tercecer di luar tutorial/assets
ASSET_EXTS = {
    ".mp4", ".mov", ".avi", ".mkv", ".webm",
    ".mp3", ".wav", ".ogg", ".flac",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".tiff",
    ".pdf", ".html", ".htm", ".csv", ".tsv",
    ".ppt", ".pptx", ".xlsx", ".xls", ".docx", ".doc",
}


def plan_moves(root: Path, tutorial: Path, dest: Path):
    """Kembalikan daftar (sumber, tujuan) yang akan dipindahkan."""
    old_assets = tutorial / "assets"
    moves: list[tuple[Path, Path]] = []

    for path in tutorial.rglob("*"):
        if not path.is_file():
            continue
        if dest in path.parents or path == dest:
            continue  # sudah di folder tujuan

        if old_assets in path.parents:
            # Aturan 1: semua file di tutorial/assets ikut pindah
            target = dest / path.relative_to(old_assets)
        elif path.suffix.lower() in ASSET_EXTS:
            # Aturan 2: aset tercecer di luar tutorial/assets
            target = dest / path.relative_to(tutorial)
        else:
            continue  # notebook / kode di luar assets -> biarkan

        moves.append((path, target))
    return moves


def main() -> None:
    parser = argparse.ArgumentParser(description="Satukan aset ke ./assets/.")
    parser.add_argument("--root", default=".", help="root proyek (default: .)")
    parser.add_argument("--dry-run", action="store_true", help="hanya tampilkan rencana")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    tutorial = root / "tutorial"
    dest = root / "assets"
    if not tutorial.is_dir():
        raise SystemExit(f"❌ Folder tidak ditemukan: {tutorial}")

    moves = plan_moves(root, tutorial, dest)
    if not moves:
        print("✅ Tidak ada aset yang perlu dipindahkan. Semua sudah rapi.")
        return

    dest.mkdir(exist_ok=True)
    moved = 0
    for src, target in moves:
        rel_src = src.relative_to(root)
        rel_target = target.relative_to(root)
        if target.exists():
            print(f"⚠️  Lewati (sudah ada di tujuan): {rel_target}")
            continue
        print(f"{'[dry-run] ' if args.dry_run else ''}move  {rel_src}  ->  {rel_target}")
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(target))
        moved += 1

    # Bersihkan folder kosong bekas tutorial/assets
    if not args.dry_run:
        old_assets = tutorial / "assets"
        for d in sorted(old_assets.rglob("*"), reverse=True):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
        if old_assets.is_dir() and not any(old_assets.iterdir()):
            old_assets.rmdir()

    print("-" * 56)
    print(f"Total: {moved} file "
          f"{'akan dipindahkan (dry-run)' if args.dry_run else 'dipindahkan ke ./assets/'}.")
    print("💡 Notebook yang memakai path 'tutorial/assets/...' perlu diubah ke 'assets/...'.")


if __name__ == "__main__":
    main()
