"""
Scanner module for discovering and validating widgets and business objects.
"""

from .widget_scanner import (
    scan_project,
    is_widget_directory,
    get_widget_files,
    list_widget_names,
    find_widget_by_name,
    count_widgets,
)

from .validator import (
    ValidationResult,
    validate_widget,
    validate_widgets,
    check_required_files,
    get_validation_summary,
)

from .business_object_scanner import (
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

__all__ = [
    # Widget Scanner
    'scan_project',
    'is_widget_directory',
    'get_widget_files',
    'list_widget_names',
    'find_widget_by_name',
    'count_widgets',
    # Validator
    'ValidationResult',
    'validate_widget',
    'validate_widgets',
    'check_required_files',
    'get_validation_summary',
    # Business Object Scanner
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
]

# Made with Bob
