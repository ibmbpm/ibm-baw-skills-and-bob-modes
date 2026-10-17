---
name: create-baw-widget
description: Creates or modifies IBM Business Automation Workflow (BAW) custom Coach View widgets — the widgets/{WidgetName}/ folder structure with Layout.html, InlineCSS.css, inlineJavascript.js, config.json, business object JSON, optional event handlers, and BAW-integrated preview files — then packages them into an importable .twx toolkit file. Use this whenever the user asks to build, scaffold, update, or fix a BAW/BPM coach widget, custom coach view, or "widget" in a BAW/BPMN/Process Designer project — including requests like "add a new coach widget for X", "package my widgets into a TWX", "this widget's preview isn't showing in the designer", "the widget isn't picking up my list data", or "style this widget with the Carbon theme." Does not deploy to a BAW server — that is a separate step.
license: Apache-2.0
compatibility: "IBM BAW 22.x and later; IBM CP4BA 22.x and later"
allowed-tools:
  - Read
  - Edit
  - Bash
metadata:
  version: "1.0.0"
  display_name: BAW Coach Widget Builder
  short_description: Scaffold, modify, and package IBM BAW custom Coach View widgets into an importable TWX toolkit file.
  author: IBM BAW Team
---

# Create BAW Widget

Build or modify an IBM BAW (Business Automation Workflow) custom Coach View widget, then package it into an importable `.twx` toolkit file. A widget lives under `widgets/{WidgetName}/` in a BAW toolkit project and is a small bundle of HTML/CSS/JS that BAW's Coach Designer loads into a running coach.

Two real widgets are bundled as reference implementations in `assets/examples/`:
- `assets/examples/DateOutput/` — a simple display-only widget (formats and shows a date, one `change.js` event handler, no business object)
- `assets/examples/TasksList/` — a more complex widget with a business object (`TaskItem.json`), two event handlers (`load.js` + `change.js`), and a full preview

Open the one structurally closer to what you are building and mirror its patterns rather than inventing structure from scratch.

## Phase 1 — Widget Authoring

### Steps

1. **Clarify the widget request.** Get the widget name (PascalCase, for example, `ProgressBar`, not `progress-bar` or `progressBar`) and what it should display or do. Figure out whether this is a new widget, a modification to an existing one, or just a preview/metadata/docs update — that determines which of the steps below actually apply.

2. **Inspect before you build.** The two committed examples in `assets/examples/` are the **primary references** — they are always present after a clone and represent proven, working patterns:
   - `assets/examples/DateOutput/` — simple display widget, scalar binding, one `change.js`, no business object. Use as the base for any widget with a plain string/date/number/boolean binding.
   - `assets/examples/TasksList/` — complex widget, list binding, business object (`TaskItem.json`), two event handlers. Use as the base for any widget that renders a collection or needs a custom business object.

   Open the example that most closely matches the widget you are building (category: simple display vs. list/business-object-backed) and mirror its file structure, config conventions, and preview pattern rather than inventing from scratch.

   If the project already has sibling widgets in `widgets/`, glance at 1–2 of them for any project-specific naming or layout conventions that differ from the examples, but treat the `assets/examples/` files as the source of truth for correct implementation patterns. Sibling widgets are references to read, not to edit — do not modify any widget other than the one requested unless the user explicitly asks.

3. **Create the required files** under `widgets/{WidgetName}/widget/`:
   - `Layout.html` — the outermost element must be `<div class="{widgetname}_maincontentbox">` (underscore before `maincontentbox`). This class is the scope anchor for both CSS and JS. Add ARIA roles and labels where the widget conveys state (for example, `role="progressbar"` with `aria-valuenow`). Do not add `id` attributes. See the DOM element lookup gotcha below for the reason.
   - `InlineCSS.css` — every rule must be prefixed with `.{widgetname}_maincontentbox` to prevent collisions with BAW's own styles and other widgets. Read the **CSS scoping** and **Carbon theme** gotchas below before writing CSS.
   - `inlineJavascript.js` — look up DOM elements using `this.context.element.querySelector(".{widgetname}_maincontentbox")` then `.querySelector()` from that container. Never use `document.getElementById()` or `getElementsByTagName`. Read the **DOM element lookup** gotcha below before writing JS.

4. **Add config.json and business objects only if the widget needs them.** If the widget binds to more than a plain string/date/boolean, or exposes configurable options, create `widget/config.json` and any business-object JSON files it references. Read the **Business object format rules** section below — format errors here cause packaging failures. Skip this step for a widget with no meaningful config.

5. **Add event handlers only if the widget's behavior requires them.** Event handler files go in `widget/events/` and are entirely optional. Decide per-event:
   - `load.js` — one-time init or registering a custom BAW event handler
   - `change.js` — re-render when bound data changes; only use this when `"changeFunction": true` in `config.json` (see Business object format rules)
   - `view.js` — refresh when the widget becomes visible (for example, when it is in a tab)
   - `validate.js` — custom validation beyond HTML5 (return `true`/`false`)
   - `unload.js` — clean up timers/listeners the widget created

   Start event handler files with `var _this = this;` to capture the BAW widget context — `this` loses its binding inside nested callbacks.

6. **Always add a preview** under `AdvancePreview/{WidgetName}.html` + `AdvancePreview/{WidgetName}Snippet.js`. Every widget must have these two files or BAW Designer shows "Error loading helper JS or HTML snippet files" on the canvas. See **Preview rules** below before writing them — the `.html` file content rule is a common source of the doubled-widget bug.

7. **Add a palette icon.** `widgets/{WidgetName}/{WidgetName}.svg`, 120×120px square, visually representing the widget so it is recognizable in the BAW Designer widget catalog. The packager auto-detects this file by name — naming must match exactly (case-sensitive).

8. **Write or update widget-local docs.** `widget/datamodel.md` (what shape of data the widget expects) and, if it has events, `widget/eventHandler.md` (what each event does). Keep these in sync with the actual implementation — stale docs are worse than no docs.

9. **Validate before moving to packaging.** Check naming is consistent across the widget folder, preview files, and config (a `WidgetNameSnippet.js` that does not match the folder name silently breaks the BAW preview loader). Check docs match the real inputs/options/events.

### Optional: scaffold with the bundled script

`scripts/create_widget_template.py` generates a starting skeleton. It can be run from any directory — the script always writes to `widgets/` inside the skill root:

```bash
python3 scripts/create_widget_template.py WidgetName "Widget description" --events load,change
```

Omit `--events` for no handlers, or use `--events all` for all five. Treat its output as a starting point, not a finished widget: its CSS is generic and its `AdvancePreview` output is a placeholder — replace preview files by hand following step 6 and the pattern in `assets/examples/`.

---

## Phase 2 — Package into TWX

After all widget files are complete and validated, package them into an importable `.twx` toolkit file. Everything needed is already inside the skill — no copying to a separate project directory is required.

### Packaging steps

All commands run from the skill root (the `create-baw-widget/` folder, for example `src/skills/create-baw-widget/` or `.bob/skills/create-baw-widget/`).

**Step A — Register business objects** (skip if no widget has a business object):
```bash
python scripts/register_business_objects.py
```
This assigns stable BAW class IDs to all business object JSON files under `widgets/*/widget/` and writes them to `scripts/toolkit_packager/baw_custom_types.json`. The script creates this file the first time it runs. Idempotent — safe to run multiple times.

**Step B — No action needed.** The packager discovers every subfolder inside `widgets/`. You do not maintain a widget list.

**Step C — Run the packager:**
```bash
python scripts/package_baw.py
```
This auto-increments the patch version in `assets/toolkit.config.json`, builds the TWX, and writes it to `output/{ToolkitName}_{version}.twx`. The `widgets/` and `output/` folders are created inside the skill root by the scaffold and packaging scripts, so they might not exist in a fresh clone.

**Step D — Report the result.** Tell the user the output path, the version, which widgets were included, and that the file is ready to import into BAW:
- **Traditional BAW (Workflow Center):** Workflow Center > Process Apps > Import
- **CP4BA containerized (Business Automation Studio):** Business Automation Studio > Business automations > Toolkits > Import

### toolkit.config.json fields

| Field | Purpose |
|---|---|
| `toolkit.name` | Display name in BAW (for example, `"Custom Widgets"`) |
| `toolkit.shortName` | Short alias (for example, `"CW"`) |
| `toolkit.version` | The packager increments this value each run |
| `toolkit.bawVersion` | BAW template version — must match a folder under `assets/templates/BaseTWX/` (use `"25.0.1"` for CP4BA 25.x/26.x) |
| `toolkit.id` | Stable GUID for the toolkit — do not change after first import |

---

## Critical gotchas

### DOM element lookup — always use `this.context.element.querySelector()`

BAW rewrites element `id` attributes at runtime when it inserts a coach view into the page, so `document.getElementById()` silently returns `null`.

The legacy `getElementsByTagName("div").ElementName` pattern (using HTML `name=` attributes) may work inside BAW's embedded browser, but it is not portable to standard browsers and is fragile when elements are renamed. **The preferred pattern** is `querySelector` scoped to `this.context.element`, which is BAW's own reference to this widget's root node and is consistent across all environments:

```html
<!-- Layout.html — use a unique outer wrapper class as the scope anchor -->
<div class="mywidget_maincontentbox">
    <div class="mywidget-track">
        <div class="mywidget-fill"></div>
    </div>
    <span class="mywidget-value"></span>
</div>
```

```javascript
// inlineJavascript.js / events/change.js
// Step 1 — anchor to this widget's root (never use document.getElementById)
var container = this.context.element.querySelector(".mywidget_maincontentbox");

// Step 2 — find children relative to the container
var fill    = container.querySelector(".mywidget-fill");
var valueEl = container.querySelector(".mywidget-value");
```

The outer wrapper class (`mywidget_maincontentbox`) also serves as the CSS scope prefix — see the **CSS scoping** gotcha below.

**Never use:**
- `document.getElementById("…")` — BAW rewrites IDs at runtime, always returns null

---

### Always use `min-height`, not `height`

BAW renders each widget inside a `<table>` cell. Setting a CSS `height` on a `<div>` child of a `<td>` is unreliable — in some browser and BAW combinations the browser ignores it and the div collapses to zero. If the widget has no visible content on initial load (for example, the binding has not resolved yet), the outer wrapper collapses and the widget disappears on the canvas. Use `min-height` throughout — browsers honor it reliably inside table cells.

Set `min-height` on `{widgetname}_maincontentbox` and on inner track elements:

```css
.mywidget_maincontentbox {
    width: 100%;
    min-height: 35px;   /* 35px for compact widgets; 120px for taller ones */
    padding: 0.5rem;
}
.mywidget_maincontentbox .mywidget-track {
    width: 100%;
    min-height: 8px;          /* use min-height, not height */
    background-color: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
}
.mywidget_maincontentbox .mywidget-fill {
    min-height: 8px;
    background-color: #0f62fe;
}
```

A nested `<table>` layout is not necessary — `min-height` on plain `<div>` elements works correctly in practice.

---

### CSS scoping — prefix every rule with the outer wrapper class

BAW loads all widget stylesheets into a single page scope. Generic selectors like `.progressbar-track` collide with BAW styles and with other widgets. Prefix every CSS rule with the unique outer wrapper class:

```css
/* CORRECT — scoped, collision-safe */
.mywidget_maincontentbox .mywidget-track { min-height: 8px; background-color: #e0e0e0; }
.mywidget_maincontentbox .mywidget-fill  { min-height: 8px; background-color: #0f62fe; }

/* WRONG — unscoped, collides with other styles */
.mywidget-track { min-height: 8px; }
```

Name the outer wrapper class with an **underscore** separator (`mywidget_maincontentbox`) — this visually distinguishes it from child classes and matches the convention used across working widgets in the reference repo.

---

### InlineCSS.css is plain CSS, not LESS

BAW widget stylesheets do not go through LESS preprocessing — `color: @bpm-color-primary;` is invalid CSS and will silently produce no styling. Use the literal hex value and put the Carbon variable name in a comment:

```css
.progressbar-fill {
    background-color: #0f62fe; /* @bpm-color-primary */
    font-family: 'IBM Plex Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif; /* @bpm-font-family-sans-serif */
    color: #161616; /* @bpm-text-color */
}
```

The full color/typography/spacing table is in `references/CARBON_THEME_VARIABLES.md` — open it when writing CSS rather than guessing hex values.

### List-bound data comes wrapped in `.items`

When `config.json`'s `bindingType` has `"isList": true`, BAW wraps the array in an object: `{ items: [...] }`. Reading `this.getData()` directly gives you that wrapper object, not the array:

```javascript
// bindingType.isList === true
var items = this.getData().items;   // correct
var items = this.getData();         // wrong — this is the wrapper object, not an array
```

### Business object format rules

Incorrect business object format is the most common cause of packaging failures. Three rules are non-negotiable:

**Rule 1 — Business object JSON must have BOTH `"name"` AND `"type": "businessObject"`:**

```json
{
  "name": "TaskItem",
  "type": "businessObject",
  "description": "A single task in the task list",
  "properties": [
    { "name": "id",     "type": "String",  "required": true,  "description": "Unique task ID" },
    { "name": "title",  "type": "String",  "required": true,  "description": "Task title" },
    { "name": "done",   "type": "Boolean", "required": false, "description": "Completion flag" }
  ]
}
```

The packager expects this format. Some older widgets in the reference repo use `"type": "TaskItem"` only (without `"name"`). The packager has a fallback for that format, but the fallback is less reliable. Use both `"name"` and `"type": "businessObject"` in this project.

**Rule 2 — `config.json`'s `businessObjects` must be an array of objects with `{name, file}`, not a string array:**
```json
"businessObjects": [
  { "name": "TaskItem", "file": "TaskItem.json" }
]
```

**Rule 3 — Set `"changeFunction": false` for complex BO bindings; use `binding.addDataChangeListener` in `inlineJavascript.js` instead of a separate `change.js`:**

For widgets bound to a business object (not a plain string/number), the reactive update pattern is:

```javascript
// inlineJavascript.js — reactive BO binding (no change.js needed)
var me = this;
if (this.context && this.context.binding && this.context.binding.addDataChangeListener) {
    this.context.binding.addDataChangeListener(function(newValue) {
        // newValue is the BO instance
        renderWidget(newValue);
    });
}
```

And in `config.json`:
```json
"changeFunction": false
```

Adding a `change.js` on top of `addDataChangeListener` causes double-renders. Only use a standalone `events/change.js` (with `"changeFunction": true`) for simple scalar bindings where the Snippet pattern is sufficient.

Valid property types: `String`, `Integer`, `Decimal`, `Boolean`, `Date`. Every property must have all four fields: `name`, `type`, `required`, `description`.

---

## Preview rules — read before writing AdvancePreview/ files

Every widget must have both `AdvancePreview/{WidgetName}.html` and `AdvancePreview/{WidgetName}Snippet.js`. Missing either file causes BAW Designer to show "Error loading helper JS or HTML snippet files" on the canvas.

### Two valid preview patterns — choose based on CSS approach

BAW injects `{WidgetName}.html` content **and** runs `{WidgetName}Snippet.js`. The two files work together; the right pattern depends on how you write CSS:

**Pattern A — Blank HTML + inline `style=` in Snippet (simple widgets)**

Use when the Snippet builds all DOM with inline `domAttr.set(el, "style", "…")` and needs no shared stylesheet. The `.html` file must be a single blank line:

```html
<!-- GreenDropdown.html — correct: blank placeholder -->

```

If `.html` has visible markup AND the Snippet also builds DOM, the widget appears **twice** on the canvas.

**Pattern B — HTML with `<style>` block + `DesignContentBox`-scoped CSS + Snippet (complex widgets)**

Use when the preview has enough CSS to warrant a stylesheet. The `.html` file contains the `<style>` block and a `<div class="SPARKPanel panel">` wrapper; the Snippet builds live DOM inside the `inputDiv`. Every CSS selector in the `<style>` block must go through `.DesignContentBox`, because the Snippet adds that class with `domClass.add(container, "DesignContentBox")`:

```html
<!-- ProgressBar.html — Pattern B -->
<style>
.progressbar_maincontentbox .DesignContentBox .progressbar-track {
    width: 100%; height: 8px; background-color: #e0e0e0;
}
.progressbar_maincontentbox .DesignContentBox .percentage-value {
    font-size: 2rem; font-weight: 600; color: #24a148;
}
</style>
<div class="SPARKPanel panel">
    <div class="widget-heading"><span class="widget-title">My Widget Preview</span></div>
    <div class="widget-body"><!-- Snippet builds DOM here --></div>
</div>
```

And in the Snippet's `generateSampleData`, add `DesignContentBox` to every container node whose children are targeted by the stylesheet:

```javascript
var container = domConstruct.create("div", null, this.context.coachViewData.inputDiv);
domClass.add(container, "progressbar_maincontentbox");

var inner = domConstruct.create("div", null, container);
domClass.add(inner, "DesignContentBox");      // ← required for CSS to apply
domClass.add(inner, "progressbar-container");
```

### Snippet.js structure

`{WidgetName}Snippet.js` must export a `mixObject` with all five methods, using Dojo APIs — not vanilla DOM:

```javascript
var mixObject = {
    createPreview: function (containingDiv, labelText, callback) {
        var previewLayerUri = this.context.getManagedAssetUrl(
            "BPMExt-Controls.preview.js", this.context.assetType_WEB, "SYSBPMUI");
        require([previewLayerUri], this.lang.hitch(this, function () {
            require(["dojo/dom-construct","dojo/dom-class","dojo/dom-attr",
                     "bpmui/preview/BPMExt-Core-Designer"],
            this.lang.hitch(this, function (domConstruct, domClass, domAttr, bpmext) {
                bpmext.uidesign.css.ensureGlyphsLoaded(this);
                bpmext.uidesign.css.ensureSparkUIClass(containingDiv);
                // build form-group, label, inputDiv, then call:
                this.generateSampleData(domConstruct, domAttr, domClass);
                callback();
            }));
        }));
    },
    getLabelDomElement: function () { return this.context.coachViewData.label; },
    generateSampleData: function (domConstruct, domAttr, domClass) { /* build widget DOM here */ },
    propertyChanged: function (propertyName, propertyValue) { /* update preview on option change */ },
    modelChanged: function (propertyName, propertyValue) { /* usually a no-op */ }
};
```

Copy the full wiring from `assets/examples/TasksList/AdvancePreview/task.js` (Pattern B with `<style>` block) or `assets/examples/DateOutput/AdvancePreview/DateOutputSnippet.js` (Pattern A blank HTML) and replace only `generateSampleData` — the Dojo module require chain is easy to get wrong from memory.

---

## Boundaries

**In scope:** creating/editing widget files, preview files, widget config and business objects, widget-local documentation, and packaging widgets into a `.twx` file for manual import into BAW.

**Out of scope:** deploying the `.twx` to a BAW server via API or MCP tools (that is a separate deployment step), designing overall coach layouts that compose multiple widgets into a screen, and parsing business documents into business objects.

---

## Output format

For each widget created or changed, report:
- The files created/modified, as a file tree rooted at `widgets/{WidgetName}/`
- Which optional pieces you included and *why* (for example, "added `change.js` because the widget re-renders on data updates; skipped `load.js` — no init logic needed")
- Any Carbon variables used, so the user can sanity-check the visual match
- If a preview was created, confirm it follows the mixObject pattern (not a placeholder)
- After packaging: the output `.twx` path, version, and list of included widgets

After delivering the Phase 1 summary, always ask the user whether they want to proceed to Phase 2 (TWX packaging). Use `ask_followup_question` with exactly two suggestions: one to proceed and one to skip. Do not proceed to Phase 2 automatically.

---

## Example

**Input:** "Create a BAW widget called RatingStars that displays a 1–5 star rating bound to an integer, then package it."

**Phase 1 output:**
1. Read `assets/examples/DateOutput/` (primary reference — simple, single-value, no business object needed).
2. Create `widgets/RatingStars/widget/Layout.html` with `role="img"` and `aria-label` describing the rating.
3. Create `widgets/RatingStars/widget/InlineCSS.css` using `#c6c6c6` (`/* @bpm-color-primary-light */`) for empty stars and `#0f62fe` (`/* @bpm-color-primary */`) for filled ones — hardcoded values, not LESS references.
4. Create `widgets/RatingStars/widget/inlineJavascript.js` reading `this.getData()` (scalar binding, no `.items` needed).
5. Skip `config.json`/business object (plain integer binding) and skip all event handlers — note this explicitly.
6. Create `widgets/RatingStars/AdvancePreview/RatingStars.html` — **blank** (single newline only).
7. Create `widgets/RatingStars/AdvancePreview/RatingStarsSnippet.js` — `mixObject` with `generateSampleData` rendering five star spans, copied from `DateOutputSnippet.js` wiring.
8. Create `widgets/RatingStars/RatingStars.svg` (120×120, five stars).
9. Create `widgets/RatingStars/widget/datamodel.md`.

**Phase 2 output:**
1. The packager discovers `RatingStars` in the `widgets/` folder. No manual step is needed.
2. Run `python3 scripts/package_baw.py`.
3. Report: `output/Custom_Widgets_1.0.1.twx` (42 KB) — contains RatingStars. Ready to import via:
   - **Traditional BAW:** Workflow Center > Process Apps > Import
   - **CP4BA (Studio):** Business Automation Studio > Business automations > Toolkits > Import
