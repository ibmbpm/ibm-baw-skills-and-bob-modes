# Business Automation Workflow Connection — standard procedure

This file is shared across all Business Automation Workflow skills. Do not modify it per skill.
Copy it into `references/BAW_CONNECTION.md` in your skill folder.

The skill-specific details (which MCP server, which sentinel tool) are declared
in the `## Execution mode` block in `SKILL.md` — Bob has already read them before
loading this file.

---

## If the required MCP server is absent

Tell the user exactly this:

> "I don't see the required Business Automation Workflow MCP server connected. Would you like to:
> 1. **Reconnect** — connect your MCP server and I'll retry automatically, or
> 2. **REST mode** — I'll use the Business Automation Workflow REST API directly instead."

Wait for their choice before continuing.

- **Reconnect chosen:** wait for the user to confirm the server is connected, then re-check your tool list before proceeding. Do not assume it is connected — check again.
- **REST mode chosen:** ask for `{BAW_BASE_URL}` if not already known (see below), then consult `references/baw-rest.md` for endpoint URLs and request shapes.

---

## Detection rule

Check your tool list only. A tool that returns an error is not the same as a tool that is absent.
Do not switch to REST mode after a single failed call — only switch if the tool itself does not appear in your tool list.

---

## REST mode — Business Automation Workflow server URL

All paths in `references/baw-rest.md` are relative. Prepend `{BAW_BASE_URL}` to construct the full URL.

If the user has not provided their Business Automation Workflow server URL, ask before making any REST call:

> "What is your Business Automation Workflow server URL? (e.g. `https://baw.example.com:9443`)"

Store it as `{BAW_BASE_URL}` and use it for all subsequent REST calls in the session.
