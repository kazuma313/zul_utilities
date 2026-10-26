"""Test skill infografis satu lembar, tanpa jaringan dan tanpa model.

    pytest framework/agentic/skills/infografis_satu_lembar/tests

Test memanggil skrip Node yang asli lewat pembungkus Python, jadi butuh Node 18+.
Tanpa Node, semuanya dilewati. Menggambar PNG dan PDF butuh Edge atau Chrome dan
huruf dari jaringan, jadi hanya berjalan bila INFOGRAFIS_UJI_BROWSER=1.
"""

import copy
import importlib.util
import json
import os
import shutil
import struct
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1]
CONTOH = SKILL / "contoh" / "tanam_kota.json"
KOSONG = SKILL / "contoh" / "kosong.json"

spec = importlib.util.spec_from_file_location(
    "infografis_satu_lembar_skill_uji", SKILL / "infografis_satu_lembar_skill.py"
)
skill = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skill)

butuh_node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js tidak ada")


def isi_contoh() -> dict:
    return json.loads(CONTOH.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def folder_hasil(tmp_path, monkeypatch):
    monkeypatch.setenv("INFOGRAFIS_OUTPUT_DIR", str(tmp_path / "hasil"))
    return tmp_path / "hasil"


# --------------------------------------------------------------------------
# Isi folder skill
# --------------------------------------------------------------------------


def test_the_skill_follows_the_pool_format():
    for nama in ("METADATA.md", "SKILL.md", "infografis_satu_lembar_skill.py"):
        assert (SKILL / nama).is_file(), nama
    for sisi in ("METADATA.md", "SKILL.md"):
        awal = (SKILL / sisi).read_text(encoding="utf-8").split("---")[1]
        assert "name: infografis-satu-lembar" in awal


def test_no_brand_from_the_owner_is_in_the_public_skill():
    for berkas in SKILL.rglob("*"):
        if berkas.is_file() and berkas.suffix in {".md", ".json", ".mjs", ".py"}:
            isi = berkas.read_text(encoding="utf-8").lower()
            if berkas.name != "test_infografis.py":
                assert "nestor" not in isi, berkas.name
    # Folder hasil/ berisi keluaran lokal yang diabaikan git; yang diperiksa hanya sumbernya.
    assert not [p for p in SKILL.rglob("*.png") if "hasil" not in p.parts]


def test_the_example_says_that_its_numbers_are_fictional():
    isi = isi_contoh()

    assert "fiktif" in isi["masalah"]["sumber"]
    assert "fiktif" in isi["kaki"]


# --------------------------------------------------------------------------
# Pemeriksaan
# --------------------------------------------------------------------------


@butuh_node
def test_the_example_passes_the_check():
    laporan = skill.periksa_infografis(CONTOH.read_text(encoding="utf-8"))

    assert "LOLOS: 0 gagal, 0 peringatan" in laporan


@butuh_node
def test_the_blank_template_is_rejected_with_the_fix():
    laporan = skill.periksa_infografis(KOSONG.read_text(encoding="utf-8"))

    assert "BELUM LOLOS" in laporan
    assert "terlalu panjang" in laporan


def ubah(mutasi):
    isi = copy.deepcopy(isi_contoh())
    mutasi(isi)
    return isi


MASALAH = {
    "emoji": (lambda c: c["kepala"].update(tujuan="Rencana tanam 🌱"), "emoji"),
    "kata kabur": (
        lambda c: c["kepala"].update(tujuan="Aplikasi tanam terbaik"),
        'kata "terbaik" tidak jelas',
    ),
    "ikon tidak ada": (
        lambda c: c["solusi"]["simpul"][0].update(ikon="rocket"),
        'nama ikon "rocket" tidak ada',
    ),
    "jumlah simpul": (
        lambda c: c["solusi"].update(simpul=c["solusi"]["simpul"][:3]),
        "harus berisi tepat 4 simpul",
    ),
    "nilai berupa teks": (
        lambda c: c["masalah"]["ukuran"][0].update(nilai="78"),
        "harus angka 0 sampai 100",
    ),
    "angka tidak sama": (
        lambda c: c["masalah"]["ukuran"][0].update(tampil="50%"),
        "harus sama dengan nilai",
    ),
    "tanpa sumber": (
        lambda c: c["masalah"].update(sumber="x"),
        "sebutkan sumber angka",
    ),
    "arti terlalu singkat": (
        lambda c: c["masalah"]["ukuran"][0].update(arti="paham"),
        "terlalu singkat",
    ),
    "tanda bintang di tempat salah": (
        lambda c: c["kepala"].update(judul_1="Tanam *sayur*"),
        "tanda * hanya boleh dipakai",
    ),
    "tanpa jual produk": (
        lambda c: c["contoh"]["label"][2].update(teks="Tanpa jual produk"),
        "ambigu",
    ),
    "merek tidak ada": (lambda c: c.update(merek="tidak_ada"), "nama merek tidak ditemukan"),
    "merek keluar folder": (
        lambda c: c.update(merek="../scripts/skema"),
        "nama merek tidak ditemukan",
    ),
}


@butuh_node
@pytest.mark.parametrize("kasus", sorted(MASALAH))
def test_each_known_mistake_is_rejected_with_a_message_that_names_the_fix(kasus):
    mutasi, pesan = MASALAH[kasus]

    laporan = skill.periksa_infografis(ubah(mutasi))

    assert "BELUM LOLOS" in laporan, kasus
    assert pesan in laporan, kasus


@butuh_node
def test_json_wrapped_by_a_small_model_is_still_read():
    teks = "Ini hasilnya:\n```json\n" + CONTOH.read_text(encoding="utf-8") + "\n```\nSemoga membantu."

    assert "LOLOS" in skill.periksa_infografis(teks)


def test_text_that_is_not_json_gets_a_plain_message():
    assert "bukan JSON" in skill.periksa_infografis("maaf, saya tidak bisa")
    assert "JSON rusak" in skill.periksa_infografis('{"merek": "tanam_kota",}')
    assert "bukan JSON" in skill.periksa_infografis("[1, 2]")


def test_without_node_the_message_says_what_to_install(monkeypatch):
    monkeypatch.setattr(skill.shutil, "which", lambda _: None)

    laporan = skill.periksa_infografis(isi_contoh())

    assert "Node.js tidak ditemukan" in laporan


# --------------------------------------------------------------------------
# Menggambar
# --------------------------------------------------------------------------


@butuh_node
def test_the_html_is_written_without_a_browser(folder_hasil):
    laporan = skill.buat_infografis(isi_contoh(), "uji", tanpa_gambar=True)

    html = (folder_hasil / "uji" / "infografis.html").read_text(encoding="utf-8")
    assert "OK infografis.html" in laporan
    assert "Panen di balkon." in html
    assert "78%" in html
    assert "undefined" not in html
    assert (folder_hasil / "uji" / "isi.json").is_file()


@butuh_node
def test_text_is_escaped_in_the_html(folder_hasil):
    isi = ubah(lambda c: c["kepala"].update(tujuan="<b>tanam</b> & panen"))

    skill.buat_infografis(isi, "uji", tanpa_gambar=True)

    html = (folder_hasil / "uji" / "infografis.html").read_text(encoding="utf-8")
    assert "&lt;b&gt;tanam&lt;/b&gt; &amp; panen" in html
    assert "<b>tanam</b>" not in html


@butuh_node
def test_nothing_is_drawn_when_the_check_fails(folder_hasil):
    isi = ubah(lambda c: c["kepala"].update(tujuan="Aplikasi tanam terbaik"))

    laporan = skill.buat_infografis(isi, "uji", tanpa_gambar=True)

    assert "BELUM DIGAMBAR" in laporan
    assert not (folder_hasil / "uji" / "infografis.html").exists()


@pytest.mark.parametrize("nama", ["../luar", "a/b", "..", "", "x" * 61, "C:\\x"])
def test_the_output_folder_cannot_leave_the_output_dir(nama, folder_hasil):
    laporan = skill.buat_infografis(isi_contoh(), nama, tanpa_gambar=True)

    assert "nama folder hanya boleh" in laporan
    assert not folder_hasil.exists()


@butuh_node
def test_a_brand_without_a_logo_gets_its_initial_in_the_circles(folder_hasil):
    skill.buat_infografis(isi_contoh(), "uji", tanpa_gambar=True)

    html = (folder_hasil / "uji" / "infografis.html").read_text(encoding="utf-8")
    assert ">T</div>" in html


def png_ukuran(berkas: Path) -> tuple[int, int]:
    data = berkas.read_bytes()[:24]
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


@butuh_node
@pytest.mark.skipif(
    os.environ.get("INFOGRAFIS_UJI_BROWSER") != "1",
    reason="menggambar PNG butuh Edge atau Chrome dan huruf dari jaringan",
)
def test_the_png_is_4_by_5_and_the_text_does_not_overlap(folder_hasil):
    laporan = skill.buat_infografis(isi_contoh(), "uji")

    assert png_ukuran(folder_hasil / "uji" / "infografis.png") == (2160, 2700)
    assert "tidak ada teks yang bertumpuk" in laporan
    assert (folder_hasil / "uji" / "infografis.pdf").is_file()
