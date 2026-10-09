"""
Menyiapkan file bobot model YOLO di folder proyek.

Gunanya:
    Tanpa langkah ini, ultralytics mengunduh bobot yang belum ada ke folder
    tempat perintah dijalankan, bukan ke folder model, dan run berikutnya
    mengunduhnya lagi. Fungsi di sini mengunduh sekali ke path yang diminta.
    Unduhannya lewat zul.adapters.ultralytics. Butuh extra yolo dan
    koneksi ke GitHub release ultralytics.

Cara pakai:
    from zul.computer_vision.weights import fetch

    fetch("models/yolo11m-pose.pt")                  # unduh jika belum ada
    fetch("models/yolo11m-pose.pt", download=False)  # periksa saja

Untuk mengganti file yang terpotong, hapus filenya lalu jalankan lagi.
"""

from __future__ import annotations

from pathlib import Path


def fetch(path: str | Path, download: bool = True) -> tuple[bool, str]:
    """Pastikan `path` ada. Mengembalikan (bisa dipakai, keterangan yang terjadi)."""
    path = Path(path)
    if path.exists():
        return True, f"ada         {path.stat().st_size / 1e6:.0f} MB"
    if not download:
        return False, "belum ada"

    from ..adapters import ultralytics as yolo

    path.parent.mkdir(parents=True, exist_ok=True)
    yolo.download_asset(path)
    if not path.exists():
        return False, "GAGAL       bukan nama file bobot yang dirilis ultralytics"
    return True, f"diunduh     {path.stat().st_size / 1e6:.0f} MB"
