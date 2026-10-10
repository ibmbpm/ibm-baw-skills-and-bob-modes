"""
Version Manager for BAW Toolkit Packager.
Handles automatic version incrementing in toolkit.config.json.
"""

import json
from pathlib import Path
from typing import Tuple, Optional
from ..utils import get_logger
from ..core.constants import (
    DEFAULT_TOOLKIT_NAME,
    DEFAULT_TOOLKIT_SHORT_NAME,
    DEFAULT_TOOLKIT_VERSION,
    DEFAULT_TOOLKIT_DESCRIPTION,
    SYSTEM_DATA_SNAPSHOT_ID,
    SYSTEM_DATA_NAME,
    UI_TOOLKIT_SNAPSHOT_ID,
    UI_TOOLKIT_NAME,
)

logger = get_logger(__name__)


class VersionManager:
    """Manages toolkit version incrementing."""
    
    def __init__(self, config_path: Path = Path("toolkit.config.json")):
        """
        Initialize version manager.
        
        Args:
            config_path: Path to toolkit.config.json
        """
        self.config_path = config_path
    
    def parse_version(self, version_str: str) -> Tuple[int, int, int]:
        """
        Parse semantic version string into components.
        
        Args:
            version_str: Version string (e.g., "1.0.0")
            
        Returns:
            Tuple of (major, minor, patch)
            
        Raises:
            ValueError: If version format is invalid
        """
        try:
            parts = version_str.split('.')
            if len(parts) != 3:
                raise ValueError(f"Version must have 3 parts (major.minor.patch), got: {version_str}")
            
            major, minor, patch = map(int, parts)
            return (major, minor, patch)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid version format '{version_str}': {e}")
    
    def format_version(self, major: int, minor: int, patch: int) -> str:
        """
        Format version components into string.
        
        Args:
            major: Major version number
            minor: Minor version number
            patch: Patch version number
            
        Returns:
            Formatted version string
        """
        return f"{major}.{minor}.{patch}"
    
    def increment_version(
        self,
        version_str: str,
        increment_type: str = "patch"
    ) -> str:
        """
        Increment version based on type.
        
        Args:
            version_str: Current version string
            increment_type: Type of increment ("major", "minor", or "patch")
            
        Returns:
            New version string
            
        Raises:
            ValueError: If increment_type is invalid
        """
        major, minor, patch = self.parse_version(version_str)
        
        if increment_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif increment_type == "minor":
            minor += 1
            patch = 0
        elif increment_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid increment type: {increment_type}. Must be 'major', 'minor', or 'patch'")
        
        return self.format_version(major, minor, patch)
    
    def get_current_version(self) -> str:
        """
        Get current version from config file.
        
        Returns:
            Current version string
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If version is not found in config
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        version = config.get('toolkit', {}).get('version')
        if not version:
            raise ValueError("Version not found in toolkit.config.json")
        
        return version
    
    def _default_config(self) -> dict:
        """Return a minimal default toolkit.config.json structure.

        The toolkit id is a fixed constant shared by all users of this skill.
        BAW uses it to identify the toolkit project across imports — keeping it
        stable means subsequent imports are treated as upgrades, not new toolkits.
        """
        return {
            "toolkit": {
                "name": DEFAULT_TOOLKIT_NAME,
                "shortName": DEFAULT_TOOLKIT_SHORT_NAME,
                "description": DEFAULT_TOOLKIT_DESCRIPTION,
                "version": DEFAULT_TOOLKIT_VERSION,
                "bawVersion": "25.0.1",
                "id": "2066.cebc1c06-68a5-4d2e-986a-aaae3072cefb",
            },
            "dependencies": {
                "systemData": {
                    "snapshotId": SYSTEM_DATA_SNAPSHOT_ID,
                    "name": SYSTEM_DATA_NAME,
                },
                "uiToolkit": {
                    "snapshotId": UI_TOOLKIT_SNAPSHOT_ID,
                    "name": UI_TOOLKIT_NAME,
                },
            },
            "output": {
                "directory": "output",
                "filename": "Custom_Widgets_{version}.twx",
            },
            "widgets": {
                "include": ["*"],
                "exclude": [],
                "source_directory": "widgets",
            },
        }

    def update_version(
        self,
        new_version: Optional[str] = None,
        increment_type: str = "patch",
        dry_run: bool = False
    ) -> Tuple[str, str]:
        """
        Update version in config file.
        If the file does not exist, bootstrap it from defaults first.

        Args:
            new_version: Specific version to set (if None, auto-increment)
            increment_type: Type of increment if auto-incrementing
            dry_run: If True, don't write changes

        Returns:
            Tuple of (old_version, new_version)
        """
        # Bootstrap config file from defaults if absent
        if not self.config_path.exists():
            logger.info(f"toolkit.config.json not found — creating default at {self.config_path}")
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._default_config(), f, indent=2, ensure_ascii=False)
                f.write('\n')

        # Read current config
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        old_version = config.get('toolkit', {}).get('version', '1.0.0')
        
        # Determine new version
        if new_version is None:
            new_version = self.increment_version(old_version, increment_type)
        else:
            # Validate new version format
            self.parse_version(new_version)
        
        if dry_run:
            logger.info(f"[DRY RUN] Would update version: {old_version} → {new_version}")
            return (old_version, new_version)
        
        # Update config
        if 'toolkit' not in config:
            config['toolkit'] = {}
        config['toolkit']['version'] = new_version
        
        # Write back to file with pretty formatting
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Add trailing newline
        
        logger.info(f"Updated version: {old_version} → {new_version}")
        return (old_version, new_version)
    
    def auto_increment_before_build(
        self,
        increment_type: str = "patch",
        skip_if_unchanged: bool = True
    ) -> Tuple[str, str]:
        """
        Automatically increment version before building.
        
        This is the main method to call before packaging.
        
        Args:
            increment_type: Type of increment ("major", "minor", or "patch")
            skip_if_unchanged: If True, skip increment if no changes detected
            
        Returns:
            Tuple of (old_version, new_version)
        """
        old_version, new_version = self.update_version(
            increment_type=increment_type,
            dry_run=False
        )
        
        logger.info(f"Version incremented for build: {old_version} → {new_version}")
        return (old_version, new_version)


def increment_toolkit_version(
    config_path: Path = Path("toolkit.config.json"),
    increment_type: str = "patch"
) -> Tuple[str, str]:
    """
    Convenience function to increment toolkit version.
    
    Args:
        config_path: Path to toolkit.config.json
        increment_type: Type of increment ("major", "minor", or "patch")
        
    Returns:
        Tuple of (old_version, new_version)
    """
    manager = VersionManager(config_path)
    return manager.auto_increment_before_build(increment_type)

# Made with Bob
