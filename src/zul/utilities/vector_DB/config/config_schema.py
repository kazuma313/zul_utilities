"""
Simplified configuration schema for Milvus utilities
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


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
    """Supported index types"""
    FLAT = "FLAT"
    IVF_FLAT = "IVF_FLAT"
    HNSW = "HNSW"
    IVF_PQ = "IVF_PQ"
    SPARSE_INVERTED_INDEX = "SPARSE_INVERTED_INDEX"


class MetricType(str, Enum):
    """Supported metric types"""
    COSINE = "COSINE"
    L2 = "L2"
    IP = "IP"
    BM25 = "BM25"


class ConnectionConfig(BaseModel):
    """Milvus connection configuration"""
    uri: str = Field(default="http://localhost")
    port: int = Field(default=19530)
    db_name: Optional[str] = Field(default=None)
    user: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)


class FieldConfig(BaseModel):
    """Field configuration"""
    field_name: str
    datatype: str
    is_primary: bool = False
    auto_id: bool = False
    max_length: Optional[int] = None
    dim: Optional[int] = None
    description: Optional[str] = None
    enable_analyzer: bool = False


class FunctionConfig(BaseModel):
    """Function configuration (e.g., BM25)"""
    name: str
    function_type: str = "BM25"
    input_field_names: List[str]
    output_field_names: List[str]


class IndexConfig(BaseModel):
    """Index configuration"""
    field_name: str
    index_name: str
    index_type: str
    metric_type: str
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SchemaConfig(BaseModel):
    """Schema configuration"""
    auto_id: bool = True
    enable_dynamic_field: bool = True
    description: Optional[str] = None
    fields: List[FieldConfig]
    functions: Optional[List[FunctionConfig]] = Field(default_factory=list)


class CollectionConfig(BaseModel):
    """Collection configuration"""
    collection_name: str
    description: Optional[str] = None
    shards_num: int = Field(default=2)
    milvus_schema: SchemaConfig
    indexes: List[IndexConfig]


class MilvusConfig(BaseModel):
    """Main configuration"""
    connection: ConnectionConfig
    collections: List[CollectionConfig] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True