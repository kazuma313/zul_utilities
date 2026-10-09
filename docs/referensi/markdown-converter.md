# Markdown converter

Dua kelas yang mengubah teks Markdown menjadi dokumen lain: `MarkdownToPDFConverter` menghasilkan PDF, dan `DynamicMarkdownToPPTXService` menghasilkan presentasi PowerPoint (`.pptx`).

Baris berikut mengimpor keduanya:

```python
from zul.utilities.markdown_converter.md_to_pdf import MarkdownToPDFConverter
from zul.utilities.markdown_converter.md_to_ppt import DynamicMarkdownToPPTXService
```

Kedua modul membutuhkan extra `converter` (`markdown`, `xhtml2pdf`, `python-pptx`).

## `MarkdownToPDFConverter(page_size="A4", margin="2cm", markdown_extensions=None)`

Menyiapkan konversi Markdown ke PDF. Markdown diubah menjadi HTML, diberi stylesheet, lalu dicetak ke PDF dengan `xhtml2pdf`. Lokasi: `zul.utilities.markdown_converter.md_to_pdf`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `page_size` | `str` | `"A4"` | Ukuran halaman, diisikan ke aturan CSS `@page`. |
| `margin` | `str` | `"2cm"` | Margin halaman, diisikan ke aturan CSS `@page`. |
| `markdown_extensions` | `list` atau `None` | `None` | Ekstensi parser Markdown. `None` diganti `["extra", "codehilite", "tables"]`. |

**Atribut:**

| Atribut | Tipe | Keterangan |
|---|---|---|
| `page_size`, `margin`, `markdown_extensions` | sesuai parameter | Nilai yang diberikan saat objek dibuat. |
| `DEFAULT_STYLES` | `str` | Atribut kelas berisi stylesheet bawaan, berupa template dengan `{page_size}` dan `{margin}`. Stylesheet ini memakai aksen oranye pada heading dan header tabel. |

### `get_styles()`

Mengembalikan CSS yang dipakai untuk PDF.

**Mengembalikan:** `str`. Stylesheet aktif diisi dengan `page_size` dan `margin`. Jika stylesheet itu CSS biasa yang tidak bisa diperlakukan sebagai template, isinya dikembalikan apa adanya.

### `create_html_document(content)`

Membungkus potongan HTML menjadi dokumen HTML lengkap berisi stylesheet dari `get_styles()`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `content` | `str` | Wajib | Isi `<body>` dalam HTML. |

**Mengembalikan:** `str` berisi dokumen HTML.

### `markdown_to_html(markdown_content)`

Mengubah Markdown menjadi HTML dengan ekstensi di `markdown_extensions`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `markdown_content` | `str` | Wajib | Teks Markdown. |

**Mengembalikan:** `str` berisi HTML.

Contoh berikut menunjukkan hasil antara berupa HTML:

```python
html = MarkdownToPDFConverter().markdown_to_html("# Judul\n\nIsi **tebal**.")
print(html)
```

Kode itu mencetak:

```text
<h1>Judul</h1>
<p>Isi <strong>tebal</strong>.</p>
```

### `convert(markdown_content, output_path, filename="output.pdf")`

Mengubah Markdown menjadi file PDF.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `markdown_content` | `str` | Wajib | Teks Markdown. |
| `output_path` | `str` | Wajib | Folder tujuan. Dibuat jika belum ada. |
| `filename` | `str` | `"output.pdf"` | Nama file PDF di dalam folder itu. |

**Mengembalikan:** `bool`. `True` jika PDF tertulis, `False` jika gagal.

Method ini tidak melempar exception. Saat berhasil, lokasi file dicetak. Saat gagal, penyebabnya dicetak.

### `convert_to_bytes(markdown_content)`

Mengubah Markdown menjadi PDF di memori, tanpa menulis file.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `markdown_content` | `str` | Wajib | Teks Markdown. |

**Mengembalikan:** `bytes` berisi PDF, atau `b""` jika konversi gagal. Method ini tidak melempar exception. Penyebab kegagalan dicetak.

### `convert_from_response(response, output_path, filename="output.pdf")`

Mengambil Markdown dari sebuah objek respons, lalu memanggil `convert`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `response` | objek dengan method `.json()` | Wajib | Respons API. Nilai `response.json()` harus berupa teks Markdown. |
| `output_path` | `str` | Wajib | Folder tujuan. |
| `filename` | `str` | `"output.pdf"` | Nama file PDF. |

**Mengembalikan:** `bool`. `False` jika `response.json()` gagal atau konversi gagal.

### `set_custom_styles(custom_styles)`

Mengganti stylesheet objek converter ini.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `custom_styles` | `str` | Wajib | CSS biasa, atau template seperti `DEFAULT_STYLES`: kurung kurawal digandakan dan `{page_size}` serta `{margin}` dipakai sebagai placeholder. |

**Mengembalikan:** `None`. CSS ini menggantikan seluruh stylesheet bawaan.

## Konstanta dan fungsi `md_to_ppt`

Lokasi: `zul.utilities.markdown_converter.md_to_ppt`.

| Nama | Nilai | Keterangan |
|---|---|---|
| `SLIDE_SEPARATOR` | `"\n---\n"` | Pemisah slide: baris `---` yang diapit baris baru. |
| `SLIDE_WIDTH_INCHES` | `10` | Lebar slide tanpa template, dalam inci. |
| `SLIDE_HEIGHT_INCHES` | `5.625` | Tinggi slide tanpa template, dalam inci. Bersama lebarnya menghasilkan rasio 16:9. |
| `MAX_BULLET_LEVEL` | `2` | Level bullet terdalam. Bullet punya tiga level, 0 sampai 2. |
| `SPACES_PER_BULLET_LEVEL` | `2` | Jumlah spasi indentasi per level bullet. |

### `strip_inline_markdown(text)`

Menghapus penanda `**tebal**` dan `*miring*` dari sebuah teks, karena PowerPoint menampilkannya sebagai tanda bintang.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `text` | `str` | Wajib | Teks berisi penanda Markdown. |

**Mengembalikan:** `str` tanpa penanda itu.

## Sintaks slide

Tabel berikut menunjukkan cara `convert_markdown` dan `convert_to_bytes` membaca setiap baris Markdown:

| Markdown | Menjadi |
|---|---|
| Baris `---` yang berdiri sendiri | Pemisah slide. Bagian yang kosong dilewati. |
| `# Judul` | Judul slide. |
| `## Judul` | Judul slide jika slide belum punya judul. Selain itu sub-judul. |
| `### Judul`, `#### Judul` | Sub-judul di dalam slide, dengan gaya `h3` atau `h4`. |
| `* teks` atau `- teks` | Bullet. Levelnya dihitung dari indentasi: dua spasi per level. |
| `** teks`, `*** teks` | Bullet level 1 dan level 2. |
| Baris tabel Markdown, yaitu baris yang diawali garis tegak dan memuat garis tegak lain | Tabel di slide. Jika satu slide memuat beberapa tabel, tabel terakhir yang dipakai. |
| `![alt](gambar.png)` di awal baris | Gambar dari file lokal. File yang tidak ada dilewati dengan peringatan. |
| Heading dengan lima `#` atau lebih | Dilewati. |
| Baris lain | Teks biasa. |

Indentasi yang lebih dalam dari level 2 diperlakukan sebagai level 2. Penanda tebal dan miring di dalam bullet dan sel tabel dihapus. Di sel tabel, `<br>` dan `<br/>` diubah menjadi baris baru.

## `DynamicMarkdownToPPTXService(template_path=None, style_config=None)`

Menyiapkan presentasi untuk diisi dari Markdown atau dari pemanggilan method.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `template_path` | `str` atau `None` | `None` | Path ke file template `.pptx`. Jika `None` atau file tidak ada, presentasi kosong berukuran 16:9 dibuat. |
| `style_config` | `dict` atau `None` | `None` | Gaya yang menimpa gaya bawaan. Rinciannya ada di [Kunci gaya](#kunci-gaya). |

Saat dibuat, service mencetak mode yang dipakai: memakai template atau membuat dari awal. Jika `template_path` diisi tetapi filenya tidak ada, peringatan ikut dicetak.

**Atribut:**

| Atribut | Tipe | Keterangan |
|---|---|---|
| `template_path` | `str` atau `None` | Nilai yang diberikan saat objek dibuat. |
| `use_template` | `bool` | `True` jika `template_path` diisi dan filenya ada. |
| `prs` | `pptx.Presentation` | Presentasi yang sedang diisi. Dengan template, presentasi ini memuat slide yang sudah ada di file template. |
| `style_config` | `dict` | Gaya aktif. |

### Kunci gaya

`style_config` adalah `dict` dari jenis teks ke pengaturan gayanya. Tabel berikut mencantumkan jenis teks dan nilai bawaannya, semuanya dengan font `Calibri`:

| Jenis | Dipakai untuk | `font_size` | `font_color` | `bold` |
|---|---|---|---|---|
| `h1` | Tidak dipakai konversi Markdown. Tersedia lewat `apply_text_style` dan `add_styled_textbox`. | `44` | `RGBColor(0, 51, 102)` | `True` |
| `h2` | Judul slide. | `32` | `RGBColor(230, 126, 34)` | `True` |
| `h3` | Sub-judul dari `###`. | `24` | `RGBColor(52, 73, 94)` | `True` |
| `h4` | Sub-judul dari `####`. | `20` | `RGBColor(52, 73, 94)` | `True` |
| `body` | Teks biasa. | `18` | `RGBColor(60, 60, 60)` | `False` |
| `bullet` | Bullet. | `18` | `RGBColor(60, 60, 60)` | `False` |

Setiap jenis di atas menerima kunci `font_size`, `font_name`, `font_color`, `bold`, dan `italic`. Nilai bawaan `italic` adalah `False`.

Jenis `table` punya kunci sendiri:

| Kunci | Default | Keterangan |
|---|---|---|
| `font_size` | `12` | Ukuran font sel. |
| `font_name` | `"Calibri"` | Nama font sel. |
| `header_color` | `RGBColor(0, 51, 102)` | Warna teks baris header. |
| `cell_color` | `RGBColor(60, 60, 60)` | Warna teks sel lain. |
| `bold_header` | `True` | Jika `True`, teks baris header ditebalkan. |

Setiap warna, yaitu `font_color`, `header_color`, dan `cell_color`, boleh berupa tuple RGB seperti `(26, 54, 93)`, string `"#1A365D"`, atau `RGBColor` dari python-pptx. Nilai lain melempar `ValueError`. Nilai bawaannya tetap `RGBColor`.

Gaya yang kamu berikan digabung per jenis: kunci yang tidak disebut tetap memakai nilai bawaan.

### `get_default_style()`

Mengembalikan gaya bawaan untuk semua jenis teks.

**Mengembalikan:** `dict` dengan kunci `h1`, `h2`, `h3`, `h4`, `body`, `bullet`, dan `table`.

### `set_style(style_dict)`

Menggabungkan gaya baru ke gaya aktif setelah service dibuat, lalu mencetak jenis teks yang diubah.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `style_dict` | `dict` | Wajib | Bentuknya sama dengan `style_config`. |

Contoh berikut memperbesar judul slide:

```python
service.set_style({"h2": {"font_size": 40}})
```

### `apply_text_style(paragraph, style_type="body")`

Menerapkan gaya sebuah jenis teks ke satu paragraf `python-pptx`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `paragraph` | paragraf `python-pptx` | Wajib | Paragraf yang diberi gaya. |
| `style_type` | `str` | `"body"` | Jenis teks. Jenis yang tidak dikenal memakai gaya `body`. |

### `enable_bullet(paragraph, level=0)`

Menjadikan sebuah paragraf sebagai bullet pada level tertentu.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `paragraph` | paragraf `python-pptx` | Wajib | Paragraf yang dijadikan bullet. |
| `level` | `int` | `0` | Level bullet. |

### `create_blank_slide()`

Menambah satu slide kosong ke presentasi. Tanpa template, semua shape bawaan dihapus dan latar diberi warna putih.

**Mengembalikan:** objek slide `python-pptx`.

### `add_styled_textbox(slide, text, left, top, width, height, style_type="body")`

Menambah kotak teks berisi satu paragraf rata kiri dengan gaya tertentu.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `slide` | slide `python-pptx` | Wajib | Slide tujuan. |
| `text` | `str` | Wajib | Isi kotak teks. |
| `left`, `top`, `width`, `height` | angka | Wajib | Posisi dan ukuran dalam inci. |
| `style_type` | `str` | `"body"` | Jenis teks untuk gaya. |

**Mengembalikan:** shape kotak teks.

### `add_content_textbox(slide, content_items, left, top, width)`

Menambah kotak teks berisi campuran sub-judul, bullet, dan teks biasa.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `slide` | slide `python-pptx` | Wajib | Slide tujuan. |
| `content_items` | `list[dict]` | Wajib | Daftar item. Setiap item punya `text`, serta `type` (`section`, `bullet`, atau lainnya untuk teks biasa; bawaan `bullet`), `level` untuk bullet, dan `header_level` (`3` atau `4`) untuk `section`. |
| `left`, `top`, `width` | angka | Wajib | Posisi dan lebar dalam inci. |

**Mengembalikan:** tinggi kotak teks dalam inci, diperkirakan dari jumlah item.

### `add_bullet_textbox(slide, bullets, left, top, width, style_type="bullet")`

Menambah kotak teks berisi daftar bullet level 0.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `slide` | slide `python-pptx` | Wajib | Slide tujuan. |
| `bullets` | `list[str]` | Wajib | Teks setiap bullet. |
| `left`, `top`, `width` | angka | Wajib | Posisi dan lebar dalam inci. |
| `style_type` | `str` | `"bullet"` | Jenis teks untuk gaya. |

**Mengembalikan:** tinggi kotak teks dalam inci, diperkirakan dari jumlah bullet.

### `parse_markdown_table(table_text)`

Mengubah teks tabel Markdown menjadi daftar baris.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `table_text` | `str` | Wajib | Tabel Markdown, satu baris tabel per baris teks. |

**Mengembalikan:** `list[list[str]]` dengan baris header di urutan pertama, atau `None` jika teks berisi kurang dari dua baris. Baris yang memuat `---` dianggap baris pemisah dan dilewati.

### `add_table(slide, table_data, left=0.5, top=1.5, width=9, height=None)`

Menambah tabel ke slide. Baris pertama diperlakukan sebagai header.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `slide` | slide `python-pptx` | Wajib | Slide tujuan. |
| `table_data` | `list[list]` | Wajib | Baris tabel. Jumlah kolom mengikuti baris pertama. |
| `left`, `top` | angka | `0.5`, `1.5` | Posisi dalam inci. |
| `width` | angka | `9` | Lebar tabel dalam inci. |
| `height` | angka atau `None` | `None` | Tinggi tabel dalam inci. `None` berarti 0,4 inci per baris. |

**Mengembalikan:** shape tabel, atau `None` jika `table_data` kosong.

### `add_image(slide, image_path, left=1.5, top=3, width=7, height=None)`

Menambah gambar dari file lokal ke slide.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `slide` | slide `python-pptx` | Wajib | Slide tujuan. |
| `image_path` | `str` | Wajib | Path ke file gambar. |
| `left`, `top` | angka | `1.5`, `3` | Posisi dalam inci. |
| `width` | angka | `7` | Lebar gambar dalam inci. |
| `height` | angka atau `None` | `None` | Tinggi gambar dalam inci. `None` berarti mengikuti rasio gambar. |

**Mengembalikan:** shape gambar, atau `None` jika file tidak ada atau gambar gagal ditambahkan. Penyebabnya dicetak.

### `fill_template_placeholder(slide, title=None, content=None)`

Mengisi placeholder judul dan isi pada slide yang dibuat dari layout template.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `slide` | slide `python-pptx` | Wajib | Slide dari layout template. |
| `title` | `str` atau `None` | `None` | Teks untuk placeholder judul, diberi gaya `h2`. |
| `content` | `str`, `list`, atau `None` | `None` | Isi untuk placeholder isi. Daftar teks menjadi bullet. Daftar dict mengikuti bentuk `content_items`. Teks tunggal menjadi satu paragraf bergaya `body`. |

### `add_slide_from_content(title=None, content=None, image_paths=None, table_data=None, layout_index=1)`

Menambah satu slide tanpa lewat Markdown.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `title` | `str` atau `None` | `None` | Judul slide. |
| `content` | `str`, `list[str]`, `list[dict]`, atau `None` | `None` | Isi slide: teks, daftar bullet, atau daftar item seperti `content_items`. |
| `image_paths` | `str`, `list[str]`, atau `None` | `None` | Satu path gambar atau daftar path. |
| `table_data` | `list[list]` atau `None` | `None` | Baris tabel, header di urutan pertama. |
| `layout_index` | `int` | `1` | Nomor layout template yang dipakai. Hanya berlaku dengan template. Jika nomor itu tidak ada, layout nomor 1 dipakai. |

**Mengembalikan:** objek slide `python-pptx`.

Tanpa template, judul, isi, tabel, dan gambar disusun dari atas ke bawah. Dengan template, judul dan isi mengisi placeholder layout, tabel ditaruh 1,5 inci dari atas, dan gambar 3 inci dari atas.

Contoh berikut menambah satu slide berisi bullet dan tabel, lalu menyimpannya:

```python
service = DynamicMarkdownToPPTXService()
service.add_slide_from_content(
    title="Ringkasan",
    content=["Pendapatan naik 12%", "Biaya turun 3%"],
    table_data=[["Produk", "Terjual"], ["A", "120"]],
)
service.save("ringkasan.pptx")
```

### `convert_markdown(md_content, output_path)`

Menambah satu slide untuk setiap bagian Markdown yang dipisahkan `SLIDE_SEPARATOR`, lalu menyimpan presentasi ke file dan mencetak jumlah slide.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `md_content` | `str` | Wajib | Teks Markdown. Rinciannya ada di [Sintaks slide](#sintaks-slide). |
| `output_path` | `str` | Wajib | Path file `.pptx` tujuan. |

**Mengembalikan:** `None`.

Slide ditambahkan ke presentasi yang sudah ada di objek service. Memanggil method ini dua kali pada objek yang sama menghasilkan file kedua yang memuat slide dari kedua pemanggilan.

### `convert_to_bytes(markdown_content)`

Mengubah Markdown menjadi PPTX di memori. Setiap pemanggilan memulai presentasi baru.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `markdown_content` | `str` | Wajib | Teks Markdown. |

**Mengembalikan:** `bytes` berisi file PPTX, atau `b""` jika konversi gagal. Method ini tidak melempar exception. Penyebab kegagalan dicetak.

### `get_bytes()`

Mengembalikan presentasi yang sedang diisi sebagai bytes, tanpa konversi Markdown.

**Mengembalikan:** `bytes` berisi file PPTX, atau `b""` jika gagal.

### `save(output_path)`

Menyimpan presentasi yang sedang diisi ke file dan mencetak lokasinya.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `output_path` | `str` | Wajib | Path file `.pptx` tujuan. |

**Mengembalikan:** `None`.

## Path impor lama

Dua modul lama tetap bisa dipakai dan meneruskan ke lokasi sekarang:

| Path lama | Lokasi sekarang | Yang bisa diimpor |
|---|---|---|
| `zul.utilities.md_to_pdf` | `zul.utilities.markdown_converter.md_to_pdf` | `MarkdownToPDFConverter` |
| `zul.utilities.md_to_ppt` | `zul.utilities.markdown_converter.md_to_ppt` | `DynamicMarkdownToPPTXService` |

## Halaman terkait

- [Mengubah Markdown menjadi PDF dan PPTX](../panduan/mengonversi-markdown.md) untuk langkah pemakaian.
- [Helper kecil](helper.md) untuk `save_text_to_md`, yang menyimpan Markdown ke file.
