# BAW REST API Reference — Service Flow Endpoints

This file covers the REST endpoints used by the `test-baw-service-flows` skill.
Source specs: `apis/baw-ops.26.0.0.json` (basePath `/ops`), `apis/baw-process.26.0.0.json` (basePath `/bpm`), `apis/baw-wle-v1.26.0.0.json` (basePath `/rest/bpm/wle/v1`).

---

## Environment differences

The API surface (`/ops`, `/bpm`, `/rest/bpm/wle/v1`) is identical across all BAW deployment types. What differs per environment is the **base URL** and **authentication method**.

| Environment | Base URL pattern | Authentication |
|---|---|---|
| **On-premises (traditional WAS)** | `https://<host>:<port>` e.g. `https://baw.example.com:9443` | HTTP Basic → CSRF token via `POST /ops/system/login`. Session held in `LtpaToken2` + `JSESSIONID` cookies. |
| **BAW on containers (standalone)** | `https://<host>:<port>` — same port structure as on-prem | HTTP Basic → CSRF token via `POST /ops/system/login`. Same cookie model. |
| **CP4BA — Workflow Authoring (BAS)** | `https://<cpd-route>/bas`. No deployed snapshot required. Has an integrated **playback server** for in-development testing. ⚠️ Service invocation uses `{BAS_BASE_URL}/rest/bpm/wle/v1/service/{id}?action=start` — the `/bpm/dev/` prefix is **not** used for invocation calls (returns 404 on BAW 26.x). Discovery endpoints (`/exposed/service`, `/exposed/process`) also respond correctly without the prefix. `GET /ops/std/bpm/servers/workflow` returns `{"servers":[]}`. | Zen token (same as runtime below). No separate login for the playback server — use the BAS Zen token. |
| **CP4BA — Workflow Runtime** | `https://<cpd-route>/baw-<instance>` e.g. `baw-dev`, `baw-aut`, `baw-prod`. The `/ops`, `/bpm`, and `/rest/bpm/wle/v1` paths are appended to this base. Requires an active snapshot to be deployed. | **Zen token** (IAM-based). Obtain via `GET https://<cpd-host>/v1/preauth/validateAuth` with Basic auth `username:password`. Capture `accessToken`. Use as `Authorization: Bearer <accessToken>` on all requests. The `/ops/system/login` CSRF call is still required — send `Authorization: Bearer <accessToken>` with body `{"refresh_groups": false}` to get `BPMCSRFToken`. |
| **BAW on Cloud (SaaS)** | `https://<tenant>.baw.ibmcloud.com` | IAM API key or OAuth2 bearer token. Consult the tenant-specific credentials. CSRF token flow is the same once authenticated. |

> **Detecting the environment type:** Call `GET {BAW_BASE_URL}/ops/std/bpm/servers/workflow`. If `servers` is an empty array, this is a Workflow Authoring (BAS) environment — service flows can be invoked directly at `{BAS_BASE_URL}/rest/bpm/wle/v1/service/{id}?action=start` (no snapshot deployment required; the `/bpm/dev/` prefix is NOT used for invocation on BAW 26.x). If `servers` contains one or more entries, this is a Workflow Runtime endpoint.

> **Detecting the server version:** Call `GET {BAW_BASE_URL}/ops/docs` → `info.version`. A version string like `8.6.2.21021` indicates BAW v21; `8.6.12.26030` indicates BAW 26.0.3. CP4BA environments expose the same version string regardless of whether the endpoint is authoring or runtime.

> **Detecting version from a TWX:** The `META-INF/package.xml` inside the TWX ZIP contains `buildVersion="8.6.12.26030"`. If this is newer than the server's `info.version`, the TWX cannot be imported — tell the user and stop.

---

## Authentication

> **Cross-platform HTTP — always use Python stdlib `urllib` for all HTTP calls.** Never use `curl` or PowerShell for REST calls — Python is available on all supported platforms (Windows, macOS, Linux) and avoids shell quoting and alias incompatibilities. No third-party packages are needed. For CP4BA environments with self-signed or private CA certificates, disable certificate verification:
> ```python
> import ssl
> ctx = ssl.create_default_context()
> ctx.check_hostname = False
> ctx.verify_mode = ssl.CERT_NONE
> # pass ctx= to every urllib.request.urlopen() call
> ```

### On-premises / BAW on containers

```
POST {BAW_BASE_URL}/ops/system/login
Authorization: Basic <base64(username:password)>
Content-Type: application/json
Body: {"refresh_groups": false}
```

**On HTTP 201:**
- Capture `csrf_token` from the JSON body → store as `{BAW_CSRF}`.
- Capture `LtpaToken2` and `JSESSIONID` cookies from `Set-Cookie` headers → store as `{BAW_SESSION}`.
- Send `BPMCSRFToken: {BAW_CSRF}` and `Cookie: {BAW_SESSION}` on all subsequent requests.

**On 401/400:** Ask the user to re-enter credentials.

**Do NOT use** `/rest/bpm/wle/v1/system/login` — that is the legacy WLE path, not valid in BAW 26.x.

### CP4BA (Zen/IAM token)

```
GET https://<cp4ba-host>/v1/preauth/validateAuth
Authorization: Basic <base64(username:password)>
```

Capture `accessToken` from the JSON response. Then call login against the BAW instance endpoint to get the CSRF token:

```
POST {BAW_BASE_URL}/ops/system/login
Authorization: Bearer <accessToken>
Content-Type: application/json
Body: {"refresh_groups": false}
```

Store `csrf_token` → `{BAW_CSRF}`. Send `Authorization: Bearer <accessToken>` and `BPMCSRFToken: {BAW_CSRF}` on all subsequent calls. No session cookies are used.

---

## Service Flow Invocation

### `POST /automationservices/rest/{appAcronym}/{servicePath}` — Preferred

**Invoke a Service Flow exposed as an Automation Service**

Available on: on-prem, BAW on containers, CP4BA. Not available on older BAW versions that predate the Automation Services feature.

```
POST {BAW_BASE_URL}/automationservices/rest/{appAcronym}/{servicePath}
Authorization: Basic <base64(user:pass)>   [on-prem/containers]
  — or —
Authorization: Bearer <zen_token>           [CP4BA]
BPMCSRFToken: {BAW_CSRF}
Content-Type: application/json
Body: { ...input fields per the service's OpenAPI contract }
```

**Responses:**
- `200`/`201` — successful invocation; response body contains the output fields.
- `400` — input validation error; response body contains details.
- `401` — authentication failure; re-authenticate and retry once.
- `403` — caller is not a member of the team authorised for this service.
- `404` — service path incorrect or not published.
- `500` — server-side error; check BAW server logs.

---

### `POST /rest/bpm/wle/v1/service/{serviceId}?action=start` — Second choice

**Invoke a directly startable Service Flow via the WLE v1 API**

Available on: on-prem, BAW on containers, CP4BA. Input variables are passed inside a **`params` form field** as a JSON-encoded string. The request must use `application/x-www-form-urlencoded` — **not** `application/json`.

```
POST {BAW_BASE_URL}/rest/bpm/wle/v1/service/{serviceId}?action=start
BPMCSRFToken: {BAW_CSRF}
Cookie: {BAW_SESSION}                       [on-prem/containers]
  — or —
Authorization: Bearer <zen_token>           [CP4BA]
Content-Type: application/x-www-form-urlencoded
Body: params=<URL-encoded JSON string of input variables>
```

Example — service with inputs `name` (String) and `quantity` (Integer):
```
params={"name":"Widget A","quantity":5}
```

> **Common mistakes:**
> - Sending `Content-Type: application/json` returns **HTTP 405**. Always use `application/x-www-form-urlencoded`.
> - Sending `{"params": "{...}"}` as a JSON body triggers `CWTBG0543E: The variable 'params' does not exist` unless the service actually has an input variable literally named `params`. The JSON object inside the `params=` form field must use the real variable names from the I/O contract.
> - Sending individual input variable names as separate form fields (i.e. `name=Widget+A&quantity=5`) does **not** work — all input variables must be nested inside a single `params` JSON string.

**Responses:**
- `200` — successful invocation. Output variables are inside `data.data` in the response JSON.
- `400` — expired CSRF token **or** invalid input. Distinguish by checking the response body:
  - `CWTBG0543E` ("The variable 'X' does not exist"): input error. **On BAW 26.x this also fires when an undeclared variable name is passed in `params` — BAW 26.x strictly rejects unknown fields; BAW 8.6/v21 silently ignores them.** If you are running a test case that sends extra/undeclared fields, treat this as a `FAIL` with the note "BAW 26.x rejects undeclared input variables."
  - `CWTBG0022E` ("callerTaskId or callerModelId was required"): the service is `process_embedded`, not directly startable. Re-classify and use the process fallback.
  - No `errorNumber` present: likely an expired CSRF token — re-authenticate and retry once.
- `401`/`403` — authentication or authorisation failure.
- `404` — service not found or not directly startable.
- `500` — server error.

**Response shape (success):**
```json
{
  "status": "200",
  "data": {
    "serviceStatus": "end",
    "data": {
      "outputVar1": "value",
      "outputVar2": 42
    }
  }
}
```

**Response shape (error):**
```json
{
  "status": "error",
  "Data": {
    "errorNumber": "CWTBG0543E",
    "errorMessage": "CWTBG0543E: The variable 'params' does not exist.",
    "status": "error"
  }
}
```

> **Common mistake:** Sending `{ "params": "{...}" }` triggers `CWTBG0543E` unless the service actually has an input variable named `params`. Always use the real variable names from the I/O contract.

---

## Process Fallback Endpoints

### `POST /bpm/processes` — Process fallback start

**Start a new process instance (use only when service is process-embedded)**

```
POST {BAW_BASE_URL}/bpm/processes
  ?model=<process_model_name>
  &container=<app_acronym>
  &version=<snapshot_acronym>
BPMCSRFToken: {BAW_CSRF}
Cookie: {BAW_SESSION}                       [on-prem/containers]
  — or —
Authorization: Bearer <zen_token>           [CP4BA]
Content-Type: application/json
Body: { "input": [ {"name": "<var>", "data": <value>} ] }
```

**Responses:**
- `201` — instance created. Capture `id` from the response as `{process_id}`.
- `400` — invalid parameters or missing required variables.
- `403` — caller is not authorised to start this process.
- `409` — process model not found in the specified snapshot.
- `500` — server error.

---

### `GET /bpm/processes/{process_id}` — Poll process state

```
GET {BAW_BASE_URL}/bpm/processes/{process_id}
  ?optional_parts=data
BPMCSRFToken: {BAW_CSRF}
Cookie: {BAW_SESSION}                       [on-prem/containers]
  — or —
Authorization: Bearer <zen_token>           [CP4BA]
```

Poll every 3 seconds for up to 30 seconds. Stop when `state` is `finished`, `stopped`, or `terminated`.

**Note on field names:** The `/bpm` API returns `state` (not `status`) with values `finished`, `stopped`, `terminated`, `running`, `suspended`, `did_not_start`. The `/rest/bpm/wle/v1` API returns `status` and uses `end` for completion. Do not mix up these conventions when asserting the final state. Valid `optional_parts` values for this endpoint are `data` and `actions` — `variables` is not valid.

**Responses:**
- `200` — instance retrieved.
- `403` — not authorised.
- `404` — instance not found.
- `500` — server error.

---

## Discovery Endpoints

### `GET /ops/docs`

**Discover all available OPS REST API paths and their parameter schemas**

```
GET {BAW_BASE_URL}/ops/docs
BPMCSRFToken: {BAW_CSRF}
```

Returns a Swagger 2.0 JSON document. Use `info.version` to determine the server version and `paths` keys to confirm which endpoints are available before calling them.

### `GET /ops/std/bpm/containers/{container}/versions`

**Check whether an app is deployed and find its active snapshot**

```
GET {BAW_BASE_URL}/ops/std/bpm/containers/{container}/versions
BPMCSRFToken: {BAW_CSRF}
Cookie: {BAW_SESSION}
```

Returns list of snapshots with `active`, `status`, and `version` (snapshot acronym) fields. If the container is not found (404), the app is not deployed.

### `GET /bpm/docs`

**Discover available BPM REST API paths on this server version**

```
GET {BAW_BASE_URL}/bpm/docs
BPMCSRFToken: {BAW_CSRF}
Cookie: {BAW_SESSION}
```

Returns a Swagger 2.0 JSON. Use `info.version` to confirm the BPM API version and check whether `/automationservices` and `/exposed-processes` paths are present.

### `GET /bpm/exposed-services?type=rest`

**List all exposed REST Automation Services**

```
GET {BAW_BASE_URL}/bpm/exposed-services?type=rest
BPMCSRFToken: {BAW_CSRF}
Cookie: {BAW_SESSION}
```

Returns `exposed_services` array. Each entry has `name`, `container`, and `definitionUrl` (link to the service's OpenAPI spec). Use `definitionUrl` to retrieve the exact endpoint path and input/output schema.

### `GET /bpm/exposed-processes`

**List processes exposed to start (used for process-embedded fallback)**

```
GET {BAW_BASE_URL}/bpm/exposed-processes
  ?container=<app_acronym>
BPMCSRFToken: {BAW_CSRF}
Cookie: {BAW_SESSION}
```

---

## Session management

- The session from `POST /ops/system/login` is valid for both `/ops/…` and `/bpm/…` calls.
- **On-prem/containers:** Send `BPMCSRFToken: {BAW_CSRF}` header and the `LtpaToken2`/`JSESSIONID` cookies on every request after login.
- **CP4BA:** Send `Authorization: Bearer <zen_token>` and `BPMCSRFToken: {BAW_CSRF}` on every request. No cookies needed.
- **401 on any endpoint:** Re-authenticate once and retry. If retry fails, stop and ask the user.
- **400 on `/rest/bpm/wle/v1/service/...`:** Check the response body. If `errorNumber` is absent or unrelated to the input, the CSRF token has expired — re-authenticate, get a new `{BAW_CSRF}`, and retry the call once.
- **403 on mutating calls:** Verify `BPMCSRFToken` header is present. Re-read the token from the login response and retry once.
