# Hosting and generation

> **Skill:** `create-baw-portal`
> **Purpose:** How to select a hosting model, generate a new application, adapt an existing one,
> and handle authentication and CORS for each configuration.

---

## Hosting models

### External portal — same proxy or gateway

The portal is hosted externally but communicates with BAW through a proxy or API gateway
that forwards the user's authenticated session or manages API keys.

**Authentication:** Session cookie forwarded by proxy, OR gateway exchanges tokens.
**CORS:** Not required if all BAW API calls are proxied (same-origin to portal).
**Note:** The proxy must not modify `Authorization` headers in ways that break BAW session validation.

**Task iframe critical constraint — proxy does NOT solve frame-ancestors for task forms:**
BAW REST API calls (XHR/fetch) work correctly through a proxy because the browser never
follows redirects for XHR. However, the BAW task form (`/teamworks/process.lsw`) issues
a **browser-visible `Location:` redirect** mid-flow to an absolute BAW URL
(e.g. `https://baw-server:9443/teamworks/fauxRedirect.lsw?...`). The browser follows this
redirect directly — outside the proxy — and lands on the BAW origin. At that point
`frame-ancestors 'self'` applies again. A proxy prefix on the initial iframe `src` URL does
not prevent this. The only solutions for iframe task launch in an external portal are:

1. **Add the portal origin to `frame-ancestors`** via `Security.ContentSecurityPolicyHeaderValue`
   in wsadmin (verified — `AdminTask.setBPMProperty` + `AdminConfig.save()` + server restart).
2. **Serve the portal over HTTPS on the same hostname as BAW** so that BAW's `SameSite=Strict`
   session cookie flows into the iframe (verified — BAW cookies are `Secure; SameSite=Strict`
   and will not flow from an `http://` portal into an `https://` iframe).

Both conditions must be met simultaneously for an external portal iframe to work:
- Portal origin must be in BAW's `frame-ancestors`
- Portal must be HTTPS (same scheme as BAW) so `SameSite=Strict` cookies are sent in the iframe

### Same-origin (BAW-hosted)

The portal HTML is served directly from the BAW server. The browser session cookie is valid
for both the portal origin and the BAW API origin — no CORS configuration required.

**Authentication:** `credentials: 'same-origin'` with existing BAW session. No token management.
**CORS:** Not required.
**CSP:** BAW server enforces `Content-Security-Policy`. Test CSP header with BAW administrator
before deploying inline implementations.

This is the model used by the approved reference implementation.
See `assets/examples/ibm-baw-task-dashboard/` for the reference design.

### External portal — direct access

The portal communicates directly with the BAW server from the browser.

**Authentication:** OAuth/OIDC bearer token or Basic Auth depending on BAW configuration.
Must configure the external origin as an allowed CORS origin in BAW.
**CORS:** BAW returns full CORS headers when an `Origin` header is present on both preflight (OPTIONS) and actual requests. Confirmed headers: `Access-Control-Allow-Origin: <requesting-origin>`, `Access-Control-Allow-Credentials: true`, `Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS`. BAW echoes the requesting origin back — it does not use `*`. This means `credentials: 'include'` works for cross-origin fetch calls when the portal origin is in BAW's allowed origins list.
**Note:** If the portal origin is not in BAW's CORS allowlist, all XHR/fetch calls will fail with CORS errors in the browser. The proxy/gateway model avoids this requirement entirely.

---

## Authentication prerequisites

Before generating external portal code, confirm:

1. **Authentication mechanism** — session cookie forwarding, OAuth bearer token, or other?
2. **CORS configuration** — is the portal origin allowed in BAW's CORS settings?
3. **Token management** — how does the portal obtain and refresh access tokens?
4. **XSRF handling** — `BPMCSRFToken` is only required for the BPM standard API (`/rest/bpm/std/`). WLE REST (`/rest/bpm/wle/`) and PFS (`/rest/bpm/federated/`) use session cookie auth for same-origin portals with no CSRF header required.
5. **Task iframe prerequisites (external portal)** — two conditions must both be met:
   - The portal origin must be added to BAW's `frame-ancestors` via `Security.ContentSecurityPolicyHeaderValue` (wsadmin `AdminTask.setBPMProperty` → `AdminConfig.save()` → server restart).
   - The portal must be served over **HTTPS**. BAW's `LtpaToken2` cookie is `Secure; SameSite=Strict`. A portal served over `http://` will not receive the BAW session cookie inside the iframe, causing a login prompt. Both the portal and BAW must use HTTPS.

For same-origin BAW-hosted portals, none of CORS, token management, or cross-origin considerations apply.

### Cookie-based proxy authentication — verified

BAW issues three cookies on authentication: `LtpaToken2` (SSO token), `JSESSIONID` (session), and `XSRF-TOKEN`. A proxy that forwards all three cookies from the authenticated user to BAW will authenticate correctly without re-issuing credentials.

### Bearer token authentication — verified

On CP4BA deployments, BAW REST accepts `Authorization: Bearer <token>` directly. The token is obtained from the CP4BA IAM endpoint (`POST /icp4d-api/v1/authorize`). No session cookie is required.

**Cross-origin caveat:** A browser-based external portal sending a Bearer token with an `Origin` header will receive HTTP 403 unless the portal's origin is in the BAW CORS allowlist. The BAW administrator must configure the allowed origin. Without that configuration, the proxy model is the only option for external portals.

**OIDC client credentials:** CP4BA exposes an OIDC token endpoint at `/oidc/endpoint/OP/token` supporting the `password` and `client_credentials` grant types. Using these flows requires a registered OIDC client ID and secret — these are deployment-specific values the BAW administrator must provide. Do not generate OIDC token-acquisition code without these values.

---

## Technology stack selection

When a developer specifies a stack, use it. Do not introduce a different framework.

**Default stack rule:** Use React only when the developer has not specified a stack.

**Supported on request:**

| Stack | Notes |
|---|---|
| React | Default when no stack specified |
| Vue | Follow existing Vue patterns if adapting |
| Angular | Follow existing Angular service/component patterns |
| Svelte | Follow existing Svelte store and component patterns |
| Plain JavaScript (ES modules) | Suitable for greenfield without build tooling |
| Standalone single HTML | Self-contained; all CSS and JS inline; no build step |

---

## Standalone single HTML

A single HTML file is a valid and useful output format. It is appropriate when:

- The developer wants to deploy without a build pipeline
- BAW is hosting the portal directly (same-origin)
- A quick demo or proof-of-concept is needed
- The deployment environment restricts external asset loading

For standalone HTML, all CSS and JS must be inline. Do not reference external CDN assets
unless the deployment is confirmed to allow the required origins in its CSP.

The approved reference implementation (`ibm-baw-task-dashboard.html`) is a standalone single HTML portal
and is the canonical example of this pattern.

---

## Existing application adaptation

When adapting an existing application:

1. **Read the existing stack first** before suggesting any API integration pattern.
2. **Use the existing HTTP client** — do not introduce `fetch` if `axios` is already present.
3. **Create a service module** (e.g., `bawApiService.js`) that wraps BAW API calls.
4. **Map BAW auth to the existing auth pattern** — do not redesign the application's authentication.
5. **Do not refactor unrelated code** — only touch files necessary for the integration.
6. **Match the existing folder and module structure** — place BAW service files where sibling services live.

---

## Branding defaults

When the developer has not specified a company name or logo, **default to IBM branding**:

- Header text: `IBM` (in `--ibm-blue-50`) followed by `BAW Process Portal` (in white)
- No logo SVG or icon — IBM branding is text-only in the header, matching the Carbon UI Shell pattern
- Do not generate placeholder SVG badges, initials boxes, or any graphic that could be mistaken for another company's logo
- If the developer specifies a company name, use that name as plain text in the header; still no invented SVG icon

---

## Fully featured portal — mandatory feature checklist

When a developer asks for a "fully featured" portal, every feature in this checklist must be present. Do not omit any item. If a feature cannot be implemented due to a known gap, name it explicitly and provide a placeholder.

### My Tasks view (task worker)
- [ ] Stat cards: Overdue, At Risk, Active, All Tasks — each clickable as a filter, colored count
- [ ] Search input with search icon inside the field
- [ ] Priority filter dropdown (custom chevron, no native appearance)
- [ ] Status filter dropdown
- [ ] Clear filters button (appears only when filters are active)
- [ ] Result count + truncation banner when `totalCount` exceeds returned items
- [ ] Refresh bar: last-updated timestamp + stale warning + refresh button with spinner
- [ ] Task table with sortable columns: Task Name, Process, Priority, Due Date, Status, Actions
- [ ] Per-row action buttons: **Open**, **Claim** (when unclaimed), **Cancel**, **Reassign**
- [ ] Inline priority dropdown per row (updates immediately via `action=update`)
- [ ] Mobile card layout (≤ 680px) — table hidden, cards shown
- [ ] Pull-to-refresh on mobile (swipe-down gesture)
- [ ] Pagination (prev/next + page numbers)
- [ ] Nav badge on My Tasks sidebar item showing overdue count
- [ ] Task iframe modal with focus trap, Escape key, return-focus on close

### Dialogs
- [ ] Generic confirm dialog (used for Release task — releases claim on a claimed task only)
- [ ] Reassign dialog — username input + reassign / back-to-pool options
- [ ] Save search dialog — name input
- [ ] Rename saved search dialog

### Process launcher view
- [ ] Load exposed processes via `GET /rest/bpm/wle/v1/exposed`
- [ ] Card grid of launchable processes
- [ ] Start process button per card — use `startURL` from the exposed item to derive `bpdId` and `processAppId`; see non-federated-api-guide.md Process launch section for the verified pattern and what fails
- [ ] Auto-open first task after start (if `data.tasks[0].tkiid` present)

### Saved searches view
- [ ] List saved searches via `GET /rest/bpm/wle/v1/searches/tasks`
- [ ] Chip/card per saved search — click to run
- [ ] Run saved search → results table (reuses task table component)
- [ ] Save current search as named search (`POST /rest/bpm/wle/v1/searches/tasks`)
- [ ] Rename saved search (`PUT /rest/bpm/wle/v1/searches/tasks/{name}`)
- [ ] Delete saved search (`DELETE /rest/bpm/wle/v1/searches/tasks/{name}`)

### Header
- [ ] IBM / company branding text (no invented SVG logo)
- [ ] User avatar (initials) — clickable
- [ ] User profile dropdown: full name, username, email, manager, job title (from `GET /rest/bpm/wle/v1/user/current?parts=all`)

### Sidebar
- [ ] Section labels
- [ ] Nav badges (overdue count on My Tasks)
- [ ] Mobile hamburger toggle (hidden on desktop)
- [ ] Sidebar overlay/close on mobile

### Accessibility (all views)
- [ ] Skip link to main content
- [ ] `role="status"` on loading, `role="alert"` on errors
- [ ] `aria-live="polite"` on result count and last-updated bar
- [ ] `aria-live="assertive"` on toast container
- [ ] `aria-sort` on sortable column headers
- [ ] `aria-pressed` on stat card filter buttons
- [ ] Focus ring visible on all interactive elements
- [ ] `prefers-reduced-motion` suppresses all animations

---

## Greenfield application generation

When generating a new portal from scratch:

1. Use the developer-specified stack (or React if none specified).
2. Structure the project following the selected framework's conventions.
3. Create a BAW API service layer separate from UI components.
4. Apply Carbon design tokens as CSS custom properties — do not import Carbon component libraries
   unless the developer has requested full Carbon component usage.
5. Apply IBM branding by default (see Branding defaults above). Use developer-supplied name/colors only when explicitly provided.
6. The existing BAW task UI is opened in an iframe modal — do not attempt to rebuild task completion.
7. **Every item in the fully featured portal checklist above must be implemented.** Before submitting generated code, verify each checkbox is covered. Name any intentionally omitted item and give a reason.

---

## Using the approved reference design

The approved reference implementation at `assets/examples/ibm-baw-task-dashboard/` demonstrates
what the API knowledge in this skill can produce.

**Permitted uses:**

- Study the integration patterns (API calls, response handling, task launch, pagination)
- Copy specific patterns (the task extraction logic, the priority normalisation, the state normalisation)
- Reference the accessibility and security patterns documented in `references/quality-and-validation.md`

**Prohibited actions:**

- Do not regenerate, restyle, or structurally rewrite the approved design
- Do not modify `ibm-baw-task-dashboard.html`
- Do not rerun completed audit passes without a specific reason

The reference implementation is an immutable baseline. New portals are derived from it, not copies of it.

---

## Carbon design system

Carbon is the default design system where appropriate.

**Supported approaches:**

| Approach | When to use |
|---|---|
| Carbon design tokens as CSS custom properties | Default — no build tooling required |
| Official `@carbon/react` components | When developer requests Carbon component library |
| Customer branding over Carbon tokens | Developer-supplied color tokens replace Carbon defaults |

Always define brand and Carbon colors in `:root` CSS custom properties so they can be
overridden per deployment without modifying generated component code.

---

## Pagination

All generated portals must handle pagination correctly.

- `size=500` requests up to 500 tasks, not all tasks
- When `totalCount` in the response exceeds the number of returned items, additional pages exist
- Page with `offset` incremented by `size`
- Show a truncation indicator when the displayed list does not include all available tasks
- The paging contract (`totalCount`, `offset`, `size`) is VERIFIED BY IBM DOCUMENTATION

Do not silently discard tasks beyond `size=500` without informing the user.
