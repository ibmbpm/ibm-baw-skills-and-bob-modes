"""
Configuration data model for BAW Toolkit Packager.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class DependencyConfig:
    """Represents a toolkit dependency."""
    snapshot_id: str
    name: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'snapshotId': self.snapshot_id,
            'name': self.name
        }


@dataclass
class OutputConfig:
    """Output configuration."""
    directory: str = "output"
    filename: str = "Custom_Widgets_{version}.twx"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'directory': self.directory,
            'filename': self.filename
        }


@dataclass
class WidgetsConfig:
    """Widget inclusion/exclusion configuration."""
    include: List[str] = field(default_factory=lambda: ["*"])
    exclude: List[str] = field(default_factory=list)
    source_directory: str = "widgets"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'include': self.include,
            'exclude': self.exclude,
            'source_directory': self.source_directory
        }


@dataclass
class ToolkitConfig:
    """
    Complete toolkit configuration.
    """
    # Toolkit metadata
    name: str = "Custom Widgets"
    short_name: str = "CW"
    description: str = "Custom widget toolkit for BAW"
    version: str = "1.0.0"
    baw_version: str = "25.0.1"  # BAW template version to use
    toolkit_id: Optional[str] = None  # Persistent toolkit ID for BAW
    branch_id: Optional[str] = None  # Persistent branch ID for BAW (for upgrade compatibility)
    is_toolkit: bool = True
    is_hidden: bool = False
    is_system: bool = False
    
    # Dependencies
    system_data: Optional[DependencyConfig] = None
    ui_toolkit: Optional[DependencyConfig] = None
    
    # Output configuration
    output: OutputConfig = field(default_factory=OutputConfig)
    
    # Widget configuration
    widgets: WidgetsConfig = field(default_factory=WidgetsConfig)
    
    def __post_init__(self):
        """Initialize default dependencies if not provided."""
        if self.system_data is None:
            self.system_data = DependencyConfig(
                snapshot_id="2064.1080ded6-d153-4654-947c-2d16fce170db",
                name="8.6.0.0_TC"
            )
        
        if self.ui_toolkit is None:
            self.ui_toolkit = DependencyConfig(
                snapshot_id="2064.304ac881-16c3-47d2-97d5-6e4c4a893177",
                name="8.6.0.0"
            )
        
        # Ensure output and widgets are proper objects
        if isinstance(self.output, dict):
            self.output = OutputConfig(**self.output)
        
        if isinstance(self.widgets, dict):
            self.widgets = WidgetsConfig(**self.widgets)
    
    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation
        """
        toolkit_dict = {
            'name': self.name,
            'shortName': self.short_name,
            'description': self.description,
            'version': self.version,
            'bawVersion': self.baw_version,
            'isToolkit': self.is_toolkit,
            'isHidden': self.is_hidden,
            'isSystem': self.is_system
        }
        
        # Add toolkit ID if present
        if self.toolkit_id:
            toolkit_dict['id'] = self.toolkit_id
        
        # Add branch ID if present
        if self.branch_id:
            toolkit_dict['branchId'] = self.branch_id
        
        return {
            'toolkit': toolkit_dict,
            'dependencies': {
                'systemData': self.system_data.to_dict() if self.system_data else None,
                'uiToolkit': self.ui_toolkit.to_dict() if self.ui_toolkit else None
            },
            'output': self.output.to_dict(),
            'widgets': self.widgets.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ToolkitConfig':
        """
        Create configuration from dictionary.
        
        Args:
            data: Dictionary with configuration data
            
        Returns:
            ToolkitConfig instance
        """
        toolkit_data = data.get('toolkit', {})
        deps_data = data.get('dependencies', {})
        output_data = data.get('output', {})
        widgets_data = data.get('widgets', {})
        
        # Parse dependencies
        system_data = None
        if 'systemData' in deps_data and deps_data['systemData']:
            system_data = DependencyConfig(
                snapshot_id=deps_data['systemData']['snapshotId'],
                name=deps_data['systemData']['name']
            )
        
        ui_toolkit = None
        if 'uiToolkit' in deps_data and deps_data['uiToolkit']:
            ui_toolkit = DependencyConfig(
                snapshot_id=deps_data['uiToolkit']['snapshotId'],
                name=deps_data['uiToolkit']['name']
            )
        
        return cls(
            name=toolkit_data.get('name', 'Custom Widgets'),
            short_name=toolkit_data.get('shortName', 'CW'),
            description=toolkit_data.get('description', 'Custom widget toolkit for BAW'),
            version=toolkit_data.get('version', '1.0.0'),
            baw_version=toolkit_data.get('bawVersion', '25.0.1'),  # Load BAW version
            toolkit_id=toolkit_data.get('id'),  # Load persistent toolkit ID
            branch_id=toolkit_data.get('branchId'),  # Load persistent branch ID
            is_toolkit=toolkit_data.get('isToolkit', True),
            is_hidden=toolkit_data.get('isHidden', False),
            is_system=toolkit_data.get('isSystem', False),
            system_data=system_data,
            ui_toolkit=ui_toolkit,
            output=OutputConfig(**output_data) if output_data else OutputConfig(),
            widgets=WidgetsConfig(**widgets_data) if widgets_data else WidgetsConfig()
        )
    
    def get_output_filename(self) -> str:
        """
        Get the output filename with version substituted.
        
        Returns:
            Filename with version
        """
        return self.output.filename.replace('{version}', self.version)
    
    def should_include_widget(self, widget_name: str) -> bool:
        """
        Check if a widget should be included based on configuration.
        
        Args:
            widget_name: Name of the widget
            
        Returns:
            True if widget should be included
        """
        # Check exclusions first
        if widget_name in self.widgets.exclude:
            return False
        
        # Check inclusions
        if '*' in self.widgets.include:
            return True
        
        return widget_name in self.widgets.include
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"ToolkitConfig(name='{self.name}', version='{self.version}')"

# Made with Bob
