# Create BAW Widget — Documentation

> Creates or modifies IBM Business Automation Workflow (BAW) custom Coach View widgets — the widgets/{WidgetName}/ folder structure with Layout.html, InlineCSS.css, inlineJavascript.js, config.json, business object JSON, optional event handlers, and BAW-integrated preview files — then packages them into an importable .twx toolkit file.

## Purpose

This skill helps developers create, scaffold, update, or fix custom UI elements (Coach Views) in IBM Business Automation Workflow (BAW). You build custom widgets as modular HTML, CSS, and JS components and package them into an importable `.twx` toolkit file. You import the file into the BAW authoring environment: Workflow Center for traditional BAW, or Business Automation Studio for CP4BA containerized deployments. Use this skill when you need to build modern, custom-styled UI elements that go beyond the stock BAW controls, style components to match the Carbon Design System, or fix canvas preview issues in the Coach Designer.

## Setup and configuration

- **No server deployment needed:** This skill runs entirely on your development machine. It produces the packaged `.twx` file as an output artifact that you import manually.
- **Python 3.x environment:** The local scaffolding, business object registration, and toolkit packager scripts require Python 3.x (standard library only). No third-party pip dependencies are needed.
- **No external accounts or MCP servers:** This skill does not require third-party API keys or MCP configurations.
- **Scaffolding and packaging scripts:**
  - `python scripts/create_widget_template.py`: Optional helper script to generate the initial widget skeleton.
  - `python scripts/register_business_objects.py`: Registers new business objects and maps each one to a stable GUID.
  - `python scripts/package_baw.py`: Packs all widgets into a `.twx` toolkit and increments the version number automatically.

## Compatibility

- **IBM BAW and CP4BA compatibility:** Designed and tested for compatibility with IBM Business Automation Workflow 25.x, 26.x, and legacy IBM BPM systems.
- **BAW WebPD manual import only:** The skill packs widgets into standard `.twx` toolkit files. You must complete the import step manually in the authoring environment:
  - **Traditional BAW (Workflow Center):** Workflow Center > Process Apps > Import
  - **CP4BA containerized (Business Automation Studio):** Business Automation Studio > Business automations > Toolkits > Import
- **Plain CSS only, scoped to the widget:** Write standard CSS. Local packaging does not support LESS compilation. The skill simulates Carbon Design System theme variables with literal hex values and variable name comments.
- **Dojo-based canvas preview pattern:** The Coach Designer canvas preview must follow the BAW Dojo `mixObject` structure. You cannot manipulate standard vanilla DOM elements globally on the canvas.
- **Business object naming:** Use PascalCase for business object names and camelCase for property names. Each schema must define both `"name"` and `"type": "businessObject"`, or packaging fails.

## Prompt examples

### Create a simple, display-only widget with scalar data binding

**Prompt:**
> I need a new BAW coach widget called StatusBadge that shows a colored pill (green/yellow/red) with a text label, bound to a simple status string like 'ON_TRACK', 'AT_RISK', or 'DELAYED'. No business object is needed, keep it simple. Put it under widgets/StatusBadge/.

**What to expect:** Bob creates the `widgets/StatusBadge/` directory containing the `Layout.html`, `InlineCSS.css`, and `inlineJavascript.js` files, along with the `StatusBadge.svg` palette icon, `datamodel.md` documentation, and Dojo preview files under `AdvancePreview/`.

---

### Create a complex list-bound widget with a custom Business Object

**Prompt:**
> Create a widget called ApprovalHistory that renders a list of approval events (approver name, date, decision, comment) bound to a list of business objects. It should re-render whenever the bound data changes. Create any necessary business object JSON schemas as well.

**What to expect:** Bob scaffolds `widgets/ApprovalHistory/` with a custom `ApprovalEvent.json` business object schema, a `config.json` referencing this BO with list-binding enabled, a layout that renders rows of approval events, and reactive data change listeners in the JavaScript.

---

### Add interactive event handlers to an existing widget

**Prompt:**
> Add a load.js and change.js event handler to my existing MultiSelect widget in widgets/MultiSelect/ so that it registers a custom BAW event on load and re-renders whenever the selection changes.

**What to expect:** Bob adds `load.js` and `change.js` to `widgets/MultiSelect/widget/events/`, uses the `var _this = this;` pattern to scope the BAW context safely, and documents their behavior in `eventHandler.md`.

---

### Fix a broken Coach Designer canvas preview (Dojo mixObject pattern)

**Prompt:**
> Our TasksList widget's preview isn't showing up correctly in BAW Designer — can you check widgets/TasksList/AdvancePreview/ and fix it so it follows the proper BAW preview pattern and does not double-render on the canvas?

**What to expect:** Bob analyzes the preview HTML and JS, corrects the Dojo `require` modules, structures the JS as a valid `mixObject` exporting standard lifecycle methods (`createPreview`, `generateSampleData`), and ensures the HTML is blank or uses proper `.DesignContentBox` CSS scoping to prevent doubling.

---

### Register business objects and package widgets into a .twx toolkit

**Prompt:**
> I've finished making the ProgressBar and TasksList widgets. Please register any custom business objects and package them into a TWX file that I can import.

**What to expect:** Bob runs the business object registration script followed by the packager script, reports the final `.twx` output path and incremented version, and provides step-by-step import instructions for both Workflow Center (traditional BAW) and Business Automation Studio (CP4BA containerized).

---

### Out-of-scope redirect — deploying directly to a BAW server

**Prompt:**
> Please deploy the packaged ProgressBar widget directly to my BAW server located at dev-server.example.com.

**What to expect:** Bob explains that automated server deployment is out of scope for this skill and redirects you to use the standard authoring environment import UI — Workflow Center (traditional BAW) or Business Automation Studio (CP4BA) — for importing the generated `.twx` file.

---

### Out-of-scope redirect — designing a multi-coach page layout

**Prompt:**
> Can you design an entire loan application dashboard layout composing the StatusBadge, ProgressBar, and TasksList widgets together on one screen?

**What to expect:** Bob explains that composing multi-widget coach page layouts is a different step performed inside the BAW Coach Designer UI, and instead provides the datamodel specifications for each widget so you know exactly how to bind them on the page.
