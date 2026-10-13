# BAW Toolkit Analyzer — Documentation

> Analyzes IBM BAW toolkit dependencies from a TWX export. Maps direct and transitive toolkit dependencies, tracks snapshot versions, and flags missing, conflicting, circular, outdated, and unused dependencies.

## Purpose

This skill analyzes the toolkit dependency tree inside an IBM BAW process application TWX export and produces a structured report covering direct dependencies, transitive dependencies resolved from embedded toolkit ZIPs, snapshot version tracking, and issue detection (conflicts, circular references, tip snapshot references, unused and missing dependencies). It is intended for BAW administrators and developers who need to understand toolkit structure, assess the impact of upgrading a toolkit snapshot, or validate a process application before deployment.

## Setup and configuration

- **Python 3** — required to run `scripts/analyze_toolkit_deps.py`. No external packages are needed; the script uses the standard library only (`zipfile`, `xml.etree.ElementTree`, `argparse`, `json`, `os`, `sys`).
- **BAW server credentials or a local TWX file** — the skill can download the TWX automatically via the BAW export REST API (preferred), or work from a `.twx` file on disk if you provide the path.
- No MCP server or API key is required.

## TWX acquisition

When you provide a server URL, the skill will:

1. Probe for the active context root (`/ops`, `/bas/ops`, `/baw/ops`, `/bpm/ops`) to handle both standalone BAW and CP4BA deployments automatically.
2. Authenticate via `POST .../ops/system/login` — credentials are used only to obtain a session token and are not stored beyond the current conversation.
3. List containers and versions if you do not know the app acronym or snapshot.
4. Download the TWX via `GET .../ops/std/bpm/containers/{container}/versions/{version}/export?use_enhanced_filenames=true` and save it to a system temp directory.

If you already have a `.twx` file on disk, provide its path — the skill uses it directly and skips the download.

## Compatibility

- Verified against **BAW 8.6.x** TWX exports (confirmed XML structure). Works with both standalone IBM Business Automation Workflow and IBM Cloud Pak for Business Automation (CP4BA) deployments.
- Tip snapshot detection relies on the snapshot name string — a snapshot named `"Tip"` (case-insensitive) is flagged. References to the live branch under a custom name will not be detected.
- For environments with self-signed certificates (typical in CP4BA on-prem), TLS verification is disabled automatically during download.

## Prompt examples

### Full dependency analysis via the export API

**Prompt:**
> Analyze the toolkit dependencies for the ClaimsProcessing process app on my BAW server at https://baw.example.com:9443. Run a full analysis.

**What to expect:** Bob determines the context root, asks for credentials, lists available snapshots, downloads the TWX, runs the analysis, and presents a summary paragraph, Mermaid dependency graph, direct-dependencies table, per-toolkit usage breakdown, transitive dependency listing, and a consolidated issues section.

---

### Discover which toolkits are present before choosing a target

**Prompt:**
> Connect to https://baw.example.com:9443 and list the toolkits that ClaimsProcessing depends on before I decide which one to investigate.

**What to expect:** Bob downloads the TWX and prints a list of every declared toolkit dependency — display name, acronym, and snapshot version — then waits for your next instruction.

---

### Where-used analysis for a specific toolkit

**Prompt:**
> On my BAW server at https://baw.example.com:9443, which services or human services inside the ClaimsProcessing app reference the UI Toolkit?

**What to expect:** Bob downloads the TWX and presents a table of every artifact that references any exported item from UI Toolkit, grouped by artifact type, with specific toolkit items (coach views, BO types, services) called out for each.

---

### What-uses drill-down on a named artifact

**Prompt:**
> Using my BAW server at https://baw.example.com:9443, for the ClaimsProcessing app — which toolkit items does the `SubmitExpense` service consume?

**What to expect:** A two-column table listing every toolkit item (coach view, Business Object type, service) consumed by `SubmitExpense`, with the source toolkit and snapshot for each one.

---

### Circular dependency and tip snapshot check

**Prompt:**
> Connect to https://baw.example.com:9443 and analyze the ClaimsProcessing app. Focus on circular toolkit dependencies and any Tip snapshot references — I need to know if this is safe to deploy.

**What to expect:** The full dependency graph plus an issues section calling out any circular cycles (e.g. `ToolkitA → ToolkitB → ToolkitA`) and any Tip snapshot references with a pinning recommendation; if neither issue is present, the skill says so explicitly.

---

### Work from a local TWX file

**Prompt:**
> I have a TWX export at `C:/baw-exports/ClaimsProcessing.twx`. Analyze the toolkit dependencies and tell me if there are any issues before I promote to production.

**What to expect:** Bob works directly from the file on disk — no server connection needed — and produces the same full report.

---

## Analysis modes

| Mode | Flag | Description |
|---|---|---|
| `full` | *(default)* | Maps all toolkit dependencies: direct, transitive, per-toolkit usage breakdown, and all detected issues |
| `where-used` | `--mode where-used --toolkit "<name>"` | Finds every artifact in the process app that references items from the named toolkit |
| `what-uses` | `--mode what-uses --toolkit "<name>"` | Shows which toolkit items (types, coach views, services) are consumed by the named artifact |

## Issues detected

| Issue | Symbol | Description |
|---|---|---|
| Missing dependency | ❌ | An artifact references a toolkit item not declared as a dependency |
| Snapshot conflict | ⚠️ | Two direct dependencies pull in different snapshots of the same transitive toolkit |
| Circular dependency | ⚠️ | A dependency chain loops back to a toolkit already in the chain |
| Tip snapshot | ⚠️ | A toolkit is referenced at the `Tip` (live) snapshot rather than a frozen named snapshot |
| Unused (no refs found) | 🔍 | A toolkit is declared but no artifact references any of its exported items — verify before removing |
| Dangling reference | ⚠️ | An artifact references a toolkit item whose toolkit is no longer declared |

## Report outputs

The script writes two files into a `<TWXName> - reports/` folder next to the TWX:

| File | Description |
|---|---|
| `toolkit-dependency-report.md` | Human-readable report read and presented by the skill |
| `toolkit-dependency-report.json` | Machine-readable full report for further processing |

The skill also offers to save the Mermaid dependency diagram as a standalone `.mmd` file on request.

