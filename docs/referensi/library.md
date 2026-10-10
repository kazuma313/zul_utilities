# Library yang dipakai

Zul adalah wrapper dari berbagai library Python. Zul tidak membuat ulang model deteksi, vector database, atau konverter dokumen. Zul merangkai library yang sudah ada menjadi alat yang siap dipakai, dengan cara pakai yang seragam: pengaturan lewat argumen atau file config, hasil berupa tipe Python biasa dan array NumPy, dan dokumentasi berbahasa Indonesia.

Setiap library hanya diimpor di satu file di `src/zul/adapters/`. Modul Zul lain memakai library lewat adapter itu, jadi mengganti, mengunci, atau mengubah perilaku sebuah library cukup di satu tempat. Alasannya ada di [Lapisan adapter](../konsep/lapisan-adapter.md).

Halaman ini mendaftar setiap library yang di-install bersama Zul. Kolom **Versi** adalah syarat versi di `pyproject.toml`.

## Instalasi dasar

Library berikut ter-install dengan `pip install zul`:

| Library | Dipakai untuk | Adapter | Lisensi | Versi |
|---|---|---|---|---|
| `typer` | Perintah `zul` di terminal | Dipakai langsung | MIT | `>=0.12.0` |
| `inquirerpy` | Pertanyaan interaktif `zul build` | Dipakai langsung | MIT | `>=0.3.4` |
| `pydantic` | Validasi config vector database dan `AIService` | Dipakai langsung | MIT | `>=2.0.0` |
| `pyyaml` | Membaca dan menulis file config YAML | `yaml` | MIT | `>=6.0` |
| `numpy` | Tipe data array untuk kotak, titik, frame, dan vektor | Dipakai langsung | BSD-3-Clause | `>=2.0.0` |

Library yang dipakai langsung, tanpa adapter, adalah bagian dari cara kerja Zul sendiri: CLI-nya dibangun dengan Typer, dan tipe datanya adalah model pydantic dan array NumPy.

## Library per extra

Library berikut hanya ter-install jika extra-nya diminta, misalnya `pip install "zul[milvus,detection]"`. Cara memilih extra ada di [Instalasi Zul](../panduan/instalasi-zul.md#memilih-extra).

| Extra | Library | Dipakai untuk | Adapter | Lisensi | Versi |
|---|---|---|---|---|---|
| `milvus` | `pymilvus` | `MilvusHelper`: menyimpan dan mencari vektor di Milvus | `milvus` | Apache 2.0 | `>=2.5.0` |
| `redis` | `redis` | Koneksi ke server Redis | `redis` | MIT | `>=6.4.0` |
| `redis` | `redisvl` | `RedisVectorDB`: index dan pencarian vektor di Redis | `redis` | MIT | `>=0.10.0` |
| `converter` | `markdown` | Markdown ke HTML, sebelum dijadikan PDF | `markdown` | BSD-3-Clause | `>=3.5` |
| `converter` | `xhtml2pdf` | HTML ke PDF | `xhtml2pdf` | Apache 2.0 | `>=0.2.17` |
| `converter` | `python-pptx` | Markdown ke slide PPTX | `pptx` | MIT | `>=1.0.2` |
| `analysis` | `matplotlib` | Grafik `ChartGenerator` | `matplotlib` | PSF | `>=3.9` |
| `analysis` | `pandas` | Membaca dan menulis CSV untuk grafik | `pandas` | BSD-3-Clause | `>=2.0` |
| `analysis` | `scipy` | Uji statistik di `ChartGenerator` | `scipy` | BSD-3-Clause | `>=1.16.2` |
| `pdf` | `pypdf` | Membaca teks per halaman PDF | `pypdf` | BSD-3-Clause | `>=4.0` |
| `pdf` | `langchain-text-splitters` | Memotong teks PDF menjadi chunk | `langchain_text_splitters` | MIT | `>=0.3.0` |
| `ocr` | `docling` | OCR dokumen dengan model VLM | `docling` | MIT | `>=2.74.0` |
| `llm` | `langchain-openai` | `AIService`: chat model dan embedding lewat endpoint OpenAI | `langchain_openai` | MIT | `>=1.0.2` |
| `llm` | `langgraph` | Contoh graph `react_graph` | `langgraph` | MIT | `>=1.0.2` |
| `gemini` | `google-genai` | OCR PDF dengan Gemini | `gemini` | Apache 2.0 | `>=1.0.0` |
| `vision` | `opencv-python` | Menggambar di frame, masker, membaca dan menulis video | `opencv` | Apache 2.0 | `>=4.10` |
| `tracking` | `lap` | Memasangkan track dengan deteksi di `ByteTracker` | `lap` | BSD-2-Clause | `>=0.5.12` |
| `detection` | `rfdetr` | Mendeteksi orang dan 17 keypoint pose | `rfdetr` | Apache 2.0 | `>=1.11.2,<1.12` |
| `mcp` | `mcp` | MCP server untuk code assistant: `zul mcp serve` | `mcp` | MIT | `>=2.3,<3` |

Extra `all` meng-install semua extra di atas sekaligus.

## Library yang ikut ter-install

Beberapa library di atas membawa library besar lain. Zul tidak memakainya langsung, tetapi ukurannya perlu kamu ketahui:

| Library | Dibawa oleh | Keterangan |
|---|---|---|
| PyTorch dan torchvision | `docling`, `rfdetr` | Sekitar 2,8 GB setelah ter-install dengan CUDA. Di Windows, PyTorch dari PyPI hanya berjalan di CPU. |
| transformers | `docling`, `rfdetr` | Model dari Hugging Face. |
| supervision | `rfdetr` | Format hasil deteksi RF-DETR, diubah adapter menjadi array NumPy. |
| langchain-core | `langchain-openai`, `langchain-text-splitters` | Inti LangChain. |
| Starlette dan Uvicorn | `mcp` | Transport HTTP untuk MCP. Zul hanya memakai transport stdio. |
| `svglib`, `python-bidi` | `xhtml2pdf` | Berlisensi LGPL, boleh dipakai lewat import biasa. |
| FFmpeg di dalam paket `av` | `supervision` | Berlisensi LGPL, boleh dipakai lewat import biasa. |

Tidak ada library berlisensi AGPL. `test_no_dependency_uses_an_agpl_license` memeriksa semua library di atas, termasuk dependency dari dependency, setiap kali test dijalankan.

## Yang ditulis sendiri di Zul

Tidak semua isi Zul adalah wrapper. Bagian berikut ditulis sendiri dengan NumPy atau library standar Python, tanpa library khusus:

| Modul | Isi |
|---|---|
| `computer_vision.tracking` | ByteTrack dan filter Kalman-nya. |
| `computer_vision.geometry` | Titik di poligon, IoU, non-max suppression, dan arah. |
| `computer_vision.zones` | Garis penghitung dan poligon penghitung. |
| `computer_vision.timers` | Timer zona dan timer kondisi. |
| `computer_vision.pose` | Arah hadap dari keypoint wajah dan bahu. |
| `computer_vision.distance` | Jarak dalam meter dari tinggi kotak. |
| `utilities.fake_embedding` | Embedding palsu untuk test. |
| `assistant.knowledge` | Daftar modul, cara pakai, pencarian dokumentasi, dan contoh kode untuk [MCP server](mcp.md). |
| `assistant.comment_style` | Pemeriksa paragraf komentar anak tangga. |

## Template hexa

Proyek hasil `zul build hexa` punya dependency-nya sendiri di `requirements.txt` proyek itu, terpisah dari library Zul: FastAPI, Uvicorn, LangChain, langchain-openai, LangGraph, OpenAI, pydantic, python-dotenv, dan Streamlit. Proyek itu tidak mengimpor Zul. Rinciannya ada di [Struktur proyek](struktur-proyek.md).

## Halaman terkait

- [Lapisan adapter](../konsep/lapisan-adapter.md) untuk alasan setiap library dipakai lewat adapter.
- [Instalasi Zul](../panduan/instalasi-zul.md) untuk memilih extra.
- [Mengubah perilaku library pihak ketiga](../panduan/mengubah-perilaku-library.md) untuk mengubah, mengganti, atau menambah library.
