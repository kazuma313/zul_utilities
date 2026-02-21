from pathlib import Path
from redis import Redis
from .config.config_loader_redis import ConfigLoader
from .config.config_schema_redis import RedisConfig
from pathlib import Path
from typing import Union


class RedisHelper:
    def __init__(self, config_path: Union[str, Path]) -> None:
        """
        Initialize RedisHelper with configuration from .yaml or .json file
        
        Args:
            config_path: Path to configuration file (.yaml or .json)
        """
        # Load and validate configuration
        self.config: RedisConfig = ConfigLoader.load(config_path)
        
        # Initialize Redis connection
        try:
            conn = self.config.connection
            redis_url = f"redis://{conn.uri.replace('http://', '').replace('https://', '')}:{conn.port}"
            
            # Add authentication if provided
            if conn.username and conn.password:
                redis_url = f"redis://{conn.username}:{conn.password}@{conn.uri.replace('http://', '').replace('https://', '')}:{conn.port}"
            elif conn.password:
                redis_url = f"redis://:{conn.password}@{conn.uri.replace('http://', '').replace('https://', '')}:{conn.port}"
            
            self.client = Redis.from_url(redis_url)
            
            # Test connection
            self.client.ping()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {str(e)}")

    def _insert(self, data: dict):
        job_data = [
            {
                **job,
                "job_embedding": emb_model.embed(
                    job["job_description"], as_buffer=True
                ),
            }
            for job in data
        ]
        index = self._create_index_params()
        index.load(job_data)

    def _create_index_params(self):
        # Convert config to dict format expected by SearchIndex
        schema_dict = self.config.schema.dict()
        
        index = SearchIndex.from_dict(schema_dict, redis_url=self.client)
        index.create(overwrite=True, drop=True)
        return index

    def _hybrid_search(self, query_text: str, query_dense_vector: list, 
                      limit: int = None):
        # Use config defaults if not provided
        hybrid_config = self.config.hybrid_search
        if hybrid_config is None:
            raise ValueError("Hybrid search configuration not found in config file")
        
        if limit is None:
            limit = hybrid_config.num_results
        
        query = HybridQuery(
            text=query_text,
            text_field_name=hybrid_config.text_field_name,
            vector=query_dense_vector,
            vector_field_name=hybrid_config.vector_field_name,
            return_fields=hybrid_config.return_fields or ["content"],
            text_scorer=hybrid_config.text_scorer,
            alpha=hybrid_config.alpha,
            num_results=limit,
        )
        
        index = self._create_index_params()
        results = index.query(query)

        return results

if __name__ == "__main__":
    # Initialize with config file
    redis_helper = RedisHelper(config_path="redis_config.yaml")

    # Perform hybrid search
    results = redis_helper._hybrid_search(
        query_text="software developer",
        query_dense_vector=[0.1, 0.2, ...],
        limit=20  # Optional, uses config default if not provided
    )