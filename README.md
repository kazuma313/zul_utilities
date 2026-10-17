<div align="center">

# 🚀 Zul

**CLI generator boilerplate + toolkit utilities untuk aplikasi AI & data engineering berbasis Python.**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Package Manager: uv](https://img.shields.io/badge/package%20manager-uv-orange)](https://github.com/astral-sh/uv)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docs](https://img.shields.io/badge/docs-zulkit.my.id-2ea44f)](https://zulkit.my.id/)

</div>

## In English

Zul is a Python toolkit for AI and data applications. It wraps libraries such as LangChain, OpenCV, RF-DETR, Docling, pymilvus, redisvl, and ragas into small composable functions, and ships four things on top of them:

- a retrieval evaluation module built on ragas (`zul.evaluation`),
- a complete computer-vision app boilerplate with RF-DETR detection and tracking,
- an MCP server that lets code assistants read Zul's modules, docs, and examples, and
- a hexagonal project generator (`zul build hexa`).

Each third-party library is imported in exactly one file under `framework/src/zul/adapters/`, and a test enforces it. The code is MIT-licensed. The documentation at [zulkit.my.id](https://zulkit.my.id/) is written in Indonesian.

Try it in under a minute, with no API key. Install Zul as a library:

```bash
pip install git+https://github.com/kazuma313/zul_utilities.git
```

Then run:

```python
from zul.evaluation.hits import retrieval_hit_stats

results = [
    {"reference": "Paris", "retrieved_contexts": ["Berlin is in Germany.", "The capital of France is Paris."]},
    {"reference": "Tokyo", "retrieved_contexts": ["Tokyo is the capital of Japan."]},
    {"reference": "Cairo", "retrieved_contexts": ["Rome is in Italy."]},
]
print(retrieval_hit_stats(results))
# {'n': 3, 'hit_rate': 0.6667, 'mrr': 0.5, 'threshold': 0.6, 'sumber': 'reference'}
```

The first question was answered at rank 2, the second at rank 1, and the third not at all, so the hit rate is 2/3 and the mean reciprocal rank is (1/2 + 1 + 0) / 3 = 0.5. For model-based scoring with ragas, see [Mengevaluasi retrieval](https://zulkit.my.id/panduan/mengevaluasi-retrieval/).

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

File di root, yaitu `pyproject.toml`, `uv.lock`, `mkdocs.yml`, dan `.venv`, dipakai bersama oleh semua kategori. Tool setiap kategori ada di folder kategorinya: `framework/scripts/` untuk gaya kode dan kunci API, `docs/tools/` untuk blog dan situs.

## Kembali setelah lama ditinggal

Lima langkah untuk mengingat kembali proyek ini:

1. Lihat apa yang terakhir dikerjakan: `git log --oneline -20`.
2. Siapkan lingkungan: `uv sync --inexact`. Jangan memakai `uv sync` tanpa `--inexact`, karena library skill pool yang tidak tercatat di `uv.lock` akan terhapus.
3. Pastikan semuanya masih jalan: `uv run pytest`, lalu perintah test lain di bagian [Pengembangan](#pengembangan).
4. Baca README folder yang akan dikerjakan; setiap folder kategori punya satu.
5. Baca aturan menulis kode dan dokumentasi di [Berkontribusi](https://zulkit.my.id/panduan/berkontribusi/).

| Saya mau... | Buka |
|---|---|
| Menambah atau mengubah fungsi di paket `zul` | `framework/src/zul/`, test di `framework/tests/` |
| Menambah library pihak ketiga | `framework/src/zul/adapters/`, satu file per library |
| Menambah skill untuk agent | `framework/agentic/skills/` (pakai model) atau `framework/agentic/utilities/` (script saja) |
| Memulai aplikasi computer vision baru | `framework/project/computer_vision/` |
| Membandingkan model atau cara kerja | Folder baru di `framework/studies/` |
| Mengubah template `zul build hexa` | `framework/src/zul/templates/hexa/` |
| Menulis halaman dokumentasi | `docs/tutorial/`, `docs/panduan/`, `docs/referensi/`, atau `docs/konsep/`, lalu daftarkan di `mkdocs.yml` |
| Menulis tulisan blog | `uv run python docs/tools/new_post.py "Judul"` |
| Latihan coding | `research/latihan/` |
| Memakai code assistant dengan konteks Zul | MCP server: `.mcp.json` di root, atau [tutorialnya](https://zulkit.my.id/tutorial/code-assistant/) |

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
| `uv run pytest docs/tools/tests` | Tool dokumentasi. |
| `uv run mkdocs build --strict` | Situs dokumentasi. |
| `uv run pytest research/latihan` | Latihan; sebagian sengaja gagal sampai soalnya dikerjakan. |

Langkah lengkapnya, termasuk gaya kode, ada di [Berkontribusi](https://zulkit.my.id/panduan/berkontribusi/).

## Lisensi

Dirilis di bawah lisensi **MIT**; lihat file [LICENSE](LICENSE).

## Penulis

**Kurnia Zulda Matondang** ([@kazuma313](https://github.com/kazuma313))
