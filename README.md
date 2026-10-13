<div align="center">

# 🚀 Zul

**CLI generator boilerplate + toolkit utilities untuk aplikasi AI & data engineering berbasis Python.**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Package Manager: uv](https://img.shields.io/badge/package%20manager-uv-orange)](https://github.com/astral-sh/uv)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docs](https://img.shields.io/badge/docs-zulkit.my.id-2ea44f)](https://zulkit.my.id/)

</div>

## Apa itu Zul?

Zul adalah perintah baris sekaligus library Python. `zul build hexa` membuat kerangka aplikasi AI berarsitektur hexagonal (FastAPI, LangChain, Streamlit), dan paket `zul` berisi fungsi siap pakai untuk vector database, OCR, LLM, computer vision, evaluasi retrieval, dan konversi dokumen.

Zul adalah wrapper: Zul tidak membuat ulang model deteksi, vector database, atau konverter dokumen, melainkan merangkai library yang sudah ada, seperti LangChain, OpenCV, RF-DETR, Docling, pymilvus, redisvl, dan ragas. Setiap library hanya diimpor di satu file di [`framework/src/zul/adapters/`](framework/src/zul/adapters/), jadi mengganti, mengunci versi, atau mengubah perilaku sebuah library cukup di satu tempat. Daftar lengkap library beserta lisensinya ada di [Library yang dipakai](https://zulkit.my.id/referensi/library/).

## Isi repository

Repository ini dibagi menjadi tiga kategori. Setiap folder punya README sendiri:

| Kategori | Folder | Isi |
|---|---|---|
| **Framework** | [`framework/`](framework/) | Paket `zul` (`src/`) dan test-nya, skill pool untuk agent (`agentic/`), notebook contoh (`notebooks/`), boilerplate proyek (`project/`), dan studi (`studies/`). |
| **Dokumentasi** | [`docs/`](docs/), `mkdocs.yml` | Situs dokumentasi framework dan blog, terbit di https://zulkit.my.id/. |
| **Pengembangan diri** | [`research/`](research/) | Latihan coding manual, proyek mandiri, dan arsip. Bukan bagian dari paket `zul`. |

File di root, yaitu `pyproject.toml`, `uv.lock`, dan `.venv`, dipakai bersama oleh semua kategori. [`scripts/`](scripts/) berisi tool untuk merawat repository ini.

## Mulai cepat

Install perintah `zul` sebagai tool global:

```bash
uv tool install git+https://github.com/kazuma313/zul_utilities.git
```

Buat proyek AI baru:

```bash
zul build hexa --name my-agent
```

Library besar seperti Docling dan PyTorch hanya ter-install lewat *extra*, misalnya `zul[milvus,redis]`. Daftar extra dan isinya ada di [Instalasi Zul](https://zulkit.my.id/panduan/instalasi-zul/).

## Fitur utama

| Fitur | Keterangan |
|---|---|
| 🏛️ **Template hexagonal** | `zul build hexa` membuat proyek dengan lapisan `domain`, `application`, `infrastructure`, dan `interface`, lengkap dengan agent ReAct, human-in-the-loop, dan playground. |
| 🗄️ **Vector database** | `MilvusHelper` dan `RedisHelper` berbasis file config, termasuk hybrid search. |
| 👁️ **OCR dan dokumen** | Docling VLM, Gemini, Markdown ke PDF dan PPTX. |
| 🎥 **Computer vision** | Fungsi kecil untuk video: deteksi RF-DETR, ByteTrack, garis dan poligon penghitung, timer, dan gambar. |
| 📏 **Evaluasi retrieval** | `zul.evaluation` menilai retriever dengan ragas, plus hit rate, MRR, dan latensi tanpa model penilai. |
| 🧩 **Skill pool** | Skill untuk agent AI di `framework/agentic/`: mind map, silabus dan materi belajar, contextual retrieval, transcript YouTube, crypto. |
| 🧑‍💻 **MCP untuk code assistant** | `zul mcp serve` memberi Claude Code, Cursor, VS Code, dan Claude Desktop akses ke modul, dokumentasi, dan boilerplate Zul. |

## Dokumentasi

Dokumentasi lengkap terbit di **https://zulkit.my.id/**, dengan bagian Tutorial, Panduan, Referensi, Konsep, dan Blog. Cara menulis dan menerbitkannya ada di [`docs/README.md`](docs/README.md).

## Pengembangan

Siapkan lingkungan dari root repository:

```bash
uv sync --inexact
```

Setiap kategori diuji dengan perintahnya sendiri:

| Perintah | Menguji |
|---|---|
| `uv run pytest` | Paket `zul` di `framework/tests/`. |
| `uv run pytest framework/agentic` | Skill pool. |
| `uv run pytest scripts/tests` | Tool dokumentasi. |
| `uv run mkdocs build --strict` | Situs dokumentasi. |
| `uv run pytest research/latihan` | Latihan; sebagian sengaja gagal sampai soalnya dikerjakan. |

Langkah lengkapnya, termasuk gaya kode, ada di [Berkontribusi](https://zulkit.my.id/panduan/berkontribusi/).

## Lisensi

Dirilis di bawah lisensi **MIT**; lihat file [LICENSE](LICENSE).

## Penulis

**Kurnia Zulda Matondang** ([@kazuma313](https://github.com/kazuma313))
