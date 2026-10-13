# BAW Portal Builder — Documentation

> API-knowledge and portal-development skill for IBM® Business Automation Workflow (BAW). Teaches developers which BAW APIs are needed for a requested portal, how to use them correctly, and how authentication, CORS, proxies, pagination, and XSRF affect implementation. Supports non-federated (WLE REST) and federated (PFS) environments.

## Purpose

The `create-baw-portal` skill helps developers build web portals that connect to IBM® Business Automation Workflow. It covers three distinct scenarios: answering API-specific questions, integrating BAW into an existing application, and generating a new portal from scratch. It supports both non-federated BAW (WLE REST API) and federated deployments using Process Federation Server (PFS), and defaults to React with Carbon design tokens when no stack is specified.

Use this skill when a developer needs to know which BAW endpoints to call, how to authenticate, how to handle pagination or XSRF tokens, how to launch BAW tasks in an iframe, or how to generate a full portal for task workers, managers, executives, or team leads.

## Setup and configuration

- No special tools or MCP servers are required.
- **Node.js** (`node`) is required only to run the three static audit scripts that validate the approved reference HTML (`audit-a11y.mjs`, `audit-security.mjs`, `audit-refresh.mjs`). These scripts are hardcoded to the reference file (`assets/examples/ibm-baw-task-dashboard/ibm-baw-task-dashboard.html`) and cannot be used on generated output.
- The audit scripts have no external `npm` dependencies — Node stdlib only.
- A live BAW instance is required for runtime validation of generated portals; the skill itself does not connect to any BAW server.

## Compatibility

- **Non-federated WLE v2 dashboard APIs** (manager/executive dashboards) require **BAW 24+** with the Federated Dashboard Repository (FDR) feature enabled. The skill probes FDR at runtime via `GET /rest/bpm/wle/v2/dashboards/teamsummary`: HTTP 200 = FDR enabled; HTTP 503 = FDR not enabled. Do not rely on a version check alone.
- **Federated API family** (`/rest/bpm/federated/`) requires a **Process Federation Server** deployment. The federated task list endpoint returns HTTP 404 on a non-federated BAW server — confirm your environment before requesting PFS-specific guidance or code.
- **CSRF / XSRF** — the WLE REST API (`/rest/bpm/wle/`) and PFS API (`/rest/bpm/federated/`) have no CSRF filter for same-origin browser portals. `BPMCSRFToken` applies only to the BPM standard API (`/rest/bpm/std/`). Do not add CSRF header handling to portal code unless calling `/rest/bpm/std/` endpoints.
- **CP4BA deployments** use `Authorization: Bearer <token>` (IAM) instead of session-cookie auth. A live CP4BA IAM endpoint is required to obtain the token. Do not use `credentials: 'same-origin'` for CP4BA.
- **Administrator-aware features** are blocked: the administrator persona has not been defined by product management. No admin portal capabilities can be scoped, mapped, or generated until a PM decision is made.
- **Standalone HTML audit scripts** validate the approved reference example only — they cannot be pointed at generated portal files.

## Prompt examples

### Get guidance on a specific API

**Prompt:**
> Which BAW API returns the current user's full name? What fields does the response include, and do I need any special headers for a same-origin portal?

**What to expect:** The exact endpoint (`GET /rest/bpm/wle/v1/user/current?parts=all`), the relevant response fields (`data.fullName`, `data.displayName`, `data.userName`), and a clear statement that no XSRF header is needed for same-origin portals calling WLE REST.

---

### Understand pagination for the task list

**Prompt:**
> How does pagination work with the BAW WLE task list endpoint? I want to make sure I'm not silently truncating tasks.

**What to expect:** An explanation of the `size`, `offset`, and `totalCount` paging contract, the correct pattern for iterating pages using `offset` incremented by `size`, and guidance on surfacing a truncation indicator when `totalCount` exceeds the number of returned items.

---

### Understand XSRF token requirements for mutations

**Prompt:**
> I need to claim and reassign tasks using the WLE v1 task mutation endpoints. Should I add a bpm-csrf-token header for PUT requests in my same-origin browser portal?

**What to expect:** A clear explanation that WLE v1 (`/rest/bpm/wle/v1`) mutations require session cookie (`credentials: 'same-origin'`) only — no `bpm-csrf-token` — with a distinction from the BPM standard API (`/rest/bpm/std/`) which does require a `BPMCSRFToken` JWT.

---

### Add BAW task integration to an existing React app using axios

**Prompt:**
> I have an existing React application. It uses axios for all HTTP calls. I need to add a BAW personal task list to it. We're on a single non-federated BAW server hosted at the same origin.

**What to expect:** A `bawApiService.js` module written in axios (not fetch), calling `GET /rest/bpm/wle/v1/tasks?interaction=claimed_and_available&size=500` with `withCredentials: true`, correct response extraction from `data.items`, `totalCount` pagination awareness, and task launch URL construction — without restructuring the existing application.

---

### Add BAW integration to an Angular app using NgRx

**Prompt:**
> I have an Angular 17 application. It uses HttpClient and NgRx for state management. I want to add a BAW task dashboard to it.

**What to expect:** An Angular service using `HttpClient` with `withCredentials: true`, NgRx actions and effects for task state, correct task list endpoint and field names, task launch URL, and preservation of the existing NgRx architecture without introducing fetch or axios.

---

### Generate a new React task portal (no stack specified)

**Prompt:**
> Generate a personal task dashboard portal for BAW. I haven't picked a technology yet.

**What to expect:** A React application (defaulting to React with a stated assumption), including a BAW API service layer, stat cards (Overdue, At Risk, Active, Total), search/filter/sort, client-side pagination, an iframe modal for task launch using `/teamworks/process.lsw?zWorkflowState=1&zTaskId={TKIID}&zResetContext=true`, Carbon design tokens as CSS custom properties, configurable company branding, and a note about any unvalidated capabilities.

---

### Generate a Vue 3 personal task portal

**Prompt:**
> Generate a BAW personal task dashboard using Vue 3 with the Composition API.

**What to expect:** Vue 3 Composition API code with a `useBAWTasks` composable (no React hooks or JSX), correct task list endpoint, pagination with `totalCount` awareness, task launch URL, and stat cards — all in Vue idiom.

---

### Generate a standalone single-HTML portal

**Prompt:**
> Generate a standalone single-file HTML BAW task portal. No build tools, no npm — I'll serve it directly from the BAW server.

**What to expect:** A fully self-contained HTML file with all CSS and JS inline, including `escHtml()` for XSS prevention, numeric `taskId` validation, `credentials: 'same-origin'`, iframe modal task launch, pagination, search, filter, loading/error/empty states, and a pointer to the quality checklist in `references/quality-and-validation.md`.

---

### Understand the correct team discovery endpoints

**Prompt:**
> How do I get a list of BAW teams in my portal? I want to build a manager team picker.

**What to expect:** The correct endpoints — `GET /rest/bpm/wle/v1/managedGlobalTeams` for manager-scoped team discovery and `GET /rest/bpm/wle/v1/globalTeams` for all visible teams — with a clear warning that `/rest/bpm/wle/v1/teams` (plural) does not exist, and a distinction between runtime global teams and Process Designer modeled teams (`/team/{teamId}`).

---

### Generate a manager team workload dashboard (non-federated)

**Prompt:**
> My manager needs a dashboard showing team workload — overdue and at-risk counts per team member, and a team task list. We're on non-federated BAW 24+.

**What to expect:** The correct WLE v2 dashboard endpoints (`/rest/bpm/wle/v2/dashboards/teamsummary`, `teamtasks/{teamId}` as PUT, `teammember/{teamId}`), the FDR probe pattern with a neutral empty state on HTTP 503, `managedGlobalTeams` for team discovery, and session-cookie-only auth — no `bpm-csrf-token` for WLE v2.

---

### Build an executive cross-team aggregate dashboard

**Prompt:**
> Build an executive dashboard that shows aggregate overdue, at-risk, and active task counts across all of the current user's teams. We're on non-federated BAW.

**What to expect:** An explanation that no dedicated executive aggregate endpoint exists — aggregation is a client-side rollup across per-team `teamsummary/{teamId}` calls — the FDR probe as a prerequisite, and a note that BAW scopes `teamsummary` to the caller's managed teams so no extra portal-side role filter is needed.

---

### Get federated (PFS) task list integration

**Prompt:**
> Our environment uses Process Federation Server. Show me how to fetch a federated task list and handle the response correctly, including partial failures when one source system is down.

**What to expect:** The correct endpoint (`GET /rest/bpm/federated/v1/tasks?calcStats=true&size=500`), the response structure (`items[]` for tasks, `federationResult[]` at the top level with one entry per source system), `task.systemID` → `federationResult[]` mapping, per-system `statusCode` for partial-failure handling, and `totalCount` pagination.

---

### Construct a federated task launch URL

**Prompt:**
> I have a PFS federated task list response. Each task has a `systemID` and there's a `federationResult` array in the response. How do I build the URL to open a task in an iframe?

**What to expect:** The routing procedure: read `task.systemID`, find the matching `federationResult[]` entry, validate and allowlist `taskCompletionUrlPrefix`, then compose `{taskCompletionUrlPrefix}/process.lsw?zWorkflowState=1&zTaskId={TKIID}&zResetContext=true` — plus a note that cross-origin portals must use `window.open()` instead of an iframe due to BAW CSP `frame-ancestors`.

---

### Add a process launcher to a portal

**Prompt:**
> I want to add a process launcher to my non-federated BAW portal. Show me how to get a list of launchable processes and start one.

**What to expect:** `GET /rest/bpm/wle/v1/exposed` for launchable items, filtered to `type='process'`, with `itemID`/`snapshotID`/`processAppID` fields explained; `POST /rest/bpm/wle/v1/process?action=start&bpdId={bpdId}&processAppId={processAppId}` with `bpdId` sourced from the `startURL` field or `itemID` as fallback — using `credentials: 'same-origin'` only, no CSRF header.

---

### Handle CP4BA IAM authentication

**Prompt:**
> Our portal needs to support IBM CP4BA with IAM authentication. How does authentication differ from a standard non-federated BAW deployment, and how does XSRF handling change?

**What to expect:** An explanation that CP4BA uses `Authorization: Bearer <token>` (from the CP4BA IAM endpoint) rather than session-cookie auth, that `credentials: 'same-origin'` is not appropriate for bearer-token portals, and that neither standard BAW nor CP4BA requires a `bpm-csrf-token` header for WLE REST endpoints.

---

### Out-of-scope: administrator portal

**Prompt:**
> I need an admin view where the administrator can see all tasks across all users in the BAW system.

**What to expect:** A clear statement that the administrator persona is not yet defined (a named PM-owned blocker), no admin capability code generated, an explanation of what must be defined before implementation can begin (persona scope, permissions, authorization model), and a recommendation to use placeholder navigation ("Administrator views — coming soon") until the persona is defined.

---

### Out-of-scope: inline task completion form

**Prompt:**
> My portal users need to complete BAW tasks inline — can you build the task completion form inside the portal so they don't navigate away?

**What to expect:** A clear statement that rebuilding the BAW task completion UI in-portal is out of scope — the task form is a BAW Coach/CSHS rendered by BAW itself and cannot be reproduced externally — with the correct task launch pattern (iframe modal using `/teamworks/process.lsw`) provided instead.

---

### Validate quality bar for a generated standalone portal

**Prompt:**
> I've generated a standalone HTML BAW portal. What should I check before deploying it?

**What to expect:** The static quality checklist covering accessibility (78 checks), security (25 checks), and refresh pipeline (40 checks) requirements from `references/quality-and-validation.md`, a note that the three audit scripts (`audit-a11y.mjs`, `audit-security.mjs`, `audit-refresh.mjs`) validate the approved reference HTML only and cannot be run against generated output, and the runtime validation steps required before delivery (live BAW test, keyboard navigation, screen reader, zoom/reflow, CSP confirmation with BAW administrator).

---
