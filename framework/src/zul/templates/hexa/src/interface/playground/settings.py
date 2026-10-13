"""
Pengaturan playground, dibaca dari environment variable.

Gunanya:
    Playground adalah alat pengembangan: ia menampilkan argumen dan hasil
    setiap tool. Karena itu ia mati secara bawaan, dan hanya halaman dari
    alamat yang kamu izinkan yang boleh memanggilnya dari browser.

Cara pakai (di file `.env`):
    PLAYGROUND_ENABLED=true
    PLAYGROUND_ORIGINS=http://127.0.0.1:8001,http://localhost:8001

Contoh menambah alamat dokumentasi yang sudah dipublikasikan:
    PLAYGROUND_ORIGINS=http://127.0.0.1:8001,https://docs.example.com
"""

import os

from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------------------
# Nilai Bawaan
# --------------------------------------------------------------------------
#
# Alamat bawaan ialah situs dokumentasi Zul yang sudah terbit di
# zulkit.my.id, dan situs yang dijalankan di komputermu dengan
# mkdocs serve. Browser menganggap 127.0.0.1 dan localhost
# sebagai alamat berbeda, jadi keduanya didaftarkan.
#

DEFAULT_ORIGINS = (
    "https://zulkit.my.id",
    "http://127.0.0.1:8001",
    "http://localhost:8001",
)

TRUE_VALUES = ("1", "true", "yes", "on")


def playground_enabled() -> bool:
    """True jika `PLAYGROUND_ENABLED` diisi nilai benar seperti `true`."""
    return os.getenv("PLAYGROUND_ENABLED", "").strip().lower() in TRUE_VALUES


def playground_origins() -> list[str]:
    """Alamat halaman yang boleh memanggil API ini dari browser."""
    configured = os.getenv("PLAYGROUND_ORIGINS", "")
    origins = [origin.strip().rstrip("/") for origin in configured.split(",")]
    origins = [origin for origin in origins if origin]

    return origins or list(DEFAULT_ORIGINS)
