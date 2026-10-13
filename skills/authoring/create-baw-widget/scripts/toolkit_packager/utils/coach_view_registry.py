"""
Coach View Registry for BAW Toolkit Packager.
Manages coach view IDs and related component IDs to enable version control.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CoachViewRegistry:
    """
    Registry for managing coach view IDs and related component IDs.
    Maintains stable IDs across packaging operations for version control.
    """
    
    def __init__(self, registry_file: Optional[Path] = None):
        """
        Initialize the coach view registry.
        
        Args:
            registry_file: Path to the registry JSON file. If None, uses default location.
        """
        if registry_file is None:
            registry_file = Path(__file__).parent.parent / 'baw_coach_views.json'
        
        self.registry_file = registry_file
        self.coach_views: Dict[str, dict] = {}
        self.modified = False
        self._load_registry()
    
    def _load_registry(self):
        """Load the coach view registry from JSON file."""
        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.coach_views = data.get('coach_views', {})
                    logger.info(f"Loaded {len(self.coach_views)} coach views from registry")
            else:
                logger.info("No existing coach view registry found, starting fresh")
                self.coach_views = {}
        except Exception as e:
            logger.warning(f"Failed to load coach view registry: {e}")
            self.coach_views = {}
    
    def save_registry(self):
        """Save the coach view registry to JSON file if modified."""
        if not self.modified:
            return
        
        try:
            data = {
                "description": "Coach View ID Mappings - Tracks widget coach view IDs and related component IDs to enable version control",
                "version": "1.0.0",
                "coach_views": self.coach_views,
                "notes": {
                    "usage": "This file tracks coach view IDs and all related component IDs to maintain consistency across packaging operations",
                    "id_types": {
                        "coachViewId": "Main coach view ID (64.xxx)",
                        "previewHtmlId": "Preview HTML managed asset ID (61.xxx)",
                        "previewJsId": "Preview JS managed asset ID (61.xxx)",
                        "iconId": "Widget icon SVG managed asset ID (61.xxx)",
                        "bindingIds": "Map of binding names to their IDs (65.xxx)",
                        "configOptionIds": "Map of config option names to their IDs (66.xxx)"
                    },
                    "version_control": "Enables proper version control by maintaining stable IDs across packaging operations",
                    "auto_update": "This file is automatically updated when widgets are packaged"
                }
            }
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.coach_views)} coach views to registry")
            self.modified = False
        except Exception as e:
            logger.error(f"Failed to save coach view registry: {e}")
    
    def get_coach_view_id(self, widget_name: str) -> Optional[str]:
        """
        Get the coach view ID for a widget if it exists.
        
        Args:
            widget_name: Name of the widget
            
        Returns:
            Coach view ID if exists, None otherwise
        """
        widget_info = self.coach_views.get(widget_name)
        if widget_info:
            return widget_info.get('coachViewId')
        return None
    
    def get_preview_html_id(self, widget_name: str) -> Optional[str]:
        """
        Get the preview HTML managed asset ID for a widget if it exists.
        
        Args:
            widget_name: Name of the widget
            
        Returns:
            Preview HTML ID if exists, None otherwise
        """
        widget_info = self.coach_views.get(widget_name)
        if widget_info:
            return widget_info.get('previewHtmlId')
        return None
    
    def get_preview_js_id(self, widget_name: str) -> Optional[str]:
        """
        Get the preview JS managed asset ID for a widget if it exists.
        
        Args:
            widget_name: Name of the widget
            
        Returns:
            Preview JS ID if exists, None otherwise
        """
        widget_info = self.coach_views.get(widget_name)
        if widget_info:
            return widget_info.get('previewJsId')
        return None
    
    def get_icon_id(self, widget_name: str) -> Optional[str]:
        """
        Get the icon managed asset ID for a widget if it exists.
        
        Args:
            widget_name: Name of the widget
            
        Returns:
            Icon ID if exists, None otherwise
        """
        widget_info = self.coach_views.get(widget_name)
        if widget_info:
            return widget_info.get('iconId')
        return None
    
    def get_binding_id(self, widget_name: str, binding_name: str) -> Optional[str]:
        """
        Get the binding ID for a specific binding in a widget.
        
        Args:
            widget_name: Name of the widget
            binding_name: Name of the binding
            
        Returns:
            Binding ID if exists, None otherwise
        """
        widget_info = self.coach_views.get(widget_name)
        if widget_info and 'bindingIds' in widget_info:
            return widget_info['bindingIds'].get(binding_name)
        return None
    
    def get_config_option_id(self, widget_name: str, option_name: str) -> Optional[str]:
        """
        Get the config option ID for a specific option in a widget.
        
        Args:
            widget_name: Name of the widget
            option_name: Name of the config option
            
        Returns:
            Config option ID if exists, None otherwise
        """
        widget_info = self.coach_views.get(widget_name)
        if widget_info and 'configOptionIds' in widget_info:
            return widget_info['configOptionIds'].get(option_name)
        return None
    
    def register_coach_view(
        self,
        widget_name: str,
        coach_view_id: str,
        preview_html_id: Optional[str] = None,
        preview_js_id: Optional[str] = None,
        description: str = "",
        icon_id: Optional[str] = None
    ) -> str:
        """
        Register or update a coach view with its IDs.
        
        Args:
            widget_name: Name of the widget
            coach_view_id: Coach view ID
            preview_html_id: Optional preview HTML managed asset ID
            preview_js_id: Optional preview JS managed asset ID
            description: Optional description
            icon_id: Optional icon managed asset ID
            
        Returns:
            The coach view ID
        """
        if widget_name in self.coach_views:
            # Update existing entry
            existing = self.coach_views[widget_name]
            existing['coachViewId'] = coach_view_id
            if preview_html_id:
                existing['previewHtmlId'] = preview_html_id
            if preview_js_id:
                existing['previewJsId'] = preview_js_id
            if icon_id:
                existing['iconId'] = icon_id
            if description:
                existing['description'] = description
            existing['last_packaged'] = datetime.utcnow().isoformat() + 'Z'
            self.modified = True
            logger.info(f"Updated coach view registry for widget '{widget_name}'")
        else:
            # Create new entry
            self.coach_views[widget_name] = {
                'coachViewId': coach_view_id,
                'description': description,
                'created': datetime.utcnow().isoformat() + 'Z',
                'last_packaged': datetime.utcnow().isoformat() + 'Z',
                'bindingIds': {},
                'configOptionIds': {}
            }
            if preview_html_id:
                self.coach_views[widget_name]['previewHtmlId'] = preview_html_id
            if preview_js_id:
                self.coach_views[widget_name]['previewJsId'] = preview_js_id
            if icon_id:
                self.coach_views[widget_name]['iconId'] = icon_id
            self.modified = True
            logger.info(f"Registered new coach view for widget '{widget_name}' with ID: {coach_view_id}")
        
        return coach_view_id
    
    def register_icon_id(self, widget_name: str, icon_id: str):
        """
        Register an icon ID for a widget.
        
        Args:
            widget_name: Name of the widget
            icon_id: Icon managed asset ID
        """
        if widget_name not in self.coach_views:
            logger.warning(f"Widget '{widget_name}' not found in registry, creating entry")
            self.coach_views[widget_name] = {
                'bindingIds': {},
                'configOptionIds': {},
                'created': datetime.utcnow().isoformat() + 'Z'
            }
        
        self.coach_views[widget_name]['iconId'] = icon_id
        self.modified = True
        logger.debug(f"Registered icon for widget '{widget_name}': {icon_id}")
    
    def register_binding_id(self, widget_name: str, binding_name: str, binding_id: str):
        """
        Register a binding ID for a widget.
        
        Args:
            widget_name: Name of the widget
            binding_name: Name of the binding
            binding_id: Binding ID
        """
        if widget_name not in self.coach_views:
            logger.warning(f"Widget '{widget_name}' not found in registry, creating entry")
            self.coach_views[widget_name] = {
                'bindingIds': {},
                'configOptionIds': {},
                'created': datetime.utcnow().isoformat() + 'Z'
            }
        
        if 'bindingIds' not in self.coach_views[widget_name]:
            self.coach_views[widget_name]['bindingIds'] = {}
        
        self.coach_views[widget_name]['bindingIds'][binding_name] = binding_id
        self.modified = True
        logger.debug(f"Registered binding '{binding_name}' for widget '{widget_name}': {binding_id}")
    
    def register_config_option_id(self, widget_name: str, option_name: str, option_id: str):
        """
        Register a config option ID for a widget.
        
        Args:
            widget_name: Name of the widget
            option_name: Name of the config option
            option_id: Config option ID
        """
        if widget_name not in self.coach_views:
            logger.warning(f"Widget '{widget_name}' not found in registry, creating entry")
            self.coach_views[widget_name] = {
                'bindingIds': {},
                'configOptionIds': {},
                'created': datetime.utcnow().isoformat() + 'Z'
            }
        
        if 'configOptionIds' not in self.coach_views[widget_name]:
            self.coach_views[widget_name]['configOptionIds'] = {}
        
        self.coach_views[widget_name]['configOptionIds'][option_name] = option_id
        self.modified = True
        logger.debug(f"Registered config option '{option_name}' for widget '{widget_name}': {option_id}")
    
    def is_widget_registered(self, widget_name: str) -> bool:
        """
        Check if a widget is already registered.
        
        Args:
            widget_name: Name of the widget
            
        Returns:
            True if widget is registered, False otherwise
        """
        return widget_name in self.coach_views
    
    def list_all_widgets(self) -> Dict[str, dict]:
        """
        Get all registered widgets.
        
        Returns:
            Dictionary of all widgets
        """
        return self.coach_views.copy()


# Global registry instance
_registry = None

def get_coach_view_registry() -> CoachViewRegistry:
    """Get the global coach view registry instance."""
    global _registry
    if _registry is None:
        _registry = CoachViewRegistry()
    return _registry

# Made with Bob