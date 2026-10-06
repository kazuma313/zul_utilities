"""
Simplified configuration schema for Milvus utilities

Bentuk config (YAML; JSON memakai struktur yang sama):
    connection:
      uri: "http://localhost"
      port: 19530
      db_name: "default"          # opsional; dibuat jika belum ada
    collections:
      - collection_name: "documents"
        milvus_schema:            # boleh juga ditulis `schema`
          fields:
            - {field_name: "id", datatype: "VARCHAR", max_length: 128, is_primary: true}
            - {field_name: "embedding", datatype: "FLOAT_VECTOR", dim: 768}
        indexes:
          - field_name: "embedding"
            index_name: "emb_idx"
            index_type: "HNSW"
            metric_type: "COSINE"
            params: {M: 16, efConstruction: 200}

`datatype` harus salah satu nilai `DataTypeEnum` (huruf besar-kecil bebas).
`index_type` dan `metric_type` diteruskan apa adanya ke Milvus.
"""

from enum import Enum
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

# --------------------------------------------------------------------------
# Pilihan Nilai
# --------------------------------------------------------------------------
#
# Hanya tipe data yang dibatasi ke daftar di bawah ini. Tipe index dan
# metric diteruskan apa adanya ke Milvus, jadi kedua enum yang lain
# hanya berisi nilai yang paling sering dipakai sebagai rujukan.
#


class DataTypeEnum(str, Enum):
    """Supported data types"""

    VARCHAR = "VARCHAR"
    INT64 = "INT64"
    FLOAT = "FLOAT"
    FLOAT_VECTOR = "FLOAT_VECTOR"
    SPARSE_FLOAT_VECTOR = "SPARSE_FLOAT_VECTOR"
    BOOL = "BOOL"
    JSON = "JSON"


class IndexType(str, Enum):
    """Commonly used index types (index_type accepts any type Milvus supports)"""

    FLAT = "FLAT"
    IVF_FLAT = "IVF_FLAT"
    HNSW = "HNSW"
    IVF_PQ = "IVF_PQ"
    SPARSE_INVERTED_INDEX = "SPARSE_INVERTED_INDEX"


class MetricType(str, Enum):
    """Commonly used metric types (metric_type accepts any metric Milvus supports)"""

    COSINE = "COSINE"
    L2 = "L2"
    IP = "IP"
    BM25 = "BM25"


# --------------------------------------------------------------------------
# Koneksi
# --------------------------------------------------------------------------


class ConnectionConfig(BaseModel):
    """Milvus connection configuration"""

    uri: str = Field(default="http://localhost")
    port: int = Field(default=19530)
    db_name: str | None = Field(default=None)
    user: str | None = Field(default=None)
    password: str | None = Field(default=None)


# --------------------------------------------------------------------------
# Isi Collection
# --------------------------------------------------------------------------


class FieldConfig(BaseModel):
    """Field configuration"""

    model_config = ConfigDict(use_enum_values=True)

    field_name: str
    datatype: DataTypeEnum
    is_primary: bool = False
    auto_id: bool = False
    max_length: int | None = None
    dim: int | None = None
    description: str | None = None
    enable_analyzer: bool = False

    @field_validator("datatype", mode="before")
    @classmethod
    def uppercase_datatype(cls, v):
        """Accept datatypes in any letter case (e.g. 'varchar')"""
        return v.upper() if isinstance(v, str) else v


class FunctionConfig(BaseModel):
    """Function configuration (e.g., BM25)"""

    name: str
    function_type: str = "BM25"
    input_field_names: list[str]
    output_field_names: list[str]


class IndexConfig(BaseModel):
    """Index configuration"""

    field_name: str
    index_name: str
    index_type: str
    metric_type: str
    params: dict[str, Any] | None = Field(default_factory=dict)


class SchemaConfig(BaseModel):
    """Schema configuration"""

    auto_id: bool = True
    enable_dynamic_field: bool = True
    description: str | None = None
    fields: list[FieldConfig]
    functions: list[FunctionConfig] | None = Field(default_factory=list)


class CollectionConfig(BaseModel):
    """Collection configuration"""

    model_config = ConfigDict(populate_by_name=True)

    collection_name: str
    description: str | None = None
    shards_num: int = Field(default=2)
    # Di file config, bagian ini bisa ditulis sebagai "milvus_schema"
    # maupun "schema". Dua nama itu dibaca ke field yang sama ini.
    milvus_schema: SchemaConfig = Field(
        validation_alias=AliasChoices("milvus_schema", "schema")
    )
    indexes: list[IndexConfig]


# --------------------------------------------------------------------------
# Akar Konfigurasi
# --------------------------------------------------------------------------


class MilvusConfig(BaseModel):
    """Main configuration"""

    connection: ConnectionConfig
    collections: list[CollectionConfig] = Field(default_factory=list)
