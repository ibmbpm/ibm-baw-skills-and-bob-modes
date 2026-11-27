# Saved Search Management — Implementation Playbook

> **Skill:** `create-baw-portal`
> **Capabilities:** `CAP-SAVED-SEARCH-MGMT-NF`, `CAP-SAVED-SEARCH-MGMT-PFS`,
>                  `CAP-SAVED-SEARCH-EXEC-NF`, `CAP-SAVED-SEARCH-EXEC-PFS`
> **Intents:** `INT-SAVED-SEARCH-MGMT`, `INT-SAVED-SEARCH-EXEC`
> **Purpose:** Teach an implementation agent how to add complete, correct saved-search
> management to an existing application integrated with Business Automation Workflow — without inventing APIs or
> replacing the application's existing architecture.

---

## 1. What this feature does and does not do

**Saved-search definition management** — CRUD on named, persisted search configurations.
A saved search is a reusable filter set (criteria, sort, column preferences). The user
creates it once and recalls it by name or ID. The Business Automation Workflow server stores it.

**Executing a saved search** — applying a stored definition's criteria to retrieve
matching task results. This is a distinct operation from managing the definition.

A saved search definition **does not contain task results**. Reading a definition returns
metadata only. Executing the definition is a separate API call that returns tasks.

Do not conflate the two:
- `GET /searches/tasks` → list of stored definitions
- `GET /searches/tasks/{id}` → one stored definition (metadata, not tasks)
- `PUT /tasks` (NF) or `PUT /federated/v1/tasks` (PFS) → task results for given criteria

---

## 2. Before touching any code — read the existing application

When adding saved-search management to an **existing application**, complete these
inspection steps before writing a single line of Business Automation Workflow integration code.

1. **Identify the framework** — React, Vue, Angular, Svelte, plain JS, other.
2. **Identify the routing strategy** — React Router, Vue Router, Angular Router, hash routing, no routing.
3. **Identify the state management pattern** — component state, Pinia, Vuex, Redux, Context, none.
4. **Identify the HTTP client** — `fetch`, `axios`, `ky`, Angular `HttpClient`, other.
5. **Identify the existing authentication pattern** — session cookie, Bearer token, proxy-forwarded session.
6. **Identify the component and file structure** — where service modules live, where views/pages are, naming conventions.
7. **Identify any existing Business Automation Workflow integration points** — reuse the same auth approach and HTTP client.
8. **Determine the smallest integration surface** — a new service module + a new component or hook is usually sufficient. Do not rebuild the surrounding portal.
9. **Identify where saved searches currently appear in the UI**, if anywhere — the existing `SavedSearchesView` or a saved-searches dropdown in the toolbar is the likely mounting point.

Do not require or introduce React, Vue, Angular, axios, or any specific HTTP client. Use
whatever the application already uses. If no HTTP client is present, introduce the simplest
addition consistent with the existing patterns (e.g. plain `fetch` for a plain-JS app).

---

## 3. Resolve deployment (NF vs PFS)

Determine deployment before selecting any capability. NF and PFS use different API base paths
and have different evidence levels for some operations.

| Question | Determines |
|---|---|
| Is Process Federation Server present? | NF vs PFS |
| Is the portal hosted on Business Automation Workflow (same-origin) or external? | Auth mechanism and CORS needs |
| Is the portal calling the Business Automation Workflow source system directly or via PFS? | Which base URL to use |

**Do not silently default to NF when the user indicates PFS.** If deployment is unclear,
ask once before proceeding.

### NF — base paths

```
/rest/bpm/wle/v1/searches/tasks          ← CRUD
/rest/bpm/wle/v1/searches/tasks/{id}     ← single definition
/rest/bpm/wle/v1/tasks                   ← execute (PUT) / exec-param (GET)
/rest/bpm/wle/v1/searches/actions        ← permission check (optional)
```

### PFS — base paths

```
/rest/bpm/federated/v1/searches/tasks          ← CRUD
/rest/bpm/federated/v1/searches/tasks/{id}     ← single definition
/rest/bpm/federated/v1/tasks                   ← execute (PUT) / exec-param (GET)
/rest/bpm/federated/v1/searches/actions        ← permission check (optional)
```

**Path-family rules — do not swap:**
- NF search metadata: `/rest/bpm/wle/v1/searches/tasks/meta/fields` — note `/tasks/` in path
- PFS search metadata: `/rest/bpm/federated/v1/searches/meta/fields` — no `/tasks/` in path
- Using the wrong variant returns HTTP 404

---

## 4. Hosting and authentication

Read `references/hosting-and-generation.md` §Hosting models and §Authentication prerequisites
before generating any HTTP calls.

### Same-origin, hosted on Business Automation Workflow (Profile A / A2)

```js
// Session cookie flows automatically — no token management
fetch(url, { credentials: 'same-origin', headers: { Accept: 'application/json' } })
```

No CORS configuration required. CSRF/XSRF for saved-search mutations: see [`non-federated-api-guide.md` §XSRF / CSRF for WLE REST mutations](../non-federated-api-guide.md#xsrf--csrf-for-wle-rest-mutations) (verification-required where unconfirmed).

### External application behind an authorized proxy (Profile C-proxy)

```js
// Proxy forwards authenticated session — portal code is identical to same-origin
fetch(PROXY_PREFIX + url, { credentials: 'include', headers: { Accept: 'application/json' } })
```

The proxy must forward the Business Automation Workflow session cookies and any `BPMCSRFToken` header the portal sends; see [`hosting-and-generation.md`](../hosting-and-generation.md#cookie-based-proxy-authentication--verified).

### External direct access (Profile C-direct)

```js
// CP4BA: Bearer token from IAM
fetch(BAW_BASE + url, {
  headers: { Authorization: `Bearer ${token}`, Accept: 'application/json' }
})
```

Requires portal origin in Business Automation Workflow CORS allowlist. Do not expose credentials in generated code.
See `references/hosting-and-generation.md` §Bearer token authentication for token acquisition.

### PFS and source-system credentials

PFS and NF source-system credentials are **not interchangeable**. A PFS session cookie
authenticates against PFS endpoints only. Task mutations (claim, assign) route to the
source Business Automation Workflow system via `restUrlPrefix` and require a credential that is valid on that
source system. On Cloud Pak for Business Automation, the IAM Bearer token covers both PFS and source systems behind
the same ingress. On standalone deployments, LTPA2 or SAML SSO must span all systems.

---

## 5. Saved search management — operations and evidence

### NF (capability: `CAP-SAVED-SEARCH-MGMT-NF`)

| Operation ID | Method | Path | Evidence |
|---|---|---|---|
| `NF-SAVED-LIST` | GET | `/rest/bpm/wle/v1/searches/tasks` | runtime-verified |
| `NF-SAVED-CREATE` | POST | `/rest/bpm/wle/v1/searches/tasks` | structural-assertion-verified (single-deployment observation, Cloud Pak for Business Automation 26.0.3 SP20 r2) |
| `NF-SAVED-GET` | GET | `/rest/bpm/wle/v1/searches/tasks/{idOrName}` | structural-assertion-verified (single deployment, no retained artifact; `data` is the definition — see §GET response shape) |
| `NF-SAVED-UPDATE` | PUT | `/rest/bpm/wle/v1/searches/tasks/{idOrName}` | structural-assertion-verified (single-deployment observation, Cloud Pak for Business Automation 26.0.3 SP20 r2) |
| `NF-SAVED-DELETE` | DELETE | `/rest/bpm/wle/v1/searches/tasks/{idOrName}` | structural-assertion-verified (single-deployment observation, Cloud Pak for Business Automation 26.0.3 SP20 r2) |
| `NF-SEARCH-ACTIONS` | GET | `/rest/bpm/wle/v1/searches/actions` | runtime-verified (HTTP 200; optional — action strings not asserted by harness) |

### PFS (capability: `CAP-SAVED-SEARCH-MGMT-PFS`)

| Operation ID | Method | Path | Evidence |
|---|---|---|---|
| `PFS-SAVED-LIST` | GET | `/rest/bpm/federated/v1/searches/tasks` | documentation-verified (no retained execution record) |
| `PFS-SAVED-CREATE` | POST | `/rest/bpm/federated/v1/searches/tasks` | documentation-verified (no retained execution record) |
| `PFS-SAVED-GET` | GET | `/rest/bpm/federated/v1/searches/tasks/{idOrName}` | documentation-verified (no retained execution record) |
| `PFS-SAVED-UPDATE` | **PUT** | `/rest/bpm/federated/v1/searches/tasks/{idOrName}` | **documentation-verified only** |
| `PFS-SAVED-DELETE` | DELETE | `/rest/bpm/federated/v1/searches/tasks/{idOrName}` | documentation-verified (no retained execution record) |
| `PFS-SEARCH-ACTIONS` | GET | `/rest/bpm/federated/v1/searches/actions` | documentation-verified (no retained execution record; optional) |

> **NF-SAVED-CREATE live-observed status:** HTTP **201** (Created) on Cloud Pak for Business Automation 26.0.3 SP20 r2.
> Accept `200` or `201` as success — do not check `=== 200` only.
> Response body: definition under `data`; server-assigned numeric-string `id`; server-set `owner`;
> no server-generated timestamps or extra keys (12 submitted fields returned as-is).
> Role-specific visibility (`shared: false` vs `shared: true` access) remains unverified.

> **NF-SAVED-UPDATE live-observed behavior:** HTTP **200** with updated definition.
> With a complete 12-field PUT body (all fields from prior GET, only `name` changed),
> all 11 non-modified fields were identical before and after (rename-only test).
> **PUT replacement-vs-merge semantics are not independently demonstrated** — do not send
> a partial body. Always fetch the full definition and include every field verbatim.

> **Caution: PFS saved-search operations are documentation-verified; PFS UPDATE has no execution claim at all** — `PFS-SAVED-UPDATE` is documented by IBM
> but has not been runtime-verified in this skill (conflict C03). Flag this
> in developer-facing code comments. Validate in the target PFS environment before shipping.

---

## 6. SavedSearchDefinition body — canonical schema

The same body shape is used for:
- `POST /searches/tasks` (create)
- `PUT /searches/tasks/{id}` (update)
- `PUT /tasks` (execute ad hoc — Strategy A execution body)

**Valid top-level fields (12 total):**

```
name · interaction · size · shared · fields · sort · conditions
owner · teams · id · aliases · organization
```

Any key outside this set causes `CWTBG0618E: Unrecognized field`.

### Critical field rules

**`fields` array — search API aliases, NOT task item properties:**

```js
// Correct — these are SavedSearchDefinition field aliases
fields: ['taskId', 'taskSubject', 'taskStatus', 'taskPriority',
         'taskDueDate', 'taskAtRiskTime', 'bpdName', 'taskActivityName']

// Wrong — TKIID etc. are task response properties; causes CWTBG0618E
fields: ['TKIID', 'TAD_DISPLAY_NAME', 'PT_NAME', 'PRIORITY']
```

**Persisted columns vs execution metadata:**
- **Persisted definition `fields`:** Stores only the user's chosen visible column selection (e.g. `['taskSubject', 'taskPriority', 'taskDueDate', 'bpdName']`). The eight canonical aliases are not unconditionally required for every saved search; persist only the user's chosen projection and never overwrite it with an internal metadata superset when saving via `POST` or `PUT /searches/tasks/{id}`.
- **Execution `fields` (`PUT /tasks`):** In Strategy A execution, request the validated execution metadata fields required by the portal's enabled functionality (`taskId` and `taskStatus` for lifecycle actions, `taskDueDate` and `taskAtRiskTime` for time-tracking badges, `taskPriority` for priority styling, `bpdName`/`taskActivityName` for process context) so runtime indicators receive necessary data regardless of the user's visible display columns.

**Alias normalization mapping:**
Some Business Automation Workflow saved searches or server responses contain raw database column identifiers instead of canonical search aliases. Normalize them to canonical aliases when loading or editing definitions:

| Raw DB Column Identifier | Canonical Search Alias | Response Field |
|---|---|---|
| `TASK.TAD_DISPLAY_NAME` | `taskSubject` | `TAD_DISPLAY_NAME` |
| `TASK.DUE` | `taskDueDate` | `DUE` |
| `TASK.PRIORITY` | `taskPriority` | `PRIORITY` |
| `TASK.STATUS` | `taskStatus` | `STATUS` / `STATE` |
| `TASK.AT_RISK_TIME` | `taskAtRiskTime` | `AT_RISK_TIME` |
| `PROCESS_TYPE.NAME` | `bpdName` | `PT_NAME` |
| `TASK.ACTIVITY_NAME` | `taskActivityName` | `NAME` |
| `TASK.TKIID` | `taskId` | `TKIID` |

Unsupported aliases (e.g., `taskOwner`, `piid`) must be rejected or filtered out rather than guessed.

**`fields: []` does NOT return all fields** — it returns only `TASK.TKIID`,
`PROCESS_INSTANCE.PIID`, and `KIND`. All display fields are absent.
Always provide an explicit alias list.

**`bpdName` not `processName`** — `processName` is not a valid alias
and causes `CWTBG0612E` at runtime. Use `bpdName` (maps to `PT_NAME` in response).

**`offset` not in body** — `offset` is **never** valid inside a `SavedSearchDefinition` JSON body.
Including it causes `CWTBG0618E`. For page navigation, pass `size` and `offset` as **URL query
parameters**, not in the JSON body.

```js
// Wrong — offset in JSON body
const body = { size: 25, offset: 0, organization: 'byTask' }

// Correct — offset in URL query string; body contains no offset
// PUT /rest/bpm/wle/v1/tasks?size=25&offset=0
const url = `/rest/bpm/wle/v1/tasks?size=${size}&offset=${offset}`;
const body = { interaction: '...', organization: 'byTask', fields: [...], sort: [...], conditions: [...] }
```

**`id` for mutations** — the `GET /searches/tasks` list returns each definition with an `"id"`
field (string, e.g. `"1102"`). Workplace uses this numeric ID for all GET/PUT/DELETE calls.
Store the `id` from the list response and prefer it for all mutation paths.
Name-based addressing still works but is not the pattern Workplace uses.

**`interaction` values:**

| Value | Semantics |
|---|---|
| `"claimed"` | Tasks the current user has actively claimed |
| `"claimed_and_available"` | Claimed + claimable (ready/received) — use for inbox-style portals |

**`organization` values:**

| Value | Meaning |
|---|---|
| `"byTask"` | Group by task — standard Workplace view |
| `"byInstance"` | Group by process instance |

**Minimal valid create body:**

```js
{
  name: 'My Search',
  interaction: 'claimed_and_available',
  size: 25,
  shared: false,
  organization: 'byTask',
  fields: ['taskId', 'taskSubject', 'taskStatus', 'taskPriority',
           'taskDueDate', 'taskAtRiskTime', 'bpdName', 'taskActivityName'],
  sort: [{ field: 'taskDueDate', order: 'ASC' }],
  conditions: [{ field: 'taskActivityType', operator: 'Equals', value: 'USER_TASK' }],
  aliases: [],
  teams: [],
}
```

**Priority conditions use string names, not numeric update codes:**

```js
// Correct — search conditions use string names (observed in the BAW saved search UI, CP4BA 26.0.3 SP20 r2)
conditions: [{ field: 'taskPriority', operator: 'Equals', value: 'Normal' }]

// Wrong — numeric codes are only valid for action=update&priority={code}
conditions: [{ field: 'taskPriority', operator: 'Equals', value: 30 }]
```

The valid priority strings, their numeric counterparts and their evidence scope (single
deployment, UI observation) are owned by
[`non-federated-api-guide.md` §Task priority](../non-federated-api-guide.md#task-priority--values-and-labels-owner).
Do not restate the table here. There is **no** verified non-federated `meta/priority`
endpoint; do not call one. On another deployment, treat the value set as verification-required
(saved-search UI dropdown; `GET /rest/bpm/wle/v1/searches/tasks/meta/constraintFields` confirms
only that `taskPriority` is a constraint field).

---

## 7. List and response normalization

### GET /searches/tasks — list response normalization

The authoritative envelope is `data.definitions[]` (IBM *Saved Search Definitions Resource – GET*,
documentation-verified; also observed on Cloud Pak for Business Automation or Business Automation Workflow 24+, raw response not retained).
`data.searches[]` and `searches[]` are **unverified** legacy shapes. An empty array is a valid empty
list; an unrecognised envelope is an error and must be surfaced, never normalised to `[]`:

```js
function extractDefinitionList(json) {
  const list = json?.data?.definitions;
  if (!Array.isArray(list)) throw new Error('Unexpected saved-search list response: data.definitions[] not found');
  return list;
}
```

Do not use `json.data` directly — it is an object, not an array.

Each definition in the list contains at minimum:
- `id` — numeric string (e.g. `"1102"`) — store for all mutations
- `name` — display name
- `shared` — boolean — whether the search is shared with other users
- `owner` — username of the creator

> **List descriptors vs full definition:** The list returned by `GET /searches/tasks` contains shallow descriptor stubs. It does **not** include `fields`, `conditions`, or `sort`. To view, edit, or apply a saved search's custom column projections and sort order, always fetch the complete definition via `GET /searches/tasks/{id}`.

### GET /searches/tasks/{id} — single definition response normalization

The definition is returned **directly in `data`**, not nested under `data.search`.

```js
function extractDefinition(json) {
  // GET-by-id live-observed response shape (structural-assertion-verified,
  // CP4BA 26.0.3 SP20 r2): definition in json.data.
  // Structural validation: must have at least one known SavedSearchDefinition field.
  const DEF_FIELDS = new Set(['name','interaction','size','shared','fields','sort',
                               'conditions','owner','teams','id','aliases','organization']);
  const def = json?.data;
  if (!def || typeof def !== 'object' || !Object.keys(def).some(k => DEF_FIELDS.has(k))) {
    // If data.search exists but data is not the definition, surface the discrepancy.
    throw new Error(
      'Unexpected saved-search GET-by-id response: expected the SavedSearchDefinition in data'
      + (json?.data?.search ? ' (found data.search — not accepted; definition must be in data)' : '')
    );
  }
  return def;
}
```

| Source | Verification level |
|---|---|
| Live response observed: definition directly in `data` (Cloud Pak for Business Automation 26.0.3 SP20 r2) | `structural-assertion-verified` |
| IBM *Saved Search Definition Resource – GET* (Cloud Pak for Business Automation or Business Automation Workflow 25.0.0, `topic=definition-get`) shows the definition directly in `data` in its JSON example | documentation-verified (example only; no response schema asserted) |
| Previously documented `data.search` envelope | not observed in live test; must not be silently accepted |

The result is the `SavedSearchDefinition` object (criteria, fields, sort, conditions).
It does **not** contain task results.

> **If your deployment returns `data.search`:** record the observation for that deployment,
> add an explicit named branch, and open a tracking item. Do not add a silent fallback.

---

## 8. Executing a saved search

### Strategy A — two-step (default; ad hoc search runtime-verified, saved-search get structural-assertion-verified)

1. `GET /rest/bpm/wle/v1/searches/tasks/{idOrName}` — fetch definition
2. Extract criteria from `json.data` using structural validation (GET-by-id live-observed shape; see §7)
3. `PUT /rest/bpm/wle/v1/tasks` with a `SavedSearchDefinition` body built from extracted criteria

Its component evidence is mixed: the ad hoc search returned HTTP 200 in a retained run on Cloud Pak for Business Automation 26.0.0; saved-search GET is a single-deployment observation on Cloud Pak for Business Automation 26.0.3 SP20 r2 with no retained artifact. Use it as the safe default.

```js
async function executeSavedSearchNF(idOrName, apiFetch) {
  // Step 1 — fetch definition
  const defJson = await apiFetch(
    `/rest/bpm/wle/v1/searches/tasks/${encodeURIComponent(idOrName)}`
  );
  // GET-by-id live-observed shape (CP4BA 26.0.3 SP20 r2): definition in data.
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

  // Step 2 — execute as ad hoc search
  // Caution: execution body must request canonical metadata fields for runtime indicators
  // (due date, at-risk badge, status, actions) regardless of saved visible columns.
  const body = {
    interaction:  criteria.interaction  || 'claimed_and_available',
    size:         criteria.size         || 25,
    organization: 'byTask',
    fields:       ['taskId', 'taskSubject', 'taskStatus', 'taskPriority',
                   'taskDueDate', 'taskAtRiskTime', 'bpdName', 'taskActivityName'],
    sort:         criteria.sort?.length
      ? criteria.sort
      : [{ field: 'taskDueDate', order: 'ASC' }],
    conditions:   criteria.conditions?.length
      ? criteria.conditions
      : [{ field: 'taskActivityType', operator: 'Equals', value: 'USER_TASK' }],
  };

  const searchJson = await apiFetch('/rest/bpm/wle/v1/tasks', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  return extractTasks(searchJson); // use the normaliseTask function
}
```

**For PFS Strategy A** — same two-step pattern using PFS paths:

```js
// Step 1: GET /rest/bpm/federated/v1/searches/tasks/{idOrName}
// Step 2: PUT /rest/bpm/federated/v1/tasks
// federationResult[] in response — check per-system statusCode
```

### Strategy B — direct GET with `savedSearch` parameter (documentation-verified only)

`GET /rest/bpm/wle/v1/tasks?savedSearch={nameOrId}` — returns task results directly
using the stored definition, bypassing the two-step approach.

This strategy is documented by IBM but **has not been runtime-verified**
in this skill (operation `NF-SAVED-EXEC-PARAM`, evidence: `documentation-verified`).

```js
// Strategy B — NF
const searchJson = await apiFetch(
  `/rest/bpm/wle/v1/tasks?savedSearch=${encodeURIComponent(nameOrId)}`
);
// For PFS: /rest/bpm/federated/v1/tasks?savedSearch=...
```

**These strategies are alternatives — not cumulative calls.** Choose one. Do not execute both.

Choose Strategy B only when:
- The target deployment has been verified to support the `savedSearch` query parameter
- The extra GET for the definition in Strategy A is measurably undesirable
- The developer explicitly requests it after being informed of the evidence level

**Default to Strategy A.**

### Pagination and `totalCount`

The paging contract (`totalCount`, `size`, `offset` as URL query parameters, truncation indicator)
is owned by [`non-federated-api-guide.md` §Personal task list](../non-federated-api-guide.md#personal-task-list)
and the `offset`/`CWTBG0618E` rule by its SavedSearchDefinition schema section. IBM documents `size` and
`offset` as optional URL query parameters for `PUT /tasks` (documentation-verified — IBM Search
Execution Resource PUT, e.g.
https://www.ibm.com/docs/en/cloud-paks/cp-biz-automation/26.0.0?topic=execution-put).

Send the **same** `SavedSearchDefinition` criteria and sort on every page request.
Use a fixed page size and advance `offset` by that size. Stop on an empty page, or when
`offset + items.length >= totalCount` **only if** the count is exact (see below).
`totalCount` is the server-reported match count, not the page length.

**Count limit.** The documented response also carries `countLimit` (search limit used, or `0`
if not set) and `countLimitExceeded` (`true` when the total exceeds the search limit and "is
actually unknown"). When `countLimitExceeded` is `true`:

- Treat `totalCount` as a lower bound, not an exact total — label it e.g. "500+ matching tasks".
- Do not show "Page N of M"; show "Page N" only.
- Do not stop on `offset + items.length >= totalCount`; keep Next enabled while a page is full.
  Treat an empty page or a short page (`items.length < size`) as terminal.

IBM documentation does not state whether records beyond `countLimit` are returned at higher
offsets. Do not assume either way — verify in the target environment.

> **Deployment note:** URL query-parameter pagination for `PUT /tasks` is documentation-verified
> only. Runtime compatibility on Cloud Pak for Business Automation 26.0.0 has not been confirmed.
> Verify in the target environment before shipping paginated UI.

---

## 9. Permissions and shared search ownership

Source: IBM docs "Configuration properties for action policies", "Administering searches",
"Saved Search Definition User Actions Resource – GET". See the policy table in
[`../baw-rest.md`](../baw-rest.md#get-restbpmwlev1searchesactions).

`GET /searches/actions` returns the user's *effective* saved-search actions. The hierarchy
(most → least permissive) is SUPER_ADMIN > ADMINISTER_SHARED > CREATE_SHARED > MANAGE > RUN; the
most permissive policy among the user's groups prevails.

- **Empty list** — private searches only (IBM). Do not block private create/edit/delete on it.
- `ACTION_CREATE_SHARED_SAVED_SEARCH` — may create shared searches. Offer "share" only when
  present (or when a higher policy is present).
- `ACTION_ADMINISTER_SHARED_SAVED_SEARCHES` — may update/delete others' shared searches and
  reassign the owner.
- `ACTION_SAVED_SEARCH_SUPER_ADMIN` — IBM-defined, CRUD on any search including others' private
  searches, via direct saved-search REST calls only. **Not documented as returned by the actions
  endpoint.** Treat it as a superset if it ever appears; never require it.
- `ACTION_MANAGE_SAVED_SEARCH` — enforced server-side; **never returned** by the actions API.
- `ACTION_RUN_SAVED_SEARCH` — run-only restriction; apply only when no higher policy is effective.
- IBM documents the JSON shape `{"status":"200","data":{"actions":[...]}}` (Cloud Pak for Business Automation 24.0.1, *Saved
  Search Definition User Actions Resource – GET Method*). It has not been observed on Cloud Pak for Business Automation 26.0.0
  (the retained run asserts HTTP 200 only); if the body is not recognisable, make no assumption
  in either direction.

A user without shared-administration actions can only edit/delete their **own** searches
(`owner` matches their username). The server enforces this at the API level (HTTP 403) and is
always authoritative; the UI hint is advisory.

**UI rule:** Hide or disable rename/delete controls for searches the current user does not
own, unless the actions list includes `ACTION_ADMINISTER_SHARED_SAVED_SEARCHES` or
`ACTION_SAVED_SEARCH_SUPER_ADMIN`. Retrieve the current username from
`GET /rest/bpm/wle/v1/user/current?parts=all` → `data.userName`.

A `shared: true` search is visible to all users but may only be edited by its owner or a
shared-search administrator.

**Scope:** these are saved-search entitlements only. They are not evidence of task- or
process-administration rights (`allClaimed`, `includeNonAdmin`) — see the Administrator section of
`references/personas-and-capabilities.md`.

---

## 10. Existing-application adaptation checklist

Work through each step in order before writing any Business Automation Workflow code:

1. **Read the application** — framework, routing, state management, HTTP client, auth pattern.
2. **Identify the existing Business Automation Workflow service layer** — if `bawApiService.js` or equivalent exists, extend it. Otherwise create it in the same location as sibling service modules.
3. **Map Business Automation Workflow auth to the existing auth pattern** — do not add a parallel auth system.
4. **Use the existing HTTP client** — wrap Business Automation Workflow calls with the same `axios` / `fetch` / `HttpClient` already used.
5. **Identify the smallest UI integration point** — prefer an integrated saved-search selector and sliding configuration drawer/panel in the task toolbar over a separate standalone page (recommended UX pattern).
6. **Add state for the saved-search list** — use the application's existing state management (component state, Pinia store, Redux slice, etc.).
7. **Add user interaction handlers** — load list on mount, create on form submit, update on rename confirm, delete on confirm dialog, execute on selection.
8. **Preserve unrelated application behavior** — do not refactor the task list, routing, or auth code.
9. **Add focused tests** — see acceptance criteria below.
10. **Validate the full saved-search workflow** against the acceptance criteria.

---

## 11. Error and state handling

Implement all four states for every saved-search UI element:

| State | What to show |
|---|---|
| **Loading** | Spinner or skeleton — do not flash empty content |
| **Empty** | "No saved searches yet. Save a filter to get started." |
| **Error** | Framework-consistent error message; offer retry; log error (not to console in production) |
| **Permission denied (403)** | "You do not have permission to perform this action." Do not expose internal error codes or API paths in UI text. |

**Network failure and loop prevention** — catch fetch/axios errors and show a user-facing error state.
Do not leave the UI in an indeterminate state after a failed request. Guard against recursive network loops: never update active selection state setters inside memoized fetch callbacks that list the selection state as a dependency.

**DELETE response body (Cloud Pak for Business Automation 26.0.3 SP20 r2; single-deployment observation, no retained artifact):** `DELETE /searches/tasks/{id}` returns
HTTP 204 with an empty body. Do not call `response.json()` unconditionally after a DELETE.
Check `response.ok` or the status code first; skip body parsing on 204:

```js
const r = await fetch(`/rest/bpm/wle/v1/searches/tasks/${encodeURIComponent(id)}`, {
  method: 'DELETE', credentials: 'same-origin',
});
if (!r.ok) throw new Error(`DELETE failed: ${r.status}`);
// Do NOT call r.json() — 204 has no body; JSON.parse('') throws
// Verify removal with a subsequent GET or list refresh
```

HTTP 200 may be returned on other deployments but was not observed on Cloud Pak for Business Automation 26.0.3 SP20 r2.
Accept 200 or 204 as success.

**Invalid criteria** — if `PUT /tasks` returns HTTP 400 with `CWTBG0618E`,
the definition body contains an invalid field. The most likely causes are:
- A task item property name in the `fields` array (e.g. `TKIID`, `PT_NAME`)
- `processName` instead of `bpdName`
- `offset` in the body

Handle 400 distinctly from other errors and surface a developer-friendly comment
(not in UI text) identifying the probable field alias error.

**Partial PFS results** — when executing via PFS Strategy A, check
`federationResult[].statusCode` in the `PUT /federated/v1/tasks` response.
When any entry is non-200, retain results from healthy systems and show:
"Results may be incomplete — some data sources are unavailable."

---

## 12. Feature acceptance criteria

These are the acceptance tests for the complete saved-search management feature.
Use controlled fixtures or mocks when no live Business Automation Workflow environment is available.
**Do not claim live Business Automation Workflow verification from mocked tests.**

### AC-1: List definitions

- [ ] `GET /searches/tasks` (or PFS equivalent) is called on feature mount
- [ ] Response is normalized using `extractDefinitionList(json)`
- [ ] An empty array renders the empty state
- [ ] A list with definitions renders each item with name and owner
- [ ] HTTP error shows error state with retry option

### AC-2: Create and retrieve

- [ ] `POST /searches/tasks` is called with a valid `SavedSearchDefinition` body
- [ ] Body contains none of the 400-triggering patterns (no `offset`, no task item property names, `bpdName` not `processName`)
- [ ] Response success is checked for **HTTP 200 or 201** — not `=== 200` alone (Cloud Pak for Business Automation 26.0.3 returns 201)
- [ ] Created `id` is extracted from the response body (`data.id`) and stored
- [ ] A separate `GET /searches/tasks/{id}` is issued after create to verify: `id` matches, `name` matches, `shared` matches
- [ ] After successful POST, list is refreshed (AC-1 re-run)
- [ ] Created definition appears in the refreshed list

### AC-3: Update and retrieve

- [ ] Before PUT: full definition is fetched with `GET /searches/tasks/{id}` and all 12 fields are included in the PUT body
- [ ] Only the intended fields are changed; all others are passed through verbatim
- [ ] `PUT /searches/tasks/{id}` is called with numeric id (not name) for NF
- [ ] Response success is checked for HTTP 200
- [ ] A separate `GET /searches/tasks/{id}` is issued after PUT to verify all non-modified fields are unchanged
- [ ] Updated definition is reflected after list refresh
- [ ] PFS update is flagged in code comments as documented by IBM but not runtime-verified

### AC-4: Delete and verify removal

- [ ] User is presented a confirmation dialog before deletion
- [ ] `DELETE /searches/tasks/{id}` is called only after confirmation
- [ ] DELETE success is checked for **HTTP 200 or 204** — not `=== 200` alone (Cloud Pak for Business Automation 26.0.3 returns 204)
- [ ] **`response.json()` is NOT called unconditionally after DELETE** — a 204 response has no body; parse errors are caught or body parsing is skipped when status is 204
- [ ] After successful DELETE, a subsequent GET or list refresh confirms the definition is absent (GET returns 404)
- [ ] After successful DELETE, the definition no longer appears in the list
- [ ] Cancelling the dialog does not delete the search

### AC-5: Execute and display task results

- [ ] Strategy A (two-step GET definition → PUT /tasks) is the default
- [ ] `fields` array in PUT body is the explicit alias list — not `criteria.fields`, not `[]`
- [ ] Task results are passed through `extractTasks()` and `normaliseTask()`
- [ ] `totalCount` vs returned count is checked — truncation indicator shown when paging needed
- [ ] PFS execution checks `federationResult[].statusCode` for partial failures

### AC-6: Empty results and null items

- [ ] When `PUT /tasks` returns `data.items: []`, the task list renders the empty-search state
- [ ] When `PUT /tasks` returns `data.items: null` with `totalCount: 0`, the empty-search state is rendered (null items accepted as zero results)
- [ ] When `PUT /tasks` returns `data.items: null` with `totalCount > 0`, an error state is rendered (malformed response — not silently accepted as zero)
- [ ] When the response has no `data` envelope at all, an error state is rendered
- [ ] Empty state message is user-facing, not a debug message

### AC-13: Saved-search filter fidelity

Every filter that is part of a saved search definition must be handled explicitly:

- [ ] Each filter in the saved-search definition is either serialized as a supported search condition in the `PUT /tasks` body, **or** explicitly excluded and communicated to the user
- [ ] Executing a saved search restores its supported filters and preserves their result semantics
- [ ] No misleading combination of server-side (Business Automation Workflow conditions) and client-only (UI-layer) filters is saved: client-side filters (text search, display-level sorting, status tab selection) must not be stored in the `SavedSearchDefinition` body — they are not Business Automation Workflow conditions
- [ ] A code comment or UI message identifies any supported filter that cannot be represented as a Business Automation Workflow condition (e.g. a free-text search that maps to `FullTextSearch` vs a client-only `String.includes()` filter) and explicitly excludes it from the saved definition
- [ ] This requirement is framework-independent — applies whether the portal is plain HTML, React, Vue, or Angular

### AC-7: Permission denied

- [ ] HTTP 403 on create/update/delete shows a permission-denied message
- [ ] No internal error code or API path appears in visible UI text
- [ ] UI correctly hides or disables edit/delete for searches not owned by the current user

### AC-8: Invalid request criteria

- [ ] HTTP 400 with body containing `CWTBG0618E` is caught and handled
- [ ] The UI shows a generic error (not the raw error code)
- [ ] A code comment identifies the probable cause (field alias error)

### AC-9: Network failure

- [ ] Network errors (fetch rejection, timeout) are caught
- [ ] Error state is shown with a retry option
- [ ] The UI is not left in an indeterminate loading state

### AC-10: Pagination and truncation

- [ ] When `totalCount > items.length`, a visible truncation banner is shown
- [ ] The banner states how many items are showing and how many exist
- [ ] Page navigation uses `size` and `offset` as **URL query parameters** (`PUT /tasks?size=N&offset=N`)
- [ ] The JSON body contains no `offset` field on any page request
- [ ] Each page request uses identical search criteria and sort order
- [ ] Deployment-specific compatibility note is present in code comments

### AC-11: NF vs PFS deployment selection

- [ ] NF feature uses `/rest/bpm/wle/v1/searches/tasks` paths throughout
- [ ] PFS feature uses `/rest/bpm/federated/v1/searches/tasks` paths throughout
- [ ] No NF path appears in PFS code and vice versa
- [ ] PFS update code carries a developer comment noting it is documented by IBM but not runtime-verified

### AC-12: Preservation of existing application stack

- [ ] No new framework dependency was introduced
- [ ] The existing HTTP client is used — no parallel `fetch` wrapper if `axios` is present
- [ ] State management uses the existing pattern
- [ ] Unrelated application code is unchanged
- [ ] The new Business Automation Workflow service module follows the same naming and location conventions as existing service modules

---

## 13. Implementation approach by framework

This section shows the service boundary pattern for each major framework.
It is **not** a complete implementation — it shows where to put the Business Automation Workflow calls.
Adapt to the application's actual conventions after reading the existing code (Section 2).

### Plain JavaScript / ES modules

```js
// bawSavedSearchService.js — place alongside other service modules
export async function listSavedSearches(apiFetch) {
  const json = await apiFetch('/rest/bpm/wle/v1/searches/tasks');
  const list = json?.data?.definitions;           // authoritative envelope; unverified shapes are not guessed
  if (!Array.isArray(list)) throw new Error('Unexpected saved-search list response: data.definitions[] not found');
  return list;
}

export async function createSavedSearch(definition, apiFetch) {
  return apiFetch('/rest/bpm/wle/v1/searches/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(definition),
  });
}

export async function updateSavedSearch(id, definition, apiFetch) {
  // Use numeric id (preferred over name)
  return apiFetch(`/rest/bpm/wle/v1/searches/tasks/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(definition),
  });
}

export async function deleteSavedSearch(id, apiFetch) {
  return apiFetch(`/rest/bpm/wle/v1/searches/tasks/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
}
```

The `apiFetch` parameter is the application's existing authenticated HTTP wrapper.
Replace with `axios.get/post/put/delete`, Angular `HttpClient`, or the application's
service pattern — whatever exists.

### React (hooks)

Add a `useSavedSearches` hook in the hooks directory alongside existing hooks:

```js
// hooks/useSavedSearches.js
import { useState, useEffect } from 'react';
import { listSavedSearches } from '../services/bawSavedSearchService';

export function useSavedSearches(apiFetch) {
  const [searches, setSearches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    listSavedSearches(apiFetch)
      .then(setSearches)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return { searches, loading, error, reload: () => { /* re-trigger */ } };
}
```

### Vue (Pinia or component state)

```js
// stores/savedSearchStore.js (Pinia)
import { defineStore } from 'pinia';
import { listSavedSearches, createSavedSearch, deleteSavedSearch } from '@/services/bawSavedSearchService';

export const useSavedSearchStore = defineStore('savedSearch', {
  state: () => ({ searches: [], loading: false, error: null }),
  actions: {
    async fetchAll(apiFetch) {
      this.loading = true;
      try { this.searches = await listSavedSearches(apiFetch); }
      catch (e) { this.error = e; }
      finally { this.loading = false; }
    },
  },
});
```

If the application uses Vuex or component-local state, apply the same pattern in that idiom.

### Angular

```ts
// services/baw-saved-search.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class BawSavedSearchService {
  constructor(private http: HttpClient) {}

  list(): Observable<any[]> {
    return this.http.get<any>('/rest/bpm/wle/v1/searches/tasks').pipe(
      map(json => {
        const list = json?.data?.definitions;     // authoritative envelope; unverified shapes are not guessed
        if (!Array.isArray(list)) throw new Error('Unexpected saved-search list response: data.definitions[] not found');
        return list;
      })
    );
  }

  create(definition: any): Observable<any> {
    return this.http.post('/rest/bpm/wle/v1/searches/tasks', definition);
  }

  update(id: string, definition: any): Observable<any> {
    return this.http.put(`/rest/bpm/wle/v1/searches/tasks/${encodeURIComponent(id)}`, definition);
  }

  delete(id: string): Observable<any> {
    return this.http.delete(`/rest/bpm/wle/v1/searches/tasks/${encodeURIComponent(id)}`);
  }
}
```

---

## 14. Security rules

1. All API response values rendered via `textContent` or equivalent — never `innerHTML` with raw API data.
2. No `localStorage` for saved-search definitions, task IDs, or user data.
3. Do not log full API payloads — they may contain PII.
4. Do not expose `LtpaToken2`, `JSESSIONID`, or Bearer tokens in generated client code.
5. CSRF/XSRF for saved-search mutations: follow `non-federated-api-guide.md` §XSRF / CSRF for WLE REST mutations; the PFS requirement is verification-required.
6. Validate search names and condition values before including them in request bodies.

---

## 15. References

- API operations and contracts: `references/non-federated-api-guide.md` §Task search
- PFS equivalents: `references/federated-api-guide.md` §PFS search APIs
- Hosting and authentication: `references/hosting-and-generation.md`
- Capability entries: `capabilities/catalog.json` — `CAP-SAVED-SEARCH-MGMT-NF`, `CAP-SAVED-SEARCH-MGMT-PFS`, `CAP-SAVED-SEARCH-EXEC-NF`, `CAP-SAVED-SEARCH-EXEC-PFS`
- Intent entries: `capabilities/intent-map.json` — `INT-SAVED-SEARCH-MGMT`, `INT-SAVED-SEARCH-EXEC`
- Conflict details: `capabilities/catalog.json` `conflicts[]` — C02 (NF numeric id), C03 (PFS update evidence), C04 (execution strategy)
