# BAW REST Reference — troubleshoot-baw-logs

---

## `/ops/system/login`

### POST /ops/system/login

**Obtain IBM Business Automation Workflow CSRF prevention token**

Obtain a CSRF prevention token and optionally refresh the user's group membership information.
This session is valid for `/ops/…` calls. The WLE v1 surface (`/rest/bpm/wle/v1/…`) uses HTTP Basic auth per request — it does not use this session.

**Parameters:**

- `login_request` (body) *(required)* — JSON object: `{"refresh_groups": false}`
- `Authorization` (header) *(required)* — `Basic <base64(username:password)>`
- `Content-Type` (header) — `application/json`

**Responses:**

- `201` — Success. Response body contains `csrf_token`. Set-Cookie headers contain `LtpaToken2` and `JSESSIONID`.
- `400` — Invalid input.
- `401` — Bad credentials.
- `500` — Internal server error.

Store `csrf_token` as `{BAW_CSRF}` and the cookies as `{BAW_SESSION}`. Send `BPMCSRFToken: {BAW_CSRF}` and the session cookie on every subsequent `/ops/…` call.

---

## `/rest/bpm/wle/v1/process/errors` *(WLE v1)*

### PUT /rest/bpm/wle/v1/process/errors

**Retrieve runtime error information for one or more BPD process instances**

Returns structured runtime error data — error message, code, exception type, and failing step — for each requested instance.
(ref: https://www.ibm.com/docs/en/baw/26.0.x?topic=information-put)

**Parameters:**

- `instanceIds` (query) *(required)* — Comma-separated list of process instance IDs (numeric, without the `BPDInstance.` prefix). Example: `7743` or `7743,8821`.
- `Authorization` (header) *(required)* — `Basic <base64(username:password)>`
- `Content-Type` (header) — `application/json`
- Request body — empty JSON object `{}`

**Responses:**

- `200` — Success. Response body:
  ```json
  {
    "status": "200",
    "data": {
      "runtimeErrors": [
        {
          "instanceId": "7743",
          "errorMessage": "TWException: Cannot read property ...",
          "errorCode": "CWTBG0019E",
          "exceptionType": "com.lombardisoftware.core.TWException",
          "failedStepName": "ValidateExpenseData",
          "timestamp": "2025-01-15T14:23:00Z"
        }
      ],
      "failedOperations": []
    }
  }
  ```
  - `runtimeErrors` — per-instance error entries. An entry with only `instanceId` and no other fields means no active error was found.
  - `failedOperations` — instance IDs whose error info could not be retrieved (e.g. record was cleaned up or instance is in an intermediate state).
- `401` — Unauthorized. Session expired or invalid credentials.
- `500` — Internal server error.

**Interpretation rules (same as MCP path):**

- If `runtimeErrors` is non-empty and contains `failedStepName`, that is the activity where the instance broke. Use it to focus log analysis.
- If the instance ID appears only in `failedOperations` with no entry in `runtimeErrors`, the error record may have been cleaned up — fall back to log content and grep for `BPDInstance.<id>`.
- Do **not** conflate Event Manager task IDs (numeric IDs in CWLLG* log messages) with process instance IDs.

---

## `/rest/bpm/wle/v1/process/{processId}` *(WLE v1)*

### GET /rest/bpm/wle/v1/process/{processId}

**Retrieve detailed information for a specific process instance**

Returns metadata, business data variables, and associated tasks for a process instance. This is the REST equivalent of the `get_process_details` MCP tool. The client calls `GET /v1/process/{processId}?parts=all` with optional task pagination.
(unverified by IBM docs — verify manually and add a citation before publishing)

**Parameters:**

- `processId` (path) *(required)* — Numeric process instance ID (without the `BPDInstance.` prefix). Example: `7743`.
- `parts` (query) *(required)* — Use `all` to return metadata, variables, and tasks in a single response.
- `taskLimit` (query) *(required)* — Maximum number of tasks to return. Recommended default: `100`.
- `taskOffset` (query) *(required)* — Zero-based index of the first task to return. Use `0` for the first page.
- `Authorization` (header) *(required)* — `Basic <base64(username:password)>`

**Typical call:**

```
GET {BAW_BASE_URL}/rest/bpm/wle/v1/process/{processId}?parts=all&taskLimit=100&taskOffset=0
Authorization: Basic <base64(username:password)>
```

**Response — 200 Success:**

```json
{
  "status": "200",
  "data": {
    "piid": "7743",
    "name": "Expense Approval - Acme Q1",
    "executionState": "Active",
    "state": "STATE_FAILED",
    "creationTime": "2025-01-15T10:00:00Z",
    "lastModificationTime": "2025-01-15T14:23:00Z",
    "dueDate": "2025-01-16T17:00:00Z",
    "variables": {
      "requestor": "jsmith",
      "amount": null,
      "@metadata": { "dirty": false }
    },
    "tasks": [
      {
        "tkiid": "88012",
        "name": "ValidateExpenseData",
        "displayName": "Validate Expense Data",
        "status": "Received",
        "state": "STATE_FAILED",
        "assignedTo": "jsmith",
        "assignedToDisplayName": "John Smith",
        "owner": "jsmith",
        "closeByUser": null,
        "closeByUserFullName": null,
        "dueTime": "2025-01-16T17:00:00Z"
      }
    ]
  }
}
```

**Field mapping to MCP response fields:**

| REST field (`data.*`) | MCP field (`meta_data.*` / `business_data.*` / `tasks[*].*`) |
|---|---|
| `piid` | `meta_data.process_instance_id` |
| `name` | `meta_data.instance_name` |
| `executionState` | `meta_data.status` |
| `state` | `meta_data.state` |
| `creationTime` | `meta_data.start_time` |
| `lastModificationTime` | `meta_data.last_modification_time` |
| `dueDate` | `meta_data.due_date` |
| `variables` (with `@metadata` stripped) | `business_data.variables` |
| `tasks[*].tkiid` | `tasks[*].task_instance_id` |
| `tasks[*].name` | `tasks[*].name` |
| `tasks[*].displayName` | `tasks[*].display_name` |
| `tasks[*].status` | `tasks[*].status` |
| `tasks[*].state` | `tasks[*].state` |
| `tasks[*].assignedTo` | `tasks[*].assigned_to` |
| `tasks[*].assignedToDisplayName` | `tasks[*].assigned_to_display_name` |
| `tasks[*].owner` | `tasks[*].owner` |
| `tasks[*].closeByUser` | `tasks[*].close_by_user` |
| `tasks[*].closeByUserFullName` | `tasks[*].close_by_user_full_name` |
| `tasks[*].dueTime` | `tasks[*].due_time` |

**Notes:**
- Strip all keys beginning with `@` from `variables` before presenting business data — these are internal BAW metadata fields, not process variables.
- Task pagination: if `tasks` returns exactly `taskLimit` entries, there may be more. Re-call with `taskOffset` incremented by `taskLimit` until fewer entries than `taskLimit` are returned.
- `state` uses `STATE_*` constants (e.g. `STATE_FAILED`, `STATE_FINISHED`); `executionState` uses human-readable labels (e.g. `Active`, `Completed`).

**Other responses:**

- `401` — Unauthorized. Credentials invalid or session expired.
- `404` — Process instance not found.
- `500` — Internal server error.

---

## `/ops/std/bpm/logs` *(OPS — Liberty only)*

### GET /ops/std/bpm/logs

**Retrieve the BAW server messages.log**

Returns the raw text content of the Liberty `messages.log` file. Available on Liberty-based BAW deployments only.
(unverified by IBM docs — grounded by manual inspection of MCP server source)

**Parameters:**

- `BPMCSRFToken` (header) *(required)* — CSRF token from login.
- `Cookie` (header) *(required)* — Session cookie from login.

**Responses:**

- `200` — Success. Response body is the raw log text (not JSON). Save to a temp file and read with a line range.
- `200` with empty body — The server is not Liberty. This endpoint only works on Liberty-based deployments.
- `403` — The caller lacks admin authorization.
- `404` — The endpoint is not wired on this BAW release.
- `500` — Internal server error.

**Handling each response:**

| Response | Action |
|---|---|
| 200 + non-empty body | Parse as raw log text. Read last 200 lines first. |
| 200 + empty body | Tell user: "This API is only available on Liberty-based BAW. Please paste the relevant log section." |
| 403 | Tell user admin rights are required and ask them to paste the log. |
| 404 | Tell user the endpoint is not available on this server and ask them to paste the log. |

---

## `/ops/std/bpm/event_manager_tasks`

### GET /ops/std/bpm/event_manager_tasks

**Retrieve a list of Event Manager tasks**

Returns Event Manager tasks filtered by state and optionally by process instance.
(ref: https://www.ibm.com/docs/en/baw/26.0.x?topic=tasks-listing-hold-event-manager)

**Parameters:**

- `BPMCSRFToken` (header) *(required)* — CSRF token from login.
- `Cookie` (header) *(required)* — Session cookie from login.
- `states` (query) — Comma-separated filter. Use `on_hold` for stuck tasks. Valid values: `acquired`, `blackedout`, `executing`, `on_hold`, `scheduled`.
- `process_id` (query) — Filter to tasks associated with a specific process instance ID.
- `optional_parts` (query) — Use `message` to include the serialised event payload in the response — this often contains the exception text and stack trace.
- `size` (query) — Maximum number of tasks to return.
- `offset` (query) — Pagination offset.

**Responses:**

- `200` — Success. Response contains a list of Event Manager task objects. Each object includes `em_task_id`, `state`, and (if `optional_parts=message`) a `message` field with the serialised payload.
- `400` — Invalid parameters.
- `403` — The caller is not authorized.
- `500` — Internal server error.

**Typical call:**

```
GET {BAW_BASE_URL}/ops/std/bpm/event_manager_tasks?states=on_hold&process_id={process_id}&optional_parts=message
BPMCSRFToken: {BAW_CSRF}
Cookie: {BAW_SESSION}
```
