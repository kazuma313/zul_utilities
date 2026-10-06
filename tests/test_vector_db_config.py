import json

import pytest

from zul.utilities.vector_DB.config.config_file import read_config_file
from zul.utilities.vector_DB.config.config_loader import (
    ConfigLoader as MilvusConfigLoader,
)
from zul.utilities.vector_DB.config.config_loader_redis import (
    ConfigLoader as RedisConfigLoader,
)
from zul.utilities.vector_DB.config.config_schema import MilvusConfig
from zul.utilities.vector_DB.config.config_schema_redis import (
    ConnectionConfig,
    RedisConfig,
)


def milvus_config(schema_key="milvus_schema", datatype="FLOAT_VECTOR"):
    return {
        "connection": {"uri": "http://localhost", "port": 19530},
        "collections": [
            {
                "collection_name": "docs",
                schema_key: {
                    "fields": [
                        {
                            "field_name": "id",
                            "datatype": "VARCHAR",
                            "max_length": 64,
                            "is_primary": True,
                        },
                        {"field_name": "embedding", "datatype": datatype, "dim": 8},
                    ]
                },
                "indexes": [
                    {
                        "field_name": "embedding",
                        "index_name": "idx",
                        "index_type": "HNSW",
                        "metric_type": "COSINE",
                    }
                ],
            }
        ],
    }


def redis_config(fields=None):
    return {
        "connection": {"uri": "http://localhost", "port": 6379},
        "schema": {
            "index": {"name": "idx", "prefix": "doc"},
            "fields": fields
            or [
                {"name": "content", "type": "text"},
                {
                    "name": "embedding",
                    "type": "vector",
                    "attrs": {
                        "dims": 8,
                        "distance_metric": "COSINE",
                        "algorithm": "FLAT",
                    },
                },
            ],
        },
    }


# --------------------------------------------------------------------------
# config file reader
# --------------------------------------------------------------------------


def test_missing_config_file_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_config_file(tmp_path / "nope.yaml")


def test_unsupported_config_format_is_rejected(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("a = 1", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file format"):
        read_config_file(config_file)


def test_empty_config_file_is_rejected(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        read_config_file(config_file)


# --------------------------------------------------------------------------
# Milvus
# --------------------------------------------------------------------------


def test_milvus_datatype_is_case_insensitive():
    config = MilvusConfig(**milvus_config(datatype="float_vector"))

    assert config.collections[0].milvus_schema.fields[1].datatype == "FLOAT_VECTOR"


def test_milvus_unknown_datatype_is_rejected():
    with pytest.raises(ValueError):
        MilvusConfig(**milvus_config(datatype="DOUBLE_VECTOR"))


@pytest.mark.parametrize("schema_key", ["milvus_schema", "schema"])
def test_milvus_schema_section_accepts_both_key_names(schema_key):
    config = MilvusConfig(**milvus_config(schema_key=schema_key))

    assert len(config.collections[0].milvus_schema.fields) == 2


def test_milvus_loader_reports_which_file_is_invalid(tmp_path):
    config_file = tmp_path / "milvus.json"
    config_file.write_text(json.dumps({"collections": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="milvus.json"):
        MilvusConfigLoader.load(config_file)


# --------------------------------------------------------------------------
# Redis
# --------------------------------------------------------------------------


def test_redis_choices_are_normalised_to_lowercase():
    attrs = RedisConfig(**redis_config()).index_schema.fields[1].attrs

    assert (attrs.distance_metric, attrs.algorithm) == ("cosine", "flat")


def test_redis_vector_field_requires_attrs():
    with pytest.raises(ValueError, match="attrs"):
        RedisConfig(**redis_config(fields=[{"name": "embedding", "type": "vector"}]))


def test_redis_field_names_must_be_unique():
    duplicated = [
        {"name": "content", "type": "text"},
        {"name": "content", "type": "tag"},
    ]

    with pytest.raises(ValueError, match="unique"):
        RedisConfig(**redis_config(fields=duplicated))


def test_redis_schema_is_converted_to_redisvl_format():
    fields = [{"name": "title", "type": "text", "sortable": True}]

    schema = RedisConfig(**redis_config(fields=fields)).index_schema.to_redisvl_dict()

    assert schema["index"] == {"name": "idx", "prefix": "doc", "storage_type": "hash"}
    assert schema["fields"] == [
        {"name": "title", "type": "text", "attrs": {"sortable": True}}
    ]


def test_redis_converted_schema_is_accepted_by_redisvl():
    redisvl_schema = pytest.importorskip("redisvl.schema")

    schema = RedisConfig(**redis_config()).index_schema.to_redisvl_dict()

    assert redisvl_schema.IndexSchema.from_dict(schema).index.name == "idx"


@pytest.mark.parametrize(
    "uri, host",
    [
        ("http://localhost", "localhost"),
        ("https://redis.internal/", "redis.internal"),
        ("redis://10.0.0.5", "10.0.0.5"),
        ("localhost", "localhost"),
    ],
)
def test_redis_host_is_uri_without_scheme(uri, host):
    assert ConnectionConfig(uri=uri).host == host


def test_redis_uri_without_hostname_is_reported():
    with pytest.raises(ValueError, match="hostname"):
        _ = ConnectionConfig(uri="http://").host


@pytest.mark.parametrize("db_name, db", [("3", 3), ("redis_db", 0), (None, 0)])
def test_redis_db_number_comes_from_numeric_db_name(db_name, db):
    assert ConnectionConfig(db_name=db_name).db == db


def test_redis_config_round_trips_through_save_and_load(tmp_path):
    config = RedisConfig(**redis_config())
    saved_file = tmp_path / "redis.yaml"

    RedisConfigLoader.save(config, saved_file)

    assert RedisConfigLoader.load(saved_file) == config
