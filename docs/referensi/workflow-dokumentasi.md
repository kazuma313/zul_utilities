# Workflow dokumentasi

Situs ini dibangun dan diterbitkan ke GitHub Pages, di domain `zulkit.my.id`, oleh workflow GitHub Actions bernama **Dokumentasi**, di `.github/workflows/docs.yml`. Versi action-nya diperbarui oleh Dependabot, yang diatur di `.github/dependabot.yml`. Langkah menerbitkan situs ada di [Menerbitkan dokumentasi](../panduan/menerbitkan-dokumentasi.md).

## Pemicu

Workflow berjalan pada tiga kejadian:

| Kejadian | Syarat | Job yang berjalan |
|---|---|---|
| `push` | Ke branch `main`, dan mengubah salah satu path di bawah | `build`, lalu `deploy` |
| `pull_request` | Mengubah salah satu path di bawah | `build` saja |
| `workflow_dispatch` | Tombol **Run workflow** di tab **Actions** | `build`, lalu `deploy` jika dijalankan di `main` |

Path yang memicu workflow:

| Path | Isi |
|---|---|
| `docs/**` | Semua halaman, gambar, dan blog. |
| `overrides/**` | Template yang menimpa bawaan Material, yaitu header. |
| `scripts/docs_hooks.py` | Hook yang membaca versi Zul untuk header. |
| `mkdocs.yml` | Menu, tema, dan plugin. |
| `pyproject.toml` | Grup dependency `docs`, dan versi Zul yang tampil di header. |
| `uv.lock` | Versi persis setiap paket. |
| `.python-version` | Versi Python. |
| `.github/workflows/docs.yml` | Workflow ini sendiri. |

## Job `build`

Membangun situs dan menyimpannya sebagai artifact.

| Pengaturan | Nilai |
|---|---|
| Runner | `ubuntu-24.04` |
| Batas waktu | 15 menit |
| Izin | `contents: read` |

Langkah-langkahnya, berurutan:

| Langkah | Yang dijalankan | Gagal jika |
|---|---|---|
| Checkout | `actions/checkout`, tanpa menyimpan kredensial git | Repository tidak bisa diambil. |
| Install uv dan Python | `astral-sh/setup-uv` dengan uv `0.12.3` dan Python `3.11`, cache berdasarkan `uv.lock` | uv atau Python tidak bisa diunduh. |
| Install dependency dokumentasi | `uv sync --frozen --only-group docs` | `uv.lock` tidak memuat paket grup `docs`. |
| Bangun situs | `uv run --no-sync mkdocs build --strict` | Ada peringatan apa pun, termasuk tautan rusak dan tulisan blog tanpa tanggal atau ringkasan. |
| Periksa hasil build | Memeriksa `site/index.html`, `site/404.html`, dan `site/blog/index.html` | Salah satu file itu tidak ada atau kosong. |
| Unggah artifact | `actions/upload-pages-artifact` dengan folder `site` | Folder `site` tidak bisa diunggah. |

`--frozen` meng-install versi persis dari `uv.lock` tanpa menyusun ulang versinya. `--only-group docs` hanya meng-install paket situs dokumentasi, tanpa Zul dan dependency pengembangan lainnya.

Artifact bernama `github-pages` dan disimpan 7 hari. File dan folder yang namanya diawali titik tidak ikut masuk artifact.

## Job `deploy`

Menerbitkan artifact dari job `build` ke GitHub Pages.

| Pengaturan | Nilai |
|---|---|
| Berjalan jika | Kejadiannya bukan `pull_request` dan branch-nya `main` |
| Menunggu | Job `build` selesai dengan sukses |
| Runner | `ubuntu-24.04` |
| Batas waktu | 15 menit |
| Izin | `pages: write`, `id-token: write` |
| Environment | `github-pages`, dengan alamat situs sebagai URL-nya |

Langkah-langkahnya, berurutan:

| Langkah | Yang dijalankan | Gagal jika |
|---|---|---|
| Terbitkan | `actions/deploy-pages` | GitHub Pages menolak artifact, atau Source di **Settings > Pages** bukan **GitHub Actions**. |
| Periksa situs yang terbit | `curl --fail` ke halaman utama dan `blog/`, diulang sampai 5 kali dengan jeda 10 detik | Salah satu halaman tetap tidak bisa dibuka setelah percobaan terakhir. |

## Antrian dan pembatalan

Run dikelompokkan dengan pengaturan `concurrency`:

| Kejadian | Grup | Run yang lebih lama |
|---|---|---|
| `push` dan `workflow_dispatch` | `pages` | Tidak pernah dibatalkan di tengah jalan. Run yang masih menunggu digantikan oleh run terbaru. |
| `pull_request` | `docs-` diikuti ref pull request | Dibatalkan begitu ada commit baru di pull request yang sama. |

## Versi yang dikunci

| Bagian | Dikunci di | Bentuk |
|---|---|---|
| Action GitHub | `.github/workflows/docs.yml` | Commit SHA lengkap. Nomor versinya tertulis di komentar setelah SHA, misalnya `# v7.0.1`. |
| uv | Input `version` pada `astral-sh/setup-uv` | Nomor versi persis. |
| Python | Input `python-version`, sama dengan `.python-version` | `3.11` |
| Runner | `runs-on` di setiap job | `ubuntu-24.04` |
| Paket Python | `uv.lock`, grup `docs` di `pyproject.toml` | Versi dan hash persis setiap paket. |

Grup `docs` di `pyproject.toml` berisi:

| Paket | Batas versi |
|---|---|
| `mkdocs` | `>=1.6,<2` |
| `mkdocs-material` | `>=9.7,<10` |
| `markdown-callouts` | `>=0.4` |

Grup `dev` memuat grup `docs`, jadi `uv sync` dan `uv run mkdocs` di komputermu memakai versi yang sama dengan workflow.

## Dependabot

`.github/dependabot.yml` mengatur pembaruan otomatis:

| Pengaturan | Nilai |
|---|---|
| Yang diperiksa | Action di `.github/workflows/` |
| Jadwal | Sebulan sekali |
| Pengelompokan | Semua pembaruan dalam satu pull request |
| Awalan pesan commit | `ci` |

Pull request dari Dependabot hanya mengubah `.github/workflows/docs.yml`, jadi job `build` berjalan di pull request itu sebelum kamu menggabungkannya. Versi paket Python di `uv.lock` tidak diperbarui Dependabot.

## Perintah yang sama di komputermu

| Langkah di workflow | Perintah di komputermu |
|---|---|
| Install dependency dokumentasi | `uv sync` |
| Bangun situs | `uv run mkdocs build --strict` |
| Pratinjau | `uv run mkdocs serve`, lalu buka `http://127.0.0.1:8001` |

## Halaman terkait

- [Menerbitkan dokumentasi](../panduan/menerbitkan-dokumentasi.md) untuk langkah menerbitkan dan memperbarui versi.
- [Cara situs dokumentasi diterbitkan](../konsep/penerbitan-dokumentasi.md) untuk alasan di balik pengaturan ini.
- [Format tulisan blog](blog.md) untuk pemeriksaan khusus tulisan blog.
