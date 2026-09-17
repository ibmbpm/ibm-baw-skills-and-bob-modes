# Non-federated API guide

> **Skill:** `create-baw-portal`
> **Purpose:** Implementation-ready guidance for non-federated BAW (WLE REST API).
> **Evidence:** See `docs/04-api-inventory.md` T1–T2 and `docs/02-evidence-inventory.md` for full classifications.

---

## Authentication

Non-federated BAW portals hosted at the same origin as the BAW server use the existing authenticated browser session.

```js
// All fetch calls use same-origin session cookie — no token management required
const response = await fetch(url, {
  method: 'GET',
  credentials: 'same-origin',
  headers: { 'Accept': 'application/json' }
});
```

No CORS configuration required. No bearer token. No login screen.
For external portals, authentication and CORS prerequisites differ — see `references/hosting-and-generation.md`.

---

## Current user — T1.1

**Evidence:** VERIFIED

```
GET /rest/bpm/wle/v1/user/current?parts=all
```

**Response fields used:**

| Field | Notes |
|---|---|
| `data.fullName` | Full display name — preferred for header greeting |
| `data.displayName` | Alternative display name |
| `data.userName` | Login username — used for initials fallback |
| `data.email` | User email address — present when `parts=all` |
| `data.managerName` | Manager's display name — present when `parts=all` |
| `data.jobTitle` | Job title — present when `parts=all` |

All six fields above are confirmed present in the `parts=all` response on this BAW instance.
Always request `parts=all` — the default `parts` response omits email, managerName, and jobTitle.
Generate initials from the first letter of each word in `fullName`.
Do not persist user data in `localStorage`.

---

## Personal task list — T1.2

**Evidence:** VERIFIED

```
GET /rest/bpm/wle/v1/tasks?interaction=claimed_and_available&size=500&offset=0&calcStats=true
```

The documented semantic filter for user-actionable tasks is `interaction=claimed_and_available`.
The prototype query also included `filterByCurrentUser=true` and `includeAllBusiness=true`; these
are distinct parameters with different semantics and `includeAllBusiness=true` is not confirmed
in the IBM endpoint specification — do not rely on it across BAW versions.

**Official response structure (RUNTIME TESTED):**

```
status
data
data.items        ← task list
data.totalCount   ← total matching tasks (paging contract)
data.offset       ← current page offset
data.size         ← page size returned
data.stats        ← server-computed stats (present when calcStats=true; optional — client can compute)
data.attributeInfo ← field metadata for task items (present when calcStats=true)
```

**`data.stats` field structure (RUNTIME TESTED):**

```json
{
  "total":   24,  // total tasks returned by query
  "open":    13,  // tasks in an open state
  "onTrack": 0,   // tasks not yet at-risk or overdue
  "atRisk":  0,   // tasks flagged IS_AT_RISK
  "overdue": 13   // tasks past their DUE date
}
```

The approved reference implementation computes stats client-side from `data.items` and ignores `data.stats`. Either is valid — server-side stats save an iteration pass for simple count displays.

**Defensive extraction (one shape observed in testing; others are compatibility handling):**

```js
function extractTasks(json) {
  if (Array.isArray(json))             return json;
  if (Array.isArray(json.items))       return json.items;
  if (Array.isArray(json.data?.items)) return json.data.items;
  if (Array.isArray(json.data))        return json.data;
  return [];
}
```

**`size=500` means up to 500 tasks — not all tasks.** When `totalCount` in the response exceeds
the number of returned items, additional pages exist. Page with `offset` incremented by `size`.
The paging contract (`totalCount`, `offset`, `size`) is VERIFIED BY IBM DOCUMENTATION.

**Truncation indicator (required in generated UI):** When `totalCount` exceeds the number of items
returned in the current page, surface a visible indicator to the user — for example:
_"Showing 500 of 1,243 tasks. Use pagination to view more."_
Do not silently discard the overflow. Do not present a partial list as if it were complete.

**Task response fields:**

| Field | Type | Notes |
|---|---|---|
| `TKIID` | string | Task ID — validate as numeric before use in URLs |
| `TAD_DISPLAY_NAME` | string | Task display name (preferred) |
| `NAME` | string | Task name (fallback — varies by BAW version) |
| `PT_NAME` | string | Process name |
| `TAD_DESCRIPTION` | string | Task description |
| `PRIORITY` | number | 10 (highest) to 50 (lowest) |
| `DUE` | string | ISO 8601 date-time |
| `STATE` | string | Prefixed with `State_` — strip prefix before display |
| `STATUS` | string | Alternative status field |

**Priority display:**

| Value | Label |
|---|---|
| 10 | Critical |
| 20 | High |
| 30 | Medium |
| 40 | Low |
| 50 | Very Low |

**State normalization** — strip `State_` prefix:

| Raw | Normalized |
|---|---|
| `State_claimed` | `claimed` |
| `State_ready` | `ready` |
| `State_received` | `received` |
| `State_finished` | `finished` — exclude from active list |
| `State_terminated` | `terminated` — exclude from active list |

---

## Task launch — T1.3

**Evidence:** VERIFIED

```
/teamworks/process.lsw?zWorkflowState=1&zTaskId={TKIID}&zResetContext=true
```

This URL opens the existing BAW task UI. Do not attempt to rebuild the task completion UI.

**Critical — task launch URL construction by profile:**

BAW sets `Content-Security-Policy: frame-ancestors 'self'` on all task form responses.
This means the iframe is only allowed when the browser considers the iframe URL **same-origin**
with the portal page. The URL pattern used to launch the task **must match the portal's hosting model**:

| Profile | Correct task launch URL pattern | Why |
|---|---|---|
| A / A2 — BAW-hosted CSHS | `/teamworks/process.lsw?...` (bare relative) | Portal is served from the BAW origin — relative URL resolves to BAW origin — same-origin ✅ |
| C — External portal via proxy | `{PROXY_BASE}/teamworks/process.lsw?...` (proxy-relative) | Proxy rewrites the path server-side; browser sees the portal origin — same-origin ✅ |
| C — External portal, direct (no proxy) | **iframe not possible without BAW CSP change** | Browser sends request to BAW origin directly — cross-origin — blocked by `frame-ancestors 'self'` ❌ |

**Never generate an absolute BAW origin URL (e.g. `https://baw-server:9443/teamworks/...`) for
the iframe `src` in an external portal.** The browser will see a cross-origin iframe and BAW's
`frame-ancestors 'self'` will block it regardless of authentication.

For Profile C with a proxy, `PROXY_BASE` is the prefix the proxy strips before forwarding to BAW
(e.g. `/baw` in the Vite dev proxy). In production it is whatever path prefix your reverse proxy
routes to BAW.

**Security requirements:**

- Validate `taskId` as numeric: `/^\d+$/.test(String(taskId))`
- Use `encodeURIComponent(taskId)` in the URL
- Hard-code the path to `/teamworks/process.lsw` — do not construct from arbitrary input
- Do not store `taskId` or task data in `localStorage`

**Iframe pattern:**

```html
<iframe id="taskFrame"
        title="Task form"
        allow="forms"
        style="width:100%;height:100%;border:0">
  <!-- src set programmatically; cleared to 'about:blank' on close -->
</iframe>
```

> **Deployment advisory:** The `sandbox` attribute has not been tested against BAW task forms.
> Apply only after confirming compatibility with the target deployment's `frame-ancestors` and CSP headers.
> See `references/quality-and-validation.md` §Task iframe security for the required TODO comment pattern.

---

## Team and group discovery — T2.6

**Evidence:** VERIFIED

| Endpoint | Purpose | Evidence |
|---|---|---|
| `GET /rest/bpm/wle/v1/managedGlobalTeams` | Global teams managed by current user — use for manager views | VERIFIED |
| `GET /rest/bpm/wle/v1/globalTeams` | All global teams visible to current user | VERIFIED |
| `GET /rest/bpm/wle/v1/globalTeamUsers/{id}` | Users in a global team | VERIFIED — 4 users returned for GeneralManagers team |
| `GET /rest/bpm/wle/v1/team/{teamId}` | Single modeled team by ID | VERIFIED — requires `snapshotId` param; accepts Process Designer modeled team IDs only, not runtime global team IDs (`24.xxx-...` format) |
| `GET /rest/bpm/wle/v1/team?name={teamName}` | Team by name | VERIFIED BY IBM DOCUMENTATION |
| `GET /rest/bpm/wle/v1/group/{groupNameOrID}` | User-registry group | VERIFIED BY IBM DOCUMENTATION |

**Do not use** `/rest/bpm/wle/v1/teams` (plural) — this endpoint does not exist.
Use `/rest/bpm/wle/v1/team/{teamId}` (singular) to look up a single modeled team by ID.
Modeled teams (Process Designer) differ from runtime global teams — do not pass a `globalTeamUsers` ID to the `team/{id}` endpoint.

---

## Manager and team dashboard APIs — T2.7–T2.12

**BAW version requirement:** Requires BAW 24+ with FDR (Federated Dashboard Repository) enabled. All four endpoints return HTTP 200. When FDR is disabled, all dashboard endpoints return HTTP 503 `CWTBG0788E`.

**FDR probe — RUNTIME CONFIRMED:**

There is no `isFDREnabled` REST field. Probe FDR availability at runtime by calling `GET /rest/bpm/wle/v2/dashboards/teamsummary`:
- HTTP 200 → FDR enabled, proceed with dashboard code
- HTTP 503 `CWTBG0788E` → FDR not enabled, show neutral empty state

Do not use a BAW version check to infer FDR status — a deployment may run a qualifying version without FDR enabled.

**Confirmed response shapes:**

| Endpoint | Top-level response key for results |
|---|---|
| `teamsummary` | `summaries[]` |
| `teammember/{teamId}` | `teamMemberList[]` |
| `teamtasktrend/{teamId}` | `data` |
| `teamtasks/{teamId}` PUT | `items[]` + `totalCount` |

### Non-federated WLE v2 dashboard endpoints

| Capability | Endpoint | Method |
|---|---|---|
| All teams summary | `GET /rest/bpm/wle/v2/dashboards/teamsummary` | GET |
| Single team summary | `GET /rest/bpm/wle/v2/dashboards/teamsummary/{teamId}` | GET |
| Team members workload | `GET /rest/bpm/wle/v2/dashboards/teammember/{teamId}` | GET |
| Single member workload | `GET /rest/bpm/wle/v2/dashboards/teammember/{teamId}/{username}` | GET |
| Team tasks | `PUT /rest/bpm/wle/v2/dashboards/teamtasks` or `PUT .../teamtasks/{teamId}` | PUT |
| Team task trend | `GET /rest/bpm/wle/v2/dashboards/teamtasktrend/{teamId}` | GET |

> The team tasks endpoint uses PUT with filter criteria in the body — not GET.
> **XSRF for WLE v2:** Session cookie (`withCredentials: true`) is sufficient — no `bpm-csrf-token` header. Do NOT carry any WLE v1 XSRF mechanism over to WLE v2.

**Authorization — RUNTIME CONFIRMED:**

BAW enforces dashboard authorization at the API level — no portal-side role check is needed:

- `teamsummary` returns only the teams the calling user manages. If the user manages no teams, BAW returns HTTP 400 `CWTBG0805E`.
- `teamsummary/{teamId}` returns HTTP 400 `CWTBG0806E` if the user does not manage that team.
- An executive or manager view is a **client-side rollup** across the teams returned by `teamsummary`. The API already scopes results to the caller's managed teams.
- Do not implement portal-side team filtering or role checks — BAW enforces visibility.

---

## Task search — T2.2–T2.5

**Evidence (T2.2, T2.3, T2.5):** VERIFIED
**Evidence (T2.4, saved search CRUD + UPDATE):** VERIFIED

| Capability | Endpoint | Method | Evidence |
|---|---|---|---|
| Ad hoc task search | `PUT /rest/bpm/wle/v1/tasks` | PUT | VERIFIED |
| Saved search list | `GET /rest/bpm/wle/v1/searches/tasks` | GET | VERIFIED |
| Saved search CREATE | `POST /rest/bpm/wle/v1/searches/tasks` | POST | VERIFIED |
| Saved search READ by name | `GET /rest/bpm/wle/v1/searches/tasks/{name}` | GET | VERIFIED |
| Saved search UPDATE by name | `PUT /rest/bpm/wle/v1/searches/tasks/{name}` | PUT | VERIFIED |
| Saved search DELETE by name | `DELETE /rest/bpm/wle/v1/searches/tasks/{name}` | DELETE | VERIFIED |
| Search actions | `GET /rest/bpm/wle/v1/searches/actions` | GET | VERIFIED |
| Search metadata — fields | `GET /rest/bpm/wle/v1/searches/tasks/meta/fields` | GET | VERIFIED |
| Search metadata — constraints | `GET /rest/bpm/wle/v1/searches/tasks/meta/constraintFields` | GET | VERIFIED |
| Search metadata — business data | `GET /rest/bpm/wle/v1/searches/tasks/meta/businessDataFields` | GET | VERIFIED |
| Advanced search (v2) | `POST /rest/bpm/wle/v2/search` | POST | Returns HTTP 503 when FDR is not enabled |

> **Search metadata paths on BAW 24+:** `/searches/tasks/meta/fields` and `/searches/tasks/meta/constraintFields` — the path `/searches/meta/fields` (without `/tasks/`) returns 404.
> **XSRF for WLE v1 saved searches:** Session cookie only — no `bpm-csrf-token` header required.

---

## Task mutations — T2.15–T2.17 (V2 scope)

**Evidence (claim, assign, update, finish):** VERIFIED
**Evidence (cancel):** VERIFIED — `action=cancel` behavior is **state-dependent**:
- On a **claimed** task: releases the claim (`cancelClaim`); task returns to `State_ready`. HTTP 200 with **empty body** (no JSON). Does **not** terminate the task.
- On a **ready/received** task: requires admin or instance-owner authority; a standard task owner receives `CWTBG0549E`. This is not a portal-level operation.

> **XSRF for WLE v1 mutations:** Session cookie (`credentials: 'same-origin'`) is sufficient — no `bpm-csrf-token` header required.
> **CP4BA:** Authenticate via `Authorization: Bearer <token>` — no XSRF cookie or header.

**Valid WLE v1 `action=` values** (verified by runtime testing):
`start`, `assign`, `setdata`, `update`, `finish`, `complete`, `claim`, `cancel`, `invite`, `getdata`

**`action=fail` does not exist in the WLE REST API** — do not generate code using it.

| Capability | Endpoint | Notes | Evidence |
|---|---|---|---|
| Task claim | `PUT /rest/bpm/wle/v1/task/{taskId}?action=claim` | | VERIFIED |
| Task assignment | `PUT /rest/bpm/wle/v1/task/{taskId}?action=assign` | Exactly one of: `&toMe=true`, `&back=true`, `&toUser={u}`, `&toGroup={g}`, `&toTeam={t}` | VERIFIED  (`&back=true` confirmed) |
| Task update (due date / priority) | `PUT /rest/bpm/wle/v1/task/{taskId}?action=update` | `&priority={10\|20\|30\|40\|50}` | VERIFIED |
| Task finish/complete | `PUT /rest/bpm/wle/v1/task/{taskId}?action=finish` | `action=complete` is a server-side alias. Requires task-specific output variable schema. | VERIFIED |
| Task release (cancel claim) | `PUT /rest/bpm/wle/v1/task/{taskId}?action=cancel` | On a **claimed** task only: releases the claim; task returns to `State_ready`. HTTP 200 with empty body. Standard task owner cannot cancel a ready/received task (`CWTBG0549E`). | VERIFIED |

> Session cookie (`credentials: same-origin`) is sufficient for WLE v1 mutations in a same-origin browser portal. No `bpm-csrf-token` header required. See XSRF note in the Task mutations section above.

---

## Process launch — T2.18–T2.19 (V2 scope)

**Evidence (T2.18 /exposed and T2.19 process start):** VERIFIED

| Capability | Endpoint | Evidence |
|---|---|---|
| Launchable items (NF) | `GET /rest/bpm/wle/v1/exposed` | VERIFIED |
| Start process | `POST /rest/bpm/wle/v1/process?action=start&bpdId={bpdId}&processAppId={processAppId}` | VERIFIED |

**`/exposed` response shape — confirmed field names (live BAW):**

| Field | Notes |
|---|---|
| `data.exposedItemsList[]` | Array of launchable items |
| `itemID` | Compound ID (`<version>.<uuid>`). **Do not use directly** — the correct `bpdId` value must be read from `startURL` (see below). |
| `processAppID` | Compound ID (`<version>.<uuid>`). **Do not use as `processAppId`** — the UUID is not the value BAW's `action=start` accepts. Read `processAppId` from `startURL` instead. |
| `snapshotID` | Present in the response. **Must not be passed** to `action=start` — BAW returns `CWTBG0012E: The parameter 'snapshotId' is invalid` even with a valid value. Omit entirely; BAW uses the current default snapshot. |
| `startURL` | **Canonical source for launch parameters.** Parse `bpdId` and `processAppId` from this URL's query string — these are the exact values BAW's REST API accepts. |
| `processAppAcronym` | Short process app identifier (e.g. `"HSS"`). Use as `processAppId` fallback only if `startURL` is absent. |
| `type` | `"process"`, `"service"`, `"url"` — filter to `"process"` for process launch |
| `display` / `title` | Display name for the process |

> **VERIFIED launch pattern — use `startURL` as the parameter source:**
> Parse the `startURL` field from each `/exposed` item using `new URL(item.startURL, 'https://x')`.
> Extract `bpdId` and `processAppId` from its query string and POST them to `action=start`.
> This is the only approach confirmed to work — constructing the parameters from `itemID`, `processAppID`,
> or `snapshotID` alone fails with HTTP 409 or HTTP 400 (`CWTBG0012E`) at runtime.
>
> **What fails (do not generate):**
> - Passing `itemID` directly as `bpdId` → HTTP 409
> - Passing stripped `processAppID` UUID as `processAppId` → HTTP 400 `CWTBG0012E: projectId invalid`
> - Passing any `snapshotId` value → HTTP 400 `CWTBG0012E: snapshotId invalid`
>
> Do not use `/rest/bpm/wle/v1/launchableEntities` — that is the federated path.

**Live process start response fields:**

| Field | Notes |
|---|---|
| `data.piid` | Process instance ID for the started process |
| `data.tasks[0].tkiid` | Task ID of the first (auto-created) task — may already be `STATE_CLAIMED` |
| `data.state` | Process state — e.g. `STATE_RUNNING` |

---

## XSRF / CSRF for WLE REST mutations

**For same-origin browser portals hosted on BAW:**
Session cookie (`credentials: 'same-origin'` / `withCredentials: true`) is sufficient for all WLE v1, v2, and PFS mutations. No `bpm-csrf-token` header is required. Do not generate portal code that adds or manages this header.

`BPMCSRFToken` (JWT from `POST /rest/bpm/std/system/login`) is only needed when calling the BPM standard API (`/rest/bpm/std/`) — a separate surface unrelated to WLE REST.

**CP4BA:** Authenticate via `Authorization: Bearer <token>`. No XSRF cookie or header of any kind required.

---

## Security rules for all generated non-federated code

1. All API response values rendered via `textContent`, DOM property assignment, or `escHtml()`.
2. No `localStorage` for task IDs, task data, or process data — in-memory session state only.
3. No `eval()`, no `document.write()`.
4. No console logging of full API payloads — they may contain PII.
5. In-flight guard: return early if a fetch is already in progress.
6. Validate `taskId` as numeric before URL construction.
7. XSRF: Use `credentials: 'same-origin'` (or `withCredentials: true`) for all BAW API calls. Do not generate code that adds or manages `bpm-csrf-token`.

---

## Data freshness pattern (reference implementation)

The approved reference implementation uses a polling + fingerprint + staleness model:

| Constant | Default | Purpose |
|---|---|---|
| `POLL_INTERVAL` | 60 000 ms | Background silent refresh interval |
| `STALE_THRESHOLD` | 5 min | After this duration, show staleness indicator |

Fingerprint computed from the serialized task list. DOM updated only when the fingerprint changes.
Visibility-aware: silent refresh fires on tab re-focus. Modal close triggers a silent refresh.
