# BAW Credential Handling

## Step 0 — Resolve credentials

Before making any REST call, resolve the three required values. **Skip this step for any operation you are about to execute via MCP** — MCP manages authentication internally. Only run this step when you are about to make a direct REST call. If the session uses MCP for some operations and REST for others, run this step once the first time a REST call is needed — not before.

**Read `.env`:**

> ⚠️ **Preferred method:** Use `execute_command` with `grep` (shown below) — this works even when `.env` is listed in `.gitignore`, which blocks `read_file`. If `execute_command` is unavailable, try `read_file` as a fallback. Never surface a tool failure to the user — recover silently.

```bash
grep -E "^(BAW_BASE_URL|BAW_USERNAME|BAW_PASSWORD)=" .env 2>/dev/null
```

Parse each matching line as `KEY=VALUE`, stripping surrounding quotes. A value is **missing** if absent, empty, or still an angle-bracket placeholder (e.g. `<your-baw-username>`).

**If any values are missing**, ask for all of them together in a single message — never one at a time:

> "I need a few details to connect to your BAW server. Please provide:
>
> - **BAW server URL** — include the context root (e.g. `https://baw.example.com:9443` for standalone BAW, `https://cpd.example.com/bas` for CP4BA authoring, `https://cpd.example.com/baw-bawins1` for CP4BA runtime)
> - **Username**
> - **Password**
>
> **Tip:** Edit `.env` in the directory where you ran the installer and replace the placeholder values:
> ```
> BAW_BASE_URL=https://your-baw-server.example.com:9443
> BAW_USERNAME=your-username
> BAW_PASSWORD=your-password
> ```"

Once all three values are known, store them in session context. Do not ask again for the rest of this session.

---

## Step 0a — Authenticate

Once credentials are resolved, authenticate **once** before the first REST call. The same flow works for standalone BAW and CP4BA.

```bash
curl -sk -c /tmp/baw_cookies.txt -X POST \
  "{BAW_BASE_URL}/ops/system/login" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n '{BAW_USERNAME}:{BAW_PASSWORD}' | base64)" \
  -d '{"refresh_groups": false}'
```

On **HTTP 201**: extract `csrf_token` from the response body → store as `{BAW_CSRF}`.

On **HTTP 401/400**: tell the user their credentials were rejected and ask them to re-enter. Do not proceed until login succeeds.

---

## Step 0b — Making subsequent REST calls

Send **both** of the following on every REST call after login:

```
Authorization: Basic $(echo -n '{BAW_USERNAME}:{BAW_PASSWORD}' | base64)
BPMCSRFToken: {BAW_CSRF}
```

Also include `-b /tmp/baw_cookies.txt` in every curl call (required for standalone BAW; harmless on CP4BA).

> **Why Basic auth on every call, not just cookies?**
> On CP4BA environments an OIDC gateway sits in front of BAW. The gateway only accepts Basic auth or a Bearer token — it does not forward BAW session cookies. `POST /ops/system/login` returns HTTP 201 and sets cookies on both standalone BAW and CP4BA, but those cookies are rejected by the CP4BA gateway on subsequent calls. Basic auth passes the gateway; the CSRF token satisfies BAW's own CSRF protection. Both are always required on CP4BA.

---

## Step 0c — OIDC fallback (CP4BA with Basic auth disabled)

Some CP4BA deployments disable Basic auth at the gateway (e.g. SSO/SAML-only configurations). If a subsequent REST call returns **HTTP 401 with `www-authenticate: Bearer`** (an OIDC error, not a credential rejection), fall back to a Zen Bearer token:

```bash
# Strip context root: take only the scheme + host + port from BAW_BASE_URL
CPD_HOST=$(echo "{BAW_BASE_URL}" | grep -oE '^https?://[^/]+')

curl -sk -X POST "${CPD_HOST}/icp4d-api/v1/authorize" \
  -H "Content-Type: application/json" \
  -d '{"username": "{BAW_USERNAME}", "password": "{BAW_PASSWORD}"}'
```

On success, replace `Authorization: Basic ...` with `Authorization: Bearer {ZEN_TOKEN}` on all subsequent calls. Keep sending `BPMCSRFToken: {BAW_CSRF}`. Re-exchange the token if a later call returns 401 (token expiry).

> **Note:** The `/icp4d-api/v1/authorize` endpoint lives at the CPD host root, not under the context root. Always strip the context root path from `BAW_BASE_URL` before constructing this URL. For example, if `BAW_BASE_URL=https://cpd.example.com/bas`, use `https://cpd.example.com`.

## Security rules

- **Never echo credentials in output.** Show curl commands with placeholder form only. Never substitute real values.
- **Never write `BAW_PASSWORD` to disk.** `/tmp/baw_cookies.txt` (session cookies only) is the only credential-related file permitted.
- **One prompt maximum per session.** Once credentials are resolved, do not ask again — not even if a new task starts within the same conversation.
- **Never commit `.env`.** It is in `.gitignore`. Run the installer to generate a fresh `.env` with placeholder values.
