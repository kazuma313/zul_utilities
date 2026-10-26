# Petunjuk untuk code assistant

Berkas ini dibaca oleh code assistant yang bekerja di repository Zul. Aturan lengkapnya ada di `docs/panduan/berkontribusi.md`, dan MCP server Zul (`.mcp.json`) menyajikannya lewat tool `conventions`. Jika pemilik repository meminta sesuatu yang bertentangan dengan berkas ini, ikuti permintaan pemilik dan sebutkan pertentangannya.

## Sebelum menulis kode

1. Panggil `conventions`, lalu `list_modules`. Pakai fungsi yang sudah ada sebelum menulis yang baru.
2. Baca satu modul yang mirip dengan `read_source`, dan cocokkan gayanya.
3. Kerjakan hanya yang diminta. Jangan menambah dependency, file, parameter yang tidak dipakai, abstraksi, atau fallback "jaga-jaga".

## Aturan keras

- Library pihak ketiga hanya diimpor di `framework/src/zul/adapters/`, satu file per library. `framework/tests/test_architecture.py` menjaganya.
- Jangan menambah dependency berlisensi AGPL atau GPL. Periksa lisensi sebelum menambah dependency baru.
- Modul adalah fungsi kecil yang berlaku umum. Jangan membuat kelas atau panduan untuk satu kasus penggunaan.
- Jangan menaruh API key, token, atau alamat server pribadi di kode, notebook, dokumentasi, atau pesan commit.
- Jangan meng-commit video, frame CCTV, bobot model, `outputs/`, atau file besar.
- Jangan mengubah `research/`, `.github/`, atau `uv.lock` dengan tangan, kecuali pemilik repository memintanya.
- Jangan menghapus, melewati, atau melonggarkan test supaya lulus. Perbaiki penyebabnya.
- Jangan menjalankan `uv sync` tanpa `--inexact`.
- Dokumentasi harus dicocokkan dengan kode lebih dulu. Jangan menulis nama fungsi atau parameter yang belum kamu periksa.

## Setelah menulis kode

Jalankan semuanya, lalu laporkan perintah dan hasil aslinya. Jangan mengaku lulus jika belum menjalankannya:

```shell
uv run pytest
uv run black framework docs/tools
uv run ruff check framework docs/tools
uv run python framework/scripts/comment_style.py
uv run mkdocs build --strict
```

Untuk setiap file Python baru, panggil juga tool `check_code`.

## Pull request

- Satu tujuan per pull request, dan usahakan di bawah 400 baris berubah di luar test dan dokumentasi.
- Sebut di deskripsi bahwa assistant dipakai, bagian mana yang dibantu, dan apa yang diperiksa manusia.
- Isi templat di `.github/pull_request_template.md`.
