# BAW Deployment Manager — Documentation

> Deploy a Process App or Toolkit snapshot into a target IBM BAW environment, list available process apps and toolkits with their snapshots, check available workflow servers, and monitor installation progress.

## Purpose

The BAW Deployment Manager skill automates snapshot deployments to IBM Business Automation Workflow (BAW) environments — both traditional BAW (tWAS) and Cloud Pak for Business Automation (CP4BA/Zen). It is designed for BAW administrators and release engineers who want to deploy, monitor, and confirm snapshot installations without manually calling REST APIs or navigating the Process Admin Console. Use it to deploy a known snapshot, browse what is available on a server before deploying, check which workflow servers are registered, or resume monitoring a deployment that is already in progress.

## Setup and configuration

- **`curl`** must be available in the shell — all BAW interactions use `curl` via `execute_command`. No MCP server is used or required.
- **Python 3** (`python3`) must be available in the shell — used inline to extract JSON fields (e.g., CSRF token, access token) from `curl` responses.
- **BAW credentials** — a username and password with deployment authority on the target BAW server. You will be prompted for these at the start of each session.
- **Network access** — Bob's execution environment must be able to reach the target BAW/CP4BA host over HTTPS. Servers using self-signed certificates are supported (the skill appends `-k` to `curl` and warns you that certificate validation is disabled).
- No API keys, MCP servers, or additional package installs are needed.

## Compatibility

- **REST API only** — this skill uses the BAW Operations REST API exclusively. TWX file import workflows and the Process Admin Console are not used.
- **Traditional BAW (tWAS)** and **CP4BA (Zen Runtime)** are both supported, but the authentication flow differs: tWAS uses Basic Auth + a CSRF token from `POST /bpm/system/login`; CP4BA uses a Zen Bearer token from `/v1/preauth/validateAuth` plus a CSRF token from `POST /ops/system/login`.
- **CSRF token required** — every `/ops/` and `/bpm/` API call needs a `BPMCSRFToken` header. If you see `403 CWTBG0651E` mid-session, the CSRF token has expired (2-hour lifetime); Bob will automatically re-authenticate and retry.
- **`server` parameter** — some BAW and CP4BA configurations require a registered Workflow Server name (`server=<name>`) in the install URL. If the install returns `CWTBG0011E` or `CWTBG0701E`, Bob will run the server-listing step to discover valid server names before retrying.

## Prompt examples

### Deploy a known snapshot to a named environment

**Prompt:**
> Deploy the BILLPAY process app snapshot 2024.04.1 to the Production environment. The BAW server is https://baw.example.com/bas, username is bawadmin, password is s3cr3t.

**What to expect:** Bob triggers the install POST, then polls the returned queue URL at 10-second intervals — reporting `[HH:MM:SS] Status: Running — N% complete` after each check — and finishes with a ✅ success summary showing container, version, target, and duration.

---

### Deploy a toolkit snapshot to CP4BA

**Prompt:**
> Deploy snapshot TIP for toolkit SHARED to the QA environment. BAW server is https://cpd.example.com/bas, username is admin, password is pass.

**What to expect:** Bob detects a CP4BA Zen URL, obtains a Bearer token and CSRF token, constructs the `/ops/` install URL, and proceeds to deploy and monitor — reporting progress and a final summary.

---

### Browse available process apps and toolkits before deploying

**Prompt:**
> List all available process apps and toolkits on my BAW server at https://baw.example.com/bas. Username: bawadmin, password: s3cr3t.

**What to expect:** Bob calls `GET /ops/std/bpm/containers`, formats the results as a grouped table of Process Applications and Toolkits with snapshot names, and then asks which container, snapshot, and target environment you want to deploy to.

---

### Check which workflow servers are available

**Prompt:**
> What workflow servers can I deploy to on https://baw.example.com/bas? Username: bawadmin, password: s3cr3t.

**What to expect:** Bob queries `GET /ops/std/bpm/servers/workflow` and returns a table of deployable (non-PLAYBACK, online) servers showing their name, type, and environment label, then prompts you to choose one if more than one is available.

---

### Resume monitoring an already-started deployment

**Prompt:**
> I started a deployment earlier and the server gave me this queue URL: https://baw.example.com/bas/system/queue/xyz-789-abc. Can you monitor it for me? Use admin / pass123 as credentials.

**What to expect:** Bob skips the install step entirely and immediately begins polling the provided URL, reporting progress after each interval and presenting a final status summary when a terminal state is reached.

---

### Deploy with force offline install

**Prompt:**
> Deploy the HRPORTAL process app snapshot 2024.10.0 to Production with force offline install enabled. BAW server is https://baw.example.com/bas, username is bawadmin, password is s3cr3t.

**What to expect:** Bob appends `&offline=true` to the install URL alongside `install_to=Production`, then deploys and monitors as normal.

---

### Deploy with custom poll interval and timeout

**Prompt:**
> Deploy snapshot 2024.08.0 for process app CLAIMS to QA on https://baw.example.com/bas. Username: bawadmin, password: s3cr3t. Use a timeout of 30 seconds and a poll interval of 5 seconds.

**What to expect:** Bob polls every 5 seconds and, if no terminal state is reached within 30 seconds, stops and reports a ⚠️ timeout warning with the last known status, percent complete, and the queue URL for manual follow-up.

---

### Missing container or version — Bob asks before acting

**Prompt:**
> I want to deploy a snapshot to the staging environment on https://baw.example.com/bas. My username is deployer and password is abc123.

**What to expect:** Bob detects that the container acronym and snapshot version are missing, asks for them using a follow-up question, and does not make any REST call until both are provided.

---

### Deployment fails midway — failure summary

**Prompt:**
> Deploy snapshot 2024.06.1 for process app INVOICING to Production on https://baw.example.com/bas. Username: bawadmin, password: s3cr3t.
>
> *(The deployment fails with message "Artifact validation error" and errorDetails "Schema mismatch on process InvoiceApproval".)*

**What to expect:** Bob stops polling immediately on a `Failed` status and presents a ❌ failure summary that includes the container, version, target, elapsed duration, error message, and errorDetails field.

---

### Out-of-scope — exporting or creating a snapshot

**Prompt:**
> Can you export the BILLPAY snapshot 2024.04.1 as a TWX file from https://baw.example.com/bas?

**What to expect:** Bob explains that snapshot export and TWX file creation are outside the scope of this skill, and directs you to use **Workflow Center** (traditional BAW) or **Business Automation Studio** (CP4BA containerized) directly for that operation.
