"""
Widget scanner for discovering widgets in a project.
"""

from pathlib import Path
from typing import List, Optional

from ..core import REQUIRED_WIDGET_FILES, DEFAULT_EXCLUDE_DIRS
from ..models import Widget, ToolkitConfig
from ..utils import get_logger

logger = get_logger(__name__)


def is_widget_directory(path: Path) -> bool:
    """
    Check if a directory contains a widget.
    A widget directory must have a 'widget' subdirectory.
    
    Args:
        path: Directory path to check
        
    Returns:
        True if directory contains a widget
    """
    if not path.is_dir():
        return False
    
    widget_subdir = path / "widget"
    return widget_subdir.exists() and widget_subdir.is_dir()


def get_widget_files(widget_path: Path) -> dict:
    """
    Get all widget files from the widget directory.
    Includes files from the events subdirectory.
    
    Args:
        widget_path: Path to widget subdirectory
        
    Returns:
        Dictionary mapping filename to Path
    """
    files = {}
    
    if not widget_path.exists():
        return files
    
    # Get all files in widget directory
    for file_path in widget_path.iterdir():
        if file_path.is_file():
            files[file_path.name] = file_path
    
    # Get event handler files from events subdirectory
    events_path = widget_path / "events"
    if events_path.exists() and events_path.is_dir():
        for event_file in events_path.iterdir():
            if event_file.is_file() and event_file.suffix == '.js':
                # Store with 'events/' prefix to distinguish from other files
                files[f"events/{event_file.name}"] = event_file
    
    return files


def scan_directory_for_widget(directory: Path, exclude_dirs: List[str]) -> Optional[Widget]:
    """
    Scan a single directory to see if it contains a widget.
    
    Args:
        directory: Directory to scan
        exclude_dirs: List of directory names to exclude
        
    Returns:
        Widget object if found, None otherwise
    """
    # Skip if directory name is in exclusion list
    if directory.name in exclude_dirs:
        return None
    
    # Check if this is a widget directory
    if not is_widget_directory(directory):
        return None
    
    widget_path = directory / "widget"
    preview_path = directory / "AdvancePreview"
    
    # Get all widget files
    files = get_widget_files(widget_path)
    
    # Create Widget object
    widget = Widget(
        name=directory.name,
        path=directory,
        widget_path=widget_path,
        preview_path=preview_path if preview_path.exists() else None,
        files=files
    )
    
    logger.debug(f"Found widget: {widget.name} with {len(files)} files")
    
    return widget


def scan_project(project_path: Path, config: Optional[ToolkitConfig] = None) -> List[Widget]:
    """
    Scan project directory for all widgets.
    
    Args:
        project_path: Root project directory path
        config: Optional toolkit configuration for filtering
        
    Returns:
        List of discovered Widget objects
    """
    if not project_path.exists():
        logger.error(f"Project path does not exist: {project_path}")
        return []
    
    if not project_path.is_dir():
        logger.error(f"Project path is not a directory: {project_path}")
        return []
    
    # Determine exclusion list
    exclude_dirs = DEFAULT_EXCLUDE_DIRS.copy()
    if config and config.widgets.exclude:
        exclude_dirs.extend(config.widgets.exclude)
    
    logger.info(f"Scanning project directory: {project_path}")
    logger.debug(f"Excluding directories: {exclude_dirs}")
    
    widgets = []
    
    # Scan all subdirectories
    for item in project_path.iterdir():
        if not item.is_dir():
            continue
        
        widget = scan_directory_for_widget(item, exclude_dirs)
        if widget:
            # Apply configuration filters
            if config and not config.should_include_widget(widget.name):
                logger.debug(f"Widget '{widget.name}' excluded by configuration")
                continue
            
            widgets.append(widget)
    
    logger.info(f"Found {len(widgets)} widgets")
    
    return widgets


def list_widget_names(project_path: Path, config: Optional[ToolkitConfig] = None) -> List[str]:
    """
    List names of all widgets in project.
    
    Args:
        project_path: Root project directory path
        config: Optional toolkit configuration for filtering
        
    Returns:
        List of widget names
    """
    widgets = scan_project(project_path, config)
    return [w.name for w in widgets]


def find_widget_by_name(project_path: Path, widget_name: str) -> Optional[Widget]:
    """
    Find a specific widget by name.
    
    Args:
        project_path: Root project directory path
        widget_name: Name of widget to find
        
    Returns:
        Widget object if found, None otherwise
    """
    widget_dir = project_path / widget_name
    
    if not widget_dir.exists():
        return None
    
    return scan_directory_for_widget(widget_dir, [])


def count_widgets(project_path: Path, config: Optional[ToolkitConfig] = None) -> int:
    """
    Count number of widgets in project.
    
    Args:
        project_path: Root project directory path
        config: Optional toolkit configuration for filtering
        
    Returns:
        Number of widgets found
    """
    return len(scan_project(project_path, config))

# Made with Bob
