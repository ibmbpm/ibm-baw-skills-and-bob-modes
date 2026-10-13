# BAW Snapshot Inspector — API Reference

Covers read-only endpoints for retrieving snapshot metadata. For lifecycle-action endpoints (activate, deactivate, delete, env vars), see the `version-lifecycle-manager` skill.

**Source:** IBM Business Automation Workflow 26.0.x — Operations REST API (`baw-ops.26.0.0.json`) and WLE REST API (`baw-wle-v1.26.0.0.json`).

---

## Table of contents

1. [Base URL by deployment type](#1-base-url-by-deployment-type)
2. [Authentication and CSRF token](#2-authentication-and-csrf-token)
3. [List all containers (Operations API)](#3-list-all-containers-operations-api)
4. [List snapshots for a container (Operations API)](#4-list-snapshots-for-a-container-operations-api)
5. [Get snapshot metadata (Operations API)](#5-get-snapshot-metadata-operations-api)
6. [List / browse Process Apps — dependency enrichment (WLE API)](#6-list--browse-process-apps--dependency-enrichment-wle-api)
7. [List / browse Toolkits — dependency enrichment (WLE API)](#7-list--browse-toolkits--dependency-enrichment-wle-api)
8. [Common errors](#8-common-errors)

---

## 1. Base URL by deployment type

| Deployment | Base URL pattern | Notes |
|---|---|---|
| BAW on-premises (root mount) | `https://<host>:9443` | Most standalone on-prem installations mount Operations API directly at `/ops/...` |
| BAW on-premises (prefixed) | `https://<host>:9443/rest`, `/bas`, or `/baw` | Some installations use context roots |
| BAW on Cloud | `https://<tenant>.baw.ibmcloud.com` | Tenant-specific |
| CP4BA | `https://<cpd-route>/bas` | OpenShift route for the BAW component |

> **Path prefix note:** All Operations API calls use the prefix `/ops/std/bpm/...` appended to the base URL. The CSRF token acquisition endpoint is `/ops/system/login`.

If the user provides only a hostname, probe port **9443** and try root context `""` (no prefix), `/rest`, `/bas`, `/baw` in order with `POST <base-url>/ops/system/login` — use the first that returns HTTP 200, 201, 401, or 403.

---

## 2. Authentication and CSRF token

### Step 1 — Authenticate (obtain a session credential)

#### On-premises: Basic auth
Send `Authorization: Basic <base64(username:password)>` on every request.

#### CP4BA: exchange credentials for a Bearer token
Basic auth returns `403` on most CP4BA clusters. Exchange credentials once per session:

```bash
curl -sk -X POST "https://<cpd-host>/icp4d-api/v1/authorize" \
  -H "Content-Type: application/json" \
  -d '{"username":"<user>","password":"<pass>"}'
```

Use the returned `token` value as `Authorization: Bearer <token>` on all subsequent calls. Tokens expire — re-exchange if you receive a `401` on a previously working call.

#### LTPA token (on-premises SSO)
```
Authorization: LtpaToken2 <token>
```

### Step 2 — Obtain a CSRF token (required for all Operations API calls)

**Every** endpoint in the Operations API (`/ops/...`) requires the `BPMCSRFToken` header. Without it the server returns `CWTBG0651E`. Obtain the token once per session before making any other call.

**Method:** `POST`  
**Path:** `/ops/system/login`  
**Auth:** Use whichever credential obtained in Step 1 (Basic or Bearer).

```bash
curl -sk -X POST "<BAW_BASE_URL>/ops/system/login" \
  -H "Authorization: Basic <base64(user:pass)>" \
  -H "Content-Type: application/json" \
  -d '{"refresh_groups": false}'
```

**CP4BA example (Bearer token):**
```bash
curl -sk -X POST "https://cpd.example.com/bas/ops/system/login" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"refresh_groups": false}'
```

**Success response — HTTP 201:**
```json
{
  "csrf_token": "abc123xyz...",
  "expiration": 7200
}
```

Pass the returned `csrf_token` value as the `BPMCSRFToken` header on every subsequent Operations API call. The token is valid for up to `expiration` seconds (default 7200 / 2 hours). Re-run this call if a `CWTBG0651E` error is received after a long pause.

> **Optional lifetime:** To request a shorter-lived token, add `"requested_lifetime": <seconds>` to the POST body. Must be ≤ 7200.

> **WLE API note:** The WLE endpoints (`/bpm/wle/v1/...`) do **not** appear in the Operations API spec and have separate CSRF handling. On some CP4BA clusters they also enforce `BPMCSRFToken`. If a WLE call returns `CWTBG0651E`, re-use the same token obtained from `POST /ops/system/login`.

---

## 3. List all containers (Operations API)

Use this when the user doesn't know which Process App or Toolkit to inspect, or wants to see everything deployed.

**Method:** `GET`  
**Path:** `/ops/std/bpm/containers`

| Query parameter | Required | Description |
|---|---|---|
| `type` | No | `PA` = Process Apps only, `TK` = Toolkits only. Omit to return both. |
| `optional_parts` | No | `versions` = include branches and snapshots inline. `branches` = branches only. |
| `offset` | No | Pagination offset (0-based) |
| `size` | No | Max results per page |

```bash
curl -sk -X GET \
  "<BAW_BASE_URL>/ops/std/bpm/containers?optional_parts=versions" \
  -H "Authorization: Basic <base64(user:pass)>" \
  -H "BPMCSRFToken: <csrf_token>"
```

**Success response — HTTP 200:**
```json
{
  "containers": [
    {
      "container_name": "HR Process Application",
      "container": "HRAPP",
      "id": "2066.bfb35867-...",
      "toolkit": false,
      "archived": false,
      "branches": [
        {
          "versions": [
            {
              "version_name": "HR Process v2.0",
              "version": "v2.0",
              "active": true,
              "creation_date": "2025-06-10T09:30:00Z"
            }
          ]
        }
      ]
    }
  ],
  "next": "<url for next page or absent if no more>"
}
```

**Key response fields:**

| Field | Description |
|---|---|
| `container` | Acronym — use this in all subsequent API calls |
| `container_name` | Human-readable display name |
| `toolkit` | `true` = Toolkit, `false` = Process App |
| `archived` | `true` = archived (hidden from normal views) |
| `branches[].versions[]` | Snapshot list — only present when `optional_parts=versions` is passed |

> Use `optional_parts=versions` to retrieve container list **and** all their snapshots in a single call, avoiding a separate list-snapshots call.

---

## 4. List snapshots for a container (Operations API)

Use this when the user knows the container acronym but not which snapshot to inspect.

**Method:** `GET`  
**Path:** `/ops/std/bpm/containers/{container}/versions`

| Parameter | Location | Required | Description |
|---|---|---|---|
| `container` | path | ✅ | Process App or Toolkit acronym (case-sensitive) |
| `branch` | query | No | Track acronym — filter to snapshots in this track only |
| `offset` | query | No | Pagination offset |
| `size` | query | No | Max results per page |

```bash
curl -sk -X GET \
  "<BAW_BASE_URL>/ops/std/bpm/containers/HRAPP/versions" \
  -H "Authorization: Basic <base64(user:pass)>" \
  -H "BPMCSRFToken: <csrf_token>"
```

**Success response — HTTP 200** — array of `version` objects (see schema in section 5).

---

## 5. Get snapshot metadata (Operations API)

The primary read call for a specific snapshot. Returns all version fields.

**Method:** `GET`  
**Path:** `/ops/std/bpm/containers/{container}/versions/{version}`

| Parameter | Location | Required | Description |
|---|---|---|---|
| `container` | path | ✅ | Process App or Toolkit acronym (case-sensitive) |
| `version` | path | ✅ | Snapshot acronym (case-sensitive) |

```bash
curl -sk -X GET \
  "<BAW_BASE_URL>/ops/std/bpm/containers/HRAPP/versions/v2.0" \
  -H "Authorization: Basic <base64(user:pass)>" \
  -H "BPMCSRFToken: <csrf_token>"
```

**Success response — HTTP 200:**
```json
{
  "version_name": "HR Process v2.0",
  "version": "v2.0",
  "id": "2064.7a3f...",
  "active": true,
  "creation_date": "2025-06-10T09:30:00Z",
  "creator_user_name": "admin",
  "branch_name": "Main",
  "branch": "Main",
  "container_name": "HR Process Application",
  "container": "HRAPP",
  "is_default": true,
  "status": "Released",
  "capability": "Standard",
  "archived": false,
  "tip": false
}
```

**Full field reference (from `baw-ops.26.0.0.json` `version` schema):**

| Field | Type | Description |
|---|---|---|
| `version_name` | string | Human-readable snapshot name |
| `version` | string | Snapshot acronym — identifier used in API calls |
| `id` | string | Internal snapshot ID |
| `description` | string | Optional description |
| `active` | boolean | `true` = currently active (serves new process instances) |
| `creation_date` | ISO 8601 | Date/time the snapshot was created |
| `creator_user_id` | string | User ID of the creator |
| `creator_user_name` | string | Username of the creator |
| `tip` | boolean | `true` = this is the tip (head) snapshot of its track |
| `branch_id` | string | Internal ID of the track |
| `branch_name` | string | Display name of the track |
| `branch` | string | Track acronym |
| `container_id` | string | Internal ID of the Process App or Toolkit |
| `container_name` | string | Display name of the Process App or Toolkit |
| `container` | string | Acronym of the Process App or Toolkit |
| `is_default` | boolean | `true` = this is the default snapshot |
| `status` | string | Development state, e.g. `New`, `Validated`, `Released` |
| `capability` | string | BPM capability: `Standard` or `Advanced` |
| `archived` | boolean | `true` = snapshot is archived |
| `installable` | boolean | `false` = snapshot has install errors; cannot be deployed |

> **Toolkit dependencies:** The Operations API `version` schema does not include a `toolkitDependencies` field. Use the WLE API enrichment (sections 6 and 7) to retrieve dependency data.

---

## 6. List / browse Process Apps — dependency enrichment (WLE API)

Use this endpoint for:
1. **Container browser** — listing Process Apps when the Ops API container list is unavailable or the user prefers WLE data
2. **Dependency enrichment** — finding toolkit references when the Ops API omits them
3. **Additional snapshot fields** — `activeSince`, `snapshotTip`, `branchName` not present in the Ops API response

**Method:** `GET`
**Path:** `/bpm/wle/v1/processApps?includeToolkitProcessApps=true`

> **Base URL note:** The WLE context root prefix (e.g. `/rest`) may differ from the Ops API prefix on on-premises installs. Once resolved for a session, reuse `<WLE_BASE_URL>` directly without re-probing.

```bash
curl -sk -X GET \
  "<WLE_BASE_URL>/bpm/wle/v1/processApps?includeToolkitProcessApps=true" \
  -H "Authorization: Basic <base64(user:pass)>" \
  -H "Accept: application/json" \
  -H "BPMCSRFToken: <csrf_token>"
```

> **CSRF note:** On CP4BA clusters, this WLE endpoint also enforces `BPMCSRFToken`. Reuse the token obtained from `POST /ops/system/login`.

**Response (excerpt):**
```json
{
  "status": "200",
  "data": {
    "processAppsList": [
      {
        "shortName": "HRAPP",
        "name": "HR Process Application",
        "lastModified_on": "2025-06-10T09:30:00Z",
        "installedSnapshots": [
          {
            "acronym": "v2.0",
            "name": "HR Process v2.0",
            "active": true,
            "activeSince": "2025-06-11T08:00:00Z",
            "createdOn": "2025-06-10T09:30:00Z",
            "branchName": "Main",
            "snapshotTip": true
          }
        ]
      }
    ]
  }
}
```

**Dependency enrichment:** Locate the container by `shortName`, then the target snapshot in `installedSnapshots` by `acronym`. Look for toolkit references in `toolkits`, `dependencies`, or `usedToolkitSnapshots` (field name varies by BAW version).

---

## 7. List / browse Toolkits — dependency enrichment (WLE API)

Same purposes as section 6, but for Toolkit containers.

**Method:** `GET`  
**Path:** `/bpm/wle/v1/toolkit?includeSnapshots=true`

```bash
curl -sk -X GET \
  "<BAW_BASE_URL>/bpm/wle/v1/toolkit?includeSnapshots=true" \
  -H "Authorization: Basic <base64(user:pass)>" \
  -H "Accept: application/json" \
  -H "BPMCSRFToken: <csrf_token>"
```

Locate the toolkit in `data.toolkitList` by `shortName`, then navigate to the target snapshot in `installedSnapshots` by `acronym`.

---

## 8. Common errors

| HTTP | Code | Cause | Action |
|---|---|---|---|
| `401` | `CWTBG0019E` | Invalid credentials | Verify username/password or token |
| `403` | `CWTBG0020E` | Insufficient permissions or wrong auth type for CP4BA | Check `tw_admins` group membership (on-premises) or switch to Bearer token (CP4BA) |
| `400` | `CWTBG0651E` | Missing or invalid CSRF token | Run `POST /ops/system/login` to obtain a fresh `BPMCSRFToken` and include it in the `BPMCSRFToken` header |
| `400` | `CWTBG0624E` | Container acronym not found | Acronyms are case-sensitive — list containers to confirm |
| `400` | `CWTBG0646E` | Snapshot acronym not found | List snapshots for the container to confirm the exact acronym |
| `404` | — | Operations API not available | Server may be BPM 8.x; Operations API requires BAW 18.0+ |
| `500` | — | BAW server error | Check `SystemOut.log`; may indicate a cluster or database issue |

**Case sensitivity:** `HRAPP` and `hrapp` are different values. Always use the exact acronym as returned by the list endpoints.
