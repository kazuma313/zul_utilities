# Menyimpan dan mencari vektor di Milvus

Halaman ini menunjukkan cara membuat collection [Milvus](https://milvus.io/) dari satu file config, lalu menyimpan, mencari, mengambil, dan menghapus data dengan `MilvusHelper`. Skema collection tercatat di file YAML atau JSON, dan helper membuatnya saat pertama kali dijalankan.

**Sebelum mulai:** kamu butuh Zul yang sudah terpasang (lihat [Memasang Zul](memasang-zul.md)) dan server Milvus yang bisa dihubungi dari komputermu.

## Menyiapkan helper dan file config

1. Pasang Zul dengan extra `milvus`:

    ```shell
    pip install "zul[milvus] @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

2. Tulis file config awal di folder proyek:

    ```shell
    zul install milvus-helper
    ```

    Perintah itu membuat `milvus_config.json`. Untuk format YAML, jalankan `zul install milvus-helper --config-name milvus.yaml`. Opsi lainnya ada di [Referensi perintah zul](../referensi/cli.md).

3. Buka file itu, lalu sesuaikan `connection` dengan server-mu dan `dim` dengan dimensi model embedding-mu:

    ```json title="milvus_config.json"
    {
        "connection": {
            "uri": "http://localhost",
            "port": 19530,
            "db_name": "default"
        },
        "collections": [
            {
                "collection_name": "my_collection",
                "shards_num": 2,
                "description": "My first collection",
                "milvus_schema": {
                    "auto_id": true,
                    "enable_dynamic_field": true,
                    "fields": [
                        {
                            "field_name": "id",
                            "datatype": "VARCHAR",
                            "max_length": 128,
                            "is_primary": true
                        },
                        {
                            "field_name": "embedding",
                            "datatype": "FLOAT_VECTOR",
                            "dim": 768
                        }
                    ],
                    "functions": []
                },
                "indexes": [
                    {
                        "field_name": "embedding",
                        "index_name": "emb_idx",
                        "index_type": "HNSW",
                        "metric_type": "COSINE",
                        "params": {
                            "M": 16,
                            "efConstruction": 200
                        }
                    }
                ]
            }
        ]
    }
    ```

4. Periksa file config tanpa menyambung ke server:

    ```python
    from zul.utilities.vector_DB.config.config_loader import ConfigLoader

    config = ConfigLoader.load("milvus_config.json")
    print([collection.collection_name for collection in config.collections])
    ```

    Jika file valid, kode itu mencetak nama collection di config:

    ```text
    ['my_collection']
    ```

    Jika ada yang salah, `ConfigLoader.load` melempar `ValueError` yang menyebut nama file dan field yang bermasalah.

5. Buat helper dari file config:

    ```python
    from zul.utilities.vector_DB.milvus_helper import MilvusHelper

    milvus = MilvusHelper(config_path="milvus_config.json")
    ```

    Saat dibuat, helper menyambung ke server, membuat database `db_name` jika belum ada, lalu membuat setiap collection di config yang belum ada beserta index-nya.

> [!NOTE]
> Collection yang sudah ada tidak diubah. Mengubah skema di file config tidak mengubah collection yang sudah dibuat. Jika skemanya harus berganti, hapus collection itu dulu dengan `drop_collection`, lalu buat helper lagi.

## Menyimpan data

1. Siapkan vektor untuk setiap record. Contoh ini memakai `FakeEmbeddingModel` supaya bisa dijalankan tanpa model embedding:

    ```python
    from zul.utilities.fake_embedding import FakeEmbeddingModel

    embedding = FakeEmbeddingModel(dimension=768, seed=42)

    first_vector = embedding.encode("dokumen pertama").flatten().tolist()
    second_vector = embedding.encode("dokumen kedua").flatten().tolist()
    ```

    Ganti `FakeEmbeddingModel` dengan model sungguhan saat kamu butuh hasil pencarian yang bermakna. Dimensi vektor harus sama dengan `dim` di config.

2. Simpan record dengan `insert`. Method ini menerima satu dict atau daftar dict, dan kunci setiap dict adalah nama field:

    ```python
    milvus.insert(
        "my_collection",
        [
            {"embedding": first_vector, "kategori": "peraturan"},
            {"embedding": second_vector, "kategori": "panduan"},
        ],
    )
    ```

    Config contoh memakai `auto_id: true`, jadi field `id` diisi Milvus. Karena `enable_dynamic_field: true`, kunci di luar skema seperti `kategori` ikut disimpan.

## Mencari vektor termirip

1. Ubah teks query menjadi vektor dengan model yang sama:

    ```python
    query_vector = embedding.encode("dokumen").flatten().tolist()
    ```

2. Cari vektor yang paling mirip dengan `search`:

    ```python
    hits = milvus.search(
        collection_name="my_collection",
        query_vectors=[query_vector],
        anns_field="embedding",
        limit=5,
        output_fields=["id"],
    )
    ```

    `query_vectors` berupa daftar, jadi kamu bisa mengirim beberapa query sekaligus. Hasilnya adalah satu daftar hasil untuk setiap query, dalam format `pymilvus`.

3. Untuk mempersempit pencarian, tambahkan argumen kata kunci lain. Argumen itu diteruskan ke `MilvusClient.search`. Contoh berikut menambah filter:

    ```python
    hits = milvus.search(
        collection_name="my_collection",
        query_vectors=[query_vector],
        anns_field="embedding",
        limit=5,
        filter='kategori == "peraturan"',
    )
    ```

## Mengambil data dengan filter

1. Untuk mengambil record tanpa pencarian vektor, panggil `query` dengan ekspresi filter:

    ```python
    rows = milvus.query(
        "my_collection",
        filter_expr='kategori == "peraturan"',
        output_fields=["id", "kategori"],
        limit=10,
    )
    ```

2. Untuk mengambil seluruh isi collection, panggil `get_all_data`. Method ini membaca per batch, jadi cocok untuk collection besar:

    ```python
    all_rows = milvus.get_all_data(
        "my_collection",
        output_fields=["id", "kategori"],
        batch_size=1024,
    )
    ```

    Kedua method mengembalikan daftar dict, satu dict per record.

## Menghapus data

1. Untuk menghapus record yang cocok dengan sebuah filter, panggil `delete`:

    ```python
    milvus.delete("my_collection", filter_expr='kategori == "panduan"')
    ```

2. Untuk menghapus satu collection, panggil `drop_collection`:

    ```python
    milvus.drop_collection("my_collection")
    ```

> [!WARNING]
> `drop_collection` menghapus collection beserta seluruh datanya dan tidak bisa dibatalkan.

## Menyiapkan collection untuk BM25

Milvus bisa membuat vektor sparse BM25 dari sebuah field teks. Bagian ini menyiapkan collection yang menyimpan vektor dense dan vektor sparse sekaligus, sebagai dasar hybrid search.

1. Tulis config dengan tiga hal: field teks yang memakai `enable_analyzer`, field bertipe `SPARSE_FLOAT_VECTOR`, dan satu entri `functions` yang menghubungkan keduanya:

    ```yaml title="milvus_hybrid.yaml"
    connection:
      uri: "http://localhost"
      port: 19530
      db_name: "default"
    collections:
      - collection_name: "documents"
        milvus_schema:
          auto_id: false
          fields:
            - {field_name: "id", datatype: "VARCHAR", max_length: 256, is_primary: true}
            - {field_name: "content", datatype: "VARCHAR", max_length: 65535, enable_analyzer: true}
            - {field_name: "dense_vector", datatype: "FLOAT_VECTOR", dim: 1024}
            - {field_name: "sparse_vector", datatype: "SPARSE_FLOAT_VECTOR"}
          functions:
            - name: "bm25_function"
              function_type: "BM25"
              input_field_names: ["content"]
              output_field_names: ["sparse_vector"]
        indexes:
          - field_name: "dense_vector"
            index_name: "dense_idx"
            index_type: "HNSW"
            metric_type: "COSINE"
            params: {M: 32, efConstruction: 256}
          - field_name: "sparse_vector"
            index_name: "sparse_idx"
            index_type: "SPARSE_INVERTED_INDEX"
            metric_type: "BM25"
    ```

2. Buat helper dari file itu supaya collection-nya dibuat:

    ```python
    milvus = MilvusHelper(config_path="milvus_hybrid.yaml")
    ```

3. Simpan data dengan mengisi `id`, `content`, dan `dense_vector` saja. Field `sparse_vector` diisi Milvus lewat function BM25:

    ```python
    dense_model = FakeEmbeddingModel(dimension=1024, seed=42)
    content = "Pasal 1 tentang ketentuan umum"

    milvus.insert(
        "documents",
        {
            "id": "doc-1",
            "content": content,
            "dense_vector": dense_model.encode(content).flatten().tolist(),
        },
    )
    ```

4. Jalankan pencarian gabungan lewat `milvus.client`, yaitu objek `pymilvus.MilvusClient`. `MilvusHelper` tidak menyediakan method hybrid search.

## Memeriksa hasilnya

Untuk memastikan collection sudah dibuat dan terisi, cetak daftar collection dan statistiknya:

```python
print(milvus.list_collections())
print(milvus.get_collection_stats("my_collection"))
```

Baris pertama mencetak daftar yang memuat nama collection dari config, misalnya `my_collection`. Baris kedua mencetak dict statistik dari Milvus. Kunci `row_count` di dict itu berisi jumlah baris.

Helper menulis log lewat modul `logging`, tetapi tidak mengatur ke mana log itu pergi. Untuk melihat log koneksi, pembuatan collection, dan setiap operasi, aktifkan logging di awal program:

```python
import logging

logging.basicConfig(level=logging.INFO)
```

## Lihat juga

- [Referensi MilvusHelper](../referensi/milvus.md) untuk semua method dan setiap kunci config.
- [Referensi perintah zul](../referensi/cli.md) untuk opsi `zul install milvus-helper`.
- [Menyimpan dan mencari vektor di Redis](memakai-redis.md) jika kamu memakai Redis sebagai vector database.
- [Memakai helper kecil](memakai-helper.md) untuk `FakeEmbeddingModel` dan pengukur waktu.
