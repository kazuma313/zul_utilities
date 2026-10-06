# Menerbitkan dokumentasi dan playground

Halaman ini menunjukkan cara menerbitkan situs dokumentasi ini ke GitHub Pages, dan cara membuat panel playground di situs itu berbicara dengan aplikasimu.

Situs dokumentasi dan aplikasi adalah dua hal yang diterbitkan terpisah. Situs dokumentasi berupa file statis. Aplikasi adalah API yang berjalan di server. Panel playground menghubungkan keduanya lewat browser pembaca.

**Sebelum mulai:** repository-mu ada di GitHub, dan kamu punya hak mengubah pengaturannya.

## Menerbitkan situs ke GitHub Pages

Repository ini membawa workflow di `.github/workflows/docs.yml`. Workflow itu membangun situs dengan `mkdocs build --strict`, lalu menerbitkannya.

1. Di halaman repository, buka **Settings**, lalu **Pages**. Pada **Source**, pilih **GitHub Actions**.

2. Di `mkdocs.yml`, pastikan `site_url` berisi alamat situsmu. Untuk GitHub Pages bentuknya `https://NAMA_AKUN.github.io/NAMA_REPOSITORY/`:

    ```yaml title="mkdocs.yml"
    site_url: https://kazuma313.github.io/zul_utilities/
    ```

3. Commit perubahanmu, lalu push ke branch `main`:

    ```shell
    git push origin main
    ```

4. Buka tab **Actions** di repository. Tunggu workflow **Dokumentasi** selesai. Alamat situsnya tampil di langkah `deploy`.

Setelah itu, setiap push ke `main` yang mengubah folder `docs/` atau `mkdocs.yml` menerbitkan ulang situsnya. Untuk menerbitkan tanpa push baru, buka workflow **Dokumentasi** di tab **Actions**, lalu klik **Run workflow**.

## Memeriksa situs sebelum diterbitkan

Workflow menolak menerbitkan situs yang punya tautan rusak. Jalankan pemeriksaan yang sama di komputermu sebelum push:

```shell
uv run mkdocs build --strict
```

Hasilnya ada di folder `site/`. Folder itu berisi file statis, jadi bisa juga diunggah ke layanan hosting statis lain.

## Playground di situs yang sudah terbit

Pembaca situs yang sudah terbit belum tentu punya proyek yang berjalan. Karena itu panel playground punya dua keadaan, dan tombol status di bilah panel menunjukkan yang sedang dipakai:

| Status | Yang dijalankan panel |
|---|---|
| **Simulasi** | Contoh jawaban yang sudah disiapkan untuk tiga fitur bawaan template. Tidak ada model yang dipanggil. |
| **Terhubung** | Agent di aplikasimu, termasuk fitur yang kamu daftarkan sendiri. |

Panel mencoba menghubungi `http://localhost:8000` saat halaman dibuka. Jika tidak ada jawaban, panel memakai simulasi. Pembaca tetap bisa melihat cara kerja agent tanpa memasang apa pun.

## Menyambungkan situs yang terbit ke aplikasimu

Aplikasimu hanya menerima panggilan browser dari alamat yang kamu izinkan. Supaya situs yang sudah terbit boleh memanggilnya:

1. Di `.env` aplikasimu, tambahkan alamat situs ke `PLAYGROUND_ORIGINS`. Tulis asal situsnya saja, tanpa path:

    ```ini title=".env"
    PLAYGROUND_ENABLED=true
    PLAYGROUND_ORIGINS=http://127.0.0.1:8001,https://NAMA_AKUN.github.io
    ```

    Ganti `NAMA_AKUN` dengan nama akun GitHub-mu.

2. Mulai ulang aplikasinya.

3. Di panel playground, klik tombol status, isi **Alamat API proyekmu**, lalu klik **Sambungkan**.

Alamat API disimpan di browser masing-masing pembaca. Pembaca lain tidak ikut tersambung ke aplikasimu.

> [!NOTE]
> Sebagian browser tidak mengizinkan halaman HTTPS memanggil alamat `http://localhost`. Jika panel tetap berstatus Simulasi padahal aplikasimu berjalan, buka dokumentasi secara lokal dengan `uv run mkdocs serve`.

## Menerbitkan aplikasinya

Aplikasi hasil `zul build hexa` dijalankan sebagai container. Langkah membangun image dan menjalankannya ada di [Menjalankan aplikasi](menjalankan-aplikasi.md). Server tujuanmu harus memberi tiga hal: variabel environment dari `.env`, port yang dibuka ke luar, dan HTTPS di depannya.

> [!WARNING]
> Jangan menyalakan playground di aplikasi yang bisa dijangkau publik. Playground menampilkan argumen dan hasil setiap tool, dan menjalankan aksi agent tanpa autentikasi. Di server produksi, isi `PLAYGROUND_ENABLED=false`.

Sebelum menjalankan lebih dari satu worker, pindahkan penyimpan percakapan ke database. Lihat [Menyimpan percakapan di database](menyimpan-percakapan.md).

## Lihat juga

- [Mencoba fitur di playground](mencoba-di-playground.md) untuk mendaftarkan fiturmu sendiri ke panel.
- [Environment variable](../referensi/konfigurasi.md) untuk `PLAYGROUND_ENABLED` dan `PLAYGROUND_ORIGINS`.
- [Berkontribusi](berkontribusi.md) untuk aturan menulis halaman dokumentasi.
