# Inspect BAW Processes: Documentation

> Use when an IBM Business Automation Workflow (BAW) administrator or operator wants to find, investigate, or take action on running BAW process instances: retry failed processes, suspend or resume instances, change due dates, or answer questions like "what's broken right now?" or "why did this instance fail?"

## Purpose

This skill lets you search, inspect, and act on live BAW process instances without writing scripts or using the BAW admin console directly. You can filter instances by status, application, or date range; drill into a specific instance to see its business data and open tasks; and take lifecycle actions: suspend, resume, retry, terminate, or change a due date. It works whether you have the BAW Runtime MCP server connected or just a BAW server URL.

## Setting up and configuring

- **MCP mode (preferred):** Connect the BAW Runtime MCP server (`workflow-runtime`). Bob detects it automatically and uses MCP tools.
- **REST mode (fallback):** You do not need MCP. Provide your BAW server URL (for example, `https://baw.example.com:9443`) and credentials when prompted. Bob authenticates by using `POST /ops/system/login` and uses the REST API for all operations.
- You need BAW administrator credentials. Standard user credentials might lack permission to search all instances or take lifecycle actions.

## Compatibility

- BAW 26.x and later (REST API paths used: `/ops/system/login`, `/std/bpm/processes`, `/std/bpm/processes/count`)
- In IBM Cloud Pak for Business Automation (CP4BA) federated deployments, the skill automatically handles the `system_id` in instance results. You do not need to take any action.
- Workflow Server (runtime-only) environments do not support export or authoring operations. This skill targets runtime instance management only.

## Prompt examples

> **Note:** Replace the placeholders, such as `<your-baw-username>` and `<your-baw-password>`, with your own values. Do not paste real production credentials into prompts. Use environment variables or a secrets manager for sensitive values.

### Find all broken or overdue instances in an app
**Prompt:**
> Show me everything failed or late in the Claims Processing app on my BAW server at https://baw.company.com:9443, username <your-baw-username>, password <your-baw-password>.

**What to expect:** A table of matching instances (ID, name, status, due date) filtered to the Claims Processing app, with an offer to inspect or act on any of them.

---

### Inspect a specific instance
**Prompt:**
> Tell me everything about process instance 247. What's the current status, what business data does it have, and what tasks are still open?

**What to expect:** A labeled breakdown of instance info, business data as a readable key/value list, and any open tasks with their assignees and due dates.

---

### Retry a failed process
**Prompt:**
> Instance 312 in the Hiring Sample app failed overnight. The underlying service issue has been fixed. Please retry it.

**What to expect:** Bob confirms the instance is in a Failed state, warns you to verify the root cause is resolved before retrying, asks for confirmation, then retries and reports the new status.

---

### Suspend an active instance
**Prompt:**
> I need to pause instance 88 (Standard Employee Requisition) while we review an error in the data.

**What to expect:** Bob confirms the instance is Active, asks for confirmation (suspending stops active tasks), suspends the instance, and offers follow-up options.

---

### Terminate an instance permanently
**Prompt:**
> Terminate process instance 501. It was created by mistake and should never have been started.

**What to expect:** Bob requires explicit confirmation before terminating (the action is irreversible), then runs the action and confirms that the instance is now Terminated.

---

### Change a due date
**Prompt:**
> Move the due date on instance 77 to 2026-09-15T17:00:00Z. The customer asked for an extension.

**What to expect:** Bob updates the due date without requiring confirmation (no state change) and confirms the new value.

---

### Bulk action across many instances
**Prompt:**
> Find all suspended instances in the Order Management app and resume all of them.

**What to expect:** Bob searches and presents the full list with a count, asks for confirmation on the batch, then iterates through each one and reports the result per instance.

---

### Out-of-scope redirect: coach widgets and task portals
**Prompt:**
> Build a custom task list dashboard portal for our operators.

**What to expect:** Bob explains that creating custom coach widgets is handled by `create-baw-widget` and building task dashboard portals is handled by `create-baw-portal`, and redirects you there.

---

### Out-of-scope redirect: authoring
**Prompt:**
> I want to add a new approval step to the Claims process. Can you help?

**What to expect:** Bob explains this skill handles runtime instance management only and directs you to the `generate-baw-bpmn` skill for process authoring.
