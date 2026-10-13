"""
Configuration loader for BAW Toolkit Packager.
"""

import json
from pathlib import Path
from typing import Optional

from .models import ToolkitConfig
from .core import (
    DEFAULT_TOOLKIT_NAME,
    DEFAULT_TOOLKIT_SHORT_NAME,
    DEFAULT_TOOLKIT_VERSION,
)

DEFAULT_TOOLKIT_DESCRIPTION = "Custom widget toolkit for BAW"
from .utils import get_logger, ConfigurationError

logger = get_logger(__name__)


def load_config(config_path: Optional[Path] = None) -> ToolkitConfig:
    """
    Load toolkit configuration from file or create default.
    
    Args:
        config_path: Path to configuration file (toolkit.config.json)
                    If None, looks for toolkit.config.json in current directory
                    
    Returns:
        ToolkitConfig instance
        
    Raises:
        ConfigurationError: If configuration file is invalid
    """
    # If no path provided, look for default config file
    if config_path is None:
        config_path = Path("toolkit.config.json")
    
    # If config file doesn't exist, return default configuration
    if not config_path.exists():
        logger.info("No configuration file found, using defaults")
        return get_default_config()
    
    # Load and parse configuration file
    try:
        logger.info(f"Loading configuration from: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Validate configuration structure
        if not validate_config_structure(config_data):
            raise ConfigurationError("Invalid configuration structure")
        
        # Create ToolkitConfig from data
        config = ToolkitConfig.from_dict(config_data)
        logger.info(f"Configuration loaded: {config.name} v{config.version}")
        
        return config
        
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        raise ConfigurationError(f"Error loading configuration: {e}")


def get_default_config() -> ToolkitConfig:
    """
    Get default toolkit configuration.
    
    Returns:
        ToolkitConfig with default values
    """
    return ToolkitConfig(
        name=DEFAULT_TOOLKIT_NAME,
        short_name=DEFAULT_TOOLKIT_SHORT_NAME,
        description=DEFAULT_TOOLKIT_DESCRIPTION,
        version=DEFAULT_TOOLKIT_VERSION,
    )


def validate_config_structure(config_data: dict) -> bool:
    """
    Validate configuration structure.
    
    Args:
        config_data: Configuration dictionary
        
    Returns:
        True if valid structure
    """
    # Check for required top-level keys
    if 'toolkit' not in config_data:
        logger.error("Configuration missing 'toolkit' section")
        return False
    
    toolkit = config_data['toolkit']
    
    # Check for required toolkit fields
    required_fields = ['name', 'version']
    for field in required_fields:
        if field not in toolkit:
            logger.error(f"Configuration missing required field: toolkit.{field}")
            return False
    
    return True


def save_config(config: ToolkitConfig, output_path: Path):
    """
    Save configuration to file.
    
    Args:
        config: ToolkitConfig to save
        output_path: Path to save configuration file
    """
    try:
        config_dict = config.to_dict()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2)
        
        logger.info(f"Configuration saved to: {output_path}")
        
    except Exception as e:
        raise ConfigurationError(f"Error saving configuration: {e}")


def create_default_config_file(output_path: Optional[Path] = None):
    """
    Create a default configuration file.
    
    Args:
        output_path: Path to save configuration file
                    Defaults to toolkit.config.json in current directory
    """
    if output_path is None:
        output_path = Path("toolkit.config.json")
    
    if output_path.exists():
        logger.warning(f"Configuration file already exists: {output_path}")
        return
    
    config = get_default_config()
    save_config(config, output_path)
    logger.info(f"Created default configuration file: {output_path}")


def merge_configs(base_config: ToolkitConfig, override_config: dict) -> ToolkitConfig:
    """
    Merge configuration with overrides.
    
    Args:
        base_config: Base configuration
        override_config: Dictionary with override values
        
    Returns:
        Merged ToolkitConfig
    """
    # Convert base config to dict
    config_dict = base_config.to_dict()
    
    # Deep merge override values
    def deep_merge(base: dict, override: dict) -> dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    merged_dict = deep_merge(config_dict, override_config)
    
    return ToolkitConfig.from_dict(merged_dict)

# Made with Bob
