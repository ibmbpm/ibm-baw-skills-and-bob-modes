# BAW REST API reference

---

## IBM Business Automation Workflow operations REST interface

*Source: `apis/baw-ops.26.0.0.json`*

### `POST /ops/system/login`
**Obtain an IBM Business Automation Workflow cross-site request forgery (CSRF) prevention token**

Obtains a CSRF prevention token and optionally refreshes the user's group membership information.

**Parameters:**
- `login_request` (body) *(required)* — Mandatory parameter that specifies whether the caller's group membership data is refreshed.

**Responses:**
- `201` — The request was processed successfully and returned a new CSRF token.
- `400` — Invalid input.
- `500` — Internal server error.

---

### `GET /ops/std/bpm/containers`
**Retrieve a list of all process applications and toolkits**

Retrieves a list of all process applications and toolkits on the Workflow Center server or Workflow Server that the user can see. Only IBM Business Automation Workflow (BAW) users are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — Cross-site request forgery (CSRF) prevention token for IBM Business Automation Workflow REST APIs.
- `type` (query, string) — Valid values (mutually exclusive): `PA`, `TK`. Specify `PA` to view only process applications and `TK` to view only toolkits.
- `ids` (query, array) — A comma-separated list of IDs of process applications or toolkits. This parameter restricts the results to the specified process applications or toolkits.
- `offset` (query, integer) — In a list of entries, the offset specifies the position of the first process application or toolkit to return from the query result set.
- `size` (query, integer) — Maximum number of process applications or toolkits to return.
- `optional_parts` (query, array) — Valid values: `branches`, `versions`. Specify `branches` to see the list of tracks in a process application or toolkit.

**Responses:**
- `200` — The information was successfully retrieved.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `500` — Internal server error.

### `POST /ops/std/bpm/containers`
**Create a process application or toolkit**

Creates a process application or toolkit. Only BAW authors are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — CSRF prevention token for IBM Business Automation Workflow REST APIs.
- `container_details` (body) — The body parameters for creating a new process application or toolkit.

**Responses:**
- `200` — The process application or toolkit was created successfully.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested operation does not exist.
- `500` — Internal server error.

---

### `GET /ops/std/bpm/containers/{container}`
**Retrieve process application or toolkit details**

Retrieves detailed information for a specified process application or toolkit, including a list of all its snapshots. Only BAW administrators or users with project read permission are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — CSRF prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit.
- `optional_parts` (query, array) — Valid values: `branches`, `versions`. Specify `branches` to see the list of tracks in a process application or toolkit.

**Responses:**
- `200` — The information was successfully retrieved.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `500` — Internal server error.

### `DELETE /ops/std/bpm/containers/{container}`
**Delete a process application or toolkit**

Deletes an archived process application or toolkit and all its snapshots from the Workflow Center server. None of them can include dependencies from other process applications. Only BAW administrators are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — CSRF prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit that you want to delete.
- `ignoreLocks` (query, boolean) — Set this parameter to `true` to delete projects with case features that have locked artifacts.

**Responses:**
- `204` — The process application or toolkit was successfully deleted.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `405` — The requested method is not allowed on this resource.
- `423` — The process application or toolkit contains locked artifacts.
- `500` — Internal server error.

---

### `GET /ops/std/bpm/containers/{container}/branches`
**Retrieve a list of all tracks for a process application or toolkit**

Retrieves information about all the tracks or a subset of the tracks of a specific process application or toolkit on the Workflow Center server or Workflow Server. Only BAW administrators or users with project read permission are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — CSRF prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit.
- `ids` (query, array) — A comma-separated list of track IDs. This parameter restricts the results to the tracks with the specified IDs.
- `offset` (query, integer) — In a list of entries, the offset specifies the position of the first track to return from the query result set.
- `size` (query, integer) — Maximum number of tracks to return.
- `optional_parts` (query, array) — Valid value: `versions`. Specify this parameter to view the snapshots in a track.

**Responses:**
- `200` — The information was successfully retrieved.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `500` — Internal server error.

### `POST /ops/std/bpm/containers/{container}/branches`
**Create a new track in a process application or toolkit**

Creates a track in a process application or toolkit. Only BAW administrators or users with project write permission are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — CSRF prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit.
- `branch_details` (body) *(required)* — The body parameters for creating a new track.

**Responses:**
- `200` — The track was created successfully.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `500` — Internal server error.

---

### `POST /ops/std/bpm/containers/{container}/versions`
**Create snapshots of process applications or toolkits**

Creates snapshots of process applications or toolkits on the Workflow Center server. You can use this API to automate the creation of an offline backup of the current snapshots of your process applications and toolkits. You can use the API for only 1 process application or toolkit at a time. Only BAW administrators or users with project write permission are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — CSRF prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit.
- `version_details` (body) *(required)* — The body parameters for creating a new snapshot.

**Responses:**
- `200` — The specified snapshot was created successfully.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested operation does not exist.
- `500` — Internal server error.

### `GET /ops/std/bpm/containers/{container}/versions`
**Retrieve information about all snapshots or a subset of snapshots**

Retrieves information about all the snapshots or a subset of the snapshots of a specific process application or toolkit on the Workflow Center server or Workflow Server. Only BAW administrators or users with project read permission are authorized to perform this call.

> **Note:** For Workflow Server, this API returns only deployed snapshots.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — CSRF prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit.
- `version_ids` (query, array) — A comma-separated list of snapshot IDs. This parameter restricts the results to the snapshots with the specified IDs.
- `branch` (query, string) — Specify the track acronym to view only those snapshots that belong to the track. If a track is not specified, all snapshots are returned.
- `offset` (query, integer) — In a list of entries, the offset specifies the position of the first snapshot to return from the query result set.
- `size` (query, integer) — Maximum number of snapshots to return.

**Responses:**
- `200` — The information was successfully retrieved.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `500` — Internal server error.

### `DELETE /ops/std/bpm/containers/{container}/versions`
**Delete snapshots of process applications or toolkits**

Deletes process application or toolkit snapshots that match the specified criteria. Having too many snapshots can cause your system to slow down. If that occurs, on Workflow Server find and delete inactive snapshots that do not have running instances and are not deployed. On a Workflow Center server, archive snapshots before deleting them.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — CSRF prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit.
- `branch_name` (query, string) — Workflow Center server only. The name of the track that is associated with the process application or toolkit.
- `versions` (query, array) — Required for Workflow Server. Optional for Workflow Center server. Use a comma-separated list to specify multiple snapshot acronyms.
- `force` (query, boolean) — Workflow Server only. To delete the last and default snapshot of a process application, set this value to `true`.
- `kept_number` (query, integer) — Workflow Center server only. Specifies the number of unnamed snapshots to keep when a snapshot cleanup is performed.
- `created_before` (query, string) — Workflow Center server only. Specifies the time before which all unnamed snapshots are deleted.
- `created_after` (query, string) — Workflow Center server only. Specifies the time after which all unnamed snapshots are deleted.
- `created_before_version` (query, string) — Workflow Center server only. Specifies the acronym of a named snapshot. Unnamed snapshots created before this named snapshot are deleted.
- `delete_archived` (query, boolean) — Workflow Center server only. To delete archived snapshots and unnamed snapshots that match the filter criteria, set this value to `true`.
- `caseDosName` (query, string) — Workflow Server only. If you are removing the last snapshot from a server, specify the case design object store name if the process application includes case artifacts.
- `continueOnError` (query, boolean) — Workflow Server only. Indicates whether the operation continues if an error occurs while deleting a snapshot.

**Responses:**
- `202` — The request to delete the specified snapshots was submitted. You can check the progress of the deletion in the system log.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `405` — The requested method is not allowed on this resource.
- `500` — Internal server error.

---

### `GET /ops/std/bpm/containers/{container}/versions/{version}`
**Retrieve the information for a specified snapshot**

Retrieves detailed information about a specified process application or toolkit snapshot, including the business process management capability it uses and its development status. Only BAW administrators or users with project read permission are authorized to perform this call.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — CSRF prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit that is associated with the snapshot.
- `version` (path, string) *(required)* — The acronym of the snapshot.

**Responses:**
- `200` — The information was successfully retrieved.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested resource does not exist.
- `500` — Internal server error.

---

### `GET /ops/std/bpm/containers/{container}/versions/{version}/export`
**Export a specified process application snapshot or toolkit snapshot**

Enables the exchange of a process application or toolkit between Workflow Center servers. This API exports a specified process application snapshot or toolkit snapshot as a Teamworks Exchange (TWX) file that you can import into a Workflow Center server. The suggested file name is URL-encoded in the `Content-Disposition` HTTP response header.

> **Security note:** The exported TWX file may contain sensitive business process data, including service URLs, environment variable values, and process logic. Store and transmit exported TWX files securely. Delete temporary copies when they are no longer needed.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — CSRF prevention token for IBM Business Automation Workflow REST APIs.
- `container` (path, string) *(required)* — The acronym of the process application or toolkit associated with the specified snapshot.
- `version` (path, string) *(required)* — The acronym of the snapshot to export.
- `format` (query, string) — The format of the export. If the value is not specified, system toolkits are included. A value of `twxWithoutToolkits` skips system toolkit dependencies.
- `use_enhanced_filenames` (query, boolean) — A value of `true` produces more meaningful file names within the exported file. If the value is `false` or not specified, default file names are used.

**Responses:**
- `200` — The specified snapshot was exported successfully.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested operation does not exist.
- `500` — Internal server error.

---

### `POST /ops/std/bpm/containers/install`
**Install an application on Workflow Server or Workflow Center**

Installs the application from the installation package file (a `.zip` file for Workflow Server or a `.twx` file for Workflow Center). This operation is asynchronous. You can see the messages for it in the system log or by using `GET /ops/system/queue/{id}` to periodically query its status.

> **Security note:** The installation package file may contain sensitive business process data. Do not upload TWX or ZIP files from untrusted sources. Verify the integrity of the file before uploading (for example, by checking its SHA-256 checksum or confirming it is a valid ZIP archive).

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — CSRF prevention token for IBM Business Automation Workflow REST APIs.
- `install_file` (formData, file) *(required)* — The file to install.
- `inactive` (query, boolean) — Deactivates the snapshot after installation. The default value is `false` and is ignored in Workflow Center.
- `caseDosName` (query, string) — Specifies the name of the case design object store.
- `caseProjectArea` (query, string) — Target environment or project area for case artifacts. You can omit this value if the default project area is defined.
- `caseOverwrite` (query, boolean) — Specifies whether to overwrite artifacts in the case store if they already exist. The default value is `false`.

**Responses:**
- `202` — A request to install the specified file was submitted. This operation is asynchronous. You can see the messages for it in the system log or by using `GET /ops/system/queue/{id}` to periodically query its status. You can find the `id` value in the `url` field of the JSON response body.
- `400` — The request contains invalid or missing parameters.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested operation does not exist.
- `500` — Internal server error.

---

### `GET /ops/system/queue/{id}`
**Obtain the status of an asynchronous operation**

Obtains information about the status of an asynchronous operation, such as group memberships that are being updated. Various REST APIs that start asynchronous operations return a URL that points to this API. Use this API to determine whether the asynchronous operation is still running, has failed, or has completed successfully.

**Parameters:**
- `BPMCSRFToken` (header, string) *(required)* — CSRF prevention token for IBM Business Automation Workflow REST APIs.
- `id` (path, string) *(required)* — Identifier of the operation, obtained from the REST API that started the asynchronous operation.
- `key` (query, string) — Authorization key, obtained from the REST API that started the asynchronous operation. Administrators can query an operation without this key.

**Responses:**
- `200` — The status of the specified operation is returned in the response.
- `400` — The request contains an invalid parameter.
- `403` — The caller is not authorized to perform the request.
- `404` — The requested operation does not exist.
- `500` — Internal server error.
