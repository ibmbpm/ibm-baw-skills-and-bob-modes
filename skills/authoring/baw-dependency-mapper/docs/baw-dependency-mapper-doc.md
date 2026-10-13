# BAW Dependency Mapper — Documentation

> Maps all usages and dependencies of a specified variable or Business Object (BO) across an entire IBM BAW process application by analyzing the TWX export.

## Purpose

This skill takes a BAW process application TWX export and a target variable or Business Object (BO) name, then produces a complete dependency map showing every artifact that declares, reads, writes, or binds to that target. It detects circular BO references, over-coupling, redundant service calls, orphaned and write-only variables, missing output mappings, stale coach bindings, and read-before-write ordering problems, and generates an impact assessment for common change scenarios (add field, remove field, rename field, delete BO, change field type). Use it when you need to understand the ripple effect of a proposed BO change, audit a process app for data quality issues, or build a complete picture of where a specific BO or variable is consumed.

## Setup and configuration

- **Python 3.6+** — required to run `scripts/analyze_dependencies.py`. No external packages are needed; the script uses the standard library only.
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

- Works with both standalone IBM Business Automation Workflow and IBM Cloud Pak for Business Automation (CP4BA) deployments. The TWX format is consistent across both.
- Cross-toolkit usages are **not** analyzed — only artifacts inside the current process app's `objects/` folder are scanned. If the target BO is defined in a toolkit dependency, run a separate analysis against that toolkit's TWX.
- IBM does not publish a formal XML schema for TWX internals; the script uses heuristics validated against real exports. Confirm findings against the actual artifacts before acting on them.
- For environments with self-signed certificates (typical in CP4BA on-prem), TLS verification is disabled automatically during download.

## Prompt examples

### Map all usages of a BO — enumerate first, then analyze

**Prompt:**
> Map the BO dependencies for the OrderFulfillment process app on my BAW server at https://baw.example.com:9443. List all the BOs first so I can pick one.

**What to expect:** Bob downloads the TWX, enumerates all BO types found in the app, prints them, and waits for you to pick a target before running the full analysis.

---

### Full dependency map for a named Business Object

**Prompt:**
> On my BAW server at https://baw.example.com:9443, map every place the `ClaimRequest` business object is declared, read, written, used as a service parameter, or bound to a coach UI control in the ClaimsProcessing app. Also flag any circular BO references.

**What to expect:** A full 10-section report including a Mermaid dependency diagram, declaration, read/write usage tables, service input/output bindings, coach bindings, all detected issues (with circular reference warnings if any), and an impact assessment for add/remove/rename/delete scenarios.

---

### Impact assessment for a field removal

**Prompt:**
> Using https://baw.example.com:9443, for the HiringApp — I'm considering removing the `salary` field from the `CandidateProfile` business object. What would break?

**What to expect:** A targeted impact assessment listing which services and coaches must be updated, which are safe, and a risk level (🟢 Low / 🟡 Medium / 🔴 High) based on the number of write consumers and coach bindings.

---

### Circular BO reference check

**Prompt:**
> Connect to https://baw.example.com:9443 and check the `ClaimHeader` business object in ClaimsProcessing for any type-reference loops.

**What to expect:** Any circular cycles are listed with the full type chain (e.g. `ClaimHeader → ClaimLine → ClaimHeader`) using `⚠️` markers; if no cycles are found, the skill says so explicitly.

---

### Over-coupling analysis

**Prompt:**
> On https://baw.example.com:9443, analyze `tw.local.orderRequest` in the OrderFulfillment app. I suspect too many services are modifying it.

**What to expect:** If more than 3 distinct services write to `orderRequest`, an over-coupling warning lists all their names and recommends splitting responsibilities; the full dependency graph is also shown.

---

### Data quality audit

**Prompt:**
> Check `C:/exports/InvoiceApp.twx` for data quality issues on the `InvoiceRequest` BO — orphaned variables, write-only variables, missing output mappings, unused BO type definitions, and stale coach bindings.

**What to expect:** The issues section covers all six detector categories with specific artifact names for each finding — `🔍` for candidates requiring manual confirmation, `⚠️` for confirmed problems.

---

### Work from a local TWX file

**Prompt:**
> I have a BAW process app exported to `C:/exports/ClaimsApp.twx`. Map every place the `ClaimRequest` business object is used — declarations, reads, writes, service parameters, and coach bindings.

**What to expect:** Bob works directly from the file on disk — no server connection needed — and produces the same full dependency report.

---

## Report sections

Every analysis produces the following sections in this order:

| # | Section | Description |
|---|---|---|
| 1 | Summary | One-paragraph description of what was found |
| 2 | Dependency graph | Mermaid `flowchart LR` diagram (capped at 20 nodes for large apps) |
| 3 | Declarations | Where and how the target is declared |
| 4 | Read usages | Artifacts that read the target |
| 5 | Write usages | Artifacts that write to the target |
| 6 | Service input bindings | Services whose input parameter maps to the target BO type |
| 7 | Service output bindings | Services whose output parameter maps to the target BO type |
| 8 | Coach bindings | Coaches binding UI controls to the target's properties |
| 9 | Issues detected | All detector findings (see below) |
| 10 | Impact assessment | Risk-rated analysis per change type |

## Issue detectors

| Icon | Detector | What it flags |
|---|---|---|
| ⚠️ | Circular BO reference | BO type A references B which transitively references A |
| ⚠️ | Over-coupling | More than `threshold` (default 3) distinct services write to the same BO |
| 🔍 | Redundant service call | Two or more services in the same flow both consume the same BO without a write between them |
| 🔍 | Orphaned variable | Declared but never read or written via script in the same artifact |
| ⚠️ | Write-only variable | Written by at least one service but never read downstream |
| ⚠️ | Missing output mapping | Service activity accepts the BO as input but has no output mapping back to the caller |
| ⚠️ | Unused BO type | BO is defined but no variable or service parameter uses it as a type |
| ⚠️ | Stale coach binding | Coach binds to a field path that does not exist in the BO definition |
| ⚠️/🔍 | Read before write | Activity reads the target before any writing activity has been reached on every inbound flow path |

## Diagram node conventions

| Artifact type | Mermaid shape | Example |
|---|---|---|
| Target BO/variable | `["label"]` rectangle | `target["ClaimRequest"]` |
| Business Object | `(("label"))` circle | `bo(("ClaimRequest\n[bo]"))` |
| Process (BPD) | `["label"]` rectangle | `proc["ClaimsHandling\n[process]"]` |
| Service flow | `>"label"]` flag | `svc>"ValidateClaim\n[service]"]` |
| Coach | `{"label"}` diamond | `cch{"SubmitClaim\n[coach]"}` |

Coach bindings use dashed edges (`-.->|"binds"|`); all other edges are solid.

## Output files

The script writes two files into a `<TWXName>.twx - reports/` folder next to the TWX:

- **`<TargetName>-dependency-report.md`** — human-readable report in the 10-section format above.
- **`<TargetName>-dependency-report.json`** — machine-readable version of the same data.

After presenting the report, the skill offers to save the Mermaid diagram as a standalone `.mmd` file.

