"""
TWX object data model for BAW Toolkit Packager.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union


@dataclass
class TWXObject:
    """
    Represents a TWX object (coach view, business object, managed asset, etc.).
    """
    id: str
    version_id: str
    name: str
    object_type: str
    xml_content: str
    file_references: List[Union[str, Dict[str, Any]]] = field(default_factory=list)
    
    @property
    def type_code(self) -> str:
        """
        Get the numeric type code from the object ID.
        
        Returns:
            Type code (e.g., "64" for coach view)
        """
        if '.' in self.id:
            return self.id.split('.', 1)[0]
        return ""
    
    @property
    def guid(self) -> str:
        """
        Get the GUID portion from the object ID.
        
        Returns:
            GUID string
        """
        if '.' in self.id:
            return self.id.split('.', 1)[1]
        return self.id
    
    @property
    def xml_filename(self) -> str:
        """
        Get the XML filename for this object.
        
        Returns:
            Filename in format: {type}.{guid}.xml
        """
        return f"{self.id}.xml"
    
    def add_file_reference(self, file_ref: str):
        """
        Add a file reference to this object.
        
        Args:
            file_ref: File reference path
        """
        if file_ref not in self.file_references:
            self.file_references.append(file_ref)
    
    def __repr__(self) -> str:
        """String representation of TWX object."""
        return f"TWXObject(id='{self.id}', name='{self.name}', type='{self.object_type}')"


@dataclass
class TWXPackage:
    """
    Represents a complete TWX package with all its objects and metadata.
    """
    toolkit_name: str
    toolkit_short_name: str
    version: str
    description: str
    objects: List[TWXObject] = field(default_factory=list)
    dependencies: List[dict] = field(default_factory=list)
    
    def add_object(self, obj: TWXObject):
        """
        Add an object to the package.
        
        Args:
            obj: TWX object to add
        """
        self.objects.append(obj)
    
    def get_objects_by_type(self, object_type: str) -> List[TWXObject]:
        """
        Get all objects of a specific type.
        
        Args:
            object_type: Object type to filter by
            
        Returns:
            List of matching objects
        """
        return [obj for obj in self.objects if obj.object_type == object_type]
    
    def get_object_by_id(self, object_id: str) -> Optional[TWXObject]:
        """
        Get an object by its ID.
        
        Args:
            object_id: Object ID to search for
            
        Returns:
            TWX object or None if not found
        """
        for obj in self.objects:
            if obj.id == object_id:
                return obj
        return None
    
    def get_all_object_ids(self) -> List[str]:
        """
        Get all object IDs in the package.
        
        Returns:
            List of object IDs
        """
        return [obj.id for obj in self.objects]
    
    def get_object_count(self) -> int:
        """
        Get total number of objects in package.
        
        Returns:
            Object count
        """
        return len(self.objects)
    
    def __repr__(self) -> str:
        """String representation of TWX package."""
        return f"TWXPackage(name='{self.toolkit_name}', version='{self.version}', objects={len(self.objects)})"

# Made with Bob
