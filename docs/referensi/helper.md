# Helper kecil

Helper di `zul.utilities` yang tidak punya halaman referensi sendiri: logger, embedding palsu, isi folder `script_helper`, dan contoh graph LangGraph terkecil.

Tabel berikut memetakan setiap modul ke isinya dan extra yang dibutuhkan:

| Modul | Isi | Extra |
|---|---|---|
| `zul.utilities.logger` | [`get_logger`](#logger) | Tidak ada |
| `zul.utilities.fake_embedding` | [`FakeEmbeddingModel`](#fakeembeddingmodeldimension2560-seednone) | Tidak ada |
| `zul.utilities.script_helper.ai_models` | [`AIService` versi ringkas](#ai_models) | `llm` |
| `zul.utilities.script_helper.eval_performance` | [`timer_func`, `TimerDecorator`](#eval_performance) | Tidak ada |
| `zul.utilities.script_helper.json_helper` | [`documents_to_custom_json`](#documents_to_custom_jsondocuments-key_mappingnone-return_dictfalse) | Tidak ada |
| `zul.utilities.script_helper.read_pdf2` | [`PDFConfig`](#pdfconfig), [`PDFProcessor`](#pdfprocessorconfignone) | `pdf` |
| `zul.utilities.script_helper.save_file` | [`save_text_to_md`, `save_latency_to_csv`](#save_file) | `analysis` |
| `zul.utilities.react_graph` | [`graph`](#react_graph) | `llm` |

## Logger

Lokasi: `zul.utilities.logger`.

### Konstanta

| Nama | Nilai | Keterangan |
|---|---|---|
| `DEFAULT_LOGGER_NAME` | `"my_service"` | Nama logger bawaan. |
| `DEFAULT_LOG_FILE` | `"logs/app.log"` | File log bawaan. |
| `LOGGING_CONFIG` | `dict` | Konfigurasi `logging.config.dictConfig` yang menjadi dasar setiap logger. |

`LOGGING_CONFIG` menetapkan hal berikut:

| Pengaturan | Nilai |
|---|---|
| Handler | Console (`logging.StreamHandler`) dan file (`logging.handlers.RotatingFileHandler`) |
| Rotasi file | Saat ukuran mencapai 1.000.000 byte, dengan 5 file cadangan |
| Encoding file | `utf-8` |
| `propagate` | `False` |
| `disable_existing_loggers` | `False`, sehingga logger library lain tetap berjalan |

Setiap baris log ditulis dengan format berikut:

```text
%(asctime)s | %(levelname)s | %(name)s | %(message)s
```

### `get_logger(name="my_service", level="INFO", log_file="logs/app.log")`

Mengembalikan logger yang menulis ke console dan ke file yang berotasi.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `name` | `str` | `DEFAULT_LOGGER_NAME` | Nama logger. |
| `level` | `str` | `"INFO"` | Level log, misalnya `DEBUG` atau `WARNING`. |
| `log_file` | `str` | `DEFAULT_LOG_FILE` | Path file log. Foldernya dibuat jika belum ada. |

**Mengembalikan:** `logging.Logger`.

Handler dipasang sekali per nama logger. Pemanggilan berikutnya dengan nama yang sama mengembalikan logger yang sama, dan `level` serta `log_file` pada pemanggilan itu diabaikan.

Contoh berikut membuat logger untuk proses ingestion:

```python
from zul.utilities.logger import get_logger

logger = get_logger("ingestion", level="DEBUG", log_file="logs/ingestion.log")
logger.info("mulai memproses %d dokumen", 120)
```

## `FakeEmbeddingModel(dimension=2560, seed=None)`

Menghasilkan vektor acak yang deterministik sebagai pengganti model embedding saat test. Lokasi: `zul.utilities.fake_embedding`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `dimension` | `int` | `2560` | Dimensi vektor. |
| `seed` | `int` atau `None` | `None` | Benih acak. `seed` berbeda menghasilkan vektor berbeda untuk teks yang sama. |

Teks yang sama selalu menghasilkan vektor yang sama untuk `seed` yang sama, antar pemanggilan dan antar proses Python. Vektornya acak, jadi kemiripan antar teks tidak bermakna.

**Atribut:** `dimension` dan `seed`, sesuai parameter.

### `encode(texts, normalize=True)`

Mengubah satu teks atau daftar teks menjadi vektor.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `texts` | `str` atau `list[str]` | Wajib | Satu teks atau daftar teks. |
| `normalize` | `bool` | `True` | Jika `True`, setiap vektor dinormalkan ke panjang 1. |

**Mengembalikan:** `numpy.ndarray` berbentuk `(jumlah teks, dimension)`. Satu teks menghasilkan bentuk `(1, dimension)`.

Contoh berikut mengambil satu vektor datar:

```python
from zul.utilities.fake_embedding import FakeEmbeddingModel

model = FakeEmbeddingModel(dimension=768, seed=42)
vector = model.encode("hallo").flatten()
```

### `similarity(embedding1, embedding2)`

Menghitung cosine similarity dua vektor.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `embedding1` | `numpy.ndarray` | Wajib | Vektor pertama, satu dimensi. |
| `embedding2` | `numpy.ndarray` | Wajib | Vektor kedua, satu dimensi. |

**Mengembalikan:** `float` antara -1 dan 1. Bernilai `0.0` jika salah satu vektor panjangnya nol.

### `get_dimension()`

Mengembalikan dimensi vektor.

**Mengembalikan:** `int`.

### `__call__(texts)`

Memanggil `encode(texts)`, sehingga objek model bisa dipanggil langsung seperti fungsi.

**Mengembalikan:** `numpy.ndarray`, sama dengan `encode`.

## `ai_models`

`AIService` versi ringkas yang memakai dataclass dan environment variable. Lokasi: `zul.utilities.script_helper.ai_models`. Modul ini membutuhkan extra `llm` (`langchain-openai`). Untuk validasi Pydantic, file config, dan model respons, pakai versi lengkap di [AI Service](ai-service.md).

### `LLMConfig`

Dataclass pengaturan chat model. Setiap nilai bawaan dibaca dari environment saat objek dibuat.

| Field | Tipe | Environment variable | Default jika variabel tidak diset |
|---|---|---|---|
| `base_url` | `str` | `LLM_BASE_URL` | Alamat server internal |
| `api_key` | `str` | `LLM_API_KEY` | `""` |
| `model` | `str` | `LLM_MODEL` | `"qwen2-32B-Instruct-resolved"` |
| `temperature` | `float` | `LLM_TEMPERATURE` | `0.1` |

**Melempar:** `ValueError` dengan pesan `Valid LLM API key is required` jika `api_key` kosong atau bernilai `"your-llm-api-key"`.

### `EmbeddingConfig`

Dataclass pengaturan model embedding.

| Field | Tipe | Environment variable | Default jika variabel tidak diset |
|---|---|---|---|
| `base_url` | `str` | `EMBEDDING_BASE_URL` | `""` |
| `api_key` | `str` | `EMBEDDING_API_KEY` | `""` |
| `model` | `str` | `EMBEDDING_MODEL` | `"Qwen3-Embedding-4B"` |

**Melempar:** `ValueError` dengan pesan `Valid Embedding API key is required` jika `api_key` kosong atau bernilai `"your-embedding-api-key"`.

### `AIConfig`

Dataclass akar konfigurasi.

| Field | Tipe | Default | Keterangan |
|---|---|---|---|
| `llm_config` | `LLMConfig` | `LLMConfig()` | Pengaturan chat model. |
| `embedding_config` | `EmbeddingConfig` atau `None` | `EmbeddingConfig()` | Pengaturan embedding. Karena nilai bawaannya dibuat otomatis, `AIConfig()` membutuhkan `EMBEDDING_API_KEY`. Berikan `None` untuk service tanpa embedding. |
| `enable_embedding` | `bool` | `True` | Jika `False`, client embedding tidak dibuat. |

### `AIService(config=None)`

Membuat client `ChatOpenAI` dan, jika embedding aktif, client `OpenAIEmbeddings`. Berbeda dari versi lengkap, kedua client dibuat langsung saat objek dibuat.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `config` | `AIConfig` atau `None` | `None` | Konfigurasi. `None` berarti `AIConfig()` dari environment. |

**Atribut:** `config`, `llm` (`ChatOpenAI`), dan `embedding` (`OpenAIEmbeddings` atau `None`).

| Method | Mengembalikan | Melempar |
|---|---|---|
| `chat(prompt)` | `str` berisi teks jawaban model | `RuntimeError` dengan pesan `Chat failed: ...` jika pemanggilan gagal |
| `embed(text)` | `list` berisi vektor embedding | `ValueError` dengan pesan `Embedding not enabled or configured` jika embedding tidak aktif; `RuntimeError` dengan pesan `Embedding failed: ...` jika pemanggilan gagal |
| `is_embedding_enabled()` | `bool` | Tidak ada |

## `eval_performance`

Decorator pengukur waktu eksekusi. Lokasi: `zul.utilities.script_helper.eval_performance`.

### `timer_func(func)`

Membungkus sebuah fungsi sehingga durasi setiap pemanggilannya dicetak dalam bentuk `Function 'NAMA' executed in 0.0000s`. Nilai kembalian fungsi asli diteruskan.

### `TimerDecorator(func)`

Membungkus sebuah fungsi sehingga durasi setiap pemanggilannya dicetak dan disimpan. Nama dan docstring fungsi asli disalin ke objek pembungkus.

**Atribut:**

| Atribut | Tipe | Keterangan |
|---|---|---|
| `func` | fungsi | Fungsi asli. |
| `times` | `list[float]` | Durasi setiap pemanggilan, dalam detik. |
| `total_time` | `float` | Jumlah semua durasi. |
| `call_count` | `int` | Jumlah pemanggilan. |

| Method | Mengembalikan |
|---|---|
| `get_last_time()` | Durasi pemanggilan terakhir dalam detik, atau `None` jika belum pernah dipanggil. |
| `get_all_times()` | Salinan daftar semua durasi. |
| `get_average_time()` | Rata-rata durasi dalam detik, atau `0` jika belum pernah dipanggil. |
| `reset_times()` | `None`. Menghapus semua catatan. |

Contoh berikut mengukur tiga pemanggilan:

```python
from zul.utilities.script_helper.eval_performance import TimerDecorator


@TimerDecorator
def search(query):
    return query.upper()


for query in ["satu", "dua", "tiga"]:
    search(query)

print(len(search.get_all_times()))
```

Selain satu baris durasi per pemanggilan, kode itu mencetak jumlah catatan:

```text
3
```

## `documents_to_custom_json(documents, key_mapping=None, return_dict=False)`

Mengubah daftar `Document` LangChain menjadi JSON. Lokasi: `zul.utilities.script_helper.json_helper`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `documents` | daftar objek dengan `page_content` dan `metadata` | Wajib | Dokumen yang diubah. |
| `key_mapping` | `dict` atau `None` | `None` | Pemetaan nama kunci lama ke nama baru, untuk `page_content` dan kunci `metadata`. `None` berarti nama asli dipakai. |
| `return_dict` | `bool` | `False` | Jika `True`, mengembalikan objek Python, bukan string. |

**Mengembalikan:** `str` berisi JSON dengan indentasi dua spasi, atau `list[dict]` jika `return_dict=True`. Setiap dokumen menjadi satu dict: `page_content` dan setiap kunci `metadata` berada di tingkat atas.

Jika nama sebuah kunci `metadata` sama dengan nama kunci isi dokumen, kunci itu diberi awalan `metadata_` supaya isi dokumen tidak tertimpa.

**Melempar:** `ValueError` jika hasilnya tidak bisa diubah menjadi JSON, misalnya karena `metadata` memuat objek yang bukan tipe JSON.

## `PDFConfig`

Dataclass pengaturan `PDFProcessor`. Lokasi: `zul.utilities.script_helper.read_pdf2`. Modul ini membutuhkan extra `pdf` (`pypdf`, `langchain-text-splitters`).

| Field | Tipe | Default | Keterangan |
|---|---|---|---|
| `encoding` | `str` | `"utf-8"` | Encoding teks. |
| `strict` | `bool` | `False` | Mode strict `pypdf` saat membuka file. |
| `verbose` | `bool` | `True` | Jika `True`, setiap pesan kesalahan dicetak dengan awalan `PDFProcessor Error:`. |

## `PDFProcessor(config=None)`

Membaca teks yang tertanam di PDF dan memotongnya menjadi chunk. Lokasi: `zul.utilities.script_helper.read_pdf2`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `config` | `PDFConfig` atau `None` | `None` | Pengaturan. `None` berarti `PDFConfig()`. |

Method `PDFProcessor` tidak melempar exception saat PDF gagal dibaca. Mereka mengembalikan `None` atau daftar kosong, dan pesan kesalahannya tersimpan di `last_error`.

**Atribut dan properti:**

| Nama | Tipe | Keterangan |
|---|---|---|
| `config` | `PDFConfig` | Pengaturan aktif. |
| `last_error` | `str` atau `None` | Pesan kesalahan terakhir. Properti baca-saja. |
| `found_pdf_files` | `list[str]` | Salinan daftar PDF dari pemindaian folder terakhir. Properti baca-saja. |

`len(pdf)` mengembalikan jumlah PDF dari pemindaian folder terakhir.

### `get_pdf_files(folder_path)`

Mencari semua file berekstensi `.pdf` di sebuah folder dan subfoldernya. Huruf besar-kecil ekstensi diabaikan.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `folder_path` | `str` atau `Path` | Wajib | Folder yang dipindai. |

**Mengembalikan:** `list[str]` berisi path file. Daftar kosong jika folder tidak ada atau pemindaian gagal.

### `read_pdf_pages(file_path)`

Membaca teks setiap halaman sebuah PDF.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `file_path` | `str` atau `Path` | Wajib | Path ke file PDF. |

**Mengembalikan:** `list[str]` berisi teks tiap halaman, atau `None` jika file tidak ada atau tidak bisa dibaca. Halaman yang gagal dibaca menjadi string kosong.

### `read_pdf_as_single_text(file_path)`

Membaca seluruh PDF sebagai satu teks, dengan halaman disambung baris baru.

**Mengembalikan:** `str`, atau `None` jika file gagal dibaca.

### `chunk_per_page(file_path)`

Membuat satu `Document` LangChain untuk setiap halaman.

**Mengembalikan:** `list[Document]` tanpa metadata. Daftar kosong jika file gagal dibaca.

### `chunk_recursive_character_splitter(file_path, chunk_size=4000, overlap=450, separators=None, length_function=len, is_sperator=True)`

Membaca PDF sebagai satu teks, lalu memotongnya dengan `RecursiveCharacterTextSplitter` dari LangChain.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `file_path` | `str` atau `Path` | Wajib | Path ke file PDF. |
| `chunk_size` | `int` | `4000` | Panjang maksimum tiap chunk, diukur dengan `length_function`. |
| `overlap` | `int` | `450` | Panjang bagian yang tumpang-tindih antar chunk. |
| `separators` | `list[str]` atau `None` | `None` | Pemisah yang dicoba berurutan. `None` diganti `["\n\n", "\n", " ", ""]`. |
| `length_function` | fungsi | `len` | Fungsi pengukur panjang teks. |
| `is_sperator` | `bool` | `True` | Diteruskan ke splitter sebagai `is_separator_regex`. Nama parameter ditulis sesuai kode. |

**Mengembalikan:** `list[Document]`. Daftar kosong jika file gagal dibaca atau teksnya kosong.

### `list_to_text(list_of_text)`

Menyambung daftar teks menjadi satu teks dengan baris baru, lalu membuang spasi di awal dan akhir. Method statis.

**Mengembalikan:** `str`. String kosong jika daftarnya kosong.

### `get_min_max_length_list(document)`

Menghitung panjang terpendek dan terpanjang dari daftar teks atau daftar objek ber-`page_content`. Method statis.

**Mengembalikan:** tuple `(minimum, maksimum)`. Bernilai `(0, 0)` jika daftarnya kosong.

### `process_folder(folder_path)`

Membaca semua PDF di sebuah folder dan subfoldernya, lalu meringkasnya.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `folder_path` | `str` atau `Path` | Wajib | Folder yang diproses. |

**Mengembalikan:** `dict` dengan kunci berikut:

| Kunci | Tipe | Keterangan |
|---|---|---|
| `total_files` | `int` | Jumlah PDF yang ditemukan. |
| `processed_files` | `int` | Jumlah PDF yang berhasil dibaca. |
| `failed_files` | `int` | Jumlah PDF yang gagal dibaca. |
| `total_pages` | `int` | Jumlah halaman dari semua PDF yang berhasil dibaca. |
| `files_data` | `list[dict]` | Satu dict per PDF yang berhasil dibaca: `file_path`, `pages_count`, `total_text_length`, dan `min_max_page_length`. |

Contoh berikut meringkas satu folder:

```python
from zul.utilities.script_helper.read_pdf2 import PDFProcessor

pdf = PDFProcessor()
summary = pdf.process_folder("dokumen/")

print(summary["total_files"], summary["total_pages"], summary["failed_files"])
```

## `save_file`

Penyimpan hasil eksperimen ke folder `data/` di direktori kerja saat ini. Lokasi: `zul.utilities.script_helper.save_file`. Modul ini membutuhkan extra `analysis`, karena mengimpor `pandas`. Folder `data/` dibuat jika belum ada.

### `save_text_to_md(text_result, filename)`

Menulis teks ke `data/FILENAME.md` dengan encoding UTF-8.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `text_result` | `str` | Wajib | Teks yang disimpan. |
| `filename` | `str` | Wajib | Nama file tanpa ekstensi. |

**Mengembalikan:** `None`.

### `save_latency_to_csv(mapping, file_name="query_latency_recursive_results")`

Menulis data latency ke `data/FILE_NAME.csv`, tanpa kolom indeks.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `mapping` | `dict` | Wajib | Nama kolom ke daftar nilai. Semua daftar harus sama panjang. |
| `file_name` | `str` | `"query_latency_recursive_results"` | Nama file tanpa ekstensi. |

**Mengembalikan:** `None`.

**Melempar:** `ValueError` dari `pandas` jika panjang daftar berbeda.

## `react_graph`

Contoh graph LangGraph terkecil: satu state dan satu node. Lokasi: `zul.utilities.react_graph`. Modul ini membutuhkan extra `llm` (`langgraph`).

| Nama | Jenis | Keterangan |
|---|---|---|
| `OverallState` | Model Pydantic | State graph, dengan satu field `a` bertipe `str`. |
| `node(state)` | Fungsi | Node satu-satunya. Mengembalikan `{"a": "goodbye"}`. |
| `builder` | `StateGraph` | Graph sebelum di-compile: `START` ke `node` ke `END`. |
| `graph` | Graph ter-compile | Hasil `builder.compile()`, siap dipanggil dengan `invoke`. |

Contoh berikut memanggil graph itu:

```python
from zul.utilities.react_graph import graph

print(graph.invoke({"a": "hello"}))
```

Kode itu mencetak state akhir:

```text
{'a': 'goodbye'}
```

## Path impor lama

Beberapa modul pernah berada di lokasi lain. Path lama tetap bisa dipakai dan meneruskan ke lokasi sekarang:

| Path lama | Lokasi sekarang | Yang bisa diimpor |
|---|---|---|
| `zul.utilities.docling_OCR` | `zul.utilities.OCR.docling_OCR` | `DoclingVLMConverter` |
| `zul.utilities.redis_vector_helper` | `zul.utilities.vector_DB.redis_helper` | `RedisVectorDB`, `reciprocal_rank_fusion` |
| `zul.utilities.md_to_pdf` | `zul.utilities.markdown_converter.md_to_pdf` | `MarkdownToPDFConverter` |
| `zul.utilities.md_to_ppt` | `zul.utilities.markdown_converter.md_to_ppt` | `DynamicMarkdownToPPTXService` |
| `zul.utilities.time` | `zul.utilities.script_helper.eval_performance` | `TimerDecorator`, `timer_func` |

Kode baru sebaiknya memakai lokasi sekarang.

## Halaman terkait

- [Memakai helper kecil](../panduan/memakai-helper.md) untuk langkah pemakaian.
- [AI Service](ai-service.md) untuk `AIService` versi lengkap.
- [OCR](ocr.md) untuk PDF hasil scan.
- [ChartGenerator](grafik.md) untuk menggambar durasi dari `TimerDecorator`.
