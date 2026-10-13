"""
Widget data model for BAW Toolkit Packager.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, List


@dataclass
class Widget:
    """
    Represents a BAW widget with all its files and metadata.
    """
    name: str
    path: Path
    widget_path: Path
    preview_path: Optional[Path] = None
    files: Dict[str, Path] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure paths are Path objects."""
        if not isinstance(self.path, Path):
            self.path = Path(self.path)
        if not isinstance(self.widget_path, Path):
            self.widget_path = Path(self.widget_path)
        if self.preview_path and not isinstance(self.preview_path, Path):
            self.preview_path = Path(self.preview_path)
    
    def get_layout_html(self) -> str:
        """
        Read and return the Layout.html content.
        
        Returns:
            HTML layout content
        """
        layout_path = self.files.get('Layout.html')
        if not layout_path or not layout_path.exists():
            raise FileNotFoundError(f"Layout.html not found for widget {self.name}")
        
        return layout_path.read_text(encoding='utf-8')
    
    def get_inline_css(self) -> str:
        """
        Read and return the InlineCSS.css content.
        
        Returns:
            CSS content
        """
        css_path = self.files.get('InlineCSS.css')
        if not css_path or not css_path.exists():
            raise FileNotFoundError(f"InlineCSS.css not found for widget {self.name}")
        
        return css_path.read_text(encoding='utf-8')
    
    def get_inline_js(self) -> str:
        """
        Read and return the inlineJavascript.js content.
        
        Returns:
            JavaScript content
        """
        js_path = self.files.get('inlineJavascript.js')
        if not js_path or not js_path.exists():
            raise FileNotFoundError(f"inlineJavascript.js not found for widget {self.name}")
        
        return js_path.read_text(encoding='utf-8')
    
    def get_config(self) -> Optional[dict]:
        """
        Read and return the widget config.json if it exists.
        
        Returns:
            Parsed config.json or None
        """
        config_path = self.files.get('config.json')
        if config_path and config_path.exists():
            return json.loads(config_path.read_text(encoding='utf-8'))
        return None
    
    def has_config(self) -> bool:
        """
        Check if widget has a config.json file.
        
        Returns:
            True if config.json exists
        """
        config_path = self.files.get('config.json')
        return config_path is not None and config_path.exists()
    
    def get_business_objects(self) -> List[dict]:
        """
        Get business object definitions from config.json.
        
        Returns:
            List of business object definitions
        """
        config = self.get_config()
        if not config or 'businessObjects' not in config:
            return []
        
        business_objects = []
        for bo_ref in config['businessObjects']:
            bo_file = bo_ref.get('file')
            if bo_file:
                bo_path = self.files.get(bo_file)
                if bo_path and bo_path.exists():
                    bo_data = json.loads(bo_path.read_text(encoding='utf-8'))
                    business_objects.append(bo_data)
        
        return business_objects
    
    def get_json_schema(self) -> dict:
        """
        Read and return the JSON schema (config.json or business object definitions).
        This method is deprecated - use get_config() instead.
        
        Returns:
            Parsed JSON schema
        """
        # Only look for config.json now
        config_path = self.files.get('config.json')
        if config_path and config_path.exists():
            return json.loads(config_path.read_text(encoding='utf-8'))
        
        raise FileNotFoundError(f"No config.json found for widget {self.name}")
    
    def has_preview_files(self) -> bool:
        """
        Check if widget has preview files.
        
        Returns:
            True if preview files exist
        """
        if not self.preview_path or not self.preview_path.exists():
            return False
        
        # Check for HTML and JS preview files
        html_files = list(self.preview_path.glob("*.html"))
        js_files = list(self.preview_path.glob("*.js"))
        
        return len(html_files) > 0 and len(js_files) > 0
    
    def get_preview_html(self) -> Optional[str]:
        """
        Get preview HTML file content.
        
        Returns:
            HTML content or None
        """
        if not self.preview_path or not self.preview_path.exists():
            return None
        
        html_files = list(self.preview_path.glob("*.html"))
        if html_files:
            return html_files[0].read_text(encoding='utf-8')
        
        return None
    
    def get_preview_js(self) -> Optional[str]:
        """
        Get preview JavaScript file content.
        
        Returns:
            JavaScript content or None
        """
        if not self.preview_path or not self.preview_path.exists():
            return None
        
        js_files = list(self.preview_path.glob("*.js"))
        if js_files:
            return js_files[0].read_text(encoding='utf-8')
        
        return None
    
    def get_event_handler(self, event_name: str) -> Optional[str]:
        """
        Get event handler code from events folder.
        
        Args:
            event_name: Name of the event (e.g., 'change', 'load', 'view')
            
        Returns:
            Event handler JavaScript code or None if not found
        """
        event_file_key = f"events/{event_name}.js"
        event_path = self.files.get(event_file_key)
        
        if event_path and event_path.exists():
            return event_path.read_text(encoding='utf-8').strip()
        
        return None
    
    def has_event_handler(self, event_name: str) -> bool:
        """
        Check if widget has a specific event handler.
        
        Args:
            event_name: Name of the event (e.g., 'change', 'load', 'view')
            
        Returns:
            True if event handler file exists
        """
        event_file_key = f"events/{event_name}.js"
        event_path = self.files.get(event_file_key)
        return event_path is not None and event_path.exists()
    
    def get_all_event_handlers(self) -> Dict[str, str]:
        """
        Get all event handlers from the events folder.
        
        Returns:
            Dictionary mapping event name to handler code
        """
        handlers = {}
        
        for file_key, file_path in self.files.items():
            if file_key.startswith('events/') and file_key.endswith('.js'):
                event_name = file_key.replace('events/', '').replace('.js', '')
                handlers[event_name] = file_path.read_text(encoding='utf-8').strip()
        
        return handlers
    
    def get_preview_html_path(self) -> Optional[Path]:
        """Get path to preview HTML file."""
        if not self.preview_path or not self.preview_path.exists():
            return None
        
        html_files = list(self.preview_path.glob("*.html"))
        return html_files[0] if html_files else None
    
    def get_preview_js_path(self) -> Optional[Path]:
        """Get path to preview JavaScript file."""
        if not self.preview_path or not self.preview_path.exists():
            return None
        
        js_files = list(self.preview_path.glob("*.js"))
        return js_files[0] if js_files else None
    
    def has_icon(self) -> bool:
        """
        Check if widget has an SVG icon file.
        
        Returns:
            True if {WidgetName}.svg exists in widget directory
        """
        icon_path = self.path / f"{self.name}.svg"
        return icon_path.exists()
    
    def get_icon_path(self) -> Optional[Path]:
        """
        Get path to widget icon SVG file.
        
        Returns:
            Path to {WidgetName}.svg or None if not found
        """
        icon_path = self.path / f"{self.name}.svg"
        return icon_path if icon_path.exists() else None
    
    def get_icon_content(self) -> Optional[str]:
        """
        Get widget icon SVG content.
        
        Returns:
            SVG content or None if icon doesn't exist
        """
        icon_path = self.get_icon_path()
        if icon_path:
            return icon_path.read_text(encoding='utf-8')
        return None
    
    def list_all_files(self) -> List[Path]:
        """
        List all files associated with this widget.
        
        Returns:
            List of file paths
        """
        all_files = list(self.files.values())
        
        if self.preview_path and self.preview_path.exists():
            all_files.extend(self.preview_path.glob("*.*"))
        
        return all_files
    
    def get_file_count(self) -> int:
        """
        Get total number of files in widget.
        
        Returns:
            File count
        """
        return len(self.list_all_files())
    
    def __repr__(self) -> str:
        """String representation of widget."""
        return f"Widget(name='{self.name}', files={len(self.files)}, has_preview={self.has_preview_files()})"

# Made with Bob
