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
(objek `pymilvus.MilvusClient`).

Modul ini tidak mengatur logging. Untuk melihat log-nya:
    logging.basicConfig(level=logging.INFO)
"""

import logging
from pathlib import Path

from pymilvus import DataType, Function, FunctionType, MilvusClient

from .config.config_loader import ConfigLoader

# Kode library tidak mengatur logging sendiri. Program pemakainya
# yang menentukan ke mana catatan ini ditulis, misalnya lewat
# logging.basicConfig ketika aplikasi itu mulai berjalan.
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Pemetaan Tipe Data
# --------------------------------------------------------------------------
#
# File config menulis tipe data sebagai teks, sedangkan Milvus meminta
# anggota enum DataType. Tabel ini menghubungkan keduanya, dan tipe
# yang di luar daftar ini ditolak dengan pesan error yang jelas.
#


_DATATYPES = {
    "VARCHAR": DataType.VARCHAR,
    "INT64": DataType.INT64,
    "FLOAT": DataType.FLOAT,
    "FLOAT_VECTOR": DataType.FLOAT_VECTOR,
    "SPARSE_FLOAT_VECTOR": DataType.SPARSE_FLOAT_VECTOR,
    "BOOL": DataType.BOOL,
    "JSON": DataType.JSON,
}


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

            client_params = {"uri": uri}
            if conn.user:
                client_params["user"] = conn.user
            if conn.password:
                client_params["password"] = conn.password

            self.client = MilvusClient(**client_params)  # type: ignore
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

            existing_dbs = self.client.list_databases()

            if db_name not in existing_dbs:
                self.client.create_database(db_name=db_name)
                logger.info(f"Created database: {db_name}")

            self.client.use_database(db_name=db_name)
            logger.info(f"Using database: {db_name}")
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise

    def _create_collections(self):
        """Create all collections defined in configuration"""
        existing = self.client.list_collections()

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
        # Build schema
        schema = self.client.create_schema(
            auto_id=col_config.milvus_schema.auto_id,
            enable_dynamic_field=col_config.milvus_schema.enable_dynamic_field,
            description=col_config.milvus_schema.description or "",
        )

        # Add fields
        for field in col_config.milvus_schema.fields:
            field_params = {
                "field_name": field.field_name,
                "datatype": self._map_datatype(field.datatype),
                "is_primary": field.is_primary,
            }

            if field.auto_id:
                field_params["auto_id"] = field.auto_id
            if field.max_length:
                field_params["max_length"] = field.max_length
            if field.dim:
                field_params["dim"] = field.dim
            if field.description:
                field_params["description"] = field.description
            if field.enable_analyzer:
                field_params["enable_analyzer"] = field.enable_analyzer

            schema.add_field(**field_params)

        # Add functions (e.g., BM25)
        for func in col_config.milvus_schema.functions or []:
            function = Function(
                name=func.name,
                input_field_names=func.input_field_names,
                output_field_names=func.output_field_names,
                function_type=self._map_function_type(func.function_type),
            )
            schema.add_function(function)

        # Build indexes
        index_params = self.client.prepare_index_params()
        for idx in col_config.indexes:
            params = {
                "field_name": idx.field_name,
                "index_name": idx.index_name,
                "index_type": idx.index_type,
                "metric_type": idx.metric_type,
            }
            if idx.params:
                params["params"] = idx.params

            index_params.add_index(**params)

        # Create collection
        self.client.create_collection(
            collection_name=col_config.collection_name,
            schema=schema,
            index_params=index_params,
            shards_num=col_config.shards_num,
        )

    def _map_datatype(self, datatype: str):
        """Map string datatype to Milvus DataType"""
        try:
            return _DATATYPES[datatype.upper()]
        except KeyError:
            raise ValueError(
                f"Unsupported datatype: {datatype}. Use one of {sorted(_DATATYPES)}"
            ) from None

    def _map_function_type(self, function_type: str):
        """Map string function type (e.g. "BM25") to Milvus FunctionType"""
        try:
            return FunctionType[function_type.upper()]
        except KeyError:
            raise ValueError(f"Unsupported function type: {function_type}") from None

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

            result = self.client.insert(collection_name=collection_name, data=data)
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
            result = self.client.search(
                collection_name=collection_name,
                data=query_vectors,
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
            result = self.client.query(
                collection_name=collection_name,
                filter=filter_expr,
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
            result = self.client.delete(
                collection_name=collection_name, filter=filter_expr
            )
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
        return self.client.list_collections()  # type: ignore

    def drop_collection(self, collection_name: str):
        """Drop a collection"""
        try:
            self.client.drop_collection(collection_name=collection_name)
            logger.info(f"Dropped collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to drop collection: {e}")
            raise

    def get_collection_stats(self, collection_name: str) -> dict:
        """Get collection statistics"""
        return self.client.get_collection_stats(collection_name=collection_name)

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
        results: list[dict] = []
        iterator = self.client.query_iterator(
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
                results.extend(batch)
        finally:
            iterator.close()

        logger.info(f"Retrieved {len(results)} records from {collection_name}")
        return results
