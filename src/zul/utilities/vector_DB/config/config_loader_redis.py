"""
Configuration loader for YAML and JSON files
"""
import json
import yaml
from pathlib import Path
from typing import Union
from .config_schema_redis import RedisConfig


class ConfigLoader:
    """Load and validate configuration from YAML or JSON files"""
    
    @staticmethod
    def load(config_path: Union[str, Path]) -> RedisConfig:
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
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Load based on file extension
        if config_path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
        elif config_path.suffix == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
        else:
            raise ValueError(
                f"Unsupported file format: {config_path.suffix}. "
                "Use .yaml, .yml, or .json"
            )
        
        if config_dict is None:
            raise ValueError(f"Configuration file is empty: {config_path}")
        
        # Validate and return
        try:
            return RedisConfig(**config_dict)
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {str(e)}")
    
    @staticmethod
    def save(config: RedisConfig, output_path: Union[str, Path], 
             format: str = 'yaml') -> None:
        """
        Save configuration to YAML or JSON file
        
        Args:
            config: RedisConfig object to save
            output_path: Path where to save the configuration
            format: Output format ('yaml' or 'json')
        """
        output_path = Path(output_path)
        config_dict = config.dict()
        
        if format.lower() in ['yaml', 'yml']:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
        elif format.lower() == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'yaml' or 'json'")