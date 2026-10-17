# Service Flow Test Generation — Artifact Analysis Instructions

This file contains the detailed instructions for producing test cases in **Phase A** of the `test-baw-service-flows` skill.
It describes how to analyse an I/O contract and author test cases covering every meaningful input combination.

---

## Table of contents

1. [Analysis approach](#1-analysis-approach)
2. [Happy-path test generation](#2-happy-path-test-generation)
3. [Error-path test generation](#3-error-path-test-generation)
4. [Boundary and edge case generation](#4-boundary-and-edge-case-generation)
5. [Naming conventions](#5-naming-conventions)
6. [Coverage checklist](#6-coverage-checklist)

---

## 1. Analysis approach

A Service Flow test is simpler than a process test — there are no task sequences or gateways to enumerate. The test is a single invocation: supply inputs, receive outputs (or an error), compare. The goal of analysis is to identify the full space of meaningful input combinations.

Work through the I/O contract in two passes:

**Pass 1 — Input space.** For every input variable, classify it:

| Variable trait | What to generate |
|---|---|
| Required | Must be present on every valid call; absence is an error-path test. |
| Optional | Omit it in at least one test to verify the service handles its absence gracefully. |
| Numeric with a range constraint | Generate a boundary test at the minimum value, at maximum, and one outside each bound. |
| String with a length constraint | Generate a test at exactly the maximum allowed length and one character over. |
| Enum / restricted value set | Generate one test per valid value (if small) or at minimum one valid and one invalid. |
| Boolean | Generate one test with `true` and one with `false` if the service branches on the value. |
| Date | If the service logic is date-sensitive, generate a test with today's date, a past date, and a future date. |
| Nested object | If a field inside the object is required, include a test where that inner field is missing. |
| Array / list | Generate a test with an empty array, a single-element array, and (if relevant) a large array. |

**Pass 2 — Error outputs.** For every declared fault type or error code in the contract:

- Identify which input combination triggers that fault.
- Design one test case whose input is crafted to trigger exactly that fault.
- Record the expected `error_code` or `error_message` pattern in the test case's `expected_error` block.

**Minimum error-path rule:** For each service flow, produce at least one error-path test case alongside its happy-path test, if the service allows it. A service flow "allows" an error path when any of the following are true:

| Condition | Error test to generate |
|---|---|
| Has one or more required input fields | Omit the most important required field and assert an error response. |
| Has declared fault outputs / error codes | Craft the input that triggers the fault and assert the specific error code. |
| Has a numeric or string-length constraint | Pass a value outside the valid range and assert a validation error. |
| Has an enum constraint | Pass an invalid enum value and assert an error response. |

Only omit the error-path test if the service's I/O contract has **no required fields, no declared faults, and no validatable input constraints** — in which case note the omission explicitly in the test suite with a comment: `"no_error_path_reason": "service has no required inputs, faults, or constraints"`.

---

## 2. Happy-path test generation

The happy-path test is the minimal valid call that reaches a successful response.

**Input selection for the happy path:**
- Include all required fields.
- Use representative, realistic values — not empty strings, zeros, or placeholders unless those are the actual defaults.
- Omit all optional fields (unless a test with all fields populated is also needed).
- For numeric fields, choose a value well within the valid range — not at a boundary.

**Expected output for the happy path:**
- Set `expected_output` to the specific field values the service should return.
- If the service returns a computed value (for example, a calculated total, a generated ID), use a placeholder operator like `"any_non_null"` or `">= 0"` rather than a fixed value.
- Set `expected_status` to `success`.

**Naming:** `SFTC-001` — happy path — [Service Flow name].

---

## 3. Error-path test generation

Generate one test case per distinct error condition. Sources of error conditions:

1. **Missing required field** — omit each required input variable one at a time. If there are many required fields, omit them in groups for efficiency (one test per group is acceptable, but prefer one test per field if the service validates them independently).

2. **Invalid type or format** — pass a value of the wrong type (for example, a string where an integer is expected, an invalid date format).

3. **Out-of-range value** — pass a value outside the declared valid range (for example, `-1` for a field with `min: 0`, a string longer than `maxLength`).

4. **Declared fault outputs** — for each fault/error code documented in the I/O contract, craft the exact input combination that triggers it (for example, a lookup that returns "not found", an authorization check that returns "denied").

5. **Empty required string** — pass an empty string `""` for a required string field.

**Expected output for error paths:**
- Set `expected_status` to `error`.
- Set `expected_error.code` to the specific error code if known.
- Set `expected_error.message_contains` to a substring of the expected error message if the full message is variable. Use `"any"` if the exact message is not predictable.
- Leave `expected_output` empty (`{}`).

**Naming:**
- `SFTC-ERR-001`, `SFTC-ERR-002`, ... — for declared-fault error paths.
- `SFTC-VAL-001`, `SFTC-VAL-002`, ... — for validation error paths (missing field, wrong type, out-of-range).

---

## 4. Boundary and edge case generation

After covering the happy path and all error paths, add the following edge cases:

| Scenario | Input to use | What to assert |
|---|---|---|
| **All optional fields supplied** | Include every optional field with a valid non-null value | Service still returns a successful response; no unexpected truncation or ignored fields. |
| **Numeric at minimum boundary** | Set a range-constrained field to exactly the minimum allowed value | Service accepts the call and returns a successful response. |
| **Numeric at maximum boundary** | Set a range-constrained field to exactly the maximum allowed value | Service accepts the call and returns a successful response. |
| **Numeric just below minimum** | Set the field to `minimum - 1` | Service returns a validation error or the declared range fault. |
| **Numeric just above maximum** | Set the field to `maximum + 1` | Service returns a validation error or the declared range fault. |
| **Empty array input** | Pass `[]` for an array input variable | Service either accepts gracefully (no error) or returns a specific "empty list" error, as documented. |
| **Large string at max length** | Pass a string of exactly `maxLength` characters | Service accepts the call; no truncation. |
| **String one character over max** | Pass a string of `maxLength + 1` characters | Service returns a validation error. |
| **Null optional field** | Pass `null` explicitly for an optional field that has a default | Service uses the default, not null. |
| **Special characters in strings** | Include `< > & " '` and a multi-byte Unicode character in a string field | Service handles them without escaping errors or injection vulnerabilities. |
| **Same-day date** | For services that compare two dates, pass the same value for both | Service handles equality correctly without an off-by-one error. |
| **Boolean toggle** | If the service branches on a boolean input, test both `true` and `false` paths | Each path returns the correct output variant. |

**Naming:** `SFTC-EDGE-001`, `SFTC-EDGE-002`, ... for edge cases; `SFTC-BND-001`, `SFTC-BND-002`, ... for boundary tests.

---

## 5. Naming conventions

| Prefix | Meaning |
|---|---|
| `SFTC-001` | Happy path |
| `SFTC-002`, `SFTC-003` | Additional happy-path variants (all-optional, all-defaults) |
| `SFTC-ERR-001` | Declared fault / documented error path |
| `SFTC-VAL-001` | Input validation error (missing field, wrong type, out-of-range) |
| `SFTC-BND-001` | Boundary value test (at min/max) |
| `SFTC-EDGE-001` | Edge case (empty array, null optional, special characters) |

IDs must be unique across the entire test suite. Do not reuse an ID even if a test is replaced.

---

## 6. Coverage checklist

Before finalising the test suite, verify:

- [ ] Happy-path test exists and uses all required fields with realistic values.
- [ ] At least one test omits each required field individually (or in groups for large field counts).
- [ ] One test per declared fault type/error code.
- [ ] Boundary tests at min and max for every numeric range constraint.
- [ ] Boundary tests at maxLength for every string length constraint.
- [ ] At least one empty-array test if the service accepts array inputs.
- [ ] Boolean toggle tests if the service branches on a boolean.
- [ ] All test case IDs are unique.
- [ ] `expected_output` field names match the exact output variable names in the I/O contract.
- [ ] `expected_error.code` values (where specified) match the exact fault codes declared in the contract.
