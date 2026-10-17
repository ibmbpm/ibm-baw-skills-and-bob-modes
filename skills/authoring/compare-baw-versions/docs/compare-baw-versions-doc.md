# Compare BAW versions: documentation

> Use this skill when you want to understand what changed between two snapshots or branches of an IBM Business Automation Workflow (BAW) process application. The skill produces a structured diff with conflict hints so you can reconcile them confidently in Process Designer.

## Purpose

This skill is for BAW developers and administrators who need to understand the differences between two versions of a process application, for example before a release, after a branched development effort, or when troubleshooting a regression. The skill exports both versions as `.twx` archives, compares them across six artifact categories (processes, services, business objects, variables, scripts, and configuration), and produces a structured Markdown diff report. The skill flags artifacts that changed in both versions as conflict hints. These are the items that need a human decision during manual reconciliation. An optional interactive step walks you through each conflict one at a time and produces a reconciliation checklist. This skill is read-only. It never imports, modifies, or writes back to BAW.

## Setup and configuration

- **REST only.** The skill requires no MCP server and does not use one. All calls go directly to the BAW REST API.
- Provide your BAW server URL and credentials when Bob asks for them. Bob uses the credentials only to obtain a session token for the current conversation.
- If you already have both `.twx` files on disk, provide both file paths. You do not need a server connection.
- The TWX export endpoint typically requires administrator access or project read permission.
- The skill always writes two output files automatically: `<acronym>-<vA>-vs-<vB>-diff.md` and, if you run conflict resolution, `<acronym>-<vA>-vs-<vB>-reconciliation.md`.

## Compatibility

- IBM BAW 22.x and later, and IBM CP4BA 22.x and later. The REST reference in this skill is based on the BAW 26.0.0 API specification. The skill uses these endpoints: `/ops/system/login`, `/ops/std/bpm/containers`, `/ops/std/bpm/containers/{container}/versions`, and `/ops/std/bpm/containers/{container}/versions/{version}/export`.
- Authoring environments only: Workflow Center for traditional BAW, or Business Automation Studio for containerized CP4BA. Workflow Server (runtime-only) deployments do not support the export API.
- Two-way diff only. Without a common ancestor snapshot, the skill cannot perform true three-way merge conflict detection. Conflict hints flag same-artifact differences that need a human decision.
- Comparing toolkit dependencies across linked toolkits is out of scope.

## Prompt examples

> **Note:** The credentials in these prompt examples are for illustration only. Never use real production credentials in prompts. Use environment variables or a secrets manager for sensitive values.

### Compare two named snapshots
**Prompt:**
> Compare version V1 and V2 of my Claims Processing app (acronym CP). BAW server: https://baw.company.com:9443, admin/secret.

**What to expect:** Bob authenticates, exports both snapshots, diffs them by artifact type, and writes `CP-V1-vs-V2-diff.md`. Conflict hints (artifacts that changed on both sides) appear at the top of the report. If Bob finds conflicts, it offers to walk through them interactively.

---

### Compare the two most recent snapshots
**Prompt:**
> What changed between the latest and the previous snapshot of my Hiring Sample app? BAW: localhost:9443, tw_admin/tw_admin.

**What to expect:** Bob lists all snapshots, identifies the two most recent, confirms the selection with you, exports both, and writes `HSS-<vA>-vs-<vB>-diff.md` with a full structured diff.

---

### Compare two local TWX files
**Prompt:**
> I have two TWX files: /Downloads/MyApp_v1.twx and /Downloads/MyApp_v2.twx. What changed between them?

**What to expect:** Bob reads both files from disk as ZIP archives, labels the first as Version A and the second as Version B (and confirms the labels with you), produces the full diff by artifact type, and writes the diff report. You do not need a server or credentials.

---

### Cross-branch comparison
**Prompt:**
> Compare the tip of my main branch with the tip of my feature/new-approval-flow branch for the Order Management app. Server: https://baw.internal:9443, devadmin/devpass.

**What to expect:** Bob lists versions from both branches, asks you to confirm which snapshot from each branch to use as Version A and Version B, exports both, and diffs them. The process is the same as for a same-branch comparison.

---

### Compare and resolve conflicts interactively
**Prompt:**
> Compare V1 and V2 of my Claims app and help me decide what to keep for each conflict. Server: https://baw.company.com:9443, admin/secret.

**What to expect:** Bob produces the diff, then works through each conflict hint one at a time. For each conflict, Bob shows a side-by-side comparison of both versions and asks you to choose (A) keep Version A, (B) keep Version B, (C) blend them, or (S) skip. After you address all conflicts, Bob writes a reconciliation checklist (`CP-V1-vs-V2-reconciliation.md`) and reminds you that it has not changed anything in BAW. You must apply all edits manually in Process Designer.

---

### Out-of-scope redirect: single-version documentation
**Prompt:**
> I only have one TWX file — can you document what's in it?

**What to expect:** Bob explains that this skill requires exactly two versions to compare. Bob then offers to help you retrieve the second version from your server, or directs you to a documentation skill for single-version analysis.

---

### Out-of-scope redirect: compliance analysis
**Prompt:**
> Compare V1 and V2 of my Claims app — is it SOX compliant?

**What to expect:** Bob explains that the `audit-baw-readiness` skill handles design-time control scoring and the `process-compliance-violation-detection` skill handles full regulatory policy compliance checks (SOX, GDPR, ISO). Bob redirects you to those skills. Bob might offer to run the version diff separately if you also want to see what changed.

---

### Out-of-scope redirect: performing the merge
**Prompt:**
> After the diff, can you generate a merged TWX file I can import?

**What to expect:** Bob explains that BAW has no merge API and that generating a modified TWX file for import is out of scope. Bob provides the reconciliation checklist instead, and you apply it manually in Process Designer.
