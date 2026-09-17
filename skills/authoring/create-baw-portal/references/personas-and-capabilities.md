# Personas and capabilities

> **Skill:** `create-baw-portal`
> **Purpose:** Maps portal end-user personas to required dashboards, APIs, and validation status.
> The Bob user is a developer. The personas below are the end users of the portal the developer builds.

---

## Persona overview

| Persona | Portal purpose | Validation status |
|---|---|---|
| Task worker | Personal task list and launch | Runtime-verified (non-federated and federated) |
| Manager/team lead | Team workload and member overview | Runtime-verified (non-federated and federated) |
| Executive/process owner | Cross-team aggregate and trend | Documented, product definition required |
| Administrator | Cross-user task and process visibility; scoped by BAW server-side role | Documented — APIs mapped; runtime verification pending |

---

## Task worker

### Portal purpose

A process participant who has personal tasks assigned to them.
The portal shows their task backlog, highlights overdue and at-risk items, and allows them to open and complete tasks using the existing BAW task UI.

### Required dashboards

- Personal task list with stat cards (Overdue, At Risk, Active, Total)
- Search, filter, and sort controls
- Task detail / launch via iframe modal

### Required data

| Data | Endpoint | Verification |
|---|---|---|
| Current user identity | `GET /rest/bpm/wle/v1/user/current?parts=all` | ✅ VERIFIED |
| Personal task list | `GET /rest/bpm/wle/v1/tasks?interaction=claimed_and_available&size=500` | ✅ VERIFIED |
| Task launch | `/teamworks/process.lsw?zWorkflowState=1&zTaskId={TKIID}&zResetContext=true` | ✅ VERIFIED |
| Federated task list | `GET /rest/bpm/federated/v1/tasks?calcStats=true&size=500` | ✅ VERIFIED (PFS01) — two federated source systems confirmed |

### Authorization expectations

- Session-cookie authentication for same-origin BAW-hosted portals
- Only the authenticated user's tasks are returned by `interaction=claimed_and_available`
- No special permissions required beyond a valid BAW user session

### Validation status

- Non-federated personal task dashboard: ✅ runtime-verified
- Federated personal task dashboard: ✅ VERIFIED (PFS01) — two source systems confirmed; `federationResult[]` top-level; partial-failure pattern documented

### Known blockers

- `sandbox` attribute on task iframe: test against BAW task forms before enabling (deployment advisory; see `references/quality-and-validation.md`)
- Server-side paging beyond 500 tasks: deployment-time validation item (documented advisory)

---

## Manager / team lead

### Portal purpose

A manager or team lead is responsible for one or more teams. The portal shows team workload at a glance,
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
| Managed teams | `GET /rest/bpm/wle/v1/managedGlobalTeams` | N/A | ✅ VERIFIED |
| All teams | `GET /rest/bpm/wle/v1/globalTeams` | `GET /rest/bpm/federated/v1/globalTeams` | ✅ VERIFIED — FED endpoint documented only |
| Team summary (all) | `GET /rest/bpm/wle/v2/dashboards/teamsummary` | `GET /rest/bpm/federated/v2/dashboards/teamsummary` | ✅ VERIFIED |
| Team summary (single) | `GET /rest/bpm/wle/v2/dashboards/teamsummary/{teamId}` | `GET /rest/bpm/federated/v2/dashboards/teamsummary/{teamId}` | ✅ VERIFIED |
| Team members | `GET /rest/bpm/wle/v2/dashboards/teammember/{teamId}` | `GET /rest/bpm/federated/v2/dashboards/teammember/{teamId}` | ✅ VERIFIED |
| Member workload | `GET /rest/bpm/wle/v2/dashboards/teammember/{teamId}/{username}` | `GET /rest/bpm/federated/v2/dashboards/teammember/{teamId}/{username}` | ⚠️ Documented |
| Team tasks (both PUT) | `PUT /rest/bpm/wle/v2/dashboards/teamtasks/{teamId}` | `PUT /rest/bpm/federated/v2/dashboards/teamtasks/{teamId}` | ✅ VERIFIED |
| Team task trend | `GET /rest/bpm/wle/v2/dashboards/teamtasktrend/{teamId}` | `GET /rest/bpm/federated/v2/dashboards/teamtasktrend/{teamId}` | ✅ VERIFIED |
| Task reassignment | `PUT /rest/bpm/wle/v1/task/{taskId}?action=assign` | N/A (V2 scope) | ⚠️ Documented |

### Authorization expectations

- `managedGlobalTeams` is the documented endpoint for manager-scoped team discovery
- Manager-level permission required for cross-user task assignment
- BAW and PFS both enforce manager authorization at the API level — HTTP 400 if caller manages no teams
- Do not include reassignment in a read-only manager dashboard baseline

### Validation status

- WLE v2 dashboard APIs: ✅ VERIFIED — safe to generate for BAW 24+; gate on FDR probe
- PFS v2 dashboard APIs: ✅ VERIFIED — all four endpoints confirmed; see `references/federated-api-guide.md`

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
| Per-team summary | `GET /rest/bpm/wle/v2/dashboards/teamsummary/{teamId}` (iterated) | `GET /rest/bpm/federated/v2/dashboards/teamsummary` | ✅ VERIFIED |
| Per-team trend | `GET /rest/bpm/wle/v2/dashboards/teamtasktrend/{teamId}` (iterated) | `GET /rest/bpm/federated/v2/dashboards/teamtasktrend/{teamId}` (iterated) | ✅ VERIFIED |

Cross-team aggregation is client-side or backend rollup using per-team API calls.
No dedicated executive-level aggregate endpoint has been identified; confirm with IBM/PM before assuming one is needed.

### Authorization expectations

- BAW enforces `teamsummary` results to teams the calling user manages — the "executive" view is a client-side rollup over all teams returned (no additional portal-side role check required)
- Do not assume enterprise-wide access or global admin visibility
- No additional portal-side role check is needed — BAW scopes the API response to the caller's managed teams

### Validation status

- Per-team APIs: ✅ VERIFIED — `teamsummary` and `teamtasktrend` runtime tested against both WLE v2 and PFS v2 dashboard endpoints; safe to generate

### Known blockers

- FDR availability must be probed at runtime; surface a neutral empty state when the `503` response is received

---

## Administrator

### Portal purpose

A user with BAW administrator privileges who needs cross-user and cross-team visibility beyond
what a manager or task worker sees. The portal surface changes but the underlying security model
does not: BAW enforces what each user can see based on their server-side role, exactly as
Workplace and Process Portal do.

### Required dashboards

- All-tasks view (tasks across all users, not just the authenticated user's own)
- All-processes view (process instances beyond the caller's own)
- Admin-capable saved search management

### Required data

| Data | Endpoint | Admin-specific parameter | Verification |
|---|---|---|---|
| Detect admin rights | `GET /rest/bpm/wle/v1/searches/actions` | Presence of `ACTION_ADMINISTER_SHARED_SAVED_SEARCHES` or `ACTION_SAVED_SEARCH_SUPER_ADMIN` in response | ⚠️ Documented — runtime verification pending |
| All claimed tasks (cross-user) | `PUT /rest/bpm/wle/v1/tasks` | `allClaimed=true` (only effective when `assignedToUser` filter also present) | ⚠️ Documented — runtime verification pending |
| All process instances (cross-user) | `GET /rest/bpm/wle/v1/processes/search` | `includeNonAdmin=true` | ⚠️ Documented — runtime verification pending |

### Authorization expectations

- Admin behavior is driven by the BAW server-side role — there is no separate admin API stack
- A portal built with this skill is a different UI surface; the BAW security model does not change
- BAW returns admin-scoped data only to users who hold the appropriate server-side permission
- Do not gate admin views with portal-side role checks — rely entirely on what BAW returns

### Admin detection pattern

Check the response from `GET /rest/bpm/wle/v1/searches/actions`. If the returned actions list
includes `ACTION_ADMINISTER_SHARED_SAVED_SEARCHES` or `ACTION_SAVED_SEARCH_SUPER_ADMIN`, the
authenticated user has administrator-level saved-search rights. Use this as the runtime signal
to show or hide admin UI surfaces.

### Validation status

- API patterns documented; runtime verification against CP4BA 26.0.x pending
- Do not generate admin-scoped code until the relevant APIs are runtime-verified in this project

### Known blockers

- None — persona definition confirmed
- Runtime verification of admin endpoints is a validation task, not a blocker
