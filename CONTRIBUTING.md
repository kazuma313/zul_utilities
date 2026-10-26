# Berkontribusi ke Zul

Terima kasih sudah mau membantu. Issue dan pull request berbahasa Indonesia atau Inggris sama-sama diterima.

*Issues and pull requests in Indonesian or English are both welcome.*

Panduan lengkapnya, termasuk aturan menulis komentar dan dokumentasi, ada di [Berkontribusi](https://zulkit.my.id/panduan/berkontribusi/). Halaman ini merangkum yang paling sering dipakai.

## Menyiapkan lingkungan

Dari root repository:

```bash
uv sync --inexact
```

Jangan memakai `uv sync` tanpa `--inexact`. Library skill pool yang tidak tercatat di `uv.lock` akan ikut terhapus.

## Mengirim perubahan

1. Buat branch dari `main`, misalnya `git checkout -b feature/nama-fitur`.
2. Kerjakan satu tujuan saja. Setiap perbaikan bug disertai test yang gagal sebelum perbaikan.
3. Jalankan test dan pemeriksa gaya kode di bawah.
4. Perbarui dokumentasi yang terkait di `docs/`, lalu jalankan `uv run mkdocs build --strict`.
5. Push branch-mu dan buka pull request ke `main`. Isi templat yang muncul.

## Test dan gaya kode

```bash
uv run pytest
uv run black framework docs/tools
uv run ruff check framework docs/tools
uv run python framework/scripts/comment_style.py
uv run mkdocs build --strict
```

`uv run pytest` menguji paket `zul` di `framework/tests/`. Kategori lain punya perintahnya sendiri, dan daftarnya ada di [README](README.md#pengembangan).

## Yang boleh

- Memperbaiki bug, dengan test yang gagal sebelum perbaikan.
- Menambah fungsi kecil yang berlaku umum, dengan docstring `Gunanya:` dan `Cara pakai:` serta test berdata buatan.
- Mendukung library baru lewat adapter di `framework/src/zul/adapters/`, jika lisensinya MIT, BSD, atau Apache 2.0.
- Menulis atau memperbaiki dokumentasi di `docs/`, setelah dicocokkan dengan kode.
- Memakai code assistant, selama mengikuti aturan di bawah.

## Yang tidak boleh

- Mengimpor library pihak ketiga di luar `framework/src/zul/adapters/`. Test arsitektur gagal jika dilanggar.
- Menambah dependency berlisensi AGPL atau GPL.
- Menaruh API key, token, password, atau alamat server pribadi di kode, notebook, dokumentasi, atau pesan commit.
- Meng-commit rekaman video, frame CCTV, bobot model, hasil jalan (`outputs/`), atau file besar lain.
- Membuat kelas atau panduan untuk satu kasus penggunaan. Modul Zul adalah fungsi kecil yang bisa dirangkai.
- Mengubah `research/`, `.github/`, atau `uv.lock` tanpa membuka issue lebih dulu.
- Menghapus, melewati, atau melonggarkan test supaya lulus.
- Memformat ulang, mengganti nama, atau memindahkan file yang tidak berkaitan dengan tujuan pull request.

Daftar lengkap beserta alasannya ada di [Yang tidak boleh](https://zulkit.my.id/panduan/berkontribusi/#yang-tidak-boleh).

## Memakai AI untuk menulis kode

Memakai code assistant, termasuk vibe coding, diperbolehkan. Kamu bertanggung jawab atas setiap baris yang kamu kirim.

1. Pahami setiap baris. Jika kamu tidak bisa menjelaskan kenapa sebuah baris ada, hapus.
2. Sebut bantuan AI di deskripsi pull request: alat atau model, bagian yang dibantu, dan apa yang kamu periksa sendiri.
3. Jalankan sendiri semua pemeriksa di atas, lalu tempel hasilnya. Jangan menulis "semua test lulus" jika belum dijalankan.
4. Satu pull request, satu tujuan, dan usahakan di bawah 400 baris berubah di luar test dan dokumentasi.
5. Sambungkan assistant ke [MCP Zul](https://zulkit.my.id/tutorial/code-assistant/), supaya ia membaca `conventions` dan memeriksa hasilnya dengan `check_code`.
6. Larang assistant menambah dependency, file, parameter, atau abstraksi yang tidak diminta.

Pull request yang berisi impor atau fungsi karangan model, test yang hanya meniru implementasi, `try/except` yang menelan error, kode yang tidak dipanggil, atau perubahan besar di file yang tidak berkaitan akan diminta direvisi. Penjelasan dan prompt awal yang bisa kamu tempel ada di [Berkontribusi dengan bantuan AI](https://zulkit.my.id/panduan/berkontribusi/#berkontribusi-dengan-bantuan-ai).

## Melaporkan masalah

Buka [issue](https://github.com/kazuma313/zul_utilities/issues) dengan langkah untuk mengulang masalahnya, hasil yang diharapkan, dan hasil yang kamu dapat. Untuk masalah keamanan, jangan membuka issue publik; kirim email ke [kurniazuldam@gmail.com](mailto:kurniazuldam@gmail.com).
