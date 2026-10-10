"""
Custom Type Registry for BAW Toolkit Packager.
Manages custom business object types to enable reuse across widgets.
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CustomTypeRegistry:
    """
    Registry for managing custom business object types.
    Prevents duplicate type definitions and enables sharing across widgets.
    """
    
    def __init__(self, registry_file: Optional[Path] = None):
        """
        Initialize the custom type registry.
        
        Args:
            registry_file: Path to the registry JSON file. If None, uses default location.
        """
        if registry_file is None:
            registry_file = Path(__file__).parent.parent / 'baw_custom_types.json'
        
        self.registry_file = registry_file
        self.custom_types: Dict[str, dict] = {}
        self.modified = False
        self._load_registry()
    
    def _load_registry(self):
        """Load the custom type registry from JSON file."""
        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.custom_types = data.get('custom_types', {})
                    logger.info(f"Loaded {len(self.custom_types)} custom types from registry")
            else:
                logger.info("No existing custom type registry found, starting fresh")
                self.custom_types = {}
        except Exception as e:
            logger.warning(f"Failed to load custom type registry: {e}")
            self.custom_types = {}
    
    def save_registry(self):
        """Save the custom type registry to JSON file if modified."""
        if not self.modified:
            return
        
        try:
            data = {
                "description": "Custom Business Object Type Mappings - Tracks custom types and their BAW class IDs to enable reuse across widgets",
                "version": "1.0.0",
                "custom_types": self.custom_types,
                "notes": {
                    "usage": "This file tracks custom business objects to prevent duplicates and enable sharing across widgets",
                    "classId_format": "Custom types use /12.{guid} format where the GUID is generated once and reused",
                    "widgets": "List of widgets that use this custom type",
                    "auto_update": "This file is automatically updated when new custom types are generated"
                }
            }
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.custom_types)} custom types to registry")
            self.modified = False
        except Exception as e:
            logger.error(f"Failed to save custom type registry: {e}")
    
    def get_type(self, type_name: str) -> Optional[str]:
        """
        Get the class ID for a custom type if it exists.
        
        Args:
            type_name: Name of the custom type
            
        Returns:
            Class ID if type exists, None otherwise
        """
        type_info = self.custom_types.get(type_name)
        if type_info:
            return type_info.get('classId')
        return None
    
    def register_type(self, type_name: str, class_id: str, widget_name: str, description: str = "") -> str:
        """
        Register a new custom type or update an existing one.
        
        Args:
            type_name: Name of the custom type
            class_id: BAW class ID for the type
            widget_name: Name of the widget using this type
            description: Optional description of the type
            
        Returns:
            The class ID (either existing or newly registered)
        """
        if type_name in self.custom_types:
            # Type already exists, add widget to the list if not already there
            existing = self.custom_types[type_name]
            widgets = existing.get('widgets', [])
            if widget_name not in widgets:
                widgets.append(widget_name)
                existing['widgets'] = widgets
                self.modified = True
                logger.info(f"Added widget '{widget_name}' to existing custom type '{type_name}'")
            return existing['classId']
        else:
            # Register new type
            self.custom_types[type_name] = {
                'classId': class_id,
                'description': description,
                'widgets': [widget_name],
                'created': datetime.utcnow().isoformat() + 'Z'
            }
            self.modified = True
            logger.info(f"Registered new custom type '{type_name}' with class ID '{class_id}' for widget '{widget_name}'")
            return class_id
    
    def is_type_registered(self, type_name: str) -> bool:
        """
        Check if a custom type is already registered.
        
        Args:
            type_name: Name of the custom type
            
        Returns:
            True if type is registered, False otherwise
        """
        return type_name in self.custom_types
    
    def get_widgets_using_type(self, type_name: str) -> List[str]:
        """
        Get list of widgets that use a specific custom type.
        
        Args:
            type_name: Name of the custom type
            
        Returns:
            List of widget names
        """
        type_info = self.custom_types.get(type_name)
        if type_info:
            return type_info.get('widgets', [])
        return []
    
    def list_all_types(self) -> Dict[str, dict]:
        """
        Get all registered custom types.
        
        Returns:
            Dictionary of all custom types
        """
        return self.custom_types.copy()


# Global registry instance
_registry = None

def get_custom_type_registry() -> CustomTypeRegistry:
    """Get the global custom type registry instance."""
    global _registry
    if _registry is None:
        _registry = CustomTypeRegistry()
    return _registry

# Made with Bob
