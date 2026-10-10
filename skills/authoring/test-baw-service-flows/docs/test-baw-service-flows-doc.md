# Test BAW Service Flows — Documentation

> Generate and execute automated tests for IBM BAW Service Flows — covering happy path, error paths, and boundary conditions — and return a structured pass/fail report, without requiring a manual test harness.

## Purpose

This skill automates end-to-end testing of IBM BAW Service Flows. It operates in two phases: **Phase A** discovers the target Service Flow, reads its input/output contract, and produces a structured test suite (JSON + Markdown); **Phase B** invokes the service against a live BAW environment with each set of test inputs, asserts the outputs, and delivers a plain-language results report. Use this skill whenever you want to validate an integration service before promoting to production, verify a change doesn't break an existing service contract, or quickly build regression coverage without writing test code manually.

## Setup and configuration

- **IBM BAW environment** — a live Workflow Runtime instance with the target process app snapshot deployed and activated. The skill cannot run against a Workflow Authoring (BAS/design-time) environment.
- **Credentials** — a BAW username and password (or a CP4BA IAM/Zen token) with permission to invoke the service. Credentials are used only to obtain a session token and are not stored beyond the session.
- **BAW Authoring MCP server** (optional) — if the IBM BAW Authoring MCP server is connected, the skill uses it for faster service discovery in Phase A. If absent, it falls back to the BAW REST API automatically — no manual configuration needed.
- **No additional packages or scripts required** — the skill has no Python scripts, Node dependencies, or local binaries to install.

## Compatibility

- **Workflow Runtime required** — the target BAW server must be a Workflow Runtime instance. CP4BA Workflow Authoring (`/bas` route) cannot execute service flows; the skill will stop and ask for a runtime URL if a BAS endpoint is detected.
- **Process app must be deployed** — the target snapshot must be installed and active on the server before testing. If it is missing, you must deploy it first (use the `baw-deployment-manager` skill or Process Admin Console).
- **Service Flows only** — this skill does not test BPMN processes with user tasks. For process/coach testing use the `generate-baw-tests` skill.
- **BAW 21+** — the Automation Service endpoint (`/automationservices/rest/...`) requires BAW 21 or later. On older versions the skill falls back to the direct-start or process-fallback invocation path automatically.

## Prompt examples

### Generate a full test suite for an Automation Service

**Prompt:**
> I have a Service Flow called `Calculate Premium` in the Insurance Quoting app (acronym IQ, snapshot IQV300). It's exposed as an Automation Service. Generate a complete test suite covering happy path, error paths, and boundary conditions.

**What to expect:** A `IQ-sf-test-suite.json` (machine-executable) and `IQ-sf-test-suite.md` (human-readable summary table) covering at minimum a happy-path test, a missing-required-field validation test, and boundary tests for any numeric constraints found in the OpenAPI spec.

---

### Run an existing test suite against a BAW server

**Prompt:**
> Here is my test suite — run all tests against `https://baw-dev.example.com:9443`. Username is `qauser`, password is `QApass2024!`.

_Before using this prompt, save your test suite as `IQ-sf-test-suite.json` and attach or reference it in the chat._

**What to expect:** A non-production confirmation prompt before any invocation, followed by a summary results table (test ID, name, result, duration) and plain-language detail for any FAIL or ERROR — no raw JSON payloads.

---

### Restrict generation to error paths only

**Prompt:**
> Generate tests only for the error scenarios of the `Validate Shipment Address` service flow in the Logistics app (acronym LOG, snapshot LOGV12). I only care about what happens when bad inputs are provided — skip the happy path.

**What to expect:** A test suite containing only `SFTC-VAL-*` and `SFTC-ERR-*` test cases, with a note in the metadata that happy-path coverage was excluded at user request.

---

### Generate tests and run the happy path only on a production server

**Prompt:**
> Generate tests for the `Get Account Balance` service flow in the Banking Services app (acronym BS, snapshot BSV5) and then run only the happy-path test. The server is `https://baw-prod.bank.internal:9443`.

**What to expect:** Phase A generates the full test suite; before Phase B starts the skill issues an explicit production-server warning (URL contains `prod`) and waits for your confirmation before invoking anything on the live server.

---

### Test a service flow that is only accessible through an exposed process

**Prompt:**
> My `Calculate Tax` service flow can't be called directly — it only runs inside the `Invoice Processing` process (acronym IP, snapshot IPV1). Can you still test it?

**What to expect:** The skill records `process_embedded` as the exposure type, starts a new `Invoice Processing` instance per test case, polls for completion, and captures the output variables — producing a full test report without requiring a direct service endpoint.

---

### Generate tests without an MCP server connected (REST mode)

**Prompt:**
> Generate tests for the `Credit Risk Score` service flow in the Lending app (acronym LND, snapshot LNDV8). I don't have the BAW MCP server connected right now.

**What to expect:** The skill asks for your BAW server URL and credentials, then uses the BAW REST API for all discovery — authenticating, checking for Automation Services, and reading the OpenAPI contract — before generating `LND-sf-test-suite.json` and `LND-sf-test-suite.md`.

---

### Run a specific subset of test cases from an existing suite

**Prompt:**
> I already have my test suite from last week. Run only `SFTC-ERR-001` and `SFTC-BND-002` from it against `https://baw-uat.example.com:9443`.

_Attach or reference your existing test suite file._

**What to expect:** Only the two named test cases are executed; all others are marked `SKIPPED` in the results file. The summary table shows all tests with their status.

---

### Minimal / ambiguous input — skill asks for clarification

**Prompt:**
> Test my claims service flow.

**What to expect:** The skill asks which process app the service belongs to (or searches via MCP if available) — it will never guess the app acronym, service ID, or exposure type. Once you confirm the match, it proceeds with discovery and generation.

---

### Out-of-scope: BPMN process testing

**Prompt:**
> Can you test the `Review Claim` process? It has three human tasks and a manager approval step.

**What to expect:** The skill recognises this is a BPMN process with user tasks — not a Service Flow — and redirects you to the `generate-baw-tests` skill, which handles process and coach testing.

---

### Out-of-scope: deploying a missing app snapshot

**Prompt:**
> Generate tests for the `Price Calculator` service flow. When I checked the server, the app snapshot isn't deployed yet.

**What to expect:** The skill tells you the process app must be deployed first and directs you to the `baw-deployment-manager` skill to install the snapshot before returning here to run tests.
