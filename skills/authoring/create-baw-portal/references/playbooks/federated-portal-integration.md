# Federated Portal Integration — Implementation Playbook

> **Skill:** `create-baw-portal`
> **Capabilities:** `CAP-TASK-LIST-PFS`, `CAP-TASK-LAUNCH-PFS`, `CAP-TASK-LIFECYCLE-PFS`,
>                  `CAP-PROCESS-DISCOVERY-PFS`, `CAP-ADHOC-SEARCH-PFS`, `CAP-SEARCH-META-PFS`,
>                  `CAP-SAVED-SEARCH-MGMT-PFS`, `CAP-SAVED-SEARCH-EXEC-PFS`,
>                  `CAP-INSTANCE-SEARCH-PFS`, PFS team-workload capabilities
> **Intents:** any intent whose resolved deployment is **PFS** — chiefly `INT-TASK-INBOX`,
>              `INT-TASK-ACTIONS`, `INT-TASK-LAUNCH`, `INT-PROCESS-DISCOVER-AND-START`,
>              `INT-ADVANCED-SEARCH`, `INT-TEAM-WORKLOAD`
> **Purpose:** Teach an implementation agent how to add Process Federation Server (PFS)
> task discovery to a Business Automation Workflow portal and route task launch and mutations to the correct source
> system — without inventing PFS endpoints and without overstating what has been tested.
>
> This playbook covers what is **different** when PFS is present. It does not repeat the
> task sequencing in [`task-lifecycle.md`](task-lifecycle.md) or the contracts in
> [`federated-api-guide.md`](../federated-api-guide.md) and `capabilities/catalog.json`; read those alongside it.

---

## 1. What PFS gives you — and what it does not

PFS aggregates **read** data from several source Business Automation Workflow systems into one REST surface
(`/rest/bpm/federated/…`): task lists and searches, saved searches, launchable entities,
instance search, system metadata and (v2) team dashboards.

PFS does **not** expose task-mutation endpoints. Claim, release, reassign, priority and
finish are WLE v1 calls sent to the **owning source system** (§6). Visibility in a PFS result
never implies permission to act.

PFS data comes from an index. It can lag the source system by `indexRefreshInterval`.

---

## 2. Before touching any code — read the existing application

1. Find existing Business Automation Workflow calls: `grep` for `/rest/bpm/federated`, `/rest/bpm/wle`, `systemID`,
   `federationResult`, `taskCompletionUrlPrefix`, `restUrlPrefix`.
2. Identify the HTTP client and auth (cookie, Bearer, proxy) — reuse them (§5).
3. Find where a task identity is stored. A federated task is identified by
   **`systemID` + `TKIID`**, not `TKIID` alone. If the existing model keys tasks by `TKIID`
   only, extend the model; do not assume uniqueness across systems.
4. Find how launch URLs are currently built and whether any origin allowlist exists.
5. Find the hosting profile ([`hosting-and-generation.md`](../hosting-and-generation.md)).
6. Choose the smallest integration surface: a federation service module (discovery +
   routing resolver) plus changes to the existing task service.

---

## 3. Identify whether the deployment is federated

Use the strongest signal available, in order:

1. **The user states it** (PFS, "federated", multiple Business Automation Workflow systems behind one portal).
2. **Existing code** already calls `/rest/bpm/federated/…`.
3. **Probe** `GET /rest/bpm/federated/v1/systems` (`PFS-SYSTEMS`): HTTP 200 with a systems
   list suggests PFS. HTTP 404 on `/federated/…` is expected on non-federated Business Automation Workflow. Other
   outcomes (401/403, 5xx, CORS/proxy failures) are **inconclusive** — do not conclude
   "non-federated" from them.

If still unclear, ask once. Do not silently default to NF, and do not call PFS endpoints on
an NF deployment. Never mix NF and PFS paths (a swapped family produces 404).

---

## 4. PFS discovery and API selection

| Need | Use | Evidence |
|---|---|---|
| Task inbox | `PFS-TASK-LIST` `GET /rest/bpm/federated/v1/tasks` | runtime-verified |
| Filtered/ad-hoc tasks | `PFS-ADHOC-SEARCH` `PUT /rest/bpm/federated/v1/tasks` | documentation-verified |
| Saved searches | `PFS-SAVED-*` — follow [`saved-search-management.md`](saved-search-management.md) | CRUD: see catalog (UPDATE is documentation-verified) |
| Launchable processes | `PFS-LAUNCHABLE-ENTITIES` | runtime-verified |
| Source-system list | `PFS-SYSTEMS` (optional) | runtime-verified |
| Instance search | `PFS-INSTANCES-SEARCH` | documentation-verified |
| Team dashboards | `PFS-DASHBOARD-*` (v2) | see §10 |

Rules:

- Use the PFS paths in `references/baw-rest.md`; do not translate NF paths by pattern.
- `size=500` is a limit. Check `totalCount`, page with `offset` and show a truncation
  indicator; see [`non-federated-api-guide.md` §Personal task list](../non-federated-api-guide.md#personal-task-list) and [`federated-api-guide.md` §Federated task list](../federated-api-guide.md#federated-task-list).
- The list endpoint returns task items **and** a top-level `federationResult[]`. Keep both
  in the data layer; the routing fields are in `federationResult[]`, not on the items.
- PFS has no federated equivalent for every NF operation (for example single-task detail,
  see §7). Do not invent one.

---

## 5. Authentication and SSO assumptions

- **Cloud Pak for Business Automation:** `Authorization: Bearer <token>`. The shared IAM token covers PFS and the source
  systems behind the same ingress. CSRF/XSRF: see [`federated-api-guide.md` §CSRF/XSRF for PFS APIs](../federated-api-guide.md#csrfxsrf-for-pfs-apis)
  (observed without an extra header on one deployment; verification-required for PFS mutations).
- **Standalone Business Automation Workflow:** LTPA2 or SAML SSO must span PFS **and every source system**. Cookie
  SSO across origins needs HTTPS (`LtpaToken2` is SameSite=Strict). Confirm with the Business Automation Workflow
  administrator before generating launch or mutation code.
- A PFS session is **not** automatically valid at a source system. Source-system requests
  need a credential valid for that origin: Bearer coverage, spanning SSO, or an allowlisted
  server-side proxy.
- Send credentials only to validated origins (§6).
- API-gateway token exchange is deployment-specific and untested ([`hosting-and-generation.md` §Open deployment decisions](../hosting-and-generation.md#open-deployment-decisions));
  do not invent one.

---

## 6. Source-system identification and routing

Every routed action starts from a task carrying `systemID`:

1. Take `task.systemID` from the PFS item (or validated existing context).
2. Find the **single** `federationResult[]` entry with that `systemID`. Zero or several
   matches → error; fail closed.
3. Require `systemType == SYSTEM_TYPE_WLE` before applying the WLE task contract.
   `SYSTEM_TYPE_WPS` (BPEL) and `SYSTEM_TYPE_CASE` sources are out of scope; unknown or
   missing → fail closed.
4. Take `restUrlPrefix` (mutations) or `taskCompletionUrlPrefix` (launch) from that entry
   and validate against a trusted allowlist keyed by `systemID`: https, no userinfo/query/
   fragment, no trailing slash, no dot-segments, expected path shape. Never use an
   unvalidated response value as a request or navigation target.
5. Build URLs with a URL parser and re-check the resulting origin equals the allowlisted
   origin.

Prefix semantics:

| Field | Used for | Already ends in |
|---|---|---|
| `restUrlPrefix` | WLE REST calls: `{restUrlPrefix}/v1/task/{id}?action=…` | `/rest/bpm/wle` — never append it again |
| `taskCompletionUrlPrefix` | Launch: `{prefix}/process.lsw?…` | `/teamworks` — never append `/rest/bpm/wle` |

Mutations (claim, release, assign back, finish, priority) use the NF operations in
[`task-lifecycle.md`](task-lifecycle.md) §6–7 but the request target is the validated
source system — **never the PFS host**. If you use a proxy, it must resolve the target from
the validated `systemID`, not from a caller-supplied URL (no open proxy).

Cross-origin calls to source systems need source-side CORS allowlisting or an allowlisted
routing proxy.

---

## 7. Task detail and launch routing

- **Detail:** there is no independently supported PFS task-detail operation.
  `CAP-TASK-DETAIL-NF` (`NF-TASK-GET`) may be called against a validated source
  `restUrlPrefix`, but that end-to-end routing is **not verified**. Say so in generated
  notes. The list item already carries the summary fields; prefer those for the row.
- **Launch:** `{taskCompletionUrlPrefix}/process.lsw?zWorkflowState=1&zTaskId={encodeURIComponent(TKIID)}&zResetContext=true`
  using the matching entry. Same iframe/`window.open` rules as NF
  (`task-lifecycle.md` §9): Business Automation Workflow sets `frame-ancestors 'self'`. A portal on a different
  origin than the source system cannot iframe the form unless the prerequisites in
  [`hosting-and-generation.md`](../hosting-and-generation.md) are met (a reverse proxy alone is
  not sufficient) — otherwise use `window.open()`/top-level navigation. One portal origin
  cannot iframe forms from multiple unrelated source origins.
- Treat `TKIID` as an opaque string (numeric or UUID) — truthiness guard only.
- Detail links and launch handlers must carry `systemID` **and** `TKIID`. A link with
  `TKIID` alone is ambiguous across systems.

---

## 8. Partial failures and unavailable source systems

`federationResult[n].statusCode` is the per-system status. Non-200 (expected 408 timeout,
503 unavailable) means that system's data is missing or degraded.

- Do not treat it as a whole-request failure; keep rows from systems that returned 200.
- Show a visible, non-blocking indicator ("Some data sources are unavailable — results may
  be incomplete") and, if useful, which `systemID` is affected.
- Do not hide rows or counts as if complete; do not retry in a tight loop.
- Do not offer actions for a system whose status was degraded at discovery time without
  re-checking it; expect the action to fail.
- De-duplicate by `TKIID` + `systemID` (transient duplicates from index lag).
- Surface `indexRefreshInterval` in freshness text. After a mutation, reconcile the row from
  the **source system**, not from PFS; re-query PFS only after the interval.
- **Status:** non-200 `statusCode` has not been observed in retained testing (both source
  systems were healthy). The handling above is defensive and untested; state that.

---

## 9. FDR requirements

- Catalog records `fdrRequired: false` for the PFS operations/capabilities above. Do not
  add an FDR probe to PFS task-list, search or launch code.
- The WLE v2 dashboards and `POST /rest/bpm/wle/v2/search` (non-federated) are FDR-gated.
  If the portal also uses them, probe with `NF-ADV-QUERIES-LIST` (positive signal). A 503
  `CWTBG0788E` is only a project-observed FDR-disabled signal; 400, 401/403, 404 and
  network errors are inconclusive.
- Whether the PFS v2 dashboards require FDR is not recorded in the catalog; the retained
  run had FDR enabled. Treat it as an open prerequisite for dashboards (§10).

---

## 10. Dashboards and unsupported functionality

PFS v2 team-dashboard operations (`teamsummary`, `teammember/{teamId}`, `teamtasks/{teamId}`
PUT, `teamtasktrend/{teamId}`) were observed to return HTTP 200 on Cloud Pak for Business Automation 26.0.0 PFS;
the checks assert status only, not response schema or workload accuracy.
`teammember/{teamId}/{username}` has no retained success record (documentation-verified).

Therefore:

- Do **not** describe PFS dashboards as runtime-proven or production-ready. Generate them
  behind a validation gate and label them "tested for HTTP status only".
- `teamtasks` uses **PUT** (the IBM-documented GET does not work); never generate GET.
- The user must manage at least one team (HTTP 400 `CWMFS4055E` / `CWMFS4056E` otherwise);
  render an empty/not-a-manager state, never infer manager status from profile fields.
- Handle `federationResult[]` per §8.
- Not supported on PFS in this skill: task detail (§7), task mutations (§6 — source system
  only), process-instance mutations (see below), administrative operations, impersonation.
- Process-instance mutations (suspend, resume, terminate, delete, retry, due date) remain
  documentation-only and gated; do not generate them as portal features.

---

## 11. Cross-user authorization limits

- Authorization is enforced by the source system for the authenticated user. PFS visibility
  is not a permission.
- Act only as the signed-in user: do not act on another user's behalf, do not forward another
  user's token, and do not query another user's tasks to get around server-side limits.
- Manager/team views show what the server returns for the signed-in user; do not widen them
  client-side.
- Expect 401/403/`CWTBG0549E`/state conflicts on actions and handle them as in
  `task-lifecycle.md` §10.

---

## 12. Runtime-evidence limitations (state these in generated notes)

- Search metadata fields, systems list, and dashboard endpoints were observed with HTTP 200 on Cloud Pak for Business Automation 26.0.0 (containerized, Bearer, two federated WLE systems); other search metadata, search actions, and saved searches are documentation-verified without a retained execution record. Traditional/on-premises Business Automation Workflow cookie-SSO federation is not covered.
- Harness checks assert HTTP status, not response schema or behavior.
- **Not verified end to end:** mutations on a PFS-discovered task (`CAP-TASK-LIFECYCLE-PFS`,
  documentation-verified, `partial`), source-system CORS/SSO for those calls, post-mutation
  index reconciliation, true partial failure, `taskCompletionUrlPrefix` page load in an iframe
  (URL pattern and SSO are recorded; no page-load assertion), BPEL/Case source behavior.
- Coverage totals and per-operation labels: see `capabilities/catalog.json` `evidence` blocks. The catalog is authoritative.

---

## 13. Tests to add

- Routing resolver: no match, duplicate match, `systemType != SYSTEM_TYPE_WLE`, non-allowlisted
  or non-https prefix, trailing slash, userinfo → each fails closed with no request sent.
- Launch/mutation URL: exact `{prefix}/process.lsw?…` and `{restUrlPrefix}/v1/task/{id}`; no
  doubled `/rest/bpm/wle`; `encodeURIComponent` on UUID and numeric IDs.
- Same `TKIID` on two `systemID`s yields two distinct rows and two distinct routes.
- Partial failure: one `federationResult` entry with 503 keeps the other rows and shows the
  indicator.
- Dedupe by `TKIID` + `systemID`.
- No NF path is used for a PFS deployment, and no PFS path for NF.
