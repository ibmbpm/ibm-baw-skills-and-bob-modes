# Task Lifecycle and Launch — Implementation Playbook

> **Skill:** `create-baw-portal`
> **Capabilities:** `CAP-TASK-LIST-NF`, `CAP-TASK-LIST-PFS`, `CAP-TASK-DETAIL-NF`,
>                  `CAP-TASK-LIFECYCLE-NF` (`CAP-TASK-CLAIM-NF`, `CAP-TASK-RELEASE-NF`,
>                  `CAP-TASK-FINISH-NF`, `CAP-TASK-CANCEL-NF`, `CAP-TASK-UPDATE-NF`),
>                  `CAP-TASK-LIFECYCLE-PFS`, `CAP-TASK-LAUNCH-NF`, `CAP-TASK-LAUNCH-PFS`
> **Intents:** `INT-TASK-INBOX`, `INT-TASK-DETAIL`, `INT-TASK-ACTIONS`, `INT-TASK-LAUNCH`
> **Purpose:** Teach an implementation agent how to add task listing, task details,
> task actions and task launch to an existing application integrated with Business Automation Workflow — using only
> documented operations, without bypassing server-side authorization.
>
> This playbook sequences the work. Request/response contracts live in the reference
> guides and the capability catalog and are linked, not repeated, here. For federated
> (PFS) deployments read this playbook **and**
> [`federated-portal-integration.md`](federated-portal-integration.md).

---

## 1. Three different features — do not conflate them

| Feature | What it does | Operation |
|---|---|---|
| **Task listing** | Returns a page of task summaries for the current user | `NF-TASK-LIST` (`GET /rest/bpm/wle/v1/tasks`) or `PFS-TASK-LIST` |
| **Task details** | Returns metadata for one task by TKIID | `NF-TASK-GET` (`GET /rest/bpm/wle/v1/task/{taskId}`) |
| **Task launch** | Opens the existing Business Automation Workflow task form (coach) so the user completes the work | URL to `/teamworks/process.lsw` — **not a REST call** |

Consequences:

- Task detail does **not** return a launch URL. `runURL` is absent from the response; build the URL
  separately.
- Task launch is a navigation, not an API operation. Do not rebuild the Business Automation Workflow task
  completion UI.
- `finish` (completing the task through REST) is a different feature from launch. A task
  that has a coach is normally completed in the launched form; `action=finish` requires a
  task-specific output-variable schema (see §7).

---

## 2. Before touching any code — read the existing application

Inspect before editing. Do not rebuild the surrounding portal.

1. **Framework and routing** — React/Vue/Angular/Svelte/plain JS; how views are mounted.
2. **State management** — component state, store, context, none.
3. **HTTP client and auth** — `fetch`/`axios`/`HttpClient`; session cookie, Bearer token or
   proxy-forwarded session. Reuse it.
4. **Existing Business Automation Workflow calls** — grep for `/rest/bpm/`, `process.lsw`, `TKIID`, `taskId`,
   `systemID`. Identify which API family (NF `wle/v1`, PFS `federated/v1`) is already used.
5. **Existing task identifiers** — find every place a task ID is validated, parsed or used
   in a URL (see §8).
6. **Existing task-launch mechanism** — iframe, `window.open`, route, or none; and how the
   launch URL is built.
7. **Hosting profile** — A/A2 (served from the Business Automation Workflow origin), or C (external, proxied or
   direct). See [`hosting-and-generation.md`](../hosting-and-generation.md).
8. **Smallest integration surface** — usually a task service module plus a hook or a
   component. Do not introduce a new framework or HTTP client.

---

## 3. Resolve deployment before selecting capabilities

| Question | Determines |
|---|---|
| Is Process Federation Server present (does `GET /rest/bpm/federated/v1/systems` succeed, or has the user said so)? | NF vs PFS |
| Is the portal served from the Business Automation Workflow origin? | Hosting profile; iframe vs `window.open` |
| Session cookie (hosted on Business Automation Workflow), or Cloud Pak for Business Automation Bearer token? | Auth mechanism; CSRF requirement per the single contract (verification-required if unconfirmed) |

- **NF:** use the NF capabilities for list, detail, actions and launch.
- **PFS:** list and launch come from PFS (`CAP-TASK-LIST-PFS`, `CAP-TASK-LAUNCH-PFS`);
  **PFS has no task-mutation endpoints** — claim/release/finish/etc. are sent to the owning
  source system. Follow `federated-portal-integration.md`. Do not call
  `CAP-TASK-DETAIL-NF` against a PFS deployment without validated source routing.
- If deployment is unclear, ask once. Never default silently to NF when the user says PFS.

---

## 4. Task listing and pagination

Contracts: [`non-federated-api-guide.md` §Personal task list](../non-federated-api-guide.md#personal-task-list);
[`federated-api-guide.md` §Federated task list](../federated-api-guide.md#federated-task-list).

- NF default: `GET /rest/bpm/wle/v1/tasks?interaction=claimed_and_available&size=500&offset=0`.
  Switch to `PUT /rest/bpm/wle/v1/tasks` with a `SavedSearchDefinition` body only after a 404
  has been classified as a missing-default-search response (guide
  [404 classification](../non-federated-api-guide.md#404-classification-for-get-tasks)); the
  strategy cache is in §4.2.
- `size=500` is a **limit, not "all tasks"**. Compare `data.totalCount` with the number of
  items received; page with `offset += size` and show a visible truncation indicator
  ("Showing 500 of 1 243 tasks") when more exist. Never present a partial list as complete.
- Extract defensively at one boundary function (`data.items`, `items`, array) and normalise
  field names there (`TKIID` bare uppercase first, then `TASK.TKIID`). Compute stats
  client-side — `data.stats` may be `null`.
- Do not use `processName` as a field alias (`CWTBG0612E`); use `bpdName`.
- Exclude finished/terminated tasks from the active list after stripping the `STATE_` prefix.
- PFS: items carry `systemID`; keep `federationResult[]` alongside the items (§ routing in the
  federated playbook). De-duplicate by `TKIID` + `systemID`.

### 4.1 Priority presentation

Users see plain-language priority labels only; an internal numeric code never appears in
visible text, tooltips, `aria-label` values, sort-menu entries, filter chips or exports
(CSV/print). Render every priority through the single `priorityLabel` helper in the guide's
[owner section](../non-federated-api-guide.md#task-priority--values-and-labels-owner), which
also defines what an unknown or missing value shows. Numeric codes stay internal: use them
only when sending `priority=` on an update or comparing for sort order. Do not copy the
mapping into components, fixtures or other documents.

### 4.2 Task-list strategy cache (session and environment scope)

Do not treat every 404 as equivalent. Only a 404 classified per the guide's
[404 classification](../non-federated-api-guide.md#404-classification-for-get-tasks) and
confirmed by a usable `PUT` result switches the inbox to `PUT`. Cache that decision for the
current browser session and the current Business Automation Workflow environment only: key it by the Business Automation Workflow origin, keep
it in `sessionStorage` (or an in-memory `Map` for non-browser hosts), and store only the
strategy word — never task data, user data or tokens. A different Business Automation Workflow origin probes `GET`
again; clear the decision on sign-out. If a cached `PUT` later returns 404, drop the decision
and re-probe `GET` once. Every other status (400, 401, 403, 408, 5xx) and network errors are
surfaced to the user's normal error handling and never cached.

<!-- snippet: loadTaskInbox -->
```js
const TASK_LIST_STRATEGY_KEY = env => 'portal.taskListStrategy:' + env;

function forgetTaskListStrategy(store, env) {
  store.removeItem(TASK_LIST_STRATEGY_KEY(env));
}

// getTasks / putTasks resolve to { status, json } and do not throw on HTTP errors.
async function loadTaskInbox({ env, store, getTasks, putTasks }) {
  const key = TASK_LIST_STRATEGY_KEY(env);
  const usable = r => r.status === 200 && r.json && typeof r.json === 'object' &&
    (Array.isArray(r.json.items) || (r.json.data && Array.isArray(r.json.data.items)));
  if (store.getItem(key) === 'put') {
    const cached = await putTasks();
    if (cached.status !== 404) return cached;
    forgetTaskListStrategy(store, env);          // stale decision: re-verify once below
  }
  const first = await getTasks();
  const bawBody = first.json && typeof first.json === 'object' && 'Data' in first.json;
  if (first.status !== 404 || !bawBody) return first;   // not the missing-default-search case
  const fallback = await putTasks();
  if (fallback.status !== 200) return fallback;
  if (!usable(fallback)) return first;           // unusable PUT: surface the original 404
  store.setItem(key, 'put');
  return fallback;
}
```

### 4.3 Process start follow-up

After a successful process start (launch flow in [`hosting-and-generation.md`](../hosting-and-generation.md)), read the
response only through `readProcessStartResult` in the guide's
[process launch section](../non-federated-api-guide.md#process-launch), which records the
evidence scope of the response shape. Then:

1. Show the process instance ID; when `taskId` is non-null, show it next to the instance ID
   (rendered as text, treated as opaque per §8).
2. Refresh the inbox (§4) after the start succeeds.
3. If the refreshed list contains a task whose `TKIID` equals `taskId` (compare as strings),
   highlight that row, scroll it into view and announce it in an `aria-live` region; keep the
   highlight until the next user action.
4. If `taskId` is absent, show the instance ID alone and refresh the inbox with no highlight.
   If `taskId` is present but the task is not visible (other page, filter, or not yet
   indexed), say that the task was created but is not shown in the current view; do not
   retry in a loop or guess another task.

### 4.4 Conservative task ownership

In general inbox searches (such as `interaction: "claimed_and_available"` or broad saved searches), tasks in `STATE_CLAIMED` may be claimed by other users. Do not assume or infer that every claimed task belongs to the current logged-in user.
- Explicitly compare the task's assigned owner (`OWNER` or `assignedTo`) with the current user's login username (`currentUserName` from `GET /user/current?parts=all`).
- Mark a task as claimed by the current user (`assignedToCurrentUser = true`) only when `OWNER` matches `currentUserName`, or when executing a dedicated query configured with `interaction: "claimed"`.

### 4.5 Distinct at-risk vs overdue calculation semantics

Keep at-risk threshold calculations and overdue evaluations distinct. Do not combine them into an unverified composite formula.
- **Overdue (`isOverdue`):** A task is overdue strictly when a valid `dueDate` (or `DUE`) exists and its timestamp has elapsed: `new Date(dueDate).getTime() < Date.now()`.
- **At-Risk (`isAtRisk`):** A task is at-risk when the server-provided `atRiskTime` (or `AT_RISK_TIME`) has passed or `IS_AT_RISK` is `true`, **and** the task is not yet overdue (`!isOverdue`): `atRiskTime && new Date(atRiskTime).getTime() <= Date.now() && !isOverdue`.

---

## 5. Task detail retrieval

`GET /rest/bpm/wle/v1/task/{encodeURIComponent(taskId)}` (`NF-TASK-GET`, runtime-verified).

- 404 means the task does not exist **or is not accessible to the user** — render a neutral
  "not found or no access" state; do not distinguish the two.
- Render every returned value with `textContent` (or the framework's escaped binding), never
  unescaped `innerHTML`.
- Do not expect a launch URL or `runURL` in the response. `actions` is **nullable under `parts=all`**;
  use `GET …/task/{id}?parts=actions` for allowed-action discovery (dedicated call), and show only
  the controls it lists. The set differs by caller and task state.
- A detail link in a list row must carry the **opaque TKIID** (and `systemID` on PFS) — see §8.

---

## 6. Claim, release, reassign, priority

All are `PUT /rest/bpm/wle/v1/task/{encodeURIComponent(taskId)}?action=…` (see
`non-federated-api-guide.md` §Task mutations; limitations are in each catalog operation).

| UI action | Operation | Evidence | Notes |
|---|---|---|---|
| Claim | `NF-TASK-CLAIM` `action=claim` | runtime-verified | Task must be ready/received. |
| Release | `NF-TASK-CANCEL` `action=cancel` **on a claimed task** | structural-assertion-verified (one deployment) | Releases the claim only; the task returns to `State_ready` and the process instance is unaffected. HTTP 200 with an **empty body** — do not parse JSON. On a ready/received task it needs admin authority (`CWTBG0549E`); it is not a portal operation. Observed on one deployment: claimed → `STATE_READY` with no owner, then re-claimable. |
| Assign back to pool | `NF-TASK-ASSIGN-BACK` `action=assign&back=true` | runtime-verified | Task must be claimed by the current user. |
| Reassign | `NF-TASK-ASSIGN-TO` `action=assign` + exactly one of `toMe`, `toUser`, `toGroup`, `toTeam` | structural-assertion-verified for **`toUser` only** (one deployment); other targets documentation-verified | Never use `action=toMe`. `toUser={username}` is the documented user-reassign contract; the new owner held the full owner action set afterwards. Gate behind `parts=actions`; Business Automation Workflow enforces assignment authorization. |
| Priority | `NF-TASK-UPDATE` `action=update&priority={code}` (codes and labels: [owner](../non-federated-api-guide.md#task-priority--values-and-labels-owner)) | runtime-verified for **priority only** | Other attributes (e.g. due date) are not verified. Observed: an administrator succeeded; the task owner without the update-priority action was rejected (HTTP 401, `CWTBG0549E`) with the task unchanged. |

Rules:

- `action=fail` does not exist. Do not invent actions.
- CSRF/XSRF: follow the contract in [`non-federated-api-guide.md` §XSRF / CSRF for WLE REST mutations](../non-federated-api-guide.md#xsrf--csrf-for-wle-rest-mutations). Bearer-authenticated mutations succeeded on observed Cloud Pak for Business Automation deployments without an extra header; do not add one by default, and do not fabricate a token. Report an unconfirmed requirement as verification-required.
- Offer reassign and priority controls only when the application already exposes them or the
  user asks; keep reassignment visibly marked as "documented by IBM, not runtime-tested" in generated notes.
- Do **not** generate admin-scope operations (cancelling ready tasks, terminating tasks or
  instances, impersonation) as portal features.

---

## 7. Completion and server-authoritative permissions

- `NF-TASK-FINISH` (`action=finish`; `complete` is an alias) is documentation-verified (documented by IBM; no retained execution record). The `params` format is task-definition-specific; do not invent a generic payload. Prefer launching the Business Automation Workflow task form (§9) for tasks with data.
- **Task finished is not process completed.** On one deployment, a `finish` with no `params`
  on a coach-flow task returned HTTP 200 and `STATE_FINISHED`, yet the parent process then
  read back `Failed` (cause unresolved). Completion needs activity-specific parameter
  validation: read the task's `data.variables` and the service's expected outputs before
  building `params`, and re-read the process instance after `finish` (expect it to advance, not
  fail). Do not claim success from the task state alone.
- **The server is the authority.** Use the client-side `STATE` only to decide which buttons
  to show. Every action must still handle a server rejection, because state, ownership and
  permissions can change between the list call and the action. Visibility in the list does not
  imply permission to act.
- Never infer permission from `data.managerName`, role names or any client-side field.
- Do not retry a failed mutation automatically; do not work around a 400/403 by trying a
  different action.

---

## 8. Task identifiers are opaque

TKIIDs are numeric strings on some Business Automation Workflow versions and UUID strings on Cloud Pak for Business Automation.

- Treat as opaque: guard with truthiness only (`if (!taskId) return`).
- Do **not** validate with `/^\d+$/`, `isNaN(Number(id))`, `parseInt` or `Number()`; do not
  coerce to number (loses UUIDs and large IDs).
- Obtain the ID only from a Business Automation Workflow response, never from free text. Always `encodeURIComponent`
  it in paths and query strings.
- Router and tests: allow UUIDs and numeric strings in route params, links and fixtures.

---

## 9. Task launch URL and hosting profiles

Contract: [`non-federated-api-guide.md` §Task launch](../non-federated-api-guide.md#task-launch); [`federated-api-guide.md` §Federated task launch](../federated-api-guide.md#federated-task-launch). Hard-code the path `/teamworks/process.lsw`.

```
/teamworks/process.lsw?zWorkflowState=1&zTaskId={encodeURIComponent(TKIID)}&zResetContext=true
```

Iframe/proxy/CSP/cookie prerequisites are owned by
[`hosting-and-generation.md`](../hosting-and-generation.md); this table states only the minimum.

| Profile | URL | Embedding |
|---|---|---|
| A / A2 — served from the Business Automation Workflow origin | bare relative URL above | iframe OK (same-origin) |
| C — external portal (direct or behind a reverse proxy) | absolute Business Automation Workflow URL, or `{PROXY_BASE}` + URL above | **No iframe by default.** Requires the portal origin in `frame-ancestors` **and** HTTPS same-site (`hosting-and-generation.md`). A reverse proxy alone is not sufficient (absolute redirects leave the proxy). Otherwise use `window.open()` / top-level navigation. |
| PFS (any profile) | `{taskCompletionUrlPrefix}` + `/process.lsw?…` from the **matching** `federationResult[]` entry | Same iframe/`window.open` rule as above |

- `taskCompletionUrlPrefix` already is the teamworks base. Do not append `/rest/bpm/wle`
  (that belongs to `restUrlPrefix`). Validate and allowlist it; never use unvalidated response
  values to build navigation URLs.
- Never put an absolute Business Automation Workflow origin in the `src` of an iframe in an external portal.
- Iframe requirements: `title`, clear `src` to `about:blank` on close, do not store task data
  or TKIID in `localStorage`. Do not add `sandbox` without testing it against the target (see
  [`hosting-and-generation.md` §Quality requirements (every UI)](../hosting-and-generation.md#quality-requirements-every-ui)).
- HTTPS is required for cookie-based SSO across origins (`LtpaToken2` is SameSite=Strict);
  Cloud Pak for Business Automation uses a Bearer token and a shared IAM session.
- After the task form closes or the user returns, **re-fetch** the list or the task detail;
  do not assume the task completed.

**Evidence:** `NF-TASK-LAUNCH` (URL pattern) is **documentation-verified**. `PFS-TASK-LAUNCH` URL pattern and SSO are documented by IBM and observed in development on Cloud Pak for Business Automation 26.0.0, but retained checks assert only `federationResult[]` presence without a page load. State this plainly in generated notes; do not claim the iframe was tested against the user's deployment.

---

## 10. Error handling and state transitions

| Situation | Handling |
|---|---|
| 401 without `CWTBG0549E` | Session/token expired — re-authenticate once; do not loop. |
| 401 or 403 with `CWTBG0549E` on an action | Not permitted for this caller/state (HTTP 401 was observed for unauthorized actions on one deployment; the wrong-state cancel is documented as 400). Show a neutral message, refresh via `parts=actions`, remove the control. Do not hardcode one status as universal. |
| 404 on detail/mutation | Task gone or inaccessible — drop it from the list view and refresh. |
| 400 state conflict (already claimed, wrong state) | Refresh the task and re-evaluate available actions. |
| 5xx / network | Keep the row, show a retry affordance; do not optimistic-update. |
| 200 empty body on release | Success — do not call `.json()`. |

Valid transitions (UI hints only; the server decides): ready/received → **claim** → claimed →
**release** or **assign back** → ready; claimed → **finish** → finished. After every mutation,
update the row from a fresh `NF-TASK-GET` (or re-fetch the list) rather than guessing the new
state. On PFS, reconcile from the source system, not PFS (index lag).

---

## 11. Tests to add

Add to the application's existing test setup. Do not generate a separate test framework.

- **List:** pagination — `totalCount > items.length` shows the truncation indicator; empty list;
  `data.stats === null`.
- **Priority:** every priority renders as a plain-language label in text, tooltip, `aria-label`
  and export; an unknown value shows no number.
- **Task-list strategy:** a classified 404 + usable `PUT` is cached and `GET` is not repeated;
  an unclassified 404, 401, 403, 408, 5xx or network error never falls back or caches; a new
  Business Automation Workflow origin probes `GET` again; a cached `PUT` returning 404 is re-verified once.
- **Process start:** with a task ID the row is highlighted and both IDs are shown; without one
  only the instance ID is shown and the inbox still refreshes; a not-visible task shows the
  neutral message.
- **Identifiers:** a UUID TKIID and a numeric-string TKIID both produce a working detail link,
  route param and launch URL; a falsy ID produces no URL.
- **Detail link:** row → detail passes the TKIID (and `systemID` on PFS) unchanged and encoded.
- **Launch URL:** assert exact path, the three query params, `encodeURIComponent` use, no
  absolute Business Automation Workflow origin in iframe `src` for external (C-proxy / C-direct) portals, and no `/rest/bpm/wle` suffix on
  `taskCompletionUrlPrefix`.
- **Launch routing (PFS):** wrong or missing `federationResult` match → no URL, error state.
- **Authorization:** an unauthorized action (HTTP 401 with `CWTBG0549E`) removes the control and does not trigger a re-login loop; `actions: null` under `parts=all` is handled; allowed actions come from `parts=actions`.
- **Completion:** `finish` builds `params` from the task's contract; after `finish`, the process instance is re-read and a `Failed` process is shown as failed even when the task is `STATE_FINISHED`.
- **Mutations:** release treats empty 200 as success; claim on 400 refreshes the row; no request
  is sent when the ID is falsy; `action=fail` and `action=toMe` never appear.
- **Security:** values are rendered as text; no task data in `localStorage`.

---

## 12. Operation evidence (as recorded in the catalog)

| Operation | Evidence |
|---|---|
| `NF-TASK-LIST`, `PFS-TASK-LIST`, `NF-TASK-GET` | runtime-verified |
| `NF-TASK-CLAIM`, `NF-TASK-ASSIGN-BACK`, `NF-TASK-UPDATE` (priority) | runtime-verified (HTTP 2xx, status-only) |
| `NF-TASK-CANCEL`, `NF-TASK-ASSIGN-TO` (`toUser`) | structural-assertion-verified — one Cloud Pak for Business Automation 26.0.3 SP20 r2 deployment, before/after read-back; `toGroup`/`toTeam`/`toMe` documentation-verified |
| `NF-TASK-FINISH` | documentation-verified (finish left the process `Failed` on one deployment, so it is not upgraded) |
| `NF-PROCESS-START`, `NF-INSTANCE-UPDATE-DUEDATE`, `-SUSPEND`, `-RESUME`, `-TERMINATE` (from `Failed`), `-DELETE` (PUT form) | structural-assertion-verified — same single deployment; see [`non-federated-api-guide.md`](../non-federated-api-guide.md) |
| `NF-TASK-LAUNCH` | documentation-verified |
| `PFS-TASK-LAUNCH` | documentation-verified (retained checks assert only `federationResult[]` presence; no task form load) |
| `CAP-TASK-LIFECYCLE-PFS` (mutations on PFS-discovered tasks) | documentation-verified, `partial` — not tested end to end |

structural-assertion-verified means a before/after state transition was read back on one named deployment (Cloud Pak for Business Automation 26.0.3 SP20 r2); it is not schema certification and not evidence for other deployments. Runtime verification here means a recorded successful, status-only check on Cloud Pak for Business Automation 26.0.0 (see `capabilities/catalog.json` `evidence` blocks and [`hosting-and-generation.md` §Open deployment decisions](../hosting-and-generation.md#open-deployment-decisions)). These labels are not production certification for any other
deployment; the catalog entry for each operation is authoritative.
