---
name: baw-deployment-manager
description: "Deploy a process app or toolkit snapshot into a target IBM Business Automation Workflow environment, list process apps and toolkits with their snapshots, check available workflow servers, and monitor installation progress. Uses the REST API to list containers, check servers, POST a snapshot installation request, and poll the returned queue URL until the install completes or fails. Use whenever the user wants to deploy, install, or promote a snapshot, list process apps or toolkits, browse snapshots, check deployment status, monitor an in-progress install, or list available workflow servers. Trigger phrases: 'deploy snapshot', 'install process app', 'promote to environment', 'list process apps', 'what toolkits are available', 'deployment status', 'monitor deployment', 'check install progress', 'what servers can I deploy to'. Also triggers on Cloud Pak for Business Automation."
license: Apache-2.0
compatibility: "Compatible with all IBM-supported releases of IBM Business Automation Workflow and IBM Cloud Pak for Business Automation, as defined by the IBM Software Support Lifecycle."
allowed-tools:
  - Bash
metadata:
  version: "1.0.0"
  display_name: Business Automation Workflow Deployment Manager
  short_description: Deploy a Business Automation Workflow process app or toolkit snapshot to a target environment and monitor the installation to completion.
  author: IBM Business Automation Workflow Team
---
<!-- baw-rest-ops: baw-ops.26.0.0.json: /std/bpm/containers, /std/bpm/containers/{container}/versions/{version}/install, /std/bpm/servers/workflow, /system/queue/{id} -->

> **⚠️ REST only — this skill does not support MCP.** All Business Automation Workflow interactions use the Business Automation Workflow REST API exclusively. Do not call any MCP tools at any point — regardless of whether an MCP server is connected or not. Never tell the user to connect an MCP server; this skill does not use one. If you find yourself reaching for an MCP tool, stop and use the REST calls described in this skill instead.

# Business Automation Workflow Deployer

Deploy a Business Automation Workflow process app or toolkit snapshot to a target environment and monitor the installation to completion. Optionally list available containers and snapshots first if the user does not know what is on the server.

## Execution mode

This skill operates in **REST mode only**. All calls use the Business Automation Workflow REST API directly.

Before making any REST call, read `references/CREDENTIAL_HANDLING.md` and follow it for how to authenticate and execute the call. Do this once per session only.

This skill makes up to three REST calls:

1. **List** *(optional)* — `GET /ops/std/bpm/containers` — discover available process apps, toolkits, and their snapshots
2. **Install** — `POST /ops/std/bpm/containers/{container}/versions/{version}/install`
3. **Poll** — `GET <queueUrl>` (URL returned directly by the install response)


## Credentials

Never prompt the user for credentials. Credentials are only needed when making a REST call.
When a REST call is about to be made, read `references/CREDENTIAL_HANDLING.md` and follow it for how to authenticate and execute the call. Do this once per session only.

---
## Step 0 — List available containers (optional)

Perform this step when the user does not know the container acronym or available snapshot versions, or when they ask to "list process apps", "show toolkits", "what can I deploy", or similar.

This step needs a working Business Automation Workflow connection. Follow `references/CREDENTIAL_HANDLING.md`.

### Endpoint

Call `GET /ops/std/bpm/containers`. The same path applies to traditional Business Automation Workflow and Cloud Pak for Business Automation; the base URL (including any instance prefix such as `/bas` or `/baw-bawins1`) and the authentication method are handled by the connection described in `references/CREDENTIAL_HANDLING.md`.

### Response Shapes

**Schema A — Traditional Business Automation Workflow (`processAppsList`):**
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

**Schema B — Cloud Pak for Business Automation / Operations API (`containers` array):**
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

> **Note:** For Schema B, query snapshots and versions per container using `GET /ops/std/bpm/containers/{container}/versions`.

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

Use this step to discover the valid `server` value required by the install endpoint on some Business Automation Workflow or Cloud Pak for Business Automation configurations. If the install in Step 1 returns error `CWTBG0011E` ("mandatory parameter 'server' is not specified") or `CWTBG0701E` ("Server X does not exist"), run this first. Also run proactively when the user asks "what servers are available", "which servers can I deploy to", or similar.

Try both endpoints in order — use whichever returns a successful response.

### Option A — Traditional Business Automation Workflow (`/ops/std/bpm/servers/workflow`)

Call `GET /ops/std/bpm/servers/workflow`.

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

### Option B — Cloud Pak for Business Automation Operations API (`/ops/std/bpm/servers/workflow`)

Use the same call as Option A: `GET /ops/std/bpm/servers/workflow`. On Cloud Pak for Business Automation the base URL already includes the instance prefix (for example `/bas` or `/baw-bawins1`) and the authentication method differs; `references/CREDENTIAL_HANDLING.md` covers both.

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
- **Traditional Business Automation Workflow (Workflow Center):** Workflow Center → Process Center → Admin → Workflow Servers
- **Cloud Pak for Business Automation containerized (Business Automation Studio):** Business Automation Studio → Workflow Servers (or check with your Cloud Pak for Business Automation administrator)

---

## Required inputs for deployment

Collect these before making any REST call. Use `ask_followup_question` for anything missing:

| Input | Notes |
|---|---|
| `target_server` | Which Business Automation Workflow server to deploy to. The connection is configured by the user in the Business Automation Workflow connection settings described in `references/CREDENTIAL_HANDLING.md`; confirm the `base_url` reported by the connection check with the user before installing. |
| `container` | Process app or toolkit acronym (container ID), e.g. `BILLPAY` |
| `version` | Snapshot ID or acronym, e.g. `2024.04.1` or `TIP` |
| `target_env` | Deployment environment name, e.g. `Production`, `QA` (passed as the `install_to` query parameter) |
| `server` | *(Cloud Pak for Business Automation or some configurations)* Registered Workflow Server name, e.g. `dev`. Required when the server returns `CWTBG0011E`. Discover using Step 0b. |

Optional inputs:

| Input | Default | Notes |
|---|---|---|
| `force_offline` | `false` | Set `true` to force offline install |
| `poll_interval_sec` | `10` | Seconds between status checks |
| `timeout_sec` | `600` | Stop polling after this many seconds and report timeout |

## Step 1 — Trigger the installation

Build the request (path is server-relative):

- **Operations API (traditional Business Automation Workflow and Cloud Pak for Business Automation):**
  ```
  POST /ops/std/bpm/containers/{container}/versions/{version}/install
       ?install_to={target_env}
       [&server={server}]       (required on some configurations)
       [&offline=true]          (only when force_offline is true)
  ```

Send it as described in `references/CREDENTIAL_HANDLING.md` (no request body is required).

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

Poll with `GET /ops/system/queue/<id>`, where `<id>` is the last path segment of the `status_url` returned by Step 1. Give the server-relative path only; the connection and authentication are handled as described in `references/CREDENTIAL_HANDLING.md`.

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

- Never reveal or ask for credentials. Authentication follows `references/CREDENTIAL_HANDLING.md`.
- If the server uses a self-signed certificate, the user must set the certificate-verification option described in `references/CREDENTIAL_HANDLING.md`; warn them that this disables certificate validation.

## Boundaries

**In scope:**
- Listing process apps and toolkits with their available snapshots via `GET …/containers`
- Triggering a snapshot installation via `POST …/install`
- Monitoring deployment progress via the queue URL
- Reporting installation success or failure

**Out of scope — redirect clearly:**
- Exporting or creating snapshots — use **Workflow Center** (traditional Business Automation Workflow) or **Business Automation Studio** (Cloud Pak for Business Automation containerized) directly
- Migrating data or process instances — not covered by this API
- Setting up environment configuration (data sources, LDAP) — administrative task outside this skill
- Deploying via TWX file import — different workflow; this skill uses the container/version REST route only
