# Business Automation Workflow REST API Reference

---


## IBM Business Automation Workflow WLE v1 REST Interface

### `GET /rest/bpm/wle/v1/user/current`
**Get current authenticated user profile**

Returns the profile of the currently authenticated Business Automation Workflow user. Used to display user name and avatar in portal header. Request parts=all to include email, managerName, and jobTitle. Evidence: runtime-verified (HTTP status only). Auth: session cookie (credentials: same-origin). Deployment: NF required; FED deployment-dependent.

**Parameters:**
- `parts` (query, string) — Use 'all' to include email, managerName, and jobTitle in the response. Default response omits these fields.

**Responses:**
- `200` — User profile. Response fields: data.fullName, data.displayName, data.userName, data.email (parts=all), data.managerName (parts=all), data.jobTitle (parts=all).
- `401` — Authentication required — no active Business Automation Workflow session.

---

### `GET /rest/bpm/wle/v1/tasks`
**Get personal task list**

Retrieves tasks matching the specified query. Use interaction=claimed_and_available as the documented semantic filter for the current user's claimed and available tasks (documented by IBM). filterByCurrentUser=true is also supported but distinct from the interaction parameter. includeAllBusiness=true was observed locally but is not confirmed in reviewed IBM endpoint specifications — treat as version-specific. Paging via size and offset — totalCount in response for pagination. Evidence: runtime-verified (HTTP status only). Auth: session cookie. Deployment: NF.

**Parameters:**
- `interaction` (query, string) — Documented semantic filter. Use 'claimed_and_available' for current user's actionable tasks.
- `calcStats` (query, boolean) — Request server-computed statistics in the response (data.stats).
- `size` (query, integer) — Maximum tasks returned per page.
- `offset` (query, integer) — Start offset for server-side pagination.
- `filterByCurrentUser` (query, boolean) — Restrict results to the authenticated user's tasks. Distinct from interaction=claimed_and_available — do not treat as interchangeable.

**Responses:**
- `200` — Task list. Response shape: data.items[] (task objects), data.totalCount (pagination), data.offset, data.size, data.stats (when calcStats=true).
- `401` — Authentication required.

### `PUT /rest/bpm/wle/v1/tasks`
**Ad hoc task search with filter body**

Execute a server-side task search with filter criteria passed in the request body. Returns items[] and totalCount. CSRF/XSRF requirement is verification-required per deployment, auth mode and API family; see references/non-federated-api-guide.md section 'XSRF / CSRF for WLE REST mutations'. This endpoint also supports cross-user admin task retrieval.

**Parameters:**
- `body` (body, object) — Search filter criteria as a `SavedSearchDefinition` object. Supported fields: `size`, `interaction`, `owner`, `shared`, `teams`, `conditions`, `fields`, `id`, `aliases`, `organization`, `name`, `sort`. `allClaimed` placement is **UNRESOLVED** (see the `allClaimed` entry below): do not generate code that sends it until the placement is verified on the target environment.
- `allClaimed` (boolean) — **UNRESOLVED / GATED.** Intended meaning: cross-user admin task view. Placement is not established:
  - IBM documentation: the term `allClaimed` does not appear in any IBM Docs, support or Redbooks page searched (keyword search returned 0 hits). The IBM-documented URL parameters of this endpoint are `size`, `offset`, `filterByCurrentUser`, `calcStats`; `filterByCurrentUser=false` is the documented way for an IBM Business Automation Workflow administrator to get an unfiltered (cross-user) search (*Search Execution Resource – PUT*, Business Automation Workflow 19.0.0 `topic=execution-put`; *What's new in V19.0.0.2*). It is **not established** that `allClaimed` is a synonym.
  - Conflicting repo statements (preserved, none verified): (a) query parameter, body returns HTTP 400 — recorded in this file and `personas-and-capabilities.md`; (b) body field together with `assignedToUser` — the `apis/baw-wle-v1.26.0.0.json` description.
  - Runtime evidence: none reproducible. `validate-apis.mjs` has no `allClaimed` check; no captured request/response exists in the repo.
  - Rule: do not generate `allClaimed` request code. If an Administrator cross-user task panel is requested, state that placement is unverified and ask for an on-environment verification (admin and non-admin account) first. The server response remains authoritative.

**Responses:**
- `200` — Search results. Response shape: items[] (task objects), totalCount.
- `401` — Authentication required.

---

### `GET /rest/bpm/wle/v1/task/{taskId}`
**Get task detail for a single task**

Retrieves full task details including description, data, and available actions. runURL field is absent — task launch URL must be constructed manually via /teamworks/process.lsw. All returned values must be rendered via textContent, not unescaped innerHTML. Evidence: runtime-verified (HTTP status only). Auth: session cookie. Deployment: NF.

**Parameters:**
- `taskId` (path, string) *(required)* — Task TKIID identifier.
- `parts` (query, string) — Optional parts qualifier (e.g., 'all').

**Responses:**
- `200` — Task detail object with task metadata. runURL field absent — construct launch URL manually.
- `401` — Authentication required.
- `404` — Task not found or not accessible to the current user.

### `PUT /rest/bpm/wle/v1/task/{taskId}`
**Mutate a task (claim, assign, finish, cancel, update)**

Perform a headless task mutation by passing action as a query parameter. Supported action values: claim — assigns task to current user (retained HTTP 200 on a pre-existing task; the new-task case is commit-message provenance only); assign — reassign: combine with toMe=true, back=true, toUser={username}, toGroup={groupName}, or toTeam={teamName} (back=true retained HTTP 200; cross-user variants documented); finish — complete and submit output params (commit-message provenance only, no retained execution record); cancel — on a claimed task, releases claim and returns State_ready HTTP 200 empty body; does NOT terminate the process instance (commit-message provenance only, no retained execution record); update — update task properties e.g. priority (retained HTTP 200). CSRF/XSRF requirement is verification-required per deployment, auth mode and API family; see references/non-federated-api-guide.md section 'XSRF / CSRF for WLE REST mutations'. Auth: session cookie. Deployment: NF.

**Parameters:**
- `taskId` (path, string) *(required)* — Task TKIID identifier.
- `action` (query, string) *(required)* — Mutation action: claim | assign | finish | cancel | update. 'finish' is the canonical action; 'complete' is a server-side alias.
- `toMe` (query, boolean) — For action=assign: assign task to the current user.
- `back` (query, boolean) — For action=assign: return task to team queue.
- `toUser` (query, string) — For action=assign: assign task to a specific username.
- `toGroup` (query, string) — For action=assign: assign task to a group.
- `toTeam` (query, string) — For action=assign: assign task to a team.
- `params` (query, string) — For action=finish: URL-encoded JSON of task output variable values. Format depends on specific task definition.

**Responses:**
- `200` — Mutation result. For action=cancel on a claimed task: HTTP 200 with empty body, task returns to State_ready. For action=claim/finish: task state updated.
- `400` — Invalid action or parameters. action=cancel on a ready/received task by non-owner returns CWTBG0549E.
- `401` — Authentication required.

---

### `GET /rest/bpm/wle/v1/searches/tasks`
**List saved task searches**

Returns the list of saved task search definitions accessible to the authenticated user. Evidence: runtime-verified for HTTP 200; envelope data.definitions[] per capabilities/catalog.json NF-SAVED-LIST. Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — List of saved search definitions.
- `401` — Authentication required.

### `POST /rest/bpm/wle/v1/searches/tasks`
**Create a saved task search**

Persist a named task search definition. CSRF/XSRF requirement is verification-required per deployment, auth mode and API family; see references/non-federated-api-guide.md section 'XSRF / CSRF for WLE REST mutations'. Evidence: structural-assertion-verified, owned by capabilities/catalog.json NF-SAVED-CREATE: single-deployment live observation on Cloud Pak for Business Automation 26.0.3 SP20 r2 (HTTP 201), no retained test artifact; accept 200 or 201. Auth: session cookie. Deployment: NF.

**Parameters:**
- `body` (body, object) *(required)* — Saved search definition object.

**Responses:**
- `200` — Saved search created (accepted success status; see description).
- `201` — Saved search created (observed on Cloud Pak for Business Automation 26.0.3 SP20 r2; single-deployment observation, see capabilities/catalog.json NF-SAVED-CREATE).
- `401` — Authentication required.

---

### `GET /rest/bpm/wle/v1/searches/tasks/{idOrName}`
**Get a specific saved task search**

Retrieve a specific saved task search by its ID or name. Evidence: structural-assertion-verified, owned by capabilities/catalog.json NF-SAVED-GET: single-deployment live observation on Cloud Pak for Business Automation 26.0.3 SP20 r2, no retained test artifact; the IBM-documented response example also shows the definition directly in data). Auth: session cookie. Deployment: NF.

**Parameters:**
- `idOrName` (path, string) *(required)* — Saved search ID or name.

**Responses:**
- `200` — Saved search definition.
- `404` — Search not found.

### `PUT /rest/bpm/wle/v1/searches/tasks/{idOrName}`
**Update a saved task search**

Update an existing saved task search definition. CSRF/XSRF requirement is verification-required per deployment, auth mode and API family; see references/non-federated-api-guide.md section 'XSRF / CSRF for WLE REST mutations'. Evidence: structural-assertion-verified, owned by capabilities/catalog.json NF-SAVED-UPDATE: single-deployment live observation on Cloud Pak for Business Automation 26.0.3 SP20 r2, no retained test artifact; partial-body (replace vs merge) behaviour is unverified, so send the complete definition. Auth: session cookie. Deployment: NF.

**Parameters:**
- `idOrName` (path, string) *(required)* — Saved search ID or name.
- `body` (body, object) *(required)* — Updated saved search definition.

**Responses:**
- `200` — Saved search updated.

### `DELETE /rest/bpm/wle/v1/searches/tasks/{idOrName}`
**Delete a saved task search**

Delete a named saved task search. CSRF/XSRF requirement is verification-required per deployment, auth mode and API family; see references/non-federated-api-guide.md section 'XSRF / CSRF for WLE REST mutations'. Evidence: structural-assertion-verified, owned by capabilities/catalog.json NF-SAVED-DELETE: single-deployment live observation on Cloud Pak for Business Automation 26.0.3 SP20 r2 (HTTP 204, empty body), no retained test artifact; accept 200 or 204 and do not parse a body unconditionally. Auth: session cookie. Deployment: NF.

**Parameters:**
- `idOrName` (path, string) *(required)* — Saved search ID or name.

**Responses:**
- `200` — Saved search deleted (accepted success status; see description).
- `204` — Saved search deleted, empty body (observed on Cloud Pak for Business Automation 26.0.3 SP20 r2; single-deployment observation, see capabilities/catalog.json NF-SAVED-DELETE).
- `404` — Search not found.

---

### `GET /rest/bpm/wle/v1/searches/actions`
**Get available saved-search actions (saved-search permission discovery)**

Returns the saved-search actions the current user is permitted to perform. Use for **saved-search UI-surface decisions only** — Business Automation Workflow enforces permissions at the saved-search endpoints. Endpoint evidence: runtime-verified for HTTP 200 (the harness asserts the status only; it does not inspect action strings).

**Action policies versus documented response values** (IBM docs: "Configuration properties for action policies", "Administering searches", "Saved Search Definition User Actions Resource – GET"):

| Policy | Defined by IBM | Documented as returned by this endpoint |
|---|---|---|
| `ACTION_CREATE_SHARED_SAVED_SEARCH` | Yes — create shared searches | Yes (IBM sample) |
| `ACTION_ADMINISTER_SHARED_SAVED_SEARCHES` | Yes — create/update/delete shared searches, including others'; reassign owner | Yes (IBM sample) |
| `ACTION_RUN_SAVED_SEARCH` | Yes — run shared searches only; cannot create, delete, modify or duplicate | Not shown in IBM sample; unobserved |
| `ACTION_MANAGE_SAVED_SEARCH` | Yes — restricts personal-search creation/editing to some groups | **No** — IBM: "never explicitly returned" by this API |
| `ACTION_SAVED_SEARCH_SUPER_ADMIN` | Yes — most permissive; CRUD on any search incl. others' private; only via direct saved-search REST calls | Not documented as returned; unobserved. Tolerate it if present, never require it |

- Hierarchy (most → least permissive): SUPER_ADMIN > ADMINISTER_SHARED > CREATE_SHARED > MANAGE > RUN. The most permissive policy among a user's groups prevails. Default for `tw_allusers` is `ACTION_CREATE_SHARED_SAVED_SEARCH`.
- An **empty list** means the user may create only private saved searches (IBM). It does not prohibit private-search creation.
- Failed or unrecognised discovery is not an authorization guarantee: do not hard-block private-search actions on it and do not infer shared/administer rights from it; the server accepts or rejects. Server responses are authoritative.
- **Documented JSON response structure.** IBM's *Saved Search Definition User Actions Resource – GET Method* (Cloud Pak for Business Automation 24.0.1: https://www.ibm.com/docs/en/cloud-paks/cp-biz-automation/24.0.1?topic=ssdua-get) lists `application/json` as the default content type and gives this example: `{"status":"200","data":{"actions":["ACTION_CREATE_SHARED_SAVED_SEARCH","ACTION_ADMINISTER_SHARED_SAVED_SEARCHES"]}}`. The same page also publishes an `application/xml` variant. Minor IBM inconsistency: the JSON schema block names the property `action`, while the example uses `actions`; code must read `data.actions` (the example) and treat anything else as unrecognised. No 26.0.x copy of this page was retrievable.
- **Not yet verified at runtime.** No live Cloud Pak for Business Automation 26.0.0 response has been captured in this repo: the harness asserts HTTP 200 only, so the envelope, the action strings actually returned and which users receive them remain unobserved on 26.0.0. Keep the failed/unrecognised-body rule above.

**Responses:**
- `200` — List of permitted search action identifiers.
- `401` — Authentication required.

---

### `GET /rest/bpm/wle/v1/searches/tasks/meta/fields`
**Get task search metadata — standard fields**

Returns standard task attribute names, types, and valid values available for constructing task search filters. Evidence: runtime-verified (HTTP status only). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — Field metadata list for task search filter construction.

---

### `GET /rest/bpm/wle/v1/searches/tasks/meta/constraintFields`
**Get task search metadata — constraint fields**

Returns constraint-based filter options available for task search construction. Evidence: runtime-verified (HTTP status only). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — Constraint field metadata list.

---

### `GET /rest/bpm/wle/v1/searches/tasks/meta/businessDataFields`
**Get task search metadata — business data fields**

Returns business data variables available for task search. Evidence: runtime-verified (HTTP status only). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — Business data field metadata list.

---

### `GET /rest/bpm/wle/v1/managedGlobalTeams`
**Get global teams managed by the current user**

Returns global teams for which the authenticated user has manager rights. Use this endpoint for manager views in NF environments — do not use embedded team data in the current-user response for manager discovery. Evidence: runtime-verified (HTTP status only). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — List of managed global team objects.

---

### `GET /rest/bpm/wle/v1/globalTeams`
**Get all global teams visible to current user**

Returns all global teams visible to the authenticated user. Evidence: runtime-verified (HTTP status only). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — List of global team objects.

---

### `GET /rest/bpm/wle/v1/globalTeamUsers/{id}`
**Get users in a global team**

Returns the members of the specified global team. Evidence: runtime-verified (HTTP status only). Auth: session cookie. Deployment: NF.

**Parameters:**
- `id` (path, string) *(required)* — Global team ID. Do not pass a Process Designer modeled team ID to this endpoint.

**Responses:**
- `200` — List of user objects in the team.

---

### `GET /rest/bpm/wle/v1/team/{teamId}`
**Get a Process Designer modeled team by ID**

Returns the definition of a Process Designer modeled team by ID. Requires snapshotId parameter. Accepts Process Designer modeled team IDs only — do not pass a global team ID. Evidence: documentation-verified (the harness check passes on HTTP 200, 400 or 404 and does not confirm successful team-definition retrieval). Auth: session cookie. Deployment: NF.

**Parameters:**
- `teamId` (path, string) *(required)* — Process Designer modeled team ID (not a global team ID).
- `snapshotId` (query, string) — Snapshot ID scoping the team definition. Required in practice.

**Responses:**
- `200` — Modeled team definition object.

---

### `GET /rest/bpm/wle/v1/team`
**Get a modeled team by name**

Returns a modeled team definition identified by team name. Evidence: documentation-verified (a development commit message claims a passing check on Cloud Pak for Business Automation 26.0.0, but no execution record was retained, so this is provenance only, not verification). Auth: session cookie. Deployment: NF.

**Parameters:**
- `name` (query, string) *(required)* — Team name.

**Responses:**
- `200` — Modeled team definition object.

---

### `GET /rest/bpm/wle/v1/group/{groupNameOrID}`
**Get a user-registry group**

Returns a user-registry group by name or ID. Note: Business Automation Workflow modeled teams (Process Designer) and runtime user-registry groups use different ID formats and different endpoints. Evidence: documentation-verified (a development commit message claims a passing check, but no execution record was retained, so this is provenance only, not verification). Auth: session cookie. Deployment: NF.

**Parameters:**
- `groupNameOrID` (path, string) *(required)* — User-registry group name or ID.

**Responses:**
- `200` — User-registry group object.

---

### `GET /rest/bpm/wle/v1/exposed`
**Get launchable items (NF — exposed processes and services)**

Returns the list of exposed process applications, services, and case types the authenticated user is authorized to start. This is the correct non-federated endpoint — do not use /rest/bpm/wle/v1/launchableEntities (that is the federated PFS path). Response: data.exposedItemsList[] with itemID, snapshotID, processAppID, type, startURL. IMPORTANT: Do not pass itemID, processAppID, or snapshotID directly to action=start — parse bpdId and processAppId from the startURL query string. Evidence: runtime-verified (HTTP status only). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — Exposed items list. Response: data.exposedItemsList[] with itemID, snapshotID, processAppID, type, startURL.
- `401` — Authentication required.

---

### `POST /rest/bpm/wle/v1/process`
**Start a process instance**

Initiates a new process instance. bpdId identifies the process definition — parse from the startURL field of the /exposed response; do not pass itemID or snapshotID directly. Optional: snapshotId, branchId, processAppId to scope the process version; params as URL-encoded JSON for input variables. Evidence: documentation-verified (a development commit message claims a passing check, but no execution record was retained, so this is provenance only, not verification). Auth: session cookie. Deployment: NF.

**Parameters:**
- `action` (query, string) *(required)* — Must be 'start'.
- `bpdId` (query, string) *(required)* — Process definition ID — parse from startURL of the exposed-items response.
- `processAppId` (query, string) — Process application ID — parse from startURL of the exposed-items response.
- `snapshotId` (query, string) — Snapshot ID to scope the process version.
- `branchId` (query, string) — Branch ID to scope the process version.
- `params` (query, string) — URL-encoded JSON of process input variable values. Format depends on specific process definition.
- `parts` (query, string) — Optional parts qualifier.

**Responses:**
- `200` — Process instance created. New task appears in the task list.
- `400` — Invalid parameters — e.g. CWTBG0012E when using wrong ID fields.
- `401` — Authentication required.

---

## IBM Business Automation Workflow WLE v2 REST Interface

### `POST /rest/bpm/wle/v2/search`
**Advanced task search (WLE v2)**

Execute an advanced task query with richer filter and sort capabilities. Accepts a request body defining filters, sort, and field selection. Returns HTTP 503 when FDR is not enabled — gate on FDR probe before calling this endpoint. Evidence: documentation-verified (a development commit message claims a passing check, but no execution record was retained, so this is provenance only, not verification) — returned 7 results on Cloud Pak for Business Automation 26.0.0. Requires Business Automation Workflow 24+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Parameters:**
- `body` (body, object) *(required)* — Search request body defining filters, sort, and field selection.

**Responses:**
- `200` — Search results.
- `503` — FDR not enabled on this Business Automation Workflow instance. Gate on FDR probe before generating code for this endpoint.

---

### `GET /rest/bpm/wle/v2/search/queries`
**List reusable search query definitions (WLE v2)**

Returns the list of named reusable search query definitions. Requires Business Automation Workflow 24+ with FDR enabled. Evidence: documentation-verified (a development commit message claims a passing check on Cloud Pak for Business Automation 26.0.0, but no execution record was retained, so this is provenance only, not verification). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — List of reusable search query definitions.
- `503` — FDR not enabled.

### `POST /rest/bpm/wle/v2/search/queries`
**Create a reusable search query definition (WLE v2)**

Create a named reusable search query definition. Requires Business Automation Workflow 24+ with FDR enabled. Evidence: documentation-verified. Auth: session cookie. Deployment: NF.

**Parameters:**
- `body` (body, object) *(required)* — Reusable search query definition object.

**Responses:**
- `200` — Reusable query created.
- `503` — FDR not enabled.

---

### `GET /rest/bpm/wle/v2/dashboards/teamsummary`
**Get all-teams performance summary (WLE v2 dashboard)**

Returns summary data (aggregate task counts, overdue/at-risk indicators) for all teams the authenticated user can manage or view. NF equivalent of the PFS team-summary endpoint. HTTP 400 CWTBG0805E returned when caller manages no teams. Gate on FDR probe — returns HTTP 503 when FDR is not enabled. Evidence: runtime-verified (HTTP status only). Requires Business Automation Workflow 24+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — All-teams summary. Response: summaries[] with teamId, name, totalOpenTasks, countOverdue, countAtRisk, countOnTrack, tasksCompletedToday.
- `400` — CWTBG0805E — caller manages no teams.
- `503` — FDR not enabled on this Business Automation Workflow instance.

---

### `GET /rest/bpm/wle/v2/dashboards/teamsummary/{teamId}`
**Get single team performance summary (WLE v2 dashboard)**

Returns aggregate task counts, overdue/at-risk indicators, and workload summary for one team. Gate on FDR probe. HTTP 400 CWTBG0806E when caller does not manage the requested team. Evidence: runtime-verified (HTTP status only). Requires Business Automation Workflow 24+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.

**Responses:**
- `200` — Single team summary object.
- `400` — CWTBG0806E — caller does not manage this team.
- `503` — FDR not enabled.

---

### `GET /rest/bpm/wle/v2/dashboards/teammember/{teamId}`
**Get team member workload list (WLE v2 dashboard)**

Returns workload data for all members of a specific team. Each entry includes task counts and risk indicators. Gate on FDR probe. Evidence: runtime-verified (HTTP status only). Requires Business Automation Workflow 24+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.

**Responses:**
- `200` — Team member workload list. Response: teamMemberList[] with name, fullName, emailAddress, assignedTasks, tasksCompletedToday.
- `503` — FDR not enabled.

---

### `GET /rest/bpm/wle/v2/dashboards/teammember/{teamId}/{username}`
**Get single team member workload (WLE v2 dashboard)**

Returns task load, overdue, and at-risk counts for a single named member. HTTP 400 when username is not a member of the team. Evidence: documentation-verified (no harness check targets this form). Requires Business Automation Workflow 24+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.
- `username` (path, string) *(required)* — Team member username.

**Responses:**
- `200` — Single member workload. Response: summary{} with name, fullName, emailAddress, totalOpenTasks, countOverdue, countAtRisk, countOnTrack, tasksCompletedToday.
- `400` — Username is not a member of the specified team.
- `503` — FDR not enabled.

---

### `PUT /rest/bpm/wle/v2/dashboards/teamtasks`
**Get tasks for all teams (WLE v2 dashboard)**

Returns the task list across all teams accessible to the authenticated user. Uses PUT (not GET) with filter criteria in request body. Gate on FDR probe. CSRF/XSRF requirement is verification-required per deployment, auth mode and API family; see references/non-federated-api-guide.md section 'XSRF / CSRF for WLE REST mutations'. Evidence: documentation-verified (success is recorded only in a development commit message; no retained log). Requires Business Automation Workflow 24.0.0.1+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Parameters:**
- `body` (body, object) — Filter criteria for the team task query.

**Responses:**
- `200` — Team tasks. Response: items[] + totalCount.
- `503` — FDR not enabled.

---

### `PUT /rest/bpm/wle/v2/dashboards/teamtasks/{teamId}`
**Get tasks for a specific team (WLE v2 dashboard)**

Returns the task list for one team. Uses PUT (not GET) with filter criteria in request body. Gate on FDR probe. CSRF/XSRF requirement is verification-required per deployment, auth mode and API family; see references/non-federated-api-guide.md section 'XSRF / CSRF for WLE REST mutations'. Evidence: documentation-verified (no harness check targets the single-team teamtasks form). Requires Business Automation Workflow 24+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.
- `body` (body, object) — Filter criteria for the team task query.

**Responses:**
- `200` — Team tasks. Response: items[] + totalCount.
- `503` — FDR not enabled.

---

### `GET /rest/bpm/wle/v2/dashboards/teamtasktrend/{teamId}`
**Get team task trend (WLE v2 dashboard)**

Returns task turnover trend data (tasks created vs completed over time) for a specific team. Enables trend charts in NF manager dashboard views. Gate on FDR probe. Evidence: runtime-verified (HTTP status only). Requires Business Automation Workflow 24+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.

**Responses:**
- `200` — Task trend data. Response: data[] array of { created: N, completed: N, timestamp: '...' } entries.
- `503` — FDR not enabled.

---

## IBM Business Automation Workflow PFS v1 Federated REST Interface

### `GET /rest/bpm/federated/v1/tasks`
**Get federated task list (PFS)**

Retrieves tasks across all federated Business Automation Workflow systems via PFS. Response includes top-level federationResult[] (one entry per source system) and items[] where each item carries a systemID. Map task.systemID to the matching federationResult entry to obtain taskCompletionUrlPrefix and restUrlPrefix for routing. Partial results may be returned when source systems are unavailable — check federationResult[].statusCode. Evidence: runtime-verified (HTTP status only) against Cloud Pak for Business Automation 26.0.0 with two federated Business Automation Workflow instances. Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `calcStats` (query, boolean) — Request server-computed statistics.
- `size` (query, integer) — Maximum tasks returned per page.
- `offset` (query, integer) — Start offset for pagination.

**Responses:**
- `200` — Federated task list. Response: items[] (each with systemID), totalCount, and top-level federationResult[] (systemID, statusCode, indexRefreshInterval, taskCompletionUrlPrefix, restUrlPrefix).
- `401` — Authentication required.
- `404` — This endpoint returns 404 on non-federated Business Automation Workflow — requires PFS deployment.

### `PUT /rest/bpm/federated/v1/tasks`
**Ad hoc federated task search (PFS)**

Execute an ad hoc federated task search with filter criteria in request body. Returns federated items[] + totalCount. CSRF/XSRF requirement is verification-required per deployment, auth mode and API family; see references/non-federated-api-guide.md section 'XSRF / CSRF for WLE REST mutations'. Evidence: documentation-verified (a development commit message claims a passing check on Cloud Pak for Business Automation 24.0.0, but no execution record was retained, so this is provenance only, not verification). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `body` (body, object) — Search filter criteria object.

**Responses:**
- `200` — Search results. Response: items[], totalCount.

---

### `GET /rest/bpm/federated/v1/systems`
**Get federated system list (PFS)**

Returns a list of federated Business Automation Workflow systems registered with PFS including systemID, restUrlPrefix, taskCompletionUrlPrefix, version, indexRefreshInterval, and statusCode. This call is optional — per-task federationResult fields in the task-list response provide routing information on demand without a separate systems call. Evidence: runtime-verified (HTTP status only) — two federated systems returned. Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — List of federated system objects. Each entry: systemID, restUrlPrefix, taskCompletionUrlPrefix, version, indexRefreshInterval, statusCode.

---

### `GET /rest/bpm/federated/v1/launchableEntities`
**Get federated launchable entities (PFS)**

Retrieves the list of exposed launchable processes and services across all federated Business Automation Workflow systems. Equivalent to /rest/bpm/wle/v1/exposed but for PFS environments. Evidence: runtime-verified (HTTP status only) against Cloud Pak for Business Automation 26.0.0. Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — Federated launchable entity list.

---

### `GET /rest/bpm/federated/v1/searches/tasks`
**List federated saved task searches (PFS)**

Returns the list of saved task search definitions in the PFS context. Evidence: documentation-verified (a development commit message claims a passing check on Cloud Pak for Business Automation 24.0.0, but no execution record was retained, so this is provenance only, not verification). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — List of federated saved search definitions.

### `POST /rest/bpm/federated/v1/searches/tasks`
**Create a federated saved task search (PFS)**

Persist a named federated task search definition. CSRF/XSRF requirement is verification-required (see references/federated-api-guide.md). Evidence: documentation-verified (a development commit message claims a passing check on Cloud Pak for Business Automation 24.0.0, but no execution record was retained, so this is provenance only, not verification). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `body` (body, object) *(required)* — Saved search definition object.

**Responses:**
- `200` — Saved search created.

---

### `GET /rest/bpm/federated/v1/searches/tasks/{idOrName}`
**Get a specific federated saved task search (PFS)**

Retrieve a specific federated saved task search by ID or name. Evidence: documentation-verified (a development commit message claims a passing check on Cloud Pak for Business Automation 24.0.0, but no execution record was retained, so this is provenance only, not verification). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `idOrName` (path, string) *(required)* — Saved search ID or name.

**Responses:**
- `200` — Saved search definition.

### `PUT /rest/bpm/federated/v1/searches/tasks/{idOrName}`
**Update a federated saved task search (PFS)**

Update an existing federated saved task search definition. CSRF/XSRF requirement is verification-required (see references/federated-api-guide.md). Evidence: documentation-verified (create, read and delete were exercised only in a development commit message; update was not independently tested). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `idOrName` (path, string) *(required)* — Saved search ID or name.
- `body` (body, object) *(required)* — Updated saved search definition.

**Responses:**
- `200` — Saved search updated.

### `DELETE /rest/bpm/federated/v1/searches/tasks/{idOrName}`
**Delete a federated saved task search (PFS)**

Delete a named federated saved task search. CSRF/XSRF requirement is verification-required (see references/federated-api-guide.md). Evidence: documentation-verified (a development commit message claims a passing check on Cloud Pak for Business Automation 24.0.0, but no execution record was retained, so this is provenance only, not verification). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `idOrName` (path, string) *(required)* — Saved search ID or name.

**Responses:**
- `200` — Saved search deleted.

---

### `GET /rest/bpm/federated/v1/searches/actions`
**Get federated search actions (PFS)**

Returns the set of federated saved-search actions the current user is permitted to perform. NOTE: This path is /searches/actions — not under /searches/tasks/actions. Evidence: documentation-verified (a development commit message claims a passing check on Cloud Pak for Business Automation 24.0.0, but no execution record was retained, so this is provenance only, not verification). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — Array of permitted federated search action identifiers.

---

### `GET /rest/bpm/federated/v1/searches/meta/fields`
**Get PFS search metadata — standard fields**

Returns task search field definitions for federated deployments. NOTE: PFS metadata paths are under /searches/meta/ — not under /searches/tasks/meta/. Evidence: runtime-verified (HTTP status only). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — Field metadata list for PFS task search filter construction.

---

### `GET /rest/bpm/federated/v1/searches/meta/constraintFields`
**Get PFS search metadata — constraint fields**

Returns constraint-based filter options for federated task search. NOTE: path is /searches/meta/constraintFields. Evidence: documentation-verified (a development commit message claims a passing check on Cloud Pak for Business Automation 24.0.0, but no execution record was retained, so this is provenance only, not verification). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — Constraint field metadata list.

---

### `GET /rest/bpm/federated/v1/searches/meta/businessDataFields`
**Get PFS search metadata — business data fields**

Returns business data variables available for PFS task search. Evidence: documentation-verified (a development commit message claims a passing check on Cloud Pak for Business Automation 24.0.0, but no execution record was retained, so this is provenance only, not verification). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — Business data field metadata list.

---

### `GET /rest/bpm/federated/v1/searches/meta/taskStatus`
**Get PFS search metadata — task status values**

Returns valid task status values for PFS search filters. Evidence: documentation-verified (a development commit message claims a passing check on Cloud Pak for Business Automation 24.0.0, but no execution record was retained, so this is provenance only, not verification). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — Task status value list.

---

### `GET /rest/bpm/federated/v1/searches/meta/priority`
**Get PFS search metadata — priority values**

Returns valid task priority values for PFS search filters. Evidence: documentation-verified (a development commit message claims a passing check on Cloud Pak for Business Automation 24.0.0, but no execution record was retained, so this is provenance only, not verification). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — Priority value list.

---

### `PUT /rest/bpm/federated/v1/instances`
**Federated process-instance search (PFS)**

Execute a federated process-instance search with filter criteria in request body. Evidence: documentation-verified (a development commit message claims a passing check on Cloud Pak for Business Automation 24.0.0, but no execution record was retained, so this is provenance only, not verification). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `body` (body, object) — Process-instance search filter criteria.

**Responses:**
- `200` — Federated process-instance search results.

---

### `GET /rest/bpm/federated/v1/globalTeams`
**Get federated global teams (PFS)**

Returns teams in a federated context. Separate from the NF team endpoints in /rest/bpm/wle/v1/. Evidence: documentation-verified (a development commit message claims a passing check, but no execution record was retained, so this is provenance only, not verification). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — List of federated global team objects.

---

## IBM Business Automation Workflow PFS v2 Federated REST Interface

### `GET /rest/bpm/federated/v2/dashboards/teamsummary`
**Get all-teams performance summary (PFS v2 dashboard)**

Returns summary data (aggregate task counts, overdue/at-risk indicators) for all teams the authenticated user can manage or view, across all federated systems. Response includes summaries[] and federationResult[]. Enables manager team-overview dashboard in FED environments. Evidence: runtime-verified (HTTP status only). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — All-teams summary. Response: summaries[] with teamId, name, totalOpenTasks, countOverdue, countAtRisk, countOnTrack, tasksCompletedToday, federationResult[].
- `401` — Authentication required.

---

### `GET /rest/bpm/federated/v2/dashboards/teamsummary/{teamId}`
**Get single team performance summary (PFS v2 dashboard)**

Returns aggregate task counts, overdue/at-risk indicators, and workload summary for one team across federated systems. Response includes summary{} (single team shape) and federationResult[]. Evidence: runtime-verified (HTTP status only). HTTP 400 when caller does not manage the team. Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.

**Responses:**
- `200` — Single team summary. Response: summary{} with federationResult[].
- `400` — Caller does not manage the requested team.

---

### `GET /rest/bpm/federated/v2/dashboards/teammember/{teamId}`
**Get team member workload list (PFS v2 dashboard)**

Returns workload data for all members of a specific team across federated systems. Response includes teamMemberList[] and federationResult[]. Evidence: runtime-verified (HTTP status only). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.

**Responses:**
- `200` — Team member workload list. Response: teamMemberList[] with name, fullName, emailAddress, assignedTasks, tasksCompletedToday, federationResult[].

---

### `GET /rest/bpm/federated/v2/dashboards/teammember/{teamId}/{username}`
**Get single team member workload (PFS v2 dashboard)**

Returns task load, overdue, and at-risk counts for a single named team member across federated systems. Response includes summary{} and federationResult[]. HTTP 400 when username is not a member of the team. Evidence: documentation-verified (success is recorded only in a development commit message; no retained log). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.
- `username` (path, string) *(required)* — Team member username.

**Responses:**
- `200` — Single member workload. Response: summary{} with name, fullName, totalOpenTasks, countOverdue, countAtRisk, federationResult[].
- `400` — Username is not a member of the specified team.

---

### `PUT /rest/bpm/federated/v2/dashboards/teamtasks/{teamId}`
**Get tasks for a team (PFS v2 dashboard)**

Returns the task list for a team across all federated systems. Uses PUT (not GET) with filter criteria in request body. Response includes items[], totalCount, and federationResult[]. Evidence: runtime-verified (HTTP status only). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.
- `body` (body, object) — Filter criteria for the team task query.

**Responses:**
- `200` — Team tasks. Response: items[], totalCount, federationResult[].

---

### `GET /rest/bpm/federated/v2/dashboards/teamtasktrend/{teamId}`
**Get team task trend (PFS v2 dashboard)**

Returns task turnover trend data (tasks created vs completed over time) for a specific team across federated systems. Response: data[] and federationResult[]. Evidence: runtime-verified (HTTP status only). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.

**Responses:**
- `200` — Task trend data. Response: data[] of { created: N, completed: N, timestamp: '...' } entries, federationResult[].
