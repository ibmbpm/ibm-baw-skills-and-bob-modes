---
name: version-inspector
description: >-
  Inspect IBM BAW snapshots and browse deployed containers. Retrieves a
  plain-language metadata summary — version name, lifecycle status, creation
  date, and toolkit dependencies — for a specific snapshot. Also lists all
  Process Apps and Toolkits when the user doesn't know which container or
  snapshot to inspect. Works for both Process App and Toolkit types on BAW
  on-premises, BAW on Cloud, and CP4BA. Use whenever an administrator wants to
  inspect, view, or browse versions or snapshots, or asks: "inspect versions",
  "inspect some versions", "see what versions are deployed", "show snapshot
  details", "get snapshot metadata", "what version is deployed", "list process
  apps", "what process apps are deployed", "show all toolkits", "what's
  installed on this server", "snapshot summary", "check snapshot state", "list
  snapshots", "list versions", "show all versions", or "inspect snapshot". Use
  proactively before activating, deactivating, or deleting a snapshot.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Version Inspector

Retrieve and present a plain-language summary of a BAW snapshot's current state — version name, lifecycle status, creation date, in-flight task count, and toolkit dependencies — using the public Operations REST API. No write operations are performed. Works for both Process App and Toolkit container types.

**Companion skill:** Lifecycle actions (activate, deactivate, delete, env var management) are handled by the `version-lifecycle-manager` skill — mention this after presenting the summary.

## Entry point — choosing the right path

Before calling any API, determine how much the user already knows:

| User knows | Start at |
|---|---|
| Container acronym **and** snapshot version | Retrieval workflow below |
| Container acronym but **not** the snapshot version | Snapshot picker section below |
| Neither container nor snapshot | Container browser section below |

You only need to perform the auth sequence (Steps A and B below) **once per session** — reuse the same credentials and CSRF token across all calls.

Read `references/BAW_SNAPSHOT_API.md` for full authentication patterns, base URL formats, and response schemas.

---

## Auth sequence — always run first

> **🔒 Security prerequisite — state this before asking for credentials:**
> *"Before we begin, please confirm:*
> - *Your BAW server URL must use **HTTPS** (not HTTP). Do not enter credentials over an unencrypted connection.*
> - *Use a **dedicated service account** with read-only / export permissions rather than a personal or admin account. If you don't have one, ask your BAW administrator to create an account with Workflow Center reader access.*
> - *Credentials are only used to obtain a session token — they are not stored beyond this session.*"

Before any API call, complete these two steps in order:

### Step A — Obtain a session credential

**On-premises:** use Basic auth (`Authorization: Basic <base64(user:pass)>`).

**CP4BA:** Basic auth returns `403`. Exchange credentials for a Bearer token first:
```bash
curl -sk -X POST "https://<cpd-host>/icp4d-api/v1/authorize" \
  -H "Content-Type: application/json" \
  -d '{"username":"<user>","password":"<pass>"}'
```
Use the returned `token` value as `Authorization: Bearer <token>` on all subsequent calls.

### Step B — Obtain the CSRF token

Every Operations API endpoint (`/ops/...`) requires a `BPMCSRFToken` header. Without it the server returns `CWTBG0651E`. Call the login endpoint **once** to get it:

```bash
curl -sk -X POST "<BAW_BASE_URL>/ops/system/login" \
  -H "Authorization: Basic <base64(user:pass)>" \
  -H "Content-Type: application/json" \
  -d '{"refresh_groups": false}'
```

**CP4BA (Bearer token):**
```bash
curl -sk -X POST "<BAW_BASE_URL>/ops/system/login" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"refresh_groups": false}'
```

**Response (HTTP 201):**
```json
{ "csrf_token": "abc123xyz...", "expiration": 7200 }
```

Pass `csrf_token` as the `BPMCSRFToken` header on every subsequent call. Valid for up to 7200 seconds. Re-run this step if `CWTBG0651E` is received after a pause.

> **WLE API:** The WLE endpoints (`/bpm/wle/v1/...`) also enforce `BPMCSRFToken` on CP4BA clusters. Reuse the same token obtained here.

---

## Container browser — user doesn't know which Process App or Toolkit

Use this path when the user says things like "what process apps are deployed?", "show me all toolkits", "list everything on this server", "what's installed?", or simply doesn't provide a container name.

After completing the auth sequence, call:

```bash
curl -sk -X GET \
  "<BAW_BASE_URL>/ops/std/bpm/containers?optional_parts=versions" \
  -H "Authorization: Basic <base64(user:pass)>" \
  -H "BPMCSRFToken: <csrf_token>"
```

The `optional_parts=versions` parameter returns containers **and** their snapshots in a single call. Use `type=PA` or `type=TK` to filter to Process Apps or Toolkits only; omit to return both.

Present results in two labelled tables — Process Apps first, then Toolkits (`"toolkit": true`):

**Process Apps**

| Name | Acronym | Created |
|------|---------|---------|
| HR Process Application | HRAPP | 2025-06-10 |

**Toolkits**

| Name | Acronym | Created |
|------|---------|---------|
| Shared Utilities | SHAREDTK | 2025-03-01 |

> `container` in the response is the acronym to use in all subsequent API calls. `container_name` is the display name.

After presenting the list, ask: "Which one would you like to inspect? I can show you its snapshots."

---

## Snapshot picker — user knows the container but not the snapshot

Use this path when the user provides a container acronym (or name) but not a snapshot version — or after selecting a container from the browser above.

```bash
curl -sk -X GET \
  "<BAW_BASE_URL>/ops/std/bpm/containers/<CONTAINER>/versions" \
  -H "Authorization: Basic <base64(user:pass)>" \
  -H "BPMCSRFToken: <csrf_token>"
```

Present that container's snapshots as a table:

| Acronym | Name | Status | Created |
|---------|------|--------|---------|
| v2.0 | HR Process v2.0 | Active ✅ | 2025-06-10 |
| v1.9 | HR Process v1.9 | Inactive ⏸ | 2025-03-01 |

Then ask: "Which snapshot would you like to inspect in detail?"

---

## Retrieval workflow — known container and snapshot

### Step 1 — Call the Operations API

**Method:** `GET`  
**Path:** `/ops/std/bpm/containers/{container}/versions/{version}`

```bash
curl -sk -X GET \
  "<BAW_BASE_URL>/ops/std/bpm/containers/<CONTAINER>/versions/<VERSION>" \
  -H "Authorization: Basic <base64(user:pass)>" \
  -H "BPMCSRFToken: <csrf_token>"
```

This is a read-only call — no confirmation is needed before making it. Show the exact `curl` command in the response.

### Step 2 — Enrich toolkit dependencies (if needed)

The Operations API `version` schema does not include a `toolkitDependencies` field. To retrieve dependency data, make a second call to the WLE endpoint.

> **WLE context root:** If `<WLE_BASE_URL>` prefix is already known or was established earlier in the session (e.g. `/rest` or `""`), reuse it directly. **Do not probe if the prefix is already known.**

**Probe only once if the WLE context root is unknown:**
If the WLE context root has not been determined yet, test prefixes (`/rest`, `""`, `/baw`, `/bas`) once and cache the working prefix for all subsequent calls in the session:

```bash
for prefix in "/rest" "" "/baw" "/bas"; do
  code=$(curl -sk -o /dev/null -w "%{http_code}" \
    "https://<host>:9443${prefix}/bpm/wle/v1/processApps?includeToolkitProcessApps=true" \
    -H "Authorization: Basic <base64(user:pass)>" \
    -H "BPMCSRFToken: <csrf_token>")
  echo "prefix='${prefix}' -> HTTP $code"
done
```

Use the first prefix that returns HTTP 200 as `<WLE_BASE_URL>` for the calls below and reuse it across all subsequent queries.

**For Process Apps:**
```bash
curl -sk -X GET \
  "<WLE_BASE_URL>/bpm/wle/v1/processApps?includeToolkitProcessApps=true" \
  -H "Authorization: Basic <base64(user:pass)>" \
  -H "BPMCSRFToken: <csrf_token>"
```
Locate the container by `shortName`, then find the target snapshot in `installedSnapshots` by `acronym`. Look for toolkit references in `toolkits`, `dependencies`, or `usedToolkitSnapshots` (field name varies by BAW version).

**For Toolkits:**
```bash
curl -sk -X GET \
  "<WLE_BASE_URL>/bpm/wle/v1/toolkit?includeSnapshots=true" \
  -H "Authorization: Basic <base64(user:pass)>" \
  -H "BPMCSRFToken: <csrf_token>"
```
Locate the toolkit by `shortName`, then find the target snapshot in `installedSnapshots`.

If neither source returns dependency data, report "No toolkit dependencies found for this snapshot." — do not infer or guess.

### Step 3 — Present the Snapshot Summary

Use this fixed block format. Fill every field; use `—` for fields not returned by the API.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Snapshot Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Container      : <container> (Process App | Toolkit)
Snapshot name  : <version_name>
Snapshot ID    : <version>
Status         : Active ✅  |  Inactive ⏸  |  Unknown
Created        : YYYY-MM-DD HH:mm UTC
Branch         : <branch_name>  (or —)
Default        : Yes | No
State          : <status>  (e.g. New, Validated, Released)

Dependencies
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
| Toolkit name     | Acronym | Snapshot |
|------------------|---------|----------|
| System Data      | TWSYS   | 1.0      |

(or: No toolkit dependencies found for this snapshot.)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Field mapping (Operations API → summary block):**

| Block field | API field | Notes |
|---|---|---|
| Container | `container` + `toolkit` flag | `toolkit: true` → "Toolkit", `false` → "Process App" |
| Snapshot name | `version_name` | Human-readable name |
| Snapshot ID | `version` | Acronym — use in subsequent API calls |
| Status | `active: true` → Active ✅ · `active: false` → Inactive ⏸ · field absent → Unknown | |
| Created | `creation_date` | Format as `YYYY-MM-DD HH:mm UTC` |
| Branch | `branch_name` | From Operations API response |
| Default | `is_default` | `true` / `false` |
| State | `status` | Development lifecycle state |
| Dependencies | WLE enrichment (Step 2) | Not in Operations API response |

### Step 4 — Offer next steps

End with: **Next steps:** To activate, deactivate, delete this snapshot, or manage its environment variables, use the `version-lifecycle-manager` skill — or ask me to do it now.

---

## Error handling

| HTTP | Likely cause | What to say |
|---|---|---|
| `401` | Invalid credentials | "Authentication failed — check the username/password or API key and try again." |
| `403` | Insufficient permissions or wrong auth type for CP4BA | "Access denied. On CP4BA, switch from Basic auth to a Bearer token (exchange via `POST /icp4d-api/v1/authorize` — see Step A in the auth sequence). On-premises: ensure the account is in the `tw_admins` group." |
| `400 CWTBG0651E` | Missing or invalid CSRF token | "CSRF token missing or expired. Run `POST <BAW_BASE_URL>/ops/system/login` to obtain a fresh token and include it as the `BPMCSRFToken` header." |
| `400 CWTBG0624E` | Container acronym not found | "The container `<acronym>` was not found — acronyms are case-sensitive. Offer to list containers to confirm the exact acronym." |
| `400 CWTBG0646E` | Snapshot acronym not found | "The snapshot `<version>` was not found in container `<acronym>`. Offer to list snapshots to confirm the exact acronym." |
| `404` | Operations API not present on server | "This server may be IBM BPM 8.x, which does not support the Operations REST API. Use the Process Admin Console to inspect snapshots manually." |

Surface the full raw API response body alongside the plain-language explanation — don't filter it.

---

## Examples

**Example 1 — Process App snapshot**

Input: "Show me the details for snapshot v2.0 of HRAPP on https://baw.hr.example.com/bas. Credentials: admin / hrpass99."

1. Step A: Basic auth — `Authorization: Basic YWRtaW46aHJwYXNzOTk=`
2. Step B: `POST https://baw.hr.example.com/bas/ops/system/login` → obtain `csrf_token`.
3. Call `GET https://baw.hr.example.com/bas/ops/std/bpm/containers/HRAPP/versions/v2.0` with both headers.
4. Probe the WLE context root (try `/rest`, `""`, `/baw`, `/bas`) to find the prefix that returns HTTP 200, then call `GET <WLE_BASE_URL>/bpm/wle/v1/processApps?includeToolkitProcessApps=true` to retrieve toolkit dependencies.
5. Render the Snapshot Summary block.
6. Offer lifecycle action next steps via `version-lifecycle-manager`.

**Example 2 — CP4BA cluster**

Input: "I want to inspect some versions from https://cpd.example.com/bas, CEAdmin/Genius1."

1. Step A: `POST https://cpd.example.com/icp4d-api/v1/authorize` with `CEAdmin`/`Genius1` → obtain Bearer token.
2. Step B: `POST https://cpd.example.com/bas/ops/system/login` with `Authorization: Bearer <token>` → obtain `csrf_token`.
3. Call `GET /bas/ops/std/bpm/containers?optional_parts=versions` with both headers.
4. Present containers table and ask which one to inspect.

**Example 3 — Toolkit snapshot**

Input: "Get metadata for snapshot 1.5 of the SHAREDTK toolkit on https://baw.example.com/bas, admin/pass."

1. Complete auth sequence (Steps A and B).
2. Call `GET /bas/ops/std/bpm/containers/SHAREDTK/versions/1.5` with both headers. Note `toolkit: true` in the response — show container type as "Toolkit" in the summary.
3. Call `GET /bpm/wle/v1/toolkit?includeSnapshots=true` and locate SHAREDTK → 1.5 for dependency data.
4. Render the Snapshot Summary block.
5. Offer lifecycle action next steps.

**Example 4 — User doesn't know the container name at all**

Input: "I'm not sure what process apps we have deployed on https://baw.corp.example.com/bas. Can you show me? admin/corp123."

1. Complete auth sequence (Steps A and B).
2. Call `GET /bas/ops/std/bpm/containers?optional_parts=versions` and present all containers as labelled tables (Process Apps and Toolkits).
3. Ask: "Which one would you like to inspect? I can show you its snapshots."
4. Once the user picks a container, present its snapshots from the `branches[].versions[]` already returned, or call `GET /ops/std/bpm/containers/{container}/versions` if snapshots weren't included.
5. Once the user picks a snapshot, proceed with the Snapshot Summary workflow (Steps 1–4).

**Example 5 — User knows the container but not the snapshot**

Input: "I want to check the status of our current INVOICING process app but I'm not sure what the snapshot name is."

1. Complete auth sequence (Steps A and B).
2. Call `GET /ops/std/bpm/containers/INVOICING/versions` and present its snapshots as a picker table (Acronym, Name, Status, Created).
3. Ask the user to confirm which snapshot to inspect.
4. Then proceed with the Snapshot Summary workflow.

## Reference files

- **`references/BAW_SNAPSHOT_API.md`** — Authentication patterns, CSRF token acquisition, base URLs by deployment type, full response schemas for the Ops API and WLE endpoints, and common error codes.
