"""
Helper vector database berbasis file config.

Isi folder:
    milvus_helper.py   MilvusHelper   (`pip install "zul[milvus]"`)
    redis_helper.py    RedisHelper, RedisVectorDB   (`pip install "zul[redis]"`)
    config/            skema dan loader config (YAML / JSON)

Cara cepat memulai:
    zul install milvus-helper      # menulis milvus_config.json
    zul install redis-helper       # menulis redis_config.yaml

    from zul.utilities.vector_DB.milvus_helper import MilvusHelper
    from zul.utilities.vector_DB.redis_helper import RedisHelper

    milvus = MilvusHelper("milvus_config.json")
    redis_helper = RedisHelper("redis_config.yaml")
"""
