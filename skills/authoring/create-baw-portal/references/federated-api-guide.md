# Federated API guide

> **Skill:** `create-baw-portal`
> **Purpose:** Guidance for BAW portals targeting Process Federation Server (PFS) deployments.
> **Evidence:** VERIFIED BY IBM DOCUMENTATION and **runtime-tested against CP4BA 26.0.0 PFS** (checks PFS01–PFS11).
> PFS runtime testing confirmed on a two-system federation. Safe to generate PFS portal code.

---

## When PFS applies

Use the federated API family when the deployment includes Process Federation Server.
PFS aggregates task and team data across multiple source BAW systems and exposes a unified REST surface.

A federated endpoint returns tasks from multiple source systems in a single response.
Each task item carries a `systemID` that must be used to route task launch back to the correct source system.

Without PFS, the non-federated WLE REST API is the correct choice — see `references/non-federated-api-guide.md`.

---

## Federated task list — T2.1

```
GET /rest/bpm/federated/v1/tasks?calcStats=true&size=500
```

**Evidence:** ✅ VERIFIED — runtime confirmed (PFS01, CP4BA 26.0.0, two federated source systems).
Returns 404 on non-federated BAW (confirmed local observation).

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
| `systemID` | Identifies the source BAW system |
| `taskCompletionUrlPrefix` | Base URL for constructing task launch URLs on that system |
| `restUrlPrefix` | Base URL for REST calls to that system |
| `statusCode` | Status of this source system (check for partial failures) |
| `indexRefreshInterval` | How often the PFS index refreshes — use for freshness indicators |

> `statusCode` and `indexRefreshInterval` are system-scoped fields in `federationResult` entries.
> They do not appear on individual task items.

**`size=500` means up to 500 tasks — not all tasks.** Page with `offset` when `totalCount` exceeds returned count.

**Partial failures:** A response may include partial results when one or more source systems are unavailable.
Check `federationResult[].statusCode` for per-system failure indicators (HTTP 408, 503).
Do not treat a single-system failure as a complete task-list failure.
Retain results from available systems and surface a partial-data indicator to the user.

---

## Federated task launch — T3.4

**Evidence:** RUNTIME TESTED — task launch URL and SSO validated at runtime.

**URL pattern — CONFIRMED:**

`taskCompletionUrlPrefix` from `federationResult[]` is the base teamworks URL of the source BAW system (e.g. `https://baw-host:port/teamworks`).

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

On CP4BA, the IAM Bearer token authenticates against all BAW instances behind the same ingress. A single token covers PFS and all federated source systems with no additional token exchange.

On standalone BAW (non-CP4BA), LTPA2 or SAML SSO must span all federated systems. This is a deployment configuration requirement — verify with the BAW administrator before generating task launch code.

**CSP `frame-ancestors` constraint (RUNTIME CONFIRMED):**

BAW task form pages enforce `frame-ancestors` scoped to the deployment origin:

- A portal served from the **same origin** as the BAW deployment can iframe task forms from all federated instances ✅
- A portal on a **different origin** will be blocked by the browser — generate `window.open()` for cross-origin deployments instead

Do not construct task launch URLs from unvalidated `federationResult` field values — always validate and allowlist `taskCompletionUrlPrefix` before use.

---

## PFS search APIs — T3.3

**Evidence:** ✅ VERIFIED — runtime confirmed (PFS04–PFS08, CP4BA 26.0.0 PFS).

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
> This differs from non-federated (WLE v1) where the confirmed path on BAW 24+ is `/searches/tasks/meta/fields` (with `/tasks/` segment).
> Do not swap these paths between API families — using the NF path against PFS or vice versa will produce a 404.
> Search actions are at `/searches/actions` — not `/searches/tasks/actions`.

---

## PFS federated system metadata — T3.2

**Evidence:** VERIFIED BY IBM DOCUMENTATION — optional, not required for every request

```
GET /rest/bpm/federated/v1/systems
```

Returns the list of federated BAW systems and their `systemID` values.
This is optional. The per-task `federationResult` object provides routing fields on demand
and is sufficient for task-launch routing without a separate systems list call.

---

## PFS federated launchable entities — T3.1

**Evidence:** ✅ VERIFIED — runtime confirmed (PFS02, CP4BA 26.0.0 PFS).

```
GET /rest/bpm/federated/v1/launchableEntities
```

Returns exposed launchable processes and services across all federated BAW systems.
Federated equivalent of the NF `/rest/bpm/wle/v1/exposed`.

---

## PFS global teams

**Evidence:** VERIFIED BY IBM DOCUMENTATION

```
GET /rest/bpm/federated/v1/globalTeams
```

Returns global teams in the federated context.

---

## PFS Team Performance Dashboard APIs — T3.5–T3.10

**Evidence:** VERIFIED

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

All responses include `federationResult[]` — one entry per source BAW system with `systemID`, `statusCode`, `version`, `systemType`, `restUrlPrefix`, `taskCompletionUrlPrefix`, `indexRefreshInterval`.

> **API family difference:** PFS teamtasks uses **PUT** (same as NF). The IBM documentation shows GET — the PUT is what actually works. Do not generate GET calls for `teamtasks`.

---

## PFS search freshness

`indexRefreshInterval` from `federationResult[]` indicates how frequently the PFS index refreshes
for a given source system. Surface this lag in freshness indicators so users understand that the
task list may not reflect the most recent state of tasks on source systems.

---

## PFS partial-failure handling

`federationResult[]` is present in every PFS dashboard response — one entry per source BAW system. Each entry carries a `statusCode` for that system's contribution to the result.

When `federationResult[n].statusCode` is non-200:

1. Do not treat it as a complete request failure — other systems may have succeeded.
2. Retain results from the systems that returned 200.
3. Surface a user-facing message that results may be incomplete (e.g. "Some data sources are unavailable — results may be incomplete.").
4. Do not generate duplicate task entries — PFS index lag can cause transient duplicates; deduplicate by `TKIID` + `systemID`.

Expected non-200 codes: HTTP 408 (source system timeout), HTTP 503 (source system unavailable).

---

## XSRF for PFS APIs

Session cookie (`credentials: 'same-origin'` / `withCredentials: true`) is sufficient for PFS federated API mutations. **No `bpm-csrf-token` header is required.** Do not generate code that adds or manages it.

On CP4BA deployments, authenticate via `Authorization: Bearer <token>`. No XSRF cookie or header required.

---

## PFS validation status

All core PFS APIs have been verified:

- ✅ Federated task list — `items[]`, `federationResult[]`, all routing fields
- ✅ Federated task launch URL pattern, SSO, and CSP `frame-ancestors` — see T3.4
- ✅ All four PFS v2 dashboard endpoints — response shapes confirmed above
- ✅ `federationResult[]` present in all dashboard responses with per-system `statusCode`

Remaining deployment-time validation items (not blocking for code generation):

- Paging behavior for users with more than 500 federated tasks — surface truncation indicator when `totalCount` exceeds returned items
- True partial-failure behavior — `federationResult[n].statusCode` non-200 not observed in testing (both source systems were healthy); handle defensively using the pattern above
- Index lag duration in production environments — use `indexRefreshInterval` from `federationResult[]` to inform freshness indicators
