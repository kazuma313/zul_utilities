"""MilvusHelper diuji dengan client palsu (tanpa server Milvus)."""

import json

import pytest

pymilvus = pytest.importorskip("pymilvus")

from zul.adapters import milvus as milvus_adapter  # noqa: E402
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
        self.calls = []
        self.iterator = None

    def list_databases(self):
        return self.databases

    def create_database(self, db_name):
        self.databases.append(db_name)

    def use_database(self, db_name):
        self.current_database = db_name

    def list_collections(self):
        return [*self.existing_collections, *self.created]

    def create_collection(self, collection_name, schema, index_params, shards_num):
        self.created[collection_name] = {
            "schema": schema,
            "indexes": [index.to_dict() for index in index_params],
            "shards_num": shards_num,
        }

    def insert(self, **kwargs):
        self.calls.append(("insert", kwargs))
        return {"insert_count": len(kwargs["data"]), "ids": ["doc-1"]}

    def search(self, **kwargs):
        self.calls.append(("search", kwargs))
        return [[{"id": "doc-1", "distance": 0.9}]]

    def query(self, **kwargs):
        self.calls.append(("query", kwargs))
        return [{"id": "doc-1"}]

    def delete(self, **kwargs):
        self.calls.append(("delete", kwargs))
        return {"delete_count": 1}

    def query_iterator(self, **kwargs):
        self.calls.append(("query_iterator", kwargs))
        self.iterator = FakeIterator([[{"id": 1}, {"id": 2}], [{"id": 3}], []])
        return self.iterator


class FakeIterator:
    def __init__(self, batches):
        self.batches = batches
        self.closed = False

    def next(self):
        return self.batches.pop(0)

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def fake_milvus(monkeypatch):
    monkeypatch.setattr(milvus_adapter, "MilvusClient", FakeMilvusClient)
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


def test_creates_indexes_from_config(tmp_path):
    helper = MilvusHelper(write_config(tmp_path))

    assert helper.client.created["documents"]["indexes"] == [
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
    ]


def test_existing_collection_is_left_untouched(tmp_path, monkeypatch):
    monkeypatch.setattr(FakeMilvusClient, "existing_collections", ["documents"])

    helper = MilvusHelper(write_config(tmp_path))

    assert helper.client.created == {}


def test_unknown_function_type_is_reported(tmp_path):
    with pytest.raises(ValueError, match="Unsupported function type: TFIDF"):
        MilvusHelper(write_config(tmp_path, function_type="TFIDF"))


def test_data_operations_send_defaults_to_the_client(tmp_path):
    helper = MilvusHelper(write_config(tmp_path))

    inserted = helper.insert("documents", {"id": "doc-1"})
    hits = helper.search("documents", [[0.1, 0.2]], limit=3, filter="id != ''")
    rows = helper.query("documents", filter_expr='id == "doc-1"')
    deleted = helper.delete("documents", filter_expr='id == "doc-1"')

    assert inserted == {"insert_count": 1, "ids": ["doc-1"]}
    assert hits == [[{"id": "doc-1", "distance": 0.9}]]
    assert rows == [{"id": "doc-1"}]
    assert deleted == {"delete_count": 1}
    assert helper.client.calls == [
        ("insert", {"collection_name": "documents", "data": [{"id": "doc-1"}]}),
        (
            "search",
            {
                "collection_name": "documents",
                "data": [[0.1, 0.2]],
                "anns_field": "embedding",
                "limit": 3,
                "output_fields": ["id", "distance"],
                "filter": "id != ''",
            },
        ),
        (
            "query",
            {
                "collection_name": "documents",
                "filter": 'id == "doc-1"',
                "output_fields": ["*"],
                "limit": None,
            },
        ),
        ("delete", {"collection_name": "documents", "filter": 'id == "doc-1"'}),
    ]


def test_get_all_data_reads_every_batch_and_closes_the_iterator(tmp_path):
    helper = MilvusHelper(write_config(tmp_path))

    rows = helper.get_all_data("documents", filter_expr="id > 0", batch_size=2)

    assert rows == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert helper.client.iterator.closed
    assert helper.client.calls == [
        (
            "query_iterator",
            {
                "collection_name": "documents",
                "batch_size": 2,
                "filter": "id > 0",
                "output_fields": ["*"],
            },
        )
    ]
