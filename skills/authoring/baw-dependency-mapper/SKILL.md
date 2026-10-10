---
name: baw-dependency-mapper
description: Maps all usages and dependencies of a specified variable or Business Object (BO) across an entire IBM BAW process application by analysing the TWX export. Produces a dependency graph showing declarations, read/write usages, service I/O bindings, and coach bindings; detects circular BO references, redundant service calls touching the same BO, and over-coupling. Use when the user asks to analyse dependencies of a variable or BO, map where a BO is used, detect circular references, assess the impact of changing a BO or variable, or identify over-coupling in a BAW process app. Also triggers on phrases like "where is this BO used", "what would break if I change X", "find all usages of", "dependency map", "circular dependency BAW".
license: Apache-2.0
compatibility: "IBM BAW 22.x and later; IBM CP4BA 22.x and later"
allowed-tools:
  - Read
  - Edit
  - Bash
metadata:
  version: "1.0.0"
  display_name: BAW Dependency Mapper
  short_description: Map all usages of a variable or Business Object across a BAW process app TWX export, with circular-reference and over-coupling detection.
  author: IBM BAW Team
---

# BAW Dependency Mapper

Analyze a BAW process application TWX export and produce a full dependency map for a specified variable or Business Object (BO), together with circular-reference detection, redundancy analysis, and an impact assessment.

The analysis is driven by `scripts/analyze_dependencies.py`.

## Input requirements

Before running the script, collect from the user:

1. **Process app and snapshot** — the process app acronym and snapshot acronym to analyze. If the user does not know the acronym, ask for the process app name or URL and resolve it via the export API. If the user already has a `.twx` file on disk, they may provide the path instead — in that case skip the TWX acquisition step.
2. **Target name** — the variable name or BO type name to analyze (e.g. `ClaimRequest`, `tw.local.invoice`). Accept both the bare BO name and qualified variable references.
3. **Over-coupling threshold** (optional, default 3) — the number of distinct services that write to the same BO above which the skill flags over-coupling.

If the process app / snapshot is missing, ask for it before proceeding. Do not attempt to analyze without the TWX.

## Steps

### 1. Confirm inputs

If the user has not provided the process app / snapshot (or a local TWX path) or the target name, ask using `ask_followup_question`. One question per missing piece.

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

Use **Python stdlib `urllib`** for all HTTP calls — no third-party packages required. Never use PowerShell or `curl` for HTTP; Python is available on all supported platforms and avoids shell quoting and alias incompatibilities. For environments with self-signed or private CA certificates (typical in CP4BA on-prem), disable certificate verification with:

```python
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
# pass ctx= to every urllib.request.urlopen() call
```

If login returns 401/400, ask the user to re-enter credentials.

#### Step C — Resolve container and version acronyms

If the user provided an acronym and snapshot, skip to Step D. Otherwise:

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

### 3. Run the analysis script

If the user asks to analyze **all BOs** in the process app, first enumerate them with:

```bash
python <skills_directory>/baw-dependency-mapper/scripts/analyze_dependencies.py \
  "<path-to-file.twx>" \
  --list-bos
```

This prints one BO name per line and exits. Then run the analysis once for each name returned.

Place the report in a `<TWXName> - reports` subfolder relative to the TWX file — this keeps all reports together and named after their source export:

```bash
python <skills_directory>/baw-dependency-mapper/scripts/analyze_dependencies.py \
  "<path-to-file.twx>" \
  "<TargetName>" \
  [--threshold <N>]
```

The script derives the output directory automatically from the TWX filename (e.g. `C:/exports/ClaimsApp.twx` → `C:/exports/ClaimsApp.twx - reports/`). Do not pass `--output-dir` unless the user has explicitly requested a different location. The directory will be created automatically if it does not exist.

The script writes structured results to `<output-dir>/<TargetName>-dependency-report.json` (machine-readable) and `<output-dir>/<TargetName>-dependency-report.md` (human-readable).

### 4. Read the output

Read the generated markdown report using `read_file` before presenting any results.

### 5. Present the dependency map

Format the report as described in `references/OUTPUT_FORMAT.md`. The sections to always include:

1. **Summary** — one-paragraph description of what was found.
2. **Dependency graph** — a Mermaid diagram showing the target BO/variable at the center, with directed edges to/from each artifact that declares, reads, writes, or binds it (see `references/OUTPUT_FORMAT.md` for node shape conventions). The script trims the diagram to 20 nodes on large process apps; a note in the diagram shows how many nodes were omitted. The full list appears in the tables below the diagram.
3. **Declaration** — where and how the target is declared (process variable, BO type definition, service input/output parameter).
4. **Read usages** — list of artifacts that read the target, with the artifact type and location.
5. **Write usages** — list of artifacts that write to the target, with artifact type and location.
6. **Service bindings** — services whose input or output parameter maps to the target BO type.
7. **Coach bindings** — coaches that bind UI controls to properties of the target.
8. **Issues detected** — circular references, over-coupling indicators, redundant service calls, orphaned variables, write-only variables, missing output mappings, unused BO types, stale coach bindings, and read-before-write (see sections below).
9. **Impact assessment** — plain-English analysis of what would break or need updating if the target were modified (field added, field removed, field renamed, or type deleted).

### 6. Issues: circular references

A circular reference exists when BO type A has a field of type B, and B (directly or transitively) has a field of type A. Report each cycle as an ordered path, e.g.:

> ⚠️ **Circular BO reference:** `OrderHeader` → `OrderLine` → `OrderHeader`

Each circular reference means the BO type hierarchy contains a loop, which can cause serialisation and deep-copy errors at runtime. List each cycle once; do not repeat shared sub-paths.

### 7. Issues: over-coupling

An over-coupling indicator fires when more than `threshold` (default 3) distinct services write to the same BO instance. Report as:

> ⚠️ **Over-coupling:** `ClaimRequest` is written by 5 services (`ValidateClaim`, `EnrichClaim`, `AssignAdjuster`, `CalculatePayout`, `CloseClaim`). Consider splitting responsibilities or introducing a dedicated update service.

### 8. Issues: redundant service calls

A redundant service call is one where two or more services in the same process flow both read the same BO, call out to an external system that returns the same data, and neither modifies the BO between calls. The script flags these as candidates (false-positive rate is non-zero); present them as "candidates for review" rather than definitive redundancies.

### 9. Issues: orphaned variables

An orphaned variable is declared in a process or service with the target as its name or type, but never appears in any script read or write within that same artifact. Flag as a 🔍 candidate — the variable may be populated via service mapping rather than script. Recommend manual confirmation before removing it.

### 10. Issues: write-only variables

A write-only variable is written by at least one service but never read by any other service, coach, or script in the process app. This is a strong signal the data is computed but discarded — a likely dead-code remnant. Flag with ⚠️.

### 11. Issues: missing output mappings

A service activity passes the target BO as input but has no corresponding output mapping for it. Changes made to the BO inside the service will not be propagated back to the calling process when the activity completes. Flag with ⚠️.

### 12. Issues: unused BO types

The target BO is defined in the process app's BO library but no process variable, service parameter, or coach ever uses it as its declared type. Flag with ⚠️ as a cleanup candidate.

### 13. Issues: stale coach bindings

A coach control binds to a field path on the target BO (e.g. `claim.claimantPhone`) that does not exist in the BO definition. The field path will not resolve at runtime. Flag with ⚠️. Note: this check requires the BO definition to be present in the same TWX — bindings to toolkit-defined BOs cannot be checked.

### 14. Issues: read before write

An activity reads the target variable before any activity that writes it has been reached on any flow path from the process start. This typically manifests as a gateway condition or coach pre-population evaluating an uninitialised BO.

The script performs a BFS over the sequence flow graph to determine whether a write node is reachable before each read node on every inbound path. Use icons to distinguish confidence:

- **⚠️** (`likely`) — linear or simple branching flow; no parallel gateways or back-edges detected.
- **🔍** (`candidate`) — parallel gateways or loop back-edges are present; ordering is ambiguous on at least one path. Confirm manually before acting.

If the process graph has no sequence flow edges (e.g. the TWX only exports activity metadata without flow XML), this check produces no results — it does not false-positive.

### 15. Impact assessment

For each proposed change type (add field, remove field, rename field, delete BO, change field type), state:
- Which artifacts require update.
- Which artifacts are safe (read-only consumers of unaffected fields).
- Estimated risk level: **Low** / **Medium** / **High**, based on the number of write consumers and whether the BO appears in coach bindings.

## Boundaries

**In scope:**
- Dependency mapping from a TWX file for any variable or BO type.
- Circular reference detection across the full BO type hierarchy.
- Over-coupling and redundant-call analysis.
- Impact assessment for proposed changes.

**Out of scope — redirect clearly:**
- **Live runtime analysis** — this skill analyzes static export artifacts, not running instances. It cannot observe what data flows through the process at runtime.
- **Generating or modifying BOs** — use `generate-baw-business-objects`.
- **Generating or modifying BPMN processes** — use `generate-baw-bpmn`.
- **TWX packaging or deployment** — not in scope.
- **REST-only dependency mapping** — the TWX export route is used for full static dependency analysis on both standalone BAW and CP4BA.

**Future upgrade path:**
- If a future MCP tool for process-app export becomes available, this boundary should be revisited — it may allow analysis without a TWX file.

## Output format

After presenting all sections, offer to save the Mermaid diagram as a standalone file:

> "Would you like me to save the dependency diagram as a Mermaid `.mmd` file? I can also save a copy of the full report as markdown."

## Reference files

- **`references/TWX_XML_STRUCTURE.md`** — the XML element paths and attribute names the script uses to locate declarations, usages, and bindings inside a TWX archive. Read before modifying the script or interpreting raw XML.
- **`references/OUTPUT_FORMAT.md`** — the exact Mermaid node/edge conventions, section order, and table schemas for the dependency report.
