---
name: create-baw-portal
description: >
  API-knowledge and portal-development skill for IBM® Business Automation Workflow.
  Teaches developers which Business Automation Workflow APIs are needed for a requested portal, what they do, how to
  use them correctly, and how authorization, authentication, CORS, proxies, pagination, and
  XSRF affect implementation. Supports non-federated (WLE REST) and federated (PFS) environments.
  Three usage patterns: (1) API guidance only, (2) adapt an existing application, (3) generate
  a new portal or full application. Carbon is the default design system where appropriate.
  Does NOT generate Business Automation Workflow process diagrams (BPMN) or internal Business Automation Workflow XML artifacts.
license: Apache-2.0
compatibility: "Compatible with all IBM-supported releases of IBM Business Automation Workflow and IBM Cloud Pak for Business Automation, as defined by the IBM Software Support Lifecycle."
allowed-tools:
  - Read
  - Edit
metadata:
  version: "1.0.0"
  display_name: Business Automation Workflow Portal Builder
  short_description: Build IBM Business Automation Workflow task portals — API guidance, portal generation, and existing-app integration for non-federated and PFS environments.
  author: IBM Business Automation Workflow Team
  example_prompts:
    - "Generate a personal task dashboard portal for Business Automation Workflow"
    - "Which API do I call to get the current user's name in my Business Automation Workflow portal?"
    - "I have an existing React app — add Business Automation Workflow task list integration using axios"
    - "How does pagination work with the Business Automation Workflow task list endpoint?"
    - "Generate a standalone single HTML Business Automation Workflow portal, no build tools"
    - "We're on Process Federation Server — show me how to fetch a federated task list"
    - "How do I open a Business Automation Workflow task in an iframe modal?"
    - "How do I handle XSRF tokens when calling Business Automation Workflow APIs?"
---

<!-- baw-rest-ops: baw-wle-v1.26.0.0.json: /user/current, /tasks, /task/{taskId}, /searches/tasks, /searches/tasks/{idOrName}, /searches/actions, /searches/tasks/meta/fields, /searches/tasks/meta/constraintFields, /searches/tasks/meta/businessDataFields, /managedGlobalTeams, /globalTeams, /globalTeamUsers/{id}, /team/{teamId}, /team, /group/{groupNameOrID}, /exposed, /process -->
<!-- baw-rest-ops: baw-wle-v2.26.0.0.json: /search, /search/queries, /dashboards/teamsummary, /dashboards/teamsummary/{teamId}, /dashboards/teammember/{teamId}, /dashboards/teammember/{teamId}/{username}, /dashboards/teamtasks, /dashboards/teamtasks/{teamId}, /dashboards/teamtasktrend/{teamId} -->
<!-- baw-rest-ops: baw-pfs-v1.26.0.0.json: /tasks, /systems, /launchableEntities, /searches/tasks, /searches/tasks/{idOrName}, /searches/actions, /searches/meta/fields, /searches/meta/constraintFields, /searches/meta/businessDataFields, /searches/meta/taskStatus, /searches/meta/priority, /instances, /globalTeams -->
<!-- baw-rest-ops: baw-pfs-v2.26.0.0.json: /dashboards/teamsummary, /dashboards/teamsummary/{teamId}, /dashboards/teammember/{teamId}, /dashboards/teammember/{teamId}/{username}, /dashboards/teamtasks/{teamId}, /dashboards/teamtasktrend/{teamId} -->

# create-baw-portal skill

Teaches which Business Automation Workflow APIs a portal needs, how to call them correctly, and how authentication, authorization, CORS, proxies, pagination and CSRF/XSRF affect the implementation. Covers non-federated (WLE REST, "NF") and federated (Process Federation Server, "PFS") environments. Not for BPMN, BPEL or other internal Business Automation Workflow XML (use `generate-baw-bpmn`).

## Identify the usage pattern

| Pattern | Typical request | Action |
|---|---|---|
| API guidance only | "Which API…", "How does pagination work…" | Answer from the references; no code unless asked. |
| Existing application | "I have a React app…", "Add Business Automation Workflow to my app…" | Read its stack, HTTP client, auth pattern and structure first. Add a service module in the existing style; do not refactor unrelated code. |
| New portal or application | "Generate a portal…", "Build a task dashboard…" | Use the requested stack (React if none), including standalone single HTML. |

## Gather required information

Ask once, before generating anything, for what the request does not already supply:

1. **Hosting profile** (essential, never default, because wrong-profile code cannot work).
   - **A**: Hosted on Business Automation Workflow, same origin. No CORS or proxy; task iframe works.
   - **A2**: portal embedded in a Business Automation Workflow Coach (same-origin benefits).
   - **C-proxy**: external app behind a reverse proxy. Task iframe needs the portal origin in the Business Automation Workflow CSP `frame-ancestors` and HTTPS.
   - **C-direct**: external app calling Business Automation Workflow directly. Needs a bearer token, a CORS allowlist and the same iframe prerequisites.
2. **Environment**: NF or PFS. Ask when PFS context is evident ("Process Federation Server", "federated tasks"); never assume NF then. Default to NF only when there is no PFS context, and say so.
3. **Persona(s)**: task worker, manager/team lead, executive, administrator. Requirements: `references/personas-and-capabilities.md`.
4. **Stack** (default React) and **branding** (default IBM text-only; see hosting guide). State defaults you apply.

Skip questions when everything is answered, for API guidance, or when the user says to proceed. In a no-questions run, if an essential fact is missing, stop and list it. Never guess an essential fact or an API contract. Profile definitions and prerequisites: `references/hosting-and-generation.md`.

## Select capabilities

Use `capabilities/intent-map.json` and `capabilities/catalog.json` as the registry. They are agent reference material: search for the intent alias, `CAP-*` or operation ID and read only that record; never load a whole file.

1. Classify the request (guidance, adaptation, generation). For a simple "which endpoint" question, go straight to the guide section and operation.
2. Resolve NF versus PFS. `CAP-*-NF` applies to NF only, `CAP-*-PFS` to PFS only.
3. Find the intent whose `aliases` match; take its capability list for the resolved deployment. If none fits, read `discoveryAmbiguities`; read `selectionRules` only when strategies conflict.
4. For each required operation, read its catalog record and the matching guide section. Surface the capability's `limitations` to the developer. When strategies are mutually exclusive (for example saved-search execution), implement only the chosen one.
5. Resolve hosting and authentication prerequisites (hosting guide) and state any unmet one before writing code.
6. Features with a playbook: load the playbook before generating code. Playbooks sequence the work; contracts stay in the catalog and guides.

| Feature | Intent IDs | Playbook |
|---|---|---|
| Saved searches (manage, execute) | `INT-SAVED-SEARCH-MGMT`, `INT-SAVED-SEARCH-EXEC` | [`saved-search-management.md`](references/playbooks/saved-search-management.md) |
| Task list, detail, actions, launch | `INT-TASK-INBOX`, `INT-TASK-DETAIL`, `INT-TASK-ACTIONS`, `INT-TASK-LAUNCH` | [`task-lifecycle.md`](references/playbooks/task-lifecycle.md) |
| Discover and start a process | `INT-PROCESS-DISCOVER-AND-START` | NF: [§Process launch](references/non-federated-api-guide.md#process-launch) and task-lifecycle §4.3. PFS: the federated playbook |
| Any PFS deployment | any intent resolved to PFS | [`federated-portal-integration.md`](references/playbooks/federated-portal-integration.md), together with the intent's own playbook |

For discovery questions (what can be built), use [`feature-catalog.md`](references/feature-catalog.md). Present only groups relevant to the persona and environment; do not claim parity with IBM portals. Once chosen, resolve through the intent map.

## API family and rules

| Condition | API family |
|---|---|
| Single Business Automation Workflow server | WLE REST `/rest/bpm/wle/v1/` |
| Process Federation Server | PFS `/rest/bpm/federated/v1/` |
| Manager/executive dashboards, Business Automation Workflow 24+ with FDR | WLE v2 `/rest/bpm/wle/v2/dashboards/` |
| Manager/executive dashboards, PFS | PFS v2 `/rest/bpm/federated/v2/dashboards/` |

- Never invent an endpoint, parameter, field or response shape. Take paths and parameters from [`baw-rest.md`](references/baw-rest.md) and behaviour from the guides and catalog. `/rest/bpm/wle/v1/teams` does not exist; use `team/{teamId}`, `managedGlobalTeams` or `globalTeams`.
- `size=500` means up to 500 tasks. Check `totalCount`, page with `offset`, and show a visible truncation message when items are missing. Never present a partial list as complete.
- `filterByCurrentUser=true` and `interaction=claimed_and_available` are not interchangeable.
- **CSRF/XSRF:** whether a deployment needs a `BPMCSRFToken` header or an `XSRF-TOKEN` check for mutations must be confirmed, not guessed. Obtain a token only through the documented login call; never fabricate, hard-code or log one; never disable a check, spoof `User-Agent` or weaken TLS or authentication. Contract: [`non-federated-api-guide.md` §XSRF / CSRF](references/non-federated-api-guide.md#xsrf--csrf-for-wle-rest-mutations); PFS: `federated-api-guide.md`.
- **FDR (manager/executive dashboards):** WLE v2 dashboards need Business Automation Workflow 24+ with FDR enabled and return HTTP 503 without it. Probe at runtime and render a plain empty state, for example `if (res.status === 503) show('Team workload data is unavailable. Contact your BAW administrator.')`. Never show the status or error code in the UI.
- **Saved searches:** load the playbook. Use the numeric `id`, send complete definitions on update, execute with one strategy, and treat an unrecognised envelope as an error.
- **Errors:** every data view has loading, empty, error and permission-denied states. Never turn a failed or unrecognised response into an empty list.
- **Authorization:** Business Automation Workflow enforces it server-side. Do not gate views on portal-side role checks, and do not use `searches/actions` policies as proof of task or process administration rights.
- **Task UI:** open the existing Business Automation Workflow task UI (iframe, panel or tab); do not rebuild task completion. An iframe in an external portal needs both prerequisites from the hosting guide; if unmet, generate no iframe code, state both prerequisites and offer new-tab launch. Never use an absolute `https://{baw-host}/teamworks/...` URL as an iframe `src`.

## Administrator persona

Never infer unrestricted administrator access; Business Automation Workflow decides server-side what each user may see, and the portal does no role checks. Generate the standard persona UI unconditionally. Generate only supported, capability-specific admin operations, each behind its own gate: hidden by default and shown only when that panel's own request returns usable data for the signed-in user (for example `includeNonAdmin=true`). Do not generate the cross-user `allClaimed` task list (request shape unresolved) and say so. Saved-search permissions from `searches/actions` govern saved searches only. Details: `references/personas-and-capabilities.md` §Administrator.

## Preserve an existing stack

Keep its structure, routing, HTTP client and auth pattern; wrap Business Automation Workflow calls in a service module; map Business Automation Workflow authentication to the existing pattern.

## Generate a new application

1. **Interfaces first** when more than one module, author or agent contributes: fix the view identifiers, shared call signatures and layout rules before writing modules (hosting guide §Stable interfaces before parallel work). Single-file output needs no separate contract.
2. **File safety:** before the first write in a conversation, check whether the target exists; if it was not generated in this conversation, choose a new name (`-v2`) rather than overwrite. Fixes go into the same file (hosting guide §Pre-write file safety check).
3. Choose layout and navigation from the persona and requested features (hosting guide §Configurable design choices). API behaviour follows the guides and catalog, never an example.
4. Meet the acceptance criteria and quality requirements in hosting guide §Mandatory requirements. Name any requested feature you omit or cannot deliver and give the reason; give a neutral placeholder for blocked features. Silently dropping a requested feature is a defect.
5. Carbon tokens as CSS custom properties where appropriate; configurable brand variables; plain-text company name, never an invented logo.

## Unvalidated capabilities and customer output

Catalog `evidence.level` and `status` are for your selection only. In responses, generated code, docs and UI, describe them in plain words: "documented by IBM, not runtime-tested", "needs FDR enabled". Never print evidence levels, check IDs, gap IDs, HTTP status codes, error codes or API paths in visible UI text.

- Developer caveats go in the chat reply or an HTML comment, not in banners or badges.
- Deployment-gated features (for example FDR dashboards) get a silent runtime check and a plain empty state such as "Team workload data is unavailable. Contact your Business Automation Workflow administrator."
- Do not generate speculative code for unresolved gaps. See hosting guide §Open deployment decisions (gateway token exchange, OIDC, external validation boundary, version matrix).
- Do not claim live runtime validation unless an authenticated Business Automation Workflow environment was used in this session.

## After generating

Flag API calls that are not runtime-tested and any unvalidated capability included. Tell the developer to confirm against a live Business Automation Workflow instance before go-live: user and task list load, task open works for the chosen profile, process start closes the launcher before opening a task, keyboard-only navigation and a screen-reader pass. Checklist: hosting guide §Before delivery.

## References: load on demand

Find the heading, operation ID, `CAP-*` ID or alias with `grep`, then read just that range.

| Request | Load |
|---|---|
| NF (WLE REST) | [`non-federated-api-guide.md`](references/non-federated-api-guide.md): only the sections for the feature; add §Authentication and §XSRF / CSRF for mutation code |
| PFS | [`federated-api-guide.md`](references/federated-api-guide.md) sections plus the federated playbook; NF sections only for operations the playbook routes to the source system |
| Exact path, method, parameters | [`baw-rest.md`](references/baw-rest.md): the matching family section |
| Operation or capability contract | [`catalog.json`](capabilities/catalog.json): that record only |
| Which capability fits | [`intent-map.json`](capabilities/intent-map.json): that intent only |
| Hosting, auth, CORS, iframe, generation, quality, open decisions | [`hosting-and-generation.md`](references/hosting-and-generation.md) |
| Persona requirements | [`personas-and-capabilities.md`](references/personas-and-capabilities.md): the persona's section |
| Discovery | [`feature-catalog.md`](references/feature-catalog.md) |

## Out of scope

BPMN or BPEL authoring, internal Business Automation Workflow XML, rebuilding the Business Automation Workflow task completion UI, and unconditional admin-scoped code.
