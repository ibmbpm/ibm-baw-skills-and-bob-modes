# Personas and capabilities

> **Skill:** `create-baw-portal`
> **Purpose:** Maps portal end-user personas to required dashboards, APIs, and validation status.
> The Bob user is a developer. The personas below are the end users of the portal the developer builds.

---

## Persona overview

| Persona | Portal purpose | Validation status |
|---|---|---|
| Task worker | Personal task list and launch | List/detail: runtime-verified, HTTP 200 (non-federated and federated); launch documentation-verified |
| Manager/team lead | Team workload and member overview | Dashboard calls runtime-verified (non-federated and federated; HTTP status only) |
| Executive/process owner | Cross-team aggregate and trend | Documentation-verified; product definition required |
| Administrator | Cross-user task and process visibility; scoped by Business Automation Workflow server-side role | No reproducible runtime test; exact entitlement unknown |

---

## Task worker

### Portal purpose

A process participant who has personal tasks assigned to them.
The portal shows their task backlog, highlights overdue and at-risk items, and allows them to open and complete tasks using the existing Business Automation Workflow task UI.

### Required dashboards

- Personal task list (summary counts such as Overdue, At Risk, Active, Total are optional)
- Search, filter, and sort controls
- Task detail / launch (iframe modal, panel or new tab, per hosting profile)

### Required data

| Data | Endpoint | Verification |
|---|---|---|
| Current user identity | `GET /rest/bpm/wle/v1/user/current?parts=all` | runtime-verified |
| Personal task list | `GET /rest/bpm/wle/v1/tasks?interaction=claimed_and_available&size=500` | runtime-verified |
| Task launch | `/teamworks/process.lsw?zWorkflowState=1&zTaskId={TKIID}&zResetContext=true` | documentation-verified URL pattern; no runtime check loads a task form (`NF-TASK-LAUNCH`) |
| Federated task list | `GET /rest/bpm/federated/v1/tasks?calcStats=true&size=500` | runtime-verified (HTTP 200) against two federated source systems; `federationResult[]` present |

### Authorization expectations

- Session-cookie authentication for same-origin portals hosted on Business Automation Workflow
- Only the authenticated user's tasks are returned by `interaction=claimed_and_available`
- No special permissions required beyond a valid Business Automation Workflow user session

### Validation status

- Non-federated personal task dashboard: task list/detail and claim/assign-back/priority-update runtime-verified (HTTP 200); finish/cancel and task launch documentation-verified
- Federated personal task dashboard: task list runtime-verified (HTTP 200) against two source systems; task launch documentation-verified (the runtime check asserts only that `federationResult[]` is present); `federationResult[]` is top-level; partial-failure pattern documented

### Known blockers

- `sandbox` attribute on task iframe: test against Business Automation Workflow task forms before enabling (deployment advisory; see [Open deployment decisions](hosting-and-generation.md#open-deployment-decisions))
- Server-side paging beyond 500 tasks: deployment-time validation item (documented advisory)

---

## Manager / team lead

### Portal purpose

A person responsible for one or more teams. The portal shows team workload at a glance,
identifies at-risk members, and allows drill-down to individual team member tasks.

### Required dashboards

- Team summary overview (aggregate counts per team)
- Team member workload list
- Individual member drill-down
- Team task list
- Task trend chart

### Required data

| Data | NF Endpoint | FED Endpoint | Verification |
|---|---|---|---|
| Managed teams | `GET /rest/bpm/wle/v1/managedGlobalTeams` | N/A | runtime-verified |
| All teams | `GET /rest/bpm/wle/v1/globalTeams` | `GET /rest/bpm/federated/v1/globalTeams` | NF: runtime-verified (HTTP 200); FED: documentation-verified only |
| Team summary (all) | `GET /rest/bpm/wle/v2/dashboards/teamsummary` | `GET /rest/bpm/federated/v2/dashboards/teamsummary` | runtime-verified (HTTP 200, status only) |
| Team summary (single) | `GET /rest/bpm/wle/v2/dashboards/teamsummary/{teamId}` | `GET /rest/bpm/federated/v2/dashboards/teamsummary/{teamId}` | runtime-verified (HTTP 200, status only) |
| Team members | `GET /rest/bpm/wle/v2/dashboards/teammember/{teamId}` | `GET /rest/bpm/federated/v2/dashboards/teammember/{teamId}` | runtime-verified (HTTP 200, status only) |
| Member workload | `GET /rest/bpm/wle/v2/dashboards/teammember/{teamId}/{username}` | `GET /rest/bpm/federated/v2/dashboards/teammember/{teamId}/{username}` | documentation-verified |
| Team tasks (both PUT) | `PUT /rest/bpm/wle/v2/dashboards/teamtasks/{teamId}` | `PUT /rest/bpm/federated/v2/dashboards/teamtasks/{teamId}` | PFS: runtime-verified (HTTP 200, status only); NF: documentation-verified |
| Team task trend | `GET /rest/bpm/wle/v2/dashboards/teamtasktrend/{teamId}` | `GET /rest/bpm/federated/v2/dashboards/teamtasktrend/{teamId}` | runtime-verified (HTTP 200, status only) |
| Task reassignment | `PUT /rest/bpm/wle/v1/task/{taskId}?action=assign` | N/A (V2 scope) | documentation-verified |

### Authorization expectations

- `managedGlobalTeams` is the documented endpoint for manager-scoped team discovery
- Manager-level permission required for cross-user task assignment
- Business Automation Workflow and PFS both enforce manager authorization at the API level — HTTP 400 if caller manages no teams
- Do not include reassignment in a read-only manager dashboard baseline

### Validation status

- WLE v2 dashboard APIs: HTTP 200 observed on Cloud Pak for Business Automation 26.0.0 for four of seven operations (status only; response schema not asserted). Generate for Business Automation Workflow 24+ behind an FDR gate that follows the four outcome classes in `non-federated-api-guide.md` §Manager and team dashboard APIs.
- PFS v2 dashboard APIs: HTTP 200 observed on Cloud Pak for Business Automation 26.0.0 for five of six operations (the single-member call is documentation-verified only). Generate with a validation gate; see `references/federated-api-guide.md`.

### Known blockers

- Paging behavior for large teams: deployment-time validation item; surface truncation indicator when `totalCount` exceeds returned items.

---

## Executive / process owner

### Portal purpose

A senior stakeholder monitoring overall process health.
The portal shows aggregate overdue, at-risk, and active work across teams or processes,
identifies trends, and allows drill-down to team detail.

### Required dashboards

- Cross-team aggregate summary (overdue, at-risk, active by team)
- Team trend charts (tasks created vs completed over time)
- Drill-down to team detail (reuses manager views)

### Required data

| Data | NF Endpoint | FED Endpoint | Verification |
|---|---|---|---|
| Per-team summary | `GET /rest/bpm/wle/v2/dashboards/teamsummary/{teamId}` (iterated) | `GET /rest/bpm/federated/v2/dashboards/teamsummary` | runtime-verified (HTTP 200, status only) |
| Per-team trend | `GET /rest/bpm/wle/v2/dashboards/teamtasktrend/{teamId}` (iterated) | `GET /rest/bpm/federated/v2/dashboards/teamtasktrend/{teamId}` (iterated) | runtime-verified (HTTP 200, status only) |

Cross-team aggregation is client-side or backend rollup using per-team API calls.
No dedicated executive-level aggregate endpoint has been identified; confirm with IBM before assuming one is needed.

### Authorization expectations

- Business Automation Workflow enforces `teamsummary` results to teams the calling user manages — the "executive" view is a client-side rollup over all teams returned (no additional portal-side role check required)
- Do not assume enterprise-wide access or global admin visibility
- No additional portal-side role check is needed — Business Automation Workflow scopes the API response to the caller's managed teams

### Validation status

- Per-team APIs: `teamsummary` and `teamtasktrend` returned HTTP 200 on both WLE v2 and PFS v2 (Cloud Pak for Business Automation 26.0.0; status only). Generate with a validation gate.

### Known blockers

- FDR availability must be probed at runtime; surface a neutral empty state when the `503` response is received

---

## Administrator

### Portal purpose

A user with Business Automation Workflow administrator privileges who needs cross-user and cross-team visibility beyond
what a manager or task worker sees. The portal surface changes but the underlying security model
does not: Business Automation Workflow enforces what each user can see based on their server-side role, exactly as
Workplace and Process Portal do.

### Required dashboards

- All-tasks view (tasks across all users, not just the authenticated user's own)
- All-processes view (process instances beyond the caller's own)
- Admin-capable saved search management

### Required data

| Data | Endpoint | Admin-specific parameter | Evidence |
|---|---|---|---|
| Saved-search permissions | `GET /rest/bpm/wle/v1/searches/actions` | Saved-search policies only (see `baw-rest.md`) — **not** a task/process admin signal | runtime-verified (HTTP 200 only); `data.actions` envelope IBM-documented (24.0.1) but unobserved on 26.0.0; action strings unobserved |
| All claimed tasks (cross-user) | `PUT /rest/bpm/wle/v1/tasks` | **GATED — not generated.** `allClaimed` placement is unverified. Ask for on-environment verification with an admin and a non-admin account first (see [`baw-rest.md`](baw-rest.md)) | Not reproducible: no runtime check; no IBM page |
| All process instances (cross-user) | `GET /rest/bpm/wle/v1/processes/search` | `includeNonAdmin=true` as query parameter; non-admin users reportedly get a scoped subset | Reported to work on Cloud Pak for Business Automation 26.0.0, but no runtime check reproduces it; the path is untested in this project; entitlement not documented in IBM pages consulted |

### Authorization expectations

- Admin behaviour is driven by Business Automation Workflow server-side authorization — there is no separate admin API stack
- A portal built with this skill is a different UI surface; the Business Automation Workflow security model does not change
- Saved-search administration (`ACTION_ADMINISTER_SHARED_SAVED_SEARCHES`, `ACTION_SAVED_SEARCH_SUPER_ADMIN`) is **not** a universal Business Automation Workflow administrator role. It authorizes saved-search operations only
- Task-, process-instance- and per-action rights are separate: e.g. `ACTION_SUSPEND_INSTANCE`, `ACTION_RESUME_INSTANCE`, `ACTION_RETRY_INSTANCE`, `ACTION_ABORT_INSTANCE`, `ACTION_DELETE_INSTANCE`, `ACTION_CHANGE_INSTANCE_DUEDATE` each have their own policy and default eligibility
- Do not gate admin views with portal-side role checks — rely entirely on what Business Automation Workflow returns

### Capability-specific gating pattern

Do not use `GET /rest/bpm/wle/v1/searches/actions` as an admin-UI gate. Instead, for each admin
panel:

1. Render nothing by default.
2. Issue the panel's own request (`includeNonAdmin=true`; the cross-user task panel stays blocked, see the table above).
3. Show the panel only on HTTP 200 with a usable result; on 401/403 or an empty result, show a neutral "not available for your account" state. An empty result is ambiguous (no data vs. no entitlement) — do not claim the user is or is not an administrator.
4. Use saved-search actions solely to enable or disable saved-search controls.

### Evidence status

- `GET /searches/actions`: only the HTTP 200 status is runtime-verified; action strings are not asserted, so "ADMINISTER present for admin, absent for standard users" is an unreproduced claim.
- `includeNonAdmin` and the cross-user task request: reports of success cannot be reproduced; no runtime check exists. The open placement question and the untested `/processes/search` path are noted in [`baw-rest.md`](baw-rest.md) and remain unresolved.
- Exact server-side entitlement for these cross-user calls is **unknown**; re-verify on the target environment with an admin and a non-admin account before shipping.

### Implementation notes

- `includeNonAdmin=true` is a query parameter on `GET /rest/bpm/wle/v1/processes/search`. Business Automation Workflow enforces the restriction server-side.
- The `processes/search` response envelope was reported as `data.processes[]` (not `data.items[]`) and `data.overview` (aggregate counts); confirm against the target environment.

### Known blockers

- "Administrator" is defined above as a user with Business Automation Workflow administrator privileges, but the exact server entitlement is unconfirmed (next bullet); do not assume it means full Business Automation Workflow system administrator rights
- Exact entitlements for the cross-user calls are unknown and have no reproducible evidence
