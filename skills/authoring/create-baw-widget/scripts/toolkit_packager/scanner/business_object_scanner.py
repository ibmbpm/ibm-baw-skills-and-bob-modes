"""
Business Object Scanner - Discovers and validates business objects from the business-objects folder.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class BusinessObject:
    """Represents a business object definition."""
    
    def __init__(self, name: str, path: Path, data: Dict):
        self.name = name
        self.path = path
        self.data = data
        self.type = data.get("type", "businessObject")
        self.description = data.get("description", "")
        self.properties = data.get("properties", [])
        
    def __repr__(self):
        return f"BusinessObject(name='{self.name}', properties={len(self.properties)})"
    
    def get_property_count(self) -> int:
        """Get the number of properties."""
        return len(self.properties)
    
    def get_referenced_types(self) -> Set[str]:
        """Get all custom types referenced by this business object."""
        referenced = set()
        for prop in self.properties:
            prop_type = prop.get("type", "")
            # Check for custom types (not primitive types)
            if prop_type and not prop_type in ["String", "Integer", "Decimal", "Date", "Boolean"]:
                # Handle array types like "Type[]"
                if prop_type.endswith("[]"):
                    base_type = prop_type[:-2]
                    referenced.add(base_type)
                else:
                    referenced.add(prop_type)
        return referenced


def scan_business_objects(base_dir: Path) -> List[BusinessObject]:
    """
    Scan the business-objects/generated directory for business object JSON files.
    
    Args:
        base_dir: Base directory to scan (typically project root)
        
    Returns:
        List of BusinessObject instances
    """
    business_objects = []
    bo_dir = base_dir / "business-objects" / "generated"
    
    if not bo_dir.exists():
        logger.warning(f"Business objects directory not found: {bo_dir}")
        return business_objects
    
    logger.info(f"Scanning business objects in: {bo_dir}")
    
    # Scan all subdirectories (contexts)
    for context_dir in bo_dir.iterdir():
        if not context_dir.is_dir():
            continue
            
        logger.info(f"  Scanning context: {context_dir.name}")
        
        # Scan all JSON files in the context
        for json_file in context_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Validate it's a business object
                if data.get("type") == "businessObject":
                    bo = BusinessObject(
                        name=data.get("name", json_file.stem),
                        path=json_file,
                        data=data
                    )
                    business_objects.append(bo)
                    logger.info(f"    ✓ Found: {bo.name} ({bo.get_property_count()} properties)")
                else:
                    logger.warning(f"    ⚠ Skipping {json_file.name}: not a businessObject type")
                    
            except json.JSONDecodeError as e:
                logger.error(f"    ✗ Error parsing {json_file.name}: {e}")
            except Exception as e:
                logger.error(f"    ✗ Error loading {json_file.name}: {e}")
    
    logger.info(f"Found {len(business_objects)} business objects")
    return business_objects


def get_business_object_by_name(business_objects: List[BusinessObject], name: str) -> Optional[BusinessObject]:
    """Find a business object by name."""
    return next((bo for bo in business_objects if bo.name == name), None)


def load_custom_types_registry(registry_path: Path) -> Dict:
    """Load the custom types registry."""
    if not registry_path.exists():
        return {
            "description": "Custom Business Object Type Mappings - Tracks custom types and their BAW class IDs to enable reuse across widgets",
            "version": "1.0.0",
            "custom_types": {},
            "notes": {
                "usage": "This file tracks custom business objects to prevent duplicates and enable sharing across widgets",
                "classId_format": "Custom types use /12.{guid} format where the GUID is generated once and reused",
                "widgets": "List of widgets that use this custom type",
                "auto_update": "This file is automatically updated when new custom types are generated"
            }
        }
    
    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_custom_types_registry(registry_path: Path, registry: Dict):
    """Save the custom types registry."""
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2)


def register_business_object(
    registry_path: Path,
    bo_name: str,
    class_id: str,
    description: str = "",
    context: str = "standalone"
) -> Dict:
    """
    Register a business object in the custom types registry.
    
    Args:
        registry_path: Path to baw_custom_types.json
        bo_name: Name of the business object
        class_id: BAW class ID (e.g., "/12.{guid}")
        description: Description of the business object
        context: Context or source (e.g., "LifeInsuranceAndAnnuities")
        
    Returns:
        Updated registry entry for the business object
    """
    registry = load_custom_types_registry(registry_path)
    
    # Check if already registered
    if bo_name in registry["custom_types"]:
        logger.info(f"Business object '{bo_name}' already registered with classId: {registry['custom_types'][bo_name]['classId']}")
        return registry["custom_types"][bo_name]
    
    # Register new business object
    registry["custom_types"][bo_name] = {
        "classId": class_id,
        "description": description,
        "context": context,
        "widgets": [],  # Will be populated when used by widgets
        "created": datetime.utcnow().isoformat() + "Z"
    }
    
    save_custom_types_registry(registry_path, registry)
    logger.info(f"Registered business object '{bo_name}' with classId: {class_id}")
    
    return registry["custom_types"][bo_name]


def get_or_create_class_id(registry_path: Path, bo_name: str, description: str = "", context: str = "standalone") -> str:
    """
    Get existing class ID for a business object or create a new one.
    
    Args:
        registry_path: Path to baw_custom_types.json
        bo_name: Name of the business object
        description: Description of the business object
        context: Context or source
        
    Returns:
        Class ID for the business object
    """
    from ..core import generate_guid
    
    registry = load_custom_types_registry(registry_path)
    
    # Check if already registered
    if bo_name in registry["custom_types"]:
        return registry["custom_types"][bo_name]["classId"]
    
    # Generate new class ID using business object name as seed for deterministic GUID
    class_id = f"/12.{generate_guid(f'businessobject:{context}:{bo_name}')}"
    register_business_object(registry_path, bo_name, class_id, description, context)
    
    return class_id


def build_dependency_graph(business_objects: List[BusinessObject]) -> Dict[str, Set[str]]:
    """
    Build a dependency graph showing which business objects reference others.
    
    Returns:
        Dictionary mapping business object names to sets of referenced business object names
    """
    graph = {}
    bo_names = {bo.name for bo in business_objects}
    
    for bo in business_objects:
        referenced = bo.get_referenced_types()
        # Filter to only include other business objects (not primitive types)
        dependencies = referenced & bo_names
        graph[bo.name] = dependencies
    
    return graph


def get_processing_order(business_objects: List[BusinessObject]) -> List[BusinessObject]:
    """
    Get business objects in dependency order (dependencies first).
    Uses topological sort to ensure objects are processed before their dependents.
    
    Returns:
        List of business objects in processing order
    """
    graph = build_dependency_graph(business_objects)
    bo_map = {bo.name: bo for bo in business_objects}
    
    # Topological sort using Kahn's algorithm
    in_degree = {name: 0 for name in graph}
    for deps in graph.values():
        for dep in deps:
            in_degree[dep] += 1
    
    queue = [name for name, degree in in_degree.items() if degree == 0]
    result = []
    
    while queue:
        name = queue.pop(0)
        result.append(bo_map[name])
        
        for dependent in graph:
            if name in graph[dependent]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
    
    # Check for cycles
    if len(result) != len(business_objects):
        logger.warning("Circular dependencies detected in business objects")
        # Return original order if there are cycles
        return business_objects
    
    return result


def list_business_object_names(base_dir: Path) -> List[str]:
    """Get a list of all business object names."""
    business_objects = scan_business_objects(base_dir)
    return [bo.name for bo in business_objects]


def count_business_objects(base_dir: Path) -> int:
    """Count the number of business objects."""
    return len(scan_business_objects(base_dir))


# Made with Bob