"""
Configuration loader for YAML and JSON files
"""
import json
import yaml
from pathlib import Path
from typing import Union
from .config_schema import MilvusConfig


class ConfigLoader:
    """Load and validate configuration from YAML or JSON files"""
    
    @staticmethod
    def load(config_path: Union[str, Path]) -> MilvusConfig:
        """
        Load configuration from YAML or JSON file
        
        Args:
            config_path: Path to configuration file (.yaml, .yml, or .json)
            
        Returns:
            Validated MilvusConfig object
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Load based on file extension
        if config_path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
        elif config_path.suffix == '.json':
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
        else:
            raise ValueError(
                f"Unsupported file format: {config_path.suffix}. "
                "Use .yaml, .yml, or .json"
            )
        
        # Validate and return
        return MilvusConfig(**config_dict)