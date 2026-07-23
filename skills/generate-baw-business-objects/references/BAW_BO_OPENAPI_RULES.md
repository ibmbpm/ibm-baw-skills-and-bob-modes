# BAW Business Object Import — OpenAPI 3.0 Format Rules

These rules are derived from a verified BAW WebPD import test.

---

## Root structure

The file must be valid JSON with exactly these top-level keys:

```json
{
  "openapi": "3.0.3",
  "info": { ... },
  "components": {
    "schemas": { ... }
  }
}
```

- `openapi` — must be the string `"3.0.3"`. Do NOT use `"3.0.0"` or `"3.1.0"`.
- `info.title` — required. Use a descriptive name (e.g. `"Order Management Business Objects"`).
- `info.version` — required. Use `"1.0.0"` unless the user specifies otherwise.
- `info.description` — optional but recommended.

**Do NOT include:** `paths`, `servers`, `security`, `tags`, or any other OpenAPI operation-level keys. BAW's BO importer reads only `components.schemas`. These keys will not cause an import failure, but they add noise and may confuse tooling.

---

## Schema definitions

Each Business Object is one entry under `components.schemas`:

```json
"components": {
  "schemas": {
    "MyObject": {
      "type": "object",
      "description": "What this BO represents.",
      "properties": { ... },
      "required": [...]
    }
  }
}
```

### Schema name (= BO name in WebPD)

- **Always PascalCase**: `Order`, `LineItem`, `CustomerAddress`, not `order`, `lineItem`, `customer_address`.
- Schema names become the exact BO type names shown in WebPD. Use names that match the domain vocabulary precisely.

### `type`

Every schema must have `"type": "object"`.

### `description`

Add a description on every schema. Keep it to one sentence. This description is visible in WebPD when a developer inspects the BO type.

---

## Properties (fields)

```json
"properties": {
  "fieldName": { "type": "string" },
  "amount":    { "type": "number" },
  "count":     { "type": "integer" },
  "isActive":  { "type": "boolean" },
  "items":     { "type": "array", "items": { "$ref": "#/components/schemas/LineItem" } },
  "address":   { "$ref": "#/components/schemas/Address" }
}
```

### Naming

- **Always camelCase**: `invoiceDate`, `totalAmount`, `customerId`, not `invoice_date`, `TotalAmount`.

### Supported primitive types

| OpenAPI type | BAW BO type | Notes |
|---|---|---|
| `string` | String (or Date/Time with `format`) | Default for text and codes; use `format` to get Date or Time type (see below) |
| `string` + `"format": "date"` | Date | Date only — no time component shown in coach views |
| `string` + `"format": "date-time"` | Time | Date and time — use for timestamp fields |
| `integer` | Integer | Whole numbers, range -2147483648 to 2147483647 |
| `number` | Decimal | Floating point / currency (IEEE 754 double precision) |
| `boolean` | Boolean | true/false |

### String format hints — date and time fields

OpenAPI `format` values on `string` fields control the BAW BO field type created on import:

| OpenAPI `format` | BAW BO field type | Coach view behaviour |
|---|---|---|
| `"date"` | `Date` | Shows **date only** (no time component rendered) |
| `"date-time"` | `Time` | Shows **date and time** |
| *(omitted)* | `String` | Plain text — no date picker |

**Choosing between `Date` and `Time`:**
- Use `"format": "date"` → `Date` for date-only fields where the time component is irrelevant (e.g. `dateOfBirth`, `dueDate`, `startDate`, `endDate`).
- Use `"format": "date-time"` → `Time` for fields that need both a date and a time (e.g. `reportedDate`, `createdAt`, `scheduledTime`, `resolvedDate`).
- When in doubt: if the field represents a moment in time (something that happened or is scheduled at a specific hour), use `date-time`. If it represents just a calendar day, use `date`.

```json
"dateOfBirth":   { "type": "string", "format": "date" },
"dueDate":       { "type": "string", "format": "date" },
"reportedDate":  { "type": "string", "format": "date-time" },
"createdAt":     { "type": "string", "format": "date-time" }
```

### Arrays

```json
"items": {
  "type": "array",
  "items": { "$ref": "#/components/schemas/LineItem" }
}
```

- The outer object has `"type": "array"` and an `"items"` key.
- `items` can be a `$ref` (list of objects) or a primitive type (`{ "type": "string" }`, etc.).

### Nested object references (`$ref`)

```json
"billingAddress": { "$ref": "#/components/schemas/Address" }
```

- The `$ref` path must be exactly `#/components/schemas/<SchemaName>`.
- The referenced schema must exist in the same file — BAW does not resolve external references.
- Do NOT use `$ref` and other properties on the same field object. A `$ref` replaces all other keywords on that property.

### Field descriptions

Add `"description"` to a field when its meaning is not obvious from its name, or when it has a controlled set of values:

```json
"status": {
  "type": "string",
  "description": "Order status. Values: PENDING, PROCESSING, SHIPPED, DELIVERED, CANCELLED"
}
```

BAW preserves field descriptions and surfaces them in the WebPD BO designer.

---

## Required fields

```json
"required": ["orderId", "status"]
```

- List field names (strings) that must be present in any instance of this BO.
- Use sparingly — only truly mandatory fields. Over-constraining makes the BO harder to use in partial-data scenarios.

---

## Self-referential schemas

BAW **does** support self-referential BOs — a schema that contains a `$ref` to itself imports without errors. For example, an `Employee` with a `manager` field of type `$ref: Employee` is valid.

At runtime, a recursive structure must bottom out somewhere (the top-level manager's `manager` field will simply be null/unset). This is normal BAW behaviour, not a defect.

A flat alternative (storing `managerId` as a string rather than a nested object) is sometimes simpler to work with in process data mappings, but it is a design choice — not a requirement. Use whichever fits the process better.

---

## Ordering

BAW does not require schemas to be declared before they are referenced. You can order schemas alphabetically or dependency-first — either works. Dependency-first (leaf objects first, composites last) is easier to read.

---

## Do not include

The following keys are outside the scope of the BO import and should be omitted from the file:

- `paths` (API operations)
- `servers`
- `security` / `securitySchemes`
- `tags`
- `externalDocs`
- OpenAPI `format` keywords (preserved as metadata but not enforced)
- OpenAPI `enum` keywords (preserved as metadata but not enforced — document allowed values in `description` instead)

---

## Complete minimal example

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "Order Management Business Objects",
    "description": "BOs for the order management process.",
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
        "description": "A customer record.",
        "properties": {
          "customerId": { "type": "string" },
          "firstName":  { "type": "string" },
          "lastName":   { "type": "string" },
          "email":      { "type": "string" },
          "phone":      { "type": "string" },
          "address":    { "$ref": "#/components/schemas/Address" }
        },
        "required": ["customerId", "firstName", "lastName"]
      },
      "Order": {
        "type": "object",
        "description": "A customer order.",
        "properties": {
          "orderId":     { "type": "string" },
          "status":      {
            "type": "string",
            "description": "Order status. Values: PENDING, PROCESSING, SHIPPED, DELIVERED, CANCELLED"
          },
          "totalAmount": { "type": "number" },
          "orderDate":   { "type": "string", "format": "date-time" },
          "customer":    { "$ref": "#/components/schemas/Customer" }
        },
        "required": ["orderId", "status"]
      }
    }
  }
}
```

This structure has been verified to import into BAW WebPD without errors.
