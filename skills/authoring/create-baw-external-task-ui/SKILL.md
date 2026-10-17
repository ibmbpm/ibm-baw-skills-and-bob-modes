---
name: create-baw-external-task-ui
description: >
  Generate a custom external task UI for an IBM Business Automation Workflow (BAW)
  human task configured with a Custom URL. Creates a Node.js Express server and a
  React (default) or user-specified stack UI that fetches task data from BAW,
  renders a Carbon-styled form, and completes the task on submission. Two intake
  paths: provide a task schema file (OpenAPI exported from your BAW service flow) or
  describe task fields verbally (generating a unified fields-spec.json). Includes
  instructions for exporting the schema from BAW and setting the External Implementation
  URL with {tw.system.task_id}. Use when building an external Node.js app for a BAW
  Custom URL task or integrating with the BAW /bpm/user-tasks REST endpoints. Do NOT
  use for task list portals (use create-baw-portal) or BAW Coach View widgets (use
  create-baw-widget). Trigger phrases: "external task UI", "custom URL task",
  "BAW external UI", "node.js BAW task", "external implementation", "Custom URL implementation".
license: Apache-2.0
compatibility: "IBM BAW 22.x and later; IBM CP4BA 22.x and later"
allowed-tools:
  - Read
  - Edit
  - Bash
metadata:
  version: "1.0.0"
  display_name: BAW External Task UI Builder
  short_description: Generate a React + Express external task UI for IBM BAW Custom URL human tasks — with Carbon styling and full BAW REST API integration.
  author: IBM BAW Team
  example_prompts:
    - "Create an external task UI for a Manager Approval task in BAW"
    - "Build a Node.js app to complete a BAW user task via Custom URL"
    - "Generate an external UI for my BAW task — here is my task schema file"
    - "Create a React form for a BAW human task with fields: firstName, lastName, approved"
    - "How do I export the OpenAPI spec from my BAW service flow?"
---

## What this skill builds

A BAW human task configured with a **Custom URL** opens an external application when
a user claims it in IBM Workplace. This skill generates that external application: a
Node.js Express server paired with a React (default) or user-specified frontend that
fetches the task's input data from BAW, renders a form for the user to complete, and
submits the output back to BAW to complete the task.

The generated application integrates with the BAW `/bpm/` REST API surface
(base path `/bpm`, documented in `references/baw-rest.md` and `references/server-pattern.md`).
This is the BPM Standard API — distinct from the WLE REST API (`/rest/bpm/wle/`) used by
BAW portals for task lists.

---

## Credentials (Skill REST Calls)

When a REST call is about to be made by the skill during this session, read `references/CREDENTIAL_HANDLING.md` and follow it — it will read credentials from `.env` automatically, and only prompt the user if a value is missing from that file. Do this once per session only.

---

## Step 1 — Identify the intake path

Ask the user which intake path applies. Both are supported:

> **"Do you have a task schema file exported from your BAW service flow?
> (This is an OpenAPI JSON file you can download from the BAW REST API Explorer.)
> If yes, share it and I will derive the form fields from it.
> If not, describe your task's input fields (data shown to the user, read-only)
> and output fields (data the user fills in and submits back to BAW)."**

- **Path A — task schema file provided:**
  - Parse `components/schemas/ioSpec_input` for read-only display fields and `components/schemas/ioSpec_output` for editable output fields.
  - Filter out any field whose name starts with `@` (metadata).
  - Save as `ExtRest.json` (or the provided schema filename) and set `SCHEMA_FILE=ExtRest.json` in `.env.example`.
- **Path B — verbal description (no OpenAPI contract):**
  - Collect field names, types, allowed values (`enum`), and read-only vs editable designation from the user.
  - Write a confirmed `fields-spec.json` mimicking the OpenAPI contract schema:
    ```json
    {
      "x-source": "user-described fields",
      "components": {
        "schemas": {
          "ioSpec_input": { "type": "object", "properties": { "fieldName": { "type": "string" } } },
          "ioSpec_output": { "type": "object", "properties": { "decision": { "type": "string", "enum": ["Approve", "Reject"] } }, "required": ["decision"] }
        }
      }
    }
    ```
  - Set `SCHEMA_FILE=fields-spec.json` in `.env.example` so the server and client logic are identical for both paths.

If the user does not have the task schema file and asks how to get one, read
[`references/export-extrest.md`](references/export-extrest.md) and provide
those instructions before continuing.

---

## Step 2 — Gather environment details

Ask only what is needed; combine into a single prompt where possible:

1. **BAW server base URL** — e.g. `https://my-baw-server:9443` — read from `.env` via `references/CREDENTIAL_HANDLING.md`; ask only if missing (stored as `BAW_SERVER_BASE_URL` or `BAW_BASE_URL`)
2. **SSL certificates** — does the BAW server use a self-signed certificate? (`IGNORE_SSL_CERTIFICATES=true`)
3. **Port** — port for the Node.js server (default: `3000`)

Ask once. Use HTTP Basic Auth — no other mechanism is supported for this pattern.

*(Note: The generated application reads its own credentials `BAW_USERNAME` and `BAW_PASSWORD` from `.env` at runtime. Do not prompt for or hardcode credentials in code).*

---

## Step 3 — Gather styling and branding preferences

Default to IBM Carbon Design System. Ask:

> **"Do you have any styling preferences — a brand color, a company name,
> a design reference, or an image of the kind of UI you are aiming for?
> If not, I will use IBM Carbon defaults."**

Apply any supplied overrides (primary color, font, logo text) as CSS custom
property overrides on top of Carbon tokens. Do not invent branding if none is provided — use Carbon defaults.

---

## Step 4 — Gather stack preference

Default to React (Vite). Ask only if the task is complex enough that the stack matters, or if the user has indicated a preference:

> **"Should I use React (default), or do you prefer plain HTML/Node.js, Vue, or Angular?"**

| Stack | Notes |
|---|---|
| React (Vite) | Default — component-based, Carbon React components available |
| Plain HTML | Single HTML file with embedded JS; Carbon loaded from CDN |
| Vue | Follow Vue 3 Composition API patterns |
| Angular | Follow Angular service/component patterns |

---

## Step 5 — Generate the implementation

Generate the minimal set of files according to the reference patterns in `references/server-pattern.md`.

### Always generated (all stacks)

**`.env.example`** — placeholders only. Do not write a `.env` file: it could overwrite one the user has already filled in, and it must never hold real values.
```
BAW_SERVER_BASE_URL=https://your-baw-server:9443
BAW_USERNAME=your_username
BAW_PASSWORD=your_password
IGNORE_SSL_CERTIFICATES=true
PORT=3000
SCHEMA_FILE=ExtRest.json
```
*(Use `SCHEMA_FILE=fields-spec.json` if using Path B).*

**`.gitignore`** — must list `.env` and `node_modules/` (plus `dist/` for React) so credentials are never committed.

**`package.json`** — dependencies: `express`, `axios`, `cors`, `dotenv`, `body-parser`. For React: add `react`, `react-dom`, `@vitejs/plugin-react`, `vite` as dev dependencies. Include `start` and (for React) `build` scripts.

**`server.js`** — Express server following `references/server-pattern.md`. Must include:
- `GET /api/config` — exposes `BAW_SERVER_BASE_URL` to the client so the client can construct redirect URLs without hardcoded hostnames.
- `GET /api/schema` — reads `SCHEMA_FILE`, resolves all `$ref` references inline, and returns clean field definitions.
- `GET /api/user-task/:taskId` — fetches task data from BAW (`/bpm/user-tasks/{id}?optional_parts=data`).
- `POST /api/user-task/:taskId/complete` — completes the task via BAW REST API.
- Fresh CSRF token acquisition via `/bpm/system/login` and auto-retry on 403 `CWTBG0651E`.
- Bound to `127.0.0.1` (never `0.0.0.0`).

### React stack (default)

Generate a named React component file based on the task name (e.g., `ManagerApproval.jsx`, `SendEmail.jsx`). Never name the component `index` or `App` as the only meaningful name.

- Use Carbon React components (`@carbon/react`) for form fields when available
- Read-only input fields from `ioSpec_input` → rendered as Carbon `TextInput` with `readOnly`
- Editable output fields from `ioSpec_output` → rendered as appropriate Carbon input components
- Confirmation dialog (`Modal`) before submission
- Post-submission: popup close / iframe redirect pattern (see below)
- `App.jsx` or `main.jsx` wires the component and reads `taskId` from the URL query string

### Plain HTML stack

Generate a single named HTML file (e.g., `manager-approval.html`) or `public/index.html`. Embed client-side JavaScript in `<script>` tags. Load Carbon from CDN (`https://1.www.s81c.com/common/carbon/web-components/version/v1.35.0/`). Follow the same form layout, confirmation dialog, and popup close pattern.

---

## Generated Application Runtime Security & BAW API Rules

Read [`references/baw-rest.md`](references/baw-rest.md) and [`references/server-pattern.md`](references/server-pattern.md) when generating server code.

### Axios instance setup

```js
const https = require('https');
const axiosInstance = axios.create({
  baseURL: process.env.BAW_SERVER_BASE_URL.replace(/\/+$/, '') + '/bpm/',
  auth: {
    username: process.env.BAW_USERNAME,
    password: process.env.BAW_PASSWORD,
  },
  httpsAgent: new https.Agent({
    rejectUnauthorized: process.env.IGNORE_SSL_CERTIFICATES !== 'true',
  }),
});
```

### Application runtime credential handling & fail-fast check

```js
const PLACEHOLDER = /^(your_username|your_password|<.+>)$|your-baw-server/i;
const missing = ['BAW_SERVER_BASE_URL', 'BAW_USERNAME', 'BAW_PASSWORD'].filter((name) => {
  const value = (process.env[name] || '').trim();
  return !value || PLACEHOLDER.test(value);
});
if (missing.length) {
  console.error(`Missing or placeholder values in .env: ${missing.join(', ')}. See .env.example.`);
  process.exit(1);
}
```

- Attach credentials in one place only — the server `axiosInstance`. Never return credentials to the browser.
- Never log raw axios error objects containing the `Authorization` header.
- On HTTP 401 from BAW, log a server-side hint to check `.env`.

### CSRF token acquisition & retry

Call `POST /bpm/system/login` with `Content-Type: application/json` before every task operation. Include `BPMCSRFToken: <token>` in subsequent calls. On HTTP 403 with `CWTBG0651E`, refresh token and retry once.

### Data format transformation

- **Task input**: Array of `{ name: "fieldName", data: value }` from `GET /bpm/user-tasks/{taskId}?optional_parts=data`. Convert to a flat key-value object and filter out `@metadata` properties.
- **Task completion**: `POST /bpm/user-tasks/{taskId}/complete` payload must be `{ output: [ { name: "fieldName", data: value }, ... ] }`.

---

## Popup / iframe close pattern

After successful task completion, close the popup or redirect the iframe. Wrap all cross-origin window operations in try-catch to prevent `DOMException` errors:

```js
const configRes = await fetch('/api/config');
const { bawServerUrl } = await configRes.json();

if (window.opener) {
  try { window.opener.location.reload(); } catch (e) { /* cross-origin */ }
  window.close();
} else if (window.parent !== window) {
  try {
    window.parent.location.href = `${bawServerUrl}/Workplace`;
  } catch (e) {
    window.location.href = `${bawServerUrl}/Workplace`;
  }
} else {
  window.location.href = `${bawServerUrl}/Workplace`;
}
```

---

## Common Customizations

| User request | Implementation Pattern |
|---|---|
| Rich text / email body | Integrate Quill.js CDN in HTML/React; capture HTML/Delta on submit |
| Template dropdown | Parse JSON string field from input; populate `<select>` or Carbon `Dropdown`; auto-fill related fields on change |
| Enums / Fixed options | Render `enum` fields as radio button groups or dropdowns with defined options |
| Required field validation | Validate fields against schema `required` list; show inline Carbon `invalid` state before submit |
| Read-only computed fields | Display formatted as read-only Carbon `TextInput` or text block, never editable input |
| Multi-step wizard | Use Carbon `ProgressIndicator`; trigger task completion on the final step |

---

## Step 6 — Post-generation instructions & BAW wiring

After generating all files:

1. List every generated file.
2. Provide run instructions:
   - Copy `.env.example` to `.env` and fill in values
   - `npm install`
   - `npm run build` (React only)
   - `npm start`
   - Access at `http://localhost:<PORT>/?taskId=YOUR_TASK_ID`
3. Provide BAW Process Designer setup instructions:
   - Set the User Task **Implementation Type** to **External Implementation** (or Custom URL).
   - Set the **External URL** to:
     ```
     http://localhost:<PORT>/?taskId={tw.system.task_id}
     ```
     *(BAW substitutes `{tw.system.task_id}` at runtime with the active task ID).*
   - Note: External Implementation on user tasks is deprecated in BAW 26.x but remains functional; for 26.x+ standalone SPAs using the standard REST API are recommended.

---

## What this skill does not do

- Does not create BAW process diagrams, BPMN, or internal BAW XML → use `generate-baw-bpmn`
- Does not build task list portals that list and open multiple tasks → use `create-baw-portal`
- Does not create BAW Coach View widgets → use `create-baw-widget`
- Does not deploy files to the BAW VM — deployment is a manual copy step
