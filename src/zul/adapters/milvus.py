"""
Adapter pymilvus: koneksi, database, collection, dan operasi data Milvus.

Gunanya:
    Satu-satunya file Zul yang mengimpor pymilvus. Schema, field, function,
    dan index ditulis sebagai dict biasa dengan tipe berupa teks, misalnya
    "FLOAT_VECTOR" atau "BM25", lalu diubah menjadi objek pymilvus di sini.
    Butuh extra milvus: `pip install "zul[milvus]"`.

Cara pakai:
    from zul.adapters import milvus

    client = milvus.connect("http://localhost:19530")
    fields = [
        {"field_name": "id", "datatype": "INT64", "is_primary": True},
        {"field_name": "embedding", "datatype": "FLOAT_VECTOR", "dim": 8},
    ]
    index = {"field_name": "embedding", "index_type": "HNSW", "metric_type": "IP"}
    milvus.create_collection(client, "documents", fields, indexes=[index])

    milvus.insert(client, "documents", [{"id": 1, "embedding": vector}])
    rows = milvus.query_all(client, "documents")

Client dari `connect` adalah objek `pymilvus.MilvusClient`. Di luar file ini
client itu hanya diteruskan kembali ke fungsi di sini. Hasil insert, search,
query, dan delete dikembalikan apa adanya dari pymilvus: dict dan list
berisi dict, jadi bisa dibaca seperti tipe Python biasa.
"""

from __future__ import annotations

from typing import Any

from pymilvus import DataType, Function, FunctionType, MilvusClient

# --------------------------------------------------------------------------
# Pemetaan Tipe Data
# --------------------------------------------------------------------------
#
# File config menulis tipe data sebagai teks, sedangkan Milvus meminta
# anggota enum DataType. Tabel ini menghubungkan keduanya, dan tipe
# yang di luar daftar ini ditolak dengan pesan error yang jelas.
#

DATATYPES = {
    "VARCHAR": DataType.VARCHAR,
    "INT64": DataType.INT64,
    "FLOAT": DataType.FLOAT,
    "FLOAT_VECTOR": DataType.FLOAT_VECTOR,
    "SPARSE_FLOAT_VECTOR": DataType.SPARSE_FLOAT_VECTOR,
    "BOOL": DataType.BOOL,
    "JSON": DataType.JSON,
}


def _datatype(name: str) -> DataType:
    """Anggota DataType untuk nama tipe, tanpa membedakan huruf besar-kecil."""
    try:
        return DATATYPES[name.upper()]
    except KeyError:
        raise ValueError(
            f"Unsupported datatype: {name}. Use one of {sorted(DATATYPES)}"
        ) from None


def _function_type(name: str) -> FunctionType:
    """Anggota FunctionType untuk nama function, misalnya "BM25"."""
    try:
        return FunctionType[name.upper()]
    except KeyError:
        raise ValueError(f"Unsupported function type: {name}") from None


# --------------------------------------------------------------------------
# Koneksi Dan Database
# --------------------------------------------------------------------------


def connect(uri: str, user: str | None = None, password: str | None = None) -> Any:
    """Client Milvus baru; `user` dan `password` hanya dikirim jika diisi."""
    params = {"uri": uri}
    if user:
        params["user"] = user
    if password:
        params["password"] = password
    return MilvusClient(**params)


def list_databases(client: Any) -> list[str]:
    """Nama semua database di server."""
    return client.list_databases()


def create_database(client: Any, name: str) -> None:
    """Buat database baru bernama `name`."""
    client.create_database(db_name=name)


def use_database(client: Any, name: str) -> None:
    """Pakai database `name` untuk semua operasi berikutnya di client ini."""
    client.use_database(db_name=name)


# --------------------------------------------------------------------------
# Collection
# --------------------------------------------------------------------------
#
# Setiap field adalah dict argumen add_field milik pymilvus, dengan nilai
# `datatype` berupa teks. Function dan index juga ditulis sebagai dict,
# dan hanya teks tipe di dalamnya yang diubah menjadi enum pymilvus.
#


def list_collections(client: Any) -> list[str]:
    """Nama semua collection di database yang sedang dipakai."""
    return client.list_collections()


def create_collection(
    client: Any,
    name: str,
    fields: list[dict[str, Any]],
    indexes: list[dict[str, Any]],
    functions: list[dict[str, Any]] | None = None,
    shards_num: int = 1,
    auto_id: bool = False,
    enable_dynamic_field: bool = False,
    description: str = "",
) -> None:
    """Buat collection dari field, function, dan index berbentuk dict.

    Kunci `datatype` di field dan `function_type` di function berupa teks.
    Kunci lain diteruskan apa adanya ke `add_field`, `Function`, dan
    `add_index` milik pymilvus.

    Raises:
        ValueError: `datatype` atau `function_type` tidak dikenal.
    """
    schema = client.create_schema(
        auto_id=auto_id,
        enable_dynamic_field=enable_dynamic_field,
        description=description,
    )
    for field in fields:
        schema.add_field(**{**field, "datatype": _datatype(field["datatype"])})

    for function in functions or []:
        function_type = _function_type(function["function_type"])
        schema.add_function(Function(**{**function, "function_type": function_type}))

    index_params = client.prepare_index_params()
    for index in indexes:
        index_params.add_index(**index)

    client.create_collection(
        collection_name=name,
        schema=schema,
        index_params=index_params,
        shards_num=shards_num,
    )


def drop_collection(client: Any, name: str) -> None:
    """Hapus collection beserta semua datanya."""
    client.drop_collection(collection_name=name)


def collection_stats(client: Any, name: str) -> dict:
    """Statistik collection; kunci `row_count` berisi jumlah baris."""
    return client.get_collection_stats(collection_name=name)


# --------------------------------------------------------------------------
# Operasi Data
# --------------------------------------------------------------------------


def insert(client: Any, collection_name: str, rows: list[dict]) -> dict:
    """Simpan baris ke collection; hasilnya berisi `insert_count` dan `ids`."""
    return client.insert(collection_name=collection_name, data=rows)


def search(
    client: Any,
    collection_name: str,
    vectors: list[list[float]],
    anns_field: str,
    limit: int,
    output_fields: list[str],
    **options: Any,
) -> list[list[dict]]:
    """Cari vektor terdekat; satu daftar hasil untuk setiap vektor query.

    `options` diteruskan apa adanya ke `MilvusClient.search`, misalnya
    `filter` atau `search_params`.
    """
    return client.search(
        collection_name=collection_name,
        data=vectors,
        anns_field=anns_field,
        limit=limit,
        output_fields=output_fields,
        **options,
    )


def query(
    client: Any,
    collection_name: str,
    filter_expr: str,
    output_fields: list[str],
    limit: int | None = None,
) -> list[dict]:
    """Baris yang cocok dengan ekspresi filter, misalnya 'id == "doc-1"'."""
    return client.query(
        collection_name=collection_name,
        filter=filter_expr,
        output_fields=output_fields,
        limit=limit,
    )


def query_all(
    client: Any,
    collection_name: str,
    filter_expr: str = "",
    output_fields: list[str] | None = None,
    batch_size: int = 1024,
) -> list[dict]:
    """Semua baris yang cocok, dibaca per batch dengan query iterator.

    Iterator selalu ditutup, juga saat terjadi error di tengah jalan.
    """
    rows: list[dict] = []
    iterator = client.query_iterator(
        collection_name=collection_name,
        batch_size=batch_size,
        filter=filter_expr,
        output_fields=output_fields or ["*"],
    )
    try:
        while True:
            batch = iterator.next()
            if not batch:
                break
            rows.extend(batch)
    finally:
        iterator.close()
    return rows


def delete(client: Any, collection_name: str, filter_expr: str) -> dict:
    """Hapus baris yang cocok dengan ekspresi filter."""
    return client.delete(collection_name=collection_name, filter=filter_expr)
