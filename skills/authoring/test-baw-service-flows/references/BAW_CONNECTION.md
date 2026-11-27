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

## REST mode — Business Automation Workflow server URL and environment resolution

All paths in `references/baw-rest.md` are relative. Prepend `{BAW_BASE_URL}` to construct the full URL.

### Base URL Patterns
- **On-premises / Standalone containers:** `{BAW_BASE_URL}` = `https://<host>:<port>` (for example, `https://baw.example.com:9443`). Paths follow `/ops/...`, `/bpm/...`, `/rest/bpm/wle/v1/...`.
- **Cloud Pak for Business Automation:** `{BAW_BASE_URL}` includes the deployment instance route prefix:
  - Studio / Workflow Authoring: `https://<cpd-host>/bas`
  - Runtime instances: `https://<cpd-host>/baw-<instance>` (for example, `/baw-aut`, `/baw-dev`, `/baw-bawins1`)
  Full API paths are appended directly: `{BAW_BASE_URL}/ops/...`, `{BAW_BASE_URL}/bpm/...`, etc.

### Cloud Pak for Business Automation — Disambiguate authoring vs runtime before proceeding

When the user provides a Cloud Pak for Business Automation URL, identify which type it is **before making any API call**:

| URL contains | Environment type | Can run tests? |
|---|---|---|
| `/bas` | Workflow Authoring (BAS) — has integrated playback server | ✅ Yes — use BAS playback server (no deployed snapshot needed) |
| `/baw-<anything>` | Workflow Runtime — execution-capable | ✅ Yes |
| No path segment | Ambiguous — check by calling `GET /bas/ops/std/bpm/servers/workflow` | See below |

If the URL has no path segment (for example, `https://cpd-demo.example.com/`) and you cannot determine the type from context, call:
```
GET https://<cpd-host>/bas/ops/std/bpm/servers/workflow
  Authorization: Bearer <zen_token>
```
- `"servers": []` → Workflow Authoring only (BAS playback server available). Proceed directly — do **not** ask the user for a runtime URL. Inform them: *"This is an authoring-only environment. I'll use the integrated playback server."*
- `"servers": [...]` → Workflow Authoring with connected runtime(s). Ask the user which runtime to target, or use the first entry's URL.

**When the user provides a BAS URL and no runtime URL is known:** Do not ask for a runtime URL. Use the BAS playback server. Only ask if the user explicitly states they want to test against a deployed runtime snapshot.

> **Cloud Pak for Business Automation multi-cluster deployments — BAS and runtime may be on completely different hostnames.** On some Cloud Pak for Business Automation installations the Workflow Authoring cluster (`/bas`) and the Business Automation Workflow runtime cluster (`/baw-<instance>`) are deployed on entirely separate OpenShift clusters with different base hostnames — not just different path segments of the same host. For example:
> - BAS: `https://cpd-demo-project.apps.**baas**.cp.fyre.ibm.com/bas`
> - Runtime: `https://cpd-demo-project.apps.**buis**.cp.fyre.ibm.com/baw-bawins1`
>
> Symptoms of this topology:
> - Attempting `POST https://<runtime-host>/bas/ops/system/login` returns HTTP 404.
> - The Zen token obtained from `<runtime-host>/v1/preauth/validateAuth` is **not** accepted by the BAS cluster (different IAM domain).
>
> When you observe a 404 on the BAS login path at the runtime host, ask the user:
> *"It looks like your Workflow Authoring (BAS) is on a different cluster from the runtime. What is the BAS URL? — it will be a completely different hostname, not just a different path segment of `<runtime-host>`."*
>
> Once the BAS host is confirmed, obtain a **separate** Zen token from `GET https://<bas-host>/v1/preauth/validateAuth` — do not reuse the runtime token.

### Authentication and token acquisition

> **Cross-platform HTTP — always use Python stdlib `urllib` for all HTTP calls.** Never use `curl` or PowerShell for REST calls — Python is available on all supported platforms (Windows, macOS, Linux) and avoids shell quoting and alias incompatibilities. No third-party packages are needed. For Cloud Pak for Business Automation environments with self-signed or private CA certificates, disable certificate verification:
> ```python
> import ssl
> ctx = ssl.create_default_context()
> ctx.check_hostname = False
> ctx.verify_mode = ssl.CERT_NONE
> # pass ctx= to every urllib.request.urlopen() call
> ```

- **On-premises / Containers:** HTTP Basic auth on `POST {BAW_BASE_URL}/ops/system/login` to obtain `{BAW_CSRF}` and session cookies (`LtpaToken2`, `JSESSIONID`).
- **Cloud Pak for Business Automation (Zen IAM):**
  1. Obtain Zen JWT access token via `GET https://<cpd-host>/v1/preauth/validateAuth` with Basic auth (`username:password`).
  2. Exchange for CSRF token via `POST {BAW_BASE_URL}/ops/system/login` with `Authorization: Bearer <accessToken>` and body `{"refresh_groups": false}`.
  3. Send `Authorization: Bearer <accessToken>` and `BPMCSRFToken: <csrf_token>` on all subsequent requests.

If the user has not provided their Business Automation Workflow server URL, ask before making any REST call:

> "What is your Business Automation Workflow server URL? (e.g. `https://baw.example.com:9443` for on-prem or `https://<cpd-host>/bas` for Cloud Pak for Business Automation)"

Store it as `{BAW_BASE_URL}` and use it for all subsequent REST calls in the session.

### URL validation — resolve port ambiguity before proceeding

On-premises Business Automation Workflow servers almost always listen on port **9443** (HTTPS) or 9080 (HTTP). When the user provides a URL with no port (for example, `https://host.example.com/`), do **not** assume port 443 is the Business Automation Workflow runtime. Instead:

1. Attempt `POST {url}/ops/system/login` with Basic auth.
2. If that returns HTTP 404 or an HTML page that is not from Business Automation Workflow, probe `https://<host>:9443/ops/system/login`.
3. If 9443 also fails, try `https://<host>:9080/ops/system/login`.
4. Use the first URL that returns a JSON login response (with a `csrf_token` field).

If none of these succeed, tell the user:

> "I couldn't find a Business Automation Workflow server at `<url>`. Common Business Automation Workflow ports are 9443 (HTTPS) and 9080 (HTTP). Could you confirm the full server URL including port, e.g. `https://host.example.com:9443`?"

Do not probe further without an explicit URL from the user.
