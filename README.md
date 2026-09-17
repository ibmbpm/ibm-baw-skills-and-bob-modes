# IBM® Business Automation Workflow Skills and Bob Modes

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A growing collection of skills and IBM Bob modes that accelerate development with IBM® Business Automation Workflow.

## IBM public repository disclosure

All content in this repository including code has been provided by IBM under the associated open source software license and IBM is under no obligation to provide enhancements, updates, or support. IBM developers produced this code as an open source project (not as an IBM product), and IBM makes no assertions as to the level of quality nor security, and will not be maintaining this code going forward.

## Table of Contents

- [Overview](#overview)
- [Concepts](#concepts)
  - [What is Bob?](#what-is-bob)
  - [Modes](#modes)
  - [Skills](#skills)
- [Prerequisites](#prerequisites)
- [Getting started](#getting-started)
- [Available modes](#available-modes)
- [Available skills](#available-skills)
- [License](#license)

## Overview

This repository provides ready-to-use Bob modes and skills that accelerate IBM® Business Automation Workflow (BAW) development across a range of tasks. It works with:

- [IBM® Business Automation Workflow](https://www.ibm.com/products/business-automation-workflow)
- [IBM® Cloud Pak® for Business Automation (CP4BA)](https://www.ibm.com/products/cloud-pak-for-business-automation)

## Concepts

### What is Bob?

[IBM Bob](https://bob.ibm.com/) is an AI coding assistant and agent framework. This repository extends Bob with BAW-specific modes and skills.

### Modes

A **mode** shapes how Bob approaches a task — its role, expertise, and which skills it reaches for. Each mode in `modes/` is a self-contained YAML definition you load into Bob.

### Skills

A **skill** is a focused instruction set that gives Bob a specific capability. Each skill lives in its own folder under `skills/` with a `SKILL.md` that tells Bob what to do, what inputs to expect, and how to respond. Some skills also include helper scripts that Bob can run as part of the workflow.

## Prerequisites

- [IBM Bob](https://bob.ibm.com/) installed and signed in
- Any skill-specific prerequisites are noted in the skill's `SKILL.md`

## Getting started

### 1. Clone and open in Bob

```bash
git clone <repository-url>
cd ibm-baw-skills-and-bob-modes
```

Open the **repository root** as your workspace in Bob. Bob discovers project configuration relative to the workspace root.

### 2. Load a mode

Copy the relevant YAML file from `modes/` into your project's `.bob/custom_modes.yaml` (or merge it in if one already exists). Then use the mode selector at the bottom of the Bob chat area to switch to the newly added mode.

If a mode does not appear, confirm `.bob/custom_modes.yaml` exists at the workspace root and reload the Bob window.

### 3. Install and use skills

Skills are organized into five categories under `skills/`:

| Category | Folder | Purpose |
|---|---|---|
| Authoring | `skills/authoring/` | Creating BPMN processes, business objects, portal applications, and test suites |
| Documentation | `skills/documentation/` | Generating docs, dependency maps, and version diffs |
| Quality & compliance | `skills/quality-compliance/` | Code review, audit readiness, and compliance checking |
| Operations | `skills/operations/` | Runtime inspection, log diagnostics, and snapshot browsing |
| Administration | `skills/administration/` | Snapshot lifecycle management and server/environment config |

To use a skill, copy its folder from the appropriate category path into your project's `.bob/skills/` directory:

```
.bob/
  skills/
    <skill-folder>/
      SKILL.md
```

For example, to install `generate-baw-bpmn`:

```
skills/authoring/generate-baw-bpmn/  →  .bob/skills/generate-baw-bpmn/
```

Once installed, no explicit invocation is needed — just make a natural language request to Bob and it will dynamically load the relevant skill for your use case. Each skill's `SKILL.md` documents the kinds of requests that trigger it.

For more on Bob configuration, see the [IBM Bob documentation](https://bob.ibm.com/docs/ide).

## Available modes

| Mode | Description |
|---|---|
| [`IBM BAW Author`](modes/baw-author.yaml) | Full IBM BAW expert covering process authoring, BPEL-to-BPMN conversion, coach view development, service flow design, artifact analysis, and documentation. |
| [`IBM BAW Admin`](modes/baw-admin.yaml) | IBM BAW operations and administration assistant. Monitor, inspect, and act on running process instances — find failed/stuck/overdue/broken processes, retry, suspend, resume, terminate, or change due dates. Administer the BAW environment: deployments, snapshots, environment variables, containers, and health. Troubleshoot failures from runtime error logs, compare application versions across deployments, and assess process applications for audit readiness and compliance. |

## Available skills

### Authoring

| Skill | Description |
|---|---|
| [`generate-baw-bpmn`](skills/authoring/generate-baw-bpmn/) | Generates BPMN 2.0 XML that imports cleanly into IBM® BAW — processes and complex business object variables — from a process description, requirements doc, SOP, or existing config JSON. |
| [`generate-baw-business-objects`](skills/authoring/generate-baw-business-objects/) | Generates and modifies BAW Business Object import files — valid OpenAPI 3.0 JSON that IBM® BAW WebPD imports via the "Import business objects" option in the Data menu. |
| [`generate-baw-tests`](skills/authoring/generate-baw-tests/) | Generates and executes automated tests for an IBM® BAW process app, case application, or service flow — covering happy paths, alternative paths, edge cases, and Coach UI validation across two phases: test suite generation (Phase A) and end-to-end MCP execution (Phase B). |
| [`create-baw-portal`](skills/authoring/create-baw-portal/) | API-knowledge and portal-development skill for IBM BAW. Guides developers on which BAW REST APIs to use for portal builds, covering authentication, CORS, XSRF, pagination, and proxy configuration. Supports non-federated (WLE REST) and federated (PFS) environments. |

### Documentation

| Skill | Description |
|---|---|
| [`baw-project-doc`](skills/documentation/baw-project-doc/) | Generates comprehensive, up-to-date documentation for IBM® BAW applications by analyzing process models, services, integrations, business objects, and application artifacts — accepts a TWX export, a BPMN + XSD pair, or a ZIP archive. No MCP server or live server connection required. |
| [`baw-dependency-mapper`](skills/documentation/baw-dependency-mapper/) | Maps all usages and dependencies of a specified variable or Business Object (BO) across an entire IBM® BAW process application by analyzing the TWX export. Produces a dependency graph showing declarations, read/write usages, service I/O bindings, and coach bindings; detects circular BO references, redundant service calls, and over-coupling. |
| [`compare-baw-versions`](skills/documentation/compare-baw-versions/) | Compares two versions (snapshots or branches) of an IBM® BAW process application. Exports both and produces a structured diff by artifact type — process steps, gateways, variables, business objects, services, scripts, and configuration — flagging artifacts modified in both versions as conflict hints. |

### Quality & compliance

| Skill | Description |
|---|---|
| [`review-baw-code`](skills/quality-compliance/review-baw-code/) | Performs automated, severity-ranked code quality reviews across IBM® BAW artifacts — server scripts, coach scripts, integration service scripts, HTML, and CSS. Flags hardcoded values, undeclared variables, inconsistent error-logging patterns, synchronous `Thread.sleep` calls, unbounded loops, and other performance anti-patterns. Each finding includes the artifact name, location, rule violated, severity, and a recommended fix. |
| [`audit-baw-readiness`](skills/quality-compliance/audit-baw-readiness/) | Evaluates an IBM® BAW process application's design for compliance and audit readiness — scores six domains (traceability, separation of duties, access control, SLA/timeliness, data completeness, error handling) and produces a Markdown scorecard with specific gaps and remediation steps. |
| [`process-compliance-violation-detection`](skills/quality-compliance/process-compliance-violation-detection/) | Evaluates IBM® BAW and CP4BA process applications against compliance, governance, regulatory, business policy, architecture, or standards documents. Detects violations, gaps, risks, and missing controls, then recommends remediation using documented BAW/CP4BA platform capabilities. |

### Operations

| Skill | Description |
|---|---|
| [`inspect-baw-processes`](skills/operations/inspect-baw-processes/) | Finds, investigates, and acts on running IBM® BAW process instances — retry failed processes, suspend or resume instances, change due dates, drill into business data and task history. Covers the full Process Inspector workflow searching by status, app, owner, and date. |
| [`troubleshoot-baw-logs`](skills/operations/troubleshoot-baw-logs/) | Diagnoses IBM® BAW runtime failures by analyzing error logs, stack traces, and FFDC files. Identifies root causes, correlates entries across log types, and provides structured remediation steps for errors found in `SystemOut.log`, `messages.log`, `trace.log`, and Liberty FFDC files. |
| [`version-inspector`](skills/operations/version-inspector/) | Inspects IBM® BAW snapshots and browses deployed containers. Retrieves a plain-language metadata summary — version name, lifecycle status, creation date, and toolkit dependencies — for a specific snapshot. Also lists all Process Apps and Toolkits when the user doesn't know which container or snapshot to inspect. Works for Process Apps and Toolkits on BAW on-premises, BAW on Cloud, and CP4BA. |

### Administration

| Skill | Description |
|---|---|
| [`version-lifecycle-manager`](skills/administration/version-lifecycle-manager/) | Manages IBM® BAW Process App and Toolkit version lifecycle via the Operations REST API — installing apps, activating, deactivating, and deleting snapshots, and reading, setting, and syncing environment variables — no Process Admin Console needed. Supports BAW on-premises, BAW on Cloud, and CP4BA. |
| [`baw-endpoint-validation`](skills/administration/baw-endpoint-validation/) | Identifies what needs to change when an IBM® BAW process application is installed on a new server. Reads BPMConfig properties files to extract source and target endpoints, scans the TWX export for hardcoded references to the old server, and generates a validation report of findings. |

## License

This project is licensed under the [Apache License 2.0](LICENSE).
