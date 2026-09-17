---
name: audit-baw-readiness
description: "Evaluates an IBM BAW process application's design for compliance and audit readiness — scores six domains (traceability, separation of duties, access control, SLA/timeliness, data completeness, error handling) and produces a Markdown scorecard with specific gaps and remediation steps. Use when someone says their process needs to be ready for an audit, asks if a process application is compliant, mentions auditors, a compliance team, a regulated industry, SOX, ISO, GDPR, or an internal/external audit, asks whether their process captures enough evidence or has the right controls, or wants to know if a workflow meets compliance requirements. This skill inspects the process design — not running instances. Do not use for finding or acting on live process instances (use inspect-baw-processes) or for authoring new processes (use generate-baw-bpmn)."
license: Apache-2.0
allowed-tools:
  - execute
  - write
  - read
  - fetch
metadata:
  version: "1.0.0"
---

> **⚠️ REST only — MCP is not supported by this skill.** All BAW interactions use the BAW REST API exclusively via HTTP calls to `{BAW_BASE_URL}`. Do not call any MCP tools at any point — regardless of whether an MCP server is connected or not. This skill has no MCP dependency. If you find yourself reaching for an MCP tool, stop and use the REST equivalent from `references/baw-rest.md` instead.

> **⚠️ Hard rule — TWX export is always REST, never MCP.** Even if an Authoring MCP server is connected and its `export_solution` tool is visible in your tool list, do not call it — ever — for this skill. The TWX must always be downloaded via `GET {BAW_BASE_URL}/ops/std/bpm/containers/{container}/versions/{version}/export?use_enhanced_filenames=true`. This applies even when MCP is fully connected. Do not mention the MCP export tool to the user. Do not reason that MCP is "more reliable" — REST is the required transport for this operation, always.

# Audit BAW readiness

Inspect an IBM BAW process application's exported TWX artifact and produce an audit readiness scorecard — a scored gap analysis across six compliance domains that tells the user exactly what needs to be fixed before an audit begins.

This skill is read-only. It exports and analyzes — it never imports, modifies, or writes back to BAW.

---

## Execution mode

This skill operates in **REST mode only**. All calls use the BAW REST API documented in `references/baw-rest.md`.

Before taking any action, confirm `{BAW_BASE_URL}` is known for this session. If not, ask:
> *"What is your BAW server URL? (e.g. `https://baw.example.com:9443`)"*

Store it and never ask again within the same session.

---

## Semantic operations

| Operation | What it does |
|---|---|
| `login` | `POST /ops/system/login` — obtain CSRF token and session |
| `list containers` | `GET /ops/std/bpm/containers` — list all process apps |
| `list versions` | `GET /ops/std/bpm/containers/{container}/versions` — list snapshots for an app |
| `export version` | `GET /ops/std/bpm/containers/{container}/versions/{version}/export?use_enhanced_filenames=true` — download the TWX |

All calls after login require `BPMCSRFToken` header and session cookie.

---

## Audit domains

Read `references/audit-domains.md` before scoring. It defines all six domains, the evidence to look for in the TWX artifacts, and the scoring criteria (Pass / Partial / Fail) for each.

The six domains are:

1. **Traceability** — decisions are captured with who, what, and when
2. **Separation of Duties** — request and approval steps are in separate lanes/teams
3. **Access Control** — lanes are bound to named teams, not open to all users
4. **SLA / Timeliness** — critical activities have timer events or escalation paths
5. **Data Completeness** — business objects capture the fields an auditor would need
6. **Error Handling** — risky service tasks have boundary error events or recovery paths

---

## Steps

### Step 0 — Establish the BAW connection

> **🔒 Security prerequisite — state this before asking for credentials:**
> *"Before we begin, please confirm:*
> - *Your BAW server URL must use **HTTPS** (not HTTP). Do not enter credentials over an unencrypted connection.*
> - *Use a **dedicated service account** with read-only / export permissions rather than a personal or admin account. If you don't have one, ask your BAW administrator to create an account with Workflow Center reader access.*"

Ask for the server URL and credentials together in a single turn:
> *"I need two things to get started:*
> *1. Your BAW server URL (e.g. `https://baw.example.com:9443`)*
> *2. Your BAW username and password*
>
> *Your credentials are only used to obtain a session token for this conversation — they are not stored beyond this session."*

Call `POST {BAW_BASE_URL}/ops/system/login` with:
- `Authorization: Basic <base64(username:password)>`
- `Content-Type: application/json`
- Body: `{"refresh_groups": false}`

On success (HTTP 201): store `csrf_token` from the JSON body as `{BAW_CSRF}`, and the session cookies as `{BAW_SESSION}`. Send `BPMCSRFToken: {BAW_CSRF}` and the session cookie on every subsequent call. Discard the raw credentials immediately.

If login returns 401 or 400, tell the user their credentials were not accepted and ask them to re-enter. Do not proceed until login succeeds.

---

### Step 1 — Identify the process application

If the user named the app, call `list containers` and find the match by name. If the name is ambiguous or not given, present a short numbered list and ask which app they mean. Confirm the acronym before proceeding — never guess one.

---

### Step 2 — Identify the version to assess

Call `list versions` for the identified app. Present the available snapshots in a concise table (Name, Acronym, Created, Active).

If the user does not specify a version, use the most recently activated snapshot and confirm:
> *"I'll assess the latest snapshot: [name] ([acronym]). Is that right?"*

---

### Step 3 — Export the TWX

Call `export version` with `use_enhanced_filenames=true`. This returns a binary `.twx` file (a ZIP archive). Extract the archive in memory.

If export fails:
- **403:** tell the user they may not have sufficient permissions — admin access is typically required for export.
- **404:** the snapshot acronym may be wrong — show what was used and ask them to confirm.
- **Other errors:** show the status code and ask how they'd like to proceed.

If export fails persistently, offer the manual fallback:
> *"If you already have the `.twx` file for this version, you can share the file path and I'll work from that directly."*

Accept local file paths and read them as ZIPs — process them identically to the REST export.

---

### Step 4 — Analyze the artifacts

Parse the extracted XML files from the TWX archive. The TWX is a ZIP of XML files representing process definitions, business objects, service flows, and configuration. Extract:

- **Process definitions** — activities, gateways, sequence flows, swim lanes, boundary events (timers, errors), and their types
- **Business objects** — field names and types from BO definition files
- **Team/lane bindings** — which lanes are assigned to which teams
- **Variables** — process variables and their types
- **Service tasks** — automated steps that call external systems

Present a brief **artifact inventory** before scoring:
```
## Artifact inventory — [Process App Name] ([snapshot])
- Processes found: [N]
- Activities: [N] total ([n] human tasks, [n] service tasks, [n] gateways, [n] events)
- Lanes: [list of lane names]
- Business objects: [list of BO names with field count]
- Timer boundary events: [list, or "none"]
- Error boundary events: [list, or "none"]
```

---

### Step 5 — Score each audit domain

Read `references/audit-domains.md` for the full scoring criteria. For each domain:

1. Apply the evidence checklist against what was found in Step 4.
2. Assign a score: **Pass**, **Partial**, or **Fail**.
3. For any Partial or Fail, record:
   - The specific artifact (activity name, lane name, BO field name)
   - The missing control or gap
   - A concrete remediation recommendation

Do not assign Pass unless all criteria for that domain are met. Do not assign Fail unless no criteria are met — use Partial when some evidence is present but gaps remain.

---

### Step 6 — Write the scorecard

**Overall rating** (compute before writing — do not include this legend in the output file):
- **Pass** — all 6 domains Pass or N/A
- **Needs Attention** — 1 or more Partial, no Fail
- **Not Ready** — 1 or more Fail

Write the scorecard to `reports/[app-acronym]-audit-readiness.md`. Create the `reports/` directory if it does not exist.

**Scorecard format:**

```markdown
# Audit Readiness Scorecard — [Process App Name]
**Snapshot:** [snapshot name] ([acronym])
**Assessed:** [date]
**Overall:** [Pass / Needs Attention / Not Ready]

## Summary

| Domain | Score | Gaps |
|---|---|---|
| Traceability | ✅ Pass | — |
| Separation of Duties | ⚠️ Partial | 1 gap |
| Access Control | ❌ Fail | 2 gaps |
| SLA / Timeliness | ✅ Pass | — |
| Data Completeness | ⚠️ Partial | 1 gap |
| Error Handling | ⚠️ Partial | 2 gaps |

## Gap Details

### [Domain Name]
**Score:** ⚠️ Partial

| # | Artifact | Missing Control | Recommendation |
|---|---|---|---|
| 1 | Task "Submit Request" | Approval step missing from a separate lane | Add a "Manager Approval" task in a dedicated approver lane |

### [Next Domain]
...

## Passing Domains

List each domain that scored Pass with one sentence confirming what evidence was found.
```

After writing the file, tell the user:
> *"Scorecard written to `reports/[filename].md`. [N] gap(s) found across [domains with gaps]. Would you like me to walk through the remediation recommendations?"*

---

## Boundaries

In scope: exporting a snapshot, parsing its XML artifacts, scoring the six audit domains, writing the Markdown scorecard.

Out of scope — do not attempt:
- **Calling any MCP tools.** This skill uses REST only.
- **Starting, modifying, or inspecting live process instances.** Use `inspect-baw-processes`.
- **Authoring new processes or fixing gaps directly.** Use `generate-baw-bpmn`.
- **Importing or writing back to BAW.** Read-only.
- **Scoring domains beyond the six defined in `references/audit-domains.md`.** Do not invent new domains.
- **Producing a certified audit artifact for external submission** — this is a gap analysis, not a compliance certificate.

---

## Output format

**Artifact inventory:** always present before scoring so the user can see what was found.

**Scorecard:** written to `reports/` as Markdown. Always confirm the file path after writing.

**Errors:** state what failed, the likely cause, and what the user can try next. Never show raw XML or a stack trace.
