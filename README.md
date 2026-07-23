# IBM® Business Automation Workflow Skills and Bob Modes

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A growing collection of skills and IBM Bob modes that accelerate development with IBM® Business Automation Workflow.

## IBM Public Repository Disclosure

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

To use a skill, copy its folder from `skills/` into your project's `.bob/skills/` directory:

```
.bob/
  skills/
    <skill-folder>/
      SKILL.md
```

Once installed, no explicit invocation is needed — just make a natural language request to Bob and it will dynamically load the relevant skill for your use case. Each skill's `SKILL.md` documents the kinds of requests that trigger it.

For more on Bob configuration, see the [IBM Bob documentation](https://bob.ibm.com/docs/ide).

## Available modes

| Mode | Description |
|---|---|
| [`IBM BAW Author`](modes/baw-author.yaml) | Full IBM BAW expert covering process authoring, BPEL-to-BPMN conversion, coach view development, service flow design, artifact analysis, and documentation. |

## Available skills

| Skill | Description |
|---|---|
| [`generate-baw-bpmn`](skills/generate-baw-bpmn/) | Generates BPMN 2.0 XML that imports cleanly into IBM® BAW — processes and complex business object variables — from a process description, requirements doc, SOP, or existing config JSON. |

## License

This project is licensed under the [Apache License 2.0](LICENSE).
