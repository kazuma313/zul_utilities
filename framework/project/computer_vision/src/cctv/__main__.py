"""
Menjalankan `python -m cctv`, sama dengan perintah `cctv`.

Gunanya:
    Berguna di dalam container atau virtual environment yang belum
    mendaftarkan perintah `cctv`.

Cara pakai:
    python -m cctv run configs/entrance.yaml --mode save
"""

from cctv.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
