# BAW REST API Reference

---


## IBM Business Automation Workflow Operations REST Interface
*Source: `apis/baw-ops.26.0.0.json`*

### `POST /ops/system/login`
**Obtain IBM Business Automation Workflow CSRF prevention token**

Obtain a CSRF prevention token and optionally refresh the user's group membership information.

**Parameters:**
- `login_request` (body, ) *(required)* — Mandatory parameter that allows you to specify whether the caller's group membership data is refreshed

**Responses:**
- `201` — The request was processed successfully and returned a new CSRF token
- `400` — Invalid input.
- `500` — Internal server error.

---

### `DELETE /ops/std/bpm/processes`
**Delete specified process instances.**

Deletes the specified process instances according to their states, completion dates, process models, or process instance identifiers. This operation is asynchronous. Messages for this operation are available only in the system log. Only Business Automation Workflow administrators are authorized to p...

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `states` (query, array) *(required)* — A comma-separated list of states. To delete process instances that are not in an end state, set the 'force' parameter to
- `force` (query, boolean) — Set this parameter to the value 'true' if you want to delete process instances regardless of whether they are in an end 
- `container` (query, string) — The acronym of the process application for which process instances are deleted.
- `versions` (query, array) — A comma-separated list of snapshot acronyms for which process instances are deleted. This parameter is only valid if the
- `ended_before` (query, string) — Only process instances that completed before this point in time are deleted. Specify the time in ISO 8601 format 'yyyy-M
- `ended_after` (query, string) — Only process instances that completed after this point in time are deleted. Specify the time in ISO 8601 format 'yyyy-MM
- `process_ids` (query, array) — A comma-separated list of process instance identifiers.
- `transaction_slice` (query, integer) — Specifies the number of instances that are deleted per transaction. The default value is 10.

**Responses:**
- `202` — The request to delete the specified process instances was submitted. To check the progress of the operation, use the 'GET /system/queue/{id}' resource to access the URL that is included in the response.
- `204` — No instances that match the request were found to delete.
- `400` — The request contains parameters that are not valid, or they are missing.
- `403` — The caller is not authorized to perform the request.
- `500` — Internal server error.

---

### `GET /ops/std/bpm/processes/count`
**Retrieve a count of process instances.**

Tells you how many process instances match the specified criteria. Only Business Automation Workflow administrators are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `states` (query, array) — A comma-separated list of states. Restricts the results to instances that are in the specified states. Valid values are:
- `containers` (query, array) — A comma-separated list of containers. Restricts the results to instances that belong to the specified process applicatio
- `versions` (query, array) — A comma-separated list of snapshot acronyms. Restricts the results to instances that belong to the specified snapshots.
- `model` (query, string) — The name of the process model. Restricts the results to instances of the specified process model.
- `ended_before` (query, string) — Only process instances that completed before this point in time are returned. Specify the time in ISO 8601 format 'yyyy-
- `ended_after` (query, string) — Only process instances that completed after this point in time are returned. Specify the time in ISO 8601 format 'yyyy-M
- `search_term` (query, string) — A string that uses the given term to filters the process instances that are returned.
- `process_ids` (query, array) — A comma-separated list of process instance identifiers. Restricts the results to instances with the specified process ID

**Responses:**
- `200` — The request was processed successfully and returned the number of process instances that match the specified query parameters.
- `400` — The request contains parameters that are not valid, or they are missing.
- `403` — The caller is not authorized to perform the request.
- `500` — Internal server error.

---

### `DELETE /ops/adv/bpm/processes`
**Delete specified BPEL process instances.**

Deletes specified BPEL process instances according to their process instance states, process models, valid-from dates, completion dates, or according to which user started the process instance. This operation is asynchronous. You can find messages for this operation only in the system log. For more ...

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `states` (query, array) — A comma-separated list of states. The default is that all instances in state finished, terminated or failed are deleted.
- `model` (query, string) — The process template name of the BPEL processes to delete.
- `valid_from` (query, string) — Only process instances of a process template that is valid from this point in time are deleted. Specify the time in ISO 
- `ended_before` (query, string) — Only process instances that completed before this point in time are deleted. Specify the time in ISO 8601 format 'yyyy-M
- `ended_after` (query, string) — Only process instances that completed after this point in time are deleted. Specify the time in ISO 8601 format 'yyyy-MM
- `starter` (query, string) — The user ID of the user who started the process instance.

**Responses:**
- `202` — The request to delete the specified process instances was submitted. To check the progress of the operation, use the 'GET /system/queue/{id}' resource to access the URL that is included in the response.
- `204` — No instances matching the request were found to delete.
- `400` — The request contains parameters that are not valid, or they are missing.
- `403` — The caller is not authorized to perform the request.
- `500` — Internal server error.
- `501` — Not implemented.
- `503` — Service unavailable.
