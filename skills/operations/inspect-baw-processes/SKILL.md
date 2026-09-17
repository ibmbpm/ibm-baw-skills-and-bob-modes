---
name: inspect-baw-processes
description: "Use when a BAW administrator or operator wants to find, investigate, or take action on running IBM BAW process instances — retry failed processes, suspend or resume instances, change due dates, or answer questions like \"what's broken right now?\", \"show me everything overdue in the Claims app\", or \"why did this instance fail?\" Covers the full Process Inspector workflow: searching by status/app/owner/date, drilling into instance details and business data, and executing lifecycle actions. Do not use for authoring new processes (generate-baw-bpmn), creating coach widgets (create-baw-widget), or packaging toolkits. Do NOT use for audit readiness, compliance checks, or questions about whether a process application is ready for an audit — use audit-baw-readiness for those."
license: Apache-2.0
allowed-tools:
  - execute
  - write
  - read
  - fetch
metadata:
  version: "1.0.0"
---

# Inspect BAW Processes

Search, inspect, and act on IBM BAW process instances at runtime. This skill covers three categories of work: finding instances by filter, inspecting the details of a specific instance, and taking lifecycle actions (suspend, resume, retry, terminate, change due date).

One rule applies to all categories: **always resolve the instance ID by searching first** — the instance ID must always come from a search result, not from the user.

---

## Execution mode

At the start of the session, check your tool list once and pick a path:

- If you have tools for **process instance and task** operations → MCP path. Use the MCP operations described in this skill.
- If no such tools are visible → REST path (see `references/baw-rest.md`).

Stay on the chosen path for the entire session. Do not use a failed tool call as evidence of absence — only absence from the tool list counts.

---

## Semantic operations

The capability logic below uses transport-agnostic operation names. When you need to execute one, look it up in the appropriate reference file:

| Operation | What it does |
|---|---|
| `list_exposed_processes` | Get all process apps with their acronyms |
| `search_processes` | Filter instances by status, app, dates |
| `get_process_details` | Full metadata, business data, and tasks for one instance |
| `get_process_documents` | Documents attached to an instance |
| `suspend_process(id)` | Halt a running instance |
| `resume_process(id)` | Restart a suspended instance |
| `retry_process(id)` | Re-run a failed instance |
| `modify_process_due_date(id, date)` | Change the due date |
| `terminate_process(id)` | Permanently end an instance |

**Valid state transitions:**

| Operation | Only valid when instance status is |
|---|---|
| `suspend_process` | Active |
| `resume_process` | Suspended |
| `retry_process` | Failed |
| `modify_process_due_date` | Any |
| `terminate_process` | Any |

**Status vocabulary** — translate user language before filtering:

| User says | Status value |
|---|---|
| stuck, paused, on hold | Suspended |
| broken, errored, failed | Failed |
| running late, overdue | Late |
| at risk | At_Risk |
| running, active | Active |
| done, finished | Completed |
| killed, stopped | Terminated |

---

## Category A — Finding / searching instances

1. **Translate intent to filter parameters.** Map natural language to the status vocabulary above. If the user names a process app by full name, note that `search_processes_by_filter` requires an acronym — go to step 2. If no app name was given, skip to step 3.

2. **Resolve app name to acronym.** Execute `list_exposed_processes`. Find the entry whose app name matches what the user said and read its acronym (e.g. `HSS`). If no match is found, tell the user and offer to search without the app filter.

3. **Execute `search_processes_by_filter`** with the resolved parameters. All filters are optional — omitting all returns all instances. Never call `search_processes` (advanced DSL) for natural-language requests.

4. **Present results** as a clean table: Instance ID, Name, Status, Due Date. Do not show raw JSON. If the list is empty, say so and suggest loosening the filter.

5. **Offer next steps** — inspect a specific instance, or take a lifecycle action. Wait for the user to choose.

---

## Category B — Inspecting a specific instance

1. **Get the instance ID.** Use results from Category A if available. Resolve the ID from search results. Ask the user to type a raw ID only as a last resort.

2. **Execute `get_process_details`.** Present in labelled sections:
   - **Instance Info:** name, status, due date, start time
   - **Business Data:** key/value list — not raw JSON
   - **Open Tasks:** task name, assigned to, due date

3. **Offer documents.** If the user mentioned documents, execute `get_process_documents` immediately. Otherwise ask: *"Would you also like to see documents attached to this instance?"*

4. **Offer next steps** — offer applicable lifecycle actions based on the instance's current status.

---

## Category C — Taking an action on an instance

1. **Confirm the instance ID.** If not already known, run Category A first. If the user described a process by name, search and present matches before acting.

2. **Check the instance is in the right state** using the state transitions table. If the user asks to resume an Active instance, stop: *"This instance is Active — it doesn't need to be resumed. Did you mean to suspend it?"*

3. **Apply the right confirmation level:**
   - **Suspend** — halts active work, may block people. Always ask: *"This will suspend [name] ([id]), stopping any active tasks. Proceed?"* Wait for confirmation.
   - **Retry** — first note: *"Before retrying, make sure the underlying issue has been resolved — retrying against an unresolved problem will fail again and may trigger duplicate side-effects."* Then ask: *"Retry [name] ([id])?"* Wait for confirmation.
   - **Resume** — low risk and reversible. Confirmation is not needed.
   - **Modify due date** — no state change. Confirmation is not needed.
   - **Terminate** — irreversible. Always ask explicitly with the instance name and ID. Do not proceed without a clear "yes."

4. **Execute the operation** via the appropriate reference file.

5. **Report the result** as one line: *"Instance [name] ([id]) is now [state]."* If the call fails with a state-conflict error (e.g. 400), check the transitions table and explain what went wrong.

6. **Offer follow-up:**
   - After suspending → *"Would you like to resume it later, or inspect its current tasks?"*
   - After resuming → *"Would you like to monitor its progress?"*
   - After retrying → *"Would you like to check its status in a moment?"*
   - After changing due date → *"Would you like to update any other instances?"*

**Bulk actions:** Action operations work on one instance at a time. For bulk requests (e.g. "retry all failed instances"), present the full list, confirm the count, then iterate one by one. Apply the confirmation level to the batch as a whole, not to each individual item.

---

## Disambiguation rules

**`search_processes_by_filter` vs `search_processes` (advanced DSL)**
Always call `search_processes_by_filter` first for all natural-language requests — it maps directly to the v1 BAW endpoint and is the reliable default. Only call `search_processes` when the user explicitly needs a complex boolean condition that `search_processes_by_filter` cannot express (e.g. combining AND/OR across multiple fields). Never use `search_processes` as the default.

**App name vs acronym**
The user will give a full name. The operation needs the acronym. Always resolve via `list_exposed_processes` — never guess.

---

## Known limitations

**No owner/starter filter.** There is no way to filter instances by who started them. Explain this if the user asks.

**All action operations work on one instance at a time.** No bulk operation exists — iterate for bulk requests.

**Non-federated environments.** In CP4BA federated deployments, instance results from the advanced search include a `system_id` that must be passed through to action operations. On standalone BAW, omit it. See `references/mcp.md` for details.

---

## Boundaries

In scope: searching instances by filter, inspecting instance details and documents, lifecycle actions (suspend, resume, retry, terminate, modify due date).

Out of scope — do not attempt:
- **Authoring or generating new processes.** Use `generate-baw-bpmn`.
- **Starting a new process instance.** Not covered by this skill.
- **Modifying process design or business objects.** Runtime inspection only.
- **Packaging or deploying TWX toolkits.**

---

## Output format

**Search results:**
| Instance ID | Name | Status | Due Date |
|---|---|---|---|
| 15 | Standard Employee Requisition for... | Active | 2026-07-21T22:00:00Z |

**Instance details:** labelled sections (Instance Info, Business Data, Open Tasks). Business data as a readable key/value list.

**Action confirmations:** *"Instance [name] ([id]) is now [state]."*

**Errors:** state what failed, likely cause, and what the user can try next. Never show a raw stack trace or JSON blob.

---

## Example

**Input:** "Show me everything stuck or late in the Hiring Sample app, then suspend the oldest one."

1. "Stuck" → Suspended, "late" → Late. "Hiring Sample" needs an acronym — execute `list_exposed_processes`, find acronym `HSS`.
2. Execute `search_processes(status=["Suspended","Late"], application="HSS")`. Get back instances 15, 22, 31.
3. Present as table. Instance 15 has the earliest due date.
4. Ask: *"Found 3 instances. Instance 15 (Standard Employee Requisition, due 2026-07-18) is most overdue. Suspend it?"*
5. User confirms. Instance 15 is Active — suspend is valid. Execute `suspend_process("15")`.
6. Report: *"Instance Standard Employee Requisition (15) is now Suspended."*
7. Offer: *"Would you like to suspend the others, resume this one later, or inspect any of them?"*
