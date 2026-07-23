# Extracting a Process From Business Requirements Documents

Read this when the input isn't a chat description but a document — a requirements
spec, a blueprint, an SOP, meeting notes, a BRD. The goal is unchanged: produce the
process JSON from `PROCESS_JSON_SCHEMA.md`. What changes is that the document is the
source of truth — extract what it says, don't invent a plausible process it doesn't
describe, and surface every assumption you're forced to make.

## 1. Find the processes

Scan for process boundaries before extracting anything:

- Sections titled "Process", "Workflow", "Procedure", "Flow", numbered step lists.
- Sequential narration ("once X happens...", "after that...", "then...").
- Actor-based descriptions ("the underwriter reviews...", "the system checks...").
- Decision trees, if/else language, approval matrices, SLA/escalation tables.

A document often describes several processes. Each one becomes its **own config and
its own .bpmn** — never merge them into a mega-process. If the document mixes process
description with pure data-model content (entity/field definitions with no workflow),
the data-model-only parts are `parse-business-blueprint` territory; only pull in what
the process actually touches.

## 2. Map document language to config constructs

| You read... | You write... |
|---|---|
| Action verbs by a person/role ("submits", "reviews", "approves", "signs off") | `userTask`, named after the action |
| Automated/system actions ("the system validates", "automatically routed", "a job runs", "an email is sent") | `serviceTask` — name it what the service flow should be called |
| Calculation/transformation phrasing ("compute", "merge", "format") with no external system | `scriptTask` |
| Questions, conditions, either/or ("if complete...", "either approves or rejects", eligibility rules) | `exclusiveGateway` + named, conditioned branches + one `isDefault` |
| "meanwhile", "in parallel", "at the same time", independent checklists | paired `parallelGateway` fork/join |
| "one or more of", "any applicable" | `inclusiveGateway` |
| Deadlines, SLAs, reminders ("within 3 days", "if no response by...") | timer `boundaryEvent` on the waiting task |
| Failure/exception handling ("if the upload fails...") | error `boundaryEvent` |
| A named sub-procedure used as one step ("run the enrichment procedure per order") | `subProcess` |
| Distinct outcomes ("approved", "rejected", "cancelled") | separate named `endEvent`s |
| Trigger phrasing ("when a claim arrives", "starts when...") | the single none `startEvent`'s name |
| Nouns with described attributes that steps read/write ("the Claim", "the application form data") | `businessObjects` + `variables` wiring (`outputFrom` the step that creates it, `inputTo` steps that use it) |
| Author commentary/caveats worth keeping visible on the diagram | `textAnnotation` |

**Roles and departments** ("the HR lane", "handled by underwriting", "the cashier
receives...") become entries in the `roles` section — **not** BPMN pools or lanes. Instead:

1. Build a `roles` array from every distinct actor the document names (hiring manager,
   general manager, HR team, POS system, kitchen staff, etc.).
2. On each task element, add `"role": "<roleId>"` for the actor who performs it.
3. For system/automated tasks, use a role like `{"id": "system", "name": "System", "type": "system"}`.

The README generator will produce a role assignment table and use role names in the
"Performed by" column — giving the swimlane clarity of the other tool's output
without adding XML BAW will drop. Teams are then assigned in Process Designer post-import.

## 3. Extract the full data model

For every distinct "thing" the process works with, build a proper `businessObject`.
Do not default to `xsd:anyType` for anything a real form or database record would carry.

**Step 1 — collect nouns.** Walk each task and ask: what does it read, what does it
write? List every distinct data entity (the order, the customer, the position, the
payment, the applicant, the decision…).

**Step 2 — expand to full fields.** For each entity, think "what would a developer
put on the data entry form for this?" Don't just use fields the document explicitly
names — apply domain knowledge to complete the shape. See the entity-type field table
in `references/MODELING_COMPLETENESS.md` for common field sets.

**Step 3 — find nested/list relationships.** Does any entity contain a variable number
of child records? (Order → line items, Position → candidates, Application → attachments.)
Model each child as its own `businessObject`; the parent carries it as `"list": true`.

**Step 4 — wire all variables.** Set `outputFrom` to the task that first creates or
captures the object. Set `inputTo` to every task that reads or updates it — not just the
last consumer. Skipping intermediate wiring means BAW won't generate data mappings for
those tasks.

**`xsd:anyType` is a last resort**, not a default. Use it only when the document gives
zero field-level information and the domain doesn't suggest obvious fields. A real
process about hiring, food ordering, insurance claims, or expense reports will always
have enough domain knowledge to model at least a 5-field primary object.

## 4. Handle gaps and ambiguity

Documents are always incomplete somewhere. Rules of thumb:

- **Unstated performer** → decide from context whether it's human or automated; if
  genuinely unclear, prefer `userTask` (a human step downgraded to automation later
  is cheaper than the reverse) and record the assumption.
- **Unstated decision conditions** → keep the gateway with named branches, put your
  best-guess `condition` in `tw.local.*` form, mark one branch default, and flag it.
- **Implied but unwritten steps** (a review that must logically precede an approval)
  → add them only when the flow is otherwise disconnected, and flag them.
- **Incompletely described data** → expand from domain knowledge. Document every
  assumed field in the object's `description` (e.g., "assumed from domain: phone, email").
  A variable of `xsd:anyType` is only acceptable when the document and domain provide
  truly no field-level information.

Every assumption goes in two places: the element's `documentation` field, and the
**Assumptions** list of your final report. A reviewer must be able to check your
inferences without rereading the source document.

## 5. Then proceed as normal

From here it's the standard workflow: write the config, validate, generate, report.
In the report, add a **Source** line (document name/path and which section each
process came from) alongside the assumptions.
