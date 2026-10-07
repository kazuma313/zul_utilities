# Menerbitkan dokumentasi dan playground

Situs dokumentasi ini terbit ke GitHub Pages, dan panel playground di situs itu bisa disambungkan ke aplikasimu.

Situs dokumentasi dan aplikasi adalah dua hal yang diterbitkan terpisah. Situs dokumentasi berupa file statis. Aplikasi adalah API yang berjalan di server. Panel playground menghubungkan keduanya lewat browser pembaca.

**Sebelum mulai:** repository-mu ada di GitHub, dan kamu punya hak mengubah pengaturannya.

## Menerbitkan situs ke GitHub Pages

Repository ini membawa workflow di `.github/workflows/docs.yml`. Workflow itu meng-install tool dokumentasi dengan versi persis dari `uv.lock`, membangun situs dengan `mkdocs build --strict`, menerbitkannya, lalu membuka situs yang terbit untuk memastikan bisa diakses.

1. Di halaman repository, buka **Settings**, lalu **Pages**. Pada **Source**, pilih **GitHub Actions**.

2. Di `mkdocs.yml`, pastikan `site_url` berisi alamat situsmu. Tanpa domain sendiri, bentuknya `https://NAMA_AKUN.github.io/NAMA_REPOSITORY/`. Situs ini memakai domain sendiri:

    ```yaml title="mkdocs.yml"
    site_url: https://zulkit.my.id/
    ```

3. Commit perubahanmu, lalu push ke branch `main`:

    ```shell
    git push origin main
    ```

4. Buka tab **Actions** di repository. Tunggu workflow **Dokumentasi** selesai. Alamat situsnya tampil di langkah `deploy`.

Setelah itu, setiap push ke `main` yang mengubah `docs/`, `overrides/`, `mkdocs.yml`, `pyproject.toml`, atau `uv.lock` menerbitkan ulang situsnya. Versi Zul di header situs dibaca dari `pyproject.toml`, jadi situs ikut terbit ulang saat versinya naik. Pull request yang mengubah file-file itu hanya dibangun, tidak diterbitkan, jadi kesalahannya ketahuan sebelum digabung. Untuk menerbitkan tanpa push baru, buka workflow **Dokumentasi** di tab **Actions**, lalu klik **Run workflow**.

## Memakai domain sendiri

Situs ini terbit di `zulkit.my.id`. Alamat bawaannya, `kazuma313.github.io/zul_utilities/`, tetap bisa dibuka dan dialihkan GitHub ke domain itu. Domain dipasang di pengaturan GitHub, bukan di file. Karena situs diterbitkan lewat workflow GitHub Actions, file `CNAME` tidak diperlukan, dan diabaikan jika ada.

**Sebelum mulai:** domainnya sudah terdaftar atas namamu, dan kamu bisa mengubah DNS-nya di panel tempat membeli domain.

1. Buka **Settings** akun GitHub-mu, bukan Settings repository, lalu **Pages**. Klik **Add a domain**, isi domainnya, lalu klik **Add domain**. GitHub menampilkan satu record TXT untuk verifikasi.

2. Di halaman repository, buka **Settings**, lalu **Pages**. Isi **Custom domain** dengan domainnya, lalu klik **Save**. Langkah ini dikerjakan sebelum DNS diarahkan ke GitHub, supaya tidak ada orang lain yang sempat memakai domainmu untuk situs GitHub Pages mereka.

3. Di panel DNS tempat membeli domain, tambahkan record berikut:

    | Tipe | Nama | Nilai |
    |---|---|---|
    | TXT | `_github-pages-challenge-NAMA_AKUN` | Nilai dari langkah 1 |
    | A | `@` | `185.199.108.153` |
    | A | `@` | `185.199.109.153` |
    | A | `@` | `185.199.110.153` |
    | A | `@` | `185.199.111.153` |
    | AAAA | `@` | `2606:50c0:8000::153` |
    | AAAA | `@` | `2606:50c0:8001::153` |
    | AAAA | `@` | `2606:50c0:8002::153` |
    | AAAA | `@` | `2606:50c0:8003::153` |
    | CNAME | `www` | `NAMA_AKUN.github.io` |

    Ganti `NAMA_AKUN` dengan nama akun GitHub-mu. Record `www` membuat `www.` di depan domainmu dialihkan ke domain utamanya. Jangan menambah record wildcard seperti `*`, karena subdomain mana pun lalu bisa diambil alih orang lain, walaupun domainnya sudah diverifikasi.

4. Tunggu perubahan DNS tersebar, paling lama 24 jam. Setelah itu kembali ke **Settings** akun, **Pages**, lalu klik **Verify** pada domainnya.

5. Di **Settings** repository, **Pages**, centang **Enforce HTTPS** setelah opsinya bisa dipilih. GitHub membuat sertifikat HTTPS-nya, paling lama 24 jam setelah DNS-nya benar.

6. Ganti `site_url` di `mkdocs.yml` dengan domainnya, lalu push ke `main`.

## Memeriksa situs sebelum diterbitkan

Workflow menghentikan penerbitan jika salah satu pemeriksaan berikut gagal:

| Pemeriksaan | Gagal jika |
|---|---|
| `mkdocs build --strict` | Ada tautan atau anchor yang rusak, atau tulisan blog tanpa tanggal atau tanpa ringkasan. |
| Hasil build | `index.html`, `404.html`, atau `blog/index.html` tidak ada di folder `site/`. |
| Situs yang terbit | Halaman utama atau halaman blog tidak bisa dibuka setelah lima kali percobaan. |

Jalankan pemeriksaan build yang sama di komputermu sebelum push:

```shell
uv run mkdocs build --strict
```

Hasilnya ada di folder `site/`. Folder itu berisi file statis, jadi bisa juga diunggah ke layanan hosting statis lain.

## Memperbarui versi tool dokumentasi

Versi MkDocs, tema Material, dan plugin-nya dikunci di `uv.lock`, di grup `docs` pada `pyproject.toml`. Karena itu situs yang dibangun workflow sama dengan yang kamu lihat di komputermu.

1. Perbarui satu paket, misalnya tema Material:

    ```shell
    uv lock --upgrade-package mkdocs-material
    ```

2. Bangun situsnya dan periksa tampilannya:

    ```shell
    uv run mkdocs build --strict
    uv run mkdocs serve
    ```

3. Commit `uv.lock`, lalu push. Workflow memakai versi barunya.

Versi action GitHub di workflow diperbarui oleh Dependabot. Sebulan sekali Dependabot membuka satu pull request jika ada versi baru, dan build dokumentasi berjalan di pull request itu. Gabungkan pull request-nya jika build-nya lolos.

## Playground di situs yang sudah terbit

Pembaca situs yang sudah terbit belum tentu punya proyek yang berjalan. Karena itu panel playground punya dua keadaan, dan tombol status di bilah panel menunjukkan yang sedang dipakai:

| Status | Yang dijalankan panel |
|---|---|
| **Simulasi** | Contoh jawaban yang sudah disiapkan untuk tiga fitur bawaan template. Tidak ada model yang dipanggil. |
| **Terhubung** | Agent di aplikasimu, termasuk fitur yang kamu daftarkan sendiri. |

Panel mencoba menghubungi `http://localhost:8000` saat halaman dibuka. Jika tidak ada jawaban, panel memakai simulasi. Pembaca tetap bisa melihat cara kerja agent tanpa meng-install apa pun.

## Menyambungkan situs yang terbit ke aplikasimu

Aplikasimu hanya menerima panggilan browser dari alamat yang kamu izinkan. Supaya situs yang sudah terbit boleh memanggilnya:

1. Di `.env` aplikasimu, tambahkan alamat situs ke `PLAYGROUND_ORIGINS`. Tulis asal situsnya saja, tanpa path:

    ```ini title=".env"
    PLAYGROUND_ENABLED=true
    PLAYGROUND_ORIGINS=http://127.0.0.1:8001,https://NAMA_AKUN.github.io
    ```

    Ganti `NAMA_AKUN` dengan nama akun GitHub-mu. Jika situsnya memakai domain sendiri, tulis domain itu, misalnya `https://zulkit.my.id`.

2. Mulai ulang aplikasinya.

3. Di panel playground, klik tombol status, isi **Alamat API proyekmu**, lalu klik **Sambungkan**.

Alamat API disimpan di browser masing-masing pembaca. Pembaca lain tidak ikut tersambung ke aplikasimu.

> [!NOTE]
> Sebagian browser tidak mengizinkan halaman HTTPS memanggil alamat `http://localhost`. Jika panel tetap berstatus Simulasi padahal aplikasimu berjalan, buka dokumentasi secara lokal dengan `uv run mkdocs serve`.

## Menerbitkan aplikasinya

Aplikasi hasil `zul build hexa` dijalankan sebagai container. Langkah membangun image dan menjalankannya ada di [Menjalankan aplikasi](menjalankan-aplikasi.md). Server tujuanmu harus memberi tiga hal: variabel environment dari `.env`, port yang dibuka ke luar, dan HTTPS di depannya.

> [!WARNING]
> Jangan menyalakan playground di aplikasi yang bisa dijangkau publik. Playground menampilkan argumen dan hasil setiap tool, dan menjalankan aksi agent tanpa autentikasi. Di server produksi, isi `PLAYGROUND_ENABLED=false`.

Sebelum menjalankan lebih dari satu worker, pindahkan penyimpan percakapan ke database. Rinciannya ada di [Menyimpan percakapan di database](menyimpan-percakapan.md).

## Halaman terkait

- [Workflow dokumentasi](../referensi/workflow-dokumentasi.md) untuk setiap langkah, pemeriksaan, dan versi yang dikunci di workflow.
- [Cara situs dokumentasi diterbitkan](../konsep/penerbitan-dokumentasi.md) untuk alasan di balik pengaturan workflow itu.
- [Menulis tulisan blog](menulis-blog.md) untuk menambah tulisan ke blog.
- [Mencoba fitur di playground](mencoba-di-playground.md) untuk mendaftarkan fiturmu sendiri ke panel.
- [Environment variable](../referensi/konfigurasi.md) untuk `PLAYGROUND_ENABLED` dan `PLAYGROUND_ORIGINS`.
- [Berkontribusi](berkontribusi.md) untuk aturan menulis halaman dokumentasi.
