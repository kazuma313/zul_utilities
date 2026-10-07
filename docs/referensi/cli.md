# Perintah zul

`zul` adalah perintah baris yang ter-install bersama package Zul. Perintah ini membuat proyek baru dari template dan menulis file config awal untuk helper vector database.

Bentuk lengkap setiap perintah adalah sebagai berikut:

```shell
zul --version
zul version
zul build hexa --name NAMA --yes
zul install milvus-helper --config-name FILE --force
zul install redis-helper --config-name FILE --force
```

`NAMA` adalah nama proyek, yang juga menjadi nama folder yang dibuat. `FILE` adalah nama file config yang ditulis. Semua opsi boleh dihilangkan.

Tabel berikut merangkum perintah yang tersedia:

| Perintah | Kegunaan |
|---|---|
| [`zul --version`](#opsi-global) | Mencetak versi Zul yang ter-install. |
| [`zul version`](#zul-version) | Mencetak versi Zul yang ter-install. |
| [`zul build hexa`](#zul-build-hexa) | Membuat proyek hexagonal baru dari template. |
| [`zul install milvus-helper`](#zul-install-milvus-helper) | Menulis file config awal untuk `MilvusHelper`. |
| [`zul install redis-helper`](#zul-install-redis-helper) | Menulis file config awal untuk `RedisHelper`. |

Perintah `zul` didaftarkan oleh `[project.scripts]` di `pyproject.toml` sebagai `zul = "zul.cli:app"`. Kelompok perintah `build` ada di `src/zul/commands/build.py`, dan kelompok `install` ada di `src/zul/commands/install.py`.

## Opsi global

Opsi berikut berlaku pada perintah `zul` itu sendiri:

| Opsi | Singkatan | Keterangan |
|---|---|---|
| `--version` | `-V` | Mencetak versi, lalu keluar dengan kode `0`. |
| `--help` | Tidak ada | Menampilkan bantuan. Opsi ini tersedia di `zul`, di setiap kelompok perintah, dan di setiap subperintah. |

`zul`, `zul build`, dan `zul install` yang dijalankan tanpa subperintah menampilkan layar bantuan masing-masing. Opsi pelengkap otomatis shell bawaan Typer (`--install-completion`) dimatikan.

Keluaran `zul --version` berbentuk seperti ini:

```text
zul version 0.0.1
```

Versi dibaca dari metadata package yang ter-install. Jika metadata itu tidak ditemukan, yang tercetak adalah `zul version unknown`.

## `zul version`

Mencetak versi Zul yang ter-install. Keluarannya sama dengan `zul --version`, dan perintah ini tidak punya opsi selain `--help`.

## `zul build hexa`

Membuat proyek baru dengan menyalin seluruh isi template `hexa` ke sebuah folder baru di direktori kerja saat ini.

| Opsi | Singkatan | Tipe | Default | Keterangan |
|---|---|---|---|---|
| `--name` | `-n` | teks | Ditanyakan | Nama proyek, sekaligus path folder yang dibuat relatif terhadap direktori kerja. |
| `--yes` | `-y` | flag | Mati | Melewati pertanyaan konfirmasi. Dipakai di script atau CI. |

Perilaku perintah ini:

- Jika `--name` tidak diberikan, Zul menanyakan `Masukkan nama proyek:` dengan jawaban bawaan `my-hexa-project`.
- Spasi di awal dan akhir nama dibuang sebelum nama dipakai.
- Jika `--yes` tidak diberikan, Zul menanyakan `Buat proyek 'NAMA' (hexa)?` dengan jawaban bawaan ya.
- Semua file dan folder template disalin, kecuali folder `__pycache__` dan file yang cocok dengan pola `*.py[cod]`.
- Teks `{{ project_name }}` di `README.md` proyek baru diganti dengan nama folder proyek.
- Jika penyalinan gagal di tengah jalan, folder proyek yang baru terisi sebagian dihapus lagi.

Contoh berikut membuat proyek `my-app` tanpa pertanyaan:

```shell
zul build hexa --name my-app --yes
```

Keluarannya mencantumkan setiap file dan folder tingkat teratas yang dibuat, lalu lokasi proyek:

```text
📄  File .env.example dicopy.
📄  File .gitignore dicopy.
📁  Folder data dicopy.
📁  Folder dockerfile dicopy.
📁  Folder logs dicopy.
📁  Folder notebooks dicopy.
📄  File pytest.ini dicopy.
📄  File README.md dicopy.
📄  File requirements-dev.txt dicopy.
📄  File requirements.txt dicopy.
📁  Folder src dicopy.
📁  Folder test dicopy.

✅ Proyek HEXA 'my-app' berhasil dibuat!
📁 Lokasi: LOKASI_PROYEK
```

`LOKASI_PROYEK` adalah path absolut folder proyek di komputermu. Isi proyek dijelaskan di [Struktur proyek hexa](struktur-proyek.md).

Tabel berikut mencantumkan pesan dan kode keluar perintah ini:

| Keadaan | Pesan | Kode keluar |
|---|---|---|
| Proyek dibuat | `✅ Proyek HEXA 'NAMA' berhasil dibuat!` | `0` |
| Kamu menjawab tidak di konfirmasi | `❌ Dibatalkan` | `0` |
| Nama kosong atau hanya berisi spasi | `❌ Error: Nama proyek tidak boleh kosong!` | `1` |
| Folder dengan nama itu sudah ada | `❌ Error: Direktori 'NAMA' sudah ada!` | `1` |

Jika folder sudah ada, isinya tidak diubah.

## `zul install milvus-helper`

Menulis file config awal untuk `MilvusHelper` ke direktori kerja saat ini.

| Opsi | Singkatan | Tipe | Default | Keterangan |
|---|---|---|---|---|
| `--config-name` | Tidak ada | teks | `milvus_config.json` | Nama file yang ditulis. Ekstensinya menentukan format: `.json`, `.yaml`, atau `.yml`. |
| `--force` | `-f` | flag | Mati | Menimpa file yang sudah ada tanpa bertanya. |

Isi file yang ditulis berasal dari `DEFAULT_MILVUS_CONFIG` dan sudah lolos validasi skema `MilvusHelper`:

| Bagian | Isi |
|---|---|
| `connection` | `uri` `http://localhost`, `port` `19530`, `db_name` `default`. |
| `collections` | Satu collection `my_collection` dengan `shards_num` `2`. |
| `milvus_schema.fields` | `id` (`VARCHAR`, `max_length` 128, primary key) dan `embedding` (`FLOAT_VECTOR`, `dim` 768). `auto_id` dan `enable_dynamic_field` bernilai `true`. |
| `indexes` | Index `emb_idx` pada `embedding`: `HNSW`, metrik `COSINE`, `M` 16, `efConstruction` 200. |

Arti setiap kunci dijelaskan di [Referensi MilvusHelper](milvus.md).

File berekstensi `.json` ditulis sebagai JSON dengan indentasi empat spasi. File berekstensi `.yaml` atau `.yml` ditulis sebagai YAML dengan urutan kunci yang sama.

Contoh berikut menulis config dalam format YAML:

```shell
zul install milvus-helper --config-name milvus.yaml
```

Keluarannya menyebut file yang dibuat dan cara memakainya:

```text
📦 Setup milvus_helper config di folder project...
✅ LOKASI_FILE berhasil dibuat!

📁 File config:
  - LOKASI_FILE
💡 Sesuaikan connection & collections di file tersebut, lalu pakai di Python:
  from zul.utilities.vector_DB.milvus_helper import MilvusHelper
  milvus = MilvusHelper(config_path='milvus.yaml')
  milvus.list_collections()
📦 Butuh dependency: pip install 'zul[milvus]'
```

`LOKASI_FILE` adalah path absolut file config di komputermu.

Jika file sudah ada dan `--force` tidak diberikan, Zul bertanya sebelum menimpanya. Jawaban bawaannya tidak:

```text
⚠️  milvus_config.json sudah ada di folder project!
Ganti konfigurasi lama? [y/N]:
```

Tabel berikut mencantumkan pesan dan kode keluar perintah ini:

| Keadaan | Pesan | Kode keluar |
|---|---|---|
| File ditulis | `✅ LOKASI_FILE berhasil dibuat!` | `0` |
| File sudah ada dan kamu menjawab tidak | `⏹️  Dibatalkan.` | `0` |
| Ekstensi `--config-name` tidak didukung | `Invalid value: Format '.toml' tidak didukung. Pakai .json, .yaml, atau .yml` | `2` |

Jika kamu menjawab tidak atau ekstensinya tidak didukung, tidak ada file yang ditulis atau diubah.

## `zul install redis-helper`

Menulis file config awal untuk `RedisHelper` ke direktori kerja saat ini.

| Opsi | Singkatan | Tipe | Default | Keterangan |
|---|---|---|---|---|
| `--config-name` | Tidak ada | teks | `redis_config.yaml` | Nama file yang ditulis. Ekstensinya menentukan format: `.json`, `.yaml`, atau `.yml`. |
| `--force` | `-f` | flag | Mati | Menimpa file yang sudah ada tanpa bertanya. |

Isi file yang ditulis berasal dari `DEFAULT_REDIS_CONFIG` dan sudah lolos validasi skema `RedisHelper`:

| Bagian | Isi |
|---|---|
| `connection` | `uri` `http://localhost`, `port` `6379`. |
| `schema.index` | `name` `my_index`, `prefix` `doc`, `storage_type` `hash`. |
| `schema.fields` | `content` (`text`) dan `content_embedding_vector` (`vector`, `dims` 768, `distance_metric` `cosine`, `algorithm` `flat`, `datatype` `float32`). |
| `hybrid_search` | `text_field_name` `content`, `vector_field_name` `content_embedding_vector`, `text_scorer` `BM25`, `alpha` `0.5`, `num_results` `10`, `return_fields` `["content"]`. |

Arti setiap kunci dijelaskan di [Referensi RedisHelper dan RedisVectorDB](redis.md).

Format file, pertanyaan saat file sudah ada, pesan, dan kode keluar sama dengan [`zul install milvus-helper`](#zul-install-milvus-helper). Keluarannya menyebut `RedisHelper` dan extra `zul[redis]`:

```text
📦 Setup redis_helper config di folder project...
✅ LOKASI_FILE berhasil dibuat!

📁 File config:
  - LOKASI_FILE
💡 Sesuaikan connection & schema di file tersebut, lalu pakai di Python:
  from zul.utilities.vector_DB.redis_helper import RedisHelper
  redis_helper = RedisHelper(config_path='redis_config.yaml')
  redis_helper.hybrid_search(query_text='...', query_vector=[...])
📦 Butuh dependency: pip install 'zul[redis]'
```

## Nama lama bergaris bawah

Kedua perintah `install` terdaftar dengan dua nama. Nama bertanda hubung adalah nama resminya. Nama bergaris bawah adalah nama lama yang tetap diterima, tetapi tidak ditampilkan di layar bantuan.

| Nama resmi | Nama lama |
|---|---|
| `zul install milvus-helper` | `zul install milvus_helper` |
| `zul install redis-helper` | `zul install redis_helper` |

Nama lama menerima opsi yang sama dan berperilaku sama dengan nama resminya.

## Kode keluar

Tabel berikut merangkum kode keluar semua perintah:

| Kode | Arti | Perintah |
|---|---|---|
| `0` | Berhasil, atau kamu membatalkan di pertanyaan konfirmasi. | Semua perintah |
| `1` | Nama proyek kosong, atau folder proyek sudah ada. | `zul build hexa` |
| `2` | Kesalahan pemakaian: perintah atau opsi tidak dikenal, atau ekstensi `--config-name` tidak didukung. | Semua perintah |

## Pesan error

Tabel berikut mencantumkan setiap pesan error beserta penyebabnya:

| Pesan | Perintah | Kode keluar | Penyebab |
|---|---|---|---|
| `❌ Error: Nama proyek tidak boleh kosong!` | `zul build hexa` | `1` | Nama yang diberikan kosong setelah spasinya dibuang. |
| `❌ Error: Direktori 'NAMA' sudah ada!` | `zul build hexa` | `1` | Folder tujuan sudah ada. |
| `Invalid value: Format 'EKSTENSI' tidak didukung. Pakai .json, .yaml, atau .yml` | `zul install ...` | `2` | Ekstensi `--config-name` bukan `.json`, `.yaml`, atau `.yml`. |
| `No such command 'NAMA'.` | Semua perintah | `2` | Subperintah tidak terdaftar. |

`NAMA` dan `EKSTENSI` adalah nilai yang kamu ketik.

## Fungsi dan konstanta di balik perintah

Fungsi berikut ada di `zul.commands.build` dan bisa dipakai langsung dari Python, misalnya di test. Baris impornya adalah sebagai berikut:

```python
from zul.commands.build import copy_template, render_project_name
```

### `copy_template(template_name, project_dir)`

Menyalin seluruh isi `templates/<template_name>` ke `project_dir`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `template_name` | `str` | Wajib | Nama folder template di dalam package, misalnya `"hexa"`. |
| `project_dir` | `Path` | Wajib | Folder tujuan. Folder ini tidak boleh sudah ada. |

**Mengembalikan:** `list[Path]`, yaitu daftar file dan folder tingkat teratas yang dibuat, terurut.

**Melempar:** `FileNotFoundError` jika template tidak ada di package. `FileExistsError` jika `project_dir` sudah ada.

Contoh berikut membuat proyek hexa di folder `my-app`:

```python
from pathlib import Path

from zul.commands.build import copy_template

created_items = copy_template("hexa", Path("my-app"))
```

### `render_project_name(project_dir, project_name)`

Mengganti teks `{{ project_name }}` di `README.md` milik `project_dir` dengan `project_name`. Jika `README.md` tidak ada, fungsi ini tidak melakukan apa pun.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `project_dir` | `Path` | Wajib | Folder proyek hasil `copy_template`. |
| `project_name` | `str` | Wajib | Nama yang ditulis ke `README.md`. |

**Mengembalikan:** `None`.

### `get_version()`

Mengembalikan versi Zul yang ter-install sebagai `str`, atau `"unknown"` jika metadata package tidak ditemukan. Fungsi ini ada di `zul.cli`.

### Konstanta

| Nama | Modul | Nilai |
|---|---|---|
| `PACKAGE_NAME` | `zul.cli` | `"zul"` |
| `TEMPLATES_DIR` | `zul.commands.build` | Path folder `templates` di dalam package `zul`. |
| `DEFAULT_HEXA_PROJECT_NAME` | `zul.commands.build` | `"my-hexa-project"` |
| `PROJECT_NAME_PLACEHOLDER` | `zul.commands.build` | `"{{ project_name }}"` |
| `YAML_SUFFIXES` | `zul.commands.install` | `(".yaml", ".yml")` |
| `JSON_SUFFIXES` | `zul.commands.install` | `(".json",)` |
| `DEFAULT_MILVUS_CONFIG` | `zul.commands.install` | Isi awal file config Milvus. |
| `DEFAULT_REDIS_CONFIG` | `zul.commands.install` | Isi awal file config Redis. |

## Halaman terkait

- [Panduan: Instalasi Zul](../panduan/instalasi-zul.md)
- [Panduan: Membuat proyek baru](../panduan/membuat-proyek.md)
- [Panduan: Berkontribusi ke Zul](../panduan/berkontribusi.md), untuk menambah perintah atau template baru
- [Referensi: Struktur proyek hexa](struktur-proyek.md)
- [Referensi: MilvusHelper](milvus.md)
- [Referensi: RedisHelper dan RedisVectorDB](redis.md)
