# Generate BAW tests: documentation

> Use when a BAW developer wants to generate or run automated tests for an IBM BAW process app, covering happy paths, alternative paths, edge cases, and Coach UI validation, without writing test scripts by hand.

## Purpose

This skill automates two tasks that BAW developers typically do manually: writing test cases and running them. In Phase A, the skill exports the process app's `.twx` artifact and analyzes the BPMN flow paths, gateway conditions, user tasks, business objects, and Coach field rules. It then produces a structured test suite that covers the happy path, every alternative gateway branch, error paths, and boundary conditions. In Phase B, the skill runs that test suite against a live BAW environment. It starts a process instance, claims each user task, supplies test data, completes the task, and reports pass or fail in plain language. The skill generates Coach test cases (UI field validation) in Phase A, but you run them manually.

## Setup and configuration

- Phase A discovery and TWX export: the skill discovers applications and snapshots through the BAW Operations REST API (`GET /ops/std/bpm/containers`). The skill downloads the `.twx` file through REST (`GET /ops/std/bpm/containers/{container}/versions/{version}/export`). This step requires your BAW server URL and credentials.
- Phase B execution (optional Runtime MCP): if the BAW Runtime MCP server (`workflow-runtime`) is connected, Bob uses it to start processes, claim tasks, and complete them. If it is not connected, Phase B runs through standard REST calls.
- Local TWX fallback: if you already have the `.twx` file on disk, you can provide the file path, and Bob works from it without connecting to a server.
- The skill uses BAW server credentials only to obtain a session token for the current conversation. It does not store them.
- The TWX export endpoint typically requires administrator credentials.

## Compatibility

- BAW 26.x (REST endpoints: `/ops/system/login`, `/ops/std/bpm/containers/{container}/versions/{version}/export`, `/bpm/processes`, `/bpm/user-tasks`)
- This skill does not support Service Flow test generation or Case application testing in this version.
- Coach test cases are static (design-time) only. This skill does not support programmatic Coach execution. Use the assertions for manual verification.

## Prompt examples

> Note: The credentials in these prompt examples are for illustration only. Never use real production credentials in prompts. Use environment variables or a secrets manager for sensitive values.

### Generate a full test suite from a live server
Prompt:
> Generate a full test suite for my Standard Employee Requisition app (acronym SER, snapshot SERV100) on https://baw.company.com:9443, user <your-baw-username>, password <your-baw-password>. I want the happy path, all rejection paths, and edge cases around the budget approval threshold.

What to expect: Bob exports the TWX through REST, analyzes the BPMN, and writes two files: `SER-test-suite.json` (machine-executable) and `SER-test-suite.md` (human-readable with a summary table). It then asks whether to run the suite immediately or stop for review.

---

### Generate tests and run them immediately
Prompt:
> Generate tests for my Claims Processing app (acronym CP, snapshot CP_DEV) and run the happy path immediately. Server: https://baw-dev.company.com:9443, credentials <your-baw-username> / <your-baw-password>.

What to expect: Bob generates `CP-test-suite.json`, asks for confirmation before creating real process instances, then runs only the happy-path test case and reports the result as PASS, FAIL, or ERROR in plain language.

---

### Run an existing test suite
Prompt:
> I have my test suite file `SER-test-suite.json` ready. Run all the tests against https://baw-test.company.com:9443, credentials <your-baw-username> / <your-baw-password>.

What to expect: Bob enters Phase B directly, re-checks for MCP availability, and issues the nonproduction confirmation prompt. It then runs every test case in sequence, claiming tasks, supplying data, and asserting outcomes, and presents a results table.

---

### Generate Coach-only tests
Prompt:
> Generate test cases just for the Submit Requisition coach form. I need to verify: Position Title is required, Budget only accepts numbers above 0, and Department dropdown shows an error if nothing is selected.

What to expect: Bob generates `type: coach` test cases with assertions for required fields, validation rules, and dropdown behavior. It explains that these are for manual verification and includes them in both the JSON and markdown test suite files.

---

### Work from a local TWX file (no server needed)
Prompt:
> I already have the TWX at /Users/me/Downloads/OrderManagement.twx. Generate a test suite from it without connecting to any server.

What to expect: Bob reads the file from disk, extracts and parses the XML, generates the full test suite, and writes both output files. You do not need a server URL or credentials.

---

### Run only non-happy-path tests
Prompt:
> I have `CP-test-suite.json`. Run only the rejection and error path tests, skip the happy path. Server is https://baw-test.company.com:9443, credentials <your-baw-username> / <your-baw-password>.

What to expect: Bob enters Phase B, filters to test cases with `path` values of `alternative`, `error`, or `boundary`, and issues the environment confirmation. It then runs only those cases and reports results.

---

### Out-of-scope redirect: coach widgets and task portals
Prompt:
> Can you generate a custom Carbon task dashboard portal or coach view for my process?

What to expect: Bob explains that the `create-baw-widget` skill creates Coach Views and custom widgets, and the `create-baw-portal` skill builds end-user task dashboards and portals. It redirects you to the appropriate skill.

---

### Out-of-scope redirect: process authoring
Prompt:
> Can you add a Finance Approval step to my Claims process and then generate tests for it?

What to expect: Bob treats these as two separate tasks. It directs you to `generate-baw-bpmn` for the authoring step, then offers to generate tests after the new version is available.
