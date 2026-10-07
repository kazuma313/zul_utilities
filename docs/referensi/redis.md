# RedisHelper dan RedisVectorDB

Dua kelas untuk memakai Redis sebagai vector database lewat RedisVL: `RedisVectorDB` menerima skema index lewat kode, dan `RedisHelper` membaca koneksi serta skema dari file config.

Baris berikut mengimpor keduanya:

```python
from zul.utilities.vector_DB.redis_helper import RedisHelper, RedisVectorDB
```

Modul ini membutuhkan extra `redis` (`redis`, `redisvl`). Modul menulis log lewat logger `zul.utilities.vector_DB.redis_helper` dan tidak mengatur handler atau level logging.

## Konstanta dan tipe modul

| Nama | Nilai | Keterangan |
|---|---|---|
| `MIN_SEARCH_MODULE_VERSION` | `20600` | Versi minimum modul pencarian untuk pencarian vektor. Redis melaporkan versi modul sebagai bilangan bulat, jadi `20600` berarti 2.6.0. |
| `SEARCH_MODULE_NAMES` | `("search", "RediSearch")` | Nama modul yang dianggap sebagai modul pencarian. |
| `Vector` | `np.ndarray`, `bytes`, atau `list[float]` | Tipe yang diterima parameter vektor query. |

## Format vektor

| Dipakai untuk | Format yang diterima |
|---|---|
| Vektor di record yang disimpan dengan storage `hash` | Bytes `float32`, misalnya `np.array(vector, dtype=np.float32).tobytes()`. |
| Vektor query di method pencarian | `numpy.ndarray`, daftar float, atau bytes. Selain bytes, nilainya diubah ke bytes `float32`. Bytes dipakai apa adanya. |

## `reciprocal_rank_fusion(*ranked_lists, K=100)`

Menggabungkan beberapa daftar peringkat menjadi satu dengan Reciprocal Rank Fusion. Setiap item mendapat skor `1 / (peringkat + K)` dari setiap daftar yang memuatnya, dengan peringkat mulai dari 1, lalu skor itu dijumlahkan.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `*ranked_lists` | `list` | Wajib | Satu daftar per sistem pencarian, urut dari yang paling relevan. |
| `K` | `int` | `100` | Konstanta di rumus RRF. Hanya bisa dikirim sebagai argumen kata kunci. |

**Mengembalikan:** tuple berisi dua daftar. Yang pertama berisi pasangan `(item, skor)` urut dari skor tertinggi. Yang kedua berisi item saja dalam urutan yang sama.

Contoh berikut menggabungkan dua daftar peringkat:

```python
from zul.utilities.vector_DB.redis_helper import reciprocal_rank_fusion

scored, ranked = reciprocal_rank_fusion(["a", "b"], ["b", "c"])
print(ranked)
```

Kode itu mencetak urutan gabungan:

```text
['b', 'a', 'c']
```

## `RedisVectorDB(host="localhost", port=6379, password=None, db=0, decode_responses=False, username=None)`

Membuat koneksi ke Redis dan mengujinya dengan `PING`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `host` | `str` | `"localhost"` | Nama host server. |
| `port` | `int` | `6379` | Port server. |
| `password` | `str` atau `None` | `None` | Password. |
| `db` | `int` | `0` | Nomor database Redis. |
| `decode_responses` | `bool` | `False` | Jika `True`, client mengubah respons bytes menjadi teks. |
| `username` | `str` atau `None` | `None` | Username ACL. |

**Melempar:** `redis.exceptions.ConnectionError` jika server tidak bisa dihubungi. Exception lain dari client dicatat ke log lalu dilempar ulang.

**Atribut:**

| Atribut | Tipe | Keterangan |
|---|---|---|
| `client` | `redis.Redis` | Client Redis. |
| `index` | `redisvl.index.SearchIndex` atau `None` | Index aktif. `None` sampai `create_index` dipanggil. |
| `schema` | `dict` atau `None` | Skema yang terakhir diberikan ke `create_index`. |
| `host`, `port`, `username`, `password`, `db`, `decode_responses` | sesuai parameter | Nilai yang diberikan saat objek dibuat. |
| `logger` | `logging.Logger` | Logger modul. |

Method yang membutuhkan index melempar `ValueError` dengan pesan `Index not created. Call create_index() first.` jika `create_index` belum dipanggil. Method itu adalah `insert_data`, `hybrid_search`, `hybrid_search_rrf`, `vector_search`, `delete_index`, dan `get_info`.

### `check_requirements()`

Memeriksa versi Redis dan modul pencarian, mencetak hasilnya, lalu mengembalikannya.

**Mengembalikan:** `dict` dengan tiga kunci:

| Kunci | Tipe | Keterangan |
|---|---|---|
| `redis_version` | `str` atau `None` | Versi server Redis. |
| `search_module_version` | `int` atau `None` | Versi modul pencarian. `None` jika modul tidak ditemukan. |
| `vector_search_supported` | `bool` | `True` jika versi modul pencarian minimal `MIN_SEARCH_MODULE_VERSION`. |

Method ini tidak melempar exception. Jika pemeriksaan gagal, pesan error dicetak dan dict dikembalikan dengan nilai yang sudah terkumpul.

### `create_index(schema, overwrite=False, validate=True)`

Membuat index dari skema dan menjadikannya index aktif.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `schema` | `dict` | Wajib | Skema index dalam format RedisVL, berisi kunci `index` dan `fields`. |
| `overwrite` | `bool` | `False` | Jika `False`, index yang sudah ada dibiarkan. Jika `True`, index lama dihapus lalu dibuat ulang dari skema ini. |
| `validate` | `bool` | `True` | Diteruskan ke RedisVL sebagai `validate_on_load`. |

**Mengembalikan:** `redisvl.index.SearchIndex`.

**Melempar:** exception dari RedisVL jika skema tidak valid atau pembuatan gagal.

Contoh berikut membuat index dengan satu field teks dan satu field vektor:

```python
db.create_index({
    "index": {"name": "user_simple", "prefix": "user_simple_docs"},
    "fields": [
        {"name": "job", "type": "text"},
        {
            "name": "user_embedding",
            "type": "vector",
            "attrs": {
                "dims": 3,
                "distance_metric": "cosine",
                "algorithm": "flat",
                "datatype": "float32",
            },
        },
    ],
})
```

### `insert_data(data, batch_size=100)`

Menyimpan record ke index aktif per batch.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `data` | `list[dict]` | Wajib | Daftar record. Bentuk field vektornya ada di [Format vektor](#format-vektor). |
| `batch_size` | `int` | `100` | Jumlah record per batch. |

**Mengembalikan:** `list[str]` berisi key record yang tersimpan.

**Melempar:** `ValueError` jika index belum dibuat. Exception dari RedisVL jika penyimpanan gagal.

### `hybrid_search(text_query, vector_query, text_field_name, vector_field_name, text_scorer="BM25", return_fields=None, num_results=10, alpha=0.7)`

Mencari dengan teks dan vektor sekaligus, lalu menggabungkan kedua skor menjadi satu skor berbobot.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `text_query` | `str` | Wajib | Teks yang dicari. |
| `vector_query` | `Vector` | Wajib | Vektor query. |
| `text_field_name` | `str` | Wajib | Field teks yang dicari. |
| `vector_field_name` | `str` | Wajib | Field vektor yang dicari. |
| `text_scorer` | `str` | `"BM25"` | Metode skor teks, misalnya `BM25` atau `TFIDF`. |
| `return_fields` | `list[str]` atau `None` | `None` | Field yang dikembalikan. `None` diganti daftar kosong. |
| `num_results` | `int` | `10` | Jumlah hasil. |
| `alpha` | `float` | `0.7` | Bobot skor vektor: `0` berarti teks saja, `1` berarti vektor saja. |

**Mengembalikan:** hasil `SearchIndex.query`, berupa daftar hasil.

**Melempar:** `ValueError` jika index belum dibuat. Exception dari RedisVL jika pencarian gagal.

### `hybrid_search_rrf(text_query, vector_query, text_field_name, vector_field_name, text_scorer="BM25", return_fields=None, num_results=5, rrf_K=100)`

Menjalankan pencarian vektor dan pencarian teks secara terpisah, lalu menggabungkan peringkatnya dengan [`reciprocal_rank_fusion`](#reciprocal_rank_fusionranked_lists-k100).

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `text_query` | `str` | Wajib | Teks yang dicari. |
| `vector_query` | `Vector` | Wajib | Vektor query. |
| `text_field_name` | `str` | Wajib | Field teks yang dicari. Nilai field ini menjadi kunci penggabungan. |
| `vector_field_name` | `str` | Wajib | Field vektor yang dicari. |
| `text_scorer` | `str` | `"BM25"` | Metode skor teks. |
| `return_fields` | `list[str]` atau `None` | `None` | Field yang dikembalikan kedua pencarian. Harus memuat `text_field_name`. |
| `num_results` | `int` | `5` | Jumlah hasil dari setiap pencarian sebelum digabung. |
| `rrf_K` | `int` | `100` | Konstanta `K` di rumus RRF. |

**Mengembalikan:** tuple berisi daftar pasangan `(nilai field teks, skor)` urut dari skor tertinggi, dan daftar nilai field teks dalam urutan yang sama.

**Melempar:** `ValueError` jika index belum dibuat.

### `vector_search(vector_query, vector_field_name, return_fields=None, num_results=10)`

Mencari record yang vektornya paling mirip dengan vektor query.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `vector_query` | `Vector` | Wajib | Vektor query. |
| `vector_field_name` | `str` | Wajib | Field vektor yang dicari. |
| `return_fields` | `list[str]` atau `None` | `None` | Field yang dikembalikan. `None` diganti daftar kosong. |
| `num_results` | `int` | `10` | Jumlah hasil. |

**Mengembalikan:** hasil `SearchIndex.query`, berupa daftar hasil.

**Melempar:** `ValueError` jika index belum dibuat. Exception dari RedisVL jika pencarian gagal.

### `delete_index()`

Menghapus index aktif beserta semua record di dalamnya, lalu mengosongkan atribut `index` dan `schema`.

**Mengembalikan:** `None`.

**Melempar:** `ValueError` jika index belum dibuat.

### `get_info()`

Mengembalikan informasi index aktif dari Redis.

**Mengembalikan:** `dict`.

**Melempar:** `ValueError` jika index belum dibuat.

### `close()`

Menutup koneksi Redis.

**Mengembalikan:** `None`.

## `RedisHelper(config_path)`

Memuat file config, menyambung ke Redis, lalu membuat index dari config jika belum ada. Index yang sudah ada beserta datanya tidak diubah, karena helper selalu memanggil `create_index` dengan `overwrite=False`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `config_path` | `str` atau `Path` | Wajib | Path ke file config berekstensi `.yaml`, `.yml`, atau `.json`. |

**Melempar:**

- `FileNotFoundError` jika file config tidak ada.
- `ValueError` jika format file tidak didukung, file kosong, atau isinya tidak lolos validasi.
- `ConnectionError` bawaan Python dengan pesan `Failed to connect to Redis: ...` jika koneksi gagal, termasuk saat `connection.uri` tidak memuat nama host.

**Atribut:**

| Atribut | Tipe | Keterangan |
|---|---|---|
| `config` | [`RedisConfig`](#redisconfig) | Config yang sudah divalidasi. |
| `db` | `RedisVectorDB` | Objek di balik helper, untuk method yang tidak dibungkus helper. |
| `client` | `redis.Redis` | Client Redis yang sama dengan `db.client`. |
| `index` | `redisvl.index.SearchIndex` | Index yang dibuat dari config. |

### `insert(data, batch_size=100)`

Menyimpan satu record atau lebih ke index.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `data` | `dict` atau `list[dict]` | Wajib | Satu record atau daftar record. Field vektor harus sudah berupa vektor, sesuai [Format vektor](#format-vektor). |
| `batch_size` | `int` | `100` | Jumlah record per batch. |

**Mengembalikan:** `list[str]` berisi key record yang tersimpan.

### `hybrid_search(query_text, query_vector, limit=None)`

Mencari dengan teks dan vektor sekaligus, memakai pengaturan dari bagian `hybrid_search` di config.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `query_text` | `str` | Wajib | Teks yang dicari. |
| `query_vector` | `Vector` | Wajib | Vektor query. |
| `limit` | `int` atau `None` | `None` | Jumlah hasil. `None` berarti memakai `num_results` dari config. |

Field teks, field vektor, `text_scorer`, dan `alpha` diambil dari config. Jika `return_fields` di config kosong, helper memakai `["content"]`.

**Mengembalikan:** hasil `RedisVectorDB.hybrid_search`.

**Melempar:** `ValueError` dengan pesan `Hybrid search configuration not found in config file` jika config tidak punya bagian `hybrid_search`.

Contoh berikut mencari dengan teks dan vektor:

```python
hits = redis_helper.hybrid_search(
    query_text="ketentuan umum",
    query_vector=query_vector,
)
```

### `vector_search(query_vector, vector_field_name, limit=10, return_fields=None)`

Mencari record yang vektornya paling mirip pada salah satu field vektor index.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `query_vector` | `Vector` | Wajib | Vektor query. |
| `vector_field_name` | `str` | Wajib | Field vektor yang dicari. |
| `limit` | `int` | `10` | Jumlah hasil. |
| `return_fields` | `list[str]` atau `None` | `None` | Field yang dikembalikan. |

**Mengembalikan:** hasil `RedisVectorDB.vector_search`.

### `close()`

Menutup koneksi Redis.

**Mengembalikan:** `None`.

## Skema config

Lokasi: `zul.utilities.vector_DB.config.config_schema_redis`. File config dibaca menjadi model Pydantic yang bersarang seperti ini:

```text
RedisConfig
├── connection: ConnectionConfig
├── schema: SchemaConfig
│   ├── index: IndexConfig
│   └── fields: list[FieldConfig]
│       └── attrs: VectorAttrs
└── hybrid_search: HybridSearchConfig
```

File YAML dan JSON memakai struktur kunci yang sama.

### Enum pilihan nilai

Setiap enum memuat nilai yang diterima satu kunci config.

| Enum | Dipakai oleh | Nilai |
|---|---|---|
| `FieldTypeEnum` | `fields[].type` | `text`, `tag`, `numeric`, `vector`, `geo` |
| `VectorAlgorithm` | `attrs.algorithm` | `flat`, `hnsw` |
| `DistanceMetric` | `attrs.distance_metric` | `cosine`, `l2`, `ip` |
| `VectorDataType` | `attrs.datatype` | `float32`, `float64` |
| `StorageType` | `index.storage_type` | `hash`, `json` |
| `TextScorer` | `hybrid_search.text_scorer` | `TFIDF`, `TFIDF.DOCNORM`, `BM25`, `DISMAX`, `DOCSCORE`, `BM25STD` |

Nilai di file config dicocokkan tanpa membedakan huruf besar dan kecil, lalu disimpan dalam bentuk bakunya: huruf besar untuk `text_scorer`, huruf kecil untuk yang lain. Nilai di luar daftar ditolak dengan pesan `Invalid ...: NILAI. Must be one of [...]`.

### `ConnectionConfig`

Isi kunci `connection`.

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `uri` | `str` | `"http://localhost"` | Alamat server. Garis miring di akhir dibuang. |
| `port` | `int` | `6379` | Port server, antara 1 dan 65535. |
| `db_name` | `str` atau `None` | `None` | Nomor database Redis sebagai teks, misalnya `"0"`. |
| `password` | `str` atau `None` | `None` | Password. |
| `username` | `str` atau `None` | `None` | Username ACL. |

Model ini punya dua properti turunan:

| Properti | Tipe | Keterangan |
|---|---|---|
| `host` | `str` | `uri` tanpa awalan `http://`, `https://`, `redis://`, atau `rediss://`. Melempar `ValueError` jika hasilnya kosong. |
| `db` | `int` | `db_name` sebagai bilangan bulat. Bernilai `0` jika `db_name` kosong atau bukan angka. |

### `VectorAttrs`

Isi kunci `attrs` pada field bertipe `vector`.

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `dims` | `int` | Wajib | Dimensi vektor, lebih dari 0. |
| `distance_metric` | `str` | Wajib | `cosine`, `l2`, atau `ip`. |
| `algorithm` | `str` | Wajib | `flat` atau `hnsw`. |
| `datatype` | `str` | `"float32"` | `float32` atau `float64`. |
| `initial_cap` | `int` atau `None` | `None` | Kapasitas awal untuk HNSW, lebih dari 0. |
| `m` | `int` atau `None` | `None` | Jumlah koneksi untuk HNSW, lebih dari 0. |
| `ef_construction` | `int` atau `None` | `None` | Ukuran daftar kandidat saat membangun index HNSW, lebih dari 0. |
| `ef_runtime` | `int` atau `None` | `None` | Ukuran daftar kandidat saat pencarian, lebih dari 0. |

### `FieldConfig`

Satu entri di `schema.fields`.

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `name` | `str` | Wajib | Nama field. |
| `type` | `str` | Wajib | `text`, `tag`, `numeric`, `vector`, atau `geo`. |
| `attrs` | [`VectorAttrs`](#vectorattrs) atau `None` | `None` | Wajib untuk tipe `vector`, dilarang untuk tipe lain. |
| `sortable` | `bool` atau `None` | `False` | `True` agar hasil bisa diurutkan menurut field ini. |
| `no_index` | `bool` atau `None` | `False` | `True` agar field disimpan tanpa di-index. |

Pelanggaran aturan `attrs` ditolak dengan pesan `Vector fields must have 'attrs' defined` atau `Only vector fields can have 'attrs'`.

`to_redisvl_dict()` mengembalikan definisi field dalam format skema RedisVL. `sortable` dan `no_index` yang bernilai `True` dimasukkan ke `attrs` field itu.

### `IndexConfig`

Isi kunci `schema.index`.

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `name` | `str` | Wajib | Nama index. |
| `prefix` | `str` | Wajib | Awalan key untuk record di index ini. |
| `storage_type` | `str` | `"hash"` | `hash` atau `json`. |

### `SchemaConfig`

Isi kunci `schema`.

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `index` | [`IndexConfig`](#indexconfig) | Wajib | Pengaturan index. |
| `fields` | `list[FieldConfig]` | Wajib | Minimal satu field. Nama field harus unik, jika tidak ditolak dengan pesan `Field names must be unique`. |

`to_redisvl_dict()` mengembalikan skema dalam format yang diterima `SearchIndex.from_dict` milik RedisVL. `RedisHelper` memakai method ini saat membuat index.

### `HybridSearchConfig`

Isi kunci `hybrid_search`. Bagian ini opsional dan dipakai `RedisHelper.hybrid_search`.

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `text_field_name` | `str` | Wajib | Field teks yang dicari. |
| `vector_field_name` | `str` | Wajib | Field vektor yang dicari. |
| `text_scorer` | `str` | `"BM25"` | `TFIDF`, `TFIDF.DOCNORM`, `BM25`, `DISMAX`, `DOCSCORE`, atau `BM25STD`. |
| `alpha` | `float` | `0.5` | Bobot skor vektor, antara 0 dan 1: `0` berarti teks saja, `1` berarti vektor saja. |
| `num_results` | `int` | `10` | Jumlah hasil, lebih dari 0. |
| `return_fields` | `list[str]` atau `None` | `None` | Field yang dikembalikan. Jika kosong, `RedisHelper.hybrid_search` memakai `["content"]`. |

### `RedisConfig`

Akar file config.

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `connection` | [`ConnectionConfig`](#connectionconfig) | Wajib | Pengaturan koneksi. |
| `schema` | [`SchemaConfig`](#schemaconfig) | Wajib | Skema index. Di Python, bagian ini diakses sebagai `config.index_schema`. Kunci `index_schema` juga diterima di file config. |
| `hybrid_search` | [`HybridSearchConfig`](#hybridsearchconfig) atau `None` | `None` | Pengaturan `RedisHelper.hybrid_search`. |

## `ConfigLoader`

Memuat dan menyimpan config Redis. Lokasi: `zul.utilities.vector_DB.config.config_loader_redis`. Pembacaan file memakai fungsi `load_config` yang dijelaskan di [Referensi MilvusHelper](milvus.md).

### `ConfigLoader.load(config_path)`

Membaca file config Redis dan mengembalikannya sebagai `RedisConfig` yang sudah divalidasi.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `config_path` | `str` atau `Path` | Wajib | Path ke file `.yaml`, `.yml`, atau `.json`. |

**Mengembalikan:** `RedisConfig`.

**Melempar:**

- `FileNotFoundError` jika file tidak ada.
- `ValueError` jika format file tidak didukung, file kosong, atau isinya tidak lolos validasi. Pesan validasi diawali `Configuration validation failed for 'FILE':` dan memuat lokasi field yang salah.

### `ConfigLoader.save(config, output_path, format="yaml")`

Menulis sebuah `RedisConfig` ke file YAML atau JSON. Bagian skema ditulis dengan kunci `schema`, dan kunci yang bernilai `None` tidak ditulis.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `config` | `RedisConfig` | Wajib | Config yang disimpan. |
| `output_path` | `str` atau `Path` | Wajib | Path file tujuan. |
| `format` | `str` | `"yaml"` | `yaml`, `yml`, atau `json`. |

**Mengembalikan:** `None`.

**Melempar:** `ValueError` jika `format` tidak dikenal.

## `DEFAULT_REDIS_CONFIG`

Isi awal file config yang ditulis `zul install redis-helper`. Lokasi: `zul.commands.install`. Isi ini lolos validasi `RedisConfig`. Dalam format YAML, isinya seperti berikut:

```yaml title="redis_config.yaml"
connection:
  uri: http://localhost
  port: 6379
schema:
  index:
    name: my_index
    prefix: doc
    storage_type: hash
  fields:
  - name: content
    type: text
  - name: content_embedding_vector
    type: vector
    attrs:
      dims: 768
      distance_metric: cosine
      algorithm: flat
      datatype: float32
hybrid_search:
  text_field_name: content
  vector_field_name: content_embedding_vector
  text_scorer: BM25
  alpha: 0.5
  num_results: 10
  return_fields:
  - content
```

## Path impor lama

Modul `zul.utilities.redis_vector_helper` tetap bisa dipakai dan meneruskan ke lokasi sekarang. Dari path lama itu hanya `RedisVectorDB` dan `reciprocal_rank_fusion` yang bisa diimpor.

## Halaman terkait

- [Menyimpan dan mencari vektor di Redis](../panduan/memakai-redis.md) untuk langkah pemakaian.
- [Perintah zul](cli.md) untuk `zul install redis-helper` dan opsinya.
- [MilvusHelper](milvus.md) untuk helper vector database yang lain dan fungsi pembaca file config.
