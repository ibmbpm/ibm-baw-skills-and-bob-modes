# BAW Endpoint Validation — Documentation

> Use when a BAW administrator wants to validate a process application before installing it on a new server — asking what new server to target, reading the BPMConfig properties file to extract source and target endpoints, scanning the TWX export for hardcoded references to the old server, and generating a report of findings with a summary of the intended endpoint changes.

## Purpose

This skill helps BAW administrators identify what must change before a process application snapshot is promoted to a new server. It reads exported BPMConfig properties files to build a source-to-target endpoint map, scans the TWX export for any hardcoded references to old hostnames, database hosts, or paths, and produces a structured markdown report that classifies each finding as Critical, Warning, or Info and tells the developer exactly where to fix it in Workflow Designer or the Process Admin Console.

Use this skill when preparing for an offline promotion, a server migration, or any environment transition where the target server differs from the source. It does not perform the promotion itself — it validates readiness before you run `BPMInstallOfflinePackage` or import via Workflow Center.

## Setup and configuration

- **Python 3.6 or later** — required to run the scan script (`scripts/scan_twx_endpoints.py`). No external packages are needed; the script uses Python stdlib only (`zipfile`, `re`, `json`, `argparse`, `xml.etree.ElementTree`).
- **BPMConfig** — if exporting properties from a live environment, the BAW deployment manager (or stand-alone server) must be running. The binary is at `<install_root>/bin/BPMConfig.sh` (Linux/AIX) or `<install_root>\bin\BPMConfig.bat` (Windows).
- **TWX file** — export from Workflow Center before starting. The TWX must not be password-protected (password-protected ZIPs cannot be scanned).
- No MCP servers, API keys, or additional configuration are required.

## Compatibility

- **TWX must be a valid ZIP archive** — password-protected TWX files cannot be scanned; the script will error with "not a valid ZIP/TWX file".
- **Python 3.6+** — f-strings and `zipfile.ZipFile.infolist()` with `is_dir()` are used; earlier versions will fail.
- **BPMConfig -export requires a running deployment manager** — export the properties file before taking any server offline.
- **No live BAW REST API calls are made** — all analysis is file-based; the target BAW server does not need to be reachable.

> **Note:** Credentials shown in prompt examples are for illustration only. Never use real production credentials in prompts. Use environment variables or a secrets manager for sensitive values.

## Prompt examples

### No TWX yet — get export instructions first

**Prompt:**
> We're planning to move our BAW process application to a new production server at baw-prod.example.com:9443. I don't have a TWX file yet. How do I get started?

**What to expect:** Step-by-step instructions for exporting a TWX from Workflow Center, plus an explanation of what the skill does once you have the file.

---

### Run BPMConfig -export from a live source server

**Prompt:**
> I want to validate my process app before moving it to a new server. My source BAW install is at `/opt/IBM/BAW26` on Linux. I don't have an exported properties file — can you generate one?

**What to expect:** Bob discovers BPMConfig, locates the profiles directory, identifies the deployment environment name, and runs `BPMConfig.sh -export` to produce a `.properties` file in a temp directory — then immediately reads and parses it.

---

### Full validation with all three inputs provided

**Prompt:**
> I have everything ready. Source BPMConfig export is at `/exports/source-DE1.properties`. The target server is baw-prod.mycompany.com and the target database is db-prod.mycompany.com on port 50000. The TWX is at `/exports/OrderManagement.twx`. Please run the full endpoint validation.

**What to expect:** Bob parses the source properties, builds a source-to-target endpoint map, scans the TWX, resolves artifact names, writes a full markdown report to `/exports/OrderManagement.twx - reports/endpoint-validation-report.md`, and gives you an inline summary of critical findings with fix guidance.

---

### Both source and target properties files provided

**Prompt:**
> Here are both BPMConfig export files. Source is at `C:\exports\source.properties` and target is at `C:\exports\target.properties`. The TWX is at `C:\exports\ClaimsProcessing.twx`. Validate the endpoint changes.

**What to expect:** Bob extracts source and target endpoint maps from both properties files, diffs the key hostnames and database addresses into a Source → Target Endpoint Mapping table, scans the TWX, and writes the report to `C:\exports\ClaimsProcessing.twx - reports\endpoint-validation-report.md`.

---

### Understanding and fixing a critical finding

**Prompt:**
> The scan found this finding: `file=services/InvoiceService.xml, line=112, matched_pattern=baw-dev.example.com, severity=critical, context_snippet='<url>http://baw-dev.example.com:9080/InvoiceAPI/rest/v1</url>'`. What does it mean and how do I fix it?

**What to expect:** Bob classifies the finding as a hardcoded REST server URL (Critical), explains that it will break at runtime on the target server, and directs you to the exact location in Workflow Designer (Process App Settings → Servers tab) or the Process Admin Console (Installed Apps → App Details → Servers tab) where the hostname and port are updated.

---

### Post-deployment fix without re-importing the TWX

**Prompt:**
> The snapshot is already installed on the target server but the REST calls are failing because the server URL still points to the old hostname. How do I update it without re-importing the TWX?

**What to expect:** Bob directs you to the Process Admin Console → Installed Apps → overflow menu of the snapshot → App Details → Servers tab, where you can update Hostname, Port, and Secure Server for each REST server binding without redeployment.

---

### Localhost findings — deciding what is a real blocker

**Prompt:**
> The scan returned 14 localhost findings. Some are in `<url>http://localhost:9080/portal/...</url>` and others are in `<url>http://localhost:8080/OrderAPI/rest/v1</url>`. Are all of these blockers?

**What to expect:** Bob distinguishes BAW-internal localhost URLs (`/portal`, `/teamworks`, `/rest/bpm`) — which are Warnings, not blockers — from custom application context roots like `/OrderAPI`, which are conditional Criticals, and asks whether that external service is co-located on the target BAW server.

---

### Multiple deployment environments in the source properties file

**Prompt:**
> My source properties file has two deployment environments — `DE1` and `DE2` — each with different database hosts. The TWX is at `/exports/SharedApp.twx`. Which endpoints should I scan for?

**What to expect:** Bob extracts endpoint values from all `bpm.de.*` blocks separately, labels them by DE number in the endpoint map, and builds the source map with all unique hostnames so the TWX scan covers both environments.

---

## Script reference — `scan_twx_endpoints.py`

Located at `scripts/scan_twx_endpoints.py`. Run directly or invoked automatically by the skill.

**Runtime:** Python 3.6+ · **Dependencies:** stdlib only (no `pip install` required)

**CLI usage:**

```bash
# Inline source map
python scan_twx_endpoints.py \
  --twx /path/to/app.twx \
  --source-map '{"baw-source.example.com": "dmgr", "db-old.example.com": "database"}'

# Source map from a JSON file (preferred — avoids shell quoting issues)
python scan_twx_endpoints.py \
  --twx /path/to/app.twx \
  --source-map-file /tmp/_baw_source_map.json \
  --json
```

**Key flags:**

| Flag | Description |
|---|---|
| `--twx` | Path to the `.twx` file (required) |
| `--source-map` | Inline JSON object mapping source hostnames to labels |
| `--source-map-file` | Path to a JSON file containing the source map (mutually exclusive with `--source-map`) |
| `--json` | Emit results as a single JSON object; used by the skill for structured parsing |

**Output shape (with `--json`):**

```json
{
  "findings": [
    {
      "file": "objects/abc123.xml",
      "line": 47,
      "matched_pattern": "baw-source.example.com",
      "severity": "critical",
      "context_snippet": "<url>http://baw-source.example.com:9080/MyAPI/rest/v1</url>"
    }
  ],
  "files_scanned": 312,
  "binary_files_skipped": 8,
  "source_terms_searched": ["baw-source.example.com", "db-old.example.com"]
}
```

**Severity classification:**

| Severity | Meaning |
|---|---|
| `critical` | Found in a URL, endpoint, WSDL, JDBC, or `urlTemplate` attribute — will break at runtime |
| `warning` | Found in a script tag, default value, or parameter; or a BAW-internal localhost URL |
| `info` | Low-priority match; no direct action required |

**Exit codes:** `0` = no critical findings; `1` = one or more critical findings or scan error.

## References

- [BPMConfig command-line utility (BAW 26.0.x)](https://www.ibm.com/docs/en/baw/26.0.x?topic=utilities-bpmconfig-command-line-utility)
- [Configuration properties for the BPMConfig command (BAW 26.0.x)](https://www.ibm.com/docs/en/baw/26.0.x?topic=utility-configuration-properties-bpmconfig-command)
- [Specifying a REST server (BAW 26.0.x)](https://www.ibm.com/docs/en/baw/26.0.x?topic=service-specifying-rest-server)
- [Changing server settings in Process Admin Console (BAW 26.0.x)](https://www.ibm.com/docs/en/baw/26.0.x?topic=properties-changing-server-settings-in-process-admin-console)
- [BPMInstallOfflinePackage command (BPM 8.5.7)](https://www.ibm.com/docs/en/bpm/8.5.7?topic=scripting-bpminstallofflinepackage)
- [Importing and exporting projects and toolkits (BAW 26.0.x)](https://www.ibm.com/docs/en/baw/26.0.x?topic=snapshots-importing-exporting-projects-toolkits)
- [`references/BPMCONFIG_REFERENCE.md`](../../skills/baw-endpoint-validation/references/BPMCONFIG_REFERENCE.md) — full BPMConfig properties key reference
