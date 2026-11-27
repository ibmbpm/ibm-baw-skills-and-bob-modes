# Feature catalog — what can I build?

> **Layer:** Feature catalog = *what can customers build?* It does not hold API contracts.
> For *which capability applies* use `capabilities/intent-map.json`; for *which operations and
> contracts exist* use `capabilities/catalog.json` and the API guides; for *how to implement*
> use the playbooks in `references/playbooks/`.
>
> **Use:** present the relevant groups, state prerequisites, let the customer choose. Do not force
> feature selection into every portal-generation request. Do not generate a feature from this file
> alone — resolve it through the intent map and catalog first.

## Classification and evidence

| Class | Meaning |
|---|---|
| **API-backed** | Existing Business Automation Workflow operations cover the core function (capability `status=available`; no FDR, PFS-only or elevated-permission gate). Ordinary task-level permissions still apply. |
| **Conditional** | Needs a version, FDR, PFS, user permission, exposed business data, or runtime validation in the target environment. |
| **Portal-implemented** | Application logic/UI composed around Business Automation Workflow responses; Business Automation Workflow provides only the data. |
| **Additional integration** | Needs functionality outside the currently evidenced Business Automation Workflow API coverage. Not promised. |

- Class describes feasibility for **non-federated (NF)** unless a row says otherwise. PFS variants and their
  differences are in the *Prerequisites* column; PFS mutations and instance features are weaker than NF.
- **Evidence** is kept separate from class and uses three levels: *runtime-verified* (HTTP status only, not
  proof of every response field), *structural-assertion-verified* (a state change was observed on one
  deployment) and *documentation-verified* (documented by IBM, not runtime-verified). Do not read `API-backed`
  as "runtime-verified". When presenting features to a customer, describe the evidence level in plain words;
  do not show these labels.
- Whether a feature works in a given environment is confirmed by asking for deployment (NF/PFS), Business Automation Workflow
  version, FDR status, hosting profile, and the user's permissions — then following the intent's own
  prerequisites and FDR probe. Nothing here is verified for the customer's environment.
- Parity with Workplace or Process Portal is **not** claimed; this catalog lists only what the evidence supports.

---

## 1. Personal task management

| Feature | What the user can do | Class | Capabilities · Intents | Evidence | Prerequisites / limits | Playbook |
|---|---|---|---|---|---|---|
| Task inbox | See assigned and available tasks with paging and a truncation indicator | API-backed | `CAP-TASK-LIST-NF`, `CAP-TASK-LIST-PFS` · `INT-TASK-INBOX` | runtime-verified | The total count may exceed one page; the task-list GET can return 404 on some deployments (use ad hoc search instead). PFS shows partial-failure per source system | [task-lifecycle](playbooks/task-lifecycle.md) |
| Task details | Review a task's metadata and context before acting | API-backed | `CAP-TASK-DETAIL-NF` · `INT-TASK-DETAIL` | runtime-verified | NF only; no PFS detail capability | [task-lifecycle](playbooks/task-lifecycle.md) |
| Claim and release | Claim a task; release it or return it to the queue | API-backed | `CAP-TASK-CLAIM-NF`, `CAP-TASK-RELEASE-NF`, `CAP-TASK-CANCEL-NF` · `INT-TASK-ACTIONS` | runtime-verified (claim, release) · structural-assertion-verified (cancel claim) | Task-level permission; XSRF handling verification-required. PFS: routed to source system, `CAP-TASK-LIFECYCLE-PFS` is partial and documentation-verified | [task-lifecycle](playbooks/task-lifecycle.md), [federated](playbooks/federated-portal-integration.md) |
| Reassign | Hand a task to a user, group or team | Conditional | `CAP-TASK-RELEASE-NF` · `INT-TASK-ACTIONS` | `toUser`: structural-assertion-verified on one deployment · `toGroup`, `toTeam`, `toMe`: documentation-verified only | Permission-dependent; assigning to a group, a team or yourself is documentation-verified only | [task-lifecycle](playbooks/task-lifecycle.md) |
| Complete task from portal | Submit a task's output without opening the Business Automation Workflow form | Conditional | `CAP-TASK-FINISH-NF` · `INT-TASK-ACTIONS` | documentation-verified | Completion inputs are task-definition-specific; generic completion cannot be generated without the task schema. Opening the Business Automation Workflow form is the default (group 6) | [task-lifecycle](playbooks/task-lifecycle.md) |
| Priority change | Change a task's priority | API-backed | `CAP-TASK-UPDATE-NF` · `INT-TASK-ACTIONS` | runtime-verified | Task-level permission | [task-lifecycle](playbooks/task-lifecycle.md) |
| Filters and sorting | Narrow and order the inbox by status, priority, due date, name | Portal-implemented | `CAP-TASK-LIST-NF`, `CAP-ADHOC-SEARCH-NF` · `INT-TASK-INBOX`, `INT-ADHOC-SEARCH` | runtime-verified (list, ad hoc search) | In-page filter/sort acts on the loaded page only. Server-side filter/sort uses ad hoc search (see group 2). PFS ad hoc search is documentation-verified | [task-lifecycle](playbooks/task-lifecycle.md) |
| Overdue / at-risk markers | Highlight past-due and due-soon tasks | Portal-implemented | `CAP-TASK-LIST-NF` · `INT-TASK-INBOX` | runtime-verified (task data) | Derived client-side from the due date; counts from one page are page counts, not whole-inbox totals | [task-lifecycle](playbooks/task-lifecycle.md) |

## 2. Advanced saved searches

| Feature | What the user can do | Class | Capabilities · Intents | Evidence | Prerequisites / limits | Playbook |
|---|---|---|---|---|---|---|
| Create, edit, delete saved searches | Keep reusable task queries | API-backed | `CAP-SAVED-SEARCH-MGMT-NF`, `CAP-SAVED-SEARCH-MGMT-PFS` · `INT-SAVED-SEARCH-MGMT` | documentation-verified (list is runtime-verified) | Validate the mutation lifecycle in the target environment; send the full definition on update (no partial `PUT`); PFS update has no execution claim | [saved-search](playbooks/saved-search-management.md) |
| Run a saved search | Execute a saved query and page the results | API-backed | `CAP-SAVED-SEARCH-EXEC-NF`, `CAP-SAVED-SEARCH-EXEC-PFS` · `INT-SAVED-SEARCH-EXEC` | documentation-verified | Choose one strategy per the playbook (two-step default); keep criteria and sort identical across pages | [saved-search](playbooks/saved-search-management.md) |
| Metadata-driven condition builder | Build conditions from fields and constraint options the server reports | API-backed | `CAP-SEARCH-META-NF`, `CAP-SEARCH-META-PFS`, `CAP-ADHOC-SEARCH-NF` · `INT-SEARCH-METADATA`, `INT-ADHOC-SEARCH` | runtime-verified (NF metadata, ad hoc) | Status and priority value lists are PFS-only (documentation-verified). Client-only filters must not be saved as conditions | [saved-search](playbooks/saved-search-management.md) |
| Configurable columns and sorting | Choose system columns, add business-data columns, set sort order | Conditional | `CAP-SEARCH-META-NF` · `INT-SEARCH-METADATA`, `INT-SAVED-SEARCH-MGMT` | runtime-verified (metadata) | Business-data columns depend on what the process app exposes; field entries are search aliases, not task properties | [saved-search](playbooks/saved-search-management.md) |
| Share a search | Make a search visible to other users | Conditional | `CAP-SAVED-SEARCH-MGMT-NF` · `INT-SAVED-SEARCH-MGMT` | documentation-verified | Needs the shared-search actions the server reports; role-specific visibility unverified; those actions govern saved searches only | [saved-search](playbooks/saved-search-management.md) |
| Save As (copy a search) | Create a new search from an existing one | Portal-implemented | `CAP-SAVED-SEARCH-MGMT-NF` · `INT-SAVED-SEARCH-MGMT` | none — no dedicated operation | Not a Business Automation Workflow operation; composed as get-then-create with a new name. Inherits create-lifecycle validation needs | [saved-search](playbooks/saved-search-management.md) |
| Advanced (v2) search | Run complex queries beyond saved-search criteria | Conditional | `CAP-ADV-SEARCH-NF` · `INT-ADVANCED-SEARCH` | documentation-verified | Business Automation Workflow 24+ with FDR; HTTP 503 without FDR; NF only, no PFS equivalent; probe before generating | — (intent map `fdrGate`) |

## 3. Process launching

| Feature | What the user can do | Class | Capabilities · Intents | Evidence | Prerequisites / limits | Playbook |
|---|---|---|---|---|---|---|
| Launchable process catalog | Browse processes the user is authorized to start | API-backed | `CAP-PROCESS-DISCOVERY-NF`, `CAP-PROCESS-DISCOVERY-PFS` · `INT-PROCESS-DISCOVER-AND-START` | runtime-verified | Appearing in the list does not guarantee startability. Categories, descriptions and favorites beyond returned fields are not evidenced | — |
| Start a process | Launch an instance from the portal | Conditional | `CAP-PROCESS-START-NF` · `INT-PROCESS-DISCOVER-AND-START` | structural-assertion-verified | Process and app identifiers are taken from the launchable item's start link; input variables are process-specific; the starter may be auto-assigned the first task. PFS: discovery only — no federated start endpoint, initiation unverified | [federated](playbooks/federated-portal-integration.md) (PFS) |

## 4. Process instance management

| Feature | What the user can do | Class | Capabilities · Intents | Evidence | Prerequisites / limits | Playbook |
|---|---|---|---|---|---|---|
| Search and inspect instances | Find instances, view state and tasks | Conditional | `CAP-PROCESS-INSTANCE-LIST-NF`, `CAP-PROCESS-INSTANCE-DETAIL-NF`, `CAP-INSTANCE-SEARCH-PFS` · `INT-PROCESS-INSTANCE-SEARCH` | documentation-verified (all `partial`) | Not runtime-verified; response shape and filter semantics need validation. PFS: ad hoc search only (no saved instance searches), evidence scoped to Cloud Pak for Business Automation 24.0.0 | — |
| Suspend, resume, change due date | Pause or resume an instance; move its due date | Conditional | `CAP-INSTANCE-SUSPEND-NF`, `CAP-INSTANCE-RESUME-NF`, `CAP-INSTANCE-UPDATE-DUEDATE-NF` · `INT-PROCESS-INSTANCE-MGMT` | structural-assertion-verified (`partial`) | Per-action permission and instance-state eligibility; observed on one deployment only; NF only | — |
| Retry a failed instance | Re-run a failed service step | Conditional | `CAP-INSTANCE-RETRY-NF` · `INT-PROCESS-INSTANCE-MGMT` | documentation-verified | Not idempotent (repeats external side effects); never auto-retry | — |
| Terminate or delete | Stop or permanently remove an instance | Conditional | `CAP-INSTANCE-TERMINATE-NF`, `CAP-INSTANCE-DELETE-NF` · `INT-PROCESS-INSTANCE-MGMT` | structural-assertion-verified | Typically admin-level; irreversible; separate explicit confirmations; delete removes audit history and needs application audit logging | — |

## 5. Team management

| Feature | What the user can do | Class | Capabilities · Intents | Evidence | Prerequisites / limits | Playbook |
|---|---|---|---|---|---|---|
| My teams | List teams the user manages or can see | API-backed | `CAP-MANAGED-TEAMS-NF`, `CAP-VISIBLE-TEAMS-NF` · `INT-USER-PROFILE-AND-TEAMS` | runtime-verified | NF only in the intent map. Modeled-team IDs differ from runtime team IDs | — |
| Team roster | See who is on a team | Conditional | `CAP-TEAM-MEMBERSHIP-NF` · `INT-USER-PROFILE-AND-TEAMS` | runtime-verified (`partial`) | Needs a runtime global team ID; caller must manage or have access to the team; minimize PII | — |
| Team workload overview | See open, overdue, at-risk and on-track counts per team | Conditional | `CAP-TEAM-WORKLOAD-OVERVIEW-NF/-PFS`, `CAP-TEAM-WORKLOAD-SINGLE-NF/-PFS` · `INT-TEAM-WORKLOAD` | runtime-verified (status only, `partial`) | NF: Business Automation Workflow 24+ with FDR (503 otherwise). A caller managing no teams gets HTTP 400 — a valid empty state. PFS variants: no FDR flag, still `partial` | — |
| Member workload | See each member's workload and drill in | Conditional | `CAP-TEAM-MEMBERS-NF/-PFS` · `INT-TEAM-WORKLOAD` | runtime-verified (list, status only) | As above; single-member form is documentation-only | — |
| Team task list | List tasks across a team | Conditional | `CAP-TEAM-TASK-SEARCH-NF/-PFS` · `INT-TEAM-WORKLOAD` | documentation-verified (NF) · runtime-verified (PFS, status only) | Search criteria are sent in the request body; NF body schema and paging need validation | — |
| Assign a team member's task | Redirect a task from the team view | Conditional | `CAP-TASK-RELEASE-NF` · `INT-TASK-ACTIONS` | runtime-verified (assign to a user only) | Manager permission; kept out of a read-only dashboard baseline | [task-lifecycle](playbooks/task-lifecycle.md) |

## 6. Embedded task experience

| Feature | What the user can do | Class | Capabilities · Intents | Evidence | Prerequisites / limits | Playbook |
|---|---|---|---|---|---|---|
| Open task in the Business Automation Workflow form (new tab, or in-page when hosted on Business Automation Workflow) | Complete a task in the standard Business Automation Workflow task UI | API-backed | `CAP-TASK-LAUNCH-NF` · `INT-TASK-LAUNCH` | documentation-verified | The URL is constructed, not returned by the API; form load needs deployment-time verification. Hosting on Business Automation Workflow (A/A2) needs no extra setup | [task-lifecycle](playbooks/task-lifecycle.md) |
| Embed the task form in an external portal | Keep users inside the portal while they work | Conditional | `CAP-TASK-LAUNCH-NF` · `INT-TASK-LAUNCH` | documentation-verified | External portals must meet the framing prerequisites in [hosting-and-generation](hosting-and-generation.md); otherwise offer a new tab. `sandbox` untested against Business Automation Workflow forms | [task-lifecycle](playbooks/task-lifecycle.md) |
| Federated task launch | Open a task on its owning source system | Conditional | `CAP-TASK-LAUNCH-PFS` · `INT-TASK-LAUNCH` | documentation-verified | Routing uses the per-source-system results in the federated response; cross-system SSO, reachability and framing must be validated per source system | [federated](playbooks/federated-portal-integration.md) |

A portal-native replacement for the Business Automation Workflow task completion form is **not offered** by this skill.

## 7. Operational dashboards and analytics

| Feature | What the user can do | Class | Capabilities · Intents | Evidence | Prerequisites / limits | Playbook |
|---|---|---|---|---|---|---|
| Personal workload summary | See counts for overdue, at-risk, active, total | Portal-implemented | `CAP-TASK-LIST-NF/-PFS` · `INT-TASK-INBOX` | runtime-verified (task data) | Computed from returned items; label page counts honestly | [task-lifecycle](playbooks/task-lifecycle.md) |
| Manager dashboard | Team KPIs, overdue/at-risk indicators, member drill-down | Conditional | `CAP-TEAM-WORKLOAD-OVERVIEW-NF/-PFS`, `CAP-TEAM-MEMBERS-NF/-PFS` · `INT-TEAM-WORKLOAD` | runtime-verified (status only) | Same gates as group 5. Use server-provided KPIs; do not total a partial page | — |
| Team task trend | Chart created vs completed over time | Conditional | `CAP-TEAM-TASK-TREND-NF/-PFS` · `INT-TEAM-WORKLOAD` | runtime-verified (status only) | FDR (NF); per-team only — do not present as organization-wide | — |
| Leadership roll-up | Combine summaries and trends across managed teams | Portal-implemented | `CAP-TEAM-WORKLOAD-OVERVIEW-NF/-PFS`, `CAP-TEAM-TASK-TREND-NF/-PFS` · `INT-TEAM-WORKLOAD` | runtime-verified (inputs, status only) | Client/backend roll-up over APIs that are scoped to the caller's managed teams; no dedicated aggregate endpoint is evidenced; not enterprise-wide | — |
| Historical process analytics (cycle time, SLA, throughput by process) | Analyze performance beyond per-team counts and trend | Additional integration | none | none | No capability in the catalog; confirm requirements before promising anything | — |

## 8. Administration and advanced integrations

| Feature | What the user can do | Class | Capabilities · Intents | Evidence | Prerequisites / limits | Playbook |
|---|---|---|---|---|---|---|
| Administer shared saved searches | Manage others' shared searches | Conditional | `CAP-SAVED-SEARCH-MGMT-NF` · `INT-SAVED-SEARCH-MGMT` | documentation-verified | Requires the administer actions the server reports; these never imply task or process admin rights | [saved-search](playbooks/saved-search-management.md) |
| Cross-user process visibility | See instances beyond the caller's own | Conditional | `CAP-PROCESS-INSTANCE-LIST-NF` · `INT-PROCESS-INSTANCE-SEARCH` | documentation-verified | Uses the include-other-users search option behind a capability-specific gate; entitlement unconfirmed; hide the panel unless the server returns usable data. See `personas-and-capabilities.md` §Administrator | — |
| Cross-user claimed-task view | See tasks claimed by any user | Additional integration | none | none | Not generated: the request placement is unverified; ask for on-environment verification first (see [`baw-rest.md`](baw-rest.md)) | — |
| Process-instance administration | Operate on failed, suspended or running instances | Conditional | see group 4 | see group 4 | Per-action permissions; confirmations; audit logging | — |
| Federated multi-system portal | Aggregate tasks and processes across Business Automation Workflow systems | Conditional | PFS capabilities in groups 1, 3, 5, 6 · all intents with a PFS mapping | runtime-verified or documentation-verified, by capability | Requires PFS; routing allowlist, SSO and CORS must be validated; generated code gated on PFS runtime testing | [federated](playbooks/federated-portal-integration.md) |
| External SSO / API gateway token exchange | Authenticate an external portal through a gateway | Additional integration | none | not tested | Deployment-specific; confirm with the Business Automation Workflow administrator (see [Open deployment decisions](hosting-and-generation.md#open-deployment-decisions)) | — |
| Notifications, user/team provisioning, audit export | Services around the portal | Additional integration | none | none | Not covered by any catalog capability | — |

---

## Using this catalog

- **"What can I build / what can the APIs support?"** Summarize the groups relevant to the customer's personas,
  mark each feature's class and key prerequisite, and ask which to include.
- **"Can you build something like Workplace or Process Portal?"** Say which groups above are evidenced, which
  are conditional, and which are not offered. Do not claim parity.
- **"What's possible in my environment?"** Ask for deployment (NF/PFS), Business Automation Workflow version, FDR status, hosting
  profile and the user's role, then apply each feature's prerequisites. State that nothing is confirmed until
  it is validated against that environment.
- **Once a feature is chosen:** resolve it through `capabilities/intent-map.json`, read the capability entry in
  `capabilities/catalog.json`, and load the listed playbook before generating code.
