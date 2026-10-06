# OCR

Modul OCR mengubah dokumen menjadi Markdown, teks, atau dict. Isinya: `DoclingVLMConverter` yang memakai Docling dan sebuah Vision Language Model (VLM), tiga fungsi OCR berbasis Google Gemini, dan satu prompt OCR siap pakai.

Baris berikut mengimpor semuanya:

```python
from zul.utilities.OCR.docling_OCR import DoclingVLMConverter
from zul.utilities.OCR.gemini_ocr import (
    create_gemini_client,
    process_pdf_with_gemini,
    setup_logger,
)
from zul.utilities.Prompts.ocr import OCR_VLM_FLOW_DESCRIPTION_PROMPT
```

`docling_OCR` tidak membutuhkan extra. `gemini_ocr` membutuhkan extra `gemini` (`google-genai`).

## Konstanta `docling_OCR`

Lokasi: `zul.utilities.OCR.docling_OCR`.

| Nama | Nilai | Keterangan |
|---|---|---|
| `DEFAULT_VLM_MODEL` | Nama model di server internal | Nama model yang dipakai `create_default` jika `DOCLING_VLM_MODEL` tidak diset. |
| `DEFAULT_VLM_URL` | Alamat server internal | URL endpoint yang dipakai `create_default` jika `DOCLING_VLM_URL` tidak diset. |
| `RESPONSE_FORMATS` | `dict` | Pemetaan nilai `response_format` ke `ResponseFormat` milik Docling. Lihat tabel berikut. |

Kunci `RESPONSE_FORMATS` adalah nilai yang diterima parameter `response_format`:

| Nilai | `ResponseFormat` Docling |
|---|---|
| `doctags` | `DOCTAGS` |
| `markdown` | `MARKDOWN` |
| `deepseek_markdown` | `DEEPSEEKOCR_MARKDOWN` |
| `html` | `HTML` |
| `otsl` | `OTSL` |
| `plaintext` | `PLAINTEXT` |

## `DoclingVLMConverter(model, hostname_and_port, ...)`

Menyiapkan konversi dokumen yang mengirim halaman PDF dan gambar ke VLM lewat endpoint chat completions yang kompatibel dengan OpenAI.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `model` | `str` | Wajib | Nama model VLM di endpoint. |
| `hostname_and_port` | `str` | Wajib | URL lengkap endpoint chat completions, termasuk path-nya. |
| `api_key` | `str` | `""` | API key. Jika kosong, header `Authorization` tidak dikirim. Jika diisi, dikirim sebagai `Bearer API_KEY`. |
| `prompt` | `str` | `"Convert this page to docling."` | Prompt konversi per halaman. |
| `picture_prompt` | `str` atau `None` | `None` | Prompt deskripsi gambar. `None` diganti `prompt` ditambah `" Describe diagrams, flowcharts, and shapes concisely."`. |
| `response_format` | `str` | `"doctags"` | Format keluaran model. Salah satu kunci `RESPONSE_FORMATS`, huruf besar-kecil bebas. |
| `temperature` | `float` | `0.0` | Keacakan keluaran model saat konversi halaman. |
| `max_tokens` | `int` | `4096` | Batas token per pemanggilan model. |
| `skip_special_tokens` | `bool` | `False` | Dikirim ke endpoint sebagai parameter `skip_special_tokens`. |
| `timeout` | `int` | `90` | Batas waktu request konversi halaman, dalam detik. |
| `scale` | `float` | `2.0` | Skala gambar halaman yang dikirim ke model. |
| `enable_picture_description` | `bool` | `False` | Jika `True`, gambar di dokumen dideskripsikan model memakai `picture_prompt`. |

**Melempar:** `ValueError` dengan pesan `Invalid response_format 'NILAI'. Valid options: doctags, markdown, deepseek_markdown, html, otsl, plaintext` jika `response_format` tidak dikenal.

Setiap parameter disimpan sebagai atribut dengan nama yang sama. Atribut `response_format` berisi anggota `ResponseFormat`, bukan teks.

Format masukan yang diterima:

| Format | Diproses dengan |
|---|---|
| PDF, gambar | Pipeline VLM: setiap halaman dikirim ke model. |
| DOCX, PPTX, HTML, AsciiDoc, CSV, Markdown | Pembaca bawaan Docling untuk format itu. |

Objek `DocumentConverter` milik Docling dibuat pada pemanggilan konversi pertama, lalu dipakai ulang. Mengubah atribut converter setelah itu tidak mengubah konversi berikutnya.

Contoh berikut membuat converter untuk model yang menulis Markdown:

```python
converter = DoclingVLMConverter(
    model="NAMA_MODEL",
    hostname_and_port="https://HOST/v1/chat/completions",
    api_key="API_KEY",
    prompt="Convert this page to markdown.",
    response_format="markdown",
)
```

`NAMA_MODEL` adalah nama model di endpoint, `HOST` alamat server model, dan `API_KEY` key-nya.

### `convert(document_path)`

Mengonversi satu dokumen dan mengembalikan objek hasil mentah dari Docling.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `document_path` | `str` | Wajib | Path ke dokumen. |

**Mengembalikan:** objek hasil `DocumentConverter.convert`. Atribut `document` menyediakan `export_to_markdown()`, `export_to_text()`, `export_to_dict()`, dan daftar `tables`.

### `convert_to_dict(document_path)`

Mengonversi satu dokumen dan mengembalikan struktur dokumennya.

**Mengembalikan:** `dict` dari `result.document.export_to_dict()`.

### `convert_to_text(document_path)`

Mengonversi satu dokumen dan mengembalikan teks polosnya.

**Mengembalikan:** `str` dari `result.document.export_to_text()`.

### `convert_to_markdown(document_path)`

Mengonversi satu dokumen dan mengembalikan Markdown.

**Mengembalikan:** `str` dari `result.document.export_to_markdown()`.

### `DoclingVLMConverter.create_default(api_key="sk", enable_picture_description=False)`

Membuat converter dengan prompt `"Convert this page to markdown."` dan `response_format="markdown"`. Method ini adalah classmethod.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `api_key` | `str` | `"sk"` | API key endpoint. |
| `enable_picture_description` | `bool` | `False` | Jika `True`, gambar di dokumen dideskripsikan. |

Nama model dan URL endpoint dibaca dari environment saat method dipanggil:

| Variabel | Kegunaan | Jika tidak diset |
|---|---|---|
| `DOCLING_VLM_MODEL` | Nama model. | `DEFAULT_VLM_MODEL` |
| `DOCLING_VLM_URL` | URL lengkap endpoint chat completions. | `DEFAULT_VLM_URL` |

**Mengembalikan:** `DoclingVLMConverter`.

## Fungsi Gemini

Lokasi: `zul.utilities.OCR.gemini_ocr`.

### `setup_logger()`

Mengatur logging dasar ke console dengan level `INFO` dan format `%(asctime)s - %(levelname)s - %(message)s`, lalu mengembalikan logger modul.

**Mengembalikan:** `logging.Logger` bernama `zul.utilities.OCR.gemini_ocr`.

### `create_gemini_client(api_key, logger)`

Membuat client Gemini.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `api_key` | `str` | Wajib | API key Google. |
| `logger` | `logging.Logger` | Wajib | Logger untuk mencatat proses dan kegagalan. |

**Mengembalikan:** `genai.Client`, atau `None` jika `api_key` kosong atau client gagal dibuat. Fungsi ini tidak melempar exception. Penyebab kegagalan ditulis ke `logger`.

### `process_pdf_with_gemini(client, pdf_path, prompt, logger, model_name="gemini-2.5-pro")`

Mengunggah PDF ke Gemini, meminta model memprosesnya sesuai prompt, lalu menghapus file yang diunggah dari server Gemini.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `client` | `genai.Client` | Wajib | Client dari `create_gemini_client`. |
| `pdf_path` | `str` | Wajib | Path ke file PDF lokal. |
| `prompt` | `str` | Wajib | Instruksi untuk model. |
| `logger` | `logging.Logger` | Wajib | Logger untuk mencatat proses dan kegagalan. |
| `model_name` | `str` | `"gemini-2.5-pro"` | Model Gemini yang dipakai. |

**Mengembalikan:** `str` berisi teks jawaban model, atau `None` jika file tidak ada atau unggahan maupun request gagal. Fungsi ini tidak melempar exception. Penyebab kegagalan ditulis ke `logger`.

File yang sudah terunggah selalu dicoba dihapus, juga saat request gagal.

Contoh berikut memproses satu PDF dan memeriksa hasilnya:

```python
import os

logger = setup_logger()
client = create_gemini_client(api_key=os.environ["GOOGLE_API_KEY"], logger=logger)

markdown = process_pdf_with_gemini(
    client=client,
    pdf_path="dokumen.pdf",
    prompt="Extract the text content from this PDF and return it in markdown format.",
    logger=logger,
)

if markdown is None:
    raise RuntimeError("OCR gagal; lihat log untuk penyebabnya")
```

## `OCR_VLM_FLOW_DESCRIPTION_PROMPT`

Prompt OCR berupa `str`. Lokasi: `zul.utilities.Prompts.ocr`. Prompt ini meminta model:

- mengubah heading, paragraf, daftar, dan tabel menjadi Markdown,
- menulis ringkasan satu kalimat sebagai alt-text setiap gambar, diikuti deskripsi rinci dalam blockquote, semuanya dalam Bahasa Indonesia,
- menjelaskan flowchart dan diagram sebagai daftar bernomor langkah demi langkah,
- menulis rumus dalam LaTeX,
- mengembalikan Markdown saja, tanpa komentar tambahan dan tanpa membungkusnya dalam blok kode.

## Path impor lama

Modul `zul.utilities.docling_OCR` tetap bisa dipakai dan meneruskan ke `zul.utilities.OCR.docling_OCR`. Dari path lama itu hanya `DoclingVLMConverter` yang bisa diimpor.

## Lihat juga

- [Mengubah dokumen menjadi teks](../panduan/membaca-dokumen-ocr.md) untuk langkah pemakaian.
- [Helper kecil](helper.md) untuk `PDFProcessor`, yang membaca PDF berteks tanpa memanggil model.
