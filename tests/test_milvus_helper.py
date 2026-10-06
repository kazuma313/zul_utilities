"""MilvusHelper diuji dengan client palsu (tanpa server Milvus)."""

import json

import pytest

pymilvus = pytest.importorskip("pymilvus")

from zul.utilities.vector_DB import milvus_helper  # noqa: E402
from zul.utilities.vector_DB.milvus_helper import MilvusHelper  # noqa: E402


class FakeMilvusClient:
    # Schema & index dibangun oleh pymilvus asli; keduanya tak butuh server.
    create_schema = staticmethod(pymilvus.MilvusClient.create_schema)
    prepare_index_params = staticmethod(pymilvus.MilvusClient.prepare_index_params)

    existing_collections: list[str] = []

    def __init__(self, **connection):
        self.connection = connection
        self.databases = ["default"]
        self.current_database = None
        self.created = {}

    def list_databases(self):
        return self.databases

    def create_database(self, db_name):
        self.databases.append(db_name)

    def use_database(self, db_name):
        self.current_database = db_name

    def list_collections(self):
        return [*self.existing_collections, *self.created]

    def create_collection(self, collection_name, schema, index_params, shards_num):
        self.created[collection_name] = {"schema": schema, "shards_num": shards_num}


@pytest.fixture(autouse=True)
def fake_milvus(monkeypatch):
    monkeypatch.setattr(milvus_helper, "MilvusClient", FakeMilvusClient)
    monkeypatch.setattr(FakeMilvusClient, "existing_collections", [])


def write_config(tmp_path, function_type="BM25", connection=None):
    config = {
        "connection": connection or {"uri": "http://localhost", "port": 19530},
        "collections": [
            {
                "collection_name": "documents",
                "shards_num": 3,
                "schema": {
                    "fields": [
                        {
                            "field_name": "id",
                            "datatype": "varchar",
                            "max_length": 64,
                            "is_primary": True,
                        },
                        {
                            "field_name": "content",
                            "datatype": "VARCHAR",
                            "max_length": 1000,
                            "enable_analyzer": True,
                        },
                        {"field_name": "dense", "datatype": "FLOAT_VECTOR", "dim": 8},
                        {"field_name": "sparse", "datatype": "SPARSE_FLOAT_VECTOR"},
                    ],
                    "functions": [
                        {
                            "name": "bm25",
                            "function_type": function_type,
                            "input_field_names": ["content"],
                            "output_field_names": ["sparse"],
                        }
                    ],
                },
                "indexes": [
                    {
                        "field_name": "dense",
                        "index_name": "dense_idx",
                        "index_type": "HNSW",
                        "metric_type": "COSINE",
                    },
                    {
                        "field_name": "sparse",
                        "index_name": "sparse_idx",
                        "index_type": "SPARSE_INVERTED_INDEX",
                        "metric_type": "BM25",
                    },
                ],
            }
        ],
    }
    config_file = tmp_path / "milvus.json"
    config_file.write_text(json.dumps(config), encoding="utf-8")
    return config_file


def test_connects_to_uri_and_port_with_credentials(tmp_path):
    connection = {
        "uri": "http://milvus.internal",
        "port": 19531,
        "user": "root",
        "password": "rahasia",
    }

    helper = MilvusHelper(write_config(tmp_path, connection=connection))

    assert helper.client.connection == {
        "uri": "http://milvus.internal:19531",
        "user": "root",
        "password": "rahasia",
    }


def test_creates_missing_database_and_switches_to_it(tmp_path):
    connection = {"uri": "http://localhost", "port": 19530, "db_name": "legal"}

    helper = MilvusHelper(write_config(tmp_path, connection=connection))

    assert "legal" in helper.client.databases
    assert helper.client.current_database == "legal"


def test_creates_collection_with_fields_from_config(tmp_path):
    helper = MilvusHelper(write_config(tmp_path))

    created = helper.client.created["documents"]
    datatypes = {field.name: field.dtype for field in created["schema"].fields}
    assert datatypes == {
        "id": pymilvus.DataType.VARCHAR,
        "content": pymilvus.DataType.VARCHAR,
        "dense": pymilvus.DataType.FLOAT_VECTOR,
        "sparse": pymilvus.DataType.SPARSE_FLOAT_VECTOR,
    }
    assert created["shards_num"] == 3


def test_creates_bm25_function_from_config(tmp_path):
    helper = MilvusHelper(write_config(tmp_path))

    functions = helper.client.created["documents"]["schema"].functions
    assert [(function.name, function.type) for function in functions] == [
        ("bm25", pymilvus.FunctionType.BM25)
    ]


def test_existing_collection_is_left_untouched(tmp_path, monkeypatch):
    monkeypatch.setattr(FakeMilvusClient, "existing_collections", ["documents"])

    helper = MilvusHelper(write_config(tmp_path))

    assert helper.client.created == {}


def test_unknown_function_type_is_reported(tmp_path):
    with pytest.raises(ValueError, match="Unsupported function type: TFIDF"):
        MilvusHelper(write_config(tmp_path, function_type="TFIDF"))
