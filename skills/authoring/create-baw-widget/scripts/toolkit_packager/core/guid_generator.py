"""
GUID/UUID generation utilities for BAW Toolkit Packager.
"""

import hashlib
import uuid
from typing import Optional


def generate_guid(seed: str) -> str:
    """
    Generate a deterministic GUID from a seed string.
    Uses SHA-256 hash to create RFC4122 compliant UUID v4.
    
    Args:
        seed: String to use as seed for GUID generation
        
    Returns:
        GUID in format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    """
    # Create SHA-256 hash of seed
    hash_obj = hashlib.sha256(seed.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    # Format as UUID v4 (RFC4122)
    # Version 4 UUID format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    # where y is one of [8, 9, a, b]
    
    guid = (
        f"{hash_hex[0:8]}-"
        f"{hash_hex[8:12]}-"
        f"4{hash_hex[13:16]}-"  # Version 4
        f"{hash_hex[16]}{hash_hex[17:20]}-"  # Variant bits
        f"{hash_hex[20:32]}"
    )
    
    # Ensure variant bits are correct (10xx in binary)
    variant_char = guid[19]
    if variant_char not in ['8', '9', 'a', 'b']:
        # Map to valid variant
        variant_map = {'0': '8', '1': '9', '2': 'a', '3': 'b',
                      '4': '8', '5': '9', '6': 'a', '7': 'b',
                      'c': '8', 'd': '9', 'e': 'a', 'f': 'b'}
        guid = guid[:19] + variant_map.get(variant_char, '8') + guid[20:]
    
    return guid


def generate_random_guid() -> str:
    """
    Generate a random UUID v4.
    
    Returns:
        Random GUID in format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    """
    return str(uuid.uuid4())


def generate_version_id() -> str:
    """
    Generate a version ID (random UUID v4).
    
    Returns:
        Random UUID for version tracking
    """
    return str(uuid.uuid4())


def generate_object_id(widget_name: str, object_type: str, timestamp: Optional[int] = None) -> str:
    """
    Generate a complete object ID for TWX objects.
    Format: {object_type}.{guid}
    
    Args:
        widget_name: Name of the widget
        object_type: BAW object type (e.g., "64" for coach view)
        timestamp: Optional timestamp for uniqueness (uses current time if None)
        
    Returns:
        Complete object ID in format: {type}.{guid}
    """
    if timestamp is None:
        import time
        timestamp = int(time.time() * 1000)
    
    seed = f"{widget_name}-{object_type}-{timestamp}"
    guid = generate_guid(seed)
    return f"{object_type}.{guid}"


def generate_binding_type_id(widget_name: str, binding_name: str, index: int = 0) -> str:
    """
    Generate a binding type ID for coach view bindings.
    
    Args:
        widget_name: Name of the widget
        binding_name: Name of the binding
        index: Index for uniqueness
        
    Returns:
        Binding type ID in format: 65.{guid}
    """
    seed = f"{widget_name}-binding-{binding_name}-{index}"
    guid = generate_guid(seed)
    return f"65.{guid}"


def generate_config_option_id(widget_name: str, option_name: str, index: int = 0) -> str:
    """
    Generate a config option ID for coach view configuration.
    
    Args:
        widget_name: Name of the widget
        option_name: Name of the configuration option
        index: Index for uniqueness
        
    Returns:
        Config option ID in format: 66.{guid}
    """
    seed = f"{widget_name}-config-{option_name}-{index}"
    guid = generate_guid(seed)
    return f"66.{guid}"


def extract_guid_from_id(object_id: str) -> str:
    """
    Extract GUID portion from a full object ID.
    
    Args:
        object_id: Full object ID (e.g., "64.aa82916a-4d0c-40f6-ab5f-99e7039bbc8a")
        
    Returns:
        GUID portion only
    """
    if '.' in object_id:
        return object_id.split('.', 1)[1]
    return object_id


def extract_type_from_id(object_id: str) -> str:
    """
    Extract object type from a full object ID.
    
    Args:
        object_id: Full object ID (e.g., "64.aa82916a-4d0c-40f6-ab5f-99e7039bbc8a")
        
    Returns:
        Object type portion
    """
    if '.' in object_id:
        return object_id.split('.', 1)[0]
    return ""

# Made with Bob
