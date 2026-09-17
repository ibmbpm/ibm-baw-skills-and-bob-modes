# Test Generation — Artifact Analysis Instructions

This file contains the detailed instructions for **Phase A** of the `generate-baw-tests` skill.
It is split by artifact type. Read the section that matches the artifacts being tested.

---

## Table of contents

1. [How to acquire and parse TWX artifacts](#1-acquiring-and-parsing-twx-artifacts)
2. [Process test generation](#2-process-test-generation)
3. [Coach test generation](#3-coach-test-generation)
4. [Coverage checklist](#4-coverage-checklist)

---

## 1. Acquiring and parsing TWX artifacts

### Via REST export

1. Call `GET /std/bpm/containers/{container}/versions/{version}/export?use_enhanced_filenames=true`.
2. The response is a binary `.twx` file (which is a ZIP). Save it and unzip it.
3. Read the extracted XML files as described below.

### What to look for in the XML

When enhanced filenames are used, files follow a pattern like:
- `objects/<ProcessName>_BPD.xml` — process definition
- `objects/<CoachName>_Coach.xml` — coach definition  
- `objects/<ObjectName>_BusinessObject.xml` — business object / variable type

If the user pastes raw XML or provides file content directly, parse it inline — no fetch needed.

---

## 2. Process test generation

### 2.1 What to extract from the process definition XML

Parse the process model and extract:

| Element | What to capture |
|---|---|
| **Process name and ID** | The authoritative name for test case IDs and `app.process_model` |
| **Start event** | Input variable types and their required fields |
| **User tasks** | Task name, lane (role), input/output variable mappings |
| **System tasks / services** | Name and whether they can fail (error boundary attached?) |
| **Gateways** | Type (exclusive, parallel, inclusive), conditions on each outgoing sequence flow |
| **Error boundary events** | Which task they attach to, what error code they catch |
| **Timer boundary events** | Task, timeout duration, escalation path |
| **End events** | Number of distinct end events and their labels (e.g. "Approved", "Rejected", "Cancelled") |
| **Process data (variables)** | All private variables with their types and whether they are required |

### 2.2 Path enumeration

For each exclusive gateway, enumerate every outgoing path separately. For parallel gateways, enumerate the join as a single combined path (parallel paths are not separate test cases).

For each path, trace it from the start event to one end event. Write that path down as an ordered list of task names with the gateway conditions that must be true to reach each branch.

**Minimum required paths:**
- One happy-path trace (all approvals granted, all thresholds met, reaches the primary "success" end event).
- One trace per alternative branch created by each exclusive gateway.
- One trace per error boundary event that has a distinct recovery flow.
- One trace per timer/escalation path if the timeout has a distinct outcome.

### 2.3 Test case authoring — Process

For each path, create one test case. Fill in the fields as follows:

**`input.data`** — Set variables to values that will route the process down the intended path. For the happy path, use the minimal valid set of values. For alternative paths, change only the variables that drive the gateway decision.

**`steps`** — Walk the path from start to end event. Each user task the path reaches becomes one step. For system tasks that are transparent to the test (no user interaction, no branching), skip them in the step list — they will run automatically.

**`expected_outcome`** — Set `final_status` to `Completed` unless the path ends at a specific error or timeout outcome. Set `output_variables` to the variables that should be set at the end of the instance.

**Naming convention:**
- `TC-001` — happy path
- `TC-002`, `TC-003`, ... — alternative paths in gateway order (left-to-right / top-to-bottom as modeled)
- `TC-ERR-001`, `TC-ERR-002` — error paths
- `TC-EDGE-001`, `TC-EDGE-002` — boundary/edge cases

### 2.4 Boundary and edge cases — Process

After covering all structural paths, consider the following edge cases:

| Scenario | What to test |
|---|---|
| **Null optional field** | Start the process with an optional variable omitted — verify the process still starts and routes correctly |
| **Empty list variable** | Pass an empty array where a list variable is expected — verify graceful handling |
| **Threshold boundary** | For any numeric gateway condition (e.g. `amount > 10000`), create two tests: one at `10000` (boundary, goes to lower path) and one at `10001` (boundary + 1, goes to upper path) |
| **Maximum string length** | If a variable has a known max length, test exactly at the limit and one character over |
| **Same-day dates** | If the process has a date comparison (e.g. due date vs. today), test the case where both dates are the same |
| **Role boundary** | If the process routes differently based on the initiating user's group, include a test case for a user at the boundary between two roles |

---

## 3. Coach test generation

Coach tests are static — they validate UI field behaviour from the artifact definition. They do not require a running process instance. The skill generates coach test cases as part of the test suite; execution is manual.

### 3.1 What to extract from coach definition XML

Parse the coach XML and extract:

| Element | What to capture |
|---|---|
| **Coach view name** | Used in the test case header |
| **Fields** | Each input element: ID/binding, label, field type (text, dropdown, date, checkbox, etc.) |
| **Required bindings** | Fields with `required="true"` or a required validator configured |
| **Read-only conditions** | Fields that become read-only under a visibility/configuration binding |
| **Hidden conditions** | Fields that are hidden when a binding variable has a certain value |
| **Validation rules** | Min/max length, regex pattern, custom validation service calls |
| **Default values** | Pre-populated field values from a configuration option |
| **User actions** | Buttons (OK, Submit, Save Draft, etc.) and which coach event they fire |
| **Boundary conditions** | Any configured min/max numeric range or date range |

### 3.2 Test case authoring — Coach

For each coach view (or sub-view if the Coach is composed of nested views), create a test case of `type: coach`. Populate `coach_assertions` with one assertion object per identifiable rule.

**Mandatory assertions to generate:**

1. **Required field validation** — for every field marked as required, assert that leaving it blank and clicking the primary submit button produces a validation error.
2. **Hidden/shown by condition** — for every conditional visibility rule, assert the field is hidden when the driving variable is set to the hiding value and visible when set to the showing value.
3. **Read-only by condition** — assert the field is not editable when the driving variable takes the read-only value.
4. **Validation constraint** — for every regex, min/max length, or numeric range constraint, write one assertion for a value that should pass and one for a value that should fail.
5. **Default value** — for every field with a configured default, assert that the default appears without the user entering a value.

**Format each assertion as:**
```json
{
  "field_id": "binding path as referenced in the XML",
  "field_label": "Label shown in the UI",
  "assertions": [
    {
      "assertion_type": "required",
      "condition": "Always",
      "expected": "Validation error shown when field is empty and form is submitted",
      "test_data": ""
    }
  ]
}
```

### 3.3 Coach edge cases

| Scenario | What to check |
|---|---|
| **All optional fields left blank** | The form can be submitted without error |
| **Special characters in text fields** | Fields accept (or correctly reject) `< > & " '` and multi-byte characters |
| **Date in the past** | If a date field has a "must be future date" rule, test with yesterday's date |
| **Maximum field length** | Paste a string exactly at the field's max character limit; verify no error. Then exceed it by one character; verify the error appears. |
| **Concurrent visibility conditions** | When two visibility conditions interact (e.g. Field B is hidden when A=true AND C=true), test both conditions independently and in combination. |

---

## 4. Coverage checklist

Before finalizing the test suite, verify:

- [ ] Happy path test case exists
- [ ] One test case per exclusive gateway branch (not just the happy path branch)
- [ ] At least one error/boundary-event path covered (if the process has them)
- [ ] At least one edge case per numeric threshold or date comparison (boundary + 1)
- [ ] Coach required-field assertions generated for every required field
- [ ] Coach conditional visibility assertions generated for every visibility rule
- [ ] All test case IDs are unique
- [ ] All `task_name` values in steps match the exact BPMN task label (copy-paste from XML, do not paraphrase)
- [ ] `app.process_model` matches the exact process name as defined in BAW
