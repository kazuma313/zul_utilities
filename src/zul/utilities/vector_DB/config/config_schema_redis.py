"""
Configuration schema for Redis utilities
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class FieldTypeEnum(str, Enum):
    """Supported field types"""
    TEXT = "text"
    TAG = "tag"
    NUMERIC = "numeric"
    VECTOR = "vector"
    GEO = "geo"


class VectorAlgorithm(str, Enum):
    """Supported vector algorithms"""
    FLAT = "flat"
    HNSW = "hnsw"


class DistanceMetric(str, Enum):
    """Supported distance metrics"""
    COSINE = "cosine"
    L2 = "l2"
    IP = "ip"


class VectorDataType(str, Enum):
    """Supported vector data types"""
    FLOAT32 = "float32"
    FLOAT64 = "float64"


class StorageType(str, Enum):
    """Supported storage types"""
    HASH = "hash"
    JSON = "json"


class TextScorer(str, Enum):
    """Supported text scorers for hybrid search"""
    TFIDF = "TFIDF"
    TFIDF_DOCNORM = "TFIDF.DOCNORM"
    BM25 = "BM25"
    DISMAX = "DISMAX"
    DOCSCORE = "DOCSCORE"
    BM25STD = "BM25STD"


class ConnectionConfig(BaseModel):
    """Redis connection configuration"""
    uri: str = Field(default="http://localhost", description="Redis server URI")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis server port")
    db_name: Optional[str] = Field(default=None, description="Redis database name")
    password: Optional[str] = Field(default=None, description="Redis password")
    username: Optional[str] = Field(default=None, description="Redis username")
    
    @validator('uri')
    def validate_uri(cls, v):
        """Ensure URI doesn't have trailing slash"""
        return v.rstrip('/')


class VectorAttrs(BaseModel):
    """Vector field attributes"""
    dims: int = Field(gt=0, description="Vector dimensions")
    distance_metric: str = Field(description="Distance metric for similarity")
    algorithm: str = Field(description="Vector search algorithm")
    datatype: str = Field(default="float32", description="Vector data type")
    initial_cap: Optional[int] = Field(default=None, gt=0, description="Initial capacity for HNSW")
    m: Optional[int] = Field(default=None, gt=0, description="Number of connections for HNSW")
    ef_construction: Optional[int] = Field(default=None, gt=0, description="Size of dynamic candidate list for HNSW")
    ef_runtime: Optional[int] = Field(default=None, gt=0, description="Size of dynamic candidate list for search")
    
    @validator('distance_metric')
    def validate_distance_metric(cls, v):
        """Validate distance metric"""
        if v.lower() not in [e.value for e in DistanceMetric]:
            raise ValueError(f"Invalid distance metric: {v}. Must be one of {[e.value for e in DistanceMetric]}")
        return v.lower()
    
    @validator('algorithm')
    def validate_algorithm(cls, v):
        """Validate algorithm"""
        if v.lower() not in [e.value for e in VectorAlgorithm]:
            raise ValueError(f"Invalid algorithm: {v}. Must be one of {[e.value for e in VectorAlgorithm]}")
        return v.lower()
    
    @validator('datatype')
    def validate_datatype(cls, v):
        """Validate datatype"""
        if v.lower() not in [e.value for e in VectorDataType]:
            raise ValueError(f"Invalid datatype: {v}. Must be one of {[e.value for e in VectorDataType]}")
        return v.lower()


class FieldConfig(BaseModel):
    """Field configuration"""
    name: str = Field(description="Field name")
    type: str = Field(description="Field type")
    attrs: Optional[VectorAttrs] = Field(default=None, description="Attributes for vector fields")
    sortable: Optional[bool] = Field(default=False, description="Whether field is sortable")
    no_index: Optional[bool] = Field(default=False, description="Whether to skip indexing")
    
    @validator('type')
    def validate_type(cls, v):
        """Validate field type"""
        if v.lower() not in [e.value for e in FieldTypeEnum]:
            raise ValueError(f"Invalid field type: {v}. Must be one of {[e.value for e in FieldTypeEnum]}")
        return v.lower()
    
    @validator('attrs')
    def validate_vector_attrs(cls, v, values):
        """Ensure vector fields have attrs"""
        if 'type' in values and values['type'].lower() == 'vector' and v is None:
            raise ValueError("Vector fields must have 'attrs' defined")
        if 'type' in values and values['type'].lower() != 'vector' and v is not None:
            raise ValueError("Only vector fields can have 'attrs'")
        return v


class IndexConfig(BaseModel):
    """Index configuration"""
    name: str = Field(description="Index name")
    prefix: str = Field(description="Key prefix for the index")
    storage_type: str = Field(default="hash", description="Storage type")
    
    @validator('storage_type')
    def validate_storage_type(cls, v):
        """Validate storage type"""
        if v.lower() not in [e.value for e in StorageType]:
            raise ValueError(f"Invalid storage type: {v}. Must be one of {[e.value for e in StorageType]}")
        return v.lower()


class SchemaConfig(BaseModel):
    """Redis schema configuration"""
    index: IndexConfig = Field(description="Index configuration")
    fields: List[FieldConfig] = Field(min_items=1, description="Field definitions")
    
    @validator('fields')
    def validate_fields(cls, v):
        """Validate field configurations"""
        field_names = [f.name for f in v]
        if len(field_names) != len(set(field_names)):
            raise ValueError("Field names must be unique")
        return v


class HybridSearchConfig(BaseModel):
    """Configuration for hybrid search"""
    text_field_name: str = Field(description="Name of the text field")
    vector_field_name: str = Field(description="Name of the vector field")
    text_scorer: str = Field(default="BM25", description="Text scoring algorithm")
    alpha: float = Field(default=0.5, ge=0.0, le=1.0, description="Weight for vector score (0=text only, 1=vector only)")
    num_results: int = Field(default=10, gt=0, description="Number of results to return")
    return_fields: Optional[List[str]] = Field(default=None, description="Fields to return in results")
    
    @validator('text_scorer')
    def validate_text_scorer(cls, v):
        """Validate text scorer"""
        if v.upper() not in [e.value for e in TextScorer]:
            raise ValueError(f"Invalid text scorer: {v}. Must be one of {[e.value for e in TextScorer]}")
        return v.upper()


class RedisConfig(BaseModel):
    """Main Redis configuration"""
    connection: ConnectionConfig = Field(description="Redis connection settings")
    schema: SchemaConfig = Field(description="Redis schema definition")
    hybrid_search: Optional[HybridSearchConfig] = Field(default=None, description="Hybrid search configuration")
    
    class Config:
        use_enum_values = True
        validate_assignment = True