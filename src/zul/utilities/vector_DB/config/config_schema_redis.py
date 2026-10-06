"""
Configuration schema for Redis utilities

Bentuk config (YAML; JSON memakai struktur yang sama):
    connection:
      uri: "http://localhost"
      port: 6379
      password: "..."             # opsional
      db_name: "0"                # opsional; angka = nomor database Redis
    schema:
      index:
        name: "my_index"
        prefix: "doc"
        storage_type: "hash"      # hash | json
      fields:
        - {name: "content", type: "text"}
        - name: "embedding"
          type: "vector"
          attrs: {dims: 768, distance_metric: "cosine", algorithm: "flat"}
    hybrid_search:                # opsional; dipakai RedisHelper.hybrid_search
      text_field_name: "content"
      vector_field_name: "embedding"
      text_scorer: "BM25"
      alpha: 0.5                  # 0 = teks saja, 1 = vektor saja
      num_results: 10

Di Python, bagian `schema` diakses sebagai `config.index_schema`.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# --------------------------------------------------------------------------
# Pilihan Nilai
# --------------------------------------------------------------------------
#
# Setiap enum di bawah ini memuat nilai yang diterima RediSearch untuk
# satu pengaturan. Nilai di file config dicocokkan tanpa membedakan
# huruf besar atau kecil, lalu disimpan dalam bentuk bakunya.
#


_URI_SCHEMES = ("http://", "https://", "redis://", "rediss://")


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


def _validate_choice(
    value: str, choices: type[Enum], label: str, upper: bool = False
) -> str:
    """Normalise letter case and make sure the value is one of the enum's values"""
    normalised = value.upper() if upper else value.lower()
    valid_values = [e.value for e in choices]
    if normalised not in valid_values:
        raise ValueError(f"Invalid {label}: {value}. Must be one of {valid_values}")
    return normalised


# --------------------------------------------------------------------------
# Koneksi
# --------------------------------------------------------------------------


class ConnectionConfig(BaseModel):
    """Redis connection configuration"""

    uri: str = Field(default="http://localhost", description="Redis server URI")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis server port")
    db_name: str | None = Field(default=None, description="Redis database name")
    password: str | None = Field(default=None, description="Redis password")
    username: str | None = Field(default=None, description="Redis username")

    @field_validator("uri")
    @classmethod
    def validate_uri(cls, v):
        """Ensure URI doesn't have trailing slash"""
        # URI yang hanya berisi skema dibiarkan apa adanya, agar
        # pesan error soal hostname yang kosong bisa menyebut
        # nilai aslinya ketika properti host dibaca nanti.
        if v.endswith("://"):
            return v

        return v.rstrip("/")

    @property
    def host(self) -> str:
        """Hostname without the scheme (e.g. 'http://localhost' -> 'localhost')"""
        host = self.uri
        for scheme in _URI_SCHEMES:
            if host.startswith(scheme):
                host = host[len(scheme) :]
                break
        if not host:
            raise ValueError(f"connection.uri has no hostname: '{self.uri}'")
        return host

    @property
    def db(self) -> int:
        """Redis logical database number; non-numeric db_name falls back to 0"""
        if self.db_name and self.db_name.isdigit():
            return int(self.db_name)
        return 0


# --------------------------------------------------------------------------
# Skema Index
# --------------------------------------------------------------------------


class VectorAttrs(BaseModel):
    """Vector field attributes"""

    dims: int = Field(gt=0, description="Vector dimensions")
    distance_metric: str = Field(description="Distance metric for similarity")
    algorithm: str = Field(description="Vector search algorithm")
    datatype: str = Field(default="float32", description="Vector data type")
    initial_cap: int | None = Field(
        default=None, gt=0, description="Initial capacity for HNSW"
    )
    m: int | None = Field(
        default=None, gt=0, description="Number of connections for HNSW"
    )
    ef_construction: int | None = Field(
        default=None, gt=0, description="Size of dynamic candidate list for HNSW"
    )
    ef_runtime: int | None = Field(
        default=None, gt=0, description="Size of dynamic candidate list for search"
    )

    @field_validator("distance_metric")
    @classmethod
    def validate_distance_metric(cls, v):
        """Validate distance metric"""
        return _validate_choice(v, DistanceMetric, "distance metric")

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, v):
        """Validate algorithm"""
        return _validate_choice(v, VectorAlgorithm, "algorithm")

    @field_validator("datatype")
    @classmethod
    def validate_datatype(cls, v):
        """Validate datatype"""
        return _validate_choice(v, VectorDataType, "datatype")


class FieldConfig(BaseModel):
    """Field configuration"""

    name: str = Field(description="Field name")
    type: str = Field(description="Field type")
    attrs: VectorAttrs | None = Field(
        default=None, description="Attributes for vector fields"
    )
    sortable: bool | None = Field(
        default=False, description="Whether field is sortable"
    )
    no_index: bool | None = Field(default=False, description="Whether to skip indexing")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        """Validate field type"""
        return _validate_choice(v, FieldTypeEnum, "field type")

    @model_validator(mode="after")
    def validate_vector_attrs(self):
        """Ensure vector fields (and only vector fields) have attrs"""
        is_vector = self.type == FieldTypeEnum.VECTOR.value
        if is_vector and self.attrs is None:
            raise ValueError("Vector fields must have 'attrs' defined")
        if not is_vector and self.attrs is not None:
            raise ValueError("Only vector fields can have 'attrs'")
        return self

    def to_redisvl_dict(self) -> dict[str, Any]:
        """Field definition in the format expected by redisvl's IndexSchema"""
        field: dict[str, Any] = {"name": self.name, "type": self.type}
        attrs: dict[str, Any] = (
            self.attrs.model_dump(exclude_none=True) if self.attrs else {}
        )
        if self.sortable:
            attrs["sortable"] = True
        if self.no_index:
            attrs["no_index"] = True
        if attrs:
            field["attrs"] = attrs
        return field


class IndexConfig(BaseModel):
    """Index configuration"""

    name: str = Field(description="Index name")
    prefix: str = Field(description="Key prefix for the index")
    storage_type: str = Field(default="hash", description="Storage type")

    @field_validator("storage_type")
    @classmethod
    def validate_storage_type(cls, v):
        """Validate storage type"""
        return _validate_choice(v, StorageType, "storage type")


class SchemaConfig(BaseModel):
    """Redis schema configuration"""

    index: IndexConfig = Field(description="Index configuration")
    fields: list[FieldConfig] = Field(min_length=1, description="Field definitions")

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, v):
        """Validate field configurations"""
        field_names = [f.name for f in v]
        if len(field_names) != len(set(field_names)):
            raise ValueError("Field names must be unique")
        return v

    def to_redisvl_dict(self) -> dict[str, Any]:
        """Schema in the format expected by redisvl's SearchIndex.from_dict()"""
        return {
            "index": self.index.model_dump(),
            "fields": [field.to_redisvl_dict() for field in self.fields],
        }


# --------------------------------------------------------------------------
# Pencarian Hybrid
# --------------------------------------------------------------------------


class HybridSearchConfig(BaseModel):
    """Configuration for hybrid search"""

    text_field_name: str = Field(description="Name of the text field")
    vector_field_name: str = Field(description="Name of the vector field")
    text_scorer: str = Field(default="BM25", description="Text scoring algorithm")
    alpha: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Weight for vector score (0=text only, 1=vector only)",
    )
    num_results: int = Field(
        default=10, gt=0, description="Number of results to return"
    )
    return_fields: list[str] | None = Field(
        default=None, description="Fields to return in results"
    )

    @field_validator("text_scorer")
    @classmethod
    def validate_text_scorer(cls, v):
        """Validate text scorer"""
        return _validate_choice(v, TextScorer, "text scorer", upper=True)


# --------------------------------------------------------------------------
# Akar Konfigurasi
# --------------------------------------------------------------------------


class RedisConfig(BaseModel):
    """Main Redis configuration"""

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    connection: ConnectionConfig = Field(description="Redis connection settings")
    # Field ini dinamai index_schema karena nama "schema" bertabrakan dengan
    # atribut BaseModel. Di file config, kuncinya tetap ditulis "schema".
    index_schema: SchemaConfig = Field(
        alias="schema", description="Redis schema definition"
    )
    hybrid_search: HybridSearchConfig | None = Field(
        default=None, description="Hybrid search configuration"
    )
