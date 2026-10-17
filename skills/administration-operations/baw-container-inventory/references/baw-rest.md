# BAW REST API Reference

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

### `GET /ops/std/bpm/containers`
**Retrieve a list of all process applications and toolkits.**

Retrieves a list of all process applications and toolkits on the Workflow Center server or Workflow Server that the user may see. Only Business Automation Workflow users are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs.
- `type` (query, string) — Valid values (mutually exclusive): 'PA', 'TK'. Specify 'PA' to view only process applications and 'TK' to view only toolkits. If the value is not set, both are returned.
- `ids` (query, array) — A comma-separated list of IDs of process applications or toolkits. This parameter restricts the results to the process applications or toolkits with the specified IDs.
- `offset` (query, integer) — In a list of entries, the offset specifies the position of the first process application or toolkit to return from the query result set.
- `size` (query, integer) — Maximum number of process applications or toolkits to return.
- `optional_parts` (query, array) — Valid values: 'branches', 'versions'. Specify 'branches' to see the list of tracks in a process application or toolkit. Specify 'versions' to see, both, the list of tracks and snapshots. Valid values are: 'branches', 'versions'.

**Responses:**
- `200` — The information was successfully retrieved.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `500` — Internal server error.

### `POST /ops/std/bpm/containers`
**Creates a process application or toolkit**

Creates a process app or toolkit. Only Business Automation Workflow authors are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs.
- `container_details` (body, ) — The body parameters for creating a new process app or toolkit.

**Responses:**
- `200` — The process app or toolkit was created successfully.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested operation does not exist.
- `500` — Internal server error.

---

### `GET /ops/std/bpm/containers/{container}`
**Retrieve process application or toolkit details.**

Retrieves detailed information for a specified process app or toolkit, including a list of all its snapshots. Only Business Automation Workflow administrators or users with project read permission are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit.
- `optional_parts` (query, array) — Valid values: 'branches' and 'versions'. Specify 'branches' to see the list of tracks in a process application or toolkit. Specify 'versions' to see, both, the list of tracks and snapshots. Valid values are: 'branches', 'versions'.

**Responses:**
- `200` — The information was successfully retrieved.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `500` — Internal server error.

### `DELETE /ops/std/bpm/containers/{container}`
**Delete a process application or toolkit.**

Deletes an archived process app or toolkit and all its snapshots from the Workflow Center server. None of them may include dependencies from other process apps. Only Business Automation Workflow administrators are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit that you want to delete.
- `ignoreLocks` (query, boolean) — Set this parameter to true to delete projects with Case features that have locked artifacts.

**Responses:**
- `204` — The process application or toolkit was successfully deleted.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `405` — The requested method is not allowed on this resource.
- `423` — The process application or toolkit contains locked artifacts.
- `500` — Internal server error.
