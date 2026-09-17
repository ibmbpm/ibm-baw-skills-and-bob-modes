# BAW Dependency Mapper — Documentation

> Maps all usages and dependencies of a specified variable or Business Object (BO) across an entire IBM® BAW process application by analyzing the TWX export.

## Purpose

The BAW Dependency Mapper skill takes a BAW process application TWX export file and a target variable or Business Object (BO) name, then produces a complete dependency map showing every artifact that declares, reads, writes, or binds to that target. It detects circular BO references, over-coupling, redundant service calls, orphaned and write-only variables, missing output mappings, stale coach bindings, and read-before-write ordering problems. It also generates an impact assessment for common change scenarios (add field, remove field, rename field, delete BO, change field type).

Use this skill when you need to understand the ripple effect of a proposed BO change, audit a process app for data quality issues, or build a complete picture of where a specific BO or variable is consumed across services, processes, and coaches.

## Setup and configuration

- Python 3 must be available on the system PATH. The analysis script (`scripts/analyze_dependencies.py`) uses Python standard library only — no `pip install` is needed.
- The `.twx` file must already exist on disk. Exporting or downloading the TWX from Workflow Center or Process Designer is outside the scope of this skill; provide the local file path before invoking it.
- No MCP server, API key, or external service is required.

## Compatibility

- Analysis is performed against the static TWX export artifacts. The TWX format is a ZIP archive containing XML and embedded JSON as produced by IBM® BAW (standalone) and IBM Cloud Pak for Business Automation (CP4BA). Both deployment targets use the same TWX structure.
- Cross-toolkit usages are **not** analyzed — only artifacts inside the current process app's `objects/` folder are scanned. If the target BO is defined in a toolkit dependency, declare that toolkit's TWX separately.
- IBM does not publish a formal XML schema for TWX internals; the script uses heuristics validated against real exports. Confirm results against the actual artifacts before making critical decisions.

## Prompt examples

### Map all usages of a Business Object

**Prompt:**
> I have a BAW process app exported to `C:/exports/ClaimsApp.twx`. Map every place the `ClaimRequest` business object is declared, read, written, used as a service parameter, or bound to a coach UI control. Also flag any circular BO references.

**What to expect:** A full 10-section dependency report including a Mermaid diagram, usage tables for declarations/reads/writes/service bindings/coach bindings, a detected-issues section with any circular reference warnings, and an impact assessment for add/remove/rename/delete scenarios.

---

### Impact assessment for a field removal

**Prompt:**
> My process app is at `/projects/HR/HiringApp.twx`. I'm considering removing the `salary` field from the `CandidateProfile` business object. What artifacts would break?

**What to expect:** A targeted impact assessment showing which services and coaches must be updated, which are safe, and a risk level (Low/Medium/High) based on the number of write consumers and coach bindings.

---

### Circular dependency check

**Prompt:**
> I think the data model in `C:/exports/claims-v2.twx` has circular BO references. Check the `ClaimHeader` business object for any type-reference loops.

**What to expect:** The issues section prominently lists each detected cycle with the full type chain (e.g., `ClaimHeader → ClaimLine → ClaimHeader`) using `⚠️` markers, or clearly states that no cycles were found.

---

### Over-coupling analysis for a qualified variable

**Prompt:**
> Analyze `tw.local.orderRequest` in `OrderFulfillment.twx`. I suspect too many services are modifying it — five of them seem to write to it.

**What to expect:** An over-coupling warning listing all write-service names with a recommendation to split responsibilities, plus the full dependency graph for `orderRequest` across the process app.

---

### Data quality audit

**Prompt:**
> Check `InvoiceApp.twx` for data quality issues on the `InvoiceRequest` BO. I want to know about orphaned variables, write-only variables, missing output mappings, unused BO type definitions, and stale coach bindings.

**What to expect:** The issues section covers all six detector categories — orphaned variables (`🔍`), write-only variables (`⚠️`), missing output mappings (`⚠️`), unused BO type (`⚠️`), stale coach bindings (`⚠️`), and read-before-write (`⚠️`/`🔍`) — with specific artifact names for each finding.

---

### List all Business Objects in a process app

**Prompt:**
> What business objects are defined in `C:/exports/ClaimsApp.twx`? I want to run a dependency analysis on each one.

**What to expect:** A printed list of every BO type name found in the TWX, one per line, which you can then use as individual analysis targets.

---

### Missing TWX file (out-of-scope redirect)

**Prompt:**
> I haven't exported my process app yet — can you analyze its BO dependencies anyway?

**What to expect:** The skill asks you to provide the path to the `.twx` export file before proceeding, explains that analysis requires the file to already exist on disk, and does not suggest REST or live-runtime alternatives (those cannot return variable read/write detection, coach bindings, or sequence flow graphs).

---

## Report sections

Every analysis produces the following sections in order:

| # | Section | Description |
|---|---------|-------------|
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

### Issue detectors

| Icon | Detector | What it flags |
|------|----------|---------------|
| ⚠️ | Circular BO reference | BO type A references B which transitively references A |
| ⚠️ | Over-coupling | More than `threshold` (default 3) distinct services write to the same BO |
| 🔍 | Redundant service call | Two or more services in the same flow both consume the same BO without a write between them |
| 🔍 | Orphaned variable | Declared but never read or written via script in the same artifact |
| ⚠️ | Write-only variable | Written by at least one service but never read downstream |
| ⚠️ | Missing output mapping | Service activity accepts the BO as input but has no output mapping back to the caller |
| ⚠️ | Unused BO type | BO is defined but no variable or service parameter ever uses it as a type |
| ⚠️ | Stale coach binding | Coach binds to a field path that does not exist in the BO definition |
| ⚠️/🔍 | Read before write | Activity reads the target before any writing activity has been reached on every inbound flow path |

## Output files

The script writes two files into a `<TWXName>.twx - reports/` folder next to the TWX (the same folder used by the `baw-endpoint-validation` skill, so all reports for a given TWX are co-located):

- **`<TargetName>-dependency-report.md`** — human-readable report in the 10-section format above.
- **`<TargetName>-dependency-report.json`** — machine-readable version of the same data.

After presenting the report, the skill offers to also save the Mermaid diagram as a standalone `.mmd` file.

## Diagram node conventions

| Artifact type | Mermaid shape | Example |
|---------------|---------------|---------|
| Business Object | `(("label"))` circle | `bo(("ClaimRequest\n[bo]"))` |
| Process (BPD) | `["label"]` rectangle | `proc["ClaimsHandling\n[process]"]` |
| Service flow | `>"label"]` flag | `svc>"ValidateClaim\n[service]"]` |
| Coach | `{"label"}` diamond | `cch{"SubmitClaim\n[coach]"}` |

Coach bindings use dashed edges (`-.->|"binds"|`); all other edges are solid.

## Out of scope

| Request | Redirect |
|---------|----------|
| Exporting or downloading the TWX | Must be done manually in Workflow Center or Process Designer |
| Live runtime analysis of a running instance | Static-export analysis only; runtime data flows are not observable |
| Generating or modifying Business Objects | Use the `generate-baw-business-objects` skill |
| Generating or modifying BPMN processes | Use the `generate-baw-bpmn` skill |
| TWX packaging or deployment | Not covered by this skill |
| Analyzing toolkit-defined BOs from a dependency | Export that toolkit's TWX separately and run a second analysis |

---
