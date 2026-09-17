# Audit BAW Readiness — Documentation

> Evaluates an IBM® BAW process application's design for compliance and audit readiness — scores six domains and produces a Markdown scorecard with specific gaps and remediation steps.

## Purpose

This skill is for BAW developers and architects preparing for internal audits, regulatory reviews (SOX, GDPR, ISO), or compliance sign-offs. It exports the process application's `.twx` artifact, analyses the BPMN design and business objects against six compliance domains, and produces a scored gap analysis telling you exactly what needs to be fixed before an audit begins. The output is a Markdown scorecard written to `reports/` with a Pass / Needs Attention / Not Ready overall rating. This skill inspects process design only — it does not touch running instances.

## Setup and configuration

- **REST only** — no MCP server required or used. All calls go directly to the BAW REST API.
- Provide your BAW server URL and credentials when prompted. Credentials are only used to obtain a session token for the current conversation.
- If you already have the `.twx` file on disk, provide the file path — no server connection needed.
- Admin-level credentials are typically required for the TWX export endpoint (`GET /ops/std/bpm/containers/{container}/versions/{version}/export`).
- The `reports/` directory is created automatically if it does not exist.

## Compatibility

- BAW 26.x (REST endpoints: `/ops/system/login`, `/ops/std/bpm/containers`, `/ops/std/bpm/containers/{container}/versions`, `/ops/std/bpm/containers/{container}/versions/{version}/export`)
- Authoring environments (Workflow Center) only — the export API is not available on Workflow Server (runtime-only) deployments
- This skill produces a gap analysis, not a certified compliance artifact for external submission

> **Note:** Credentials shown in prompt examples are for illustration only. Never use real production credentials in prompts. Use environment variables or a secrets manager for sensitive values.

## Prompt examples

### Full audit readiness check from a live server
**Prompt:**
> Run an audit readiness check on my Hiring Sample app on https://baw.internal.com:9443, username tw_admin, password tw_admin.

**What to expect:** Bob authenticates, lists available snapshots, confirms which to assess, exports the TWX, presents an artifact inventory, scores all six domains (Traceability, Separation of Duties, Access Control, SLA/Timeliness, Data Completeness, Error Handling), and writes `reports/HSS-audit-readiness.md`. It then tells you how many gaps were found and offers to walk through remediation.

---

### SOX audit preparation
**Prompt:**
> I have a SOX audit next month. Does my Claims Processing app (acronym CP, snapshot CP_V2) meet the requirements? BAW is at https://baw.company.com:9443, admin/secret.

**What to expect:** Bob runs the full six-domain assessment with particular attention to Traceability and Separation of Duties (the domains most relevant to SOX). Writes the scorecard to `reports/CP-audit-readiness.md` with an overall Pass / Needs Attention / Not Ready verdict.

---

### Assess from a local TWX file
**Prompt:**
> I already have the TWX at /Users/me/Downloads/OrderMgmt.twx — check it for audit readiness without connecting to a server.

**What to expect:** Bob reads the file from disk, processes it identically to a REST export, presents the artifact inventory, scores all six domains, and writes the scorecard to `reports/`. No server URL or credentials needed.

---

### GDPR compliance gap check
**Prompt:**
> Check my Employee Onboarding app for GDPR compliance gaps. BAW: https://baw.internal:9443, user admin, pass admin123.

**What to expect:** Bob runs the full assessment with particular attention to the Data Completeness domain (personal data fields, retention/deletion controls). Scores all six standard domains — no additional GDPR-specific domains are invented. Writes the scorecard with any gaps identified.

---

### Missing app name — Bob asks
**Prompt:**
> Run an audit check on my BAW server at https://baw.example.com:9443.

**What to expect:** Bob asks for credentials, then lists all available process applications and asks which one to assess before proceeding.

---

### Out-of-scope redirect — live instance inspection
**Prompt:**
> Show me all the running instances in my Claims app that are stuck.

**What to expect:** Bob explains this skill is for design-time audit analysis only and redirects you to the `inspect-baw-processes` skill for searching and acting on live instances.

---

### Out-of-scope redirect — fixing gaps
**Prompt:**
> The audit check found that my process has no timer events. Can you add them?

**What to expect:** Bob explains this skill is read-only and directs you to `generate-baw-bpmn` to make authoring changes to the process.
