# Service Flow Execution — Protocol

This file contains the detailed execution protocol for **Phase B** of the `test-baw-service-flows` skill.
It covers the invocation call sequence, assertion rules, and error handling for each test case.

---

## Isolation contract

Phase B is **create/read only**. These rules are absolute:

1. **Never reuse existing instances.** Do not search for or drive a pre-existing process instance. If using the process fallback, always start a new instance per test.
2. **Input data is synthetic.** The values in each test case's `input.data` are test data only. Never substitute real personal data, production record IDs, or live credentials.
3. **Side effects are the user's responsibility.** Service Flows may call external systems (databases, REST APIs, email). The user must confirm the environment is non-production before execution begins.
4. **No cleanup.** The skill does not delete or revert instances or data created during testing. If cleanup is needed, the user must do it manually.

---

## Table of contents

1. [Pre-execution setup](#1-pre-execution-setup)
2. [Per-test execution — Automation Service path](#2-per-test-execution--automation-service-path)
3. [Per-test execution — Direct service start path](#3-per-test-execution--direct-service-start-path)
4. [Per-test execution — Process fallback path](#4-per-test-execution--process-fallback-path)
5. [Assertion rules](#5-assertion-rules)
6. [Error and failure handling](#6-error-and-failure-handling)
7. [REST call quick reference](#7-rest-call-quick-reference)

---

## 1. Pre-execution setup

Before executing any test case:

1. **Read the test suite metadata.** Check `metadata.exposure_type` in the test suite file. This determines the invocation path for all tests. If `exposure_type` is absent, default to `automation_service` and fall back through the priority order on the first 404.

2. **Authenticate (REST).** If `{BAW_CSRF}` and `{BAW_SESSION}` were established during Phase A, reuse them — do not ask for credentials again. Otherwise:
   > *"What is your BAW server URL and credentials? — these are only used to get a session token and are not stored."*

   Use **Python stdlib `urllib`** for all HTTP calls — no third-party packages required. Never use `curl` or PowerShell; Python works on all supported platforms (Windows, macOS, Linux) and avoids shell quoting and alias incompatibilities. For CP4BA environments with self-signed certificates, disable verification:
   ```python
   import ssl
   ctx = ssl.create_default_context()
   ctx.check_hostname = False
   ctx.verify_mode = ssl.CERT_NONE
   # pass ctx= to every urllib.request.urlopen() call
   ```

   **On-premises / containers:** Call `POST {BAW_BASE_URL}/ops/system/login` with Basic auth:
   ```
   POST {BAW_BASE_URL}/ops/system/login
   Authorization: Basic <base64(username:password)>
   Content-Type: application/json
   Body: {"refresh_groups": false}
   ```
   On HTTP 201: capture `csrf_token` → `{BAW_CSRF}`; capture `LtpaToken2` and `JSESSIONID` cookies → `{BAW_SESSION}`.
   On 401/400: ask the user to re-enter credentials.

   **CP4BA (Zen IAM):** First obtain the Zen JWT token, then exchange it:
   ```
   GET https://<cpd-host>/v1/preauth/validateAuth
   Authorization: Basic <base64(username:password)>
   → captures accessToken → {ZEN_TOKEN}

   POST {BAW_BASE_URL}/ops/system/login
   Authorization: Bearer {ZEN_TOKEN}
   Content-Type: application/json
   Body: {"refresh_groups": false}
   → captures csrf_token → {BAW_CSRF}
   ```
   Send `Authorization: Bearer {ZEN_TOKEN}` and `BPMCSRFToken: {BAW_CSRF}` on all subsequent CP4BA requests — there are no `LtpaToken2`/`JSESSIONID` cookies.

3. **Confirm test scope.** If not already specified, ask:
   - "Run all tests" → iterate through all test cases in order.
   - "Run happy path only" → filter to `path: happy`.
   - "Run a specific test" → match by `id` or `name`.

4. **Confirm environment** (if not already confirmed):

   **BAS playback server:** If the target is a Workflow Authoring (`/bas`) playback server, show a lighter notice:
   > *"⚠️ I'll invoke the Service Flow on the BAS integrated playback server. This targets the current tip branch — no deployed snapshot is needed. Any external side effects (database writes, REST calls to real APIs) the service triggers will be real. Do you want to continue? (yes / no)"*

   **Runtime / unknown:** For all other environments:
   > *"⚠️ Running these tests will invoke the Service Flow on your BAW server. Any database writes, external API calls, or other side effects the service performs will be real. It is strongly recommended to run against a non-production environment. Do you want to continue? (yes / no)"*

---

## 2. Per-test execution — Automation Service path

Use when `metadata.exposure_type = automation_service`.

### Step 1 — Invoke the service

```
POST {BAW_BASE_URL}/automationservices/rest/{app_acronym}/{service_path}
Authorization: Basic <base64(username:password)>  (or Bearer token if OAuth)
Content-Type: application/json
Body: { ...test_case.input.data }
```

The `{service_path}` comes from the OpenAPI specification endpoint path recorded during Phase A (`metadata.automation_service_path`).

**On 200/201:** Capture the response body as `actual_output`.

**On 4xx:** The service rejected the input. If the test case `expected_status` is `error`, proceed to assertion step. If not, mark the test `ERROR`.

**On 5xx:** Mark the test `ERROR`, record the HTTP status and a plain-language description of the error, and continue to the next test.

### Step 2 — Assert

See [Section 5 — Assertion rules](#5-assertion-rules).

---

## 3. Per-test execution — Direct service start path

Use when `metadata.exposure_type = startable`.

### Step 1 — Invoke the service

```
POST {BAW_BASE_URL}/rest/bpm/wle/v1/service/{serviceId}?action=start
BPMCSRFToken: {BAW_CSRF}
Cookie: {BAW_SESSION}                       [on-prem/containers]
  — or —
Authorization: Bearer <zen_token>           [CP4BA]
Content-Type: application/x-www-form-urlencoded
Body: params=<URL-encoded JSON string of input variables>
```

The `{serviceId}` comes from `metadata.service_id`. The WLE v1 endpoint **requires `application/x-www-form-urlencoded`** — sending `application/json` returns HTTP 405. The body must be the literal string `params=` followed by a JSON-encoded object of the service's input variables, using their exact variable names.

Example for a service with inputs `name` (String) and `quantity` (Integer):

```
params={"name":"Widget A","quantity":5}
```

When constructing the body in Python, URL-encode the JSON string:
```python
import json, urllib.parse
params_json = json.dumps({"name": "Widget A", "quantity": 5})
body = urllib.parse.urlencode({"params": params_json}).encode()
# use body as the data= argument to urllib.request.urlopen()
```

> **Common mistake — wrong content type:** Sending `Content-Type: application/json` with body `{ "params": "{...}" }` returns HTTP 405. Always use form-encoded.
>
> **Common mistake — wrong variable name:** Sending `params={"params": "..."}` triggers `CWTBG0543E: The variable 'params' does not exist.` The JSON object inside `params=` must use the real variable names from the I/O contract, not a wrapper key.

**On 200:** The response body contains a `data` field with the service output. Capture `response.data` as `actual_output`.

**On 400:** Parse the response for a `errorMessage` field. If `expected_status` is `error`, proceed to assertion. Otherwise mark `ERROR`.

**On 401/403:** Session expired or insufficient permissions. Re-authenticate once and retry. If it fails again, mark `ERROR` and stop.

**On 404:** The `serviceId` is incorrect or the service is not startable on this version. Record the 404 and mark `ERROR`.

**On 5xx:** Mark `ERROR` and continue.

### Step 2 — Assert

See [Section 5 — Assertion rules](#5-assertion-rules).

---

## 4. Per-test execution — Process fallback path

Use when `metadata.exposure_type = process_embedded`. This path exercises the Service Flow indirectly by starting a process that calls it.

### Step 1 — Start the process

Use the WLE v1 process start endpoint with `action=start`. Pass `bpdId` (the process BPD ID from the test suite metadata) and `processAppId`:

```
POST {BAW_BASE_URL}/rest/bpm/wle/v1/process?action=start
  &bpdId={metadata.process_bpd_id}
  &processAppId={metadata.process_app_id}
BPMCSRFToken: {BAW_CSRF}
Cookie: {BAW_SESSION}           — or — Authorization: Bearer <zen_token> (CP4BA)
Content-Type: application/x-www-form-urlencoded
Body: params=<URL-encoded JSON of input variables, or {}>
```

**On 200:** Capture `data.piid` as `{process_id}`. The process may still be running — proceed to polling.

**On 4xx/5xx:** Mark the test `ERROR`, record the HTTP status, and move to the next test.

### Step 2 — Poll for process completion

Poll the WLE v1 process detail endpoint (not the `/bpm/processes/` path, which returns null fields on CP4BA runtimes):

```
GET {BAW_BASE_URL}/rest/bpm/wle/v1/process/{process_id}?parts=data,variables
  BPMCSRFToken: {BAW_CSRF}
  Cookie: {BAW_SESSION}           — or — Authorization: Bearer <zen_token> (CP4BA)
```

Poll every **3 seconds** for up to **30 seconds**. Read `data.state`:

- **`STATE_COMPLETED`** (or `data.variables` is non-null and populated): Process finished. Capture `data.variables` as `actual_output`.
- **`STATE_FAILED` or `STATE_TERMINATED`:** The service threw an unhandled error. If `test_case.expected_status` is `error`, capture error details from the response and proceed to assertion. Otherwise mark `FAIL`.
- **State is still `STATE_RUNNING` after 30 seconds:** Mark the test `ERROR` with message: *"Process did not complete within the 30-second timeout. The Service Flow may be waiting on an external system or is stuck."*

> **CP4BA note:** On CP4BA runtimes the `/bpm/processes/{id}` path returns a 200 with all fields `null` — it is not a reliable state source. Always use `/rest/bpm/wle/v1/process/{id}?parts=data,variables` to read process state and output variables.

### Step 3 — Assert

See [Section 5 — Assertion rules](#5-assertion-rules).

---

## 5. Assertion rules

### Success assertions (`expected_status: success`)

For each key-value pair in `test_case.expected_output`:

1. Look up the key in `actual_output`.
2. Compare using the rule for the value type:
   - **Exact string / number / boolean:** exact equality (case-sensitive for strings).
   - **`"any"` placeholder:** skip — do not assert.
   - **`"any_non_null"` placeholder:** assert the value is present and not null/undefined.
   - **Range operator (e.g. `">= 100"`, `"< 0"`):** parse the operator, evaluate `actual_value op threshold`, assert true.
   - **`"contains:<substring>"`:** assert `actual_value.toString().includes(substring)`.
   - **`"today"` (date field):** compare only the date portion of the ISO-8601 string to the execution date.
   - **`null`:** assert the field is absent or explicitly null in the actual output.
3. Record each assertion individually in the result.

### Error assertions (`expected_status: error`)

1. Assert that the service returned a non-2xx HTTP status OR that the response body contains an error indicator.
2. If `test_case.expected_error.code` is set (and not `"any"`): assert the actual error code matches exactly.
3. If `test_case.expected_error.message_contains` is set: assert `actual_error_message.includes(expected_substring)`.
4. If `test_case.expected_error.http_status` is set: assert the HTTP status code matches.

### Pass / Fail / Error semantics

| Result | Meaning |
|---|---|
| `PASS` | All assertions in `expected_output` or `expected_error` passed. |
| `FAIL` | At least one assertion failed — the service responded but the output did not match expectations. |
| `ERROR` | An invocation failure (4xx/5xx, timeout, auth failure, network error) prevented the test from producing assertable output. Result is inconclusive. |

---

## 6. Error and failure handling

### Authentication failure (401) or session expiry (400 on WLE v1)

Re-authenticate via `POST {BAW_BASE_URL}/ops/system/login` and retry the failed call once. If the retry also fails, mark all remaining tests `ERROR` and tell the user their credentials need attention.

> **WLE v1 endpoint note:** The `/rest/bpm/wle/v1/service/{serviceId}?action=start` endpoint returns **HTTP 400** (not 401) when the CSRF token has expired. If a WLE v1 call returns 400 and the response body contains `"status":"error"` with `"errorNumber"` absent or unrelated to input validation, treat it as a session expiry: re-authenticate, update `{BAW_CSRF}` and `{BAW_SESSION}`, and retry the call once before marking the test `ERROR`.

### CSRF token issues (403)

Ensure the `BPMCSRFToken` header is being sent. Re-read the token from the last login response and retry once.

### Service not found (404 on direct invocation)

The `serviceId` is incorrect or the service is not startable. Record the 404, mark the test `ERROR`, and note that the service may not be startable or the ID may have changed since discovery.

### Process fallback timeout

If the process does not reach `Completed` or `Failed` within 30 seconds, mark the test `ERROR` with the timeout message. Do not attempt to terminate the instance — leave it for the user to investigate.

### Suite-level abort

Do not abort the suite for any reason. Every test is independent. Continue through all tests regardless of individual failures or errors.

---

## 7. REST call quick reference

| Action | Endpoint |
|---|---|
| Authenticate | `POST /ops/system/login` |
| Invoke via Automation Service | `POST /automationservices/rest/{app}/{service}` |
| Invoke via direct start | `POST /rest/bpm/wle/v1/service/{serviceId}?action=start` |
| Start process (fallback) | `POST /rest/bpm/wle/v1/process?action=start&bpdId=<bpdId>&processAppId=<appId>` |
| Poll process state | `GET /rest/bpm/wle/v1/process/{processId}?parts=data,variables` |
| List exposed processes | `GET /bpm/exposed-processes?container=<container>` |
| Discover API endpoints | `GET /bpm/docs` |
