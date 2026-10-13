"""
Utility modules for the BAW Toolkit Packager.
"""

from .exceptions import (
    ToolkitPackagerError,
    ConfigurationError,
    WidgetValidationError,
    XMLGenerationError,
    PackagingError,
    FileNotFoundError,
    InvalidSchemaError,
)
from .logger import setup_logger, get_logger
from .version_manager import VersionManager, increment_toolkit_version
from .custom_type_registry import CustomTypeRegistry, get_custom_type_registry
from .coach_view_registry import CoachViewRegistry, get_coach_view_registry
from .template_parser import (
    get_system_data_dependency_id,
    get_ui_toolkit_dependency_id,
    clear_template_cache,
)

__all__ = [
    'ToolkitPackagerError',
    'ConfigurationError',
    'WidgetValidationError',
    'XMLGenerationError',
    'PackagingError',
    'FileNotFoundError',
    'InvalidSchemaError',
    'setup_logger',
    'get_logger',
    'VersionManager',
    'increment_toolkit_version',
    'CustomTypeRegistry',
    'get_custom_type_registry',
    'CoachViewRegistry',
    'get_coach_view_registry',
    'get_system_data_dependency_id',
    'get_ui_toolkit_dependency_id',
    'clear_template_cache',
]

# Made with Bob
