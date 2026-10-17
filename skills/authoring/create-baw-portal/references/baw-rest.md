# BAW REST API Reference

---


## IBM Business Automation Workflow WLE v1 REST Interface

### `GET /rest/bpm/wle/v1/user/current`
**Get current authenticated user profile**

Returns the profile of the currently authenticated BAW user. Used to display user name and avatar in portal header. Request parts=all to include email, managerName, and jobTitle. Evidence: VERIFIED IN ON-PREM BAW (NF01). Auth: session cookie (credentials: same-origin). Deployment: NF required; FED deployment-dependent.

**Parameters:**
- `parts` (query, string) — Use 'all' to include email, managerName, and jobTitle in the response. Default response omits these fields.

**Responses:**
- `200` — User profile. Response fields: data.fullName, data.displayName, data.userName, data.email (parts=all), data.managerName (parts=all), data.jobTitle (parts=all).
- `401` — Authentication required — no active BAW session.

---

### `GET /rest/bpm/wle/v1/tasks`
**Get personal task list**

Retrieves tasks matching the specified query. Use interaction=claimed_and_available as the documented semantic filter for the current user's claimed and available tasks (VERIFIED BY IBM DOCUMENTATION). filterByCurrentUser=true is also supported but distinct from the interaction parameter. includeAllBusiness=true was observed locally but is not confirmed in reviewed IBM endpoint specifications — treat as version-specific. Paging via size and offset — totalCount in response for pagination. Evidence: VERIFIED IN ON-PREM BAW (NF02, NF03, NF04). Auth: session cookie. Deployment: NF.

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

Execute a server-side task search with filter criteria passed in the request body. Returns items[] and totalCount. Session cookie (credentials: same-origin) is sufficient — no bpm-csrf-token required for WLE v1 same-origin browser portals. This endpoint also supports cross-user admin task retrieval: include allClaimed=true and an assignedToUser filter in the body; requires administrator-level permission (NOT YET RUNTIME-VERIFIED for admin cross-user use — T2.21). Evidence: VERIFIED IN ON-PREM BAW (NF14/NF23 standard use). Deployment: NF.

**Parameters:**
- `body` (body, object) — Search filter criteria object. Supports standard task filter fields. Include allClaimed=true and assignedToUser for admin cross-user queries (admin permission required).

**Responses:**
- `200` — Search results. Response shape: items[] (task objects), totalCount.
- `401` — Authentication required.

---

### `GET /rest/bpm/wle/v1/task/{taskId}`
**Get task detail for a single task**

Retrieves full task details including description, data, and available actions. runURL field is absent — task launch URL must be constructed manually via /teamworks/process.lsw. All returned values must be rendered via textContent, not unescaped innerHTML. Evidence: VERIFIED IN ON-PREM BAW (NF06). Auth: session cookie. Deployment: NF.

**Parameters:**
- `taskId` (path, string) *(required)* — Task TKIID identifier.
- `parts` (query, string) — Optional parts qualifier (e.g., 'all').

**Responses:**
- `200` — Task detail object with task metadata. runURL field absent — construct launch URL manually.
- `401` — Authentication required.
- `404` — Task not found or not accessible to the current user.

### `PUT /rest/bpm/wle/v1/task/{taskId}`
**Mutate a task (claim, assign, finish, cancel, update)**

Perform a headless task mutation by passing action as a query parameter. Supported action values: claim — assigns task to current user (NF23/NF28 VERIFIED); assign — reassign: combine with toMe=true, back=true, toUser={username}, toGroup={groupName}, or toTeam={teamName} (NF24 back=true VERIFIED; cross-user variants documented); finish — complete and submit output params (NF29 VERIFIED); cancel — on a claimed task, releases claim and returns State_ready HTTP 200 empty body; does NOT terminate the process instance (NF36 VERIFIED); update — update task properties e.g. priority (NF25 VERIFIED). Session cookie (credentials: same-origin) is sufficient for all WLE v1 mutations — no bpm-csrf-token required. Auth: session cookie. Deployment: NF.

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

Returns the list of saved task search definitions accessible to the authenticated user. Evidence: VERIFIED IN ON-PREM BAW (NF15). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — List of saved search definitions.
- `401` — Authentication required.

### `POST /rest/bpm/wle/v1/searches/tasks`
**Create a saved task search**

Persist a named task search definition. Session cookie (credentials: same-origin) is sufficient — no bpm-csrf-token required. Evidence: VERIFIED IN ON-PREM BAW (NF31). Auth: session cookie. Deployment: NF.

**Parameters:**
- `body` (body, object) *(required)* — Saved search definition object.

**Responses:**
- `200` — Saved search created.
- `401` — Authentication required.

---

### `GET /rest/bpm/wle/v1/searches/tasks/{idOrName}`
**Get a specific saved task search**

Retrieve a specific saved task search by its ID or name. Evidence: VERIFIED IN ON-PREM BAW (NF32). Auth: session cookie. Deployment: NF.

**Parameters:**
- `idOrName` (path, string) *(required)* — Saved search ID or name.

**Responses:**
- `200` — Saved search definition.
- `404` — Search not found.

### `PUT /rest/bpm/wle/v1/searches/tasks/{idOrName}`
**Update a saved task search**

Update an existing saved task search definition. Session cookie is sufficient — no bpm-csrf-token required. Evidence: VERIFIED IN ON-PREM BAW (NF34). Auth: session cookie. Deployment: NF.

**Parameters:**
- `idOrName` (path, string) *(required)* — Saved search ID or name.
- `body` (body, object) *(required)* — Updated saved search definition.

**Responses:**
- `200` — Saved search updated.

### `DELETE /rest/bpm/wle/v1/searches/tasks/{idOrName}`
**Delete a saved task search**

Delete a named saved task search. Session cookie is sufficient — no bpm-csrf-token required. Evidence: VERIFIED IN ON-PREM BAW (NF33). Auth: session cookie. Deployment: NF.

**Parameters:**
- `idOrName` (path, string) *(required)* — Saved search ID or name.

**Responses:**
- `200` — Saved search deleted.
- `404` — Search not found.

---

### `GET /rest/bpm/wle/v1/searches/actions`
**Get available search actions (admin rights detection)**

Returns the set of saved-search actions the current user is permitted to perform. Presence of ACTION_ADMINISTER_SHARED_SAVED_SEARCHES or ACTION_SAVED_SEARCH_SUPER_ADMIN indicates admin-level rights. Use for UI-surface decisions only — BAW enforces permissions at the data endpoint. Evidence: VERIFIED IN ON-PREM BAW (NF21). Auth: session cookie. Deployment: NF. NOTE: Admin-scoped code generation should not proceed until admin-rights detection is runtime-verified for that deployment (T2.20 — not yet verified for admin use).

**Responses:**
- `200` — Array of permitted search action identifiers.
- `401` — Authentication required.

---

### `GET /rest/bpm/wle/v1/searches/tasks/meta/fields`
**Get task search metadata — standard fields**

Returns standard task attribute names, types, and valid values available for constructing task search filters. Evidence: VERIFIED IN ON-PREM BAW (NF16). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — Field metadata list for task search filter construction.

---

### `GET /rest/bpm/wle/v1/searches/tasks/meta/constraintFields`
**Get task search metadata — constraint fields**

Returns constraint-based filter options available for task search construction. Evidence: VERIFIED IN ON-PREM BAW (NF17). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — Constraint field metadata list.

---

### `GET /rest/bpm/wle/v1/searches/tasks/meta/businessDataFields`
**Get task search metadata — business data fields**

Returns business data variables available for task search. Evidence: VERIFIED IN ON-PREM BAW (NF20). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — Business data field metadata list.

---

### `GET /rest/bpm/wle/v1/managedGlobalTeams`
**Get global teams managed by the current user**

Returns global teams for which the authenticated user has manager rights. Use this endpoint for manager views in NF environments — do not use embedded team data in the current-user response for manager discovery. Evidence: VERIFIED IN ON-PREM BAW (NF07). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — List of managed global team objects.

---

### `GET /rest/bpm/wle/v1/globalTeams`
**Get all global teams visible to current user**

Returns all global teams visible to the authenticated user. Evidence: VERIFIED IN ON-PREM BAW (NF08). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — List of global team objects.

---

### `GET /rest/bpm/wle/v1/globalTeamUsers/{id}`
**Get users in a global team**

Returns the members of the specified global team. Evidence: VERIFIED IN ON-PREM BAW (NF18). Auth: session cookie. Deployment: NF.

**Parameters:**
- `id` (path, string) *(required)* — Global team ID. Do not pass a Process Designer modeled team ID to this endpoint.

**Responses:**
- `200` — List of user objects in the team.

---

### `GET /rest/bpm/wle/v1/team/{teamId}`
**Get a Process Designer modeled team by ID**

Returns the definition of a Process Designer modeled team by ID. Requires snapshotId parameter. Accepts Process Designer modeled team IDs only — do not pass a global team ID. Evidence: VERIFIED IN ON-PREM BAW (NF19). Auth: session cookie. Deployment: NF.

**Parameters:**
- `teamId` (path, string) *(required)* — Process Designer modeled team ID (not a global team ID).
- `snapshotId` (query, string) — Snapshot ID scoping the team definition. Required in practice.

**Responses:**
- `200` — Modeled team definition object.

---

### `GET /rest/bpm/wle/v1/team`
**Get a modeled team by name**

Returns a modeled team definition identified by team name. Evidence: VERIFIED IN ON-PREM BAW (NF37 — CP4BA 26.0.0). Auth: session cookie. Deployment: NF.

**Parameters:**
- `name` (query, string) *(required)* — Team name.

**Responses:**
- `200` — Modeled team definition object.

---

### `GET /rest/bpm/wle/v1/group/{groupNameOrID}`
**Get a user-registry group**

Returns a user-registry group by name or ID. Note: BAW modeled teams (Process Designer) and runtime user-registry groups use different ID formats and different endpoints. Evidence: VERIFIED IN ON-PREM BAW (NF38 — CP4BA 26.0.0). Auth: session cookie. Deployment: NF.

**Parameters:**
- `groupNameOrID` (path, string) *(required)* — User-registry group name or ID.

**Responses:**
- `200` — User-registry group object.

---

### `GET /rest/bpm/wle/v1/exposed`
**Get launchable items (NF — exposed processes and services)**

Returns the list of exposed process applications, services, and case types the authenticated user is authorized to start. This is the correct non-federated endpoint — do not use /rest/bpm/wle/v1/launchableEntities (that is the federated PFS path). Response: data.exposedItemsList[] with itemID, snapshotID, processAppID, type, startURL. IMPORTANT: Do not pass itemID, processAppID, or snapshotID directly to action=start — parse bpdId and processAppId from the startURL query string. Evidence: VERIFIED IN ON-PREM BAW (NF09, NF22). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — Exposed items list. Response: data.exposedItemsList[] with itemID, snapshotID, processAppID, type, startURL.
- `401` — Authentication required.

---

### `POST /rest/bpm/wle/v1/process`
**Start a process instance**

Initiates a new process instance. bpdId identifies the process definition — parse from the startURL field of the /exposed response; do not pass itemID or snapshotID directly. Optional: snapshotId, branchId, processAppId to scope the process version; params as URL-encoded JSON for input variables. Evidence: VERIFIED IN ON-PREM BAW (NF26). Auth: session cookie. Deployment: NF.

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

Execute an advanced task query with richer filter and sort capabilities. Accepts a request body defining filters, sort, and field selection. Returns HTTP 503 when FDR is not enabled — gate on FDR probe before calling this endpoint. Evidence: VERIFIED IN ON-PREM BAW (NF35) — returned 7 results on CP4BA 26.0.0. Requires BAW 24+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Parameters:**
- `body` (body, object) *(required)* — Search request body defining filters, sort, and field selection.

**Responses:**
- `200` — Search results.
- `503` — FDR not enabled on this BAW instance. Gate on FDR probe before generating code for this endpoint.

---

### `GET /rest/bpm/wle/v2/search/queries`
**List reusable search query definitions (WLE v2)**

Returns the list of named reusable search query definitions. Requires BAW 24+ with FDR enabled. Evidence: VERIFIED IN ON-PREM BAW (NF40 — CP4BA 26.0.0). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — List of reusable search query definitions.
- `503` — FDR not enabled.

### `POST /rest/bpm/wle/v2/search/queries`
**Create a reusable search query definition (WLE v2)**

Create a named reusable search query definition. Requires BAW 24+ with FDR enabled. Evidence: DOCUMENTED (T2.4). Auth: session cookie. Deployment: NF.

**Parameters:**
- `body` (body, object) *(required)* — Reusable search query definition object.

**Responses:**
- `200` — Reusable query created.
- `503` — FDR not enabled.

---

### `GET /rest/bpm/wle/v2/dashboards/teamsummary`
**Get all-teams performance summary (WLE v2 dashboard)**

Returns summary data (aggregate task counts, overdue/at-risk indicators) for all teams the authenticated user can manage or view. NF equivalent of the PFS T3.5 endpoint. HTTP 400 CWTBG0805E returned when caller manages no teams. Gate on FDR probe — returns HTTP 503 when FDR is not enabled. Evidence: VERIFIED IN ON-PREM BAW (NF10). Requires BAW 24+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — All-teams summary. Response: summaries[] with teamId, name, totalOpenTasks, countOverdue, countAtRisk, countOnTrack, tasksCompletedToday.
- `400` — CWTBG0805E — caller manages no teams.
- `503` — FDR not enabled on this BAW instance.

---

### `GET /rest/bpm/wle/v2/dashboards/teamsummary/{teamId}`
**Get single team performance summary (WLE v2 dashboard)**

Returns aggregate task counts, overdue/at-risk indicators, and workload summary for one team. Gate on FDR probe. HTTP 400 CWTBG0806E when caller does not manage the requested team. Evidence: VERIFIED IN ON-PREM BAW (NF11). Requires BAW 24+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.

**Responses:**
- `200` — Single team summary object.
- `400` — CWTBG0806E — caller does not manage this team.
- `503` — FDR not enabled.

---

### `GET /rest/bpm/wle/v2/dashboards/teammember/{teamId}`
**Get team member workload list (WLE v2 dashboard)**

Returns workload data for all members of a specific team. Each entry includes task counts and risk indicators. Gate on FDR probe. Evidence: VERIFIED IN ON-PREM BAW (NF13). Requires BAW 24+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.

**Responses:**
- `200` — Team member workload list. Response: teamMemberList[] with name, fullName, emailAddress, assignedTasks, tasksCompletedToday.
- `503` — FDR not enabled.

---

### `GET /rest/bpm/wle/v2/dashboards/teammember/{teamId}/{username}`
**Get single team member workload (WLE v2 dashboard)**

Returns task load, overdue, and at-risk counts for a single named member. HTTP 400 when username is not a member of the team. Evidence: VERIFIED IN ON-PREM BAW (NF on BAW 26.0.0 CP4BA — also on PFS). Requires BAW 24+ with FDR enabled. Auth: session cookie. Deployment: NF.

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

Returns the task list across all teams accessible to the authenticated user. Uses PUT (not GET) with filter criteria in request body. Gate on FDR probe. Session cookie is sufficient — no bpm-csrf-token required. Evidence: VERIFIED IN ON-PREM BAW (NF39 — CP4BA 26.0.0). Requires BAW 24.0.0.1+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Parameters:**
- `body` (body, object) — Filter criteria for the team task query.

**Responses:**
- `200` — Team tasks. Response: items[] + totalCount.
- `503` — FDR not enabled.

---

### `PUT /rest/bpm/wle/v2/dashboards/teamtasks/{teamId}`
**Get tasks for a specific team (WLE v2 dashboard)**

Returns the task list for one team. Uses PUT (not GET) with filter criteria in request body. Gate on FDR probe. Session cookie is sufficient — no bpm-csrf-token required. Evidence: VERIFIED IN ON-PREM BAW (NF13 — both all-teams and single-team forms). Requires BAW 24+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.
- `body` (body, object) — Filter criteria for the team task query.

**Responses:**
- `200` — Team tasks. Response: items[] + totalCount.
- `503` — FDR not enabled.

---

### `GET /rest/bpm/wle/v2/dashboards/teamtasktrend/{teamId}`
**Get team task trend (WLE v2 dashboard)**

Returns task turnover trend data (tasks created vs completed over time) for a specific team. Enables trend charts in NF manager dashboard views. Gate on FDR probe. Evidence: VERIFIED IN ON-PREM BAW (NF12). Requires BAW 24+ with FDR enabled. Auth: session cookie. Deployment: NF.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.

**Responses:**
- `200` — Task trend data. Response: data[] array of { created: N, completed: N, timestamp: '...' } entries.
- `503` — FDR not enabled.

---

## IBM Business Automation Workflow PFS v1 Federated REST Interface

### `GET /rest/bpm/federated/v1/tasks`
**Get federated task list (PFS)**

Retrieves tasks across all federated BAW systems via PFS. Response includes top-level federationResult[] (one entry per source system) and items[] where each item carries a systemID. Map task.systemID to the matching federationResult entry to obtain taskCompletionUrlPrefix and restUrlPrefix for routing. Partial results may be returned when source systems are unavailable — check federationResult[].statusCode. Evidence: VERIFIED IN ON-PREM BAW (PFS01/PFS02) against CP4BA 26.0.0 with two federated BAW instances. Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `calcStats` (query, boolean) — Request server-computed statistics.
- `size` (query, integer) — Maximum tasks returned per page.
- `offset` (query, integer) — Start offset for pagination.

**Responses:**
- `200` — Federated task list. Response: items[] (each with systemID), totalCount, and top-level federationResult[] (systemID, statusCode, indexRefreshInterval, taskCompletionUrlPrefix, restUrlPrefix).
- `401` — Authentication required.
- `404` — This endpoint returns 404 on non-federated BAW — requires PFS deployment.

### `PUT /rest/bpm/federated/v1/tasks`
**Ad hoc federated task search (PFS)**

Execute an ad hoc federated task search with filter criteria in request body. Returns federated items[] + totalCount. Session cookie is sufficient — no bpm-csrf-token required. Evidence: VERIFIED IN ON-PREM BAW (PFS18 — CP4BA 24.0.0). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `body` (body, object) — Search filter criteria object.

**Responses:**
- `200` — Search results. Response: items[], totalCount.

---

### `GET /rest/bpm/federated/v1/systems`
**Get federated system list (PFS)**

Returns a list of federated BAW systems registered with PFS including systemID, restUrlPrefix, taskCompletionUrlPrefix, version, indexRefreshInterval, and statusCode. This call is optional — per-task federationResult fields in the task-list response provide routing information on demand without a separate systems call. Evidence: VERIFIED IN ON-PREM BAW (PFS03) — two federated systems returned. Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — List of federated system objects. Each entry: systemID, restUrlPrefix, taskCompletionUrlPrefix, version, indexRefreshInterval, statusCode.

---

### `GET /rest/bpm/federated/v1/launchableEntities`
**Get federated launchable entities (PFS)**

Retrieves the list of exposed launchable processes and services across all federated BAW systems. Equivalent to /rest/bpm/wle/v1/exposed but for PFS environments. Evidence: VERIFIED IN ON-PREM BAW (PFS04) against CP4BA 26.0.0. Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — Federated launchable entity list.

---

### `GET /rest/bpm/federated/v1/searches/tasks`
**List federated saved task searches (PFS)**

Returns the list of saved task search definitions in the PFS context. Evidence: VERIFIED IN ON-PREM BAW (PFS17 — CP4BA 24.0.0). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — List of federated saved search definitions.

### `POST /rest/bpm/federated/v1/searches/tasks`
**Create a federated saved task search (PFS)**

Persist a named federated task search definition. Session cookie is sufficient. Evidence: VERIFIED IN ON-PREM BAW (PFS17 — CP4BA 24.0.0). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `body` (body, object) *(required)* — Saved search definition object.

**Responses:**
- `200` — Saved search created.

---

### `GET /rest/bpm/federated/v1/searches/tasks/{idOrName}`
**Get a specific federated saved task search (PFS)**

Retrieve a specific federated saved task search by ID or name. Evidence: VERIFIED IN ON-PREM BAW (PFS17 — CP4BA 24.0.0). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `idOrName` (path, string) *(required)* — Saved search ID or name.

**Responses:**
- `200` — Saved search definition.

### `PUT /rest/bpm/federated/v1/searches/tasks/{idOrName}`
**Update a federated saved task search (PFS)**

Update an existing federated saved task search definition. Session cookie is sufficient. Evidence: DOCUMENTED (T3.3 — CREATE/READ/DELETE verified PFS17; UPDATE path not independently tested). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `idOrName` (path, string) *(required)* — Saved search ID or name.
- `body` (body, object) *(required)* — Updated saved search definition.

**Responses:**
- `200` — Saved search updated.

### `DELETE /rest/bpm/federated/v1/searches/tasks/{idOrName}`
**Delete a federated saved task search (PFS)**

Delete a named federated saved task search. Session cookie is sufficient. Evidence: VERIFIED IN ON-PREM BAW (PFS17 — CP4BA 24.0.0). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `idOrName` (path, string) *(required)* — Saved search ID or name.

**Responses:**
- `200` — Saved search deleted.

---

### `GET /rest/bpm/federated/v1/searches/actions`
**Get federated search actions (PFS)**

Returns the set of federated saved-search actions the current user is permitted to perform. NOTE: This path is /searches/actions — not under /searches/tasks/actions. Evidence: VERIFIED IN ON-PREM BAW (PFS16 — CP4BA 24.0.0). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — Array of permitted federated search action identifiers.

---

### `GET /rest/bpm/federated/v1/searches/meta/fields`
**Get PFS search metadata — standard fields**

Returns task search field definitions for federated deployments. NOTE: PFS metadata paths are under /searches/meta/ — not under /searches/tasks/meta/. Evidence: VERIFIED IN ON-PREM BAW (PFS05). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — Field metadata list for PFS task search filter construction.

---

### `GET /rest/bpm/federated/v1/searches/meta/constraintFields`
**Get PFS search metadata — constraint fields**

Returns constraint-based filter options for federated task search. NOTE: path is /searches/meta/constraintFields. Evidence: VERIFIED IN ON-PREM BAW (PFS12 — CP4BA 24.0.0). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — Constraint field metadata list.

---

### `GET /rest/bpm/federated/v1/searches/meta/businessDataFields`
**Get PFS search metadata — business data fields**

Returns business data variables available for PFS task search. Evidence: VERIFIED IN ON-PREM BAW (PFS13 — CP4BA 24.0.0). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — Business data field metadata list.

---

### `GET /rest/bpm/federated/v1/searches/meta/taskStatus`
**Get PFS search metadata — task status values**

Returns valid task status values for PFS search filters. Evidence: VERIFIED IN ON-PREM BAW (PFS14 — CP4BA 24.0.0). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — Task status value list.

---

### `GET /rest/bpm/federated/v1/searches/meta/priority`
**Get PFS search metadata — priority values**

Returns valid task priority values for PFS search filters. Evidence: VERIFIED IN ON-PREM BAW (PFS15 — CP4BA 24.0.0). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — Priority value list.

---

### `PUT /rest/bpm/federated/v1/instances`
**Federated process-instance search (PFS)**

Execute a federated process-instance search with filter criteria in request body. Evidence: VERIFIED IN ON-PREM BAW (PFS19 — CP4BA 24.0.0). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `body` (body, object) — Process-instance search filter criteria.

**Responses:**
- `200` — Federated process-instance search results.

---

### `GET /rest/bpm/federated/v1/globalTeams`
**Get federated global teams (PFS)**

Returns teams in a federated context. Separate from the NF team endpoints in /rest/bpm/wle/v1/. Evidence: VERIFIED IN ON-PREM BAW (PFS20 — CP4BA 24.0.0). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — List of federated global team objects.

---

## IBM Business Automation Workflow PFS v2 Federated REST Interface

### `GET /rest/bpm/federated/v2/dashboards/teamsummary`
**Get all-teams performance summary (PFS v2 dashboard)**

Returns summary data (aggregate task counts, overdue/at-risk indicators) for all teams the authenticated user can manage or view, across all federated systems. Response includes summaries[] and federationResult[]. Enables manager team-overview dashboard in FED environments. Evidence: VERIFIED IN ON-PREM BAW (PFS06). Auth: PFS session cookie. Deployment: FED.

**Responses:**
- `200` — All-teams summary. Response: summaries[] with teamId, name, totalOpenTasks, countOverdue, countAtRisk, countOnTrack, tasksCompletedToday, federationResult[].
- `401` — Authentication required.

---

### `GET /rest/bpm/federated/v2/dashboards/teamsummary/{teamId}`
**Get single team performance summary (PFS v2 dashboard)**

Returns aggregate task counts, overdue/at-risk indicators, and workload summary for one team across federated systems. Response includes summary{} (single team shape) and federationResult[]. Evidence: VERIFIED IN ON-PREM BAW (PFS07). HTTP 400 when caller does not manage the team. Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.

**Responses:**
- `200` — Single team summary. Response: summary{} with federationResult[].
- `400` — Caller does not manage the requested team.

---

### `GET /rest/bpm/federated/v2/dashboards/teammember/{teamId}`
**Get team member workload list (PFS v2 dashboard)**

Returns workload data for all members of a specific team across federated systems. Response includes teamMemberList[] and federationResult[]. Evidence: VERIFIED IN ON-PREM BAW (PFS08). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.

**Responses:**
- `200` — Team member workload list. Response: teamMemberList[] with name, fullName, emailAddress, assignedTasks, tasksCompletedToday, federationResult[].

---

### `GET /rest/bpm/federated/v2/dashboards/teammember/{teamId}/{username}`
**Get single team member workload (PFS v2 dashboard)**

Returns task load, overdue, and at-risk counts for a single named team member across federated systems. Response includes summary{} and federationResult[]. HTTP 400 when username is not a member of the team. Evidence: VERIFIED IN ON-PREM BAW (PFS09). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.
- `username` (path, string) *(required)* — Team member username.

**Responses:**
- `200` — Single member workload. Response: summary{} with name, fullName, totalOpenTasks, countOverdue, countAtRisk, federationResult[].
- `400` — Username is not a member of the specified team.

---

### `PUT /rest/bpm/federated/v2/dashboards/teamtasks/{teamId}`
**Get tasks for a team (PFS v2 dashboard)**

Returns the task list for a team across all federated systems. Uses PUT (not GET) with filter criteria in request body. Response includes items[], totalCount, and federationResult[]. Evidence: VERIFIED IN ON-PREM BAW (PFS10). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.
- `body` (body, object) — Filter criteria for the team task query.

**Responses:**
- `200` — Team tasks. Response: items[], totalCount, federationResult[].

---

### `GET /rest/bpm/federated/v2/dashboards/teamtasktrend/{teamId}`
**Get team task trend (PFS v2 dashboard)**

Returns task turnover trend data (tasks created vs completed over time) for a specific team across federated systems. Response: data[] and federationResult[]. Evidence: VERIFIED IN ON-PREM BAW (PFS11). Auth: PFS session cookie. Deployment: FED.

**Parameters:**
- `teamId` (path, string) *(required)* — Team ID.

**Responses:**
- `200` — Task trend data. Response: data[] of { created: N, completed: N, timestamp: '...' } entries, federationResult[].
