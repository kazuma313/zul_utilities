# Instalasi Zul

Zul berlisensi MIT, dan ter-install sebagai perintah `zul` di terminal dan sebagai library Python. Instalasi dasar hanya berisi yang dibutuhkan perintah `zul`, config vector database, dan helper kecil. Utilities lain di-install per fitur lewat *extra*, jadi library besar seperti Docling dan PyTorch hanya ter-install jika fiturnya dipakai.

**Sebelum mulai:** kamu butuh Python 3.11 atau lebih baru (periksa dengan `python --version`), Git, dan [uv](https://github.com/astral-sh/uv) atau `pip`.

> [!NOTE]
> Contoh perintah di dokumentasi ini memakai sintaks shell Unix. Di Windows, perintah `zul`, `uv`, `pip`, dan `pytest` sama persis. Yang berbeda hanya perintah sistem seperti `cp`, dan perbedaannya disebut di tempatnya.

## Instalasi perintah zul

Zul belum diterbitkan di PyPI, jadi instalasinya memakai alamat repository.

Untuk memakai perintah `zul` di folder mana saja, install sebagai tool global dengan uv:

```shell
uv tool install git+https://github.com/kazuma313/zul_utilities.git
```

Untuk instalasi ke environment Python yang sedang aktif, gunakan pip:

```shell
pip install git+https://github.com/kazuma313/zul_utilities.git
```

Instalasi dasar berisi Typer, InquirerPy, Pydantic, PyYAML, NumPy, dan dependency-nya. Dengan instalasi itu, yang sudah bisa dipakai adalah perintah `zul`, config vector database dari `zul install`, `FakeEmbeddingModel`, `get_logger`, pengukur waktu, `documents_to_custom_json`, dan modul Computer Vision yang hanya butuh NumPy: `geometry`, `pose`, `zones`, `timers`, `distance`, `config`, dan `report`.

## Memilih extra

Setiap kelompok utilities punya extra sendiri. Tabel berikut memetakan extra ke utilities yang membutuhkannya:

| Extra | Dibutuhkan oleh | Library yang di-install | Tambahan ukuran |
|---|---|---|---|
| `milvus` | [`MilvusHelper`](memakai-milvus.md) | `pymilvus` | 55 MB |
| `redis` | [`RedisHelper`, `RedisVectorDB`](memakai-redis.md) | `redis`, `redisvl` | 6 MB |
| `converter` | [Markdown ke PDF dan PPTX](mengonversi-markdown.md) | `markdown`, `xhtml2pdf`, `python-pptx` | 52 MB |
| `analysis` | [`ChartGenerator`](membuat-grafik.md), [penyimpan hasil eksperimen](memakai-helper.md#menyimpan-hasil-eksperimen) | `matplotlib`, `pandas`, `scipy` | 197 MB |
| `pdf` | [`PDFProcessor`](memakai-helper.md#membaca-dan-memotong-pdf) | `pypdf`, `langchain-text-splitters` | 14 MB |
| `ocr` | [`DoclingVLMConverter`](membaca-dokumen-ocr.md) | `docling`, yang ikut meng-install PyTorch  | 3,4 GB |
| `llm` | [`AIService`](memanggil-llm-dan-embedding.md), [`react_graph`](memakai-helper.md#menjalankan-graph-langgraph-terkecil) | `langchain-openai`, `langgraph` | 27 MB |
| `gemini` | [OCR dengan Gemini](membaca-dokumen-ocr.md#membaca-pdf-dengan-gemini) | `google-genai` | 23 MB |
| `vision` | [`draw`, `masks`, dan `video` dari Computer Vision](menggambar-di-frame.md) | `opencv-python` | 118 MB |
| `tracking` | [`ByteTracker` dari Computer Vision](mendeteksi-dan-melacak-orang.md) | `lap` | 2 MB |
| `detection` | [Deteksi orang dengan RF-DETR](mendeteksi-dan-melacak-orang.md) | `vision`, `tracking`, dan `rfdetr`, yang ikut meng-install PyTorch, transformers, dan supervision  | 3,4 GB |
| `mcp` | [MCP server untuk code assistant](menghubungkan-code-assistant.md) | `mcp` | 33 MB |
| `evaluation` | [Evaluasi retrieval dan RAG dengan ragas](mengevaluasi-retrieval.md) | `ragas`, `openpyxl`, `rapidfuzz`, `tqdm` | 348 MB |
| `all` | Semua di atas | Semua di atas  | 3,7 GB |

Kolom terakhir adalah ruang disk yang ditambahkan extra itu dibanding instalasi dasar (60 MB), jika dipasang sendirian. Cara mengukurnya ada di [Seberapa besar tiap pilihan](#seberapa-besar-tiap-pilihan).

## Memasang per topik

Pasang hanya extra untuk topik yang kamu kerjakan. Tabel berikut menunjukkan perintahnya, dan ruang disk tambahan untuk kombinasi itu.

| Saya mau... | Extra | Tambahan ukuran |
|---|---|---|
| Memakai perintah `zul`, `zul build hexa`, dan helper kecil | Tidak ada | 0 |
| Menyimpan dan mencari vektor di [Milvus](memakai-milvus.md) atau [Redis](memakai-redis.md) | `milvus`, `redis` | 61 MB |
| Memanggil [LLM dan embedding](memanggil-llm-dan-embedding.md), atau menjalankan graph LangGraph | `llm` | 27 MB |
| Menghubungkan [code assistant lewat MCP](menghubungkan-code-assistant.md), termasuk merapikan struktur proyek | `mcp` | 33 MB |
| [Mengevaluasi retrieval](mengevaluasi-retrieval.md) dengan ragas, dengan Redis dan LLM | `evaluation`, `redis`, `llm` | sekitar 370 MB |
| Mengubah [Markdown menjadi PDF dan PPTX](mengonversi-markdown.md), membaca PDF, dan membuat grafik | `converter`, `pdf`, `analysis` | 244 MB |
| [Menggambar di frame](menggambar-di-frame.md) dan membaca video, tanpa model deteksi | `vision`, `tracking` | 120 MB |
| [Mendeteksi dan melacak orang](mendeteksi-dan-melacak-orang.md) dengan RF-DETR | `detection` | 3,4 GB |
| [Mengubah dokumen menjadi teks](membaca-dokumen-ocr.md) dengan Docling | `ocr` | 3,4 GB |
| [Mengubah dokumen menjadi teks](membaca-dokumen-ocr.md) dengan Gemini | `gemini` | 23 MB |
| Menghitung dengan garis, poligon, timer, arah hadap, dan jarak | Tidak ada | 0 |

Contohnya, untuk aplikasi yang memakai vector database dan LLM:

```shell
pip install "zul[milvus,llm] @ git+https://github.com/kazuma313/zul_utilities.git"
```

Beberapa topik tidak memakai extra:

- **Proyek hasil `zul build hexa`** punya `requirements.txt` sendiri (FastAPI, LangChain, LangGraph, Streamlit, dan lainnya). Instal dengan `pip install -r requirements.txt` di proyek itu, bukan lewat extra Zul.
- **Boilerplate computer vision** punya `pyproject.toml` sendiri yang meminta `zul[detection]`, jadi ia membawa model deteksi (3,4 GB).
- **Skill pool** di `framework/agentic/` dijalankan dari checkout repository, dan tiap skill punya kebutuhan sendiri: mind map hanya butuh Python, poster dan slide butuh Edge atau Chrome atau `python-pptx`, dan `youtube_transcript` butuh `youtube-transcript-api`. Rinciannya ada di [`framework/agentic/skills/REQUIREMENTS.md`](https://github.com/kazuma313/zul_utilities/blob/main/framework/agentic/skills/REQUIREMENTS.md).

## Seberapa besar tiap pilihan

Dua extra mendominasi ukuran: `ocr` dan `detection`, karena keduanya meng-install PyTorch. Yang lain jauh lebih kecil.

| Pilihan | Paket | Ruang disk |
|---|---|---|
| Instalasi dasar | 19 | 60 MB |
| Semua extra kecuali `ocr` dan `detection` | 158 | sekitar 650 MB |
| `zul[all]` | 203 | sekitar 3,8 GB |

Memasang semuanya (`zul[all]`) sekitar enam kali lebih besar dibanding semua extra tanpa `ocr` dan `detection`. Jika kamu tidak memakai deteksi orang atau Docling, jangan memasang kedua extra itu.

> [!NOTE]
> Angka diukur di environment pengembangan repository ini: Windows, Python 3.11, dengan PyTorch build CUDA 13 dari index PyTorch. Ukuran dihitung dari berkas yang ter-install (dari `RECORD` setiap paket), termasuk dependency dari dependency, dan tiap extra dihitung sendiri-sendiri dibanding instalasi dasar. Karena paket yang dipakai bersama dihitung di setiap extra, jumlah beberapa extra bisa lebih besar dari ukuran gabungannya. Di mesin lain angkanya berbeda, terutama untuk `ocr` dan `detection`, yang ukurannya mengikuti build PyTorch yang terpasang.

Library yang tidak diimpor tidak memakai memori. Modul inti Zul tidak mengimpor library dari extra mana pun, dan `test_dependencies.py` memastikan hal itu setiap kali test dijalankan. Karena itu, memasang lebih sedikit extra mengurangi ruang disk dan waktu instalasi, dan tidak mengubah memori program yang berjalan.

## Instalasi sebagian utilities

1. Pilih extra untuk fitur yang kamu pakai dari tabel di atas.

2. Install Zul dengan extra itu. Untuk lebih dari satu extra, pisahkan namanya dengan koma di dalam kurung siku.

    Dengan pip:

    ```shell
    pip install "zul[milvus] @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

    Di proyek yang dikelola uv:

    ```shell
    uv add "zul[milvus,redis] @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

    Di `requirements.txt`, tulis extra-nya di baris yang sama:

    ```text title="requirements.txt"
    zul[milvus,redis] @ git+https://github.com/kazuma313/zul_utilities.git
    ```

3. Pastikan utility-nya bisa diimpor, misalnya `MilvusHelper`:

    ```shell
    python -c "from zul.utilities.vector_DB.milvus_helper import MilvusHelper"
    ```

    Perintah itu selesai tanpa keluaran. Jika extra-nya belum ter-install, Python melempar `ModuleNotFoundError`. Extra yang perlu di-install ada di [ModuleNotFoundError saat mengimpor utility](#modulenotfounderror-saat-mengimpor-utility).

Untuk menambah fitur lain kemudian, jalankan lagi perintah langkah 2 dengan daftar extra yang lengkap, misalnya `zul[milvus,redis,pdf]`. Pip dan uv hanya meng-install library yang belum ada.

Untuk instalasi semua extra sekaligus:

```shell
pip install "zul[all] @ git+https://github.com/kazuma313/zul_utilities.git"
```

## Mengurangi instalasi yang sudah terlanjur besar

Pip dan `uv pip install` tidak melepas library saat sebuah extra dihapus dari perintah instalasi. Untuk mengecilkan environment yang sudah memasang `zul[all]`, buat environment baru yang hanya berisi extra yang dipakai:

```shell
uv venv .venv-baru
uv pip install --python .venv-baru "zul[milvus,llm] @ git+https://github.com/kazuma313/zul_utilities.git"
```

Pindahkan proyekmu ke environment itu, lalu hapus environment lama. Cara ini lebih aman daripada mencopot paket satu per satu, karena paket yang dipakai bersama oleh beberapa extra tidak ikut terlepas.

Untuk kontributor Zul, `uv sync --inexact` meng-install semuanya, termasuk PyTorch. Jika perubahanmu tidak menyentuh modul OCR atau deteksi, grup `ci` cukup untuk menjalankan test dan pemeriksa gaya kode tanpa PyTorch:

```shell
uv sync --inexact --no-default-groups --group ci
```

Grup itu yang dipakai workflow Pemeriksaan kode. Test yang butuh `docling` atau `rfdetr` dilewati.

## Instalasi tanpa dependency apa pun

Instalasi dasar tetap berisi Typer, InquirerPy, Pydantic, PyYAML, dan NumPy. Jika environment-mu hanya boleh berisi library yang benar-benar diimpor, install Zul tanpa dependency, lalu install sendiri library yang diimpor modul pilihanmu:

1. Install Zul tanpa dependency:

    ```shell
    pip install --no-deps "zul @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

2. Install library yang diimpor modul pilihanmu. `MilvusHelper` mengimpor `pymilvus`, Pydantic, dan PyYAML:

    ```shell
    pip install pymilvus pydantic pyyaml
    ```

3. Pastikan modulnya bisa diimpor:

    ```shell
    python -c "from zul.utilities.vector_DB.milvus_helper import MilvusHelper"
    ```

Dengan cara ini, perintah `zul` baru jalan setelah Typer dan InquirerPy di-install. `pip check` juga melaporkan dependency Zul yang belum ter-install, karena pip tidak tahu bahwa kamu sengaja melewatinya. Library yang diimpor setiap modul tercantum di halaman referensinya, misalnya [MilvusHelper](../referensi/milvus.md).

## Memeriksa hasilnya

Untuk memastikan perintah `zul` ter-install, jalankan:

```shell
zul --version
```

Perintah itu mencetak versi yang ter-install:

```text
zul version 0.1.0
```

Untuk memastikan library bisa diimpor, jalankan:

```shell
python -c "from zul.utilities.fake_embedding import FakeEmbeddingModel; print(FakeEmbeddingModel(dimension=4).encode('halo').shape)"
```

Perintah itu mencetak `(1, 4)`. `FakeEmbeddingModel` tidak membutuhkan extra, jadi perintah ini jalan di instalasi dasar.

## Mengatasi masalah

### Perintah zul tidak ditemukan

Setelah `uv tool install`, folder tempat uv menaruh perintah mungkin belum ada di `PATH`. Tambahkan dengan:

```shell
uv tool update-shell
```

Lalu buka terminal baru.

### Versi Python terlalu lama

Jika instalasi gagal dengan pesan tentang `requires-python`, environment-mu memakai Python di bawah 3.11. Dengan uv, kamu bisa meminta versi tertentu saat instalasi:

```shell
uv tool install --python 3.11 git+https://github.com/kazuma313/zul_utilities.git
```

### ModuleNotFoundError saat mengimpor utility

Pesan seperti `No module named 'pymilvus'` berarti extra untuk utility itu belum ter-install. Tabel berikut memetakan library di pesan error ke extra-nya:

| Library di pesan error | Extra |
|---|---|
| `pymilvus` | `milvus` |
| `redis`, `redisvl` | `redis` |
| `markdown`, `xhtml2pdf`, `pptx` | `converter` |
| `matplotlib`, `pandas`, `scipy` | `analysis` |
| `pypdf`, `langchain_text_splitters` | `pdf` |
| `docling` | `ocr` |
| `langchain_openai`, `langgraph` | `llm` |
| `google` | `gemini` |
| `cv2` | `vision` |
| `lap` | `tracking` |
| `rfdetr` | `detection` |
| `mcp` | `mcp` |
| `ragas`, `openpyxl`, `tqdm` | `evaluation` |

Install extra itu dengan perintah di [Instalasi sebagian utilities](#instalasi-sebagian-utilities), langkah 2.

## Halaman terkait

- [Membuat proyek baru](membuat-proyek.md) untuk langkah berikutnya.
- [Berkontribusi](berkontribusi.md) untuk instalasi Zul dari source supaya bisa diubah.
- [Perintah zul](../referensi/cli.md) untuk daftar lengkap perintah dan opsinya.
