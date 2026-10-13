# BAW REST API Reference — process-compliance-violation-detection

Generated from `baw-ops.26.0.0.json`. Base path: `/ops`.

All paths below are relative — prepend `{BAW_BASE_URL}` to form the full URL.

---

## POST /ops/system/login

**Summary:** Obtain IBM Business Automation Workflow CSRF prevention token

Obtain a CSRF prevention token and optionally refresh the user's group membership information.

**Authentication:** `Authorization: Basic <base64(username:password)>`

**Request headers:**
- `Content-Type: application/json`

**Request body** (`application/json`, required):
```json
{
  "refresh_groups": false
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `refresh_groups` | boolean | yes | Whether to refresh the caller's group membership in the BAW database. Pass `false` unless you need a group refresh. |
| `requested_lifetime` | integer | no | Token lifetime in seconds (max 7200, default 7200). |

**Responses:**

| Code | Meaning |
|---|---|
| 201 | Success — response body contains a `csrf_token` string and an `expiration` integer. Store `csrf_token` as `{BAW_CSRF}`. Also capture the `LtpaToken2` and `JSESSIONID` cookies as `{BAW_SESSION}`. |
| 400 | Invalid input. |
| 401 | Authentication failed — credentials rejected. |
| 500 | Internal server error. |

**Success response body:**
```json
{
  "csrf_token": "<token-string>",
  "expiration": 7200
}
```

**How to use the token on subsequent calls:**
- Header: `BPMCSRFToken: {BAW_CSRF}`
- Cookies: include the `LtpaToken2` and `JSESSIONID` values from the Set-Cookie response headers.

---

## GET /ops/std/bpm/containers

**Summary:** Retrieve a list of all process applications and toolkits

Retrieves a list of all process applications and toolkits on the Workflow Center server that the authenticated user may see. Use this endpoint to validate process application and snapshot acronyms before attempting an export.

**Authentication:** Session cookies (`{BAW_SESSION}`) + `BPMCSRFToken: {BAW_CSRF}`

**Query parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `type` | string | no | Filter results: `PA` for process applications only, `TK` for toolkits only. Omit to return both. |
| `optional_parts` | array (comma-separated) | no | Pass `versions` to include snapshot/version details in each container entry. Pass `branches` to include track details. |
| `offset` | integer | no | Pagination offset (0-based). |
| `size` | integer | no | Maximum number of results to return. |
| `ids` | array (comma-separated) | no | Restrict results to specific container IDs. |

**Recommended call for container validation:**
```
GET {BAW_BASE_URL}/ops/std/bpm/containers?type=PA&optional_parts=versions
BPMCSRFToken: {BAW_CSRF}
Cookie: LtpaToken2=...; JSESSIONID=...
```

**Responses:**

| Code | Meaning |
|---|---|
| 200 | Success — response body contains a `containers` array. |
| 400 | Invalid or missing parameters. |
| 403 | Not authorized. |
| 404 | Resource not found. |
| 500 | Internal server error. |

**Key fields in the response:**

Each entry in `containers`:

| Field | Description |
|---|---|
| `container_name` | Display name of the process application |
| `container` | Acronym — use this to validate the user-supplied container acronym |
| `branches[].versions[].version_name` | Display name of the snapshot |
| `branches[].versions[].version` | Acronym — use this to validate the user-supplied version acronym |

---

## GET /ops/std/bpm/containers/{container}/versions/{version}/export

**Summary:** Export a process application or toolkit snapshot as a .twx file

Downloads a specified process application snapshot or toolkit snapshot as a binary `.twx` file. Only BAW administrators or users with project read permission are authorized. The suggested filename is URL-encoded in the `Content-Disposition` response header.

**Authentication:** Session cookies (`{BAW_SESSION}`) + `BPMCSRFToken: {BAW_CSRF}`

**Path parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `container` | string | yes | Acronym of the process application or toolkit (e.g. `HSS`). Verify against the containers list before calling. |
| `version` | string | yes | Acronym of the snapshot to export (e.g. `RHSV180`, `Tip`). Verify against the containers list before calling. |

**Query parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `format` | string | no | Export format. Omit to export with system toolkits included. Pass `twxWithoutToolkits` to skip toolkit dependencies. |
| `use_enhanced_filenames` | boolean | no | Pass `true` for more meaningful internal file names. Defaults to `false`. |

**Example call:**
```
GET {BAW_BASE_URL}/ops/std/bpm/containers/{container}/versions/{version}/export
BPMCSRFToken: {BAW_CSRF}
Cookie: LtpaToken2=...; JSESSIONID=...
```

Save the response body as `{container}-{version}.twx`. Verify the HTTP status code and the downloaded file size before proceeding to analysis.

**Responses:**

| Code | Meaning |
|---|---|
| 200 | Success — response body is the binary `.twx` file. |
| 400 | Invalid or missing parameters. |
| 403 | Not authorized — user does not have read permission for this snapshot. |
| 404 | Container or version acronym does not exist on this server. |
| 500 | Internal server error. |
