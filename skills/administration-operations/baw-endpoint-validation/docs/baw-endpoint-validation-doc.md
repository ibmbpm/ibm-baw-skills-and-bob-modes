# BAW Endpoint Validation — Documentation

> Validates a BAW process application before installing it on a new server — supports both traditional BAW (BPMConfig properties files) and CP4BA containerized deployments (custom resource file) — and generates a report classifying every hardcoded server reference as Critical, Warning, or Info with exact fix guidance.

## Purpose

This skill helps BAW administrators identify what must change before a process application snapshot is promoted to a new server. It supports **both** traditional BAW (on-premises / WebSphere) and **CP4BA containerized** (OpenShift / Kubernetes) deployments. It reads exported BPMConfig properties files or the `ICP4ACluster` custom resource to build a source-to-target endpoint map, scans the TWX export for hardcoded references to old hostnames, database hosts, or install paths, and produces a structured markdown report that tells the developer exactly where to fix each finding in Workflow Designer or the Process Admin Console. Use it when preparing for an offline promotion, a server migration, or any environment transition where the target server differs from the source. It does not perform the promotion itself — it validates readiness before you run `BPMInstallOfflinePackage` or import via **Workflow Center** (traditional BAW) or **Business Automation Studio** (CP4BA containerized).

## Setup and configuration

- **Python 3.6+** — required to run `scripts/scan_twx_endpoints.py`. No external packages are needed; the script uses the standard library only (`zipfile`, `re`, `json`, `argparse`, `xml.etree.ElementTree`).
- **Traditional BAW path:** `BPMConfig.bat` / `BPMConfig.sh` must be accessible on the BAW deployment manager host. The deployment manager must be running at the time of export.
- **CP4BA containerized path:** The OpenShift CLI (`oc`) or `kubectl` must be installed and logged in to the cluster, **or** the user must be able to paste the `ICP4ACluster` CR YAML directly. `BPMConfig` is **not** used on CP4BA; the skill will not attempt it.
- **BAW server credentials or a local TWX file** — the skill can download the TWX via the export REST API (preferred) or scan a `.twx` file on disk.
- No MCP server or API key is required.

## TWX acquisition

When you provide a server URL for the TWX download, the skill will:

1. Probe for the active context root (`/ops`, `/bas/ops`, `/baw/ops`, `/bpm/ops`) to handle both standalone BAW and CP4BA deployments automatically.
2. Authenticate via `POST .../ops/system/login` — credentials are used only to obtain a session token and are not stored beyond the current conversation.
3. List containers and versions if you do not know the app acronym or snapshot.
4. Download the TWX via `GET .../ops/std/bpm/containers/{container}/versions/{version}/export?use_enhanced_filenames=true` and save it to a system temp directory.

If you already have a `.twx` file on disk, provide its path — the skill uses it directly. All scan steps are purely file-based regardless of how the TWX was obtained.

## Compatibility

- **Traditional BAW** (on-premises, WebSphere Network Deployment): uses `BPMConfig -export` — the deployment manager must be running during export.
- **CP4BA containerized** (OpenShift / Kubernetes): uses `oc get ICP4ACluster` — `BPMConfig` is unavailable by design and is never invoked.
- **Mixed migration** (traditional BAW → CP4BA): supported — source endpoints come from `BPMConfig`, target endpoints come from the `ICP4ACluster` CR.
- **TWX must be a valid, unencrypted ZIP archive** — password-protected TWX files cannot be scanned and will cause the script to error.
- **BPMConfig -export requires a running deployment manager** — export the properties file before taking any server offline.
- For environments with self-signed certificates, TLS verification is disabled automatically during TWX download.

## Prompt examples

### Full validation using the export API

**Prompt:**
> I want to validate the OrderManagement process app before installing it on a new server. My source BAW server is https://baw.example.com:9443. The target server hostname is baw-prod.example.com. I don't have a BPMConfig properties file yet — can you run BPMConfig -export to get it?

**What to expect:** Bob discovers BPMConfig automatically, exports the source properties, asks for credentials to download the TWX via the export API, scans the TWX, resolves artifact names, writes a full report, and gives an inline summary of critical findings with fix guidance.

---

### Full validation with both properties files and local TWX

**Prompt:**
> Here are both BPMConfig export files. Source is at `C:\exports\source.properties` and target is at `C:\exports\target.properties`. The TWX is at `C:\exports\ClaimsProcessing.twx`. Validate the endpoint changes.

**What to expect:** Bob extracts source and target endpoint maps from both properties files, builds a Source → Target Endpoint Mapping table, scans the TWX file directly (no server connection needed), and writes the report to `C:\exports\ClaimsProcessing.twx - reports\endpoint-validation-report.md`.

---

### Run BPMConfig -export from an install root

**Prompt:**
> My source BAW install is at `/opt/IBM/BAW26` on Linux. I don't have an exported properties file — can you generate one?

**What to expect:** Bob searches the install tree for BPMConfig, locates the profiles directory and deployment environment name automatically, runs `BPMConfig.sh -export`, and immediately reads and parses the resulting `.properties` file.

---

### Validate a CP4BA-to-CP4BA process app migration

**Prompt:**
> We're migrating our process app from one CP4BA cluster to another. The source cluster project is `cp4ba-dev` and the target cluster project is `cp4ba-prod` on a different cluster. The TWX is at `/exports/ClaimsApp.twx`. Please run the full validation.

**What to expect:** The skill runs `oc version --client` to verify `oc` is available, retrieves the `ICP4ACluster` CR from both namespaces, extracts BAW hostnames and database endpoints, runs the TWX scan against source hostnames, and produces a report without invoking `BPMConfig` at any point.

---

### Validate a migration from traditional BAW to CP4BA

**Prompt:**
> We're migrating from our old on-premises BAW server at `/opt/IBM/BAW` to a new CP4BA cluster on OpenShift, project `cp4ba-prod`. The TWX is at `/exports/MigrationApp.twx`.

**What to expect:** The skill identifies this as a mixed scenario, confirms the split with you (traditional BAW as source, CP4BA as target), collects source endpoints via `BPMConfig` and target endpoints via `oc get ICP4ACluster`, then runs the scan and generates a report.

---

### CP4BA deployment — `oc` not installed on this machine

**Prompt:**
> We're on CP4BA containerized on OpenShift. Project is `cp4ba`. I need to validate `/exports/MyApp.twx` before deploying to `baw-prod.apps.newcluster.example.com`. Note: when I try to run `oc` on this machine I get `oc: command not found`.

**What to expect:** The skill acknowledges that `oc` is unavailable, provides the exact command to run on a machine with cluster access (`oc get ICP4ACluster icp4adeploy -n cp4ba -o yaml`), mentions the OpenShift web console as an alternative, and waits for you to paste the YAML before continuing — it does not fall back to `BPMConfig`.

---

### `oc` installed but not logged in

**Prompt:**
> We're on CP4BA on OpenShift, project `cp4ba`. I need to validate `/exports/MyApp.twx`. Note: `oc version --client` works and shows `Client Version: 4.14.0`, but when I run `oc get ICP4ACluster` I get: `Error from server (Unauthorized): the server has asked for the client to provide credentials`.

**What to expect:** The skill recognises this as an authentication error (not a missing binary), tells you to run `oc login <cluster-api-url>`, and offers to continue once you're logged in or to proceed with a pasted CR YAML instead.

---

### BPMConfig not found — redirect to CP4BA path

**Prompt:**
> I need to validate my process app before moving it to a new server. My BAW install is at `/opt/IBM/BAW-OLD`. The TWX is at `/exports/ClaimsApp.twx`. Note: I searched `/opt/IBM/BAW-OLD` and `BPMConfig.sh` is not anywhere in that directory.

**What to expect:** The skill displays a warning that `BPMConfig` was not found, explains this is expected on CP4BA containerized deployments, and offers two options: confirm a different traditional BAW install root, or confirm CP4BA and proceed via the `ICP4ACluster` CR.

---

### Ambiguous deployment type — skill asks before proceeding

**Prompt:**
> I want to move my process app to a new server. The TWX is at `/exports/ClaimsApp.twx` and the new server is at `claims-prod.example.com`.

**What to expect:** The skill asks whether your environment is a traditional on-premises BAW installation or a CP4BA containerized deployment on OpenShift/Kubernetes before collecting any endpoint data or running the scan.

---

### Understand and fix a critical finding

**Prompt:**
> The scan found: `file=services/OrderService.xml, line=47, matched_pattern=baw-source.mycompany.com, severity=critical, context_snippet='<url>http://baw-source.mycompany.com:9080/OrderAPI/rest/v1</url>'`. What does this mean and how do I fix it?

**What to expect:** Bob classifies the finding as Critical (a hardcoded REST server URL that will fail at runtime), identifies it as an external REST service binding, and directs you to Workflow Designer → Process App Settings → Servers tab to update the hostname and port before deployment.

---

### Post-deployment fix without re-importing the TWX

**Prompt:**
> The snapshot is already installed on the target server but REST calls are failing because the server URL still points to the old hostname. How do I update it without re-importing the TWX?

**What to expect:** Bob directs you to the Process Admin Console → Installed Apps → snapshot overflow menu → App Details → Servers tab, where you can update Hostname, Port, and Secure Server without redeployment.

---

### Localhost findings — which are real blockers

**Prompt:**
> The scan returned 14 localhost findings. Some are in `<url>http://localhost:9080/portal/...</url>` and others in `<url>http://localhost:8080/OrderAPI/rest/v1</url>`. Are all of these blockers?

**What to expect:** Bob distinguishes BAW-internal localhost URLs (`/portal`, `/teamworks`, `/rest/bpm`) — Warnings, not blockers — from custom context roots like `/OrderAPI`, which are conditional Criticals that depend on whether the API is co-located on the target server.

---

### Multiple deployment environments in the source properties file

**Prompt:**
> My source properties file has two deployment environments — `DE1` and `DE2` — each with different database hosts. The TWX is at `/exports/SharedApp.twx`. Which endpoints should I scan for?

**What to expect:** Bob extracts endpoint values from all `bpm.de.*` blocks separately, labels them by DE number in the endpoint map, and includes all unique hostnames in the source map so the TWX scan covers both environments.

---

## Script reference — `scan_twx_endpoints.py`

Located at `scripts/scan_twx_endpoints.py`. Invoked automatically by the skill; can also be run directly.

**Runtime:** Python 3.6+ · **Dependencies:** stdlib only

**CLI usage:**

```bash
# Source map from a JSON file (preferred)
python scan_twx_endpoints.py \
  --twx /path/to/app.twx \
  --source-map-file /tmp/_baw_source_map.json \
  --json

# Inline source map
python scan_twx_endpoints.py \
  --twx /path/to/app.twx \
  --source-map '{"baw-old.example.com": "dmgr", "db-old.example.com": "database"}'
```

**Key flags:**

| Flag | Description |
|---|---|
| `--twx` | Path to the `.twx` file (required) |
| `--source-map` | Inline JSON object mapping source hostnames to labels |
| `--source-map-file` | Path to a JSON file containing the source map |
| `--json` | Emit results as a single JSON object for structured parsing |

**Output shape (with `--json`):**

```json
{
  "findings": [
    {
      "file": "objects/abc123.xml",
      "line": 47,
      "matched_pattern": "baw-old.example.com",
      "severity": "critical",
      "context_snippet": "<url>http://baw-old.example.com:9080/OrderAPI/rest/v1</url>"
    }
  ],
  "files_scanned": 312,
  "binary_files_skipped": 8,
  "source_terms_searched": ["baw-old.example.com", "db-old.example.com"]
}
```

**Severity classification:**

| Severity | Meaning |
|---|---|
| `critical` | Found in a URL, `urlTemplate`, WSDL, or JDBC attribute — will break at runtime |
| `warning` | Found in a script tag, default value, or parameter; or a BAW-internal localhost URL |
| `info` | Low-priority match; no direct action required |

**Exit codes:** `0` = no critical findings; `1` = one or more critical findings or scan error.

## Known limitations

- **CP4BA `oc` / `kubectl` access:** Collecting source endpoints from a CP4BA deployment requires `oc` or `kubectl` installed and logged in, or the user must paste the CR YAML. The skill pauses and asks rather than failing silently.
- **`BPMConfig` not available on CP4BA:** By design. The skill detects this automatically and redirects to the `ICP4ACluster` CR path.
- **Encrypted property values (traditional BAW):** `BPMConfig` exports mask passwords with `{xor}` encoding. These values are excluded from the endpoint map and are not scanned.
- **Binary/compiled artifacts inside TWX:** Compiled JavaScript or minified CSS may contain encoded references that pattern matching misses. The report notes any binary files skipped.

## References

- [BPMConfig command-line utility (BAW 26.0.x)](https://www.ibm.com/docs/en/baw/26.0.x?topic=utilities-bpmconfig-command-line-utility)
- [Configuration properties for the BPMConfig command (BAW 26.0.x)](https://www.ibm.com/docs/en/baw/26.0.x?topic=utility-configuration-properties-bpmconfig-command)
- [Adding a REST server in Process App Settings (BAW 19.0)](https://www.ibm.com/docs/en/baw/19.0.0?topic=service-adding-rest-server)
- [Changing REST server settings in Process Admin Console (BAW 24.0.x)](https://www.ibm.com/docs/en/baw/24.0.x?topic=properties-changing-server-settings-in-process-admin-console)
- [BPMInstallOfflinePackage command (BAW 24.0.x)](https://www.ibm.com/docs/en/baw/24.0.x?topic=scripting-bpminstallofflinepackage)
- [Exporting process apps from Workflow Center (BAW 19.0)](https://www.ibm.com/docs/en/baw/19.0.0?topic=mpa-importing-exporting-process-apps-case-solutions-from-workflow-center-console)
- `references/BPMCONFIG_REFERENCE.md` — full BPMConfig properties key reference (included in the skill folder)

