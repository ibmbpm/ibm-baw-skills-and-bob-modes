# BAW toolkit packager

A Python toolkit that packages IBM Business Automation Workflow (BAW) custom widgets into TWX files.

## Features

- **Widget discovery**: Scans project directories for widgets automatically.
- **Validation**: Validates widget structure and required files.
- **GUID generation**: Generates deterministic GUIDs for TWX objects.
- **XML generation**: Generates TWX XML structures.
- **File hashing**: Uses SHA-256 hashing for file integrity.
- **TWX packaging**: Creates complete TWX archives that are ready for BAW import.

## Installation

The packager has no external dependencies. It uses the Python 3.8+ standard library only.

```bash
# Run the packaging script from the skill root
python scripts/package_baw.py --help
```

## Quick start

### As a library

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

### Command line

Run the packaging script from the skill root. The script discovers every widget in `widgets/`, reads `assets/toolkit.config.json`, and writes the TWX file to `output/`.

```bash
python scripts/package_baw.py
```

## Project structure

Structure your BAW widget project as follows:

```text
project/
├── assets/toolkit.config.json   # Toolkit configuration
├── WidgetName1/
│   ├── widget/
│   │   ├── Layout.html          # Required
│   │   ├── InlineCSS.css        # Required
│   │   ├── inlineJavascript.js  # Required
│   │   ├── config.json          # Required
│   │   ├── datamodel.md         # Optional
│   │   ├── eventHandler.md      # Optional
│   │   └── WidgetName1.json     # Optional (business object schema, only if widget uses a custom type)
│   └── AdvancePreview/          # Optional
│       ├── WidgetName1.html
│       └── WidgetName1.js
├── WidgetName2/
│   └── widget/
│       └── ...
└── output/                      # Generated TWX files
```

## Configuration

Edit `assets/toolkit.config.json` in the skill root:

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

## Module overview

### Core (`toolkit_packager/core/`)

- **constants.py**: BAW object type constants and defaults
- **guid_generator.py**: GUID and UUID generation utilities
- **xml_utils.py**: XML escaping and formatting
- **file_hasher.py**: File hashing for the TWX structure

### Models (`toolkit_packager/models/`)

- **widget.py**: Widget data model
- **twx_object.py**: TWX object representation
- **config_model.py**: Configuration data model

### Scanner (`toolkit_packager/scanner/`)

- **widget_scanner.py**: Discovers widgets in the project
- **validator.py**: Validates widget structure

### Generators (`toolkit_packager/generators/`)

- **base_generator.py**: Base class for generators
- **coach_view_generator.py**: Generates coach view XML (64.*.xml)
- **business_object_generator.py**: Generates business object XML (12.*.xml)
- **managed_asset_generator.py**: Generates managed asset XML (61.*.xml)

### Packager (`toolkit_packager/packager/`)

- **twx_builder.py**: Builds and zips the TWX file; maps files to the TWX structure and generates META-INF

## API reference

### Widget scanner

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

### GUID generation

```python
from toolkit_packager.core import generate_guid, generate_object_id

# Generate deterministic GUID
guid = generate_guid("my-seed-string")

# Generate object ID
object_id = generate_object_id("WidgetName", "64", timestamp=1234567890)
# Returns: "64.xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
```

### XML utilities

```python
from toolkit_packager.core import escape_xml, create_element

# Escape XML content
safe_html = escape_xml("<div>Hello & goodbye</div>")

# Create XML element
element = create_element("name", "MyWidget", id="123")
# Returns: '<name id="123">MyWidget</name>'
```

## Examples

### Example 1: list all widgets

```python
from pathlib import Path
from toolkit_packager.scanner import list_widget_names

widgets = list_widget_names(Path("."))
print(f"Found widgets: {', '.join(widgets)}")
```

### Example 2: validate a project

```python
from pathlib import Path
from toolkit_packager.scanner import scan_project, validate_widgets

widgets = scan_project(Path("."))
results = validate_widgets(widgets)

for result in results:
    if not result.is_valid:
        print(f"\n{result.widget_name}:")
        for error in result.errors:
            print(f"  Error: {error}")
```

### Example 3: generate GUIDs

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

The toolkit uses a modular, extensible design. To add features:

1. Follow the existing module structure.
2. Add appropriate error handling.
3. Include logging statements.
4. Update the documentation.

## License

Apache 2.0

## Support

For issues or questions, refer to the BAW documentation or IBM support channels.
