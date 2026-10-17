---
name: baw-endpoint-validation
description: "Use when a BAW administrator wants to validate a process application before installing it on a new server — asking what new server to target, collecting source and target endpoints, scanning the TWX export for hardcoded references to the old server, and generating a report of findings. Supports both traditional BAW (reads BPMConfig .properties files or runs BPMConfig -export) and CP4BA containerized deployments on OpenShift (reads the ICP4ACluster custom resource via oc get). Trigger phrases: 'install process app on new server', 'check for hardcoded endpoints', 'validate TWX for new environment', 'endpoint validation', 'what needs to change to move to new server', 'BPMConfig export', 'scan TWX for old server references', 'run BPMConfig', 'validate TWX on CP4BA', 'CP4BA endpoint validation', 'oc get ICP4ACluster'. Do not use for runtime process inspection (use inspect-baw-processes) or BPMN authoring (use generate-baw-bpmn)."
license: Apache-2.0
compatibility: "IBM BAW 22.x and later; IBM CP4BA 22.x and later"
allowed-tools:
  - Read
  - Edit
  - Bash
metadata:
  version: "1.0.0"
  display_name: BAW Endpoint Validation
  short_description: Scan a BAW process app TWX export for hardcoded server endpoints and generate a migration report before moving to a new environment.
  author: IBM BAW Team
---
# BAW Endpoint Validation

Identify what needs to change when a BAW process application is installed on a new server. Supports both deployment types:

| Deployment type | How source endpoints are collected |
|---|---|
| **Traditional BAW** (on-premises / VM with WebSphere) | `BPMConfig -export` or a user-provided `.properties` file |
| **CP4BA containerized** (OpenShift / Kubernetes) | `oc get ICP4ACluster` YAML or a user-provided CR YAML snippet |

Steps for both paths:
1. Detect deployment type (traditional BAW or CP4BA containerized).
2. Collect source environment endpoints (Option A/B for traditional, Option C for CP4BA).
3. Collect target environment endpoints (same options).
4. Scan the TWX export for hardcoded references pointing to the old server.
5. Generate a report of findings with a summary of the intended endpoint changes.

The TWX scan is driven by `scripts/scan_twx_endpoints.py`.


## Credentials

Never prompt the user for credentials. Credentials are only needed when making a REST call.
When a REST call is about to be made, read `references/CREDENTIAL_HANDLING.md` and follow it — it will read credentials from `.env` automatically, and only prompt the user if a value is missing from that file. Do this once per session only.

---

## Key constraint

Bob derives all environment information from exported BPMConfig properties files, values the user provides directly, or commands run by Bob via `execute_command`. Paths come from the user or are discovered automatically (profiles directory). Do not invent paths that are not discoverable.

## Offline promotion context

`BPMConfig -export` requires the **deployment manager (or stand-alone server) to be running**. Export the properties file before taking any server offline.

The TWX scan (Steps 4–5) is entirely file-based and safe to run with the server stopped.

The actual offline promotion step uses the `BPMInstallOfflinePackage` wsadmin command, which installs a snapshot onto a Workflow Server not connected to Workflow Center. This skill validates the TWX *before* that step — it does not perform the promotion itself.

## Deployment type detection

**Perform this check before any other step.** Determine whether the user is on a traditional BAW deployment or a CP4BA containerized deployment.

### Signals that indicate CP4BA containerized

- User mentions **CP4BA**, **Cloud Pak for Business Automation**, **OpenShift**, **OCP**, **Kubernetes**, **k8s**, or **pods**
- User mentions `icp4adeploy` or a `ICP4ACluster` custom resource
- User mentions `cpd-cli`, `oc` (OpenShift CLI), or `kubectl`
- User provides a hostname ending in a cluster domain (e.g. `.svc.cluster.local`, `.apps.<cluster>`)
- User mentions that `BPMConfig` is not found or unavailable
- A provided BAW install root path does not exist when tested via `execute_command` (the directory is absent — this is normal inside a CP4BA container where no traditional BAW filesystem is present)
- `oc version --client` or `kubectl version --client` succeeds when run via `execute_command` (indicates Bob is running inside or alongside an OpenShift/Kubernetes environment)

### Signals that indicate traditional BAW

- User provides a `.properties` file exported by `BPMConfig`
- User mentions WebSphere, Deployment Manager (dmgr), Network Deployment, or a profiles directory
- User describes an on-premises or VM-based installation
- User provides a BAW install root path **AND** confirms they are working directly on that server (e.g. SSH'd into the BAW host, not a cluster node)

> **Note:** Install root path alone is **not** sufficient to conclude traditional BAW. An admin managing a migration from traditional BAW to CP4BA will often state the old install root as the source, while their current machine has `oc` and no BAW filesystem. Always confirm the working environment before attempting `BPMConfig`.

### When the deployment type is ambiguous

Ask using `ask_followup_question`:

> "Is your BAW environment a traditional on-premises installation (running on VMs with WebSphere), or a CP4BA containerized deployment on OpenShift/Kubernetes?"

With options:
- "Traditional BAW on-premises / VM installation"
- "CP4BA containerized deployment on OpenShift or Kubernetes"

### If CP4BA containerized is confirmed

Do not invoke any BPMConfig steps. **Do not attempt to access any BAW install root path** — on CP4BA there is no BAW filesystem accessible outside of pods, and `oc exec` into pods is not required. All endpoint data comes from the `ICP4ACluster` custom resource and OpenShift routes. Proceed with **Option C** (see Step 1, Option C below).

### Mixed scenario — migrating from traditional BAW to CP4BA

When the user mentions **both** an old on-premises BAW install root (the source) **and** a CP4BA/OpenShift target, the deployment types are different per role:

| Role | Deployment type | How to collect endpoints |
|---|---|---|
| **Source** | Traditional BAW | `BPMConfig -export` on the old server, or user provides `.properties` file |
| **Target** | CP4BA containerized | `oc get ICP4ACluster` on the target cluster |

In this case: use Option B for source, Option C for target. Confirm this split with the user before proceeding.

## Input requirements

Collect all three items before proceeding. Do not assume which environment (source or target) a block belongs to — always read the user's explicit labelling in their message.

| # | Input | Traditional BAW | CP4BA containerized |
|---|---|---|---|
| 1 | **Source endpoints** | User-provided `.properties` file path, or run `BPMConfig -export` | User-provided CR YAML snippet, or run `oc get ICP4ACluster` |
| 2 | **Target endpoints** | User-provided `.properties` file path, or stated hostname/URL | User-provided CR YAML snippet, or stated hostname/URL |
| 3 | **TWX file** | Prefer to download via the export API (see Step 4 — Acquire TWX). If the user already has a `.twx` path on disk, use it directly — no export needed. |

**Ownership rule — do not assume ownership of a block.** If the user says "my target is `https://host:9443/` [block]", the block is the **target**. Misassigning source/target will produce an inverted endpoint map and incorrect findings.

Ask using `ask_followup_question` for any item not yet clearly provided with an explicit source/target label.

**Tool scope** — this skill uses exactly four tools: `read_file` (read properties, CR YAML, and TWX files), `write_file` (write the endpoint validation report in Step 5), `execute_command` (run BPMConfig/oc discovery in Steps B1–B5/C1 and the scan script in Step 4c), and `ask_followup_question` (collect missing inputs). No other tools are used.

**Automatic execution** — `execute_command` is restricted to read-only discovery and export operations. Discovery commands (`python`, `find`, `BPMConfig -export`, `oc get`) and the scan script run immediately without a confirmation prompt. Any command that modifies, deletes, or overwrites files on the server requires a pause and explicit user approval before running. Pause on read-only operations only if a command fails.

**`read_file` is for explicit file paths only — never for filesystem exploration.** Only use `read_file` on paths the user has explicitly provided (e.g. a `.properties` file path, a CR YAML file, a `.twx` path) or that this skill has written itself. Do not use `read_file` to probe whether a directory exists, search for binaries, or list directory contents — use `execute_command` for all discovery.

**If `execute_command` reports that a BAW install root does not exist** (e.g. "no such file or directory") — do not simply ask for a different path. First run the following probe to determine what environment Bob is actually on:

```bash
oc version --client 2>/dev/null || kubectl version --client 2>/dev/null || echo "no-k8s-cli"
```

- If `oc` or `kubectl` responds → this machine is part of a CP4BA/OpenShift environment. `BPMConfig` does not exist here. Discard the install root. Tell the user: *"The path `<install_root>` does not exist on this machine — this appears to be a CP4BA/OpenShift environment where `BPMConfig` is not available. I'll collect configuration from the `ICP4ACluster` custom resource instead."* Proceed to **Option C**.
- If the probe returns `no-k8s-cli` → this machine has neither BAW nor Kubernetes tooling. Tell the user: *"The path `<install_root>` is not accessible from this machine. Please either run the BPMConfig discovery commands on the BAW server and paste the output here, or provide an already-exported `.properties` file."*

## Steps

### Step 1 — Collect environment info

**Before reading any files, identify which environment each piece of input belongs to** by reading the user's explicit labels in their message. Common patterns:

- "my source install is in `C:\baw`" → `C:\baw` is the **source** install root
- "my target is `https://host:9443/` [properties block]" → the properties block is the **target**
- "this .properties is for the target server" → block is **target**
- A bare properties block with no label → **ask** which environment it belongs to before proceeding

Once ownership is established, determine how to obtain each:

**Traditional BAW — source environment** — choose the first that applies:
- User provided a `.properties` **file path** → read it with `read_file`
- User provided an **install root path** (e.g. `C:\baw`) → run `BPMConfig -export` (Option B)
- User pasted properties **inline and labelled it as source** → parse the pasted content
- None of the above → ask: "Should I run `BPMConfig -export` against your source server, or do you have an exported `.properties` file?"

**Traditional BAW — target environment** — choose the first that applies:
- User provided a `.properties` **file path** → read it with `read_file`
- User pasted properties **inline and labelled it as target** → parse the pasted content
- User provided only a **hostname/URL** → ask: "Do you have a BPMConfig `.properties` file for the target server, or should I use just the hostname you provided?"
- None of the above → ask for it

**CP4BA containerized — source environment** — choose the first that applies:
- User pasted a CR YAML snippet **labelled as source** → parse it (Option C)
- User provided a namespace and CR name → run `oc get ICP4ACluster` (Option C)
- None of the above → ask: "Should I run `oc get ICP4ACluster` against your source cluster, or do you have the CR YAML?"

**CP4BA containerized — target environment** — choose the first that applies:
- User pasted a CR YAML snippet **labelled as target** → parse it (Option C)
- User provided a target namespace/CR name → run `oc get ICP4ACluster` on the target cluster (Option C)
- User provided only a **hostname/URL** → use it directly as the target; no CR needed
- None of the above → ask for the target hostname or CR YAML

#### Option A — User provides existing `.properties` file (traditional BAW)
Read it directly with `read_file`. No further questions needed for the source.

#### Option B — Run `BPMConfig -export` directly

**Ask for the BAW install root if it is not already in the conversation:**

> "What is the BAW install root directory on the source server? (e.g. `/opt/IBM/BAW` on Linux or `C:\IBM\BAW` on Windows)"

Once provided, discover everything else automatically. **Do not assume a fixed directory layout** — BAW installations vary; search the tree before asking anything.

**Step B1 — Locate BPMConfig**

Check the standard location first: `<install_root>\bin\BPMConfig.bat` (Windows) or `<install_root>/bin/BPMConfig.sh` (Linux). If not found there, search the entire tree using Python:

```python
python -c "
import os, sys
root = sys.argv[1]
name = 'BPMConfig.bat' if os.name == 'nt' else 'BPMConfig.sh'
for dirpath, dirnames, filenames in os.walk(root):
    if name in filenames:
        print(os.path.join(dirpath, name))
" "<install_root>"
```

If multiple matches are found, prefer the one whose path contains `\bin\` or `/bin/`.

**If BPMConfig is not found anywhere in the tree** — do not silently fail. Display:

> ⚠️ **BPMConfig not found under `<install_root>`.**
> `BPMConfig` ships only with traditional BAW (WebSphere-based). It is not present on CP4BA containerized deployments.
>
> - If this is a **traditional BAW** installation, please confirm the correct install root — `BPMConfig.bat` / `BPMConfig.sh` should be under `<install_root>/bin/`.
> - If this is a **CP4BA containerized deployment** on OpenShift/Kubernetes, `BPMConfig` is unavailable by design. I'll collect configuration from the `ICP4ACluster` custom resource instead.

Ask using `ask_followup_question`:
- "This is traditional BAW — provide the correct install root"
- "This is a CP4BA containerized deployment — proceed with ICP4ACluster CR"

If the user confirms CP4BA, stop Option B entirely and proceed to **Option C**.

**Step B2 — Locate the profiles directory**

Once `BPMConfig` is found, its parent `bin\` directory gives the real install root. Look for `profiles\` as a sibling of `bin\`. If that doesn't exist, search the tree using Python (depth-limited to 4 levels):

```python
python -c "
import os, sys
root = sys.argv[1]
for dirpath, dirnames, dirfiles in os.walk(root):
    depth = dirpath[len(root):].count(os.sep)
    if depth >= 4:
        dirnames[:] = []
        continue
    if 'profiles' in dirnames:
        print(os.path.join(dirpath, 'profiles'))
" "<real_install_root>"
```

If still not found, search for `BPMConfig.bat`/`.sh` inside any `config\cells` directory as an alternative sign of a profile root — or look directly for directories containing a `config\cells` subdirectory.

**Step B3 — Discover the profile name**

List child directories inside the discovered `profiles\` directory. If exactly one exists, use it. If multiple exist, ask the user to choose.

**Step B4 — Discover the DE name**

Check `<profile>\config\cells\*\bpmconfig\` for `.properties` files. The DE name is the filename without extension. If exactly one file exists, use it. If multiple exist, ask.

As a fallback, search the entire profile root using Python:

```python
python -c "
import os, sys
root = sys.argv[1]
for dirpath, dirnames, filenames in os.walk(root):
    if 'bpmconfig' in dirpath:
        for f in filenames:
            if f.endswith('.properties'):
                print(os.path.join(dirpath, f))
" "<profile_root>"
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

#### Option C — Read the `ICP4ACluster` custom resource (CP4BA containerized)

**Step C0 — Check whether `oc` is available**

Before attempting any `oc` command, run a client-only version check (no cluster connection required):

```bash
oc version --client
```

- **If the command succeeds** — `oc` is present. Ask for the namespace and CR name if not already in the conversation (default CR name: `icp4adeploy`), then run:

  ```bash
  oc get ICP4ACluster icp4adeploy -n <namespace> -o yaml
  ```

  If the command fails with an authentication or connection error (not a "command not found" error), the user is not logged in. Tell them:

  > ⚠️ **`oc` is installed but you are not logged in to a cluster.**
  > Please run `oc login <cluster-api-url>` and try again, or paste the CR YAML directly.

- **If `oc version --client` fails** — `oc` is not installed on this machine. Do not attempt further `oc` commands. Tell the user:

  > ⚠️ **The OpenShift CLI (`oc`) is not available on this machine.**
  > Please run the following command on a machine with cluster access and paste the output here:
  >
  > ```bash
  > oc get ICP4ACluster icp4adeploy -n <your-namespace> -o yaml
  > ```
  >
  > Alternatively, if you have access to the OpenShift web console, navigate to **Administration → CustomResourceDefinitions → ICP4ACluster → Instances** and copy the YAML from there.

  Wait for the user to paste the YAML before continuing.

> **Note:** `kubectl` can substitute for `oc` for read-only CR access when the user is logged in via `kubeconfig`. If `oc` is absent but `kubectl` is present, run `kubectl get ICP4ACluster icp4adeploy -n <namespace> -o yaml` instead.

> **Security note:** Store `{BAW_CSRF}` and `{BAW_SESSION}` in memory for this conversation only. Do not write them to any file. Ensure all calls use HTTPS.

Parse the YAML output — the key fields to extract are:

**Workflow hostname (BAW external URL)**
- `spec.baw_configuration[*].hostname` — external hostname for each BAW instance

**Deployment hostname suffix (applies to all routes if `hostname` is not set per-component)**
- `spec.shared_configuration.sc_deployment_hostname_suffix` — wildcard suffix (e.g. `apps.mycluster.example.com`)
  - If set, the BAW route hostname is `<baw-instance-name>.<sc_deployment_hostname_suffix>`

**Databases**
- `spec.datasource_configuration.dc_baw_datasource[*].dc_database_type` — database type
- `spec.datasource_configuration.dc_baw_datasource[*].dc_oracle_server_name` or equivalent hostname field
- `spec.datasource_configuration.dc_baw_datasource[*].database_port`

**Namespace / cluster**
- `metadata.namespace` — the namespace this CR lives in (used to identify the cluster)

If the `hostname` field is absent, construct the BAW URL as `https://<cr-name>-baw-server.<sc_deployment_hostname_suffix>` or ask the user for the actual route:

```bash
oc get route -n <namespace> | grep baw
```

Build a **Source Endpoints Map** from whichever fields are present. Include every distinct hostname found.

### Step 2 — Parse source configuration

**Traditional BAW path** — use `read_file` to read the source `.properties` file. Extract:

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

**CP4BA containerized path** — parse the CR YAML obtained in Option C. Extract the fields listed in Option C above.

Build a **Source Endpoints Map**: a deduplicated list of every distinct hostname, IP address, and (for traditional BAW only) file path found.

### Step 3 — Capture target environment

**Traditional BAW:**
1. **Explicit `.properties` path already provided** — read it with `read_file` and extract the same fields as Step 2.
2. **No target `.properties` provided** — ask using `ask_followup_question`:
   > "Do you have a BPMConfig `.properties` file exported from the target server? If so, please provide the path. Otherwise I'll use the hostname/URL you've already stated."
3. **User confirms no file** — fall back to verbal values already in the conversation (hostname, port, protocol). Extract the hostname and port from any URL provided; infer HTTPS if port is 9443.

**CP4BA containerized:**
1. **User provided a target CR YAML or namespace** — run `oc get ICP4ACluster` on the target cluster (Option C) and extract the same fields.
2. **User provided only a target hostname/URL** — use it directly. Note the BAW URL pattern on CP4BA containers is `https://<baw-route-hostname>/WorkflowCenter` or `/ProcessPortal`.
3. **No target info provided** — ask: "What is the hostname or namespace of your target CP4BA cluster?"

Build the **Target Endpoints Map** from whichever source is used.

### Step 4 — Acquire the TWX

Use the first path that succeeds. If the user already stated a `.twx` file path earlier in the conversation, skip to Step 5 directly using that path.

**Path 1 — Export API (preferred)**


#### Step 4a — Resolve container and version acronyms

If the user provided an acronym and snapshot, skip to Step 4b. Otherwise:

1. **List containers:**
   ```
   GET {BAW_BASE_URL}{CTX}/ops/std/bpm/containers
   ```
   Match `container_name` against the app name the user gave. Record the `container` field as `{CONTAINER}`.

2. **List versions:**
   ```
   GET {BAW_BASE_URL}{CTX}/ops/std/bpm/containers/{CONTAINER}/versions
   ```
   Pick the most recent non-archived version. Record its `version` field as `{VERSION}`. If there are multiple snapshots, show the user a brief table and ask which to export.

#### Step 4b — Export the TWX

```
GET {BAW_BASE_URL}{CTX}/ops/std/bpm/containers/{CONTAINER}/versions/{VERSION}/export?use_enhanced_filenames=true
```

Include headers:
```
Authorization: Basic <base64(user:pass)>
BPMCSRFToken: {BAW_CSRF}
Cookie: {BAW_SESSION}
Accept: application/octet-stream, */*
```

The `Accept: application/octet-stream, */*` header is **required** — omitting it causes a `406 Not Acceptable` error.

The response is a binary `.twx` file. Get the system temp directory:

```python
python -c "import tempfile; print(tempfile.gettempdir())"
```

Save as `<temp_dir>/<CONTAINER>_<VERSION>.twx`. Use that path as `<absolute_path_to_twx>` throughout Steps 5–6.

If the export returns 403/404, re-check `{CONTAINER}` and `{VERSION}` via the listing calls in Step 4a.

**Path 2 — Local file (fall back after Path 1 has visibly failed)**

If the REST export fails or errors more than once, offer:
> *"If you already have the `.twx` file for this app on your machine, you can point me to it and I'll work from that directly."*

Use the provided path directly as `<absolute_path_to_twx>`. Do not ask pre-emptively — only after a real failure.

### Step 5 — Run TWX endpoint scan

The script path is `<skill_dir>/scripts/scan_twx_endpoints.py` where `<skill_dir>` is the directory containing this SKILL.md.

Obtain the system temp directory once and reuse it for all temp files in Steps 4a–4d:
```
python -c "import tempfile; print(tempfile.gettempdir())"
```

Delete the source map immediately after the scan, regardless of success or failure.

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

| XML tag | Artifact type in Workflow Center / Studio |
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

### Step 6 — Generate report

Write the report using `write_file` to `<report_dir>/endpoint-validation-report.md`. Use this structure:

```markdown
# BAW Endpoint Validation Report

## Environment Transition Summary
| | Value |
|---|---|
| Process App TWX | <filename> |
| Deployment type | Traditional BAW / CP4BA containerized |
| Source config | <path or "ICP4ACluster CR — namespace/name"> |
| Target config | <path, CR, or "stated verbally"> |
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
| 1 | External service | External Service | External service operation1 | 99 | `urlTemplate="http://localhost:9080/MyAPI/rest/v1"` | **Traditional BAW:** Workflow Designer → Process App Settings → Servers → MyAPI. **CP4BA (Studio):** Business Automation Studio → open process app → Process App Settings → Servers → MyAPI |
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
- **Where to fix** column: use the table in Step 7 to select the right navigation path; include the artifact name so the developer knows exactly what to open. For inline scripts, add "⚠️ Cannot fix via Process Admin Console — requires code change in Workflow Designer."
- **Group duplicate entries**: if the same artifact + line context appears twice (e.g. line 84 and 216 in the same file, both containing the same script), merge them into a single row with a note like "(2 occurrences — fixing in Designer updates both)".
- Do not expose internal UUID paths in the report body. They may appear in a collapsed `<details>` footnote at most.
- **Hyperlinks must resolve.** Only include a hyperlink in the report if the URL is taken directly from the verified References section at the bottom of this SKILL.md. Do not construct version-specific IBM Docs URLs that are not in the References section — they cannot be verified without a search. Navigation paths (e.g. `Workflow Designer → Process App Settings → Servers`) are always written as plain text; a link is optional and only added when a verified URL is available.

### Step 7 — Present summary and fix guidance

After writing the report, give the user a plain-language summary inline covering:
- How many critical references were found and in which files
- What the endpoint changes are (old → new, per property)
- Whether the process app is ready to install on the new server

For each Critical finding, tell the user exactly where to fix it in BAW 26.0.x:

| Finding type | Where to fix (BAW 26.0.x) |
|---|---|
| REST server URL hardcoded in `<urlTemplate>` or `urlTemplate` attribute | **Traditional BAW:** In **Workflow Designer**, open the process app → **Process App Settings** → **Servers** tab → find the REST server entry → update **Host name** and **Port**. **CP4BA (Studio):** Business Automation Studio → open process app → **Process App Settings** → **Servers** tab → update the entry. |
| REST server host/port needs updating post-deployment (without re-importing TWX) | In the **Process Admin Console** → **Installed Apps** → click the overflow menu of the snapshot → **App Details** → **Servers** tab → update **Hostname**, **Port**, and **Secure Server** on each REST server binding. (ref: https://www.ibm.com/docs/en/baw/26.0.x?topic=properties-changing-server-settings-in-process-admin-console) |
| Hardcoded URL in a service flow script (`<script>` tag) | **Traditional BAW:** In **Workflow Designer**, navigate to the service flow → **Script** tab of the script task → update the hardcoded URL. **CP4BA (Studio):** Business Automation Studio → open process app → open the service flow → script task → **Script** tab. Consider replacing with a server variable bound via Process App Settings instead. |
| Hardcoded URL in a client-side human service (coach view script) | **Traditional BAW:** In **Workflow Designer**, open the Coach or client-side human service → find the view with the inline script → **Script** tab. **CP4BA (Studio):** Business Automation Studio → open process app → open the coach view → **Script** tab. |
| Hostname in a variable default value (`<defaultValue>`) | **Traditional BAW:** In **Workflow Designer**, open the service or process → **Variables** tab → find the variable → update the default value. **CP4BA (Studio):** Business Automation Studio → open process app → open the artifact → **Variables** tab. |
| Hardcoded portal link in notification / task activity documentation | **Traditional BAW:** In **Workflow Designer**, open the process → click the notification or task activity → edit the **Documentation** or **Notification** field. **CP4BA (Studio):** Business Automation Studio → open process app → open the process → click the activity → edit **Documentation** / **Notification** field. |
| JDBC URL in a service SQL call | In the **WebSphere Integrated Solutions Console (ISC)** on the target server → **Resources → JDBC → Data Sources** → update the data source URL. This is a server-side change, not made in Designer. |
| REST server URL hardcoded in TWX (CP4BA target) | REST server hostname/port can be updated post-deployment in the **Process Admin Console** → **Installed Apps** → overflow menu → **App Details** → **Servers** tab. On CP4BA containers the Process Admin Console is available at `https://<baw-route-hostname>/ProcessAdmin`. |
| Environment endpoint needs updating at cluster level (CP4BA) | Edit `spec.baw_configuration[*].hostname` or the external service configuration in the `ICP4ACluster` CR and re-apply with `oc apply -f`. Server-level endpoint changes (e.g. database host) must be made in the CR, not in Designer. Consult your CP4BA platform administrator. |

Do not offer to generate XML patches, apply configuration, or edit files inside the TWX — that is out of scope.

## Disambiguation rules

**No live BAW API calls**
REST calls are only used to: (1) authenticate via `POST {CTX}/ops/system/login`, and (2) download the TWX via `GET {CTX}/ops/std/bpm/containers/{container}/versions/{version}/export`. Do not make any other REST calls to the BAW runtime. All environment analysis is file-based.

**No TWX path provided and no server access**
If the user cannot connect to the BAW server and has no `.twx` file on disk, explain how to export based on their deployment:

- **Traditional BAW (Workflow Center):** Open Workflow Center → navigate to the process app → find the snapshot → click **Export** → select **.twx** → save the file. The `.twx` option is for Workflow Center import/export; use `.zip` only for installing directly to a runtime environment. (ref: https://www.ibm.com/docs/en/baw/26.0.x?topic=snapshots-importing-exporting-projects-toolkits)
- **CP4BA containerized (Business Automation Studio):** Open Business Automation Studio → **Business automations** → open the process app → select the snapshot → overflow menu → **Export** → save the `.twx` file.

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

**CP4BA containerized — `oc` / `kubectl` access required** — Collecting source endpoints from a CP4BA deployment requires the OpenShift CLI (`oc`) or `kubectl` to be installed and logged in, or the user must supply the `ICP4ACluster` CR YAML manually. If neither is available, the skill pauses and asks for a paste rather than failing silently. The skill does **not** support `BPMConfig` on containerized deployments — that tool is absent by design on CP4BA.

**Encrypted property values (traditional BAW)** — BPMConfig exports mask passwords with `{xor}` encoding. The scan does not attempt to decrypt these; the skill excludes them from the endpoint map.

**Binary or compiled artifacts inside TWX** — some TWX files contain compiled JavaScript or minified CSS where pattern matching may miss encoded references. The scan reports binary files skipped; flag this in the report if relevant.

**Script requires Python 3.6+** — `scripts/scan_twx_endpoints.py` uses only stdlib (`zipfile`, `xml.etree.ElementTree`, `re`, `json`, `argparse`). No pip install required.

## References

- IBM Docs — BPMConfig command-line utility: https://www.ibm.com/docs/en/baw/26.0.x?topic=utilities-bpmconfig-command-line-utility
- IBM Docs — Configuration properties for the BPMConfig command: https://www.ibm.com/docs/en/baw/26.0.x?topic=utility-configuration-properties-bpmconfig-command
- IBM Docs — Specifying a REST server in Process App Settings: https://www.ibm.com/docs/en/baw/26.0.x?topic=service-specifying-rest-server
- IBM Docs — Changing REST server settings in Process Admin Console: https://www.ibm.com/docs/en/baw/26.0.x?topic=properties-changing-server-settings-in-process-admin-console
- IBM Docs — BPMInstallOfflinePackage command: https://www.ibm.com/docs/en/baw/26.0.x?topic=scripting-bpminstallofflinepackage
- IBM Docs — Importing and exporting projects and toolkits from Workflow Center: https://www.ibm.com/docs/en/baw/26.0.x?topic=snapshots-importing-exporting-projects-toolkits
- IBM Docs — CP4BA custom resource pattern structure: https://www.ibm.com/docs/en/cloud-paks/cp-biz-automation/26.0.0?topic=deployment-installing-capabilities-in-openshift-console
- IBM Docs — BAW on containers — verifying installation (ConfigMap/route URLs): https://www.ibm.com/docs/en/baw/23.0.x?topic=deployment-verifying-installation
- IBM Docs — Moving from BAW traditional to CP4BA: https://www.ibm.com/docs/en/cloud-paks/cp-biz-automation/26.0.0?topic=cloud-business-automation-workflow
- `references/BPMCONFIG_REFERENCE.md` — full properties key reference
