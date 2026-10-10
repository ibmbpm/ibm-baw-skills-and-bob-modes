"""
Constants for BAW Toolkit Packager.
"""

# BAW Object Type Constants
OBJECT_TYPE_PROCESS = "1"
OBJECT_TYPE_BUSINESS_OBJECT = "12"
OBJECT_TYPE_MANAGED_ASSET = "61"
OBJECT_TYPE_ENV_VARIABLE = "62"
OBJECT_TYPE_PROJECT_DEFAULTS = "63"
OBJECT_TYPE_COACH_VIEW = "64"
OBJECT_TYPE_BINDING_TYPE = "65"
OBJECT_TYPE_CONFIG_OPTION = "66"
OBJECT_TYPE_ES_ARTIFACT = "6023"
OBJECT_TYPE_PROJECT = "2066"
OBJECT_TYPE_BRANCH = "2063"
OBJECT_TYPE_SNAPSHOT = "2064"
OBJECT_TYPE_DEPENDENCY = "2069"

# Object Type Names
OBJECT_TYPE_NAMES = {
    OBJECT_TYPE_PROCESS: "process",
    OBJECT_TYPE_BUSINESS_OBJECT: "twClass",
    OBJECT_TYPE_MANAGED_ASSET: "managedAsset",
    OBJECT_TYPE_ENV_VARIABLE: "environmentVariableSet",
    OBJECT_TYPE_PROJECT_DEFAULTS: "projectDefaults",
    OBJECT_TYPE_COACH_VIEW: "coachView",
    OBJECT_TYPE_ES_ARTIFACT: "eSArtifact",
}

# Required Widget Files
REQUIRED_WIDGET_FILES = [
    "Layout.html",
    "InlineCSS.css",
    "inlineJavascript.js",
    "config.json",
]

# Optional Widget Files
OPTIONAL_WIDGET_FILES = [
    "datamodel.md",
    "eventHandler.md",
]

# Default Configuration
DEFAULT_TOOLKIT_NAME = "Custom Widgets"
DEFAULT_TOOLKIT_SHORT_NAME = "CW"
DEFAULT_TOOLKIT_VERSION = "1.0.0"
DEFAULT_TOOLKIT_DESCRIPTION = "Custom widget toolkit for BAW"

# System Dependencies
SYSTEM_DATA_SNAPSHOT_ID = "2064.1080ded6-d153-4654-947c-2d16fce170db"
SYSTEM_DATA_NAME = "8.6.0.0_TC"
UI_TOOLKIT_SNAPSHOT_ID = "2064.304ac881-16c3-47d2-97d5-6e4c4a893177"
UI_TOOLKIT_NAME = "8.6.0.0"

# TWX Structure
TWX_META_INF_DIR = "META-INF"
TWX_OBJECTS_DIR = "objects"
TWX_FILES_DIR = "files"
TWX_TOOLKITS_DIR = "toolkits"

# File Names
MANIFEST_FILE = "MANIFEST.MF"
METADATA_FILE = "metadata.xml"
PACKAGE_FILE = "package.xml"
PROPERTIES_FILE = "properties.json"

# XML Namespaces
XML_NAMESPACE_PACKAGE = "http://lombardisoftware.com/schema/teamworks/7.0.0/package.xsd"
XML_NAMESPACE_LAYOUT = "http://www.ibm.com/bpm/CoachDesignerNG"
XML_NAMESPACE_COACHVIEW = "http://www.ibm.com/bpm/coachview"

# Build Information
BUILD_VERSION = "8.6.10"
BUILD_DESCRIPTION = "IBM Business Process Manager V8.6.10.25010"
FIX_PACK = "25010"

# Default Exclusions
DEFAULT_EXCLUDE_DIRS = [
    "BaseTWX",
    "docs",
    "Loclisation",
    ".bob",
    ".vscode",
    ".git",
    "__pycache__",
    "output",
    "toolkit_packager",
]

# Made with Bob
