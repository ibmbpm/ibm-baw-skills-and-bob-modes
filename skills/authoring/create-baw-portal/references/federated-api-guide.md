# Federated API guide

> **Skill:** `create-baw-portal`
> **Purpose:** Guidance for Business Automation Workflow portals targeting Process Federation Server (PFS) deployments.
> **Verification status:** Contracts follow IBM documentation. HTTP 200 in a retained run on Cloud Pak for Business Automation 26.0.0 PFS (status only) covers the federated task list, system metadata, launchable entities, search metadata fields, and PFS v2 dashboard endpoints; checks assert only that `federationResult[]` is present without validating full response schemas or business behavior. Search actions, saved-search CRUD, ad hoc task search, process-instance search, and global teams are documentation-verified without a retained run. HTTP-status verification does not establish response-schema correctness or business behavior.
> Dashboard checks assert HTTP 200 only. Generate PFS task, search and launch code per the capability catalog; emit validation gates for dashboards and any `documentation-verified` operation.

---

## When PFS applies

Use the federated API family when the deployment includes Process Federation Server.
PFS aggregates task and team data across multiple source Business Automation Workflow systems and exposes a unified REST surface.

A federated endpoint returns tasks from multiple source systems in a single response.
Each task item carries a `systemID` that must be used to route task launch back to the correct source system.

Without PFS, the non-federated WLE REST API is the correct choice — see `references/non-federated-api-guide.md`.

---

## Federated task list

```
GET /rest/bpm/federated/v1/tasks?calcStats=true&size=500
```

**Evidence:** runtime-verified — HTTP 200 in a retained run (Cloud Pak for Business Automation 26.0.0, two federated source systems; status-level verification only).
Returns 404 on non-federated Business Automation Workflow (observed on non-federated deployment).

**Response structure:**

```
items[]                         ← tasks from all federated systems
federationResult[]              ← one entry per involved source system
```

Each task item carries a `systemID`. The top-level `federationResult[]` array has one entry per
involved source system. Map `task.systemID` to the matching `federationResult` entry to obtain
routing fields for that task.

**`federationResult[]` entry fields:**

| Field | Purpose |
|---|---|
| `systemID` | Identifies the source Business Automation Workflow system |
| `taskCompletionUrlPrefix` | Base URL for constructing task launch URLs on that system |
| `restUrlPrefix` | Base URL for REST calls to that system |
| `statusCode` | Status of this source system (check for partial failures) |
| `indexRefreshInterval` | How often the PFS index refreshes — use for freshness indicators |

> `statusCode` and `indexRefreshInterval` are system-scoped fields in `federationResult` entries.
> They do not appear on individual task items.

**`size=500` means up to 500 tasks — not all tasks.** Page with `offset` when `totalCount` exceeds returned count; see [`non-federated-api-guide.md` §Personal task list](non-federated-api-guide.md#personal-task-list).

**Partial failures:** A response may include partial results when one or more source systems are unavailable.
Check `federationResult[].statusCode` for per-system failure indicators (HTTP 408, 503).
Do not treat a single-system failure as a complete task-list failure.
Retain results from available systems and surface a partial-data indicator to the user.

**Registered system absent from the list (observed on Cloud Pak for Business Automation 26.0.3 SP20 r2, one deployment).** A task owned on a second registered source system was missing from `items[]`, and that system had no `federationResult[]` entry, although the task was directly retrievable from the system and the system's `statusCode` in `GET /rest/bpm/federated/v1/systems` was 200. That systems entry reported `taskSearchEnabled: false` while the system whose tasks were listed reported `true`. This is a candidate explanation, not a proven cause (index and registration state were not inspected, and federation configuration was not changed). Consequently do not present the federated list as every task the user owns, and read `taskSearchEnabled` from the systems call when diagnosing a missing system. A `?systemID=` query filter returned HTTP 500 on this deployment — filter by `systemID` client-side.

**No allowed-actions on PFS items.** PFS items did not carry an allowed-actions member. Read actions from the source system with `GET {restUrlPrefix}/v1/task/{taskId}?parts=actions`. A task created by a process start appeared in the PFS list with the expected state and the source `systemID`.

---

## Federated task launch

**Evidence:** documentation-verified — the launch URL pattern, HTTP 303 → 200 chain and SSO below are documented by IBM and observed in development; retained checks assert only that `federationResult[]` is present without loading a task form.

**URL pattern (development claim):**

`taskCompletionUrlPrefix` from `federationResult[]` is the base teamworks URL of the source Business Automation Workflow system (e.g. `https://baw-host:port/teamworks`).

The task launch URL is identical in structure to non-federated:

```
{taskCompletionUrlPrefix}/process.lsw?zWorkflowState=1&zTaskId={TKIID}&zResetContext=true
```

**Response chain:** HTTP 303 → `fauxRedirect.lsw?...&zTaskId=t{TKIID}&zComponentName=CoachFlow` → HTTP 200 (task form).
The `TKIID` integer is used as-is; the server normalizes it to `t{TKIID}` internally.

**Routing procedure:**

1. Read `task.systemID` from the task item.
2. Find the matching `federationResult[]` entry by `systemID`.
3. Validate and allowlist `taskCompletionUrlPrefix` from that entry.
4. Compose the task launch URL: `{taskCompletionUrlPrefix}/process.lsw?zWorkflowState=1&zTaskId={TKIID}&zResetContext=true`
5. Open the URL — iframe (same-origin portal) or new tab (cross-origin portal). See SSO and CSP constraints below.

**SSO:**

On Cloud Pak for Business Automation, the IAM Bearer token authenticates against all Business Automation Workflow instances behind the same ingress. A single token covers PFS and all federated source systems with no additional token exchange.

On standalone Business Automation Workflow (not on Cloud Pak for Business Automation), LTPA2 or SAML SSO must span all federated systems. This is a deployment configuration requirement — verify with the Business Automation Workflow administrator before generating task launch code.

**CSP `frame-ancestors` constraint (observed on the tested Cloud Pak for Business Automation deployment):**

Business Automation Workflow task form pages enforce `frame-ancestors` scoped to the deployment origin. Prerequisites for embedding from another origin are owned by [`hosting-and-generation.md`](hosting-and-generation.md):

- A portal served from the **same origin** as the Business Automation Workflow deployment can iframe task forms from all federated instances.
- A portal on a **different origin** is blocked unless the hosting prerequisites are met; a reverse proxy alone is not sufficient. Generate `window.open()` for cross-origin deployments instead

Do not construct task launch URLs from unvalidated `federationResult` field values — always validate and allowlist `taskCompletionUrlPrefix` before use.

---

## PFS search APIs

**Evidence:** Search metadata fields: HTTP 200 in a retained run on Cloud Pak for Business Automation 26.0.0 PFS (status only). Other metadata, search actions, saved-search CRUD, ad hoc search, and instance search are documentation-verified without a retained run.

### Saved search CRUD

| Endpoint | Method | Purpose |
|---|---|---|
| `/rest/bpm/federated/v1/searches/tasks` | GET | List saved task searches |
| `/rest/bpm/federated/v1/searches/tasks` | POST | Create a saved task search |
| `/rest/bpm/federated/v1/searches/tasks/{idOrName}` | GET | Retrieve a specific saved search |
| `/rest/bpm/federated/v1/searches/tasks/{idOrName}` | PUT | Update a saved search |
| `/rest/bpm/federated/v1/searches/tasks/{idOrName}` | DELETE | Delete a saved search |

### Ad hoc search and instances

| Endpoint | Method | Purpose |
|---|---|---|
| `PUT /rest/bpm/federated/v1/tasks` | PUT | Execute an ad hoc federated task search (distinct from saved-search CRUD) |
| `PUT /rest/bpm/federated/v1/instances` | PUT | Federated process-instance search |

### Search metadata

| Endpoint | Purpose |
|---|---|
| `GET /rest/bpm/federated/v1/searches/meta/fields` | Task search field names and types |
| `GET /rest/bpm/federated/v1/searches/meta/constraintFields` | Constraint filter options |
| `GET /rest/bpm/federated/v1/searches/meta/businessDataFields` | Business data variables |
| `GET /rest/bpm/federated/v1/searches/meta/taskStatus` | Task status values |
| `GET /rest/bpm/federated/v1/searches/meta/priority` | Priority values |

### Search actions

```
GET /rest/bpm/federated/v1/searches/actions
```

> **Federated search metadata paths** are under `/searches/meta/` — for example `/rest/bpm/federated/v1/searches/meta/fields`.
> This differs from non-federated (WLE v1) where the confirmed path on Business Automation Workflow 24+ is `/searches/tasks/meta/fields` (with `/tasks/` segment).
> Do not swap these paths between API families — using the NF path against PFS or vice versa will produce a 404.
> Search actions are at `/searches/actions` — not `/searches/tasks/actions`.

---

## PFS federated system metadata

**Evidence:** runtime-verified — HTTP 200 in a retained run (Cloud Pak for Business Automation 26.0.0 PFS; status-level only); optional, not required for every request.

```
GET /rest/bpm/federated/v1/systems
```

Returns the list of federated Business Automation Workflow systems and their `systemID` values.
This is optional. The per-task `federationResult` object provides routing fields on demand
and is sufficient for task-launch routing without a separate systems list call.
Each entry also reports `taskSearchEnabled`, `taskHistoryEnabled`, `hostsTaskFilterService` and `groupWorkItemsEnabled` (observed on Cloud Pak for Business Automation 26.0.3 SP20 r2); `taskSearchEnabled: false` was observed on a system whose tasks were absent from the federated task list.

---

## PFS federated launchable entities

**Evidence:** runtime-verified, HTTP status only: a retained run on Cloud Pak for Business Automation 26.0.0 PFS returned HTTP 200. The response content (entity fields, `federationResult[]` per source system) and starting a process or service from an entity are documented by IBM but were not verified at runtime. Do not claim end-to-end launch is verified.

```
GET /rest/bpm/federated/v1/launchableEntities
```

Returns exposed launchable processes and services across all federated Business Automation Workflow systems.
Federated equivalent of the NF `/rest/bpm/wle/v1/exposed`.

---

## PFS global teams

**Evidence:** documentation-verified — documented by IBM; no retained execution record.

```
GET /rest/bpm/federated/v1/globalTeams
```

Returns global teams in the federated context.

---

## PFS Team Performance Dashboard APIs

**Evidence:** HTTP 200 in a retained run for team summary, single team summary, team members, team tasks PUT, and team task trend on Cloud Pak for Business Automation 26.0.0 PFS (status only); single member summary is documentation-verified without a retained run.

| Capability | Endpoint | Method |
|---|---|---|
| All teams summary | `GET /rest/bpm/federated/v2/dashboards/teamsummary` | GET |
| Single team summary | `GET /rest/bpm/federated/v2/dashboards/teamsummary/{teamId}` | GET |
| Team members workload | `GET /rest/bpm/federated/v2/dashboards/teammember/{teamId}` | GET |
| Single member workload | `GET /rest/bpm/federated/v2/dashboards/teammember/{teamId}/{username}` | GET |
| Team tasks | `PUT /rest/bpm/federated/v2/dashboards/teamtasks/{teamId}` | PUT |
| Team task trend | `GET /rest/bpm/federated/v2/dashboards/teamtasktrend/{teamId}` | GET |

**Authorization:** User must manage at least one team. HTTP 400 `CWMFS4055E` if not a manager of the requested team; HTTP 400 `CWMFS4056E` if not a manager of any team.

**Confirmed response shapes:**

`teamsummary` → `summaries[]` (all teams) or `summary{}` (single team):
```
teamId, name, description, processAppId, processAppName,
totalOpenTasks, countOverdue, countAtRisk, countOnTrack, tasksCompletedToday
```

`teammember/{teamId}` → `teamMemberList[]`:
```
name, fullName, emailAddress, phoneNumber, jobTitle, assignedTasks, tasksCompletedToday
```

`teamtasks/{teamId}` PUT → `items[]` + `totalCount` (same shape as NF teamtasks).

`teamtasktrend/{teamId}` → `data[]` array of time-series entries:
```json
{ "created": 0, "completed": 0, "timestamp": "2026-08-12T17:00:00.000Z" }
```

All responses include `federationResult[]` — one entry per source Business Automation Workflow system with `systemID`, `statusCode`, `version`, `systemType`, `restUrlPrefix`, `taskCompletionUrlPrefix`, `indexRefreshInterval`.

> **API family difference:** PFS teamtasks uses **PUT** (same as NF). The IBM documentation shows GET — the PUT is what actually works. Do not generate GET calls for `teamtasks`.

---

## PFS search freshness

`indexRefreshInterval` from `federationResult[]` indicates how frequently the PFS index refreshes
for a given source system. Surface this lag in freshness indicators so users understand that the
task list may not reflect the most recent state of tasks on source systems.

---

## PFS partial-failure handling

`federationResult[]` is present in every PFS dashboard response — one entry per source Business Automation Workflow system. Each entry carries a `statusCode` for that system's contribution to the result.

When `federationResult[n].statusCode` is non-200:

1. Do not treat it as a complete request failure — other systems may have succeeded.
2. Retain results from the systems that returned 200.
3. Surface a user-facing message that results may be incomplete (e.g. "Some data sources are unavailable — results may be incomplete.").
4. Do not generate duplicate task entries — PFS index lag can cause transient duplicates; deduplicate by `TKIID` + `systemID`.

Expected non-200 codes: HTTP 408 (source system timeout), HTTP 503 (source system unavailable).

---

## CSRF/XSRF for PFS APIs

The shared contract (documented `BPMCSRFToken` requirement, deployment-controlled legacy `XSRF-TOKEN` cookie check, authentication modes, what generated code does) is in [XSRF / CSRF for WLE REST mutations](non-federated-api-guide.md#xsrf--csrf-for-wle-rest-mutations). PFS-specific points:

- The legacy `XSRF-TOKEN` cookie check is documented for `/rest/bpm/wle/v1/*`; no reviewed source documents it for `/rest/bpm/federated/*`.
- The IBM-documented token operation is `POST /bpm/system/login` on the Business Automation Workflow Process REST surface. No reviewed source documents a PFS-specific token endpoint, or states that a token issued by Business Automation Workflow is accepted or rejected by PFS. Do not assume the PFS token contract equals the WLE one, and do not invent a PFS token endpoint.
- Observed: PFS read, search and dashboard calls returned HTTP 200 with Cloud Pak for Business Automation Bearer authentication (`Authorization: Bearer <token>`) on Cloud Pak for Business Automation 26.0.0 with no `BPMCSRFToken` sent during testing. The PFS mutation endpoints in this skill (saved-search create/update/delete, ad hoc search `PUT`) are documentation-verified only; their CSRF requirement is **verification-required** for each deployment and auth mode.

---

## PFS validation status

Retained HTTP-status evidence (2026-08-10, Cloud Pak for Business Automation 26.0.0 PFS) covers the task list, system list, launchable entities, search metadata fields and the PFS v2 dashboard endpoints; HTTP-status verification does not establish response-schema correctness or business behavior. The response shapes below come from IBM documentation and development observation:

- Federated task list — `items[]`, `federationResult[]`, routing fields (HTTP 200 retained; `federationResult[]` presence asserted)
- Federated task launch URL pattern, SSO and CSP `frame-ancestors` — see [Federated task launch](#federated-task-launch) (observed in development; documentation-verified)
- PFS v2 dashboard endpoints — HTTP 200 in a retained run (status only); response shapes are not asserted by automated checks

Remaining deployment-time validation items (not blocking for code generation):

- Paging behavior for users with >500 federated tasks — surface truncation indicator when `totalCount` exceeds returned items
- True partial-failure behavior — `federationResult[n].statusCode` non-200 not observed in testing (both source systems were healthy); handle defensively using the pattern above
- Index lag duration in production environments — use `indexRefreshInterval` from `federationResult[]` to inform freshness indicators
