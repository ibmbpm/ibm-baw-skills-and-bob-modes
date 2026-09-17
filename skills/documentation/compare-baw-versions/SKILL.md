---
name: compare-baw-versions
description: "Use when a BAW developer or administrator wants to compare two versions (snapshots or branches) of an IBM BAW process application. Exports both versions and produces a structured diff by artifact type — process steps, gateways, variables, business objects, services, scripts, and configuration. Flags artifacts modified in both versions as conflict hints so the developer knows what to reconcile manually in BAW Process Designer. Use when the user says 'what changed between snapshots', 'compare two versions', 'diff my branches', 'what changed in this release', 'show me what was added or removed', or 'help me understand what to merge'. Also use proactively when a developer describes divergent branches needing reconciliation. Applies under both BAW Author and BAW Admin modes. Do not use for generating processes (generate-baw-bpmn), running tests (generate-baw-tests), or inspecting live instances (inspect-baw-processes)."
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

# Compare BAW versions

Compare two versions of an IBM BAW process application and produce a structured, human-readable diff. The output tells the developer exactly what changed and flags artifacts modified in both versions — so they know what needs careful manual reconciliation in BAW Process Designer.

This skill does not perform merges. BAW has no merge API, and generating or modifying a TWX for import back into BAW is out of scope. The skill's job is to make the diff clear enough that the developer can merge confidently themselves.

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
| `list containers` | `GET /ops/std/bpm/containers` — list all process apps |
| `list versions` | `GET /ops/std/bpm/containers/{container}/versions` — list snapshots for a given app |
| `export version` | `GET /ops/std/bpm/containers/{container}/versions/{version}/export?use_enhanced_filenames=true` — download a TWX |

All three require an active session. Establish one first — see the discovery steps below.

---

## Guided discovery

Work through these steps in order. Do not announce step labels to the user — ask the questions naturally.

**Step 0a — establish the BAW connection.**

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

Once the user replies, immediately call `POST {BAW_BASE_URL}/ops/system/login` with:
- `Authorization: Basic <base64(username:password)>`
- `Content-Type: application/json`
- Body: `{"refresh_groups": false}`

On success (HTTP 201): store `csrf_token` from the JSON body as `{BAW_CSRF}`, and the `LtpaToken2`/`JSESSIONID` cookies as `{BAW_SESSION}`. Send `BPMCSRFToken: {BAW_CSRF}` and the session cookie on every subsequent REST call. Discard the raw credentials immediately. Never ask again.

If login returns 401 or 400, tell the user their credentials were not accepted and ask them to re-enter — do not proceed until login succeeds.

---

**Step 1 — identify the process application.**

If the user named the app, call `list containers` and find the match by name. If the name is ambiguous or not given, present a short numbered list from the response and ask which app they mean. Confirm the acronym before proceeding — never guess one.

---

**Step 2 — identify the two versions to compare.**

Call `list versions` for the identified app. Present the available snapshots with their names, acronyms, activation status, and creation dates in a concise table.

Ask the user which two to compare:
> *"Which two versions would you like to compare? You can refer to them by name or acronym."*

Label them **Version A** (older / base) and **Version B** (newer / target) — by convention, the diff shows what changed going from A to B. If the user doesn't specify which is older, use creation date order and confirm.

If the user says "latest" or "current" for one side, use the most recently activated snapshot.

---

**Step 3 — export both versions.**

For each version, call `export version` with `use_enhanced_filenames=true`. This returns a binary `.twx` file (a ZIP archive). Extract both archives into memory.

If a REST export fails:
- On 403: tell the user they may not have sufficient permissions to export this snapshot — admin access is usually required.
- On 404: the snapshot acronym may be wrong — show what was used and ask them to confirm.
- On other errors: show the status code and response body, and ask how they'd like to proceed.

If REST export fails persistently after two attempts, offer the manual fallback:
> *"If you already have the `.twx` files for both versions on your machine, you can share the file paths and I'll work from those directly."*
Accept local file paths and read them as ZIPs — process them identically to the REST exports.

---

**Step 4 — analyze and produce the diff.**

Read `references/DIFF_OUTPUT.md` for the exact output structure before starting analysis.

Parse the extracted XML files from both TWX archives. Organize your analysis by artifact type, working through each category in turn. For each artifact, classify every change as:

- **Added** — exists in B but not A
- **Removed** — exists in A but not B
- **Modified** — exists in both but differs
- **Conflict hint** — modified in both A and B relative to each other (same artifact name, different content on both sides). This is the set the developer must pay the most attention to during manual reconciliation.

> **On conflict hints:** You are doing a 2-way diff — you do not have a common ancestor, so you cannot detect true 3-way merge conflicts. A conflict hint means "this artifact differs between the two versions and the developer will need to choose which side's version to keep, or manually blend them." Present conflict hints prominently and separately from straightforward one-sided changes.

**Artifact types to compare — work through these in order:**

1. **Processes (BPMN)** — steps/activities (added, removed, reordered), gateways (condition changes), sequence flows, lanes/swimlanes, subprocess boundaries
2. **Services and service flows** — integration services, decision services, human services added/removed/changed
3. **Business objects** — parameters, field types, field additions/removals, nested BO changes
4. **Variables** — process variables, exposed process values (EPVs), private variables — type changes, additions, removals
5. **Scripts** — inline script bodies that changed (show a compact diff of the script content, not raw XML)
6. **Configuration** — environment variables, team bindings, server configurations

For each category, skip it entirely (don't mention it) if there are zero changes — only show categories where something actually changed.

---

**Step 5 — present the diff and save the report file.**

Follow the output format in `references/DIFF_OUTPUT.md` exactly. Lead with a summary header, then expand each artifact type that has changes. Present conflict hints in their own clearly marked section at the top, before the rest of the diff categories.

**Always write the report to a file** at the same time as presenting it in chat — do not wait to be asked. Save it as:
`<app-acronym>-<versionA-acronym>-vs-<versionB-acronym>-diff.md`

After saving, tell the user:
> *"I've also saved the full report to `{filename}`. Let me know if you'd like a JSON version as well."*

After presenting the diff, if there are **zero conflict hints**, close with:
> *"The changes above are informational only — no modifications have been made to either version. To apply changes, open the target version in BAW Process Designer and make the edits manually."*

If there **are conflict hints**, instead close with:
> *"I found N conflict(s) — artifacts that differ on both sides and will need a decision when you reconcile. Want me to walk you through each one so you can decide which version to keep?"*

Then proceed to Step 6 if they say yes.

---

**Step 6 — interactive conflict resolution (only if the user agrees).**

Work through each conflict hint one at a time. For each one, present a clean side-by-side and ask for a decision:

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

Wait for the user's response before moving to the next conflict. Do not batch them.

**Handling each response:**
- **(A) or (B):** Record the decision and move to the next conflict.
- **(C) Blend:** Ask the user to describe what the blended result should look like. Capture their description as the decision. Move on.
- **(S) Skip:** Mark it as "to decide later" and move on without recording a decision.

After all conflicts have been addressed, produce a **reconciliation checklist** — see `references/DIFF_OUTPUT.md` for the format. Present it in chat and **always save it to a file** at the same time:
`<app-acronym>-<versionA-acronym>-vs-<versionB-acronym>-reconciliation.md`

The checklist covers:
1. Every conflict decision the user made (what to change and to what value)
2. All one-sided additions and removals from the diff (these are safe to apply without a decision — just list them as action items)
3. Any skipped conflicts, flagged clearly as still needing a decision

Close with:
> *"This checklist is your guide for reconciling the two versions manually in BAW Process Designer. No changes have been made to either version — all edits need to be applied by you in the designer."*

---

## Important boundaries

- **Read-only.** This skill only exports and reads — it never imports, modifies, or writes back to BAW.
- **No merge generation.** Do not generate a merged TWX or suggest importing a generated artifact. If the user asks you to perform the merge, explain that BAW does not have a merge API and direct them to reconcile manually in Process Designer using the diff output.
- **2-way diff only.** Without a common ancestor snapshot, true merge conflict detection is not possible. Conflict hints surface same-artifact differences — they are not guaranteed to be conflicts in the strict 3-way-merge sense.
- **Authoring environments only for export.** The export API requires an authoring environment (Workflow Center). It is not available on Workflow Server (runtime-only) environments.
- **Process Apps only.** Toolkits can also be exported via the same API, but comparison across toolkit dependencies is out of scope for this skill.

---

## Disambiguation

**"Compare" vs "document":** If the user wants documentation or a summary of a single version (not a diff between two), direct them to a documentation skill or offer to describe one version at a time. This skill requires exactly two versions to compare.

**"Compare" vs "audit":** If the user wants compliance or audit readiness analysis, not a version diff, this is the wrong skill. Direct them to the audit-readiness skill.

**Same branch vs different branches:** Both are fully supported. Snapshot-to-snapshot comparisons on the same branch are the most common case (e.g., v1.0 vs v2.0). Cross-branch comparisons (e.g., `main` tip vs `feature/new-approval-flow`) work the same way — the skill exports a specific snapshot from each branch.
