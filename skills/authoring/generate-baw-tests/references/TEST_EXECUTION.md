# Test Execution — Protocol

This file contains the detailed execution protocol for **Phase B** of the `generate-baw-tests` skill.
It covers the REST API call sequence, assertion rules, and error handling for each test case.

---

## Isolation contract

Phase B is **read/create only with respect to existing data**. These rules are absolute and apply to every test run:

1. **Always start fresh.** Every test case begins with a `start_process` call that creates a brand-new process instance. Never claim, complete, update, suspend, resume, retry, or terminate an instance that was not started by the current test run.
2. **Never search for and reuse existing instances.** Do not call `search_processes` or `list_processes` and pick an existing instance to drive. Test instances are created by the skill, owned by the skill, and driven to completion by the skill.
3. **Test instances are disposable.** The instances created during a test run are real BAW instances and will appear in the server's task lists and reporting. This is expected and acceptable on non-production environments. On production, warn the user first (see pre-execution setup below).
4. **No side-effect cleanup is performed.** The skill does not delete or terminate test instances after the run. If the user wants to clean up, they can use the `inspect-baw-processes` skill. Do not offer to terminate them automatically.
5. **Input data is test data only.** The values in each test case's `input.data` and step `output` blocks are synthetic test values. Never substitute real personal data, production record IDs, or live integration credentials into the test payload.

---

## Table of contents

1. [Pre-execution setup](#1-pre-execution-setup)
2. [Per-test execution sequence](#2-per-test-execution-sequence)
3. [Assertion rules](#3-assertion-rules)
4. [Error and failure handling](#4-error-and-failure-handling)
5. [REST call quick reference](#5-rest-call-quick-reference)

---

## 1. Pre-execution setup

Before executing any test case:

1. **Resolve transport** — check the tool list for process execution MCP tools (`start_process`, `search_tasks`, `claim_task`, `complete_task`).
   - **MCP present:** use MCP for all execution steps. Skip steps 2–3 entirely — do not ask for a server URL or credentials.
   - **MCP absent:** use REST. Continue with steps 2–3 below.

2. **REST only — obtain a session.** Ask for the server URL and credentials immediately before the first login call — not earlier:
   > *"What is your BAW server URL and credentials? (e.g. `https://baw.example.com:9443`) — these are only used to get a session token and are not stored."*

   If `{BAW_BASE_URL}` and credentials were already set during Phase A, reuse them — do not ask again.

   Call `POST {BAW_BASE_URL}/ops/system/login` with:
   - `Authorization: Basic <base64(username:password)>`
   - `Content-Type: application/json`
   - Body: `{"refresh_groups": false}`

   On success (HTTP 201): capture `csrf_token` from the JSON body and store as `{BAW_CSRF}`. Capture the `LtpaToken2` and `JSESSIONID` cookies from the `Set-Cookie` headers and store as `{BAW_SESSION}`. Send `BPMCSRFToken: {BAW_CSRF}` and the cookie on all subsequent requests. The session is valid for all `/ops/…` and `/bpm/…` calls alike.

   **Do not use `/rest/bpm/wle/v1/system/login`** — that is the legacy WLE path, not valid in BAW 26.x.

   **If login returns 401/400:** ask the user to check their credentials and re-enter them.

3. **REST only — confirm the process model name and snapshot** — the test suite's `app.process_model` and `app.snapshot` must match what is deployed in the target environment. If in doubt, call `GET /std/bpm/containers` and `GET /std/bpm/containers/{container}/versions` to confirm the snapshot is present and active.

4. **Ask which tests to run** if not already specified:
   - "Run all tests" → iterate through all test cases in order.
   - "Run happy path only" → filter to `path: happy`.
   - "Run a specific test" → match by `id` or `name`.

---

## 2. Per-test execution sequence

For each test case (`type: process`), follow this exact sequence:

### Step 1 — Start the process instance

```
POST /bpm/processes
  ?model=<app.process_model>
  &container=<app.acronym>
  &version=<app.snapshot>
Body: { ...test_case.input.data }
```

**On success:** Capture the returned `process_id` (or `instanceId` depending on the response shape). Store it for all subsequent calls in this test.

**On failure (4xx/5xx):** Mark the test `ERROR`, record the HTTP status and response body in the result, and move to the next test. Do not attempt to continue executing this test.

---

### Step 2 — Iterate through the expected task steps

For each `step` in the test case's `steps` array, in order:

#### 2a — Confirm the expected task is available

```
GET /bpm/user-tasks
  ?process_id=<process_id>
  &states=ready,claimed
```

Check that the task named `step.task_name` appears in the list.

- **If it is present:** Capture its `task_id` and proceed.
- **If a different task appears instead:** The process has branched unexpectedly. Record a `FAIL` for this step: note the expected task name and the actual task name found. Log the actual branch taken as diagnostic information. **Stop executing this test** — do not complete the unexpected task. Record the full result for this test as `FAIL`.
- **If no tasks are available and the process has not yet completed:** Wait up to 10 seconds (retry twice with a 5-second interval) for async service tasks to finish. If still no task appears, mark the step `ERROR`.

#### 2b — Claim the task

```
POST /bpm/user-tasks/{task_id}/claim
```

If claiming fails with a 409 (already claimed by another user), call `get_task_details` to confirm who holds it and report the conflict in the result. Do not force-unclaim.

#### 2c — Assert pre-completion business data

If `step.expected_business_data` is non-empty:

```
GET /bpm/user-tasks/{task_id}
  ?optional_parts=data
```

For each key-value pair in `expected_business_data`, compare the actual value to the expected value. Record any mismatches as step-level assertion failures — they do not stop execution of this step, but they do contribute to the overall test result.

#### 2d — Complete the task

```
POST /bpm/user-tasks/{task_id}/complete
Body: { ...step.output }
```

If completion fails with a 4xx error, mark this step `ERROR` and stop executing the test.

---

### Step 3 — Assert the final state

After all steps are complete (or after reaching a step that ends at `[End Event]`):

```
GET /bpm/processes/{process_id}
  ?optional_parts=data,variables
```

Check:
1. The instance `status` matches `expected_outcome.final_status`.
2. Each key-value pair in `expected_outcome.output_variables` matches the actual variable value from the response.

Record the result of each assertion individually in the result file.

---

## 3. Assertion rules

### Pass / Fail / Error semantics

| Result | Meaning |
|---|---|
| `PASS` | Every step assertion passed AND the final state assertion passed. |
| `FAIL` | At least one assertion failed (wrong task appeared, wrong business data, wrong final state, or missing output variable value). The process ran but behaved differently from the test case expectation. |
| `ERROR` | An execution failure prevented the test from completing (API call returned 4xx/5xx, timeout waiting for a task, auth failure, network error). The test result is inconclusive. |

### Assertion comparison

- String values: exact match (case-sensitive). If the test case uses a placeholder like `"any"`, skip the assertion.
- Numeric values: exact equality unless the test case specifies a range (e.g. `{"amount": ">= 100"}`). For range assertions, parse the operator and evaluate accordingly.
- Boolean values: `true`/`false` exact match.
- Null/missing: if the test case expects `null` and the variable is absent, treat as a pass. If the test case expects a non-null value and the variable is absent, treat as a fail.
- Date values: compare as ISO-8601 strings. If the test case uses `"today"` as a placeholder, compare to the execution date only (ignore time component).

---

## 4. Error and failure handling

### API authentication failure (401)

If a REST call returns 401, the session token has expired. Re-authenticate via `POST {BAW_BASE_URL}/ops/system/login` (same body and headers as the initial login), then retry the failed call once. If the retry also returns 401, mark all remaining tests `ERROR` and tell the user their credentials need attention. Do not switch to MCP tools after an auth failure.

### CSRF token issues (403)

If a mutating REST call returns 403, ensure the `BPMCSRFToken` header is being sent. Re-read the token from the login response and retry once.

### Task not found (404 on task claim/complete)

If claiming or completing a task returns 404, the task may have been completed or routed away by an async step. Call `get_process_details` to see the current state and report it in the result.

### Process stuck in running state after final step

If the process does not reach a terminal state within 30 seconds after the last task is completed (poll every 5 seconds), mark the final state assertion `ERROR` with the message "Process did not reach a terminal state within the timeout period."

### Suite-level abort conditions

Do not abort the entire suite. Every test is independent. Even if five consecutive tests error out, continue to the remaining tests and report all results together.

---

## 5. REST call quick reference

| Action | Endpoint |
|---|---|
| Start a process instance | `POST /bpm/processes?model=<model>&container=<container>&version=<version>` |
| List open tasks for an instance | `GET /bpm/user-tasks?process_id=<id>&states=ready,claimed` |
| Get task details + business data | `GET /bpm/user-tasks/{task_id}?optional_parts=data` |
| Claim a task | `POST /bpm/user-tasks/{task_id}/claim` |
| Complete a task | `POST /bpm/user-tasks/{task_id}/complete` with JSON body |
| Get process final state | `GET /bpm/processes/{process_id}?optional_parts=data,variables` |
