# BAW export and import helper — documentation

> Migrate IBM BAW or CP4BA Process Apps, toolkits, case solutions, and Business Applications from one environment to another — automatically resolving toolkit dependencies and determining the correct import order.

## Purpose

This skill guides Bob through a complete, end-to-end migration of BAW or CP4BA projects between 2 servers. It handles authentication, discovers all snapshots and branches, resolves and exports custom toolkit dependencies in the correct order, skips system-managed toolkits, checks what already exists on the target to avoid duplicate imports, monitors each asynchronous import job to completion, and produces a formatted migration report. It is intended for BAW administrators and developers performing environment promotions (dev → test → prod), environment consolidation, or disaster recovery restores.

## Setup and configuration

- **Network access:** The machine running Bob must have HTTP/HTTPS access to both the source and target BAW servers simultaneously.
- **Credentials:** A username and password with sufficient permissions to export snapshots on the source and import them on the target. Use admin-level credentials.
- **No MCP server required:** This skill uses the BAW REST API exclusively via direct HTTP calls. You do not need to connect a BAW MCP server.
- **Local disk space:** Bob writes exported Teamworks Exchange (TWX) files to a temporary local directory during the migration. Ensure sufficient disk space for the containers being migrated. Temporary files are deleted automatically after a successful migration run; if the run fails, Bob prompts you to clean them up manually.
- **Self-signed certificates:** On-premises BAW and CP4BA environments commonly use self-signed TLS certificates. When detected, the skill appends `-k` to `curl` calls and warns you that certificate validation is disabled for that session. Do not disable certificate validation in production environments unless your security policy explicitly permits it.

## Compatibility

- IBM BAW and IBM Cloud Pak for Business Automation (CP4BA) environments are both supported.
- **Target must be the same version or newer than source.** BAW does not support importing snapshots from a newer fix pack into an older one. The skill detects this automatically from the exported TWX manifest and warns you before proceeding. The warning is blocking — Bob does not continue until you explicitly confirm or cancel.
- **Business Applications** are migrated transparently through the same flow as Process Apps. The public BAW REST API does not distinguish them by type — the app type (`workflow` vs `app`) is only visible after TWX manifest inspection, which the skill performs automatically.
- **Case solutions** appear in the same container list as Process Apps and are exported and imported using the same API flow.
- **System toolkits** (for example, System Data, UI Toolkit, Coaches) are automatically detected and skipped — they are platform-managed and already present on every BAW server.

## Prompt examples

> **Note:** Credentials shown in prompt examples are for illustration only. Never use real production credentials in prompts. Use environment variables or a secrets manager for sensitive values.

### Migrate a specific Process App by name

**Prompt:**
> I need to migrate my Process App called 'Customer Onboarding' from our dev BAW server to our test server. Dev is at https://baw-dev.example.com:9443 and test is at https://baw-test.example.com:9443.

**What to expect:** Bob asks for source and target credentials in a single turn, then proceeds to authenticate, discover snapshots and dependencies, and walk through the full migration flow.

---

### Migrate with all credentials provided upfront

**Prompt:**
> Migrate Process App HSS from https://baw-dev.example.com:9443 (<username>/<password>) to https://baw-test.example.com:9443 (<username>/<password>).

**What to expect:** Bob skips the credential prompt, logs into both servers immediately, checks version compatibility, discovers all branches and snapshots, resolves toolkit dependencies, checks what already exists on the target, imports oldest-snapshot-first, polls each async job to completion, and prints the full migration report.

---

### Migrate multiple projects by acronym

**Prompt:**
> Migrate Process Apps COP, IRP, and OMS from https://source.example.com:9443 (<username>/<password>) to https://target.example.com:9443 (<username>/<password>).

**What to expect:** Bob authenticates to both servers, verifies each acronym exists on the source, and proceeds with all 3 — or tells you which acronym was not found and asks you to clarify before continuing.

---

### Migrate all projects

**Prompt:**
> Migrate all my Process Apps. Source: https://baw-dev.example.com:9443, target: https://baw-test.example.com:9443. Both use <username>/<password>.

**What to expect:** Bob authenticates, lists all non-system containers on the source, presents them for your confirmation, and waits before exporting anything.

---

### Migrate only the default branch

**Prompt:**
> I want to migrate just the default branch of my Process App P1 from https://baw-dev.example.com:9443 (<username>/<password>) to https://baw-test.example.com:9443 (<username>/<password>).

**What to expect:** Bob migrates only snapshots from the default branch of P1 — since you specified this upfront, it does not ask the branch question again.

---

### Migrate a project that does not exist

**Prompt:**
> Migrate WRONGACRONYM from https://baw-dev.example.com:9443 (<username>/<password>) to https://baw-test.example.com:9443 (<username>/<password>).

**What to expect:** Bob authenticates, attempts to find the container, tells you it was not found, and offers to show the full list of available containers so you can identify the correct acronym.

---

### Save the migration report to disk

After the migration completes and the report is printed to chat, Bob asks:

> "Would you like me to save this report to disk?"

Reply **yes** and Bob writes a file named `baw-migration-{target-host}-{YYYYMMDD-HHmm}.md` to the current working directory and tells you the exact path.

---

## Migration report format

After every migration run (successful or failed), Bob prints a report to chat in this format:

```markdown
## Migration report

**Source:** https://source.example.com:9443 (BAW 26.0.0.0)

**Target:** https://target.example.com:9443 (BAW 26.0.0.0)

**Date:** 2026-09-20 23:00

**Version compatibility:** Compatible

### Summary
- Total snapshots in scope: 3
- Successfully imported: 3
- Skipped (already on target): 0
- Failed: 0

### Import order used
| # | Container | Snapshot | Branch | Notes |
|---|---|---|---|---|
| 1 | MyToolkit (TK) | v1 | Main | Custom toolkit dependency |
| 2 | CustomerOnboarding (CO) | v2 | Main | Process App |

### Results
| Status | Container | Snapshot | Branch | Notes |
|---|---|---|---|---|
| ✅ Imported | MyToolkit (TK) | v1 | Main | HTTP 202 → job 42 → success |
| ✅ Imported | CustomerOnboarding (CO) | v2 | Main | HTTP 202 → job 43 → success |

### Not migrated
None — all in-scope snapshots were successfully imported.
```

## How dependencies are resolved

When a Process App snapshot is exported, its TWX file contains a manifest (`META-INF/package.xml`) that lists all toolkit dependencies. The skill:

1. Reads this manifest to find all custom toolkit dependencies (skipping any marked `isSystem="true"`)
2. Recursively inspects each toolkit's own manifest to find transitive dependencies
3. Exports all snapshots across all branches of each custom toolkit — not just the version the app depends on — so the target has complete snapshot history
4. Imports toolkits before the apps that depend on them, oldest snapshot first within each container

## Error handling summary

| Error | What Bob does |
|---|---|
| Login fails (401/400) | Asks you to re-enter credentials for the failing server |
| Container not found | Names the missing acronym, offers to show the full container list |
| Version mismatch detected | Warns you that the target server is older than the source, and waits for explicit confirmation or cancellation before proceeding |
| Export fails (403/404) | Reports the snapshot and HTTP status, asks whether to skip or stop |
| TWX inspection fails | Reports the issue, asks whether to import anyway or skip |
| Import fails on target | Stops immediately, reports the error, and explains the dependency risk |
| Session expires mid-run | Re-authenticates automatically and retries once |
