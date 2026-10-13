"""
Coach View XML Generator for BAW Toolkit Packager.
Generates XML for Coach View widgets (64.xxx.xml).
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .base_generator import BaseGenerator
from ..models import Widget, TWXObject
from ..core import generate_object_id, generate_version_id, escape_xml
from ..utils import get_logger, get_system_data_dependency_id
from ..utils.coach_view_registry import get_coach_view_registry

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


class CoachViewGenerator(BaseGenerator):
    """
    Generator for Coach View XML files (64.xxx.xml).
    Creates the main widget definition with layout, bindings, and scripts.
    """
    
    def __init__(self, widget: Widget, object_ids: Dict[str, str], config_schema: Optional[dict] = None, template_path: Optional[Path] = None):
        """
        Initialize coach view generator.
        
        Args:
            widget: Widget to generate coach view for
            object_ids: Dictionary of object IDs
            config_schema: Optional config.json schema for configuration
            template_path: Path to template directory for extracting dependency IDs
        """
        super().__init__(widget, object_ids)
        self.config_schema = config_schema or {}
        self.template_path = template_path
        
        # Extract System Data dependency ID from template
        self.system_data_dep_id = None
        if template_path:
            self.system_data_dep_id = get_system_data_dependency_id(template_path)
            if self.system_data_dep_id:
                logger.debug(f"Using System Data dependency ID: {self.system_data_dep_id}")
    
    def generate(self) -> TWXObject:
        """
        Generate coach view TWX object.
        Uses registry to maintain stable IDs across packaging operations.
        
        Returns:
            TWXObject for coach view
        """
        registry = get_coach_view_registry()
        
        # Get or generate coach view ID
        coach_view_id = registry.get_coach_view_id(self.widget.name)
        if not coach_view_id:
            coach_view_id = generate_object_id(self.widget.name, '64')
            logger.info(f"Generated new coach view ID for '{self.widget.name}': {coach_view_id}")
        else:
            logger.info(f"Reusing existing coach view ID for '{self.widget.name}': {coach_view_id}")
        
        # Get or generate preview HTML ID
        preview_html_id = registry.get_preview_html_id(self.widget.name)
        if not preview_html_id and self.widget.has_preview_files():
            preview_html_id = generate_object_id(f'{self.widget.name}_preview_html', '61')
            logger.info(f"Generated new preview HTML ID for '{self.widget.name}': {preview_html_id}")
        elif preview_html_id:
            logger.info(f"Reusing existing preview HTML ID for '{self.widget.name}': {preview_html_id}")
        
        # Get or generate preview JS ID
        preview_js_id = registry.get_preview_js_id(self.widget.name)
        if not preview_js_id and self.widget.has_preview_files():
            preview_js_id = generate_object_id(f'{self.widget.name}_preview_js', '61')
            logger.info(f"Generated new preview JS ID for '{self.widget.name}': {preview_js_id}")
        elif preview_js_id:
            logger.info(f"Reusing existing preview JS ID for '{self.widget.name}': {preview_js_id}")
        
        # Get or generate icon ID
        icon_id = registry.get_icon_id(self.widget.name)
        if not icon_id and self.widget.has_icon():
            icon_id = generate_object_id(f'{self.widget.name}_icon', '61')
            logger.info(f"Generated new icon ID for '{self.widget.name}': {icon_id}")
        elif icon_id:
            logger.info(f"Reusing existing icon ID for '{self.widget.name}': {icon_id}")
        
        # Register the coach view with all IDs
        registry.register_coach_view(
            self.widget.name,
            coach_view_id,
            preview_html_id,
            preview_js_id,
            self.get_widget_description(),
            icon_id
        )
        
        # Store IDs in object_ids for use by other generators
        self.object_ids['coach_view_id'] = coach_view_id
        self.object_ids['preview_html_id'] = preview_html_id or ''
        self.object_ids['preview_js_id'] = preview_js_id or ''
        self.object_ids['icon_id'] = icon_id or ''
        
        xml_content = self.generate_coach_view_xml(
            coach_view_id=coach_view_id,
            preview_html_id=preview_html_id or '',
            preview_js_id=preview_js_id or '',
            icon_id=icon_id or ''
        )
        
        twx_obj = self.create_twx_object(
            object_id=coach_view_id,
            name=self.widget.name,
            object_type="coachView",
            xml_content=xml_content
        )
        
        self.log_generation("Coach View", coach_view_id)
        return twx_obj
    
    def generate_coach_view_xml(
        self,
        coach_view_id: str,
        preview_html_id: str,
        preview_js_id: str,
        icon_id: str = ''
    ) -> str:
        """
        Generate complete coach view XML.
        
        Args:
            coach_view_id: Coach view object ID
            preview_html_id: Preview HTML managed asset ID
            preview_js_id: Preview JS managed asset ID
            icon_id: Icon managed asset ID (optional)
            
        Returns:
            Complete XML string
        """
        timestamp = self.get_timestamp()
        version_id = generate_version_id()
        
        # Generate layout XML
        layout_xml = self.generate_layout_xml()
        
        # Generate binding types
        binding_types_xml = self.generate_binding_types(coach_view_id)
        
        # Generate config options
        config_options_xml = self.generate_config_options(coach_view_id)
        
        # Generate inline scripts
        inline_scripts_xml = self.generate_inline_scripts(coach_view_id)
        
        # Build preview references
        preview_html_ref = f"/{preview_html_id}" if preview_html_id else ""
        preview_js_ref = f"/{preview_js_id}" if preview_js_id else ""
        
        # Build icon reference
        icon_ref = f"/{icon_id}" if icon_id else ""
        palette_icon_xml = f'<paletteIcon>{icon_ref}</paletteIcon>' if icon_ref else '<paletteIcon isNull="true" />'
        
        # Get widget description
        description = self.get_widget_description()
        
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<teamworks>
    <coachView id="{coach_view_id}" name="{self.widget.name}">
        <lastModified>{timestamp}</lastModified>
        <lastModifiedBy>bob</lastModifiedBy>
        <tenantId isNull="true" />
        <coachViewId>{coach_view_id}</coachViewId>
        <isTemplate>false</isTemplate>
        <layout>{escape_xml(layout_xml)}</layout>
        {palette_icon_xml}
        <previewImage isNull="true" />
        <hasLabel>false</hasLabel>
        <labelPosition>0</labelPosition>
        <nineSliceX1Coord>0</nineSliceX1Coord>
        <nineSliceX2Coord>0</nineSliceX2Coord>
        <nineSliceY1Coord>0</nineSliceY1Coord>
        <nineSliceY2Coord>0</nineSliceY2Coord>
        <emitBoundary>false</emitBoundary>
        <isPrototypeFunc>false</isPrototypeFunc>
        <enableDevMode>false</enableDevMode>
        <isMobileReady>false</isMobileReady>
        <loadJsFunction{self._get_event_handler_attr('load')}
        <unloadJsFunction{self._get_event_handler_attr('unload')}
        <viewJsFunction{self._get_event_handler_attr('view')}
        <changeJsFunction{self._get_event_handler_attr('change')}
        <collaborationJsFunction{self._get_event_handler_attr('collaboration')}
        <description>{escape_xml(description)}</description>
        <validateJsFunction isNull="true" />
        <previewAdvHtml>{preview_html_ref}</previewAdvHtml>
        <previewAdvJs>{preview_js_ref}</previewAdvJs>
        <useUrlBinding>false</useUrlBinding>
        <guid>guid:{coach_view_id.split('.')[1]}</guid>
        <versionId>{version_id}</versionId>
        <field1 isNull="true" />
        <field2 isNull="true" />
        <field3>0</field3>
        <field4 isNull="true" />
        <field5>false</field5>
        <clobField1 isNull="true" />
{binding_types_xml}{config_options_xml}{inline_scripts_xml}    </coachView>
</teamworks>
'''
        return xml
    
    def generate_layout_xml(self) -> str:
        """
        Generate layout XML with CustomHTML containing the widget's Layout.html.
        
        Returns:
            Layout XML string
        """
        layout_html = self.widget.get_layout_html()
        escaped_html = escape_xml(layout_html)
        
        layout_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<ns2:layout xmlns:ns2="http://www.ibm.com/bpm/CoachDesignerNG" '
            'xmlns:ns3="http://www.ibm.com/bpm/coachview">'
            '<ns2:layoutItem xsi:type="ns2:CustomHTML" version="8550" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<ns2:id>{generate_version_id()}</ns2:id>'
            '<ns2:layoutItemId>CustomHTML1</ns2:layoutItemId>'
            '<ns2:configData>'
            f'<ns2:id>{generate_version_id()}</ns2:id>'
            '<ns2:optionName>@customHTML.contentType</ns2:optionName>'
            '<ns2:value>TEXT</ns2:value>'
            '</ns2:configData>'
            '<ns2:configData>'
            f'<ns2:id>{generate_version_id()}</ns2:id>'
            '<ns2:optionName>@customHTML.textContent</ns2:optionName>'
            f'<ns2:value>{escaped_html}</ns2:value>'
            '</ns2:configData>'
            '</ns2:layoutItem>'
            '</ns2:layout>'
        )
        
        return layout_xml
    
    def generate_binding_types(self, coach_view_id: str) -> str:
        """
        Generate binding type definitions from schema or config.json.
        Uses registry to maintain stable binding IDs.
        
        Args:
            coach_view_id: Coach view ID
            
        Returns:
            XML string for binding types
        """
        # Try config.json first
        config = self.widget.get_config()
        if config and 'bindingType' in config:
            return self.generate_binding_from_config(coach_view_id, config['bindingType'])
        
        # Fall back to schema extraction
        bindings = self.extract_bindings_from_schema()
        if not bindings:
            return ""
        
        registry = get_coach_view_registry()
        binding_xml_parts = []
        for seq, binding in enumerate(bindings):
            binding_name = binding['name']
            
            # Get or generate binding ID from registry
            binding_id = registry.get_binding_id(self.widget.name, binding_name)
            if not binding_id:
                binding_id = generate_object_id(f"{binding_name}_binding", '65')
                registry.register_binding_id(self.widget.name, binding_name, binding_id)
                logger.debug(f"Generated new binding ID for '{self.widget.name}.{binding_name}': {binding_id}")
            else:
                logger.debug(f"Reusing existing binding ID for '{self.widget.name}.{binding_name}': {binding_id}")
            
            guid = generate_object_id(f"{binding_name}_binding_guid", '65').split('.', 1)[1]
            
            # Get class_id with fallback to Date type
            class_id = binding.get('class_id')
            if not class_id:
                class_id = self._add_dependency_prefix('12.68474ab0-d56f-47ee-b7e9-510b45a2a8be')  # Date
            
            binding_xml = f'''        <bindingType name="{binding_name}">
            <lastModified isNull="true" />
            <lastModifiedBy isNull="true" />
            <tenantId isNull="true" />
            <coachViewBindingTypeId>{binding_id}</coachViewBindingTypeId>
            <coachViewId>{coach_view_id}</coachViewId>
            <isList>{str(binding.get('is_list', False)).lower()}</isList>
            <classId>{class_id}</classId>
            <seq>{seq}</seq>
            <description isNull="true" />
            <guid>guid:{guid}</guid>
            <versionId>{generate_version_id()}</versionId>
        </bindingType>
'''
            binding_xml_parts.append(binding_xml)
        
        return "\n".join(binding_xml_parts)
    
    def generate_binding_from_config(self, coach_view_id: str, binding_config: dict) -> str:
        """
        Generate binding type XML from config.json binding configuration.
        Uses registry to maintain stable binding IDs.
        
        Args:
            coach_view_id: Coach view ID
            binding_config: Binding configuration from config.json
            
        Returns:
            XML string for binding type
        """
        binding_name = binding_config.get('name', 'Data')
        is_list = str(binding_config.get('isList', False)).lower()
        # Support both 'type' (new standard) and 'classId' (backward compatibility)
        binding_type_name = binding_config.get('type') or binding_config.get('classId', 'String')

        # ── Step 1: check business objects first (highest priority) ──────────
        # A business object registered for this widget always wins over primitive
        # type resolution. Check both: the binding type name matches a registered
        # BO name, OR the widget's businessObjects list contains any registered BO.
        class_id = None
        business_objects = self.object_ids.get('business_objects', {})
        if business_objects:
            # Direct match: binding type name == a registered BO name
            if binding_type_name and binding_type_name in business_objects:
                class_id = f"/{business_objects[binding_type_name]}"
                logger.info(f"Linked binding '{binding_name}' to business object '{binding_type_name}' (direct match) with ID: {class_id}")
            else:
                # Indirect match: any BO in the widget's businessObjects list
                widget_config = self.widget.get_config() if self.widget else None
                if widget_config and 'businessObjects' in widget_config:
                    for bo_ref in widget_config['businessObjects']:
                        bo_name = bo_ref.get('name')
                        if bo_name and bo_name in business_objects:
                            class_id = f"/{business_objects[bo_name]}"
                            logger.info(f"Linked binding '{binding_name}' to business object '{bo_name}' (config lookup) with ID: {class_id}")
                            break

        # ── Step 2: fall back to primitive type resolution ───────────────────
        if class_id is None:
            if binding_type_name and not binding_type_name.startswith('/') and '/' not in binding_type_name:
                class_id = self.get_default_class_id(binding_type_name.lower())
            else:
                class_id = binding_type_name if binding_type_name else self._add_dependency_prefix('12.db884a3c-c533-44b7-bb2d-47bec8ad4022')

        # ── Step 3: schema inference last resort ─────────────────────────────
        if not class_id.startswith('/') and self.config_schema:
            inferred_class_id = self._infer_class_id_from_schema(binding_name)
            if inferred_class_id:
                class_id = inferred_class_id
                logger.debug(f"Inferred classId for binding '{binding_name}' from schema: {class_id}")
        
        # Get or generate binding ID from registry
        registry = get_coach_view_registry()
        binding_id = registry.get_binding_id(self.widget.name, binding_name)
        if not binding_id:
            binding_id = generate_object_id(f"{binding_name}_binding", '65')
            registry.register_binding_id(self.widget.name, binding_name, binding_id)
            logger.debug(f"Generated new binding ID for '{self.widget.name}.{binding_name}': {binding_id}")
        else:
            logger.debug(f"Reusing existing binding ID for '{self.widget.name}.{binding_name}': {binding_id}")
        
        guid = generate_object_id(f"{binding_name}_binding_guid", '65').split('.', 1)[1]
        
        binding_xml = f'''        <bindingType name="{binding_name}">
            <lastModified isNull="true" />
            <lastModifiedBy isNull="true" />
            <tenantId isNull="true" />
            <coachViewBindingTypeId>{binding_id}</coachViewBindingTypeId>
            <coachViewId>{coach_view_id}</coachViewId>
            <isList>{is_list}</isList>
            <classId>{class_id}</classId>
            <seq>0</seq>
            <description isNull="true" />
            <guid>guid:{guid}</guid>
            <versionId>{generate_version_id()}</versionId>
        </bindingType>
'''
        return binding_xml
    
    def generate_config_options(self, coach_view_id: str) -> str:
        """
        Generate configuration option definitions from schema.
        Uses registry to maintain stable config option IDs.
        
        Args:
            coach_view_id: Coach view ID
            
        Returns:
            XML string for config options
        """
        options = self.extract_config_options_from_schema()
        if not options:
            return ""
        
        registry = get_coach_view_registry()
        option_xml_parts = []
        for seq, option in enumerate(options):
            option_name = option['name']
            
            # Get or generate config option ID from registry
            option_id = registry.get_config_option_id(self.widget.name, option_name)
            if not option_id:
                option_id = generate_object_id(f"{option_name}_option", '66')
                registry.register_config_option_id(self.widget.name, option_name, option_id)
                logger.debug(f"Generated new config option ID for '{self.widget.name}.{option_name}': {option_id}")
            else:
                logger.debug(f"Reusing existing config option ID for '{self.widget.name}.{option_name}': {option_id}")
            
            # Get class_id with fallback to String type
            class_id = option.get('class_id')
            if not class_id:
                class_id = self._add_dependency_prefix('12.db884a3c-c533-44b7-bb2d-47bec8ad4022')  # String
            
            option_xml = f'''        <configOption name="{option_name}">
            <lastModified isNull="true" />
            <lastModifiedBy isNull="true" />
            <tenantId isNull="true" />
            <coachViewConfigOptionId>{option_id}</coachViewConfigOptionId>
            <coachViewId>{coach_view_id}</coachViewId>
            <isList>{str(option.get('is_list', False)).lower()}</isList>
            <propertyType>{option.get('property_type', 'OBJECT')}</propertyType>
            <label>{escape_xml(option.get('label', option_name))}</label>
            <classId>{class_id}</classId>
            <processId isNull="true" />
            <actionflowId isNull="true" />
            <isAdaptive>false</isAdaptive>
            <seq>{seq}</seq>
            <description>{escape_xml(option.get('description', ''))}</description>
            <groupName></groupName>
            <guid>guid:{coach_view_id.split('.')[1]}-{option_name.lower()}</guid>
            <versionId>{generate_version_id()}</versionId>
        </configOption>
'''
            option_xml_parts.append(option_xml)
        
        return "\n".join(option_xml_parts)
    
    def generate_inline_scripts(self, coach_view_id: str) -> str:
        """
        Generate inline script definitions (JS and CSS).
        
        Args:
            coach_view_id: Coach view ID
            
        Returns:
            XML string for inline scripts
        """
        scripts = []
        
        # JavaScript
        try:
            js_content = self.widget.get_inline_js()
            js_id = generate_object_id('js_script', '68')
            js_xml = f'''        <inlineScript name="Inline Javascript">
            <lastModified isNull="true" />
            <lastModifiedBy isNull="true" />
            <tenantId isNull="true" />
            <coachViewInlineScriptId>{js_id}</coachViewInlineScriptId>
            <coachViewId>{coach_view_id}</coachViewId>
            <scriptType>JS</scriptType>
            <scriptBlock>{escape_xml(js_content)}</scriptBlock>
            <seq>0</seq>
            <description></description>
            <guid>guid:{coach_view_id.split('.')[1]}-js</guid>
            <versionId>{generate_version_id()}</versionId>
        </inlineScript>
'''
            scripts.append(js_xml)
        except FileNotFoundError:
            logger.warning(f"No inline JavaScript found for widget {self.widget.name}")
        
        # CSS
        try:
            css_content = self.widget.get_inline_css()
            css_id = generate_object_id('css_script', '68')
            css_xml = f'''        <inlineScript name="Inline CSS">
            <lastModified isNull="true" />
            <lastModifiedBy isNull="true" />
            <tenantId isNull="true" />
            <coachViewInlineScriptId>{css_id}</coachViewInlineScriptId>
            <coachViewId>{coach_view_id}</coachViewId>
            <scriptType>CSS</scriptType>
            <scriptBlock>{escape_xml(css_content)}</scriptBlock>
            <seq>1</seq>
            <description></description>
            <guid>guid:{coach_view_id.split('.')[1]}-css</guid>
            <versionId>{generate_version_id()}</versionId>
        </inlineScript>
'''
            scripts.append(css_xml)
        except FileNotFoundError:
            logger.warning(f"No inline CSS found for widget {self.widget.name}")
        
        return "\n".join(scripts)
    
    def extract_bindings_from_schema(self) -> List[Dict]:
        """
        Extract binding type definitions from config.json schema.
        
        Returns:
            List of binding definitions
        """
        bindings = []
        
        # Try to extract from config schema bindingType
        if 'bindingType' in self.config_schema:
            schemas = self.config_schema['components']['schemas']
            
            # Look for the main widget schema (e.g., DateOutputWidget)
            widget_schema_name = f"{self.widget.name}Widget"
            widget_schema = schemas.get(widget_schema_name)
            
            if widget_schema and 'properties' in widget_schema:
                # Extract 'data' binding if present
                if 'data' in widget_schema['properties']:
                    data_prop = widget_schema['properties']['data']
                    # Resolve $ref if present
                    if '$ref' in data_prop:
                        ref_name = data_prop['$ref'].split('/')[-1]
                        data_schema = schemas.get(ref_name, {})
                    else:
                        data_schema = data_prop
                    
                    # Determine the correct class ID based on type
                    data_type = data_schema.get('type', 'string')
                    class_id = data_schema.get('x-class-id', self.get_default_class_id(data_type))
                    
                    binding = {
                        'name': 'data',
                        'is_list': data_type == 'array',
                        'class_id': class_id
                    }
                    bindings.append(binding)
            
            # Also look for explicit binding definitions
            for schema_name, schema_def in schemas.items():
                if schema_name.endswith('Binding') or 'x-binding' in schema_def:
                    data_type = schema_def.get('type', 'string')
                    binding = {
                        'name': schema_name.replace('Binding', '').lower(),
                        'is_list': data_type == 'array',
                        'class_id': schema_def.get('x-class-id', self.get_default_class_id(data_type))
                    }
                    bindings.append(binding)
        
        return bindings
    
    def extract_config_options_from_schema(self) -> List[Dict]:
        """
        Extract configuration options from config.json schema.
        
        Returns:
            List of config option definitions
        """
        options = []
        
        # Try to extract from config schema configOptions
        if 'configOptions' in self.config_schema:
            # Direct configOptions format (new format)
            for option in self.config_schema['configOptions']:
                options.append({
                    'name': option.get('name', ''),
                    'label': option.get('label', option.get('name', '').replace('_', ' ').title()),
                    'description': option.get('description', ''),
                    'property_type': self.map_type_to_property_type(option.get('type', 'String')),
                    'is_list': option.get('isList', False),
                    'class_id': option.get('classId', self.get_default_class_id(option.get('type', 'String'))),
                    'default': option.get('default')
                })
            return options
        
        # OpenAPI schema format (old format)
        if 'components' in self.config_schema and 'schemas' in self.config_schema['components']:
            schemas = self.config_schema['components']['schemas']
            
            # Look for the main widget schema first
            widget_schema_name = f"{self.widget.name}Widget"
            widget_schema = schemas.get(widget_schema_name)
            
            # Check if widget has 'options' property
            if widget_schema and 'properties' in widget_schema and 'options' in widget_schema['properties']:
                options_prop = widget_schema['properties']['options']
                
                # Resolve $ref if present
                if '$ref' in options_prop:
                    ref_name = options_prop['$ref'].split('/')[-1]
                    options_schema = schemas.get(ref_name, {})
                else:
                    options_schema = options_prop
                
                # Extract properties from options schema
                if 'properties' in options_schema:
                    for prop_name, prop_def in options_schema['properties'].items():
                        option = {
                            'name': prop_name,
                            'label': prop_def.get('title', prop_name.replace('_', ' ').title()),
                            'description': prop_def.get('description', ''),
                            'property_type': self.map_type_to_property_type(prop_def.get('type', 'string')),
                            'is_list': prop_def.get('type') == 'array',
                            'class_id': prop_def.get('x-class-id', self.get_default_class_id(prop_def.get('type', 'string')))
                        }
                        options.append(option)
            
            # Fallback: Look for generic config schemas
            if not options:
                for schema_name in ['Config', 'Configuration', 'Options', f"{self.widget.name}Options"]:
                    config_schema = schemas.get(schema_name, {})
                    if 'properties' in config_schema:
                        for prop_name, prop_def in config_schema['properties'].items():
                            option = {
                                'name': prop_name,
                                'label': prop_def.get('title', prop_name.replace('_', ' ').title()),
                                'description': prop_def.get('description', ''),
                                'property_type': self.map_type_to_property_type(prop_def.get('type', 'string')),
                                'is_list': prop_def.get('type') == 'array',
                                'class_id': prop_def.get('x-class-id', self.get_default_class_id(prop_def.get('type', 'string')))
                            }
                            options.append(option)
                        break
        
        return options
    
    def map_type_to_property_type(self, json_type: str) -> str:
        """
        Map JSON schema type to BAW property type.
        
        Args:
            json_type: JSON schema type (can be 'Event', 'String', 'Boolean', 'Integer', etc.)
            
        Returns:
            BAW property type
        """
        # Handle Event type specially
        if json_type and json_type.lower() == 'event':
            return 'EVENT'
        
        type_map = {
            'string': 'OBJECT',
            'String': 'OBJECT',
            'number': 'OBJECT',
            'Number': 'OBJECT',
            'integer': 'OBJECT',
            'Integer': 'OBJECT',
            'boolean': 'OBJECT',
            'Boolean': 'OBJECT',
            'object': 'OBJECT',
            'Object': 'OBJECT',
            'array': 'OBJECT',
            'Array': 'OBJECT'
        }
        return type_map.get(json_type, 'OBJECT')
    
    def get_default_class_id(self, json_type: str, json_format: Optional[str] = None) -> str:
        """
        Get default BAW class ID for a JSON type with dynamic dependency prefix.
        
        Args:
            json_type: JSON schema type (e.g., 'string', 'String', 'NameValuePair')
            json_format: JSON schema format (e.g., 'date-time', 'date')
            
        Returns:
            BAW class ID with dependency prefix (e.g., "dep-id/12.type-id")
        """
        # Load type mappings from configuration (returns type IDs only)
        type_mappings = load_type_mappings()
        
        # Check for date/time formats first
        if json_format in ('date-time', 'date'):
            type_id = type_mappings.get('date', '12.68474ab0-d56f-47ee-b7e9-510b45a2a8be')
            return self._add_dependency_prefix(type_id)
        elif json_format == 'time':
            type_id = type_mappings.get('time', '12.20fdb1a2-f6ec-462e-8627-d49859ba42ae')
            return self._add_dependency_prefix(type_id)
        
        # Try to find mapping (case-insensitive)
        if json_type:
            type_id = type_mappings.get(json_type) or type_mappings.get(json_type.lower())
            if type_id:
                return self._add_dependency_prefix(type_id)
        
        # Default to String if no mapping found
        type_id = type_mappings.get('string', '12.db884a3c-c533-44b7-bb2d-47bec8ad4022')
        return self._add_dependency_prefix(type_id)
    
    def _add_dependency_prefix(self, type_id: str) -> str:
        """
        Add System Data dependency prefix to a type ID.
        
        Args:
            type_id: Type ID (e.g., "12.db884a3c-c533-44b7-bb2d-47bec8ad4022")
            
        Returns:
            Full class reference with dependency prefix
        """
        if self.system_data_dep_id:
            return f"{self.system_data_dep_id}/{type_id}"
        else:
            logger.warning(f"System Data dependency ID not available, using type ID only: {type_id}")
            return type_id
    
    def _infer_class_id_from_schema(self, binding_name: str) -> Optional[str]:
        """
        Infer BAW class ID from config schema based on binding name.
        
        Args:
            binding_name: Name of the binding to infer type for
            
        Returns:
            BAW class ID or None if cannot be inferred
        """
        if not self.config_schema or 'components' not in self.config_schema:
            return None
        
        schemas = self.config_schema.get('components', {}).get('schemas', {})
        
        # Look for a schema matching the binding name
        schema = schemas.get(binding_name)
        if not schema:
            return None
        
        # Check for date/time formats
        if 'format' in schema:
            json_format = schema['format']
            if json_format in ('date-time', 'date', 'time'):
                logger.debug(f"Detected date/time format '{json_format}' for binding '{binding_name}'")
                type_id = '12.68474ab0-d56f-47ee-b7e9-510b45a2a8be'  # Date
                return self._add_dependency_prefix(type_id)
        
        # Check oneOf for date formats (like DateValue schema)
        if 'oneOf' in schema:
            for option in schema['oneOf']:
                if option.get('format') in ('date-time', 'date', 'time'):
                    logger.debug(f"Detected date/time in oneOf for binding '{binding_name}'")
                    type_id = '12.68474ab0-d56f-47ee-b7e9-510b45a2a8be'  # Date
                    return self._add_dependency_prefix(type_id)
        
        # Check type
        json_type = schema.get('type')
        if json_type:
            return self.get_default_class_id(json_type, schema.get('format'))
        
        return None
    
    def get_widget_description(self) -> str:
        """
        Get widget description from schema or README.
        
        Returns:
            Widget description
        """
        # Try config schema first (new format)
        if 'description' in self.config_schema:
            return self.config_schema['description']
        
        # Try OpenAPI format (old format)
        if 'info' in self.config_schema and 'description' in self.config_schema['info']:
            return self.config_schema['info']['description']
        
        # Try README
        readme_path = self.widget.path / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding='utf-8')
            # Extract first paragraph
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            if lines:
                return lines[0]
        
        return f"Custom {self.widget.name} widget"
    
    def _get_event_handler_attr(self, handler_name: str) -> str:
        """
        Get event handler attribute string (either isNull="true" or the handler code).
        
        Args:
            handler_name: Name of the handler (load, change, view, etc.)
            
        Returns:
            Attribute string for XML
        """
        handler_code = self._read_event_handler(handler_name)
        if handler_code:
            return f">{escape_xml(handler_code)}</{handler_name}JsFunction>"
        else:
            return ' isNull="true" />'
    
    def _read_event_handler(self, handler_name: str) -> Optional[str]:
        """
        Read event handler code from events folder.
        Falls back to eventHandler.md if events folder doesn't exist.
        
        Args:
            handler_name: Name of the handler (load, change, view, etc.)
            
        Returns:
            Handler code or None if not found
        """
        # Try to read from events folder first
        handler_code = self.widget.get_event_handler(handler_name)
        if handler_code:
            logger.debug(f"Loaded event handler '{handler_name}' from events/{handler_name}.js")
            return handler_code
        
        # Fallback to eventHandler.md for backward compatibility
        event_handler_path = self.widget.widget_path / "eventHandler.md"
        if not event_handler_path.exists():
            return None
        
        try:
            content = event_handler_path.read_text(encoding='utf-8')
            
            # Look for the handler section (## handler_name)
            lines = content.split('\n')
            in_handler = False
            in_code_block = False
            handler_code_lines = []
            
            for line in lines:
                # Check for handler heading
                if line.strip().lower() == f"## {handler_name.lower()}":
                    in_handler = True
                    continue
                
                # Check for next handler heading (stop collecting)
                if in_handler and line.strip().startswith('##') and not line.strip().lower().startswith(f"## {handler_name.lower()}"):
                    break
                
                if in_handler:
                    # Check for code block markers
                    if line.strip().startswith('```'):
                        if not in_code_block:
                            in_code_block = True
                            continue
                        else:
                            # End of code block
                            break
                    
                    # Collect code lines
                    if in_code_block:
                        handler_code_lines.append(line)
            
            if handler_code_lines:
                # Remove console.log statements and clean up
                code = '\n'.join(handler_code_lines).strip()
                # Remove console.log lines
                code_lines = [line for line in code.split('\n') if 'console.log' not in line]
                logger.debug(f"Loaded event handler '{handler_name}' from eventHandler.md (fallback)")
                return '\n'.join(code_lines).strip()
            
            return None
            
        except Exception as e:
            logger.warning(f"Error reading event handler '{handler_name}' for widget {self.widget.name}: {e}")
            return None


# Made with Bob