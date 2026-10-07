# Memasang Zul

Zul terpasang sebagai perintah `zul` di terminal dan sebagai library Python. Instalasi dasar hanya memasang yang dibutuhkan perintah `zul`, config vector database, dan helper kecil. Utilities lain dipasang per fitur lewat *extra*, jadi library besar seperti Docling dan PyTorch hanya terpasang jika fiturnya dipakai.

**Sebelum mulai:** kamu butuh Python 3.11 atau lebih baru (periksa dengan `python --version`), Git, dan [uv](https://github.com/astral-sh/uv) atau `pip`.

> [!NOTE]
> Contoh perintah di dokumentasi ini memakai sintaks shell Unix. Di Windows, perintah `zul`, `uv`, `pip`, dan `pytest` sama persis. Yang berbeda hanya perintah sistem seperti `cp`, dan perbedaannya disebut di tempatnya.

## Memasang perintah zul

Zul belum diterbitkan di PyPI, jadi instalasinya memakai alamat repository.

Untuk memakai perintah `zul` di folder mana saja, pasang sebagai tool global dengan uv:

```shell
uv tool install git+https://github.com/kazuma313/zul_utilities.git
```

Untuk memasangnya ke environment Python yang sedang aktif, gunakan pip:

```shell
pip install git+https://github.com/kazuma313/zul_utilities.git
```

Instalasi dasar memasang Typer, InquirerPy, Pydantic, PyYAML, NumPy, dan dependency-nya. Dengan instalasi itu, yang sudah bisa dipakai adalah perintah `zul`, config vector database dari `zul install`, `FakeEmbeddingModel`, `get_logger`, pengukur waktu, dan `documents_to_custom_json`.

## Memilih extra

Setiap kelompok utilities punya extra sendiri. Tabel berikut memetakan extra ke utilities yang membutuhkannya:

| Extra | Dibutuhkan oleh | Library yang dipasang |
|---|---|---|
| `milvus` | [`MilvusHelper`](memakai-milvus.md) | `pymilvus` |
| `redis` | [`RedisHelper`, `RedisVectorDB`](memakai-redis.md) | `redis`, `redisvl` |
| `converter` | [Markdown ke PDF dan PPTX](mengonversi-markdown.md) | `markdown`, `xhtml2pdf`, `python-pptx` |
| `analysis` | [`ChartGenerator`](membuat-grafik.md), [penyimpan hasil eksperimen](memakai-helper.md#menyimpan-hasil-eksperimen) | `matplotlib`, `pandas`, `scipy` |
| `pdf` | [`PDFProcessor`](memakai-helper.md#membaca-dan-memotong-pdf) | `pypdf`, `langchain-text-splitters` |
| `ocr` | [`DoclingVLMConverter`](membaca-dokumen-ocr.md) | `docling`, yang ikut memasang PyTorch |
| `llm` | [`AIService`](memanggil-llm-dan-embedding.md), [`react_graph`](memakai-helper.md#menjalankan-graph-langgraph-terkecil) | `langchain-openai`, `langgraph` |
| `gemini` | [OCR dengan Gemini](membaca-dokumen-ocr.md#membaca-pdf-dengan-gemini) | `google-genai` |
| `all` | Semua di atas | Semua di atas |

## Memasang sebagian utilities

1. Pilih extra untuk fitur yang kamu pakai dari tabel di atas.

2. Pasang Zul dengan extra itu. Untuk lebih dari satu extra, pisahkan namanya dengan koma di dalam kurung siku.

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

    Perintah itu selesai tanpa keluaran. Jika extra-nya belum terpasang, Python melempar `ModuleNotFoundError`. Extra yang perlu dipasang ada di [ModuleNotFoundError saat mengimpor utility](#modulenotfounderror-saat-mengimpor-utility).

Untuk menambah fitur lain kemudian, jalankan lagi perintah langkah 2 dengan daftar extra yang lengkap, misalnya `zul[milvus,redis,pdf]`. Pip dan uv hanya memasang library yang belum ada.

Untuk memasang semuanya sekaligus:

```shell
pip install "zul[all] @ git+https://github.com/kazuma313/zul_utilities.git"
```

## Memasang tanpa dependency apa pun

Instalasi dasar tetap memasang Typer, InquirerPy, Pydantic, PyYAML, dan NumPy. Jika environment-mu hanya boleh berisi library yang benar-benar diimpor, pasang Zul tanpa dependency, lalu pasang sendiri library yang diimpor modul pilihanmu:

1. Pasang Zul tanpa dependency:

    ```shell
    pip install --no-deps "zul @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

2. Pasang library yang diimpor modul pilihanmu. `MilvusHelper` mengimpor `pymilvus`, Pydantic, dan PyYAML:

    ```shell
    pip install pymilvus pydantic pyyaml
    ```

3. Pastikan modulnya bisa diimpor:

    ```shell
    python -c "from zul.utilities.vector_DB.milvus_helper import MilvusHelper"
    ```

Dengan cara ini, perintah `zul` baru jalan setelah Typer dan InquirerPy dipasang. `pip check` juga melaporkan dependency Zul yang belum terpasang, karena pip tidak tahu bahwa kamu sengaja melewatinya. Library yang diimpor setiap modul tercantum di halaman referensinya, misalnya [MilvusHelper](../referensi/milvus.md).

## Pindah dari versi 0.1

Sampai versi 0.1.3, instalasi dasar ikut memasang Docling, LangChain OpenAI, dan LangGraph. Sejak versi 0.2.0, ketiganya dipasang lewat extra `ocr` dan `llm`. Jika kodemu memakai salah satu modul berikut, tambahkan extra-nya saat memperbarui Zul:

| Modul | Extra |
|---|---|
| `zul.utilities.OCR.docling_OCR` (juga `zul.utilities.docling_OCR`) | `ocr` |
| `zul.utilities.embedding_service` | `llm` |
| `zul.utilities.script_helper.ai_models` | `llm` |
| `zul.utilities.react_graph` | `llm` |

Contohnya, untuk kode yang memakai `DoclingVLMConverter` dan `AIService`:

```shell
pip install --upgrade "zul[ocr,llm] @ git+https://github.com/kazuma313/zul_utilities.git"
```

## Memeriksa hasilnya

Untuk memastikan perintah `zul` terpasang, jalankan:

```shell
zul --version
```

Perintah itu mencetak versi yang terpasang:

```text
zul version 0.2.0
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

Jika instalasi gagal dengan pesan tentang `requires-python`, environment-mu memakai Python di bawah 3.11. Dengan uv, kamu bisa meminta versi tertentu saat memasang:

```shell
uv tool install --python 3.11 git+https://github.com/kazuma313/zul_utilities.git
```

### ModuleNotFoundError saat mengimpor utility

Pesan seperti `No module named 'pymilvus'` berarti extra untuk utility itu belum terpasang. Tabel berikut memetakan library di pesan error ke extra-nya:

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

Pasang extra itu dengan perintah di [Memasang sebagian utilities](#memasang-sebagian-utilities), langkah 2.

## Halaman terkait

- [Membuat proyek baru](membuat-proyek.md) untuk langkah berikutnya.
- [Berkontribusi](berkontribusi.md) jika kamu ingin memasang Zul dari source untuk mengubahnya.
- [Perintah zul](../referensi/cli.md) untuk daftar lengkap perintah dan opsinya.
