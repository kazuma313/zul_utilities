"""RedisVectorDB / RedisHelper diuji dengan Redis & index palsu (tanpa server)."""

import numpy as np
import pytest
import yaml

pytest.importorskip("redisvl")

from zul.utilities.vector_DB import redis_helper
from zul.utilities.vector_DB.redis_helper import (
    RedisHelper,
    RedisVectorDB,
    _to_vector_bytes,
    reciprocal_rank_fusion,
)

SCHEMA = {
    "index": {"name": "idx", "prefix": "doc"},
    "fields": [{"name": "content", "type": "text"}],
}


class FakeRedis:
    modules = [{b"name": b"search", b"ver": 20810}]

    def __init__(self, **connection):
        self.connection = connection
        self.closed = False

    def ping(self):
        return True

    def info(self):
        return {"redis_version": "7.4.0"}

    def execute_command(self, *_args):
        return self.modules

    def close(self):
        self.closed = True


class FakeIndex:
    def __init__(self, schema):
        self.schema = schema
        self.create_calls = []
        self.loaded_batches = []
        self.queries = []

    @classmethod
    def from_dict(cls, schema, **_kwargs):
        return cls(schema)

    def create(self, overwrite=False, drop=False):
        self.create_calls.append({"overwrite": overwrite, "drop": drop})

    def load(self, batch):
        self.loaded_batches.append(batch)
        return [f"doc:{len(self.loaded_batches)}:{i}" for i in range(len(batch))]

    def query(self, query):
        self.queries.append(query)
        return [{"content": "hasil"}]


@pytest.fixture(autouse=True)
def fake_redis_stack(monkeypatch):
    monkeypatch.setattr(redis_helper, "Redis", FakeRedis)
    monkeypatch.setattr(redis_helper, "SearchIndex", FakeIndex)
    # Query asli diganti perekam argumen, supaya test ini tak
    # bergantung pada cara kerja internal redisvl sendiri.
    monkeypatch.setattr(
        redis_helper, "AggregateHybridQuery", lambda **kwargs: {"hybrid": kwargs}
    )
    monkeypatch.setattr(
        redis_helper, "VectorQuery", lambda **kwargs: {"vector": kwargs}
    )


def write_config(tmp_path, hybrid_search=None):
    config = {
        "connection": {
            "uri": "http://redis.internal",
            "port": 6380,
            "password": "p@ss!",
            "db_name": "2",
        },
        "schema": {
            "index": {"name": "idx", "prefix": "doc"},
            "fields": [
                {"name": "content", "type": "text"},
                {
                    "name": "embedding",
                    "type": "vector",
                    "attrs": {
                        "dims": 3,
                        "distance_metric": "cosine",
                        "algorithm": "flat",
                    },
                },
            ],
        },
    }
    if hybrid_search:
        config["hybrid_search"] = hybrid_search
    config_file = tmp_path / "redis.yaml"
    config_file.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_file


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


@pytest.mark.parametrize("vector", [[0.5, 1.0], np.array([0.5, 1.0], dtype=np.float64)])
def test_vectors_are_sent_to_redis_as_float32_bytes(vector):
    assert _to_vector_bytes(vector) == np.array([0.5, 1.0], dtype=np.float32).tobytes()


def test_vector_bytes_are_passed_through_unchanged():
    assert _to_vector_bytes(b"\x00\x01") == b"\x00\x01"


def test_rrf_ranks_item_found_by_both_systems_first():
    scored, ranked = reciprocal_rank_fusion(["a", "b"], ["b", "c"], K=100)

    assert ranked[0] == "b"
    assert dict(scored)["b"] == pytest.approx(1 / 102 + 1 / 101)


# --------------------------------------------------------------------------
# RedisVectorDB
# --------------------------------------------------------------------------


def test_connects_with_given_credentials():
    db = RedisVectorDB(host="10.0.0.1", port=6380, password="rahasia", db=1)

    assert db.client.connection["host"] == "10.0.0.1"
    assert db.client.connection["port"] == 6380
    assert db.client.connection["password"] == "rahasia"
    assert db.client.connection["db"] == 1


@pytest.mark.parametrize(
    "operation",
    [
        lambda db: db.insert_data([{"content": "a"}]),
        lambda db: db.vector_search([0.1], "embedding"),
        lambda db: db.hybrid_search("q", [0.1], "content", "embedding"),
        lambda db: db.hybrid_search_rrf("q", [0.1], "content", "embedding"),
        lambda db: db.get_info(),
        lambda db: db.delete_index(),
    ],
)
def test_operations_require_an_index(operation):
    with pytest.raises(ValueError, match="create_index"):
        operation(RedisVectorDB())


def test_insert_data_loads_in_batches_and_returns_all_keys():
    db = RedisVectorDB()
    db.create_index(SCHEMA)

    keys = db.insert_data([{"content": str(i)} for i in range(5)], batch_size=2)

    assert [len(batch) for batch in db.index.loaded_batches] == [2, 2, 1]
    assert len(keys) == 5


def test_requirements_met_when_search_module_is_recent_enough():
    requirements = RedisVectorDB().check_requirements()

    assert requirements == {
        "redis_version": "7.4.0",
        "search_module_version": 20810,
        "vector_search_supported": True,
    }


@pytest.mark.parametrize(
    "modules, module_version",
    [
        ([{"name": "search", "ver": 20400}], 20400),
        ([{"name": "bf", "ver": 20800}], None),
    ],
)
def test_requirements_not_met_without_recent_search_module(
    monkeypatch, modules, module_version
):
    monkeypatch.setattr(FakeRedis, "modules", modules)

    requirements = RedisVectorDB().check_requirements()

    assert requirements["search_module_version"] == module_version
    assert requirements["vector_search_supported"] is False


# --------------------------------------------------------------------------
# RedisHelper (configuration-based)
# --------------------------------------------------------------------------


def test_helper_connects_using_connection_section_of_config(tmp_path):
    helper = RedisHelper(write_config(tmp_path))

    assert helper.client.connection["host"] == "redis.internal"
    assert helper.client.connection["port"] == 6380
    assert helper.client.connection["password"] == "p@ss!"
    assert helper.client.connection["db"] == 2


def test_helper_never_drops_an_existing_index(tmp_path):
    helper = RedisHelper(write_config(tmp_path))
    helper.insert({"content": "a"})
    helper.vector_search([0.1, 0.2, 0.3], "embedding")

    assert helper.index.create_calls == [{"overwrite": False, "drop": False}]


def test_helper_builds_index_from_schema_section(tmp_path):
    helper = RedisHelper(write_config(tmp_path))

    assert [field["name"] for field in helper.index.schema["fields"]] == [
        "content",
        "embedding",
    ]


def test_helper_hybrid_search_uses_settings_from_config(tmp_path):
    hybrid_search = {
        "text_field_name": "content",
        "vector_field_name": "embedding",
        "text_scorer": "bm25",
        "alpha": 0.3,
        "num_results": 7,
    }
    helper = RedisHelper(write_config(tmp_path, hybrid_search))

    helper.hybrid_search(query_text="software developer", query_vector=[0.1, 0.2, 0.3])

    query = helper.index.queries[-1]["hybrid"]
    assert query["text"] == "software developer"
    assert (query["text_field_name"], query["vector_field_name"]) == (
        "content",
        "embedding",
    )
    assert (query["text_scorer"], query["alpha"], query["num_results"]) == (
        "BM25",
        0.3,
        7,
    )
    assert query["return_fields"] == ["content"]


def test_helper_hybrid_search_limit_overrides_config(tmp_path):
    hybrid_search = {
        "text_field_name": "content",
        "vector_field_name": "embedding",
        "num_results": 7,
    }
    helper = RedisHelper(write_config(tmp_path, hybrid_search))

    helper.hybrid_search(query_text="q", query_vector=[0.1, 0.2, 0.3], limit=2)

    assert helper.index.queries[-1]["hybrid"]["num_results"] == 2


def test_helper_hybrid_search_needs_hybrid_section(tmp_path):
    helper = RedisHelper(write_config(tmp_path))

    with pytest.raises(ValueError, match="Hybrid search configuration"):
        helper.hybrid_search(query_text="q", query_vector=[0.1, 0.2, 0.3])


def test_old_import_path_still_works():
    from zul.utilities.redis_vector_helper import RedisVectorDB as OldPathRedisVectorDB

    assert OldPathRedisVectorDB is RedisVectorDB
