# Version Inspector — Documentation

> Inspect IBM® BAW snapshots and browse deployed containers — retrieves a plain-language metadata summary (version name, lifecycle status, creation date, and toolkit dependencies) for a specific snapshot, and lists all Process Apps and Toolkits when the user doesn't know which container or snapshot to inspect.

## Purpose

This skill retrieves and presents read-only snapshot metadata from a BAW server using the Operations REST API. It is designed for BAW administrators who want to know what is deployed, what state a snapshot is in, or what toolkit dependencies it carries — before taking any lifecycle action. The skill handles three levels of discovery automatically: browsing all containers when nothing is known, listing snapshots within a container when only the app name is known, and retrieving the full detail summary when both the container and snapshot are known.

> **Companion skill:** To activate, deactivate, delete a snapshot, or manage its environment variables, use the `version-lifecycle-manager` skill. The two skills are designed to work together — inspect first, act there.

## Setup and configuration

- BAW server URL and credentials are required. The skill will ask for them if not supplied.
- On-premises: provide `https://<host>:9443` and a username/password for Basic authentication.
- CP4BA (Cloud Pak for Business Automation): provide the CP4BA route (e.g. `https://<cpd-route>/bas`) and credentials. The skill exchanges them automatically for a Bearer token when Basic auth returns `403`.
- BAW on Cloud: provide the tenant URL (`https://<tenant>.baw.ibmcloud.com`) and an IBM Cloud IAM Bearer token.
- No local software, packages, or MCP servers are required. The skill uses `execute_command` (curl) when available, or shows the exact command for you to run.
- The skill obtains a `BPMCSRFToken` from the login endpoint automatically at the start of each session — you do not need to supply one.

## Compatibility

- BAW 18.0.0.0 or later required. The Operations REST API (`/ops/std/bpm/...`) used for snapshot inspection is not available on IBM BPM 8.x. If the server returns `404` on the Operations path, this skill cannot retrieve snapshot metadata — use the Process Admin Console instead.
- Every Operations API call requires a `BPMCSRFToken` header obtained from `POST .../ops/system/login`. The skill handles this automatically, but if `CWTBG0651E` is returned after a pause the token has expired and must be refreshed.
- Container and snapshot acronyms are **case-sensitive** — a mismatch returns `CWTBG0624E` (container not found) or `CWTBG0646E` (snapshot not found).
- Supported deployment types: BAW on-premises (root-mount or prefixed context root), BAW on Cloud, and CP4BA.

> **Note:** Credentials shown in prompt examples are for illustration only. Never use real production credentials in prompts. Use environment variables or a secrets manager for sensitive values.

## Prompt examples

### Inspect a specific snapshot — Process App

**Prompt:**
> Show me the details for snapshot v3.1 of the CLAIMSAPP process app on https://baw.claims.example.com/bas. Credentials: admin / Welcome1.

**What to expect:** A Snapshot Summary block showing container type, snapshot name, snapshot ID, active/inactive status, creation date, branch, default flag, lifecycle state, and a toolkit dependencies table (or a "no dependencies" note), followed by an offer to use `version-lifecycle-manager` for any follow-on actions.

---

### Inspect a specific snapshot — Toolkit

**Prompt:**
> Get the metadata for snapshot 2.0 of the SHAREDUTILS toolkit on https://baw.example.com/bas. admin / pass.

**What to expect:** A Snapshot Summary block identical in structure to a Process App inspection, with the container type clearly shown as "Toolkit", and toolkit dependency data retrieved from the WLE toolkit endpoint.

---

### Known container, unknown snapshot — snapshot picker

**Prompt:**
> I want to check the status of the ORDERSMGMT process app before activating the new version, but I don't remember the snapshot acronym. Server: https://baw.ops.example.com/bas, admin / opspass.

**What to expect:** A table of all snapshots for ORDERSMGMT (acronym, name, status, created date) is presented and you are asked which one to inspect in detail.

---

### Unknown container — browse everything on the server

**Prompt:**
> I don't know what process apps and toolkits are deployed on https://baw.corp.example.com/bas. Can you list them all? admin / corp123.

**What to expect:** Two labelled tables — Process Apps first, Toolkits second — each listing name, acronym, and creation date, followed by a prompt asking which container you'd like to drill into.

---

### Find which snapshot is currently active

**Prompt:**
> Which snapshot of INVOICING is currently active on https://baw.finance.example.com/bas? Credentials: svc_baw / Finpass1.

**What to expect:** The snapshots for INVOICING are listed with their active/inactive status highlighted, so you can immediately see which version is live.

---

### Inspect on a CP4BA cluster

**Prompt:**
> Inspect snapshot v4.0 of LOANAPP on our CP4BA cluster at https://cpd.openshift.myorg.com/bas. Username: CEAdmin, password: Genius1.

**What to expect:** The skill exchanges credentials for a Bearer token via the CP4BA authorize endpoint, obtains the CSRF token, then retrieves and presents the Snapshot Summary block for LOANAPP v4.0.

---

### Diagnose an API error — container not found

**Prompt:**
> I tried to inspect snapshot v2.0 of hrapp on https://baw.hr.example.com/bas and got CWTBG0624E. What does that mean?

**What to expect:** A plain-language explanation that `CWTBG0624E` means the container acronym was not found (noting that acronyms are case-sensitive, so `hrapp` ≠ `HRAPP`), the full raw API response, and an offer to list all containers to find the correct acronym.

---

### Diagnose an API error — server may be BPM 8.x

**Prompt:**
> I'm getting a 404 when trying to inspect snapshots on https://baw-legacy.corp.example.com:9443. The server is pretty old.

**What to expect:** An explanation that the Operations REST API is not present on this server (likely IBM BPM 8.x, which predates BAW 18.0), and a recommendation to use the Process Admin Console to inspect snapshots manually instead.

---

### Out-of-scope — lifecycle action after inspection

**Prompt:**
> Now that I can see snapshot v3.1 of CLAIMSAPP is active, please deactivate it.

**What to expect:** The skill explains that lifecycle actions (deactivate, activate, delete, env var management) are handled by the `version-lifecycle-manager` skill, and offers to hand off to it immediately.
