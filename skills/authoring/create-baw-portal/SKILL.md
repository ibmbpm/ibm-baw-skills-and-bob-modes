---
name: create-baw-portal
description: >
  API-knowledge and portal-development skill for IBM Business Automation Workflow (BAW).
  Teaches developers which BAW APIs are needed for a requested portal, what they do, how to
  use them correctly, and how authorization, authentication, CORS, proxies, pagination, and
  XSRF affect implementation. Supports non-federated (WLE REST) and federated (PFS) environments.
  Three usage patterns: (1) API guidance only, (2) adapt an existing application, (3) generate
  a new portal or full application. Carbon is the default design system where appropriate.
  Does NOT generate BAW process diagrams (BPMN) or internal BAW XML artifacts.
metadata:
  version: 1.0.0
  display_name: BAW Portal Builder
  short_description: Build IBM BAW task portals — API guidance, portal generation, and existing-app integration for non-federated and PFS environments.
  example_prompts:
    - "Generate a personal task dashboard portal for BAW"
    - "Which API do I call to get the current user's name in my BAW portal?"
    - "I have an existing React app — add BAW task list integration using axios"
    - "How does pagination work with the BAW task list endpoint?"
    - "Generate a standalone single HTML BAW portal, no build tools"
    - "We're on Process Federation Server — show me how to fetch a federated task list"
    - "How do I open a BAW task in an iframe modal?"
    - "How do I handle XSRF tokens when calling BAW APIs?"
---

# create-baw-portal skill

## When to use this skill

Use this skill when a developer asks to:

- Understand which BAW REST APIs to call for a portal pattern (task dashboard, manager view, executive view)
- Integrate a portal with BAW task data, user identity, or team information
- Generate a new portal or full application that connects to BAW
- Adapt an existing application (React, Vue, plain JS, etc.) to use BAW APIs
- Understand authentication, CORS, proxy, XSRF, or pagination requirements
- Generate standalone single-HTML portal implementations
- Understand federated (PFS) versus non-federated (WLE) API differences
- Identify what BAW APIs are missing or unvalidated for a requested capability

Do not use this skill for:

- BAW process (BPMN) generation → `generate-baw-bpmn`
- Internal BAW XML or BPEL authoring

---

## Identify the usage pattern

Before proceeding, determine which of the three patterns applies:

| Pattern | Trigger phrases | Action |
|---|---|---|
| **API guidance only** | "Which API…", "What does this endpoint do…", "How does pagination work…", "What fields does the task list return…" | Provide accurate, evidence-classified API guidance from the references. No code unless asked. |
| **Existing application adaptation** | "I have a React app…", "Add BAW integration to my app…", "How do I call BAW from my Node/Vue/Angular app…" | Read the existing stack. Provide targeted integration guidance and code examples that fit the existing patterns. Do not replace the existing architecture. |
| **New portal or application generation** | "Generate a portal…", "Create a task dashboard…", "Build a BAW portal for my team…" | Generate using the developer-selected stack. Default to React only when no stack is specified. Support standalone single HTML when requested. |

---

## Gather required information

Before generating code or guidance, determine:

1. **Deployment environment** — non-federated BAW (WLE REST) or federated (PFS required)?
2. **Usage pattern** — guidance, adaptation, or generation?
3. **Persona(s)** — task worker, manager/team lead, executive/process owner, administrator-aware?
4. **Technology stack** — React, Vue, Angular, plain JS, single HTML, or developer's existing stack?
5. **Hosting** — same-origin BAW-hosted, external with proxy/gateway, or direct external access?
6. **Company branding** — brand name, primary color, or use defaults?

### Defaults for new portal generation

When the user requests new portal or application generation and has not specified the following, apply documented defaults rather than blocking:

- **Stack not specified** → default to **React**. State this assumption at the top of the response (e.g. "Defaulting to React since no stack was specified — let me know if you prefer Vue, Angular, or plain JS.").
- **Deployment environment not specified** → default to **non-federated (WLE REST)**. State this assumption. Do not assume non-federated when PFS context is mentioned.
- **Hosting not specified** → default to **same-origin BAW-hosted**. State this assumption. Provide proxy/CORS notes as a comment in generated code so the developer knows what to change for external deployments.
- **Company branding not specified** → default to **IBM branding**: header reads `IBM` (in `--ibm-blue-50`) + `BAW Process Portal` (in white). Do not generate placeholder SVG logos, initials badges, or any graphic that could be mistaken for another company's brand. If the developer names a company, use that name as plain text only.

**Block and ask only when:**
- The user explicitly mentions an existing application — read the stack before generating.
- PFS or Process Federation Server is mentioned — confirm the federated deployment before generating federated code.

---

## When to inspect an existing repository

If the user has an existing application:

1. Read the existing stack, dependencies, and folder structure before recommending any API patterns.
2. Identify the existing HTTP client (fetch, axios, etc.) and use it rather than introducing a new one.
3. Identify the existing authentication pattern and map BAW session or token requirements to it.
4. Preserve the existing component architecture. Do not refactor unrelated code.

---

## Choose the correct API family

Read [`references/non-federated-api-guide.md`](references/non-federated-api-guide.md) and [`references/federated-api-guide.md`](references/federated-api-guide.md) before generating any BAW API calls.

| Condition | API family |
|---|---|
| Single BAW server, no PFS | WLE REST API (`/rest/bpm/wle/v1/`) |
| Process Federation Server deployed | PFS Federated API (`/rest/bpm/federated/v1/`) |
| Manager or executive dashboards, BAW 24+ | WLE v2 dashboard APIs (`/rest/bpm/wle/v2/dashboards/`) |
| Manager or executive dashboards, PFS | PFS v2 dashboard APIs (`/rest/bpm/federated/v2/dashboards/`) |
| Task mutations (claim, assign, finish, cancel) | WLE v1 task action pattern (delivery scope label: V2 — not a reference to the WLE v2 API family) |

**Key rules:**

- Do not use `/rest/bpm/wle/v1/teams` (plural) — this endpoint does not exist. The correct endpoints are: `/rest/bpm/wle/v1/team/{teamId}` (singular — look up a single modeled team by ID, documented in IBM BAW docs), `/rest/bpm/wle/v1/managedGlobalTeams` (teams managed by the current user), and `/rest/bpm/wle/v1/globalTeams` (all global teams visible to the current user).
- `size=500` means up to 500 tasks, not all tasks. Always check `totalCount` and page when needed.
- **CSRF (also called XSRF) for browser portals:** Same-origin browser portals use session cookie (`credentials: 'same-origin'`) only — no `bpm-csrf-token` header required for any WLE endpoint. `BPMCSRFToken` applies only to the BPM standard API (`/rest/bpm/std/`), not to WLE REST. Do not add CSRF header handling to generated portal code unless calling `/rest/bpm/std/` endpoints.
- Do not use `filterByCurrentUser=true` and `interaction=claimed_and_available` interchangeably — they have different semantics.

---

## Preserve an existing stack

When adapting an existing application:

1. Keep the existing component structure and routing.
2. Wrap BAW API calls in a service module that the existing app can import.
3. Map BAW authentication to the existing auth pattern (same-origin session, proxy-forwarded session, or token).
4. Use the existing HTTP client — do not add fetch wrappers if axios is already present.
5. Do not restructure non-API parts of the application.

---

## Generate a new application

When generating a new portal:

1. Use the developer-specified stack. Default to React only when no stack is specified.
2. Support standalone single HTML when requested — this is a valid and useful output format.
3. Derive patterns from the approved reference design in `assets/examples/ibm-baw-task-dashboard/`.
4. Do not copy the approved reference design destructively. Treat it as a reference, not a template to be overwritten or restyled.
5. Apply Carbon design tokens as CSS custom properties where appropriate.
6. Support company branding via configurable CSS variables and header text.
7. The existing BAW task UI is opened in an iframe modal — do not attempt to rebuild the task completion UI.
8. **Always include a truncation indicator** when the task list is paginated. When `totalCount` in the API response exceeds the number of items returned, surface a visible message to the user — for example: _"Showing 500 of 1,243 tasks. Use pagination to view more."_ Do not silently drop overflow items or present a partial list as complete.
9. **Task iframe in an external portal requires two server-side prerequisites — state both explicitly before generating iframe code for Profile C.**
   BAW's task form issues browser-visible redirects to absolute BAW URLs mid-flow. A proxy prefix on the iframe `src` does not help — the browser follows the redirect outside the proxy and lands on the BAW origin directly. The only working approach for Profile C is:
   - **BAW CSP change (required):** Add the portal origin to the BAW CSP `frame-ancestors` directive.
     - **Traditional WAS deployment:** Set `Security.ContentSecurityPolicyHeaderValue` via wsadmin — `AdminTask.setBPMProperty(['-name', 'Security.ContentSecurityPolicyHeaderValue', '-value', "... frame-ancestors 'self' https://{portal-origin} ..."])` → `AdminConfig.save()` → server restart.
     - **CP4BA on containers (OpenShift):** Edit the `ICP4ACluster` custom resource. Set `spec.baw_configuration[*].environment_config.content_security_policy_additional_frame_ancestor` to include `["https://{portal-origin}"]`. The operator applies the change without a manual server restart.
   - **Portal must be HTTPS (required):** BAW's `LtpaToken2` is `Secure; SameSite=Strict`. An `http://` portal will not receive this cookie inside the iframe — the user gets a BAW login prompt. The portal must be served over HTTPS on the same scheme as BAW.
   - **Profile A / A2 (BAW-hosted):** No prerequisites. Use bare relative `/teamworks/process.lsw?...` — same origin, `frame-ancestors 'self'` satisfied automatically, cookies flow freely.
   - **Profile C, prerequisites not met:** Do not generate iframe code. Tell the developer both prerequisites and offer new-tab launch as a fallback that works without any server change.
   - **Never generate `https://{baw-host}:{port}/teamworks/...` as an iframe `src`** — cross-origin, blocked immediately.

Read [`references/hosting-and-generation.md`](references/hosting-and-generation.md) for hosting patterns, authentication prerequisites, and CORS requirements.

---

## Handle unvalidated capabilities

This skill distinguishes runtime-tested APIs from documentation-only and untested ones. Before generating code for an unvalidated capability:

1. If an API has only been confirmed in IBM documentation but not runtime-tested, say so plainly — e.g. "This endpoint is documented by IBM but has not been tested at runtime in this project."
2. For capabilities gated on runtime validation (e.g. PFS dashboard APIs, administrator-aware endpoints), state the validation requirement clearly.
3. The Administrator persona is defined — dashboards, APIs, and detection pattern are documented in `references/personas-and-capabilities.md`. Do not generate admin-scoped code until the relevant APIs are runtime-verified.
4. Do not generate speculative code for unresolved gaps without an explicit PM or product decision.

Read [`references/known-gaps.md`](references/known-gaps.md) before generating code for PFS dashboard or OAuth/OIDC capabilities.

---

## Keep developer notes out of rendered UI

API validation status, gap references, runtime-test results, and deployment caveats are
**developer communications**, not end-user content. They must never appear as visible UI elements
— banners, info cards, badges, or notices — in generated HTML.

Apply this rule for every capability gated on a deployment condition or validation gap:

1. **Developer communication** → place in the chat response text or as an HTML comment. Never
   render it as a visible DOM element.
2. **Deployment-gated features** (e.g. FDR required for dashboard APIs) → generate a clean
   runtime check in JavaScript. Catch the relevant HTTP status silently and render a plain,
   user-facing empty-state message. Never hardcode HTTP status codes, internal error codes
   (`CWTBG0788E`), gap IDs, or API paths into any visible UI string.
3. **Feature not yet available** → render a neutral empty state (e.g. "This feature is not
   available in your environment. Contact your administrator."). No technical details visible.

**Concrete pattern for FDR-gated features:**
```js
if (res.status === 503) {
  resultEl.innerHTML = '<p>Team workload data is unavailable. Contact your BAW administrator.</p>';
  return;
}
```
Not:
```js
// ❌ Never do this
result.innerHTML = '<strong>HTTP 503 — FDR not enabled.</strong> Contact your BAW administrator.';
```

---

## Validate and report results

After generating or adapting code:

1. Flag any API call that has not been runtime-tested — use plain language, not internal evidence labels.
2. Identify any unvalidated capabilities included and state the validation required.
3. Do not claim live runtime validation unless an authenticated BAW environment was used in this session.
4. For other stacks, state equivalent quality requirements from [`references/quality-and-validation.md`](references/quality-and-validation.md).

For standalone HTML implementations, point the developer to the quality bar defined in
[`references/quality-and-validation.md`](references/quality-and-validation.md). The three static
audit scripts (`audit-a11y.mjs`, `audit-security.mjs`, `audit-refresh.mjs`) validate the approved
reference example only — they are hardcoded to
`assets/examples/ibm-baw-task-dashboard/ibm-baw-task-dashboard.html` and cannot be pointed at
generated output. Use them to understand the expected quality bar, not as a post-generation check
for new portals.

---

## References

Read the appropriate references before responding:

| Reference | When to read |
|---|---|
| [`references/architecture-and-usage.md`](references/architecture-and-usage.md) | Always — understand the skill's flow and output types |
| [`references/non-federated-api-guide.md`](references/non-federated-api-guide.md) | Always before generating any non-federated BAW API calls — tasks, user identity, task launch, mutations, dashboard endpoints |
| [`references/federated-api-guide.md`](references/federated-api-guide.md) | Always before generating any PFS/federated API calls |
| [`references/personas-and-capabilities.md`](references/personas-and-capabilities.md) | Understanding persona requirements and API mapping |
| [`references/hosting-and-generation.md`](references/hosting-and-generation.md) | Stack selection, hosting, CORS, auth, generation patterns |
| [`references/quality-and-validation.md`](references/quality-and-validation.md) | Accessibility, security, refresh pipeline, static audit scripts |
| [`references/known-gaps.md`](references/known-gaps.md) | Unresolved API and validation gaps affecting any capability |

Full API inventory and discovery evidence: `docs/04-api-inventory.md`, `docs/02-evidence-inventory.md`

---

## What this skill does not do

- Generate internal BAW XML or BPEL artifacts
- Build BAW processes or BPMN diagrams
- Rebuild the BAW task completion UI (the existing BAW task UI is launched via iframe)
- Generate admin-scoped code before administrator API endpoints are runtime-verified (see `references/personas-and-capabilities.md` §Administrator)
