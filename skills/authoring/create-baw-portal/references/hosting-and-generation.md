# Hosting and generation

> **Skill:** `create-baw-portal`
> **Purpose:** How to select a hosting model, generate a new application, adapt an existing one,
> and handle authentication and CORS for each configuration.

---

## Hosting models

### External portal — same proxy or gateway

The portal is hosted externally but communicates with Business Automation Workflow through a proxy or API gateway
that forwards the user's authenticated session or manages API keys.

**Authentication:** Session cookie forwarded by proxy, OR gateway exchanges tokens.
**CORS:** Not required if all Business Automation Workflow API calls are proxied (same-origin to portal).
**Note:** The proxy must not modify `Authorization` headers in ways that break Business Automation Workflow session validation.

**Task iframe constraint — a reverse proxy does NOT, by itself, make the task form embeddable.**

> **Policy owner.** This section is the single owner of the iframe / proxy / CSP / cookie
> prerequisites. Every other file (`SKILL.md`, the API guides, `task-lifecycle.md`,
> `federated-portal-integration.md`, `catalog.json`, `intent-map.json`) states only the minimum
> and links here.

Business Automation Workflow REST API calls (XHR/fetch) work through a proxy because the browser never follows
redirects for XHR. The Business Automation Workflow task form (`/teamworks/process.lsw`) is different: on the tested
deployment it issued a **browser-visible `Location:` redirect** mid-flow to an absolute Business Automation Workflow URL
(e.g. `https://baw-server:9443/teamworks/fauxRedirect.lsw?...`). The browser follows that
redirect directly — outside the proxy — and lands on the Business Automation Workflow origin, where
`frame-ancestors 'self'` applies again. A proxy prefix on the initial iframe `src` does not
prevent this, and a proxy does not by itself resolve CSP, absolute redirects, session-cookie
`SameSite` behavior, or iframe restrictions. A proxy-only iframe was **not** validated; no proxy
iframe test is retained. Do not generate or document "proxy ⇒ iframe OK".

Observed prerequisites for iframe task launch in an external portal (single-deployment
observation; confirm on the target environment):

1. **Add the portal origin to `frame-ancestors`** via `Security.ContentSecurityPolicyHeaderValue`
   in wsadmin (`AdminTask.setBPMProperty` + `AdminConfig.save()` + server restart).
2. **Serve the portal over HTTPS, same site as Business Automation Workflow**, so Business Automation Workflow's `SameSite=Strict` session cookie
   flows into the iframe (Business Automation Workflow cookies were `Secure; SameSite=Strict`; they did not flow from an
   `http://` portal into an `https://` iframe).

Both conditions must be met simultaneously for an external portal iframe to work:
- Portal origin must be in Business Automation Workflow's `frame-ancestors`
- Portal must be HTTPS (same scheme as Business Automation Workflow) so `SameSite=Strict` cookies are sent in the iframe

When the prerequisites are not confirmed, do not embed the task form: use `window.open` / a new
browser tab to the Business Automation Workflow task URL instead.

### Same-origin (hosted on Business Automation Workflow)

The portal HTML is served directly from the Business Automation Workflow server. The browser session cookie is valid
for both the portal origin and the Business Automation Workflow API origin — no CORS configuration required.

**Authentication:** `credentials: 'same-origin'` with existing Business Automation Workflow session. No token management.
**CORS:** Not required.
**CSP:** Business Automation Workflow server enforces `Content-Security-Policy`. Test CSP header with Business Automation Workflow administrator
before deploying inline implementations.


### External portal — direct access

The portal communicates directly with the Business Automation Workflow server from the browser.

**Authentication:** OAuth/OIDC bearer token or Basic Auth depending on Business Automation Workflow configuration.
Must configure the external origin as an allowed CORS origin in Business Automation Workflow.
**CORS:** Business Automation Workflow returns full CORS headers when an `Origin` header is present on both preflight (OPTIONS) and actual requests. Confirmed headers: `Access-Control-Allow-Origin: <requesting-origin>`, `Access-Control-Allow-Credentials: true`, `Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS`. Business Automation Workflow echoes the requesting origin back — it does not use `*`. This means `credentials: 'include'` works for cross-origin fetch calls when the portal origin is in Business Automation Workflow's allowed origins list.
**Note:** If the portal origin is not in Business Automation Workflow's CORS allowlist, all XHR/fetch calls will fail with CORS errors in the browser. The proxy/gateway model avoids this requirement entirely.

---

## Authentication prerequisites

Before generating external portal code, confirm:

1. **Authentication mechanism** — session cookie forwarding, OAuth bearer token, or other?
2. **CORS configuration** — is the portal origin allowed in Business Automation Workflow's CORS settings?
3. **Token management** — how does the portal obtain and refresh access tokens?
4. **CSRF/XSRF handling** — follow the single contract in [`non-federated-api-guide.md` §XSRF / CSRF for WLE REST mutations](non-federated-api-guide.md#xsrf--csrf-for-wle-rest-mutations). Confirm the deployment's auth mode (session cookie or Bearer) and whether it enforces the documented `BPMCSRFToken` header or the legacy `XSRF-TOKEN` cookie check for mutations. If unconfirmed, report verification-required; do not guess.
5. **Task iframe prerequisites (external portal)** — two conditions must both be met:
   - The portal origin must be added to Business Automation Workflow's `frame-ancestors` via `Security.ContentSecurityPolicyHeaderValue` (wsadmin `AdminTask.setBPMProperty` → `AdminConfig.save()` → server restart).
   - The portal must be served over **HTTPS**. Business Automation Workflow's `LtpaToken2` cookie is `Secure; SameSite=Strict`. A portal served over `http://` will not receive the Business Automation Workflow session cookie inside the iframe, causing a login prompt. Both the portal and Business Automation Workflow must use HTTPS.

For same-origin portals hosted on Business Automation Workflow, none of CORS, token management, or cross-origin considerations apply.

### Cookie-based proxy authentication — verified

Business Automation Workflow issues three cookies on authentication: `LtpaToken2` (SSO token), `JSESSIONID` (session), and `XSRF-TOKEN`. A proxy that forwards all three cookies from the authenticated user to Business Automation Workflow will authenticate correctly without re-issuing credentials. If the deployment requires the `BPMCSRFToken` header for mutations, the proxy must pass that header through as well.

### Bearer token authentication — verified

On Cloud Pak for Business Automation deployments, Business Automation Workflow REST accepts `Authorization: Bearer <token>` directly. The token is obtained from the Cloud Pak for Business Automation IAM endpoint (`POST /icp4d-api/v1/authorize`). No session cookie is required.

**Cross-origin caveat:** A browser-based external portal sending a Bearer token with an `Origin` header will receive HTTP 403 unless the portal's origin is in the Business Automation Workflow CORS allowlist. The Business Automation Workflow administrator must configure the allowed origin. Without that configuration, the proxy model is the only option for external portals.

**OIDC client credentials:** `POST /icp4d-api/v1/authorize` is the token source documented for and observed on the applicable Cloud Pak for Business Automation deployment. IBM Cloud Pak foundational services documents a separate `client_credentials` token call at `/idprovider/v1/auth/token` ([OIDC Registration APIs](https://www.ibm.com/docs/en/cloud-paks/foundational-services/4.x?topic=apis-oidc-registration)). The grant types supported by `/oidc/endpoint/OP/token` on a given deployment were not verified against IBM documentation; confirm with the Business Automation Workflow administrator. Any OIDC flow needs a registered client ID and secret — deployment-specific values the administrator must provide. Do not generate OIDC token-acquisition code without these values.

---

## Pre-write file safety check

Initial generation only.

- Before writing a new portal for the **first time in a conversation**, use `glob` or `list_files` to check whether the target path already exists.
- If it **already exists and was not generated in this conversation**, choose a new filename by appending `-v2`, `-v3`, etc. — never silently overwrite prior work from another session.
- If the active file shown in `environment_details` matches the intended output path before any generation has occurred, treat that as prior work — read it with `read_file` to confirm.
- The user's prior work in `output/` is irreplaceable (gitignored, no recovery path).
- **Do NOT create a new versioned file for every bug fix or follow-up edit.** Once a file is established as the working output for a conversation, all fixes go into that same file using `apply_diff` or `search_and_replace`. A new version number is only warranted when the user explicitly requests a snapshot or a complete restart.
- State the chosen filename to the user before the first write only.

## Task iframe prerequisites — CSP change by platform

Adds the portal origin to the Business Automation Workflow CSP `frame-ancestors` directive (required for external C-proxy / C-direct iframe launch):

- **Traditional WAS deployment:** Set `Security.ContentSecurityPolicyHeaderValue` via wsadmin — `AdminTask.setBPMProperty(['-name', 'Security.ContentSecurityPolicyHeaderValue', '-value', "... frame-ancestors 'self' https://{portal-origin} ..."])` → `AdminConfig.save()` → server restart.
- **Cloud Pak for Business Automation on containers (OpenShift):** Edit the `ICP4ACluster` custom resource. Set `spec.baw_configuration[*].environment_config.content_security_policy_additional_frame_ancestor` to include `["https://{portal-origin}"]`. The operator applies the change without a manual server restart.

---

## Optional: remote development

Use this section only when the Vite dev server must be reached from another machine (for example a shared development VM). Local development on `localhost` needs none of it. This is a development convenience, never a deployment profile: production hosting follows the profiles above.

Policy:

- **Specific hostnames only.** `server.allowedHosts` is an explicit list of the exact hostnames developers use. Do not set `allowedHosts: true`: it disables the host check and exposes the dev server to DNS-rebinding requests ([GHSA-vg6x-rcgg-rjx6](https://github.com/vitejs/vite/security/advisories/GHSA-vg6x-rcgg-rjx6)). Do not use a leading-dot wildcard, `*`, or a bare top-level domain.
- **The allowlist is not the access control under HTTPS.** Vite skips its host check whenever `server.https` is set (stated in the [`server.allowedHosts` documentation](https://vite.dev/config/server-options); also observed on Vite 6.4.5, where a request with an unlisted `Host` header was answered). With the HTTPS setup below, `allowedHosts` therefore does not reject other hostnames: keep the list accurate as a statement of intent, and treat the single bind address, a trusted network or VPN, and the certificate you supply as the controls. Do not rely on `allowedHosts` for protection here.
- **HTTPS with certificate validation.** Serve the dev server over HTTPS with a key and certificate you supply (`server.https`); the snippet refuses to start without them. The Business Automation Workflow proxy target must be an `https://` origin and TLS verification toward Business Automation Workflow stays at its default. Do not set `secure: false`, `rejectUnauthorized: false` or `NODE_TLS_REJECT_UNAUTHORIZED=0`. If Business Automation Workflow uses a private CA, add that CA to the Node trust store with `NODE_EXTRA_CA_CERTS=/path/to/ca.pem` instead of turning validation off.
- **Self-signed certificates are for local development only.** A self-signed or auto-generated certificate (for example from `@vitejs/plugin-basic-ssl`) gives encryption without identity assurance; it is not for production and is not evidence that the setup is secure. Vite itself recommends supplying your own certificate.
- **Bind deliberately.** Bind to one named interface address rather than all interfaces, and leave `server.cors` at its default. Keep the dev server on a trusted network or behind a VPN.
- **Iframe and CORS prerequisites are unchanged.** A remote dev origin that embeds the Business Automation Workflow task form needs the same `frame-ancestors` and HTTPS conditions as any external portal: see Task iframe prerequisites above. Do not restate or relax them here.

Source: Vite [`server.allowedHosts`, `server.https` and `server.host`](https://vite.dev/config/server-options). The snippet follows that documentation; it has not been run against a live remote environment, and the Vite version in use should be at or above the release that fixes the advisory.

<!-- snippet: vite-remote-dev -->
```js
import { defineConfig } from 'vite';
import { readFileSync } from 'node:fs';

const env = process.env;
const hostRe = /^(?:localhost|[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+)$/i;
const allowedHosts = (env.PORTAL_DEV_HOSTS || '').split(',').map(h => h.trim());
if (allowedHosts.length === 0 || !allowedHosts.every(h => hostRe.test(h))) {
  throw new Error('PORTAL_DEV_HOSTS must list specific hostnames, e.g. portal-dev.example.com');
}
if (!env.PORTAL_DEV_TLS_KEY || !env.PORTAL_DEV_TLS_CERT) {
  throw new Error('PORTAL_DEV_TLS_KEY and PORTAL_DEV_TLS_CERT are required: HTTPS only');
}
if (!/^https:\/\/[a-z0-9.-]+(?::\d{1,5})?$/i.test(env.BAW_BASE_URL || '')) {
  throw new Error('BAW_BASE_URL must be a bare https://host[:port] origin');
}
const bind = env.PORTAL_DEV_BIND || 'localhost';
if (['0.0.0.0', '::', 'true'].includes(bind)) throw new Error('PORTAL_DEV_BIND must be one specific address');

export default defineConfig({
  server: {
    host: bind,
    allowedHosts,
    https: { key: readFileSync(env.PORTAL_DEV_TLS_KEY), cert: readFileSync(env.PORTAL_DEV_TLS_CERT) },
    proxy: { '/rest/bpm': { target: env.BAW_BASE_URL, changeOrigin: true } },
  },
});
```

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
- Business Automation Workflow is hosting the portal directly (same-origin)
- A quick demo or proof-of-concept is needed
- The deployment environment restricts external asset loading

For standalone HTML, all CSS and JS must be inline. Do not reference external CDN assets
unless the deployment is confirmed to allow the required origins in its CSP.


---

## Existing application adaptation

When adapting an existing application:

1. **Read the existing stack first** before suggesting any API integration pattern.
2. **Use the existing HTTP client** — do not introduce `fetch` if `axios` is already present.
3. **Create a service module** (e.g., `bawApiService.js`) that wraps Business Automation Workflow API calls.
4. **Map Business Automation Workflow auth to the existing auth pattern** — do not redesign the application's authentication.
5. **Do not refactor unrelated code** — only touch files necessary for the integration.
6. **Match the existing folder and module structure** — place Business Automation Workflow service files where sibling services live.

---

## Branding defaults

Branding is a **configurable design choice**. When the developer has not specified a company name, logo or colours, default to IBM text-only branding:

- Header text: `IBM` (in `--ibm-blue-50`) followed by `BAW Process Portal` (in white)
- No logo SVG or icon — IBM branding is text-only, matching the Carbon UI Shell pattern
- Do not generate placeholder SVG badges, initials boxes, or any graphic that could be mistaken for another company's logo
- If the developer specifies a company name, colours or a design system, use those; still no invented SVG icon

---

## Mandatory requirements

These requirements hold for every generated or adapted portal, whatever the layout, framework or navigation model. They exist for API correctness, security, authorization or quality. Verify each against the API guides; do not rely on how any example implements them.

### What "full-featured" means

"Full-featured" does not mean reproducing the reference example's feature checklist, navigation or layout. Choose the feature set from the user persona and the functionality the customer asked for (see `personas-and-capabilities.md`), then implement each chosen feature to the acceptance criteria below. Name any requested feature that cannot be implemented because of a known gap and provide an explicit placeholder.

### Feature-level acceptance criteria (layout-independent)

Acceptance is judged on behaviour. A feature passes whether its UI is a dropdown, a dedicated screen, a panel or a modal.

| Feature | Acceptance criteria (all UI variants) |
|---|---|
| Task list & search | Personal inbox uses standard GET: `GET /rest/bpm/wle/v1/tasks?interaction=claimed_and_available&size=500&offset=0` (or `filterByCurrentUser=true`). Multi-criteria, filtered, or ad hoc task queries use the verified search request shape: `PUT /rest/bpm/wle/v1/tasks` with `size`, `offset`, and `filterByCurrentUser` as **URL query parameters**, a `SavedSearchDefinition` body, and never `offset` or `calcStats` in the body. Shows result count and a truncation indicator when `totalCount` exceeds the returned items. |
| Task lifecycle | Claim, release (`action=cancel`, releases the claim, does not terminate the task) and reassign use the verified operations from `playbooks/task-lifecycle.md`. Actions are offered only for states where they are valid. Task completion happens in the Business Automation Workflow task UI, not in a rebuilt form. |
| Saved searches | List (`data.definitions[]`; an unrecognised envelope is an error, never an empty list), run (definition → search request; replace the stored `fields` with the explicit field list from the guide; never forward it or send `fields: []`), create, rename (send a complete definition) and delete. Address a saved search by its numeric `id`. Reload the list after every mutation. |
| Process launcher | Lists `GET /rest/bpm/wle/v1/exposed`, passes every item through `normaliseExposedProcess` (items it rejects are not offered), filters by name, and starts with the `bpdId`/`processAppId` it returns (`non-federated-api-guide.md`). After a start, dismiss the launcher before opening any task view, then follow "Process start follow-up" in `task-lifecycle.md` (show IDs, refresh, highlight). |
| Task open | Opens the Business Automation Workflow task UI in the way the selected hosting profile allows (iframe prerequisites for external C-proxy / C-direct; navigation or new tab otherwise). Return focus to the invoking control when a modal or panel closes. |
| Identity | Current user and profile from `GET /rest/bpm/wle/v1/user/current?parts=all` when the UI shows user details. |
| Mutations | Follow the single CSRF/XSRF contract in `non-federated-api-guide.md` (or the PFS section of `federated-api-guide.md`). No fabricated tokens; report deployment-dependent behaviour as verification-required. |
| Pagination | See [Pagination](#pagination). |

### Quality requirements (every UI)

Accessibility and interaction:

- Explicit loading, empty, error and permission-denied states for every data view. Never convert a failed or unrecognised response into an empty state.
- `role="status"` on loading, `role="alert"` on errors, `aria-live="polite"` on result counts and refresh status, `aria-live="assertive"` on toasts.
- Skip link to main content; visible focus indicator on every interactive element; keyboard-operable controls with a minimum 44×44 px touch target; every form control has an explicit label; focus trap, Escape handling and return focus on every dialog, modal or panel.
- `aria-sort` on sortable table headers; `aria-pressed` or `aria-selected` on toggle-style filters. Priority and status badges carry text, not colour alone.
- Responsive layout that remains usable at narrow widths (a table may become cards; a navigation may collapse).
- `prefers-reduced-motion` suppresses animation.
- Loading, error and pagination controls that are inactive are removed from layout and focus order (`display: none` or the framework equivalent), not only made transparent.

Security and data handling:

- Server data is rendered as text (escape or use text nodes), never through unescaped `innerHTML`; URLs derived from server data are validated before navigation or framing; no `eval()` or `document.write()`.
- Task IDs are opaque: guard with a truthiness check and `encodeURIComponent`, never numeric validation (see [`non-federated-api-guide.md`](non-federated-api-guide.md#task-launch)). The task iframe URL is a fixed `/teamworks/process.lsw` path, has a descriptive `title`, and its `src` is reset to `about:blank` on close. Leave a `TODO` comment that the iframe `sandbox` attribute is pending deployment validation; test it with Business Automation Workflow task forms before enabling it.
- Same-origin calls use `credentials: 'same-origin'`. Keep task, task-ID and process data in memory only (no `localStorage`) and do not log full API payloads to the console.
- Mutations follow the single CSRF/XSRF contract in [`non-federated-api-guide.md`](non-federated-api-guide.md#xsrf--csrf-for-wle-rest-mutations): the token comes only from the documented login call and is never fabricated or logged; no attempt to disable or bypass checks; an unconfirmed requirement is reported as verification-required.

Data freshness (when the UI refreshes automatically):

- One in-flight guard so overlapping loads cannot race; clear it in a `finally` block. Debounce search input; clear-all applies filters immediately.
- Pause polling while the page is hidden and refresh silently when it becomes visible; a silent failure marks the data as stale and notifies the user rather than blanking the list. Refresh after a task dialog closes.

Respect the developer's chosen framework, build tooling and existing application conventions.

### Before delivery

Static review is necessary but not sufficient. The developer should confirm against a live Business Automation Workflow instance for the target deployment: the task list returns data and task launch opens, keyboard-only navigation and a screen-reader announcement pass, content reflows at 200% and 400% zoom, `totalCount` versus returned count is surfaced when paging applies, and the CSP and iframe `sandbox` behaviour were agreed with the Business Automation Workflow administrator. Do not claim live runtime validation unless an authenticated Business Automation Workflow environment was used in the current session.

---

## Configurable design choices

The items below are decisions for the consuming agent and the customer, not skill requirements. Honour the customer's stated preference. When none is stated, choose a reasonable design from the persona and requested functionality. Do not impose a layout unless the customer asks for it or a verified deployment constraint requires it.

| Choice | Options (any accessible pattern is acceptable) |
|---|---|
| Application shape | Single-page or multi-page |
| Primary navigation | Sidebar, top navigation, tabs, or none for a single-purpose screen |
| Saved searches | Dropdown or combobox, dedicated page, side panel, or another accessible pattern. Any pattern must support the full saved-search acceptance criteria above. Use a filterable control when many saved searches are expected |
| Process launcher | Dedicated page, modal or side panel |
| Summary statistics | Any subset of overdue, at-risk, active and total counts, or none. Counts come from `calcStats` or the returned items; never invent statistics the API does not provide |
| Toolbar | Placement, ordering and which filters appear (search text, priority, status, process) |
| Dashboard layout | Table, cards, board, or a hybrid |
| Dimensions | Header and navigation sizes, spacing, density |
| Branding and visual style | IBM text-only default (above), customer branding, Carbon tokens or components, or another design system |
| Task-open presentation | Modal iframe, side panel, new tab or same-window navigation, within what the hosting profile permits |

### Persona-based starting points

These are suggestions for a generic request, to be overridden by the customer:

- **Task worker:** a compact experience centred on the user's task list, with saved searches and process start as reachable features. One screen is often sufficient.
- **Team lead or manager:** the task worker features plus a team workload view and reassignment.
- **Administrator:** see `personas-and-capabilities.md` §Administrator.

---

## Greenfield application generation

When generating a new portal from scratch:

1. Use the developer-specified stack (or React if none specified).
2. Structure the project following the selected framework's conventions.
3. Create a Business Automation Workflow API service layer separate from UI components.
4. Apply Carbon design tokens as CSS custom properties only when Carbon styling is wanted — do not import Carbon component libraries unless the developer has requested full Carbon component usage.
5. Apply the branding choice (see Branding defaults).
6. The existing Business Automation Workflow task UI is opened in an iframe, panel or tab — do not attempt to rebuild task completion.
7. Verify every chosen feature against the acceptance criteria above before submitting generated code. Name any intentionally omitted requested feature and give a reason.

### Stable interfaces before parallel work

Whatever the framework or orchestration model, when more than one author, module or agent works on the portal, fix the cross-boundary interfaces first and write all modules against them. Do not infer names or signatures from code written in a different turn.

A contract should cover: the navigation/view identifiers used by the router and navigation controls, the signature for opening a task (pass the full task object, not a bare ID), the toast/notification signature, and the reassign trigger.

Illustrative contract (React-style naming; adapt to Vue events, Angular outputs, or plain-JS modules as appropriate):

```
onOpenTask(task: object)         // receives the full task object
onShowToast(msg: string, type: 'info'|'success'|'error')
onReassign(task: object)
onNavigate(viewId: string)       // viewId is one of the identifiers the app defines
```

Keep notification helpers' argument order consistent; adapt at the call site if two helpers differ.

### Layout notes — only if a fixed header or fixed sidebar is chosen

A fixed header or sidebar must not hide content. Reserve space for each fixed element (padding for a fixed header, a margin for a fixed sidebar that is removed on narrow screens) and let flex children shrink with `min-width: 0` so wide content does not overflow. The dimensions are a design choice.

```css
/* Illustrative only — values are design choices */
.app-shell { padding-top: var(--header-h); }
.app-body  { margin-left: var(--nav-w); }   /* 0 on narrow screens */
.view      { flex: 1; min-width: 0; overflow-y: auto; width: 100%; }
```

---

## Requests for an example portal

No example portal ships with this skill, so generated output follows the API guides rather than a fixed layout. When a developer asks to see one, say so and offer to generate one from the API guides and capability catalog.

---

## Open deployment decisions

Each item below is unresolved. Do not generate code that depends on it until the stated action is done.

| Topic | What is unresolved | Required action |
|---|---|---|
| API gateway token exchange | The mechanism is deployment-specific and was never tested; there is no standard endpoint to probe. | State that it must be confirmed with the Business Automation Workflow administrator. Do not generate gateway token-exchange code without knowing the gateway configuration. |
| External runtime-validation boundary (external proxy / direct) | Which external authentication, proxy and hosting configurations must be demonstrated as working, versus delivered as generated code with documented prerequisites. | The product owner defines the boundary before external-portal acceptance criteria are final. |
| Supported Business Automation Workflow version matrix | Which Business Automation Workflow versions and configurations must be supported; WLE v2 availability is version-dependent. | The product owner confirms the matrix. Until then, gate WLE v2 code on the FDR probe result. |

---

## Carbon design system

Carbon is the default design system where appropriate.

**Supported approaches:**

| Approach | When to use |
|---|---|
| Carbon design tokens as CSS custom properties | Default — no build tooling required |
| Official `@carbon/react` components | When developer requests Carbon component library |
| Customer branding over Carbon tokens | Developer-supplied color tokens replace Carbon defaults |

Always define brand and Carbon colours in `:root` CSS custom properties so they can be
overridden per deployment without modifying generated component code.

---

## Pagination

All generated portals must handle pagination correctly.

- `size=500` requests up to 500 tasks, not all tasks
- When `totalCount` in the response exceeds the number of returned items, additional pages exist
- Page with `offset` incremented by `size`
- Show a truncation indicator when the displayed list does not include all available tasks
- The paging contract (`totalCount`, `offset`, `size`) is documented by IBM

Do not silently discard tasks beyond `size=500` without informing the user.
