---
name: baw-export-import-helper
description: Migrate IBM BAW or CP4BA Process Apps, toolkits, case solutions, and Business Applications from one environment to another, automatically resolving toolkit dependencies and determining the correct import order. Use when someone says "migrate my process app", "move my workflow to another environment", "export and import BAW projects", "copy my toolkit to production", "migrate between BAW servers", or "transfer my process application". Also use proactively when a user describes environment promotion (dev to test to prod), environment consolidation, disaster recovery restores, or any scenario where BAW artifacts need to move between servers.
allowed-tools:
  - execute
  - write
  - read
  - fetch
license: Apache-2.0
metadata:
  version: "1.0.0"
---


> **⚠️ REST only. MCP is not supported by this skill.** All BAW interactions use the BAW REST API exclusively via HTTP calls. Do not call any MCP tools at any point, regardless of whether an MCP server is connected or not. This skill has no MCP dependency. If you find yourself reaching for an MCP tool, stop and use the REST equivalent from `references/baw-rest.md` instead.

# BAW export and import helper

Migrate IBM BAW or CP4BA Process Apps, toolkits, case solutions, and Business Applications between environments. The skill handles authentication, dependency discovery, correct import ordering, and produces a migration report using public BAW REST APIs.

## Execution mode

This skill operates in **REST mode only**. All calls use the BAW REST API documented in `references/baw-rest.md`.

Before taking any action, confirm `{SOURCE_URL}` and `{TARGET_URL}` are known for this session. If not, see Step 0a.

---

## Semantic operations

| Operation | What it does |
|---|---|
| `login` | Authenticate to a BAW server and obtain a CSRF token and session |
| `list containers` | List all Process Apps and toolkits visible on a server |
| `get container` | Retrieve details for a specific Process App or toolkit by acronym |
| `list branches` | List all branches (tracks) for a given Process App or toolkit |
| `list snapshots` | List all snapshots for a given container, optionally filtered by branch |
| `export snapshot` | Download a snapshot as a `.twx` binary file |
| `inspect twx` | Unzip a local Teamworks Exchange (TWX) file and read its package manifest. Extracts dependency info and BAW version (`buildVersion`, `fixPack`) |
| `check exists on target` | Determine whether a given container and snapshot already exists on the target server |
| `import twx` | Upload a `.twx` file to the target server (returns HTTP 202, asynchronous) |
| `poll import job` | Poll `GET /ops/system/queue/{id}` every 5 s until the job reaches `success` or `failure` |

All REST details for each operation are in `references/baw-rest.md`. The step logic below uses operation names only. Never duplicate endpoint details inline.

---

## Step 0a — establish connections

If the user's opening message already contains source URL, source credentials, target URL, and target credentials, skip the question and go straight to login.

Otherwise ask for everything in a single turn:

> *"To get started I need:*
> *1. Source BAW server URL (e.g. `https://source.example.com:9443`)*
> *2. Source username and password*
> *3. Target BAW server URL (e.g. `https://target.example.com:9443`)*
> *4. Target username and password*
>
> *Both source and target are required. Do not paste real production credentials into chat. Use test or placeholder values here and supply production credentials through environment variables or a secrets manager.*
>
> *Credentials are used only to obtain a session token for this conversation."*

All 6 values (source URL, source user, source password, target URL, target user, target password) are mandatory. Do not proceed until all 6 are provided.

Once all 6 are known:
- Call `login` on the **source** server. Store the CSRF token as `{SOURCE_CSRF}`.
- Call `login` on the **target** server. Store the CSRF token as `{TARGET_CSRF}`.
- Never repeat, echo, log, or include raw credentials in any output, report, or tool call after the session token is obtained.

If either login fails (HTTP 401 or 400), tell the user which server rejected the credentials and ask them to re-enter before continuing. Do not proceed until both logins succeed.

**Self-signed certificates:** On-premises BAW and CP4BA environments commonly use self-signed TLS certificates. When a connection fails due to a certificate error, append `-k` to `curl` calls to bypass validation and warn the user explicitly:

> *"Certificate validation is disabled for this session because the server uses a self-signed certificate. Do not disable certificate validation in production environments unless your security policy explicitly permits it."*

---

## Step 0b — validate version compatibility

Check server versions before exporting any TWX files. Read the BAW version from the login response headers or from the `fixPack` field in `META-INF/package.xml` of the first exported TWX, whichever is available first.

- Store the source server version as `{SOURCE_VERSION}`.
- Store the target server version as `{TARGET_VERSION}`.
- If `{TARGET_VERSION}` < `{SOURCE_VERSION}`, warn the user before continuing:
  > *"Warning: source is BAW {SOURCE_VERSION} and target is BAW {TARGET_VERSION}. IBM BAW does not support importing snapshots into an older version. Do you want to continue anyway?"*
- Same version or target newer: proceed silently.
- User confirms despite mismatch: proceed and note it in the report.

---

## Step 1 — identify what to migrate

If the user already named what to migrate in their opening message, skip the question and use that.

Otherwise ask:

> *"What would you like to migrate?*
> *- A specific project by name (e.g. 'Customer Onboarding')*
> *- Multiple projects by acronym (e.g. 'COP,IRP,OMS')*
> *- All projects ('all')"*

- **1 project by name or acronym:** verify it exists via `get container` before continuing. If not found, show the full container list and ask the user to clarify.
- **Multiple projects by acronym:** verify each one exists via `get container`. Tell the user which acronyms were not found and ask them to clarify before continuing.
- **All:** call `list containers` on the source. Filter out system-managed containers (hidden, system-flagged, or internal platform containers identifiable by `isSystem=true` or `isHidden=true` in the container metadata). Present the list to the user for confirmation before continuing.

---

## Step 2 — discover snapshots and branches

For each Process App or toolkit the user wants to migrate:

1. Call `get container` to confirm it exists on source and retrieve its metadata.
2. Call `list branches` and check how many branches exist.
   - If there is only **1** branch (the default): proceed without asking and collect that branch's snapshots.
   - If there are multiple branches: ask the user:
     > *"I found {N} branches for {app name}. Should I migrate all branches, or only the default branch ({default branch name})?"*
   - Default answer if the user does not specify: **all branches** (matching the tool's default behaviour).
3. For each branch in scope: call `list snapshots` to enumerate all snapshots.
4. Present a summary (container name, branches in scope, snapshot count per branch) and ask the user to confirm before exporting anything.

---

## Step 3 — build the full migration set

> **Why toolkit snapshots need separate handling:** When BAW exports a Process App, it bundles only the specific toolkit snapshot version that app depends on (verified by manual test). Older snapshots of that toolkit are not bundled. For a complete environment migration, export and import all historical snapshots of every toolkit dependency separately so the target has the full snapshot history, not just the versions each app happens to need.

> **System toolkits** (`isSystem="true"` in the manifest) are platform-managed and must not be migrated. Skip them entirely.

> **TWX manifest structure:** The manifest path `META-INF/package.xml` is based on heuristics validated against real exports. IBM does not publish a formal XML schema for TWX internals. Confirm findings against the actual artifacts before acting on them if unexpected results occur.

For each Process App snapshot to be migrated:

1. Call `export snapshot` to download the `.twx` file to a local temporary directory.
2. Call `inspect twx` on the downloaded file:
   - Unzip the file using available shell tools (`execute_command` with `unzip` or `python3 -c "import zipfile..."`)
   - Locate and read the package manifest (`META-INF/package.xml`) inside the archive
   - From the manifest, extract all toolkit dependencies. Each entry has a toolkit name, short name (acronym), and the specific snapshot version the app depends on
   - For each dependency where `isSystem="false"`, this is a custom toolkit that must be migrated separately
   - Recursively inspect each bundled toolkit ZIP's own manifest to discover transitive dependencies
3. For each custom toolkit dependency discovered:
   - Call `list snapshots` on the source to get **all snapshot versions across all branches**, not just the one bundled in the app
   - Call `export snapshot` for each snapshot version individually
4. Build the complete migration set: all Process App TWX files plus all custom toolkit TWX files across all their snapshots and branches

Read the manifest contents at runtime and reason about what you find. The structure is self-describing.

**Import ordering:** Within each container, import snapshots oldest-first (by creation date) so branch history is preserved correctly on the target.

**Temporary files:** TWX files may contain sensitive business process data. After a successful migration, delete all temporary TWX files automatically and confirm deletion to the user. If the migration fails before completion, tell the user which temporary files remain and prompt them to delete the files manually.

---

## Step 4 — check what already exists on target

Before importing anything, check the target server for existing content to avoid unnecessary work and duplicate imports:

For each (container, snapshot) pair in the dependency-ordered list:
- Call `check exists on target` by calling `list containers` on the target and checking whether the container and snapshot acronym are already present.
- Mark each pair as `to import`, `already exists (skip)`, or `already exists (different version)`.

Present a summary to the user:
> *"Here is what I found on the target server: X snapshots are already present and will be skipped, Y snapshots need to be imported. Proceed?"*

Wait for confirmation before importing.

---

## Step 5 — import

For each (container, snapshot) pair marked `to import`, oldest snapshot first within each container:

1. Call `import twx` to upload the `.twx` file to the target server.
2. The import endpoint returns **HTTP 202** (asynchronous). Extract the queue job URL from the `url` field of the JSON response body.
3. Poll `GET /ops/system/queue/{id}` on the target server (using `{TARGET_CSRF}` and `{TARGET_SESSION}`) every 10 seconds until the job reaches a terminal state:
   - `state: "success"`: import completed successfully. Proceed to the next snapshot.
   - `state: "failure"`: import failed. Capture the `result` field for the error message.
   - Any other state (`pending`, `running`): continue polling. After 10 minutes without a terminal state, treat the job as timed out and stop.
4. Record the outcome: success, already exists (treat as success), or failure with error message.
5. If an import fails or times out, **stop immediately**. Tell the user which snapshot failed and what the error was, then ask how to proceed.

---

## Step 6 — migration report

After all imports complete (or after a failure stops the run), print the full migration report to chat. Then ask the user:

> *"Would you like me to save this report to disk?"*

If yes, write the file using `write_file` (or `execute_command` with a shell redirect if `write_file` is unavailable).

**File name:** `baw-migration-{TARGET_HOST}-{YYYYMMDD-HHmm}.md`
Derive `TARGET_HOST` from the hostname portion of `{TARGET_URL}`. Derive the timestamp from the current date/time at the moment of writing.

Tell the user the exact path once the file is written.

**Never include raw credentials, session tokens, or CSRF tokens in the report.**

**Report format:**

```markdown
## Migration report

**Source:** {SOURCE_URL} (BAW {SOURCE_VERSION})

**Target:** {TARGET_URL} (BAW {TARGET_VERSION})

**Date:** {current date/time}

**Version compatibility:** {Compatible / Warning: source newer than target}

### Summary
- Total snapshots in scope: N
- Successfully imported: N
- Skipped (already on target): N
- Failed: N

### Import order used
List the import sequence (container name, snapshot name, branch) in the order they were imported (toolkits first, oldest snapshot first within each container).

### Results
For each snapshot: status (✅ imported / ⏭ skipped / ❌ failed), container name, snapshot name, branch, and any error message on failure.

### Not migrated
If any snapshots were identified but not imported (for example, user cancelled, or failure stopped the run early), list them here.
```

---

## Error handling

**Login fails:** Ask the user to re-enter credentials for the failing server. Do not proceed.

**Container not found on source:** Tell the user which name or acronym was not found. Ask them to confirm the correct one via `list containers`.

**Export fails (HTTP 4xx/5xx):** Report which snapshot failed and the HTTP status. Common causes: insufficient permissions (403), snapshot archived or deleted (404). Ask the user if they want to skip and continue or stop.

**TWX inspection fails (unzip error, manifest not readable):** Report the issue. Ask the user if they want to attempt the import anyway (without verified dependency order for that snapshot) or skip it.

**Import fails on target:** Stop the migration immediately. Report the failing snapshot and error. Explain that continuing risks broken imports for any snapshots that depend on the 1 that failed.

**Session expires mid-run (HTTP 403 on a request that previously worked):** Re-run `login` for the affected server automatically, then retry the failed request 1 time. If it fails again after re-login, treat it as a genuine error.

---

## Important constraints

- **Verify all acronyms against live API responses** before using them in export or import calls.
- **Skip system toolkits** (`isSystem="true"` in the manifest). Do not export or import them. They are platform-managed and already present on every BAW server.
- **Migrate all toolkit snapshots across all branches**, not just the version bundled in a Process App's TWX file. The bundled version covers runtime correctness; the separate export covers full history.
- **Never log, echo, or store raw credentials.** Do not include credentials, session tokens, or CSRF tokens in any output, report, tool call, or saved file.
