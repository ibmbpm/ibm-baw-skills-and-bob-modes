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
  - [Required skills per mode](#required-skills-per-mode)
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

Skills are organized into two categories under `skills/`:

| Category | Folder | Scope |
|---|---|---|
| Authoring | `skills/authoring/` | Creating artifacts, generating documentation, and reviewing code quality and compliance |
| Administration & Operations | `skills/administration-operations/` | Deploying and configuring environments, managing snapshot lifecycles, and inspecting runtime health |

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

### Required skills per mode

Each mode relies on specific skills that must be present in your `.bob/skills/` folder. If a skill is missing, the mode will not be able to perform the associated function. When a missing skill is needed, the mode will tell you which skill to install and where to copy it from.

#### IBM BAW Author

| Skill | Source path in this repository | Purpose |
|---|---|---|
| `generate-baw-bpmn` | `skills/authoring/generate-baw-bpmn/` | Generate BPMN 2.0 XML importable into BAW |
| `generate-baw-business-objects` | `skills/authoring/generate-baw-business-objects/` | Generate BAW Business Object import files |
| `baw-project-doc` | `skills/authoring/baw-project-doc/` | Generate documentation from a TWX or BPMN + XSD |
| `generate-baw-tests` | `skills/authoring/generate-baw-tests/` | Generate and execute automated test suites |
| `test-baw-service-flows` | `skills/authoring/test-baw-service-flows/` | Generate and run test suites for Service Flows against a live environment |
| `review-baw-code` | `skills/authoring/review-baw-code/` | Code quality reviews of BAW JS, HTML, and CSS artifacts |
| `create-baw-portal` | `skills/authoring/create-baw-portal/` | Build or adapt custom BAW task portals |
| `create-baw-widget` | `skills/authoring/create-baw-widget/` | Scaffold, author, and package custom Coach View widgets into importable .twx toolkit files |
| `compare-baw-versions` | `skills/authoring/compare-baw-versions/` | Diff two snapshots or branches |
| `audit-baw-readiness` | `skills/authoring/audit-baw-readiness/` | Score a process app against compliance domains |
| `baw-dependency-mapper` | `skills/authoring/baw-dependency-mapper/` | Map BO and variable dependencies across a TWX |
| `baw-toolkit-analyzer` | `skills/authoring/baw-toolkit-analyzer/` | Analyze toolkit dependencies and upgrade impact from a TWX |
| `baw-endpoint-validation` | `skills/administration-operations/baw-endpoint-validation/` | Validate TWX endpoints before a server migration |
| `baw-export-import-helper` | `skills/administration-operations/baw-export-import-helper/` | Migrate process apps and toolkits between environments in the correct import order |
| `process-compliance-violation-detection` | `skills/authoring/process-compliance-violation-detection/` | Evaluate a process app against compliance documents |

#### IBM BAW Admin

| Skill | Source path in this repository | Purpose |
|---|---|---|
| `inspect-baw-processes` | `skills/administration-operations/inspect-baw-processes/` | Find, inspect, and act on running process instances |
| `troubleshoot-baw-logs` | `skills/administration-operations/troubleshoot-baw-logs/` | Diagnose runtime failures from BAW error logs |
| `compare-baw-versions` | `skills/authoring/compare-baw-versions/` | Diff two snapshots or branches |
| `audit-baw-readiness` | `skills/authoring/audit-baw-readiness/` | Score a process app against compliance domains |
| `version-lifecycle-manager` | `skills/administration-operations/version-lifecycle-manager/` | Activate, deactivate, delete snapshots; manage env vars |
| `version-inspector` | `skills/administration-operations/version-inspector/` | Browse containers and inspect snapshot metadata |
| `baw-container-inventory` | `skills/administration-operations/baw-container-inventory/` | List all Process Apps and Toolkits on a BAW server |
| `baw-deployment-manager` | `skills/administration-operations/baw-deployment-manager/` | Install and monitor snapshot deployments |
| `baw-endpoint-validation` | `skills/administration-operations/baw-endpoint-validation/` | Validate TWX endpoints before a server migration |


## Available skills

### Authoring

*Creating artifacts, generating documentation, and reviewing code quality and compliance.*

| Skill | Description |
|---|---|
| [`generate-baw-bpmn`](skills/authoring/generate-baw-bpmn/) | Generates BPMN 2.0 XML that imports cleanly into IBM® BAW — processes and complex business object variables — from a process description, requirements doc, SOP, or existing config JSON. |
| [`generate-baw-business-objects`](skills/authoring/generate-baw-business-objects/) | Generates and modifies BAW Business Object import files — valid OpenAPI 3.0 JSON that IBM® BAW WebPD imports via the "Import business objects" option in the Data menu. |
| [`generate-baw-tests`](skills/authoring/generate-baw-tests/) | Generates and executes automated tests for an IBM® BAW process app, case application, or service flow — covering happy paths, alternative paths, edge cases, and Coach UI validation across two phases: test suite generation (Phase A) and end-to-end MCP execution (Phase B). |
| [`test-baw-service-flows`](skills/authoring/test-baw-service-flows/) | Generates and executes automated test suites for IBM® BAW Service Flows against live BAW and CP4BA environments. Discovers the service flow, reads its input/output contract, and produces structured test cases covering happy path, error paths, and boundary conditions — then invokes the service and returns a structured pass/fail report. |
| [`create-baw-portal`](skills/authoring/create-baw-portal/) | API-knowledge and portal-development skill for IBM BAW. Guides developers on which BAW REST APIs to use for portal builds, covering authentication, CORS, XSRF, pagination, and proxy configuration. Supports non-federated (WLE REST) and federated (PFS) environments. |
| [`baw-project-doc`](skills/authoring/baw-project-doc/) | Generates comprehensive, up-to-date documentation for IBM® BAW applications by analyzing process models, services, integrations, business objects, and application artifacts — accepts a TWX export, a BPMN + XSD pair, or a ZIP archive. No MCP server or live server connection required. |
| [`baw-dependency-mapper`](skills/authoring/baw-dependency-mapper/) | Maps all usages and dependencies of a specified variable or Business Object (BO) across an entire IBM® BAW process application by analyzing the TWX export. Produces a dependency graph showing declarations, read/write usages, service I/O bindings, and coach bindings; detects circular BO references, redundant service calls, and over-coupling. |
| [`compare-baw-versions`](skills/authoring/compare-baw-versions/) | Compares two versions (snapshots or branches) of an IBM® BAW process application. Exports both and produces a structured diff by artifact type — process steps, gateways, variables, business objects, services, scripts, and configuration — flagging artifacts modified in both versions as conflict hints. |
| [`review-baw-code`](skills/authoring/review-baw-code/) | Performs automated, severity-ranked code quality reviews across IBM® BAW artifacts — server scripts, coach scripts, integration service scripts, HTML, and CSS. Flags hardcoded values, undeclared variables, inconsistent error-logging patterns, synchronous `Thread.sleep` calls, unbounded loops, and other performance anti-patterns. Each finding includes the artifact name, location, rule violated, severity, and a recommended fix. |
| [`audit-baw-readiness`](skills/authoring/audit-baw-readiness/) | Evaluates an IBM® BAW process application's design for compliance and audit readiness — scores six domains (traceability, separation of duties, access control, SLA/timeliness, data completeness, error handling) and produces a Markdown scorecard with specific gaps and remediation steps. |
| [`process-compliance-violation-detection`](skills/authoring/process-compliance-violation-detection/) | Evaluates IBM® BAW and CP4BA process applications against compliance, governance, regulatory, business policy, architecture, or standards documents. Detects violations, gaps, risks, and missing controls, then recommends remediation using documented BAW/CP4BA platform capabilities. |
| [`create-baw-widget`](skills/authoring/create-baw-widget/) | Scaffolds, authors, and packages custom Coach View widgets for IBM® BAW and CP4BA. Creates the full widget folder structure (Layout.html, InlineCSS.css, inlineJavascript.js, config.json, business objects, event handlers, and AdvancePreview files), then packages them into an importable `.twx` toolkit file using the bundled Python packaging toolkit. |
| [`baw-toolkit-analyzer`](skills/authoring/baw-toolkit-analyzer/) | Analyzes IBM® BAW toolkit dependencies from a TWX export. Maps direct and transitive toolkit dependencies, tracks snapshot versions, and flags missing, conflicting, circular, outdated, and unused dependencies. Supports where-used and what-uses analysis to assess upgrade impact before deployment. |

### Administration & Operations

*Deploying and configuring environments, managing snapshot lifecycles, and inspecting runtime health.*

| Skill | Description |
|---|---|
| [`baw-deployment-manager`](skills/administration-operations/baw-deployment-manager/) | Deploys IBM® BAW Process App and Toolkit snapshots to workflow environments via the REST API — lists available process apps, toolkits, snapshots, and servers, then installs and monitors deployment progress. Supports BAW on-premises, BAW on Cloud, and CP4BA. |
| [`version-lifecycle-manager`](skills/administration-operations/version-lifecycle-manager/) | Manages IBM® BAW Process App and Toolkit version lifecycle via the Operations REST API — installing apps, activating, deactivating, and deleting snapshots, and reading, setting, and syncing environment variables — no Process Admin Console needed. Supports BAW on-premises, BAW on Cloud, and CP4BA. |
| [`baw-endpoint-validation`](skills/administration-operations/baw-endpoint-validation/) | Identifies what needs to change when an IBM® BAW process application is installed on a new server. Reads BPMConfig properties files to extract source and target endpoints, scans the TWX export for hardcoded references to the old server, and generates a validation report of findings. |
| [`inspect-baw-processes`](skills/administration-operations/inspect-baw-processes/) | Finds, investigates, and acts on running IBM® BAW process instances — retry failed processes, suspend or resume instances, change due dates, drill into business data and task history. Covers the full Process Inspector workflow searching by status, app, owner, and date. |
| [`troubleshoot-baw-logs`](skills/administration-operations/troubleshoot-baw-logs/) | Diagnoses IBM® BAW runtime failures by analyzing error logs, stack traces, and FFDC files. Identifies root causes, correlates entries across log types, and provides structured remediation steps for errors found in `SystemOut.log`, `messages.log`, `trace.log`, and Liberty FFDC files. |
| [`version-inspector`](skills/administration-operations/version-inspector/) | Inspects IBM® BAW snapshots and browses deployed containers. Retrieves a plain-language metadata summary — version name, lifecycle status, creation date, and toolkit dependencies — for a specific snapshot. Also lists all Process Apps and Toolkits when the user doesn't know which container or snapshot to inspect. Works for Process Apps and Toolkits on BAW on-premises, BAW on Cloud, and CP4BA. |
| [`baw-container-inventory`](skills/administration-operations/baw-container-inventory/) | Inspects the container inventory of a live IBM® BAW server — lists, counts, and searches Process Apps and Toolkits by name or acronym, shows container metadata, and confirms whether a specific container exists. Read-only; no Workflow Center or Business Automation Studio needed. |
| [`baw-export-import-helper`](skills/administration-operations/baw-export-import-helper/) | Migrates IBM® BAW and CP4BA Process Apps, toolkits, case solutions, and Business Applications between environments, automatically resolving toolkit dependencies and determining the correct import order. Supports environment promotion (dev → test → prod), consolidation, and disaster recovery restores. |

## License

This project is licensed under the [Apache License 2.0](LICENSE).
