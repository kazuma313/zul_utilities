"""
Collection Milvus untuk pencarian hybrid: vektor dense dan BM25 dari teksnya.

Gunanya:
    Milvus menghitung vektor sparse BM25 sendiri dari field teks, jadi yang
    perlu dikirim hanya teks dan vektor embedding-nya. Pencarian hybrid
    menjalankan pencarian vektor dan BM25, lalu menggabungkan peringkatnya
    dengan RRF. Skema dan index-nya sama untuk semua collection, supaya
    perbandingan antar cara memotong dokumen tidak tercampur dengan
    perbedaan skema. Semua pemanggilan pymilvus lewat `zul.adapters.milvus`.
    Butuh extra milvus: `pip install "zul[milvus]"`.

Cara pakai:
    from zul.evaluation.config import MilvusSettings
    from zul.evaluation.milvus_store import MilvusHybridStore

    store = MilvusHybridStore(MilvusSettings.from_env())
    store.ensure_collection("recursive_qwen", dims=2560)
    store.insert("recursive_qwen", records)       # vektor berupa list float
    hits = store.hybrid_search("recursive_qwen", "apa itu mistika?", vector)
"""

from __future__ import annotations

from typing import Any

from zul.adapters import milvus as milvus_adapter

from .config import MilvusSettings


class MilvusHybridStore:
    """Koneksi Milvus dan operasi collection hybrid di database dari pengaturan."""

    def __init__(self, settings: MilvusSettings | None = None) -> None:
        self.settings = settings or MilvusSettings.from_env()
        self.client = milvus_adapter.connect(self.settings.address)
        name = self.settings.db_name
        if name:
            if name not in milvus_adapter.list_databases(self.client):
                milvus_adapter.create_database(self.client, name)
            milvus_adapter.use_database(self.client, name)

    def ensure_collection(
        self,
        name: str,
        dims: int,
        *,
        text_field: str = "content",
        vector_field: str = "content_embedding_vector",
        sparse_field: str = "content_embedding_sparse",
    ) -> bool:
        """Buat collection jika belum ada; True jika baru dibuat.

        Primary key berupa INT64 auto-id, karena Milvus tidak bisa membuat
        id otomatis untuk VARCHAR.
        """
        if name in milvus_adapter.list_collections(self.client):
            return False
        fields = [
            {"field_name": "id", "datatype": "INT64", "is_primary": True},
            {
                "field_name": text_field,
                "datatype": "VARCHAR",
                "max_length": 65535,
                "enable_analyzer": True,
            },
            {"field_name": vector_field, "datatype": "FLOAT_VECTOR", "dim": dims},
            {"field_name": sparse_field, "datatype": "SPARSE_FLOAT_VECTOR"},
        ]
        functions = [
            {
                "name": "text_bm25",
                "input_field_names": [text_field],
                "output_field_names": [sparse_field],
                "function_type": "BM25",
            }
        ]
        indexes = [
            {"field_name": vector_field, "index_type": "HNSW", "metric_type": "COSINE"},
            {
                "field_name": sparse_field,
                "index_type": "SPARSE_INVERTED_INDEX",
                "metric_type": "BM25",
            },
        ]
        milvus_adapter.create_collection(
            self.client,
            name,
            fields,
            indexes,
            functions=functions,
            auto_id=True,
            enable_dynamic_field=True,
            description="collection hybrid untuk evaluasi retrieval",
        )
        return True

    def insert(
        self, name: str, records: list[dict[str, Any]], batch_size: int = 200
    ) -> int:
        """Masukkan record per batch; jumlah record yang dimasukkan.

        Vektor di setiap record harus berupa list float, misalnya hasil
        `embed_records(..., as_bytes=False)`.
        """
        for start in range(0, len(records), batch_size):
            batch = records[start : start + batch_size]
            milvus_adapter.insert(self.client, name, batch)
        return len(records)

    def hybrid_search(
        self,
        name: str,
        query_text: str,
        query_vector: list[float],
        *,
        limit: int = 5,
        output_fields: list[str] | None = None,
        rrf_k: int = 100,
        text_field: str = "content",
        vector_field: str = "content_embedding_vector",
        sparse_field: str = "content_embedding_sparse",
    ) -> list[list[dict]]:
        """Hasil hybrid untuk satu query: daftar berisi satu daftar hasil."""
        requests = [
            {
                "data": [query_vector],
                "anns_field": vector_field,
                "param": {},
                "limit": limit,
            },
            {
                "data": [query_text],
                "anns_field": sparse_field,
                "param": {"drop_ratio_search": 0.2},
                "limit": limit,
            },
        ]
        return milvus_adapter.hybrid_search(
            self.client,
            name,
            requests,
            limit=limit,
            output_fields=output_fields or [text_field],
            rrf_k=rrf_k,
        )

    def drop_collection(self, name: str) -> None:
        """Hapus collection beserta datanya, jika ada."""
        if name in milvus_adapter.list_collections(self.client):
            milvus_adapter.drop_collection(self.client, name)
