---
name: test-baw-service-flows
description: "Generate and execute automated tests for IBM BAW Service Flows. Phase A discovers the Service Flow, reads its input/output contract, and produces a structured test suite covering happy path, error paths, and boundary conditions. Phase B invokes the Service Flow — preferring the exposed Automation Service OpenAPI endpoint, falling back to direct service start, then to a process fallback — and returns a structured test report. Use when the user says 'test this service flow', 'generate tests for my service', 'validate my integration service', 'run service flow tests', 'test the automation service', or wants to test a BAW integration service without building a test harness manually. Also use proactively when a user shares a Service Flow and asks if it works, wants to verify inputs and outputs, or asks how to test before going to production."
license: Apache-2.0
compatibility: "IBM BAW 22.x and later; IBM CP4BA 22.x and later"
allowed-tools:
  - Read
  - Edit
  - Bash
metadata:
  version: "1.0.0"
  display_name: Test BAW Service Flows
  short_description: Generate and execute automated test suites for IBM BAW Service Flows against live BAW and CP4BA environments.
  author: IBM BAW Team
---

# Test BAW Service Flows

Generate comprehensive test suites for IBM BAW Service Flows and execute them against a live environment, capturing structured pass/fail results usable for regression tracking.

| Phase | What it does |
|---|---|
| **A — Generation** | Discover the Service Flow and read its I/O contract, then produce a test suite covering happy path, error paths, and boundary conditions. |
| **B — Execution** | Invoke the Service Flow with each set of test inputs, capture the synchronous output or error, assert against expected values, and return a structured report. |

---

## Execution mode

The skill uses MCP when relevant tools are present; REST is the fallback.

- **Phase A:** If Authoring MCP tools are present → use MCP for service flow discovery. If absent → use REST per the steps in `references/SERVICE_FLOW_DISCOVERY.md`.
- **Phase B:** Use the first available invocation path (see Priority Order below). The Phase A login session (if it exists) is still valid.

### CP4BA URL — resolve before the first API call

When the user provides a CP4BA URL (contains `cpd-` or ends without a port), determine the environment type from the URL path segment **and any context the user has already provided** — do not probe blindly:

| Signal | Type | Action |
|---|---|---|
| Path segment `/bas` | Workflow Authoring — has integrated playback server | Proceed directly using the BAS playback server — do not ask the user if they have a runtime. See Step 0 in `references/SERVICE_FLOW_DISCOVERY.md` for the full procedure. |
| Path segment `/baw-<name>` | Workflow Runtime | Proceed with authentication |
| User stated it is an authoring environment (any phrasing) | Workflow Authoring | Set `{BAW_BASE_URL}` to `https://<host>/bas` and proceed as Workflow Authoring. Do not ask the user to clarify. |
| User stated it is a runtime environment (any phrasing) | Workflow Runtime | Ask for the runtime path (for example, `/baw-<instance>`) if not already in the URL |
| No path segment, no prior context | Unknown | Probe `GET <url>/bas/ops/std/bpm/servers/workflow`. If `servers: []` → use BAS playback. If `servers: [...]` → ask which runtime. Only ask the user if the probe also fails. |

> **Prior context takes precedence over URL inspection.** If the user has already described the environment type earlier in the conversation, treat that as authoritative and do not ask again. Only fall back to asking when neither the URL path nor the conversation provides a signal.

See `references/BAW_CONNECTION.md` for the full authentication procedure for each environment type.

---

## Semantic operations

| Operation | Phase | Transport | What it does |
|---|---|---|---|
| `discover_service_flows` | A | MCP / REST fallback | List Service Flows in a process app and their exposure type |
| `get_service_flow_contract` | A | MCP / REST fallback | Read the I/O variable types, required fields, and error outputs |
| `login` | A / B | REST only | `POST /ops/system/login` — obtain CSRF token and session |
| `invoke_automation_service` | B | REST | `POST /automationservices/rest/{app}/{service}` via the generated OpenAPI contract |
| `invoke_service_direct` | B | REST | `POST /rest/bpm/wle/v1/service/{serviceId}?action=start` |
| `start_process_fallback` | B | REST | `POST /rest/bpm/wle/v1/process?action=start&bpdId=<id>&processAppId=<id>` |
| `get_process_result` | B | REST | `GET /rest/bpm/wle/v1/process/{piid}?parts=data,variables` |

---


## Credentials

Never prompt the user for credentials. Credentials are only needed when making a REST call.
When a REST call is about to be made, read `references/CREDENTIAL_HANDLING.md` and follow it — it will read credentials from `.env` automatically, and only prompt the user if a value is missing from that file. Do this once per session only.

---
## Phase A — Test Suite Generation

Full discovery protocol is in `references/SERVICE_FLOW_DISCOVERY.md`. Follow it step-by-step.

### Resolve unknowns before generating

Resolve in this order — do not announce step names to the user, just act.

1. **Authenticate.** Follow `references/BAW_CONNECTION.md`. On CP4BA: obtain a Zen token via `GET /v1/preauth/validateAuth`, then exchange it for a CSRF token via `POST {BAW_BASE_URL}/ops/system/login`. Both the authoring host (`/bas`) and the runtime host (`/baw-<instance>`) require separate tokens — obtain both if you need to export a TWX from authoring while running tests on the runtime. Use **Python stdlib `urllib`** for all HTTP calls — never `curl` or PowerShell (see `references/BAW_CONNECTION.md` for the cross-platform pattern).

2. **Identify the Service Flow.** Call **both** exposed-item endpoints — they list different things on CP4BA:
   - `GET {BAW_BASE_URL}/rest/bpm/wle/v1/exposed/process` — BPMN processes and some service types
   - `GET {BAW_BASE_URL}/rest/bpm/wle/v1/exposed/service` — Ajax-exposed services (integration Service Flows appear here on CP4BA, not in `/exposed/process`)

   Do not call `/bpm/exposed-processes` — it returns 404 on CP4BA runtimes. If neither endpoint returns integration service flows for the target app, proceed to TWX export (see `references/SERVICE_FLOW_DISCOVERY.md` Step 6).

3. **Determine exposure type.** From the TWX XML for each service flow:
   - `isAjaxExposed=true` **and** `isSecured=false` → **startable** (direct WLE v1 invocation works)
   - `isAjaxExposed=true` **and** `isSecured=true` → **process_embedded** (requires `callerModelId`; invoke via parent process)
   - `isAjaxExposed=false` → **process_embedded** (direct invocation blocked with HTTP 401 `CWTBG0549E`)
   - BAW 21+ and published as Automation Service → **automation_service** (preferred)

   Record `exposure_type` in the test suite metadata. Full detection procedure including BAW version check is in `references/SERVICE_FLOW_DISCOVERY.md`.

4. **Read the I/O contract.** Retrieve the full input variable list (names, types, required flag, default values) and the output variable list (names, types). Also read any declared error outputs or fault types. Ask the user:
   > *"I found [Service Flow name] in [app] — it accepts [N input fields] and returns [M output fields]. Are there any specific error scenarios, boundary values, or input combinations you especially want covered?"*

5. **Ask about execution:**
   > *"Once the test suite is ready, would you like me to run it against your BAW server straight away, or just generate the file for review first?"*

### Generating the tests

1. **Analyse the I/O contract.** Follow `references/SERVICE_FLOW_TEST_GENERATION.md`. The goal is to enumerate every meaningful input combination: the minimal valid happy-path call, each documented error condition, and boundary values for any numeric, string-length, or date constraint.

2. **Generate the test suite.** Use the format in `references/SERVICE_FLOW_TEST_SUITE_FORMAT.md` exactly. Every test case must have a clear ID, human-readable name, path label, input data, and expected output or error assertion. Produce at minimum:
   - One happy-path test per service flow — **unless the user explicitly requests a restricted scope** (for example, "only error paths", "only validation tests"). If the user has explicitly excluded the happy path, skip it and record `"scope_note": "happy-path excluded at user request"` in the test suite metadata.
   - At least one error-path test **for the same service flow**, if the service allows it — meaning it has any required input, declared fault, or input validation that can be triggered. A service flow "allows" an error path if omitting a required field, supplying an out-of-range value, or using a wrong variable name produces an error response. Only skip the error-path test if the I/O contract has no required fields, no declared faults, and no validatable constraints whatsoever.
   - Boundary tests for any numeric or string-length constraint — unless the user has restricted scope to exclude them.

3. **Output.** Create the directory `output/<app-acronym>/` if it does not exist, then write two files into it:
   - `output/<app-acronym>/<app-acronym>-sf-test-suite.json` — machine-executable test suite (input to Phase B).
   - `output/<app-acronym>/<app-acronym>-sf-test-suite.md` — human-readable version for review.

   Show the summary table (test ID, name, path, inputs used) and ask if the user wants to adjust anything before execution.

---

## Phase B — Test Execution

Full execution protocol is in `references/SERVICE_FLOW_EXECUTION.md`. Key endpoints:

- **Direct start:** `POST /rest/bpm/wle/v1/service/{serviceId}?action=start` with `Content-Type: application/x-www-form-urlencoded` and body `params=<JSON>`.
- **Process start (fallback):** `POST /rest/bpm/wle/v1/process?action=start&bpdId=<bpdId>&processAppId=<appId>` with `params=<JSON>`.
- **Process poll:** `GET /rest/bpm/wle/v1/process/{piid}?parts=data,variables` — **not** `/bpm/processes/{id}` (that path returns all-null fields on CP4BA runtimes).

> **Isolation guarantee.** Phase B only ever creates new service invocations or process instances for testing. It never touches, modifies, or terminates any pre-existing instance. Test invocations are synthetic and all input data is test data only — never substitute real personal data, production record IDs, or live integration credentials.

### Phase B entry — confirm in order

1. **Resolve transport.** Use the priority order below (decided once, applied to all tests).
2. Is there a test suite file to run? If not, offer to go back to Phase A.
3. Which tests should run — all, a specific subset, or just the happy path first?
4. **Confirm environment.** Use the appropriate message based on the target:

   **BAS playback server** (detected in Phase A, or URL contains `/bas`):
   > *"⚠️ I'll invoke the Service Flow on the BAS integrated playback server. Any external side effects the service triggers (database writes, REST calls to real APIs) will be real. Do you want to continue? (yes / no)"*

   **Runtime / unknown:**
   > *"⚠️ Running these tests will invoke the Service Flow on your BAW server. It is strongly recommended to run against a non-production environment to avoid unintended side effects. Do you want to continue? (yes / no)"*

   Wait for explicit "yes" before starting.
5. **REST only — authenticate** (skip if session from Phase A is still valid): read `references/CREDENTIAL_HANDLING.md` to resolve credentials, then authenticate. Use **Python stdlib `urllib`** for all HTTP calls — never `curl` or PowerShell. For CP4BA: obtain a Zen token via `GET /v1/preauth/validateAuth`, then a CSRF token via `POST {BAW_BASE_URL}/ops/system/login`. For on-premises: use Basic auth on `POST {BAW_BASE_URL}/ops/system/login` and store the `{BAW_CSRF}` and `{BAW_SESSION}` cookies. See `references/BAW_CONNECTION.md` for the full authentication flow.
6. **Production warning.** If the server URL contains `prod`, the user says it is production, or it matches a known production hostname, add:
   > *"This appears to be a production server. Invoking service flows here may trigger real integrations (email, database, external APIs). Are you sure you want to continue on production?"*
   Wait for explicit confirmation.

### Priority order for service invocation

Check in this order and use the first path that is available. The BAW version (detected in Phase A via `/rest/bpm/wle/v1/systems`) determines which paths are viable:

| Priority | Path | When to use |
|---|---|---|
| 1 | **Exposed Automation Service** | BAW 21+ only. Service Flow is exposed as an Automation Service with a generated OpenAPI contract. Use `POST /automationservices/rest/{appAcronym}/{serviceName}` with the JSON body from the test case `input.data`. Skip this path entirely on BAW 8.6. |
| 2 | **Direct service start** | Service Flow is directly startable (`isAjaxExposed=true`). Use `POST /rest/bpm/wle/v1/service/{serviceId}?action=start` with `Content-Type: application/x-www-form-urlencoded` and body `params=<JSON>`. |
| 3 | **Process fallback** | Service Flow is only accessible through an exposed process (`isAjaxExposed=false`). Use `POST /bpm/processes?model=<model>&container=<container>&version=<version>` then poll `GET /bpm/processes/{processId}?optional_parts=data,variables` for the output. |

Record which invocation path was used in each test result — this is important diagnostic information.

### Per-test execution sequence

For each test case, follow this sequence:

1. **Invoke the service** using the resolved invocation path with `test_case.input.data`.
   - On success: capture the response body as the actual output.
   - On 4xx/5xx: mark the test `ERROR`, record the HTTP status and a plain-language translation of the response body, and move to the next test.

2. **Assert the output.** Compare every key-value pair in `expected_output` against the actual response. For `expected_error`, check that an error was returned and that the error code or message matches. Comparison rules follow `references/SERVICE_FLOW_EXECUTION.md`.

3. **Record the result.** Follow `references/SERVICE_FLOW_RESULT_FORMAT.md`. A test passes only when all output assertions pass. A test fails when any assertion fails. A test errors when the invocation itself fails.

4. **Present the report.** After all tests complete, present a summary table (test ID, name, result, duration) followed by plain-language detail for any FAIL or ERROR. Never show raw JSON payloads — translate them into one sentence describing what failed and what to investigate.

**Execution rules:**
- Run tests in order unless the user specifies otherwise.
- If an invocation fails with 4xx, mark that test `ERROR` and continue — do not abort the suite.
- If an assertion fails, record the mismatch and continue checking the remaining assertions in the same test before marking it `FAIL`.
- Never halt the suite; every test is independent.

---

## Disambiguation

**Phase A vs Phase B:** If the user says "test this service flow" with no prior test suite, start at Phase A. If they provide a test suite file, go to Phase B directly.

**Service Flow vs Process:** This skill is for Service Flows only. If the artifact is a BPMN process (has user tasks, a task sequence), use the `generate-baw-tests` skill instead.

**Invocation path selection:** The invocation path is resolved once at Phase B entry based on the exposure type recorded in the test suite metadata. If the metadata is absent, attempt the Automation Service path first, then fall back through the priority order.

---

## Output files produced

All files are written to `output/<app-acronym>/`. Create this directory if it does not exist.

| File | When | Contents |
|---|---|---|
| `output/<acronym>/<acronym>-sf-test-suite.json` | End of Phase A | Machine-executable test suite (input to Phase B) |
| `output/<acronym>/<acronym>-sf-test-suite.md` | End of Phase A | Human-readable version for review and sign-off |
| `output/<acronym>/<acronym>-sf-test-results.json` | End of Phase B | Pass/fail results for each test case |

All formats are fully specified in `references/SERVICE_FLOW_TEST_SUITE_FORMAT.md` and `references/SERVICE_FLOW_RESULT_FORMAT.md`.

---

## Boundaries

In scope: Service Flow test generation (I/O contract analysis, happy path, error paths, boundary conditions), service invocation via Automation Service, direct service start, or process fallback, output assertion, structured test reporting. **Includes testing against the BAS integrated playback server** — no deployed snapshot is required when the user points to a Workflow Authoring (`/bas`) environment.

Out of scope — do not attempt:
- **Deploying or importing a process app** — on a Workflow Runtime, the app must already be deployed and its snapshot active before tests can run. If missing, direct the user to the `baw-deployment-manager` skill. On a BAS playback server, no deployment is needed. Do not attempt to import a TWX as part of this skill.
- **BPMN Process testing** — use `generate-baw-tests`.
- **Coach/UI field validation** — use `generate-baw-tests`.
- **Case application testing** — out of scope for both skills.
- **Federated multi-system orchestration** — each test targets a single BAW system.
- **Authoring or modifying Service Flow definitions** — use `service-artifact-generation`.
