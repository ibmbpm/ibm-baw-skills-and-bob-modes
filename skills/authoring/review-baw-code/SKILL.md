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
compatibility: "IBM BAW 22.x and later; IBM CP4BA 22.x and later"
allowed-tools:
  - Read
  - Edit
  - Bash
metadata:
  version: "1.0.0"
  display_name: BAW Code Review
  short_description: Automated severity-ranked code quality review of IBM BAW artifacts — scripts, coaches, and services — from an uploaded TWX file.
  author: IBM BAW Team
---
# Review BAW code

Scan JavaScript artifacts extracted from a BAW TWX application and produce a
severity-ranked findings report. The goal is to surface real issues before deployment —
hardcoded values that break across environments, variables used before the script declares them,
logging that makes incidents hard to diagnose, and patterns that degrade runtime
performance.

The review runs in three stages: **collect** artifacts (scripts, HTML, CSS, optionally
a Checkstyle XML), **analyze** each one against the default rule set (extended by any
user-supplied rules), then **report** findings grouped by severity.

Read `references/RULES.md` for the complete rule definitions, severity rationale, and
recommended-fix templates. Refer back to it whenever you need to classify or explain a
finding.


## Credentials

Never prompt the user for credentials. Credentials are only needed when making a REST call.
When a REST call is about to be made, read `references/CREDENTIAL_HANDLING.md` and follow it — it will read credentials from `.env` automatically, and only prompt the user if a value is missing from that file. Do this once per session only.

---

---

## Stage 0 — Obtain the TWX artifacts

Before Stage 1 can begin, the TWX contents must be available locally. Work through the
following paths in order — stop at the first that succeeds.

### Path 1 — REST export (preferred)

Read credentials from `references/CREDENTIAL_HANDLING.md`. If the container acronym or snapshot version is not yet known, ask the user before calling the export endpoint.

**Step 1 — Download the TWX:**

```bash
TWX_WORKDIR=/tmp/twx-review
mkdir -p "$TWX_WORKDIR"

curl -sk \
  -H "Authorization: Basic <base64(BAW_USERNAME:BAW_PASSWORD)>" \
  -H "BPMCSRFToken: {BAW_CSRF}" \
  -b /tmp/baw_cookies.txt \
  "{BAW_BASE_URL}/ops/std/bpm/containers/<container>/versions/<version>/export?use_enhanced_filenames=true" \
  -o "$TWX_WORKDIR/app.twx"
```

If the download returns a non-200 HTTP status or the saved file is empty, report the
error and fall through to Path 2.

**Step 2 — Extract:**

```bash
unzip -q "$TWX_WORKDIR/app.twx" -d "$TWX_WORKDIR"
```

Non-zero exit means the download was not a valid ZIP (the file is corrupt, or curl
saved an error page instead). Report the error and fall through to Path 2.

### Path 2 — Uploaded or local TWX file (fallback)

Offer this path only after Path 1 has visibly failed (authentication error, server
unreachable, or failed extraction) — do not offer it pre-emptively:

> *"If you already have the `.twx` file for this app on your machine, you can upload it
> or give me its path, and I work from that directly — this step needs no server
> connection."*

When the user provides a file path or uploads a file, run:

```bash
TWX_WORKDIR=/tmp/twx-review
mkdir -p "$TWX_WORKDIR"
unzip -q "<file_path>" -d "$TWX_WORKDIR"
```

Non-zero exit means corrupt or password-protected archive — tell the user and stop.

### Path 3 — Pre-extracted folder or pasted scripts

If neither Path 1 nor Path 2 is possible (no server access, no TWX file), the user can
point you at an already-extracted folder or paste script content directly. Move straight
to Stage 1 — no extraction needed.

---

Once extraction succeeds (Path 1 or 2), hand the extracted directory (`/tmp/twx-review`)
to Stage 1 as the artifact source, exactly as if the user had pointed you at an extracted
folder (method 2 in Stage 1).

After the review is complete, clean up:

```bash
rm -rf "$TWX_WORKDIR"
```

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

For method 2 or 4, read each file before analyzing it — never analyze code you have not
read. If the directory is large (>50 files), confirm the scope with the user before
reading everything: *"The directory contains 62 JS files. Should I review all of them, or focus on a
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
  For every `tw.local.*` reference, check whether the script assigns or declares the
  variable before first use in the same script scope. Flag reads before writes.
  Flag variables assigned but never subsequently read.

- **Logging pattern (LOG-*)**  
  Identify the project's dominant logging idiom (for example, `log.info(...)`, `tw.system.log`,
  `console.log`, a custom `logger.*` wrapper). Any artifact that uses a different idiom
  or mixes idioms in the same script is inconsistent. Flag bare `console.log` or
  `log.error` calls that swallow the exception object without including it.

- **Performance (PERF-*)**  
  Flag `java.lang.Thread.sleep(...)` calls (synchronous blocking). Flag `while(true)`,
  `for(;;)`, or any loop for which you cannot statically confirm a bounded termination
  condition (no counter increment, no collection iteration). Flag deeply nested loops
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
`source` attribute (for example, `com.puppycrawl.tools.checkstyle.checks.coding.*`). If no
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
**Checkstyle findings ingested:** Y  (only if the user provides a report)

---

### 🔴 Critical

#### [ARTIFACT_NAME] — line N
**Rule:** HARD-01 — Hardcoded credential
**Finding:** `password = "hunter2"` — the script assigns a string literal directly to a
  variable whose name suggests a credential.
**Fix:** Store credentials in a BAW managed team/environment variable, a process
  variable initialized from a system configuration property, or an external secrets
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

If the user provides a custom rule set (for example, *"also flag any call to
`tw.system.findUser`"* or *"treat DEBUG-level logs as High"*), incorporate those rules
before beginning Stage 2. State explicitly which custom rules you applied.

---

## Iterative reviews

If the user re-submits files after making fixes, compare against the previous report.
Open your previous findings summary from the conversation context, identify which rules
were resolved, and focus the new report on remaining issues and any issues that the
changes introduce.
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
