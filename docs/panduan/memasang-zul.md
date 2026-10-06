# Memasang Zul

Halaman ini menunjukkan cara memasang Zul sebagai perintah `zul` di terminal dan sebagai library Python. Setelah selesai, `zul --version` berjalan dan `zul.utilities` bisa diimpor.

**Sebelum mulai:** kamu butuh Python 3.11 atau lebih baru (periksa dengan `python --version`), Git, dan [uv](https://github.com/astral-sh/uv) atau `pip`.

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

> [!NOTE]
> Instalasi dasar ikut memasang Docling, LangChain, dan LangGraph, sehingga unduhan pertama cukup besar.

## Menambahkan Zul sebagai dependency proyek

Jika proyekmu mengimpor `zul.utilities`, tulis baris berikut di `requirements.txt` proyek itu:

```text title="requirements.txt"
zul @ git+https://github.com/kazuma313/zul_utilities.git
```

## Memasang dependency utilities

Setiap kelompok utilities membutuhkan library tambahan. Library itu dipasang lewat *extra*, supaya kamu hanya memasang yang dipakai.

Tabel berikut memetakan extra ke utilities yang membutuhkannya:

| Extra | Dibutuhkan oleh | Library yang dipasang |
|---|---|---|
| `milvus` | [`MilvusHelper`](memakai-milvus.md) | `pymilvus` |
| `redis` | [`RedisHelper`, `RedisVectorDB`](memakai-redis.md) | `redis`, `redisvl`, `numpy` |
| `converter` | [Markdown ke PDF dan PPTX](mengonversi-markdown.md) | `markdown`, `xhtml2pdf`, `python-pptx` |
| `analysis` | [`ChartGenerator`](membuat-grafik.md) | `matplotlib`, `pandas`, `scipy`, `numpy` |
| `pdf` | [`PDFProcessor`](memakai-helper.md) | `pypdf`, `langchain-text-splitters` |
| `gemini` | [OCR dengan Gemini](membaca-dokumen-ocr.md) | `google-genai` |
| `all` | Semua di atas | Semua di atas |

Untuk memasang satu atau beberapa extra, tulis namanya di dalam kurung siku:

```shell
pip install "zul[milvus,redis] @ git+https://github.com/kazuma313/zul_utilities.git"
```

Untuk memasang semuanya:

```shell
pip install "zul[all] @ git+https://github.com/kazuma313/zul_utilities.git"
```

Jika kamu mengimpor sebuah utility tanpa extra-nya, Python melempar `ModuleNotFoundError` yang menyebut library yang kurang, misalnya `No module named 'pymilvus'`.

## Memeriksa hasilnya

Untuk memastikan perintah `zul` terpasang, jalankan:

```shell
zul --version
```

Perintah itu mencetak versi yang terpasang:

```text
zul version 0.1.3
```

Untuk memastikan library bisa diimpor, jalankan:

```shell
python -c "from zul.utilities.fake_embedding import FakeEmbeddingModel; print(FakeEmbeddingModel(dimension=4).encode('halo').shape)"
```

Perintah itu mencetak `(1, 4)`.

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

## Lihat juga

- [Membuat proyek baru](membuat-proyek.md) untuk langkah berikutnya.
- [Berkontribusi](berkontribusi.md) jika kamu ingin memasang Zul dari source untuk mengubahnya.
- [Perintah zul](../referensi/cli.md) untuk daftar lengkap perintah dan opsinya.
