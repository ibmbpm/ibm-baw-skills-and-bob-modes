# Audit domains reference

Defines the six audit domains, the evidence to look for in a TWX artifact's XML files, and the scoring criteria for each. Read this file during Step 5 of the assessment.

---

## TWX artifact structure (quick reference)

A TWX file is a ZIP archive. With `use_enhanced_filenames=true` the key files are:

| File pattern | What it contains |
|---|---|
| `processes/*.bpmn` or `processes/*.xml` | Process definitions — activities, gateways, sequence flows, lanes, boundary events |
| `businessObjects/*.xml` | Business object definitions — field names and types |
| `teams/*.xml` or team references in process XML | Lane-to-team bindings |
| `services/*.xml` | Service flow and coach flow definitions |
| `*.xml` (root or config) | Environment variables, EPVs, process variables |

When parsing: look for `<activity>`, `<gateway>`, `<lane>`, `<boundaryEvent>`, `<dataObject>`, `<property>` elements (BAW uses BPMN 2.0 XML with IBM extensions). Lane names appear in `<lane name="...">`. Boundary events have a `eventDefinitionRef` attribute indicating timer (`timerEventDefinition`) or error (`errorEventDefinition`).

---

## Scoring scale

| Score | Meaning |
|---|---|
| ✅ **Pass** | All criteria for this domain are satisfied by evidence in the TWX |
| ⚠️ **Partial** | Some criteria are satisfied; one or more gaps remain |
| ❌ **Fail** | No criteria for this domain are satisfied |

Do not assign Pass unless **all** listed criteria are met. Do not assign Fail unless **none** are met.

---

## Domain 1 — Traceability

> "Can you prove who approved what, and when?"

Auditors require that every significant decision in a process is captured with enough context to reconstruct what happened: who was involved, what decision was made, and when it occurred.

### Criteria

| # | Criterion | Evidence to look for in TWX |
|---|---|---|
| T1 | Every decision gateway has at least one human activity immediately upstream | In the process XML: a `<gateway>` element is preceded (by sequence flow) by an `<activity>` in a non-system lane — not a service task or another gateway |
| T2 | Business objects capture the decision-maker | In BO XML: a field named (or semantically equivalent to) `approvedBy`, `reviewedBy`, `decidedBy`, `assignee`, or similar |
| T3 | Business objects capture the decision outcome | In BO XML: a field for `decision`, `status`, `outcome`, `result`, or similar |
| T4 | Business objects capture a timestamp for key decisions | In BO XML: a field of type `Date`, `DateTime`, or `Time` (e.g. `approvalDate`, `reviewedOn`, `completedAt`) |

### Scoring guide

- **Pass:** T1–T4 all met across all significant decision points
- **Partial:** T1 met but T2, T3, or T4 missing; or T2–T4 met but a decision gateway has no upstream human task
- **Fail:** Multiple gateways have no upstream human task, or the business object has no decision-capture fields at all

### Common gaps

- An automated service task feeds directly into a gateway with no human review step
- `status` field present in the BO but no corresponding timestamp field
- Decision outcome captured only in a service output variable not stored in the main BO

---

## Domain 2 — Separation of Duties

> "Does the same person request AND approve their own request?"

No single actor should be able to initiate and also approve their own request without a second party's involvement.

### Criteria

| # | Criterion | Evidence to look for in TWX |
|---|---|---|
| S1 | The first human activity and the approval activity are in different lanes | In process XML: `<lane name="...">` values differ between the submitting activity and the approving activity |
| S2 | No single lane contains both a submission-type and an approval-type activity | Scan all `<lane>` elements — a lane containing both "Submit…" and "Approve…" named activities is a flag |
| S3 | At least two distinct non-system lanes exist | Count `<lane>` elements that are not marked as system lanes — must be ≥ 2 |

### Scoring guide

- **Pass:** S1–S3 all met
- **Partial:** Multiple lanes exist (S3 met) but one marginal case on S1 or S2 (e.g. an "Acknowledge" step in the same lane as "Submit")
- **Fail:** Only one lane, or submission and approval are in the same lane, or all activities are in a lane named "All Users" / "Everyone"

### Common gaps

- All human activities in a single lane named "Team", "All Participants", or "All Users"
- A self-service process with no approval step at all — if this is by design, score Pass and note it explicitly

---

## Domain 3 — Access Control

> "Is access locked down, or can anyone complete any task?"

Lanes must be bound to named, restricted teams. A lane open to all users is an access control gap regardless of separation of duties.

### Criteria

| # | Criterion | Evidence to look for in TWX |
|---|---|---|
| A1 | Every human lane has a specific, non-generic name | In process XML: lane `name` attributes are not "All Users", "Everyone", "Default", "Participants", or blank |
| A2 | System lanes are distinguishable from human lanes | Look for IBM BAW `systemLane="true"` attribute or equivalent on automated lanes |
| A3 | No human activity sits in a system lane | Cross-check activity lane assignments — a user task in a system lane is a misconfiguration |

### Scoring guide

- **Pass:** A1–A3 all met
- **Partial:** Most lanes are specifically named but one uses a generic name; or one activity is in an ambiguously named lane
- **Fail:** All human activities are in a generic lane or lane names are blank

### Notes

The TWX shows lane **names** as defined in Process Designer. Whether those lanes are bound to actual teams at runtime requires checking team binding XML files in the TWX (`teams/` directory or inline team references). If lane names are specific (e.g. "HR Manager", "Finance Approver") but no team binding files are found, score A1 as passing and note: *"Confirm runtime team bindings are configured in BAW Administration."*

---

## Domain 4 — SLA / Timeliness

> "Are there enforced deadlines, or can tasks sit forever?"

### Criteria

| # | Criterion | Evidence to look for in TWX |
|---|---|---|
| SL1 | At least one timer boundary event exists on a critical human activity | In process XML: a `<boundaryEvent>` attached to a human activity with `<timerEventDefinition>` |
| SL2 | Timer boundary events lead to an escalation path, not just a terminate end event | Follow the sequence flow from the boundary event — it should reach another activity (e.g. notify, escalate), not only a terminate end event |
| SL3 | A process-level due date variable exists | In variable/EPV XML: a variable named (or equivalent to) `dueDate`, `deadline`, `slaDeadline` |

### Scoring guide

- **Pass:** SL1–SL3 all met
- **Partial:** SL1 met but SL2 missing (timers terminate rather than escalate); or SL3 present but SL1 missing
- **Fail:** No timer boundary events anywhere and no due date variable

### Notes

- A process with no SLA requirement by design should still score at least Partial if it has a `dueDate` variable.
- Timer escalation to a notification service task counts for SL2.

---

## Domain 5 — Data Completeness

> "Does the process collect all the evidence an auditor would need?"

### Criteria

| # | Criterion | Evidence to look for in TWX |
|---|---|---|
| DC1 | The primary business object has ≥ 5 fields | In BO XML: count `<property>` or field elements in the main BO definition |
| DC2 | A requester/initiator identity field is present | Field named (or equivalent to) `requestedBy`, `submittedBy`, `initiator`, `employee`, `applicant` |
| DC3 | A justification or reason field is present | Field named (or equivalent to) `justification`, `reason`, `rationale`, `notes`, `comments` |
| DC4 | A decision/outcome field is present | Field named (or equivalent to) `decision`, `outcome`, `status`, `result`, `approvalStatus` |

### Scoring guide

- **Pass:** DC1–DC4 all met
- **Partial:** DC1 met but one of DC2, DC3, or DC4 missing
- **Fail:** Business object has fewer than 3 fields, or all of DC2–DC4 are missing

### Notes

- For apps with multiple business objects, assess the primary one — the BO referenced by the most process variables or activities.
- If the TWX contains no BO definition files, score DC1–DC4 as Fail and note that no structured business objects were found.

---

## Domain 6 — Error Handling

> "What happens when something goes wrong?"

External service calls can fail. Without error boundary events or recovery paths, a failure silently stalls the process.

### Criteria

| # | Criterion | Evidence to look for in TWX |
|---|---|---|
| E1 | Service tasks have at least one error or timer boundary event | In process XML: a `<boundaryEvent>` attached to a service activity with `<errorEventDefinition>` or `<timerEventDefinition>` |
| E2 | At least one error path leads to a human intervention activity | Follow the sequence flow from the error boundary event — it should reach a human lane activity (e.g. "Notify Administrator"), not only a terminate end event |
| E3 | No service task is a single point of failure with no recovery path | Every service activity that calls an external system should have at least one boundary event |

### Scoring guide

- **Pass:** E1–E3 all met for all service tasks
- **Partial:** Some service tasks have error handling but one or more do not; or error paths go to a terminate event rather than a human recovery activity
- **Fail:** No service task in the process has any boundary event

### Notes

- If there are no service tasks in the process (all activities are human tasks), score this domain as **N/A (Pass)** and note: *"No service tasks found — error handling domain not applicable."*
