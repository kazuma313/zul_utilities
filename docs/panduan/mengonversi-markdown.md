# Mengubah Markdown menjadi PDF dan PPTX

Halaman ini menunjukkan cara mengubah teks Markdown, misalnya jawaban LLM, menjadi file PDF atau presentasi PowerPoint. Hasilnya bisa ditulis ke file atau diambil sebagai bytes untuk langsung diunduh lewat API.

**Sebelum mulai:** kamu butuh Zul yang sudah terpasang (lihat [Memasang Zul](memasang-zul.md)). Kedua converter di halaman ini memakai extra `converter`, yang dipasang di langkah pertama.

## Mengubah Markdown menjadi PDF

1. Pasang Zul dengan extra `converter`:

    ```shell
    pip install "zul[converter] @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

2. Siapkan teks Markdown. Heading, daftar, tabel, kode, teks tebal, dan teks miring didukung:

    ```python
    markdown = """
    # Laporan Mingguan

    ## Ringkasan

    Penjualan naik **12%** dibanding minggu lalu.

    | Produk | Terjual |
    |--------|---------|
    | A      | 120     |
    | B      | 85      |
    """
    ```

    Tulis isi Markdown mulai dari tepi kiri, tanpa indentasi tambahan, supaya heading dan tabel dikenali.

3. Buat converter, lalu tulis PDF ke sebuah folder:

    ```python
    from zul.utilities.markdown_converter.md_to_pdf import MarkdownToPDFConverter

    converter = MarkdownToPDFConverter(page_size="A4", margin="2cm")
    succeeded = converter.convert(markdown, output_path="output", filename="laporan.pdf")
    ```

    `convert` membuat folder `output` jika belum ada dan menulis `output/laporan.pdf`.

4. Periksa nilai kembaliannya. `convert` mengembalikan `True` jika berhasil. Jika gagal, method ini mencetak penyebabnya dan mengembalikan `False`, tanpa melempar exception:

    ```python
    if not succeeded:
        raise RuntimeError("PDF gagal dibuat")
    ```

## Mengubah tampilan PDF

Stylesheet bawaan memakai aksen oranye pada heading dan header tabel.

1. Untuk menggantinya, berikan CSS-mu sendiri ke `set_custom_styles` sebelum memanggil `convert`:

    ```python
    converter.set_custom_styles("""
    body { font-family: Georgia, serif; font-size: 11pt; }
    h1 { color: #1a365d; border-bottom: 2px solid #1a365d; }
    table th { background-color: #1a365d; color: white; }
    """)
    ```

    CSS itu menggantikan seluruh stylesheet bawaan, dan hanya berlaku untuk objek converter tersebut.

2. Jika CSS-mu perlu ukuran halaman dan margin dari converter, tulis sebagai template: gandakan setiap kurung kurawal, lalu pakai `{page_size}` dan `{margin}`:

    ```python
    converter.set_custom_styles(
        "@page {{ size: {page_size}; margin: {margin}; }} body {{ font-size: 10pt; }}"
    )
    ```

## Mengubah Markdown menjadi PPTX

1. Tulis Markdown dengan baris `---` sebagai pemisah slide. Setiap bagian menjadi satu slide:

    ```python
    markdown = """# Laporan Kuartal 3

    ---

    ## Ringkasan
    * Pendapatan naik 12%
      * Terutama dari produk A
    * Biaya turun 3%

    ---

    ## Penjualan per Produk
    | Produk | Terjual |
    |--------|---------|
    | A      | 120     |
    | B      | 85      |
    """
    ```

    Indentasi dua spasi di depan bullet menurunkannya satu level, jadi tulis bullet tingkat teratas mulai dari tepi kiri.

2. Buat service, lalu konversi ke file:

    ```python
    from zul.utilities.markdown_converter.md_to_ppt import DynamicMarkdownToPPTXService

    service = DynamicMarkdownToPPTXService()
    service.convert_markdown(markdown, "laporan.pptx")
    ```

    Contoh ini menghasilkan tiga slide berukuran 16:9. Cara setiap elemen Markdown diubah menjadi isi slide ada di [Referensi Markdown converter](../referensi/markdown-converter.md).

> [!NOTE]
> Pemisah slide harus berupa baris `---` yang berdiri sendiri, dengan baris baru sebelum dan sesudahnya.

## Memakai template PowerPoint

1. Untuk memakai desain perusahaan, berikan file template saat membuat service. Judul dan isi mengisi placeholder pada layout slide template:

    ```python
    service = DynamicMarkdownToPPTXService(template_path="template.pptx")
    service.convert_markdown(markdown, "laporan.pptx")
    ```

    Slide baru ditambahkan setelah slide yang sudah ada di file template. Jika file template tidak ditemukan, service mencetak peringatan dan membuat slide polos.

2. Tanpa template, atur font dan warna per jenis teks lewat `style_config`:

    ```python
    from pptx.dml.color import RGBColor

    service = DynamicMarkdownToPPTXService(
        style_config={
            "h2": {"font_size": 36, "font_color": RGBColor(26, 54, 93)},
            "bullet": {"font_size": 20},
        }
    )
    ```

    Judul slide memakai gaya `h2`. Jenis teks lain yang bisa diatur ada di [Referensi Markdown converter](../referensi/markdown-converter.md).

## Mengirim file lewat API

Kedua converter punya `convert_to_bytes`, yang mengembalikan isi file tanpa menulis ke disk.

1. Panggil `convert_to_bytes` di dalam endpoint. Contoh berikut adalah aplikasi FastAPI yang mengembalikan PDF:

    ```python title="app.py"
    from fastapi import FastAPI, Response
    from pydantic import BaseModel

    from zul.utilities.markdown_converter.md_to_pdf import MarkdownToPDFConverter

    app = FastAPI()


    class ReportRequest(BaseModel):
        markdown: str


    @app.post("/reports/pdf")
    def create_pdf(request: ReportRequest) -> Response:
        pdf_bytes = MarkdownToPDFConverter().convert_to_bytes(request.markdown)
        if not pdf_bytes:
            return Response(status_code=500)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="laporan.pdf"'},
        )
    ```

    Jika konversi gagal, `convert_to_bytes` mengembalikan bytes kosong (`b""`). Karena itu endpoint memeriksanya sebelum mengirim respons.

2. Untuk PPTX, ganti converter dengan service PPTX dan sesuaikan tipe medianya:

    ```python
    pptx_bytes = DynamicMarkdownToPPTXService().convert_to_bytes(markdown)
    media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ```

> [!NOTE]
> Setiap pemanggilan `convert_to_bytes` pada service PPTX memulai presentasi baru. `convert_markdown` berbeda: method itu menambah slide ke presentasi yang sudah ada di objek service, jadi memanggilnya dua kali pada objek yang sama menggandakan slide.

## Memeriksa hasilnya

Saat PDF berhasil dibuat, `convert` mencetak lokasi file:

```text
✓ PDF berhasil disimpan di: output/laporan.pdf
✓ Absolute path: /home/kamu/proyek/output/laporan.pdf
```

Path absolut mengikuti folder kerjamu, dan di Windows pemisah foldernya adalah `\`.

Saat PPTX berhasil dibuat, `convert_markdown` mencetak nama file dan jumlah slide:

```text
✅ Presentasi berhasil dibuat (generated): laporan.pptx
   Total slides: 3
```

Buka kedua file untuk memastikan isinya sesuai.

## Lihat juga

- [Referensi Markdown converter](../referensi/markdown-converter.md) untuk semua method, sintaks slide, dan kunci gaya.
- [Menambah endpoint](menambah-endpoint.md) untuk menaruh endpoint unduhan di proyek hasil `zul build hexa`.
- [Memanggil LLM dan embedding](memanggil-llm-dan-embedding.md) untuk menghasilkan Markdown dari LLM.
