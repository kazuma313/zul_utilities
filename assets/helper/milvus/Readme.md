# Milvus Helper - Configuration-Based Utilities

Simple, clean, and powerful utilities for Milvus with YAML/JSON configuration support.


## Quick Start

### 1. Create Configuration File

**config.yaml:**
```yaml
connection:
  uri: "http://localhost"
  port: 19530
  db_name: "my_database"

collections:
  - collection_name: "my_collection"
    shards_num: 2
    schema:
      auto_id: true
      enable_dynamic_field: true
      fields:
        - field_name: "id"
          datatype: "VARCHAR"
          max_length: 128
          is_primary: true
        - field_name: "embedding"
          datatype: "FLOAT_VECTOR"
          dim: 768
      functions: []
    indexes:
      - field_name: "embedding"
        index_name: "emb_idx"
        index_type: "HNSW"
        metric_type: "COSINE"
        params:
          M: 16
          efConstruction: 200
```

**Or use JSON (config.json):**
```json
{
  "connection": {
    "uri": "http://localhost",
    "port": 19530,
    "db_name": "my_database"
  },
  "collections": [
    {
      "collection_name": "my_collection",
      "shards_num": 2,
      "schema": {
        "auto_id": true,
        "enable_dynamic_field": true,
        "fields": [
          {
            "field_name": "id",
            "datatype": "VARCHAR",
            "max_length": 128,
            "is_primary": true
          },
          {
            "field_name": "embedding",
            "datatype": "FLOAT_VECTOR",
            "dim": 768
          }
        ],
        "functions": []
      },
      "indexes": [
        {
          "field_name": "embedding",
          "index_name": "emb_idx",
          "index_type": "HNSW",
          "metric_type": "COSINE",
          "params": {
            "M": 16,
            "efConstruction": 200
          }
        }
      ]
    }
  ]
}
```

### 2. Use in Python

```python
from milvus_helper import MilvusHelper

# Initialize (automatically creates collections from config)
helper = MilvusHelper("config.yaml")

# Insert data
data = {
    "embedding": [0.1] * 768
}
helper.insert("my_collection", data)

# Search
query_vector = [0.2] * 768
results = helper.search(
    collection_name="my_collection",
    query_vectors=[query_vector],
    limit=10
)

print(results)
```

## Features

✅ **Simple**: One config file for everything  
✅ **Auto-create**: Collections created automatically on init  
✅ **Type-safe**: Pydantic validation  
✅ **Flexible**: YAML or JSON  
✅ **Clean API**: Minimal, intuitive methods  

## Configuration Reference

### Connection

```yaml
connection:
  uri: "http://localhost"  # Milvus URI
  port: 19530              # Milvus port
  db_name: "my_database"   # Database name (optional)
  user: null               # Username (optional)
  password: null           # Password (optional)
```

### Collection Schema

```yaml
collections:
  - collection_name: "my_collection"
    shards_num: 2          # Number of shards
    description: "Optional description"
    
    schema:
      auto_id: true                    # Auto-generate IDs
      enable_dynamic_field: true       # Allow dynamic fields
      description: "Schema description"
      
      fields:
        - field_name: "id"
          datatype: "VARCHAR"          # See data types below
          max_length: 128              # For VARCHAR
          is_primary: true
        
        - field_name: "embedding"
          datatype: "FLOAT_VECTOR"
          dim: 768                     # Vector dimension
        
        - field_name: "metadata"
          datatype: "JSON"             # JSON field
      
      functions: []                    # BM25 functions (see advanced)
    
    indexes:
      - field_name: "embedding"
        index_name: "emb_idx"
        index_type: "HNSW"             # See index types below
        metric_type: "COSINE"          # See metric types below
        params:                        # Index-specific params
          M: 16
          efConstruction: 200
```

### Data Types

- `VARCHAR` - Variable-length string (requires `max_length`)
- `INT64` - 64-bit integer
- `FLOAT` - Floating point
- `FLOAT_VECTOR` - Dense vector (requires `dim`)
- `SPARSE_FLOAT_VECTOR` - Sparse vector
- `BOOL` - Boolean
- `JSON` - JSON data

### Index Types

- `FLAT` - Brute force (exact search)
- `IVF_FLAT` - Inverted file
- `HNSW` - Hierarchical graph (recommended)
- `IVF_PQ` - Product quantization
- `SPARSE_INVERTED_INDEX` - For sparse vectors

### Metric Types

- `COSINE` - Cosine similarity
- `L2` - Euclidean distance
- `IP` - Inner product
- `BM25` - For text search

## Advanced: BM25 Hybrid Search

```yaml
collections:
  - collection_name: "documents"
    schema:
      fields:
        - field_name: "content"
          datatype: "VARCHAR"
          max_length: 65535
          enable_analyzer: true
        
        - field_name: "dense_vector"
          datatype: "FLOAT_VECTOR"
          dim: 1024
        
        - field_name: "sparse_vector"
          datatype: "SPARSE_FLOAT_VECTOR"
      
      functions:
        - name: "bm25_fn"
          function_type: "BM25"
          input_field_names: ["content"]
          output_field_names: ["sparse_vector"]
    
    indexes:
      - field_name: "dense_vector"
        index_name: "dense_idx"
        index_type: "HNSW"
        metric_type: "COSINE"
      
      - field_name: "sparse_vector"
        index_name: "sparse_idx"
        index_type: "SPARSE_INVERTED_INDEX"
        metric_type: "BM25"
```

## API Reference

### MilvusHelper

```python
helper = MilvusHelper("config.yaml")  # or "config.json"
```

### Insert Data

```python
# Single record
helper.insert("collection_name", {"id": "1", "embedding": [...]})

# Multiple records
helper.insert("collection_name", [
    {"id": "1", "embedding": [...]},
    {"id": "2", "embedding": [...]}
])
```

### Search

```python
results = helper.search(
    collection_name="my_collection",
    query_vectors=[[0.1, 0.2, ...]],
    anns_field="embedding",
    limit=10,
    output_fields=["id", "distance"]
)
```

### Query with Filter

```python
results = helper.query(
    collection_name="my_collection",
    filter_expr='id in ["doc_001", "doc_002"]',
    output_fields=["id", "embedding"],
    limit=100
)
```

### Delete

```python
helper.delete(
    collection_name="my_collection",
    filter_expr='id == "doc_001"'
)
```

### Collection Management

```python
# List collections
collections = helper.list_collections()

# Get stats
stats = helper.get_collection_stats("my_collection")

# Drop collection
helper.drop_collection("my_collection")
```

## Examples

See `examples.py` for comprehensive usage examples:

```python
python examples.py
```

## Multiple Collections

You can define multiple collections in one config:

```yaml
connection:
  uri: "http://localhost"
  port: 19530
  db_name: "multi_db"

collections:
  - collection_name: "documents"
    schema:
      # ... document schema
    indexes:
      # ... document indexes
  
  - collection_name: "images"
    schema:
      # ... image schema
    indexes:
      # ... image indexes
  
  - collection_name: "products"
    schema:
      # ... product schema
    indexes:
      # ... product indexes
```

All collections are created automatically when initializing `MilvusHelper`.

## File Structure

```
.
├── config_schema.py       # Pydantic models
├── config_loader.py       # Config loader
├── milvus_helper.py       # Main helper class
├── examples.py            # Usage examples
├── requirements.txt       # Dependencies
├── config.yaml            # Example YAML config
├── config.json            # Example JSON config
├── config_advanced.yaml   # Advanced example
└── README.md              # This file
```

## Error Handling

The helper includes comprehensive error handling with logging:

```python
import logging

logging.basicConfig(level=logging.INFO)

try:
    helper = MilvusHelper("config.yaml")
    helper.insert("my_collection", data)
except Exception as e:
    print(f"Error: {e}")
```

## Best Practices

1. **Validate config structure** before deployment
2. **Use version control** for config files
3. **Separate configs** for dev/staging/prod
4. **Set appropriate dimensions** for your embedding model
5. **Choose right index type** based on data size:
   - Small (<1M): `FLAT`
   - Medium (1M-10M): `IVF_FLAT`
   - Large (>10M): `HNSW`
6. **Enable dynamic fields** for flexibility
7. **Use BM25** for text search combined with vectors

## Troubleshooting

**Connection failed?**
- Check Milvus is running: `docker ps | grep milvus`
- Verify URI and port
- Check network connectivity

**Validation errors?**
- Ensure all required fields are present
- Check data types match schema
- Verify vector dimensions

**Import error?**
- Install dependencies: `pip install -r requirements.txt`
- Check Python version >= 3.8
