"""
Business Object XML Generator for BAW Toolkit Packager.
Generates XML for Business Objects (12.xxx.xml).
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from .base_generator import BaseGenerator
from ..models import Widget, TWXObject
from ..core import generate_object_id, generate_version_id, escape_xml
from ..utils import get_logger, get_system_data_dependency_id
from ..utils.custom_type_registry import get_custom_type_registry

logger = get_logger(__name__)

# Load BAW type mappings from configuration file
_TYPE_MAPPINGS = None

def load_type_mappings() -> Dict[str, str]:
    """Load BAW type mappings from JSON configuration file (type IDs only, without dependency prefix)."""
    global _TYPE_MAPPINGS
    if _TYPE_MAPPINGS is None:
        mappings_file = Path(__file__).parent.parent / 'baw_type_mappings.json'
        try:
            with open(mappings_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Combine mappings and aliases into a single lookup dict
                _TYPE_MAPPINGS = {}
                # Add direct mappings
                for type_name, type_id in config['mappings'].items():
                    _TYPE_MAPPINGS[type_name.lower()] = type_id
                    _TYPE_MAPPINGS[type_name] = type_id
                # Add aliases
                for alias, target in config['aliases'].items():
                    if target in config['mappings']:
                        _TYPE_MAPPINGS[alias] = config['mappings'][target]
                logger.info(f"Loaded {len(_TYPE_MAPPINGS)} BAW type mappings from configuration")
        except Exception as e:
            logger.warning(f"Failed to load BAW type mappings: {e}. Using defaults.")
            _TYPE_MAPPINGS = {}
    return _TYPE_MAPPINGS


class BusinessObjectGenerator(BaseGenerator):
    """
    Generator for Business Object XML files (12.xxx.xml).
    Creates business object definitions from JSON specifications.
    """
    
    def __init__(self, widget: Optional[Widget], object_ids: Dict[str, str], bo_definition: dict, template_path: Optional[Path] = None):
        """
        Initialize business object generator.
        
        Args:
            widget: Widget containing the business object (None for standalone business objects)
            object_ids: Dictionary of object IDs
            bo_definition: Business object definition from JSON
            template_path: Path to template directory for extracting dependency IDs
        """
        super().__init__(widget, object_ids)
        self.bo_definition = bo_definition
        self.template_path = template_path
        # Get business object name:
        # 1. First try 'name' field (used by standalone BOs and some widget BOs)
        # 2. Then try 'type' field (used by widget BOs like ProgressData, TaskItem)
        # 3. Fall back to 'BusinessObject' if neither exists
        self.bo_name = bo_definition.get('name') or bo_definition.get('type', 'BusinessObject')
        
        # Extract System Data dependency ID from template
        self.system_data_dep_id = None
        if template_path:
            self.system_data_dep_id = get_system_data_dependency_id(template_path)
            if self.system_data_dep_id:
                logger.debug(f"Using System Data dependency ID: {self.system_data_dep_id}")
    
    def generate(self) -> TWXObject:
        """
        Generate business object TWX object.
        Checks custom type registry to reuse existing class IDs if the type was already generated.
        
        Returns:
            TWXObject for business object
        """
        # Check if this business object type already exists in the registry
        registry = get_custom_type_registry()
        existing_class_id = registry.get_type(self.bo_name)
        
        widget_name = self.widget.name if self.widget else "standalone"
        
        if existing_class_id:
            # Reuse existing class ID
            bo_id = existing_class_id.lstrip('/')  # Remove leading / if present
            logger.info(f"Reusing existing business object '{self.bo_name}' with ID: {bo_id}")
            # Register this widget as using the type
            registry.register_type(
                self.bo_name,
                existing_class_id,
                widget_name,
                self.bo_definition.get('description', '')
            )
        else:
            # Generate new ID and register it
            bo_id = generate_object_id(self.bo_name, '12')
            class_id_with_slash = f"/{bo_id}"
            registry.register_type(
                self.bo_name,
                class_id_with_slash,
                widget_name,
                self.bo_definition.get('description', '')
            )
            logger.info(f"Created new business object '{self.bo_name}' with ID: {bo_id}")
        
        xml_content = self.generate_business_object_xml(bo_id)
        
        twx_obj = self.create_twx_object(
            object_id=bo_id,
            name=self.bo_name,
            object_type="twClass",
            xml_content=xml_content
        )
        
        self.log_generation("Business Object", bo_id)
        return twx_obj
    
    def generate_business_object_xml(self, bo_id: str) -> str:
        """
        Generate complete business object XML.
        
        Args:
            bo_id: Business object ID
            
        Returns:
            Complete XML string
        """
        timestamp = self.get_timestamp()
        version_id = generate_version_id()
        
        properties = self.bo_definition.get('properties', [])
        properties_xml = self.generate_properties_xml(properties)
        json_data = self.generate_json_data(properties)
        
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<teamworks>
    <twClass id="{bo_id}" name="{self.bo_name}">
        <lastModified>{timestamp}</lastModified>
        <lastModifiedBy>bob</lastModifiedBy>
        <tenantId isNull="true" />
        <classId>{bo_id}</classId>
        <type>1</type>
        <isSystem>false</isSystem>
        <shared>false</shared>
        <isShadow>false</isShadow>
        <globalLifetime>false</globalLifetime>
        <internalName isNull="true" />
        <extensionType isNull="true" />
        <saveServiceRef isNull="true" />
        <bpmn2Data isNull="true" />
        <externalId>itm.{bo_id}</externalId>
        <dependencySummary isNull="true" />
        <jsonData>{escape_xml(json_data)}</jsonData>
        <dataName isNull="true" />
        <allowAdditionalProperties>false</allowAdditionalProperties>
        <description isNull="true" />
        <guid>guid:{generate_version_id()}</guid>
        <versionId>{version_id}</versionId>
        <definition>
{properties_xml}
            <validator>
                <className isNull="true" />
                <errorMessage isNull="true" />
                <webWidgetJavaClass isNull="true" />
                <externalType isNull="true" />
                <configData>
                    <schema>
                        <simpleType name="{self.bo_name}">
                            <restriction base="String" />
                        </simpleType>
                    </schema>
                </configData>
            </validator>
            <annotation type="com.lombardisoftware.core.xml.XMLTypeAnnotation" version="2.0">
                <exclude isNull="true" />
                <anonymous isNull="true" />
                <local isNull="true" />
                <name isNull="true" />
                <namespace isNull="true" />
                <elementName isNull="true" />
                <elementNamespace isNull="true" />
                <protoTypeName isNull="true" />
                <baseTypeName isNull="true" />
                <specialType isNull="true" />
                <contentTypeVariety isNull="true" />
                <xscRef isNull="true" />
            </annotation>
        </definition>
    </twClass>
</teamworks>
'''
        return xml
    
    def generate_properties_xml(self, properties: list) -> str:
        """
        Generate XML for business object properties.
        
        Args:
            properties: List of property definitions
            
        Returns:
            XML string for properties
        """
        properties_xml = []
        
        for prop in properties:
            prop_name = prop.get('name', 'property')
            prop_type = prop.get('type', 'String')
            prop_required = str(prop.get('required', False)).lower()
            prop_desc = prop.get('description', '')
            
            # Map type to BAW class reference
            class_ref = self.get_class_ref_for_type(prop_type)
            
            prop_xml = f'''            <property>
                <name>{prop_name}</name>
                <description isNull="true" />
                <classRef>{class_ref}</classRef>
                <arrayProperty>false</arrayProperty>
                <propertyDefault isNull="true" />
                <propertyRequired>{prop_required}</propertyRequired>
                <propertyHidden>false</propertyHidden>
                <annotation type="com.lombardisoftware.core.xml.XMLFieldAnnotation" version="2.0">
                    <exclude isNull="true" />
                    <nodeType isNull="true" />
                    <name isNull="true" />
                    <namespace isNull="true" />
                    <typeName isNull="true" />
                    <typeNamespace isNull="true" />
                    <minOccurs isNull="true" />
                    <maxOccurs isNull="true" />
                    <nillable isNull="true" />
                    <order isNull="true" />
                    <wrapArray isNull="true" />
                    <arrayTypeName isNull="true" />
                    <arrayTypeAnonymous isNull="true" />
                    <arrayItemName isNull="true" />
                    <arrayItemWildcard isNull="true" />
                    <wildcard isNull="true" />
                    <wildcardVariety isNull="true" />
                    <wildcardMode isNull="true" />
                    <wildcardNamespace isNull="true" />
                    <parentModelGroupCompositor isNull="true" />
                    <timeZone isNull="true" />
                </annotation>
            </property>'''
            
            properties_xml.append(prop_xml)
        
        return '\n'.join(properties_xml)
    
    def generate_json_data(self, properties: list) -> str:
        """
        Generate JSON data for business object.
        
        Args:
            properties: List of property definitions
            
        Returns:
            JSON string
        """
        import json
        
        elements = []
        for prop in properties:
            prop_name = prop.get('name', 'property')
            prop_type = prop.get('type', 'String')
            prop_required = prop.get('required', False)
            prop_desc = prop.get('description', '')
            
            element = {
                "annotation": {
                    "documentation": [{}],
                    "appinfo": [{
                        "propertyName": [prop_name],
                        "propertyRequired": [prop_required],
                        "propertyHidden": [False],
                        "advancedParameterProperties": [{}]
                    }]
                },
                "name": prop_name,
                "type": "{http://lombardi.ibm.com/schema/}String",
                "otherAttributes": {
                    "{http://www.ibm.com/bpmsdk}refid": "12.db884a3c-c533-44b7-bb2d-47bec8ad4022"
                }
            }
            elements.append(element)
        
        json_data = {
            "attributeFormDefault": "unqualified",
            "elementFormDefault": "unqualified",
            "targetNamespace": "http://CW",
            "complexType": [{
                "annotation": {
                    "documentation": [{}],
                    "appinfo": [{
                        "shared": [False],
                        "advancedProperties": [{}],
                        "shadow": [False],
                        "allowAdditionalProperties": [False]
                    }]
                },
                "sequence": {
                    "element": elements
                },
                "name": self.bo_name
            }],
            "id": f"_12.{generate_version_id()}"
        }
        
        return json.dumps(json_data, separators=(',', ':'))
    
    def get_class_ref_for_type(self, prop_type: str) -> str:
        """
        Get BAW class reference for a property type.
        Uses centralized type mappings from baw_type_mappings.json.
        Handles primitive types, arrays, and custom business object references.
        
        Args:
            prop_type: Property type (String, Integer, Boolean, Date, Decimal, CustomType, CustomType[], etc.)
            
        Returns:
            Class reference string with dependency prefix (e.g., "dep-id/12.type-id")
        """
        type_mappings = load_type_mappings()
        registry = get_custom_type_registry()
        
        # Check if it's an array type (ends with [])
        is_array = prop_type.endswith('[]')
        base_type = prop_type[:-2] if is_array else prop_type
        
        # Try to find in primitive type mappings first (returns type ID only)
        type_id = type_mappings.get(base_type) or type_mappings.get(base_type.lower())
        
        if type_id:
            # Primitive type found - prepend with System Data dependency ID
            if self.system_data_dep_id:
                class_id = f"{self.system_data_dep_id}/{type_id}"
            else:
                # Fallback if dependency ID not available
                logger.warning(f"System Data dependency ID not available, using type ID only: {type_id}")
                class_id = type_id
        else:
            # Check if it's a custom business object
            custom_type_id = registry.get_type(base_type)
            if custom_type_id:
                # Custom business object reference - use the registered class ID
                class_id = custom_type_id.lstrip('/')
                logger.debug(f"Using custom business object reference for type '{base_type}': {class_id}")
            else:
                # Unknown type - default to String
                logger.warning(f"Unknown type '{prop_type}' for business object property, defaulting to String")
                string_type_id = type_mappings.get('String', '12.db884a3c-c533-44b7-bb2d-47bec8ad4022')
                if self.system_data_dep_id:
                    class_id = f"{self.system_data_dep_id}/{string_type_id}"
                else:
                    class_id = string_type_id
        
        return class_id


# Made with Bob