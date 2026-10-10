"""
Base generator class for TWX XML generators.
"""

from abc import ABC, abstractmethod
from typing import Dict, Union, List, Optional

from ..models import Widget, TWXObject
from ..core import generate_version_id
from ..utils import get_logger

logger = get_logger(__name__)


class BaseGenerator(ABC):
    """
    Abstract base class for TWX object generators.
    """
    
    def __init__(self, widget: Optional[Widget], object_ids: Dict[str, str]):
        """
        Initialize generator.
        
        Args:
            widget: Widget to generate XML for (None for standalone business objects)
            object_ids: Dictionary of object IDs for this widget
        """
        self.widget = widget
        self.object_ids = object_ids
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def generate(self) -> Union[TWXObject, List[TWXObject]]:
        """
        Generate TWX object(s) with XML content.
        
        Returns:
            TWXObject or list of TWXObject instances
        """
        pass
    
    def get_timestamp(self) -> int:
        """
        Get current timestamp in milliseconds.
        
        Returns:
            Timestamp in milliseconds
        """
        import time
        return int(time.time() * 1000)
    
    def create_twx_object(
        self,
        object_id: str,
        name: str,
        object_type: str,
        xml_content: str,
        file_references: list = None  # type: ignore
    ) -> TWXObject:
        """
        Create a TWXObject with generated content.
        
        Args:
            object_id: Object ID
            name: Object name
            object_type: Object type
            xml_content: Generated XML content
            file_references: Optional list of file references
            
        Returns:
            TWXObject instance
        """
        version_id = generate_version_id()
        
        return TWXObject(
            id=object_id,
            version_id=version_id,
            name=name,
            object_type=object_type,
            xml_content=xml_content,
            file_references=file_references or []
        )
    
    def log_generation(self, object_type: str, object_id: str):
        """
        Log generation of an object.
        
        Args:
            object_type: Type of object generated
            object_id: ID of generated object
        """
        widget_name = self.widget.name if self.widget else "standalone"
        self.logger.debug(f"Generated {object_type}: {object_id} for widget '{widget_name}'")

# Made with Bob
