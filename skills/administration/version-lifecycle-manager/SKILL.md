---
name: version-lifecycle-manager
description: >-
  Manages IBM Business Automation Workflow (BAW) Process App and Toolkit
  version lifecycle via the Operations REST API — installing apps, activating,
  deactivating, and deleting snapshots, and reading, setting, and syncing
  environment variables — no Process Admin Console needed. Use when a BAW
  administrator wants to install a process app or toolkit, activate or
  deactivate a snapshot, delete a snapshot, set or sync environment variables,
  or asks about version lifecycle management. Trigger phrases: "install the
  app", "activate snapshot", "deactivate version", "delete snapshot", "set env
  vars", "sync environment variables". Do NOT use for browsing, listing, or
  inspecting snapshots — use the version-inspector skill for those. Supports
  BAW on-premises, BAW on Cloud, and CP4BA (IBM Cloud Pak for Business
  Automation).
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Version Lifecycle Manager

Manage IBM BAW Process App and Toolkit version lifecycles using the BAW Operations REST API. This skill installs applications, activates, deactivates, and deletes snapshots, verifies snapshot state, and manages environment variables — all via documented public REST endpoints with no Process Admin Console required.

> **Companion skill:** To inspect a snapshot's metadata (version name, status, creation date, dependencies) before taking a lifecycle action, use the `version-inspector` skill. The two skills are designed to work together — inspect first, act here.

Before performing any operation:
1. Identify the **container** (Process App or Toolkit acronym/ID) and, where applicable, the **snapshot version** (snapshot acronym/ID).
2. State the **intended operation** clearly and explain its effect.
3. For **deactivation, deletion, or environment-variable changes on a live snapshot**, require explicit user confirmation before proceeding.

Read `references/BAW_SNAPSHOT_API.md` for the exact API details, parameter formats, authentication, deployment-specific base URLs, and response schemas.

## Deployment types

BAW is deployed in three forms — the base URL and authentication differ, but the API path structure is the same:

| Deployment | Base URL pattern | Auth |
|---|---|---|
| BAW on-premises (root mount) | `https://<host>:9443` (Ops API directly at `/ops/...`) | Basic auth or LTPA token |
| BAW on-premises (prefixed) | `https://<host>:9443/rest`, `/bas`, or `/baw` | Basic auth or LTPA token |
| BAW on Cloud | `https://<tenant>.baw.ibmcloud.com` | API key / OAuth |
| CP4BA (Cloud Pak) | `https://<cpd-host>/bas` | ZenAPI key or OAuth |

> **Version requirement:** The `/ops/std/bpm/...` Operations REST API (used for activate, deactivate, delete, verify, and env-var endpoints) requires **BAW 18.0.0.0 or later**. It is not available on IBM BPM 8.x (released before 2018). If the user appears to be on BPM 8.x, state this clearly — see the version detection note below.

The default on-premises port is **9443** (HTTPS). Port 9080 (HTTP) usually redirects to 9443. If the user provides only a hostname with no port, probe port 9443 first. If the user provides only a hostname with no context root, probe the root `""` (no prefix), `/rest`, `/bas`, then `/baw` on port 9443 in that order using `POST <base-url>/ops/system/login` or container probe — use the first that returns HTTP 200, 201, 401, or 403 (401/403 means the root exists but the credentials or auth method were rejected, which is still a valid root).

**Version detection:** After finding the context root, probe the Operations API with a lightweight call:
```bash
curl -sk -o /dev/null -w "%{http_code}" \
  "<base-url>/ops/std/bpm/containers?containerType=PA" \
  -H "Authorization: Basic <credentials>"
```
- If it returns **200, 401, or 403** → Operations API is present; proceed normally. A 403 on CP4BA typically means Basic auth is not accepted — switch to a Zen Bearer token (see CP4BA auth note below).
- If it returns **404** but `GET <base-url>/bpm/wle/v1/processApps` returns **200** → the server is likely IBM BPM 8.x. Stop and tell the user:
  > "The Operations REST API (`/ops/std/bpm/...`) is not available on this server. It requires IBM Business Automation Workflow 18.0 or later, but this server appears to be IBM BPM 8.x. Snapshot lifecycle management through this skill is not supported on BPM 8.x. Use the Process Admin Console on that server to manage snapshots manually."

Ask the user for the base URL and credentials if not supplied. Never hard-code or invent a URL.

> **CP4BA auth note:** On CP4BA clusters, `Authorization: Basic` returns 403 and `Authorization: ZenApiKey <base64>` may return 401 depending on cluster configuration. If either occurs, exchange credentials for a Bearer token first:
> ```bash
> curl -sk -X POST "https://<cpd-host>/icp4d-api/v1/authorize" \
>   -H "Content-Type: application/json" \
>   -d '{"username":"<user>","password":"<pass>"}'
> ```
> Use the returned `token` value as `Authorization: Bearer <token>` for all subsequent calls. Tokens expire; re-exchange if you receive a 401 on a previously working call.

## Step-by-step workflow

### Step 1 — Gather context

Collect everything needed before constructing an API call. Ask for missing values in a single question rather than one at a time:

- **BAW base URL:** e.g. `https://baw.example.com/bas`
- **Container:** Process App or Toolkit acronym (e.g. `MYAPP`) or numeric container ID
- **Snapshot version:** snapshot acronym (e.g. `0.9.3`) or snapshot ID (tip: if unsure, list snapshots first — see `references/BAW_SNAPSHOT_API.md` section 8; snapshots are nested in the `installedSnapshots` array of the container response)
- **Operation:** install / verify / activate / deactivate / delete / read-env-vars / set-env-vars / sync-env-vars / list-versions
- **Credentials:** username/password, API key, or Zen API key, depending on deployment type

For **install**, also collect the `.twx` file path or upload URL.
For **set-env-vars**, also collect the variable name–value pairs to write.
If the user only gave a Process App *name* but not an acronym, ask for the acronym or offer to retrieve it by listing containers first.

### Step 2 — Identify the target and state the operation

Before making any API call, present a clear summary:

```
Container:  MYAPP (Process App)
Snapshot:   0.9.3
Operation:  Activate
Effect:     Snapshot 0.9.3 becomes the active (default) version for new process instances.
```

For deactivation, deletion, or env-var changes on an active snapshot, include the lifecycle-management warning from the relevant section below.

### Step 3 — Confirm destructive or disruptive operations

**Read-only operations** (verify, list versions, read env vars) — present the operation summary and wait for the user to acknowledge before calling the API.

**Install / activate / set env vars** — low risk; present the operation summary and ask the user to confirm before calling the API.

**Sync env vars** ⚠️ — requires confirmation when targeting an active snapshot:
> "Syncing environment variables pushes changes to the running snapshot. Any service or process that reads these variables sees the new values immediately. Ready to proceed?"

**Deactivation** ⚠️ — requires confirmation:
> "Deactivating a snapshot removes it from the active execution path. Any running process instances on this snapshot continue to completion, but no new instances start on it. Ready to proceed?"

**Deletion** 🚨 — requires confirmation with a stronger warning:
> "Deleting a snapshot is permanent and cannot be undone. All process instance history tied exclusively to this snapshot may be lost or corrupted. Confirm you have archived or migrated any relevant instance data before continuing. Ready to proceed?"

Do not make the API call until the user replies affirmatively for any of the above.

### Step 4 — Execute the API call

Construct and execute the call using the endpoint details from `references/BAW_SNAPSHOT_API.md`.

Provide the exact `curl` command (or equivalent) so the user can audit what will be sent:

```bash
# Example — activate
curl -X POST \
  "https://baw.example.com/bas/std/bpm/containers/MYAPP/versions/0.9.3/activate" \
  -H "Authorization: Basic <base64-encoded-credentials>" \
  -H "Content-Type: application/json"
```

Then execute the call if you have the `execute_command` tool available, or ask the user to run it and paste the response.

### Step 5 — Report the result

Report the outcome clearly. Structure:

```
Operation:  Activate snapshot 0.9.3 on MYAPP
Status:     ✅ Success  (HTTP 200)
Message:    <any message returned by the API>
```

If the API returns a warning or error:
- Surface the full response body — don't filter or summarize it.
- Explain what the error code means in plain language (see `references/BAW_SNAPSHOT_API.md` for common errors).
- Suggest a corrective action where applicable.

---

## Lifecycle management best practices

Include the relevant practice note whenever it applies to the requested operation.

### Installing a process app or toolkit
- The install endpoint accepts a `.twx` file (exported from Process Center or Workflow Center).
- If a container with the same acronym already exists on the target server, BAW may create a new snapshot within it rather than a brand-new container — verify with the list endpoint afterward.
- After install, use the verify endpoint to confirm the snapshot was registered and check its initial status before activating.

### Verifying a snapshot
- Use verify proactively after install and before activation to confirm the snapshot is present and its metadata matches expectations.
- The verify endpoint returns the snapshot's current lifecycle state; use it to detect if a snapshot was accidentally deleted or never deployed.

### Activating a snapshot
- Only one snapshot can be active at a time per container. Activating a new version implicitly deactivates the currently active one.
- Verify the snapshot was successfully tested on a non-production environment before activating on production.
- Consider scheduling activation during a maintenance window if the process app is under heavy load.

### Deactivating a snapshot
- Running instances on the deactivated snapshot continue until they complete. Check the verify endpoint (`GET /ops/std/bpm/containers/{container}/versions/{version}`) to see the active instance count before deactivating if there is any concern about in-flight work.
- Do not deactivate the only snapshot of a Process App unless you intend to disable it entirely.

### Environment variables
- Read env vars first (`GET`) before making changes so you have a baseline to roll back to if needed.
- Setting env vars (`POST`) writes the values to the snapshot's configuration but does not push them into the running environment; use the sync endpoint afterward to apply them.
- Syncing env vars (`POST .../sync`) applies the stored configuration to the live snapshot. Warn the user if the snapshot is currently active, since the change is immediate.
- Keep a record of env var values externally (e.g. in a secrets manager or version-controlled config file) — BAW does not maintain a history of previous values.

### Deleting a snapshot
- Deletion is irreversible. Export or archive the snapshot (`.twx` file via Process Center or Workflow Center) before deleting if there is any chance the version will be needed again.
- You cannot delete the currently active snapshot without first deactivating it.
- BAW may reject the deletion if there are active process instances on the snapshot; resolve those first.
- On CP4BA, namespace-level RBAC may require additional authorization for deletion.

---

## Boundaries

**In scope:** Installing, verifying, activating, deactivating, and deleting BAW snapshots; reading, setting, and synchronizing environment variables; listing containers and snapshot versions — all via the Operations REST API; explaining lifecycle-management implications.

**Out of scope — redirect explicitly:**
- **Exporting or backing up a snapshot (.twx):** use the Process Center / Workflow Center UI. This skill only administers snapshots already present on the server or being installed via the install endpoint.
- **Migrating running instances from one snapshot to another:** that is a separate administration task using the BAW Process Admin Console migration tooling.
- **Installing or upgrading BAW itself:** not covered here.
- **Generating BPMN processes or Business Objects:** use `generate-baw-bpmn` or `generate-baw-business-objects`.

---

## Output format

For every operation, always produce (in this order):

1. **Operation summary** — container, snapshot (where applicable), intended action, and effect
2. **Warning / confirmation prompt** (sync env vars, deactivation, and deletion only)
3. **Curl command** — the exact API call that will be (or was) made, with placeholders replaced by the real values
4. **Result** — HTTP status, response body, and a plain-language interpretation
5. **Next steps** (optional) — what the administrator should verify or do after the operation

For **env var operations**, include a table of the variables read or written alongside the result.

For **install**, include a follow-up suggestion to verify the snapshot using the verify endpoint.

---

## Examples

**Example 1 — Deactivate a snapshot**

Input: "Deactivate snapshot v2.1 of our HRAPP process app on https://baw.corp.example.com/bas. My username is admin and password is hunter2."

1. Container: `HRAPP`, snapshot: `v2.1`, operation: Deactivate.
2. Present summary and ⚠️ deactivation warning; wait for confirmation.
3. On confirmation, construct and execute:
   ```bash
   curl -X POST \
     "https://baw.corp.example.com/bas/std/bpm/containers/HRAPP/versions/v2.1/deactivate" \
     -H "Authorization: Basic YWRtaW46aHVudGVyMg==" \
     -H "Content-Type: application/json"
   ```
4. Report HTTP status, response body, and note that running instances on `v2.1` complete normally but no new instances start on that version.

**Example 2 — Install and verify**

Input: "Install snapshot from /tmp/SUPPLYAPP_v3.twx to https://baw.prod.example.com/bas, then verify it landed."

1. Construct the install call (POST to `/ops/std/bpm/containers/install` with the `.twx` file path).
2. After install, automatically follow up with a verify call (GET `/ops/std/bpm/containers/SUPPLYAPP/versions/v3`) and present the snapshot status.
3. Suggest running an env vars sync if the snapshot has environment configuration to carry over from the previous version.

**Example 3 — Set and sync environment variables**

Input: "Set DB_URL to jdbc:db2://prod-db:50000/BAWDB and DB_POOL_SIZE to 20 on snapshot v3.0 of SUPPLYAPP."

1. Summarize the variables to be written: two key–value pairs on SUPPLYAPP v3.0.
2. Call POST `.../env_vars` to store the values.
3. Ask: "Would you like me to sync these variables to the live snapshot now? This will apply them immediately."
4. On confirmation, call POST `.../env_vars/sync` and report the result.

## Reference files

- **`references/BAW_SNAPSHOT_API.md`** — full API reference: all endpoints, parameters, authentication, common errors, and response schemas for all deployment types. Read this before constructing any API call.
