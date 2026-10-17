---
name: baw-project-doc
description: "Generates comprehensive, up-to-date documentation for IBM Business Automation Workflow (BAW) applications by analyzing process models, services, integrations, business objects, and application artifacts — no MCP server or live server connection required. Accepts three input types: a TWX export file, a BPMN + XSD pair (output of the generate-baw-bpmn skill), or a ZIP archive containing a BPMN + XSD. Use whenever the user wants to document a BAW application, generate technical or functional documentation, understand what a BAW process app contains, or keep documentation synchronized with an application. Trigger phrases include \"document this BAW app\", \"generate documentation for\", \"what does this process app do\", \"document my TWX file\", \"generate a README for my BAW process\", \"summarize my BAW project\", \"document this BPMN\"."
license: Apache-2.0
compatibility: "IBM BAW 22.x and later; IBM CP4BA 22.x and later"
allowed-tools:
  - Read
  - Edit
metadata:
  version: "1.0.0"
  display_name: BAW Project Documentation
  short_description: Generate comprehensive Markdown documentation for a BAW application from a TWX export, BPMN+XSD pair, or ZIP archive.
  author: IBM BAW Team
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
get one — the most natural source for a BAW project is a TWX export from the authoring
environment:

> "I couldn't find any BAW artifacts for that project in `business-processes/`. To
> document it, export the application from your BAW authoring environment:
>
> - **Traditional BAW (Workflow Center):**
>   1. Open **Workflow Center** and navigate to your process app.
>   2. Click the snapshot you want to document (or create one if needed).
>   3. Select **Export** and save the `.twx` file.
>      (ref: [Importing and exporting projects and toolkits](https://www.ibm.com/docs/en/baw/26.0.x?topic=snapshots-importing-exporting-projects-toolkits))
>
> - **CP4BA containerized (Business Automation Studio):**
>   1. Open **Business Automation Studio** and navigate to **Business automations**.
>   2. Open your process application and select the snapshot.
>   3. Use the overflow menu → **Export** to save the `.twx` file.
>
> Then share the file path (e.g. `C:\Users\you\Downloads\MyApp - v1.twx`) and I'll
> document it. Alternatively, if you already have a `.bpmn`/`.xsd` pair or a ZIP
> from the `generate-baw-bpmn` skill, share those instead."

---

### Step 0.5 — Ask the user who the documentation is for

Once the input file is confirmed, use `ask_followup_question` to ask:

> "What is this documentation for?"

Present exactly these four options as suggestions:

- **Executive summary** — Business value and process overview for stakeholders, without implementation details.
- **Knowledge transfer (KT)** — Detailed process walkthroughs and developer guidance for teams inheriting the application.
- **Partner handoff** — Application overview with improvement opportunities highlighted for an external partner or client.
- **Technical reference** — Full technical documentation covering all processes, services, business objects, and integrations.

Wait for the user's selection before proceeding. Store the chosen audience as `<AUDIENCE>` for use in all subsequent steps.

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
- Always: `references/DOCUMENTATION_OUTPUT.md` — Technical Reference output structure,
  section order, table formats, and Mermaid diagram conventions
- Always: `references/AUDIENCE_FORMATS.md` — output structures for all four audiences

### 3 — Generate the documentation

Use `<AUDIENCE>` to select the correct output structure and file path from
`references/AUDIENCE_FORMATS.md`. Generate the documentation accordingly.

| Audience | Output file |
|---|---|
| Executive summary | `docs/baw/<AppName>/<AppName>-executive-summary.md` |
| Knowledge transfer (KT) | `docs/baw/<AppName>/<AppName>-kt-guide.md` |
| Partner handoff | `docs/baw/<AppName>/<AppName>-partner-handoff.md` |
| Technical reference | `docs/baw/<AppName>/<AppName>-documentation.md` |

Follow the structure defined in `references/AUDIENCE_FORMATS.md` for the selected
audience exactly. For **Technical reference**, follow `references/DOCUMENTATION_OUTPUT.md`
exactly as before — nothing changes for that audience.

**Content rules by audience:**

- **Executive summary:** Omit all implementation detail. No service steps, no Mermaid
  diagrams, no field-level business object tables. Lead every section with business
  context. If a section would only contain implementation detail, omit it.

- **Knowledge transfer (KT):** Include everything from Technical Reference, plus a
  step-by-step narrative walkthrough for each process, developer notes on each service,
  and a developer onboarding checklist. Flag any known issues or technical debt.

- **Partner handoff:** Include process flows and business objects at standard depth.
  Replace the Assumptions & Gaps section with a populated Improvement Recommendations
  table. Identify recommendations from: missing descriptions, hardcoded values that
  should be environment variables, undocumented endpoints, missing error handling,
  and deprecated service types.

- **Technical reference:** Follow `references/DOCUMENTATION_OUTPUT.md` unchanged.

If a section has no data, include the heading with a note — never silently omit a section
(except for Executive summary, where implementation-only sections are intentionally excluded).

### 4 — Post a plain-language summary in chat

After writing the file, post a conversational summary **directly in the chat response**
(not as a file). Tailor the summary content and tone to `<AUDIENCE>`:

**Executive summary audience:**
Lead with the business purpose in one paragraph. Follow with key roles (inline list)
and the main business outcome. No diagrams, no technical terms. Close with:
> Full executive summary written to `docs/baw/<AppName>/<AppName>-executive-summary.md`.

**Knowledge transfer (KT) audience:**
One paragraph on what the app does. Then bullet-point the most important things a
new developer needs to know: key integration dependencies, any known quirks, data
that flows through the process, and any open issues. Close with the onboarding checklist
preview and:
> Full KT guide written to `docs/baw/<AppName>/<AppName>-kt-guide.md`.

**Partner handoff audience:**
One paragraph describing what is being handed off. Mermaid diagram of the main process
flow. Then list the top improvement recommendations (up to 5, most impactful first).
Close with:
> Full partner handoff document written to `docs/baw/<AppName>/<AppName>-partner-handoff.md`.

**Technical reference audience:**
Follow the existing Step 4 format exactly:

`<App Name> — Project Summary`

One short paragraph: what the application does and who uses it.

**Process Flow** — Mermaid diagram of the main BPD, followed by:
- Swimlanes list (inline)
- **Key decisions** bullet list
- **Process variables**: inline list

**Services (`N` total)** — compact table: Service | Type | Purpose.

**Coach Views (`N`)** — compact table: View | Purpose.

**Notable gaps** — short bullet list.

Close with:
> Full technical documentation written to `docs/baw/<AppName>/<AppName>-documentation.md`.

**Tone rules (all audiences):**
- Write in plain English. Avoid BAW jargon unless the term is immediately explained.
- Be concrete: name the roles, name the decisions, name what data flows through.
- Keep the summary readable without needing to open the document.

## Boundaries

**In scope:**
- Documenting from a TWX export, a BPMN+XSD pair, or a ZIP containing BPMN+XSD
- Running `extract_twx.py` for TWX inputs; direct XML parsing for BPMN+XSD inputs
- Documenting all artifact types present in the input
- All four audience output formats

**Out of scope — redirect clearly:**
- **REST API path:** not in scope
- **MCP path** (`get_process_model`, `export_solution_expanded`): not in scope
- **Deploying to BAW or managing versions**: use `baw-deployment-manager` or `version-lifecycle-manager`
- **Generating new BPMN from descriptions**: use `generate-baw-bpmn`
- **Generating or modifying Business Object import files**: use `generate-baw-business-objects`
- **Creating coach widgets or task portals**: use `create-baw-widget` or `create-baw-portal`
- **Modifying the application being documented**: this skill is read-only
