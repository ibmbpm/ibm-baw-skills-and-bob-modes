"""
BAW Toolkit Packager - Package IBM BAW custom widgets into TWX files.

This toolkit provides utilities for:
- Discovering widgets in a project
- Validating widget structure
- Generating TWX object IDs
- Creating TWX XML structures
- Packaging widgets into TWX archives

Example usage:
    from toolkit_packager import scan_project, validate_widgets
    from pathlib import Path
    
    # Scan for widgets
    widgets = scan_project(Path("."))
    
    # Validate widgets
    results = validate_widgets(widgets)
    
    # Check results
    for result in results:
        if result.is_valid:
            print(f"✓ {result.widget_name}")
        else:
            print(f"✗ {result.widget_name}: {len(result.errors)} errors")
"""

__version__ = "1.0.0"
__author__ = "BAW Toolkit Packager Team"

# Core utilities
from .core import (
    generate_guid,
    generate_object_id,
    generate_version_id,
    escape_xml,
    hash_content,
    OBJECT_TYPE_COACH_VIEW,
    OBJECT_TYPE_BUSINESS_OBJECT,
    OBJECT_TYPE_MANAGED_ASSET,
)

# Models
from .models import (
    Widget,
    TWXObject,
    TWXPackage,
    ToolkitConfig,
)

# Scanner
from .scanner import (
    scan_project,
    validate_widget,
    validate_widgets,
    ValidationResult,
    BusinessObject,
    scan_business_objects,
    get_business_object_by_name,
    load_custom_types_registry,
    save_custom_types_registry,
    register_business_object,
    get_or_create_class_id,
    build_dependency_graph,
    get_processing_order,
    list_business_object_names,
    count_business_objects,
)

# Generators
from .generators import (
    BaseGenerator,
    CoachViewGenerator,
    ManagedAssetGenerator,
)

# Packager
from .packager import (
    TWXBuilder,
)

# Configuration
from .config import (
    load_config,
    get_default_config,
)

# Utils
from .utils import (
    setup_logger,
    get_logger,
    ToolkitPackagerError,
    ConfigurationError,
    WidgetValidationError,
)

__all__ = [
    # Version
    '__version__',
    '__author__',
    # Core
    'generate_guid',
    'generate_object_id',
    'generate_version_id',
    'escape_xml',
    'hash_content',
    'OBJECT_TYPE_COACH_VIEW',
    'OBJECT_TYPE_BUSINESS_OBJECT',
    'OBJECT_TYPE_MANAGED_ASSET',
    # Models
    'Widget',
    'TWXObject',
    'TWXPackage',
    'ToolkitConfig',
    # Scanner
    'scan_project',
    'validate_widget',
    'validate_widgets',
    'ValidationResult',
    'BusinessObject',
    'scan_business_objects',
    'get_business_object_by_name',
    'load_custom_types_registry',
    'save_custom_types_registry',
    'register_business_object',
    'get_or_create_class_id',
    'build_dependency_graph',
    'get_processing_order',
    'list_business_object_names',
    'count_business_objects',
    # Generators
    'BaseGenerator',
    'CoachViewGenerator',
    'ManagedAssetGenerator',
    # Packager
    'TWXBuilder',
    # Configuration
    'load_config',
    'get_default_config',
    # Utils
    'setup_logger',
    'get_logger',
    'ToolkitPackagerError',
    'ConfigurationError',
    'WidgetValidationError',
]

# Made with Bob
