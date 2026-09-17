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

### `GET /ops/std/bpm/containers/{container}/versions/{version}/export`
**Exports a specified process application snapshot or toolkit snapshot**

Enables the exchange of a process app or toolkit between Workflow Center servers. This API exports a specified process app snapshot or toolkit snapshot as a .twx file that you can import into a Workflow Center server. The suggested file name is URL-encoded in the Content-Disposition HTTP response he...

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit associated with the specified snapshot.
- `version` (path, string) *(required)* — The acronym of the snapshot to be exported.
- `format` (query, string) — The format of the export. If the value is not specified, system toolkits are exported. A value of twxWithoutToolkits ski
- `use_enhanced_filenames` (query, boolean) — A value of true produces more meaningful file names within the exported file. If the value is false or unspecified, the 

**Responses:**
- `200` — The specified snapshot was exported successfully.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested operation does not exist.
- `500` — Internal server error.

---

## IBM Business Automation Workflow REST Interface
*Source: `apis/baw-process.26.0.0.json`*

### `GET /bpm/processes`
**Retrieve a list of process instances.**

Lists the process instances that the user may see. 

Only users with the following roles are authorized to perform this call: Business Automation Workflow administrator or process application administrator.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `model` (query, string) — The name of the process model. Restricts the results to instances of the specified process model.
- `containers` (query, array) — A comma-separated list of containers acronyms. Restricts the results to instances that belong to the specified process a
- `versions` (query, array) — A comma-separated list of snapshot acronyms. Restricts the results to instances that belong to the specified snapshots.
- `states` (query, array) — A comma-separated list of states. Restricts the results to instances in the specified states. Valid values are: 'running
- `search_term` (query, string) — A string that filters the process instances returned by the given term. The search term is compared against the process 
- `sort` (query, array) — A comma-separated list of sort criteria. The order of the items determines the sorting sequence. The list entries must h
- `offset` (query, string) — In a list of entries the offset specifies the position of the first process instance to return from the query result set
- `size` (query, integer) — Maximum number of process instances to return.
- `optional_parts` (query, array) — A comma-separated list of optional parts to be returned in the response object. Valid values are: 'data', 'actions'.

**Responses:**
- `200` — The request was processed successfully and returned a list of process instance objects that match the specified query parameters.
- `400` — The request contains invalid parameters, or they are missing.
- `500` — Internal server error.

### `POST /bpm/processes`
**Start a new process instance.**

Starts a new process instance of the specified process model. 

Only members of teams assigned to the 'Expose to start' option for the process are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `model` (query, string) *(required)* — The name of the process model for which a new instance is started.
- `container` (query, string) *(required)* — The acronym of the process application that contains the process model.
- `version` (query, string) — The acronym of the process application snapshot that contains the process model. If a version is not specified, the inst
- `optional_parts` (query, array) — A comma-separated list of optional parts to be returned in the response object. Valid values are: 'data', 'actions'.
- `input` (body, ) — Values for process variables.
- `branch_name` (query, string) — The name of the branch of the process application that contains the process model.

**Responses:**
- `201` — The request was processed successfully and returned the newly created process instance.
- `400` — The request contains invalid parameters, or they are missing.
- `403` — The caller is not authorized to perform the request.
- `409` — The request cannot be processed because of one or more conflicts in the request.
- `500` — Internal server error.

---

### `GET /bpm/processes/{process_id}`
**Retrieve a process instance.**

Retrieves detailed information about a process instance. 

Only users with the following roles or statuses are authorized to perform this call: Business Automation Workflow administrator, process application administrator, instance owner, follower of the instance, tagged in the instance, or members ...

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `process_id` (path, string) *(required)* — The ID of the process instance.
- `optional_parts` (query, array) — A comma-separated list of optional parts to be returned in the response object. Valid values are: 'data', 'actions'.

**Responses:**
- `200` — The request was processed successfully and returned the requested process instance object.
- `400` — The request contains invalid parameters, or they are missing.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `500` — Internal server error.

### `DELETE /bpm/processes/{process_id}`
**Delete a process instance.**

Deletes a process instance. 

Only users with the following roles are authorized to perform this call: Business Automation Workflow administrator, process application administrator, or instance owner.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `process_id` (path, string) *(required)* — The ID of the process instance to delete.

**Responses:**
- `204` — The specified process instance was deleted.
- `400` — The request contains invalid parameters, or they are missing.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `409` — The request cannot be processed because of one or more conflicts in the request.
- `500` — Internal server error.

---

### `GET /bpm/user-tasks`
**Retrieve a list of user task instances.**

Lists user task instances that the user may see. 

Only users with the following roles are authorized to perform this call: Business Automation Workflow administrator, task owner, or a potential task owner for unclaimed tasks.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `model` (query, string) — The name of the process model for which user task instances are returned.
- `process_id` (query, string) — The ID of the process instance for which user task instances are returned.
- `states` (query, array) — A comma-separated list of user task states. Valid values are: 'claimed', 'ready', 'completed', 'terminated', 'suspended'
- `offset` (query, string) — In a list of entries offset specifies the position of the first user task instance to return from the query result set.
- `size` (query, integer) — The maximum number of user task instances to be returned.
- `optional_parts` (query, array) — A comma-separated list of optional parts to be returned in the response object. Valid values are: 'data', 'actions', 'te
- `sort` (query, array) — A comma-separated list of sort criteria. The order of the items determines the sorting sequence. The list entries must h

**Responses:**
- `200` — The request was processed successfully and returned a list of user task instance objects that match the specified query parameters.
- `400` — The request contains invalid parameters, or they are missing.
- `500` — Internal server error.

---

### `GET /bpm/user-tasks/{task_id}`
**Retrieve a user task instance.**

Retrieves details of a specific user task instance. 

Only users with the following roles are authorized to perform this call: Business Automation Workflow administrator, process application administrator, instance owner, task team manager, task owner, or a potential task owner, collaborator.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `task_id` (path, string) *(required)* — User task instance ID.
- `optional_parts` (query, array) — A comma-separated list of optional parts to be returned in the response object. Valid values are: 'data', 'actions', 'te

**Responses:**
- `200` — The request was processed successfully and returned a user task instance object with details of the specified user task instance.
- `400` — The request contains invalid parameters, or they are missing.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `500` — Internal server error.

---

### `POST /bpm/user-tasks/{task_id}/claim`
**Claim a user task instance.**

Claims a user task instance. 

Only users with the following roles are authorized to perform this call: Business Automation Workflow administrator, process application administrator, or a potential task owner if an owner is not assigned.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `task_id` (path, string) *(required)* — User task instance ID.
- `optional_parts` (query, array) — A comma-separated list of optional parts to be returned in the response object. Valid values are: 'data', 'actions', 'te

**Responses:**
- `200` — The request was processed successfully.
- `400` — The request contains invalid parameters, or they are missing.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `409` — The request cannot be processed because of one or more conflicts in the request.
- `500` — Internal server error.

---

### `POST /bpm/user-tasks/{task_id}/complete`
**Complete a user task instance.**

Completes a user task instance. 

Only users with the following roles are authorized to perform this call: Business Automation Workflow administrator, process application administrator, instance owner, or task owner.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `task_id` (path, string) *(required)* — User task instance ID.
- `optional_parts` (query, array) — A comma-separated list of optional parts to be returned in the response object. Valid values are: 'data', 'actions', 'te
- `output` (body, ) — The data output of the specified user task instance.

**Responses:**
- `200` — The request was processed successfully.
- `400` — The request contains invalid parameters, or they are missing.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `409` — The request cannot be processed because of one or more conflicts in the request.
- `500` — Internal server error.
