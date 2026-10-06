"""
Configuration loader for YAML and JSON files

Cara pakai:
    from zul.utilities.vector_DB.config.config_loader import ConfigLoader

    config = ConfigLoader.load("milvus_config.json")
    config.connection.uri
    config.collections[0].milvus_schema.fields
"""

from pathlib import Path

from .config_file import load_config
from .config_schema import MilvusConfig


class ConfigLoader:
    """Load and validate configuration from YAML or JSON files"""

    @staticmethod
    def load(config_path: str | Path) -> MilvusConfig:
        """
        Load configuration from YAML or JSON file

        Args:
            config_path: Path to configuration file (.yaml, .yml, or .json)

        Returns:
            Validated MilvusConfig object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If file format is unsupported or validation fails
        """
        return load_config(MilvusConfig, config_path)
