# inspect-baw-processes — MCP execution reference

Maps each semantic operation to its BAW Runtime MCP tool. Read this file when the skill has determined MCP is the active transport. Do not read it during REST execution.

---

## Operation → MCP tool mapping

### list_exposed_processes
```
get_exposed_processes()
```
Returns array. Each entry: `process_app_name`, `process_app_acronym`, `process_id`, `version` (has `branch_id` or `snapshot_id`, `is_tip`, `label`).

Use this to resolve a full app name to its acronym before calling `search_processes`. Also the only source of acronyms — never guess them.

**Schema error handling:** If `get_exposed_processes` fails with a schema validation error (null entries in the response), do not retry in a loop. Ask the user: *"I couldn't retrieve the process list automatically. What is the acronym for your process app?"*

### search_processes
Primary: `search_processes_by_filter(status=[...], application="{acronym}", created_after=..., created_before=..., sort_by=...)`

All parameters optional. `status` accepts a list of `ProcessStatus` values: `Active`, `Completed`, `Failed`, `Suspended`, `Terminated`, `Late`, `At_Risk`.

Returns: `process_instance_id`, `name`, `status`, `last_modified_on`, `due_date`.

Advanced (complex boolean queries only): `search_processes` — uses a `population`/`filters`/`output` DSL. Call `explain_search_processes` first to get the DSL structure. Use only when `search_processes_by_filter` cannot express the query.

### get_process_details
```
get_process_details(process_instance_id="{id}", task_limit=10, task_offset=0)
```
Returns: `meta_data` (name, status, state, start_time, due_date, instance_error), `business_data.variables` (all process variables), `tasks[]` (each with `task_instance_id`, `name`, `status`, `state`, `assigned_to`, `due_time`).

### get_process_documents
```
get_process_documents(process_instance_id="{id}")
```
Returns document names and URLs attached to the instance.

### suspend_process
```
suspend_process(process_instance_id="{id}")
```
Only call when instance status is `Active`. Returns `ProcessInstanceInfo` with `process_instance_id`, `status`, `instance_name`.

### resume_process
```
resume_process(process_instance_id="{id}")
```
Only call when instance status is `Suspended`.

### retry_process
```
retry_process(process_instance_id="{id}")
```
Only call when instance status is `Failed`.

### modify_process_due_date
```
modify_process_due_date(process_instance_id="{id}", due_date="{ISO8601 with timezone}")
```
Valid for any instance state. `due_date` must be a full ISO 8601 timestamp with timezone — e.g. `2026-07-25T12:00:00Z`. Never pass a date-only string.

### terminate_process
```
terminate_process(process_instance_id="{id}")
```
Valid for any instance state. Irreversible.

---

## system_id (federation)

All action tools accept an optional `system_id`. On standalone BAW, omit it — the MCP server routes to the configured default. In CP4BA federated deployments, `search_processes` (advanced search) returns a `system_id` per result — pass it through to the action tool for that instance. Never surface `system_id` to the user.

---

## State transition rules

| Operation | Required instance status |
|---|---|
| suspend_process | Active |
| resume_process | Suspended |
| retry_process | Failed |
| modify_process_due_date | Any |
| terminate_process | Any |

A call on an instance in the wrong state returns a BAW 400 error. Verify current status before acting if unsure.
