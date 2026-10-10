"""
Managed Asset XML Generator for BAW Toolkit Packager.
Generates XML for managed assets (preview files, resources, etc.).
"""

from typing import Optional
from datetime import datetime

from .base_generator import BaseGenerator
from ..models import Widget, TWXObject
from ..core import generate_object_id, generate_version_id, escape_xml
from ..utils import get_logger
from ..utils.coach_view_registry import get_coach_view_registry

logger = get_logger(__name__)


class ManagedAssetGenerator(BaseGenerator):
    """
    Generator for managed asset XML files (61.xxx.xml).
    Used for preview HTML/JS files and other widget resources.
    """
    
    def __init__(self, widget: Widget, object_ids: dict):
        """
        Initialize managed asset generator.
        
        Args:
            widget: Widget to generate assets for
            object_ids: Dictionary of object IDs
        """
        super().__init__(widget, object_ids)
    
    def generate(self) -> list:
        """
        Generate all managed asset TWX objects for the widget.
        
        Returns:
            List of TWXObject instances for managed assets
        """
        assets = []
        
        # Generate preview HTML asset if exists
        if self.widget.has_preview_files():
            html_asset = self.generate_preview_html_asset()
            if html_asset:
                assets.append(html_asset)
            
            js_asset = self.generate_preview_js_asset()
            if js_asset:
                assets.append(js_asset)
        
        # Generate icon asset if exists
        if self.widget.has_icon():
            icon_asset = self.generate_icon_asset()
            if icon_asset:
                assets.append(icon_asset)
        
        return assets
    
    def generate_preview_html_asset(self) -> Optional[TWXObject]:
        """
        Generate managed asset for preview HTML file.
        Uses registry to maintain stable asset IDs.
        
        Returns:
            TWXObject for HTML asset or None
        """
        html_content = self.widget.get_preview_html()
        if not html_content:
            return None
        
        html_path = self.widget.get_preview_html_path()
        asset_name = html_path.name if html_path else f"{self.widget.name}.html"
        
        # Get asset ID from object_ids (set by coach_view_generator)
        asset_id = self.object_ids.get('preview_html_id')
        if not asset_id:
            # Fallback: get from registry or generate new
            registry = get_coach_view_registry()
            asset_id = registry.get_preview_html_id(self.widget.name)
            if not asset_id:
                asset_id = generate_object_id(f'{self.widget.name}_preview_html', '61')
                logger.info(f"Generated new preview HTML ID for '{self.widget.name}': {asset_id}")
            else:
                logger.info(f"Reusing existing preview HTML ID for '{self.widget.name}': {asset_id}")
        
        file_id = generate_version_id()
        
        xml_content = self.generate_managed_asset_xml(
            asset_id=asset_id,
            asset_name=asset_name,
            file_content=html_content,
            file_id=file_id,
            mime_type="text/html"
        )
        
        twx_obj = self.create_twx_object(
            object_id=asset_id,
            name=asset_name,
            object_type="managedAsset",
            xml_content=xml_content,
            file_references=[{
                'file_id': file_id,
                'content': html_content
            }]
        )
        
        self.log_generation("Managed Asset (HTML)", asset_id)
        return twx_obj
    
    def generate_preview_js_asset(self) -> Optional[TWXObject]:
        """
        Generate managed asset for preview JavaScript file.
        Uses registry to maintain stable asset IDs.
        
        Returns:
            TWXObject for JS asset or None
        """
        js_content = self.widget.get_preview_js()
        if not js_content:
            return None
        
        js_path = self.widget.get_preview_js_path()
        asset_name = js_path.name if js_path else f"{self.widget.name}Snippet.js"
        
        # Get asset ID from object_ids (set by coach_view_generator)
        asset_id = self.object_ids.get('preview_js_id')
        if not asset_id:
            # Fallback: get from registry or generate new
            registry = get_coach_view_registry()
            asset_id = registry.get_preview_js_id(self.widget.name)
            if not asset_id:
                asset_id = generate_object_id(f'{self.widget.name}_preview_js', '61')
                logger.info(f"Generated new preview JS ID for '{self.widget.name}': {asset_id}")
            else:
                logger.info(f"Reusing existing preview JS ID for '{self.widget.name}': {asset_id}")
        
        file_id = generate_version_id()
        
        xml_content = self.generate_managed_asset_xml(
            asset_id=asset_id,
            asset_name=asset_name,
            file_content=js_content,
            file_id=file_id,
            mime_type="application/javascript"
        )
        
        twx_obj = self.create_twx_object(
            object_id=asset_id,
            name=asset_name,
            object_type="managedAsset",
            xml_content=xml_content,
            file_references=[{
                'file_id': file_id,
                'content': js_content
            }]
        )
        
        self.log_generation("Managed Asset (JS)", asset_id)
        return twx_obj
    
    def generate_icon_asset(self) -> Optional[TWXObject]:
        """
        Generate managed asset for widget icon SVG file.
        Uses registry to maintain stable asset IDs.
        
        Returns:
            TWXObject for icon asset or None
        """
        icon_content = self.widget.get_icon_content()
        if not icon_content:
            return None
        
        icon_path = self.widget.get_icon_path()
        asset_name = icon_path.name if icon_path else f"{self.widget.name}.svg"
        
        # Get or generate icon asset ID from registry
        registry = get_coach_view_registry()
        asset_id = registry.get_icon_id(self.widget.name)
        if not asset_id:
            asset_id = generate_object_id(f'{self.widget.name}_icon', '61')
            registry.register_icon_id(self.widget.name, asset_id)
            logger.info(f"Generated new icon ID for '{self.widget.name}': {asset_id}")
        else:
            logger.info(f"Reusing existing icon ID for '{self.widget.name}': {asset_id}")
        
        file_id = generate_version_id()
        
        xml_content = self.generate_managed_asset_xml(
            asset_id=asset_id,
            asset_name=asset_name,
            file_content=icon_content,
            file_id=file_id,
            mime_type="image/svg+xml"
        )
        
        twx_obj = self.create_twx_object(
            object_id=asset_id,
            name=asset_name,
            object_type="managedAsset",
            xml_content=xml_content,
            file_references=[{
                'file_id': file_id,
                'content': icon_content
            }]
        )
        
        self.log_generation("Managed Asset (Icon)", asset_id)
        return twx_obj
    
    def generate_managed_asset_xml(
        self,
        asset_id: str,
        asset_name: str,
        file_content: str,
        file_id: str,
        mime_type: Optional[str] = None
    ) -> str:
        """
        Generate managed asset XML.
        
        Args:
            asset_id: Asset object ID (61.xxx)
            asset_name: Asset file name
            file_content: File content
            file_id: UUID for the file
            mime_type: MIME type (auto-detected if None)
            
        Returns:
            XML string for managed asset
        """
        if mime_type is None:
            mime_type = self.detect_mime_type(asset_name)
        
        file_length = len(file_content.encode('utf-8'))
        timestamp = self.get_timestamp()
        version_id = generate_version_id()
        
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<teamworks>
    <managedAsset id="{asset_id}" name="{asset_name}">
        <lastModified>{timestamp}</lastModified>
        <lastModifiedBy>bob</lastModifiedBy>
        <tenantId isNull="true" />
        <managedAssetId>{asset_id}</managedAssetId>
        <assetUuid>{file_id}</assetUuid>
        <mimeType>{mime_type}</mimeType>
        <charEncoding isNull="true" />
        <assetTypeCode>W</assetTypeCode>
        <length>{file_length}</length>
        <localLastModification>{timestamp}</localLastModification>
        <description isNull="true" />
        <isDocumentationFile>false</isDocumentationFile>
        <guid>guid:{asset_id.split('.')[1]}</guid>
        <versionId>{version_id}</versionId>
    </managedAsset>
</teamworks>
'''
        return xml
    
    def detect_mime_type(self, filename: str) -> str:
        """
        Detect MIME type from filename extension.
        
        Args:
            filename: File name with extension
            
        Returns:
            MIME type string
        """
        extension = filename.lower().split('.')[-1]
        
        mime_types = {
            'html': 'text/html',
            'htm': 'text/html',
            'js': 'application/javascript',
            'css': 'text/css',
            'json': 'application/json',
            'xml': 'application/xml',
            'txt': 'text/plain',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'svg': 'image/svg+xml',
        }
        
        return mime_types.get(extension, 'application/octet-stream')
    
    def calculate_file_length(self, content: str) -> int:
        """
        Calculate file length in bytes.
        
        Args:
            content: File content
            
        Returns:
            Length in bytes
        """
        return len(content.encode('utf-8'))


# Made with Bob