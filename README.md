# IBM® Business Automation Workflow Skills and Bob Modes

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A growing collection of skills and IBM Bob modes that accelerate development with IBM Business Automation Workflow.

## IBM public repository disclosure

All content in this repository including code has been provided by IBM under the associated open source software license and IBM is under no obligation to provide enhancements, updates, or support. IBM developers produced this code as an open source project (not as an IBM product), and IBM makes no assertions as to the level of quality nor security, and will not be maintaining this code going forward.

## Table of contents

- [Overview](#overview)
- [Concepts](#concepts)
  - [What is Bob?](#what-is-bob)
  - [Modes](#modes)
  - [Skills](#skills)
- [Prerequisites](#prerequisites)
- [Getting started](#getting-started)
  - [Quick install](#quick-install-recommended)
  - [Installer options](#installer-options)
  - [After installing](#after-installing)
- [BAW credentials and configuration](#baw-credentials-and-configuration)
- [Using with another AI agent](#using-with-another-ai-agent)
- [Available modes](#available-modes)
  - [Required skills per mode](#required-skills-per-mode)
- [Available skills](#available-skills)
- [License](#license)

## Overview

This repository provides ready-to-use Bob modes and skills that accelerate IBM Business Automation Workflow (BAW) development across a range of tasks. It works with:

- [IBM Business Automation Workflow](https://www.ibm.com/products/business-automation-workflow)
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

## Getting Started

To use these skills with **IBM Bob**, follow the instructions below. To use them with another AI agent, see [Using with another AI agent](#using-with-another-ai-agent).

### Quick install (recommended)

Clone this repository and run the installer in a single command:

**macOS / Linux — one line:**
```bash
git clone https://github.com/ibmbpm/ibm-baw-skills-and-bob-modes.git && cd ibm-baw-skills-and-bob-modes && ./install.sh
```

**Windows (PowerShell 5.1+) — one line:**
```powershell
git clone https://github.com/ibmbpm/ibm-baw-skills-and-bob-modes.git; cd ibm-baw-skills-and-bob-modes; .\install.ps1
```

> **What this does:**
> 1. Clones the repository and checks Python prerequisites (`pyyaml`, `lxml`).
> 2. Copies all skills from this repository to your global Bob skills directory (`~/.bob/skills/`).
> 3. Safely merges Bob modes into your custom modes files (`~/.bob/settings/custom_modes.yaml` for Bob IDE and `~/.bob/custom_modes.yaml` for Bob Shell) without overwriting existing modes.
> 4. Generates a `.env` template for your BAW credentials.

Skills are organized into two categories under `skills/`:

| Category | Folder | Scope |
|---|---|---|
| Authoring | `skills/authoring/` | Creating artifacts, generating documentation, and reviewing code quality and compliance |
| Administration and Operations | `skills/administration-operations/` | Deploying and configuring environments, managing snapshot lifecycles, and inspecting runtime health |

---

### Installer options

Run the script with flags from the repository root for more control:

**macOS / Linux:**
```bash
./install.sh --scope project                           # install into current project's .bob/
./install.sh --dry-run                                 # preview what would be installed
./install.sh --skills "generate-baw-bpmn,inspect-baw-processes"  # specific skills only
./install.sh --uninstall                               # remove all BAW skills and modes
./install.sh --help                                    # full usage
```

**Windows (PowerShell 5.1+):**
```powershell
.\install.ps1 -Scope project                           # install into current project's .bob\
.\install.ps1 -DryRun                                  # preview without writing files
.\install.ps1 -Skills "generate-baw-bpmn,inspect-baw-processes"  # specific skills only
.\install.ps1 -Uninstall                               # remove all BAW skills and modes
```

### After installing

1. Open your BAW project as your workspace in Bob.
2. Configure your BAW credentials in `.env` (see [BAW credentials and configuration](#baw-credentials-and-configuration)).
3. Use the mode selector at the bottom of the Bob chat to switch to **IBM BAW Author** or **IBM BAW Admin** mode. If a mode doesn't appear, confirm the modes were merged into the custom modes file for your install scope, then reload the Bob window:
   - **Global install (default):** `~/.bob/settings/custom_modes.yaml` (Bob IDE) and `~/.bob/custom_modes.yaml` (Bob Shell)
   - **Project install (`--scope project`):** `.bob/custom_modes.yaml` in your project
4. Make a natural-language request. No explicit skill invocation is needed. For example:

> "Generate a BAW BPMN process for expense approvals."

Bob picks up the skill automatically from your `~/.bob/skills/` folder. Skills are also referenced by their Bob mode — you don't need to name the skill explicitly. Skills are self-contained and work independently of any mode.

---

## BAW Credentials and Configuration

Several skills connect to a live BAW environment via the REST API. The installer creates a `.env` file template automatically.

### .env setup

Open `.env` (located in the directory where you ran the installer, or in your Bob workspace) and fill in the three values:

| Variable | Description |
|---|---|
| `BAW_BASE_URL` | Base URL of your BAW server, no trailing slash (e.g. `https://baw.example.com:9443` for standalone BAW, `https://cpd.example.com/bas` for CP4BA authoring) |
| `BAW_USERNAME` | Username of a BAW account with sufficient permissions |
| `BAW_PASSWORD` | Password for that account |

Skills read these values automatically at runtime. You will only be prompted if a value is missing or still contains a placeholder.

### Example configuration

```dotenv
# IBM® BAW Skills and Bob Modes — Environment Configuration
#
# Fill in the three values below before using BAW skills that connect
# to a live BAW environment.
#
# NEVER commit this file to source control — it is listed in .gitignore.

# Base URL of your BAW server (no trailing slash)
BAW_BASE_URL=https://your-baw-server.example.com:9443

# BAW credentials (used by skills that call the BAW REST API)
BAW_USERNAME=your-username
BAW_PASSWORD=your-password
```

### Credential security

- **Never commit `.env`.** The file is listed in `.gitignore`. If you accidentally staged it, run `git rm --cached .env`.
- **Do not hard-code credentials in scripts or skill files.** All skills read from `.env` exclusively.

---

## Using with Another AI Agent

If you are not using IBM Bob, clone the repository and copy the skills folder into whatever directory your agent loads skills from. Replace `<your-skills-directory>` with the path your agent uses (for example, `~/.claude/skills/`):

**macOS / Linux:**
```bash
git clone https://github.com/ibmbpm/ibm-baw-skills-and-bob-modes.git
cp -r ibm-baw-skills-and-bob-modes/skills/* <your-skills-directory>/
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/ibmbpm/ibm-baw-skills-and-bob-modes.git
Copy-Item -Recurse ibm-baw-skills-and-bob-modes\skills\* <your-skills-directory>\
```

For skills that connect to a live BAW environment, create a `.env` file in the directory your agent runs commands from. Copy `.env.example` and fill in the values — see [BAW credentials and configuration](#baw-credentials-and-configuration). Your agent must be able to run shell commands, because skills read credentials from `.env` with `grep`.

---

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
| `create-baw-external-task-ui` | `skills/authoring/create-baw-external-task-ui/` | Generate a React + Express external task UI for BAW Custom URL human tasks |
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
| [`generate-baw-bpmn`](skills/authoring/generate-baw-bpmn/) | Generates BPMN 2.0 XML that imports cleanly into IBM BAW — processes and complex business object variables — from a process description, requirements doc, SOP, or existing config JSON. |
| [`generate-baw-business-objects`](skills/authoring/generate-baw-business-objects/) | Generates and modifies BAW Business Object import files — valid OpenAPI 3.0 JSON that IBM BAW WebPD imports via the "Import business objects" option in the Data menu. |
| [`generate-baw-tests`](skills/authoring/generate-baw-tests/) | Generates and executes automated tests for an IBM BAW process app, case application, or service flow — covering happy paths, alternative paths, edge cases, and Coach UI validation across two phases: test suite generation (Phase A) and end-to-end MCP execution (Phase B). |
| [`test-baw-service-flows`](skills/authoring/test-baw-service-flows/) | Generates and executes automated test suites for IBM BAW Service Flows against live BAW and CP4BA environments. Discovers the service flow, reads its input/output contract, and produces structured test cases covering happy path, error paths, and boundary conditions — then invokes the service and returns a structured pass/fail report. |
| [`create-baw-portal`](skills/authoring/create-baw-portal/) | Provides API knowledge and portal development guidance for IBM BAW. Guides developers on which BAW REST APIs to use for portal builds, covering authentication, CORS, XSRF, pagination, and proxy configuration. Supports non-federated (WLE REST) and federated (PFS) environments. |
| [`baw-project-doc`](skills/authoring/baw-project-doc/) | Generates comprehensive, up-to-date documentation for IBM BAW applications by analyzing process models, services, integrations, business objects, and application artifacts — accepts a TWX export, a BPMN + XSD pair, or a ZIP archive. No MCP server or live server connection required. |
| [`baw-dependency-mapper`](skills/authoring/baw-dependency-mapper/) | Maps all usages and dependencies of a specified variable or Business Object (BO) across an entire IBM BAW process application by analyzing the TWX export. Produces a dependency graph showing declarations, read/write usages, service I/O bindings, and coach bindings; detects circular BO references, redundant service calls, and over-coupling. |
| [`compare-baw-versions`](skills/authoring/compare-baw-versions/) | Compares two versions (snapshots or branches) of an IBM BAW process application. Exports both and produces a structured diff by artifact type — process steps, gateways, variables, business objects, services, scripts, and configuration — flagging artifacts modified in both versions as conflict hints. |
| [`review-baw-code`](skills/authoring/review-baw-code/) | Performs automated, severity-ranked code quality reviews across IBM BAW artifacts — server scripts, coach scripts, integration service scripts, HTML, and CSS. Flags hardcoded values, undeclared variables, inconsistent error-logging patterns, synchronous `Thread.sleep` calls, unbounded loops, and other performance anti-patterns. Each finding includes the artifact name, location, rule violated, severity, and a recommended fix. |
| [`audit-baw-readiness`](skills/authoring/audit-baw-readiness/) | Evaluates an IBM BAW process application's design for compliance and audit readiness — scores six domains (traceability, separation of duties, access control, SLA/timeliness, data completeness, error handling) and produces a Markdown scorecard with specific gaps and remediation steps. |
| [`process-compliance-violation-detection`](skills/authoring/process-compliance-violation-detection/) | Evaluates IBM BAW and CP4BA process applications against compliance, governance, regulatory, business policy, architecture, or standards documents. Detects violations, gaps, risks, and missing controls, then recommends remediation using documented BAW/CP4BA platform capabilities. |
| [`create-baw-widget`](skills/authoring/create-baw-widget/) | Scaffolds, authors, and packages custom Coach View widgets for IBM BAW and CP4BA. Creates the full widget folder structure (Layout.html, InlineCSS.css, inlineJavascript.js, config.json, business objects, event handlers, and AdvancePreview files), then packages them into an importable `.twx` toolkit file using the bundled Python packaging toolkit. |
| [`create-baw-external-task-ui`](skills/authoring/create-baw-external-task-ui/) | Generates a custom external task UI for an IBM BAW human task configured with a Custom URL — a Node.js Express server with a React (default) or user-specified frontend, styled with Carbon, that fetches task data from the BAW `/bpm/user-tasks` REST API and completes the task on submission. Accepts a verbal field description or an exported task schema file, and includes instructions for exporting the schema and setting the External Implementation URL with `{tw.system.task_id}`. |
| [`baw-toolkit-analyzer`](skills/authoring/baw-toolkit-analyzer/) | Analyzes IBM BAW toolkit dependencies from a TWX export. Maps direct and transitive toolkit dependencies, tracks snapshot versions, and flags missing, conflicting, circular, outdated, and unused dependencies. Supports where-used and what-uses analysis to assess upgrade impact before deployment. |

### Administration and Operations

*Deploying and configuring environments, managing snapshot lifecycles, and inspecting runtime health.*

| Skill | Description |
|---|---|
| [`baw-deployment-manager`](skills/administration-operations/baw-deployment-manager/) | Deploys IBM BAW Process App and Toolkit snapshots to workflow environments via the REST API — lists available process apps, toolkits, snapshots, and servers, then installs and monitors deployment progress. Supports BAW on-premises, BAW on Cloud, and CP4BA. |
| [`version-lifecycle-manager`](skills/administration-operations/version-lifecycle-manager/) | Manages IBM BAW Process App and Toolkit version lifecycle via the Operations REST API — installing apps, activating, deactivating, and deleting snapshots, and reading, setting, and syncing environment variables — no Process Admin Console needed. Supports BAW on-premises, BAW on Cloud, and CP4BA. |
| [`baw-endpoint-validation`](skills/administration-operations/baw-endpoint-validation/) | Identifies what needs to change when an IBM BAW process application is installed on a new server. Reads BPMConfig properties files to extract source and target endpoints, scans the TWX export for hardcoded references to the old server, and generates a validation report of findings. |
| [`inspect-baw-processes`](skills/administration-operations/inspect-baw-processes/) | Finds, investigates, and acts on running IBM BAW process instances — retry failed processes, suspend or resume instances, change due dates, drill into business data and task history. Covers the full Process Inspector workflow searching by status, app, owner, and date. |
| [`troubleshoot-baw-logs`](skills/administration-operations/troubleshoot-baw-logs/) | Diagnoses IBM BAW runtime failures by analyzing error logs, stack traces, and FFDC files. Identifies root causes, correlates entries across log types, and provides structured remediation steps for errors found in `SystemOut.log`, `messages.log`, `trace.log`, and Liberty FFDC files. |
| [`version-inspector`](skills/administration-operations/version-inspector/) | Inspects IBM BAW snapshots and browses deployed containers. Retrieves a plain-language metadata summary — version name, lifecycle status, creation date, and toolkit dependencies — for a specific snapshot. Also lists all Process Apps and Toolkits when the user does not know which container or snapshot to inspect. Works for Process Apps and Toolkits on BAW on-premises, BAW on Cloud, and CP4BA. |
| [`baw-container-inventory`](skills/administration-operations/baw-container-inventory/) | Inspects the container inventory of a live IBM BAW server — lists, counts, and searches Process Apps and Toolkits by name or acronym, shows container metadata, and confirms whether a specific container exists. Read-only; no Workflow Center or Business Automation Studio needed. |
| [`baw-export-import-helper`](skills/administration-operations/baw-export-import-helper/) | Migrates IBM BAW and CP4BA Process Apps, toolkits, case solutions, and Business Applications between environments, automatically resolving toolkit dependencies and determining the correct import order. Supports environment promotion (dev → test → prod), consolidation, and disaster recovery restores. |

## License

This project is licensed under the [Apache License 2.0](LICENSE).
