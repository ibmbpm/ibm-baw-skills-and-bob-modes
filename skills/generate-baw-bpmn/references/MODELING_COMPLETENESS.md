# Modeling Completeness — process structure and data model

Read this before writing the config (or before treating a draft plan/data model as
final). A short linear happy-path with one flat business object is almost always
under-modeling. This reference is the checklist for both halves of that problem:
process structure (roles, decisions, exceptions, SLAs, parallelism, end states) and
data (the business objects and their fields).

## Process completeness — think before you write the config

Mentally walk through the process from every angle before writing the config:

**Roles and actors.** Who does each step — a specific person, a team, or the system?
Different actors suggest distinct work areas. Capture this in a `roles` section (see
`references/PROCESS_JSON_SCHEMA.md`) and reference each role from its tasks; the
generator uses role names in the README's "Performed by" column and role table so
teams can be assigned in Process Designer after import.

**Decision points.** Every question in the process needs an `exclusiveGateway`. For
every gateway, ask: what are ALL the realistic outcomes? Common ones to not omit:
- Approved / Rejected / Needs more information (3 outcomes, not 2)
- Retry / Escalate / Cancel on failures or timeouts
- New record vs existing record (branching at the start of many workflows)
- Priority/tier routing (high-priority customers get a different path)

**Exception and rework loops.** Real processes loop back:
- A "quality check fails → fix → re-check" cycle needs a back-edge to the earlier task.
- A "payment fails → retry or cancel" needs both paths.
- An "applicant fails screening → notify and close" needs its own end event, not a shared one.
Don't model these as single happy-path lines — model the loop explicitly.

**SLA and escalation.** Whenever a human task has a time expectation ("within 2 days",
"must respond before deadline"), add a non-interrupting timer `boundaryEvent` on that
task. The boundary event should lead to an escalation task and its own end event.

**Multiple end states.** A well-modeled process has a named end event for each
meaningfully different outcome: Approved, Rejected, Cancelled, Escalated, Error.
A single "End" is almost always a sign the process is underspecified.

**Parallel work.** When two things happen independently at the same time (e.g., IT
provisioning and desk assignment during onboarding), use a `parallelGateway` fork/join.
Do not serialize steps that the real world does concurrently.

A good rule of thumb: if your process has fewer than 8 elements or only 1-2 end events
for anything beyond a trivial workflow, stop and ask whether you've modeled all the
decision branches, exception paths, and rework loops the real process contains.

## Data completeness — model ALL the business objects

A single flat variable of `xsd:anyType` or a single shallow object with 2–3 fields is
almost always under-modeling. Before writing the `businessObjects` section, think
through the full data model the process actually needs. Use this checklist:

**1. Identify every noun that travels through the process.**
Each task either reads or writes data. Walk every step and ask: what information does
this task need to do its work, and what does it produce? Collect all the distinct
"things" — the order, the applicant, the position, the payment, the approval decision.
Each distinct "thing" is a candidate business object.

**2. Expand every object to its natural fields.**
For each object you found, ask: what fields does a real-world instance of this thing
carry? Go beyond the one or two fields you see in the process description — think about
what a database record or form for this entity would contain. Common field sets by
entity type:

| Entity type | Typical fields you should include |
|---|---|
| Order / Request | id, status, submittedDate, totalAmount, priority, notes |
| Person / Applicant / Customer | id, name, email, phone, address (nested BO) |
| Product / Item | id, name, sku, quantity, unitPrice, category |
| Address | street, city, state, postalCode, country |
| Decision / Review | outcome (Approved/Rejected/…), reviewerId, reviewDate, comments |
| Payment | amount, currency, method, transactionId, status, processedDate |
| Notification | channel (email/SMS/push), recipient, sentDate, templateId |
| Schedule / Appointment | scheduledDate, duration, location, attendees |
| Document / Attachment | documentId, name, url, uploadedDate, fileType |

**3. Find the nested / child objects.**
If one object contains a collection of another kind of thing (an order has line items;
a position has candidates; an application has attachments), model that as a separate
`businessObject` with `"list": true` on the parent's field. Flat objects that carry
"item1Name, item2Name, item3Name" style fields are a smell — make it a list.

**4. Model status and decision fields explicitly.**
Every process-controlled object needs at least one status field (String) whose
possible values are documented in the object's `description`. Decision objects should
carry the outcome, the actor who made it, and the timestamp — not just a boolean.

**5. Wire variables correctly.**
Every business object must be reachable from at least one variable. That variable must
have `outputFrom` set to the task that creates/captures it (usually the first userTask
or the start of data entry) and `inputTo` set to every task that reads or updates it.
An orphan business object that no variable references will trigger a generator warning
and import as a disconnected type that is hard to use in Process Designer.

**Minimum bar for a real process:**
- At least one complex `businessObject` with 5+ fields for the primary entity
- Nested object or list field when the domain naturally has one (e.g., order → line items)
- A status/decision object separate from the main entity when approval or routing is involved
- All variables wired across all tasks that touch them (not just the first and last)

A process about food ordering with only one `ShakeOrder` object and 4 fields, or a
hiring process with only one `Position` object with 2 fields, is under-modeled. Define
the complete shape of the data a real system would carry, not just the fields the
source material happens to mention.
