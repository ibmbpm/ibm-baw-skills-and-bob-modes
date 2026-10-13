"""
Core utilities for BAW Toolkit Packager.
"""

from .constants import (
    OBJECT_TYPE_PROCESS,
    OBJECT_TYPE_BUSINESS_OBJECT,
    OBJECT_TYPE_MANAGED_ASSET,
    OBJECT_TYPE_ENV_VARIABLE,
    OBJECT_TYPE_PROJECT_DEFAULTS,
    OBJECT_TYPE_COACH_VIEW,
    OBJECT_TYPE_BINDING_TYPE,
    OBJECT_TYPE_CONFIG_OPTION,
    OBJECT_TYPE_NAMES,
    REQUIRED_WIDGET_FILES,
    OPTIONAL_WIDGET_FILES,
    DEFAULT_TOOLKIT_NAME,
    DEFAULT_TOOLKIT_SHORT_NAME,
    DEFAULT_TOOLKIT_VERSION,
    DEFAULT_EXCLUDE_DIRS,
)

from .guid_generator import (
    generate_guid,
    generate_random_guid,
    generate_version_id,
    generate_object_id,
    generate_binding_type_id,
    generate_config_option_id,
    extract_guid_from_id,
    extract_type_from_id,
)

from .xml_utils import (
    escape_xml,
    unescape_xml,
    format_xml,
    create_element,
    create_cdata_section,
    wrap_in_element,
    create_null_element,
    build_xml_tree,
    add_xml_declaration,
    validate_xml_name,
)

from .file_hasher import (
    hash_content,
    hash_file,
    generate_file_id,
    generate_short_hash,
    verify_file_hash,
    hash_string_list,
    generate_checksum,
)

__all__ = [
    # Constants
    'OBJECT_TYPE_PROCESS',
    'OBJECT_TYPE_BUSINESS_OBJECT',
    'OBJECT_TYPE_MANAGED_ASSET',
    'OBJECT_TYPE_ENV_VARIABLE',
    'OBJECT_TYPE_PROJECT_DEFAULTS',
    'OBJECT_TYPE_COACH_VIEW',
    'OBJECT_TYPE_BINDING_TYPE',
    'OBJECT_TYPE_CONFIG_OPTION',
    'OBJECT_TYPE_NAMES',
    'REQUIRED_WIDGET_FILES',
    'OPTIONAL_WIDGET_FILES',
    'DEFAULT_TOOLKIT_NAME',
    'DEFAULT_TOOLKIT_SHORT_NAME',
    'DEFAULT_TOOLKIT_VERSION',
    'DEFAULT_EXCLUDE_DIRS',
    # GUID Generator
    'generate_guid',
    'generate_random_guid',
    'generate_version_id',
    'generate_object_id',
    'generate_binding_type_id',
    'generate_config_option_id',
    'extract_guid_from_id',
    'extract_type_from_id',
    # XML Utils
    'escape_xml',
    'unescape_xml',
    'format_xml',
    'create_element',
    'create_cdata_section',
    'wrap_in_element',
    'create_null_element',
    'build_xml_tree',
    'add_xml_declaration',
    'validate_xml_name',
    # File Hasher
    'hash_content',
    'hash_file',
    'generate_file_id',
    'generate_short_hash',
    'verify_file_hash',
    'hash_string_list',
    'generate_checksum',
]

# Made with Bob
