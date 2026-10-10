---
name: generate-baw-business-objects
description: "Generates and modifies BAW Business Object import files — individual .bo.json files, a combined OpenAPI 3.0 JSON, a discovery report, and an optional toolkit TWX. Use when the user wants to generate Business Objects or BOs for a BAW process app or toolkit, modify an existing BO .json file, handle enum-to-Selection-BO conversion, or package BOs into a reusable TWX toolkit. Always use this skill for BO modifications — even simple field additions, removals, or renames — because the output must comply with BAW's specific OpenAPI format rules, include import instructions, and surface safety warnings when fields are removed or renamed. Three delivery options are available: WebPD UI import, new toolkit TWX, or updating an existing toolkit TWX. This skill covers ONLY Business Object artifacts — for BPMN process generation use generate-baw-bpmn instead."
license: Apache-2.0
compatibility: "IBM BAW 22.x and later; IBM CP4BA 22.x and later"
allowed-tools:
  - Read
  - Edit
  - Bash
metadata:
  version: "1.0.0"
  display_name: Generate BAW Business Objects
  short_description: Generate and modify importable BAW Business Object files (OpenAPI JSON, TWX toolkit) from any data model description.
  author: IBM BAW Team
---

# Generate BAW Business Objects

Produce importable BAW Business Objects from any data-model description, generating structured output files and helping the user choose how to deliver them into BAW.

**One important note about imported BOs:** they appear as read-only in WebPD after import. The correct workflow is: finalize all BO specs with Bob before importing, then import once. If changes are needed later, update the files with Bob and re-import — re-importing overrides the previous BOs.

## Output folder structure

All files are written under `business-objects/` at the workspace root:

```
business-objects/<domain-slug>/
├── generated_bos/      ← one <BOName>.bo.json per BO (complex + selection)
├── reports/            ← <domain-slug>.discovery-report.md
└── output/
    ├── <domain-slug>.json   ← combined OpenAPI 3.0 import file
    └── twx/                 ← *.twx files (options 2 and 3 only)
```

- `<domain-slug>` is derived from the BO domain, slugified to kebab-case (e.g. `invoice-management`, `life-insurance`).
- **Collision Avoidance (CRITICAL):** Before writing any files, you MUST check if `business-objects/<domain-slug>/` already exists in the workspace. If the folder exists, you MUST append an incrementing suffix (e.g., `<domain-slug>_1`, `<domain-slug>_2`) and write to that new directory instead. Never overwrite or merge files into an existing folder from a previous run.
- Always finish by listing every generated file path.

## Steps

### 1. Understand the data model

Read the user's input carefully. Accept any of:
- Natural language description of the data structures
- A table or bulleted list of objects and fields
- A pasted document (Word export, PDF text, markdown, meeting notes)
- An existing OpenAPI 3.0 BO JSON the user wants to modify

Extract every distinct "thing" from the description. Each distinct thing — an order, a customer, an address, a line item — becomes its own schema.

Before writing files, do a quick mental pass:

**Completeness check:**
- Did you find ALL the distinct objects? Walk the description once more and look for nouns that carry data (not just action verbs).
- Did you expand each object to its natural fields? If the user said "Customer," they probably want name, email, phone, and an address — not just an id.
- Are there any list relationships? If an order has multiple line items, model `OrderItem` separately and make `Order.items` an array referencing `OrderItem`.
- Are there fields with a fixed set of values (described as an enum, dropdown, or controlled list)? Note each one — each becomes a Selection BO.

**Task list planning (update_todo_list):**
- When initializing the checklist, keep it clean and condensed.
- Group the generation of all individual `.bo.json` files into a single task item (e.g., `[ ] Write generated_bos/ files (<Count> BOs)`).
- Do NOT list each individual `.bo.json` file as its own separate checklist item. This avoids excessive tool calls and clutter without impacting output quality.
- Keep high-level deliverables (writing the combined OpenAPI JSON, writing the discovery report, and presenting import options) as separate checklist items.

**For modifications:** If the user provided an existing JSON, load it mentally as the base. Apply only the changes asked for. Preserve all existing fields and schemas the user did not mention. Document what changed.

If the request involves removing or renaming any field or schema, include a warning — placed after the "What changed" section, just before the save offer, so the user sees it at the point they are about to act. Name each affected field explicitly:

> ⚠️ **Warning:** Removing or renaming `<fieldName>` takes effect immediately on re-import. Any services, processes, or coaches that reference this field will need to be updated.

Adding new fields is safe and does not affect existing consumers.

### 2. Write the files

**Pre-write check (MANDATORY):**
- Before writing any files or initializing your task list, you MUST run a `list_files` tool call on the `business-objects/` directory to check for collisions. **Never assume or state that the directory is empty without executing this tool call first.**
- Look carefully at the returned listing. If you see `<domain-slug>` in the list (e.g., `book-store`), you MUST immediately increment the slug suffix (e.g., `<domain-slug>_1`, `<domain-slug>_2`) and write all output files into that new suffixed directory.
- You are strictly forbidden from overwriting or merging files into a folder that already exists from a previous run.

#### 2a. Write `.bo.json` files

Write one `<BOName>.bo.json` file per Business Object to `generated_bos/`. See `references/TWX_BO_TOOLS_README.md` for the full format spec. Two kinds:

**Complex BO** (`"kind": "complex"`) — a record with named typed properties:

```json
{
  "kind": "complex",
  "description": "A customer record.",
  "properties": [
    { "name": "customerId", "type": "String" },
    { "name": "name",       "type": "String" },
    { "name": "email",      "type": "String" },
    { "name": "status",     "type": "CustomerStatus" }
  ]
}
```

**Selection BO** (`"kind": "selection"`) — an enumeration of value/display pairs:

```json
{
  "kind": "selection",
  "description": "Customer account status.",
  "options": [
    { "value": "ACTIVE",   "display": "ACTIVE"   },
    { "value": "INACTIVE", "display": "INACTIVE" }
  ]
}
```

**Enum → Selection BO rule:** when a field has a fixed set of values (expressed as an `enum` or described as a dropdown), auto-generate a Selection BO for it:
- Name: PascalCase the field name (e.g. `status` → `Status`, `policyType` → `PolicyType`).
- Display values equal the value strings exactly (no transformation).
- The parent BO property type becomes the Selection BO name.
- The Selection BO gets its own `.bo.json` file.

**BO authoring rules:**
- BO names must be PascalCase with no spaces — the name is the data type name.
- Property names must be camelCase with no spaces.
- Primitive type names (`String`, `Integer`, `Boolean`, `Decimal`, `Date`, `Time`) always resolve to System Data primitives — never to a local BO of the same name.
- For Selection BOs: `value` is the stored value that flows through process data; `display` is the UI label. Do not swap them.
- A single-field BO that just aliases a primitive is not worth creating — use the primitive directly.

**Property type reference:**

| Value | Resolves to |
|---|---|
| `"String"` | System Data String |
| `"Integer"` | System Data Integer |
| `"Boolean"` | System Data Boolean |
| `"Decimal"` | System Data Decimal |
| `"Date"` | System Data Date |
| `"Time"` | System Data Time |
| `"SomeName"` | Another local BO in the same run or existing TWX |

#### 2b. Write the combined OpenAPI import file

Write `output/<domain-slug>.json` — a valid OpenAPI 3.0 file importable via the WebPD "Import business objects" dialog. Follow the full rules in `references/BAW_BO_OPENAPI_RULES.md`. Key points:

- Root keys: `openapi` (emit `"3.0.3"`; any `"3.0.x"` value is accepted by BAW), `info`, `components`
- All schemas go under `components.schemas`
- Schema names → PascalCase (become the BO names in WebPD)
- Field names → camelCase
- No `paths`, `servers`, `security`, or other OpenAPI operation-level keys
- Primitive types: `string`, `integer`, `number`, `boolean`
- Arrays: `"type": "array"` with an `"items"` key
- Nested object references: `"$ref": "#/components/schemas/OtherObjectName"`
- Enum fields: use an inline `"enum": [...]` array on the Selection BO schema; the parent property uses `$ref` to the Selection BO

Include all complex BOs and all Selection BOs as schemas.

**Validate before writing:** every `$ref` points to a schema that exists in the file; all schema names are PascalCase; no extra top-level keys.

### 3. Write the discovery report

Write `reports/<domain-slug>.discovery-report.md`. The report documents the analysis behind the generated artifacts. Include these sections:

1. **Header metadata** — Generated by (Bob), Source Documents (all inputs the user provided), Context/domain. Do not include a date or timestamp — omit it entirely.
2. **Entities Discovered** — table: #, Business Object, Source, Role.
3. **Entity Relationship Map** — A Mermaid `erDiagram` visualizing the entity relationships (using standard Mermaid cardinality notation, e.g., `||--|{`, `||--||`) + Relationship Details table (Entity A, Relationship, Entity B, Cardinality). Ensure relationships are accurate and match the generated business object properties exactly.
4. **Enumerations Extracted** — table: Enumeration (Selection BO name), Values, Used By.
5. **Normalization Decisions** — table: Decision, Reasoning.
6. **Assumptions & Ambiguities** — numbered table: #, Ambiguity, Assumption Applied.
7. **Generated Artifacts Summary** — file tree of everything written.

Detail scales with complexity: a simple two-BO domain warrants a concise report; a complex domain with many BOs and relationships warrants full tables.

### 4. Ask how to import

After all files are written:

1. List every generated file path.
2. Direct the user to the generated discovery report (e.g. `reports/<domain-slug>.discovery-report.md`) so they can review the design choices, entities, and assumptions before importing.
3. Ask the user which import option they want. Remind them that after they proceed with one delivery option, they can still request to try other options (e.g., generating a toolkit TWX if they started with WebPD UI import) at any time in the conversation.

---

**Option 1 — Import via WebPD UI** *(BOs will be read-only in the designer)*

BOs imported this way are **read-only** in the BAW designer — you cannot edit their fields directly in the tool after import. To change them later, update the files with Bob and re-import.

Copy the import steps from `references/IMPORT_STEPS.md` and paste them directly.

**Option 2 — Create a new toolkit TWX** *(BOs will be fully editable)*

Suggest defaults for the toolkit metadata (derived from the domain) using clean, user-friendly names instead of command-line arguments:
- **Toolkit Name** (maps to `--name`): e.g. `"Invoice Management BOs"`
- **Toolkit Acronym** (maps to `--acronym`): e.g. `IMBO` (short uppercase slug)
- **Snapshot Version** (maps to `--snapshot`): `"1.0.0.0"`

Do NOT mention script flags/args (such as `--name`, `--acronym`, `--snapshot`) directly to the user. Simply ask them to confirm or customize these user-friendly fields, and apply them to the command flags behind the scenes. Produce a toolkit; do not use `--process-app`.

**Script paths:** The paths shown below are relative to this skill's own folder. Resolve them to their full path before executing — the scripts live at `scripts/twx-bo-tools/` inside the skill directory (e.g. `.bob/skills/generate-baw-business-objects/scripts/twx-bo-tools/`). All other paths (`--out`, `--source`, the generated_bos directory) are relative to the workspace root.

Steps:
1. ```bash
   python scripts/twx-bo-tools/create_empty_twx.py \
     --name "NAME" --acronym ACRONYM --snapshot VERSION \
     --out business-objects/<domain-slug>/output/twx/ACRONYM.twx
   ```
2. ```bash
   python scripts/twx-bo-tools/apply_bos.py \
     --source business-objects/<domain-slug>/output/twx/ACRONYM.twx \
     --version VERSION \
     --out business-objects/<domain-slug>/output/twx/ACRONYM-VERSION.twx \
     business-objects/<domain-slug>/generated_bos
   ```
3. **Delete the intermediate empty TWX file** (the one at `business-objects/<domain-slug>/output/twx/ACRONYM.twx`) immediately after creating the applied version. Only keep the final populated `ACRONYM-VERSION.twx` toolkit in the output directory.

See `references/TWX_BO_TOOLS_README.md` for full argument reference.

**Option 3 — Update an existing toolkit TWX** *(BOs will be fully editable)*

Ask for the path to the existing `.twx`. Then:

1. Run `python scripts/twx-bo-tools/list_bos.py <twx> --json` to read existing BOs.
2. Compare existing BO names against the generated BO names.
3. If conflicts exist, show a conflict table (BO name, existing definition vs. generated definition) and ask the user: overwrite each conflicting BO, or rename the generated BO (user provides the new name). Wait for resolution before proceeding.
4. Suggest a new snapshot version by incrementing the patch of the existing snapshot name (e.g. `1.0.0.0` → `1.0.0.1`). Ask the user to confirm or provide their own value.
5. Run:
   ```bash
   python scripts/twx-bo-tools/apply_bos.py \
     --source <existing.twx> \
     --version <version> \
     --out business-objects/<domain-slug>/output/twx/<name>-<version>.twx \
     business-objects/<domain-slug>/generated_bos
   ```

See `references/TWX_BO_TOOLS_README.md` for full argument reference.

### Future Updates & Script Abstraction Rules (IMPORTANT)

- **Do NOT expose internal implementation details, file structures, or scripts to the user.** The Python scripts (`create_empty_twx.py`, `apply_bos.py`, `list_bos.py`) and the `.bo.json` files are backend details of this skill, not developer tools for the end user.
- **Do NOT instruct the user to run any Python scripts, modify, or regenerate `.bo.json` files themselves.**
- **For future updates**, instruct the user: *"For future updates or modifications, simply provide Bob (this skill) with your updated requirements. Bob will automatically apply the changes and generate a new TWX toolkit snapshot or updated OpenAPI JSON file for you to import."*

---

## Boundaries

**In scope:**
- Generating a new BO set from any description, document, table, or natural language
- Modifying an existing BO import file (JSON) and producing an updated importable set
- Explaining the BAW BO data model, field type constraints, and import behavior
- Walking the user through WebPD manual import steps
- Generating toolkit TWX files via the bundled Python scripts

**Out of scope — redirect clearly:**
- **Auto-importing into BAW:** there is no public API for programmatic Business Object import in BAW WebPD. This skill generates the files; the import is a manual step the user performs in the WebPD UI. Tell the user this directly if they ask.
- **Making imported BOs editable after import:** imported BOs are read-only in BAW WebPD. The correct workflow is finalize → import → re-import if changes are needed.
- **Generating BPMN processes or service flows:** that is `generate-baw-bpmn`. If the user asks for both BOs and a process in the same request, generate the BO files first, then suggest `generate-baw-bpmn` for the process.
  - **Do NOT proactively ask or prompt the user** if they want to generate BPMN processes or service flows to go with the Business Objects. BPMN generation is strictly out of scope. Suggest `generate-baw-bpmn` ONLY if the user explicitly asks how to build process workflows for these BOs.

## Output format

Always produce (in this order):

1. Write `generated_bos/<BOName>.bo.json` for every BO (complex and selection).
2. Write `output/<domain-slug>.json` — the combined OpenAPI import file.
3. Write `reports/<domain-slug>.discovery-report.md` — the discovery report.
4. List all generated file paths.
5. Ask the user which import option they want (1, 2, or 3).
6. If option 1: paste import steps and offer to save.
7. If option 2: suggest toolkit metadata, confirm with user, run the two scripts.
8. If option 3: inspect existing TWX, resolve conflicts, confirm version, run `apply_bos.py`.

For modifications of existing files, also include:
- **What changed** — a brief changelog of additions, removals, and renames
- **Removal/rename warning** (if applicable) — the ⚠️ warning naming each affected field

## Example

**Input:** "I need Business Objects for an invoice management process: Invoice (number, date, due date, status — one of DRAFT, SENT, PAID, OVERDUE, CANCELLED — total amount, a reference to a Customer, and a list of line items), LineItem (product name, quantity, unit price), Customer (name, email, and billing address), Address (street, city, postal code, country)."

**Output walkthrough:**

Five schemas: `Invoice`, `LineItem`, `Customer`, `Address`, and `Status` (Selection BO extracted from the `status` enum field). The `status` field on `Invoice` becomes a `$ref` to `Status`.

Files written:
- `business-objects/invoice-management/generated_bos/Address.bo.json`
- `business-objects/invoice-management/generated_bos/Customer.bo.json`
- `business-objects/invoice-management/generated_bos/LineItem.bo.json`
- `business-objects/invoice-management/generated_bos/Invoice.bo.json`
- `business-objects/invoice-management/generated_bos/Status.bo.json`
- `business-objects/invoice-management/output/invoice-management.json`
- `business-objects/invoice-management/reports/invoice-management.discovery-report.md`

Then the import option prompt.

## Reference files

- **`references/BAW_BO_OPENAPI_RULES.md`** — full import format rules. Read whenever you need to check a specific rule (array syntax, `$ref` path format, what keys BAW ignores, enum-to-Selection-BO mapping, etc.).
- **`references/IMPORT_STEPS.md`** — the manual WebPD import sequence. Paste verbatim for Option 1.
- **`references/TWX_BO_TOOLS_README.md`** — full argument reference for all three twx-bo-tools scripts (`apply_bos.py`, `create_empty_twx.py`, `list_bos.py`).
- **`scripts/twx-bo-tools/apply_bos.py`** — adds or overwrites BOs in an existing TWX.
- **`scripts/twx-bo-tools/create_empty_twx.py`** — creates a new empty toolkit TWX from the bundled template.
- **`scripts/twx-bo-tools/list_bos.py`** — lists existing BOs in a TWX; used for conflict detection in Option 3.
