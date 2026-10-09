"""
Adapter redis dan redisvl: koneksi Redis, index RediSearch, dan query vektor.

Gunanya:
    Satu-satunya file Zul yang mengimpor redis dan redisvl. Query vektor,
    teks, dan hybrid dibangun dari argumen biasa, dan hasilnya keluar
    sebagai list dict, jadi helper tidak perlu tahu nama kelas query
    redisvl. Perbedaan nama kelas antar versi redisvl juga diurus di
    sini. Butuh extra redis: `pip install "zul[redis]"`.

Cara pakai:
    from zul.adapters import redis as redis_adapter

    client = redis_adapter.create_client(host="localhost", port=6379)
    redis_adapter.ping(client)
    index = redis_adapter.index_from_schema(client, schema)
    redis_adapter.create_index(index, overwrite=False)
    keys = redis_adapter.load(index, records)
    hits = redis_adapter.vector_query(index, vector_bytes, "embedding")
    redis_adapter.close(client)

Client dari `create_client` adalah objek `redis.Redis`, dan index dari
`index_from_schema` adalah objek `redisvl.index.SearchIndex`. Di luar file
ini keduanya hanya diteruskan kembali ke fungsi di sini. Vektor dikirim
sebagai bytes float32, misalnya hasil `np.float32(vector).tobytes()`.
"""

from __future__ import annotations

from typing import Any

from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import ResponseError
from redisvl.index import SearchIndex
from redisvl.query import TextQuery, VectorQuery

# Mulai redisvl 0.11, query hybrid yang memakai FT.AGGREGATE diberi nama
# AggregateHybridQuery, sedangkan nama HybridQuery kini dipakai untuk
# query yang berbeda. Versi sebelumnya hanya mengenal HybridQuery.
try:
    from redisvl.query import AggregateHybridQuery
except ImportError:  # redisvl < 0.11
    from redisvl.query import HybridQuery as AggregateHybridQuery

# --------------------------------------------------------------------------
# Koneksi Dan Server
# --------------------------------------------------------------------------
#
# Error dari redis tetap dilempar apa adanya, supaya pemanggil yang sudah
# menangkap kelas error redis tidak berubah perilakunya. Dua fungsi is_*
# di bawah dipakai modul lain untuk membedakan jenis error tersebut.
#


def create_client(
    host: str = "localhost",
    port: int = 6379,
    username: str | None = None,
    password: str | None = None,
    db: int = 0,
    decode_responses: bool = False,
) -> Any:
    """Client Redis baru. Koneksi baru dibuka saat perintah pertama dikirim."""
    return Redis(
        host=host,
        port=port,
        username=username,
        password=password,
        db=db,
        decode_responses=decode_responses,
    )


def ping(client: Any) -> bool:
    """Kirim PING; error koneksi dilempar jika server tidak bisa dihubungi."""
    return client.ping()


def server_info(client: Any) -> dict[str, Any]:
    """Isi perintah INFO sebagai dict, misalnya kunci `redis_version`."""
    return client.info()


def module_list(client: Any) -> list[dict]:
    """Modul yang dimuat server, satu dict per modul dengan `name` dan `ver`.

    Kunci dan nilainya bisa berupa bytes, tergantung `decode_responses`.
    """
    return client.execute_command("MODULE LIST")


def close(client: Any) -> None:
    """Tutup koneksi client."""
    client.close()


def is_connection_error(error: BaseException) -> bool:
    """True jika `error` adalah error koneksi dari redis."""
    return isinstance(error, RedisConnectionError)


def is_command_error(error: BaseException) -> bool:
    """True jika `error` adalah error dari server saat menjalankan perintah."""
    return isinstance(error, ResponseError)


# --------------------------------------------------------------------------
# Index
# --------------------------------------------------------------------------


def index_from_schema(
    client: Any, schema: dict[str, Any], validate: bool = True
) -> Any:
    """Index dari schema dict redisvl, belum dibuat di server.

    Dengan `validate=True`, setiap record diperiksa terhadap schema saat
    disimpan lewat `load`.
    """
    return SearchIndex.from_dict(schema, redis_client=client, validate_on_load=validate)


def create_index(index: Any, overwrite: bool = False) -> None:
    """Buat index di server. Index yang sudah ada dibiarkan, kecuali `overwrite`.

    Dengan `overwrite=True`, index lama dihapus lalu dibuat ulang.
    """
    index.create(overwrite=overwrite)


def load(index: Any, records: list[dict[str, Any]]) -> list[str]:
    """Simpan record ke index; hasilnya key Redis untuk setiap record."""
    return index.load(records)


def index_info(index: Any) -> dict[str, Any]:
    """Informasi index dari perintah FT.INFO."""
    return index.info()


def delete_index(index: Any) -> None:
    """Hapus index beserta semua record di dalamnya."""
    index.delete()


# --------------------------------------------------------------------------
# Query
# --------------------------------------------------------------------------


def vector_query(
    index: Any,
    vector: bytes,
    vector_field_name: str,
    return_fields: list[str] | None = None,
    num_results: int = 10,
) -> list[dict[str, Any]]:
    """Record dengan vektor paling mirip dengan `vector`."""
    query = VectorQuery(
        vector=vector,
        vector_field_name=vector_field_name,
        return_fields=return_fields,
        num_results=num_results,
    )
    return index.query(query)


def text_query(
    index: Any,
    text: str,
    text_field_name: str,
    text_scorer: str = "BM25",
    return_fields: list[str] | None = None,
    num_results: int = 10,
) -> list[dict[str, Any]]:
    """Record yang paling cocok dengan `text` menurut full-text search."""
    query = TextQuery(
        text=text,
        text_field_name=text_field_name,
        text_scorer=text_scorer,
        num_results=num_results,
        return_fields=return_fields,
    )
    return index.query(query)


def hybrid_query(
    index: Any,
    text: str,
    text_field_name: str,
    vector: bytes,
    vector_field_name: str,
    text_scorer: str = "BM25",
    alpha: float = 0.7,
    return_fields: list[str] | None = None,
    num_results: int = 10,
) -> list[dict[str, Any]]:
    """Gabungan skor teks dan vektor; `alpha` adalah bobot skor vektor."""
    query = AggregateHybridQuery(
        text=text,
        text_field_name=text_field_name,
        vector=vector,
        vector_field_name=vector_field_name,
        text_scorer=text_scorer,
        alpha=alpha,
        return_fields=return_fields,
        num_results=num_results,
    )
    return index.query(query)
