# Menyimpan dan mencari vektor di Redis

Redis bisa dipakai sebagai vector database lewat [RedisVL](https://docs.redisvl.com/): membuat index, menyimpan record, lalu mencari dengan vektor, teks, atau gabungan keduanya. Zul menyediakan dua kelas untuk itu. `RedisHelper` membaca skema dari file config, cocok untuk aplikasi. `RedisVectorDB` menerima skema lewat kode, cocok untuk notebook dan eksperimen.

**Sebelum mulai:** kamu butuh Zul yang sudah terpasang ([Memasang Zul](memasang-zul.md)) dan server Redis yang punya modul pencarian (RediSearch) versi 2.6 atau lebih baru, seperti yang ada di Redis Stack.

## Menyiapkan RedisHelper dari file config

1. Pasang Zul dengan extra `redis`:

    ```shell
    pip install "zul[redis] @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

2. Tulis file config awal di folder proyek:

    ```shell
    zul install redis-helper
    ```

    Perintah itu membuat `redis_config.yaml`. Opsinya ada di [Referensi perintah zul](../referensi/cli.md).

3. Buka file itu, lalu sesuaikan `connection` dengan server-mu dan `dims` dengan dimensi model embedding-mu:

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

    Jika server-mu memakai password, tambahkan kunci `password` di bawah `connection`. Jangan menyimpan file berisi password ke Git.

4. Periksa file config tanpa menyambung ke server:

    ```python
    from zul.utilities.vector_DB.config.config_loader_redis import ConfigLoader

    config = ConfigLoader.load("redis_config.yaml")
    print(config.connection.host, config.index_schema.index.name)
    ```

    Jika file valid, kode itu mencetak host dan nama index:

    ```text
    localhost my_index
    ```

5. Buat helper dari file config:

    ```python
    from zul.utilities.vector_DB.redis_helper import RedisHelper

    redis_helper = RedisHelper(config_path="redis_config.yaml")
    ```

    Helper menyambung ke Redis dan membuat index jika belum ada. Index yang sudah ada beserta datanya tidak disentuh.

## Menyimpan dan mencari dengan RedisHelper

1. Ubah teks menjadi vektor, lalu ubah vektor itu menjadi bytes `float32`. Untuk storage `hash`, vektor di record yang disimpan harus berbentuk bytes. Contoh ini memakai `FakeEmbeddingModel` supaya bisa dijalankan tanpa model embedding:

    ```python
    import numpy as np

    from zul.utilities.fake_embedding import FakeEmbeddingModel

    embedding = FakeEmbeddingModel(dimension=768, seed=42)


    def to_bytes(text: str) -> bytes:
        return np.asarray(embedding.encode(text).flatten(), dtype=np.float32).tobytes()
    ```

2. Simpan record dengan `insert`. Method ini menerima satu dict atau daftar dict, dan mengembalikan daftar key yang tersimpan:

    ```python
    keys = redis_helper.insert([
        {
            "content": "Pasal 1 tentang ketentuan umum",
            "content_embedding_vector": to_bytes("Pasal 1 tentang ketentuan umum"),
        },
        {
            "content": "Pasal 2 tentang hak dan kewajiban",
            "content_embedding_vector": to_bytes("Pasal 2 tentang hak dan kewajiban"),
        },
    ])
    ```

3. Cari dengan teks dan vektor sekaligus. Pengaturan pencarian diambil dari bagian `hybrid_search` di config:

    ```python
    query_vector = embedding.encode("ketentuan umum").flatten()

    hits = redis_helper.hybrid_search(
        query_text="ketentuan umum",
        query_vector=query_vector,
    )

    for hit in hits:
        print(hit["content"])
    ```

    Vektor query boleh berupa `numpy.ndarray`, daftar float, atau bytes. Helper mengubahnya ke bytes `float32`.

4. Untuk pencarian vektor saja, panggil `vector_search` dan sebut field vektornya:

    ```python
    hits = redis_helper.vector_search(
        query_vector,
        vector_field_name="content_embedding_vector",
        limit=5,
        return_fields=["content"],
    )
    ```

> [!NOTE]
> Kunci `alpha` di bagian `hybrid_search` adalah bobot skor vektor: `0` berarti hanya skor teks yang dipakai, `1` berarti hanya skor vektor.

## Memakai RedisVectorDB tanpa file config

1. Buat koneksi dengan host dan port. Baca password dari environment, jangan menulisnya di kode:

    ```python
    import os

    from zul.utilities.vector_DB.redis_helper import RedisVectorDB

    db = RedisVectorDB(
        host="localhost",
        port=6379,
        password=os.getenv("REDIS_PASSWORD"),
    )
    ```

2. Periksa apakah server mendukung pencarian vektor:

    ```python
    requirements = db.check_requirements()
    print(requirements["vector_search_supported"])
    ```

    `check_requirements` mencetak versi Redis dan versi modul pencarian, lalu mengembalikannya sebagai dict. Jika `vector_search_supported` bernilai `False`, server belum punya modul pencarian versi 2.6 atau lebih baru.

3. Buat index dari skema berupa dict dalam format RedisVL:

    ```python
    schema = {
        "index": {"name": "user_simple", "prefix": "user_simple_docs"},
        "fields": [
            {"name": "user", "type": "tag"},
            {"name": "job", "type": "text"},
            {"name": "age", "type": "numeric"},
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
    }

    db.create_index(schema)
    ```

    Jika index dengan nama itu sudah ada, `create_index(schema)` membiarkannya. Untuk mengganti skema, panggil `create_index(schema, overwrite=True)`, yang menghapus index lama lalu membuatnya ulang.

4. Simpan data dengan `insert_data`, yang mengirimnya per batch:

    ```python
    import numpy as np

    keys = db.insert_data([
        {
            "user": "john",
            "job": "engineer",
            "age": 1,
            "user_embedding": np.array([0.1, 0.1, 0.5], dtype=np.float32).tobytes(),
        },
        {
            "user": "joe",
            "job": "dentist",
            "age": 3,
            "user_embedding": np.array([0.9, 0.9, 0.1], dtype=np.float32).tobytes(),
        },
    ])
    ```

5. Cari vektor termirip dengan `vector_search`:

    ```python
    query_vector = np.array([0.1, 0.1, 0.5], dtype=np.float32)

    hits = db.vector_search(
        vector_query=query_vector,
        vector_field_name="user_embedding",
        return_fields=["user", "job"],
        num_results=2,
    )

    for hit in hits:
        print(hit["user"], hit["job"])
    ```

6. Setelah selesai, tutup koneksi:

    ```python
    db.close()
    ```

> [!WARNING]
> `db.delete_index()` menghapus index beserta semua record di dalamnya dan tidak bisa dibatalkan.

## Menggabungkan pencarian teks dan vektor

Bagian ini melanjutkan contoh `RedisVectorDB` di atas, sebelum koneksi ditutup. Ada dua cara menggabungkan hasil, pilih salah satu.

1. Untuk satu skor gabungan berbobot, panggil `hybrid_search` dan atur `alpha`, yaitu bobot skor vektor antara `0` (teks saja) dan `1` (vektor saja):

    ```python
    hits = db.hybrid_search(
        text_query="engineer",
        vector_query=query_vector,
        text_field_name="job",
        vector_field_name="user_embedding",
        text_scorer="BM25",
        alpha=0.7,
        return_fields=["user", "job"],
        num_results=5,
    )
    ```

2. Untuk menggabungkan peringkat, bukan skor, panggil `hybrid_search_rrf`. Method ini menjalankan pencarian vektor dan pencarian teks secara terpisah, lalu menggabungkan urutannya dengan Reciprocal Rank Fusion, sehingga hasilnya tidak bergantung pada skala skor masing-masing pencarian:

    ```python
    scored, ranked = db.hybrid_search_rrf(
        text_query="engineer",
        vector_query=query_vector,
        text_field_name="job",
        vector_field_name="user_embedding",
        return_fields=["job"],
        num_results=5,
    )

    print(ranked)
    ```

    `ranked` berisi nilai field teks, urut dari yang paling relevan. `return_fields` wajib memuat field teks, karena hasil digabung berdasarkan nilai field itu.

## Memeriksa hasilnya

Untuk memastikan record tersimpan, cetak jumlah key yang dikembalikan `insert` atau `insert_data`:

```python
print(len(keys))
```

Untuk contoh di halaman ini, kode itu mencetak jumlah record yang kamu kirim:

```text
2
```

Untuk melihat keadaan index di server, cetak informasinya:

```python
print(redis_helper.db.get_info())
```

`get_info` mengembalikan dict informasi index dari Redis. Jika kamu memakai `RedisVectorDB` langsung, panggil `db.get_info()`.

## Halaman terkait

- [Referensi RedisHelper dan RedisVectorDB](../referensi/redis.md) untuk semua method, format vektor, dan setiap kunci config.
- [Referensi perintah zul](../referensi/cli.md) untuk opsi `zul install redis-helper`.
- [Menyimpan dan mencari vektor di Milvus](memakai-milvus.md) jika kamu memakai Milvus sebagai vector database.
- [Memakai helper kecil](memakai-helper.md) untuk `FakeEmbeddingModel` dan pengukur waktu.
