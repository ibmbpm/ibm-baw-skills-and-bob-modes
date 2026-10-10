---
name: baw-toolkit-analyzer
description: 'Analyzes IBM BAW toolkit dependencies from a TWX export. Maps direct and transitive toolkit dependencies, tracks snapshot versions, and flags missing, conflicting, circular, outdated, and unused dependencies. Supports where-used (what artifacts reference a toolkit) and what-uses (what toolkits an app consumes) analysis. Use when a BAW admin or developer needs to understand toolkit structure, assess upgrade impact, audit before deployment, or answer questions like "what toolkits does this app depend on?", "is this toolkit safe to remove?", "do I have circular toolkit deps?". Trigger phrases: toolkit dependencies, toolkit dependency graph, where is this toolkit used, analyze toolkit, toolkit impact, missing toolkit, circular toolkit, outdated snapshot, unnecessary dependency, toolkit analyzer, TWX toolkit.'
license: Apache-2.0
compatibility: "IBM BAW 22.x and later; IBM CP4BA 22.x and later"
allowed-tools:
  - Read
  - Edit
  - Bash
metadata:
  version: "1.0.0"
  display_name: BAW Toolkit Analyzer
  short_description: Map direct and transitive toolkit dependencies in a BAW TWX export and flag missing, circular, conflicting, and unused dependencies.
  author: IBM BAW Team
---

# BAW Toolkit Dependency and Usage Analyzer

Analyse the toolkit dependencies inside a BAW process application TWX export and produce a full dependency report: direct and transitive dependencies, snapshot tracking, conflict and gap detection, and impact assessment.

## Input requirements

Before running the script, collect from the user:

1. **Process app and snapshot** — the process app acronym and snapshot acronym to analyse. If the user does not know the acronym, ask for the process app name or URL and resolve it via the export API.
2. **Analysis mode** — one of:
   - `full` (default) — maps all toolkit dependencies for the process app in the TWX.
   - `where-used <toolkit-name>` — finds which artifacts inside the process app reference items from the named toolkit.
   - `what-uses <artifact-name>` — shows which toolkit items (types, coach views, services) are consumed by the named artifact in the process app.
3. **Optional: target toolkit name** — required for `where-used` and `what-uses` modes.

If the process app / snapshot is missing, ask for it before proceeding. If the user already has a `.twx` file on disk, they may provide the path instead — in that case skip the TWX acquisition step.

## Steps

### 1. Confirm inputs

Use `ask_followup_question` for any missing required input. Ask one question at a time.

### 2. Acquire the TWX

Use the first path that succeeds.

**Path 1 — Export API (preferred)**

Ask for the server URL and credentials only at this point, immediately before making the login call — do not ask earlier:
> *"To export the app artifacts I'll need your BAW server URL and credentials — these are only used to get a session token for this conversation and are not stored."*

#### Step A — Determine the context root

The login endpoint path varies by deployment type:

| Deployment | Login endpoint |
|---|---|
| Standalone BAW | `{BAW_BASE_URL}/ops/system/login` |
| CP4BA / Cloud Pak (common) | `{BAW_BASE_URL}/bas/ops/system/login` |
| CP4BA alternate context roots | `{BAW_BASE_URL}/baw/ops/system/login`, `{BAW_BASE_URL}/bpm/ops/system/login` |

If the user has not told you the deployment type, probe the known paths in order with a GET request (expect 401, not 404) to discover the active context root. Store it as `{CTX}` (e.g. `/bas`). All subsequent REST calls use `{BAW_BASE_URL}{CTX}/...`.

#### Step B — Login

Call `POST {BAW_BASE_URL}{CTX}/ops/system/login` with `Authorization: Basic <base64(user:pass)>`, `Content-Type: application/json`, body `{"refresh_groups": false}`. On HTTP 201 store `csrf_token` as `{BAW_CSRF}` and all `Set-Cookie` values (`LtpaToken2`/`JSESSIONID` or their prefixed equivalents such as `basLtpaToken2`/`BAS-JSESSIONID`) as `{BAW_SESSION}` — send both on all subsequent REST calls.

Use **Python (`requests`)** for all HTTP calls — it works on Windows, macOS, and Linux without any shell-specific setup. For environments with self-signed or private CA certificates (typical in CP4BA on-prem), disable certificate verification:

```python
requests.post(..., verify=False)
```

Suppress the resulting `InsecureRequestWarning` by calling `urllib3.disable_warnings()` at the top of every script block.

If login returns 401/400, ask the user to re-enter credentials.

#### Step C — Resolve container and version acronyms

If the user provided an acronym (e.g. `TAT`) and snapshot, skip to Step D. Otherwise:

1. **List containers:**
   ```
   GET {BAW_BASE_URL}{CTX}/ops/std/bpm/containers
   ```
   Match `container_name` against the app name the user gave. Record the `container` (acronym) field as `{CONTAINER}`.

2. **List versions:**
   ```
   GET {BAW_BASE_URL}{CTX}/ops/std/bpm/containers/{CONTAINER}/versions
   ```
   Pick the most recent non-archived version. Record its `version` field as `{VERSION}`. If there are multiple snapshots, show the user a brief table and ask which to export.

#### Step D — Export the TWX

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

The response is a binary `.twx` file (a ZIP). Get the system temp directory:

```python
python -c "import tempfile; print(tempfile.gettempdir())"
```

Save as `<temp_dir>/<CONTAINER>_<VERSION>.twx` and use that path as `<path-to-file.twx>` in all subsequent steps.

If the export returns 403/404, re-check `{CONTAINER}` and `{VERSION}` via the listing calls in Step C.

**Path 2 — Local file (fall back after Path 1 has visibly failed)**

If the REST export fails or errors more than once, offer:
> *"If you already have the `.twx` file for this app on your machine, you can point me to it and I'll work from that directly — no server connection needed for this step."*

If the user provides a path, use it directly as `<path-to-file.twx>`. Do not ask for a file path pre-emptively — only after a real failure.

### 3. List toolkits (optional discovery)

To list all toolkits found in the TWX before the user chooses a target, run:

```bash
python <skills_directory>/baw-toolkit-analyzer/scripts/analyze_toolkit_deps.py \
  "<path-to-file.twx>" \
  --list-toolkits
```

This prints one toolkit name (with snapshot) per line and exits. Offer this as a discovery step when the user hasn't named a target.

### 4. Run the analysis script

```bash
python <skills_directory>/baw-toolkit-analyzer/scripts/analyze_toolkit_deps.py \
  "<path-to-file.twx>" \
  [--mode full|where-used|what-uses] \
  [--toolkit "<toolkit-name>"]
```

The script derives the output directory from the TWX filename automatically (e.g. `C:/exports/ClaimsApp.twx` → `C:/exports/ClaimsApp.twx - reports/`) and creates it if it does not exist.

The script writes:
- `toolkit-dependency-report.json` — machine-readable full report.
- `toolkit-dependency-report.md` — human-readable markdown report.

### 5. Read the output

Read the generated markdown report with `read_file` before presenting any results.

### 6. Present the report

Structure the response using the sections below for the active mode.

#### full mode

**Summary** — one paragraph: process app name, total toolkit count (direct / transitive), issues found, recommended next step.

**Dependency graph** — Mermaid diagram with the process app at the root. Use directed edges (`-->`) to show "depends on"; label edges `direct` or `via <toolkit>` for transitive. Cap at 25 nodes; note omissions if truncated.

```
graph TD
  AppA["Process App\n(v1.2)"] -->|direct| TK1["Toolkit A\n(snapshot: 2024-11)"]
  AppA -->|direct| TK2["Toolkit B\n(snapshot: 2025-01)"]
  TK2 -->|via Toolkit B| TK3["Toolkit C\n(snapshot: 2024-06)"]
```

**Direct dependencies overview table**

| Toolkit Name | Acronym | Referenced Snapshot | Usage Status | Issues / Notes |
|---|:---:|:---:|:---:|---|
| **System Data** | `TWSYS` | `8.6.0.0_TC` | ✅ **In Use** | Healthy |

Columns:
- **Toolkit Name** — display name of the toolkit.
- **Acronym** — short name (e.g., `TWSYS`, `SYSBPMUI`).
- **Referenced Snapshot** — snapshot version referenced.
- **Usage Status** — `✅ In Use` or `🔍 No direct refs`.
- **Issues / Notes** — `Healthy`, `⚠️ Snapshot Conflict`, or `Unused (no refs found — verify before removing)`.

**Toolkit usage breakdown** — per-toolkit two-column table:

| Where Used (Process App Item) | What It Uses from Toolkit |
|---|---|
| **Service flow** <br><sub>Type: Service Flow</sub> | • Business Object / Variable Type: `String`<br>• Participant: `System`<br>• Service Flow / Process: `Default BPD Event` |
| **Client-side human service** <br><sub>Type: Client-Side Human Service</sub> | • Coach View: `Button` |

**Transitive dependencies** — toolkit dependencies pulled in indirectly via embedded toolkit ZIPs, showing the direct parent toolkit and snapshot.

**Issues detected** — circular dependencies, snapshot version conflicts, tip snapshot references, unused dependencies. State explicitly if none are found.

**Actionable recommendations** — concrete steps to resolve conflicts, align snapshot versions, or remove unused toolkits.

#### where-used mode

Present a single table grouping all references to the target toolkit across every artifact that uses it:

| Artifact (Name · Type) | What It Uses from Toolkit |
|---|---|
| **ValidateCustomer** <br><sub>Type: Service Flow</sub> | • Variable Type: `CustomerRecord`<br>• Service: `LookupCustomer` |
| **ApprovalForm** <br><sub>Type: Client-Side Human Service</sub> | • Coach View: `CustomerSummary` |

If no references are found, say so explicitly and note that the toolkit may be unused (verify before removing).

#### what-uses mode

Present a two-column table listing every toolkit item consumed by the named artifact:

| Toolkit | Item Used |
|---|---|
| **Customer Utilities** (`CU`) | • Coach View: `CustomerSummary`<br>• Variable Type: `CustomerRecord` |
| **System Data** (`TWSYS`) | • Variable Type: `String`<br>• Participant: `System` |

If the artifact has no cross-toolkit references, say so explicitly.

---

## Issues: Missing dependencies

A toolkit is referenced in artifact code (e.g. a service call, BO field type, variable type) but does not appear in the process app's declared dependency list. Flag with ❌.

> ❌ **Missing dependency:** `Customer Utilities` is referenced in `ValidateCustomer` (service task) but is not declared as a dependency of this process app.

---

## Issues: Conflicting dependencies

Two direct dependencies both pull in different snapshots of the same transitive toolkit. The dependency may resolve unpredictably at runtime, which can produce inconsistent behavior.

> ⚠️ **Conflict:** `Toolkit A (2024-11)` and `Toolkit B (2025-01)` both declare a dependency on `Shared Utils`, but at different snapshots (`2024-06` vs `2025-03`). Resolve by aligning both to the same snapshot.

---

## Issues: Circular dependencies

Toolkit A depends on Toolkit B, which depends on Toolkit A (directly or transitively). Circular toolkit references may cause deployment failures or unpredictable behavior.

> ⚠️ **Circular dependency:** `Toolkit A` → `Toolkit B` → `Toolkit A`

Report each cycle once; do not repeat shared sub-paths.

---

## Issues: Tip snapshot references

The process app references a toolkit via the `Tip` (latest) snapshot rather than a frozen named snapshot. Any future change to that toolkit — including breaking changes — will be picked up automatically, which is a risk in production environments.

> ⚠️ **Tip snapshot:** `Customer Utilities` is referenced at `Tip`. Pin to a named snapshot before promoting to production.

---

## Issues: Unused dependencies (no references found)

A toolkit appears in the dependency list but no artifact in the process app references any exported item from it (type, service, variable, coach view, etc.). This may be a cleanup opportunity, though the dependency may have been required by a since-deleted artifact.

> 🔍 **Unused (no references found):** `Legacy Utilities` is declared as a dependency but no artifact in this process app references it. Verify in Process Designer before removing.

---

## Output file

After presenting all sections, offer to save the Mermaid diagram as a standalone `.mmd` file, or the full report as a separate markdown file.

---

## Boundaries

**In scope:**
- Toolkit dependency mapping (direct and transitive) from a TWX export.
- Snapshot tracking and Tip-reference detection.
- Missing, conflicting, circular, outdated, and unused dependency detection.
- "Where used" and "what this uses" analysis.
- Impact assessment for toolkit snapshot changes or removal.

**Out of scope — redirect clearly:**
- **Updating toolkit dependencies at runtime.** Changing which toolkit snapshot a process app references must be done in Process Designer.
- **Variable or Business Object dependency mapping within a single process app.** Use `baw-dependency-mapper`.
- **Generating or modifying BPMN processes or BOs.** Use `generate-baw-bpmn` / `generate-baw-business-objects`.
- **TWX packaging or deployment.**

## Reference files

- **`references/TWX_TOOLKIT_STRUCTURE.md`** — XML element paths and attribute names for toolkit dependencies, snapshot references, and artifact cross-references inside a TWX archive.
