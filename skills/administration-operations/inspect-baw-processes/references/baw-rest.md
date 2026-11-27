# Business Automation Workflow REST API Reference

---


## IBM Business Automation Workflow REST Interface

### `POST /bpm/system/login`
**Obtain IBM Business Automation Workflow CSRF prevention token**

Obtain a CSRF prevention token and optionally refresh the user's group membership information.

**Parameters:**
- `login_request` (body, ) *(required)* — Mandatory parameter that allows you to specify whether the caller's group membership data is refreshed

**Responses:**
- `201` — The request was processed successfully and returned a new CSRF token
- `400` — Invalid input.
- `500` — Internal server error.

---

### `GET /bpm/processes`
**Retrieve a list of process instances.**

Lists the process instances that the user may see. 

Only users with the following roles are authorized to perform this call: Business Automation Workflow administrator or process application administrator.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `model` (query, string) — The name of the process model. Restricts the results to instances of the specified process model.
- `containers` (query, array) — A comma-separated list of containers acronyms. Restricts the results to instances that belong to the specified process application acronyms.
- `versions` (query, array) — A comma-separated list of snapshot acronyms. Restricts the results to instances that belong to the specified snapshots.
- `states` (query, array) — A comma-separated list of states. Restricts the results to instances in the specified states. Valid values are: 'running', 'finished', 'terminated', 'suspended', 'stopped', 'did_not_start'.
- `search_term` (query, string) — A string that filters the process instances returned by the given term. The search term is compared against the process model name and process instance name and handled as if wildcard characters are at the beginning and end.
- `sort` (query, array) — A comma-separated list of sort criteria. The order of the items determines the sorting sequence. The list entries must have the following format: property:sort_direction. Valid values are: 'creation_time:asc', 'creation_time:desc', 'model:asc', 'model:desc', 'state:asc', 'state:desc', 'due_date:asc', 'due_date:desc'.
- `offset` (query, string) — In a list of entries the offset specifies the position of the first process instance to return from the query result set.
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
- `version` (query, string) — The acronym of the process application snapshot that contains the process model. If a version is not specified, the instance is started from the default snapshot in a Workflow Server environment and from the latest snapshot in a Workflow Center environment.
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

Only users with the following roles or statuses are authorized to perform this call: Business Automation Workflow administrator, process application administrator, instance owner, follower of the instance, tagged in the instance, or members of teams assigned to the Expose Performance Metrics option for the process.

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

## IBM Business Automation Workflow Operations REST Interface

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

### `GET /ops/system/queue/{id}`
**Obtain status of an asynchronous operation.**

Obtains information about the status of an asynchronous operation, such as group memberships that are being updated. Various REST APIs that start asynchronous operations return a URL that points to this API. Use this API to determine whether the asynchronous operation is still running, it failed, or it finished successfully and to determine the result of the operation. By default, the information about the operation is available for at least 48 hours; then it is discarded. Only Business Automation Workflow administrators or users who initiated the asynchronous call are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for Business Automation Workflow REST APIs.
- `id` (path, string) *(required)* — Identifier of the operation, obtained from the REST API that started the asynchronous operation.
- `key` (query, string) — Authorization key, obtained from the REST API that started the asynchronous operation. Administrators can query an operation status without any authorization key; in all other cases, the authorization key is mandatory to ensure that only callers who started the operation can query its status.

**Responses:**
- `200` — The status of the specified operation is returned in the response
- `400` — The request contains invalid parameter
- `403` — The caller is not authorized to perform the request.
- `404` — The requested operation does not exist.
- `500` — Internal server error.

---

### `GET /ops/std/bpm/processes/count`
**Retrieve a count of process instances.**

Tells you how many process instances match the specified criteria. Only Business Automation Workflow administrators are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `states` (query, array) — A comma-separated list of states. Restricts the results to instances that are in the specified states. Valid values are: 'finished', 'terminated', 'running', 'suspended', 'stopped', 'did_not_start'.
- `containers` (query, array) — A comma-separated list of containers. Restricts the results to instances that belong to the specified process application acronyms.
- `versions` (query, array) — A comma-separated list of snapshot acronyms. Restricts the results to instances that belong to the specified snapshots.
- `model` (query, string) — The name of the process model. Restricts the results to instances of the specified process model.
- `ended_before` (query, string) — Only process instances that completed before this point in time are returned. Specify the time in ISO 8601 format 'yyyy-MM-dd'T'HH:mm:ssz'.
- `ended_after` (query, string) — Only process instances that completed after this point in time are returned. Specify the time in ISO 8601 format 'yyyy-MM-dd'T'HH:mm:ssz'.
- `search_term` (query, string) — A string that uses the given term to filters the process instances that are returned.
- `process_ids` (query, array) — A comma-separated list of process instance identifiers. Restricts the results to instances with the specified process IDs.

**Responses:**
- `200` — The request was processed successfully and returned the number of process instances that match the specified query parameters.
- `400` — The request contains parameters that are not valid, or they are missing.
- `403` — The caller is not authorized to perform the request.
- `500` — Internal server error.

---

### `DELETE /ops/std/bpm/processes`
**Delete specified process instances.**

Deletes the specified process instances according to their states, completion dates, process models, or process instance identifiers. This operation is asynchronous. Messages for this operation are available only in the system log. Only Business Automation Workflow administrators are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `states` (query, array) *(required)* — A comma-separated list of states. To delete process instances that are not in an end state, set the 'force' parameter to 'true'. Valid values are: 'finished', 'terminated', 'running', 'suspended', 'stopped', 'did_not_start'.
- `force` (query, boolean) — Set this parameter to the value 'true' if you want to delete process instances regardless of whether they are in an end state.
- `container` (query, string) — The acronym of the process application for which process instances are deleted.
- `versions` (query, array) — A comma-separated list of snapshot acronyms for which process instances are deleted. This parameter is only valid if the container parameter is specified.
- `ended_before` (query, string) — Only process instances that completed before this point in time are deleted. Specify the time in ISO 8601 format 'yyyy-MM-dd'T'HH:mm:ssz'.
- `ended_after` (query, string) — Only process instances that completed after this point in time are deleted. Specify the time in ISO 8601 format 'yyyy-MM-dd'T'HH:mm:ssz'.
- `process_ids` (query, array) — A comma-separated list of process instance identifiers.
- `transaction_slice` (query, integer) — Specifies the number of instances that are deleted per transaction. The default value is 10.

**Responses:**
- `202` — The request to delete the specified process instances was submitted. To check the progress of the operation, use the 'GET /system/queue/{id}' resource to access the URL that is included in the response.
- `204` — No instances that match the request were found to delete.
- `400` — The request contains parameters that are not valid, or they are missing.
- `403` — The caller is not authorized to perform the request.
- `500` — Internal server error.

---

### `POST /ops/std/bpm/processes/resume`
**Resume suspended process instances.**

Resume suspended process instances belonging to the specified container and snapshot. This command can not be used to resume instances that belong to a tip. This operation is asynchronous. Only Business Automation Workflow administrators and authors are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — A cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `container` (query, string) *(required)* — The acronym of the process application process instances are to be resumed for.
- `version` (query, string) *(required)* — The acronym of the snapshot process instances are to be resumed for.
- `max_instances` (query, integer) — The maximum number of instances to resume (between 1 and 2147483647). If this parameter is not set, all suspended instances belonging to the specified container and version are resumed. When the 'get_instances' parameter is set, this command is mutually exclusive.
- `get_instances` (query, boolean) — If set to true, this parameter return the number of suspended instances belonging to the specified container and version. When the 'max_instances' parameter is set, this command is mutually exclusive.

**Responses:**
- `202` — The request to resume the specified on-hold process instances was submitted. To check the progress of the operation, use the 'GET /system/queue/{id}' resource to access the URL that is included in the response.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `500` — Internal server error.

---

### `DELETE /ops/adv/bpm/processes`
**Delete specified BPEL process instances.**

Deletes specified BPEL process instances according to their process instance states, process models, valid-from dates, completion dates, or according to which user started the process instance. This operation is asynchronous. You can find messages for this operation only in the system log. For more information about which roles are authorized to perform this call, see the documentation.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `states` (query, array) — A comma-separated list of states. The default is that all instances in state finished, terminated or failed are deleted. Valid values are: 'failed', 'finished', 'terminated'.
- `model` (query, string) — The process template name of the BPEL processes to delete.
- `valid_from` (query, string) — Only process instances of a process template that is valid from this point in time are deleted. Specify the time in ISO 8601 format 'yyyy-MM-dd'T'HH:mm:ssz'. This parameter is only valid if the model parameter is specified.
- `ended_before` (query, string) — Only process instances that completed before this point in time are deleted. Specify the time in ISO 8601 format 'yyyy-MM-dd'T'HH:mm:ssz'.
- `ended_after` (query, string) — Only process instances that completed after this point in time are deleted. Specify the time in ISO 8601 format 'yyyy-MM-dd'T'HH:mm:ssz'.
- `starter` (query, string) — The user ID of the user who started the process instance.

**Responses:**
- `202` — The request to delete the specified process instances was submitted. To check the progress of the operation, use the 'GET /system/queue/{id}' resource to access the URL that is included in the response.
- `204` — No instances matching the request were found to delete.
- `400` — The request contains parameters that are not valid, or they are missing.
- `403` — The caller is not authorized to perform the request.
- `500` — Internal server error.
- `501` — Not implemented.
- `503` — Service unavailable.

---

## IBM Business Automation Workflow WLE v1 REST Interface

### `GET /rest/bpm/wle/v1/exposed`
**Get launchable items (NF — exposed processes and services)**

Returns the list of exposed process applications, services, and case types the authenticated user is authorized to start. This is the correct non-federated endpoint — do not use /rest/bpm/wle/v1/launchableEntities (that is the federated PFS path). Response: data.exposedItemsList[] with itemID, snapshotID, processAppID, type, startURL. IMPORTANT: Do not pass itemID, processAppID, or snapshotID directly to action=start — parse bpdId and processAppId from the startURL query string. Evidence: VERIFIED IN ON-PREM Business Automation Workflow (NF09, NF22). Auth: session cookie. Deployment: NF.

**Responses:**
- `200` — Exposed items list. Response: data.exposedItemsList[] with itemID, snapshotID, processAppID, type, startURL.
- `401` — Authentication required.

---

### `GET /rest/bpm/wle/v1/processes/search`
**Search process instances**

Retrieves a list of BPD instances and the number of instances per status. Response envelope: data.processes[] (bpdName, piid, name, executionState, snapshotId, lastModificationTime, instanceError on failed instances) and data.overview (counts per status plus Total). Admins (bpmAdminGroup, tw_admins by default) see all instances; members of a team in the Process Application Administrators setting see instances of that app; other users see only a scoped subset when includeNonAdmin=true. statusFilter accepts Active, Completed, Failed, Terminated, Suspended, Late, At_Risk (comma-separated for several). projectFilter takes process app acronyms (comma-separated). Dates are ISO 8601, for example 2011-08-04T03:12:53Z. Evidence: DOCUMENTED (restbpm.xml, since 8.5.6); response envelope also VERIFIED IN ON-PREM Business Automation Workflow (Cloud Pak for Business Automation 26.0.0, see create-baw-portal 04-api-inventory.md). Auth: session cookie. Deployment: NF.

**Parameters:**
- `modifiedAfter` (query, string) — Include only instances modified on or after this ISO 8601 date.
- `modifiedBefore` (query, string) — Include only instances modified on or before this ISO 8601 date.
- `createdAfter` (query, string) — Include only instances created on or after this ISO 8601 date.
- `createdBefore` (query, string) — Include only instances created on or before this ISO 8601 date.
- `closedAfter` (query, string) — Include only instances closed on or after this ISO 8601 date.
- `closedBefore` (query, string) — Include only instances closed on or before this ISO 8601 date.
- `userFilter` (query, string) — Include only instances associated with the specified user.
- `searchFilter` (query, string) — Match instance name, process app short name, or both. searchFilterScope selects which.
- `searchFilterScope` (query, string) — Scope of searchFilter. Default is Both.
- `statusFilter` (query, string) — Return only instances with these statuses: Active, Completed, Failed, Terminated, Suspended, Late, At_Risk. Comma-separate for several, for example Active,Late,Failed,At_Risk.
- `projectFilter` (query, string) — Return instances of the specified process apps, identified by acronym (short name). Comma-separate for several, for example APP1,APP2.
- `limit` (query, integer) — Maximum number of instance summaries to return. All are returned by default.
- `offset` (query, integer) — Number of instance summaries to skip. Default starts at the first.
- `sortBy` (query, string) — Sort type. Default is lastModified.
- `includeNonAdmin` (query, boolean) — For non-admin users: true includes instances the current user can view. Default is false.
- `startedByMe` (query, boolean) — True returns only instances started by the current user. Default is false.

**Responses:**
- `200` — Search results: data.processes[] and data.overview.
- `400` — Parameters are not valid or are missing.
- `401` — The caller is not authorized for this request.
- `406` — The requested content type or encoding is not supported.
- `500` — A severe problem has occurred.

---

### `GET /rest/bpm/wle/v1/process/{instanceId}`
**Get process instance details**

Retrieves the details of one process instance: header and summary (name, executionState, state, dueDate, piid), business data and variables (data), open tasks (tasks[], paged with taskLimit/taskOffset), attached documents (documents[]), and optionally available actions. With the default parts=all, everything except the Actions section is returned; add actions to see which lifecycle actions the current user can perform. Use parts=excludeDocs to omit ECM documents. Evidence: DOCUMENTED (restbpm.xml, since 7.5.0). Auth: session cookie. Deployment: NF.

**Parameters:**
- `instanceId` (path, string) *(required)* — Process instance identifier (piid), for example from data.processes[].piid in a /processes/search response.
- `parts` (query, string) — Parts of the response to return. Separate several with '|'. Values: header, summary, data, diagram, executionTree, actions, relationships, excludeTaskData, excludeDocs, all (default, everything except actions), none.
- `taskLimit` (query, integer) — Maximum number of task instances to return. Zero or negative means no limit.
- `taskOffset` (query, integer) — Number of task instances to skip, counting from 0.

**Responses:**
- `200` — Process instance details (ProcessDetails).
- `400` — Invalid parameters.
- `401` — The caller is not authorized for this request.
- `404` — The process does not exist.
- `500` — A severe problem has occurred.

### `PUT /rest/bpm/wle/v1/process/{instanceId}`
**Suspend, resume, terminate, retry, or update the due date of a process instance**

Performs a lifecycle action on one process instance, selected by the action query parameter. action=suspend, resume, terminate, or retry changes the instance state. action=update changes the due date and also requires dueDate. For action=update, dueDate may be sent as a query parameter or in a JSON request body, but not both. restbpm.xml documents these as separate PUT methods on this path and marks POST as an accepted alternative method. parts controls what the returned ProcessDetails contains (default all). Deleting an instance uses DELETE with action=delete and is not covered here. Evidence: DOCUMENTED (restbpm.xml, since 7.5.0). The due date is returned normalized to UTC, even when sent with an offset. Auth: session cookie. Deployment: NF.

**Parameters:**
- `instanceId` (path, string) *(required)* — Process instance identifier (piid).
- `action` (query, string) *(required)* — suspend halts an active instance; resume restarts a suspended one; terminate ends an instance permanently; retry re-runs a failed instance; update changes the due date and requires dueDate.
- `dueDate` (query, string) — Required when action=update. New due date as an ISO 8601 timestamp with timezone or offset, for example 2026-11-12T17:08:00Z or 2026-11-03T06:00:00-05:00. URL-encode the colons and plus sign. May instead be sent in a JSON request body, but not both.
- `parts` (query, string) — Parts of the response to return. Separate several with '|'. Values: header, summary, data, dataModel, diagram, executionTree, actions, relationships, excludeDocs, all (default), none.

**Responses:**
- `200` — Action performed. Returns the updated process instance details (ProcessDetails).
- `400` — Invalid parameters: unknown action (CWTBG0010E) or missing dueDate for action=update (CWTBG0023E).
- `401` — The caller is not authorized for this request.
- `404` — The process does not exist.
- `409` — The instance state does not allow the requested action (CWTBG0014E), for example resume or retry on an Active instance.
- `500` — A severe problem has occurred.
