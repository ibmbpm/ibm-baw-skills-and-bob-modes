# BAW Container Inventory — Documentation

> Inspect the container inventory of a live IBM BAW server — list all Process Apps and Toolkits, count them, search by name or acronym, view metadata, and confirm whether a specific container exists.

## Purpose

Inspect and query the container inventory of a live IBM Business Automation Workflow (BAW) server directly via the BAW REST API. This skill enables BAW administrators, operators, and developers to discover installed Process Apps and Toolkits, check counts, search for specific containers, or review metadata without logging into Workflow Center or Business Automation Studio. It is strictly read-only and never modifies or deletes server resources.

## Setup and configuration

- **BAW server URL:** Base URL of your BAW server (e.g., `https://baw.example.com:9443`) with no trailing slash.
- **BAW credentials:** Username and password for an account authorized on the BAW instance. The skill uses these in-session to acquire a cross-site request forgery (CSRF) token and never stores them permanently.
- **Network access:** Direct HTTP/HTTPS connectivity to the BAW server REST API endpoints.
- **Tools / runtime:** `curl` (for REST API communication) and `Python 3.x` (stdlib only, for running the deterministic processing script [`process_containers.py`](../scripts/process_containers.py)).
- **No MCP required:** The skill operates via the BAW REST API; no external MCP server connection is needed.

## Compatibility

- **BAW REST Operations API:** The skill requires access to the `/ops/system/login` and `/ops/std/bpm/containers` endpoints (BAW 22.x and later, including 26.x).
- **REST only:** The skill performs all server operations via HTTP calls and does not use MCP tools for container querying.
- **Role permissions:** Requires a BAW user with permissions to view Process Apps and Toolkits on the authoring or runtime server (**Workflow Center** or **Business Automation Studio** for authoring; Workflow Server for runtime-only environments).

## Prompt examples

### List all installed containers

**Prompt:**
> Please list all Process Apps and Toolkits installed on our BAW server.

**What to expect:** Bob prompts for the server URL and credentials if not already supplied, fetches all containers across paginated REST responses, and returns two structured tables (Process Apps and Toolkits) followed by a total count summary.

---

### Count installed containers

**Prompt:**
> Give me a breakdown and total count of all Process Apps and Toolkits on BAW.

**What to expect:** Bob fetches the full container inventory and outputs an inline count summary showing the exact number of Process Apps, Toolkits, and combined total.

---

### Filter by container type (Toolkits only)

**Prompt:**
> Show me only the toolkits available on our BAW environment.

**What to expect:** Bob queries the server with the toolkit type filter and displays a single Markdown table listing toolkit names and acronyms along with the toolkit count.

---

### Filter by container type (Process Apps only)

**Prompt:**
> List only the Process Applications installed on the system.

**What to expect:** Bob queries the server with the Process Application type filter and outputs a single Markdown table of Process Apps with the total process app count.

---

### Search by container name or acronym

**Prompt:**
> Find any containers related to "Claims" on our BAW server.

**What to expect:** Bob retrieves the container inventory, performs a case-insensitive search across names and acronyms, and returns matching Process Apps or Toolkits.

---

### Check container existence

**Prompt:**
> Is the "Customer Onboarding" Process App installed on this server?

**What to expect:** Bob checks the container inventory and provides a direct yes/no confirmation including the container name, acronym, and type.

---

### View metadata for a specific container

**Prompt:**
> Show me the details and metadata for the container with acronym CLAIMS.

**What to expect:** Bob retrieves details for the specified acronym and presents a human-readable labelled block containing name, acronym, type, ID, description, and creation metadata.

---

### Inspect container branches or track versions

**Prompt:**
> Show me the branches and versions available for the container "HSS".

**What to expect:** Bob calls the single-container endpoint with branch/version parameters and displays the track and version hierarchy in a formatted table.

---

### Out-of-scope lifecycle redirect (snapshot management)

**Prompt:**
> Can you activate snapshot v1.2.0 of the Hiring Sample Process App on this server?

**What to expect:** Bob identifies that snapshot lifecycle operations are out of scope for this read-only inventory skill and redirects you to the [`version-lifecycle-manager`](../../version-lifecycle-manager/docs/version-lifecycle-manager-doc.md) skill.

---

### Out-of-scope process instance redirect

**Prompt:**
> Show me all failed process instances for the Claims process application.

**What to expect:** Bob clarifies that runtime instance inspection is outside the scope of container inventory and directs you to the [`inspect-baw-processes`](../../inspect-baw-processes/docs/inspect-baw-processes-doc.md) skill.
