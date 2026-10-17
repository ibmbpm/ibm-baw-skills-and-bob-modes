---
name: generate-baw-tests
description: "Use when a BAW developer wants to generate or execute automated tests for an IBM BAW process app, case application, or service flow. Covers two phases: Phase A analyzes artifacts and generates a structured test suite file (processes and coaches); Phase B executes process tests end-to-end (start instance, claim tasks, update task data, complete tasks, assert each step and final state). Use when the user says 'generate tests for my process', 'run my test suite', 'test this service', 'test all paths', 'create edge case tests', 'test my case', 'test coach validation', or 'test with invalid data'. Also use proactively when a user shares a BAW process app and asks if it works, wants to validate a workflow, or asks how to test before going to production. Do not use for authoring new processes (generate-baw-bpmn), inspecting running instances (inspect-baw-processes), creating coach widgets (create-baw-widget), or building custom portals (create-baw-portal)."
license: Apache-2.0
compatibility: "IBM BAW 22.x and later; IBM CP4BA 22.x and later"
allowed-tools:
  - Read
  - Edit
  - Bash
metadata:
  version: "1.0.0"
  display_name: Generate BAW Tests
  short_description: Generate and execute end-to-end automated test suites for IBM BAW process apps, case applications, and service flows.
  author: IBM BAW Team
---

# Generate BAW tests

Generate comprehensive, structured test suites from IBM Business Automation Workflow (BAW) process application artifacts, and run them end-to-end against a live environment.

This skill has two distinct phases. Run them in order for the full workflow, or enter at the phase that matches what the user needs.

| Phase | What it does |
|---|---|
| A: Generation | Fetch the process app artifacts, analyze them, and produce a test suite JSON file that covers the happy path, alternative paths, and edge cases for Processes and Coaches. |
| B: Execution | Take a test suite file and drive it against a live BAW environment: start a process, claim each user task, supply test data, complete the task, and report pass or fail in plain language. |

---

## Execution mode

Check the tool list at the start of each phase independently. Always use MCP when the relevant tools are present. Use REST as a fallback when they are absent.

- Phase A: If process authoring MCP tools are present, use MCP. If they are absent, use REST (`references/baw-rest.md`).
- Phase B: If process execution MCP tools are present, use MCP. If they are absent, use REST (`references/baw-rest.md`).

Decide each phase independently. A failed tool call is not evidence of absence. Only absence from the tool list counts.

---

## Credentials

Never prompt the user for credentials. Credentials are only needed when making a REST call.
When a REST call is about to be made, read `references/CREDENTIAL_HANDLING.md` and follow it — it will read credentials from `.env` automatically, and only prompt the user if a value is missing from that file. Do this once per session only.

---

> Hard rule: always download the TWX through REST, never through MCP. The Authoring MCP tool list includes a solution-export tool. Never call it for this skill, because it is not production-ready. Always download the TWX with `GET {BAW_BASE_URL}/ops/std/bpm/containers/{container}/versions/{version}/export?use_enhanced_filenames=true`. This rule applies even when the Authoring MCP is fully connected. Ignore the MCP export tool silently, and do not mention it to the user.

---

## Semantic operations

| Operation | Phase | Transport | What it does |
|---|---|---|---|
| `get_process_apps` | A | MCP / REST fallback | List all process apps and their acronyms |
| `get_process_app` | A | MCP / REST fallback | Get snapshots for a specific process app |
| `export solution` | A | REST always, not MCP | `GET /ops/std/bpm/containers/{container}/versions/{version}/export` |
| `start_process` | B | MCP / REST fallback | Start a new process instance |
| `get_task_list` | B | MCP / REST fallback | List open user tasks for an instance |
| `get_task_details` | B | MCP / REST fallback | Task model and current business data |
| `claim_task` | B | MCP / REST fallback | Assign the task to the current user |
| `complete_task` | B | MCP / REST fallback | Complete the task with test output data |
| `get_process_details` | B | MCP / REST fallback | Final instance state after execution |

---

## Phase A: test suite generation

Read `references/TEST_GENERATION.md` before proceeding. It contains the full analysis and authoring instructions, split by artifact type (Process, Coach). Come back here once you understand the analysis protocol.

Before generating any tests, resolve unknowns in this order. Do not announce step names or protocol labels to the user. Ask each question naturally.

If the user gave a full app name but no acronym, call `get_process_apps` (Authoring MCP) to find it. Present the match, or a short list if the match is ambiguous, and confirm before proceeding. Never guess an acronym.

Call `get_process_app` to get available snapshots. If only one exists, use it and mention it. If multiple exist, present them and ask which to test against. Default to the most recently activated snapshot if the user says "latest" or "current".

Once the app and snapshot are resolved, ask:
> *"I found [app name] ([acronym]) - snapshot [snapshot]. What would you like me to test?*
> *- (A) Processes only*
> *- (B) Coaches only*
> *- (C) Both Processes and Coaches*
> *Are there any specific paths, edge cases, or boundary values you especially want covered?"*

Also ask:
> *"Once the test suite is ready, would you like me to run it against your BAW server immediately, or just generate the file for review first?"*

The answer determines whether to chain directly into Phase B or stop after writing the file.

Generate the tests as follows:

1. Acquire artifacts. The TWX export is the only source for test generation, because it contains the full process model, coach definitions, business objects, and all variable bindings that thorough test coverage needs. Use the first path that succeeds:

   Path 1: REST TWX export. The TWX download always requires REST. Read credentials from `references/CREDENTIAL_HANDLING.md` (already resolved earlier in this session if a REST call was made in Phase A — do not resolve again). Then call `GET {BAW_BASE_URL}/ops/std/bpm/containers/{container}/versions/{version}/export?use_enhanced_filenames=true`. The response is a binary `.twx` file (a ZIP). Extract it and read the XML files for the process model, coach definitions, and business object details.

   Path 2: local TWX file (offer only after Path 1 visibly fails). If the REST export fails or errors more than once, offer this option without making it feel like a demotion:
   > *"If you already have the `.twx` file for this app on your machine, you can point me to it and I can work from that directly. No server connection is needed for this step."*
   If the user provides a file path, read the file from disk, treat it as a ZIP, and extract and parse the XML files exactly as in Path 1. Do not ask for the file path preemptively. Ask only after a real failure.

2. Analyze. Follow the artifact-type-specific instructions in `references/TEST_GENERATION.md`. Map every flow path, gateway decision, user task sequence, coach field, and boundary condition before writing a single test case.

3. Generate the test suite. Use the format in `references/TEST_SUITE_FORMAT.md` exactly. Every test case must have a clear ID, a human-readable name, a type label (`process` or `coach`), preconditions, a step sequence with data, and expected outcomes. Produce at minimum one happy-path test, at least one alternative or error path per gateway or decision point, and relevant boundary and edge cases.

4. Write the output. Write two files:
   - `<app-acronym>-test-suite.json`: the machine-executable test suite that Phase B uses.
   - `<app-acronym>-test-suite.md`: a human-readable version for review. Follow the format in `references/TEST_SUITE_FORMAT.md` (Human-readable output format section).

   Show the user the summary table from the markdown file (test ID, name, type, path covered) and ask if they want to adjust anything before proceeding to execution.

---

## Phase B: test execution

Read `references/TEST_EXECUTION.md` before proceeding. It has the step-by-step execution protocol and assertion rules.

> Isolation guarantee: Phase B only ever creates new process instances for testing. It never touches, modifies, suspends, retries, or terminates any pre-existing instance in the environment. Every test case starts a fresh instance through `start_process` with clearly labeled test data and drives only that instance to completion. Phase B does not touch existing business data, running processes, or production records at any point.

Phase B entry: confirm these items in order before starting.

1. Resolve transport. Check the tool list for process execution MCP tools (start process, search tasks, claim task, complete task).
   - If present, use MCP for all Phase B steps. Do not ask for a server URL or credentials, because MCP handles authentication internally.
   - If absent, use REST. Defer the credentials request to step 5 below (after the environment confirmation), immediately before the first REST call.
2. Check whether a test suite file exists to run. If not, offer to go back to Phase A.
3. Ask which tests to run: all, a specific subset, or just the happy path first.
4. Confirm the environment is nonproduction. Tell the user:
   > *"Running these tests creates real process instances on your BAW server. Run them against an authoring or nonproduction environment to avoid polluting task lists, reporting dashboards, and audit logs with test data. Do you want to continue? (yes / no)"*
   Wait for an explicit "yes" before starting. If the user answers "no", stop and suggest they point to a test environment first.
5. REST only (skip entirely if using MCP): resolve credentials via `references/CREDENTIAL_HANDLING.md` — credentials are read from `.env` automatically and the session from Phase A is reused if already established. No prompt to the user unless `.env` is incomplete.
6. If the server is production (the URL contains `prod`, the user says so, or the URL matches a known production hostname), add a second warning: *"This appears to be a production server. Running tests here creates real process instances that appear in your users' task lists and might affect reporting and SLAs. Consider running against a staging or authoring environment instead. Are you sure you want to continue on production?"* Wait for explicit confirmation before continuing.

Phase B steps (for each test case, in sequence):

1. Start the process. Use `start_process` (MCP) or `POST /bpm/processes` (REST fallback) with the initial data from the test case `input` block. Capture the returned `process_id`.

2. Drive the task sequence. For each expected task in the test case:
   a. Use `search_tasks` (MCP) or `GET /bpm/user-tasks?process_id=…` (REST fallback) and confirm that the expected task name is present. If a different task appears, record a `FAIL` with the divergence.
   b. Use `claim_task` (MCP) or `POST /bpm/user-tasks/{task_id}/claim` (REST fallback).
   c. Use `get_task_details` (MCP) or `GET /bpm/user-tasks/{task_id}?optional_parts=data` (REST fallback) and verify that the business data matches what the test case expects at this step. Record any mismatches.
   d. Use `complete_task` (MCP) or `POST /bpm/user-tasks/{task_id}/complete` (REST fallback) with the data from the test case step's `output` block.

3. Assert the final state. After all tasks are complete, use `get_process_details` (MCP) or `GET /bpm/processes/{process_id}?optional_parts=data,variables` (REST fallback). Verify that the final status and any output variables match the test case's `expected_outcome` block.

4. Record the result. Follow the format in `references/TEST_RESULT_FORMAT.md`. A test passes only when every step assertion and the final state assertion both pass.

5. Present the report. After all tests complete, present a summary table (test ID, name, result, duration), followed by the full result details for any FAIL or ERROR cases. Express failures in plain language. Never show raw stack traces or JSON blobs to the user.

Execution rules:
- Run tests in the order they appear in the test suite unless the user specifies otherwise.
- If a `start_process` call fails with a 4xx error, mark that test `ERROR` and continue with the next test. Do not abort the whole suite.
- If a task assertion fails mid-sequence, mark the test `FAIL`, record the step where it diverged, and stop driving that test instance. Do not complete the remaining tasks on a failed instance.
- After an unexpected gateway branch, log the actual branch taken and continue driving the instance to its natural end. This is useful diagnostic information even on a failing test.

---

## Disambiguation

Phase A or Phase B: If the user says "test my process" with no prior test suite, start at Phase A. If they provide a test suite file, go to Phase B directly.

Process tests or Coach tests: Process tests drive full end-to-end execution through the process API. Coach tests validate UI field behavior and validation rules from the artifact definitions. They do not require a live execution context and are part of the Phase A output only. The skill does not currently execute Coach tests programmatically. Mark them `manual` in the result file and explain what to check.

Transport per phase: Decide the transport independently for each phase by checking the tool list at the start of that phase, before asking the user anything. Use MCP whenever the relevant tools are present. Use REST only when they are absent.

---

## Output files produced

| File | When | Contents |
|---|---|---|
| `<acronym>-test-suite.json` | End of Phase A | Machine-executable test suite (input to Phase B) |
| `<acronym>-test-suite.md` | End of Phase A | Human-readable version for review and sign-off |
| `<acronym>-test-results.json` | End of Phase B | Pass/fail results for each test case |

`references/TEST_SUITE_FORMAT.md` and `references/TEST_RESULT_FORMAT.md` fully specify these formats.

---

## Boundaries

In scope: Process test generation (BPMN paths, gateways, user tasks, business data), Coach test generation (fields, validation, required conditions), process test execution (start, claim, complete), and result reporting.

Out of scope. Do not attempt:
- Service Flow test generation or execution: use the `test-baw-service-flows` skill.
- Case application testing: out of scope for this version.
- Federated multi-system test orchestration: each test targets a single BAW system.
- Authoring or modifying process definitions: use `generate-baw-bpmn`.
- UI rendering or screenshot capture of Coaches: this skill performs static artifact analysis only.
- Creating coach widgets or task portals: use `create-baw-widget` or `create-baw-portal`.
