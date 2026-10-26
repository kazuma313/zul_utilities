"""Pembungkus Python untuk skill infografis satu lembar 4:5.

Skrip yang memeriksa dan menggambar ada di `scripts/*.mjs` (Node 18+, tanpa paket).
File ini hanya menjalankannya dari Python dan dari agent LangChain:

    from skills.infografis_satu_lembar.infografis_satu_lembar_skill import (
        buat_infografis, periksa_infografis)

    laporan = periksa_infografis(isi_json)          # LOLOS atau GAGAL beserta perbaikannya
    hasil = buat_infografis(isi_json, "produkku")   # hasil/produkku/infografis.png, .pdf, .html

Susunan dipilih dari isian "susunan" di dalam JSON: "produk" (bawaan) atau "linimasa".
`isi_json` boleh berupa teks JSON, teks JSON yang dibungkus tanda ``` atau diberi kalimat
pembuka (model kecil sering begitu), atau dict. Semua fungsi mengembalikan teks pendek
yang bisa dibaca model, dan tidak pernah melempar exception.

Berkas hasil ditulis di bawah `INFOGRAFIS_OUTPUT_DIR` (bawaan `./hasil`), di subfolder
yang namanya hanya huruf, angka, `_`, `-`, dan `.`. Nama folder dari model tidak bisa
keluar dari folder itu.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent
SCRIPTS = SKILL / "scripts"
TIMEOUT_DETIK = 180
NAMA_FOLDER = re.compile(r"[\w.-]{1,60}")


def _ambil_json(isi) -> tuple[dict | None, str]:
    """JSON dari dict atau teks, dengan membuang pagar kode dan kalimat di sekitarnya."""
    if isinstance(isi, dict):
        return isi, ""
    teks = str(isi).strip()
    teks = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", teks)
    awal, akhir = teks.find("{"), teks.rfind("}")
    if awal == -1 or akhir <= awal:
        return None, "GAGAL      isian bukan JSON. Jawab hanya dengan JSON seperti contoh/kosong.json."
    try:
        data = json.loads(teks[awal : akhir + 1])
    except json.JSONDecodeError as galat:
        return None, (
            f"GAGAL      JSON rusak di baris {galat.lineno}: {galat.msg}. "
            "Biasanya karena koma kurang atau berlebih, atau tanda kutip tidak berpasangan."
        )
    return data, ""


def _jalankan(argumen: list[str]) -> tuple[int, str]:
    node = shutil.which("node")
    if node is None:
        return 127, (
            "Node.js tidak ditemukan. Pasang Node 18 atau lebih baru "
            "(https://nodejs.org), lalu coba lagi."
        )
    try:
        selesai = subprocess.run(
            [node, *argumen],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=TIMEOUT_DETIK,
            cwd=SKILL,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 124, f"Perintah melebihi {TIMEOUT_DETIK} detik dan dihentikan."
    return selesai.returncode, (selesai.stdout + selesai.stderr).strip()


def _tulis(data: dict, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    berkas = folder / "isi.json"
    berkas.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return berkas


def periksa_infografis(isi_json) -> str:
    """Periksa isi infografis tanpa menggambar.

    Mengembalikan baris GAGAL atau PERINGATAN beserta cara memperbaikinya, lalu LOLOS atau
    BELUM LOLOS. Perbaiki yang GAGAL, lalu panggil lagi sampai LOLOS.
    """
    data, galat = _ambil_json(isi_json)
    if data is None:
        return galat
    with tempfile.TemporaryDirectory(prefix="infografis-") as sementara:
        berkas = _tulis(data, Path(sementara))
        _, keluaran = _jalankan([str(SCRIPTS / "cek.mjs"), str(berkas)])
    return keluaran


def buat_infografis(
    isi_json, folder_keluar: str = "infografis", tanpa_gambar: bool = False
) -> str:
    """Periksa lalu gambar infografis: infografis.html, .png (2160x2700), dan .pdf.

    `folder_keluar` adalah nama folder saja, di bawah INFOGRAFIS_OUTPUT_DIR (bawaan ./hasil).
    `tanpa_gambar=True` hanya menulis infografis.html, tanpa Chrome atau Edge.
    Bila isinya belum lolos pemeriksaan, tidak ada yang digambar dan pesannya dikembalikan.
    """
    data, galat = _ambil_json(isi_json)
    if data is None:
        return galat
    if not NAMA_FOLDER.fullmatch(str(folder_keluar)) or str(folder_keluar) in {".", ".."}:
        return (
            "GAGAL      nama folder hanya boleh berisi huruf, angka, _, -, dan titik, "
            "tanpa garis miring."
        )
    dasar = Path(os.environ.get("INFOGRAFIS_OUTPUT_DIR", "hasil")).resolve()
    tujuan = dasar / str(folder_keluar)
    berkas = _tulis(data, tujuan)
    argumen = [str(SCRIPTS / "bangun.mjs"), str(berkas), "--keluar", str(tujuan)]
    if tanpa_gambar:
        argumen.append("--tanpa-gambar")
    kode, keluaran = _jalankan(argumen)
    dibuat = sorted(p.name for p in tujuan.glob("infografis.*"))
    if kode in (0, 3) and dibuat:
        keluaran += f"\nBerkas di {tujuan}: {', '.join(dibuat)}"
    return keluaran


def _buat_tool():
    try:
        from langchain_core.tools import tool
    except ImportError:  # pragma: no cover - langchain-core tidak ter-install
        return None, None

    @tool
    def periksa_infografis_tool(isi_json: str) -> str:
        """Periksa isi.json infografis satu lembar. Perbaiki baris GAGAL, ulangi sampai LOLOS."""
        return periksa_infografis(isi_json)

    @tool
    def buat_infografis_tool(isi_json: str, folder_keluar: str = "infografis") -> str:
        """Gambar infografis satu lembar 4:5 dari isi.json yang sudah LOLOS pemeriksaan."""
        return buat_infografis(isi_json, folder_keluar)

    return periksa_infografis_tool, buat_infografis_tool


periksa_infografis_tool, buat_infografis_tool = _buat_tool()

__all__ = [
    "periksa_infografis",
    "buat_infografis",
    "periksa_infografis_tool",
    "buat_infografis_tool",
]
