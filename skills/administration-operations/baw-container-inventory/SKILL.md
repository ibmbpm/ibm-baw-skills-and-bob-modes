---
name: baw-container-inventory
description: "Inspect the container inventory of a live IBM BAW server — list all Process Apps and Toolkits, count them, search by name or acronym, view metadata, and confirm whether a specific container exists. Use when a BAW administrator wants to know what is installed on a server without opening Workflow Center (traditional BAW) or Business Automation Studio (CP4BA containerized). Trigger phrases: 'list process apps', 'list toolkits', 'what containers are installed', 'how many process apps', 'does this app exist', 'find container', 'show me the toolkits', 'container inventory', 'what's installed in BAW', 'show container details', 'look up acronym'. This skill is read-only — it queries and reports. For snapshot lifecycle operations use version-lifecycle-manager; for running process instances use inspect-baw-processes."
license: Apache-2.0
compatibility: "IBM BAW 22.x and later; IBM CP4BA 22.x and later"
allowed-tools:
  - Read
  - Bash
metadata:
  version: "1.0.0"
  display_name: BAW Container Inventory
  short_description: List and search all Process Apps and Toolkits installed on a live IBM BAW server without opening Workflow Center or Business Automation Studio.
  author: IBM BAW Team
---

> **⚠️ REST only — MCP is not supported by this skill.** All BAW interactions use the BAW REST API exclusively via HTTP calls to `{BAW_BASE_URL}`. Do not call any MCP tools at any point — regardless of whether an MCP server is connected or not. Never tell the user to connect an MCP server; this skill does not use one. If you find yourself reaching for an MCP tool, stop and use the REST equivalent from `references/baw-rest.md` instead.

# BAW Container Inventory

Inspect the container inventory of a live IBM BAW server — list all Process Apps and Toolkits, count them, search by name or acronym, view metadata, and confirm whether a specific container exists. No Workflow Center (traditional BAW) or Business Automation Studio (CP4BA containerized) access required.

This skill is **read-only**. It queries and reports — it never creates, archives, or deletes containers.

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
| `login` | `POST /ops/system/login` — obtain CSRF token and session |
| `list containers` | `GET /ops/std/bpm/containers` — list all containers; supports `type`, `ids`, `offset`, `size`, `optional_parts` |
| `get container` | `GET /ops/std/bpm/containers/{container}` — fetch one container by acronym; supports `optional_parts=branches` or `optional_parts=versions` |

All calls after login require `BPMCSRFToken` header and session cookie.

---

## Steps

### Step 0 — Establish the BAW connection

Ask for the server URL and credentials together in a single turn:
> *"Before I get started, I need two things:*
> *1. Your BAW server URL — no trailing slash (e.g. `https://baw.example.com:9443`)*
> *2. Your BAW username and password*
>
> *Your credentials are only used to obtain a session token for this conversation — they are not stored anywhere."*

Once the user replies, store `{BAW_BASE_URL}`, `{BAW_USER}`, and `{BAW_PASS}` for the session. Then immediately acquire the CSRF token.

Use `curl` for all REST calls. On Windows, PowerShell's built-in `curl` is an alias for `Invoke-WebRequest` — always use `cmd /c "curl ..."` on Windows to invoke the real curl executable. Write the JSON body to a temp file before POSTing on Windows to avoid shell quoting issues. Use both snippets below — pick the one that matches the platform:

```bash
# macOS / Linux
curl -sk -X POST "{BAW_BASE_URL}/ops/system/login" \
  -u "{BAW_USER}:{BAW_PASS}" \
  -H "Content-Type: application/json" \
  -d '{"refresh_groups": false}'
```

```powershell
# Windows — write body to temp file first, then POST
Set-Content -Path "$env:TEMP\baw_login.json" -Value '{"refresh_groups": false}'
cmd /c "curl -sk -X POST {BAW_BASE_URL}/ops/system/login -u {BAW_USER}:{BAW_PASS} -H ""Content-Type: application/json"" -d @%TEMP%\baw_login.json"
```

On success (HTTP 201): extract `csrf_token` from the JSON response body and store it as `{BAW_CSRF}`. Discard the raw credentials immediately. Never ask again.

If login returns 401 or 400, tell the user their credentials were not accepted and ask them to re-enter — do not proceed until login succeeds.

---

### Step 1 — Understand what the user wants

Before fetching anything, identify which of these the user is asking for:

| Request type | API call | Output |
|---|---|---|
| List all containers | `GET /ops/std/bpm/containers` (no filter) | Two tables (Process Apps, Toolkits) + count summary derived from the response |
| List only Process Apps | `GET /ops/std/bpm/containers?type=PA` | One table of Process Apps + count derived from the response |
| List only Toolkits | `GET /ops/std/bpm/containers?type=TK` | One table of Toolkits + count derived from the response |
| Total count (PA + TK + combined) | `GET /ops/std/bpm/containers` (no filter) | Count summary line only — no table. Partition response: `toolkit: false` → PA count, `toolkit: true` → TK count |
| Count only Process Apps | `GET /ops/std/bpm/containers?type=PA` | Count line only — no table: "X Process Apps" |
| Count only Toolkits | `GET /ops/std/bpm/containers?type=TK` | Count line only — no table: "X Toolkits" |
| Search by name or acronym | `GET /ops/std/bpm/containers` (no filter) | Match client-side after a single fetch |
| Existence check | `GET /ops/std/bpm/containers` (no filter) | Search result in memory — no second call needed |
| Basic metadata for a specific container | `GET /ops/std/bpm/containers` (no filter) | Standard response includes all metadata fields |
| Branches or versions for a specific container | `GET /ops/std/bpm/containers/{ACRONYM}?optional_parts=branches` | Single targeted call only when explicitly requested |

**Do not repeat an identical REST call** within the same request. If you have already fetched all containers and the user's request can be satisfied from that response, re-use it — do not call the same endpoint with the same parameters again.

---

### Step 2 — Fetch containers

Each curl snippet below is shown in both macOS/Linux and Windows form. Use the form that matches the platform. On Windows always use `cmd /c "curl ..."` — never call `curl` directly from PowerShell.

#### Fetching all pages — mandatory for list and count requests

The API returns a maximum of 100 items per call. Always paginate to retrieve the full inventory before processing. Use `size=100` to minimise round-trips. Repeat with increasing `offset` until the `next` field in the response is `null` — that is the last page. Save each page's response to a file, then merge all pages into a single JSON array for the script to process.

**Page fetch — macOS / Linux** (increment `offset` by 100 each time):
```bash
curl -sk -X GET "{BAW_BASE_URL}/ops/std/bpm/containers?size=100&offset=0" \
  -u "{BAW_USER}:{BAW_PASS}" \
  -H "BPMCSRFToken: {BAW_CSRF}" \
  -o /tmp/baw_page0.json
```

**Page fetch — Windows** (increment `offset` by 100 each time):
```powershell
cmd /c "curl -sk -X GET ""{BAW_BASE_URL}/ops/std/bpm/containers?size=100&offset=0"" -u {BAW_USER}:{BAW_PASS} -H ""BPMCSRFToken: {BAW_CSRF}"" -o %TEMP%\baw_page0.json"
```

If `next` is not `null` in the response, fetch the next page (`offset=100`, `offset=200`, …) saving each to its own file. When `next` is `null`, all pages are collected.

**With type filter** (`PA` or `TK`) — same pagination rule, add `?type=PA` or `?type=TK`:
```bash
curl -sk -X GET "{BAW_BASE_URL}/ops/std/bpm/containers?type=PA&size=100&offset=0" \
  -u "{BAW_USER}:{BAW_PASS}" \
  -H "BPMCSRFToken: {BAW_CSRF}" \
  -o /tmp/baw_page0.json
```

**Single container by acronym** (no pagination):
```bash
# macOS / Linux
curl -sk -X GET "{BAW_BASE_URL}/ops/std/bpm/containers/{ACRONYM}" \
  -u "{BAW_USER}:{BAW_PASS}" \
  -H "BPMCSRFToken: {BAW_CSRF}"
```
```powershell
# Windows
cmd /c "curl -sk -X GET ""{BAW_BASE_URL}/ops/std/bpm/containers/{ACRONYM}"" -u {BAW_USER}:{BAW_PASS} -H ""BPMCSRFToken: {BAW_CSRF}"""
```

Append `?optional_parts=branches` or `?optional_parts=versions` when branches or versions are needed. Replace `{ACRONYM}` with the actual container acronym. The single-container call response can be read directly — no script needed.

---

### Step 2b — Process the response with the script

**Do not count or format containers by reading the raw JSON yourself.** Use `scripts/process_containers.py` for all list, count, and search operations. The script counts deterministically and formats the Markdown tables — this avoids the miscounting that occurs when an LLM reads large JSON arrays.

The script accepts one or more page files as arguments and merges them automatically. There is no separate merge step.

**Run the script** with the appropriate `--mode`, passing all page files as arguments:

| User request | Mode flag |
|---|---|
| List all containers (PA + TK) | `--mode list` |
| List only Process Apps | `--mode pa` |
| List only Toolkits | `--mode tk` |
| Count (any combination) | `--mode count` |

**Single page (most common case):**
```bash
# macOS / Linux
python3 scripts/process_containers.py /tmp/baw_page0.json --mode list
```
```powershell
# Windows
python3 scripts/process_containers.py $env:TEMP\baw_page0.json --mode list
```

**Multiple pages** — pass all files as space-separated arguments:
```bash
# macOS / Linux
python3 scripts/process_containers.py /tmp/baw_page0.json /tmp/baw_page1.json --mode list
```
```powershell
# Windows
python3 scripts/process_containers.py $env:TEMP\baw_page0.json $env:TEMP\baw_page1.json --mode list
```

Use `$env:TEMP` on Windows (PowerShell environment variable syntax) — never use `%TEMP%` inside a Python command or script argument, as Python does not expand Windows environment variables.

Present the script's stdout directly to the user. Do not recount, reformat, or summarise the numbers yourself — the script output is the authoritative result.

**For name/acronym searches and existence checks:** run with `--mode list`, then filter the script output rows by the search term. Do not re-read the raw JSON file to search.

**For basic metadata** on a specific container: call `GET /containers/{ACRONYM}` directly (no script needed) and present the returned fields as a labelled block.

#### Name-based searches

After running the script in `--mode list`, search the output rows for the user's term. Match case-insensitively against both the Name and Acronym columns. If no match is found, say so clearly.

---

### Step 3 — Present results

Present the output from `scripts/process_containers.py` directly. The script produces correctly formatted Markdown tables and accurate counts — do not reformat or recount anything.

#### Output format by mode

**`--mode list`** — two headed tables followed by a count summary:
```
### Process Apps

| Name                     | Acronym |
|--------------------------|---------|
| Hiring Sample            | HSS     |
| Old Invoicing (Archived) | OIA     |

### Toolkits

| Name        | Acronym |
|-------------|---------|
| System Data | SYSDATA |

2 Process Apps, 1 Toolkit (3 total)
```

**`--mode count`** — count summary line only, no tables:
```
46 Process Apps, 13 Toolkits (59 total)
```

**`--mode pa`** or **`--mode tk`** — single table for that type plus its count.

#### Large result sets

If the total exceeds 25 containers, ask the user whether they want the full output in chat or written to a `.md` file. Default to file. Write the script output to the file as-is.

#### Existence check
Answer directly first, then provide details:
> *"✅ **Hiring Sample** (HSS) exists — it is a **Process App**."*
> *"❌ No container named 'Legacy Payroll' was found."*

If not found, list available containers so the user can check for a similar name.

#### Basic metadata view (single container)
Use a labelled block — not a one-line table row:
```
**Name:** Hiring Sample
**Acronym:** HSS
**Type:** Process App
**ID:** 2066.a26f1…
**Description:** Sample process for hiring workflow
**Created:** 2024-03-15
**Created by:** admin
```

#### Branches or versions
When `optional_parts=branches` or `optional_parts=versions` is requested for a specific container, present the data as a nested table under the container header. Keep it readable — do not dump the raw JSON.

---

### Step 4 — Errors

| Situation | What to say |
|---|---|
| 401 on any call after login | "Your session may have expired. Let me re-authenticate." Re-run Step 0. |
| 403 | "You may not have sufficient permissions for this operation. Check that your account has the BAW admin role." |
| 404 on `get container` | "Container '[acronym]' was not found on the server. Confirm the acronym is correct." |
| Network or timeout error | State what failed and ask: "Would you like me to retry, or would you prefer to check the server URL?" |

Never display raw JSON, stack traces, or internal error objects to the user.

---

## Boundaries

**In scope:**
- Listing all containers (Process Apps and Toolkits)
- Total counts and PA vs TK breakdown counts
- Searching and filtering by name or acronym
- Displaying basic metadata per container
- Confirming whether a specific container exists
- Showing branches or versions for a specific container when requested

**Out of scope — redirect to the appropriate skill:**
- Installing, activating, deactivating, or deleting snapshots → `version-lifecycle-manager`
- Inspecting or acting on running process instances → `inspect-baw-processes`
- Auditing a process app for compliance → `audit-baw-readiness`
- Generating BPMN processes or Business Objects → `generate-baw-bpmn`, `generate-baw-business-objects`
- Calling any MCP tools — this skill is REST only

---

## Output format summary

| Output type | Format |
|---|---|
| Container list | Markdown table: Name, Acronym, Type |
| Count | Inline summary: "X Process Apps, Y Toolkits (Z total)" |
| Existence check | Direct yes/no answer with name, acronym, and type |
| Basic metadata | Labelled key/value block |
| Branches / versions | Nested table under container header |
| Large result sets | File output (`.md`) when > 25 items or when metadata-heavy |

Never output raw JSON. Never expose internal field names like `toolkit`, `container_name`, or `creator_user_id` as labels — always use human-readable equivalents.
