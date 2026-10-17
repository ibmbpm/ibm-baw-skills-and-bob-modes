# Generate BAW Business Objects — Documentation

> Generates and modifies BAW Business Object import files — individual `.bo.json` files, a combined OpenAPI 3.0 JSON, a discovery report, and an optional toolkit TWX.

## Purpose

This skill produces importable IBM Business Automation Workflow (BAW) Business Objects from any data-model description. It targets BAW developers and architects who need to define structured data types for process apps or toolkits. Use it when you want to create a new BO set from scratch, update an existing import file, convert enum fields to Selection BOs, or package BOs into a reusable toolkit TWX. The skill also provides the manual WebPD import sequence and can generate toolkit TWX files using bundled Python scripts.

## Setup and configuration

- You need Python 3.9+ to generate toolkit TWX files (Options 2 and 3). The scripts require no third-party packages — they all use the Python standard library only.
- You do not need to download the `empty-project.twx` template separately — it is bundled in the skill folder alongside the scripts, and `create_empty_twx.py` uses it automatically to scaffold a new toolkit.
- You do not need an MCP server, API key, or environment variable for the default WebPD import path (Option 1).
- You do not need Python if you only want the OpenAPI JSON for manual WebPD import.

## Compatibility

- **BAW WebPD only for manual import** — there is no public API for programmatic Business Object import. The skill generates the files; you perform the import step manually in the WebPD UI.
- **OpenAPI `3.0.x` required** — the combined import file must use `"openapi": "3.0.3"` (or another `3.0.x` value). OpenAPI `3.1.0` or `4.x` will not import correctly.
- **WebPD treats imported BOs as read-only** — the correct update workflow is: finalize with Bob → import → re-import when changes are needed. There is no way to edit BOs in place after import.
- **TWX template stamped as BAW 24 (`8.6.8`)** — the generated toolkit TWX is importable into BAW 24, 25, 26, and beyond. A TWX stamped for a newer version cannot be imported into an older server.
- **Simple restricted types not creatable** — `apply_bos.py` cannot create BAW "simple restricted" BO types (for example, length-constrained strings). `apply_bos.py` supports only Complex and Selection BOs.
- **Cross-toolkit BO references not supported** — BO properties must reference either a primitive type or another local BO within the same project. `.bo.json` files cannot express references to BOs in dependency toolkits.

## Prompt examples

### Generate BOs from a natural-language description

**Prompt:**
> I'm building a claims management process. I need Business Objects for Claim (claimId, policyNumber, claimType — one of MEDICAL, DENTAL, VISION, LIFE — submittedAt as a timestamp, totalAmount as a decimal, and a reference to a Claimant), and Claimant (claimantId, firstName, lastName, email, phoneNumber, and a mailingAddress). Address should have street, city, state, postalCode, country. Generate the BAW import files.

**What to expect:** Bob generates `.bo.json` files for each object (including a `ClaimType` Selection BO), a combined OpenAPI 3.0 JSON ready for WebPD import, a discovery report with an ER diagram, then asks which delivery option you want.

---

### Generate BOs from a markdown table or bulleted list

**Prompt:**
> Create BAW Business Objects from this data model:
>
> **Order**: orderId (String, required), orderDate (date only), status (PENDING, PROCESSING, SHIPPED, DELIVERED, CANCELLED), totalAmount (Decimal), customer (→ Customer), items (list of → OrderItem)
> **OrderItem**: itemId, productName, quantity (Integer), unitPrice (Decimal)
> **Customer**: customerId, firstName, lastName, email, phone, address (→ Address)
> **Address**: street, city, postalCode, country

**What to expect:** Bob identifies five schemas (Order, OrderItem, Customer, Address, Status), generates all files with correct `format: date` on `orderDate` and `$ref` on the status field, then prompts for import options.

---

### Add new fields to an existing BO import file (safe modification)

**Prompt:**
> Here is my current BO import file:
>
> ```json
> {
>   "openapi": "3.0.3",
>   "info": { "title": "HR Business Objects", "version": "1.0.0" },
>   "components": {
>     "schemas": {
>       "Employee": {
>         "type": "object",
>         "description": "An employee record.",
>         "properties": {
>           "employeeId": { "type": "string" },
>           "firstName":  { "type": "string" },
>           "lastName":   { "type": "string" },
>           "email":      { "type": "string" }
>         },
>         "required": ["employeeId"]
>       }
>     }
>   }
> }
> ```
>
> Please add a `department` field (String) and a new `EmployeeRole` schema with fields: roleId, roleTitle, and gradeLevel (Integer).

**What to expect:** Bob adds `department` to `Employee`, creates the new `EmployeeRole` schema, preserves all existing fields unchanged, includes a "What changed" summary, and offers import options — with no removal warning because only additions were made.

---

### Remove or rename a field (destructive modification — triggers a warning)

**Prompt:**
> Here is my current BO import file:
>
> ```json
> {
>   "openapi": "3.0.3",
>   "info": { "title": "Contract Business Objects", "version": "1.0.0" },
>   "components": {
>     "schemas": {
>       "Contract": {
>         "type": "object",
>         "description": "A legal contract.",
>         "properties": {
>           "contractId":   { "type": "string" },
>           "legacyRef":    { "type": "string" },
>           "contractName": { "type": "string" },
>           "startDate":    { "type": "string", "format": "date" },
>           "endDate":      { "type": "string", "format": "date" }
>         },
>         "required": ["contractId"]
>       }
>     }
>   }
> }
> ```
>
> Remove the `legacyRef` field and rename `contractName` to `title`.

**What to expect:** Bob produces the updated JSON, includes a "What changed" section listing both the removal and the rename, then shows a ⚠️ warning — placed just before the save/import offer — naming `legacyRef` and `contractName` explicitly and noting that consumers will need updating.

---

### Generate BOs and package them in a new toolkit TWX

**Prompt:**
> I need Business Objects for a simple library system: Book (bookId, title, author, isbn, publishedDate as a date, genre — FICTION, NON_FICTION, MYSTERY, BIOGRAPHY, SCIENCE), and Borrower (borrowerId, fullName, email, memberSince as a date). Generate the files and create a new toolkit TWX called "Library BOs" with acronym LIBO.

**What to expect:** Bob generates all files, confirms toolkit metadata (Name, Acronym, Snapshot version) before proceeding, creates the toolkit TWX, and delivers the final `.twx` file path — without exposing any script flags or asking you to run Python commands yourself.

---

### Update an existing toolkit TWX with new BOs

**Prompt:**
> I have an existing toolkit at `output/twx/HRBO-1.0.0.0.twx`. I want to add a new PerformanceReview BO with: reviewId, employeeId, reviewDate as a timestamp, overallRating (Integer), and reviewerNotes (String). Please update the toolkit with a new snapshot version.

**What to expect:** Bob inspects the existing TWX for conflicts, proposes a new snapshot version (e.g. `1.0.0.1`), confirms with you, then applies the new BO and delivers an updated `HRBO-1.0.0.1.twx` file.

---

### Handle an enum with multiple fixed-value fields

**Prompt:**
> Create BAW Business Objects for a policy management process: Policy (policyId, policyType — TERM_LIFE, WHOLE_LIFE, UNIVERSAL_LIFE — coverageAmount as a decimal, startDate as a date, endDate as a date, status — ACTIVE, LAPSED, CANCELLED, EXPIRED — and a reference to a Policyholder), Policyholder (holderId, firstName, lastName, dateOfBirth as a date, email).

**What to expect:** Bob creates two Selection BOs (`PolicyType` and `Status`) in addition to the two complex BOs, wires `$ref` correctly for both enum fields in the OpenAPI JSON, and produces a discovery report with an enumeration table.

---

### Request for auto-import (out-of-scope redirect)

**Prompt:**
> Can you automatically import the generated Business Objects directly into my BAW server?

**What to expect:** Bob explains that no public API exists for programmatic BO import in BAW WebPD, provides the manual 6-step import sequence, and offers to help with the toolkit TWX path as an alternative.

---

### Request for BPMN process generation (redirects to the correct skill)

**Prompt:**
> Now that the BOs are ready, can you also generate the BPMN process flows and service integrations for the invoice management process?

**What to expect:** Bob notes that the `generate-baw-bpmn` skill handles BPMN and service flow generation and redirects you there, without generating any process artifacts itself.
