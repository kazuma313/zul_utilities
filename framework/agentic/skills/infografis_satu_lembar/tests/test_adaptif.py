"""Test susunan adaptif: blok yang dipilih menurut bentuk informasi, dengan tinggi yang menyesuaikan.

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
CONTOH = SKILL / "contoh"
KATALOG = SKILL / "references" / "katalog_blok.md"

spec = importlib.util.spec_from_file_location(
    "infografis_adaptif_uji", SKILL / "infografis_satu_lembar_skill.py"
)
skill = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skill)

butuh_node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js tidak ada")


def baca(nama: str) -> dict:
    return json.loads((CONTOH / nama).read_text(encoding="utf-8"))


def ubah(nama: str, mutasi) -> dict:
    isi = copy.deepcopy(baca(nama))
    mutasi(isi)
    return isi


@pytest.fixture(autouse=True)
def folder_hasil(tmp_path, monkeypatch):
    monkeypatch.setenv("INFOGRAFIS_OUTPUT_DIR", str(tmp_path / "hasil"))
    return tmp_path / "hasil"


def html_dari(isi, folder_hasil) -> str:
    skill.buat_infografis(isi, "uji", tanpa_gambar=True)
    return (folder_hasil / "uji" / "infografis.html").read_text(encoding="utf-8")


def atas_dari(html: str, id_teks: str) -> float:
    cocok = re.search(rf'data-teks="{id_teks}" style="position:absolute;left:[\d.]+px;top:([\d.]+)px', html)
    assert cocok, id_teks
    return float(cocok.group(1))


CONTOH_ADAPTIF = ["adaptif_dua_kota.json", "adaptif_cara_menanam.json"]


# --------------------------------------------------------------------------
# Pemeriksaan
# --------------------------------------------------------------------------


@butuh_node
@pytest.mark.parametrize("nama", CONTOH_ADAPTIF)
def test_the_adaptive_examples_pass_the_check(nama):
    laporan = skill.periksa_infografis((CONTOH / nama).read_text(encoding="utf-8"))

    assert "LOLOS: 0 gagal, 0 peringatan" in laporan


def tambah_blok_padat(c):
    c["blok"] = [
        c["blok"][0],
        {
            "jenis": "tahap",
            "items": [
                {"nama": f"Tahap {i}", "ikon": "centang", "poin": ["Satu butir pendek"]}
                for i in range(5)
            ],
        },
        {
            "jenis": "banding",
            "judul": "Pot atau tanah",
            "kiri": {"nama": "Pot", "ikon": "keranjang"},
            "kanan": {"nama": "Tanah", "ikon": "lokasi"},
            "baris": [{"topik": f"Baris {i}", "kiri": "Satu", "kanan": "Dua"} for i in range(5)],
        },
    ]


MASALAH = {
    "terlalu sedikit blok": (
        "adaptif_cara_menanam.json",
        lambda c: c.update(blok=c["blok"][:1]),
        "harus berisi 2 sampai 4 blok",
    ),
    "jenis blok tidak dikenal": (
        "adaptif_cara_menanam.json",
        lambda c: c["blok"][0].update(jenis="spiral"),
        "harus salah satu dari: pita_waktu, tahap, alur, banding, langkah, angka",
    ),
    "jenis blok ganda": (
        "adaptif_cara_menanam.json",
        lambda c: c["blok"][1].update(jenis="langkah"),
        "blok langkah sudah dipakai",
    ),
    "terlalu padat": (
        "adaptif_cara_menanam.json",
        tambah_blok_padat,
        "terlalu padat: isinya butuh",
    ),
    "ikuti pita tanpa pita": (
        "adaptif_cara_menanam.json",
        lambda c: c["blok"].__setitem__(
            0,
            {"jenis": "tahap", "ikuti_pita": True, "items": [{"nama": "A", "ikon": "pohon", "poin": ["Satu"]}, {"nama": "B", "ikon": "api", "poin": ["Dua"]}]},
        ),
        "butuh blok pita_waktu yang sah",
    ),
    "jumlah tahap tidak sama dengan masa": (
        "adaptif_dua_kota.json",
        lambda c: c["blok"].__setitem__(
            1,
            {"jenis": "tahap", "ikuti_pita": True, "items": [{"nama": "A", "ikon": "pohon", "poin": ["Satu"]}, {"nama": "B", "ikon": "api", "poin": ["Dua"]}]},
        ),
        "harus berisi 3 tahap, sama dengan jumlah masa",
    ),
    "angka tahap diisi padahal dihitung": (
        "adaptif_dua_kota.json",
        lambda c: c["blok"].__setitem__(
            1,
            {
                "jenis": "tahap",
                "ikuti_pita": True,
                "items": [{"nama": n, "ikon": "pohon", "poin": ["Satu"], "angka": "9"} for n in "ABC"],
            },
        ),
        "dihitung dari pita waktu",
    ),
    "peristiwa berdesakan": (
        "adaptif_dua_kota.json",
        lambda c: c["blok"][0].update(
            peristiwa=[
                {"tahun": 1389, "teks": "Satu", "ikon": "mahkota"},
                {"tahun": 1390, "teks": "Dua", "ikon": "api"},
                {"tahun": 1391, "teks": "Tiga", "ikon": "pedang"},
            ]
        ),
        "tidak punya tempat karena terlalu dekat",
    ),
    "masa tidak berurutan": (
        "adaptif_dua_kota.json",
        lambda c: c["blok"][0]["masa"][1].update(mulai=1480),
        "harus 1478, sama dengan akhir masa sebelumnya",
    ),
    "peristiwa di luar pita": (
        "adaptif_dua_kota.json",
        lambda c: c["blok"][0]["peristiwa"][0].update(tahun=1300),
        "di dalam pita waktu (1389 sampai 1815)",
    ),
    "unggul salah": (
        "adaptif_dua_kota.json",
        lambda c: c["blok"][1]["baris"][0].update(unggul="tengah"),
        'harus "kiri" atau "kanan"',
    ),
    "topik terlalu panjang": (
        "adaptif_dua_kota.json",
        lambda c: c["blok"][1]["baris"][0].update(topik="Penghancuran"),
        "terlalu panjang",
    ),
    "terlalu sedikit langkah": (
        "adaptif_cara_menanam.json",
        lambda c: c["blok"][0].update(langkah=c["blok"][0]["langkah"][:2]),
        "harus berisi 3 sampai 5 langkah",
    ),
    "nilai angka berupa teks": (
        "adaptif_cara_menanam.json",
        lambda c: c["blok"][2]["angka"][0].update(nilai="78"),
        "harus angka 0 sampai 100",
    ),
    "sorot lama_pita tanpa pita": (
        "adaptif_cara_menanam.json",
        lambda c: c["kepala"].update(sorot={"nilai": "lama_pita", "arti": "tahun"}),
        '"lama_pita" butuh blok pita_waktu',
    ),
    "sorot salah bentuk": (
        "adaptif_cara_menanam.json",
        lambda c: c["kepala"].update(sorot="besar"),
        "atau hapus isian ini supaya dibuat otomatis",
    ),
    "kata kabur": (
        "adaptif_cara_menanam.json",
        lambda c: c["blok"][0]["langkah"][0].update(rincian="alat terbaik untuk pemula"),
        'kata "terbaik" tidak jelas',
    ),
}


@butuh_node
@pytest.mark.parametrize("kasus", sorted(MASALAH))
def test_each_mistake_is_rejected_with_a_message_that_names_the_fix(kasus):
    nama, mutasi, pesan = MASALAH[kasus]

    laporan = skill.periksa_infografis(ubah(nama, mutasi))

    assert "BELUM LOLOS" in laporan, kasus
    assert pesan in laporan, kasus


@butuh_node
def test_the_blank_adaptive_template_is_not_accepted_until_filled_in():
    laporan = skill.periksa_infografis((CONTOH / "kosong_adaptif.json").read_text(encoding="utf-8"))

    assert "BELUM LOLOS" in laporan
    assert "kepala.judul_1" in laporan


# --------------------------------------------------------------------------
# Katalog blok: setiap contoh di katalog harus lolos pemeriksaan
# --------------------------------------------------------------------------


def potongan_katalog() -> dict[str, dict]:
    teks = KATALOG.read_text(encoding="utf-8")
    hasil = {}
    for jenis, isi in re.findall(r"<!-- blok:(\w+) -->\s*```json\n(.*?)\n```", teks, re.S):
        hasil[jenis] = json.loads(isi)
    return hasil


def test_the_catalog_has_an_example_for_every_block():
    assert set(potongan_katalog()) == {"pita_waktu", "tahap", "alur", "banding", "langkah", "angka"}


@butuh_node
@pytest.mark.parametrize("jenis", ["pita_waktu", "tahap", "alur", "banding", "langkah", "angka"])
def test_every_catalog_example_passes_the_check(jenis):
    potongan = potongan_katalog()
    pengisi = "langkah" if jenis != "langkah" else "banding"
    isi = copy.deepcopy(baca("adaptif_cara_menanam.json"))
    isi["blok"] = [potongan[jenis], potongan[pengisi]]

    laporan = skill.periksa_infografis(isi)

    assert "LOLOS" in laporan and "BELUM" not in laporan, f"{jenis}: {laporan}"


# --------------------------------------------------------------------------
# Menyesuaikan diri
# --------------------------------------------------------------------------


@butuh_node
def test_the_highlight_is_computed_from_the_first_block(folder_hasil):
    langkah = html_dari(baca("adaptif_cara_menanam.json"), folder_hasil)
    pita = html_dari(baca("adaptif_dua_kota.json"), folder_hasil)

    assert re.search(r'data-teks="sorot-nilai"[^>]*>4<', langkah)
    assert re.search(r'data-teks="sorot-arti"[^>]*>langkah<', langkah)
    assert re.search(r'data-teks="sorot-nilai"[^>]*>426<', pita)


@butuh_node
def test_without_a_highlight_the_brand_initial_is_shown(folder_hasil):
    isi = ubah("adaptif_cara_menanam.json", lambda c: c["kepala"].update(sorot="tanpa"))

    html = html_dari(isi, folder_hasil)

    assert re.search(r'data-teks="sorot-inisial"[^>]*>T<', html)
    assert "sorot-nilai" not in html


@butuh_node
def test_blocks_are_drawn_in_the_order_given_and_use_the_space(folder_hasil):
    tiga = html_dari(baca("adaptif_cara_menanam.json"), folder_hasil)
    dua = html_dari(
        ubah("adaptif_cara_menanam.json", lambda c: c.update(blok=c["blok"][:2])), folder_hasil
    )

    assert atas_dari(tiga, "b0-judul") < atas_dari(tiga, "b1-judul") < atas_dari(tiga, "b2-judul")
    # dengan satu blok lebih sedikit, blok kedua mendapat ruang lebih besar
    selisih_dua = atas_dari(dua, "b1-judul") - atas_dari(dua, "b0-judul")
    selisih_tiga = atas_dari(tiga, "b1-judul") - atas_dari(tiga, "b0-judul")
    assert selisih_dua > selisih_tiga


@butuh_node
def test_the_cards_follow_the_number_of_periods(folder_hasil):
    def lima_masa(c):
        c["blok"][0]["masa"] = [
            {"nama": f"Masa {i + 1}", "mulai": 1000 + i * 100, "selesai": 1100 + i * 100}
            for i in range(5)
        ]
        c["blok"][0]["peristiwa"] = [
            {"tahun": 1000, "teks": "Awal", "ikon": "mahkota"},
            {"tahun": 1250, "teks": "Tengah", "ikon": "api"},
            {"tahun": 1500, "teks": "Akhir", "ikon": "pohon"},
        ]
        c["blok"][1] = {
            "jenis": "tahap",
            "ikuti_pita": True,
            "items": [
                {"nama": f"Masa {i + 1}", "ikon": "pohon", "poin": ["Satu butir"]}
                for i in range(5)
            ],
        }

    html = html_dari(ubah("adaptif_dua_kota.json", lima_masa), folder_hasil)

    assert html.count('data-teks="b0-masa-') >= 5
    assert html.count('data-teks="b1-') >= 5 * 3
    assert re.search(r'data-teks="sorot-nilai"[^>]*>500<', html)
    assert re.search(r'data-teks="b1-4-angka"[^>]*>100<', html)


@butuh_node
def test_the_palette_has_one_color_per_period(folder_hasil):
    def tiga_warna(c):
        c["blok"] = c["blok"][:1]
        c["blok"].append({"jenis": "angka", "judul": "Dua angka", "angka": [
            {"nilai": 10, "tampil": "10%", "arti": "angka pertama contoh"},
            {"nilai": 20, "tampil": "20%", "arti": "angka kedua contoh"},
        ]})

    html = html_dari(ubah("adaptif_dua_kota.json", tiga_warna), folder_hasil)

    warna = set(re.findall(r"background:linear-gradient\(90deg,(#[0-9a-f]{6}),", html))
    assert len(warna) >= 3


@butuh_node
def test_the_old_timeline_layout_still_renders_through_the_adaptive_engine(folder_hasil):
    html = html_dari(baca("majapahit_masa_pudar.json"), folder_hasil)

    assert re.search(r'data-teks="sorot-nilai"[^>]*>426<', html)
    assert "Masa Kehancuran" in html
    assert "KE MANA PENDUDUK PERGI" in html


@butuh_node
def test_text_is_escaped_in_every_block(folder_hasil):
    def berbahaya(c):
        c["blok"][0]["langkah"][0]["nama"] = "<i>x</i>"
        c["blok"][1]["baris"][0]["kiri"] = "a & b"

    html = html_dari(ubah("adaptif_cara_menanam.json", berbahaya), folder_hasil)

    assert "&lt;i&gt;x&lt;/i&gt;" in html
    assert "a &amp; b" in html
    assert "<i>x</i>" not in html


def png_ukuran(berkas: Path) -> tuple[int, int]:
    data = berkas.read_bytes()[:24]
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


@butuh_node
@pytest.mark.skipif(
    os.environ.get("INFOGRAFIS_UJI_BROWSER") != "1",
    reason="menggambar PNG butuh Edge atau Chrome dan huruf dari jaringan",
)
@pytest.mark.parametrize("nama", CONTOH_ADAPTIF)
def test_the_adaptive_pngs_are_4_by_5_and_the_text_does_not_overlap(nama, folder_hasil):
    laporan = skill.buat_infografis((CONTOH / nama).read_text(encoding="utf-8"), "uji")

    assert png_ukuran(folder_hasil / "uji" / "infografis.png") == (2160, 2700)
    assert "tidak ada teks yang bertumpuk" in laporan
