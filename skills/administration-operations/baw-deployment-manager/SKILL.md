---
name: baw-deployment-manager
description: Deploy a process app or toolkit snapshot into a target IBM BAW (Business Automation Workflow) environment, list available process apps and toolkits with their snapshots, check available workflow servers, and monitor installation progress. Uses the BAW REST API to list containers, check workflow servers, POST a snapshot installation request, and poll the returned queue URL until the operation completes or fails. Use whenever the user wants to deploy, install, or promote a snapshot to a workflow environment, list process apps or toolkits, browse available snapshots, check deployment status, monitor an in-progress install, check available servers, list workflow servers, or when phrases like "deploy snapshot", "install process app", "promote to environment", "list process apps", "what toolkits are available", "show me the snapshots", "deployment status", "monitor deployment", "check install progress", "available servers", "workflow servers", or "what servers can I deploy to" appear. Also triggers on CP4BA.
license: Apache-2.0
compatibility: "IBM BAW 22.x and later; IBM CP4BA 22.x and later"
allowed-tools:
  - Bash
metadata:
  version: "1.0.0"
  display_name: BAW Deployment Manager
  short_description: Deploy a BAW process app or toolkit snapshot to a target environment and monitor the installation to completion.
  author: IBM BAW Team
---
<!-- baw-rest-ops: baw-ops.26.0.0.json: /std/bpm/containers, /std/bpm/containers/{container}/versions/{version}/install, /std/bpm/servers/workflow, /system/queue/{id} -->

> **⚠️ REST only — this skill does not support MCP.** All BAW interactions use the BAW REST API exclusively via HTTP calls using `curl`. Do not call any MCP tools at any point — regardless of whether an MCP server is connected or not. Never tell the user to connect an MCP server; this skill does not use one. If you find yourself reaching for an MCP tool, stop and use the REST calls described in this skill instead.

# BAW Deployer

Deploy a BAW process app or toolkit snapshot to a target environment and monitor the installation to completion. Optionally list available containers and snapshots first if the user does not know what is on the server.

## Execution mode

This skill operates in **REST mode only**. All calls use the BAW REST API directly via `curl`.

Before making any REST call, read `references/CREDENTIAL_HANDLING.md` and follow it — it will read credentials from `.env` automatically. Do this once per session only.

This skill makes up to three REST calls:

1. **List** *(optional)* — `GET /std/bpm/containers` — discover available process apps, toolkits, and their snapshots
2. **Install** — `POST /std/bpm/containers/{container}/versions/{version}/install`
3. **Poll** — `GET <queueUrl>` (URL returned directly by the install response)


## Credentials

Never prompt the user for credentials. Credentials are only needed when making a REST call.
When a REST call is about to be made, read `references/CREDENTIAL_HANDLING.md` and follow it — it will read credentials from `.env` automatically, and only prompt the user if a value is missing from that file. Do this once per session only.

---
## Step 0 — List available containers (optional)

Perform this step when the user does not know the container acronym or available snapshot versions, or when they ask to "list process apps", "show toolkits", "what can I deploy", or similar.

This step uses the `baw_url`, `username`, and `password` inputs. If the target environment is a CP4BA Zen deployment (e.g. `https://<cpd-host>/<instance_name>`), obtain a Zen Bearer token and CSRF token first (see Authentication section below).

### Authentication & Endpoints

Depending on the environment topology:

1. **Traditional BAW / Workflow Center (tWAS):**

   **Step A — Obtain CSRF token** via `POST /bpm/system/login`. This is **required** — every `/ops/` and `/bpm/` API call needs a `BPMCSRFToken` header or it returns `403 CWTBG0651E`:
   ```bash
   CSRF=$(curl -s -k -u "<username>:<password>" -X POST \
     -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -d '{"refresh-groups": false, "requested-lifetime": 7200}' \
     "<baw_url>/bpm/system/login" \
     | python3 -c 'import sys, json; print(json.load(sys.stdin).get("csrf_token",""))')
   ```

   **Step B — Call the Operations REST API** with Basic Auth and CSRF token:
   ```bash
   curl -s -k \
     -u "<username>:<password>" \
     -H "Accept: application/json" \
     -H "BPMCSRFToken: $CSRF" \
     "<baw_url>/ops/std/bpm/containers" \
     -w "\n__HTTP_STATUS__:%{http_code}"
   ```

   > **Note:** The CSRF token expires after 7200 seconds (2 hours). If calls start returning `403 CWTBG0651E` mid-session, re-run Step A to refresh it.

2. **Cloud Pak for Business Automation (CP4BA / Zen Runtime):**

   **Step A — Obtain Zen Bearer token** via `/v1/preauth/validateAuth` (use the CPD host, not the instance prefix):
   ```bash
   TOKEN=$(curl -s -k -u "<username>:<password>" \
     "https://<cpd_host>/v1/preauth/validateAuth" \
     | python3 -c 'import sys, json; print(json.load(sys.stdin).get("accessToken",""))')
   ```

   **Step B — Obtain CSRF token** via `POST /ops/system/login`. This is **required** — every `/ops/` call needs a `BPMCSRFToken` header or it returns `403 CWTBG0651E`. The `baw_url` here includes the instance prefix (e.g. `https://<cpd-host>/bas` or `https://<cpd-host>/baw-bawins1`):
   ```bash
   CSRF=$(curl -s -k -X POST \
     -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{}' \
     "<baw_url>/ops/system/login" \
     | python3 -c 'import sys, json; print(json.load(sys.stdin).get("csrf_token",""))')
   ```

   **Step C — Call the Operations REST API** with both headers:
   ```bash
   curl -s -k \
     -H "Accept: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -H "BPMCSRFToken: $CSRF" \
     "<baw_url>/ops/std/bpm/containers" \
     -w "\n__HTTP_STATUS__:%{http_code}"
   ```

   > **Note:** The CSRF token expires after 7200 seconds (2 hours). If calls start returning `403 CWTBG0651E` mid-session, re-run Step B to refresh it.

### Response Shapes

**Schema A — Traditional BAW (`processAppsList`):**
```json
{
  "status": "200",
  "data": {
    "processAppsList": [
      {
        "ID": "2066.b1e4...",
        "shortName": "BILLPAY",
        "name": "Bill Payment",
        "defaultVersion": "Main",
        "installedSnapshots": [
          {
            "name": "2024.04.1",
            "ID": "...",
            "acronym": "2024041",
            "active": true
          }
        ]
      }
    ]
  }
}
```

**Schema B — CP4BA / Operations API (`containers` array):**
```json
{
  "containers": [
    {
      "container": "BILLPAY",
      "container_name": "Bill Payment",
      "toolkit": false,
      "id": "2066.b1e4...",
      "branches": []
    },
    {
      "container": "SYSBPMUI",
      "container_name": "UI Toolkit",
      "toolkit": true,
      "id": "2066.c2f5..."
    }
  ]
}
```

> **Note:** For Schema B, query snapshots and versions per container using `GET <baw_url>/ops/std/bpm/containers/{container}/versions`.

### Key fields mapping

| Field (Schema A / Schema B) | Meaning | Used as |
|---|---|---|
| `shortName` / `container` | Container acronym | `container` input for deployment |
| `name` / `container_name` | Human-readable name | display only |
| `toolkit` (`true`/`false`) | Toolkit flag | group into Process Apps vs Toolkits |
| `installedSnapshots[].name` / `version_name` | Snapshot name | `version` input for deployment |
| `installedSnapshots[].acronym` / `version` | Snapshot acronym | alternative `version` input |

### Presenting the results

Format the output as a table or grouped list, separating toolkits and process apps:

```
Process Applications
  BILLPAY  "Bill Payment"
    Snapshots: 2024.04.1 (active), 2024.03.0

Toolkits
  SYSBPMUI "UI Toolkit"
    Snapshots: 8.6.0.0 (active)
```

After displaying the list, prompt:

> "Which container and snapshot would you like to deploy, and to which target environment?"

### Error handling

| HTTP | Likely cause |
|---|---|
| 401 / 403 | Credentials rejected or insufficient permissions |
| 404 | The `/std/bpm/containers` endpoint is unavailable on this server version |
| 500 | Internal server error — share the body for diagnosis |

---

## Step 0b — List registered Workflow Servers (optional, use before deployment)

Use this step to discover the valid `server` value required by the install endpoint on some BAW/CP4BA configurations. If the install in Step 1 returns error `CWTBG0011E` ("mandatory parameter 'server' is not specified") or `CWTBG0701E` ("Server X does not exist"), run this first. Also run proactively when the user asks "what servers are available", "which servers can I deploy to", or similar.

Try both endpoints in order — use whichever returns a successful response.

### Option A — Traditional BAW (`/ops/std/bpm/servers/workflow`)

Obtain a CSRF token first (see Step 0 authentication), then:

```bash
curl -s -k \
  -u "<username>:<password>" \
  -H "Accept: application/json" \
  -H "BPMCSRFToken: $CSRF" \
  "<baw_url>/ops/std/bpm/servers/workflow" \
  -w "\n__HTTP_STATUS__:%{http_code}"
```

**Response shape:**

```json
{
  "servers": [
    {
      "server_name": "dev",
      "server_type": "TEST",
      "online": true,
      "environment_name": "Development"
    }
  ]
}
```

Key fields:

| Field | Meaning |
|---|---|
| `server_name` | The value to pass as the `server` query parameter in the install call |
| `server_type` | `TEST` or `PRODUCTION` = deployable target; `PLAYBACK` = authoring server, skip |
| `online` | If `false`, the server is unreachable — do not deploy to it |
| `environment_name` | Human-readable environment label |

### Option B — CP4BA Operations API (`/ops/std/bpm/servers/workflow`)

Use this endpoint when the BAW environment is a CP4BA Zen deployment (e.g. `https://<cpd-host>/bas/`). Obtain a Zen Bearer token and CSRF token first (see Step 0 authentication), then:

```bash
curl -s -k \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "BPMCSRFToken: $CSRF" \
  "<baw_url>/ops/std/bpm/servers/workflow" \
  -w "\n__HTTP_STATUS__:%{http_code}"
```

For example, with the environment `https://cpd-demo-project.apps.hs.cp.fyre.ibm.com/bas`:

```bash
TOKEN=$(curl -s -k -u "<username>:<password>" \
  "https://cpd-demo-project.apps.hs.cp.fyre.ibm.com/v1/preauth/validateAuth" \
  | python3 -c 'import sys, json; print(json.load(sys.stdin).get("accessToken",""))')

CSRF=$(curl -s -k -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{}' \
  "https://cpd-demo-project.apps.hs.cp.fyre.ibm.com/bas/ops/system/login" \
  | python3 -c 'import sys, json; print(json.load(sys.stdin).get("csrf_token",""))')

curl -s -k \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "BPMCSRFToken: $CSRF" \
  "https://cpd-demo-project.apps.hs.cp.fyre.ibm.com/bas/ops/std/bpm/servers/workflow" \
  -w "\n__HTTP_STATUS__:%{http_code}"
```

**Response shape:**

```json
{
  "servers": [
    {
      "server_name": "dev",
      "server_type": "TEST",
      "online": true,
      "environment_name": "Development"
    },
    {
      "server_name": "production",
      "server_type": "PRODUCTION",
      "online": true,
      "environment_name": "Production"
    }
  ]
}
```

Key fields:

| Field | Meaning |
|---|---|
| `server_name` | The value to pass as the `server` query parameter in the install call |
| `server_type` | `TEST` or `PRODUCTION` = deployable target; `PLAYBACK` = authoring server, skip |
| `online` | If `false`, the server is unreachable — do not deploy to it |
| `environment_name` | Human-readable environment label |

### Presenting results

Present all non-`PLAYBACK` / non-offline servers in a table:

```
Available Workflow Servers
  Name         Type        Status   Environment
  dev          TEST        Online   Development
  production   PRODUCTION  Online   Production
```

If more than one deployable server exists, ask the user which one to deploy to before proceeding.

### If both endpoints return 404

Neither server-listing path is available. Instruct the user to find the server name in one of these places:

- **Process Admin Console** → Server Admin → Overview → "Server Name" field
- **Traditional BAW (Workflow Center):** Workflow Center → Process Center → Admin → Workflow Servers
- **CP4BA containerized (Business Automation Studio):** Business Automation Studio → Workflow Servers (or check with your CP4BA administrator)

---

## Required inputs for deployment

Collect these before making any REST call. Use `ask_followup_question` for anything missing:

| Input | Notes |
|---|---|
| `baw_url` | Base URL of the target BAW/CP4BA server, e.g. `https://baw.example.com/bas` or `https://cpd.example.com/bas/`. Strip any trailing slash before building URLs. |
| `username` | BAW user with deployment authority |
| `password` | Password — treat as sensitive; do not log or echo it |
| `container` | Process app or toolkit acronym (container ID), e.g. `BILLPAY` |
| `version` | Snapshot ID or acronym, e.g. `2024.04.1` or `TIP` |
| `target_env` | Deployment environment name, e.g. `Production`, `QA` (passed as the `install_to` query parameter) |
| `server` | *(CP4BA/some configs)* Registered Workflow Server name, e.g. `dev`. Required when the server returns `CWTBG0011E`. Discover using Step 0b. |

Optional inputs:

| Input | Default | Notes |
|---|---|---|
| `force_offline` | `false` | Set `true` to force offline install |
| `poll_interval_sec` | `10` | Seconds between status checks |
| `timeout_sec` | `600` | Stop polling after this many seconds and report timeout |

## Step 1 — Trigger the installation

Build the URL:

- **Traditional BAW / Workflow Center:**
  ```
  POST {baw_url}/std/bpm/containers/{container}/versions/{version}/install
       ?install_to={target_env}
       [&server={server}]       (required on some BAW configurations)
       [&offline=true]          (only when force_offline is true)
  ```
- **CP4BA Zen Runtime (Operations REST):**
  ```
  POST {baw_url}/ops/std/bpm/containers/{container}/versions/{version}/install
       ?install_to={target_env}
       [&offline=true]          (only when force_offline is true)
  ```

Set headers:
- `Content-Type: application/json`
- `Accept: application/json`
- Authorization + CSRF (**required on both tWAS and CP4BA**):
  - Traditional BAW: `-u "<username>:<password>"` + `-H "BPMCSRFToken: $CSRF"` (token from `POST /bpm/system/login`)
  - CP4BA Zen: `-H "Authorization: Bearer $TOKEN"` + `-H "BPMCSRFToken: $CSRF"` (token from `POST /ops/system/login`)

Use `execute_command` with `curl` to make the request. Acquire the CSRF token first (see Step 0 authentication). Example:

```bash
# Traditional BAW (CSRF must already be set — see Step 0 authentication)
curl -s -k -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -u "<username>:<password>" \
  -H "BPMCSRFToken: $CSRF" \
  "<baw_url>/ops/std/bpm/containers/<container>/versions/<version>/install?install_to=<target_env>&server=<server>" \
  -w "\n__HTTP_STATUS__:%{http_code}"

# CP4BA Zen (TOKEN and CSRF must already be set — see Step 0 authentication)
curl -s -k -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "BPMCSRFToken: $CSRF" \
  "<baw_url>/ops/std/bpm/containers/<container>/versions/<version>/install?install_to=<target_env>&server=<server>" \
  -w "\n__HTTP_STATUS__:%{http_code}"
```

Parse the response body (JSON) and the HTTP status code.

### Install response handling

**Success (HTTP 200 or 202):**

The response body contains a `status_url` (or equivalent) field — a fully qualified URL pointing to the queue item for this job, for example:

```json
{
  "status": "Queued",
  "status_url": "https://baw.example.com/bas/system/queue/a1b2c3d4-..."
}
```

Extract the `status_url` value verbatim. Do **not** reconstruct the URL from only the queue ID — use the `status_url` exactly as the response returns it. Proceed to Step 2.

**Synchronous success (HTTP 200 with `status: "Completed"`):**

Report success immediately and skip polling.

**Error (4xx / 5xx):**

Report the HTTP status code and the full response body to the user. Common causes:

| Code | Likely cause |
|---|---|
| 400 | Invalid container ID, version, or environment name |
| 401 / 403 | Credentials rejected or insufficient permissions |
| 404 | Container or version not found on this server |
| 409 | Snapshot already installed in this environment |
| 500 | Internal server error — share the body for diagnosis |

Do not proceed to polling if the install POST fails.

## Step 2 — Poll for completion

Poll the `status_url` that Step 1 returns at the configured interval until the status reaches a terminal state or the timeout elapses.

For **CP4BA** the queue endpoint also requires `BPMCSRFToken`. The `status_url` is a fully-qualified URL to `<baw_url>/ops/system/queue/<id>` — use the same `$TOKEN` and `$CSRF` variables:

```bash
# Traditional BAW
curl -s -k \
  -H "Accept: application/json" \
  -u "<username>:<password>" \
  "<status_url>" \
  -w "\n__HTTP_STATUS__:%{http_code}"

# CP4BA Zen
curl -s -k \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "BPMCSRFToken: $CSRF" \
  "<status_url>" \
  -w "\n__HTTP_STATUS__:%{http_code}"
```

The queue item response looks like:

```json
{
  "queueId": "a1b2c3d4-...",
  "status": "Running",
  "percentComplete": 45,
  "message": "Installing artifacts..."
}
```

### Terminal states

| `status` value | Meaning | Action |
|---|---|---|
| `Completed` | Install succeeded | Report success with any message from the response |
| `Failed` | Install failed | Report failure with `message` and `errorDetails` from the response |
| `Cancelled` | Install cancelled | Report cancellation |

Continue polling for all other status values (`Queued`, `Running`, etc.).

### Progress reporting

After each poll, report to the user:

```
[HH:MM:SS] Status: Running — 45% complete — "Installing artifacts..."
```

Use `date` in the shell to get the current time, or derive it from elapsed seconds since the install started.

### Timeout

If `timeout_sec` elapses without reaching a terminal state, report:

> ⚠️ **Deployment timed out** after {timeout_sec}s. The last known status was `{status}` ({percentComplete}% complete).
> The operation may still be in progress on the server. You can check manually using:
> `GET <status_url>`

## Step 3 — Final report

When the status reaches a terminal state, present a summary:

```
✅ Deployment complete
   Container : BILLPAY
   Version   : 2024.04.1
   Target    : Production
   Duration  : 1m 23s
   Message   : Successfully installed.
```

For failures:

```
❌ Deployment failed
   Container : BILLPAY
   Version   : 2024.04.1
   Target    : Production
   Duration  : 0m 47s
   Error     : <message from response>
   Details   : <errorDetails from response, if present>
```

## Resuming a monitor session

If the user already has a queue URL from a previous install (the server returned a queue URL but this session did not capture it), skip Step 1 and go directly to Step 2 with the provided URL. Ask:

> "Do you have the queue status URL from the install response? If so I can monitor it directly."

## Security notes

- Never reveal the password in any output — this covers both command stdout and any curl commands shown to the user. Always display credentials as `-u "<username>:<password>"` (placeholder form) or `-u "$BAW_USER:$BAW_PASS"` (env var form), never substituting the real password value.
- If the server uses a self-signed certificate, append `-k` to curl commands and warn the user that `-k` disables certificate validation.

## Boundaries

**In scope:**
- Listing process apps and toolkits with their available snapshots via `GET …/containers`
- Triggering a snapshot installation via `POST …/install`
- Monitoring deployment progress via the queue URL
- Reporting installation success or failure

**Out of scope — redirect clearly:**
- Exporting or creating snapshots — use **Workflow Center** (traditional BAW) or **Business Automation Studio** (CP4BA containerized) directly
- Migrating data or process instances — not covered by this API
- Setting up environment configuration (data sources, LDAP) — administrative task outside this skill
- Deploying via TWX file import — different workflow; this skill uses the container/version REST route only
