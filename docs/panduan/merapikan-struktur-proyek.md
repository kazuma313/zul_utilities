# Merapikan struktur proyek

Panduan ini membagi proyek aplikasi yang sudah ada menjadi empat induk di root-nya: `backend`, `frontend`, `mobile`, dan `assets`. Code assistant yang tersambung ke MCP Zul menyusun rencananya, dan memindahkan file hanya setelah kamu setuju. Alasan dan aturan strukturnya ada di [Struktur proyek berinduk](../konsep/struktur-proyek-berinduk.md).

## Sebelum mulai

- MCP Zul sudah tersambung ke code assistant-mu. Caranya ada di [Menghubungkan code assistant](menghubungkan-code-assistant.md).
- Proyek berada di repository git, dan semua file sudah di-commit. `git mv` menolak file yang belum dilacak git dengan pesan `not under version control`.
- Code assistant dibuka dari folder root proyek yang akan dirapikan. MCP Zul hanya memeriksa folder tempat assistant dibuka, kecuali kamu mendaftarkan folder lain (lihat [Memeriksa folder lain](#memeriksa-folder-lain)).

## Merapikan proyek

1. Di Claude Code, buka folder proyek, lalu jalankan prompt:

    ```text
    /mcp__zul__rapikan_arsitektur
    ```

    Di client lain, minta assistant memanggil tool `layout_rules`, lalu `check_layout`.

2. Baca rencana yang ditunjukkan assistant. Bentuknya seperti ini untuk proyek dengan `main.py`, `requirements.txt`, `logo.png`, folder `web` berisi aplikasi React, dan folder `app` berisi aplikasi Flutter:

    ```text
    ## Perlu dipindahkan

    1. `main.py` termasuk backend (backend: file .py).
       `git mv -- main.py backend/main.py`
    2. `requirements.txt` termasuk backend (backend: file requirements.txt).
       `git mv -- requirements.txt backend/requirements.txt`
    3. `web` termasuk frontend (frontend: package.json memakai react-dom).
       `git mv -- web frontend`
    4. `app` termasuk mobile (mobile: file pubspec.yaml).
       `git mv -- app mobile`
    5. `logo.png` termasuk assets (assets: file .png).
       `git mv -- logo.png assets/images/logo.png`

    ## Perlu keputusan pemilik proyek

    1. `misc`: tidak ada tanda yang dikenali.
    ```

    Folder yang berisi satu aplikasi utuh diganti namanya menjadi induknya, seperti `web` menjadi `frontend`. Jika ada dua aplikasi sejenis, keduanya dipindahkan ke dalam induknya, misalnya `backend/api` dan `backend/worker`.

3. Jawab bagian **Perlu keputusan**. Untuk setiap folder, sebutkan induk tujuannya, atau minta assistant membiarkannya di root jika memang untuk seluruh proyek (seperti `docs/` atau `scripts/`). Assistant tidak menebak.

4. Setujui rencananya. Assistant menjalankan perintah `git mv` satu per satu, supaya riwayat file tetap terjaga.

5. Biarkan assistant memperbarui path yang berubah di Dockerfile, `docker-compose.yml`, konfigurasi CI, README, dan skrip, lalu menjalankan test di setiap induk.

6. Pastikan assistant memanggil `check_layout` lagi. Hasil akhirnya harus berbunyi:

    ```text
    Struktur sudah sesuai: tidak ada temuan.
    ```

Setelah itu, commit hasilnya sebagai satu commit, supaya pemindahan mudah ditelusuri.

## Memperbaiki temuan lain

`check_layout` melaporkan hal lain di luar pemindahan file. Untuk masing-masing, perbaikannya begini:

| Temuan | Perbaikan |
|---|---|
| `... mengimpor ... (induk backend)` | Kode di `frontend` atau `mobile` mengimpor file `backend`. Ganti dengan panggilan HTTP ke API `backend`, jangan memindahkan kodenya. |
| `... belum punya README.md` atau `manifest dependency` | Tambahkan README dan manifest (`pyproject.toml`, `package.json`, atau `pubspec.yaml`) ke induk itu. |
| `.env ada, tetapi .gitignore belum mengabaikannya` | Tambahkan `.env` ke `.gitignore`. Jika `.env` pernah di-commit, anggap isinya bocor dan ganti kuncinya. |
| `.env ada tanpa .env.example` | Salin `.env` menjadi `.env.example` dengan nilai kosong, lalu commit `.env.example`. |
| `... adalah kode, bukan asset` | Pindahkan file itu keluar dari `assets`, ke induk yang memakainya. |
| `nama mengandung karakter khusus` | Ganti nama file atau folder itu dulu. Tool sengaja tidak membuatkan perintah untuknya. |
| `... adalah symlink; tidak diperiksa` | Symlink tidak diikuti. Periksa isinya sendiri. |

## Memeriksa folder lain

Secara bawaan, `check_layout` hanya memeriksa folder tempat code assistant dibuka. Untuk memeriksa proyek di tempat lain, daftarkan folder itu sebelum server MCP dinyalakan, lewat environment variable `ZUL_PROJECT_ROOTS`. Pisahkan beberapa folder dengan `;` di Windows atau `:` di Linux dan macOS. Contoh config ada di [referensi MCP](../referensi/mcp.md#pemeriksaan-check_layout).

Root drive dan folder home selalu ditolak, karena terlalu luas untuk satu proyek.

## Jika hasilnya tidak sesuai

| Pesan | Penyebab dan jalan keluar |
|---|---|
| `... berada di luar folder kerja server` | Folder itu bukan folder tempat assistant dibuka. Buka assistant dari folder proyek, atau daftarkan folder itu di `ZUL_PROJECT_ROOTS`. |
| `... terlalu luas untuk satu proyek` | Yang diberikan adalah root drive atau folder home. Pilih folder root proyeknya. |
| `fatal: not under version control` dari `git mv` | File belum dilacak git. Jalankan `git add` dan commit dulu, lalu ulangi. |
| Folder tidak terklasifikasi walaupun jelas milik satu induk | Folder itu tidak punya tanda yang dikenali. Tanda yang dicari ada di tabel [Cara mengenali induk](../konsep/struktur-proyek-berinduk.md#cara-mengenali-induk-sebuah-folder). Pindahkan folder itu secara manual, atau tambahkan manifest ke dalamnya. |

## Langkah berikutnya

- [Struktur proyek berinduk](../konsep/struktur-proyek-berinduk.md) menjelaskan aturan dan alasannya.
- [MCP server](../referensi/mcp.md) memuat argumen dan keluaran `check_layout`.
- [Membuat proyek baru](membuat-proyek.md) membuat kerangka `backend` hexagonal dengan `zul build hexa`.
