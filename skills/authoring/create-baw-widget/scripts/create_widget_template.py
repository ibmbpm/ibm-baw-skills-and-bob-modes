#!/usr/bin/env python3
"""
Create a new BAW Coach Widget with the correct structure for toolkit_packager.

Generates all required files with proper templates to ensure compatibility
with the BAW Package Manager packaging system.

Usage:
    python3 create_widget_template.py WidgetName "Widget description" [--events load,change,view]

Options:
    --events: Comma-separated list of event handlers to create
              (load, change, view, validate, unload)
              If not specified, only creates the events/ folder without any event files.
              Use 'all' to create all five handlers.

Examples:
    python3 create_widget_template.py MyWidget "A simple widget"
    python3 create_widget_template.py MyWidget "A widget" --events load,change
    python3 create_widget_template.py MyWidget "A widget" --events all

Notes:
    - Can be run from any directory; it always writes to {skill_root}/widgets/{WidgetName}/
    - The AdvancePreview files are PLACEHOLDERS — replace them by hand following
      the mixObject pattern documented in the skill before using in BAW Designer.
    - config.json uses the correct {name, file} object-array format for businessObjects.
"""

import sys
import json
from pathlib import Path
from datetime import datetime


def create_widget_structure(widget_name: str, description: str = "", events=None):
    """Create a complete widget directory structure with all required files.

    Args:
        widget_name: Name of the widget (PascalCase)
        description: Widget description
        events: List of event handlers to create (load, change, view, validate, unload).
                If None or empty, only creates the events/ folder.
    """
    if events is None:
        events = []

    if not widget_name:
        print("❌ Error: Widget name is required")
        return False

    if not widget_name[0].isupper():
        print("⚠️  Warning: Widget name should be PascalCase (e.g., MyWidget)")

    # Anchor to the skill root (two levels above this script) so the widget
    # lands in the correct place regardless of the caller's working directory.
    _skill_root = Path(__file__).parent.parent
    base_path = _skill_root / "widgets" / widget_name
    widget_path = base_path / "widget"
    preview_path = base_path / "AdvancePreview"

    if base_path.exists():
        print(f"❌ Error: Widget '{widget_name}' already exists at {base_path}")
        return False

    print(f"📦 Creating widget: {widget_name}")
    print(f"📁 Location: {base_path}")
    print()

    # Create directories
    widget_path.mkdir(parents=True, exist_ok=True)
    events_path = widget_path / "events"
    events_path.mkdir(parents=True, exist_ok=True)
    preview_path.mkdir(parents=True, exist_ok=True)

    css_prefix = widget_name.lower()

    # ── 1. Layout.html ────────────────────────────────────────────────────────
    layout_html = f"""<div class="{css_prefix}-container" role="region" aria-label="{widget_name}">
  <div class="{css_prefix}-content">
    <!-- Widget content goes here -->
  </div>
</div>"""
    (widget_path / "Layout.html").write_text(layout_html)
    print("✓ Created Layout.html")

    # ── 2. InlineCSS.css ──────────────────────────────────────────────────────
    # NOTE: InlineCSS.css is plain CSS — LESS variables (@bpm-*) do NOT work here.
    # Use hardcoded hex values and document the corresponding Carbon variable in a comment.
    inline_css = f"""/* {widget_name} Widget Styles — Carbon Design System */
/* Colors and typography aligned with the Carbon theme.
   InlineCSS.css is plain CSS — do NOT use @bpm-* LESS variables here; they will not compile. */

.{css_prefix}-container {{
    width: 100%;
    padding: 16px;
    box-sizing: border-box;
    font-family: 'IBM Plex Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif; /* @bpm-font-family-sans-serif */
}}

.{css_prefix}-content {{
    background-color: #ffffff; /* @bpm-body-bg */
    border: 1px solid #e0e0e0; /* Gray 20 */
    padding: 12px;
    font-size: 14px; /* @bpm-font-size-base */
    color: #161616; /* @bpm-text-color */
}}
"""
    (widget_path / "InlineCSS.css").write_text(inline_css)
    print("✓ Created InlineCSS.css")

    # ── 3. inlineJavascript.js ────────────────────────────────────────────────
    inline_js = f"""// {widget_name} Widget
// Runs inside the BAW coach view context.
// Use this.getData() / this.getOption() to read bound data and configuration.
// If config.json has bindingType.isList === true, access data via this.getData().items

var cv = this;

function render() {{
    var data = cv.getData();
    var container = cv.context.element.querySelector('.{css_prefix}-content');

    if (!container) {{ return; }}

    if (!data) {{
        container.textContent = '(no data)';
        return;
    }}

    // TODO: render widget content from data
    console.log('{widget_name} render', data);
}}

render();
"""
    (widget_path / "inlineJavascript.js").write_text(inline_js)
    print("✓ Created inlineJavascript.js")

    # ── 4. config.json ────────────────────────────────────────────────────────
    # businessObjects must be an array of {name, file} objects — NOT a string array.
    # Business object JSON files must use "type" as the identifier field, NOT "name".
    config_json = {
        "name": widget_name,
        "description": description or f"Custom {widget_name} widget for IBM Business Automation Workflow",
        "bindingType": {
            "name": f"{widget_name}Data",
            "isList": False,
            "type": "String"
        },
        "configOptions": [],
        "businessObjects": [],
        "changeFunction": True
    }
    (widget_path / "config.json").write_text(json.dumps(config_json, indent=2))
    print("✓ Created config.json")

    # ── 5. datamodel.md ───────────────────────────────────────────────────────
    datamodel_md = f"""# {widget_name} Data Model

## Binding

`config.json` bindingType: scalar String (set `isList: true` and add a business object if needed).

## Expected data shape

```javascript
// scalar String binding (default scaffold)
var data = this.getData();  // returns the bound string directly

// list binding example (update config.json bindingType.isList to true)
var items = this.getData().items;  // BAW wraps list data in .items
```

## Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| (update this table to match your actual data shape) | | | |

## Configuration options

None defined. Add entries to `configOptions` in config.json as needed.
"""
    (widget_path / "datamodel.md").write_text(datamodel_md)
    print("✓ Created datamodel.md")

    # ── 6. eventHandler.md ────────────────────────────────────────────────────
    event_handler_md = f"""# {widget_name} Event Handlers

## Conventions

Every event handler starts with `var _this = this;` to capture the widget context.

## Handlers

### load.js
Executed once when the widget initialises. Use for custom BAW event registration or
one-time setup that can't live in inlineJavascript.js.

### change.js
Executed when bound data changes. The most common handler — re-render the widget.

### view.js
Executed when the widget becomes visible (e.g. the user switches to its tab).

### validate.js
Executed during form validation. Return `true` if valid, `false` to block submission.

### unload.js
Executed when the widget is destroyed. Clear any timers or listeners created in load.js.
"""
    (widget_path / "eventHandler.md").write_text(event_handler_md)
    print("✓ Created eventHandler.md")

    # ── 7. Event handler JS files (optional) ─────────────────────────────────
    events_created = []

    if "load" in events:
        load_js = f"""// {widget_name} — Load Event Handler
// Executed once when the widget is first loaded and initialised.
var _this = this;

var data = _this.getData();
var options = _this.getOption();

console.log('{widget_name} loaded', data);

// Register a custom BAW event handler (uncomment if needed):
// bpmext.ui.registerEventHandlingFunction(_this, "CustomEvent", "eventName");

// Perform initial rendering or setup:
// render();
"""
        (events_path / "load.js").write_text(load_js)
        events_created.append("load.js")
        print("✓ Created events/load.js")

    if "change" in events:
        change_js = f"""// {widget_name} — Change Event Handler
// Executed when the widget's bound data changes.
var _this = this;

var data = _this.getData();

console.log('{widget_name} data changed:', data);

// Update the widget display based on the new data:
// render();
"""
        (events_path / "change.js").write_text(change_js)
        events_created.append("change.js")
        print("✓ Created events/change.js")

    if "view" in events:
        view_js = f"""// {widget_name} — View Event Handler
// Executed when the widget becomes visible (e.g. tab switch).
var _this = this;

var data = _this.getData();

console.log('{widget_name} now visible');

// Refresh or recalculate layout:
// render();
"""
        (events_path / "view.js").write_text(view_js)
        events_created.append("view.js")
        print("✓ Created events/view.js")

    if "validate" in events:
        validate_js = f"""// {widget_name} — Validate Event Handler
// Executed during form validation. Return true to allow submission, false to block it.
var _this = this;

var data = _this.getData();
var isValid = true;

// Example: require a non-empty value
// if (!data || !data.value) {{
//     isValid = false;
//     console.error('{widget_name} validation failed: value is required');
// }}

return isValid;
"""
        (events_path / "validate.js").write_text(validate_js)
        events_created.append("validate.js")
        print("✓ Created events/validate.js")

    if "unload" in events:
        unload_js = f"""// {widget_name} — Unload Event Handler
// Executed when the widget is being destroyed.
// Clean up anything created in load.js (timers, listeners, external references).
var _this = this;

console.log('{widget_name} unloading');

// Example cleanup:
// if (window.{css_prefix}Timer) {{
//     clearInterval(window.{css_prefix}Timer);
// }}
"""
        (events_path / "unload.js").write_text(unload_js)
        events_created.append("unload.js")
        print("✓ Created events/unload.js")

    if events_created:
        print(f"✓ Created {len(events_created)} event handler(s): {', '.join(events_created)}")
    else:
        print("ℹ️  No event handlers created (events/ folder is ready when you need them)")

    # ── 8. AdvancePreview — PLACEHOLDER ──────────────────────────────────────
    # ⚠️  This is a PLACEHOLDER preview only.
    # For BAW Designer to render the preview, replace these files with a proper
    # mixObject implementation (see assets/examples/ for working patterns).
    preview_html = f"""<!--
  {widget_name} AdvancePreview — PLACEHOLDER
  ⚠️  This file is a scaffold placeholder, NOT a BAW Designer-compatible preview.
  Replace it with a proper mixObject implementation before using in BAW Designer.
  See assets/examples/DateOutput/AdvancePreview/ or assets/examples/TasksList/AdvancePreview/
  for working patterns.
-->
<style>
.{css_prefix}-preview-container {{
    padding: 16px;
    font-family: 'IBM Plex Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 14px;
    color: #161616;
}}
</style>

<div class="SPARKPanel panel">
    <div class="{css_prefix}-preview-container">
        <!-- Preview content generated by {widget_name}Snippet.js -->
    </div>
</div>
"""
    (preview_path / f"{widget_name}.html").write_text(preview_html)
    print("✓ Created AdvancePreview/{widget_name}.html (placeholder — replace with mixObject pattern)")

    preview_snippet_js = f"""/*
 * {widget_name}Snippet.js — AdvancePreview PLACEHOLDER
 *
 * ⚠️  This is a scaffold placeholder. BAW Designer requires the mixObject pattern.
 * Replace this file following the pattern in assets/examples/DateOutput/AdvancePreview/
 * or assets/examples/TasksList/AdvancePreview/ before deploying.
 *
 * Required mixObject methods:
 *   createPreview(containingDiv, labelText, callback)
 *   getLabelDomElement()
 *   generateSampleData(domConstruct, domAttr, domClass)
 *   propertyChanged(propertyName, propertyValue)
 *   modelChanged(propertyName, propertyValue)
 */

var mixObject = {{

    createPreview: function (containingDiv, labelText, callback) {{
        var previewLayerUri = this.context.getManagedAssetUrl(
            "BPMExt-Controls.preview.js",
            this.context.assetType_WEB,
            "SYSBPMUI"
        );

        require([previewLayerUri], this.lang.hitch(this, function () {{
            require([
                "dojo/dom-construct",
                "dojo/dom-class",
                "dojo/dom-attr",
                "bpmui/preview/BPMExt-Core-Designer"
            ], this.lang.hitch(this, function (domConstruct, domClass, domAttr, bpmext) {{

                bpmext.uidesign.css.ensureGlyphsLoaded(this);
                bpmext.uidesign.css.ensureSparkUIClass(containingDiv);

                this.context.coachViewData.containingDiv = containingDiv;

                var formGroupDiv = domConstruct.create("div", null, containingDiv);
                domClass.add(formGroupDiv, "form-group");
                this.context.coachViewData.formGroupDiv = formGroupDiv;

                var label = domConstruct.create("span", null, formGroupDiv);
                domClass.add(label, "control-label");
                label.appendChild(document.createTextNode(labelText));
                this.context.coachViewData.label = label;

                var inputDiv = domConstruct.create("div", null, formGroupDiv);
                domClass.add(inputDiv, "input");
                this.context.coachViewData.inputDiv = inputDiv;

                this.generateSampleData(domConstruct, domAttr, domClass);

                callback();
            }}));
        }}));
    }},

    getLabelDomElement: function () {{
        return this.context.coachViewData.label;
    }},

    generateSampleData: function (domConstruct, domAttr, domClass) {{
        // TODO: replace with widget-specific preview content using Dojo DOM APIs.
        // Do NOT use document.createElement() or other vanilla DOM APIs here.
        var container = this.context.coachViewData.inputDiv;
        var placeholder = domConstruct.create("span", null, container);
        placeholder.appendChild(document.createTextNode("{widget_name} preview"));
    }},

    propertyChanged: function (propertyName, propertyValue) {{
        // Handle config option changes — update the preview when the user
        // modifies widget options in the BAW Designer property panel.
    }},

    modelChanged: function (propertyName, propertyValue) {{
        // Usually not needed for preview.
    }}
}};

// Made with Bob
"""
    (preview_path / f"{widget_name}Snippet.js").write_text(preview_snippet_js)
    print(f"✓ Created AdvancePreview/{widget_name}Snippet.js (placeholder — replace generateSampleData)")

    # ── 9. README.md ──────────────────────────────────────────────────────────
    readme_md = f"""# {widget_name} Widget

{description or f"Custom {widget_name} widget for IBM Business Automation Workflow (BAW)"}

## File structure

```
widgets/{widget_name}/
├── widget/
│   ├── Layout.html           # Widget HTML
│   ├── InlineCSS.css         # Scoped styles (plain CSS — no LESS variables)
│   ├── inlineJavascript.js   # Widget logic
│   ├── config.json           # BAW metadata: binding type, config options, business objects
│   ├── datamodel.md          # Data shape documentation
│   ├── eventHandler.md       # Event handler documentation
│   └── events/               # Optional BAW event handlers
├── AdvancePreview/
│   ├── {widget_name}.html        # Preview styles + container (replace placeholder)
│   └── {widget_name}Snippet.js  # BAW mixObject preview (replace placeholder)
└── README.md
```

## Data model

See [widget/datamodel.md](widget/datamodel.md).

## Packaging

1. If this widget has business objects, run: `python3 scripts/register_business_objects.py`
2. Run: `python3 scripts/package_baw.py` (the packager auto-discovers all widgets under `widgets/`)
3. Import `output/Custom_Widgets_{{version}}.twx` via BAW Process Admin Console → Toolkits → Import

Generated: {datetime.now().strftime('%Y-%m-%d')}
"""
    (base_path / "README.md").write_text(readme_md)
    print("✓ Created README.md")

    print()
    print("=" * 70)
    print(f"✅ Widget '{widget_name}' scaffolded successfully!")
    print()
    print("📝 Next steps:")
    print(f"   1. Implement widget logic in {widget_path}/")
    print(f"   2. Replace AdvancePreview placeholder with mixObject pattern")
    print(f"   3. Run: python3 scripts/package_baw.py")
    print("=" * 70)

    return True


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 create_widget_template.py WidgetName [description] [--events event1,event2,...]")
        print()
        print("Options:")
        print("  --events: Comma-separated list of event handlers to create")
        print("            Available: load, change, view, validate, unload")
        print("            Use 'all' to create all five handlers")
        print()
        print("Examples:")
        print('  python3 create_widget_template.py MyWidget "A custom widget"')
        print('  python3 create_widget_template.py MyWidget "A widget" --events load,change')
        print('  python3 create_widget_template.py MyWidget "A widget" --events all')
        sys.exit(1)

    widget_name = sys.argv[1]
    description = ""
    events = []

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--events":
            if i + 1 < len(sys.argv):
                events_arg = sys.argv[i + 1]
                if events_arg.lower() == "all":
                    events = ["load", "change", "view", "validate", "unload"]
                else:
                    events = [e.strip().lower() for e in events_arg.split(",")]
                    valid_events = ["load", "change", "view", "validate", "unload"]
                    invalid = [e for e in events if e not in valid_events]
                    if invalid:
                        print(f"❌ Error: Invalid event name(s): {', '.join(invalid)}")
                        print(f"   Valid events: {', '.join(valid_events)}")
                        sys.exit(1)
                i += 2
            else:
                print("❌ Error: --events requires a value")
                sys.exit(1)
        elif not description and not arg.startswith("--"):
            description = arg
            i += 1
        else:
            i += 1

    success = create_widget_structure(widget_name, description, events)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

# Made with Bob
