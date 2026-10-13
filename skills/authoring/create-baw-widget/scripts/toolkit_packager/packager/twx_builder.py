"""
TWX Builder for BAW Toolkit Packager.
Handles creation of complete TWX packages with all artifacts.
"""

import re
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict
import xml.etree.ElementTree as ET
import io
import tempfile

from ..models import Widget, TWXObject, ToolkitConfig
from ..core import generate_object_id, generate_version_id, generate_guid, escape_xml
from ..generators import CoachViewGenerator, ManagedAssetGenerator, BusinessObjectGenerator
from ..utils import get_logger
from ..utils.custom_type_registry import get_custom_type_registry
from ..utils.coach_view_registry import get_coach_view_registry

logger = get_logger(__name__)


class TWXBuilder:
    """
    Builder for creating TWX packages from widgets.
    Orchestrates the generation and packaging of all TWX artifacts.
    """
    
    def __init__(
        self,
        config: ToolkitConfig,
        template_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        coaches_dir: Optional[Path] = None
    ):
        """
        Initialize TWX builder.
        
        Args:
            config: Toolkit configuration
            template_dir: Path to template directory (optional, defaults to templates/BaseTWX/{bawVersion} from config)
            output_dir: Path to output directory (optional, defaults to output directory from config)
            coaches_dir: Path to coaches directory (default: coaches)
        """
        self.config = config
        # Use bawVersion from config to determine template directory
        baw_version = getattr(config, 'baw_version', '25.0.1')
        self.template_dir = template_dir or Path(f"templates/BaseTWX/{baw_version}")
        self.output_dir = output_dir or Path(config.output.directory if hasattr(config, 'output') else "output")
        self.coaches_dir = coaches_dir or Path("coaches")
        self.widgets: List[Widget] = []
        self.twx_objects: List[TWXObject] = []
        self.coach_objects: List[TWXObject] = []
        
        # Log the template version being used
        logger.info(f"Using BAW template version: {baw_version}")
        logger.info(f"Template directory: {self.template_dir}")
        
    def add_widget(self, widget: Widget) -> 'TWXBuilder':
        """
        Add a widget to the package.
        
        Args:
            widget: Widget to add
            
        Returns:
            Self for chaining
        """
        self.widgets.append(widget)
        logger.info(f"Added widget: {widget.name}")
        return self
    
    def build(self, output_filename: Optional[str] = None) -> Path:
        """
        Build the complete TWX package.
        
        Args:
            output_filename: Optional custom output filename
            
        Returns:
            Path to created TWX file
        """
        if not self.widgets:
            raise ValueError("No widgets added to package")
        
        logger.info(f"Building TWX package with {len(self.widgets)} widget(s)")
        
        # Generate all TWX objects
        self._generate_twx_objects()
        
        # Load coaches from coaches directory
        self._load_coaches()
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Determine output filename
        if output_filename is None:
            # Use the filename template from config (with {version} substituted)
            output_filename = self.config.get_output_filename()
        
        output_path = self.output_dir / output_filename
        
        # Build the TWX file
        self._create_twx_file(output_path)
        
        # Save registries after successful build
        custom_type_registry = get_custom_type_registry()
        custom_type_registry.save_registry()
        
        coach_view_registry = get_coach_view_registry()
        coach_view_registry.save_registry()
        
        logger.info(f"TWX package created: {output_path}")
        logger.info(f"Package size: {output_path.stat().st_size / 1024:.2f} KB")
        
        return output_path
    
    def _generate_twx_objects(self):
        """Generate all TWX objects for widgets and standalone business objects."""
        self.twx_objects = []
        
        # Scan and add standalone business objects from business-objects/generated
        from ..scanner import scan_business_objects, get_processing_order
        
        standalone_bos = scan_business_objects(Path.cwd())
        if standalone_bos:
            logger.info(f"📦 Found {len(standalone_bos)} standalone business object(s)")
            # Process in dependency order to ensure referenced types are created first
            ordered_bos = get_processing_order(standalone_bos)
            
            for bo in ordered_bos:
                # Create minimal object_ids for standalone business objects
                object_ids = {'coach_view': 'standalone'}
                bo_gen = BusinessObjectGenerator(None, object_ids, bo.data, self.template_dir)
                bo_obj = bo_gen.generate()
                self.twx_objects.append(bo_obj)
                logger.info(f"  ✓ Added standalone BO: {bo.name}")
        else:
            logger.info("No standalone business objects found in business-objects/generated")
        
        # Process widgets
        for widget in self.widgets:
            logger.info(f"Generating objects for widget: {widget.name}")
            
            # Generate object IDs
            object_ids = self._generate_object_ids(widget)
            
            # Load config.json schema
            config_schema = widget.get_config()
            
            # Generate business objects if widget has them and store their IDs
            business_objects = widget.get_business_objects()
            bo_id_map = {}  # Map business object names to their IDs
            for bo_definition in business_objects:
                bo_gen = BusinessObjectGenerator(widget, object_ids, bo_definition, self.template_dir)
                bo_obj = bo_gen.generate()
                self.twx_objects.append(bo_obj)
                
                # Store the business object ID for linking.
                # BOs may use 'name' (standalone format) or 'type' (widget BO format).
                bo_name = bo_definition.get('name') or bo_definition.get('type', 'Unknown')
                bo_id_map[bo_name] = bo_obj.id
                logger.debug(f"Generated business object: {bo_name} with ID: {bo_obj.id}")
            
            # Store business object IDs separately for coach view generator
            if bo_id_map:
                object_ids = {**object_ids, 'business_objects': bo_id_map}
            
            # Generate coach view
            coach_view_gen = CoachViewGenerator(widget, object_ids, config_schema, self.template_dir)
            coach_view_obj = coach_view_gen.generate()
            self.twx_objects.append(coach_view_obj)
            
            # Generate managed assets
            managed_asset_gen = ManagedAssetGenerator(widget, object_ids)
            managed_assets = managed_asset_gen.generate()
            if isinstance(managed_assets, list):
                self.twx_objects.extend(managed_assets)
            else:
                self.twx_objects.append(managed_assets)
    
    def _generate_object_ids(self, widget: Widget) -> Dict[str, str]:
        """
        Generate all object IDs for a widget.
        
        Args:
            widget: Widget to generate IDs for
            
        Returns:
            Dictionary of object IDs
        """
        return {
            'coach_view_id': generate_object_id(widget.name, '64'),
            'preview_html_id': generate_object_id(f'{widget.name}_preview_html', '61'),
            'preview_js_id': generate_object_id(f'{widget.name}_preview_js', '61'),
        }
    
    def _load_coaches(self):
        """Load coach XML files from coaches directory."""
        if not self.coaches_dir.exists():
            logger.info(f"Coaches directory not found: {self.coaches_dir}")
            return
        
        coach_files = list(self.coaches_dir.glob("*.xml"))
        if not coach_files:
            logger.info("No coach files found in coaches directory")
            return
        
        logger.info(f"Loading {len(coach_files)} coach file(s) from {self.coaches_dir}")
        
        for coach_file in coach_files:
            try:
                # Read the coach XML file
                xml_content = coach_file.read_text(encoding='utf-8')
                
                # Parse XML to extract coach metadata
                root = ET.fromstring(xml_content)
                
                # Extract coach ID and name - handle both direct process and teamworks wrapper
                if root.tag == 'teamworks':
                    # Look for process element inside teamworks
                    process_elem = root.find('process')
                    if process_elem is not None:
                        coach_id = process_elem.get('id', '')
                        coach_name = process_elem.get('name', coach_file.stem)
                    else:
                        logger.warning(f"Coach file {coach_file.name} has teamworks wrapper but no process element, skipping")
                        continue
                else:
                    # Direct process element
                    coach_id = root.get('id', '')
                    coach_name = root.get('name', coach_file.stem)
                
                if not coach_id:
                    logger.warning(f"Coach file {coach_file.name} missing ID, skipping")
                    continue
                
                # Generate version ID for the coach
                version_id = generate_version_id()
                
                # Create TWXObject for the coach
                coach_obj = TWXObject(
                    id=coach_id,
                    version_id=version_id,
                    name=coach_name,
                    object_type="process",
                    xml_content=xml_content
                )
                
                self.coach_objects.append(coach_obj)
                logger.info(f"✓ Loaded coach: {coach_name} ({coach_file.name})")
                
            except ET.ParseError as e:
                logger.error(f"Failed to parse coach file {coach_file.name}: {e}")
            except Exception as e:
                logger.error(f"Error loading coach file {coach_file.name}: {e}")
    
    def _create_twx_file(self, output_path: Path):
        """
        Create the TWX ZIP file with all artifacts.
        
        Args:
            output_path: Path to output TWX file
        """
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as twx:
            # Add dependency toolkits (if available in template)
            self._add_dependency_toolkits(twx)
            
            # Add META-INF files
            self._add_meta_inf(twx)
            
            # Add template defaults
            self._add_template_defaults(twx)
            
            # Add widget objects
            self._add_widget_objects(twx)
            
            # Add managed asset files
            self._add_managed_asset_files(twx)
    
    def _add_meta_inf(self, twx: zipfile.ZipFile):
        """Add META-INF files to TWX."""
        logger.info("Adding META-INF files...")
        
        # Add MANIFEST.MF
        manifest_path = self.template_dir / "META-INF/MANIFEST.MF"
        if manifest_path.exists():
            twx.write(manifest_path, "META-INF/MANIFEST.MF")
        
        # Add metadata.xml
        metadata_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<metadata>
</metadata>
'''
        twx.writestr("META-INF/metadata.xml", metadata_xml)
        
        # Add package.xml
        package_xml = self._generate_package_xml()
        twx.writestr("META-INF/package.xml", package_xml)
        
        # Add properties.json
        properties_path = self.template_dir / "META-INF/properties.json"
        if properties_path.exists():
            twx.write(properties_path, "META-INF/properties.json")
    
    def _add_dependency_toolkits(self, twx: zipfile.ZipFile):
        """
        Add dependency toolkit ZIP files to TWX for standalone deployment.
        Reads toolkit dependencies from the template directory based on bawVersion.
        """
        toolkits_dir = self.template_dir / "toolkits"
        
        if not toolkits_dir.exists():
            logger.info("No toolkits directory in template - dependencies will be referenced only")
            return
        
        toolkit_files = list(toolkits_dir.glob("*.zip"))
        
        if not toolkit_files:
            logger.info("No toolkit dependency files found in template")
            return
        
        logger.info(f"Adding {len(toolkit_files)} dependency toolkit(s) for standalone deployment...")
        
        for toolkit_file in toolkit_files:
            toolkit_name = toolkit_file.name
            twx.write(toolkit_file, f"toolkits/{toolkit_name}")
            
            # Log file size for visibility
            size_kb = toolkit_file.stat().st_size / 1024
            logger.info(f"  ✓ Added dependency: {toolkit_name} ({size_kb:.1f} KB)")
        
        logger.info("Dependency toolkits embedded for standalone deployment")
    
    def _add_template_defaults(self, twx: zipfile.ZipFile):
        """Add template default objects to TWX, packaging theme as ZIP file (v1.0.110 format)."""
        logger.info("Adding template defaults...")
        
        objects_dir = self.template_dir / "objects"
        if not objects_dir.exists():
            logger.warning(f"Template objects directory not found: {objects_dir}")
            return
        
        # Track theme managed asset IDs to package as ZIP
        theme_asset_ids = []
        theme_uuid_from_ref = None
        
        # First pass: Add Toolkit Settings (63.xxx) and identify theme assets
        # v1.0.113 includes 63.xxx objects
        for xml_file in objects_dir.glob("*.xml"):
            filename = xml_file.name
            # Process Toolkit Settings (63.xxx) - included in v1.0.113
            if filename.startswith("63."):
                # Add the 63.xxx XML file to TWX
                twx.writestr(f"objects/{filename}", xml_file.read_bytes())
                logger.info(f"Added template default object: {filename}")
                
                # Parse to find theme reference for later use
                try:
                    tree = ET.parse(xml_file)
                    root = tree.getroot()
                    theme_elem = root.find(".//defaultTheme")
                    if theme_elem is not None and theme_elem.text:
                        # Theme format: "uuid/72.theme-uuid"
                        theme_ref = theme_elem.text
                        if '/' in theme_ref:
                            theme_uuid_from_ref = theme_ref.split('/')[1].replace('72.', '')
                            logger.info(f"Found theme reference: {theme_ref}")
                            # Find the managed asset with this UUID in its name
                            for asset_xml in objects_dir.glob("61.*.xml"):
                                asset_tree = ET.parse(asset_xml)
                                asset_root = asset_tree.getroot()
                                asset_name = asset_root.find(".//managedAsset[@name]")
                                if asset_name is not None and theme_uuid_from_ref in asset_name.get('name', ''):
                                    asset_id = asset_xml.stem
                                    theme_asset_ids.append(asset_id)
                                    logger.info(f"Identified theme managed asset: {asset_id}")
                                    break
                except Exception as e:
                    logger.warning(f"Failed to parse theme reference from {filename}: {e}")
        
        # Second pass: Package theme as ZIP file (v1.0.110 format)
        files_dir = self.template_dir / "files"
        for asset_id in theme_asset_ids:
            asset_file_dir = files_dir / asset_id
            if asset_file_dir.exists() and asset_file_dir.is_dir():
                # Create ZIP file containing theme files
                theme_files = list(asset_file_dir.iterdir())
                if theme_files:
                    # Generate IDs for the ZIP managed asset
                    zip_asset_id = generate_object_id("theme_zip", "61")
                    zip_file_uuid = generate_guid("theme_zip_file")
                    zip_version_id = generate_version_id()
                    
                    # Use the theme UUID from reference as ZIP filename
                    if theme_uuid_from_ref:
                        zip_filename = f"{theme_uuid_from_ref}.zip"
                    else:
                        zip_filename = "theme.zip"
                    
                    # Create ZIP in memory
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as theme_zip:
                        for file_path in theme_files:
                            if file_path.is_file():
                                theme_zip.write(file_path, file_path.name)
                                logger.debug(f"Added to theme ZIP: {file_path.name}")
                    
                    zip_content = zip_buffer.getvalue()
                    zip_size = len(zip_content)
                    
                    # Create managed asset XML for the ZIP
                    zip_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<teamworks>
    <managedAsset id="{zip_asset_id}" name="{zip_filename}">
        <lastModified>{int(datetime.now().timestamp() * 1000)}</lastModified>
        <lastModifiedBy>cpmanager</lastModifiedBy>
        <tenantId isNull="true" />
        <managedAssetId>{zip_asset_id}</managedAssetId>
        <assetUuid>{zip_file_uuid}</assetUuid>
        <mimeType>application/zip</mimeType>
        <charEncoding isNull="true" />
        <assetTypeCode>T</assetTypeCode>
        <length>{zip_size}</length>
        <localLastModification>0</localLastModification>
        <description isNull="true" />
        <isDocumentationFile>false</isDocumentationFile>
        <guid>guid:{zip_asset_id.split('.')[1]}</guid>
        <versionId>{zip_version_id}</versionId>
    </managedAsset>
</teamworks>
'''
                    
                    # Add ZIP managed asset XML to TWX
                    twx.writestr(f"objects/{zip_asset_id}.xml", zip_xml)
                    logger.info(f"Added theme ZIP managed asset: {zip_asset_id}.xml")
                    
                    # Add ZIP file to TWX
                    twx.writestr(f"files/{zip_asset_id}/{zip_file_uuid}", zip_content)
                    logger.info(f"Added theme ZIP file: files/{zip_asset_id}/{zip_file_uuid} ({zip_size} bytes)")
            else:
                logger.warning(f"Theme asset directory not found: {asset_file_dir}")
    
    def _add_widget_objects(self, twx: zipfile.ZipFile):
        """Add widget object XML files to TWX."""
        logger.info("Adding widget objects...")
        
        for twx_obj in self.twx_objects:
            object_path = f"objects/{twx_obj.id}.xml"
            twx.writestr(object_path, twx_obj.xml_content)
            logger.debug(f"Added object: {object_path}")
        
        # Add coach objects
        if self.coach_objects:
            logger.info(f"Adding {len(self.coach_objects)} coach object(s)...")
            for coach_obj in self.coach_objects:
                object_path = f"objects/{coach_obj.id}.xml"
                twx.writestr(object_path, coach_obj.xml_content)
                logger.debug(f"Added coach: {object_path}")
    
    def _add_managed_asset_files(self, twx: zipfile.ZipFile):
        """Add managed asset files to TWX."""
        logger.info("Adding managed asset files...")
        
        for twx_obj in self.twx_objects:
            if twx_obj.object_type == "managedAsset" and twx_obj.file_references:
                for file_ref in twx_obj.file_references:
                    file_id = file_ref.get('file_id')
                    content = file_ref.get('content')
                    if file_id and content:
                        file_path = f"files/{twx_obj.id}/{file_id}"
                        twx.writestr(file_path, content)
                        logger.debug(f"Added file: {file_path}")
    
    def _generate_package_xml(self) -> str:
        """
        Generate package.xml with all objects and files.
        
        Returns:
            Package XML string
        """
        # Load template package.xml
        template_package_path = self.template_dir / "META-INF/package.xml"
        if template_package_path.exists():
            template_xml = template_package_path.read_text(encoding='utf-8')
        else:
            template_xml = self._get_default_package_xml_template()
        
        # Use persistent toolkit ID if configured, otherwise generate new one
        if self.config.toolkit_id:
            package_project_id = self.config.toolkit_id
            logger.info(f"Using persistent toolkit ID: {package_project_id}")
        else:
            package_project_id = generate_object_id(f"{self.config.short_name}_project", "2066")
            logger.warning(f"No toolkit ID configured, generated new ID: {package_project_id}")
            logger.warning("Add 'id' field to toolkit.config.json to maintain consistent toolkit identity")
        
        # Use persistent branch ID if configured, otherwise generate deterministic one
        # Branch ID MUST remain constant across versions for upgrade compatibility
        if hasattr(self.config, 'branch_id') and self.config.branch_id:
            package_branch_id = self.config.branch_id
            logger.info(f"Using persistent branch ID: {package_branch_id}")
        else:
            # Generate deterministic branch ID using generate_guid (no timestamp)
            # This ensures the same branch ID across all versions
            branch_guid = generate_guid(f"{self.config.short_name}_branch_Main")
            package_branch_id = f"2063.{branch_guid}"
            logger.info(f"Generated deterministic branch ID: {package_branch_id}")
            logger.info("Consider adding 'branchId' field to toolkit.config.json for explicit control")
        
        # Snapshot ID should change with each version (includes timestamp for uniqueness)
        package_snapshot_id = generate_object_id(f"{self.config.short_name}_snapshot_{self.config.version}", "2064")
        
        # Replace project info
        package_xml = template_xml
        package_xml = self._replace_project_info(package_xml, package_project_id, package_branch_id, package_snapshot_id)
        
        # Replace objects section
        objects_xml = self._generate_objects_section()
        package_xml = self._replace_section(package_xml, "objects", objects_xml)
        
        # Replace files section
        files_xml = self._generate_files_section()
        package_xml = self._replace_section(package_xml, "files", files_xml)
        
        return package_xml
    
    def _replace_project_info(
        self,
        package_xml: str,
        project_id: str,
        branch_id: str,
        snapshot_id: str
    ) -> str:
        """Replace project/branch/snapshot IDs in package.xml using regex string replacement.

        Avoids an XML parse+serialise round-trip which would mangle the Lombardisoftware
        namespace prefix (p:) to ns0: and cause BAW to reject the TWX on import.

        Only patches elements inside the <target> block — the <dependencies> block must
        keep the original system toolkit IDs or BAW will reject the import.
        """
        creation_date = f"{datetime.utcnow().isoformat(timespec='milliseconds')}Z"

        # Extract the <target>...</target> block, patch it, put it back.
        # This keeps <dependencies> untouched.
        target_match = re.search(r'(<target>)(.*?)(</target>)', package_xml, re.DOTALL)
        if not target_match:
            logger.warning("No <target> block found in package.xml — patching whole document (may corrupt dependencies)")
            target_block = package_xml
            prefix = suffix = ""
        else:
            prefix       = package_xml[:target_match.start(2)]
            target_block = target_match.group(2)
            suffix       = package_xml[target_match.end(2):]

        # -- project element: patch id, name, shortName, description ---------
        def patch_project(m):
            tag = m.group(0)
            tag = re.sub(r'\bid="[^"]*"',          f'id="{project_id}"', tag)
            tag = re.sub(r'\bname="[^"]*"',         f'name="{escape_xml(self.config.name)}"', tag)
            tag = re.sub(r'\bshortName="[^"]*"',    f'shortName="{escape_xml(self.config.short_name)}"', tag)
            tag = re.sub(r'\bdescription="[^"]*"',  f'description="{escape_xml(self.config.description)}"', tag)
            return tag

        target_block = re.sub(r'<project\b[^>]*/?>',  patch_project,  target_block)

        # -- branch element: patch id only ------------------------------------
        def patch_branch(m):
            return re.sub(r'\bid="[^"]*"', f'id="{branch_id}"', m.group(0))

        target_block = re.sub(r'<branch\b[^>]*/?>',   patch_branch,   target_block)

        # -- snapshot element: patch id, name, acronym, originalCreationDate --
        def patch_snapshot(m):
            tag = m.group(0)
            tag = re.sub(r'\bid="[^"]*"',                   f'id="{snapshot_id}"', tag)
            tag = re.sub(r'\bname="[^"]*"',                 f'name="{escape_xml(self.config.version)}"', tag)
            tag = re.sub(r'\bacronym="[^"]*"',              f'acronym="{escape_xml(self.config.version)}"', tag)
            tag = re.sub(r'\boriginalCreationDate="[^"]*"', f'originalCreationDate="{creation_date}"', tag)
            return tag

        target_block = re.sub(r'<snapshot\b[^>]*/?>',  patch_snapshot, target_block)

        result = prefix + target_block + suffix
        logger.debug(f"Patched <target> in package.xml: project={project_id}, branch={branch_id}, snapshot={snapshot_id}")
        return result
    
    def _generate_objects_section(self) -> str:
        """Generate objects section for package.xml."""
        object_lines = []
        
        # Include template defaults (63.xxx) - v1.0.113 format includes them
        # Template defaults are added to package.xml in v1.0.113
        objects_dir = self.template_dir / "objects"
        if objects_dir.exists():
            for xml_file in sorted(objects_dir.glob("*.xml")):
                filename = xml_file.name
                # Process Toolkit Settings (63.xxx) - included in v1.0.113 format
                if filename.startswith("63."):
                    # Parse XML to extract metadata
                    try:
                        tree = ET.parse(xml_file)
                        root = tree.getroot()
                        obj_id = filename.replace('.xml', '')
                        
                        # Find the actual object element (projectDefaults, environmentVariableSet, etc.)
                        # The root is <teamworks>, we need the child element
                        obj_elem = None
                        for child in root:
                            if child.tag in ['projectDefaults', 'environmentVariableSet']:
                                obj_elem = child
                                break
                        
                        if obj_elem is None:
                            logger.warning(f"Could not find object element in {filename}")
                            continue
                        
                        # Extract versionId from the object element
                        version_elem = obj_elem.find(".//versionId")
                        version_id = version_elem.text if version_elem is not None else generate_version_id()
                        
                        # Extract name attribute from object element
                        name = obj_elem.get('name', 'Toolkit Settings')
                        
                        obj_type = obj_elem.tag
                        
                        # Map XML tag to BAW object type
                        type_map = {
                            'environmentVariableSet': 'environmentVariableSet',
                            'projectDefaults': 'projectDefaults'
                        }
                        baw_type = type_map.get(obj_type, obj_type)
                        
                        object_line = f'        <object id="{obj_id}" versionId="{version_id}" name="{escape_xml(name)}" type="{baw_type}"/>'
                        object_lines.append(object_line)
                        logger.debug(f"Added template default to objects section: {obj_id}")
                    except Exception as e:
                        logger.warning(f"Failed to parse template default {filename}: {e}")
        
        # Add widget objects
        for twx_obj in self.twx_objects:
            object_line = f'        <object id="{twx_obj.id}" versionId="{twx_obj.version_id}" name="{escape_xml(twx_obj.name)}" type="{twx_obj.object_type}"/>'
            object_lines.append(object_line)
        
        # Add coach objects
        for coach_obj in self.coach_objects:
            object_line = f'        <object id="{coach_obj.id}" versionId="{coach_obj.version_id}" name="{escape_xml(coach_obj.name)}" type="{coach_obj.object_type}"/>'
            object_lines.append(object_line)
        
        return "\n".join(object_lines)
    
    def _generate_files_section(self) -> str:
        """Generate files section for package.xml."""
        file_lines = []
        
        for twx_obj in self.twx_objects:
            if twx_obj.object_type == "managedAsset" and twx_obj.file_references:
                for file_ref in twx_obj.file_references:
                    file_id = file_ref.get('file_id')
                    if file_id:
                        file_line = f'        <file path="{file_id}" id="{twx_obj.id}"/>'
                        file_lines.append(file_line)
        
        return "\n".join(file_lines)
    
    def _replace_section(self, xml: str, section_name: str, new_content: str) -> str:
        """Replace a section in the XML.

        Handles both plain ``<objects>`` and namespace-prefixed ``<p:objects>``
        tags as found in the Lombardisoftware package.xml template.
        """
        # Try bare tag first, then any namespace-prefixed variant (e.g. p:objects)
        patterns = [
            (f"<{section_name}>",    f"</{section_name}>"),
            (f"<p:{section_name}>",  f"</p:{section_name}>"),
        ]

        for start_tag, end_tag in patterns:
            start_idx = xml.find(start_tag)
            end_idx   = xml.find(end_tag)
            if start_idx != -1 and end_idx != -1:
                before = xml[:start_idx + len(start_tag)]
                after  = xml[end_idx:]
                return f"{before}\n{new_content}\n    {after}"

        logger.warning(f"Section '{section_name}' not found in template")
        return xml
    
    def _get_default_package_xml_template(self) -> str:
        """Get default package.xml template if template file doesn't exist."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.ibm.com/xmlns/prod/bpm/package/v1.0" id="2066.91beba32-f01f-45a0-9952-da866f54afe6" name="Custom Widget" description="" shortName="CW" originalCreationDate="2026-04-30T06:56:13.051Z">
    <branch id="2063.71237652-c729-4857-afe9-498c68376c60">
        <snapshot id="2064.960ed891-137d-4537-a66f-ad81b5f230db" name="2" acronym="2">
            <objects>
            </objects>
            <files>
            </files>
        </snapshot>
    </branch>
</package>
'''


# Made with Bob