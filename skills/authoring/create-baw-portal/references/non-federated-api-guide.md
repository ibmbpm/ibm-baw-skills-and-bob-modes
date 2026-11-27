# Non-Federated API Guide

> **Skill:** `create-baw-portal`
> **Purpose:** Implementation-ready guidance for non-federated Business Automation Workflow (WLE REST API).

---

## Authentication

Non-federated Business Automation Workflow portals hosted at the same origin as the Business Automation Workflow server use the existing authenticated browser session.

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

## Current user

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

All six fields above were observed in the `parts=all` response on the tested Business Automation Workflow instance.
Always request `parts=all` — the default `parts` response omits email, managerName, and jobTitle.
Generate initials from the first letter of each word in `fullName`.
Do not persist user data in `localStorage`.

---

## Personal task list

**Endpoint depends on server configuration:**

| Scenario | Endpoint | Notes |
|---|---|---|
| Standard Business Automation Workflow / Cloud Pak for Business Automation (most servers) | `GET /rest/bpm/wle/v1/tasks?interaction=claimed_and_available&size=500&offset=0` | Documented WLE v1 endpoint — use this by default |
| Server whose `GET /tasks` returns a verified missing-default-search 404 (see [404 classification](#404-classification-for-get-tasks)) | `PUT /rest/bpm/wle/v1/tasks` with `SavedSearchDefinition` body | The server requires a named saved search that doesn't exist; PUT is used only after that classification, and the decision is cached per session and Business Automation Workflow environment |

> **Deployment note:** On some Business Automation Workflow deployments, `GET /tasks` returns HTTP 404 because the server
> requires a named saved search that does not exist. `PUT /tasks` returns HTTP 200 on those servers.
> Do not assume PUT is universally required — other Business Automation Workflow deployments use GET successfully.

### 404 classification for GET /tasks

Not every 404 is a missing-default-search response. A 404 is classified as the PUT-fallback trigger only when **all** of the following hold:

1. the request was `GET /rest/bpm/wle/v1/tasks` (not a task detail, action or saved-search call);
2. the body parses as Business Automation Workflow's JSON error envelope (a JSON object with a `Data` member) — a Business Automation Workflow application answered, as opposed to a proxy, gateway, wrong context root or static host;
3. the follow-up `PUT /tasks` returns 200 with a usable result envelope.

Any other 404 (empty or non-JSON body, HTML, proxy error) is surfaced as an error and never triggers PUT or caching. 400, 401, 403, 408, 5xx and network errors are never treated as this condition. The Business Automation Workflow JSON-body test is a skill heuristic derived from the observed deployment; it is not stated in IBM documentation. The session-and-environment caching behaviour is owned by the [task-lifecycle playbook](playbooks/task-lifecycle.md#42-task-list-strategy-cache-session-and-environment-scope).

**`PUT /tasks` body (Workplace-observed; use after the 404 classification above):**

```
PUT /rest/bpm/wle/v1/tasks
Content-Type: application/json

{
  "size": 500,
  "interaction": "claimed_and_available",
  "organization": "byTask",
  "fields": ["taskId","taskSubject","taskStatus","taskPriority","taskDueDate","taskIsAtRisk","bpdName","taskActivityName"],
  "conditions": [{ "field": "taskActivityType", "operator": "Equals", "value": "USER_TASK" }],
  "sort": [{ "field": "taskDueDate", "order": "ASC" }]
}
```

> **Note:** The full Workplace body also includes `"id":0`, `"name":""`, `"shared":false`, `"teams":[]`, `"aliases":[]`. These are optional — the server accepts the body without them.

**`interaction` values — critical distinction (observed in Workplace traffic):**

| Value | Semantics | When to use |
|---|---|---|
| `"claimed"` | Tasks the user has actively claimed only | Workplace default task list — shows the user's in-progress work |
| `"claimed_and_available"` | Claimed tasks plus tasks available to claim (ready/received) | Broader inbox view — shows everything the user could work on |

Workplace's own default full-load uses
`"claimed"`. Use `"claimed_and_available"` for an inbox-style portal (shows all actionable tasks).
Use `"claimed"` to replicate Workplace's exact default view (claimed tasks only).
Do not use `filterByCurrentUser=true` and `includeAllBusiness=true` — different semantics and
`includeAllBusiness=true` is not confirmed in the IBM endpoint specification.

**`organization` field — Workplace-observed:**

Workplace sends `"organization": "byTask"` on every `PUT /tasks` call. This field is part of the
`SavedSearchDefinition` schema. The value `"byTask"` groups results by task (the standard view).
Include `"organization": "byTask"` in generated `PUT /tasks` bodies to match Workplace behavior.

**Stats — server vs client:**

`data.stats` may be `null` on some deployments. **Always compute stats
client-side from `data.items`.** Do not depend on `data.stats` being populated.

The `calcStats=true` query parameter and the stats-only `size=0` pattern appear in
Workplace network traffic but have not been confirmed to work on all deployments.
Do not generate code that requires `data.stats` to be non-null.

**`taskActivityType` condition — required to exclude system tasks (runtime-verified):**

Workplace adds this condition when the task list is filtered or paged to restrict results to
human tasks only. Generated portals that omit this condition may include system tasks:

```json
{ "field": "taskActivityType", "operator": "Equals", "value": "USER_TASK" }
```

Include this condition in the `conditions` array for any portal task list intended for human tasks only.

**Condition `operator` — documented values (documentation-verified):**

| Operator | Meaning |
|---|---|
| `"Equals"` | Exact match |
| `"NotEquals"` | Excludes exact match |
| `"Contains"` | Substring match |
| `"StartsWith"` | Prefix match |
| `"LessThan"` | Numeric or date less-than |
| `"GreaterThan"` | Numeric or date greater-than |
| `"FullTextSearch"` | Full-text search across indexed fields |

Use only these values in the `operator` field of any `conditions` entry. **`"LIKE"` is not a documented operator** — do not use it; it will cause a server error on standard deployments.

**Free-text search — target field not established.** No document or test in this skill identifies which `field` a `"FullTextSearch"` condition should target, or the value format. IBM documents only that a search metadata field can carry a `full_text_searchable` attribute (`GET /rest/bpm/wle/v1/searches/tasks/meta/fields`); that attribute and any `FullTextSearch` request were not runtime-verified here. Do not invent a field name, operator or value format. Either (a) build the condition only from a field the target deployment's metadata response marks `full_text_searchable`, labelled documentation-verified only and unverified at runtime, or (b) filter the already-loaded page client-side, labelled as a client-only filter, never saved as a saved search and never described as a server-side search.

**Official response structure:**

```
status
data
data.items        ← task list (may be [] or null on zero results — see below)
data.totalCount   ← total matching tasks (paging contract) — observed present
data.offset       ← current page offset
data.size         ← page size returned
data.stats        ← null on the tested server; may be populated on other deployments
data.attributeInfo ← field metadata (present on some deployments)
```

**Empty search results and null `items`:**

A successful search with no matching tasks may return `data.items: []` (empty array) or `data.items: null`.
Both are accepted as a legitimate empty result **only when** `data` is present and `data.totalCount` is `0`
(or `data.status` or `json.status` is `"200"`).

> **Do not interpret `items: null` with `totalCount > 0` as a normal empty result.** A `null` items
> array paired with a positive `totalCount` indicates a malformed envelope — surface it as an error.

```js
function parseSearchResponse(json) {
  // Must have a recognisable data envelope.
  if (!json || typeof json.data !== 'object') {
    throw new Error('Unexpected search response: no data envelope');
  }
  const items = json.data.items;
  const total = json.data.totalCount ?? 0;

  if (items === null || items === undefined) {
    // null/missing items is acceptable only as an empty result (totalCount = 0).
    if (total > 0) {
      throw new Error(
        `Malformed search response: items is null/missing but totalCount is ${total}`
      );
    }
    return { tasks: [], totalCount: 0 };
  }
  if (!Array.isArray(items)) {
    throw new Error('Unexpected search response: data.items is not an array');
  }
  return { tasks: items.map(normaliseTask), totalCount: total };
}
```

**Defensive extraction — always normalise at the boundary:**

```js
function extractTasks(json) {
  let arr;
  if (Array.isArray(json))             arr = json;
  else if (Array.isArray(json.items))       arr = json.items;
  else if (Array.isArray(json.data?.items)) arr = json.data.items;
  else if (json.data?.items === null && (json.data.totalCount ?? 0) === 0) arr = [];  // null items, zero count
  else if (Array.isArray(json.data))        arr = json.data;
  else arr = [];
  return arr.map(normaliseTask);   // always normalise — see field name note below
}
```

> **Zero-result case vs malformed envelope.** `extractTasks` returns `[]` for both zero results and
> for unrecognised envelopes. For cases where the distinction matters (e.g. telemetry, error reporting),
> use `parseSearchResponse` instead, which distinguishes zero-results from unrecognised shapes.

**Field name normalisation — required:**

Output field names in `PUT /tasks` response items depend on which input field aliases were
requested:

| Input alias (in `fields` array) | Output field name in response item |
|---|---|
| `taskId` | `TKIID` (bare uppercase) — **and** `TASK.TKIID` also present as duplicate |
| `taskSubject` | `TAD_DISPLAY_NAME` |
| `taskStatus` | `STATUS` (human-readable: `"Received"`, `"Claimed"`) |
| `taskPriority` | `PRIORITY` (numeric: `30`) |
| `taskDueDate` | `DUE` (ISO 8601) |
| `taskIsAtRisk` | `IS_AT_RISK` (boolean) |
| `bpdName` | `PT_NAME` — **Workplace label: "Workflow definition"** |
| `taskActivityName` | `NAME` (task activity name — fallback display name) |
| `taskAtRiskTime` | `AT_RISK_TIME` |
| `taskOwner` | `OWNER` |
| `teamName` | team name field |
| `taskCreatedDate` | created date |
| `taskAssignedDate` | assigned date |
| `taskCompletionDate` | completion date |
| `piid` | `PROCESS_INSTANCE.PIID` |
| `workflowStatus` | workflow state |
| `processAppAcronym` | process app short ID |
| `taskActivityType` | `ACTIVITY_TYPE` — use in `conditions`, not `fields` |

> **`processName` is NOT a valid alias** — causes `CWTBG0612E` (runtime-verified). Use `bpdName` for the process/workflow name column.

> **Saved Search Database Column Normalization:** When loading or executing saved searches from Business Automation Workflow, stored definitions may contain raw database column identifiers instead of search aliases. Normalize them to canonical aliases before execution or display: `TASK.TAD_DISPLAY_NAME` → `taskSubject`, `TASK.DUE` → `taskDueDate`, `TASK.PRIORITY` → `taskPriority`, `TASK.STATUS` → `taskStatus`, `TASK.AT_RISK_TIME` → `taskAtRiskTime`, `PROCESS_TYPE.NAME` → `bpdName`, `TASK.ACTIVITY_NAME` → `taskActivityName`, `TASK.TKIID` → `taskId`. Unsupported aliases (e.g. `taskOwner`, `piid`) must be rejected or filtered rather than guessed.

> **`STATE` vs `STATUS`:** `STATE` (e.g. `STATE_CLAIMED`, `STATE_READY`) and `STATUS`
> (e.g. `"Claimed"`, `"Received"`) are both present. `STATE` requires prefix-stripping;
> `STATUS` is already human-readable. Use `STATE` for logic (canClaim/canRelease checks);
> use `STATUS` for display if preferred.

Always normalise at the extract boundary — **check bare uppercase first**:

```js
function normaliseTask(t) {
  // Bare uppercase is the canonical form. TASK.TKIID also present as duplicate — check bare first.
  // STATE values: STATE_CLAIMED, STATE_READY, STATE_RECEIVED — strip STATE_ prefix.
  return {
    TKIID:            t.TKIID            ?? t['TASK.TKIID'] ?? '',
    TAD_DISPLAY_NAME: t.TAD_DISPLAY_NAME ?? t.NAME          ?? '',
    PT_NAME:          t.PT_NAME          ?? '',
    PRIORITY:         t.PRIORITY         ?? '',
    DUE:              t.DUE              ?? '',
    STATE:            t.STATE            ?? t.STATUS        ?? '',
    IS_AT_RISK:       t.IS_AT_RISK       ?? false,
    _raw:             t,
  };
}
```

**`PRIORITY` is returned as a string in some Business Automation Workflow versions** — always coerce with `Number(p)` before the lookup map. The numeric-to-label mapping is owned by [§Task priority](#task-priority--values-and-labels-owner); the map below must match that table (checked by `scripts/validate-capabilities.test.mjs`). Unknown or missing values display the plain word "Unspecified" — a raw numeric code is never shown to the user:

<!-- snippet: priorityLabel -->
```js
function priorityLabel(p) {
  const labels = { 10: 'Very high', 20: 'High', 30: 'Normal', 40: 'Low', 50: 'Very low' };
  const usable = typeof p === 'number' || (typeof p === 'string' && p.trim() !== '');
  return (usable && labels[Number(p)]) || 'Unspecified';
}
```

**`size=500` means up to 500 tasks — not all tasks.** When `totalCount` in the response exceeds
the number of returned items, additional pages exist. Page with `offset` incremented by `size`.
The paging contract (`totalCount`, `offset`, `size`) is documented by IBM.

**Truncation indicator (required in generated UI):** When `totalCount` exceeds the number of items
returned in the current page, surface a visible indicator to the user — for example:
_"Showing 500 of 1,243 tasks. Use pagination to view more."_
Do not silently discard the overflow. Do not present a partial list as if it were complete.

**Task response fields:**

| Field | Type | Notes |
|---|---|---|
| `TKIID` | string | Task ID — numeric string (traditional Business Automation Workflow) or UUID string (Cloud Pak for Business Automation); treat as an opaque identifier, guard with truthiness and `encodeURIComponent` (see Task launch) |
| `TAD_DISPLAY_NAME` | string | Task display name (preferred) |
| `NAME` | string | Task name (fallback — varies by Business Automation Workflow version) |
| `PT_NAME` | string | Process name |
| `TAD_DESCRIPTION` | string | Task description |
| `PRIORITY` | number | 10 (highest) to 50 (lowest) |
| `DUE` | string | ISO 8601 date-time |
| `IS_AT_RISK` | boolean | `true` when task is within the at-risk window |
| `STATE` | string | Prefixed with `STATE_` (uppercase) — strip prefix before display |
| `STATUS` | string | Human-readable alternative to STATE (`"Claimed"`, `"Received"` etc.) |

**Priority display:** `PRIORITY` is `10` (highest) to `50` (lowest). The label for each value is owned by [§Task priority](#task-priority--values-and-labels-owner) — do not restate the mapping elsewhere.

**State normalization** — strip `STATE_` prefix (uppercase, runtime-verified):

```js
return String(s || '').replace(/^STATE_/i, '').toLowerCase();
```

| Raw (observed) | Normalised |
|---|---|
| `STATE_CLAIMED` | `claimed` |
| `STATE_READY` | `ready` |
| `STATE_RECEIVED` | `received` |
| `STATE_FINISHED` | `finished` — exclude from active list |
| `STATE_TERMINATED` | `terminated` — exclude from active list |

---

## Task launch

```
/teamworks/process.lsw?zWorkflowState=1&zTaskId={TKIID}&zResetContext=true
```

> **TKIID format:** Business Automation Workflow can return TKIIDs as either numeric strings (traditional Business Automation Workflow) or UUID strings (Cloud Pak for Business Automation / Business Automation Workflow on containers). Do **not** validate `taskId` with `isNaN(Number(...))` or `/^\d+$/` — this blocks UUID-format IDs. The only required guard is a truthiness check (`if (!taskId) return`).

This URL opens the existing Business Automation Workflow task UI. Do not attempt to rebuild the task completion UI.

**Critical — task launch URL construction by profile:**

The URL pattern **must match the portal's hosting model**. The iframe / `frame-ancestors` / HTTPS /
reverse-proxy prerequisites are owned by [`hosting-and-generation.md`](hosting-and-generation.md) — this table
states only the minimum:

| Profile | Task launch URL pattern | Iframe? |
|---|---|---|
| A / A2 — CSHS hosted on Business Automation Workflow | `/teamworks/process.lsw?...` (bare relative) | Yes — the portal is served from the Business Automation Workflow origin (same-origin) |
| C — External portal | Hosting prerequisites must be confirmed (see `hosting-and-generation.md`: portal origin in `frame-ancestors` **and** HTTPS same-site) | Caution: only when both prerequisites are confirmed; otherwise use `window.open` / a new tab |

A reverse proxy path prefix (`{PROXY_BASE}`) does **not** by itself make the task form embeddable
(see `hosting-and-generation.md`). Do not describe a proxy as making the task form "same-origin".

**Never generate an absolute Business Automation Workflow origin URL (e.g. `https://baw-server:9443/teamworks/...`) for
the iframe `src` in an external portal** unless the prerequisites above are confirmed.

**Security requirements:**

- Take `taskId` only from a Business Automation Workflow API response (`TKIID`), never from free-text user input. Treat it as an opaque identifier: truthiness check only (`if (!taskId) return`); do not require numeric-only format — UUID-format TKIIDs are valid. Business Automation Workflow remains authoritative for whether the ID exists and is accessible.
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

> **Deployment advisory:** The `sandbox` attribute has not been tested against Business Automation Workflow task forms.
> Apply only after confirming compatibility with the target deployment's `frame-ancestors` and CSP headers.
> Generated code leaves a TODO comment noting that the iframe `sandbox` attribute is pending deployment validation (test it with Business Automation Workflow task forms before enabling); see [Quality requirements (every UI)](hosting-and-generation.md#quality-requirements-every-ui).

---

## Team and group discovery

| Endpoint | Purpose |
|---|---|
| `GET /rest/bpm/wle/v1/managedGlobalTeams` | Global teams managed by current user — use for manager views |
| `GET /rest/bpm/wle/v1/globalTeams` | All global teams visible to current user |
| `GET /rest/bpm/wle/v1/globalTeamUsers/{id}` | Users in a global team |
| `GET /rest/bpm/wle/v1/team/{teamId}` | Single modeled team by ID — requires `snapshotId` param; accepts Process Designer modeled team IDs only, not runtime global team IDs (`24.xxx-...` format) |
| `GET /rest/bpm/wle/v1/team?name={teamName}` | Team by name (IBM documented) |
| `GET /rest/bpm/wle/v1/group/{groupNameOrID}` | User-registry group (IBM documented) |

**Do not use** `/rest/bpm/wle/v1/teams` (plural) — this endpoint does not exist.
Use `/rest/bpm/wle/v1/team/{teamId}` (singular, IBM documented) to look up a single modeled team by ID.
Modeled teams (Process Designer) differ from runtime global teams — do not pass a `globalTeamUsers` ID to the `team/{id}` endpoint.

---

## Manager and team dashboard APIs

**Business Automation Workflow version requirement:** The v2 dashboards are documented for Business Automation Workflow 24+ and depend on FDR (Federated Data Repository) being enabled. A version number alone never proves FDR status.

**FDR detection — four outcome classes.** There is no `isFDREnabled` REST field and no dedicated FDR-status operation. The decision contract is owned by the catalog (`CAP-ADV-SEARCH-NF` `_strategyNote`, conflict C05) and the intent map (`INT-TEAM-WORKLOAD` `fdrGate`); this section summarizes it:

| Class | Request / signal | Meaning |
|---|---|---|
| Supported positive probe | `GET /rest/bpm/wle/v2/search/queries` (`NF-ADV-QUERIES-LIST`; documentation-verified; does not depend on team management) → HTTP 2xx | FDR-backed v2 endpoints are reachable. Preferred probe. |
| Secondary diagnostic request | `GET /rest/bpm/wle/v2/dashboards/teamsummary` (`NF-DASHBOARD-TEAMSUMMARY-ALL`) → HTTP 2xx | FDR-backed v2 endpoints are reachable. Depends on the caller managing teams, so a failure here is weaker evidence. |
| Confirmed error behavior (version-specific) | HTTP 503 with message ID `CWTBG0788E` on a dashboard endpoint | Product-code inspection of one development build (Business Automation Workflow 8.6.11.26000; remediation record no longer retained) shows `DashboardService.checkBPDIndexingEnabled()` throws `FederatedDataRepositoryDisabledException` (HTTP 503, `CWTBG0788E`) unless `federatedIndexEnabled \|\| fdrIndexEnabled`. Do not generalize this to other Business Automation Workflow versions. The mapping was not tested on a known FDR-disabled environment elsewhere and is not in IBM documentation; treat 503/`CWTBG0788E` as a project-observed association and show a neutral empty state only for that signal. |
| Inconclusive | HTTP 400 (including `CWTBG0805E` when the caller manages no teams), 401/403, 404, 408, other 5xx, CORS/proxy failure, network error, timeout | Not evidence that FDR is disabled. Do not report FDR disabled; re-probe later. |

Cache the result per environment. Do not use a Business Automation Workflow version check to infer FDR status.

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
> **CSRF/XSRF for WLE v2:** the WLE v1 legacy `XSRF-TOKEN` cookie check is scoped to `/rest/bpm/wle/v1/*`; do not assume the WLE v1 mechanism applies to v2. The v2 requirement is verification-required — see [XSRF / CSRF for WLE REST mutations](#xsrf--csrf-for-wle-rest-mutations). Dashboard `PUT` calls carry filter bodies and do not change task state.

**Authorization:**

Business Automation Workflow enforces dashboard authorization at the API level — no portal-side role check is needed:

- `teamsummary` returns only the teams the calling user manages. If the user manages no teams, Business Automation Workflow returns HTTP 400 `CWTBG0805E`.
- `teamsummary/{teamId}` returns HTTP 400 `CWTBG0806E` if the user does not manage that team.
- An executive or manager view is a **client-side rollup** across the teams returned by `teamsummary`. The API already scopes results to the caller's managed teams.
- Do not implement portal-side team filtering or role checks — Business Automation Workflow enforces visibility.

---

## Task search

| Capability | Endpoint | Method |
|---|---|---|
| Ad hoc task search | `PUT /rest/bpm/wle/v1/tasks` | PUT |
| Saved search list | `GET /rest/bpm/wle/v1/searches/tasks` | GET |
| Saved search CREATE | `POST /rest/bpm/wle/v1/searches/tasks` | POST |
| Saved search READ by name or ID | `GET /rest/bpm/wle/v1/searches/tasks/{nameOrId}` | GET |
| Saved search UPDATE **by numeric ID** | `PUT /rest/bpm/wle/v1/searches/tasks/{id}` | PUT |
| Saved search DELETE by name or ID | `DELETE /rest/bpm/wle/v1/searches/tasks/{nameOrId}` | DELETE |
| Search actions | `GET /rest/bpm/wle/v1/searches/actions` | GET |
| Search metadata — fields | `GET /rest/bpm/wle/v1/searches/tasks/meta/fields` | GET |
| Search metadata — constraints | `GET /rest/bpm/wle/v1/searches/tasks/meta/constraintFields` | GET |
| Search metadata — business data | `GET /rest/bpm/wle/v1/searches/tasks/meta/businessDataFields` | GET |
| Advanced search (v2) | `POST /rest/bpm/wle/v2/search` | POST — returns HTTP 503 when FDR is not enabled |

> **Saved searches are addressed by numeric `id`:**
> `GET /searches/tasks` returns each definition with an `"id"` field (string e.g. `"1102"`).
> Workplace uses this numeric ID for all subsequent GET, PUT, and DELETE calls.
> Always store the `id` from the list response and prefer it over name-based addressing for mutations.
> Name-based addressing (`/searches/tasks/Completed`) still works but is not the Workplace pattern.

> **Search metadata paths on Business Automation Workflow 24+:** `/searches/tasks/meta/fields` and `/searches/tasks/meta/constraintFields` — the path `/searches/meta/fields` (without `/tasks/`) returns 404.
> **CSRF/XSRF for WLE v1 saved-search mutations:** see [XSRF / CSRF for WLE REST mutations](#xsrf--csrf-for-wle-rest-mutations).

> **Confirmed `SavedSearchDefinition` body fields:**
> `size: 500`, `aliases: []`, `teams: []`, `id: <numeric>`, `organization: "byTask"`, `shared: false`.
> Recommended `fields` array: `["taskId","taskSubject","taskPriority","taskDueDate","taskStatus","bpdName","taskAtRiskTime","taskActivityType"]`.
> Default sort: `[{field:"taskDueDate", order:"ASC"}]`.

> **`POST /searches/tasks` HTTP status (Cloud Pak for Business Automation 26.0.3 SP20 r2; single-deployment live observation, no retained artifact):**
> Returns **HTTP 201** (Created) on Cloud Pak for Business Automation 26.0.3 SP20 r2 — not 200.
> Accept both `201` and `200` as success. Do not use `=== 200` as the sole success check.
> The response body contains the created definition under `data` with the server-assigned
> `id` (numeric string) and server-set `owner`. No server-generated timestamps or extra keys
> are added — the 12 submitted fields are returned as-is (observed on that deployment).

> **`PUT /searches/tasks/{id}` HTTP status and body contract (Cloud Pak for Business Automation 26.0.3 SP20 r2; single-deployment live observation, no retained artifact):**
> Returns **HTTP 200** with the updated definition. When the PUT body is complete (all 12 fields),
> every field is preserved — only the changed field differs in the subsequent GET (observed in a
> rename-only test).
> **Always send a complete PUT body:** fetch the full definition first with
> `GET /searches/tasks/{id}`, change only the intended fields, and include all others verbatim.
> Whether a partial PUT body would drop omitted fields (full-replacement) or retain them
> (merge/patch) has not been independently demonstrated and is **not safe to assume either way**.

> **`DELETE /searches/tasks/{id}` HTTP status and response body (Cloud Pak for Business Automation 26.0.3 SP20 r2; single-deployment live observation, no retained artifact):**
> Returns **HTTP 204** (No Content) with an empty response body on Cloud Pak for Business Automation 26.0.3 SP20 r2
> (observed on that deployment). HTTP 200 may be returned on other deployments
> but was not observed in this test. Accept 200 or 204 as success.
> **Do not call `response.json()` unconditionally after DELETE** — a 204 response carries no
> body; calling `.json()` throws a parse error. Check `response.ok` (or status 200–204) first,
> then skip body parsing. A subsequent GET returns HTTP 404 confirming removal.

### GET /searches/tasks response shape

Authoritative envelope: `json.data.definitions[]`, each item `{id, name, owner, organization, shared}`.

| Source | Verification level |
|---|---|
| IBM *Saved Search Definitions Resource – GET* (Cloud Pak for Business Automation or Business Automation Workflow 25.0.0, `topic=ssd-get`) documents `{"status":"200","data":{"definitions":[…]}}` | documentation-verified |
| Live observation of `data.definitions[]` on Cloud Pak for Business Automation or Business Automation Workflow 24+ | observed; raw response not retained, so not independently re-verifiable |
| `json.data.searches[]`, `json.searches[]` | **unverified** — appear in older example code only; not found in the IBM documentation reviewed |

An empty `definitions` array is a valid empty list. A response with **no** recognised array is an
error — surface it; never map it to "no saved searches".

```js
function parseSavedSearchList(json) {
  const list = json?.data?.definitions;
  if (!Array.isArray(list)) throw new Error('Unexpected saved-search list response: data.definitions[] not found');
  return list;
}
```

If a target deployment is observed to return a different envelope, record that observation for that
deployment and add an explicit, named branch for it. Do not add silent fallbacks. Do not use
`json.data` itself as the list — it is an object.

### Running a saved search — two-step pattern

`GET /searches/tasks/{name}` returns the saved search **definition** (criteria, conditions, sort). It does **not** return task results. To execute the search:

1. `GET /rest/bpm/wle/v1/searches/tasks/{name}` → extract criteria from `json.data` using structural validation (GET-by-id live-observed shape; IBM-documented example agrees — see evidence table)
2. `PUT /rest/bpm/wle/v1/tasks` with the criteria as a `SavedSearchDefinition` body → returns `items[]` task results

| Source | Verification level |
|---|---|
| Live response: definition directly in `data` (observed on Cloud Pak for Business Automation 26.0.3 SP20 r2) | `structural-assertion-verified` |
| IBM *Saved Search Definition Resource – GET* (Cloud Pak for Business Automation or Business Automation Workflow 25.0.0, `topic=definition-get`) shows the definition directly in `data` in its JSON example | documentation-verified (example only; no response schema asserted) |
| Previously documented `data.search` envelope | not observed in live test; must not be silently accepted |

```js
// Step 1 — fetch definition
const defJson  = await apiFetch(`/rest/bpm/wle/v1/searches/tasks/${encodeURIComponent(name)}`);
// GET-by-id live-observed shape: definition in data (CP4BA 26.0.3 SP20 r2).
// Structural validation — must have at least one known SavedSearchDefinition field.
const DEF_FIELDS = new Set(['name','interaction','size','shared','fields','sort',
                             'conditions','owner','teams','id','aliases','organization']);
const criteria = defJson?.data;
if (!criteria || typeof criteria !== 'object' || !Object.keys(criteria).some(k => DEF_FIELDS.has(k))) {
  throw new Error(
    'Unexpected saved-search definition response'
    + (defJson?.data?.search ? ' (found data.search — expected definition in data)' : '')
  );
}

// Step 2 — execute as ad hoc search with explicit fields list.
// fields:[] returns only TASK.TKIID/PROCESS_INSTANCE.PIID/KIND (observed on CP4BA 26.0.0).
// Always provide an explicit list of the aliases needed for display.
const body = JSON.stringify({
  interaction:  criteria.interaction || 'claimed_and_available',
  size:         criteria.size        || 25,
  organization: 'byTask',
  fields:       ['taskId', 'taskSubject', 'taskStatus', 'taskPriority', 'taskDueDate', 'taskAtRiskTime', 'bpdName'],
  sort:         criteria.sort        || [{ field: 'taskId', order: 'ASC' }],
  conditions:   criteria.conditions?.length
    ? criteria.conditions
    : [{ field: 'taskActivityType', operator: 'Equals', value: 'USER_TASK' }],
});
const searchJson = await apiFetch('/rest/bpm/wle/v1/tasks', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body,
});
const tasks = extractTasks(searchJson);
```

Calling `extractTasks()` directly on the definition response always returns `[]` — there are no task items in a search definition object.

### How the Workplace toolkit runs saved searches

The Business Automation Workflow Workplace toolkit uses the following two-step pattern:

1. **Saved searches are identified by numeric `ID`**, not by name.

2. The toolkit calls `GET /searches/tasks/{id}`, then extracts `interaction`, `conditions`, `fields`, and `sort` from `data` (the definition object — see §Running a saved search for the evidence table).

3. **There is no separate "run saved search" endpoint** — Business Automation Workflow always executes saved search criteria as an ad-hoc `PUT /tasks` body.

4. **`fields` in the stored definition = display column preferences**, not a search filter restriction. For non-FDR environments, `"taskAtRiskTime"` and `"taskStatus"` are always appended. Note: `taskStatus` may appear twice in Workplace requests — this is harmless.

   **Critical — `fields: []` does NOT return all fields.** Sending `fields: []` returns only `TASK.TKIID`, `PROCESS_INSTANCE.PIID`, and `KIND` — all display fields (`taskSubject`, `taskPriority`, `taskDueDate`, `taskStatus`) are absent. Always provide an explicit fields list:
   ```
   fields: ['taskId', 'taskSubject', 'taskStatus', 'taskPriority', 'taskDueDate', 'taskAtRiskTime', 'bpdName', 'taskActivityName']
   ```
   > **`processName` is NOT a valid SavedSearchDefinition field alias** — causes `CWTBG0612E`. Use `bpdName` instead — it maps to `PT_NAME` (process template name) in task response objects.

5. **Always replace stored `fields` with the explicit list above** when forwarding a stored definition to `PUT /tasks`. Stored definitions may have a partial or empty `fields` array. Always reconstruct the body with the explicit fields list above — never forward `criteria.fields` and never send `fields: []`.

### SavedSearchDefinition body schema

The `POST /rest/bpm/wle/v1/searches/tasks` and `PUT /rest/bpm/wle/v1/tasks` (ad hoc search) bodies both accept a `SavedSearchDefinition` object. The 12 valid top-level fields are:

`name` · `interaction` · `size` · `shared` · `fields` · `sort` · `conditions` · `owner` · `teams` · `id` · `aliases` · `organization`

**`organization` valid values (observed in Workplace traffic):**

| Value | Meaning |
|---|---|
| `"byTask"` | Group results by task — standard view used by Workplace |
| `"byInstance"` | Group results by process instance |

Always include `"organization": "byTask"` in generated portal `PUT /tasks` bodies unless grouping by instance is explicitly required.

**Critical — two separate field namespaces. Do not confuse them:**

| Namespace | Where it appears | Example values |
|---|---|---|
| **Task item properties** | Fields on task objects returned by `GET /tasks` and rendered in the UI | `TKIID`, `TAD_DISPLAY_NAME`, `PT_NAME`, `PRIORITY`, `DUE`, `STATE` |
| **SavedSearchDefinition `fields` aliases** | The `fields` array inside the `SavedSearchDefinition` body sent to `POST /searches/tasks` or `PUT /tasks` | `taskId`, `taskSubject`, `taskStatus` |

These are entirely independent vocabularies. Business Automation Workflow validates the `fields` array against the search schema and returns **HTTP 400** for any task item property name (`TKIID`, `TAD_DISPLAY_NAME`, etc.) placed in that array.

**Example `SavedSearchDefinition` body:**

```js
{
  name: 'My Search',
  interaction: 'claimed_and_available',
  size: 25,
  shared: false,
  fields: ['taskId', 'taskSubject', 'taskStatus'],   // search API aliases — NOT task property names
  sort: [{ field: 'taskId', order: 'ASC' }],
}
```

**What causes HTTP 400 / CWTBG0618E — `Unrecognized field` errors:**

```js
// Wrong — never do this: TKIID, TAD_DISPLAY_NAME, etc. are task response properties, not search field aliases
fields: ['TKIID', 'TAD_DISPLAY_NAME', 'NAME', 'PT_NAME', 'PRIORITY', 'DUE', 'STATE']
```

**What causes `CWTBG0618E: Unrecognized field "offset"` — pagination confusion:**

> `offset` is a **URL query parameter** for both `GET /rest/bpm/wle/v1/tasks` and `PUT /rest/bpm/wle/v1/tasks`
> (IBM Search Execution Resource PUT: `PUT /rest/bpm/wle/v1/tasks[?size={integer}][&offset={integer}]`).
> It is **never** a valid field inside a `SavedSearchDefinition` body.
> Page through `PUT /tasks` results with `?size=N&offset=N` on the URL, sending the same criteria and sort each time.
> **Do not include `offset`, `page`, `skip`, `startIndex`, or any other pagination key in a `PUT /tasks` body.**

```js
// Wrong — offset is not a SavedSearchDefinition field; causes CWTBG0618E
const body = { size: 25, offset: 0, organization: 'byTask', ... }

// Correct — only the 12 valid fields
const body = { size: 25, organization: 'byTask', ... }
```

---

## Task mutations

Headless task mutations (claim, assign, update, finish, cancel) are documented or observed APIs, not a form-rendering contract: there is no confirmed generic public API to rebuild an arbitrary task's completion UI (fields, validation, Coach behavior), so open the existing Business Automation Workflow task UI instead. `finish` requires task-specific output `params`.

`action=cancel` behaviour is **state-dependent**:
- On a **claimed** task: releases the claim (`cancelClaim`); task returns to `State_ready`. HTTP 200 with **empty body** (no JSON). Does **not** terminate the task.
- On a **ready/received** task: requires admin or instance-owner authority; a standard task owner receives `CWTBG0549E`. This is not a portal-level operation.

**Allowed-action discovery.** Request `GET /rest/bpm/wle/v1/task/{taskId}?parts=actions` to read the actions the caller may perform on this task in its current state. With `parts=all` the `actions` member was `null` on the observed Cloud Pak for Business Automation 26.0.3 SP20 r2 deployment, so treat `actions` as nullable and use `parts=actions` when gating controls. The action set differs by caller and state (observed: owner — cancel-claim, complete, reassign-to-user; non-owner — view only; administrator — additionally update priority, update due date, reassign-to-group). PFS task items carry no actions member; read actions from the source WLE.

**Unauthorized actions.** A caller without the action received **HTTP 401 with `CWTBG0549E`** on the observed Cloud Pak for Business Automation 26.0.3 SP20 r2 deployment (priority update by the task owner; cancel by a non-owner), with the task unchanged. The wrong-state cancel documented above is HTTP 400. Do not hardcode either status as a universal rule: treat `CWTBG0549E` or any 401/403/400 on an action as "not permitted in this state", refresh the task and remove the control.

**Reassign (`toUser`).** `action=assign&toUser={username}` was observed on one deployment: the owner changed to the target user (read back), who then held the full owner action set, and the target returned it with `toUser={original}`. No assign-back action was advertised on a user-owned task; release used `action=cancel`. `toGroup`, `toTeam` and `toMe` were not tested.

### Task priority — values and labels (owner)

> **Single owner.** This section is the only place that defines the numeric `PRIORITY` codes, their display labels and the search-condition strings. Other files (`task-lifecycle.md`, `saved-search-management.md`, evals, the evidence inventory) must link here instead of restating the table.

There are two separate namespaces. **Do not confuse numeric task-update priority codes with priority name strings used in search conditions.**

**Task-update priority codes** (`action=update&priority={code}`):

| Code | Priority name (display) |
|---|---|
| `10` | Very high |
| `20` | High |
| `30` | Normal |
| `40` | Low |
| `50` | Very low |

These codes appear in raw task response objects as `PRIORITY: 30` and are used exclusively for `PUT /task/{taskId}?action=update&priority={code}`. Evidence: `runtime-verified` (Cloud Pak for Business Automation 26.0.0 — priority updated to `30`; `priority: 30` read back in task object).

> **Display labels:** The display labels for task response numeric codes are `Very high / High / Normal / Low / Very low`, as observed in the Business Automation Workflow saved search UI on a Cloud Pak for Business Automation 26.0.3 SP20 r2 deployment.

**Search condition priority values** — the `taskPriority` condition field in a `SavedSearchDefinition` uses **string names**, not numeric codes:

```js
// Observed in the BAW saved search UI (CP4BA 26.0.3 SP20 r2):
{ field: 'taskPriority', operator: 'Equals', value: 'Normal' }
```

Valid string values (observed in the Business Automation Workflow saved search UI, Cloud Pak for Business Automation 26.0.3 SP20 r2):

| Priority name (search condition) | Corresponding task-update code |
|---|---|
| `'Very high'` | `10` |
| `'High'`      | `20` |
| `'Normal'`    | `30` |
| `'Low'`       | `40` |
| `'Very low'`  | `50` |

> **Evidence scope.** The full set `Very high / High / Normal / Low / Very low` was observed in the Business Automation Workflow saved-search UI dropdown on one deployment (Cloud Pak for Business Automation 26.0.3 SP20 r2). It is not enumerated in IBM documentation, and no retained test artifact exists. An earlier single-value observation recorded only `'Highest'`; that value is not part of the set observed on that deployment. Other deployments may differ.
>
> **No non-federated `meta/priority` endpoint is verified.** IBM documents `GET /rest/bpm/wle/v1/searches/tasks/meta/{type}` for the `constraintFields` and `businessDataFields` types only; it does not document a `priority` type, the project's OpenAPI spec lists no such path, and the catalog has no corresponding non-federated operation. Do not call `GET /rest/bpm/wle/v1/searches/tasks/meta/priority`. The federated `GET /rest/bpm/federated/v1/searches/meta/priority` (`PFS-META-PRIORITY`, documentation-verified) is a PFS-only operation and must not be assumed to exist on the non-federated API. To confirm names on another deployment, use `GET /rest/bpm/wle/v1/searches/tasks/meta/constraintFields` (confirms `taskPriority` is a constraint field; it does not enumerate its values) and the saved-search UI dropdown, and treat the value set as verification-required.

Do **not** pass numeric codes (`10`, `20`, `30`) as search condition values — they are not search API values.
Do **not** use `'Highest'`, `'Medium'`, `'Critical'`, or `'Very Low'` (capital L) — these are not valid values.

**Finish.** `action=finish` returning HTTP 200 and the task reaching `STATE_FINISHED` does **not** prove the process advanced: on the observed Cloud Pak for Business Automation 26.0.3 SP20 r2 deployment a finish with no `params` on a coach-flow task left the parent process `Failed` (cause unresolved). Inspect the task's `data.variables` and the service's expected outputs to build activity-specific `params`, then re-read the process instance after finish.

> **CSRF/XSRF for WLE v1 mutations:** see [XSRF / CSRF for WLE REST mutations](#xsrf--csrf-for-wle-rest-mutations). Cloud Pak for Business Automation authenticates via `Authorization: Bearer <token>`.

**Valid WLE v1 `action=` values** (IBM-documented; retained HTTP 200 records exist for `claim`, `assign` with `back=true`, and `update` priority on Cloud Pak for Business Automation 26.0.0, plus single-deployment state-transition observations on Cloud Pak for Business Automation 26.0.3 SP20 r2 for `cancel` and `assign&toUser`; `finish` remains documentation-verified):
`start`, `assign`, `setdata`, `update`, `finish`, `complete`, `claim`, `cancel`, `invite`, `getdata`

**`action=fail` does not exist in the WLE REST API** — do not generate code using it.

| Capability | Endpoint | Notes |
|---|---|---|
| Task claim | `PUT /rest/bpm/wle/v1/task/{taskId}?action=claim` | |
| Task assignment | `PUT /rest/bpm/wle/v1/task/{taskId}?action=assign` | Exactly one of: `&toMe=true`, `&back=true`, `&toUser={u}`, `&toGroup={g}`, `&toTeam={t}` |
| Task update (due date / priority) | `PUT /rest/bpm/wle/v1/task/{taskId}?action=update` | `&priority={10\|20\|30\|40\|50}` |
| Task finish/complete | `PUT /rest/bpm/wle/v1/task/{taskId}?action=finish` | `action=complete` is a server-side alias. Requires task-specific output variable schema. |
| Task release (cancel claim) | `PUT /rest/bpm/wle/v1/task/{taskId}?action=cancel` | On a **claimed** task only: releases the claim; task returns to `State_ready`. HTTP 200 with empty body. Standard task owner cannot cancel a ready/received task (`CWTBG0549E`). |

---

## Process instance management

> **Status (CAP-INSTANCE-LIFECYCLE-NF):** partial — retry is documentation-verified only. Suspend, resume, due-date update, terminate (from `Failed`) and delete (PUT form) were observed with before/after read-back on **one** Cloud Pak for Business Automation 26.0.3 SP20 r2 deployment (administrator caller); other deployments were not tested.
> Do not describe instance-management as verified or production-ready without first validating against the target deployment.

### Endpoints

| Action | Method | Path | Required auth policy |
|---|---|---|---|
| Suspend | `PUT` | `/rest/bpm/wle/v1/process/{instanceId}?action=suspend` | `ACTION_SUSPEND_INSTANCE` |
| Resume | `PUT` | `/rest/bpm/wle/v1/process/{instanceId}?action=resume` | `ACTION_RESUME_INSTANCE` |
| Retry | `PUT` | `/rest/bpm/wle/v1/process/{instanceId}?action=retry` | `ACTION_RETRY_INSTANCE` |
| Update due date | `PUT` | `/rest/bpm/wle/v1/process/{instanceId}?action=update&dueDate={value}` | `ACTION_CHANGE_INSTANCE_DUEDATE` |
| Terminate | `PUT` | `/rest/bpm/wle/v1/process/{instanceId}?action=terminate` | `ACTION_ABORT_INSTANCE` |
| Delete | `PUT` | `/rest/bpm/wle/v1/process/{instanceId}?action=delete` | `ACTION_DELETE_INSTANCE` |
| Fetch instance detail | `GET` | `/rest/bpm/wle/v1/process/{instanceId}` | caller authorized for instance |

> **Conflict C06 — delete HTTP method:** IBM Business Automation Workflow 23.0.x documents a separate `DELETE /rest/bpm/wle/v1/process/{instanceId}?action=delete` HTTP endpoint.
> The Cloud Pak for Business Automation 26.0.0 authorization reference documents the delete action exclusively as `PUT … ?action=…` (and the equivalent `POST` form).
> These two documentation sources cannot be reconciled without deployment-level testing.
> **Verify which form is accepted in the target Business Automation Workflow version before relying on either in production code.**

### State-action map

Actions are **state-dependent alternatives**, not a sequential workflow.

| Action | Eligible source state |
|---|---|
| Suspend | Running / Active |
| Resume | Suspended |
| Retry | Failed |
| Update due date | Active (Running or Suspended) |
| Terminate | Suspended, Failed, or Terminated *(authorization reference)*; verify in target |
| Delete | Suspended, Failed, or Terminated *(authorization reference)*; Business Process Manager 8.5.0 reference additionally lists Completed — verify in target |

**Observed behavior (one deployment, administrator caller):** suspend `Active`→`Suspended` (open task `STATE_SUSPENDED_BY_PARENT`); resume back to `Active` (task `STATE_CLAIMED`); suspend on a `Failed` instance → HTTP 401 `CWTBG0549E`; terminate `Failed`→`Terminated`; delete (PUT form) on a terminated instance → HTTP 200, then GET → 404. The process owner without administrator authority was offered only comments/diagram/view actions. Terminate from `Active`, retry, and the DELETE/POST delete forms were not tested. All other entries above derive from IBM documentation.
A caller who already holds a valid authorized PIID does not need to call the instance-listing endpoint first — obtain the instance's current state by calling `GET /rest/bpm/wle/v1/process/{instanceId}` before submitting an action.

### Authorization

Business Automation Workflow enforces each action server-side using the per-action policy listed above. A portal UI may choose to hide unavailable actions based on the instance state, but **must not treat a UI-level hide as a permission gate** — the server is authoritative.

Authorization policies are typically assigned at the process-application level in Process Designer. Terminate and delete require admin-level authority on most deployments.

### Critical constraints

**Retry**
- Retry re-runs the **failed service from its beginning**, repeating all external side effects (service calls, database writes, email sends, etc.).
- Never auto-retry; always require an explicit confirmation that includes the process name and PIID.
- Require an idempotency assessment of the failing service before allowing retry in a portal.

**Terminate** *(action=terminate)*
- Terminate is irreversible and may cascade to dependent child instances.
- Require an explicit user confirmation showing the process name and PIID before submitting.

**Delete** *(conflict C06 — see above)*
- Delete permanently removes runtime history; **no recovery** through documented application REST actions is possible (infrastructure-level backup restore may be possible depending on deployment configuration).
- Require a **separate** explicit confirmation distinct from any termination confirmation.
- Write an application-level audit event before submitting (fields: actor, PIID, process name, timestamp, outcome — no process variable data).
- Do not auto-retry a failed delete call.

**dueDate format**
- The documented action is `action=update&dueDate={value}`; an ISO-8601 UTC string (`YYYY-MM-DDTHH:MM:SSZ`) was accepted on the observed Cloud Pak for Business Automation 26.0.3 SP20 r2 deployment (read back changed). Epoch milliseconds were not tested — validate other formats on the target.

**Scope**
- Applies to BPD/WLE process instances only; not applicable to BPEL/BFM instances.
- NF-only: actions on PFS-discovered instances are not modeled in this skill.

### XSRF

See [XSRF / CSRF for WLE REST mutations](#xsrf--csrf-for-wle-rest-mutations).

---

## Process launch

| Capability | Endpoint |
|---|---|
| Launchable items (NF) | `GET /rest/bpm/wle/v1/exposed` |
| Start process | `POST /rest/bpm/wle/v1/process?action=start&bpdId={bpdId}&processAppId={processAppId}` |

**`/exposed` response shape — observed field names (runtime-verified):**

| Field | Notes |
|---|---|
| `data.exposedItemsList[]` | Array of launchable items |
| `itemID` | Compound ID (`<version>.<uuid>`). **Do not use directly** — the correct `bpdId` value must be read from `startURL` (see below). |
| `processAppID` | Compound ID (`<version>.<uuid>`). **Do not use as `processAppId`** — the UUID is not the value Business Automation Workflow's `action=start` accepts. Read `processAppId` from `startURL` instead. |
| `snapshotID` | Present in the response. **Must not be passed** to `action=start` — Business Automation Workflow returns `CWTBG0012E: The parameter 'snapshotId' is invalid` even with a valid value. Omit entirely; Business Automation Workflow uses the current default snapshot. |
| `startURL` | **Canonical source for launch parameters.** Parse `bpdId` and `processAppId` from this URL's query string — these are the exact values Business Automation Workflow's REST API accepts. |
| `processAppAcronym` | Short process app identifier (e.g. `"HSS"`). Display only — never a launch parameter. |
| `type` | `"process"`, `"service"`, `"url"` — filter to `"process"` for process launch |
| `display` / `title` | Display name for the process |

> **Use `startURL` as the parameter source:**
> Parse the `startURL` field from each `/exposed` item using `new URL(item.startURL, 'https://x')`.
> Extract `bpdId` and `processAppId` from its query string and POST them to `action=start`.
> This is the only approach observed to work — constructing the parameters from `itemID`, `processAppID`,
> or `snapshotID` alone fails with HTTP 409 or HTTP 400 (`CWTBG0012E`) at runtime.
>
> **What fails (do not generate):**
> - Passing `itemID` directly as `bpdId` → HTTP 409
> - Passing stripped `processAppID` UUID as `processAppId` → HTTP 400 `CWTBG0012E: projectId invalid`
> - Passing any `snapshotId` value → HTTP 400 `CWTBG0012E: snapshotId invalid`
>
> Do not use `/rest/bpm/wle/v1/launchableEntities` — that is the federated path.

**Exposed-process normaliser (single definition — all generated code calls this, none re-implements it).** It reads `bpdId` and `processAppId` only from `startURL`. Never substitute `itemID`, `processAppID`, `snapshotID` or `processAppAcronym` when a required parameter is missing: the item is rejected with a reason code and not offered for launch. Only root-relative start URLs are accepted; the path is ignored because the caller always POSTs to the fixed `action=start` endpoint above. `snapshotId` is never forwarded. This is the evidence-backed rule recorded above (`itemID` → HTTP 409; `snapshotId` → `CWTBG0012E`); it adds no new API fact.

<!-- snippet: normaliseExposedProcess -->
```js
function normaliseExposedProcess(item) {
  const fail = reason => ({ ok: false, reason });
  try {
    if (!item || typeof item !== 'object' || Array.isArray(item)) return fail('item-not-object');
    if (item.type !== 'process') return fail('unsupported-type');
    const u = item.startURL;
    if (typeof u !== 'string' || u === '') return fail('start-url-missing');
    if (u.length > 2048) return fail('start-url-too-long');
    if (/[\u0000-\u0020\u007f\\]/.test(u)) return fail('start-url-illegal-character');
    if (u[0] !== '/' || u[1] === '/') return fail('start-url-not-root-relative');
    const q = u.indexOf('?');
    if (q < 0) return fail('start-url-no-query');
    const params = new URLSearchParams(u.slice(q + 1).split('#')[0]);
    const once = key => {
      const v = params.getAll(key);
      if (v.length !== 1) return null;
      return v[0] !== '' && v[0].length <= 256 && !/[\u0000-\u001f\u007f]/.test(v[0]) ? v[0] : null;
    };
    const action = params.getAll('action');
    if (action.length > 1 || (action.length === 1 && action[0] !== 'start')) return fail('unsupported-action');
    const bpdId = once('bpdId');
    const processAppId = once('processAppId');
    if (bpdId === null) return fail('bpdId-missing-or-invalid');
    if (processAppId === null) return fail('processAppId-missing-or-invalid');
    const name = typeof item.display === 'string' ? item.display : (typeof item.title === 'string' ? item.title : '');
    return { ok: true, process: { bpdId, processAppId, name } };
  } catch (e) {
    return fail('start-url-unparseable');
  }
}
```

**Live process start response fields:** evidence scope. `apis/baw-wle-v1.26.0.0.json` (`POST /process`) declares no response schema; it lists only "200: Process instance created". The fields below were observed once, on one deployment (Cloud Pak for Business Automation 26.0.3 SP20 r2), and are `structural-assertion-verified`. They are not a universal contract: treat everything except a readable `data.piid` as optional.

| Field | Notes |
|---|---|
| `data.piid` | Process instance ID for the started process |
| `data.tasks[0].tkiid` | Task ID of the first (auto-created) task — optional: `tasks` may be absent or empty, for example when the process starts with no human task. When present the task may already be `STATE_CLAIMED` by the starting user (observed on that deployment; read task state before issuing `claim`) |
| `data.state` | Process state — e.g. `STATE_RUNNING` |

<!-- snippet: readProcessStartResult -->
```js
function readProcessStartResult(json) {
  const d = json && typeof json === 'object' ? json.data : null;
  if (!d || typeof d !== 'object') return { piid: null, taskId: null };
  const id = v => (typeof v === 'string' && v.trim() !== '' ? v : (Number.isSafeInteger(v) ? String(v) : null));
  const first = Array.isArray(d.tasks) ? d.tasks[0] : null;
  return { piid: id(d.piid), taskId: first && typeof first === 'object' ? id(first.tkiid) : null };
}
```

The UI behaviour built on this result (display, inbox refresh, highlight) is owned by the [task-lifecycle playbook](playbooks/task-lifecycle.md).

---

## XSRF / CSRF for WLE REST mutations

This is the single CSRF contract for the skill; other files point here. It separates four kinds of statement — do not merge them.

**1. Documented requirement (IBM).** Workflow REST API operations require the HTTP header `BPMCSRFToken` on every request. The client obtains the token by calling `POST /bpm/system/login` with a JSON payload (always send one, even if empty), for example `{"refresh-groups": false, "requested-lifetime": 7200}`. The token is returned in the `csrf_token` property; 7200 seconds is the default and maximum lifetime. An expired or unverifiable token fails with HTTP 403 and `CWTBG0651E`; renew by calling login again and retry the request. Sources: [Preventing cross site request forgery](https://www.ibm.com/docs/en/baw/24.0.x?topic=apis-preventing-cross-site-request-forgery), [Process REST APIs](https://www.ibm.com/docs/en/baw/26.0.x?topic=apis-process-rest), and the `createBPMCSRFToken` operation in `apis/baw-process.26.0.0.json` (basePath `/bpm`). The retrieved pages do not scope the header to particular path families, and the skill's hand-authored `baw-wle-*`/`baw-pfs-*` catalogs declare no `BPMCSRFToken` parameter (they are not IBM-published). Whether `/rest/bpm/wle/*` and `/rest/bpm/federated/*` enforce the header on a given deployment is therefore **verification-required**, and the WLE and PFS token contracts are not assumed to be identical.

**2. Deployment configuration (operator-controlled).** Legacy `/rest/bpm/wle/v1/*` POST/PUT/DELETE requests can be subject to `XSRF-TOKEN` cookie validation: Cloud Pak for Business Automation `environment_config.csrf.check_xsrf_for_old_restapi` (default `true`), with `environment_config.csrf.user_agent_keyword_allow_list_for_old_restapi_csrf_check` (named `..._white_list_...` in Cloud Pak for Business Automation 22.0.2) and the Referer/Origin allow lists as related controls; traditional Business Automation Workflow uses the `Security.*` hardening properties. Sources: [Cloud Pak for Business Automation 26.0.0 Workflow Runtime parameters](https://www.ibm.com/docs/en/cloud-paks/cp-biz-automation/26.0.0?topic=parameters-business-automation-workflow-runtime-workstream-services), [Business Automation Workflow security-hardening properties](https://www.ibm.com/docs/en/baw/25.0.x?topic=environment-security-hardening-properties). The sources reviewed state only that the server validates the cookie; they do not document how a client satisfies it. This check is separate from the `BPMCSRFToken` header. Generated code must not assume it is disabled, must not recommend disabling it, and must not spoof a `User-Agent` to skip it.

**3. Authentication modes.** (a) Browser session cookie (hosted on Business Automation Workflow, same-origin): no retained mutation run covers this mode, so its requirement is verification-required. (b) Cloud Pak for Business Automation `Authorization: Bearer <token>`: WLE v1 mutations (`claim`, `assign&back=true`, `update` priority) returned HTTP 200 on Cloud Pak for Business Automation 26.0.0, and further single-deployment state transitions were observed on Cloud Pak for Business Automation 26.0.3 SP20 r2. The harness builds Bearer requests with only `Accept`, `Content-Type` and `Authorization` (no `BPMCSRFToken`, `bpm-csrf-token`, `X-Requested-With` or cookie), but raw request/response logs were not retained, so the omission rests on harness source, not captured traffic, and a gateway adding headers cannot be excluded. Treat these as observations for that auth mode on those deployments — not as proof that no CSRF control exists or that other deployments behave the same.

**4. What generated code does.** Route every mutation (`POST`/`PUT`/`DELETE`) through one helper. When the target deployment is known to require the token, or a mutation returns HTTP 403 with `CWTBG0651E`, the helper calls the documented login operation (context root taken from the target's Process REST definition, not guessed), reads `csrf_token` from the response, sends it as `BPMCSRFToken`, and renews once on `CWTBG0651E`. Never hard-code, fabricate or log a token; never invent a header or endpoint to satisfy the `XSRF-TOKEN` cookie check; keep TLS verification and authentication unchanged. For Bearer-authenticated Cloud Pak for Business Automation mutations, no extra header is added by default (observed behaviour above). If the requirement for the chosen combination of deployment, auth mode and API family is unconfirmed, say so in the handoff as verification-required rather than asserting that CSRF is or is not needed. GET requests were observed without a token on one deployment; that observation does not narrow the documented every-request scope in part 1. The Operations REST API also publishes a `POST /ops/system/login` (basePath `/ops`); it is a separate API family and is not interchangeable with `POST /bpm/system/login` for Process, WLE or PFS calls.

---

## Security rules for all generated non-federated code

1. All API response values rendered via `textContent`, DOM property assignment, or `escHtml()`.
2. No `localStorage` for task IDs, task data, or process data — in-memory session state only.
3. No `eval()`, no `document.write()`.
4. No console logging of full API payloads — they may contain PII.
5. In-flight guard: return early if a fetch is already in progress.
6. Guard `taskId` with a truthiness check and `encodeURIComponent` before URL construction. Do not require numeric-only format (UUID-format TKIIDs are valid).
7. CSRF/XSRF: Use `credentials: 'same-origin'` (or `withCredentials: true`) for session-cookie calls; follow the contract in [XSRF / CSRF for WLE REST mutations](#xsrf--csrf-for-wle-rest-mutations). Never fabricate or log a token.

---

## Data freshness pattern (reference implementation)

The approved reference implementation uses a polling + fingerprint + staleness model:

| Constant | Default | Purpose |
|---|---|---|
| `POLL_INTERVAL` | 60 000 ms | Background silent refresh interval |
| `STALE_THRESHOLD` | 5 min | After this duration, show staleness indicator |

Fingerprint computed from the serialised task list. DOM updated only when the fingerprint changes.
Visibility-aware: silent refresh fires on tab re-focus. Modal close triggers a silent refresh.
