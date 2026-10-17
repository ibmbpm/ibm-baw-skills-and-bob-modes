# Service Flow Discovery — Protocol

This file contains the detailed instructions for **Phase A discovery** of the `test-baw-service-flows` skill.
It covers how to find a Service Flow, read its input/output contract, and determine the invocation path to use in Phase B.

---

## Table of contents

1. [What is a Service Flow](#1-what-is-a-service-flow)
2. [Discovery via Authoring MCP](#2-discovery-via-authoring-mcp)
3. [Discovery via REST fallback](#3-discovery-via-rest-fallback)
4. [Reading the I/O contract](#4-reading-the-io-contract)
5. [Determining the invocation path](#5-determining-the-invocation-path)
6. [Discovery checklist](#6-discovery-checklist)

---

## 1. What is a Service Flow

A Service Flow (also called a Service Component in some BAW versions) is a synchronous integration service in IBM BAW. It accepts a set of typed input variables, executes internal logic (REST calls, database queries, script tasks, decision services), and returns typed output variables. Unlike a BPMN process, it has no user tasks and no task claim/complete lifecycle — it runs start-to-finish in a single synchronous call.

A Service Flow can be:

| Exposure type | Description | Phase B invocation |
|---|---|---|
| **Automation Service** | Published as a managed API with a generated OpenAPI specification. Callable via `/automationservices/rest/{app}/{service}`. | **Preferred** |
| **Directly startable** | The Service Flow is marked as startable and can be invoked via `/rest/bpm/wle/v1/service/{serviceId}?action=start`. | **Second choice** |
| **Process-embedded** | The Service Flow runs only when triggered by a BPMN process; there is no direct callable endpoint. Must be exercised via an exposed process. | **Fallback** |

Always record the exposure type in the test suite `metadata.exposure_type` field so Phase B does not need to re-discover it.

---

## 2. Discovery via Authoring MCP

If Authoring MCP tools are present, use them as follows:

1. Call the list-services (or equivalent) tool with the process app acronym to retrieve the list of Service Flows in that app. Present the list if more than one matches the user's description.

2. Once a specific Service Flow is confirmed, call the get-service (or equivalent) tool to retrieve:
   - `serviceId` — the runtime ID for direct invocation.
   - `serviceType` — indicates whether this is an Integration Service, General System Service, or Ajax Service (relevant for invocation constraints).
   - `inputParameters` — array of variable objects: `name`, `type`, `required`, `defaultValue`.
   - `outputParameters` — array of variable objects: `name`, `type`.
   - `faultOutputs` — any declared fault/error outputs.
   - `exposureType` — `automation_service`, `startable`, or `process_embedded`.
   - `openApiUrl` — present only when `exposureType` is `automation_service`.

3. If `exposureType` is `automation_service`, also retrieve the OpenAPI specification URL so Phase B can construct the correct request path.

---

## 3. Discovery via REST fallback

If Authoring MCP tools are absent, use REST.

### Step 0 — Detect the BAW version and environment type

Before searching for service flows, establish the BAW version and environment type.

```
GET {BAW_BASE_URL}/rest/bpm/wle/v1/systems
  Headers: BPMCSRFToken: {BAW_CSRF}, Cookie: {BAW_SESSION}
           — or — Authorization: Bearer <zen_token> (CP4BA)
```

Read `data.systems[0].version` from the response. Store this as `{BAW_VERSION}` for use in subsequent steps.

**Version implications:**
- `{BAW_VERSION}` starts with `8.6` → This is BAW 8.6. The Automation Services endpoint (`/automationservices/rest/...`) **does not exist** on this version — skip Step 4 entirely and proceed directly to Step 5 (exposed processes) then Step 6 (TWX-based discovery). Do not probe the Automation Services endpoint on BAW 8.6.
- `{BAW_VERSION}` starts with `21`, `22`, `23`, `24`, `25`, or `26` → Automation Services may be available. Proceed through Steps 4–6 in order.

Then establish the environment type:

```
GET {BAW_BASE_URL}/ops/std/bpm/servers/workflow
  Headers: BPMCSRFToken: {BAW_CSRF}, Cookie: {BAW_SESSION}
           — or — Authorization: Bearer <zen_token> (CP4BA)
```

**If `servers` is a non-empty array:** This is a Workflow Runtime — proceed with the discovery steps below.

**If `servers` is an empty array (`{"servers": []}`):** This is a Workflow Authoring (BAS) environment. BAS has a built-in **playback server** — an embedded runtime used for in-development testing. Service flows can be invoked against it **without deploying a snapshot to a separate runtime**. Proceed directly using the playback server — do **not** ask the user whether they have a runtime. Inform them instead:

> *"This is a Workflow Authoring environment with no connected runtime. I'll run the tests against the integrated playback server — no deployment needed."*

Only ask about an external runtime if the user explicitly says they want to test against a deployed snapshot rather than the tip branch.

**BAS playback server — API paths:**

> ⚠️ **`/bpm/dev/` prefix applies to discovery endpoints only — NOT to invocation.** Tested on BAW 26.x (CP4BA): `POST /bpm/dev/rest/bpm/wle/v1/service/{id}?action=start` returns HTTP 404. Service invocation must use the standard path without the playback prefix:

| Action | Correct BAS path |
|---|---|
| Invoke service (startable) | `{BAS_BASE_URL}/rest/bpm/wle/v1/service/{id}?action=start` — **no `/bpm/dev/`** |
| Start process (fallback) | `{BAS_BASE_URL}/rest/bpm/wle/v1/process?action=start` — **no `/bpm/dev/`** |
| Discover exposed services | `{BAS_BASE_URL}/rest/bpm/wle/v1/exposed/service` — **no `/bpm/dev/`** (returns 404 with prefix) |
| Discover exposed processes | `{BAS_BASE_URL}/rest/bpm/wle/v1/exposed/process` — **no `/bpm/dev/`** |

The `/bpm/dev/` prefix was documented in IBM docs as the playback path, but live testing shows it is not honoured on CP4BA BAS 26.x for these endpoints. Use `{BAS_BASE_URL}` as the base for all calls.

Authentication uses the same Zen token flow as the BAS host (already obtained). No separate login is required.

> **Scope of the playback server:** The playback server runs the **tip branch** of the app currently open in Workflow Designer — it does not require a snapshot to be activated. Changes made in the designer are reflected immediately. This makes it ideal for testing service flows during development. Side effects (database writes, external REST calls) are still real — warn the user accordingly.

> **Playback server is not a substitute for a runtime test:** Results on the playback server reflect the current uncommitted tip, not a specific snapshot. For regression testing against a pinned version, a deployed runtime snapshot is required.

For the playback server, use `{BAS_BASE_URL}` as the base for all subsequent steps — **do not** prepend `/bpm/dev/` (see path table above). All discovery and invocation steps apply unchanged.

If the user explicitly requests testing against a deployed runtime, ask for the URL and proceed as normal.

**CP4BA URL patterns to know:**

| URL pattern | Environment type |
|---|---|
| `https://<host>/bas/...` | Workflow Authoring (BAS) — has playback server at `/bas/bpm/dev/...` |
| `https://<host>/baw-dev/...` | Workflow Runtime — execution-capable |
| `https://<host>/baw-aut/...` | Workflow Runtime (alternate naming) |
| `https://<host>:<port>/...` | On-premises BAW — always a runtime |

### Step 1 — Verify the app is deployed

After confirming the environment is a runtime, verify the process app is present:

```
GET {BAW_BASE_URL}/ops/std/bpm/containers/{app_acronym}/versions
  Headers: BPMCSRFToken: {BAW_CSRF}, Cookie: {BAW_SESSION}
```

If the app is not listed, the user must deploy it first. Do not attempt to import a TWX on behalf of the user as part of this skill — importing is the responsibility of the `baw-deployment-manager` skill. Tell the user:
> *"The app '[name]' does not appear to be deployed on this server. Please deploy it first — you can use the `baw-deployment-manager` skill or the Process Admin Console to install the snapshot, then come back here to run the tests."*

**TWX version mismatch (if the user attempts a manual import and it fails with `CWTBG0737E`):**
Check the server API version from `/ops/docs` → `info.version` (for example, `8.6.2.21021` = BAW v21) and compare it against the `buildVersion` attribute in the TWX's `META-INF/package.xml` (for example, `buildVersion="8.6.12.26030"` = BAW 26.0.3). If the TWX version is newer than the server version, tell the user:
> *"The TWX was exported from BAW [TWX version] but this server is running BAW [server version]. A TWX cannot be imported into an older server. You need a server running BAW [TWX version] or later."*

**App exists on the runtime but not on Workflow Authoring (BAS):**
An app can be deployed directly to the runtime without going through Workflow Authoring — for example, by importing a TWX file directly via the Process Admin Console. In this case, the app is not available on the BAS host and a TWX cannot be exported from there. When the runtime confirms the app is deployed but the BAS export returns `CWTBG0624E: Container does not exist`:
> *"This app was deployed directly to the runtime and does not exist in Workflow Authoring. I can't export the TWX from BAS to read its I/O contract. Do you have a local `.twx` file for this app? If so, point me to it and I'll extract the service flow contract from it directly."*
If the user cannot provide a local TWX, offer to probe startability without a contract: the service IDs can be guessed from the `/exposed/service` endpoint and probed live, but typed test case generation will not be possible.

**App exists on Workflow Authoring but not on the runtime:**
The snapshot was never installed on this BAW runtime. The TWX can be exported from BAS for contract analysis, but service invocations fail at Phase B. Tell the user:
> *"I can read the service flow contract from Workflow Authoring, but this app isn't installed on the runtime (`{BAW_BASE_URL}`). Phase A test generation will work, but Phase B execution will fail until the snapshot is deployed. Would you like to proceed with generation only, or deploy the app first?"*

### Step 2 — Authenticate

Call `POST {BAW_BASE_URL}/ops/system/login` (see `baw-rest.md` for full request format). Store `{BAW_CSRF}` and `{BAW_SESSION}`.

### Step 3 — List exposed services

Use **both** WLE v1 exposed-item endpoints — `/exposed/process` and `/exposed/service` are separate on CP4BA runtimes and must each be called:

```
GET {BAW_BASE_URL}/rest/bpm/wle/v1/exposed/process
  Headers: BPMCSRFToken: {BAW_CSRF}, Cookie: {BAW_SESSION}
           — or — Authorization: Bearer <zen_token> (CP4BA)
```

```
GET {BAW_BASE_URL}/rest/bpm/wle/v1/exposed/service
  Headers: BPMCSRFToken: {BAW_CSRF}, Cookie: {BAW_SESSION}
           — or — Authorization: Bearer <zen_token> (CP4BA)
```

> **CP4BA behaviour:** On CP4BA runtimes, integration Service Flows do **not** appear in `/exposed/process` — they are only returned by `/exposed/service`. Always call both endpoints and merge the results. Do not skip `/exposed/service` because `/exposed/process` returned results.

From `/exposed/process`: Items with `type=service` are candidate Service Flows. Items with `type=process` are BPMN processes.

From `/exposed/service`: Items with `subtype=url` that belong to system apps (Process Portal, Workplace, Heritage Process Portal) are Coach/UI services — ignore them. Items from user-authored process apps with `subtype=url` are Ajax-exposed services worth probing. Items with `subtype=dashboard` are portal dashboards — ignore them.

**Important:** Neither endpoint is a complete picture on its own. The IDs returned are only confirmed as startable after a live probe (see Step 6). The TWX is still required for the I/O contract.

If both endpoints return no items from the target app, proceed directly to Step 6 (TWX export) to discover service flows from the artifact.

If `{BAW_VERSION}` starts with `8.6`, skip Step 4 — the `/automationservices` endpoint is not present and will always 404.

### Step 4 — Check for Automation Services (BAW 21+ only)

```
GET {BAW_BASE_URL}/bpm/exposed-services?type=rest&optional_parts=definition
  Headers: BPMCSRFToken: {BAW_CSRF}, Cookie: {BAW_SESSION}
```

The `optional_parts=definition` parameter inlines the full OpenAPI spec as the `definition` field on each entry, eliminating a second HTTP call. Each entry in the `exposed_services` array has `name`, `container`, `definitionUrl`, and (with `optional_parts=definition`) `definition` — the inline OpenAPI JSON/YAML string.

Search the `exposed_services` array for the Service Flow name or container acronym. If found:

1. Read the inline `definition` field directly (no separate fetch needed).
2. Parse the `paths` object to find the POST endpoint path — this is `metadata.automation_service_path` for Phase B.
3. Read `components/schemas` for input field names, types, and the `required` array. This is the I/O contract.

If `exposed_services` is an empty array (`[]`), or the `exposed_services` key is absent: no Automation Services are published. Fall through to Step 5.

> **Note on `/automationservices/rest`:** Directly calling `GET {BAW_BASE_URL}/automationservices/rest` without an app path returns an empty body or 404 on most BAW versions — it is not a directory listing. Always use `GET /bpm/exposed-services?type=rest` as the discovery endpoint.

### Step 5 — Check for exposed processes (if not found as Automation Service)

```
GET {BAW_BASE_URL}/bpm/exposed-processes
  ?container=<app_acronym>
  Headers: BPMCSRFToken: {BAW_CSRF}, Cookie: {BAW_SESSION}
```

Look for a process whose name matches or wraps the Service Flow. If found, record the process model name and container — this is the `process_embedded` exposure type.

### Step 6 — TWX export and direct startability check

Directly startable Service Flows are not reliably listed via REST discovery endpoints alone. The TWX export is the primary and most complete source for service flow IDs and I/O contracts on all BAW versions.

**TWX export — CP4BA: always try BAS first**

On CP4BA, the runtime export endpoint (`/baw-<instance>/ops/.../export`) is known to fail with `CWTBG0019E` (`errorVariableObjArr is null`) for many snapshots. This is not a configuration problem — it is a server-side bug on certain CP4BA runtime versions. **Do not spend time retrying or troubleshooting it.** Go straight to BAS:

```
GET https://<bas-host>/bas/ops/std/bpm/containers/{app_acronym}/versions/{snapshot_acronym}/export
  ?use_enhanced_filenames=true
  Authorization: Bearer <zen_token>
  BPMCSRFToken: <bas_csrf_token>
  Accept: application/zip, application/octet-stream, */*
```

> **Fix 1 — 406 Not Acceptable:** The export endpoint requires an explicit `Accept` header. Omitting it causes the server to return HTTP 406. Always include `Accept: application/zip, application/octet-stream, */*` on this request.

> **BAS may be on a different hostname from the runtime.** On CP4BA multi-cluster deployments, the BAS host (`<bas-host>`) and the BAW runtime host (`<runtime-host>`) are often on completely different subdomains — for example `baas.cp.fyre.ibm.com` vs `buis.cp.fyre.ibm.com`. They are not always the same base URL with different path segments. If `POST https://<runtime-host>/bas/ops/system/login` returns 404, ask the user:
> *"What is your Workflow Authoring (BAS) URL? It may be on a different host from the runtime — for example `https://cpd-demo.apps.bas-cluster.example.com`."*
> A separate Zen token is required for the BAS host: re-run `GET https://<bas-host>/v1/preauth/validateAuth` and `POST https://<bas-host>/bas/ops/system/login`.

The TWX content from BAS is identical to the runtime version — use it for discovery only; service invocations still target the runtime.

**TWX export — on-premises / standalone containers (runtime export):**

On non-CP4BA environments, use the runtime export directly:

```
GET {BAW_BASE_URL}/ops/std/bpm/containers/{app_acronym}/versions/{snapshot_acronym}/export
  ?use_enhanced_filenames=true
  Headers: BPMCSRFToken: {BAW_CSRF}, Cookie: {BAW_SESSION}
           Accept: application/zip, application/octet-stream, */*
```

If this returns `CWTBG0019E`, fall back to asking the user for a local `.twx` file.

**No `_Service Flow.*.xml` files found in the TWX:**

If the `objects/` directory of the extracted TWX contains no files matching `*_Service Flow.*.xml`, the app contains no Service Flows — only BPMN processes. Tell the user:
> *"No Service Flows were found in [app name]. It contains only BPMN processes — to test those, use the `generate-baw-tests` skill instead."*
Stop Phase A for this app.

**Analysing each `_Service Flow.*.xml` file found:**

> ⚠️ **`isAjaxExposed=true` does NOT guarantee direct startability.** If `isSecured=true` is also present, the service requires a `callerModelId` (a running process context). A direct call returns `CWTBG0022E`. Always check **both** flags together before classifying the exposure type — never rely on `isAjaxExposed` alone.

Classification rules from the XML:

| `isAjaxExposed` | `isSecured` | Preliminary classification |
|---|---|---|
| `false` | any | `process_embedded` — direct invocation blocked with `CWTBG0549E` |
| `true` | `true` | Candidate `startable` on BAS playback; `process_embedded` on runtime — **must confirm with a live probe** |
| `true` | `false` | Candidate `startable` — **must confirm with a live probe** |

> **BAS playback note:** On the BAS integrated playback server, `isSecured=true` does not always block direct invocation — live testing on BAW 26.x CP4BA shows that services with `isSecured=true` can return HTTP 200 on direct start. The XML flags are a guide only; the mandatory live probe below is the authoritative classification for all environments.

Extract `<processParameter>` elements to read input/output variable names and types (`parameterType` 1 = input, 2 = output).

**Mandatory live probe — confirm every candidate `startable` service:**

Do not record `exposure_type: startable` based on XML flags alone. Always probe on the runtime:

```
POST {BAW_BASE_URL}/rest/bpm/wle/v1/service/{serviceId}?action=start
  Content-Type: application/x-www-form-urlencoded
  Body: params={}
  Authorization: Bearer <zen_token>   [CP4BA]
  BPMCSRFToken: {BAW_CSRF}
```

> **Important:** Use `Content-Type: application/x-www-form-urlencoded` with a `params` form field whose value is a JSON string — not `application/json`. Sending a JSON body returns HTTP 405.

Probe results:

- **HTTP 200 or 400** (including input validation errors like `CWTBG0543E`): Service is directly startable. Record `exposure_type: startable`.
- **HTTP 400 with `CWTBG0022E`** ("callerTaskId or callerModelId was required"): `isSecured=true` was confirmed in practice. Record `exposure_type: process_embedded`.
- **HTTP 401 with `CWTBG0549E`**: `isAjaxExposed=false` confirmed. Record `exposure_type: process_embedded`.
- **HTTP 403 with `CWTBG0568E`** ("Service type must be AJAX or HUMAN"): This is a Coach/UI service (COACHFLOW), not an integration Service Flow. Out of scope — skip it.
- **HTTP 404**: The service ID is incorrect, or the snapshot is not active on this runtime. Verify via `GET /ops/std/bpm/containers/{app}/versions`.

---

## 4. Reading the I/O contract

Once the Service Flow is located, extract the following. The source of truth depends on exposure type:

### From an Automation Service OpenAPI spec

Download the OpenAPI JSON/YAML from `{openApiUrl}`. Read:

- `paths` — the POST endpoint and its `requestBody.content['application/json'].schema`.
- `components/schemas` — the input and output object schemas, with field names, types, and required arrays.
- Any `4xx` response schemas — these are the declared error outputs.

Record every input field as:
```json
{ "name": "fieldName", "type": "string|number|boolean|object|array", "required": true, "defaultValue": null }
```

### From a directly startable service (WLE v1 API)

The WLE v1 endpoint does not expose a schema endpoint. Extract the I/O contract from the process app TWX export:

1. Download the TWX (see Step 6 above; use the BAS host if the runtime export fails with `CWTBG0019E`).
2. Locate `objects/<ServiceName>_Service Flow.{UUID}.xml`.
3. **Primary source — `<processVariable>` blocks:** Search for `<processVariable>` elements. Each has `<name>`, `<type>`, and `<parameterType>` (1 = input, 2 = output). If `<processVariable>` elements are absent, proceed to the next source.
4. **Secondary source — `jsonData` → `ioSpecification`:** Extract the `<jsonData>` block, decode XML entities (`&lt;` → `<`), and parse as JSON. Read `ioSpecification.dataInput` and `ioSpecification.dataOutput` for parameter names and `itemSubjectRef` type references.
5. **Fallback — `tw.local` references:** If both sources above yield empty arrays (the `ioSpecification` is `{}`), search the `jsonData` string for all occurrences of `tw\.local\.(\w+)`. Each unique capture is a variable used by the service. Cross-reference against `dataInputAssociation` and `dataOutputAssociation` blocks in the JSON to classify as input or output. This is the last-resort approach when no formal schema is declared.
6. Look for `<error>` elements to capture declared fault outputs.

### From a process-embedded service

Read the process definition XML (`objects/<ProcessName>_BPD.xml`) to find the service task that calls the Service Flow. Extract the input/output variable mappings on that task. These become the test inputs and expected outputs.

---

## 5. Determining the invocation path

After discovery, record `exposure_type` in the test suite metadata using exactly one of these values:

| Value | Meaning |
|---|---|
| `automation_service` | Service is published as an Automation Service. Phase B uses `POST /automationservices/rest/...`. |
| `startable` | Service is directly startable. Phase B uses `POST /rest/bpm/wle/v1/service/{serviceId}?action=start`. |
| `process_embedded` | Service is only accessible via a process. Phase B uses `POST /bpm/processes` + poll. |

Also record:
- `service_id` — for `startable` path.
- `automation_service_path` — the OpenAPI-defined path for `automation_service`.
- `process_model` and `container` — for `process_embedded` path.
- `app_acronym` and `snapshot` — always required.

---

## 6. Discovery checklist

Before proceeding to test generation, verify:

- [ ] Environment confirmed as a Workflow Runtime **or** you are using the BAS playback server.
- [ ] Service Flow name confirmed with the user (do not guess).
- [ ] `serviceId` (or Automation Service path) recorded.
- [ ] All input variables listed with name, type, and required flag.
- [ ] All output variables listed with name and type.
- [ ] Error outputs / fault types listed (may be empty if none declared).
- [ ] `exposure_type` recorded as `automation_service`, `startable`, or `process_embedded`.
- [ ] App acronym and snapshot recorded.
