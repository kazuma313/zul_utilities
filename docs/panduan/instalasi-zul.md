# Instalasi Zul

Zul ter-install sebagai perintah `zul` di terminal dan sebagai library Python. Instalasi dasar hanya berisi yang dibutuhkan perintah `zul`, config vector database, dan helper kecil. Utilities lain di-install per fitur lewat *extra*, jadi library besar seperti Docling dan PyTorch hanya ter-install jika fiturnya dipakai.

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

| Extra | Dibutuhkan oleh | Library yang di-install |
|---|---|---|
| `milvus` | [`MilvusHelper`](memakai-milvus.md) | `pymilvus` |
| `redis` | [`RedisHelper`, `RedisVectorDB`](memakai-redis.md) | `redis`, `redisvl` |
| `converter` | [Markdown ke PDF dan PPTX](mengonversi-markdown.md) | `markdown`, `xhtml2pdf`, `python-pptx` |
| `analysis` | [`ChartGenerator`](membuat-grafik.md), [penyimpan hasil eksperimen](memakai-helper.md#menyimpan-hasil-eksperimen) | `matplotlib`, `pandas`, `scipy` |
| `pdf` | [`PDFProcessor`](memakai-helper.md#membaca-dan-memotong-pdf) | `pypdf`, `langchain-text-splitters` |
| `ocr` | [`DoclingVLMConverter`](membaca-dokumen-ocr.md) | `docling`, yang ikut meng-install PyTorch |
| `llm` | [`AIService`](memanggil-llm-dan-embedding.md), [`react_graph`](memakai-helper.md#menjalankan-graph-langgraph-terkecil) | `langchain-openai`, `langgraph` |
| `gemini` | [OCR dengan Gemini](membaca-dokumen-ocr.md#membaca-pdf-dengan-gemini) | `google-genai` |
| `vision` | [`draw`, `masks`, dan `video` dari Computer Vision](menggambar-di-frame.md) | `opencv-python` |
| `yolo` | [Deteksi dan tracking dari Computer Vision](mendeteksi-dan-melacak-orang.md) | `vision`, `ultralytics`, yang ikut meng-install PyTorch, dan `lap` |
| `all` | Semua di atas | Semua di atas |

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
zul version 0.0.1
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
| `ultralytics` | `yolo` |

Install extra itu dengan perintah di [Instalasi sebagian utilities](#instalasi-sebagian-utilities), langkah 2.

## Halaman terkait

- [Membuat proyek baru](membuat-proyek.md) untuk langkah berikutnya.
- [Berkontribusi](berkontribusi.md) untuk instalasi Zul dari source supaya bisa diubah.
- [Perintah zul](../referensi/cli.md) untuk daftar lengkap perintah dan opsinya.
