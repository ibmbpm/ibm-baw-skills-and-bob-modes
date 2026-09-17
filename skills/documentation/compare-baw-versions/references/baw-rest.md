# BAW REST API reference

---


## IBM Business Automation Workflow operations REST interface
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

### `GET /ops/std/bpm/containers`
**Retrieve a list of all process applications and toolkits.**

Retrieves a list of all process applications and toolkits on the Workflow Center server or Workflow Server that the user may see. Only Business Automation Workflow users are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs.
- `type` (query, string) — Valid values (mutually exclusive): 'PA', 'TK'. Specify 'PA' to view only process applications and 'TK' to view only tool
- `ids` (query, array) — A comma-separated list of IDs of process applications or toolkits. This parameter restricts the results to the process a
- `offset` (query, integer) — In a list of entries, the offset specifies the position of the first process application or toolkit to return from the q
- `size` (query, integer) — Maximum number of process applications or toolkits to return.
- `optional_parts` (query, array) — Valid values: 'branches', 'versions'. Specify 'branches' to see the list of tracks in a process application or toolkit. 

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

### `POST /ops/std/bpm/containers/{container}/versions`
**Create snapshots of process applications or toolkits.**

Creates snapshots of process apps or toolkits on the Workflow Center server. You might want to use this API to automate the creation of an offline backup of the current snapshots of your process apps and toolkits. You can use the API for only one process app or toolkit at a time. Only Business Autom...

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit.
- `version_details` (body, ) *(required)* — The body parameters for creating a new snapshot.

**Responses:**
- `200` — The specified snapshot was created successfully.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested operation does not exist.
- `500` — Internal server error.

### `GET /ops/std/bpm/containers/{container}/versions`
**Retrieve information about all the snapshots or a subset of the snapshots.**

Retrieves information about all the snapshots or a subset of the snapshots of a specific process app or toolkit on the Workflow Center server or Workflow Server. Only Business Automation Workflow administrators users with project read permission are authorized to perform this call. Note: For Workflo...

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit.
- `version_ids` (query, array) — A comma-separated list of snapshot IDs. This parameter restricts the results to the snapshots with the specified IDs.
- `branch` (query, string) — Specify the track acronym to view only those snapshots that belong to the track. If a track is not specified, all the sn
- `offset` (query, integer) — In a list of entries, the offset specifies the position of the first snapshot to return from the query result set.
- `size` (query, integer) — Maximum number of snapshots to return.

**Responses:**
- `200` — The information was successfully retrieved.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `500` — Internal server error.

### `DELETE /ops/std/bpm/containers/{container}/versions`
**Delete snapshots of process applications or toolkits.**

Deletes process app or toolkit snapshots that match the specified criteria. Having too many snapshots might cause your system to slow down. If that occurs, on Workflow Server find and delete inactive snapshots that don't have running instances and are not deployed. On a Workflow Center server, archi...

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `container` (path, string) *(required)* — The acronym of the process application or toolkit.
- `branch_name` (query, string) — Workflow Center server only. The name of the track that is associated with the process application or toolkit. If this p
- `versions` (query, array) — Required for Workflow Server. Optional for Workflow Center server. Use a comma-separated list to specify multiple snapsh
- `force` (query, boolean) — Workflow Server only. To delete the last and default snapshot of a process application, set this value to 'true'. The de
- `kept_number` (query, integer) — Workflow Center server only. This parameter specifies the number of unnamed snapshots to keep when a snapshot cleanup is
- `created_before` (query, string) — Workflow Center server only. This parameter specifies the time before which all unnamed snapshots must be deleted. Speci
- `created_after` (query, string) — Workflow Center server only. This parameter specifies the time after which all unnamed snapshots must be deleted. Specif
- `created_before_version` (query, string) — Workflow Center server only. This parameter specifies the acronym of a named snapshot. Unnamed snapshots are deleted if 
- `delete_archived` (query, boolean) — Workflow Center server only. To delete archived snapshots and unnamed snapshots that match the filter criteria, set this
- `caseDosName` (query, string) — Workflow Server only. If you are removing the last snapshot off a server, specify the case design object store name if t
- `continueOnError` (query, boolean) — Workflow Server only. This parameter indicates whether the operation should continue even if an error occurs while delet

**Responses:**
- `202` — The request to delete the specified snapshots was submitted. You can check the progress of the deletion in system log.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `405` — The requested method is not allowed on this resource.
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
