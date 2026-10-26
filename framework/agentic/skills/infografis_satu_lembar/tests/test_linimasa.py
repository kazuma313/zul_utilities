"""Test susunan linimasa, tanpa jaringan dan tanpa model.

    pytest framework/agentic/skills/infografis_satu_lembar/tests

Butuh Node 18+; tanpa Node semuanya dilewati. Menggambar PNG butuh Edge atau Chrome dan
huruf dari jaringan, jadi hanya berjalan bila INFOGRAFIS_UJI_BROWSER=1.
"""

import copy
import importlib.util
import json
import os
import re
import shutil
import struct
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1]
CONTOH = SKILL / "contoh" / "majapahit_masa_pudar.json"
KOSONG = SKILL / "contoh" / "kosong_linimasa.json"

spec = importlib.util.spec_from_file_location(
    "infografis_linimasa_uji", SKILL / "infografis_satu_lembar_skill.py"
)
skill = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skill)

butuh_node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js tidak ada")


def isi_contoh() -> dict:
    return json.loads(CONTOH.read_text(encoding="utf-8"))


def ubah(mutasi) -> dict:
    isi = copy.deepcopy(isi_contoh())
    mutasi(isi)
    return isi


@pytest.fixture(autouse=True)
def folder_hasil(tmp_path, monkeypatch):
    monkeypatch.setenv("INFOGRAFIS_OUTPUT_DIR", str(tmp_path / "hasil"))
    return tmp_path / "hasil"


# --------------------------------------------------------------------------
# Pemeriksaan
# --------------------------------------------------------------------------


@butuh_node
def test_the_history_example_passes_the_check():
    laporan = skill.periksa_infografis(CONTOH.read_text(encoding="utf-8"))

    assert "LOLOS: 0 gagal, 0 peringatan" in laporan


@butuh_node
def test_the_blank_timeline_template_is_rejected_with_the_fix():
    laporan = skill.periksa_infografis(KOSONG.read_text(encoding="utf-8"))

    assert "BELUM LOLOS" in laporan
    assert "harus tahun berupa bilangan bulat" in laporan


def tukar_periode(c):
    c["periode"][1]["mulai"] = 1480


MASALAH = {
    "masa tidak berurutan": (tukar_periode, "harus 1478, sama dengan akhir masa sebelumnya"),
    "selesai sebelum mulai": (
        lambda c: c["periode"][0].update(selesai=1300),
        "harus lebih besar dari mulai (1389)",
    ),
    "tahun berupa teks": (
        lambda c: c["periode"][0].update(mulai="1389"),
        "harus tahun berupa bilangan bulat",
    ),
    "jumlah masa": (
        lambda c: c.update(periode=c["periode"][:2]),
        "harus berisi tepat 3 masa berurutan",
    ),
    "jumlah poin": (
        lambda c: c["periode"][0].update(poin=["satu saja"]),
        "harus berisi tepat 2 butir",
    ),
    "peristiwa di luar pita": (
        lambda c: c["peristiwa"][0].update(tahun=1300),
        "di dalam pita waktu (1389 sampai 1815)",
    ),
    "sampai sebelum tahun": (
        lambda c: c["peristiwa"][1].update(sampai=1300),
        "tidak lebih kecil dari tahun mulai",
    ),
    "titik di luar rentang": (
        lambda c: c["peristiwa"][1].update(titik=[1395, 1600]),
        "masing-masing di antara tahun dan sampai",
    ),
    "terlalu sedikit peristiwa": (
        lambda c: c.update(peristiwa=c["peristiwa"][:2]),
        "harus berisi 3 sampai 7 peristiwa",
    ),
    "ikon tidak ada": (
        lambda c: c["peristiwa"][0].update(ikon="rocket"),
        'nama ikon "rocket" tidak ada',
    ),
    "jumlah tujuan": (
        lambda c: c["sebaran"].update(tujuan=c["sebaran"]["tujuan"][:2]),
        "harus berisi tepat 3 tujuan",
    ),
    "tujuan utama di luar daftar": (
        lambda c: c["sebaran"].update(utama=3),
        "harus 0, 1, atau 2",
    ),
    "tanpa sumber": (lambda c: c.update(sumber="x"), "sebutkan sumbernya"),
    "judul terlalu panjang": (
        lambda c: c["kepala"].update(judul_1="Masa Pudar Yang Panjang"),
        "terlalu panjang",
    ),
    "kata kabur": (
        lambda c: c["periode"][2]["poin"].__setitem__(0, "Kerajaan terbaik di Jawa"),
        'kata "terbaik" tidak jelas',
    ),
    "emoji": (lambda c: c["kepala"].update(tujuan="Dari Trowulan 🔥"), "emoji"),
    "susunan tidak dikenal": (
        lambda c: c.update(susunan="spiral"),
        "harus salah satu dari: produk, linimasa",
    ),
}


@butuh_node
@pytest.mark.parametrize("kasus", sorted(MASALAH))
def test_each_known_mistake_is_rejected_with_a_message_that_names_the_fix(kasus):
    mutasi, pesan = MASALAH[kasus]

    laporan = skill.periksa_infografis(ubah(mutasi))

    assert "BELUM LOLOS" in laporan, kasus
    assert pesan in laporan, kasus


# --------------------------------------------------------------------------
# Menggambar
# --------------------------------------------------------------------------


def html_dari(isi, folder_hasil) -> str:
    skill.buat_infografis(isi, "uji", tanpa_gambar=True)
    return (folder_hasil / "uji" / "infografis.html").read_text(encoding="utf-8")


@butuh_node
def test_the_durations_and_the_total_are_computed_from_the_years(folder_hasil):
    html = html_dari(isi_contoh(), folder_hasil)

    for angka in ("89", "49", "288", "426"):
        assert f">{angka}<" in html or f">{angka} tahun<" in html, angka
    assert "1389–1815" in html
    assert "undefined" not in html


@butuh_node
def test_other_years_give_other_numbers_without_the_model_writing_them(folder_hasil):
    def periode_lain(c):
        for masa, (mulai, selesai) in zip(
            c["periode"], [(1000, 1100), (1100, 1150), (1150, 1400)]
        ):
            masa.update(mulai=mulai, selesai=selesai)
        c["peristiwa"] = [
            {"tahun": 1000, "teks": "Awal", "ikon": "mahkota"},
            {"tahun": 1100, "teks": "Tengah", "ikon": "api"},
            {"tahun": 1400, "teks": "Akhir", "ikon": "pohon"},
        ]

    html = html_dari(ubah(periode_lain), folder_hasil)

    for angka in ("100", "50", "250", "400"):
        assert f">{angka}<" in html or f">{angka} tahun<" in html, angka
    assert ">426<" not in html


@butuh_node
def test_events_are_drawn_in_year_order_whatever_the_input_order(folder_hasil):
    def balik(c):
        c["peristiwa"].reverse()

    html = html_dari(ubah(balik), folder_hasil)

    urutan = [int(t) for t in re.findall(r'data-teks="b0-p\d+-tahun"[^>]*>(\d{4})', html)]
    assert urutan == sorted(urutan)
    assert len(urutan) == 6


@butuh_node
def test_text_is_escaped_in_the_timeline(folder_hasil):
    def teks_berbahaya(c):
        c["peristiwa"][0]["teks"] = "<b>wafat</b> & pergi"

    html = html_dari(ubah(teks_berbahaya), folder_hasil)

    assert "&lt;b&gt;wafat&lt;/b&gt; &amp; pergi" in html
    assert "<b>wafat</b>" not in html


@butuh_node
def test_a_failing_timeline_draws_nothing(folder_hasil):
    laporan = skill.buat_infografis(ubah(tukar_periode), "uji", tanpa_gambar=True)

    assert "BELUM DIGAMBAR" in laporan
    assert not (folder_hasil / "uji" / "infografis.html").exists()


def png_ukuran(berkas: Path) -> tuple[int, int]:
    data = berkas.read_bytes()[:24]
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


@butuh_node
@pytest.mark.skipif(
    os.environ.get("INFOGRAFIS_UJI_BROWSER") != "1",
    reason="menggambar PNG butuh Edge atau Chrome dan huruf dari jaringan",
)
def test_the_timeline_png_is_4_by_5_and_the_text_does_not_overlap(folder_hasil):
    laporan = skill.buat_infografis(isi_contoh(), "uji")

    assert png_ukuran(folder_hasil / "uji" / "infografis.png") == (2160, 2700)
    assert "tidak ada teks yang bertumpuk" in laporan
