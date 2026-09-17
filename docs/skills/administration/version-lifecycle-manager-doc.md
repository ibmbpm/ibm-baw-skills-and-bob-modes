# Version Lifecycle Manager — Documentation

> Manages IBM® Business Automation Workflow (BAW) Process App and Toolkit version lifecycle via the Operations REST API — installing apps, activating, deactivating, and deleting snapshots, and reading, setting, and syncing environment variables — no Process Admin Console needed.

## Purpose

This skill administers the full snapshot lifecycle of BAW Process Apps and Toolkits by calling the BAW Operations REST API directly. It is designed for BAW administrators who need to install, activate, deactivate, or delete snapshots, or manage environment variables on a running server — all without opening a browser. For every destructive or disruptive operation (deactivation, deletion, sync to live), the skill presents a plain-language summary of the effect and requires explicit confirmation before making any API call.

> **Companion skill:** Use the `version-inspector` skill to browse and inspect snapshot metadata (version names, statuses, dependencies) before taking lifecycle actions here. The two skills are designed to work together — inspect first, act with version-lifecycle-manager.

## Setup and configuration

- BAW server URL and credentials are required. The skill will ask for them if not supplied.
- On-premises: provide `https://<host>:9443` (default port) and a username/password for Basic authentication. LTPA token is also accepted for SSO environments.
- CP4BA (Cloud Pak for Business Automation): provide the CP4BA route (e.g. `https://<cpd-route>/bas`) and a Zen API key (generated from **Profile → API Key** in the CP4BA admin UI). If Basic auth returns 403, the skill will exchange credentials for a Bearer token automatically.
- BAW on Cloud: provide the tenant URL (`https://<tenant>.baw.ibmcloud.com`) and an IBM Cloud IAM Bearer token.
- No local software, packages, or MCP servers are required. The skill uses `execute_command` (curl) when available, or shows the exact command for you to run.

## Compatibility

- BAW 18.0.0.0 or later required. The Operations REST API (`/ops/std/bpm/...`) used for activate, deactivate, delete, and env-var operations is not available on IBM BPM 8.x (pre-2018). If your server is BPM 8.x, this skill cannot help — use the Process Admin Console manually.
- Supported deployment types: BAW on-premises (root-mount or prefixed context root), BAW on Cloud, and CP4BA.
- Snapshot acronyms are **case-sensitive** on the API. An acronym mismatch returns `CWTBG0624E` or `CWTBG0646E`.

> **Note:** Credentials shown in prompt examples are for illustration only. Never use real production credentials in prompts. Use environment variables or a secrets manager for sensitive values.

## Prompt examples

### Activate a snapshot

**Prompt:**
> Activate snapshot v2.5 for the CLAIMSAPP process app. Server is https://baw.example.com/bas, username: admin, password: Welcome1.

**What to expect:** An operation summary is presented (container, snapshot, effect), you are asked to confirm, then the skill executes the activation call, shows the curl command, reports the HTTP status and API response, and notes that the previously active snapshot is automatically deactivated.

---

### Deactivate a snapshot

**Prompt:**
> Deactivate snapshot 1.8.0 on the INVOICING process app at https://baw.finance.example.com/bas. Credentials: svc_baw / Passw0rd!

**What to expect:** A ⚠️ warning explains that running instances continue to completion but no new instances will start on this version; you are asked to confirm before the API call is made.

---

### Delete a snapshot (destructive)

**Prompt:**
> Delete snapshot ARCHIVE_2021 from the LOANAPP process app on our CP4BA cluster at https://cpd.openshift.myorg.com/bas. My Zen API key is zen-abcd-1234.

**What to expect:** A 🚨 warning that deletion is permanent and may affect instance history, a recommendation to export a `.twx` archive first, and a note that the snapshot must be deactivated before it can be deleted — all before asking for explicit confirmation.

---

### Install a process app from a .twx file

**Prompt:**
> Install /releases/SUPPLYAPP_v4.1.twx to https://baw.prod.example.com/bas (admin / prodpass), then verify it landed.

**What to expect:** The skill constructs a multipart POST to the install endpoint, follows up automatically with a verify call, presents the snapshot's status fields in a readable format, and suggests activating the snapshot as the next step.

---

### Verify a snapshot

**Prompt:**
> Verify that snapshot v3.0 of HRAPP is present and in good shape on https://baw.hr.example.com/bas (hr_admin / hrpass99).

**What to expect:** The skill calls the verify endpoint and presents the snapshot's lifecycle state, active flag, and instance count in a structured result block.

---

### List all snapshots for a container

**Prompt:**
> List all deployed snapshots for the ORDERSMGMT process app on https://baw.ops.example.com/bas (admin / pass). I need to see which one is active.

**What to expect:** A table of all snapshots with columns for acronym, name, active status, and creation date, with the currently active snapshot highlighted.

---

### Unknown acronym — discover before acting

**Prompt:**
> I want to delete an old snapshot of PAYROLLAPP on https://baw.hr.example.com/bas (admin / pass123), but I'm not sure of its exact acronym.

**What to expect:** The skill lists all snapshots for PAYROLLAPP first so you can confirm the exact acronym (case-sensitive), then constructs the delete call only after you confirm which snapshot to target.

---

### Read environment variables

**Prompt:**
> Show me the current environment variables for snapshot v5.0 of CLAIMSAPP on https://baw.claims.example.com/bas (admin / claimspass).

**What to expect:** A GET to the env-vars endpoint is made and results are presented as a table of variable names and current values.

---

### Set and sync environment variables

**Prompt:**
> Set PAYMENT_GATEWAY_URL to https://payments.newprovider.com/api and TIMEOUT_SECONDS to 30 on snapshot v5.0 of CLAIMSAPP at https://baw.claims.example.com/bas (admin / claimspass), then sync them.

**What to expect:** Current variables are shown first as a baseline, the new values are written via the set endpoint, then a ⚠️ warning explains that syncing pushes changes immediately to the live snapshot and confirmation is required before the sync call is made.

---

### Diagnose an API error

**Prompt:**
> I tried to activate snapshot PROD_Q4 on FINANCEAPP and got HTTP 400 with error code CWTBG0646E. What does this mean?

**What to expect:** A plain-language explanation that `CWTBG0646E` means the snapshot acronym was not found (note: acronyms are case-sensitive), along with curl commands to list containers and snapshots so you can confirm the exact acronym before retrying.

---

### Out-of-scope — exporting or backing up a snapshot

**Prompt:**
> Can you export snapshot v2.0 of HRAPP as a .twx file so I have a backup before I delete it?

**What to expect:** The skill explains that exporting `.twx` files is done through the Process Center or Workflow Center UI, not via the Operations REST API, and redirects you there before proceeding with any deletion.

---

### Out-of-scope — migrating running instances

**Prompt:**
> Migrate all running process instances on LOANAPP v1.5 to the new snapshot v2.0.

**What to expect:** The skill explains that instance migration is a separate administration task handled through the BAW Process Admin Console migration tooling, not via the snapshot lifecycle API, and directs you there instead.
