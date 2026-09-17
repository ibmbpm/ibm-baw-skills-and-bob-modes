# Generate BAW Business Objects — Documentation

> Generates and modifies BAW Business Object import files — valid OpenAPI 3.0 JSON that IBM® BAW WebPD imports via the "Import business objects" option in the Data menu.

## Purpose

This skill produces the JSON import file you need to define Business Objects (BOs) in IBM® Business Automation Workflow (BAW) WebPD. Give it a description of your data model in any form — natural language, a table, a pasted document, or an existing BO JSON to modify — and it outputs a ready-to-import file along with step-by-step import instructions. It also handles safe and destructive modifications, surfacing an explicit warning whenever a field removal or rename would break existing consumers on re-import.

## Setup and configuration

- No special server access, MCP server, or API key is required.
- The generated JSON is delivered inline (copy-paste ready) or saved to disk on request — no BAW server connection is needed.
- Optional: Python 3.x is required only if you want to run the local validator script (`scripts/validate_bo_json.py`) to double-check a generated file before importing. No third-party packages are needed — the script uses only the Python standard library (`json`, `re`, `sys`, `pathlib`).

## Compatibility

- BAW WebPD only — manual import, no programmatic API. There is no public API for automated Business Object import in BAW WebPD. The import is a manual step performed in the WebPD UI (Data → Import business objects).
- The OpenAPI version must be `"3.0.3"` (string). Using `"3.0.0"`, `"3.1.0"`, or a numeric value produces a file the importer may reject. BAW's BO importer enforces this as a hard constraint.
- Imported BOs are read-only in WebPD. After import, you cannot edit Business Objects directly in WebPD. The correct workflow is: finalize specs with Bob → import once → re-import if changes are needed.
- Self-referential schemas are supported. A schema may contain a `$ref` to itself (e.g., `Employee.manager → Employee`); this imports without errors in BAW.

## Prompt examples

### Generate from a natural language description

**Prompt:**
> I need Business Objects for a loan application process. The main objects are: LoanApplication (applicationId, applicantName, requestedAmount, submittedDate, status), Applicant (applicantId, fullName, email, phone, dateOfBirth, and a homeAddress), and Address (street, city, postalCode, country). Generate the BAW import file.

**What to expect:** A complete, importable OpenAPI 3.0.3 JSON with `LoanApplication`, `Applicant`, and `Address` schemas, a schema summary table, step-by-step WebPD import instructions, and an offer to save the file.

---

### Generate from a markdown table

**Prompt:**
> Generate a BAW Business Objects import file from this data model:
>
> | Object | Fields |
> |---|---|
> | Product | productId (string, required), name (string), category (string), unitPrice (number), stockCount (integer), isActive (boolean) |
> | PurchaseOrder | orderId (string, required), orderDate (date), status (string — DRAFT, SUBMITTED, APPROVED, REJECTED), lines (list of OrderLine), buyer (reference to Buyer) |
> | OrderLine | lineId (string), product (reference to Product), quantity (integer), lineTotal (number) |
> | Buyer | buyerId (string, required), companyName (string), contactEmail (string) |

**What to expect:** A valid JSON with four schemas using the correct `$ref` and array syntax, all field names in camelCase and schema names in PascalCase, ready for WebPD import.

---

### Generate from pasted meeting notes or an unstructured document

**Prompt:**
> Here are notes from our process design session. Extract the data objects and generate the BO import file.
>
> "We need to track employee onboarding requests. Each request has an employee name, their start date, their department, and the hiring manager. There's also a checklist of tasks — each task has a name, an owner, a due date, and a completion flag. We'll also need an equipment list per request: item name, quantity, and whether it's been provisioned."

**What to expect:** Bob extracts the implied objects (e.g., `OnboardingRequest`, `OnboardingTask`, `EquipmentItem`), expands each to its natural fields, and produces the full import JSON with import instructions.

---

### Safe modification — adding fields and a new schema

**Prompt:**
> Here is my current BO import file:
>
> ```json
> {
>   "openapi": "3.0.3",
>   "info": { "title": "Expense Report Business Objects", "version": "1.0.0" },
>   "components": {
>     "schemas": {
>       "ExpenseReport": {
>         "type": "object",
>         "description": "An employee expense report.",
>         "properties": {
>           "reportId": { "type": "string" },
>           "submittedBy": { "type": "string" },
>           "totalAmount": { "type": "number" },
>           "status": { "type": "string" }
>         },
>         "required": ["reportId"]
>       }
>     }
>   }
> }
> ```
>
> Please add a `submittedDate` (date) field and a `notes` (string) field to `ExpenseReport`, and add a new `ExpenseLine` schema with fields: description (string), amount (number), receiptDate (date), and category (string).

**What to expect:** The updated JSON preserves all existing fields, adds the new ones, includes a "What changed" section, and shows no removal/rename warning because only additions were made.

---

### Destructive modification — removing a field and renaming another

**Prompt:**
> Here is my current BO import file:
>
> ```json
> {
>   "openapi": "3.0.3",
>   "info": { "title": "Support Ticket Business Objects", "version": "1.0.0" },
>   "components": {
>     "schemas": {
>       "SupportTicket": {
>         "type": "object",
>         "description": "A customer support ticket.",
>         "properties": {
>           "ticketId":      { "type": "string" },
>           "legacyCode":    { "type": "string" },
>           "customerName":  { "type": "string" },
>           "issueCategory": { "type": "string" },
>           "priority":      { "type": "string" },
>           "createdAt":     { "type": "string", "format": "date-time" }
>         },
>         "required": ["ticketId"]
>       }
>     }
>   }
> }
> ```
>
> Remove the `legacyCode` field and rename `customerName` to `reporterName`.

**What to expect:** The updated JSON with the changes applied, a "What changed" section, and an explicit ⚠️ warning naming `legacyCode` (removed) and `customerName` (renamed) — reminding you that these changes take effect immediately on re-import and any services or coaches referencing those fields must be updated.

---

### Save the generated file to disk

**Prompt:**
> Save the last generated file as `support-ticket-business-objects.json` in `C:\projects\my-baw-app\`.

**What to expect:** Bob writes the file to the specified path and confirms the full saved path so you know exactly where to find it for step 1 of the import instructions.

---

### Out-of-scope redirect — request for auto-import

**Prompt:**
> Can you import these Business Objects directly into my BAW server?

**What to expect:** Bob explains that there is no public API for programmatic BO import in BAW WebPD and walks you through the manual import steps instead.

---

### Out-of-scope redirect — request for BPMN process generation

**Prompt:**
> Generate the BPMN process for this loan application workflow along with the Business Objects.

**What to expect:** Bob generates the BO import file first, then directs you to use the `generate-baw-bpmn` skill for the BPMN process definition.