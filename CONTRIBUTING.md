# Berkontribusi ke Zul

Terima kasih sudah mau membantu. Issue dan pull request berbahasa Indonesia atau Inggris sama-sama diterima.

*Issues and pull requests in Indonesian or English are both welcome.*

Panduan lengkapnya, termasuk aturan menulis komentar dan dokumentasi, ada di [Berkontribusi](https://zulkit.my.id/panduan/berkontribusi/). Halaman ini merangkum langkah yang paling sering dipakai.

## Menyiapkan lingkungan

Dari root repository:

```bash
uv sync --inexact
```

Jangan memakai `uv sync` tanpa `--inexact`. Library skill pool yang tidak tercatat di `uv.lock` akan ikut terhapus.

## Mengirim perubahan

1. Buat branch dari `main`, misalnya `git checkout -b feature/nama-fitur`.
2. Kerjakan perubahannya. Setiap perbaikan bug disertai test yang gagal sebelum perbaikan.
3. Jalankan test dan pemeriksa gaya kode di bawah.
4. Perbarui dokumentasi yang terkait di `docs/`, lalu jalankan `uv run mkdocs build --strict`.
5. Push branch-mu dan buka pull request ke `main`. Jelaskan apa yang berubah, kenapa, dan cara mengujinya.

## Test dan gaya kode

```bash
uv run pytest
uv run black framework docs/tools
uv run ruff check framework docs/tools
uv run python framework/scripts/comment_style.py
```

`uv run pytest` menguji paket `zul` di `framework/tests/`. Kategori lain punya perintahnya sendiri, dan daftarnya ada di [README](README.md#pengembangan).

## Dua aturan yang tidak boleh dilanggar

- **Library pihak ketiga hanya diimpor di `framework/src/zul/adapters/`**, satu file per library. Test arsitektur akan gagal kalau aturan ini dilanggar.
- **Lisensi harus MIT-compatible.** Jangan menambahkan dependency dengan lisensi AGPL.

## Melaporkan masalah

Buka [issue](https://github.com/kazuma313/zul_utilities/issues) dengan langkah untuk mengulang masalahnya, hasil yang diharapkan, dan hasil yang kamu dapat. Untuk masalah keamanan, jangan membuka issue publik; kirim email ke [kurniazuldam@gmail.com](mailto:kurniazuldam@gmail.com).
