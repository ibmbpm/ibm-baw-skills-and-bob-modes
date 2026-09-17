---
name: baw-endpoint-validation
description: "Use when a BAW administrator wants to validate a process application before installing it on a new server — asking what new server to target, reading the BPMConfig properties file to extract source and target endpoints (hostnames, database hosts, ports), scanning the TWX export for hardcoded references to the old server, and generating a report of findings with a summary of the intended endpoint changes. Can also run BPMConfig -export to capture a live environment. Trigger phrases: 'install process app on new server', 'check for hardcoded endpoints', 'validate TWX for new environment', 'endpoint validation', 'what needs to change to move to new server', 'BPMConfig export', 'scan TWX for old server references', 'run BPMConfig'. Do not use for runtime process inspection (use inspect-baw-processes) or BPMN authoring (use generate-baw-bpmn)."
permissions:
  - file_write    # write_file — used in Step 5 to write the endpoint validation report
  - execute_command    # execute_command — used in Steps B1–B5 (BPMConfig discovery/export) and Step 4c (scan script)
  - shell    # shell — used for cross-platform discovery commands (Get-ChildItem, find)
license: Apache-2.0
metadata:
  version: 1.0.0
---

# BAW endpoint validation

Identify what needs to change when a BAW process application is installed on a new server by:
1. Collecting environment info (properties files or running `BPMConfig -export` directly).
2. Reading BPMConfig properties files to extract source and target endpoints.
3. Scanning the TWX export for hardcoded references pointing to the old server.
4. Generating a report of findings with a summary of the intended endpoint changes.

The TWX scan is driven by `scripts/scan_twx_endpoints.py`.

## Key constraint

All environment information is derived from exported BPMConfig properties files, values the user provides directly, or commands run by Bob via `execute_command`. Paths come from the user or are discovered automatically (profiles directory). Do not invent paths that are not discoverable.

## Offline promotion context

`BPMConfig -export` requires the **deployment manager (or stand-alone server) to be running**. Export the properties file before taking any server offline.

The TWX scan (Steps 4–5) is entirely file-based and safe to run with the server stopped.

The actual offline promotion step uses the `BPMInstallOfflinePackage` wsadmin command, which installs a snapshot onto a Workflow Server not connected to Workflow Center. This skill validates the TWX *before* that step — it does not perform the promotion itself.

## Input requirements

Collect all three items before proceeding. Do not assume which environment (source or target) a properties block belongs to — always read the user's explicit labelling in their message.

| # | Input | How to obtain |
|---|---|---|
| 1 | **Source `.properties`** | The user may provide a file path, paste content inline, or ask you to run `BPMConfig -export`. Read the user's message carefully — if they label the pasted block "target", it is the target, not the source. Ask for the source separately if it is missing. |
| 2 | **Target `.properties`** | The user may provide a file path or paste content inline. Read the user's explicit label ("my target is…", "this is for the target server", etc.) to determine which block is the target. If the target is not yet provided, ask for it. |
| 3 | **TWX file** | Use the path the user states. If a `.twx` path is visible in the conversation, use it directly — no need to ask. |

**Ownership rule — do not assume ownership of a properties block.** If the user says "my target is `https://host:9443/` [properties block]", the block is the **target**. If the user says "my source install is at `C:\baw`", that install path is the **source** — not the pasted block. Misassigning source/target will produce an inverted endpoint map and incorrect findings.

Ask using `ask_followup_question` for any item not yet clearly provided with an explicit source/target label.

**Tool scope** — this skill uses exactly four tools: `read_file` (read properties and TWX files), `write_file` (write the endpoint validation report in Step 5), `execute_command` (run BPMConfig discovery/export in Steps B1–B5 and the scan script in Step 4c), and `ask_followup_question` (collect missing inputs). No other tools are used.

**Automatic execution** — `execute_command` is restricted to read-only discovery and export operations. Discovery commands (`Get-ChildItem`, `find`, `BPMConfig -export`) and the scan script run immediately without a confirmation prompt. Any command that modifies, deletes, or overwrites files on the BAW server requires a pause and explicit user approval before running. Pause on read-only operations only if a command fails.

## Steps

### Step 1 — Collect environment info

**Before reading any files, identify which environment each piece of input belongs to** by reading the user's explicit labels in their message. Common patterns:

- "my source install is in `C:\baw`" → `C:\baw` is the **source** install root
- "my target is `https://host:9443/` [properties block]" → the properties block is the **target**
- "this .properties is for the target server" → block is **target**
- A bare properties block with no label → **ask** which environment it belongs to before proceeding

Once ownership is established, determine how to obtain each:

**Source environment** — choose the first that applies:
- User provided a `.properties` **file path** → read it with `read_file`
- User provided an **install root path** (e.g. `C:\baw`) → run `BPMConfig -export` (Option B)
- User pasted properties **inline and labelled it as source** → parse the pasted content
- None of the above → ask: "Should I run `BPMConfig -export` against your source server, or do you have an exported `.properties` file?"

**Target environment** — choose the first that applies:
- User provided a `.properties` **file path** → read it with `read_file`
- User pasted properties **inline and labelled it as target** → parse the pasted content
- User provided only a **hostname/URL** → ask: "Do you have a BPMConfig `.properties` file for the target server, or should I use just the hostname you provided?"
- None of the above → ask for it

#### Option A — User provides existing `.properties` file
Read it directly with `read_file`. No further questions needed for the source.

#### Option B — Run `BPMConfig -export` directly

**Ask for the BAW install root if it is not already in the conversation:**

> "What is the BAW install root directory on the source server? (e.g. `/opt/IBM/BAW` on Linux or `C:\IBM\BAW` on Windows)"

Once provided, discover everything else automatically. **Do not assume a fixed directory layout** — BAW installations vary; search the tree before asking anything.

**Step B1 — Locate BPMConfig**

Check the standard location first: `<install_root>\bin\BPMConfig.bat` (Windows) or `<install_root>/bin/BPMConfig.sh` (Linux). If not found there, search the entire tree:

Windows:
```powershell
Get-ChildItem -Path "<install_root>" -Recurse -Filter "BPMConfig.bat" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
```
Linux:
```bash
find "<install_root>" -name "BPMConfig.sh" 2>/dev/null
```

If multiple matches are found, prefer the one whose path contains `\bin\` or `/bin/`. If none are found, the directory is not a BAW runtime — tell the user and ask for the correct install root or an exported `.properties` file.

**Step B2 — Locate the profiles directory**

Once `BPMConfig` is found, its parent `bin\` directory gives the real install root. Look for `profiles\` as a sibling of `bin\`. If that doesn't exist, search the tree:

Windows:
```powershell
Get-ChildItem -Path "<real_install_root>" -Recurse -Directory -Filter "profiles" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
```
Linux:
```bash
find "<real_install_root>" -maxdepth 4 -type d -name "profiles" 2>/dev/null
```

If still not found, search for `BPMConfig.bat`/`.sh` inside any `config\cells` directory as an alternative sign of a profile root — or look directly for directories containing a `config\cells` subdirectory.

**Step B3 — Discover the profile name**

List child directories inside the discovered `profiles\` directory. If exactly one exists, use it. If multiple exist, ask the user to choose.

**Step B4 — Discover the DE name**

Check `<profile>\config\cells\*\bpmconfig\` for `.properties` files. The DE name is the filename without extension. If exactly one file exists, use it. If multiple exist, ask.

As a fallback, search the entire profile root:
Windows:
```powershell
Get-ChildItem -Path "<profile_root>" -Recurse -Filter "*.properties" -ErrorAction SilentlyContinue | Where-Object { $_.DirectoryName -like "*bpmconfig*" } | Select-Object -ExpandProperty FullName
```
Linux:
```bash
find "<profile_root>" -path "*/bpmconfig/*.properties" 2>/dev/null
```

**Step B5 — Output directory and export**

Use the system temp directory:
```
python -c "import tempfile; print(tempfile.gettempdir())"
```

Then run the export. On Linux/AIX:
```bash
<real_install_root>/bin/BPMConfig.sh -export -profile <DmgrProfile> -de <DE_name> -outputDir <temp_dir>
```
On Windows:
```
<real_install_root>\bin\BPMConfig.bat -export -profile <DmgrProfile> -de <DE_name> -outputDir <temp_dir>
```
The `-de` option can be omitted when only one DE exists in the cell. The command produces `<DE_name>.properties` in `<temp_dir>`.

After the export completes, read the output file immediately.

### Step 2 — Parse source properties file

Use `read_file` to read the source `.properties` file at the path provided. Extract:

**Server / topology**
- `bpm.de.node.#.hostname` — managed node hostname(s)
- `bpm.dmgr.hostname` — deployment manager hostname (ND topology only)

**Databases** (for each `bpm.de.db.#.*` block)
- `bpm.de.db.#.hostname` — database server hostname
- `bpm.de.db.#.portNumber` — database port
- `bpm.de.db.#.databaseName` — database name
- `bpm.de.db.#.name` — logical DB label (e.g. `ProcessServerDb`)

**Install paths**
- `bpm.de.node.#.installPath` — BAW installation path on each node
- `bpm.de.caseManager.networkSharedDirectory` — Case Manager shared directory

Build a **Source Endpoints Map**: a deduplicated list of every distinct hostname, IP address, and file path found.

### Step 3 — Capture target environment

1. **Explicit `.properties` path already provided** — if the user already gave a target `.properties` file path, read it with `read_file` and extract the same fields as Step 2.
2. **No target `.properties` provided** — ask using `ask_followup_question`:
   > "Do you have a BPMConfig `.properties` file exported from the target server? If so, please provide the path. Otherwise I'll use the hostname/URL you've already stated."
3. **User confirms no file** — fall back to verbal values already in the conversation (hostname, port, protocol). Extract the hostname and port from any URL provided; infer HTTPS if port is 9443.

Build the **Target Endpoints Map** from whichever source is used.

### Step 4 — Run TWX endpoint scan

The script path is `<skill_dir>/scripts/scan_twx_endpoints.py` where `<skill_dir>` is the directory containing this SKILL.md.

Obtain the system temp directory once and reuse it for all temp files in Steps 4a–4d:
```
python -c "import tempfile; print(tempfile.gettempdir())"
```

The source map is deleted immediately after the scan regardless of success or failure.

**Step 4a — Write the source map**

Write the source map to `<temp_dir>/_baw_source_map.json`. Include every distinct hostname and path value from the Source Endpoints Map. Example:

```json
{
  "old-node-hostname": "node-hostname",
  "old-db-hostname": "db-hostname",
  "C:/baw/BUILT/deploy2/AppServer": "source-install-path"
}
```

Include `localhost` if the source environment genuinely uses it (e.g. a single-node install where all services run on the same host). Do **not** include values like `localhost` that map to themselves unless the source properties actually contain `localhost` — only include terms that are meaningful to search for.

**Step 4b — Derive the report output path**

```
<twx_dir>/<twxfilename> - reports/
```
where `<twx_dir>` is the directory containing the TWX and `<twxfilename>` is the full TWX filename including the `.twx` extension (e.g. `ClaimsApp.twx`). Create this directory:
```
python -c "import os; os.makedirs(r'<report_dir>', exist_ok=True)"
```

**Step 4c — Run the scan**

Use `--json` for structured output.

On Windows:
```
python "<skill_dir>\scripts\scan_twx_endpoints.py" --twx "<absolute_path_to_twx>" --source-map-file "<temp_dir>\_baw_source_map.json" --json
```

On Linux/AIX:
```bash
python "<skill_dir>/scripts/scan_twx_endpoints.py" \
  --twx "<absolute_path_to_twx>" \
  --source-map-file "<temp_dir>/_baw_source_map.json" --json
```

After the run (success or failure), delete the temp source map:
```
python -c "import os; os.remove(r'<temp_dir>/_baw_source_map.json')"
```

The `--json` flag causes the script to print a single JSON object to stdout. Parse this object — it has the shape `{"findings": [...], "files_scanned": N, "binary_files_skipped": N, "source_terms_searched": [...]}`. Each finding has `file`, `line`, `matched_pattern`, `severity`, and `context_snippet` fields. Capture this JSON and use it in Step 4d.

If the script errors, diagnose first: verify the TWX path, check `python --version` (3.6+ required), confirm the TWX is not password-protected.

**Step 4d — Resolve artifact names from the TWX**

For every unique `objects/*.xml` path in the findings, extract the artifact's human-readable name and type from inside the TWX. Write the following to `<temp_dir>/_baw_resolve_names.py` and run it:

```python
import zipfile, re, json, sys

twx_path = sys.argv[1]
files_arg = sys.argv[2]  # comma-separated list of TWX-internal paths to resolve

targets = [f.strip() for f in files_arg.split(',') if f.strip().startswith('objects/')]

results = {}
with zipfile.ZipFile(twx_path) as z:
    for entry in targets:
        try:
            content = z.read(entry).decode('utf-8', errors='replace')
            # Extract root element tag and name attribute from first ~800 chars
            head = content[:800]
            tag_match = re.search(r'<(\w+)\s', head)
            name_match = re.search(r'\bname="([^"]+)"', head)
            tag = tag_match.group(1) if tag_match else 'unknown'
            name = name_match.group(1) if name_match else entry
            results[entry] = {'tag': tag, 'name': name}
        except Exception as e:
            results[entry] = {'tag': 'unknown', 'name': entry, 'error': str(e)}

print(json.dumps(results))
```

Run it:
```
python "<temp_dir>/_baw_resolve_names.py" "<absolute_path_to_twx>" "<comma-separated unique objects/*.xml paths from findings>"
```

Delete the temp script after running:
```
python -c "import os; os.remove(r'<temp_dir>/_baw_resolve_names.py')"
```

The output is a JSON object mapping each TWX internal path to `{"tag": "<xml-element-name>", "name": "<artifact-name>"}`. Use the following tag-to-type mapping to produce a human-readable artifact type:

| XML tag | Artifact type in Workflow Center |
|---|---|
| `process` (processType=12) | Service Flow |
| `process` (processType=11) | Heritage Human Service |
| `process` (processType=10 or other) | Service Flow |
| `bpd` | Process (BPD) |
| `externalActivity` | REST operation (child of External Service) |
| `environmentVariableSet` | Environment Variables |
| `teamworks` wrapping `process` with no processType | Service |
| any other | BAW Artifact |

To distinguish Service Flow from Heritage Human Service, check for `<processType>12</processType>` in the XML content (processType 12 = Service Flow, 11 = Heritage Human Service). If processType is absent or ambiguous, label it "Service".

For `files/*` entries (not `objects/*.xml`), do not attempt name resolution — label them as **"Auto-generated binding file"** and note they are regenerated when the parent artifact is saved.

### Step 5 — Generate report

Write the report using `write_file` to `<report_dir>/endpoint-validation-report.md`. Use this structure:

```markdown
# BAW Endpoint Validation Report

## Environment Transition Summary
| | Value |
|---|---|
| Process App TWX | <filename> |
| Source properties | <path> |
| Target properties | <path or "stated verbally"> |
| Scan Date | <today's date> |
| Files scanned | <N> |
| Binary files skipped | <N> |

## Source → Target Endpoint Mapping
| Property | Source Value | Target Value | Status |
|---|---|---|---|
| bpm.de.node.1.hostname | old-host | new-host | ✅ Changed |
...

## TWX Hardcoded Reference Findings

### 🔴 Critical (<count>)

| # | Artifact Name | Type | Step / Variable | Line | Context | Where to fix |
|---|---|---|---|---|---|---|
| 1 | External service | External Service | External service operation1 | 99 | `urlTemplate="http://localhost:9080/MyAPI/rest/v1"` | Workflow Designer → Process App Settings → Servers → MyAPI |
...

### 🟡 Warning (<count>)

| # | Artifact Name | Type | Step / Variable | Line | Context | Notes |
|---|---|---|---|---|---|---|
...

### ℹ️ Info (<count>)
<count> additional lower-priority matches. No direct action required.

## Recommended Actions

### Blockers (must resolve before install)

1. **<short title>** — <what to do and where, using plain navigation text only>
   - <sub-step if needed>

### Warnings (review before go-live)

1. **<short title>** — <what to check>

## Version Compatibility Note
*(include only if source and target fix pack versions differ)*

| | Source | Target |
|---|---|---|
| Fix pack | `<version>` | `<version>` |
| Product type | <type> | <type> |
| Environment | <env> | <env> |

> **Blocker/Warning:** <one-sentence plain-text explanation>

## Overall Readiness
✅ Ready to promote / ⚠️ Review required / 🔴 Blockers must be resolved
```

**Report writing rules:**

- **Artifact Name** column: use the `name` value from Step 4d. For `files/*` entries use "Auto-generated binding file".
- **Type** column: use the mapped type from the tag-to-type table in Step 4d.
- **Step / Variable** column: for `<script>` findings, extract the nearest `name="…"` attribute in the 25 lines before the match (this is the step name). For `environmentVariableSet`, use the `envVar name` attribute. For `externalActivity`, use the operation name. Leave blank if not determinable.
- **Where to fix** column: use the table in Step 6 to select the right navigation path; include the artifact name so the developer knows exactly what to open. For inline scripts, add "⚠️ Cannot fix via Process Admin Console — requires code change in Workflow Designer."
- **Group duplicate entries**: if the same artifact + line context appears twice (e.g. line 84 and 216 in the same file, both containing the same script), merge them into a single row with a note like "(2 occurrences — fixing in Designer updates both)".
- Do not expose internal UUID paths in the report body. They may appear in a collapsed `<details>` footnote at most.
- **Hyperlinks must resolve.** Only include a hyperlink in the report if the URL is taken directly from the verified References section at the bottom of this SKILL.md. Do not construct version-specific IBM Docs URLs that are not in the References section — they cannot be verified without a search. Navigation paths (e.g. `Workflow Designer → Process App Settings → Servers`) are always written as plain text; a link is optional and only added when a verified URL is available.

### Step 6 — Present summary and fix guidance

After writing the report, give the user a plain-language summary inline covering:
- How many critical references were found and in which files
- What the endpoint changes are (old → new, per property)
- Whether the process app is ready to install on the new server

For each Critical finding, tell the user exactly where to fix it in BAW 26.0.x:

| Finding type | Where to fix (BAW 26.0.x) |
|---|---|
| REST server URL hardcoded in `<urlTemplate>` or `urlTemplate` attribute | In **Workflow Designer**, open the process app, click the **Process App Settings** dropdown in the toolbar → **Servers** tab → find the REST server entry → update **Host name** and **Port** for the relevant environment (Development / Test / Staging / Production). |
| REST server host/port needs updating post-deployment (without re-importing TWX) | In the **Process Admin Console** → **Installed Apps** → click the overflow menu of the snapshot → **App Details** → **Servers** tab → update **Hostname**, **Port**, and **Secure Server** on each REST server binding. (See [Changing server settings in Process Admin Console](https://www.ibm.com/docs/en/baw/26.0.x?topic=properties-changing-server-settings-in-process-admin-console).) |
| Hardcoded URL in a service flow script (`<script>` tag) | In **Workflow Designer**, navigate to the service flow (Heritage Human Service or Service Flow) containing the script step → open the **Script** tab of the script task → update the hardcoded URL in the JavaScript. Consider replacing with a server variable bound via Process App Settings instead. |
| Hardcoded URL in a client-side human service (coach view script) | In **Workflow Designer**, open the Coach or client-side human service → find the view with the inline script → update the URL in the **Script** tab of the view. |
| Hostname in a variable default value (`<defaultValue>`) | In **Workflow Designer**, open the service or process → go to the **Variables** tab → find the variable → update the default value in the **Default** field. |
| Hardcoded portal link in notification / task activity documentation | In **Workflow Designer**, open the process → click the notification or task activity → edit the **Documentation** or **Notification** text field to replace the hardcoded `localhost` link with the correct target portal URL. |
| JDBC URL in a service SQL call | In the **WebSphere Integrated Solutions Console (ISC)** on the target server → **Resources → JDBC → Data Sources** → update the data source URL. This is a server-side change, not made in Designer. |

Do not offer to generate XML patches, apply configuration, or edit files inside the TWX — that is out of scope.

## Disambiguation rules

**No live BAW API calls**
Use only file inspection, `execute_command` for BPMConfig or Python scripts, and user-provided information. Do not make REST calls to the BAW runtime.

**No TWX path provided**
If the user does not have a TWX, explain: in Workflow Center, open the process app → find the snapshot → click **Export** → select **.twx** → save the file. The `.twx` option is for Workflow Center import/export; use `.zip` only for installing directly to a runtime environment. (See [Importing and exporting projects and toolkits](https://www.ibm.com/docs/en/baw/26.0.x?topic=snapshots-importing-exporting-projects-toolkits).)

**Multiple deployment environments**
If the source properties file contains multiple `bpm.de.*` blocks, extract endpoints from all blocks and report them separately by DE number.

**`localhost` in source properties**
`localhost` in a single-node (Express/stand-alone) source environment is valid — include it in the source map so references to `http://localhost:9080/...` are caught in the TWX scan.

**`localhost` findings in the TWX — BAW-internal vs external**
Not all `localhost` findings are blockers. Apply this classification when reporting:

| URL pattern | Classification | Rationale |
|---|---|---|
| `http://localhost:.../portal/...` | ⚠️ Warning | BAW portal — resolves to the local server. Valid for stand-alone. Only a concern if HTTPS is required. |
| `http://localhost:.../teamworks/...` | ⚠️ Warning | BAW internal endpoint — same reasoning. |
| `http://localhost:.../rest/bpm/...` | ⚠️ Warning | BAW REST API — resolves locally. |
| `<defaultValue>` or variable binding with `"host":"localhost"` | ⚠️ Warning | Likely a BAW server variable, not an external service. |
| `http://localhost:.../<custom-app>/...` | 🔴 Critical — conditional | External REST API (e.g. `MyAPI`, `OrderAPI`). Whether `localhost` is valid depends on whether the API is co-located on the target BAW server. Flag as conditional blocker and ask the user to confirm deployment topology. |
| `urlTemplate` or `<url>` pointing to `localhost` with a non-BAW context root | 🔴 Critical — conditional | Same as above. |

When in doubt, flag as conditional and explain the two scenarios clearly rather than asserting it is definitely broken.

## Known limitations

**Encrypted property values** — BPMConfig exports mask passwords with `{xor}` encoding. The scan does not attempt to decrypt these; they are excluded from the endpoint map.

**Binary or compiled artifacts inside TWX** — some TWX files contain compiled JavaScript or minified CSS where pattern matching may miss encoded references. The scan reports binary files skipped; flag this in the report if relevant.

**Script requires Python 3.6+** — `scripts/scan_twx_endpoints.py` uses only stdlib (`zipfile`, `xml.etree.ElementTree`, `re`, `json`, `argparse`). No pip install required.

## References

- [BPMConfig command-line utility](https://www.ibm.com/docs/en/baw/26.0.x?topic=utilities-bpmconfig-command-line-utility) — IBM Docs
- [Configuration properties for the BPMConfig command](https://www.ibm.com/docs/en/baw/26.0.x?topic=utility-configuration-properties-bpmconfig-command) — IBM Docs
- [Specifying a REST server in Process App Settings](https://www.ibm.com/docs/en/baw/26.0.x?topic=service-specifying-rest-server) — IBM Docs
- [Changing server settings in Process Admin Console](https://www.ibm.com/docs/en/baw/26.0.x?topic=properties-changing-server-settings-in-process-admin-console) — IBM Docs
- [BPMInstallOfflinePackage command](https://www.ibm.com/docs/en/baw/26.0.x?topic=scripting-bpminstallofflinepackage) — IBM Docs
- [Importing and exporting projects and toolkits](https://www.ibm.com/docs/en/baw/26.0.x?topic=snapshots-importing-exporting-projects-toolkits) — IBM Docs
- `references/BPMCONFIG_REFERENCE.md` — full properties key reference
