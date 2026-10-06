"""
Skema dan loader config untuk helper vector database.

Isi folder:
    config_file.py           pembaca file YAML / JSON yang dipakai bersama
    config_schema.py         skema Milvus (MilvusConfig)
    config_loader.py         loader Milvus
    config_schema_redis.py   skema Redis (RedisConfig)
    config_loader_redis.py   loader Redis

Contoh memvalidasi config tanpa menyambung ke server:
    from zul.utilities.vector_DB.config.config_loader import ConfigLoader

    config = ConfigLoader.load("milvus_config.json")
    print([collection.collection_name for collection in config.collections])
"""
