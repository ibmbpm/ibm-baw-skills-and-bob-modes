---
name: troubleshoot-baw-logs
description: "Diagnoses IBM Business Automation Workflow (BAW) runtime failures by analyzing error logs, stack traces, and FFDC files. Identifies root causes, correlates entries across log types, and provides structured remediation steps. Use when the user: pastes BAW log content (SystemOut.log, messages.log, trace.log, FFDC files, or Liberty log lines); asks about a BAW error code (e.g. BPMD0049E, CWTBG0019E, CWWKB*, CWLLG*); mentions a process instance in error or stuck state; says snapshot deployment or activation failed; or asks why a process/task/service failed. Also use when pointing to a local BAW log file, or when the MCP server is connected and they want get_process_instance_errors or get_baw_server_logs called. Trigger phrases: BAW error, FFDC, process is stuck, error state, task keeps failing, service call failed, stack trace, TWException, BPDInstance, messages.log, SystemOut.log, trace.log, BPMD, CWWKB, or any pasted log content with Liberty/BPM thread IDs and error codes."
license: Apache-2.0
metadata:
  version: 1.0.0
---

# Troubleshoot BAW Logs

Help developers and administrators diagnose IBM BAW runtime failures quickly and accurately. The goal is to move from raw log noise to a clear root cause with actionable next steps.

## Execution mode

At the start of the session, check your tool list once and pick a path:

- If you have `get_exposed_processes` in your tool list → MCP path. Use the MCP operations described in this skill.
- If `get_exposed_processes` is absent → REST path. Execute all REST calls directly using `execute_command` (curl). Do not ask the user to run curl commands themselves — run them for the user. See `references/baw-rest.md` for endpoint details and the REST fallback section below for the exact call sequence.

Stay on the chosen path for the entire session. Do not use a failed tool call as evidence of absence — only absence from the tool list counts.

Also read `references/BAW_CONNECTION.md` — it covers the no-MCP user prompt and how to ask for `{BAW_BASE_URL}` before making REST calls.

## How to detect which input mode applies

Read the user's message and pick the right starting point — modes are not mutually exclusive, use all available information.

**Live-log mode (MCP path only — try first when MCP server is connected)** — Call `get_baw_server_logs` to fetch the messages.log directly from the BAW server. This is only available on Liberty-based deployments. Check `available` in the response before proceeding:
- `available: true` → analyze `content` directly. Skip asking the user for log files.
- `available: false, error contains "404"` → endpoint not wired on this server. Fall back to paste or file mode.
- `available: false, error contains "403"` → caller lacks admin rights. Tell the user and fall back.
- `available: false, error contains "empty response"` → server is not Liberty. Tell the user this API only works on Liberty and fall back.
- Any other error → tell the user what went wrong and fall back to paste or file mode.
- **No MCP available** → attempt live log retrieval via REST (`GET /ops/std/bpm/logs`) after establishing a session. See the REST fallback section. If that endpoint returns 404, 403, or an empty body, **stop immediately and ask the user** — do not probe any other endpoints.

**Paste mode** — The user has pasted raw log content (Liberty log lines, an FFDC snippet, a Java stack trace, a script error message). Analyse the text directly.

**File mode** — The user says "my log is at `/logs/SystemOut.log`" or similar, and you can read that path with `read_file`. Do so. If the path is inaccessible (remote server, no filesystem access), say so plainly and ask the user to paste the relevant section. Do not fail silently.

**Instance mode** — The user mentions a specific process instance ID (a number, or `BPDInstance.<number>`). When MCP is connected, call `get_process_instance_errors` first to retrieve structured error data, then combine it with whatever log content you have. When using REST, call `PUT /rest/bpm/wle/v1/process/errors?instanceIds={process_id}` to retrieve runtime error details — see the REST fallback section below for full details.

---

## Analysis steps

Before diving into any log content, read `references/BAW_LOG_FORMATS.md`. It covers the structure of every BAW log type, the `process/errors` API response fields, and the common error patterns table.

### Step 1 — Orient yourself

Identify what you're looking at:
- Which log type(s) are present? (`messages.log`, `SystemOut.log`, `trace.log`, FFDC file, `process/errors` API response, or a mix)
- What is the failure surface? (Process instance stuck in error, failing script task, unreachable service, auth failure, DB issue, server startup failure)
- Is there a process instance ID in the text? (`BPDInstance.<number>`, `piid=<number>`) — capture it; you'll use it for correlation.

### Step 2 — Find the earliest causal error

Log files record *symptoms* repeatedly. Your job is to find the *cause* — the first error in the chain before the cascade began.

- **In Liberty logs (`messages.log` / `SystemOut.log`):** scan for `E` (ERROR) and `F` (FAILURE) level entries, sorted by timestamp. The earliest is usually the trigger. When you see `FFDC1015I`, note the filename it names — that file has the full stack.

  > **⚠️ Do not conflate scheduler task IDs with process instance IDs.** BAW log messages contain many numeric IDs. A line like `CWLLG0181E: The following error occurred in the 360 task` refers to an **Event Manager scheduler task ID**, not a process instance. Only treat a numeric ID as a process instance reference when the log explicitly uses `BPDInstance.<number>`, `piid=<number>`, or the structured `instanceId` field from the `process/errors` API. Before attributing any log error to a specific instance, verify with a grep for `BPDInstance.<id>` in the log.
- **In FFDC files:** go straight to the `Stack Dump` section and read the `Caused by:` chain bottom-up — the deepest `Caused by:` is the root exception.
- **In `process/errors` API response:** `failedStepName` tells you where it broke; `errorMessage` tells you what the script said; `errorCode` gives you the BPM code to look up in `references/BAW_LOG_FORMATS.md`.
- **Cross-log correlation:** use the thread ID (8-digit hex, e.g. `00000087`) to join entries across `messages.log`, `trace.log`, and the FFDC prologue. A single failing request stays on one thread.

### Step 3 — Match against known patterns

Check the error code, exception class name, or key phrase against the Common Error Patterns table in `references/BAW_LOG_FORMATS.md` (section 7). If you find a match, use the "First Response Step" column as the starting point for your remediation advice.

If the error isn't in the table, reason from first principles:
- Script errors → `failedScriptName` and `failedLine`; likely a null reference or type mismatch
- Service call failures → downstream endpoint unreachable or returned an unexpected response
- Auth errors → LDAP, OIDC, or token configuration
- DB errors (SQLCODE) → connection pool exhaustion or lock timeout
- Memory errors → large Business Object payloads or insufficient heap

### Step 4 — Synthesise

Write the diagnosis report (see template below). Be specific — name the exact step, service, script, or configuration that failed. Don't just restate the error message; explain *why* it happened and *what to do next*.

---

## Using the MCP tools (MCP path)

Use the exact function names written below. Do not paraphrase, rename, or substitute a tool name.

### get_baw_server_logs (Liberty only)

Call this first whenever the MCP server is connected and the user hasn't already pasted log content. It fetches the live `messages.log` directly from BAW.

```
get_baw_server_logs(system_id=<optional>)
```

Always check `available` before using `content`. If `available` is false, read `error` and tell the user in plain language. An empty body means the server is not Liberty and this path won't work.

In the diagnosis report header, write the source exactly as:
```
**Log source(s):** live messages.log via `get_baw_server_logs`
```

### get_process_instance_errors

When you have a process instance ID, call **`get_process_instance_errors`** — this is the exact name of the MCP tool. Do not call any other function or invent a substitute name.

```
get_process_instance_errors(instance_ids=<numeric-id>)
```

1. Call with `instance_ids` set to the numeric instance ID (just the number — e.g. `7743`, not `"BPDInstance.7743"`).
2. Use `failing_step`, `error_message`, `error_code`, and `exception_type` from the response to focus your log analysis.
3. If `failed_operations` is populated, **do not assume the instance failed**. Check `get_process_details` first:
   - If `state` is `STATE_FINISHED` or `STATUS_COMPLETED` → the instance completed normally; there is no active runtime error record to retrieve. Report this accurately.
   - If `state` is `STATE_FAILED` or `STATUS_FAILED` → the error record may have been cleaned up or was not serializable. Ask the user for log content and search for `BPDInstance.<id>` in the logs.
4. Follow up with `get_process_details` (MCP) or `GET /rest/bpm/wle/v1/process/{processId}` (REST) to see instance state, business data, and task history for the execution path leading to the failure.
5. When searching logs for a process instance, always grep explicitly for `BPDInstance.<id>` — never assume that a numeric ID appearing elsewhere in the log (e.g. in a task scheduler message) refers to the process instance.

In the diagnosis report header, always record the exact call you made, e.g.:
```
**Log source(s):** `get_process_instance_errors(instance_ids=7743)` via workflow-runtime-mcp-server
```
If the tool call failed or was unavailable, record that too:
```
**Log source(s):** `get_process_instance_errors(instance_ids=7743)` — call failed (tool unavailable)
```
This is the audit record. It must be accurate regardless of whether the call succeeded.

---

### get_process_details

When you need instance state, business variables, and task history for a known process instance ID, call `get_process_details`:

```
get_process_details(
    process_instance_id=<numeric-id>,
    task_limit=100,
    task_offset=0,
    system_id=<optional>
)
```

1. Use `meta_data.state` (`STATE_FAILED`, `STATE_FINISHED`, etc.) to determine whether the instance is still in an error state before reporting.
2. Use `meta_data.status` (`executionState`) as the human-readable label for the report.
3. Strip any `business_data.variables` entries — they are process variables from the response; use them to understand the instance's data context at the time of failure.
4. Each entry in `tasks` corresponds to one task instance. `state` and `status` on the task reveal whether that step completed, failed, or is still pending.
5. If `tasks` returns exactly 100 entries, there may be more — re-call with `task_offset=100` and continue until fewer than `task_limit` entries are returned.

In the diagnosis report header, record the call:
```
**Log source(s):** `get_process_details(process_instance_id=7743, task_limit=100, task_offset=0)` via workflow-runtime-mcp-server
```

---

## REST fallback (no MCP)

When the MCP server is not connected, execute all REST calls directly using `execute_command` with `curl`. Do not present curl commands for the user to run — run them yourself. Use `-k` to allow self-signed certificates and `-s` for silent output. BAW servers commonly use self-signed certs on localhost; always include `-k`.

### Establish connection first

> **🔒 Security prerequisite — state this before asking for credentials:**
> *"Before we begin, please confirm:*
> - *Your BAW server URL must use **HTTPS** (not HTTP). Do not enter credentials over an unencrypted connection.*
> - *Use a **dedicated service account** with read-only permissions rather than a personal or admin account. If you don't have one, ask your BAW administrator to create an account with Workflow Center reader access.*"

Before any REST call, confirm `{BAW_BASE_URL}` and credentials with the user if not already provided. Credentials are only used to obtain a session token — they are not stored beyond this session. Once you have them, execute the login call:

```bash
curl -k -s -X POST "{BAW_BASE_URL}/ops/system/login" \
  -H "Authorization: Basic <base64(username:password)>" \
  -H "Content-Type: application/json" \
  -d '{"refresh_groups": false}'
```

On HTTP 201, parse `csrf_token` from the JSON response body and capture the `Set-Cookie` headers for `LtpaToken2` and `JSESSIONID`. Store these as `{BAW_CSRF}` and `{BAW_SESSION}` for all subsequent `/ops/…` calls.

To capture cookies with curl, add `-c /tmp/baw_cookies.txt` to the login call and `-b /tmp/baw_cookies.txt` to subsequent calls.

The WLE v1 endpoint (`/rest/bpm/wle/v1/process/errors`) uses HTTP Basic auth per request — it does not require the session or CSRF token.

### Retrieve process instance runtime errors

Execute directly — no session required for this endpoint:

```bash
curl -k -s -X PUT \
  "{BAW_BASE_URL}/rest/bpm/wle/v1/process/errors?instanceIds={process_id}" \
  -H "Authorization: Basic <base64(username:password)>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

You can pass multiple comma-separated IDs in `instanceIds`. Parse the JSON response and extract:
- `data.runtimeErrors[]` — array of per-instance error objects, each containing:
  - `instanceId` — the process instance ID
  - `errorMessage` — the exception message (maps to `error_message` in MCP response)
  - `errorCode` — BPM error code (maps to `error_code`)
  - `exceptionType` — Java exception class (maps to `exception_type`)
  - `failedStepName` — the activity that failed (maps to `failing_step`)
  - `timestamp` — when the error occurred
- `data.failedOperations[]` — instance IDs whose error info could not be retrieved

Apply the same interpretation logic as the MCP path: if `runtimeErrors` is empty and the ID appears in `failedOperations`, the error record may have been cleaned up — ask the user for log content. If `failedStepName` is present, use it as the failing step for log correlation (grep for `BPDInstance.<id>`).

In the diagnosis report header, record the call made:
```
**Log source(s):** `PUT /rest/bpm/wle/v1/process/errors?instanceIds=7743` via REST (curl)
```

### Retrieve process instance details

After retrieving runtime errors, fetch the full instance state, business data, and tasks. No session is required — this endpoint uses HTTP Basic auth per request:

```bash
curl -k -s \
  "{BAW_BASE_URL}/rest/bpm/wle/v1/process/{process_id}?parts=all&taskLimit=100&taskOffset=0" \
  -H "Authorization: Basic <base64(username:password)>"
```

Parse the JSON response and extract from `data`:
- `piid` → process instance ID (confirm it matches what you queried)
- `executionState` → human-readable status (e.g. `Active`, `Completed`)
- `state` → machine-readable state constant (e.g. `STATE_FAILED`, `STATE_FINISHED`)
- `creationTime`, `lastModificationTime`, `dueDate` → timeline context
- `variables` → business data; strip all keys starting with `@` (e.g. `@metadata`) before presenting
- `tasks[]` → each task entry has `tkiid`, `name`, `displayName`, `status`, `state`, `assignedTo`, `dueTime`

See `references/baw-rest.md` — `/rest/bpm/wle/v1/process/{processId}` — for the full field list and field mapping to MCP response fields.

Apply the same state interpretation as the MCP path:
- `state: STATE_FINISHED` or `executionState: Completed` → instance completed; no active error to report.
- `state: STATE_FAILED` → instance is in an error state; combine with error data from the previous step.

If `tasks` returns exactly `taskLimit` entries, re-call with `taskOffset` incremented by `taskLimit` until fewer are returned.

In the diagnosis report header, record the call:
```
**Log source(s):** `GET /rest/bpm/wle/v1/process/7743?parts=all&taskLimit=100&taskOffset=0` via REST (curl)
```

### Retrieve event manager tasks for an instance

If the user reports a task that failed silently or a repeating error (which in BAW often manifests as a stuck Event Manager task), execute:

```bash
curl -k -s \
  "{BAW_BASE_URL}/ops/std/bpm/event_manager_tasks?states=on_hold&process_id={process_id}&optional_parts=message" \
  -H "BPMCSRFToken: {BAW_CSRF}" \
  -b /tmp/baw_cookies.txt
```

The `message` optional part returns the serialised event payload, which may contain the exception text and stack trace. This is particularly useful for failures in timer events, receive tasks, and integration services.

### Retrieve live server logs

`GET /ops/std/bpm/logs` is available on Liberty-based BAW deployments only. Execute after establishing a session:

```bash
curl -k -s \
  "{BAW_BASE_URL}/ops/std/bpm/logs" \
  -H "BPMCSRFToken: {BAW_CSRF}" \
  -b /tmp/baw_cookies.txt
```

- HTTP 200 with a non-empty body → the response body is the raw `messages.log` content. Write it to a temp file (e.g. `/tmp/baw_messages.log`) and read with `read_file` using a line range (last 200 lines first).
- HTTP 404 → the endpoint is not wired on this BAW release. **Stop. Do not try any other endpoints.** Ask the user immediately (see prompt below).
- HTTP 403 → caller lacks admin rights. **Stop. Do not try any other endpoints.** Tell the user and ask (see prompt below).
- Empty body → the server is not Liberty. **Stop. Do not try any other endpoints.** Tell the user and ask (see prompt below).

When any of the above non-200 conditions occur, ask immediately:

> "The server log endpoint isn't available on this server (`<HTTP status>`). Could you paste the relevant section of `messages.log` (or `SystemOut.log`), or give me a local file path I can read?"

Record the source accurately in the report:
```
**Log source(s):** `GET /ops/std/bpm/logs` via REST (curl) — pasted on fallback
```

---

## Diagnosis report template

Always produce a report in this structure. Keep it scannable — headings and bullets rather than long paragraphs.

```
## BAW Failure Diagnosis

**Instance / Context:** [process instance ID if known, or "N/A"]
**Log source(s):** [exact source — use the precise MCP tool call if one was made, e.g.
  `get_process_instance_errors(instance_ids=7743)` via workflow-runtime-mcp-server,
  `get_baw_server_logs` via workflow-runtime-mcp-server,
  pasted SystemOut.log excerpt,
  FFDC file defaultServer_XXXXXXXX_...txt,
  or a combination. Never invent a tool name.]
**Failure surface:** [one sentence: what failed, where, when]

### Root cause
[One to three sentences. Name the exact exception class or error code, the failing step or service,
and the immediate trigger — e.g. "A `TWException: Cannot read property 'amount' of undefined`
was thrown at line 3 of the 'ValidateExpenseData' script task because the `orderData` variable
was null when the process reached that step."]

### Evidence
- [Key log line or API field that confirms the root cause — quote it]
- [Any corroborating entry — e.g. the FFDC1015I pointer in messages.log]

### Likely contributing factors
- [Why the variable was null / why the service was unreachable / etc.]

### Remediation steps
1. [Immediate fix — the specific change to make]
2. [Verification — how to confirm the fix worked]
3. [Optional: longer-term hardening — guard clause, error boundary, retry logic]

### If this recurs
[One sentence on where to look first — e.g. "Enable `WLE.wle_bpd=all` trace before reproducing
to capture the exact variable state at the failing step."]
```

Omit sections that don't apply. Add a "What I can't determine from this log" section when there's a critical gap in the evidence.

---

## File mode assumptions

When reading a log file via `read_file`:
- Large files (> 500 lines): read the last 200 lines first — errors are typically near the end. Expand earlier if needed.
- If the user says "the error happened around 2pm", use timestamps to jump to that window.
- State which lines you analysed so the user knows what you saw.

If the file is inaccessible (remote server, missing path, requires credentials), say so and ask the user to paste the relevant section.

---

## What this skill does not do

- Replace Process Admin Console (PAC) or the WebPD debugger for stepping through live process execution.
- Cover all log types exhaustively — focus on what's in front of you and say so when evidence is limited.
