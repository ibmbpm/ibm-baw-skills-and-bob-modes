# Compare BAW Versions — Documentation

> Use when you want to understand what changed between two snapshots or branches of an IBM® BAW process application — and get a structured diff with conflict hints so you can reconcile them confidently in Process Designer.

## Purpose

This skill is for BAW developers and administrators who need to understand differences between two versions of a process app — before a release, after a branched development effort, or when troubleshooting a regression. It exports both versions as `.twx` archives, compares them across six artifact categories (Processes, Services, Business Objects, Variables, Scripts, Configuration), and produces a structured Markdown diff report. Artifacts modified in both versions are flagged as conflict hints — the things that need a human decision during manual reconciliation. An optional interactive step walks you through each conflict one at a time and produces a reconciliation checklist. This skill is read-only: it never imports, modifies, or writes back to BAW.

## Setup and configuration

- **REST only** — no MCP server required or used. All calls go directly to the BAW REST API.
- Provide your BAW server URL and credentials when prompted. Credentials are only used to obtain a session token for the current conversation.
- If you already have both `.twx` files on disk, provide both file paths — no server connection needed.
- Admin-level credentials are typically required for the TWX export endpoint.
- Two output files are always written automatically: `<acronym>-<vA>-vs-<vB>-diff.md` and, if conflict resolution is run, `<acronym>-<vA>-vs-<vB>-reconciliation.md`.

## Compatibility

- BAW 26.x (REST endpoints: `/ops/system/login`, `/ops/std/bpm/containers`, `/ops/std/bpm/containers/{container}/versions`, `/ops/std/bpm/containers/{container}/versions/{version}/export`)
- Authoring environments (Workflow Center) only — the export API is not available on Workflow Server (runtime-only) deployments
- 2-way diff only — without a common ancestor snapshot, true 3-way merge conflict detection is not possible; conflict hints flag same-artifact differences that need a human decision
- Toolkit dependency comparison across linked toolkits is out of scope

> **Note:** Credentials shown in prompt examples are for illustration only. Never use real production credentials in prompts. Use environment variables or a secrets manager for sensitive values.

## Prompt examples

### Compare two named snapshots
**Prompt:**
> Compare version V1 and V2 of my Claims Processing app (acronym CP). BAW server: https://baw.company.com:9443, admin/secret.

**What to expect:** Bob authenticates, exports both snapshots, diffs them by artifact type, and writes `CP-V1-vs-V2-diff.md`. Conflict hints (artifacts changed on both sides) appear at the top of the report. If conflicts are found, Bob offers to walk through them interactively.

---

### Compare the two most recent snapshots
**Prompt:**
> What changed between the latest and the previous snapshot of my Hiring Sample app? BAW: localhost:9443, tw_admin/tw_admin.

**What to expect:** Bob lists all snapshots, identifies the two most recent, confirms the selection with you, exports both, and writes `HSS-<vA>-vs-<vB>-diff.md` with a full structured diff.

---

### Compare two local TWX files
**Prompt:**
> I have two TWX files: /Downloads/MyApp_v1.twx and /Downloads/MyApp_v2.twx. What changed between them?

**What to expect:** Bob reads both files from disk as ZIPs, labels the first as Version A and the second as Version B (confirms with you), produces the full diff by artifact type, and writes the diff report. No server or credentials needed.

---

### Cross-branch comparison
**Prompt:**
> Compare the tip of my main branch with the tip of my feature/new-approval-flow branch for the Order Management app. Server: https://baw.internal:9443, devadmin/devpass.

**What to expect:** Bob lists versions from both branches, lets you confirm which snapshot from each branch to use as Version A and B, exports both, and diffs them — same process as a same-branch comparison.

---

### Compare and resolve conflicts interactively
**Prompt:**
> Compare V1 and V2 of my Claims app and help me decide what to keep for each conflict. Server: https://baw.company.com:9443, admin/secret.

**What to expect:** Bob produces the diff, then works through each conflict hint one at a time — showing a side-by-side of both versions and asking you to choose (A) keep Version A, (B) keep Version B, (C) blend them, or (S) skip. After all conflicts are addressed, it writes a reconciliation checklist (`CP-V1-vs-V2-reconciliation.md`) and reminds you that no changes have been made to BAW — all edits must be applied manually in Process Designer.

---

### Out-of-scope redirect — single version documentation
**Prompt:**
> I only have one TWX file — can you document what's in it?

**What to expect:** Bob explains this skill requires exactly two versions to compare and offers to either help you retrieve the second version from your server, or direct you to a documentation skill for single-version analysis.

---

### Out-of-scope redirect — compliance analysis
**Prompt:**
> Compare V1 and V2 of my Claims app — is it SOX compliant?

**What to expect:** Bob explains that compliance scoring is handled by the `audit-baw-readiness` skill and redirects you there. It may offer to run the version diff separately if you also want to see what changed.

---

### Out-of-scope redirect — performing the merge
**Prompt:**
> After the diff, can you generate a merged TWX file I can import?

**What to expect:** Bob explains that BAW has no merge API and generating a modified TWX for import is out of scope. It provides the reconciliation checklist instead, which you apply manually in Process Designer.
