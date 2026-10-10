# MCP server

MCP server Zul memberi code assistant akses baca ke modul, source code, dokumentasi, dan aturan gaya Zul lewat Model Context Protocol. Server berjalan lewat stdin dan stdout, dan dijalankan oleh code assistant dengan `zul mcp serve`. Server butuh extra `mcp`, yang meng-install SDK MCP resmi (`mcp`, berlisensi MIT).

Kode server ada di `src/zul/assistant/`. `zul.assistant.server` merakit server lewat adapter `zul.adapters.mcp`, dan isi setiap tool ada di `zul.assistant.knowledge`, yang hanya memakai library standar Python.

## Perintah

Perintah `zul mcp` punya tiga subperintah:

| Perintah | Kegunaan | Butuh extra `mcp` |
|---|---|---|
| `zul mcp serve` | Menjalankan server lewat stdin dan stdout sampai client menutup koneksi. Perintah ini dijalankan oleh code assistant, bukan olehmu. | Ya |
| `zul mcp check` | Menjalankan server dengan client MCP di proses yang sama, lalu mencetak jumlah dan nama tool, resource, dan prompt, beserta satu hasil `search_docs`. | Ya |
| `zul mcp config CLIENT` | Mencetak config untuk sebuah client. | Tidak |

`zul mcp serve` tidak mencetak apa pun ke stdout, karena stdout dipakai protokol MCP.

### Opsi `zul mcp config`

| Argumen atau opsi | Tipe | Default | Keterangan |
|---|---|---|---|
| `CLIENT` | teks | Wajib | `claude-code`, `cursor`, `vscode`, atau `claude-desktop`. |
| `--repo` | path | Tidak ada | Path checkout repository Zul. Jika diisi, server dijalankan dengan `uv --directory PATH run --no-dev --extra mcp zul mcp serve`, bukan dengan `zul mcp serve`. |

Bentuk keluarannya per client:

| Client | Keluaran |
|---|---|
| `claude-code` | Perintah `claude mcp add --scope user zul -- …`, lalu isi `.mcp.json` dengan kunci `"mcpServers"`. |
| `cursor`, `claude-desktop` | JSON dengan kunci `"mcpServers"`. |
| `vscode` | JSON dengan kunci `"servers"` dan `"type": "stdio"` di setiap server. |

### Kode keluar

| Kode | Arti | Perintah |
|---|---|---|
| `0` | Berhasil. | Semua |
| `1` | Extra `mcp` belum ter-install. Pesannya diawali `MCP server butuh extra mcp`. | `serve`, `check` |
| `1` | Panggilan contoh `search_docs` gagal. | `check` |
| `2` | Client tidak dikenal. Pesannya `Client 'NAMA' tidak dikenal. Pilih: …`. | `config` |

## Tool

Semua tool hanya membaca: tidak ada yang menulis file atau menjalankan kode. Setiap tool ditandai `readOnlyHint`, tanda di protokol MCP bahwa tool itu tidak mengubah apa pun. Setiap tool mengembalikan teks Markdown.

| Tool | Argumen | Mengembalikan |
|---|---|---|
| `list_modules` | Tidak ada | Semua modul Zul per paket, dengan baris pertama docstring dan extra yang dibutuhkan. |
| `module_guide` | `module: str` | Docstring modul, lalu signature dan docstring setiap fungsi dan kelas publik. Property ditulis sebagai `nama` (property). |
| `read_source` | `module: str` | Seluruh source code modul, beserta path file-nya. |
| `list_docs` | Tidak ada | Semua halaman dokumentasi per bagian, dengan judulnya. |
| `read_doc` | `page: str` | Isi lengkap satu halaman, misalnya `panduan/menggambar-di-frame`. |
| `search_docs` | `query: str`, `limit: int = 8` | Bagian dokumentasi dan docstring modul yang paling cocok, dengan potongan isinya. |
| `find_examples` | `topic: str`, `limit: int = 5` | Blok kode Python dari dokumentasi yang cocok dengan topik. |
| `conventions` | Tidak ada | Aturan menulis kode di dalam Zul. |
| `check_code` | `code: str`, `inside_zul: bool = True` | Daftar masalah bernomor, atau `Tidak ada masalah` jika kode lolos. |

`module` boleh ditulis lengkap, seperti `zul.computer_vision.zones`, atau tanpa awalan `zul`, seperti `computer_vision.zones`. Nama modul atau halaman yang tidak ditemukan dijawab dengan sampai tiga nama yang mirip.

`search_docs` memotong setiap halaman per judul bagian. Kata kunci yang muncul di judul bernilai tiga kali kata kunci di isi, jadi hasil teratas menunjuk ke bagian yang membahas topik itu.

Contoh dari `find_examples` yang berjudul file, misalnya `garis_penghitung.py`, juga dijalankan oleh test Zul, jadi contoh itu berjalan dengan versi Zul yang ter-install.

### Isi `conventions`

`conventions` merangkai aturan dari sumber yang sama dengan yang dibaca kontributor, jadi aturannya tidak perlu disalin ulang saat halaman sumbernya berubah:

- Aturan fungsi kecil: setiap modul mengerjakan satu hal yang bisa dirangkai, tanpa kelas untuk satu kasus.
- Docstring `zul.adapters`: library pihak ketiga hanya diimpor di `zul/adapters/`, beserta daftar library yang boleh diimpor langsung.
- Bagian **Mengikuti gaya kode**, **Menulis komentar dan docstring**, dan **Mengikuti gaya penulisan** dari [Berkontribusi](../panduan/berkontribusi.md).
- Aturan lisensi: tidak ada library berlisensi AGPL atau GPL.

### Pemeriksaan `check_code`

| Pemeriksaan | Berlaku untuk |
|---|---|
| Sintaks Python. Jika salah, hanya pesan ini yang dikembalikan, dengan nomor barisnya. | Semua kode |
| Paragraf komentar yang belum berbentuk anak tangga, beserta lipatan baris yang menggantikannya jika ada. | Semua kode |
| Docstring modul tanpa bagian `Gunanya:` atau `Cara pakai:`. | `inside_zul=True` |
| Library pihak ketiga yang diimpor langsung. Jika sudah ada adapter yang mengimpornya, adapter itu disebut, misalnya `zul.adapters.opencv` untuk `cv2`. | `inside_zul=True` |

## Resource

Resource berisi teks yang sama dengan tool, untuk client yang melampirkan konteks lewat resource. Di Claude Code, sebut resource dengan `@zul:URI`, misalnya `@zul:zul://conventions`. Semua resource bertipe `text/markdown`.

| URI | Isi | Sama dengan |
|---|---|---|
| `zul://conventions` | Aturan gaya Zul. | `conventions` |
| `zul://modules` | Daftar semua modul. | `list_modules` |
| `zul://docs/{section}/{page}` | Satu halaman dokumentasi, misalnya `zul://docs/panduan/mengukur-durasi`. | `read_doc` |
| `zul://source/{module}` | Source code satu modul, misalnya `zul://source/zul.computer_vision.zones`. | `read_source` |

## Prompt

Prompt berisi urutan tool yang perlu dipanggil untuk sebuah pekerjaan. Di Claude Code, prompt tampil sebagai perintah `/mcp__zul__NAMA`.

| Prompt | Argumen | Urutan kerja |
|---|---|---|
| `pakai_zul` | `tugas` | `search_docs`, `find_examples`, dan `module_guide`, lalu menulis kode yang merangkai fungsi Zul dan menyebut extra yang perlu di-install. |
| `tulis_modul_zul` | `topik` | `conventions`, `list_modules`, dan `read_source` modul yang mirip. Library baru diperiksa lisensinya dan diletakkan di adapter. Modul dan test-nya ditulis, lalu setiap file baru diperiksa dengan `check_code`. |

## Sumber dokumentasi

Tool dokumentasi membaca file Markdown dari folder pertama yang ditemukan:

1. `zul/_docs` di dalam paket yang ter-install. Saat wheel dibuat, folder `docs/tutorial`, `docs/panduan`, `docs/referensi`, dan `docs/konsep` disalin ke sana oleh `[tool.hatch.build.targets.wheel.force-include]` di `pyproject.toml`.
2. Folder `docs` di sebelah `src`, saat Zul dipakai dari checkout repository, termasuk instalasi editable.

Jika keduanya tidak ada, tool dokumentasi menjawab bahwa dokumentasi tidak ikut ter-install dan menyebut alamat situsnya. Tool modul tetap berjalan, karena membaca source code paket.

## Python API

Server bisa dirakit dan diuji dari Python. Fungsi berikut ada di `zul.assistant.server` dan butuh extra `mcp`:

| Fungsi | Mengembalikan |
|---|---|
| `build_server()` | Server dengan semua tool, resource, dan prompt terdaftar. |
| `serve()` | `None`. Menjalankan server lewat stdin dan stdout sampai client menutup koneksi. |
| `check()` | `dict` dengan kunci `tools`, `resources`, dan `prompts` (masing-masing `list[str]`), `sample` (teks hasil `search_docs`), dan `sample_failed` (`bool`). |

Fungsi tool di `zul.assistant.knowledge` dan prompt di `zul.assistant.prompts` adalah fungsi Python biasa yang mengembalikan `str`. Keduanya bisa dipanggil tanpa extra `mcp`:

```python
from zul.assistant.knowledge import check_code

print(check_code("import cv2\n"))
```

Kode itu mencetak tiga masalah bernomor:

```text
1. Docstring modul belum punya bagian `Gunanya:`.

2. Docstring modul belum punya bagian `Cara pakai:`.

3. `cv2` diimpor langsung. Di dalam Zul, library pihak ketiga hanya diimpor di adapter. Pakai fungsi dari `zul.adapters.opencv`, yang sudah membungkusnya.
```

Adapter `zul.adapters.mcp` membungkus SDK MCP dengan fungsi `create_server`, `add_tool`, `add_resource`, `add_prompt`, `run_stdio`, dan `self_check`. Nama fungsi menjadi nama tool, docstring menjadi deskripsinya, dan type hint menjadi skema argumennya.

## Halaman terkait

- [Tutorial: Menghubungkan Zul ke code assistant](../tutorial/code-assistant.md)
- [Panduan: Menghubungkan code assistant lain](../panduan/menghubungkan-code-assistant.md)
- [Perintah zul](cli.md)
- [Lapisan adapter](../konsep/lapisan-adapter.md)
