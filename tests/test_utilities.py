"""Integration test: butuh server Milvus yang hidup di localhost:19530.

Di-skip secara default. Jalankan dengan:
    ZUL_RUN_INTEGRATION=1 pytest tests/test_utilities.py
"""

import copy
import json
import os

import pytest

pytest.importorskip("pymilvus")

from zul.commands.install import DEFAULT_MILVUS_CONFIG
from zul.utilities.vector_DB.milvus_helper import MilvusHelper

TEST_COLLECTION = "zul_integration_test"

pytestmark = pytest.mark.skipif(
    not os.getenv("ZUL_RUN_INTEGRATION"),
    reason="butuh server Milvus; set ZUL_RUN_INTEGRATION=1 untuk menjalankan",
)


def test_milvus_helper_creates_collection_from_config(tmp_path):
    config = copy.deepcopy(DEFAULT_MILVUS_CONFIG)
    config["collections"][0]["collection_name"] = TEST_COLLECTION
    config_file = tmp_path / "milvus_config.json"
    config_file.write_text(json.dumps(config), encoding="utf-8")

    client = MilvusHelper(config_path=config_file)
    try:
        assert TEST_COLLECTION in client.list_collections()
    finally:
        client.drop_collection(TEST_COLLECTION)
