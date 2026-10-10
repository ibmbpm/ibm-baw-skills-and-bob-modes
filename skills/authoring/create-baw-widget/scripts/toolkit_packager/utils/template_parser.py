"""
Template Parser Utility for BAW Toolkit Packager.
Extracts dependency information from template package.xml files.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Dict
from ..utils import get_logger

logger = get_logger(__name__)

# Cache for parsed template dependencies
_TEMPLATE_CACHE: Dict[str, Dict[str, str]] = {}


def get_system_data_dependency_id(template_path: Path) -> Optional[str]:
    """
    Extract the System Data (TWSYS) dependency ID from a template's package.xml.
    
    Args:
        template_path: Path to the template directory (e.g., templates/BaseTWX/24.0.1)
        
    Returns:
        The dependency ID (without '2069.' prefix) or None if not found
        
    Example:
        >>> get_system_data_dependency_id(Path('templates/BaseTWX/24.0.1'))
        '6b8d712d-9bce-46dd-b112-f94df7c41b0d'
    """
    template_key = str(template_path)
    
    # Check cache first
    if template_key in _TEMPLATE_CACHE:
        return _TEMPLATE_CACHE[template_key].get('system_data_id')
    
    package_xml = template_path / 'META-INF' / 'package.xml'
    
    if not package_xml.exists():
        logger.error(f"Template package.xml not found: {package_xml}")
        return None
    
    try:
        tree = ET.parse(package_xml)
        root = tree.getroot()
        
        # Define namespace - ElementTree requires the full namespace in the tag
        ns = {'p': 'http://lombardisoftware.com/schema/teamworks/7.0.0/package.xsd'}
        
        # Find all dependencies - try both with and without namespace prefix
        dependencies = root.findall('.//p:dependency', ns)
        if not dependencies:
            # Fallback: try without namespace (for templates without explicit namespace prefix)
            dependencies = root.findall('.//dependency')
        
        for dep in dependencies:
            # Get the project element - try both with and without namespace
            project = dep.find('p:project', ns)
            if project is None:
                project = dep.find('project')
            
            if project is not None:
                short_name = project.get('shortName', '')
                
                # Look for System Data toolkit (TWSYS)
                if short_name == 'TWSYS':
                    dep_id = dep.get('id', '')
                    # Remove '2069.' prefix if present
                    if dep_id.startswith('2069.'):
                        dep_id = dep_id[5:]
                    
                    # Cache the result
                    if template_key not in _TEMPLATE_CACHE:
                        _TEMPLATE_CACHE[template_key] = {}
                    _TEMPLATE_CACHE[template_key]['system_data_id'] = dep_id
                    
                    logger.info(f"Found System Data dependency ID in {template_path.name}: {dep_id}")
                    return dep_id
        
        logger.warning(f"System Data (TWSYS) dependency not found in {package_xml}")
        return None
        
    except ET.ParseError as e:
        logger.error(f"Failed to parse {package_xml}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading template dependencies: {e}")
        return None


def get_ui_toolkit_dependency_id(template_path: Path) -> Optional[str]:
    """
    Extract the UI Toolkit (SYSBPMUI) dependency ID from a template's package.xml.
    
    Args:
        template_path: Path to the template directory
        
    Returns:
        The dependency ID (without '2069.' prefix) or None if not found
    """
    template_key = str(template_path)
    
    # Check cache first
    if template_key in _TEMPLATE_CACHE:
        return _TEMPLATE_CACHE[template_key].get('ui_toolkit_id')
    
    package_xml = template_path / 'META-INF' / 'package.xml'
    
    if not package_xml.exists():
        logger.error(f"Template package.xml not found: {package_xml}")
        return None
    
    try:
        tree = ET.parse(package_xml)
        root = tree.getroot()
        
        # Define namespace - ElementTree requires the full namespace in the tag
        ns = {'p': 'http://lombardisoftware.com/schema/teamworks/7.0.0/package.xsd'}
        
        # Find all dependencies - try both with and without namespace prefix
        dependencies = root.findall('.//p:dependency', ns)
        if not dependencies:
            # Fallback: try without namespace (for templates without explicit namespace prefix)
            dependencies = root.findall('.//dependency')
        
        for dep in dependencies:
            # Get the project element - try both with and without namespace
            project = dep.find('p:project', ns)
            if project is None:
                project = dep.find('project')
            
            if project is not None:
                short_name = project.get('shortName', '')
                
                # Look for UI Toolkit (SYSBPMUI)
                if short_name == 'SYSBPMUI':
                    dep_id = dep.get('id', '')
                    # Remove '2069.' prefix if present
                    if dep_id.startswith('2069.'):
                        dep_id = dep_id[5:]
                    
                    # Cache the result
                    if template_key not in _TEMPLATE_CACHE:
                        _TEMPLATE_CACHE[template_key] = {}
                    _TEMPLATE_CACHE[template_key]['ui_toolkit_id'] = dep_id
                    
                    logger.info(f"Found UI Toolkit dependency ID in {template_path.name}: {dep_id}")
                    return dep_id
        
        logger.warning(f"UI Toolkit (SYSBPMUI) dependency not found in {package_xml}")
        return None
        
    except ET.ParseError as e:
        logger.error(f"Failed to parse {package_xml}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading template dependencies: {e}")
        return None


def clear_template_cache():
    """Clear the template dependency cache."""
    global _TEMPLATE_CACHE
    _TEMPLATE_CACHE.clear()
    logger.debug("Template dependency cache cleared")

# Made with Bob
