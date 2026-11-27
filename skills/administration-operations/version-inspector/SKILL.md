---
name: version-inspector
description: >-
  Inspect IBM Business Automation Workflow snapshots and browse deployed containers. Handles read-only
  queries, including snapshot metadata (version name, lifecycle status, creation
  date, toolkit dependencies), process-app listings, and container inventories.
  Works for both Process App and Toolkit types on Business Automation Workflow on-premises, Business Automation Workflow on Cloud,
  and Cloud Pak for Business Automation. Use whenever an administrator wants to inspect, view, or browse
  versions or snapshots. This skill is read-only and does not change state.
  For state-changing lifecycle operations (installing applications, activating,
  deactivating, deleting snapshots, or setting/syncing environment variables),
  use version-lifecycle-manager.
license: Apache-2.0
compatibility: "Compatible with all IBM-supported releases of IBM Business Automation Workflow and IBM Cloud Pak for Business Automation, as defined by the IBM Software Support Lifecycle."
allowed-tools:
  - Bash
metadata:
  version: "1.0.0"
  display_name: Business Automation Workflow Version Inspector
  short_description: Browse and inspect Business Automation Workflow snapshot metadata — version names, lifecycle status, creation dates, and toolkit dependencies.
  author: IBM Business Automation Workflow Team
---
# Version Inspector

Retrieve and present a plain-language summary of a Business Automation Workflow snapshot's current state — version name, lifecycle status, creation date, in-flight task count, and toolkit dependencies — using the public Operations REST API. No write operations are performed. Works for both Process App and Toolkit container types.

**Companion skill:** The `version-lifecycle-manager` skill handles lifecycle actions (activate, deactivate, delete, env var management) — mention this after presenting the summary.


## Credentials

Never prompt the user for credentials. Credentials are only needed when making a REST call.
When a REST call is about to be made, read `references/CREDENTIAL_HANDLING.md` and follow it for how to authenticate and execute the call. Do this once per session only.

---

## Entry point — choosing the right path

Before calling any API, determine how much the user already knows:

| User knows | Start at |
|---|---|
| Container acronym **and** snapshot version | Retrieval workflow below |
| Container acronym but **not** the snapshot version | Snapshot picker section below |
| Neither container nor snapshot | Container browser section below |

---

## Container browser — user does not know which Process App or Toolkit

Use this path when the user says things like "what process apps are deployed?", "show me all toolkits", "list everything on this server", "what's installed?", or does not provide a container name.

Call `GET /ops/std/bpm/containers` with the query `optional_parts=versions`.

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

Call `GET /ops/std/bpm/containers/<CONTAINER>/versions`.

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

This is a read-only call — no confirmation is needed before making it. Show the method and path you called in the response.

### Step 2 — Enrich toolkit dependencies (if needed)

The Operations API `version` schema does not include a `toolkitDependencies` field. To retrieve dependency data, make a second call to the WLE endpoint.

> **WLE context root:** If `<WLE_BASE_URL>` prefix is already known or was established earlier in the session (e.g. `/rest` or `""`), reuse it directly. **Do not probe if the prefix is already known.**

**Probe only once if the WLE context root is unknown:**
If the WLE context root has not been determined yet, test prefixes (`/rest`, `""`, `/baw`, `/bas`) once and cache the working prefix for all subsequent calls in the session:

For each prefix in `/rest`, `""`, `/baw`, `/bas`, call `GET <prefix>/bpm/wle/v1/processApps` with the query `includeToolkitProcessApps=true` and note the HTTP status.

Use the first prefix that returns HTTP 200 as `<WLE_BASE_URL>` for the calls below and reuse it across all subsequent queries.

**For Process Apps:**
Call `GET <WLE_BASE_URL>/bpm/wle/v1/processApps` with the query `includeToolkitProcessApps=true`.

Locate the container by `shortName`, then find the target snapshot in `installedSnapshots` by `acronym`. Look for toolkit references in `toolkits`, `dependencies`, or `usedToolkitSnapshots` (field name varies by Business Automation Workflow version).

**For Toolkits:**
Call `GET <WLE_BASE_URL>/bpm/wle/v1/toolkit` with the query `includeSnapshots=true`.

Locate the toolkit by `shortName`, then find the target snapshot in `installedSnapshots`.

If no dependency data is found from either source, report "No toolkit dependencies found for this snapshot." — do not infer or guess.

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

## Boundaries

**In scope:** Read-only snapshot metadata queries, listing process apps and toolkits, container inventory discovery, toolkit dependency inspection.

**Out of scope — redirect explicitly:**
- **State-changing lifecycle operations:** Installing applications, activating/deactivating snapshots, deleting snapshots, and setting/syncing environment variables → use `version-lifecycle-manager`.
- **Runtime process instance operations:** Inspecting or acting on running/failed instances → use `inspect-baw-processes`.
- **Generating BPMN processes or Business Objects:** → use `generate-baw-bpmn` or `generate-baw-business-objects`.

---

## Error handling

| HTTP | Likely cause | What to say |
|---|---|---|
| `401` | Invalid credentials | "Authentication failed — check the username/password or API key and try again." |
| `403` | Insufficient permissions or wrong auth type for Cloud Pak for Business Automation | "Access denied. Follow `references/CREDENTIAL_HANDLING.md` to check credentials and permissions. On-premises: ensure the account is in the `tw_admins` group." |
| `400 CWTBG0651E` | Missing or invalid CSRF token | "CSRF token missing or expired. Retry the call as described in `references/CREDENTIAL_HANDLING.md`." |
| `400 CWTBG0624E` | Container acronym not found | "The container `<acronym>` was not found — acronyms are case-sensitive. Offer to list containers to confirm the exact acronym." |
| `400 CWTBG0646E` | Snapshot acronym not found | "The snapshot `<version>` was not found in container `<acronym>`. Offer to list snapshots to confirm the exact acronym." |
| `404` | Operations API not present on server | "This server may be IBM Business Process Manager 8.x, which does not support the Operations REST API. Use the Process Admin Console to inspect snapshots manually." |

Surface the full raw API response body alongside the plain-language explanation — do not filter it.

---

## Examples

**Example 1 — Process App snapshot**

Input: "Show me the details for snapshot v2.0 of HRAPP."

1. Follow `references/CREDENTIAL_HANDLING.md` to connect.
2. Call `GET /ops/std/bpm/containers/HRAPP/versions/v2.0`.
3. Probe the WLE context root (try `/rest`, `""`, `/baw`, `/bas`) to find the prefix that returns HTTP 200, then call `GET <WLE_BASE_URL>/bpm/wle/v1/processApps?includeToolkitProcessApps=true` to retrieve toolkit dependencies.
4. Render the Snapshot Summary block.
5. Offer lifecycle action next steps via `version-lifecycle-manager`.

**Example 2 — Cloud Pak for Business Automation cluster**

Input: "I want to inspect some versions from our Cloud Pak for Business Automation environment."

1. Follow `references/CREDENTIAL_HANDLING.md` to connect.
2. Call `GET /ops/std/bpm/containers?optional_parts=versions`.
3. Present containers table and ask which one to inspect.

**Example 3 — Toolkit snapshot**

Input: "Get metadata for snapshot 1.5 of the SHAREDTK toolkit."

1. Follow `references/CREDENTIAL_HANDLING.md` to connect.
2. Call `GET /ops/std/bpm/containers/SHAREDTK/versions/1.5`. Note `toolkit: true` in the response — show container type as "Toolkit" in the summary.
3. Call `GET /bpm/wle/v1/toolkit?includeSnapshots=true` and locate SHAREDTK to find 1.5 for dependency data.
4. Render the Snapshot Summary block.
5. Offer lifecycle action next steps.

**Example 4 — User does not know the container name at all**

Input: "I'm not sure what process apps we have deployed. Can you show me?"

1. Follow `references/CREDENTIAL_HANDLING.md` to connect.
2. Call `GET /ops/std/bpm/containers?optional_parts=versions` and present all containers as labelled tables (Process Apps and Toolkits).
3. Ask: "Which one would you like to inspect? I can show you its snapshots."
4. Once the user picks a container, present its snapshots from the `branches[].versions[]` already returned, or call `GET /ops/std/bpm/containers/{container}/versions` if snapshots weren't included.
5. Once the user picks a snapshot, proceed with the Snapshot Summary workflow (Steps 1–4).

**Example 5 — User knows the container but not the snapshot**

Input: "I want to check the status of our current INVOICING process app but I'm not sure what the snapshot name is."

1. Follow `references/CREDENTIAL_HANDLING.md` to connect.
2. Call `GET /ops/std/bpm/containers/INVOICING/versions` and present its snapshots as a picker table (Acronym, Name, Status, Created).
3. Ask the user to confirm which snapshot to inspect.
4. Then proceed with the Snapshot Summary workflow.

## Reference files

- **`references/BAW_SNAPSHOT_API.md`** — Authentication patterns, CSRF token acquisition, base URLs by deployment type, full response schemas for the Ops API and WLE endpoints, and common error codes.
