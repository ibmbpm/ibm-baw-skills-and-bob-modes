# Test Result Format

This file defines the structure of the `<acronym>-test-results.json` file produced at the end of Phase B.
The execution protocol in `TEST_EXECUTION.md` writes to this format. Use it when presenting results to the user.

---

## Top-level structure

```json
{
  "schema_version": "1.0",
  "suite_ref": "<acronym>-test-suite.json",
  "environment": {
    "baw_base_url": "https://baw.example.com:9443",
    "execution_mode": "rest",
    "executed_at": "ISO-8601 timestamp",
    "executed_by": "username or 'bob-agent'"
  },
  "summary": {
    "total": 10,
    "passed": 7,
    "failed": 2,
    "errored": 1,
    "pass_rate": "70%"
  },
  "results": [ /* array of test result objects — see below */ ]
}
```

---

## Test result object

```json
{
  "test_case_id": "TC-001",
  "test_case_name": "Happy path — requisition approved",
  "type": "process | coach",
  "result": "PASS | FAIL | ERROR | SKIPPED",
  "duration_ms": 3420,
  "process_instance_id": "12345",
  "failure_summary": "Brief plain-language description of what went wrong (null if PASS)",
  "step_results": [ /* array of step result objects — see below */ ],
  "final_state_assertions": [ /* array of assertion result objects — see below */ ],
  "coach_assertion_results": [ /* for type: coach only — see below */ ],
  "error_details": "HTTP 500 from POST /bpm/user-tasks/67/complete — 'Service timeout' (null if no error)"
}
```

**Result values:**
- `PASS` — all step assertions and final state assertions passed.
- `FAIL` — at least one assertion failed; execution completed (or was halted at the failure point).
- `ERROR` — an API call or system failure prevented the test from completing; result is inconclusive.
- `SKIPPED` — the test was excluded from this run (e.g. user requested only happy path tests).

---

## Step result object

```json
{
  "step_number": 1,
  "expected_task_name": "Submit Requisition",
  "actual_task_name": "Submit Requisition",
  "task_found": true,
  "claim_result": "success | failed | already_claimed",
  "pre_completion_assertions": [
    {
      "field": "position_title",
      "expected": "Software Engineer",
      "actual": "Software Engineer",
      "passed": true
    }
  ],
  "completion_result": "success | failed",
  "completion_error": null,
  "step_result": "PASS | FAIL | ERROR"
}
```

**`task_found: false`** means the expected task was not in the task list for this instance at this point in the flow. `actual_task_name` records what was found instead (if anything). This always marks the step `FAIL` and halts execution of this test.

---

## Final state assertion object

```json
{
  "assertion": "final_status",
  "expected": "Completed",
  "actual": "Completed",
  "passed": true
}
```

One entry for `final_status` and one entry per variable in `expected_outcome.output_variables`.

---

## Coach assertion result object (for `type: coach` tests)

Coach tests are executed manually. Record the result after the user reviews and confirms each assertion.

```json
{
  "field_id": "binding path",
  "field_label": "Label shown in the UI",
  "assertion_type": "required",
  "condition": "Always",
  "expected": "Validation error shown when field is empty",
  "manual_result": "PASS | FAIL | NOT_TESTED",
  "tester_note": "Optional note from the person who ran the manual check"
}
```

---

## Summary table (for display to user)

After Phase B completes, present this table to the user before showing failure details:

```
| Test ID  | Name                              | Result | Duration |
|----------|-----------------------------------|--------|----------|
| TC-001   | Happy path — requisition approved | PASS   | 3.4s     |
| TC-002   | HR rejection path                 | FAIL   | 2.1s     |
| TC-003   | Budget threshold at boundary      | PASS   | 4.0s     |
| TC-ERR-1 | Error boundary — service timeout  | ERROR  | 0.8s     |
```

Then show the full detail block for each `FAIL` or `ERROR` test. Express failures in plain language:

> **TC-002 FAIL** — Expected task "Finance Approval" after HR rejection, but found "End Event: Rejected" instead. The process terminated at step 2 rather than routing to Finance.

> **TC-ERR-1 ERROR** — Could not complete task "Process Refund" (task ID 1042). The BAW server returned HTTP 500 with "Internal service error". The test is inconclusive — check the server logs for errors in the RefundService integration service.

Never show raw JSON error payloads to the user. Translate them into one sentence that describes what failed and what to investigate next.
