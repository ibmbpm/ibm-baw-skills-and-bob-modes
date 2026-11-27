# Business Automation Workflow portal builder — documentation

> API-knowledge and portal-development skill for IBM® Business Automation Workflow. Teaches developers which Business Automation Workflow APIs are needed for a requested portal, how to use them correctly, and how authentication, CORS, proxies, pagination, and XSRF affect implementation. Supports non-federated (WLE REST) and federated (PFS) environments.

## Purpose

The `create-baw-portal` skill helps developers build web portals that connect to IBM® Business Automation Workflow. It covers three distinct scenarios: answering API-specific questions, integrating Business Automation Workflow into an existing application, and generating a new portal from scratch. It supports both non-federated Business Automation Workflow (WLE REST API) and federated deployments using Process Federation Server (PFS), and defaults to React with Carbon design tokens when no stack is specified.

Use this skill when a developer needs to know which Business Automation Workflow endpoints to call, how to authenticate, how to handle pagination or XSRF tokens, how to launch Business Automation Workflow tasks in an iframe, or how to generate a full portal for task workers, managers, executives, or team leads.

## Setup and configuration

- No special tools or MCP servers are required.
- The skill applies layout-independent accessibility, security and data-freshness requirements from [`references/hosting-and-generation.md`](../references/hosting-and-generation.md#quality-requirements-every-ui) to every generated portal.
- A live Business Automation Workflow instance is required for runtime validation of generated portals; the skill itself does not connect to any Business Automation Workflow server.
- The package contains `SKILL.md`; `references/` (`baw-rest`, `feature-catalog`, `federated-api-guide`, `hosting-and-generation`, `non-federated-api-guide`, `personas-and-capabilities` and three playbooks); `capabilities/` (`catalog.json`, `intent-map.json`); and `scripts/validate-capabilities.mjs`.

## Compatibility

- **Non-federated WLE v2 dashboard APIs** (manager/executive dashboards) require **Business Automation Workflow 24+** with the Federated Dashboard Repository (FDR) feature enabled. The skill probes FDR at runtime via `GET /rest/bpm/wle/v2/dashboards/teamsummary`: HTTP 200 = FDR enabled; HTTP 503 = FDR not enabled. Do not rely on a version check alone.
- **Federated API family** (`/rest/bpm/federated/`) requires a **Process Federation Server** deployment. The federated task list endpoint returns HTTP 404 on a non-federated Business Automation Workflow server — confirm your environment before requesting PFS-specific guidance or code.
- **CSRF / XSRF** — IBM documents a `BPMCSRFToken` header (obtained via `POST /bpm/system/login`) for Workflow REST API operations, and a deployment setting that validates an `XSRF-TOKEN` cookie on legacy `/rest/bpm/wle/v1/*` mutations. Whether a given WLE v1/v2 or PFS mutation needs a token depends on deployment, auth mode and API family; unproven combinations are verification-required. Never fabricate tokens, disable checks or spoof user agents.
- **Cloud Pak for Business Automation deployments** — external portals use `Authorization: Bearer <token>` (IAM) instead of session-cookie auth. A live Cloud Pak for Business Automation IAM endpoint is required to obtain the token. Do not use `credentials: 'same-origin'` for external bearer-token scenarios. Same-origin portals hosted on the Cloud Pak for Business Automation server itself still use session-cookie auth with `credentials: 'same-origin'`.
- **Administrator-aware features** — dashboards, APIs, and detection patterns for the administrator persona are in `references/personas-and-capabilities.md`. Administrator access is never inferred: Business Automation Workflow decides what each user may see. The cross-user task list (`allClaimed`) is not generated because its request shape is unresolved. The cross-user process panel (`includeNonAdmin=true`) is generated only behind a capability-specific gate: it stays hidden unless the server returns usable data for the signed-in user. Saved-search permissions never imply task or process administration rights.

## Prompt examples

### Get guidance on a specific API

**Prompt:**
> Which Business Automation Workflow API returns the current user's full name? What fields does the response include, and do I need any special headers for a same-origin portal?

**What to expect:** The exact endpoint (`GET /rest/bpm/wle/v1/user/current?parts=all`), the relevant response fields (`data.fullName`, `data.displayName`, `data.userName`), and a note that CSRF/XSRF requirements for mutations are covered separately and are deployment- and auth-mode-dependent.

---

### Understand pagination for the task list

**Prompt:**
> How does pagination work with the Business Automation Workflow WLE task list endpoint? I want to make sure I'm not silently truncating tasks.

**What to expect:** An explanation of the `size`, `offset`, and `totalCount` paging contract, the correct pattern for iterating pages using `offset` incremented by `size`, and guidance on surfacing a truncation indicator when `totalCount` exceeds the number of returned items.

---

### Understand XSRF token requirements for mutations

**Prompt:**
> I need to claim and reassign tasks using the WLE v1 task mutation endpoints. Should I add a bpm-csrf-token header for PUT requests in my same-origin browser portal?

**What to expect:** A clear explanation that IBM documents the `BPMCSRFToken` header (token from `POST /bpm/system/login`, `csrf_token` property) and a separate legacy `XSRF-TOKEN` cookie check for `/rest/bpm/wle/v1/*` (`check_xsrf_for_old_restapi`); that Bearer-authenticated WLE v1 mutations were observed to succeed on Cloud Pak for Business Automation 26.0.0 without them; that session-cookie mode is verification-required; and that tokens must not be fabricated and checks must not be disabled.

---

### Add Business Automation Workflow task integration to an existing React app using axios

**Prompt:**
> I have an existing React application. It uses axios for all HTTP calls. I need to add a Business Automation Workflow personal task list to it. We're on a single non-federated Business Automation Workflow server hosted at the same origin.

**What to expect:** A `bawApiService.js` module written in axios (not fetch), calling `GET /rest/bpm/wle/v1/tasks?interaction=claimed_and_available&size=500` with `withCredentials: true`, correct response extraction from `data.items`, `totalCount` pagination awareness, and task launch URL construction — without restructuring the existing application.

---

### Add Business Automation Workflow integration to an Angular app using NgRx

**Prompt:**
> I have an Angular 17 application. It uses HttpClient and NgRx for state management. I want to add a Business Automation Workflow task dashboard to it.

**What to expect:** An Angular service using `HttpClient` with `withCredentials: true`, NgRx actions and effects for task state, correct task list endpoint and field names, task launch URL, and preservation of the existing NgRx architecture without introducing fetch or axios.

---

### Generate a new React task portal (no stack specified)

**Prompt:**
> Generate a personal task dashboard portal for Business Automation Workflow. I haven't picked a technology yet.

**What to expect:** A React application (defaulting to React with a stated assumption), including a Business Automation Workflow API service layer, stat cards (Overdue, At Risk, Active, Total), search/filter/sort, client-side pagination, an iframe modal for task launch using `/teamworks/process.lsw?zWorkflowState=1&zTaskId={TKIID}&zResetContext=true`, Carbon design tokens as CSS custom properties, configurable company branding, and a note about any unvalidated capabilities.

---

### Generate a Vue 3 personal task portal

**Prompt:**
> Generate a Business Automation Workflow personal task dashboard using Vue 3 with the Composition API.

**What to expect:** Vue 3 Composition API code with a `useBAWTasks` composable (no React hooks or JSX), correct task list endpoint, pagination with `totalCount` awareness, task launch URL, and stat cards — all in Vue idiom.

---

### Generate a standalone single-HTML portal

**Prompt:**
> Generate a standalone single-file HTML Business Automation Workflow task portal. No build tools, no npm — I'll serve it directly from the Business Automation Workflow server.

**What to expect:** A fully self-contained HTML file with all CSS and JS inline, including `escHtml()` for XSS prevention, numeric `taskId` validation, `credentials: 'same-origin'`, iframe modal task launch, pagination, search, filter, loading/error/empty states, and a pointer to the quality requirements in `references/hosting-and-generation.md`.

---

### Understand the correct team discovery endpoints

**Prompt:**
> How do I get a list of Business Automation Workflow teams in my portal? I want to build a manager team picker.

**What to expect:** The correct endpoints — `GET /rest/bpm/wle/v1/managedGlobalTeams` for manager-scoped team discovery and `GET /rest/bpm/wle/v1/globalTeams` for all visible teams — with a clear warning that `/rest/bpm/wle/v1/teams` (plural) does not exist, and a distinction between runtime global teams and Process Designer modeled teams (`/team/{teamId}`).

---

### Generate a manager team workload dashboard (non-federated)

**Prompt:**
> My manager needs a dashboard showing team workload — overdue and at-risk counts per team member, and a team task list. We're on non-federated Business Automation Workflow 24+.

**What to expect:** The correct WLE v2 dashboard endpoints (`/rest/bpm/wle/v2/dashboards/teamsummary`, `teamtasks/{teamId}` as PUT, `teammember/{teamId}`), the FDR probe pattern with a neutral empty state on HTTP 503, `managedGlobalTeams` for team discovery, and a statement that the WLE v1 legacy XSRF cookie mechanism is not assumed to apply to WLE v2 (verification-required).

---

### Build an executive cross-team aggregate dashboard

**Prompt:**
> Build an executive dashboard that shows aggregate overdue, at-risk, and active task counts across all of the current user's teams. We're on non-federated Business Automation Workflow.

**What to expect:** An explanation that no dedicated executive aggregate endpoint exists — aggregation is a client-side rollup across per-team `teamsummary/{teamId}` calls — the FDR probe as a prerequisite, and a note that Business Automation Workflow scopes `teamsummary` to the caller's managed teams so no extra portal-side role filter is needed.

---

### Get federated (PFS) task list integration

**Prompt:**
> Our environment uses Process Federation Server. Show me how to fetch a federated task list and handle the response correctly, including partial failures when one source system is down.

**What to expect:** The correct endpoint (`GET /rest/bpm/federated/v1/tasks?calcStats=true&size=500`), the response structure (`items[]` for tasks, `federationResult[]` at the top level with one entry per source system), `task.systemID` → `federationResult[]` mapping, per-system `statusCode` for partial-failure handling, and `totalCount` pagination.

---

### Construct a federated task launch URL

**Prompt:**
> I have a PFS federated task list response. Each task has a `systemID` and there's a `federationResult` array in the response. How do I build the URL to open a task in an iframe?

**What to expect:** The routing procedure: read `task.systemID`, find the matching `federationResult[]` entry, validate and allowlist `taskCompletionUrlPrefix`, then compose `{taskCompletionUrlPrefix}/process.lsw?zWorkflowState=1&zTaskId={TKIID}&zResetContext=true` — plus a note that cross-origin portals must use `window.open()` instead of an iframe due to Business Automation Workflow CSP `frame-ancestors`.

---

### Add a process launcher to a portal

**Prompt:**
> I want to add a process launcher to my non-federated Business Automation Workflow portal. Show me how to get a list of launchable processes and start one.

**What to expect:** `GET /rest/bpm/wle/v1/exposed` for launchable items, filtered to `type='process'`, with `itemID`/`snapshotID`/`processAppID` fields explained; `POST /rest/bpm/wle/v1/process?action=start&bpdId={bpdId}&processAppId={processAppId}` with `bpdId` and `processAppId` parsed from the `startURL` field (never passing `itemID` directly, which causes HTTP 409) — using `credentials: 'same-origin'`; CSRF handling follows the verification-required contract.

---

### Handle Cloud Pak for Business Automation IAM authentication

**Prompt:**
> Our portal needs to support IBM Cloud Pak for Business Automation with IAM authentication. How does authentication differ from a standard non-federated Business Automation Workflow deployment, and how does XSRF handling change?

**What to expect:** An explanation that Cloud Pak for Business Automation uses `Authorization: Bearer <token>` (from the Cloud Pak for Business Automation IAM endpoint) rather than session-cookie auth, that `credentials: 'same-origin'` is not appropriate for bearer-token portals, and that Bearer-authenticated WLE v1 mutations were observed without a CSRF header on Cloud Pak for Business Automation 26.0.0 while the documented `BPMCSRFToken` contract remains verification-required for other deployments.

---

### Partly supported: administrator portal

**Prompt:**
> I need an admin view where the administrator can see all tasks across all users in the Business Automation Workflow system.

**What to expect:** An explanation that the all-users task list cannot be generated because its request shape is unresolved, and an offer of the supported alternatives: the standard persona UI plus a process-visibility panel that appears only when Business Automation Workflow returns data for the signed-in user. No unrestricted administrator access is assumed and no portal-side role check is used.

---

### Out-of-scope: inline task completion form

**Prompt:**
> My portal users need to complete Business Automation Workflow tasks inline — can you build the task completion form inside the portal so they don't navigate away?

**What to expect:** A clear statement that rebuilding the Business Automation Workflow task completion UI in-portal is out of scope — the task form is a Business Automation Workflow Coach/CSHS rendered by Business Automation Workflow itself and cannot be reproduced externally — with the correct task launch pattern (iframe modal using `/teamworks/process.lsw`) provided instead.

---

### Validate quality bar for a generated standalone portal

**Prompt:**
> I've generated a standalone HTML Business Automation Workflow portal. What should I check before deploying it?

**What to expect:** The accessibility, security and data-freshness requirements from [`references/hosting-and-generation.md`](../references/hosting-and-generation.md#quality-requirements-every-ui), and the runtime validation steps required before delivery (a test against a live Business Automation Workflow, keyboard navigation, screen reader, zoom/reflow, and CSP confirmation with the Business Automation Workflow administrator).

---
