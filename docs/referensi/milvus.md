# MilvusHelper

`MilvusHelper` membuat koneksi, database, collection, dan index Milvus dari satu file config, lalu menyediakan operasi insert, search, query, dan delete.

Baris berikut mengimpor kelasnya:

```python
from zul.utilities.vector_DB.milvus_helper import MilvusHelper
```

Modul ini membutuhkan extra `milvus` (`pymilvus`). Modul menulis log lewat logger `zul.utilities.vector_DB.milvus_helper` dan tidak mengatur handler atau level logging.

## `MilvusHelper(config_path)`

Memuat file config, menyambung ke server, menyiapkan database, lalu membuat collection yang belum ada.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `config_path` | `str` atau `Path` | Wajib | Path ke file config berekstensi `.yaml`, `.yml`, atau `.json`. |

Urutan kerja saat objek dibuat:

- Config dibaca dan divalidasi dengan [`ConfigLoader.load`](#configloaderloadconfig_path).
- Client dibuat dengan alamat `{uri}:{port}`. `user` dan `password` dikirim hanya jika diisi.
- Jika `db_name` diisi, database itu dibuat bila belum ada, lalu dipakai. Jika `db_name` kosong, langkah ini dilewati.
- Setiap collection di config yang belum ada di database dibuat beserta field, function, dan index-nya. Collection yang sudah ada tidak diubah.

**Melempar:**

- `FileNotFoundError` jika file config tidak ada.
- `ValueError` jika format file tidak didukung, file kosong, atau isinya tidak lolos validasi. Error ini muncul sebelum helper mencoba menyambung.
- `ValueError` dengan pesan `Unsupported function type: ...` jika `function_type` sebuah function bukan anggota `pymilvus.FunctionType`. Error ini muncul saat collection dibuat.
- Exception dari `pymilvus` jika koneksi, penyiapan database, atau pembuatan collection gagal. Exception itu dicatat ke log lalu dilempar ulang apa adanya.

**Atribut:**

| Atribut | Tipe | Keterangan |
|---|---|---|
| `config` | [`MilvusConfig`](#milvusconfig) | Config yang sudah divalidasi. |
| `client` | `pymilvus.MilvusClient` | Client untuk operasi yang tidak disediakan helper. |

## `insert(collection_name, data)`

Menyimpan satu record atau lebih ke sebuah collection.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `collection_name` | `str` | Wajib | Nama collection tujuan. |
| `data` | `dict` atau `list[dict]` | Wajib | Satu record atau daftar record. Kunci setiap dict adalah nama field. Satu dict dibungkus menjadi daftar berisi satu record. |

**Mengembalikan:** `dict` hasil `MilvusClient.insert`.

**Melempar:** exception dari `pymilvus` jika penyimpanan gagal.

Contoh berikut menyimpan dua record sekaligus:

```python
milvus.insert(
    "my_collection",
    [
        {"embedding": first_vector, "kategori": "peraturan"},
        {"embedding": second_vector, "kategori": "panduan"},
    ],
)
```

## `search(collection_name, query_vectors, anns_field="embedding", limit=10, output_fields=None, **kwargs)`

Mencari vektor yang paling mirip dengan setiap vektor query.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `collection_name` | `str` | Wajib | Nama collection. |
| `query_vectors` | `list[list[float]]` | Wajib | Daftar vektor query. |
| `anns_field` | `str` | `"embedding"` | Field vektor yang dicari. |
| `limit` | `int` | `10` | Jumlah hasil per query. |
| `output_fields` | `list[str]` atau `None` | `None` | Field yang dikembalikan. `None` diganti `["id", "distance"]`. |
| `**kwargs` | apa saja | Tidak ada | Diteruskan ke `MilvusClient.search`, misalnya `filter` atau `search_params`. |

**Mengembalikan:** hasil `MilvusClient.search`, yaitu satu daftar hasil untuk setiap vektor query.

**Melempar:** exception dari `pymilvus` jika pencarian gagal.

Contoh berikut mencari lima vektor termirip dengan satu query:

```python
hits = milvus.search(
    collection_name="my_collection",
    query_vectors=[query_vector],
    anns_field="embedding",
    limit=5,
    output_fields=["id"],
)
```

## `query(collection_name, filter_expr, output_fields=None, limit=None)`

Mengambil record yang cocok dengan sebuah ekspresi filter, tanpa pencarian vektor.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `collection_name` | `str` | Wajib | Nama collection. |
| `filter_expr` | `str` | Wajib | Ekspresi filter Milvus, misalnya `'id == "doc-1"'`. |
| `output_fields` | `list[str]` atau `None` | `None` | Field yang dikembalikan. `None` diganti `["*"]`, yaitu semua field. |
| `limit` | `int` atau `None` | `None` | Jumlah maksimum record. |

**Mengembalikan:** hasil `MilvusClient.query`, berupa daftar dict.

**Melempar:** exception dari `pymilvus` jika query gagal.

## `delete(collection_name, filter_expr)`

Menghapus record yang cocok dengan sebuah ekspresi filter.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `collection_name` | `str` | Wajib | Nama collection. |
| `filter_expr` | `str` | Wajib | Ekspresi filter yang memilih record untuk dihapus. |

**Mengembalikan:** hasil `MilvusClient.delete`.

**Melempar:** exception dari `pymilvus` jika penghapusan gagal.

## `list_collections()`

Mengembalikan nama semua collection di database yang sedang dipakai.

**Mengembalikan:** `list[str]`.

## `drop_collection(collection_name)`

Menghapus sebuah collection beserta seluruh datanya.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `collection_name` | `str` | Wajib | Nama collection yang dihapus. |

**Mengembalikan:** `None`.

**Melempar:** exception dari `pymilvus` jika penghapusan gagal.

## `get_collection_stats(collection_name)`

Mengembalikan statistik sebuah collection.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `collection_name` | `str` | Wajib | Nama collection. |

**Mengembalikan:** `dict` hasil `MilvusClient.get_collection_stats`. Kunci `row_count` berisi jumlah baris.

## `get_all_data(collection_name, filter_expr="", output_fields=None, batch_size=1024)`

Mengambil semua record dari sebuah collection per batch, memakai `MilvusClient.query_iterator`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `collection_name` | `str` | Wajib | Nama collection. |
| `filter_expr` | `str` | `""` | Ekspresi filter. String kosong berarti semua record. |
| `output_fields` | `list[str]` atau `None` | `None` | Field yang dikembalikan. `None` diganti `["*"]`. |
| `batch_size` | `int` | `1024` | Jumlah record per batch, antara 1 dan 16384. |

**Mengembalikan:** `list[dict]` berisi semua record yang cocok. Iterator ditutup setelah selesai, juga saat terjadi error.

## Skema config

Lokasi: `zul.utilities.vector_DB.config.config_schema`. File config dibaca menjadi model Pydantic yang bersarang seperti ini:

```text
MilvusConfig
├── connection: ConnectionConfig
└── collections: list[CollectionConfig]
    ├── milvus_schema: SchemaConfig
    │   ├── fields: list[FieldConfig]
    │   └── functions: list[FunctionConfig]
    └── indexes: list[IndexConfig]
```

File YAML dan JSON memakai struktur kunci yang sama. Contoh berikut menunjukkan config YAML yang paling ringkas untuk satu collection:

```yaml title="milvus_config.yaml"
connection:
  uri: "http://localhost"
  port: 19530
  db_name: "default"
collections:
  - collection_name: "documents"
    milvus_schema:
      fields:
        - {field_name: "id", datatype: "VARCHAR", max_length: 128, is_primary: true}
        - {field_name: "embedding", datatype: "FLOAT_VECTOR", dim: 768}
    indexes:
      - field_name: "embedding"
        index_name: "emb_idx"
        index_type: "HNSW"
        metric_type: "COSINE"
        params: {M: 16, efConstruction: 200}
```

### `DataTypeEnum`

Nilai yang diterima kunci `datatype` pada sebuah field.

| Nilai | Tipe Milvus |
|---|---|
| `VARCHAR` | `DataType.VARCHAR` |
| `INT64` | `DataType.INT64` |
| `FLOAT` | `DataType.FLOAT` |
| `FLOAT_VECTOR` | `DataType.FLOAT_VECTOR` |
| `SPARSE_FLOAT_VECTOR` | `DataType.SPARSE_FLOAT_VECTOR` |
| `BOOL` | `DataType.BOOL` |
| `JSON` | `DataType.JSON` |

Nilai di luar daftar ini ditolak saat config dimuat.

### `IndexType`

Daftar tipe index yang sering dipakai: `FLAT`, `IVF_FLAT`, `HNSW`, `IVF_PQ`, `SPARSE_INVERTED_INDEX`. Enum ini hanya rujukan. Kunci `index_type` tidak divalidasi terhadapnya.

### `MetricType`

Daftar metrik yang sering dipakai: `COSINE`, `L2`, `IP`, `BM25`. Enum ini hanya rujukan. Kunci `metric_type` tidak divalidasi terhadapnya.

### `ConnectionConfig`

Isi kunci `connection`.

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `uri` | `str` | `"http://localhost"` | Alamat server tanpa port. |
| `port` | `int` | `19530` | Port server. Helper menyambung ke `{uri}:{port}`. |
| `db_name` | `str` atau `None` | `None` | Database yang dipakai. Dibuat jika belum ada. |
| `user` | `str` atau `None` | `None` | Username. Dikirim ke client hanya jika diisi. |
| `password` | `str` atau `None` | `None` | Password. Dikirim ke client hanya jika diisi. |

### `FieldConfig`

Satu entri di `milvus_schema.fields`.

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `field_name` | `str` | Wajib | Nama field. |
| `datatype` | [`DataTypeEnum`](#datatypeenum) | Wajib | Tipe data. Huruf besar-kecil bebas: `varchar` dibaca sebagai `VARCHAR`. |
| `is_primary` | `bool` | `False` | `True` untuk primary key. |
| `auto_id` | `bool` | `False` | `True` agar Milvus mengisi field ini. Diteruskan ke Milvus hanya jika `True`. |
| `max_length` | `int` atau `None` | `None` | Panjang maksimum field `VARCHAR`. Diteruskan ke Milvus hanya jika diisi. |
| `dim` | `int` atau `None` | `None` | Dimensi field `FLOAT_VECTOR`. Diteruskan ke Milvus hanya jika diisi. |
| `description` | `str` atau `None` | `None` | Keterangan field. Diteruskan ke Milvus hanya jika diisi. |
| `enable_analyzer` | `bool` | `False` | `True` untuk field teks yang menjadi masukan function BM25. Diteruskan ke Milvus hanya jika `True`. |

### `FunctionConfig`

Satu entri di `milvus_schema.functions`.

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `name` | `str` | Wajib | Nama function. |
| `function_type` | `str` | `"BM25"` | Nama anggota `pymilvus.FunctionType`, huruf besar-kecil bebas. Diperiksa saat collection dibuat, bukan saat config dimuat. |
| `input_field_names` | `list[str]` | Wajib | Field masukan, misalnya field teks. |
| `output_field_names` | `list[str]` | Wajib | Field keluaran, misalnya field `SPARSE_FLOAT_VECTOR`. |

### `IndexConfig`

Satu entri di `indexes`.

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `field_name` | `str` | Wajib | Field yang di-index. |
| `index_name` | `str` | Wajib | Nama index. |
| `index_type` | `str` | Wajib | Tipe index. Diteruskan apa adanya ke Milvus, jadi tipe di luar [`IndexType`](#indextype) juga diterima. |
| `metric_type` | `str` | Wajib | Metrik. Diteruskan apa adanya ke Milvus, jadi metrik di luar [`MetricType`](#metrictype) juga diterima. |
| `params` | `dict` atau `None` | `{}` | Parameter index, misalnya `M` dan `efConstruction` untuk HNSW. Diteruskan ke Milvus hanya jika tidak kosong. |

### `SchemaConfig`

Isi kunci `milvus_schema` pada sebuah collection.

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `auto_id` | `bool` | `True` | Jika `True`, Milvus mengisi primary key. |
| `enable_dynamic_field` | `bool` | `True` | Jika `True`, kunci di luar skema ikut disimpan. |
| `description` | `str` atau `None` | `None` | Keterangan skema. Dikirim ke Milvus saat skema dibuat. `None` dikirim sebagai string kosong. |
| `fields` | `list[FieldConfig]` | Wajib | Daftar field. |
| `functions` | `list[FunctionConfig]` atau `None` | `[]` | Daftar function, misalnya BM25. |

### `CollectionConfig`

Satu entri di `collections`.

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `collection_name` | `str` | Wajib | Nama collection. |
| `description` | `str` atau `None` | `None` | Keterangan collection di file config. Helper tidak mengirim nilai ini ke Milvus. Yang dikirim adalah `milvus_schema.description`. |
| `shards_num` | `int` | `2` | Jumlah shard. |
| `milvus_schema` | [`SchemaConfig`](#schemaconfig) | Wajib | Skema collection. Kunci ini boleh juga ditulis `schema`. |
| `indexes` | `list[IndexConfig]` | Wajib | Daftar index. |

### `MilvusConfig`

Akar file config.

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `connection` | [`ConnectionConfig`](#connectionconfig) | Wajib | Pengaturan koneksi. Boleh berupa mapping kosong, sehingga semua nilai bawaan dipakai. |
| `collections` | `list[CollectionConfig]` | `[]` | Collection yang dibuat helper. |

## `ConfigLoader.load(config_path)`

Membaca file config Milvus dan mengembalikannya sebagai `MilvusConfig` yang sudah divalidasi. Lokasi: `zul.utilities.vector_DB.config.config_loader`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `config_path` | `str` atau `Path` | Wajib | Path ke file `.yaml`, `.yml`, atau `.json`. |

**Mengembalikan:** `MilvusConfig`.

**Melempar:** sama dengan [`load_config`](#load_configmodel-config_path).

Contoh berikut memvalidasi config tanpa menyambung ke server:

```python
from zul.utilities.vector_DB.config.config_loader import ConfigLoader

config = ConfigLoader.load("milvus_config.json")
print([collection.collection_name for collection in config.collections])
```

## Pembaca file config

Lokasi: `zul.utilities.vector_DB.config.config_file`. Fungsi di modul ini dipakai bersama oleh loader Milvus dan loader Redis.

### Konstanta

| Nama | Nilai | Keterangan |
|---|---|---|
| `YAML_SUFFIXES` | `(".yaml", ".yml")` | Ekstensi yang dibaca sebagai YAML. |
| `JSON_SUFFIXES` | `(".json",)` | Ekstensi yang dibaca sebagai JSON. |

Format dipilih dari ekstensi file, bukan dari isinya. Huruf besar-kecil ekstensi diabaikan.

### `read_config_file(config_path)`

Membaca file YAML atau JSON menjadi `dict` tanpa validasi skema.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `config_path` | `str` atau `Path` | Wajib | Path ke file config. |

**Mengembalikan:** `dict[str, Any]`.

**Melempar:**

- `FileNotFoundError` dengan pesan `Configuration file not found: ...` jika file tidak ada.
- `ValueError` dengan pesan `Unsupported file format: ... Use .yaml, .yml, or .json` jika ekstensinya lain.
- `ValueError` dengan pesan `Configuration file is empty: ...` jika file kosong.
- `ValueError` dengan pesan `Configuration root must be a mapping: ...` jika akar file bukan mapping.

### `load_config(model, config_path)`

Membaca file config lalu memvalidasinya dengan sebuah model Pydantic.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `model` | kelas turunan `pydantic.BaseModel` | Wajib | Model yang dipakai untuk validasi, misalnya `MilvusConfig`. |
| `config_path` | `str` atau `Path` | Wajib | Path ke file config. |

**Mengembalikan:** objek `model` yang sudah terisi.

**Melempar:**

- Semua error dari [`read_config_file`](#read_config_fileconfig_path).
- `ValueError` dengan pesan `Configuration validation failed for 'FILE': ...` jika isi file tidak lolos validasi. Pesan itu memuat nama file, lokasi field yang salah, dan alasannya.

### `write_config_file(config_dict, output_path, format="yaml")`

Menulis sebuah `dict` ke file YAML atau JSON.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `config_dict` | `dict[str, Any]` | Wajib | Isi yang ditulis. |
| `output_path` | `str` atau `Path` | Wajib | Path file tujuan. |
| `format` | `str` | `"yaml"` | `yaml`, `yml`, atau `json`. Huruf besar-kecil bebas. |

**Mengembalikan:** `None`. YAML ditulis dengan urutan kunci asli. JSON ditulis dengan indentasi dua spasi.

**Melempar:** `ValueError` dengan pesan `Unsupported format: ... Use 'yaml' or 'json'` jika `format` tidak dikenal.

## `DEFAULT_MILVUS_CONFIG`

Isi awal file config yang ditulis `zul install milvus-helper`. Lokasi: `zul.commands.install`. Isi ini lolos validasi `MilvusConfig`. Dalam format YAML, isinya seperti berikut:

```yaml title="milvus.yaml"
connection:
  uri: http://localhost
  port: 19530
  db_name: default
collections:
- collection_name: my_collection
  shards_num: 2
  description: My first collection
  milvus_schema:
    auto_id: true
    enable_dynamic_field: true
    fields:
    - field_name: id
      datatype: VARCHAR
      max_length: 128
      is_primary: true
    - field_name: embedding
      datatype: FLOAT_VECTOR
      dim: 768
    functions: []
  indexes:
  - field_name: embedding
    index_name: emb_idx
    index_type: HNSW
    metric_type: COSINE
    params:
      M: 16
      efConstruction: 200
```

## Halaman terkait

- [Menyimpan dan mencari vektor di Milvus](../panduan/memakai-milvus.md) untuk langkah pemakaian.
- [Perintah zul](cli.md) untuk `zul install milvus-helper` dan opsinya.
- [RedisHelper dan RedisVectorDB](redis.md) untuk helper vector database yang lain.
