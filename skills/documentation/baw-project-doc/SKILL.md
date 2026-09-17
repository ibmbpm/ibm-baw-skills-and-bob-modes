---
name: baw-project-doc
description: "Generates comprehensive, up-to-date documentation for IBM Business Automation Workflow (BAW) applications by analyzing process models, services, integrations, business objects, and application artifacts — no MCP server or live server connection required. Accepts three input types: a TWX export file, a BPMN + XSD pair (output of the generate-baw-bpmn skill), or a ZIP archive containing a BPMN + XSD. Use whenever the user wants to document a BAW application, generate technical or functional documentation, understand what a BAW process app contains, or keep documentation synchronized with an application. Trigger phrases include \"document this BAW app\", \"generate documentation for\", \"what does this process app do\", \"document my TWX file\", \"generate a README for my BAW process\", \"summarize my BAW project\", \"document this BPMN\"."
metadata:
  version: "1.0.0"
---

# BAW documentation

Generate comprehensive Markdown documentation for an IBM BAW application. No MCP server
or live server connection required.

## Input paths

Three input types are accepted: a TWX export, a BPMN + XSD pair, or a ZIP archive
containing a BPMN + XSD.

### Step 0 — Scan the workspace first

Before saying anything to the user, use the file tools to search:

1. `business-processes/bpmn/` recursively for `.bpmn`, `.xsd`, and `.zip` files.
2. `business-processes/` recursively for `.twx` files.

**Did the user name a specific process?**

- If **yes** (e.g. "document Cook Pizza") — match the name against folder/file names
  case-insensitively, then proceed directly once found. Tell the user what you found:

  > "Found `<filename>` in `business-processes/<path>/`. Documenting it now."

- If **no specific project was named** — stop and ask. This applies even when only one
  artifact exists in the workspace. Do not assume or proceed:

  > "I found the following BAW artifacts in your workspace:
  >
  > - `<path/to/File1.bpmn>` (BPMN + XSD)
  > - `<path/to/File2.twx>` (TWX export)
  >
  > Which one would you like me to document?"

  Wait for the user's answer before doing anything else.

**Found nothing?** Do not ask the user to "provide a file". Instead, tell them how to
get one — the most natural source for a BAW project is a TWX export from Workflow Center:

> "I couldn't find any BAW artifacts for that project in `business-processes/`. To
> document it, export the application from IBM Workflow Center:
>
> 1. Open **Workflow Center** and navigate to your process app.
> 2. Click the snapshot you want to document (or create one if needed).
> 3. Select **Export** and save the `.twx` file.
>    (See [Importing and exporting projects and toolkits](https://www.ibm.com/docs/en/baw/26.0.x?topic=snapshots-importing-exporting-projects-toolkits).)
>
> Then share the file path (e.g. `C:\Users\you\Downloads\MyApp - v1.twx`) and I'll
> document it. Alternatively, if you already have a `.bpmn`/`.xsd` pair or a ZIP
> from the `generate-baw-bpmn` skill, share those instead."

---

### Path A — TWX file

A BAW process application or toolkit export (`.twx`).

**Coverage:** processes, services (all types), business objects, coach views.

---

### Path B — BPMN + XSD pair (or ZIP)

A `.bpmn` file and companion `.xsd` produced by the `generate-baw-bpmn` skill.
If the user provides a `.zip`, unzip it first to locate the `.bpmn` and `.xsd` inside.

**Coverage:** process flow, roles/lanes, all steps and decisions, process variables,
business objects and their fields. Services and coach views are not available from
this input type — note this in the Assumptions & Gaps section.

---

## Steps

### 1 — Discover and identify input

Follow Step 0 above to scan the workspace and confirm the file with the user (or
request one if nothing is found). Once you have a confirmed file path, determine
which input path applies (A = TWX, B = BPMN+XSD or ZIP) and collect the data.

### 2 — Read the reference files

Before generating documentation, read:
- For Path A: `references/TWX_ANALYSIS.md`
- For Path B: `references/BPMN_XSD_ANALYSIS.md`
- Always: `references/DOCUMENTATION_OUTPUT.md` — required output structure, section
  order, table formats, and Mermaid diagram conventions

### 3 — Generate the documentation

Write the Markdown documentation to:
```
docs/baw/<AppName>/<AppName>-documentation.md
```

Follow `references/DOCUMENTATION_OUTPUT.md` exactly. Required sections:
1. Application Overview
2. Processes (one subsection per BPD — flow diagram, steps table, variables table, decision logic, timers)
3. Services (one subsection per service — type, parameters, steps, endpoints)
4. Business Objects (one subsection per non-primitive BO — field table)
5. Coach Views (one subsection per coach view — config options, event handlers)
6. Integration Points (consolidated table of all external endpoints)
7. Assumptions & Gaps (skipped artifacts, missing descriptions, Path B limitations)

If a section has no data, include the heading with a note — never omit a section.

### 4 — Post a plain-language summary in chat

After writing the file, post a conversational summary **directly in the chat response** (not as a file). This is the first thing the user reads — write it for a business analyst or project manager, not a developer.

Structure the summary as follows:

**`<App Name> — Project Summary`**

One short paragraph: what the application does and who uses it.

**Process Flow** — Mermaid diagram of the main BPD, followed by:
- Swimlanes list (inline, e.g. "Swimlanes: Hiring Manager · General Manager · HR · System")
- **Key decisions** bullet list: for each gateway, one line explaining what it routes and why
- **Process variables**: inline list of data objects

**Services (`N` total)** — a compact table: Service | Type | Purpose. One row per service; keep Purpose to one short phrase.

**Coach Views (`N`)** — a compact table: View | Purpose.

**Notable gaps** — a short bullet list covering only the gaps that matter to someone using or extending the app (skip low-level extractor internals unless they affect usability). Each bullet in plain English — no XML tag names.

Tone rules:
- Write in plain English. Avoid BAW jargon (no "CSHS", "BPD", "microflow", "Call Activity") unless the term is immediately explained.
- Be concrete: name the roles, name the decisions, name what data flows through.
- Keep the whole summary readable without needing to open the document.

### 5 — Report

After the summary, add a short closing line:

> Full technical documentation written to `docs/baw/<AppName>/<AppName>-documentation.md`.

## Boundaries

**In scope:**
- Documenting from a TWX export, a BPMN+XSD pair, or a ZIP containing BPMN+XSD
- Running `extract_twx.py` for TWX inputs; direct XML parsing for BPMN+XSD inputs
- Documenting all artifact types present in the input

**Out of scope — redirect clearly:**
- **REST API path:** This path is deferred and not yet in scope.
- **MCP path** (`get_process_model`, `export_solution_expanded`): handled separately once MCP tools are available
- **Deploying to BAW or importing artifacts**: use `generate-baw-bpmn` + `package-baw-toolkit`
- **Generating new BPMN from descriptions**: use `generate-baw-bpmn`
- **Generating or modifying Business Object import files**: use `generate-baw-business-objects`
- **Creating coach widgets**: use `create-baw-widget`
- **Modifying the application being documented**: this skill is read-only
