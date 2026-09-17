---
name: review-baw-code
description: >
  Perform automated, severity-ranked code quality reviews across IBM BAW artifacts —
  server scripts, coach (client-side) scripts, integration service scripts, HTML, CSS,
  and optionally a Checkstyle XML report. Accepts an uploaded .twx file directly and
  extracts it automatically. Flags hardcoded values (URLs, credentials, IPs), undeclared
  tw.local.* variables, inconsistent error-logging patterns, synchronous Thread.sleep
  calls, unbounded loops, and other performance anti-patterns. Each finding includes the
  artifact name, line/location, rule violated, severity (Critical / High / Medium / Low),
  and a recommended fix. Use whenever a BAW developer says "review my scripts", "check
  for hardcoded values", "find unused variables", "audit my BAW code", "analyze my TWX
  artifacts", "run a code review before deployment", uploads a .twx file, or provides a
  Checkstyle report to ingest. Also triggers when the user mentions code quality, code
  smell, anti-patterns, or performance issues in BAW artifacts.
license: Apache-2.0
metadata:
  version: 1.0.0
permissions:
  file_upload: true
---

# Review BAW Code

Scan JavaScript artifacts extracted from a BAW TWX application and produce a
severity-ranked findings report. The goal is to surface real issues before deployment —
hardcoded values that break across environments, variables used before they're declared,
logging that makes incidents hard to diagnose, and patterns that degrade runtime
performance.

The review runs in three stages: **collect** artifacts (scripts, HTML, CSS, optionally
a Checkstyle XML), **analyze** each one against the default rule set (extended by any
user-supplied rules), then **report** findings grouped by severity.

Read `references/RULES.md` for the complete rule definitions, severity rationale, and
recommended-fix templates. Refer back to it whenever you need to classify or explain a
finding.

---

## Stage 0 — Unzip an uploaded .twx file (if provided)

If the user uploads a `.twx` file, handle it before Stage 1:

1. The tool saves the uploaded file to a temporary path on disk. Use `execute_command` to
   unzip it into a fixed, well-known working directory (the destination is always
   `/tmp/twx-review` — it is never derived from user input):
   ```bash
   TWX_WORKDIR=/tmp/twx-review
   unzip -q "<uploaded_file_path>" -d "$TWX_WORKDIR"
   ```
2. Confirm the unzip succeeded (non-zero exit = corrupt or password-protected archive —
   tell the user and stop).
3. Hand the extracted directory (`/tmp/twx-review`) to Stage 1 as the artifact source,
   exactly as if the user had pointed you at an extracted folder (method 2 in Stage 1).
4. After the review is complete, clean up using the same variable to avoid any ambiguity:
   ```bash
   rm -rf "$TWX_WORKDIR"
   ```

If no `.twx` file was uploaded, skip this stage entirely.

---

## Stage 1 — Collect artifacts

Artifacts arrive in one of four ways:

1. **Files pasted or attached in the chat** — treat each paste as a named artifact
   (ask the user for the artifact name / script path if not obvious).
2. **A directory of extracted TWX content** — the user points you at a folder produced
   by the `extract-twx` tool or a manual unzip of the `.twx` file. Use `list_files` /
   `glob` to discover all `.js`, `.html`, `.css`, and `.xml` (Checkstyle) files under
   that directory.
3. **A Checkstyle XML report** — the user provides a `checkstyle-result.xml` (or
   similar). Parse it alongside any scripts; see Stage 2 → Checkstyle ingestion.
4. **Explicit file paths** — the user lists specific files to review.

For method 2 or 4, read each file before analyzing it — never analyze code you haven't
read. If the directory is large (>50 files), confirm the scope with the user before
reading everything: *"I found 62 JS files. Shall I review all of them, or focus on a
specific folder?"*

---

## Stage 2 — Analyze each artifact

Apply every rule in `references/RULES.md` to each artifact. For JavaScript artifacts
(server scripts, coach scripts, integration service scripts) apply all JS rules. For
HTML artifacts apply HTML rules. For CSS apply CSS rules.

### Pattern-matching guidance

Work through each artifact top-to-bottom. For each line (or block):

- **Hardcoded values (HARD-*)**  
  Look for string literals that resemble URLs (`http://`, `https://`, `ftp://`),
  IP addresses (`\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}`), credentials
  (variable names containing `password`, `passwd`, `secret`, `apikey`, `token` assigned
  a string literal), and environment-specific hostnames or port numbers.

- **Variable discipline (VAR-*)**  
  For every `tw.local.*` reference, check whether the variable was assigned or
  declared before first use in the same script scope. Flag reads before writes.
  Flag variables assigned but never subsequently read.

- **Logging pattern (LOG-*)**
  Identify the project's dominant logging idiom (e.g. `log.info(...)`, `tw.system.log`,
  `console.log`, a custom `logger.*` wrapper). Any artifact that uses a different idiom
  or mixes idioms in the same script is inconsistent. Flag bare `console.log` or
  `log.error` calls that swallow the exception object without including it.

- **Performance (PERF-*)**  
  Flag `java.lang.Thread.sleep(...)` calls (synchronous blocking). Flag `while(true)`,
  `for(;;)`, or any loop whose termination condition cannot be statically determined to
  be bounded (no counter increment, no collection iteration). Flag deeply nested loops
  (3+ levels) as a Medium finding.

- **General quality (QUAL-*)**  
  Flag empty catch blocks `catch(e){}`. Flag unreachable code after a `return` or
  `throw`. Flag `eval()` calls. Flag inline `style=` attributes in HTML coach views.
  Flag `!important` in CSS.

Capture each finding as:
```
{artifact, line_or_location, rule_id, severity, description, recommended_fix}
```

If you are unsure whether something is a real violation or a false positive, err on
the side of reporting it at the lower severity and add a note in `recommended_fix` that
the developer should verify.

### Checkstyle XML ingestion

If a Checkstyle report is present, read it and extract every `<error>` element. Map
each Checkstyle finding to its closest rule from `references/RULES.md` using the
`source` attribute (e.g. `com.puppycrawl.tools.checkstyle.checks.coding.*`). If no
mapping exists, still surface the finding under a synthetic rule ID `CS-<source_suffix>`
with the Checkstyle severity verbatim. Add the Checkstyle findings to the same findings
list before sorting by severity.

---

## Stage 3 — Report findings

Present the report in this exact structure. Do not emit raw JSON — the output is for
humans.

```
## BAW Code Review Report
**Artifacts reviewed:** N files (list them)
**Total findings:** X  (Critical: A  High: B  Medium: C  Low: D)
**Checkstyle findings ingested:** Y  (only if a report was provided)

---

### 🔴 Critical

#### [ARTIFACT_NAME] — line N
**Rule:** HARD-01 — Hardcoded credential
**Finding:** `password = "hunter2"` — a string literal is assigned directly to a
  variable whose name suggests a credential.
**Fix:** Store credentials in a BAW managed team/environment variable, a process
  variable initialised from a system configuration property, or an external secrets
  manager. Never hardcode them in scripts.

---
[repeat for every Critical finding]

### 🟠 High
[findings]

### 🟡 Medium
[findings]

### 🔵 Low
[findings]

---
### Summary table
| Artifact | Critical | High | Medium | Low | Total |
|---|---|---|---|---|---|
| server-script-1.js | 1 | 2 | 0 | 1 | 4 |
| coach-script-2.js | 0 | 1 | 3 | 2 | 6 |
| **Total** | **1** | **3** | **3** | **3** | **10** |
```

After the report, append a **Top 3 recommendations** section — the three highest-impact
changes the developer should tackle first, based on severity and frequency:

```
### Top 3 recommendations
1. **Remove all hardcoded credentials** (HARD-01, Critical, N occurrences)
   Hardcoded credentials are the most common source of BAW environment-portability
   failures and security incidents. Replace with process variables sourced from
   BAW's managed team/environment variable store.

2. …
3. …
```

---

## Handling custom rule sets

If the user provides a custom rule set (e.g., *"also flag any call to
`tw.system.findUser`"* or *"treat DEBUG-level logs as High"*), incorporate those rules
before beginning Stage 2. State explicitly which custom rules you applied.

---

## Iterative reviews

If the user re-submits files after making fixes, compare against the previous report.
Open your previous findings summary from the conversation context, identify which rules
were resolved, and focus the new report on remaining and any newly introduced issues.
Report the delta: *"3 of 7 previous issues resolved; 1 new issue introduced."*

---

## Boundaries

In scope:
- JavaScript artifacts from BAW TWX: server scripts, coach (client-side) scripts,
  integration service scripts.
- HTML and CSS from BAW coach views.
- Checkstyle XML reports mapped to the same finding structure.
- Custom rules supplied by the user in the current conversation.

Out of scope — hand off to the appropriate skill instead:
- **BAW process flow modelling** → `generate-baw-bpmn`
- **BAW runtime process inspection** → `inspect-baw-processes`
- **Business object generation** → `generate-baw-business-objects`
- **Coach widget scaffolding** → `create-baw-widget`
- **TWX packaging / deployment** — not covered by any script-level review skill.

---

## Quick-reference rule IDs

Full definitions (severity rationale, pattern regex, fix templates) are in
`references/RULES.md`. The IDs here are for cross-referencing findings.

| Category | ID | One-line description |
|---|---|---|
| Hardcoded | HARD-01 | Secret or password literal in variable assignment |
| Hardcoded | HARD-02 | Hardcoded URL / hostname |
| Hardcoded | HARD-03 | Hardcoded IP address |
| Hardcoded | HARD-04 | Hardcoded environment-specific port |
| Variables | VAR-01 | `tw.local.*` read before declared/assigned |
| Variables | VAR-02 | `tw.local.*` assigned but never read (unused) |
| Logging | LOG-01 | Inconsistent logging idiom across artifacts |
| Logging | LOG-02 | Exception caught but not included in log call |
| Logging | LOG-03 | Bare `console.log` in production script |
| Performance | PERF-01 | Synchronous `Thread.sleep` call |
| Performance | PERF-02 | Unbounded loop (no deterministic termination) |
| Performance | PERF-03 | Deeply nested loops (3+ levels) |
| Quality | QUAL-01 | Empty catch block |
| Quality | QUAL-02 | `eval()` call |
| Quality | QUAL-03 | Unreachable code after `return` / `throw` |
| Quality | QUAL-04 | Inline `style=` attribute in HTML coach view |
| Quality | QUAL-05 | `!important` in CSS |
