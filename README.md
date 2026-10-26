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

### Memasang hanya yang dipakai

Instalasi dasar hanya 60 MB. Library untuk tiap topik dipasang lewat *extra*, jadi yang tidak kamu pakai tidak ikut terpasang:

```bash
pip install "zul[milvus,llm] @ git+https://github.com/kazuma313/zul_utilities.git"
```

| Extra | Untuk | Tambahan ukuran |
|---|---|---|
| `milvus`, `redis` | Vector database | 55 MB, 6 MB |
| `llm`, `gemini` | LLM, embedding, dan OCR dengan Gemini | 27 MB, 23 MB |
| `converter`, `pdf`, `analysis` | Markdown ke PDF dan PPTX, membaca PDF, grafik | 52 MB, 14 MB, 197 MB |
| `evaluation` | Evaluasi retrieval dengan ragas | 348 MB |
| `vision`, `tracking` | Gambar, video, dan pelacakan | 118 MB, 2 MB |
| `mcp` | MCP server untuk code assistant | 33 MB |
| `ocr`, `detection` | OCR dengan Docling, deteksi orang dengan RF-DETR | 3,4 GB masing-masing, karena membawa PyTorch |

Atau minta code assistant memasangnya. Tempel teks dari [Memasang Zul lewat code assistant](https://zulkit.my.id/panduan/memasang-zul-dengan-code-assistant/#prompt-untuk-ditempel), dan assistant bertanya dulu apa yang kamu butuhkan (MCP, OCR, evaluasi retrieval, atau semuanya), meminta persetujuanmu, lalu memasang hanya extra untuk jawabanmu.

Semua extra kecuali `ocr` dan `detection` sekitar 650 MB. `zul[all]` sekitar 3,8 GB. Ukuran diukur di Windows dengan PyTorch build CUDA 13, dan cara menghitungnya ada di [Seberapa besar tiap pilihan](https://zulkit.my.id/panduan/instalasi-zul/#seberapa-besar-tiap-pilihan). Resep per topik ada di [Memasang per topik](https://zulkit.my.id/panduan/instalasi-zul/#memasang-per-topik), dan kolom Install di tabel [Dokumentasi](#dokumentasi) di bawah.

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

Setiap topik punya halaman dengan peran berbeda: tutorial dan panduan untuk mengerjakan sesuatu, referensi untuk mencari fakta, dan konsep untuk memahami alasannya. Kolom Install menunjukkan yang perlu dipasang, supaya hanya library yang dipakai yang terpasang. Cara memilihnya dan ukuran tiap pilihan ada di [Instalasi Zul](https://zulkit.my.id/panduan/instalasi-zul/#memasang-per-topik).

### Memulai

| Topik | Isi | Install | Halaman |
|---|---|---|---|
| **Instalasi** | Memasang perintah `zul`, memilih extra, dan mengisi environment variable. | Dasar | [Instalasi Zul](https://zulkit.my.id/panduan/instalasi-zul/), [Memasang lewat code assistant](https://zulkit.my.id/panduan/memasang-zul-dengan-code-assistant/), [Perintah zul](https://zulkit.my.id/referensi/cli/), [Environment variable](https://zulkit.my.id/referensi/konfigurasi/), [Library yang dipakai](https://zulkit.my.id/referensi/library/) |
| **Proyek pertama** | Membuat proyek dari template, mengatur model, dan menjalankannya. | Dasar. Proyek hasil `zul build hexa` punya `requirements.txt` sendiri. | [Membuat agent pertamamu](https://zulkit.my.id/tutorial/agent-pertama/), [Membuat proyek baru](https://zulkit.my.id/panduan/membuat-proyek/), [Mengatur model dan API key](https://zulkit.my.id/panduan/mengatur-llm/), [Menjalankan aplikasi](https://zulkit.my.id/panduan/menjalankan-aplikasi/) |

### Agent dan template hexagonal

| Topik | Isi | Install | Halaman |
|---|---|---|---|
| **Arsitektur hexagonal** | Lapisan `domain`, `application`, `infrastructure`, dan `interface`, dan arah dependensinya. | Tidak ada | [Arsitektur hexagonal](https://zulkit.my.id/konsep/arsitektur-hexagonal/), [Perjalanan sebuah request](https://zulkit.my.id/konsep/alur-request/), [Struktur proyek hexa](https://zulkit.my.id/referensi/struktur-proyek/), [Hexagonal dari nol](https://zulkit.my.id/hexagonal/) |
| **Agent ReAct** | Putaran model dan tool, batas langkah, tool, node, dan system prompt. | Di `requirements.txt` proyek hasil `zul build hexa` | [Cara kerja agent ReAct](https://zulkit.my.id/konsep/agent-react/), [API agent](https://zulkit.my.id/referensi/agent/), [Menambah tool](https://zulkit.my.id/panduan/menambah-tool/), [Menambah node](https://zulkit.my.id/panduan/menambah-node/), [Mengatur batas langkah](https://zulkit.my.id/panduan/mengatur-batas-langkah/), [Mengubah system prompt](https://zulkit.my.id/panduan/mengubah-system-prompt/) |
| **Human-in-the-loop** | Agent berhenti menunggu persetujuan, lalu dilanjutkan. | Di `requirements.txt` proyek hasil `zul build hexa` | [Meminta persetujuan manusia](https://zulkit.my.id/tutorial/persetujuan-manusia/), [Cara kerja](https://zulkit.my.id/konsep/human-in-the-loop/), [Mewajibkan persetujuan](https://zulkit.my.id/panduan/mewajibkan-persetujuan/), [Format review](https://zulkit.my.id/referensi/format-review/) |
| **Subagents** | Supervisor yang mendelegasikan pekerjaan ke spesialis. | Di `requirements.txt` proyek hasil `zul build hexa` | [Membangun tim agent](https://zulkit.my.id/tutorial/tim-agent/), [Cara kerja subagents](https://zulkit.my.id/konsep/subagents/), [Menambah subagent](https://zulkit.my.id/panduan/menambah-subagent/) |
| **Memory dan percakapan** | Apa yang disimpan checkpointer, dan menyimpan percakapan di database. | Di `requirements.txt` proyek hasil `zul build hexa` | [Memory dan thread](https://zulkit.my.id/konsep/memory/), [Menyimpan percakapan](https://zulkit.my.id/panduan/menyimpan-percakapan/) |
| **REST API dan playground** | Endpoint HTTP, dan panel untuk mencoba agent di browser. | Di `requirements.txt` proyek hasil `zul build hexa` | [HTTP API](https://zulkit.my.id/referensi/http-api/), [Playground API](https://zulkit.my.id/referensi/playground-api/), [Menambah endpoint](https://zulkit.my.id/panduan/menambah-endpoint/), [Mencoba di playground](https://zulkit.my.id/panduan/mencoba-di-playground/) |
| **Pengujian** | Menguji agent dengan model palsu, tanpa memanggil LLM asli. | Di `requirements.txt` proyek hasil `zul build hexa` | [Menguji tanpa LLM asli](https://zulkit.my.id/konsep/pengujian/), [Menguji agent](https://zulkit.my.id/panduan/menguji-agent/) |

### Data, dokumen, dan model

| Topik | Isi | Install | Halaman |
|---|---|---|---|
| **Vector database** | `MilvusHelper` dan `RedisHelper` berbasis file config, termasuk hybrid search. | `zul[milvus]` atau `zul[redis]` | [Milvus](https://zulkit.my.id/panduan/memakai-milvus/), [Redis](https://zulkit.my.id/panduan/memakai-redis/), [MilvusHelper](https://zulkit.my.id/referensi/milvus/), [RedisHelper](https://zulkit.my.id/referensi/redis/) |
| **OCR** | Mengubah PDF dan gambar menjadi teks dengan Docling VLM atau Gemini. | `zul[ocr]` (Docling, 3,4 GB) atau `zul[gemini]` (23 MB) | [Mengubah dokumen menjadi teks](https://zulkit.my.id/panduan/membaca-dokumen-ocr/), [Menyiapkan dokumen untuk RAG](https://zulkit.my.id/panduan/menyiapkan-dokumen-untuk-rag/), [OCR](https://zulkit.my.id/referensi/ocr/) |
| **LLM dan embedding** | `AIService` untuk memanggil model chat dan embedding. | `zul[llm]` | [Memanggil LLM dan embedding](https://zulkit.my.id/panduan/memanggil-llm-dan-embedding/), [AI Service](https://zulkit.my.id/referensi/ai-service/) |
| **Konversi dokumen** | Markdown menjadi PDF dan PPTX. | `zul[converter]` | [Mengubah Markdown](https://zulkit.my.id/panduan/mengonversi-markdown/), [Markdown converter](https://zulkit.my.id/referensi/markdown-converter/) |
| **Grafik dan crypto** | Grafik perbandingan dengan uji statistik, candlestick, dan snapshot harga. | `zul[analysis]` untuk grafik; skill crypto dijalankan dari checkout repository | [Membuat grafik](https://zulkit.my.id/panduan/membuat-grafik/), [ChartGenerator](https://zulkit.my.id/referensi/grafik/), [Candlestick crypto](https://zulkit.my.id/panduan/membuat-chart-crypto/), [Snapshot crypto](https://zulkit.my.id/panduan/mengambil-snapshot-crypto/) |
| **Helper kecil** | Fungsi pendukung, seperti logger dan pengukur waktu. | Dasar; `zul[pdf]`, `zul[analysis]`, atau `zul[llm]` untuk tiga helper tertentu | [Memakai helper kecil](https://zulkit.my.id/panduan/memakai-helper/), [Helper kecil](https://zulkit.my.id/referensi/helper/) |

### Evaluasi dan computer vision

| Topik | Isi | Install | Halaman |
|---|---|---|---|
| **Evaluasi retrieval** | `zul.evaluation` menilai retriever dengan ragas, plus hit rate, MRR, dan latensi tanpa model penilai. | `zul[evaluation,redis,llm]` | [Mengevaluasi retrieval dan RAG](https://zulkit.my.id/panduan/mengevaluasi-retrieval/), [Evaluasi retrieval](https://zulkit.my.id/referensi/evaluation/) |
| **Computer vision** | Fungsi kecil untuk video: deteksi RF-DETR, ByteTrack, garis dan poligon penghitung, timer, dan gambar. | Dasar untuk garis, poligon, timer, arah hadap, dan jarak; `zul[vision]` untuk gambar dan video; `zul[detection]` untuk model (3,4 GB) | [Mendeteksi dan melacak orang](https://zulkit.my.id/panduan/mendeteksi-dan-melacak-orang/), [Garis dan poligon](https://zulkit.my.id/panduan/menghitung-dengan-garis-dan-poligon/), [Durasi per orang](https://zulkit.my.id/panduan/mengukur-durasi/), [Menggambar di frame](https://zulkit.my.id/panduan/menggambar-di-frame/), [Arah hadap dan jarak](https://zulkit.my.id/panduan/membaca-arah-hadap-dan-jarak/), [Menyamarkan area](https://zulkit.my.id/panduan/menghitamkan-dan-menyamarkan-area/), [Cara kerjanya](https://zulkit.my.id/konsep/cara-kerja-computer-vision/), [Computer Vision](https://zulkit.my.id/referensi/computer-vision/) |
| **Boilerplate computer vision** | Aplikasi analitik kamera lengkap di `framework/project/computer_vision`. | `zul[detection]`, ikut terpasang lewat `pyproject.toml` boilerplate | [Memulai dari boilerplate](https://zulkit.my.id/panduan/memulai-proyek-computer-vision/) |

### Code assistant dan struktur kode

| Topik | Isi | Install | Halaman |
|---|---|---|---|
| **MCP server** | `zul mcp serve` memberi Claude Code, Cursor, VS Code, dan Claude Desktop akses ke modul, dokumentasi, dan boilerplate Zul. | `zul[mcp]` | [Menghubungkan Zul ke code assistant](https://zulkit.my.id/tutorial/code-assistant/), [Menghubungkan code assistant lain](https://zulkit.my.id/panduan/menghubungkan-code-assistant/), [MCP server](https://zulkit.my.id/referensi/mcp/) |
| **Struktur proyek berinduk** | Membagi proyek menjadi `backend`, `frontend`, `mobile`, dan `assets`, dan merapikannya lewat MCP. | `zul[mcp]` | [Struktur proyek berinduk](https://zulkit.my.id/konsep/struktur-proyek-berinduk/), [Merapikan struktur proyek](https://zulkit.my.id/panduan/merapikan-struktur-proyek/) |
| **Lapisan adapter** | Library pihak ketiga hanya diimpor di `framework/src/zul/adapters/`. | Dasar | [Lapisan adapter](https://zulkit.my.id/konsep/lapisan-adapter/), [Mengubah perilaku library](https://zulkit.my.id/panduan/mengubah-perilaku-library/) |

### Skill pool

| Topik | Isi | Install | Halaman |
|---|---|---|---|
| **Mind map** | Skill yang membuat mind map dari sebuah topik. | Python saja (stdlib) | [Membuat mind map](https://zulkit.my.id/panduan/membuat-mindmap/) |
| **Silabus dan materi belajar** | Skill yang menyusun silabus dan materi, dengan model lokal atau API. | Dari checkout repository; kebutuhannya ada di halamannya | [Membuat silabus dan materi](https://zulkit.my.id/panduan/membuat-silabus-dan-materi/), [Model lokal untuk skill belajar](https://zulkit.my.id/konsep/model-lokal-untuk-skill-belajar/) |
| **Transcript YouTube** | Skill yang mengambil transcript video YouTube. | `youtube-transcript-api`, lihat halamannya | [Mengambil transcript YouTube](https://zulkit.my.id/panduan/mengambil-transcript-youtube/) |

### Berkontribusi dan menerbitkan

| Topik | Isi | Install | Halaman |
|---|---|---|---|
| **Berkontribusi** | Yang boleh dan tidak boleh, aturan untuk bantuan AI, dan cara meninjau kontribusi. | `uv sync --inexact`, atau grup `ci` tanpa PyTorch | [Berkontribusi ke Zul](https://zulkit.my.id/panduan/berkontribusi/) |
| **Situs dokumentasi dan blog** | Cara situs dibangun dan diterbitkan, dan cara menulis tulisan blog. | Grup `docs`: `uv sync --only-group docs` | [Menerbitkan dokumentasi](https://zulkit.my.id/panduan/menerbitkan-dokumentasi/), [Cara situs diterbitkan](https://zulkit.my.id/konsep/penerbitan-dokumentasi/), [Workflow dokumentasi](https://zulkit.my.id/referensi/workflow-dokumentasi/), [Menulis tulisan blog](https://zulkit.my.id/panduan/menulis-blog/), [Format tulisan blog](https://zulkit.my.id/referensi/blog/) |

Tulisan bertanggal tentang apa yang dipelajari ada di [Blog](https://zulkit.my.id/blog/).

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
