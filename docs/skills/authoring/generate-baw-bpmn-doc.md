# Generate BAW BPMN — Documentation

> Generates BPMN 2.0 XML that imports cleanly into IBM Business Automation Workflow (BAW) — processes and complex business object variables (via a bundled XSD) — by writing a process JSON and running a bundled deterministic generator that emits BAW's own export dialect and packages the `.zip` the import wizards expect.

## Purpose

This skill turns any process description into a validated, import-ready BAW artifact: a `.bpmn`, an optional `.xsd` for business objects, a `.zip` that the BAW import wizards accept on first attempt, and a generated `README.md` with a Mermaid diagram and process documentation. It is intended for BAW developers and process authors who need importable BPMN without hand-writing XML. Use it whenever you want to model a workflow in BAW from a chat description, a requirements document, an SOP, meeting notes, or an existing process design — including when a previous import attempt lost elements or swimlanes.

## Setup and configuration

- **Python 3 (any version)** — required to run `scripts/generate_baw_bpmn.py`. Uses the standard library only; no `pip install` needed.
- No MCP server, API key, or environment variable is required.
- The generator script is bundled inside the skill folder at `scripts/generate_baw_bpmn.py` and is invoked automatically during generation.

## Compatibility

- **BAW import wizards only** — the deliverable is a `.zip` for Workflow Center → **Import Process App** or Process Designer → **File > Import**. The skill does not deploy to a running BAW server.
- **Single none start event per process** — BAW honors only one start event per process on import; multiple starts will be silently dropped.
- **No BPMN DI / layout section** — BAW ignores incoming diagram layout and auto-arranges on import. Diagram layout is an expected post-import step in Process Designer.
- **Supported constructs only** — elements outside IBM's documented import mapping (callActivity, signal/escalation/compensation events, data stores, pools) are rejected at validation time rather than being silently dropped by BAW at import time.
- **Business objects require BAW 22.x or later** — the `.xsd` sidecar mechanism requires a BAW version that supports itemDefinition-based business object import.

## Prompt examples

### Model a process from a conversational description

**Prompt:**
> I need a BAW process for handling customer refund requests. A customer submits a refund request online, the system validates it against our refund policy, then a service agent reviews it and either approves or denies it. Approved refunds get processed automatically by the system and the customer gets a confirmation email. Denied requests also get an email notification. Domain is CustomerService.

**What to expect:** The skill walks you through a guided conversation (plan → data model → confirmation), then generates a `.bpmn`, `.xsd`, and `.zip` in `business-processes/bpmn/CustomerService/refund-request-handling/`, plus a process config JSON and a `README.md` with a Mermaid diagram.

---

### Model a process with business object data

**Prompt:**
> Generate a BAW process for a job position request. A hiring manager submits a new position, the general manager approves or rejects it, and HR then finds and screens candidates. I want real business objects: a Position object with id, title, department, headcount, and status, and a Candidate object with name, email, phone, and screeningOutcome. Wire them to the tasks that use them.

**What to expect:** The skill proposes a data model (in YAML), lets you refine it, then generates `.bpmn` + `.xsd` + `.zip` with BAW-compatible itemDefinitions and a sidecar XSD defining the Position and Candidate complex types.

---

### Extract a process from a requirements document or BRD

**Prompt:**
> Here is section 4.1 of our loan origination BRD — please generate the importable BAW BPMN from it:
>
> "4.1 Loan Application Process. When an applicant submits a loan application online, the system performs an automated credit check. If the credit score is below 600, a loan officer conducts a manual underwriting review and either approves with conditions, approves outright, or declines. Applications above 600 are auto-approved. Approved applications in either path proceed to document collection by the loan coordinator. Once documents are received, the system activates the loan and sends a disbursement notice to the applicant. If documents are not received within 10 business days, the application is automatically cancelled."

**What to expect:** The skill extracts a single process from the BRD text — mapping each actor, decision, SLA timer, and end state to config constructs — and generates the `.bpmn`/`.zip` plus a `process-extraction-report.md` that records every inference and assumption for stakeholder review.

---

### Fix a broken BPMN import (swimlanes disappearing, elements dropped)

**Prompt:**
> My BPMN import into BAW keeps losing the swimlanes and one gateway always disappears on import. The process is a new employee onboarding: HR enters employee details, IT provisions accounts and orders equipment in parallel, then a welcome meeting is scheduled. Can you regenerate this properly so it imports cleanly?

**What to expect:** The skill explains what BAW's import mapping does (and doesn't) support — lanes are replaced by role annotations and Process Designer team assignments, and only supported gateway/event types survive — then generates a clean `.bpmn`/`.zip` that imports without surprises.

---

### Automation-heavy process with service flows and error handling

**Prompt:**
> I need a BAW process for a nightly data sync. The system fetches open orders from our ERP, enriches each order with product catalog data, then publishes them to our warehouse platform. If the publish step fails, someone from the ops team needs to investigate and either retry or cancel the batch. Everything is automated except that last step.

**What to expect:** The skill creates a serviceTask-heavy config (fetch, enrich, publish as named service flows) with an error boundary event on the publish task routing to a user task for ops, generates `.bpmn`/`.zip`, and reports the service flow names BAW will create on import.

---

### Modify or extend an existing process config

**Prompt:**
> I already have a process config at `business-processes/configs/Finance/ExpenseApproval.bpmn.json`. I need to add a second approval level: after the manager approves, amounts over $10,000 must also be approved by the finance director before the payout is triggered. Please update the config and regenerate.

**What to expect:** The skill reads the existing config, adds the second exclusive gateway and finance director user task, updates the flows, revalidates, and regenerates the `.bpmn`/`.zip` — deterministic IDs mean the output is diff-friendly and safe to re-import.

---

### Out-of-scope redirect — coach or widget development

**Prompt:**
> Can you build the BAW coach UI for my expense approval process? I want a form with fields for expense type, amount, and receipt attachment.

**What to expect:** The skill redirects this request to the `create-baw-widget` skill, which handles BAW coach view development.

---

### Out-of-scope redirect — deploying to a BAW server

**Prompt:**
> Once the BPMN is generated, can you deploy it directly to our BAW server at https://baw.mycompany.com?

**What to expect:** The skill clarifies that deployment to a running server is out of scope; it delivers the `.zip` file and the import route (Workflow Center or Process Designer), and redirects server-side deployment to the `version-lifecycle-manager` skill.

---

### Out-of-scope redirect — standalone business object catalog

**Prompt:**
> I have a business blueprint document with 15 entity definitions. Can you generate all the business object JSON artifacts and register them as a catalog?

**What to expect:** The skill redirects this to the `generate-baw-business-objects` skill, which handles standalone BO artifact generation; this skill only generates business objects as part of a BPMN process config.
