# Format tulisan blog

Blog di situs ini dibangun oleh plugin blog bawaan [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/plugins/blog/). Langkah menulis tulisan ada di [Menulis tulisan blog](../panduan/menulis-blog.md).

## Lokasi file

Semua file blog ada di `docs/blog/`:

| Path | Isi | Ikut terbit |
|---|---|---|
| `docs/blog/index.md` | Pengantar di atas daftar tulisan. | Ya, sebagai halaman `blog/`. |
| `docs/blog/posts/` | Satu file Markdown untuk setiap tulisan. Nama file tidak memengaruhi alamat halaman. | Ya, kecuali draf. |
| `docs/blog/resources/` | Gambar dan file pendukung, satu subfolder untuk setiap tulisan. | Ya, disalin apa adanya ke `blog/resources/`. |
| `docs/blog/_template.md` | Template yang dipakai `scripts/new_post.py`. | Tidak. Dikecualikan lewat `exclude_docs` di `mkdocs.yml`. |
| `docs/blog/.authors.yml` | Data penulis. | Tidak. Dibaca plugin saat build. |

## Header tulisan

Setiap tulisan diawali header YAML di antara dua baris `---`. Judul tulisan adalah heading `#` pertama di bawah header.

```yaml title="docs/blog/posts/2026-10-07-contoh.md"
---
date:
  created: 2026-10-07
  updated: 2026-10-20
categories:
  - RAG
authors:
  - kurnia
draft: true
---

# Judul tulisan
```

Kunci yang dikenali plugin:

| Kunci | Wajib | Nilai | Keterangan |
|---|---|---|---|
| `date.created` | Ya | Tanggal `YYYY-MM-DD`, atau tanggal dan jam | Menentukan urutan tulisan, bulan arsipnya, dan alamat halamannya. Tanpa kunci ini build gagal. |
| `date.updated` | Tidak | Tanggal `YYYY-MM-DD` | Tampil di halaman tulisan sebagai tanggal pembaruan. |
| `categories` | Tidak | Daftar teks | Setiap kategori mendapat halaman sendiri. Nama kategori bebas. |
| `authors` | Tidak | Daftar kunci dari `.authors.yml` | Kunci yang tidak ada di `.authors.yml` menggagalkan build. |
| `draft` | Tidak | `true` atau `false` | `true`: tulisan tampil di `mkdocs serve` dengan label **Draf**, tetapi tidak ikut `mkdocs build`. |
| `pin` | Tidak | `true` atau `false`; bawaan `false` | `true`: tulisan selalu berada di urutan teratas daftar. |
| `slug` | Tidak | Teks | Bagian akhir alamat halaman. Bawaannya dibentuk dari judul: huruf kecil, kata dipisah tanda hubung. |
| `readtime` | Tidak | Bilangan bulat | Menit baca yang ditampilkan, menggantikan perkiraan otomatis. |
| `links` | Tidak | Daftar path halaman atau pasangan `Judul: URL` | Tampil di bagian **Tautan yang berhubungan** pada halaman tulisan. Path halaman ditulis relatif terhadap folder `docs/`. |

Contoh `links` dengan satu halaman situs dan satu tautan luar:

```yaml
links:
  - panduan/menulis-blog.md
  - Contextual Retrieval: https://www.anthropic.com/engineering/contextual-retrieval
```

## Ringkasan tulisan

Baris `<!-- more -->` memisahkan ringkasan dari isi tulisan. Teks di atas baris itu tampil di halaman daftar tulisan, diikuti tautan **Lanjut membaca**. Setiap tulisan wajib punya baris ini, karena `post_excerpt` diatur ke `required`.

## Gambar dan file

File di `docs/blog/resources/` dipanggil dari tulisan dengan path relatif terhadap file tulisan:

```markdown
![Keterangan gambar](../resources/2026-10-07-contoh/gambar.png)
[Unduh contoh kode](../resources/2026-10-07-contoh/contoh.py)
```

Akhiran `#only-light` atau `#only-dark` pada path gambar membuat gambar itu hanya tampil di mode terang atau mode gelap:

```markdown
![Grafik](../resources/2026-10-07-contoh/grafik-terang.svg#only-light)
![Grafik](../resources/2026-10-07-contoh/grafik-gelap.svg#only-dark)
```

PDF di folder resources ikut terbit. Hanya PDF di root `docs/` yang dikecualikan.

## Diagram dan HTML

Blok kode berbahasa `mermaid` digambar sebagai diagram oleh [Mermaid](https://mermaid.js.org) di browser pembaca. Pengaturannya ada di `pymdownx.superfences` pada `mkdocs.yml`. Warna diagram mengikuti mode terang atau gelap untuk jenis berikut:

| Jenis | Baris pertama blok |
|---|---|
| Flowchart | `flowchart LR` atau `flowchart TB` |
| Sequence diagram | `sequenceDiagram` |
| State diagram | `stateDiagram-v2` |
| Class diagram | `classDiagram` |
| Entity-relationship diagram | `erDiagram` |

Jenis lain, misalnya `pie` atau `gantt`, tetap tergambar dengan warna bawaan Mermaid.

Blok kode di dalam komentar HTML (`<!-- ... -->`) tetap diproses dan ditampilkan. Contoh diagram hanya hilang dari halaman jika blok kodenya dihapus.

Tulisan juga boleh memuat HTML. Contohnya, video YouTube disematkan dengan `<iframe>` ke alamat `https://www.youtube-nocookie.com/embed/ID_VIDEO`, dengan gaya `width: 100%; aspect-ratio: 16 / 9` supaya lebarnya mengikuti kolom.

## Alamat halaman

Plugin membuat halaman-halaman berikut. Alamatnya relatif terhadap alamat situs, `https://zulkit.my.id/`:

| Halaman | Alamat | Contoh |
|---|---|---|
| Daftar tulisan | `blog/` | `blog/` |
| Halaman daftar berikutnya | `blog/page/NOMOR/` | `blog/page/2/` |
| Tulisan | `blog/TAHUN/BULAN/TANGGAL/SLUG/` | `blog/2026/10/07/memilih-model-lokal-untuk-menulis-konteks-chunk/` |
| Arsip satu bulan | `blog/archive/TAHUN/BULAN/` | `blog/archive/2026/10/` |
| Kategori | `blog/category/SLUG_KATEGORI/` | `blog/category/model-lokal/` |

Tanggal di alamat tulisan diambil dari `date.created`. `SLUG` adalah nilai `slug`, atau dibentuk dari judul jika `slug` tidak diisi.

## Pengaturan plugin

Plugin diatur di bagian `plugins` pada `mkdocs.yml`:

| Pengaturan | Nilai | Akibatnya |
|---|---|---|
| `blog_dir` | `blog` | Blog ada di `docs/blog/` dan terbit di `blog/`. |
| `blog_toc` | `true` | Halaman daftar tulisan punya daftar isi berisi judul tulisan. |
| `post_date_format` | `long` | Tanggal tampil lengkap dalam bahasa situs, misalnya "7 Oktober 2026". |
| `post_url_format` | `"{date}/{slug}"` | Alamat tulisan diawali tanggalnya. |
| `post_excerpt` | `required` | Tulisan tanpa `<!-- more -->` menggagalkan build. |
| `post_readtime` | `true` | Menit baca diperkirakan dari jumlah kata, 265 kata per menit. |
| `archive_date_format` | `MMMM yyyy` | Arsip dikelompokkan per bulan, misalnya "Oktober 2026". |
| `archive_url_date_format` | `yyyy/MM` | Alamat arsip berbentuk `blog/archive/2026/10/`. |
| `pagination_per_page` | `10` | Satu halaman daftar memuat 10 tulisan. |

Pengaturan lain memakai nilai bawaan plugin. Yang memengaruhi penulisan:

| Pengaturan | Nilai bawaan | Akibatnya |
|---|---|---|
| `draft_on_serve` | `true` | Draf tampil di `mkdocs serve`. |
| `draft_if_future_date` | `false` | Tulisan bertanggal di masa depan tetap terbit. |
| `categories_allowed` | Kosong | Nama kategori apa pun diterima. |

Label seperti "Arsip", "Kategori", "Lanjut membaca", dan "menit baca" mengikuti `theme.language: id`.

## Data penulis

`docs/blog/.authors.yml` memetakan kunci penulis ke datanya:

```yaml title="docs/blog/.authors.yml"
authors:
  kurnia:
    name: Kurnia Zulda Matondang
    description: Penulis Zul
    avatar: https://github.com/kazuma313.png
    url: https://github.com/kazuma313
```

| Kunci | Keterangan |
|---|---|
| `name` | Nama yang tampil di tulisan. |
| `description` | Keterangan singkat di bawah nama. |
| `avatar` | URL atau path gambar foto penulis. |
| `url` | Tautan pada nama penulis. |

## `scripts/new_post.py`

Membuat file tulisan dari `docs/blog/_template.md` dan folder resources-nya:

```shell
uv run python scripts/new_post.py JUDUL [--tanggal TANGGAL] [--kategori KATEGORI]...
```

| Argumen | Wajib | Bawaan | Keterangan |
|---|---|---|---|
| `JUDUL` | Ya | Tidak ada | Judul tulisan. Juga dipakai untuk nama file. |
| `--tanggal` | Tidak | Hari ini | Tanggal tulisan, berformat `YYYY-MM-DD`. |
| `--kategori` | Tidak | `Catatan` | Kategori tulisan. Ulangi untuk lebih dari satu kategori. |

Skrip menulis dua hal, dengan `NAMA` berbentuk `TANGGAL-SLUG`:

| Hasil | Path |
|---|---|
| File tulisan | `docs/blog/posts/NAMA.md` |
| Folder resources, kosong | `docs/blog/resources/NAMA/` |

`SLUG` dibentuk dari judul: aksen dihapus, huruf kecil, setiap deret karakter selain huruf dan angka diganti satu tanda hubung, paling panjang 60 karakter. Judul "RAG: hasil & catatan!" menghasilkan `rag-hasil-catatan`. Git tidak menyimpan folder kosong, jadi folder resources baru ikut di-commit setelah berisi file.

Skrip mengganti penanda berikut di template:

| Penanda | Diganti dengan |
|---|---|
| `{{tanggal}}` | Tanggal tulisan, `YYYY-MM-DD`. |
| `{{judul}}` | Judul tulisan. |
| `{{kategori}}` | Daftar kategori YAML, setiap nama dalam tanda kutip. |
| `{{folder}}` | `NAMA`, untuk path di contoh pemanggilan gambar. |

Kode keluar skrip:

| Kode | Arti |
|---|---|
| `0` | Tulisan dan foldernya dibuat. |
| `1` | Judul tidak memuat huruf atau angka, atau tulisan dengan tanggal dan judul yang sama sudah ada. File yang ada tidak ditimpa. |
| `2` | Argumen salah, misalnya `--tanggal` bukan `YYYY-MM-DD`. |

## Error yang menggagalkan build

Dengan `mkdocs build --strict`, kesalahan berikut menghentikan build dan penerbitan. `FILE` adalah path tulisan yang bermasalah:

| Penyebab | Pesan |
|---|---|
| Tidak ada `date.created` | `Error reading metadata 'date' of post 'FILE'` |
| Tidak ada `<!-- more -->` | `Couldn't find '<!-- more -->' in post 'FILE'` |
| Kunci di `authors` tidak ada di `.authors.yml` | `Couldn't find author 'KUNCI'` |
| Tautan ke file yang tidak ada | `Doc file 'FILE' contains a link 'PATH', but the target '...' is not found among documentation files.` |

## Halaman terkait

- [Menulis tulisan blog](../panduan/menulis-blog.md) untuk langkah membuat dan menerbitkan tulisan.
- [Workflow dokumentasi](workflow-dokumentasi.md) untuk pemeriksaan yang dijalankan sebelum situs terbit.
