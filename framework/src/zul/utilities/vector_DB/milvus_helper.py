"""
Refined Milvus Helper - Simple and focused

Gunanya:
    Membuat koneksi, database, collection, dan index Milvus dari satu file
    config, lalu menyediakan operasi insert / search / query / delete.
    Collection yang sudah ada tidak diubah.

Cara pakai (`pip install "zul[milvus]"`, config dari `zul install milvus-helper`):
    from zul.utilities.vector_DB.milvus_helper import MilvusHelper

    milvus = MilvusHelper(config_path="milvus_config.json")

    milvus.insert("my_collection", [{"id": "doc-1", "embedding": vector}])

    hits = milvus.search(
        collection_name="my_collection",
        query_vectors=[query_vector],
        anns_field="embedding",
        limit=5,
        output_fields=["id"],
    )
    rows = milvus.query("my_collection", filter_expr='id == "doc-1"')
    all_rows = milvus.get_all_data("my_collection")
    milvus.delete("my_collection", filter_expr='id == "doc-1"')

Operasi di luar helper ini bisa dilakukan lewat `milvus.client`
(objek `pymilvus.MilvusClient`). Helper ini sendiri tidak mengimpor
pymilvus; semua pemanggilannya lewat `zul.adapters.milvus`.

Modul ini tidak mengatur logging. Untuk melihat log-nya:
    logging.basicConfig(level=logging.INFO)
"""

import logging
from pathlib import Path
from typing import Any

from zul.adapters import milvus

from .config.config_loader import ConfigLoader

# Kode library tidak mengatur logging sendiri. Program pemakainya
# yang menentukan ke mana catatan ini ditulis, misalnya lewat
# logging.basicConfig ketika aplikasi itu mulai berjalan.
logger = logging.getLogger(__name__)


class MilvusHelper:
    """Simplified Milvus helper with configuration-based design"""

    def __init__(self, config_path: str | Path):
        """
        Initialize Milvus helper from configuration file

        Args:
            config_path: Path to YAML or JSON configuration file
        """
        self.config = ConfigLoader.load(config_path)
        self._initialize_client()
        self._setup_database()
        self._create_collections()

        logger.info("MilvusHelper initialized successfully")

    # ----------------------------------------------------------------------
    # Persiapan Koneksi dan Collection
    # ----------------------------------------------------------------------

    def _initialize_client(self):
        """Initialize Milvus client"""
        try:
            conn = self.config.connection
            uri = f"{conn.uri}:{conn.port}"

            self.client = milvus.connect(uri, user=conn.user, password=conn.password)
            logger.info(f"Connected to Milvus at {uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    def _setup_database(self):
        """Setup database"""
        try:
            db_name = self.config.connection.db_name
            if not db_name:
                return

            existing_dbs = milvus.list_databases(self.client)

            if db_name not in existing_dbs:
                milvus.create_database(self.client, db_name)
                logger.info(f"Created database: {db_name}")

            milvus.use_database(self.client, db_name)
            logger.info(f"Using database: {db_name}")
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise

    def _create_collections(self):
        """Create all collections defined in configuration"""
        existing = milvus.list_collections(self.client)

        for col_config in self.config.collections:
            if col_config.collection_name in existing:  # type: ignore
                logger.info(f"Collection '{col_config.collection_name}' already exists")
                continue

            try:
                self._create_single_collection(col_config)
                logger.info(f"Created collection: {col_config.collection_name}")
            except Exception as e:
                logger.error(
                    f"Failed to create collection '{col_config.collection_name}': {e}"
                )
                raise

    def _create_single_collection(self, col_config):
        """Create a single collection"""
        schema = col_config.milvus_schema
        milvus.create_collection(
            self.client,
            col_config.collection_name,
            fields=[self._field_params(field) for field in schema.fields],
            functions=[
                {
                    "name": func.name,
                    "input_field_names": func.input_field_names,
                    "output_field_names": func.output_field_names,
                    "function_type": func.function_type,
                }
                for func in schema.functions or []
            ],
            indexes=[self._index_params(idx) for idx in col_config.indexes],
            shards_num=col_config.shards_num,
            auto_id=schema.auto_id,
            enable_dynamic_field=schema.enable_dynamic_field,
            description=schema.description or "",
        )

    @staticmethod
    def _field_params(field) -> dict[str, Any]:
        """Argumen satu field; nilai yang kosong di config tidak dikirim."""
        params = {
            "field_name": field.field_name,
            "datatype": field.datatype,
            "is_primary": field.is_primary,
        }
        if field.auto_id:
            params["auto_id"] = field.auto_id
        if field.max_length:
            params["max_length"] = field.max_length
        if field.dim:
            params["dim"] = field.dim
        if field.description:
            params["description"] = field.description
        if field.enable_analyzer:
            params["enable_analyzer"] = field.enable_analyzer
        return params

    @staticmethod
    def _index_params(idx) -> dict[str, Any]:
        """Argumen satu index; `params` hanya dikirim jika diisi."""
        params = {
            "field_name": idx.field_name,
            "index_name": idx.index_name,
            "index_type": idx.index_type,
            "metric_type": idx.metric_type,
        }
        if idx.params:
            params["params"] = idx.params
        return params

    # ----------------------------------------------------------------------
    # Operasi Data
    # ----------------------------------------------------------------------

    def insert(self, collection_name: str, data: dict | list[dict]) -> dict:
        """
        Insert data into collection

        Args:
            collection_name: Name of collection
            data: Single dict or list of dicts

        Returns:
            Insert result
        """
        try:
            if isinstance(data, dict):
                data = [data]

            result = milvus.insert(self.client, collection_name, data)
            logger.info(f"Inserted {len(data)} records into {collection_name}")
            return result
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            raise

    def search(
        self,
        collection_name: str,
        query_vectors: list[list[float]],
        anns_field: str = "embedding",
        limit: int = 10,
        output_fields: list[str] | None = None,
        **kwargs,
    ):
        """
        Perform vector search

        Args:
            collection_name: Collection name
            query_vectors: List of query vectors
            anns_field: Field to search on
            limit: Number of results
            output_fields: Fields to return
            **kwargs: Additional search parameters
        """
        try:
            result = milvus.search(
                self.client,
                collection_name,
                query_vectors,
                anns_field=anns_field,
                limit=limit,
                output_fields=output_fields or ["id", "distance"],
                **kwargs,
            )
            logger.info(f"Search completed on {collection_name}")
            return result
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def query(
        self,
        collection_name: str,
        filter_expr: str,
        output_fields: list[str] | None = None,
        limit: int | None = None,
    ):
        """
        Query with filter expression

        Args:
            collection_name: Collection name
            filter_expr: Filter expression
            output_fields: Fields to return
            limit: Max results
        """
        try:
            result = milvus.query(
                self.client,
                collection_name,
                filter_expr,
                output_fields=output_fields or ["*"],
                limit=limit,
            )
            logger.info(f"Query completed on {collection_name}")
            return result
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    def delete(self, collection_name: str, filter_expr: str):
        """
        Delete entities

        Args:
            collection_name: Collection name
            filter_expr: Filter for deletion
        """
        try:
            result = milvus.delete(self.client, collection_name, filter_expr)
            logger.info(f"Deleted from {collection_name}")
            return result
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise

    # ----------------------------------------------------------------------
    # Pengelolaan Collection
    # ----------------------------------------------------------------------

    def list_collections(self) -> list[str]:
        """List all collections"""
        return milvus.list_collections(self.client)

    def drop_collection(self, collection_name: str):
        """Drop a collection"""
        try:
            milvus.drop_collection(self.client, collection_name)
            logger.info(f"Dropped collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to drop collection: {e}")
            raise

    def get_collection_stats(self, collection_name: str) -> dict:
        """Get collection statistics"""
        return milvus.collection_stats(self.client, collection_name)

    def get_all_data(
        self,
        collection_name: str,
        filter_expr: str = "",
        output_fields: list[str] | None = None,
        batch_size: int = 1024,
    ) -> list[dict]:
        """
        Retrieve all records from a collection using the iterator pattern.

        Args:
            collection_name: Target collection
            filter_expr: Optional Milvus filter expression (e.g. "judul != ''")
            output_fields: Fields to return; defaults to all fields
            batch_size: Rows per batch, 1–16384

        Returns:
            List of all matching records as dicts
        """
        results = milvus.query_all(
            self.client,
            collection_name,
            filter_expr=filter_expr,
            output_fields=output_fields or ["*"],
            batch_size=batch_size,
        )
        logger.info(f"Retrieved {len(results)} records from {collection_name}")
        return results
