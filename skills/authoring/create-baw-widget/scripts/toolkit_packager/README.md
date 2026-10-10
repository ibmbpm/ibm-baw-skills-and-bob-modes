# BAW Toolkit Packager

A Python toolkit for packaging IBM Business Automation Workflow (BAW) custom widgets into TWX files.

## Features

- **Widget Discovery**: Automatically scan project directories for widgets
- **Validation**: Validate widget structure and required files
- **GUID Generation**: Deterministic GUID generation for TWX objects
- **XML Generation**: Generate proper TWX XML structures
- **File Hashing**: SHA-256 hashing for file integrity
- **TWX Packaging**: Create complete TWX archives ready for BAW import

## Installation

No external dependencies required - uses Python 3.8+ standard library only.

```bash
# Add toolkit_packager to your Python path or use directly
python -m toolkit_packager --help
```

## Quick Start

### As a Library

```python
from pathlib import Path
from toolkit_packager import scan_project, validate_widgets
from toolkit_packager.models import ToolkitConfig

# Scan for widgets
project_path = Path(".")
widgets = scan_project(project_path)
print(f"Found {len(widgets)} widgets")

# Validate widgets
results = validate_widgets(widgets)
for result in results:
    print(result.get_summary())

# Load configuration
config = ToolkitConfig.from_dict({
    'toolkit': {
        'name': 'My Custom Widgets',
        'version': '1.0.0'
    }
})
```

### Command Line

```bash
# List all widgets in project
python -m toolkit_packager list

# Validate widgets
python -m toolkit_packager validate

# Package widgets into TWX
python -m toolkit_packager package --config toolkit.config.json
```

## Project Structure

Your BAW widget project should follow this structure:

```
project/
├── toolkit.config.json          # Optional configuration
├── WidgetName1/
│   ├── widget/
│   │   ├── Layout.html          # Required
│   │   ├── InlineCSS.css        # Required
│   │   ├── inlineJavascript.js  # Required
│   │   ├── WidgetName1.json     # Required (OpenAPI schema)
│   │   ├── datamodel.md         # Optional
│   │   └── eventHandler.md      # Optional
│   └── AdvancePreview/          # Optional
│       ├── WidgetName1.html
│       └── WidgetName1.js
├── WidgetName2/
│   └── widget/
│       └── ...
└── output/                      # Generated TWX files
```

## Configuration

Create `toolkit.config.json` in your project root:

```json
{
  "toolkit": {
    "name": "Custom Widgets",
    "shortName": "CW",
    "description": "Custom widget toolkit for BAW",
    "version": "1.0.0",
    "isToolkit": true,
    "isHidden": false,
    "isSystem": false
  },
  "dependencies": {
    "systemData": {
      "snapshotId": "2064.1080ded6-d153-4654-947c-2d16fce170db",
      "name": "8.6.0.0_TC"
    },
    "uiToolkit": {
      "snapshotId": "2064.304ac881-16c3-47d2-97d5-6e4c4a893177",
      "name": "8.6.0.0"
    }
  },
  "output": {
    "directory": "output",
    "filename": "Custom_Widgets_{version}.twx"
  },
  "widgets": {
    "include": ["*"],
    "exclude": ["BaseTWX", "docs", ".vscode"]
  }
}
```

## Module Overview

### Core (`toolkit_packager/core/`)

- **constants.py**: BAW object type constants and defaults
- **guid_generator.py**: GUID/UUID generation utilities
- **xml_utils.py**: XML escaping and formatting
- **file_hasher.py**: File hashing for TWX structure

### Models (`toolkit_packager/models/`)

- **widget.py**: Widget data model
- **twx_object.py**: TWX object representation
- **config_model.py**: Configuration data model

### Scanner (`toolkit_packager/scanner/`)

- **widget_scanner.py**: Discover widgets in project
- **validator.py**: Validate widget structure

### Generators (`toolkit_packager/generators/`)

- **base_generator.py**: Base class for generators
- **coach_view.py**: Generate coach view XML (64.*.xml)
- **business_object.py**: Generate business object XML (12.*.xml)
- **managed_asset.py**: Generate managed asset XML (61.*.xml)
- **meta_inf.py**: Generate META-INF files

### Packager (`toolkit_packager/packager/`)

- **file_mapper.py**: Map files to TWX structure
- **twx_builder.py**: Build and ZIP TWX file

## API Reference

### Widget Scanner

```python
from toolkit_packager.scanner import scan_project, validate_widget

# Scan for widgets
widgets = scan_project(Path("."))

# Validate a widget
result = validate_widget(widgets[0])
if result.is_valid:
    print("Widget is valid!")
else:
    for error in result.errors:
        print(f"Error: {error}")
```

### GUID Generation

```python
from toolkit_packager.core import generate_guid, generate_object_id

# Generate deterministic GUID
guid = generate_guid("my-seed-string")

# Generate object ID
object_id = generate_object_id("WidgetName", "64", timestamp=1234567890)
# Returns: "64.xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
```

### XML Utilities

```python
from toolkit_packager.core import escape_xml, create_element

# Escape XML content
safe_html = escape_xml("<div>Hello & goodbye</div>")

# Create XML element
element = create_element("name", "MyWidget", id="123")
# Returns: '<name id="123">MyWidget</name>'
```

## Development Status

### Completed Modules ✅

- ✅ Core utilities (GUID, XML, hashing)
- ✅ Data models (Widget, TWXObject, Config)
- ✅ Widget scanner and validator
- ✅ Exception handling and logging
- ✅ Base generator class

### In Progress 🚧

- 🚧 XML generators (Coach View, Business Object, Managed Assets)
- 🚧 META-INF file generators
- 🚧 File mapper and TWX builder
- 🚧 CLI interface
- 🚧 Complete documentation

### Planned 📋

- 📋 Unit tests
- 📋 Integration tests
- 📋 Example projects
- 📋 Advanced features (incremental builds, caching)

## Examples

### Example 1: List All Widgets

```python
from pathlib import Path
from toolkit_packager.scanner import list_widget_names

widgets = list_widget_names(Path("."))
print(f"Found widgets: {', '.join(widgets)}")
```

### Example 2: Validate Project

```python
from pathlib import Path
from toolkit_packager.scanner import scan_project, validate_widgets

widgets = scan_project(Path("."))
results = validate_widgets(widgets)

for result in results:
    if not result.is_valid:
        print(f"\n{result.widget_name}:")
        for error in result.errors:
            print(f"  ❌ {error}")
```

### Example 3: Generate GUIDs

```python
from toolkit_packager.core import generate_object_id, generate_binding_type_id

# Generate coach view ID
coach_view_id = generate_object_id("Breadcrumb", "64")
print(f"Coach View ID: {coach_view_id}")

# Generate binding type ID
binding_id = generate_binding_type_id("Breadcrumb", "items", 0)
print(f"Binding Type ID: {binding_id}")
```

## Contributing

This toolkit is designed to be modular and extensible. To add new features:

1. Follow the existing module structure
2. Add appropriate error handling
3. Include logging statements
4. Update documentation

## License

Apache 2.0

## Support

For issues or questions, refer to the BAW documentation or IBM support channels.