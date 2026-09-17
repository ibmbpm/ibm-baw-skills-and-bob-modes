---
name: generate-baw-business-objects
description: Generates and modifies BAW Business Object import files -- valid OpenAPI 3.0 JSON that IBM BAW WebPD imports via the "Import business objects" option in the Data menu. Use when the user wants to generate Business Objects or BOs for a BAW process app, or when the user wants to modify an existing Business Object or BO .json file (whether pasted inline or referenced via @file). Always use this skill for BO modifications -- even simple field additions, removals, or renames -- because the output must comply with BAW's specific OpenAPI format rules, include import instructions, and surface safety warnings when fields are removed or renamed (removing or renaming a field breaks consumers immediately on re-import). Do not edit BO JSON files directly without this skill. This skill covers ONLY the Business Objects import artifact -- for BPMN process generation use generate-baw-bpmn instead.
---

# Generate BAW Business Objects

Produce an OpenAPI 3.0 JSON file that IBM BAW WebPD imports successfully as Business Objects, first time, every time.

The core contract is simple: everything the user's data model needs lives under `components.schemas`. Each schema becomes one Business Object in WebPD. Nested objects use `$ref` to point at a sibling schema in the same file. The result is a single JSON file the user drops into the WebPD import dialog — no server access required on Bob's side.

**One important note about imported BOs:** they appear as read-only in WebPD after import. The correct workflow is: finalize all BO specs with Bob before importing, then import once. If changes are needed later, update the JSON file with Bob's help and re-import — re-importing overrides the previous BOs.

## Steps

### 1. Understand the data model

Read the user's input carefully. Accept any of:
- Natural language description of the data structures
- A table or bulleted list of objects and fields
- A pasted document (Word export, PDF text, markdown, meeting notes)
- An existing OpenAPI 3.0 BO JSON the user wants to modify

Extract every distinct "thing" from the description. Each distinct thing — an order, a customer, an address, a line item — becomes its own schema under `components.schemas`.

Before writing the JSON, do a quick mental pass:

**Completeness check:**
- Did you find ALL the distinct objects? Walk the description once more and look for nouns that carry data (not just action verbs).
- Did you expand each object to its natural fields? If the user said "Customer," they probably want name, email, phone, and an address — not just an id.
- Are there any list relationships? If an order has multiple line items, model `OrderItem` separately and make the `Order.items` field an array of `$ref` to `OrderItem`.
- Are enum-like fields documented? If `status` has specific values, put them in the field's `description`.

**For modifications:** If the user provided an existing JSON, load it mentally as the base. Apply only the changes asked for. Preserve all existing fields and schemas the user did not mention. Document what changed.

If the request involves removing or renaming any field or schema, include a warning in the output — placed after the "What changed" section, just before the save offer, so the user sees it at the point they are about to act. Name each affected field explicitly:

> ⚠️ **Warning:** Removing or renaming `<fieldName>` takes effect immediately on re-import. Any services, processes, or coaches that reference this field will need to be updated.

Adding new fields is safe and does not affect existing consumers.

### 2. Write the JSON

Follow the format in `references/BAW_BO_OPENAPI_RULES.md` exactly. The key rules:

- Root keys: `openapi` (must be `"3.0.3"`), `info`, `components`
- All schemas go under `components.schemas`
- Schema names → PascalCase (these become the BO names in WebPD)
- Field names → camelCase
- No `paths`, `servers`, `security`, or other OpenAPI operation-level keys — BAW's importer only reads `components.schemas`
- Primitive types: `string`, `integer`, `number`, `boolean`
- Arrays: `"type": "array"` with `"items": { "$ref": "..." }` or `"items": { "type": "string" }` etc.
- Nested object references: `"$ref": "#/components/schemas/OtherObjectName"`
- Add `"description"` to each schema and to any field whose meaning isn't obvious from its name
- Add `"required": [...]` for fields that must be present
- For string fields with controlled values, document the values in `"description"` (BAW doesn't enforce enums from OpenAPI, but the documentation is preserved and visible in WebPD)

**Present the JSON in a code block.** Never produce a file path and tell the user to write it themselves — put the complete JSON inline so they can copy it.

### 3. Validate the JSON mentally before presenting it

Read `references/BAW_BO_OPENAPI_RULES.md` for the rules, then do a quick check:

- Every `$ref` in the file points to a schema that actually exists in `components.schemas`
- All `$ref` paths are exactly `#/components/schemas/<SchemaName>` and point to a schema that exists in the file
- No top-level keys other than `openapi`, `info`, `components`
- `openapi` value is exactly `"3.0.3"` (string, not a number)
- All schema names are PascalCase

If you spot a problem, fix it before presenting.

Optionally, if the user has Python available, you can also run `scripts/validate_bo_json.py` against the generated JSON to catch structural issues programmatically:
```bash
python <path-to-this-skill>/scripts/validate_bo_json.py <path-to-output.json>
```

### 4. Present the output

Give the user:

1. **The complete JSON** in a fenced code block (language: `json`)
2. **A summary table** of the schemas produced:

   | Schema (BO name) | Fields | Notes |
   |---|---|---|
   | `Customer` | customerId, firstName, lastName, email, phone, address | `address` → `Address` |
   | `Address` | street, city, postalCode, country | Required: city |

3. **The import steps** — copy them from `references/IMPORT_STEPS.md` and paste them directly into your reply (don't tell the user to go read a file).

4. **If modifying an existing file**, add a brief "What changed" section listing the additions, removals, and renames you made.

5. **Offer to save the file.** After the import steps, ask:

   > "Would you like me to save this as a `.json` file? I can save it to the current directory, or tell me a path and I'll save it there."

   When the user confirms (or gives a path), write the file using the exact JSON from step 1. Use a descriptive filename derived from the `info.title` value, kebab-cased — e.g. `invoice-management-business-objects.json`. If the user gives a specific path, use it; otherwise save to the current working directory. Confirm the full saved path in your reply so the user knows exactly where to find it for step 1 of the import instructions.

## Boundaries

**In scope:**
- Generating a new BO import file from any description, document, table, or natural language
- Modifying an existing BO import file (JSON) and producing an updated importable JSON
- Explaining the BAW BO data model, field type constraints, and import behavior
- Walking the user through the WebPD manual import steps

**Out of scope — redirect clearly:**
- **Auto-importing into BAW:** there is currently no public API for programmatic Business Object import in BAW WebPD. This skill generates the JSON; the import is a manual step the user performs in the WebPD UI. If a public API becomes available (e.g., via an MCP server), this skill should be updated — for now, guided manual import is the only path. Tell the user this directly if they ask.
- **Making imported BOs editable after import:** imported BOs are read-only in BAW WebPD. The correct workflow is finalize → import → re-import if changes are needed.
- **Generating BPMN processes or service flows:** that is `generate-baw-bpmn`. If the user asks for both BOs and a process in the same request, generate the BO import file first, then suggest they also use `generate-baw-bpmn` for the process.
- **Packaging TWX toolkits** or deploying to a BAW server.

## Output format

Always produce (in this order):

1. **Complete JSON** — the full importable file, in a `json` code block
2. **Schema summary table** — one row per schema, with field names and any `$ref` notes
3. **Import instructions** — the 6-step sequence from `references/IMPORT_STEPS.md`
4. **What changed** (modification requests only) — a brief changelog
5. **Removal/rename warning** (modification requests only, if applicable) — the ⚠️ warning naming each affected field
6. **Save offer** — a short follow-up question offering to save the file (see step 4 above)

## Example

**Input:** "I need Business Objects for an invoice management process: Invoice (number, date, due date, status, total amount, a reference to a Customer, and a list of line items), LineItem (product name, quantity, unit price), Customer (name, email, and billing address), Address (street, city, postal code, country)."

**Output walkthrough:**

Four schemas: `Invoice`, `LineItem`, `Customer`, `Address`. `Invoice.customer` is a `$ref` to `Customer`. `Invoice.lineItems` is an array with `items.$ref` to `LineItem`. `Customer.billingAddress` is a `$ref` to `Address`. `Invoice.status` has its typical values documented. Required fields set on the primary identifiers.

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "Invoice Management Business Objects",
    "description": "Business objects for the invoice management process.",
    "version": "1.0.0"
  },
  "components": {
    "schemas": {
      "Address": {
        "type": "object",
        "description": "A postal address.",
        "properties": {
          "street":     { "type": "string" },
          "city":       { "type": "string" },
          "postalCode": { "type": "string" },
          "country":    { "type": "string" }
        },
        "required": ["city"]
      },
      "Customer": {
        "type": "object",
        "description": "A customer.",
        "properties": {
          "customerId":      { "type": "string" },
          "name":            { "type": "string" },
          "email":           { "type": "string" },
          "billingAddress":  { "$ref": "#/components/schemas/Address" }
        },
        "required": ["customerId", "name"]
      },
      "LineItem": {
        "type": "object",
        "description": "A single line item on an invoice.",
        "properties": {
          "productName": { "type": "string" },
          "quantity":    { "type": "integer" },
          "unitPrice":   { "type": "number" }
        },
        "required": ["productName", "quantity", "unitPrice"]
      },
      "Invoice": {
        "type": "object",
        "description": "An invoice sent to a customer.",
        "properties": {
          "invoiceNumber": { "type": "string" },
          "invoiceDate":   { "type": "string", "format": "date" },
          "dueDate":       { "type": "string", "format": "date" },
          "status": {
            "type": "string",
            "description": "Invoice status. Values: DRAFT, SENT, PAID, OVERDUE, CANCELLED"
          },
          "totalAmount":   { "type": "number" },
          "customer":      { "$ref": "#/components/schemas/Customer" },
          "lineItems": {
            "type": "array",
            "items": { "$ref": "#/components/schemas/LineItem" }
          }
        },
        "required": ["invoiceNumber", "status"]
      }
    }
  }
}
```

Then the schema summary table, then the import steps from `references/IMPORT_STEPS.md`.

## Reference files

- **`references/BAW_BO_OPENAPI_RULES.md`** — the full import format rules, derived from the verified test import file. Read this whenever you need to check a specific rule (array syntax, `$ref` path format, what keys BAW ignores, etc.).
- **`references/IMPORT_STEPS.md`** — the exact 7-step manual import sequence to paste into every response. Always include these; do not paraphrase or shorten them.
- **`scripts/validate_bo_json.py`** — lightweight Python validator that checks structural rules programmatically. Run it if you want to double-check a generated file before presenting it to the user.
