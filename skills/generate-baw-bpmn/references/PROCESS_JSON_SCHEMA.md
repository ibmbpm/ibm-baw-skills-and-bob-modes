# Process JSON Schema — generate-baw-bpmn

This is the authoritative schema for the process JSON that `scripts/generate_baw_bpmn.py`
consumes. You (the model) write this JSON; the script deterministically turns it into
BAW-importable BPMN 2.0 XML. Your judgment lives entirely in this file — element choice,
naming, branching, data — and the XML generation stays mechanical.

Config IDs are yours to choose (short, readable, kebab-case works well). The generator
derives every XML id from them with uuid5, so the same config always produces the same
XML and every `sourceRef`/`targetRef` is guaranteed to resolve. Never invent XML ids
yourself.

## Top-level structure

```json
{
  "process":         { ... },      // required
  "roles":           [ ... ],      // optional: named actors; used in README, not in BPMN XML
  "elements":        [ ... ],      // required
  "flows":           [ ... ],      // required
  "variables":       [ ... ],      // optional: process data
  "businessObjects": [ ... ]       // optional: complex/nested data types
}
```

## `roles` (optional)

Names the actors involved in the process — people, teams, and systems. The generator
uses these to:
- Populate the README's "Performed by" column and role assignment table.
- **Emit a `<laneSet>` with one `<lane>` per role** so BAW creates swim-lanes on import.
- **Emit a `<performer>` on every task** that references a role — BAW's primary signal
  for lane assignment and team binding.

Assign a `"role"` to every task. Elements with no role land in an "Unassigned" lane.

```json
{
  "id": "hiring-manager",          // short kebab-case identifier; referenced by elements
  "name": "Hiring Manager",        // display name used in the README
  "type": "human"                  // optional: "human" | "system" | "team" (default: "human")
}
```

Reference a role from any task element with `"role": "<roleId>"`. If no role is
given on an element, the README infers "System" for serviceTasks/scriptTasks and
"User/team (assign in Process Designer)" for userTasks.

**Example:**

```json
"roles": [
  {"id": "hiring-manager", "name": "Hiring Manager"},
  {"id": "gm",             "name": "General Manager"},
  {"id": "hr",             "name": "HR Team"},
  {"id": "system",         "name": "System", "type": "system"}
]
```

Then on tasks:
```json
{"id": "task-submit", "type": "userTask",    "name": "Submit Position Request", "role": "hiring-manager"},
{"id": "task-review", "type": "userTask",    "name": "Review New Position",     "role": "gm"},
{"id": "sf-notify",   "type": "serviceTask", "name": "Notify Hiring Manager",   "role": "system"}
```

## `process`

```json
{
  "name": "Claim Review",                  // required; becomes the process name in BAW
  "processApp": "Claims Intake",           // optional; used in targetNamespace (BAW style: http://App/Snapshot/Name)
  "snapshot": "1.0",                       // optional
  "description": "One or two sentences."   // optional; becomes bpmn:documentation
}
```

Avoid `< > & " \ / : * ? |` in the name — BAW rejects them in artifact names.

## `elements`

Each element: `{"id", "type", "name", ...}`. Allowed types (each maps 1:1 to a row in
IBM's import mapping — see `BAW_BPMN_DIALECT.md`):

| type | Imports into BAW as | Notes |
|---|---|---|
| `startEvent` | Start event | Exactly one plain startEvent per process (and per subProcess). Optional `eventDefinition`: `message`, `timer`, `error` for additional typed starts. |
| `endEvent` | End event | At least one required. Optional `eventDefinition`: `message`, `error`, `terminate`. |
| `userTask` | Activity (user task) + a generated client-side human service | Human work. |
| `serviceTask` | Activity (system task) + **a generated service flow named after the task** | This is how you get service flows from a BPMN import — name the serviceTask exactly what the service flow should be called. |
| `scriptTask` | Activity with a JavaScript implementation | Optional `script` field for starter JS. |
| `businessRuleTask` | Decision task + a generated service flow | |
| `manualTask` / `task` | Activity | Prefer the specific types above. |
| `exclusiveGateway` | Exclusive gateway | Decision (XOR). |
| `inclusiveGateway` | Inclusive (IOR) gateway | One-or-more paths. |
| `parallelGateway` | Parallel gateway | All paths (AND). |
| `subProcess` | Activity with subprocess type | Carries its own nested `elements` and `flows` arrays (same schema, one plain startEvent, at least one endEvent). |
| `intermediateCatchEvent` | Intermediate event | Requires `eventDefinition`: `message` or `timer`. |
| `intermediateThrowEvent` | Intermediate message event (sending) | Requires `eventDefinition`: `message`. |
| `boundaryEvent` | Event attached to an activity | Requires `eventDefinition` (`message`, `timer`, `error`) and `attachedToRef` (id of a task/subProcess). Optional `interrupting`: false. Its outgoing flow is the exception path. |
| `textAnnotation` | Note | Free-standing note on the diagram. Takes a `text` field instead of `name`, and no flows. |

Optional on any element: `"documentation": "..."` (imported as the element's documentation).

Anything not in this table (pools, call activities, event subprocesses, data
stores, signal/escalation events...) should not be included.

## `flows`

```json
{
  "id": "f5",
  "sourceRef": "gw-decision",              // element id
  "targetRef": "sf-notify-approved",       // element id
  "name": "Approved",                      // optional; defaults to "To <target name>" (BAW's own style)
  "condition": "tw.local.claim.decision == \"APPROVED\"",  // only meaningful on gateway outputs
  "isDefault": true                        // marks the gateway's default path (at most one per gateway)
}
```

Give every exclusive/inclusive gateway's outgoing flows a short `name` (it labels the
branch in the diagram) and either a `condition` or `isDefault: true`. Conditions are
carried into the XML but BAW expects you to finish the conditional logic in Process
Designer after import — write them in `tw.local.*` JavaScript style so they're a
useful starting point, not decoration.

## `variables` (optional)

Declares business data that flows between tasks. Each becomes a `bpmn:itemDefinition`
(imported as a business object / private variable) plus `ioSpecification` entries on
the tasks that use it.

```json
{
  "name": "claim",
  "type": "xsd:anyType",                   // keep xsd:anyType unless a simple XSD type clearly fits
  "description": "The claim under review",
  "outputFrom": ["task-submit"],           // element ids that produce it
  "inputTo": ["sf-validate", "task-review"] // element ids that consume it
}
```

Use variables when the process has obvious business data moving between steps; skip
them for quick structural drafts. They are additive — a config without `variables`
imports fine.

A variable's `type` is either a simple XSD type (`xsd:anyType`, `xsd:string`,
`xsd:integer`, `xsd:decimal`, `xsd:boolean`, `xsd:date`, `xsd:time`, `xsd:dateTime`)
or the name of a business object defined in `businessObjects` below.

## `businessObjects` (optional)

Complex, nested data types — the "business objects" the process works with. The
generator emits them as complexTypes in a sidecar `.xsd` file, adds a `bpmn:import`
for it, and points the matching itemDefinitions at the types. On import BAW
materializes each one as a business object (IBM mapping: item definition → business
object). The `.xsd` travels inside the same .zip as the `.bpmn` — never separate them.

```json
{
  "name": "Position",                       // simple identifier (becomes the XSD type / BAW BO name)
  "description": "The position requested",  // optional
  "fields": [
    {"name": "positionId", "type": "String", "required": true},
    {"name": "isNewPosition", "type": "Boolean"},
    {"name": "location", "type": "Address"},              // nests another business object
    {"name": "candidates", "type": "Candidate", "list": true}  // one-to-many
  ]
}
```

Field types: `String`, `Integer`, `Decimal`, `Boolean`, `Date`, `Time`, `DateTime`
(BAW's business-object primitive set), or the name of another business object defined
in the same config. `required: true` → `minOccurs="1"`; `list: true` →
`maxOccurs="unbounded"`. The generator orders the XSD so referenced types come first.
There is no enum construct — document a closed value set in the field-owning object's
`description`.

To actually attach a business object to the process, reference it from a variable:
`{"name": "position", "type": "Position", "outputFrom": [...], "inputTo": [...]}`.
A business object no variable (or other object) uses draws a warning — it would
import as an orphan type.

### How to decide what business objects to model

**Start by walking every task and asking: what data does this step read, and what
does it write?** That produces a list of candidate "nouns." Each distinct noun that has
more than one meaningful field becomes a `businessObject`. Here is the systematic
decision tree:

```
Is this piece of data a single scalar value (one string, one boolean)?
  → Use a simple xsd:* variable, no businessObject needed.

Does this piece of data have 2+ named fields OR does it nest inside another object?
  → Define a businessObject with all its natural fields.

Does any step produce a *list* of these things (line items, candidates, attachments)?
  → Make the parent field "list": true; the child type gets its own businessObject entry.

Is there a status or routing outcome that drives a gateway decision?
  → Add a dedicated status/decision object OR add a status field to the primary object.
  → Document the allowed values in the object's "description" field.
```

For the completeness bar a real process needs to clear (primary entity, nested party,
nested line items, decision/review object) and the field-set table by entity type, see
`references/MODELING_COMPLETENESS.md` -- read it before finalizing this section.

## Structural rules the generator enforces

The generator validates before writing anything, and refuses to generate on error:

- Exactly one plain (none) `startEvent` per process and per subProcess; at least one `endEvent`.
- All ids unique; every `sourceRef`/`targetRef`/`attachedToRef`/variable task reference resolves.
- Start events have no incoming flows; end events no outgoing; every task/gateway/subProcess has at least one of each.
- Every element reachable from the start (boundary events count as reachable via their attached task).
- At most one `isDefault` flow per gateway; element types outside the supported table rejected.

Warnings (non-blocking) flag unnamed elements, do-nothing gateways (1-in/1-out),
conditions on non-gateway flows, and unconditioned non-default gateway branches.

## Worked examples

### 1. Minimal linear process (mirrors a real BAW export)

```json
{
  "process": {"name": "Process1", "processApp": "Simple PA", "snapshot": "Version2"},
  "elements": [
    {"id": "start", "type": "startEvent", "name": "Start"},
    {"id": "task-user", "type": "userTask", "name": "Inline user task"},
    {"id": "sf-1", "type": "serviceTask", "name": "Service flow1"},
    {"id": "end", "type": "endEvent", "name": "End"}
  ],
  "flows": [
    {"id": "f1", "sourceRef": "start", "targetRef": "task-user"},
    {"id": "f2", "sourceRef": "task-user", "targetRef": "sf-1"},
    {"id": "f3", "sourceRef": "sf-1", "targetRef": "end"}
  ]
}
```

On import BAW creates the process, a human service for "Inline user task", and a
service flow named "Service flow1".

### 2. Approval with roles, decision, default path, and escalation timer

This example shows the full `roles` section. Role names appear in the README's
"Performed by" column and role table — zero effect on the BPMN XML.

```json
{
  "process": {
    "name": "Claim Review",
    "processApp": "Claims Intake",
    "description": "Agent submits a claim, the system validates it, an underwriter decides."
  },
  "roles": [
    {"id": "agent",       "name": "Claims Agent"},
    {"id": "underwriter", "name": "Underwriter"},
    {"id": "system",      "name": "System", "type": "system"},
    {"id": "supervisor",  "name": "Supervisor"}
  ],
  "elements": [
    {"id": "start", "type": "startEvent", "name": "Claim Received"},
    {"id": "task-submit",  "type": "userTask",    "name": "Submit Claim",           "role": "agent"},
    {"id": "sf-validate",  "type": "serviceTask", "name": "Validate Claim Data",    "role": "system"},
    {"id": "task-review",  "type": "userTask",    "name": "Review Claim",           "role": "underwriter"},
    {"id": "gw-decision",  "type": "exclusiveGateway", "name": "Approved?"},
    {"id": "sf-notify-approved", "type": "serviceTask", "name": "Notify Customer Approved", "role": "system"},
    {"id": "sf-notify-denied",   "type": "serviceTask", "name": "Notify Customer Denied",   "role": "system"},
    {"id": "timer-escalate", "type": "boundaryEvent", "eventDefinition": "timer",
     "name": "Review Overdue", "attachedToRef": "task-review", "interrupting": false},
    {"id": "task-escalate", "type": "userTask", "name": "Escalate Review", "role": "supervisor"},
    {"id": "end-approved",  "type": "endEvent", "name": "Approved"},
    {"id": "end-denied",    "type": "endEvent", "name": "Denied"},
    {"id": "end-escalated", "type": "endEvent", "name": "Escalated"}
  ],
  "flows": [
    {"id": "f1", "sourceRef": "start",         "targetRef": "task-submit"},
    {"id": "f2", "sourceRef": "task-submit",   "targetRef": "sf-validate"},
    {"id": "f3", "sourceRef": "sf-validate",   "targetRef": "task-review"},
    {"id": "f4", "sourceRef": "task-review",   "targetRef": "gw-decision"},
    {"id": "f5", "sourceRef": "gw-decision",   "targetRef": "sf-notify-approved",
     "name": "Approved", "condition": "tw.local.claim.decision == \"APPROVED\""},
    {"id": "f6", "sourceRef": "gw-decision",   "targetRef": "sf-notify-denied",
     "name": "Denied", "isDefault": true},
    {"id": "f7", "sourceRef": "sf-notify-approved", "targetRef": "end-approved"},
    {"id": "f8", "sourceRef": "sf-notify-denied",   "targetRef": "end-denied"},
    {"id": "f9", "sourceRef": "timer-escalate", "targetRef": "task-escalate"},
    {"id": "f10", "sourceRef": "task-escalate", "targetRef": "end-escalated"}
  ],
  "variables": [
    {"name": "claim", "type": "xsd:anyType", "description": "The claim under review",
     "outputFrom": ["task-submit"], "inputTo": ["sf-validate", "task-review"]},
    {"name": "validationResult", "type": "xsd:anyType",
     "outputFrom": ["sf-validate"], "inputTo": ["task-review"]}
  ]
}
```

### 3. Parallel fork/join

```json
{
  "process": {"name": "Employee Onboarding", "processApp": "HR"},
  "elements": [
    {"id": "start", "type": "startEvent", "name": "Offer Accepted"},
    {"id": "gw-fork", "type": "parallelGateway", "name": "Start Setup"},
    {"id": "sf-it", "type": "serviceTask", "name": "Provision IT Accounts"},
    {"id": "task-desk", "type": "userTask", "name": "Assign Desk"},
    {"id": "gw-join", "type": "parallelGateway", "name": "Setup Complete"},
    {"id": "task-orient", "type": "userTask", "name": "Run Orientation"},
    {"id": "end", "type": "endEvent", "name": "Onboarded"}
  ],
  "flows": [
    {"id": "f1", "sourceRef": "start", "targetRef": "gw-fork"},
    {"id": "f2", "sourceRef": "gw-fork", "targetRef": "sf-it"},
    {"id": "f3", "sourceRef": "gw-fork", "targetRef": "task-desk"},
    {"id": "f4", "sourceRef": "sf-it", "targetRef": "gw-join"},
    {"id": "f5", "sourceRef": "task-desk", "targetRef": "gw-join"},
    {"id": "f6", "sourceRef": "gw-join", "targetRef": "task-orient"},
    {"id": "f7", "sourceRef": "task-orient", "targetRef": "end"}
  ]
}
```

Parallel gateways take no conditions — every branch runs. Always pair a fork with a
join so downstream steps wait for all branches.

### 4. Service-flow-heavy automation with a subprocess

```json
{
  "process": {"name": "Nightly Order Sync", "processApp": "Order Hub"},
  "elements": [
    {"id": "start", "type": "startEvent", "name": "Start"},
    {"id": "sf-fetch", "type": "serviceTask", "name": "Fetch Orders From ERP"},
    {"id": "sub-enrich", "type": "subProcess", "name": "Enrich Each Order",
     "elements": [
       {"id": "sub-start", "type": "startEvent", "name": "Start"},
       {"id": "sf-lookup", "type": "serviceTask", "name": "Lookup Customer Record"},
       {"id": "script-merge", "type": "scriptTask", "name": "Merge Order Data",
        "script": "// TODO: merge tw.local.order with tw.local.customer"},
       {"id": "sub-end", "type": "endEvent", "name": "End"}
     ],
     "flows": [
       {"id": "sf1", "sourceRef": "sub-start", "targetRef": "sf-lookup"},
       {"id": "sf2", "sourceRef": "sf-lookup", "targetRef": "script-merge"},
       {"id": "sf3", "sourceRef": "script-merge", "targetRef": "sub-end"}
     ]},
    {"id": "err-sync", "type": "boundaryEvent", "eventDefinition": "error",
     "name": "Sync Failed", "attachedToRef": "sub-enrich"},
    {"id": "task-fix", "type": "userTask", "name": "Resolve Sync Errors"},
    {"id": "sf-publish", "type": "serviceTask", "name": "Publish To Warehouse"},
    {"id": "end", "type": "endEvent", "name": "Synced"},
    {"id": "end-failed", "type": "endEvent", "name": "Needs Attention"}
  ],
  "flows": [
    {"id": "f1", "sourceRef": "start", "targetRef": "sf-fetch"},
    {"id": "f2", "sourceRef": "sf-fetch", "targetRef": "sub-enrich"},
    {"id": "f3", "sourceRef": "sub-enrich", "targetRef": "sf-publish"},
    {"id": "f4", "sourceRef": "sf-publish", "targetRef": "end"},
    {"id": "f5", "sourceRef": "err-sync", "targetRef": "task-fix"},
    {"id": "f6", "sourceRef": "task-fix", "targetRef": "end-failed"}
  ]
}
```

### 5. Full data model — food-service ordering with multiple nested objects

This is the canonical example of **complete business object modeling** for a realistic
process. Notice: primary entity + nested customer + nested line items + separate
decision object + all variables wired end-to-end. This is what "complete" looks like.

```json
{
  "process": {
    "name": "Shake Ordering",
    "processApp": "Food Service",
    "description": "End-to-end shake order: customer places order, system checks inventory, prepares and dispatches, or notifies of unavailability with escalation for delayed preparation."
  },
  "roles": [
    {"id": "customer",   "name": "Customer"},
    {"id": "system",     "name": "System",     "type": "system"},
    {"id": "supervisor", "name": "Supervisor"}
  ],
  "elements": [
    {"id": "start",             "type": "startEvent",       "name": "Order Received"},
    {"id": "task-place",        "type": "userTask",         "name": "Place Shake Order",
     "role": "customer",
     "documentation": "Customer selects flavor, size, quantity, any special instructions, and provides contact info."},
    {"id": "sf-inventory",      "type": "serviceTask",      "name": "Check Inventory Availability",
     "role": "system",
     "documentation": "Queries ingredient inventory; sets order.inventoryStatus to AVAILABLE or OUT_OF_STOCK."},
    {"id": "gw-available",      "type": "exclusiveGateway", "name": "Items Available?",
     "documentation": "Routes on order.inventoryStatus."},
    {"id": "sf-prepare",        "type": "serviceTask",      "name": "Prepare Shake",
     "role": "system",
     "documentation": "Triggers kitchen prep workflow; sets order.status to IN_PREPARATION."},
    {"id": "timer-overdue",     "type": "boundaryEvent",    "name": "Preparation Overdue",
     "eventDefinition": "timer", "attachedToRef": "sf-prepare", "interrupting": false,
     "documentation": "Non-interrupting timer. Fires if preparation exceeds 5-minute SLA."},
    {"id": "task-escalate",     "type": "userTask",         "name": "Escalate Delayed Order",
     "role": "supervisor",
     "documentation": "Supervisor investigates delay and updates expected completion time."},
    {"id": "sf-notify-ready",   "type": "serviceTask",      "name": "Notify Customer Order Ready",
     "role": "system",
     "documentation": "Sends SMS/push notification; sets order.status to READY."},
    {"id": "sf-notify-unavail", "type": "serviceTask",      "name": "Notify Customer Item Unavailable",
     "role": "system",
     "documentation": "Contacts customer about unavailability; offers alternatives or refund; sets order.status to CANCELLED."},
    {"id": "end-fulfilled",  "type": "endEvent", "name": "Order Fulfilled"},
    {"id": "end-cancelled",  "type": "endEvent", "name": "Order Cancelled"},
    {"id": "end-escalated",  "type": "endEvent", "name": "Escalation Logged"}
  ],
  "flows": [
    {"id": "f1",  "sourceRef": "start",             "targetRef": "task-place"},
    {"id": "f2",  "sourceRef": "task-place",        "targetRef": "sf-inventory"},
    {"id": "f3",  "sourceRef": "sf-inventory",      "targetRef": "gw-available"},
    {"id": "f4",  "sourceRef": "gw-available",      "targetRef": "sf-prepare",
     "name": "Available", "condition": "tw.local.order.inventoryStatus == \"AVAILABLE\""},
    {"id": "f5",  "sourceRef": "gw-available",      "targetRef": "sf-notify-unavail",
     "name": "Out of Stock", "isDefault": true},
    {"id": "f6",  "sourceRef": "sf-prepare",        "targetRef": "sf-notify-ready"},
    {"id": "f7",  "sourceRef": "sf-notify-ready",   "targetRef": "end-fulfilled"},
    {"id": "f8",  "sourceRef": "sf-notify-unavail", "targetRef": "end-cancelled"},
    {"id": "f9",  "sourceRef": "timer-overdue",     "targetRef": "task-escalate"},
    {"id": "f10", "sourceRef": "task-escalate",     "targetRef": "end-escalated"}
  ],
  "variables": [
    {
      "name": "order",
      "type": "ShakeOrder",
      "description": "The primary order entity, created at placement and read by all downstream steps.",
      "outputFrom": ["task-place"],
      "inputTo": ["sf-inventory", "sf-prepare", "task-escalate", "sf-notify-ready", "sf-notify-unavail"]
    },
    {
      "name": "customer",
      "type": "Customer",
      "description": "The customer who placed the order — captured during placement, used for notifications.",
      "outputFrom": ["task-place"],
      "inputTo": ["sf-notify-ready", "sf-notify-unavail"]
    }
  ],
  "businessObjects": [
    {
      "name": "Address",
      "description": "Postal address used for delivery or customer records.",
      "fields": [
        {"name": "street",     "type": "String"},
        {"name": "city",       "type": "String", "required": true},
        {"name": "state",      "type": "String"},
        {"name": "postalCode", "type": "String"},
        {"name": "country",    "type": "String"}
      ]
    },
    {
      "name": "Customer",
      "description": "The person who placed the order.",
      "fields": [
        {"name": "customerId",   "type": "String", "required": true},
        {"name": "name",         "type": "String", "required": true},
        {"name": "email",        "type": "String"},
        {"name": "phone",        "type": "String"},
        {"name": "deliveryAddress", "type": "Address"}
      ]
    },
    {
      "name": "OrderItem",
      "description": "A single shake line within an order. flavor values: Chocolate, Vanilla, Strawberry, Mango. size values: Small, Medium, Large.",
      "fields": [
        {"name": "itemId",            "type": "String", "required": true},
        {"name": "flavor",            "type": "String", "required": true},
        {"name": "size",              "type": "String", "required": true},
        {"name": "quantity",          "type": "Integer", "required": true},
        {"name": "unitPrice",         "type": "Decimal"},
        {"name": "specialInstructions","type": "String"}
      ]
    },
    {
      "name": "ShakeOrder",
      "description": "Primary order entity. status values: PENDING, INVENTORY_CHECKED, IN_PREPARATION, READY, CANCELLED, ESCALATED. inventoryStatus values: AVAILABLE, OUT_OF_STOCK.",
      "fields": [
        {"name": "orderId",          "type": "String",   "required": true},
        {"name": "orderTimestamp",   "type": "DateTime", "required": true},
        {"name": "status",           "type": "String",   "required": true},
        {"name": "inventoryStatus",  "type": "String"},
        {"name": "totalAmount",      "type": "Decimal"},
        {"name": "priority",         "type": "String"},
        {"name": "notes",            "type": "String"},
        {"name": "items",            "type": "OrderItem", "list": true},
        {"name": "customer",         "type": "Customer"}
      ]
    }
  ]
}
```

**What makes this model complete:**
- `ShakeOrder` is the primary entity with 9 fields — id, timestamps, status lifecycle,
  financial value, and links to its children.
- `OrderItem` is a nested list — the order has *multiple* items, modeled as a list not
  flat fields.
- `Customer` is a nested party object with contact fields; `Address` nests inside it.
- `status` and `inventoryStatus` fields have their allowed values documented in the
  object's `description` — because there is no enum in XSD's BAW subset.
- Both variables (`order` and `customer`) are wired to every task that reads or writes them.
