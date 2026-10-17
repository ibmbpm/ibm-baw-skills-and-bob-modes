# Service Flow Test Result Format

This file defines the structure of the `output/<acronym>/<acronym>-sf-test-results.json` file produced at the end of Phase B.
Write this file to `output/<acronym>/` — create the directory if it does not exist.
The execution protocol in `SERVICE_FLOW_EXECUTION.md` writes to this format. Use it when presenting results to the user.

---

## Top-level structure

```json
{
  "schema_version": "1.0",
  "suite_ref": "output/<acronym>/<acronym>-sf-test-suite.json",
  "service_flow": {
    "name": "Calculate Claim Amount",
    "exposure_type": "automation_service | startable | process_embedded"
  },
  "environment": {
    "baw_base_url": "https://baw.example.com:9443",
    "invocation_path_used": "automation_service | startable | process_embedded",
    "executed_at": "ISO-8601 timestamp",
    "executed_by": "username or 'bob-agent'"
  },
  "summary": {
    "total": 8,
    "passed": 5,
    "failed": 2,
    "errored": 1,
    "pass_rate": "62.5%"
  },
  "results": [ /* array of test result objects — see below */ ]
}
```

`invocation_path_used` records the actual path taken during execution — it may differ from the `exposure_type` in the suite if the skill used a fallback.

---

## Test result object

```json
{
  "test_case_id": "SFTC-001",
  "test_case_name": "Happy path — valid claim with standard deductible",
  "path": "happy",
  "result": "PASS | FAIL | ERROR | SKIPPED",
  "duration_ms": 842,
  "http_status": 200,
  "invocation_path": "automation_service",
  "process_instance_id": null,
  "failure_summary": "Brief plain-language description of what went wrong (null if PASS or SKIPPED)",
  "output_assertions": [ /* array of assertion result objects — see below */ ],
  "error_assertion": { /* error assertion result — see below */ },
  "error_details": "Plain-language description of the execution error (null if no error)"
}
```

**Result values:**
- `PASS` — all assertions passed.
- `FAIL` — at least one assertion failed; the service responded but the output did not match expectations.
- `ERROR` — an invocation failure (4xx/5xx on unexpected path, timeout, auth failure) prevented the test from producing assertable output. Result is inconclusive.
- `SKIPPED` — the test was excluded from this run (for example, user requested only happy-path tests).

`process_instance_id` is non-null only when the `process_embedded` invocation path was used — it records the BAW process instance ID created during the test, for post-run cleanup reference.

---

## Output assertion result object

One entry per field in `test_case.expected_output`.

```json
{
  "field": "payoutAmount",
  "expected": ">= 0",
  "actual": 3500.00,
  "operator": ">=",
  "threshold": 0,
  "passed": true
}
```

**Fields:**
- `field` — the output variable name.
- `expected` — the expectation string from the test case (for example, `">= 0"`, `"approved"`, `"any_non_null"`).
- `actual` — the value returned by the service.
- `operator` — parsed comparison operator if the expected value was a range expression; `null` for exact or placeholder assertions.
- `threshold` — parsed numeric threshold if applicable; `null` otherwise.
- `passed` — `true` if the assertion passed.

---

## Error assertion result object

Only populated when `test_case.expected_status = "error"`.

```json
{
  "expected_http_status": 400,
  "actual_http_status": 400,
  "http_status_passed": true,
  "expected_code": "any",
  "actual_code": "BPMVALIDATION001",
  "code_passed": true,
  "expected_message_contains": "policyNumber",
  "actual_message": "Required field 'policyNumber' is missing.",
  "message_passed": true,
  "overall_passed": true
}
```

All three sub-assertions (`http_status_passed`, `code_passed`, `message_passed`) must be true for `overall_passed` to be true. A `"any"` or absent expected value is treated as a skipped sub-assertion (always passes).

---

## Summary table (for display to user)

After Phase B completes, present this table before showing failure details:

```
| Test ID      | Name                                  | Path       | Result | Duration |
|--------------|---------------------------------------|------------|--------|----------|
| SFTC-001     | Happy path — valid claim              | happy      | PASS   | 0.8s     |
| SFTC-VAL-001 | Missing policyNumber                  | validation | PASS   | 0.4s     |
| SFTC-VAL-002 | Invalid claimType                     | validation | FAIL   | 0.3s     |
| SFTC-BND-001 | incurredAmount at minimum (0)         | boundary   | PASS   | 0.5s     |
| SFTC-ERR-001 | Policy not found fault                | error      | ERROR  | 0.2s     |
```

Then show a plain-language detail block for each `FAIL` or `ERROR` test:

> **SFTC-VAL-002 FAIL** — Expected the service to reject `claimType: "unknown"` with a validation error, but the service returned HTTP 200 with `status: "approved"`. The service does not appear to validate the `claimType` enum. This may indicate a missing input validation rule.

> **SFTC-ERR-001 ERROR** — Could not invoke the service. The server returned HTTP 403 (Forbidden). The test user may not have permission to call this Automation Service endpoint. Check that the user is a member of the team associated with the Automation Service exposure.

**Rules for the failure narrative:**
- Never show raw JSON payloads, stack traces, or XML error bodies.
- Translate every failure into one plain sentence: what was expected, what actually happened, and what to investigate.
- For `ERROR` results, suggest a concrete next step (check permissions, verify the service ID, inspect server logs).
