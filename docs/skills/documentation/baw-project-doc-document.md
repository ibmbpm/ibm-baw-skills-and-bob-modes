# BAW Project Doc — Documentation

> Generates comprehensive, up-to-date documentation for IBM® Business Automation Workflow (BAW) applications by analyzing process models, services, integrations, business objects, and application artifacts — no MCP server or live server connection required.

## Purpose

This skill produces a complete Markdown documentation file for a BAW process application. Give it a TWX export, a BPMN + XSD pair (from the `generate-baw-bpmn` skill), or a ZIP archive containing those files, and it writes a structured document covering every process, service, business object, coach view, integration point, and gap it can identify. It also posts a plain-language summary in chat — written for a business analyst or project manager — so the key points are immediately readable without opening the file.

## Setup and configuration

- No special server access, MCP server, or API key is required.
- TWX input: Python 3.x is required to run `scripts/extract_twx.py`, which unpacks and parses the TWX archive. The script uses only the Python standard library (`zipfile`, `json`, `xml.etree.ElementTree`, `pathlib`) — no pip dependencies.
- BPMN + XSD / ZIP input: No Python needed — the files are parsed directly from XML using built-in tools.
- The skill searches `business-processes/` in your workspace automatically before asking for a file path.

## Compatibility

- TWX exports from BAW ≥ 8.6.x (CP4A flat layout) and older ≤ 8.5 subfolder layout are both supported. The extraction script handles both automatically.
- BPMN + XSD output from the `generate-baw-bpmn` skill is fully supported as an alternative input.
- Services, coach views, and integration endpoint details are not available from BPMN + XSD input. These are only extracted from a TWX export. The skill notes the gap automatically in the Assumptions & Gaps section.
- No live BAW server connection. REST API and MCP paths are out of scope for this skill.

## Prompt examples

### Document a process by name (workspace scan)

**Prompt:**
> Can you document my Expense Approval process?

**What to expect:** The skill searches `business-processes/` for any `.twx`, `.bpmn`, `.xsd`, or `.zip` matching "Expense Approval", confirms the found file with you, then generates the full documentation.

---

### Document when nothing is found in the workspace

**Prompt:**
> Can you generate documentation for my Leave Management application?

**What to expect:** The skill searches `business-processes/`, finds no match, and gives you clear instructions for exporting a TWX from IBM Workflow Center or providing a BPMN+XSD pair — no server credentials are requested.

---

### Document from a TWX export file

**Prompt:**
> Here is my TWX file: `C:\Downloads\HiringApp - v2.twx`. Please generate documentation.

**What to expect:** The skill runs `extract_twx.py` against the TWX, reads all processes, services, business objects, and coach views, and writes a 7-section Markdown document to `docs/baw/HiringApp/HiringApp-documentation.md`, then posts a plain-language project summary in chat.

---

### Document from a BPMN + XSD pair

**Prompt:**
> Document my BAW process from these files: `ExpenseApproval.bpmn` and `ExpenseApproval.xsd`

**What to expect:** The skill parses the BPMN for process flow, lanes, steps, and decision logic, and the XSD for business object schemas, then writes the documentation — noting in Assumptions & Gaps that services and coach views are not available from this input type.

---

### Document from a ZIP archive

**Prompt:**
> Here is my file: `CookPizza.zip`. Please document it.

**What to expect:** The skill unzips the archive to find the `.bpmn` and `.xsd` inside, then follows the same BPMN + XSD path, producing a full documentation file and a chat summary.

---

### Out-of-scope redirect — request for auto-generation via REST API or MCP

**Prompt:**
> Generate documentation for my BAW process app by connecting to the server.

**What to expect:** The skill explains that REST API and MCP server paths are not in scope for this skill and asks you to provide a TWX export, a BPMN + XSD pair, or a ZIP instead.

---

### Out-of-scope redirect — request to modify the application

**Prompt:**
> Document this BPMN and also fix the missing approval step.

**What to expect:** The skill generates the documentation (read-only), then directs you to the `generate-baw-bpmn` skill for any process authoring or modification work.
