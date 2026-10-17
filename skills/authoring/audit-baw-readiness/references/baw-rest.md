# BAW REST API reference

---


## IBM Business Automation Workflow operations REST interface

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

### `POST /ops/std/bpm/containers/{container}/versions`
**Create snapshots of process applications or toolkits.**

Creates snapshots of process apps or toolkits on the Workflow Center server. You might want to use this API to automate the creation of an offline backup of the current snapshots of your process apps and toolkits. You can use the API for only one process app or toolkit at a time. Only Business Automation Workflow administrators or users with project write permission are authorized to perform this call.

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

Retrieves information about all the snapshots or a subset of the snapshots of a specific process app or toolkit on the Workflow Center server or Workflow Server. Only Business Automation Workflow administrators users with project read permission are authorized to perform this call. Note: For Workflow Center only named snapshots are returned.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit.
- `version_ids` (query, array) — A comma-separated list of snapshot IDs. This parameter restricts the results to the snapshots with the specified IDs.
- `branch` (query, string) — Specify the track acronym to view only those snapshots that belong to the track. If a track is not specified, all the snapshots of the specified process application or toolkit are returned.
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

Deletes process app or toolkit snapshots that match the specified criteria. Having too many snapshots might cause your system to slow down. If that occurs, on Workflow Server find and delete inactive snapshots that don't have running instances and are not deployed. On a Workflow Center server, archive named snapshots. Delete unnamed and archived snapshots when they are obsolete. This operation is asynchronous and returns a URL that you can use to monitor the status of the call. However, this operation doesn't support parallel execution. Because only one snapshot delete operation can occur at a time, ensure the status of the operation is 'success' before invoking the next snapshot delete operation. Messages for this operation are available only in the system log. Only Business Automation Workflow administrators are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs
- `container` (path, string) *(required)* — The acronym of the process application or toolkit.
- `branch_name` (query, string) — Workflow Center server only. The name of the track that is associated with the process application or toolkit. If this parameter is not specified, the default track is used.
- `versions` (query, array) — Required for Workflow Server. Optional for Workflow Center server. Use a comma-separated list to specify multiple snapshot acronyms. For a Workflow Center server, if this parameter is specified, you cannot specify any other filters, such as values for the kept_number, created_before, created_after, created_before_version, or delete_archived parameters.
- `force` (query, boolean) — Workflow Server only. To delete the last and default snapshot of a process application, set this value to 'true'. The default snapshot can be deleted only if it is the last existing snapshot of the process application. When its last snapshot is deleted, the process application is removed.
- `kept_number` (query, integer) — Workflow Center server only. This parameter specifies the number of unnamed snapshots to keep when a snapshot cleanup is run. The most recent snapshots are kept. The tip snapshot is not counted in kept_number. If kept_number is greater than or equal to the total number of unnamed snapshots, no snapshots are deleted. If kept_number equals 0, all the unnamed snapshots are deleted except the tip snapshot. The kept_number parameter cannot be specified with the created_before or created_after parameters.
- `created_before` (query, string) — Workflow Center server only. This parameter specifies the time before which all unnamed snapshots must be deleted. Specify the time in ISO 8601 format 'yyyy-MM-dd'T'HH:mm:ss.sssz'.
- `created_after` (query, string) — Workflow Center server only. This parameter specifies the time after which all unnamed snapshots must be deleted. Specify the time in ISO 8601 format 'yyyy-MM-dd'T'HH:mm:ss.sssz'.
- `created_before_version` (query, string) — Workflow Center server only. This parameter specifies the acronym of a named snapshot. Unnamed snapshots are deleted if they were created before the specified snapshot. When created_before_version is used with the kept_number parameter, the specified number of snapshots is retained. When created_before_version is used with the created_before or created_after parameters, unnamed snapshots are deleted that were created between the time when the named snapshot was created and the time that is specified by the created_before or created_after parameter.
- `delete_archived` (query, boolean) — Workflow Center server only. To delete archived snapshots and unnamed snapshots that match the filter criteria, set this value to 'true'.
- `caseDosName` (query, string) — Workflow Server only. If you are removing the last snapshot off a server, specify the case design object store name if the content engine is not using the default name 'dos'.
- `continueOnError` (query, boolean) — Workflow Server only. This parameter indicates whether the operation should continue even if an error occurs while deleting one or more versions. When set to 'true', the API will attempt to process all items in the request, skipping over any errors encountered and proceeding with the next item. If set to 'false' (default behaviour), the operation will halt upon encountering the first error, and no further items will be processed. The 'versions' parameter must also be speicied. Refer to the system log to view specific results of which versions were successfully deleted and which encountered errors.

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

Enables the exchange of a process app or toolkit between Workflow Center servers. This API exports a specified process app snapshot or toolkit snapshot as a .twx file that you can import into a Workflow Center server. The suggested file name is URL-encoded in the Content-Disposition HTTP response header. Only Business Automation Workflow administrators or users with project read permission are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit associated with the specified snapshot.
- `version` (path, string) *(required)* — The acronym of the snapshot to be exported.
- `format` (query, string) — The format of the export. If the value is not specified, system toolkits are exported. A value of twxWithoutToolkits skips exporting system toolkits that are not versioned (the latest version is already on the server).
- `use_enhanced_filenames` (query, boolean) — A value of true produces more meaningful file names within the exported file. If the value is false or unspecified, the default internal format is used.

**Responses:**
- `200` — The specified snapshot was exported successfully.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested operation does not exist.
- `500` — Internal server error.
