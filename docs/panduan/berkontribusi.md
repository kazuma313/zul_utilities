# Berkontribusi ke Zul

Mengubah Zul sendiri mencakup menambah perintah, memperbaiki helper, mengembangkan template, dan menulis dokumentasi.

**Sebelum mulai:** kamu butuh Python 3.11 atau lebih baru, Git, dan [uv](https://github.com/astral-sh/uv).

## Menyiapkan lingkungan

1. Clone repository dan install semuanya:

    ```shell
    git clone https://github.com/kazuma313/zul_utilities.git
    cd zul_utilities
    uv sync --inexact
    ```

    `uv sync` membuat `.venv`, meng-install Zul dalam mode editable beserta semua extra, dan meng-install tool pengembangan: pytest, ruff, black, dan MkDocs. Opsi `--inexact` menjaga paket lain di environment tetap terpasang. Tanpa opsi itu, `uv sync` menghapus paket yang tidak tercatat di `uv.lock`, misalnya library untuk skill pool.

2. Pastikan semuanya ter-install:

    ```shell
    uv run zul --version
    uv run pytest
    ```

## Mengenali isi repository

Repository ini dibagi menjadi tiga kategori. Setiap folder kategori punya `README.md` sendiri yang menjelaskan isi dan cara menjalankannya.

| Kategori | Folder | Isi |
|---|---|---|
| Framework | [`framework/`](https://github.com/kazuma313/zul_utilities/tree/main/framework) | Paket `zul`, test-nya, skill pool, notebook contoh, boilerplate proyek, dan studi. |
| Dokumentasi | `docs/`, `mkdocs.yml` | Sumber situs dokumentasi ini dan blog-nya, template tema di `docs/overrides/`, dan script dokumentasi di `docs/tools/`. |
| Pengembangan diri | `research/` | Latihan coding, proyek mandiri, dan arsip. Bukan bagian dari package. |

Isi folder framework:

| Path | Isi |
|---|---|
| `framework/src/zul/cli.py` | Entry point perintah `zul`. |
| `framework/src/zul/commands/` | Kelompok perintah: `build.py`, `install.py`, `mcp.py`. |
| `framework/src/zul/assistant/` | MCP server untuk code assistant. Rinciannya ada di [MCP server](../referensi/mcp.md). |
| `framework/src/zul/templates/hexa/` | Template proyek yang disalin `zul build hexa`. |
| `framework/src/zul/adapters/` | Satu-satunya tempat library pihak ketiga diimpor, satu file per library. Rinciannya ada di [Mengubah perilaku library pihak ketiga](mengubah-perilaku-library.md). |
| `framework/src/zul/evaluation/` | Evaluasi retrieval dan RAG dengan ragas. Rinciannya ada di [Mengevaluasi retrieval dan RAG](mengevaluasi-retrieval.md). |
| `framework/src/zul/computer_vision/` | Fungsi computer vision: deteksi, garis dan poligon penghitung, timer, gambar. |
| `framework/src/zul/utilities/` | Helper yang bisa diimpor. |
| `framework/tests/` | Test paket `zul`: CLI, utilities, template, dan aturan arsitektur (`test_architecture.py`). |
| `framework/agentic/` | Skill pool untuk agent AI: `skills/` dengan model di dalamnya, `utilities/` berupa script. Rinciannya ada di [Membuat mind map](membuat-mindmap.md). |
| `framework/notebooks/` | Notebook contoh pemakaian utilities. |
| `framework/project/` | Boilerplate aplikasi yang dibangun di atas `zul`, misalnya `computer_vision/`. |
| `framework/scripts/` | Pemeriksa komentar anak tangga (`comment_style.py`) dan penyamar API key (`mask_api_keys.py`). |
| `framework/studies/` | Studi yang membandingkan model atau cara kerja, beserta data dan laporannya. |

File lain di root:

| Path | Isi |
|---|---|
| `pyproject.toml`, `uv.lock` | Dependency dan pengaturan tool untuk seluruh repository. `.venv` dibuat di root. |
| `.mcp.json` | MCP server `zul` untuk Claude Code yang dibuka di repository ini. Rinciannya ada di [Memakai Zul dari checkout repository](menghubungkan-code-assistant.md#memakai-zul-dari-checkout-repository). |
| `.github/workflows/docs.yml` | Workflow yang membangun dan menerbitkan situs dokumentasi. |
| `.github/workflows/ci.yml` | Workflow yang menjalankan black, ruff, pemeriksa komentar, dan test di setiap pull request. Rinciannya ada di [Pemeriksaan otomatis](#pemeriksaan-otomatis). |
| `.github/pull_request_template.md` | Templat deskripsi pull request. |
| `AGENTS.md`, `CLAUDE.md` | Petunjuk untuk code assistant yang bekerja di repository ini. |

## Menjalankan test

Test di `framework/tests/` tidak membutuhkan server atau API key. LLM diganti model palsu, dan Milvus serta Redis diganti client tiruan.

```shell
uv run pytest
```

Untuk menjalankan satu file:

```shell
uv run pytest framework/tests/test_template_hexa.py
```

Satu test integrasi membutuhkan server Milvus di `localhost:19530` dan dilewati secara bawaan. Untuk menjalankannya:

```shell
ZUL_RUN_INTEGRATION=1 uv run pytest framework/tests/test_utilities.py
```

Test template bekerja dengan membuat proyek sungguhan dari template ke folder sementara, lalu mengimpor dan menjalankan kodenya. Setiap perubahan di `framework/src/zul/templates/hexa/` langsung teruji.

Perintah `pytest` tanpa argumen hanya menguji paket `zul`. Kategori lain diuji dengan perintahnya sendiri:

```shell
uv run pytest framework/agentic
uv run pytest docs/tools/tests
```

> [!NOTE]
> Test di `research/latihan/` sebagian sengaja gagal, karena latihannya belum diselesaikan. Kegagalan di sana bukan regresi.

## Mengikuti gaya kode

Sebelum mengirim perubahan, jalankan tiga pemeriksa berikut. Ketiganya harus lolos tanpa temuan:

```shell
uv run black framework docs/tools
uv run ruff check framework docs/tools
uv run python framework/scripts/comment_style.py
```

Aturannya ada di `pyproject.toml`. Skill pool, notebook, studi, dan `research/` tidak ikut diperiksa, karena masing-masing punya gaya sendiri.

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
uv run python framework/scripts/comment_style.py --fix
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

## Pemeriksaan otomatis

Setiap pull request, dan setiap push ke `main`, menjalankan workflow **Pemeriksaan kode** (`.github/workflows/ci.yml`). Urutannya:

1. `black --check framework docs/tools`
2. `ruff check framework docs/tools`
3. `comment_style.py`
4. `pytest framework/tests`
5. `pytest docs/tools/tests`

Dependency-nya di-install persis dari `uv.lock` lewat grup `ci` di `pyproject.toml`. Situs dokumentasi dibangun oleh workflow terpisah, **Dokumentasi**, pada pull request yang mengubah `docs/`.

Workflow ini sengaja tidak meng-install extra `ocr` dan `detection`, karena keduanya membawa torch CUDA berukuran beberapa GB. Akibatnya, test yang butuh `docling` atau `rfdetr` dilewati di sana. Jalankan `uv run pytest` di komputermu sebelum mengirim perubahan di modul OCR atau deteksi. Test integrasi Milvus, skill pool, boilerplate computer vision, dan `research/` juga tidak dijalankan di workflow ini.

Status hijau berarti lima langkah di atas lulus. Status itu tidak menggantikan review: workflow tidak tahu apakah perubahan sesuai tujuan, apakah dokumentasinya benar, atau apakah ada kunci rahasia di diff.

## Yang boleh dan tidak boleh

Aturan di bawah dijaga oleh test atau pemeriksa bila ada. Sisanya dijaga lewat review, dan pull request yang melanggarnya diminta direvisi.

### Yang boleh

| Boleh | Syaratnya |
|---|---|
| Memperbaiki bug | Sertakan test yang gagal sebelum perbaikan dan lulus sesudahnya. |
| Menambah fungsi kecil yang berlaku umum | Docstring dengan bagian `Gunanya:` dan `Cara pakai:`, nama yang umum tanpa istilah domain, dan test dengan data buatan. |
| Menambah dukungan library baru | Buat adapter di `framework/src/zul/adapters/`, satu file per library, dengan lisensi MIT, BSD, atau Apache 2.0, dan daftarkan sebagai extra di `pyproject.toml`. |
| Menulis atau memperbaiki dokumentasi di `docs/` | Cocokkan dengan kode lebih dulu, dan `mkdocs build --strict` lolos. |
| Menambah studi di `framework/studies/` atau skill di `framework/agentic/` | Folder baru dengan `README.md` sendiri. |
| Memakai code assistant | Ikuti [aturan untuk bantuan AI](#berkontribusi-dengan-bantuan-ai). |

### Yang tidak boleh

| Tidak boleh | Alasan dan penjagaannya |
|---|---|
| Mengimpor library pihak ketiga di luar `framework/src/zul/adapters/` | Mengganti atau mengunci versi sebuah library dilakukan di satu file. `test_architecture.py` gagal jika dilanggar. |
| Menambah dependency berlisensi AGPL atau GPL | Zul berlisensi MIT. `test_no_dependency_uses_an_agpl_license` gagal jika dilanggar. Periksa lisensi dependency baru sebelum menambahkannya. |
| Menaruh API key, token, password, atau alamat server pribadi di kode, notebook, dokumentasi, atau pesan commit | Repository ini publik, dan riwayat git tidak bisa dibersihkan sepenuhnya. Notebook disamarkan dengan `framework/scripts/mask_api_keys.py`. Jika kunci terlanjur ter-commit, cabut di penyedianya; menghapus commit tidak cukup. |
| Meng-commit rekaman video, frame CCTV, bobot model (`weights/`), hasil jalan (`outputs/`), atau file besar lain | Ukuran repository, dan privasi orang yang terekam. Dokumentasi tidak boleh memuat frame dari rekaman asli. |
| Membuat kelas atau panduan untuk satu kasus penggunaan | Modul Zul adalah fungsi kecil yang bisa dirangkai. Tunjukkan kasusnya sebagai rangkaian fungsi yang sudah ada. |
| Mengubah isi `research/` | Folder itu berisi latihan pribadi pemilik repository dan tidak menerima kontribusi. |
| Mengedit `uv.lock` dengan tangan, atau memperbarui banyak dependency di pull request fitur | Perubahan dependency diulas sendiri. Jalankan `uv lock` hanya jika `pyproject.toml` berubah. |
| Menghapus, melewati (`skip`), atau melonggarkan test supaya lulus | Test yang gagal adalah informasi. Perbaiki penyebabnya. |
| Mematikan pemeriksa dengan `# noqa` atau `# type: ignore` tanpa alasan, atau mengubah aturan di `pyproject.toml` supaya lolos | Pemeriksa dijaga supaya gaya kode tetap seragam. Beri alasan di komentar jika memang perlu. |
| Memformat ulang, mengganti nama, atau memindahkan file yang tidak berkaitan dengan tujuan pull request | Diff yang berisi perubahan acak tidak bisa ditinjau. |
| Mengubah `.github/` (workflow dan Dependabot) tanpa membuka issue lebih dulu | Workflow berjalan dengan izin ke repository dan situs. |
| Menulis di dokumentasi hal yang belum kamu periksa terhadap kode | Dokumentasi yang rapi tetapi salah lebih merugikan daripada yang berantakan tetapi benar. |

## Berkontribusi dengan bantuan AI

Memakai code assistant, termasuk menulis hampir seluruh kode lewat percakapan dengan model (vibe coding), diperbolehkan. Satu hal berlaku sama untuk semua kontributor: kamu bertanggung jawab atas setiap baris yang kamu kirim. Reviewer meninjau hasil kerjamu, bukan keluaran model.

### Aturannya

1. **Pahami setiap baris.** Jika kamu tidak bisa menjelaskan kenapa sebuah baris ada, hapus baris itu.
2. **Sebut bantuan AI di deskripsi pull request.** Tulis alat atau model yang dipakai, bagian mana yang dibantu, dan apa yang kamu periksa sendiri. Memakai AI tidak dihukum. Pull request yang jelas dibuat model tetapi tidak mengakuinya diminta direvisi.
3. **Jalankan sendiri semua pemeriksa, lalu tempel hasilnya.** Jangan menulis "semua test lulus" kalau kamu belum menjalankannya. Perintahnya ada di bagian [Menjalankan test](#menjalankan-test) dan [Mengikuti gaya kode](#mengikuti-gaya-kode).
4. **Satu pull request, satu tujuan.** Usahakan di bawah 400 baris berubah, di luar test dan dokumentasi. Pull request yang lebih besar dipecah.
5. **Sambungkan assistant ke MCP Zul.** Minta ia memanggil `conventions`, `list_modules`, dan `module_guide` sebelum menulis, lalu `check_code` untuk setiap file baru. Di Claude Code, prompt `/mcp__zul__tulis_modul_zul` menjalankan urutan itu. Caranya ada di [Menghubungkan code assistant](menghubungkan-code-assistant.md).
6. **Batasi apa yang boleh diubah assistant.** Sebutkan file yang boleh disentuh, dan larang menambah dependency, file, atau abstraksi yang tidak diminta.

Prompt awal yang bisa kamu tempel ke assistant:

```text
Baca aturan lewat tool `conventions` dari MCP Zul, lalu kerjakan hanya
tugas ini: TUGAS.

Ubah hanya file ini: DAFTAR_FILE. Jangan menambah dependency, file baru,
parameter yang tidak dipakai, atau fallback "jaga-jaga". Tulis test dengan
data buatan. Setelah selesai, jalankan `check_code`, `pytest`, `black`,
`ruff`, `comment_style.py`, dan `mkdocs build --strict`, lalu laporkan
perintah dan hasil aslinya.
```

Ganti `TUGAS` dan `DAFTAR_FILE` dengan tugas dan file yang kamu maksud.

### Tanda pull request yang akan diminta direvisi

- Impor atau fungsi yang tidak ada di library, hasil karangan model. Jalankan kodenya sebelum mengirim.
- Test yang hanya mengulang implementasi, atau yang meniru (mock) fungsi yang sedang diuji.
- `try/except` yang menelan error, blok `pass`, `TODO` tanpa issue, atau kode yang dikomentari.
- Parameter, kelas, atau helper yang tidak dipanggil di mana pun.
- Docstring yang hanya mengulang nama fungsi, dan dokumentasi dengan nama parameter yang tidak ada di kode.
- Komentar bergaya asisten, seperti "Langkah 1" atau penjelasan yang mengulang kode, serta emoji dan kata promosi.
- Perubahan besar di file yang tidak berkaitan dengan tujuan pull request.
- Kunci, alamat server, atau jalur folder pribadi di contoh.

## Meninjau kontribusi

Bagian ini untuk pemilik repository dan reviewer. Urutannya dari yang paling murah dan paling sering menolak.

1. **Baca deskripsi pull request.** Tujuan, bantuan AI, dan hasil pemeriksa harus ada. Jika tidak, minta dilengkapi sebelum membaca kodenya.
2. **Lihat ukuran dan sebarannya:**

    ```shell
    git diff --stat main...HEAD
    ```

    Perubahan di folder yang tidak berkaitan, di `research/` atau `.github/`, atau di `uv.lock` tanpa penjelasan sudah menjadi alasan untuk meminta revisi.

3. **Cari pelanggaran yang bisa dicari dengan mesin:**

    ```shell
    git diff main...HEAD -U0 -- pyproject.toml
    git diff main...HEAD -U0 -- framework/src/zul ':!framework/src/zul/adapters' | grep -E "^\+(import|from) "
    git diff main...HEAD -U0 | grep -nE "sk-[A-Za-z0-9]{10,}|api[_-]?key|password|token"
    ```

    Perintah pertama menampilkan dependency baru, yang kedua impor baru di luar adapter, dan yang ketiga pola kunci rahasia. Hasil kosong tidak menjamin bersih, karena pola ini hanya mencari yang umum.

4. **Lihat status workflow Pemeriksaan kode** di pull request. Jika merah, minta kontributor memperbaikinya sebelum kamu membaca lebih jauh. Jika hijau, jalankan pemeriksa sendiri hanya untuk perubahan di modul OCR atau deteksi, yang dilewati di workflow, atau jika ada alasan tidak percaya hasilnya:

    ```shell
    uv run pytest
    uv run black --check framework docs/tools
    uv run ruff check framework docs/tools
    uv run python framework/scripts/comment_style.py
    uv run mkdocs build --strict
    ```

5. **Baca test sebelum implementasi.** Untuk perbaikan bug, test barunya harus gagal pada commit sebelum perbaikan. Test yang tidak pernah gagal tidak membuktikan apa pun.
6. **Cocokkan dokumentasi dengan kode.** Jalankan satu contoh kode dari halaman yang diubah, dan periksa nama parameter terhadap fungsinya.
7. **Putuskan.** Setujui, minta revisi dengan daftar yang spesifik, atau tutup dengan alasan. Alasan penutupan yang umum: tidak ada penjelasan bantuan AI, perubahan terlalu besar atau mencampur beberapa tujuan, melanggar salah satu aturan di [Yang tidak boleh](#yang-tidak-boleh), atau mengubah perilaku tanpa test.

Di Claude Code, `/code-review` dan `/security-review` bisa menjadi pendapat kedua atas diff pull request. Keduanya melengkapi, bukan menggantikan, langkah di atas.

## Mengirim perubahan

1. Buat branch dari `main`: `git checkout -b feature/nama-fitur`.
2. Kerjakan perubahannya, tambahkan test, dan perbarui dokumentasi yang terkait.
3. Jalankan test, ketiga pemeriksa gaya kode, dan `uv run mkdocs build --strict`.
4. Commit dan push branch-mu, lalu buka pull request ke `main`.
5. Isi templat pull request: apa yang berubah dan kenapa, cara mengujinya, bantuan AI, dan hasil pemeriksa.
6. Tunggu workflow **Pemeriksaan kode** selesai. Jika merah, perbaiki di branch yang sama; workflow berjalan lagi setiap kali kamu push.
