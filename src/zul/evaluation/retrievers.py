"""
Retriever dengan satu antarmuka, apa pun tempat penyimpanannya.

Gunanya:
    Evaluasi hanya memanggil `retriever.retrieve(query, top_k)`, yang
    mengembalikan list teks konteks. Membandingkan Redis dengan Milvus,
    hybrid dengan RRF, atau dua index yang dipotong berbeda cukup dengan
    mengganti objek retriever-nya. Yang tersedia:

        RedisRetriever      index RedisVL: vector, text, hybrid, atau rrf
        MilvusRetriever     collection Milvus hybrid dari MilvusHybridStore
        FunctionRetriever   fungsi apa pun `(query, top_k) -> list[str]`

    Objek database dan layanan embedding diberikan dari luar, jadi modul ini
    hanya butuh library standar.

Cara pakai:
    from zul.evaluation.retrievers import FunctionRetriever, RedisRetriever

    retriever = RedisRetriever(db, ai, mode="rrf", rrf_k=100)
    contexts = retriever.retrieve("Apa itu mistika?", top_k=5)

    stub = FunctionRetriever(lambda query, k: ["konteks"] * k, name="stub")
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, Protocol, runtime_checkable

from zul.utilities.ranking import reciprocal_rank_fusion

RedisMode = Literal["vector", "text", "hybrid", "rrf"]
REDIS_MODES = ("vector", "text", "hybrid", "rrf")


@runtime_checkable
class Retriever(Protocol):
    """Antarmuka retriever: `name` untuk label hasil, dan method `retrieve`."""

    name: str

    def retrieve(self, query: str, top_k: int = 5) -> list[str]: ...


class Embedder(Protocol):
    """Layanan embedding; `AIService` di `zul.utilities.embedding_service` cocok."""

    def embed(self, text: str) -> Any: ...


def embed_vector(embedder: Embedder, text: str) -> list[float]:
    """Vektor embedding sebagai list float, dari objek berisi `vector` atau list."""
    result = embedder.embed(text)
    return [float(value) for value in getattr(result, "vector", result)]


def fuse(*ranked_lists: list[str], k: int = 100) -> list[str]:
    """Gabungkan beberapa daftar konteks, misalnya dari dua retriever, dengan RRF."""
    _scored, ranked = reciprocal_rank_fusion(*ranked_lists, K=k)
    return ranked


@dataclass
class FunctionRetriever:
    """Retriever dari fungsi `(query, top_k) -> list[str]`, misalnya API luar."""

    fn: Callable[[str, int], list[str]]
    name: str = "function"

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        return [str(text) for text in self.fn(query, top_k)][:top_k]


# --------------------------------------------------------------------------
# Redis
# --------------------------------------------------------------------------
#
# Mode rrf menjalankan pencarian vektor dan full-text secara terpisah,
# lalu menggabungkan peringkatnya. Mode hybrid membiarkan Redis yang
# menggabungkan skornya, dengan bobot alpha untuk skor vektor.
#


@dataclass
class RedisRetriever:
    """
    Retriever di atas `RedisVectorDB` yang index-nya sudah dipasang.

    Args:
        db: `RedisVectorDB` setelah `create_index(schema, overwrite=False)`.
        embedder: Layanan embedding untuk mengubah pertanyaan menjadi vektor.
        mode: "vector", "text" (BM25), "hybrid", atau "rrf".
        text_field: Nama field teks di index.
        vector_field: Nama field vektor di index.
        alpha: Bobot skor vektor di mode hybrid: 0 teks saja, 1 vektor saja.
        rrf_k: Konstanta K di mode rrf.
        text_scorer: Penilai full-text, misalnya "BM25" atau "TFIDF".
        name: Label hasil; bawaannya `redis-<mode>`.
    """

    db: Any
    embedder: Embedder
    mode: RedisMode = "hybrid"
    text_field: str = "content"
    vector_field: str = "content_embedding_vector"
    alpha: float = 0.7
    rrf_k: int = 100
    text_scorer: str = "BM25"
    name: str = ""

    def __post_init__(self) -> None:
        if self.mode not in REDIS_MODES:
            raise ValueError(
                f"Mode {self.mode!r} tidak dikenal: {', '.join(REDIS_MODES)}."
            )
        self.name = self.name or f"redis-{self.mode}"

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        fields = [self.text_field]
        if self.mode == "text":
            hits = self.db.text_search(
                query,
                self.text_field,
                text_scorer=self.text_scorer,
                return_fields=fields,
                num_results=top_k,
            )
            return [hit[self.text_field] for hit in hits]
        vector = embed_vector(self.embedder, query)
        if self.mode == "vector":
            hits = self.db.vector_search(
                vector, self.vector_field, return_fields=fields, num_results=top_k
            )
            return [hit[self.text_field] for hit in hits]
        if self.mode == "hybrid":
            hits = self.db.hybrid_search(
                query,
                vector,
                self.text_field,
                self.vector_field,
                text_scorer=self.text_scorer,
                return_fields=fields,
                num_results=top_k,
                alpha=self.alpha,
            )
            return [hit[self.text_field] for hit in hits]
        _scored, ranked = self.db.hybrid_search_rrf(
            query,
            vector,
            self.text_field,
            self.vector_field,
            text_scorer=self.text_scorer,
            return_fields=fields,
            num_results=top_k,
            rrf_K=self.rrf_k,
        )
        return list(ranked)[:top_k]


# --------------------------------------------------------------------------
# Milvus
# --------------------------------------------------------------------------


@dataclass
class MilvusRetriever:
    """Retriever hybrid di atas `MilvusHybridStore`: vektor dense dan BM25, lalu RRF."""

    store: Any
    embedder: Embedder
    collection: str
    text_field: str = "content"
    rrf_k: int = 100
    name: str = "milvus-hybrid"

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        results = self.store.hybrid_search(
            self.collection,
            query_text=query,
            query_vector=embed_vector(self.embedder, query),
            limit=top_k,
            output_fields=[self.text_field],
            rrf_k=self.rrf_k,
        )
        # Milvus mengembalikan satu daftar hasil untuk setiap query.
        hits = results[0] if results else []
        return [hit["entity"][self.text_field] for hit in hits][:top_k]
