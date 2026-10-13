"""
Embedding untuk setiap potongan dokumen, dan skema index Redis untuk menyimpannya.

Gunanya:
    `embed_records` menambahkan vektor embedding ke setiap record dari
    `chunks_to_records`. Vektor ditulis sebagai bytes float32 untuk Redis
    dengan storage hash, atau sebagai list float untuk Milvus. Durasi setiap
    panggilan embedding bisa dicatat untuk membandingkan latensi.
    `redis_schema` membuat skema RedisVL dengan satu field teks dan satu
    field vektor. Hanya butuh NumPy.

Cara pakai:
    from zul.evaluation.indexing import embed_records, redis_schema

    schema = redis_schema("recursive_qwen", prefix="recursive", dims=2560)
    db.create_index(schema, overwrite=False)       # index lama dibiarkan

    durations = []
    records = embed_records(chunks_to_records(chunks), ai, durations=durations)
    db.insert_data(records, batch_size=100)
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from typing import Any

import numpy as np

from ._progress import progress
from .retrievers import Embedder, embed_vector


def redis_schema(
    name: str,
    prefix: str,
    dims: int,
    *,
    algorithm: str = "hnsw",
    distance_metric: str = "cosine",
    text_field: str = "content",
    vector_field: str = "content_embedding_vector",
    storage: str = "hash",
) -> dict[str, Any]:
    """Skema RedisVL: satu field full-text dan satu field vektor float32."""
    return {
        "index": {"name": name, "prefix": prefix, "storage_type": storage},
        "fields": [
            {"name": text_field, "type": "text"},
            {
                "name": vector_field,
                "type": "vector",
                "attrs": {
                    "dims": dims,
                    "distance_metric": distance_metric,
                    "algorithm": algorithm,
                    "datatype": "float32",
                },
            },
        ],
    }


def to_vector_bytes(vector: Iterable[float]) -> bytes:
    """Vektor sebagai bytes float32, bentuk yang dibutuhkan Redis storage hash."""
    return np.asarray(list(vector), dtype=np.float32).tobytes()


def embed_records(
    records: Iterable[dict[str, Any]],
    embedder: Embedder,
    *,
    text_field: str = "content",
    vector_field: str = "content_embedding_vector",
    as_bytes: bool = True,
    durations: list[float] | None = None,
    show_progress: bool = True,
) -> list[dict[str, Any]]:
    """
    Salinan setiap record dengan vektor embedding dari kolom `text_field`.

    Args:
        records: Record dari `chunks_to_records`, atau dict lain berisi teks.
        embedder: Layanan dengan method `embed(text)`, misalnya `AIService`.
        text_field: Kolom teks yang di-embed.
        vector_field: Kolom tempat vektor ditulis.
        as_bytes: True untuk Redis (bytes float32), False untuk Milvus
            (list float).
        durations: Jika diberikan, durasi setiap panggilan embedding dalam
            detik ditambahkan ke list ini.
        show_progress: Tampilkan progress bar jika extra evaluation ada.
    """
    rows = list(records)
    embedded = []
    for row in progress(rows, "Embedding", show_progress):
        start = time.perf_counter()
        vector = embed_vector(embedder, row[text_field])
        if durations is not None:
            durations.append(time.perf_counter() - start)
        value = to_vector_bytes(vector) if as_bytes else vector
        embedded.append({**row, vector_field: value})
    return embedded
