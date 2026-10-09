"""
Menyiapkan file bobot model RF-DETR di folder proyek.

Gunanya:
    Tanpa langkah ini, RF-DETR mengunduh bobot ke folder cache di home
    directory, ~/.roboflow/models. Fungsi di sini mengunduh sekali ke path
    yang diminta, misalnya folder models di proyek, dan memeriksa MD5-nya.
    Unduhannya lewat zul.adapters.rfdetr. Butuh extra detection dan koneksi
    ke storage rilis RF-DETR.

Cara pakai:
    from zul.computer_vision.weights import fetch

    path = "models/rf-detr-keypoint-preview-xlarge.pth"
    fetch(path)                  # unduh jika belum ada
    fetch(path, download=False)  # periksa saja

Nama file harus sama dengan nama bobot rilis RF-DETR, misalnya hasil
zul.adapters.rfdetr.default_weights("keypoint"). Untuk mengganti file
yang terpotong, hapus filenya lalu jalankan lagi.
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

    from ..adapters import rfdetr as rfdetr_adapter

    rfdetr_adapter.download_weights(path)
    if not path.exists():
        return False, "GAGAL       bukan nama file bobot yang dirilis RF-DETR"
    return True, f"diunduh     {path.stat().st_size / 1e6:.0f} MB"
