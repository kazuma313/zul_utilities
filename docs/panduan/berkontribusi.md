# Berkontribusi ke Zul

Mengubah Zul sendiri mencakup menambah perintah, memperbaiki helper, mengembangkan template, dan menulis dokumentasi.

**Sebelum mulai:** kamu butuh Python 3.11 atau lebih baru, Git, dan [uv](https://github.com/astral-sh/uv).

## Menyiapkan lingkungan

1. Clone repository dan install semuanya:

    ```shell
    git clone https://github.com/kazuma313/zul_utilities.git
    cd zul_utilities
    uv sync
    ```

    `uv sync` membuat `.venv`, meng-install Zul dalam mode editable beserta semua extra, dan meng-install tool pengembangan: pytest, ruff, black, dan MkDocs.

2. Pastikan semuanya ter-install:

    ```shell
    uv run zul --version
    uv run pytest tests
    ```

## Mengenali isi repository

| Path | Isi |
|---|---|
| `src/zul/cli.py` | Entry point perintah `zul`. |
| `src/zul/commands/` | Kelompok perintah: `build.py`, `install.py`, `mcp.py`. |
| `src/zul/assistant/` | MCP server untuk code assistant. Rinciannya ada di [MCP server](../referensi/mcp.md). |
| `src/zul/templates/hexa/` | Template proyek yang disalin `zul build hexa`. |
| `src/zul/adapters/` | Satu-satunya tempat library pihak ketiga diimpor, satu file per library. Rinciannya ada di [Mengubah perilaku library pihak ketiga](mengubah-perilaku-library.md). |
| `src/zul/computer_vision/` | Fungsi computer vision: deteksi, garis dan poligon penghitung, timer, gambar. |
| `src/zul/utilities/` | Helper yang bisa diimpor. |
| `tests/` | Test untuk CLI, utilities, template, dan aturan arsitektur (`test_architecture.py`). |
| `research/agentic/algorithms/skills/` | Kumpulan skill untuk agent AI. Rinciannya ada di [Membuat mind map](membuat-mindmap.md). |
| `scripts/comment_style.py` | Pemeriksa bentuk komentar. Isinya ada di `zul.assistant.comment_style`, yang juga dipakai tool MCP `check_code`. |
| `scripts/new_post.py` | Pembuat tulisan blog baru dari template. Rinciannya ada di [Menulis tulisan blog](menulis-blog.md). |
| `docs/` | Sumber dokumentasi ini. Blog ada di `docs/blog/`. |
| `mkdocs.yml` | Susunan menu, tema, dan plugin situs dokumentasi. |
| `.mcp.json` | MCP server `zul` untuk Claude Code yang dibuka di repository ini. Rinciannya ada di [Memakai Zul dari checkout repository](menghubungkan-code-assistant.md#memakai-zul-dari-checkout-repository). |
| `.github/workflows/docs.yml` | Workflow yang membangun dan menerbitkan situs dokumentasi. |
| `tutorial/` | Notebook contoh pemakaian utilities. |
| `research/` | Latihan dan eksperimen; bukan bagian dari package. |

## Menjalankan test

Test di `tests/` tidak membutuhkan server atau API key. LLM diganti model palsu, dan Milvus serta Redis diganti client tiruan.

```shell
uv run pytest tests
```

Untuk menjalankan satu file:

```shell
uv run pytest tests/test_template_hexa.py
```

Satu test integrasi membutuhkan server Milvus di `localhost:19530` dan dilewati secara bawaan. Untuk menjalankannya:

```shell
ZUL_RUN_INTEGRATION=1 uv run pytest tests/test_utilities.py
```

Test template bekerja dengan membuat proyek sungguhan dari template ke folder sementara, lalu mengimpor dan menjalankan kodenya. Setiap perubahan di `src/zul/templates/hexa/` langsung teruji.

> [!NOTE]
> Perintah `pytest` tanpa argumen juga menjalankan test di `research/`. Folder itu berisi latihan yang sebagian sengaja belum diimplementasikan, jadi kegagalan di sana bukan regresi.

## Mengikuti gaya kode

Sebelum mengirim perubahan, jalankan tiga pemeriksa berikut. Ketiganya harus lolos tanpa temuan:

```shell
uv run black src tests scripts
uv run ruff check src tests scripts
uv run python scripts/comment_style.py src tests scripts
```

Aturannya ada di `pyproject.toml`. Folder `research/` dan `tutorial/` tidak ikut diperiksa.

Pedoman yang dipakai di repository ini:

- Nama menjelaskan maksud: `tools_requiring_approval`, bukan `tools2`.
- Satu fungsi mengerjakan satu hal.
- Aturan bisnis yang dilanggar dilaporkan dengan exception khusus, bukan dengan mengembalikan `None`.
- Setiap perbaikan bug disertai test yang gagal sebelum perbaikan.

## Menulis komentar dan docstring

Setiap modul diawali docstring yang menjawab tiga pertanyaan, supaya pembaca bisa mulai memakainya tanpa membuka dokumentasi:

```python
"""
Ringkasan satu baris tentang isi modul.

Gunanya:
    Masalah apa yang diselesaikan dan kapan modul ini dipakai.

Cara pakai:
    from paket.modul import sesuatu

    hasil = sesuatu(argumen)

Contoh:
    Potongan kode yang bisa disalin, atau cara menambah hal baru di modul ini.
"""
```

Bagian-bagian di dalam modul dipisah dengan blok komentar berjudul. Paragraf di bawah judulnya menjelaskan alasan, bukan mengulang kodenya:

```python
# --------------------------------------------------------------------------
# Batas Langkah
# --------------------------------------------------------------------------
#
# Satu putaran tool di graph ReAct melewati dua node: "tool_node" lalu
# "llm_call". Node LLM memakai angka ini untuk tahu kapan ia harus
# berhenti meminta tool, agar masih ada langkah untuk menjawab.
#

STEPS_PER_TOOL_ROUND = 2
```

Paragraf komentar yang lebih dari satu baris berbentuk anak tangga: setiap baris lebih pendek satu sampai enam karakter dari baris di atasnya. Bentuk ini mengikuti gaya komentar Laravel. Untuk memeriksanya dan melipat ulang baris yang belum pas:

```shell
uv run python scripts/comment_style.py src tests scripts --fix
```

Jika pemeriksa melaporkan "ubah kalimatnya", tidak ada pelipatan yang pas untuk kalimat itu. Ganti satu atau dua kata sampai pemeriksa lolos.

Folder kosong di template juga punya `__init__.py` berisi docstring: apa yang seharusnya ditaruh di sana, beserta contohnya.

## Menulis dokumentasi

Dokumentasi ditulis dalam Markdown di folder `docs/` dan dibangun dengan [MkDocs Material](https://squidfunk.github.io/mkdocs-material/). Untuk melihat pratinjau yang diperbarui saat file berubah:

```shell
uv run mkdocs serve
```

Buka `http://127.0.0.1:8001`. Sebelum mengirim perubahan, pastikan situs terbangun tanpa peringatan. Mode `--strict` menggagalkan build jika ada tautan atau anchor yang rusak:

```shell
uv run mkdocs build --strict
```

### Memilih jenis halaman

Dokumentasi ini mengikuti [Diátaxis](https://diataxis.fr). Setiap halaman hanya berisi satu jenis tulisan, dan jenisnya menentukan foldernya:

| Jenis | Folder | Untuk pembaca yang | Isi |
|---|---|---|---|
| Tutorial | `docs/tutorial/` | Baru belajar | Pelajaran berurutan dengan hasil yang terlihat di setiap langkah. |
| Panduan | `docs/panduan/` | Punya tugas tertentu | Langkah bernomor menuju satu tujuan. |
| Referensi | `docs/referensi/` | Sedang bekerja dan butuh fakta | Parameter, nilai kembalian, dan error, tanpa cerita. |
| Konsep | `docs/konsep/` | Ingin mengerti alasannya | Penjelasan, alasan desain, dan akibat tiap pilihan. |

Jika sebuah panduan butuh menjelaskan alasan, tulis satu kalimat lalu tautkan ke halaman Konsep. Jika butuh daftar parameter, tautkan ke halaman Referensi. Setelah menambah halaman, daftarkan di bagian `nav` pada `mkdocs.yml`.

Blog di `docs/blog/` berada di luar keempat jenis itu: isinya catatan bertanggal tentang apa yang dipelajari. Tulisan blog tidak perlu didaftarkan di `nav`. Cara menulisnya ada di [Menulis tulisan blog](menulis-blog.md).

### Mengikuti gaya penulisan

- Sapa pembaca dengan "kamu" dan tulis dengan kalimat aktif. Di tutorial, pakai "kita" untuk hal yang dikerjakan bersama.
- Awali setiap contoh kode dengan kalimat yang menjelaskan apa yang dilakukannya.
- Beri judul file pada blok kode yang menunjukkan isi sebuah file: ` ```python title="src/..." `.
- Tulis nilai yang harus diganti pembaca dengan huruf besar, misalnya `API_KEY`, lalu jelaskan setelah contohnya.
- Hindari kata seperti "mudah", "cukup", dan "powerful". Pembaca yang sedang kesulitan tidak terbantu olehnya.
- Pakai `> [!NOTE]` untuk informasi tambahan dan `> [!WARNING]` untuk hal yang bisa menghilangkan data atau membahayakan. Pakai paling banyak satu per bagian.
- Periksa setiap perintah, nama parameter, dan contoh kode terhadap kodenya. Dokumentasi yang rapi tetapi salah lebih merugikan daripada yang berantakan tetapi benar.

### Menaruh panel playground

Halaman tutorial dan panduan bisa memuat panel untuk mencoba agent. Atributnya ada di [Mencoba fitur di playground](mencoba-di-playground.md). Tulis satu kalimat di dalam `div` sebagai pengganti saat halaman dibaca di GitHub:

```html
<div class="zul-playground" data-feature="ReAct">
Panel Playground tampil saat halaman ini dibuka sebagai situs dokumentasi.
</div>
```

## Mengirim perubahan

1. Buat branch dari `main`: `git checkout -b feature/nama-fitur`.
2. Kerjakan perubahannya, tambahkan test, dan perbarui dokumentasi yang terkait.
3. Jalankan test, ketiga pemeriksa gaya kode, dan `uv run mkdocs build --strict`.
4. Commit dan push branch-mu, lalu buka pull request ke `main`.

Jelaskan di pull request apa yang berubah dan kenapa, serta cara mengujinya.
