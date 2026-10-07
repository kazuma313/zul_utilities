"""
Redis Vector Database helpers (RedisVL / RediSearch)

Gunanya:
    RedisVectorDB   koneksi + index + search, schema diberikan lewat kode
    RedisHelper     versi berbasis file config (.yaml / .json), seperti MilvusHelper

Cara pakai RedisHelper (`pip install "zul[redis]"`, config dari
`zul install redis-helper`):
    from zul.utilities.vector_DB.redis_helper import RedisHelper

    redis_helper = RedisHelper(config_path="redis_config.yaml")

    redis_helper.insert([
        {"content": "teks dokumen", "content_embedding_vector": vector_bytes},
    ])
    hits = redis_helper.hybrid_search(query_text="dokumen", query_vector=query_vector)
    hits = redis_helper.vector_search(query_vector, "content_embedding_vector", limit=5)

Cara pakai RedisVectorDB:
    from zul.utilities.vector_DB.redis_helper import RedisVectorDB

    db = RedisVectorDB(
        host="localhost", port=6379, password=os.getenv("REDIS_PASSWORD")
    )
    db.check_requirements()                  # versi Redis dan modul search
    db.create_index(schema, overwrite=False)
    db.insert_data(records)
    db.vector_search(query_vector, "embedding", return_fields=["content"])
    db.hybrid_search("teks", query_vector, "content", "embedding", alpha=0.7)
    db.hybrid_search_rrf("teks", query_vector, "content", "embedding")

Catatan penting:
    - Untuk storage `hash`, vektor harus dikirim sebagai bytes float32:
      `np.array(vector, dtype=np.float32).tobytes()`.
    - `create_index(overwrite=True)` menghapus index lama lalu membuatnya ulang.
      RedisHelper selalu memakai `overwrite=False`, jadi index yang sudah ada
      dibiarkan. `delete_index()` menghapus index beserta semua record-nya.
    - Contoh lengkap ada di blok `__main__` di akhir file.
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import ResponseError
from redisvl.index import SearchIndex
from redisvl.query import TextQuery, VectorQuery

try:
    from redisvl.query import AggregateHybridQuery
except ImportError:  # redisvl < 0.11 menamai query ini HybridQuery
    from redisvl.query import HybridQuery as AggregateHybridQuery

from .config.config_loader_redis import ConfigLoader
from .config.config_schema_redis import RedisConfig

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Syarat Server Redis
# --------------------------------------------------------------------------
#
# Pencarian vektor membutuhkan modul RediSearch versi 2.6.0 ke atas. Redis
# melaporkan versi modul sebagai bilangan bulat, sehingga 2.6.0 ditulis
# 20600. Modul itu bisa terdaftar dengan salah satu dari dua nama.
#


MIN_SEARCH_MODULE_VERSION = 20600
SEARCH_MODULE_NAMES = ("search", "RediSearch")

Vector = np.ndarray | bytes | list[float]

# --------------------------------------------------------------------------
# Fungsi Pembantu
# --------------------------------------------------------------------------


def _to_vector_bytes(vector: Vector) -> bytes:
    """Redis menyimpan vector sebagai bytes float32"""
    if isinstance(vector, bytes):
        return vector
    return np.asarray(vector, dtype=np.float32).tobytes()


def _decode(value: Any) -> Any:
    return value.decode() if isinstance(value, bytes) else value


def reciprocal_rank_fusion(
    *ranked_lists: list[Any], K: int = 100
) -> tuple[list[tuple[Any, float]], list[Any]]:
    """
    Fuse rank from multiple IR systems using Reciprocal Rank Fusion.

    Args:
        *ranked_lists: Ranked results from different IR system.
        K (int): A constant used in the RRF formula (default is 100).

    Returns:
        Tuple of list of (document, score) sorted by score, and the sorted documents
    """
    rrf_scores: dict[Any, float] = defaultdict(float)
    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            rrf_scores[item] += 1 / (rank + K)

    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_items, [item for item, _score in sorted_items]


# --------------------------------------------------------------------------
# Klien Vector Database
# --------------------------------------------------------------------------


class RedisVectorDB:
    """
    Class untuk mengelola koneksi dan operasi Redis Vector Database
    dengan RedisVL (RediSearch).
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str | None = None,
        db: int = 0,
        decode_responses: bool = False,
        username: str | None = None,
    ):
        """
        Inisialisasi koneksi Redis

        Args:
            host: Redis host
            port: Redis port
            password: Redis password
            db: Redis database number
            decode_responses: Whether to decode responses
            username: Redis username (ACL), opsional
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db = db
        self.decode_responses = decode_responses

        self.logger = logger

        # Redis client
        self.client: Redis | None = None

        # Search index
        self.index: SearchIndex | None = None
        self.schema: dict | None = None

        # Connect to Redis
        self._connect()

    def _connect(self) -> None:
        """Membuat koneksi ke Redis"""
        try:
            self.client = Redis(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                db=self.db,
                decode_responses=self.decode_responses,
            )

            # Test connection
            self.client.ping()
            self.logger.info(
                f"Successfully connected to Redis at {self.host}:{self.port}"
            )

        except RedisConnectionError as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during connection: {e}")
            raise

    def _require_index(self) -> SearchIndex:
        if not self.index:
            raise ValueError("Index not created. Call create_index() first.")
        return self.index

    def check_requirements(self) -> dict[str, Any]:
        """
        Mengecek requirements Redis (versi dan modul)

        Returns:
            Dictionary dengan informasi server dan modul:
            redis_version, search_module_version, vector_search_supported
        """
        requirements: dict[str, Any] = {
            "redis_version": None,
            "search_module_version": None,
            "vector_search_supported": False,
        }
        try:
            info = self.client.info()  # type: ignore
            redis_version = info.get("redis_version", "Unknown")  # type: ignore
            requirements["redis_version"] = _decode(redis_version)
            print(f"Versi Redis: {requirements['redis_version']}")

            module_version = self._search_module_version()
            requirements["search_module_version"] = module_version

            if module_version is None:
                print(
                    "Modul Search (RediSearch) tidak ditemukan. "
                    "Install Redis Stack atau load modul secara manual."
                )
            elif module_version >= MIN_SEARCH_MODULE_VERSION:
                requirements["vector_search_supported"] = True
                print(f"Modul Search ditemukan dengan versi: {module_version}")
                print(
                    "Requirement terpenuhi! "
                    "Anda bisa menggunakan fitur vector database."
                )
            else:
                print(f"Modul Search ditemukan dengan versi: {module_version}")
                print(
                    "Versi modul Search terlalu rendah. "
                    f"Harus >= {MIN_SEARCH_MODULE_VERSION}. "
                    "Upgrade atau tambahkan modul."
                )

        except RedisConnectionError as e:
            print(f"Error koneksi: {e}")
        except ResponseError as e:
            print(f"Error saat eksekusi perintah: {e}")
        except Exception as e:
            print(f"Error tak terduga: {e}")
        return requirements

    def _search_module_version(self) -> int | None:
        """Versi modul 'search' / 'RediSearch', atau None jika modul tidak ada"""
        modules = self.client.execute_command("MODULE LIST")  # type: ignore
        for module in modules:
            module = {_decode(key): _decode(value) for key, value in module.items()}
            if module.get("name") in SEARCH_MODULE_NAMES:
                return int(module.get("ver", 0))
        return None

    def create_index(
        self, schema: dict[str, Any], overwrite: bool = False, validate: bool = True
    ) -> SearchIndex:
        """
        Membuat index dengan schema yang diberikan

        Args:
            schema: Dictionary schema untuk index
            overwrite: Apakah akan overwrite index yang sudah ada
            validate: Validasi schema saat load

        Returns:
            SearchIndex object
        """
        try:
            self.schema = schema

            # Create index from schema
            self.index = SearchIndex.from_dict(
                schema, redis_client=self.client, validate_on_load=validate
            )

            # Create index
            self.index.create(overwrite=overwrite)

            self.logger.info(f"Index '{schema['index']['name']}' created successfully")
            return self.index

        except Exception as e:
            self.logger.error(f"Error creating index: {e}")
            raise

    def insert_data(
        self, data: list[dict[str, Any]], batch_size: int = 100
    ) -> list[str]:
        """
        Insert data ke index

        Args:
            data: List of dictionaries containing data to insert
            batch_size: Number of records to insert per batch

        Returns:
            List of keys yang telah di-insert
        """
        index = self._require_index()

        try:
            # Insert data in batches
            all_keys = []

            for i in range(0, len(data), batch_size):
                batch = data[i : i + batch_size]
                keys = index.load(batch)
                all_keys.extend(keys)

                self.logger.info(
                    f"Inserted batch {i//batch_size + 1}: {len(batch)} records"
                )

            self.logger.info(f"Total {len(all_keys)} records inserted successfully")
            return all_keys

        except Exception as e:
            self.logger.error(f"Error inserting data: {e}")
            raise

    def hybrid_search(
        self,
        text_query: str,
        vector_query: Vector,
        text_field_name: str,
        vector_field_name: str,
        text_scorer: str = "BM25",
        return_fields: list[str] | None = None,
        num_results: int = 10,
        alpha: float = 0.7,
    ) -> Any:
        """
        Melakukan hybrid search (text + vector)

        Args:
            text_query: Text query string
            vector_query: Vector embedding (numpy array, list of float, or bytes)
            text_field_name: Field name untuk text search
            vector_field_name: Field name untuk vector search
            text_scorer: Text scoring method (TFIDF, BM25, etc.)
            return_fields: Fields to return in results
            num_results: Number of results to return
            alpha: Bobot skor vector (0 = text saja, 1 = vector saja)

        Returns:
            Search results
        """
        index = self._require_index()

        try:
            query = AggregateHybridQuery(
                text=text_query,
                text_field_name=text_field_name,
                vector=_to_vector_bytes(vector_query),
                vector_field_name=vector_field_name,
                text_scorer=text_scorer,
                alpha=alpha,
                return_fields=return_fields or [],
                num_results=num_results,
            )

            results = index.query(query)

            self.logger.info(f"Hybrid search completed: {len(results)} results found")
            return results

        except Exception as e:
            self.logger.error(f"Error during hybrid search: {e}")
            raise

    def hybrid_search_rrf(
        self,
        text_query: str,
        vector_query: Vector,
        text_field_name: str,
        vector_field_name: str,
        text_scorer: str = "BM25",
        return_fields: list[str] | None = None,
        num_results: int = 5,
        rrf_K: int = 100,
    ):
        """
        Hybrid search dengan Reciprocal Rank Fusion: vector search dan full-text
        search dijalankan terpisah, lalu ranking keduanya digabung.

        Returns:
            Tuple of list of (text, score) sorted by RRF score, and the sorted texts
        """
        index = self._require_index()

        vector_result = index.query(
            VectorQuery(
                vector=_to_vector_bytes(vector_query),
                vector_field_name=vector_field_name,
                num_results=num_results,
                return_fields=return_fields,
            )
        )
        full_text_result = index.query(
            TextQuery(
                text=text_query,
                text_field_name=text_field_name,
                text_scorer=text_scorer,
                num_results=num_results,
                return_fields=return_fields,
            )
        )

        return reciprocal_rank_fusion(
            [res[text_field_name] for res in vector_result],
            [res[text_field_name] for res in full_text_result],
            K=rrf_K,
        )

    def vector_search(
        self,
        vector_query: Vector,
        vector_field_name: str,
        return_fields: list[str] | None = None,
        num_results: int = 10,
    ) -> Any:
        """
        Melakukan vector similarity search

        Args:
            vector_query: Vector embedding (numpy array, list of float, or bytes)
            vector_field_name: Field name untuk vector search
            return_fields: Fields to return in results
            num_results: Number of results to return

        Returns:
            Search results
        """
        index = self._require_index()

        try:
            query = VectorQuery(
                vector=_to_vector_bytes(vector_query),
                vector_field_name=vector_field_name,
                return_fields=return_fields or [],
                num_results=num_results,
            )

            results = index.query(query)

            self.logger.info(f"Vector search completed: {len(results)} results found")
            return results

        except Exception as e:
            self.logger.error(f"Error during vector search: {e}")
            raise

    def delete_index(self) -> None:
        """Delete index"""
        index = self._require_index()

        try:
            index.delete()
            self.logger.info("Index deleted successfully")
            self.index = None
            self.schema = None
        except Exception as e:
            self.logger.error(f"Error deleting index: {e}")
            raise

    def get_info(self) -> dict[str, Any]:
        """Get index info"""
        index = self._require_index()

        try:
            return index.info()
        except Exception as e:
            self.logger.error(f"Error getting index info: {e}")
            raise

    def close(self) -> None:
        """Close Redis connection"""
        if self.client:
            self.client.close()
            self.logger.info("Redis connection closed")


# --------------------------------------------------------------------------
# Helper Berbasis File Config
# --------------------------------------------------------------------------


class RedisHelper:
    """Redis vector helper with configuration-based design"""

    def __init__(self, config_path: str | Path) -> None:
        """
        Initialize RedisHelper with configuration from .yaml or .json file.
        The index defined in the config is created if it does not exist yet;
        an existing index (and its data) is left untouched.

        Args:
            config_path: Path to configuration file (.yaml or .json)
        """
        self.config: RedisConfig = ConfigLoader.load(config_path)

        conn = self.config.connection
        try:
            self.db = RedisVectorDB(
                host=conn.host,
                port=conn.port,
                username=conn.username,
                password=conn.password,
                db=conn.db,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {str(e)}") from e

        self.client = self.db.client
        self.index = self.db.create_index(
            self.config.index_schema.to_redisvl_dict(), overwrite=False
        )

    def insert(
        self, data: dict[str, Any] | list[dict[str, Any]], batch_size: int = 100
    ) -> list[str]:
        """
        Insert records into the index

        Args:
            data: Single dict or list of dicts. Vector fields must already be
                embedded (bytes float32 for hash storage).
            batch_size: Number of records to insert per batch

        Returns:
            List of inserted keys
        """
        if isinstance(data, dict):
            data = [data]
        return self.db.insert_data(data, batch_size=batch_size)

    def hybrid_search(
        self, query_text: str, query_vector: Vector, limit: int | None = None
    ):
        """
        Hybrid search (text + vector) using the `hybrid_search` section of the config

        Args:
            query_text: Text query string
            query_vector: Dense embedding of the query
            limit: Number of results; uses config default if not provided
        """
        hybrid_config = self.config.hybrid_search
        if hybrid_config is None:
            raise ValueError("Hybrid search configuration not found in config file")

        return self.db.hybrid_search(
            text_query=query_text,
            vector_query=query_vector,
            text_field_name=hybrid_config.text_field_name,
            vector_field_name=hybrid_config.vector_field_name,
            text_scorer=hybrid_config.text_scorer,
            alpha=hybrid_config.alpha,
            return_fields=hybrid_config.return_fields or ["content"],
            num_results=limit or hybrid_config.num_results,
        )

    def vector_search(
        self,
        query_vector: Vector,
        vector_field_name: str,
        limit: int = 10,
        return_fields: list[str] | None = None,
    ):
        """Vector similarity search on one of the index's vector fields"""
        return self.db.vector_search(
            vector_query=query_vector,
            vector_field_name=vector_field_name,
            return_fields=return_fields,
            num_results=limit,
        )

    def close(self) -> None:
        """Close Redis connection"""
        self.db.close()


# --------------------------------------------------------------------------
# Contoh Pemakaian
# --------------------------------------------------------------------------
#
# Contoh ini butuh server Redis Stack yang sedang berjalan. Host
# dan password-nya dibaca dari environment variable, sehingga
# tidak ada kredensial yang tertulis di dalam kode sumber.
#


if __name__ == "__main__":
    import os

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # 1. Koneksi ke Redis
    redis_db = RedisVectorDB(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD"),
    )

    # Check requirements
    requirements = redis_db.check_requirements()
    print(f"Requirements: {requirements}")

    # 2. Membuat index dari schema
    schema = {
        "index": {
            "name": "user_simple",
            "prefix": "user_simple_docs",
        },
        "fields": [
            {"name": "user", "type": "tag"},
            {"name": "credit_score", "type": "tag"},
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

    redis_db.create_index(schema, overwrite=True)

    # 3. Memasukkan data
    data = [
        {
            "user": "john",
            "age": 1,
            "job": "engineer",
            "credit_score": "high",
            "user_embedding": np.array([0.1, 0.1, 0.5], dtype=np.float32).tobytes(),
        },
        {
            "user": "mary",
            "age": 2,
            "job": "doctor",
            "credit_score": "low",
            "user_embedding": np.array([0.1, 0.1, 0.5], dtype=np.float32).tobytes(),
        },
        {
            "user": "joe",
            "age": 3,
            "job": "dentist",
            "credit_score": "medium",
            "user_embedding": np.array([0.9, 0.9, 0.1], dtype=np.float32).tobytes(),
        },
    ]

    keys = redis_db.insert_data(data)
    print(f"Inserted keys: {keys}")

    # 4. Pencarian vektor
    query_vector = np.array([0.1, 0.1, 0.5], dtype=np.float32)

    results = redis_db.vector_search(
        vector_query=query_vector,
        vector_field_name="user_embedding",
        return_fields=["user", "job", "age", "credit_score"],
        num_results=3,
    )

    print("\n=== Search Results ===")
    for doc in results:
        print(
            f"User: {doc['user']}, Job: {doc['job']}, "
            f"Age: {doc['age']}, Score: {doc['credit_score']}"
        )

    # Get index info
    info = redis_db.get_info()
    print(f"\nIndex info: {info}")

    # Close connection
    redis_db.close()
