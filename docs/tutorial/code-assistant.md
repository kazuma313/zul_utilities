# Menghubungkan Zul ke code assistant

Di tutorial ini, kamu menyambungkan Zul ke Claude Code lewat MCP (Model Context Protocol), lalu meminta Claude Code menulis kode dengan Zul. Hasil akhirnya: code assistant yang membaca daftar modul, cara pakai fungsi, contoh dari dokumentasi, dan aturan gaya Zul sebelum menulis kode. Jadi kode yang ditulisnya memakai fungsi Zul yang sudah ada dan ditulis dengan cara yang sama seperti kode Zul. Sekitar 10 menit.

Tutorial ini memakai Claude Code. Untuk Cursor, VS Code, atau Claude Desktop, ikuti bagian [Instalasi Zul dengan extra mcp](#instalasi-zul-dengan-extra-mcp) dan [Memeriksa server](#memeriksa-server), lalu lanjutkan di [Menghubungkan code assistant lain](../panduan/menghubungkan-code-assistant.md).

**Sebelum mulai:** kamu butuh Python 3.11 atau lebih baru, [uv](https://github.com/astral-sh/uv), dan Claude Code yang sudah ter-install. Periksa Claude Code dengan `claude --version`.

## Instalasi Zul dengan extra mcp

MCP server Zul butuh extra `mcp`. Install Zul sebagai tool global supaya perintah `zul` bisa dijalankan dari folder mana saja, termasuk oleh Claude Code:

```shell
uv tool install "zul[mcp] @ git+https://github.com/kazuma313/zul_utilities.git"
```

Jika `zul` sudah ter-install sebagai tool tanpa extra `mcp`, perintah yang sama meng-install ulang Zul dengan extra itu.

Dokumentasi Zul ikut ter-install di dalam paketnya. Dari dokumentasi itulah MCP server mengambil contoh kode dan aturan gaya, jadi isinya selalu sesuai dengan versi Zul yang ter-install.

## Memeriksa server

Sebelum menyambungkan Claude Code, jalankan server sekali dengan client uji bawaan Zul:

```shell
zul mcp check
```

Perintah itu menyalakan server di proses yang sama, membaca semua isinya, dan mencoba satu pencarian. Keluarannya seperti ini:

```text
MCP server zul siap: 9 tool, 4 resource, 2 prompt.
Tool: list_modules, module_guide, read_source, list_docs, read_doc, search_docs, find_examples, conventions, check_code
Resource: zul://conventions, zul://modules, zul://docs/{section}/{page}, zul://source/{module}
Prompt: tulis_modul_zul, pakai_zul
Contoh search_docs: ## panduan/menghitung-dengan-garis-dan-poligon > Menghitung lintasan dengan garis
```

Jika yang muncul adalah `MCP server butuh extra mcp`, perintah `zul` yang terpanggil berasal dari instalasi lain tanpa extra itu, misalnya dari virtual environment yang sedang aktif. Periksa dengan `which zul`, atau `where zul` di Windows.

## Mendaftarkan server di Claude Code

Daftarkan server untuk semua proyekmu:

```shell
claude mcp add --scope user zul -- zul mcp serve
```

Semua yang ada setelah `--` adalah perintah yang dijalankan Claude Code untuk menyalakan server. Server tidak perlu kamu jalankan sendiri: Claude Code menyalakannya setiap kali sesi baru dimulai, dan berbicara dengannya lewat stdin dan stdout.

Pastikan server tersambung:

```shell
claude mcp list
```

Baris `zul` di daftar itu berstatus tersambung (`Connected`). Di dalam sesi Claude Code, perintah `/mcp` menampilkan status yang sama beserta daftar tool-nya.

## Meminta kode yang memakai Zul

Buka Claude Code di folder proyekmu, lalu minta sesuatu yang bisa dikerjakan dengan Zul, misalnya:

```text
Buat script yang menghitung orang yang melewati sebuah garis di video.mp4, pakai Zul.
```

Sebelum menulis kode, Claude Code memanggil tool dari server `zul`. Biasanya urutannya `search_docs` untuk mencari halaman yang membahas garis penghitung, `find_examples` untuk contoh kode yang sudah diuji, lalu `module_guide` untuk melihat signature `LineCounter` dan fungsi deteksi. Setiap panggilan tool tampil di percakapan. Dengan bekal itu, script yang ditulisnya merangkai fungsi dari `zul.computer_vision` dan menyebut extra yang perlu di-install, bukan menulis ulang deteksi atau pelacakan dari nol.

Urutan kerja itu juga tersedia sebagai prompt siap pakai. Ketik prompt berikut di Claude Code, dengan tugasmu di dalam tanda kutip:

```text
/mcp__zul__pakai_zul "hitung orang yang berdiri di dalam poligon"
```

## Menulis kode di dalam Zul

Kalau kamu menambah fitur ke Zul sendiri, prompt `tulis_modul_zul` meminta Claude Code mengikuti aturan Zul. Buka Claude Code di checkout repository Zul, lalu ketik:

```text
/mcp__zul__tulis_modul_zul "timer yang menghitung jumlah frame, bukan detik"
```

Claude Code lalu membaca aturan gaya dengan `conventions`, memeriksa fungsi yang sudah ada dengan `list_modules`, dan membaca modul yang mirip dengan `read_source` sebagai contoh. Setelah menulis modul dan test-nya, Claude Code memeriksa setiap file baru dengan `check_code`. Tool itu melaporkan docstring tanpa bagian `Gunanya:` atau `Cara pakai:`, paragraf komentar yang belum berbentuk anak tangga beserta lipatan barunya, dan library pihak ketiga yang diimpor di luar `zul/adapters/`.

Kamu juga bisa melampirkan aturan gaya ke prompt mana pun dengan menyebut resource-nya:

```text
@zul:zul://conventions rapikan komentar di file ini.
```

## Yang sudah kamu kerjakan

Zul sekarang bisa dibaca oleh Claude Code di semua proyekmu. Server-nya hanya membaca: tidak ada tool yang menulis file atau menjalankan kode. Yang menulis kode tetap Claude Code, dengan izin darimu seperti biasa.

## Langkah berikutnya

- [Menghubungkan code assistant lain](../panduan/menghubungkan-code-assistant.md): config untuk Cursor, VS Code, dan Claude Desktop, juga cara memakai Zul dari checkout repository.
- [MCP server](../referensi/mcp.md): argumen setiap tool, resource, prompt, dan perintah `zul mcp`.
