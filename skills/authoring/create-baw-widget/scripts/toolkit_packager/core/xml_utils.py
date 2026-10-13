"""
XML utilities for BAW Toolkit Packager.
"""

import html
import xml.dom.minidom as minidom
from typing import Dict, Optional


def escape_xml(text: str) -> str:
    """
    Escape special XML characters in text.
    
    Args:
        text: Text to escape
        
    Returns:
        XML-escaped text
    """
    if not text:
        return text
    
    # Use html.escape which handles XML entities correctly
    # Then handle additional XML-specific entities
    escaped = html.escape(text, quote=True)
    
    # Additional escaping for XML
    escaped = escaped.replace("'", "'")
    
    return escaped


def unescape_xml(text: str) -> str:
    """
    Unescape XML entities in text.
    
    Args:
        text: XML-escaped text
        
    Returns:
        Unescaped text
    """
    if not text:
        return text
    
    unescaped = html.unescape(text)
    unescaped = unescaped.replace("'", "'")
    
    return unescaped


def format_xml(xml_string: str, indent: str = "    ") -> str:
    """
    Pretty-print XML string with proper indentation.
    
    Args:
        xml_string: XML string to format
        indent: Indentation string (default: 4 spaces)
        
    Returns:
        Formatted XML string
    """
    try:
        dom = minidom.parseString(xml_string)
        pretty_xml = dom.toprettyxml(indent=indent)
        
        # Remove extra blank lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        return '\n'.join(lines)
    except Exception:
        # If parsing fails, return original
        return xml_string


def create_element(tag: str, text: Optional[str] = None, **attrs) -> str:
    """
    Create an XML element with optional text content and attributes.
    
    Args:
        tag: Element tag name
        text: Optional text content
        **attrs: Element attributes
        
    Returns:
        XML element string
    """
    # Build attributes string
    attrs_str = ""
    if attrs:
        attrs_list = [f'{k}="{escape_xml(str(v))}"' for k, v in attrs.items()]
        attrs_str = " " + " ".join(attrs_list)
    
    # Build element
    if text is not None:
        escaped_text = escape_xml(str(text))
        return f"<{tag}{attrs_str}>{escaped_text}</{tag}>"
    else:
        return f"<{tag}{attrs_str}/>"


def create_cdata_section(content: str) -> str:
    """
    Create a CDATA section for XML.
    
    Args:
        content: Content to wrap in CDATA
        
    Returns:
        CDATA section string
    """
    # Escape any existing CDATA end markers
    safe_content = content.replace("]]>", "]]]]><![CDATA[>")
    return f"<![CDATA[{safe_content}]]>"


def wrap_in_element(tag: str, content: str, **attrs) -> str:
    """
    Wrap content in an XML element.
    
    Args:
        tag: Element tag name
        content: Content to wrap (already formatted XML or text)
        **attrs: Element attributes
        
    Returns:
        Wrapped XML string
    """
    attrs_str = ""
    if attrs:
        attrs_list = [f'{k}="{escape_xml(str(v))}"' for k, v in attrs.items()]
        attrs_str = " " + " ".join(attrs_list)
    
    return f"<{tag}{attrs_str}>{content}</{tag}>"


def create_null_element(tag: str) -> str:
    """
    Create an element with isNull="true" attribute.
    
    Args:
        tag: Element tag name
        
    Returns:
        XML element with isNull attribute
    """
    return f'<{tag} isNull="true" />'


def build_xml_tree(root_tag: str, children: list, **root_attrs) -> str:
    """
    Build an XML tree from a root tag and children.
    
    Args:
        root_tag: Root element tag name
        children: List of child XML strings
        **root_attrs: Root element attributes
        
    Returns:
        Complete XML tree string
    """
    attrs_str = ""
    if root_attrs:
        attrs_list = [f'{k}="{escape_xml(str(v))}"' for k, v in root_attrs.items()]
        attrs_str = " " + " ".join(attrs_list)
    
    children_str = "\n".join(f"    {child}" for child in children)
    
    return f"""<{root_tag}{attrs_str}>
{children_str}
</{root_tag}>"""


def add_xml_declaration(xml_content: str, encoding: str = "UTF-8") -> str:
    """
    Add XML declaration to content.
    
    Args:
        xml_content: XML content
        encoding: Character encoding (default: UTF-8)
        
    Returns:
        XML with declaration
    """
    declaration = f'<?xml version="1.0" encoding="{encoding}"?>'
    if xml_content.startswith('<?xml'):
        # Already has declaration, replace it
        lines = xml_content.split('\n')
        lines[0] = declaration
        return '\n'.join(lines)
    else:
        return f"{declaration}\n{xml_content}"


def validate_xml_name(name: str) -> bool:
    """
    Validate if a string is a valid XML name.
    
    Args:
        name: Name to validate
        
    Returns:
        True if valid XML name
    """
    if not name:
        return False
    
    # XML names must start with letter or underscore
    if not (name[0].isalpha() or name[0] == '_'):
        return False
    
    # Rest can be letters, digits, hyphens, underscores, or periods
    for char in name[1:]:
        if not (char.isalnum() or char in '-_.'):
            return False
    
    return True

# Made with Bob
