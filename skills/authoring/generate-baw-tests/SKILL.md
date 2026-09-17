---
name: generate-baw-tests
description: "Use when a BAW developer wants to generate or execute automated tests for an IBM BAW process app, case application, or service flow. Covers two phases: Phase A analyses artifacts and generates a structured test suite file (processes and coaches); Phase B executes process tests end-to-end (start instance, claim tasks, update task data, complete tasks, assert each step and final state). Use when the user says 'generate tests for my process', 'run my test suite', 'test this service', 'test all paths', 'create edge case tests', 'test my case', 'test coach validation', or 'test with invalid data'. Also use proactively when a user shares a BAW process app and asks if it works, wants to validate a workflow, or asks how to test before going to production. Do not use for authoring new processes (generate-baw-bpmn), inspecting running instances (inspect-baw-processes), or creating coach UIs (create-baw-widget)."
license: Apache-2.0
allowed-tools:
  - execute
  - write
  - read
  - fetch
metadata:
  version: "1.0.0"
---

# Generate BAW Tests

Generate comprehensive, structured test suites from IBM BAW process application artifacts and execute them end-to-end against a live environment.

This skill has two distinct phases. Run them in order for the full workflow, or enter at the phase that matches what the user needs.

| Phase | What it does |
|---|---|
| **A — Generation** | Fetch the process app artifacts, analyse them, and produce a test suite JSON file covering happy path, alternative paths, and edge cases for Processes and Coaches. |
| **B — Execution** | Take a test suite file and drive it against a live BAW environment: start a process, claim each user task, supply test data, complete it, and report pass/fail in plain language. |

---

## Execution mode

Check the tool list at the start of each phase independently. MCP is always used when the relevant tools are present — REST is a fallback for when they are absent.

- **Phase A:** If process authoring MCP tools are present → use MCP. If absent → use REST (`references/baw-rest.md`).
- **Phase B:** If process execution MCP tools are present → use MCP. If absent → use REST (`references/baw-rest.md`). The Phase A login session (if it exists) is still valid — do not ask for credentials again.

Each phase is decided independently. A failed tool call is not evidence of absence — only absence from the tool list counts.

---

> **⚠️ Hard rule — TWX download is always REST, never MCP.** The Authoring MCP tool list includes a solution-export tool. Do not call it — ever — for this skill. It is not production-ready. The TWX must always be downloaded via `GET {BAW_BASE_URL}/ops/std/bpm/containers/{container}/versions/{version}/export?use_enhanced_filenames=true`. This applies even when the Authoring MCP is fully connected. Ignore the MCP export tool silently — do not mention it to the user.

---

## Semantic operations

| Operation | Phase | Transport | What it does |
|---|---|---|---|
| `get_process_apps` | A | MCP / REST fallback | List all process apps and their acronyms |
| `get_process_app` | A | MCP / REST fallback | Get snapshots for a specific process app |
| `export solution` | A | **REST always — not MCP** | `GET /ops/std/bpm/containers/{container}/versions/{version}/export` |
| `start_process` | B | MCP / REST fallback | Start a new process instance |
| `get_task_list` | B | MCP / REST fallback | List open user tasks for an instance |
| `get_task_details` | B | MCP / REST fallback | Task model and current business data |
| `claim_task` | B | MCP / REST fallback | Assign the task to the current user |
| `complete_task` | B | MCP / REST fallback | Complete the task with test output data |
| `get_process_details` | B | MCP / REST fallback | Final instance state after execution |

---

## Phase A — Test Suite Generation

Read `references/TEST_GENERATION.md` before proceeding. It contains the full analysis and authoring instructions split by artifact type (Process, Coach). Come back here once you understand the analysis protocol.

Before generating any tests, resolve unknowns in this order. Do not announce step names or protocol labels to the user — just ask each question naturally.

If the user gave a full app name but no acronym, call `get_process_apps` (Authoring MCP) to find it. Present the match or a short list if ambiguous and confirm before proceeding. Never guess an acronym.

Call `get_process_app` to get available snapshots. If only one exists, use it and mention it. If multiple, present them and ask which to test against. Default to the most recently activated if the user says "latest" or "current".

Once the app and snapshot are resolved, ask:
> *"I found [app name] ([acronym]) — snapshot [snapshot]. What would you like me to test?*
> *- (A) Processes only*
> *- (B) Coaches only*
> *- (C) Both Processes and Coaches*
> *Are there any specific paths, edge cases, or boundary values you especially want covered?"*

Also ask:
> *"Once the test suite is ready, would you like me to run it against your BAW server straight away, or just generate the file for review first?"*

This determines whether to chain directly into Phase B or stop after the file is written.

**Generating the tests:**

1. **Acquire artifacts.** The TWX export is the only source for test generation — it contains the full process model, coach definitions, business objects, and all variable bindings needed for thorough test coverage. Use the first path that succeeds:

   **Path 1 — REST TWX export.** The TWX download always requires REST. Ask for the server URL and credentials only at this point, immediately before making the login call — do not ask earlier:
   > *"To export the app artifacts I'll need your BAW server URL and credentials — these are only used to get a session token for this conversation and are not stored."*

   Call `POST {BAW_BASE_URL}/ops/system/login` with `Authorization: Basic <base64(user:pass)>`, `Content-Type: application/json`, body `{"refresh_groups": false}`. On HTTP 201 store `csrf_token` as `{BAW_CSRF}` and the `LtpaToken2`/`JSESSIONID` cookies as `{BAW_SESSION}` — send both on all subsequent REST calls.

   Then call `GET {BAW_BASE_URL}/ops/std/bpm/containers/{container}/versions/{version}/export?use_enhanced_filenames=true`. The response is a binary `.twx` file (a ZIP) — extract it and read the XML files for process model, coach definitions, and business object details.

   If login returns 401/400, ask the user to re-enter credentials. Do not fall back to MCP tools — the export is REST-only.

   **Path 2 — local TWX file (offer only after Path 1 has visibly failed).** If the REST export fails or errors more than once, offer this without making it feel like a demotion:
   > *"If you already have the `.twx` file for this app on your machine, you can point me to it and I'll work from that directly — no server connection needed for this step."*
   If the user provides a file path, read the file from disk, treat it as a ZIP, extract and parse the XML files exactly as in Path 1. Do not ask for the file path pre-emptively — only after a real failure.

2. **Analyse.** Follow the artifact-type-specific instructions in `references/TEST_GENERATION.md`. The goal is to map every flow path, gateway decision, user task sequence, coach field, and boundary condition before writing a single test case.

3. **Generate the test suite.** Use the format in `references/TEST_SUITE_FORMAT.md` exactly. Every test case must have a clear ID, human-readable name, a type label (`process` or `coach`), preconditions, step sequence with data, and expected outcomes. Produce at minimum: one happy-path test, at least one alternative/error path per gateway or decision point, and relevant boundary/edge cases.

4. **Output.** Write two files:
   - `<app-acronym>-test-suite.json` — the machine-executable test suite (used by Phase B).
   - `<app-acronym>-test-suite.md` — a human-readable version for review. Follow the format in `references/TEST_SUITE_FORMAT.md` (Human-readable output format section).

   Show the user the summary table from the markdown file (test ID, name, type, path covered) and ask if they want to adjust anything before proceeding to execution.

---

## Phase B — Test Execution

Read `references/TEST_EXECUTION.md` before proceeding. It has the step-by-step execution protocol and assertion rules.

> **Isolation guarantee.** Phase B **only ever creates new process instances** for testing — it never touches, modifies, suspends, retries, or terminates any pre-existing instance in the environment. Every test case starts a fresh instance via `start_process` with clearly labelled test data and drives only that instance to completion. No existing business data, running processes, or production records are touched at any point.

**Phase B entry — confirm these in order before starting:**

1. **Resolve transport.** Check the tool list for process execution MCP tools (start process, search tasks, claim task, complete task).
   - Present → use MCP for all Phase B steps. Do not ask for a server URL or credentials — MCP handles authentication internally.
   - Absent → use REST. Defer the credentials ask to step 4 below (after the env confirmation), immediately before the first REST call.
2. Is there a test suite file to run? If not, offer to go back to Phase A.
3. Which tests should run — all, a specific subset, or just the happy path first?
4. **Confirm the environment is non-production.** Tell the user:
   > *"⚠️ Running these tests will create real process instances on your BAW server. It is strongly recommended to run against an **authoring or non-production environment** to avoid polluting task lists, reporting dashboards, and audit logs with test data. Do you want to continue? (yes / no)"*
   Wait for an explicit "yes" before starting. If the user answers "no", stop and suggest they point to a test environment first.
5. **REST only — ask for server URL and credentials** (skip entirely if using MCP): *"What is your BAW server URL, and what credentials should I use? These are only used to get a session token and are not stored."* If credentials were already obtained during Phase A, reuse that session — do not ask again. Call `POST {BAW_BASE_URL}/ops/system/login` as described in the Phase A credential flow and store `{BAW_CSRF}` and `{BAW_SESSION}`.
6. **If the server is production** (URL contains `prod`, user says so, or matches a known production hostname), add a second warning: *"This appears to be a production server. Running tests here creates real process instances that will appear in your users' task lists and may affect reporting and SLAs. Consider running against a staging or authoring environment instead. Are you sure you want to continue on production?"* Wait for explicit confirmation before continuing.

**Phase B steps — for each test case in sequence:**

1. **Start the process.** Use `start_process` (MCP) or `POST /bpm/processes` (REST fallback) with the initial data from the test case `input` block. Capture the returned `process_id`.

2. **Drive the task sequence.** For each expected task in the test case:
   a. Use `search_tasks` (MCP) or `GET /bpm/user-tasks?process_id=…` (REST fallback) and confirm the expected task name is present. If a different task appears, record a `FAIL` with the divergence.
   b. Use `claim_task` (MCP) or `POST /bpm/user-tasks/{task_id}/claim` (REST fallback).
   c. Use `get_task_details` (MCP) or `GET /bpm/user-tasks/{task_id}?optional_parts=data` (REST fallback) and verify the business data matches what the test case expects at this step. Record any mismatches.
   d. Use `complete_task` (MCP) or `POST /bpm/user-tasks/{task_id}/complete` (REST fallback) with the data from the test case step's `output` block.

3. **Assert final state.** After all tasks are complete, use `get_process_details` (MCP) or `GET /bpm/processes/{process_id}?optional_parts=data,variables` (REST fallback). Verify the final status and any output variables match the test case's `expected_outcome` block.

4. **Record the result.** Follow the format in `references/TEST_RESULT_FORMAT.md`. A test passes only when every step assertion and the final state assertion both pass.

5. **Present the report.** After all tests complete, present a summary table (test ID, name, result, duration) followed by the full result details for any FAIL or ERROR cases. Express failures in plain language — never show raw stack traces or JSON blobs to the user.

**Execution rules:**
- Run tests in the order they appear in the test suite unless the user specifies otherwise.
- If a `start_process` call fails with a 4xx error, mark that test `ERROR` and continue with the next test — do not abort the whole suite.
- If a task assertion fails mid-sequence, mark the test `FAIL`, record the step where it diverged, and stop driving that test instance (do not complete the remaining tasks on a failed instance).
- After an unexpected gateway branch, log the actual branch taken and continue driving the instance to its natural end — this is useful diagnostic information even on a failing test.

---

## Disambiguation

**Phase A vs Phase B:** If the user says "test my process" with no prior test suite, start at Phase A. If they provide a test suite file, go to Phase B directly.

**Process tests vs Coach tests:** Process tests drive full end-to-end execution via the process API. Coach tests validate UI field behaviour and validation rules from the artifact definitions — they do not require a live execution context and are part of Phase A output only; the skill does not currently execute Coach tests programmatically (mark them `manual` in the result file and explain what to check).

**Transport per phase:** Transport is decided independently per phase by checking the tool list at the start of that phase — before asking the user anything. MCP is always used when the relevant tools are present. REST is only used when they are absent.

---

## Output files produced

| File | When | Contents |
|---|---|---|
| `<acronym>-test-suite.json` | End of Phase A | Machine-executable test suite (input to Phase B) |
| `<acronym>-test-suite.md` | End of Phase A | Human-readable version for review and sign-off |
| `<acronym>-test-results.json` | End of Phase B | Pass/fail results for each test case |

Both formats are fully specified in `references/TEST_SUITE_FORMAT.md` and `references/TEST_RESULT_FORMAT.md`.

---

## Boundaries

In scope: Process test generation (BPMN paths, gateways, user tasks, business data), Coach test generation (fields, validation, required conditions), process test execution (start / claim / complete), result reporting.

Out of scope — do not attempt:
- **Service Flow test generation or execution** — covered by a separate skill.
- **Case application testing** — out of scope for this version.
- **Federated multi-system test orchestration** — each test targets a single BAW system.
- **Authoring or modifying process definitions** — use `generate-baw-bpmn`.
- **UI rendering or screenshot capture of Coaches** — static artifact analysis only.
