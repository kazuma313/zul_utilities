from redisvl.query import HybridQuery, VectorQuery, TextQuery
from typing import List, Dict, Any, Optional, Union
from redis.exceptions import ConnectionError
from collections import defaultdict
from redisvl.index import SearchIndex
from redis import Redis
import numpy as np
import logging
import redis


class RedisVectorDB:
    """
    Class untuk mengelola koneksi dan operasi Redis Vector Database
    dengan RedisVL (RediSearch).
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        decode_responses: bool = False,
    ):
        """
        Inisialisasi koneksi Redis

        Args:
            host: Redis host
            port: Redis port
            password: Redis password
            db: Redis database number
            decode_responses: Whether to decode responses
        """
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.decode_responses = decode_responses

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Redis client
        self.client: Optional[Redis] = None

        # Search index
        self.index: Optional[SearchIndex] = None
        self.schema: Optional[Dict] = None

        # Connect to Redis
        self._connect()

    def _connect(self) -> None:
        """Membuat koneksi ke Redis"""
        try:
            redis_url = (
                f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
                if self.password
                else f"redis://{self.host}:{self.port}/{self.db}"
            )

            self.client = Redis.from_url(
                redis_url, decode_responses=self.decode_responses
            )

            # Test connection
            self.client.ping()
            self.logger.info(
                f"Successfully connected to Redis at {self.host}:{self.port}"
            )

        except ConnectionError as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during connection: {e}")
            raise

    def check_requirements(self):
        """
        Mengecek requirements Redis (versi dan modul)

        Returns:
            Dictionary dengan informasi server dan modul
        """
        try:
            info = self.client.info()  # type: ignore
            redis_version = info.get("redis_version", "Unknown")  # type: ignore
            print(f"Versi Redis: {redis_version}")

            # Get modules
            modules = self.client.execute_command("MODULE LIST")  # type: ignore
            print(modules)

            # Cari modul 'search' atau 'RediSearch'
            search_module = next(
                (mod for mod in modules if mod.get("name") in ["search", "RediSearch"]),
                None,
            )

            if search_module:
                module_version = search_module.get("ver", 0)
                print(f"Modul Search ditemukan dengan versi: {module_version}")
                if module_version >= 20600:
                    print(
                        "Requirement terpenuhi! Anda bisa menggunakan fitur vector database."
                    )
                else:
                    print(
                        "Versi modul Search terlalu rendah. Harus >= 20600. Upgrade atau tambahkan modul."
                    )
            else:
                print(
                    "Modul Search (RediSearch) tidak ditemukan. Instal Redis Stack atau load modul secara manual."
                )

        except redis.exceptions.ConnectionError as e:  # type: ignore
            print(f"Error koneksi: {e}")
        except redis.exceptions.ResponseError as e:  # type: ignore
            print(f"Error saat eksekusi perintah: {e}")
        except Exception as e:
            print(f"Error tak terduga: {e}")

    def create_index(
        self, schema: Dict[str, Any], overwrite: bool = False, validate: bool = True
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
        self, data: List[Dict[str, Any]], batch_size: int = 100
    ) -> List[str]:
        """
        Insert data ke index

        Args:
            data: List of dictionaries containing data to insert
            batch_size: Number of records to insert per batch

        Returns:
            List of keys yang telah di-insert
        """
        if not self.index:
            raise ValueError("Index not created. Call create_index() first.")

        try:
            # Insert data in batches
            all_keys = []

            for i in range(0, len(data), batch_size):
                batch = data[i : i + batch_size]
                keys = self.index.load(batch)
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
        vector_query: Union[np.ndarray, bytes],
        text_field_name: str,
        vector_field_name: str,
        text_scorer: str = "BM25",
        return_fields: Optional[List[str]] = None,
        num_results: int = 10,
    ) -> Any:
        """
        Melakukan hybrid search (text + vector)

        Args:
            text_query: Text query string
            vector_query: Vector embedding (numpy array or bytes)
            text_field_name: Field name untuk text search
            vector_field_name: Field name untuk vector search
            text_scorer: Text scoring method (TFIDF, BM25, etc.)
            return_fields: Fields to return in results
            num_results: Number of results to return

        Returns:
            Search results
        """
        if not self.index:
            raise ValueError("Index not created. Call create_index() first.")

        try:
            # Convert vector to bytes if numpy array
            if isinstance(vector_query, np.ndarray):
                vector_bytes = vector_query.astype(np.float32).tobytes()
            else:
                vector_bytes = vector_query

            # Create hybrid query
            query = HybridQuery(
                text=text_query,
                text_field_name=text_field_name,
                vector=vector_bytes,
                vector_field_name=vector_field_name,
                text_scorer=text_scorer,
                return_fields=return_fields or [],
                num_results=num_results,
            )

            # Execute query
            results = self.index.query(query)

            self.logger.info(f"Hybrid search completed: {len(results)} results found")
            return results

        except Exception as e:
            self.logger.error(f"Error during hybrid search: {e}")
            raise

    def hybrid_search_rrf(
        self,
        text_query: str,
        vector_query: Union[np.ndarray, bytes],
        text_field_name: str,
        vector_field_name: str,
        text_scorer: str = "BM25",
        return_fields: Optional[List[str]] = None,
        num_results: int = 5,
        rrf_K: int = 100,
    ):
        def reciprocal_rank_fusion(*list_of_list_ranks_system, K=100):
            """
            Fuse rank from multiple IR systems using Reciprocal Rank Fusion.

            Args:
            * list_of_list_ranks_system: Ranked results from different IR system.
            K (int): A constant used in the RRF formula (default is 100).

            Returns:
            Tuple of list of sorted documents by score and sorted documents
            """
            # Dictionary to store RRF mapping
            rrf_map = defaultdict(float)

            # Calculate RRF score for each result in each list
            for rank_list in list_of_list_ranks_system:
                for rank, item in enumerate(rank_list, 1):
                    rrf_map[item] += 1 / (rank + K)

            # Sort items based on their RRF scores in descending order
            sorted_items = sorted(rrf_map.items(), key=lambda x: x[1], reverse=True)

            # Return tuple of list of sorted documents by score and sorted documents
            return sorted_items, [item for item, score in sorted_items]

        vector = np.array(vector_query, dtype=np.float32).tobytes()
        query = VectorQuery(
            vector=vector,
            vector_field_name=vector_field_name,
            num_results=num_results,
            return_fields=return_fields,
        )

        vector_result = self.index.query(query)  # type: ignore
        vector_result_list = [res[text_field_name] for res in vector_result]

        query = TextQuery(
            text=text_query,
            text_field_name=text_field_name,
            text_scorer=text_scorer,
            num_results=num_results,
            return_fields=return_fields,
        )

        full_text_result = self.index.query(query)  # type: ignore
        full_text_result_list = [res[text_field_name] for res in full_text_result]

        return reciprocal_rank_fusion(
            vector_result_list, full_text_result_list, K=rrf_K
        )

    def vector_search(
        self,
        vector_query: Union[np.ndarray, bytes],
        vector_field_name: str,
        return_fields: Optional[List[str]] = None,
        num_results: int = 10,
    ) -> Any:
        """
        Melakukan vector similarity search

        Args:
            vector_query: Vector embedding (numpy array or bytes)
            vector_field_name: Field name untuk vector search
            return_fields: Fields to return in results
            num_results: Number of results to return

        Returns:
            Search results
        """
        if not self.index:
            raise ValueError("Index not created. Call create_index() first.")

        try:
            # Convert vector to bytes if numpy array
            if isinstance(vector_query, np.ndarray):
                vector_bytes = vector_query.astype(np.float32).tobytes()
            else:
                vector_bytes = vector_query

            # Create vector query
            query = VectorQuery(
                vector=vector_bytes,
                vector_field_name=vector_field_name,
                return_fields=return_fields or [],
                num_results=num_results,
            )

            # Execute query
            results = self.index.query(query)

            self.logger.info(f"Vector search completed: {len(results)} results found")
            return results

        except Exception as e:
            self.logger.error(f"Error during vector search: {e}")
            raise

    def delete_index(self) -> None:
        """Delete index"""
        if not self.index:
            raise ValueError("Index not created.")

        try:
            self.index.delete()
            self.logger.info("Index deleted successfully")
            self.index = None
            self.schema = None
        except Exception as e:
            self.logger.error(f"Error deleting index: {e}")
            raise

    def get_info(self) -> Dict[str, Any]:
        """Get index info"""
        if not self.index:
            raise ValueError("Index not created.")

        try:
            return self.index.info()
        except Exception as e:
            self.logger.error(f"Error getting index info: {e}")
            raise

    def close(self) -> None:
        """Close Redis connection"""
        if self.client:
            self.client.close()
            self.logger.info("Redis connection closed")


# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # 1. KONEKSI KE REDIS
    redis_db = RedisVectorDB(
        host="10.14.204.202", port=6006, password="1c0nd3v@2025!!!"
    )

    # Check requirements
    requirements = redis_db.check_requirements()
    print(f"Requirements: {requirements}")

    # 2. CREATE INDEX DENGAN SCHEMA
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

    # 3. INSERT DATA
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

    # 4. SEARCH (VECTOR SEARCH)
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
            f"User: {doc.user}, Job: {doc.job}, Age: {doc.age}, Score: {doc.credit_score}"
        )

    # Get index info
    info = redis_db.get_info()
    print(f"\nIndex info: {info}")

    # Close connection
    redis_db.close()
