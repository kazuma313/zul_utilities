# Mengubah dokumen menjadi teks

PDF, gambar, dan dokumen lain bisa diubah menjadi Markdown atau teks, supaya bisa dipotong menjadi chunk dan disimpan ke vector database. Ada dua jalur: `DoclingVLMConverter`, yang mengirim halaman ke *Vision Language Model* (VLM) pilihanmu, dan fungsi OCR berbasis Google Gemini.

**Sebelum mulai:** kamu butuh Zul yang sudah terpasang ([Memasang Zul](memasang-zul.md)). Untuk jalur Docling, kamu butuh endpoint *chat completions* yang kompatibel dengan OpenAI dan melayani sebuah model VLM. Untuk jalur Gemini, kamu butuh API key Google. Jika PDF-mu berisi teks yang bisa diseleksi, kamu tidak butuh OCR: pakai `PDFProcessor` di [Memakai helper kecil](memakai-helper.md).

## Mengonversi dokumen dengan Docling

1. Pasang Zul dengan extra `ocr`. Extra ini memasang Docling, yang ikut membawa PyTorch, jadi unduhannya besar:

    ```shell
    pip install "zul[ocr] @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

2. Buat converter dengan nama model, alamat endpoint, dan format keluaran model:

    ```python
    from zul.utilities.OCR.docling_OCR import DoclingVLMConverter

    converter = DoclingVLMConverter(
        model="NAMA_MODEL",
        hostname_and_port="https://HOST/v1/chat/completions",
        api_key="API_KEY",
        prompt="Convert this page to markdown.",
        response_format="markdown",
    )
    ```

    Ganti `NAMA_MODEL` dengan nama model VLM di endpoint, misalnya `Qwen3-VL-8B-Instruct`. Ganti `HOST` dengan alamat server model, dan `API_KEY` dengan key-nya. `hostname_and_port` adalah URL lengkap endpoint, termasuk path-nya.

3. Konversi dokumen ke bentuk yang kamu butuhkan:

    ```python
    markdown = converter.convert_to_markdown("dokumen.pdf")
    text = converter.convert_to_text("dokumen.pdf")
    data = converter.convert_to_dict("dokumen.pdf")
    ```

    Converter menerima PDF, gambar, DOCX, PPTX, HTML, AsciiDoc, CSV, dan Markdown. Halaman PDF dan gambar dikirim ke VLM.

4. Saat memakai model lain, cocokkan `response_format` dengan format yang ditulis model itu. Pakai `markdown` untuk VLM umum yang diminta menulis Markdown, dan `doctags` (nilai bawaan) untuk model yang menulis DocTags. Nilai di luar daftar yang didukung melempar `ValueError`. Daftarnya ada di [Referensi OCR](../referensi/ocr.md).

## Menyertakan deskripsi gambar

Secara bawaan, gambar di dalam dokumen tidak dijelaskan.

1. Buat converter dengan `enable_picture_description=True` dan prompt untuk gambar:

    ```python
    converter = DoclingVLMConverter(
        model="NAMA_MODEL",
        hostname_and_port="https://HOST/v1/chat/completions",
        api_key="API_KEY",
        prompt="Convert this page to markdown.",
        response_format="markdown",
        enable_picture_description=True,
        picture_prompt="Describe the image and flowchart in detail.",
    )
    ```

2. Konversi dokumen seperti biasa:

    ```python
    markdown = converter.convert_to_markdown("sop.pdf")
    ```

    Deskripsi gambar memanggil model lagi untuk gambar di dokumen, jadi konversi berjalan lebih lama.

## Mengambil tabel sebagai DataFrame

1. Panggil `convert`, yang mengembalikan objek hasil dari Docling, bukan teks:

    ```python
    result = converter.convert("laporan.pdf")
    ```

2. Ubah setiap tabel di dokumen menjadi DataFrame, lalu simpan sebagai CSV:

    ```python
    for index, table in enumerate(result.document.tables, start=1):
        dataframe = table.export_to_dataframe(doc=result.document)
        dataframe.to_csv(f"tabel_{index}.csv", index=False)
    ```

    Objek `result.document` juga menyediakan `export_to_markdown()`, `export_to_text()`, dan `export_to_dict()`.

## Memakai converter bawaan

`create_default` membuat converter berformat `markdown` tanpa menulis nama model dan endpoint di kode. Model dan endpoint bawaannya menunjuk ke server internal, jadi arahkan ke server-mu lewat environment.

1. Set nama model dan URL endpoint di environment:

    ```shell
    export DOCLING_VLM_MODEL=NAMA_MODEL
    export DOCLING_VLM_URL=https://HOST/v1/chat/completions
    ```

    Ganti `NAMA_MODEL` dan `HOST` seperti pada bagian sebelumnya. Di PowerShell, pakai `$env:DOCLING_VLM_MODEL = "NAMA_MODEL"`.

2. Buat converter dengan API key-mu:

    ```python
    converter = DoclingVLMConverter.create_default(api_key="API_KEY")
    ```

## Membaca PDF dengan Gemini

Jalur ini mengunggah PDF ke Gemini, meminta model memprosesnya sesuai prompt, lalu menghapus file dari server Gemini.

1. Pasang Zul dengan extra `gemini`:

    ```shell
    pip install "zul[gemini] @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

2. Simpan API key Google di environment:

    ```shell
    export GOOGLE_API_KEY=API_KEY
    ```

    Ganti `API_KEY` dengan key-mu.

3. Buat logger dan client, lalu proses file:

    ```python
    import os

    from zul.utilities.OCR.gemini_ocr import (
        create_gemini_client,
        process_pdf_with_gemini,
        setup_logger,
    )

    logger = setup_logger()
    client = create_gemini_client(api_key=os.environ["GOOGLE_API_KEY"], logger=logger)

    markdown = process_pdf_with_gemini(
        client=client,
        pdf_path="dokumen.pdf",
        prompt="Extract the text content from this PDF and return it in markdown format.",
        logger=logger,
        model_name="gemini-2.5-pro",
    )
    ```

4. Periksa nilai kembaliannya. Kedua fungsi tidak melempar exception saat gagal. Mereka mengembalikan `None` dan menulis penyebabnya ke logger:

    ```python
    if markdown is None:
        raise RuntimeError("OCR gagal; lihat log untuk penyebabnya")
    ```

5. Jika dokumenmu berisi gambar dan flowchart, ganti prompt dengan `OCR_VLM_FLOW_DESCRIPTION_PROMPT`. Prompt ini meminta model menulis Markdown, mendeskripsikan setiap gambar dalam Bahasa Indonesia, menjelaskan flowchart langkah demi langkah, dan menulis rumus dalam LaTeX:

    ```python
    from zul.utilities.Prompts.ocr import OCR_VLM_FLOW_DESCRIPTION_PROMPT

    markdown = process_pdf_with_gemini(
        client=client,
        pdf_path="sop.pdf",
        prompt=OCR_VLM_FLOW_DESCRIPTION_PROMPT,
        logger=logger,
    )
    ```

## Memeriksa hasilnya

Untuk memastikan konversi menghasilkan teks, cetak tipe dan sebagian isinya:

```python
print(type(markdown).__name__, len(markdown) > 0)
print(markdown[:200])
```

Jika berhasil, baris pertama mencetak tipe `str` dan `True`:

```text
str True
```

Baris kedua mencetak 200 karakter pertama dokumenmu. Untuk menyimpan hasilnya ke file, pakai `save_text_to_md` di [Memakai helper kecil](memakai-helper.md).

## Halaman terkait

- [Referensi OCR](../referensi/ocr.md) untuk semua parameter `DoclingVLMConverter`, pilihan `response_format`, dan fungsi Gemini.
- [Memakai helper kecil](memakai-helper.md) untuk `PDFProcessor`, yang membaca PDF berteks tanpa memanggil model.
- [Menyimpan dan mencari vektor di Milvus](memakai-milvus.md) untuk menyimpan hasil konversi sebagai vektor.
