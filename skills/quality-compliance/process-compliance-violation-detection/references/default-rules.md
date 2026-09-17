# Default Compliance Rule Set

> **These rules are illustrative examples.** They represent widely accepted governance, operational, and security best practices for IBM BAW / CP4BA process applications, but they are not an authoritative or pre-approved standard. When no compliance document is provided, present them to the user as suggestions only — do not apply them silently. The user must explicitly include, exclude, or modify each rule before the active rule set is finalized.

Rule IDs use the `[DEF-NNN]` series.
Severity: Critical | High | Medium | Low

---

## Category: Approval (APR)

| Rule ID | Description | Severity | Required Evidence |
|---|---|---|---|
| DEF-001 | Every process that creates, updates, or deletes a significant business record must include at least one human approval step. | High | Human Task with approval outcome variable in BPD flow. |
| DEF-002 | Approval decisions must be stored in a retrievable process variable or tracking field. | High | Process variable mapped to task output containing decision value. |
| DEF-003 | Rejected items must follow a defined rejection path — not silently terminate. | High | Gateway after approval Human Task with explicit rejection sequence flow. |

---

## Category: Separation of Duties (SOD)

| Rule ID | Description | Severity | Required Evidence |
|---|---|---|---|
| DEF-010 | The user who initiates a process must not be the sole approver of that same process instance. | Critical | Separate lane or team assignment for initiator lane vs approver lane. |
| DEF-011 | Roles must be defined at the team or lane level — no process may assign tasks directly to a named individual user (hard-coded user assignment). | Medium | Team-based or lane-based task routing, no literal user name in assignment logic. |

---

## Category: Audit Trail (AUD)

| Rule ID | Description | Severity | Required Evidence |
|---|---|---|---|
| DEF-020 | All task completions and status transitions must be traceable via BAW's built-in process history or a tracking group. | High | BPDW tracking group configured, or process history enabled. |
| DEF-021 | Process variables carrying decision data (approval/rejection, amount, risk score) must be tracked. | High | Tracked variables in the BPD tracking group definition. |
| DEF-022 | Process start and end times must be captured. | Medium | Verify that process instance start and end timestamps are available via process history or a tracking group. |

---

## Category: Error Handling (ERR)

| Rule ID | Description | Severity | Required Evidence |
|---|---|---|---|
| DEF-030 | Every service call (REST, database, EIS) must have an error handling path — either a Boundary Error Intermediate Event or a try/catch block in the service flow. | Critical | Error boundary event attached to service task, or explicit error path in service flow. |
| DEF-031 | Integration failures must not silently abort the process — the process must enter a recoverable or notifiable error state. | Critical | Error path leads to human task, notification, or compensating flow. |
| DEF-032 | Unhandled script exceptions in JavaScript coach views or service flows must be caught. | Medium | try/catch in JavaScript code blocks. |

---

## Category: SLA / Timer (SLA)

| Rule ID | Description | Severity | Required Evidence |
|---|---|---|---|
| DEF-040 | Human tasks that require a response within a defined SLA must have a Boundary Intermediate Timer Event configured. | High | Non-interrupting boundary timer event on Human Task step. |
| DEF-041 | Timer interval must be at least 1 minute as a best practice to avoid excessive server polling. | High | Timer configuration value ≥ 1 minute. |
| DEF-042 | Repeatable escalation timers must have a defined maximum escalation count or terminal condition. | Medium | Timer set to Repeatable with documented max iterations or downstream termination. |

---

## Category: Escalation (ESC)

| Rule ID | Description | Severity | Required Evidence |
|---|---|---|---|
| DEF-050 | Overdue tasks must trigger an escalation notification to the task owner's manager or an escalation team. | High | Timer event with escalation path containing notification activity. |
| DEF-051 | Escalated tasks must have a defined fallback assignee or team. | Medium | Escalation path re-routes task or updates team assignment. |

---

## Category: Notification (NOT)

| Rule ID | Description | Severity | Required Evidence |
|---|---|---|---|
| DEF-060 | Process initiators must receive confirmation when their process request reaches key milestones (submitted, approved, rejected, completed). | Medium | Notification service call or Intermediate Message Event at milestone boundary. |
| DEF-061 | Rejected submissions must notify the original requester with a reason. | High | Rejection path includes notification step with rejection reason variable. |

---

## Category: Security (SEC)

| Rule ID | Description | Severity | Required Evidence |
|---|---|---|---|
| DEF-070 | All Human Services (coaches) must be accessible only to authenticated users. | Critical | Lane or task restricted to a defined Team or BPM security role (not public/anonymous). |
| DEF-071 | Administrative operations (process termination, bulk reassignment) must be restricted to the BPMAdministrator role or equivalent. | Critical | BPM security role check or process app exposure restriction. |
| DEF-072 | Sensitive data fields (SSN, account number, PII) in coaches must not be exposed in plain text — use masking or server-side retrieval. | High | Coach control configured as masked/password type, or data retrieved only on demand. |

---

## Category: Data Validation (DAT)

| Rule ID | Description | Severity | Required Evidence |
|---|---|---|---|
| DEF-080 | Required business object fields must be validated before the process advances to the next step. | High | Coach validation script, required field marking, or Decision Service input validation. |
| DEF-081 | Numeric fields with business constraints (amounts, dates) must have boundary validation. | Medium | Validation rule in coach or decision service checking range/boundary. |

---

## Category: Reporting / Tracking (RPT)

| Rule ID | Description | Severity | Required Evidence |
|---|---|---|---|
| DEF-090 | Process applications must expose at least one tracking group in the Business Performance Data Warehouse (BPDW). | Medium | Tracking group defined with at least one tracked variable. |
| DEF-091 | Process KPIs (cycle time, approval rate, rejection reason) must be trackable. | Medium | Tracked variables include decision outcome and timestamps. |

---

## Category: Role / Team Configuration (ROL)

| Rule ID | Description | Severity | Required Evidence |
|---|---|---|---|
| DEF-100 | Every lane in every BPD must be assigned to a Team or a Role — unassigned lanes are a governance violation. | High | All BPD lanes have explicit Team binding. |
| DEF-101 | Teams must be sourced from an LDAP/directory group, not from a static list of named users. | Medium | Team definition uses group sync, not individual user list. |

---

## Category: Exception Handling (EXC)

| Rule ID | Description | Severity | Required Evidence |
|---|---|---|---|
| DEF-110 | Processes must handle the "timeout with no action" scenario — if no user completes a task within the maximum SLA window, the process must not hang indefinitely. | Critical | Interrupting timer event or process-level end state configured for max timeout. |
| DEF-111 | Exception paths must not lead to a blank end event — they must route to a named error-end event or a documented compensating flow. | Medium | Error end event or labeled compensating sequence. |

---

## Severity definitions

| Severity | Meaning |
|---|---|
| Critical | Violates platform security or regulatory requirements; must be fixed before production deployment |
| High | Significant operational or governance risk; should be remediated in the current sprint |
| Medium | Governance gap or best-practice deviation; should be tracked and remediated |
| Low | Minor improvement opportunity; address in backlog |
