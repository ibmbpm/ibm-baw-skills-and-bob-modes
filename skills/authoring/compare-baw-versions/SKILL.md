---
name: compare-baw-versions
description: "Use when an IBM Business Automation Workflow (BAW) developer or administrator wants to compare two versions (snapshots or branches) of a process application. Exports both versions and produces a structured diff by artifact type: process steps, gateways, variables, business objects, services, scripts, and configuration. Flags artifacts that changed in both versions as conflict hints so the developer knows what to reconcile manually in BAW Process Designer. Use when the user says 'what changed between snapshots', 'compare two versions', 'diff my branches', 'what changed in this release', 'show me what was added or removed', or 'help me understand what to merge'. Also use proactively when a developer describes divergent branches needing reconciliation. Applies under both BAW Author and BAW Admin modes. Do not use for generating processes (generate-baw-bpmn), running tests (generate-baw-tests), or inspecting live instances (inspect-baw-processes)."
license: Apache-2.0
compatibility: "IBM BAW 22.x and later; IBM CP4BA 22.x and later"
allowed-tools:
  - Read
  - Edit
  - Bash
metadata:
  version: "1.0.0"
  display_name: Compare BAW Versions
  short_description: Diff two BAW process app snapshots or branches by artifact type and flag conflicting changes for manual reconciliation.
  author: IBM BAW Team
---
> **Important: REST only. This skill does not support MCP.** All BAW interactions use the BAW REST API exclusively, through HTTP calls to `{BAW_BASE_URL}`. Do not call any MCP tools at any point, whether or not an MCP server is connected. This skill has no MCP dependency. If you are about to use an MCP tool, stop and use the REST equivalent from `references/baw-rest.md` instead.

> **Important: always export the TWX file through REST, never through MCP.** Even if an Authoring MCP server is connected and its `export_solution` tool is visible in your tool list, do not call it for this skill. Always download the TWX file with `GET {BAW_BASE_URL}/ops/std/bpm/containers/{container}/versions/{version}/export?use_enhanced_filenames=true`. This rule applies even when MCP is fully connected. Do not mention the MCP export tool to the user. Do not reason that MCP is more reliable. REST is the required transport for this operation.

# Compare BAW versions

Compare two versions of an IBM Business Automation Workflow (BAW) process application and produce a structured, human-readable diff. The output tells the developer exactly what changed. It also flags the artifacts that changed in both versions, so the developer knows what needs careful manual reconciliation in BAW Process Designer.

This skill does not perform merges. BAW has no merge API, and generating or modifying a TWX file for import back into BAW is out of scope. The skill makes the diff clear enough that the developer can merge confidently.

---

## Execution mode

This skill operates in REST mode only. All calls use the BAW REST API documented in `references/baw-rest.md`.

---

## Credentials

Never prompt the user for credentials. Credentials are only needed when making a REST call.
When a REST call is about to be made, read `references/CREDENTIAL_HANDLING.md` and follow it — it will read credentials from `.env` automatically, and only prompt the user if a value is missing from that file. Do this once per session only.

---

## Semantic operations

| Operation | Description |
|---|---|
| `list containers` | `GET /ops/std/bpm/containers` lists all process applications. |
| `list versions` | `GET /ops/std/bpm/containers/{container}/versions` lists the snapshots for a given application. |
| `export version` | `GET /ops/std/bpm/containers/{container}/versions/{version}/export?use_enhanced_filenames=true` downloads a TWX file. |

All three operations require an active session. Establish a session first, as described in the discovery steps.

---

## Guided discovery

Work through these steps in order. Do not announce step labels to the user. Ask the questions naturally.

### Step 1: Identify the process application

If the user named the application, call `list containers` and find the match by name. If the name is ambiguous or missing, present a short numbered list from the response and ask which application the user means. Confirm the acronym before you proceed. Do not guess an acronym.

---

### Step 2: Identify the two versions to compare

Call `list versions` for the identified application. Present the available snapshots in a concise table with their names, acronyms, activation status, and creation dates.

Ask the user which two to compare:
> *"Which two versions would you like to compare? You can refer to them by name or acronym."*

Label them Version A (older or base) and Version B (newer or target). By convention, the diff shows what changed going from A to B. If the user does not specify which version is older, order them by creation date and confirm the order with the user.

If the user says "latest" or "current" for one side, use the most recently activated snapshot.

---

### Step 3: Export both versions

For each version, call `export version` with `use_enhanced_filenames=true`. The call returns a binary `.twx` file, which is a ZIP archive. Extract both archives into memory.

If a REST export fails:
- On 403, tell the user that they might not have permission to export this snapshot. Export usually requires administrator access or project read permission.
- On 404, show the snapshot acronym that you used and ask the user to confirm it.
- On other errors, show the status code and the response body, and ask how the user wants to proceed.

If the REST export fails twice, offer the manual fallback:
> *"If you already have the `.twx` files for both versions on your machine, you can share the file paths and I'll work from those directly."*

Accept local file paths, read them as ZIP archives, and process them the same way as the REST exports.

---

### Step 4: Analyze and produce the diff

Read `references/DIFF_OUTPUT.md` for the exact output structure before you start the analysis.

Parse the extracted XML files from both TWX archives. Organize your analysis by artifact type, and work through each category in turn. Classify every change for each artifact as one of the following:

- **Added**: exists in B but not in A.
- **Removed**: exists in A but not in B.
- **Modified**: exists in both but differs.
- **Conflict hint**: the same artifact name has different content in A and B. This set needs the most attention during manual reconciliation.

> **Note on conflict hints:** This skill runs a two-way diff. Without a common ancestor, it cannot detect true three-way merge conflicts. A conflict hint means that the artifact differs between the two versions, and the developer must choose which version to keep or blend them manually. Present conflict hints prominently and separately from straightforward one-sided changes.

Compare these artifact types in this order:

1. **Processes (BPMN)**: steps and activities (added, removed, reordered), gateways (condition changes), sequence flows, lanes and swimlanes, subprocess boundaries.
2. **Services and service flows**: integration services, decision services, and human services that were added, removed, or changed.
3. **Business objects**: parameters, field types, field additions and removals, nested business object changes.
4. **Variables**: process variables, exposed process values (EPVs), and private variables, with their type changes, additions, and removals.
5. **Scripts**: inline script bodies that changed. Show a compact diff of the script content, not raw XML.
6. **Configuration**: environment variables, team bindings, and server configurations.

Skip a category entirely, without mentioning it, if it has zero changes. Show only the categories where something changed.

---

### Step 5: Present the diff and save the report file

Follow the output format in `references/DIFF_OUTPUT.md` exactly. Lead with a summary header, then expand each artifact type that has changes. Present conflict hints in their own clearly marked section at the top, before the other diff categories.

Write the report to a file at the same time that you present it in chat. Do not wait for the user to ask. Save it as:
`<app-acronym>-<versionA-acronym>-vs-<versionB-acronym>-diff.md`

After you save the file, tell the user:
> *"I've also saved the full report to `{filename}`. Let me know if you'd like a JSON version as well."*

If the diff has zero conflict hints, close with:
> *"The changes above are informational only. I have not modified either version. To apply changes, open the target version in BAW Process Designer and make the edits manually."*

If the diff has conflict hints, close with:
> *"I found N conflict(s): artifacts that differ on both sides and need a decision when you reconcile. Want me to walk you through each one so you can decide which version to keep?"*

If the user agrees, proceed to Step 6.

---

### Step 6: Resolve conflicts interactively (only if the user agrees)

Work through each conflict hint one at a time. For each conflict, present a clean side-by-side comparison and ask for a decision:

```
─────────────────────────────────────────
Conflict 1 of N: [Artifact Type] — [Artifact Name]
─────────────────────────────────────────
  Version A ([snapshot name]):
    [human-readable description of Version A's value/state]

  Version B ([snapshot name]):
    [human-readable description of Version B's value/state]

→ What would you like to do?
  (A) Keep Version A's version
  (B) Keep Version B's version
  (C) Blend them — describe what you want
  (S) Skip for now
```

Wait for the user's response before you move to the next conflict. Do not batch the conflicts.

Handle each response as follows:
- **(A) or (B):** Record the decision and move to the next conflict.
- **(C) Blend:** Ask the user to describe what the blended result should look like. Capture the description as the decision, and move on.
- **(S) Skip:** Mark the conflict as "to decide later" and move on without recording a decision.

After the user addresses all conflicts, produce a reconciliation checklist. See `references/DIFF_OUTPUT.md` for the format. Present the checklist in chat and save it to a file at the same time:
`<app-acronym>-<versionA-acronym>-vs-<versionB-acronym>-reconciliation.md`

The checklist covers:
1. Every conflict decision that the user made, with what to change and the target value.
2. All one-sided additions and removals from the diff. These are safe to apply without a decision, so list them as action items.
3. Any skipped conflicts, flagged clearly as still needing a decision.

Close with:
> *"This checklist is your guide for reconciling the two versions manually in BAW Process Designer. I have not changed either version. You need to apply all edits in the designer."*

---

## Important boundaries

- **Read-only.** This skill only exports and reads. It never imports, modifies, or writes back to BAW.
- **No merge generation.** Do not generate a merged TWX file or suggest importing a generated artifact. If the user asks you to perform the merge, explain that BAW has no merge API and direct the user to reconcile manually in Process Designer by using the diff output.
- **Two-way diff only.** Without a common ancestor snapshot, true merge conflict detection is not possible. Conflict hints surface same-artifact differences. They are not guaranteed to be conflicts in the strict three-way-merge sense.
- **Authoring environments only for export.** The export API requires an authoring environment: Workflow Center for traditional BAW, or Business Automation Studio for containerized CP4BA. Workflow Server (runtime-only) environments do not support export.
- **Process applications only.** The same API can export toolkits, but comparing toolkit dependencies is out of scope for this skill.

---

## Disambiguation

**Compare versus document:** If the user wants documentation or a summary of a single version instead of a diff between two versions, direct the user to `baw-project-doc` or offer to describe one version at a time. This skill requires exactly two versions.

**Compare versus audit:** If the user wants a compliance or audit readiness analysis instead of a version diff, this is the wrong skill. Direct the user to `audit-baw-readiness` (design-time scorecard analysis against six internal control domains) or `process-compliance-violation-detection` (policy and regulatory compliance checks against external standards such as SOX, GDPR, and ISO).

**Same branch versus different branches:** The skill supports both. Snapshot-to-snapshot comparisons on the same branch are the most common case (for example, v1.0 versus v2.0). Cross-branch comparisons (for example, the `main` tip versus `feature/new-approval-flow`) work the same way. The skill exports a specific snapshot from each branch.
