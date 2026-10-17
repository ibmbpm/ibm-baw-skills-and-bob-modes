# BAW External Task UI Builder — Documentation

> Generate a custom external task UI for an IBM Business Automation Workflow (BAW) human task configured with a Custom URL — a Node.js Express server with a React or user-specified frontend that fetches task data from BAW, renders a Carbon-styled form, and completes the task on submission.

## Purpose

When a BAW human task is configured with a **Custom URL**, IBM Workplace opens an external application instead of a BAW coach when a user claims that task. This skill generates that external application. It creates a Node.js Express server paired with a React (default) or user-specified frontend, wired to BAW's `/bpm/user-tasks` REST API for fetching task data and submitting results.

The skill supports two ways to describe the task's fields: supply a task schema file (an OpenAPI spec exported from your BAW service flow), or describe the fields verbally. If you do not have the schema file yet, the skill provides step-by-step instructions for exporting it from BAW.

Use this skill when you need to build a standalone external UI for a single BAW human task. For task list portals that display and manage multiple tasks, use the `create-baw-portal` skill instead. For BAW Coach View widgets, use `create-baw-widget`.

---

## Setup and configuration

- **Node.js** installed on the target BAW VM or server where the generated application will run (v16 or later recommended)
- **IBM BAW server** accessible from the host where the Node.js app runs — HTTP Basic Authentication credentials (username and password) required
- **BAW server base URL** — e.g. `https://my-baw-server:9443`
- **SSL certificate handling** — if your BAW server uses a self-signed certificate, set `IGNORE_SSL_CERTIFICATES=true` in the generated `.env` file
- For React projects: **Node.js** with npm available locally for the build step (`npm run build`) before copying files to the VM
- No API keys or MCP servers required — the skill generates files only

---

## Compatibility

- IBM BAW 22.x and later; IBM CP4BA 22.x and later
- Uses the BAW `/bpm/` REST API surface (BPM Standard API) — not the WLE REST API (`/rest/bpm/wle/`) used by BAW portals
- Self-signed SSL certificates are supported via an `IGNORE_SSL_CERTIFICATES` environment flag
- Generated React apps use Vite; Node.js 16+ required on the build machine

---

## Prompt examples

### Generate an external task UI from a verbal field description

**Prompt:**
> Create an external task UI for a BAW Manager Approval task. The task receives a customer name (read-only string) and credit score (read-only number). The manager must submit an approved decision (boolean: Approve or Reject) and a justification note (string).

**What to expect:** A `.env`, `package.json`, `server.js`, and a named React component (`ManagerApproval.jsx`) with Carbon Design System styling, a confirmation dialog before submission, and the correct BAW API integration for fetching and completing the task.

---

### Generate an external task UI from a task schema file

**Prompt:**
> Build an external task UI for my BAW Send Email task. Here is my task schema file:
>
> ```json
> {
>   "openapi": "3.0.1",
>   "components": {
>     "schemas": {
>       "ioSpec_input": {
>         "type": "object",
>         "properties": {
>           "fromEmail": { "type": "string" },
>           "@metadata": { "type": "object" }
>         }
>       },
>       "ioSpec_output": {
>         "type": "object",
>         "properties": {
>           "toEmail":       { "type": "string" },
>           "emailSubject":  { "type": "string" },
>           "emailTemplate": { "type": "string" },
>           "sendAction":    { "type": "string" }
>         },
>         "required": ["toEmail", "emailSubject"]
>       }
>     }
>   }
> }
> ```
>
> BAW server is at https://baw-prod.example.com:9443. Use self-signed SSL.

**What to expect:** The skill derives all form fields from the schema (`fromEmail` as read-only, output fields as editable Carbon inputs with `toEmail` and `emailSubject` marked required), generates a `server.js` with a `/api/schema` endpoint that resolves `$ref` references, and produces a `SendEmail.jsx` React component — no need to describe any field manually.

---

### Get instructions to export the task schema file

**Prompt:**
> I want to use my BAW service flow schema to generate the external UI, but I don't have the task schema file yet. How do I export it from BAW?

**What to expect:** Step-by-step instructions covering how to create a service flow with an `ioSpec` operation, expose it as a REST endpoint, navigate to the BAW REST API Explorer, and download the OpenAPI spec — plus a `curl` command for self-signed certificate environments.

---

### Generate with a custom brand color

**Prompt:**
> Create an external task UI for a Loan Approval task. Fields: applicantName (read-only string), loanAmount (read-only number). Outputs: approved (boolean), reviewerComment (string). Our company primary color is #003366.

**What to expect:** IBM Carbon Design System structure with `#003366` applied as a CSS custom property override for the primary color token — the Carbon layout, spacing, and typography remain intact.

---

### Generate with plain HTML instead of React

**Prompt:**
> Build an external task UI for a Vacation Request approval task. Fields: employeeName (read-only), vacationDates (read-only), requestReason (read-only). Outputs: approved (boolean), managerNote (string). Use plain HTML, not React. BAW server: https://baw-dev.internal:9443, credentials admin/admin, self-signed SSL.

**What to expect:** Three files — `.env`, `package.json`, `server.js` — plus a single named HTML file (`vacation-approval.html`) with all client JavaScript embedded in `<script>` tags and Carbon loaded from CDN; no Vite, no React components.

---

### Add a Vue frontend

**Prompt:**
> Generate a BAW external task UI for an Invoice Approval task using Vue 3. Input fields: invoiceNumber (string, read-only), supplierName (string, read-only), amount (number, read-only). Output fields: approved (boolean), rejectionReason (string). BAW is at https://baw.company.com:9443.

**What to expect:** A Vue 3 Composition API component for the approval form alongside the standard `server.js` and configuration files, using Carbon tokens for styling.

---

## How the generated application works

### File structure (React default)

```
.env                    # BAW server URL, credentials, SSL flag, port
package.json            # Express + axios server deps; React + Vite dev deps
server.js               # Express API proxy to BAW
<TaskName>.jsx          # React form component (named after the task)
```

### Runtime flow

1. User claims the task in IBM Workplace — the Custom URL opens your Node.js app with `?taskId=<id>`
2. The React component calls `GET /api/user-task/:taskId` on `server.js`
3. `server.js` acquires a CSRF token from BAW (`POST /bpm/system/login`), then fetches the task (`GET /bpm/user-tasks/:taskId?optional_parts=data`)
4. BAW returns input data as `[{name, data}]` arrays; the server flattens these and strips `@metadata` fields before returning them to the client
5. The user fills in the output fields and clicks Submit
6. A confirmation dialog appears; on confirm, `server.js` posts to `POST /bpm/user-tasks/:taskId/complete`
7. After completion, the popup closes or the page redirects to IBM Workplace (`/Workplace`)

### Running the application

After copying files to your BAW VM:

```bash
# 1. Edit .env with your BAW server details
# 2. Install dependencies
npm install

# 3. For React: build the frontend
npm run build

# 4. Start the server
npm start
```

Access via: `http://localhost:3000/?taskId=YOUR_TASK_ID`

> The Node.js server must run on a host the user's browser can reach when Workplace opens the Custom URL. Copy all generated files to that host — do not run the server locally on the machine where Bob generated the code.

---

## What this skill does not do

| Request | Use instead |
|---|---|
| Build a task list portal that lists and opens multiple BAW tasks | `create-baw-portal` |
| Create BAW Coach View widgets | `create-baw-widget` |
| Generate BAW process diagrams or BPMN | `generate-baw-bpmn` |
| Deploy or copy files to the BAW VM | Manual step — the skill generates files only |
