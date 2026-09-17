# Generate BAW Tests — Documentation

> Use when a BAW developer wants to generate or execute automated tests for an IBM® BAW process app — covering happy paths, alternative paths, edge cases, and Coach UI validation — without writing test scripts by hand.

## Purpose

This skill automates two things that BAW developers typically do manually: writing test cases and running them. In Phase A it exports the process app's `.twx` artifact, analyzes the BPMN flow paths, gateway conditions, user tasks, business objects, and Coach field rules, then produces a structured test suite covering the happy path, every alternative gateway branch, error paths, and boundary conditions. In Phase B it drives that test suite against a live BAW environment — starting a process instance, claiming each user task, supplying test data, completing the task, and reporting pass/fail in plain language. Coach test cases (UI field validation) are generated in Phase A but executed manually.

## Setup and configuration

- Phase A discovery (optional MCP): If the BAW Authoring MCP server (`workflow-runtime-authoring`) is connected, Bob uses it to list apps and snapshots. If not, discovery falls back to REST using `GET /ops/std/bpm/containers`.
- Phase A TWX export (always REST): Regardless of MCP availability, the `.twx` file is always downloaded via REST (`GET /ops/std/bpm/containers/{container}/versions/{version}/export`). Your BAW server URL and credentials are required for this step.
- Phase B execution (optional MCP): If the BAW Runtime MCP server (`workflow-runtime`) is connected, Bob uses it to start processes, claim tasks, and complete them. If not, Phase B falls back to REST.
- Local TWX fallback: If you already have the `.twx` file on disk, provide the file path and Bob will work from it without connecting to a server.
- BAW server credentials are only used to obtain a session token for the current conversation — they are not stored.
- Admin-level credentials are typically required for the TWX export endpoint.

## Compatibility

- BAW 26.x (REST endpoints: `/ops/system/login`, `/ops/std/bpm/containers/{container}/versions/{version}/export`, `/bpm/processes`, `/bpm/user-tasks`)
- Service Flow test generation and Case application testing are out of scope for this version
- Coach test cases are static (design-time) only — programmatic Coach execution is not supported; assertions are for manual verification

> **Note:** Credentials shown in prompt examples are for illustration only. Never use real production credentials in prompts. Use environment variables or a secrets manager for sensitive values.

## Prompt examples

### Generate a full test suite from a live server
**Prompt:**
> Generate a full test suite for my Standard Employee Requisition app (acronym SER, snapshot SERV100) on https://baw.company.com:9443, user admin, password admin123. I want the happy path, all rejection paths, and edge cases around the budget approval threshold.

**What to expect:** Bob exports the TWX via REST, analyses the BPMN, and writes two files — `SER-test-suite.json` (machine-executable) and `SER-test-suite.md` (human-readable with a summary table). It then asks whether to run the suite immediately or stop for review.

---

### Generate tests and run them straight away
**Prompt:**
> Generate tests for my Claims Processing app (acronym CP, snapshot CP_DEV) and run the happy path immediately. Server: https://baw-dev.company.com:9443, admin/secret.

**What to expect:** Bob generates `CP-test-suite.json`, asks for confirmation before creating real process instances, then runs only the happy-path test case and reports the result as PASS, FAIL, or ERROR in plain language.

---

### Run an existing test suite
**Prompt:**
> I have my test suite file `SER-test-suite.json` ready. Run all the tests against https://baw-test.company.com:9443, credentials admin/admin123.

**What to expect:** Bob enters Phase B directly, re-checks for MCP availability, issues the non-production confirmation prompt, then executes every test case in sequence — claiming tasks, supplying data, asserting outcomes — and presents a results table.

---

### Generate Coach-only tests
**Prompt:**
> Generate test cases just for the Submit Requisition coach form. I need to verify: Position Title is required, Budget only accepts numbers above 0, and Department dropdown shows an error if nothing is selected.

**What to expect:** Bob generates `type: coach` test cases with assertions for required fields, validation rules, and dropdown behavior. It explains these are for manual verification and includes them in both the JSON and markdown test suite files.

---

### Work from a local TWX file (no server needed)
**Prompt:**
> I already have the TWX at /Users/me/Downloads/OrderManagement.twx — generate a test suite from it without connecting to any server.

**What to expect:** Bob reads the file from disk, extracts and parses the XML, generates the full test suite, and writes both output files — no server URL or credentials needed.

---

### Run only non-happy-path tests
**Prompt:**
> I have `CP-test-suite.json` — run only the rejection and error path tests, skip the happy path. Server is https://baw-test.company.com:9443, admin/secret.

**What to expect:** Bob enters Phase B, filters to test cases with `path` values of `alternative`, `error`, or `boundary`, issues the environment confirmation, then runs only those cases and reports results.

---

### Out-of-scope redirect — process authoring
**Prompt:**
> Can you add a Finance Approval step to my Claims process and then generate tests for it?

**What to expect:** Bob handles these as two separate tasks — directs you to `generate-baw-bpmn` for the authoring step, then offers to generate tests once the new version is available.
