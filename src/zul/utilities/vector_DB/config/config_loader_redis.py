"""
Configuration loader for YAML and JSON files

Cara pakai:
    from zul.utilities.vector_DB.config.config_loader_redis import ConfigLoader

    config = ConfigLoader.load("redis_config.yaml")
    config.connection.host
    config.index_schema.fields

    ConfigLoader.save(config, "redis_config.json", format="json")
"""

from pathlib import Path

from .config_file import load_config, write_config_file
from .config_schema_redis import RedisConfig


class ConfigLoader:
    """Load and validate configuration from YAML or JSON files"""

    @staticmethod
    def load(config_path: str | Path) -> RedisConfig:
        """
        Load configuration from YAML or JSON file

        Args:
            config_path: Path to configuration file (.yaml, .yml, or .json)

        Returns:
            Validated RedisConfig object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If file format is unsupported or validation fails
        """
        return load_config(RedisConfig, config_path)

    @staticmethod
    def save(
        config: RedisConfig, output_path: str | Path, format: str = "yaml"
    ) -> None:
        """
        Save configuration to YAML or JSON file

        Args:
            config: RedisConfig object to save
            output_path: Path where to save the configuration
            format: Output format ('yaml' or 'json')
        """
        config_dict = config.model_dump(by_alias=True, exclude_none=True)
        write_config_file(config_dict, output_path, format)
