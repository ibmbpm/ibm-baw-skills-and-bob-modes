# BAW Version Lifecycle — Operations REST API Reference

This file is the authoritative reference for all BAW version lifecycle endpoints used by the `version-lifecycle-manager` skill. Read it before constructing any API call.

**IBM Docs source:** IBM Business Automation Workflow 24.x / 25.x / 26.x — "BPMContainers REST API" and "Operations REST APIs" sections under "Administering > REST APIs".
Always verify against the IBM documentation for the exact server version in use: https://www.ibm.com/docs/en/baw

> **Path prefix note:** Endpoints under `/ops/std/bpm/...` use the Operations API prefix. Endpoints under `/std/bpm/...` use the standard BPM API prefix. Both are appended to the same base URL.

---

## Table of contents

1. [Base URL by deployment type](#1-base-url-by-deployment-type)
2. [Authentication](#2-authentication)
3. [Install a process app or toolkit](#3-install-a-process-app-or-toolkit)
4. [Verify a snapshot](#4-verify-a-snapshot)
5. [Activate a snapshot](#5-activate-a-snapshot)
6. [Deactivate a snapshot](#6-deactivate-a-snapshot)
7. [Delete a snapshot](#7-delete-a-snapshot)
8. [List snapshots for a container using the WLE API](#8-list-snapshots-for-a-container-using-the-wle-api)
9. [Read environment variables](#9-read-environment-variables)
10. [Set environment variables](#10-set-environment-variables)
11. [Synchronize environment variables](#11-synchronize-environment-variables)
12. [List containers (Process Apps / Toolkits)](#12-list-containers)
13. [Common errors and remediation](#13-common-errors-and-remediation)

---

## 1. Base URL by deployment type

| Deployment | Base URL pattern | Notes |
|---|---|---|
| BAW on-premises (root mount) | `https://<host>:9443` | Most standalone on-prem installations mount Operations API directly at `/ops/...` |
| BAW on-premises (prefixed) | `https://<host>:9443/rest`, `/bas`, or `/baw` | Some installations use `/rest`, `/bas`, or `/baw` |
| BAW on Cloud | `https://<tenant>.baw.ibmcloud.com` | Tenant-specific; supplied by IBM Cloud |
| CP4BA (Cloud Pak for Business Automation) | `https://<cpd-route>/bas` | `cpd-route` is the OpenShift route for the BAW component |

All API paths below are appended to the base URL. Never invent or guess the base URL — ask the user.

**Port and Context Discovery:** The default on-premises HTTPS port is **9443**. Port 9080 (HTTP) is commonly configured to redirect to 9443. If the user provides a hostname without a port, try port 9443 first. If they provide a hostname without a context root, probe root `""` (no prefix), `/rest`, `/bas`, `/baw` on port 9443 in that order using `POST <base-url>/ops/system/login` — use the first that returns HTTP 200, 201, 401, or 403.

**Important:** The BAW REST API has two overlapping path spaces:
- **WLE REST API** (`/rest/bpm/wle/v1/...`) — used for listing Process Apps, Toolkits, and their installed snapshots.
- **Operations REST API** (`/ops/std/bpm/...`) — used for install, activate, deactivate, delete, and env var management.

The WLE API paths are appended to the base URL **without** the context root prefix repeated. For example, if the base URL is `https://host:9443/rest`, the list process-apps call is `https://host:9443/rest/bpm/wle/v1/processApps` (not `/rest/rest/...`).

---

## 2. Authentication

### Basic authentication (on-premises, most common)
Pass `Authorization: Basic <base64(username:password)>` in the request header.

```bash
# Encode credentials
echo -n "admin:mypassword" | base64
# → YWRtaW46bXlwYXNzd29yZA==
```

### LTPA token (on-premises SSO)
Pass `Authorization: LtpaToken2 <token>` obtained from a prior `/ibm/console` login.

### Zen API key (CP4BA)
Pass `Authorization: ZenApiKey <api-key>` where the API key is generated from the CP4BA admin UI under **Profile → API Key**.

### OAuth / bearer token (BAW on Cloud)
Pass `Authorization: Bearer <token>` obtained from the IBM Cloud IAM token endpoint.

---

## 3. Install a process app or toolkit

Installs a new Process App or Toolkit (or a new snapshot of an existing one) from a `.twx` export file.

**Method:** `POST`
**Path:** `/ops/std/bpm/containers/install`

**Request body — `multipart/form-data`:**

| Field | Required | Description |
|---|---|---|
| `file` | ✅ | The `.twx` file to install |
| `containerAcronym` | optional | Override the acronym from the `.twx` metadata |

**Headers:**
```
Authorization: Basic <credentials>
Content-Type: multipart/form-data
```

**Example request:**
```bash
curl -X POST \
  "https://baw.example.com/bas/ops/std/bpm/containers/install" \
  -H "Authorization: Basic YWRtaW46bXlwYXNzd29yZA==" \
  -F "file=@/tmp/MYAPP_v3.0.twx"
```

**Success response — HTTP 200:**
```json
{
  "status": "200",
  "data": {
    "containerAcronym": "MYAPP",
    "snapshotAcronym": "3.0",
    "installed": true
  }
}
```

**After install:** always verify the snapshot using section 4 to confirm it was registered with the expected state before activating.

---

## 4. Verify a snapshot

Returns the current state and metadata of a specific snapshot. Use after install, before activation, and to diagnose unexpected states.

**Method:** `GET`
**Path:** `/ops/std/bpm/containers/{container}/versions/{version}`

| Parameter | Location | Required | Description |
|---|---|---|---|
| `container` | path | ✅ | Process App or Toolkit acronym or numeric container ID |
| `version` | path | ✅ | Snapshot acronym or snapshot ID |

**Example request:**
```bash
curl -X GET \
  "https://baw.example.com/bas/ops/std/bpm/containers/MYAPP/versions/3.0" \
  -H "Authorization: Basic YWRtaW46bXlwYXNzd29yZA=="
```

**Success response — HTTP 200:**
```json
{
  "status": "200",
  "data": {
    "containerAcronym": "MYAPP",
    "snapshotAcronym": "3.0",
    "snapshotName": "Release 3.0",
    "active": false,
    "installedAt": "2025-08-20T14:00:00Z",
    "instanceCount": 0
  }
}
```

Key fields to check: `active` (is this the running version?), `instanceCount` (in-flight work), `installedAt` (confirms the install succeeded).

---

## 5. Activate a snapshot

Makes the specified snapshot the active (default) version for new process instances in the container.

**Method:** `POST`
**Path:** `/std/bpm/containers/{container}/versions/{version}/activate`

| Parameter | Location | Required | Description |
|---|---|---|---|
| `container` | path | ✅ | Process App or Toolkit acronym (e.g. `MYAPP`) or numeric container ID |
| `version` | path | ✅ | Snapshot acronym (e.g. `0.9.3`) or snapshot ID |

**Request body:** none (empty body)

**Headers:**
```
Authorization: Basic <credentials>
Content-Type: application/json
```

**Example request:**
```bash
curl -X POST \
  "https://baw.example.com/bas/std/bpm/containers/MYAPP/versions/0.9.3/activate" \
  -H "Authorization: Basic YWRtaW46bXlwYXNzd29yZA==" \
  -H "Content-Type: application/json"
```

**Success response — HTTP 200:**
```json
{
  "status": "200",
  "data": {
    "containerAcronym": "MYAPP",
    "snapshotAcronym": "0.9.3",
    "active": true
  }
}
```

**Effect:** The previously active snapshot is automatically set to inactive. Only one snapshot can be active per container at a time.

---

## 6. Deactivate a snapshot

Removes the snapshot from the active execution path. Running instances already on this snapshot complete normally; no new instances start on it.

**Method:** `POST`  
**Path:** `/std/bpm/containers/{container}/versions/{version}/deactivate`

| Parameter | Location | Required | Description |
|---|---|---|---|
| `container` | path | ✅ | Process App or Toolkit acronym or numeric container ID |
| `version` | path | ✅ | Snapshot acronym or snapshot ID |

**Request body:** none

**Example request:**
```bash
curl -X POST \
  "https://baw.example.com/bas/std/bpm/containers/MYAPP/versions/0.9.3/deactivate" \
  -H "Authorization: Basic YWRtaW46bXlwYXNzd29yZA==" \
  -H "Content-Type: application/json"
```

**Success response — HTTP 200:**
```json
{
  "status": "200",
  "data": {
    "containerAcronym": "MYAPP",
    "snapshotAcronym": "0.9.3",
    "active": false
  }
}
```

**⚠️ Disruptive:** In-flight process instances on this snapshot continue to completion, but any orchestration or event subscription routing that relied on this being the active snapshot may behave differently. Warn the administrator before proceeding.

---

## 7. Delete a snapshot

Permanently removes the snapshot from the BAW server. You cannot undo this action.

**Method:** `DELETE`
**Path:** `/ops/std/bpm/containers/{container}/versions/{version}`

> **Path note:** Earlier documentation referenced `/std/bpm/containers/...` (without the `/ops` prefix) for this endpoint. On CP4BA and recent BAW on-premises installations, all version lifecycle endpoints — including delete — are served under `/ops/std/bpm/...`. The `/std/bpm/...` path returns 404 on these deployments. Use `/ops/std/bpm/...` consistently.

| Parameter | Location | Required | Description |
|---|---|---|---|
| `container` | path | ✅ | Process App or Toolkit acronym or numeric container ID |
| `version` | path | ✅ | Snapshot acronym or snapshot ID |

**Request body:** none

**Example request:**
```bash
curl -X DELETE \
  "https://baw.example.com/bas/ops/std/bpm/containers/MYAPP/versions/0.9.3" \
  -H "Authorization: Basic YWRtaW46bXlwYXNzd29yZA=="
```

**Success response — HTTP 200:**
```json
{
  "status": "200",
  "data": {
    "containerAcronym": "MYAPP",
    "snapshotAcronym": "0.9.3",
    "deleted": true
  }
}
```

**🚨 Destructive:** Deletion is permanent. BAW rejects this call if:
- The snapshot is currently active (`HTTP 409`) — deactivate it first.
- There are active process instances on the snapshot (`HTTP 409`) — migrate or complete them first.

> **CP4BA caveat — HTTP 405 on DELETE:** On some CP4BA cluster configurations, `DELETE /ops/std/bpm/containers/{container}/versions/{version}` returns **405 Method Not Allowed** even when the snapshot is deactivated and the path resolves correctly (GET returns 200). This is a server-side restriction — the DELETE method is not exposed on that endpoint for the authenticated user's role. `CEAdmin` and equivalent non-admin roles are known to hit this. If you receive 405:
> 1. Try authenticating as a higher-privileged user (e.g. `admin`).
> 2. If 405 persists, use **Workflow Center** (`/bas/WorkflowCenter`) or **Process Admin Console** (`/bas/ProcessAdmin`) to delete the snapshot via the UI — these bypass the REST API restriction.

---

## 8. List snapshots for a container using the WLE API

Retrieve all installed snapshots for a given Process App or Toolkit. This uses the WLE REST API, not the Operations API. The `installedSnapshots` array contains the snapshots for each container in the response.

**Method:** `GET`
**Path:** `/bpm/wle/v1/processApps` (for Process Apps) or `/bpm/wle/v1/toolkit` (for Toolkits)

> These paths are appended to the base URL including its context root. For example, with base `https://host:9443/rest`, the full URL is `https://host:9443/rest/bpm/wle/v1/processApps`.

**Query parameters:**

| Parameter | Description |
|---|---|
| `includeToolkitProcessApps` | Set to `true` to include results (required for the call to succeed on most installations) |
| `includeSnapshots` | Set to `true` when calling the toolkit endpoint to include snapshot details |

**Example request (Process Apps):**
```bash
curl -X GET \
  "https://baw.example.com:9443/rest/bpm/wle/v1/processApps?includeToolkitProcessApps=true" \
  -u "tw_admin:tw_admin" \
  -H "Accept: application/json"
```

**Example request (Toolkits):**
```bash
curl -X GET \
  "https://baw.example.com:9443/rest/bpm/wle/v1/toolkit?includeSnapshots=true" \
  -u "tw_admin:tw_admin" \
  -H "Accept: application/json"
```

**Success response — HTTP 200 (excerpt):**
```json
{
  "status": "200",
  "data": {
    "processAppsList": [
      {
        "ID": "2066.abc...",
        "shortName": "MYAPP",
        "name": "My Process Application",
        "lastModified_on": "2025-08-20T14:00:00Z",
        "installedSnapshots": [
          {
            "name": "Release 3.0",
            "ID": "2064.xyz...",
            "acronym": "3.0",
            "active": true,
            "activeSince": "2025-08-21T09:00:00Z",
            "createdOn": "2025-08-20T14:00:00Z",
            "snapshotTip": true,
            "branchName": "Main"
          },
          {
            "name": "Release 2.9",
            "ID": "2064.uvw...",
            "acronym": "2.9",
            "active": false,
            "activeSince": null,
            "createdOn": "2025-05-10T09:00:00Z",
            "snapshotTip": false,
            "branchName": "Main"
          }
        ]
      }
    ]
  }
}
```

Key response fields per snapshot: `acronym` (use this as the `{version}` parameter in other API calls), `name`, `active`, `activeSince`, `createdOn`, `snapshotTip` (most recent on branch — not the same as active).

Present this as a table: container name, acronym, snapshot name, snapshot acronym, active, createdOn.

---

## 9. Read environment variables

Returns the environment variables configured for a specific snapshot.

**Method:** `GET`
**Path:** `/ops/std/bpm/containers/{container}/versions/{version}/env_vars`

| Parameter | Location | Required | Description |
|---|---|---|---|
| `container` | path | ✅ | Process App or Toolkit acronym or numeric container ID |
| `version` | path | ✅ | Snapshot acronym or snapshot ID |

**Example request:**
```bash
curl -X GET \
  "https://baw.example.com/bas/ops/std/bpm/containers/MYAPP/versions/3.0/env_vars" \
  -H "Authorization: Basic YWRtaW46bXlwYXNzd29yZA=="
```

**Success response — HTTP 200:**
```json
{
  "status": "200",
  "data": {
    "env_vars": [
      { "name": "DB_URL",       "value": "jdbc:db2://db-host:50000/BAWDB" },
      { "name": "DB_POOL_SIZE", "value": "10" }
    ]
  }
}
```

Always read env vars before making changes so you have a baseline for rollback.

---

## 10. Set environment variables

Writes one or more environment variables to a snapshot's stored configuration. Values are persisted but **not applied to the running environment** until a sync is performed (section 11).

**Method:** `POST`
**Path:** `/ops/std/bpm/containers/{container}/versions/{version}/env_vars`

| Parameter | Location | Required | Description |
|---|---|---|---|
| `container` | path | ✅ | Process App or Toolkit acronym or numeric container ID |
| `version` | path | ✅ | Snapshot acronym or snapshot ID |

**Request body — `application/json`:**
```json
{
  "env_vars": [
    { "name": "DB_URL",       "value": "jdbc:db2://prod-db:50000/BAWDB" },
    { "name": "DB_POOL_SIZE", "value": "20" }
  ]
}
```

**Example request:**
```bash
curl -X POST \
  "https://<baw-host>/bas/ops/std/bpm/containers/MYAPP/versions/3.0/env_vars" \
  -H "Authorization: Basic <base64-credentials>" \
  -H "Content-Type: application/json" \
  -d '{"env_vars":[{"name":"DB_URL","value":"<db-connection-string>"},{"name":"DB_POOL_SIZE","value":"20"}]}'
```

**Success response — HTTP 200:**
```json
{
  "status": "200",
  "data": {
    "updated": true
  }
}
```

After setting, offer to sync (section 11) so the values take effect on the running snapshot.

---

## 11. Synchronize environment variables

Copies the stored environment variable values from a **source** snapshot to a **target** snapshot within the same container. Use this to propagate a baseline configuration forward to a newer snapshot (e.g. after updating values on an older version and wanting to carry them across).

> **Behavior note:** This endpoint does **not** "push env vars to the live runtime" in the traditional sense. It performs a **cross-snapshot copy**: the `{version}` path segment is the *source* snapshot, and `target_version` (query parameter, required) is the *destination* snapshot. Source and target must be different snapshots within the same container. The operation is asynchronous — the server returns HTTP 202 with a queue URL; poll that URL to confirm completion.

**Method:** `POST`
**Path:** `/ops/std/bpm/containers/{container}/versions/{version}/env_vars/sync`

| Parameter | Location | Required | Description |
|---|---|---|---|
| `container` | path | ✅ | Process App or Toolkit acronym or numeric container ID |
| `version` | path | ✅ | **Source** snapshot acronym or snapshot ID — the snapshot whose env var values will be copied |
| `target_version` | query | ✅ | **Target** snapshot acronym — the snapshot that will receive the copied values. Must be different from `{version}` |

**Request body:** none

**Example request:**
```bash
curl -X POST \
  "https://baw.example.com/bas/ops/std/bpm/containers/MYAPP/versions/1.0/env_vars/sync?target_version=2.0" \
  -H "Authorization: Basic YWRtaW46bXlwYXNzd29yZA==" \
  -H "Content-Type: application/json"
```

**Success response — HTTP 202 (async):**
```json
{
  "description": "Your request to synchronize the environment variables for the specified snapshot was submitted. You can check the progress of the synchronization by accessing the URL in the response.",
  "url": "https://<host>/bas/ops/system/queue/<id>?key=<key>"
}
```

Poll the returned `url` (with the same `Authorization` header) until the response contains `"state": "success"`:
```json
{
  "state": "success",
  "result": {
    "Message": "The environment variables of '2.0' target snapshot were successfully synchronized with '1.0' source snapshot.",
    "status": "success"
  }
}
```

**Common errors:**
| HTTP | Error code | Meaning |
|---|---|---|
| 400 | `CWTBG0011E` | `target_version` query parameter missing |
| 400 | `CWTBG0692E` | Source and target snapshot are the same |
| 400 | `CWTBG0646E` | `target_version` snapshot does not exist |

**⚠️ Live impact:** If the target snapshot is active, all services and processes on that snapshot that read these variables immediately see the new values. Confirm with the user before syncing to a production-active snapshot.

---

## 12. List containers (Process Apps and Toolkits)

Retrieve available Process Apps and Toolkits. Use this to find the correct container acronym when the user only knows the display name, or to get a full inventory of what is deployed.

**This uses the WLE REST API** — there are two separate endpoints, one for Process Apps and one for Toolkits.

### List Process Apps

**Method:** `GET`
**Path:** `/bpm/wle/v1/processApps?includeToolkitProcessApps=true`

**Example request:**
```bash
curl -X GET \
  "https://baw.example.com:9443/rest/bpm/wle/v1/processApps?includeToolkitProcessApps=true" \
  -u "admin:mypassword" \
  -H "Accept: application/json"
```

### List Toolkits

**Method:** `GET`
**Path:** `/bpm/wle/v1/toolkit?includeSnapshots=true`

**Example request:**
```bash
curl -X GET \
  "https://baw.example.com:9443/rest/bpm/wle/v1/toolkit?includeSnapshots=true" \
  -u "admin:mypassword" \
  -H "Accept: application/json"
```

**Success response — HTTP 200 (BAW on-premises / WLE API, excerpt):**
```json
{
  "status": "200",
  "data": {
    "processAppsList": [
      {
        "ID": "2066.abc...",
        "shortName": "MYAPP",
        "name": "My Process Application",
        "lastModifiedBy": "tw_admin",
        "lastModified_on": "2025-08-20T14:00:00Z",
        "installedSnapshots": [ ... ]
      }
    ]
  }
}
```

The `shortName` field is the container acronym to use in all other API calls.

> **CP4BA response schema difference:** On CP4BA clusters, `GET /bas/ops/std/bpm/containers?containerType=PA|TK` returns a flat array under the `containers` key (not `data.processAppsList`), and field names differ:
>
> | WLE API (on-premises) | CP4BA Ops API |
> |---|---|
> | `shortName` | `container` |
> | `name` | `container_name` |
> | `ID` | `id` |
> | *(no field)* | `toolkit` (`true`/`false`) |
> | *(no field)* | `archived` (`true`/`false`) |
>
> **CP4BA example response (single item):**
> ```json
> {
>   "containers": [
>     {
>       "container_name": "Hiring Sample",
>       "container": "HSS",
>       "id": "2066.d4616c46-a8b9-45b2-90a3-f71c3d8f9b2a",
>       "description": "...",
>       "creation_date": "2026-06-15T16:17:56z",
>       "creator_user_name": "Automation System Account",
>       "toolkit": false,
>       "archived": false
>     }
>   ]
> }
> ```
>
> Use the `container` field value as the container acronym in all subsequent API calls (e.g. activate, deactivate, verify, env-var endpoints). The `toolkit` boolean lets you distinguish Process Apps (`false`) from Toolkits (`true`) in a single response — no need to call both `containerType=PA` and `containerType=TK` separately if you only need a combined list.

## 13. Common errors and remediation

| HTTP status | Code / message | Cause | Remediation |
|---|---|---|---|
| `401 Unauthorized` | `CWTBG0019E` | Invalid or missing credentials | Verify username/password or API key; check that the account has BAW administrative rights |
| `403 Forbidden` | `CWTBG0020E` | Authenticated user lacks permission | Ensure the user is in the `tw_admins` group (on-premises) or has the BAW Admin role (CP4BA) |
| `400 Bad Request` | `CWTBG0624E` | Container acronym does not exist | Use `GET /ops/std/bpm/containers` (section 12) to list containers and confirm the correct acronym; acronyms are case-sensitive |
| `400 Bad Request` | `CWTBG0646E` | Snapshot acronym does not exist within the container | Use `GET /ops/std/bpm/containers/{container}/versions` (section 8) to list snapshots and confirm the exact acronym |
| `409 Conflict` | `CWTBG0550E` | Trying to delete the active snapshot | Deactivate the snapshot first (section 4), then retry the delete |
| `409 Conflict` | `CWTBG0551E` | Snapshot has active process instances | Complete or migrate running instances before deleting; check the Process Admin Console for active instances |
| `500 Internal Server Error` | — | BAW server error | Inspect the BAW SystemOut.log; may indicate a cluster node issue or database problem; retry after checking server health |

### Case sensitivity note
Container and snapshot acronyms are **case-sensitive**. `MYAPP` and `myapp` are different values. Always use the exact acronym as returned by the list endpoints.

### CP4BA-specific notes
- On CP4BA, Basic auth (`Authorization: Basic`) returns **403**. `ZenApiKey <base64>` may return **401** depending on cluster configuration. If either occurs, exchange credentials for a Bearer token via `POST /icp4d-api/v1/authorize` with `{"username":"…","password":"…"}` and use `Authorization: Bearer <token>` for all API calls. Tokens expire; re-exchange on 401.
- The base URL uses the OpenShift route for the BAW component, not the CP4BA dashboard URL. Retrieve it with `oc get route -n <namespace> | grep baw`.
- Namespace-level RBAC policies may further restrict which operations a given service account can perform; coordinate with the cluster admin if you receive `403` despite correct credentials.
