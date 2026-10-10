# BAW Connection — standard procedure

---

## If the required MCP server is absent

Tell the user exactly this:

> "I don't see the required BAW MCP server connected. Would you like to:
> 1. **Reconnect** — connect your MCP server and I'll retry automatically, or
> 2. **REST mode** — I'll use the BAW REST API directly instead."

Wait for their choice before continuing.

- **Reconnect chosen:** wait for the user to confirm the server is connected, then re-check your tool list before proceeding. Do not assume it is connected — check again.
- **REST mode chosen:** ask for `{BAW_BASE_URL}` if not already known (see below), then consult `references/baw-rest.md` for endpoint URLs and request shapes.

---

## Detection rule

Check your tool list only. A tool that returns an error is not the same as a tool that is absent.
Do not switch to REST mode after a single failed call — only switch if the tool itself does not appear in your tool list.

---

## REST mode — BAW server URL

All paths in `references/baw-rest.md` are relative. Prepend `{BAW_BASE_URL}` to construct the full URL.

If the user has not provided their BAW server URL, ask before making any REST call:

> "What is your BAW server URL? (e.g. `https://baw.example.com:9443`)"

Store it as `{BAW_BASE_URL}` and use it for all subsequent REST calls in the session.
