# BAW Credential Handling

## Step 0 — Resolve credentials

Before making any REST call, resolve the three required values. **Skip this step for any operation you are about to execute via MCP** — MCP manages authentication internally. Only run this step when you are about to make a direct REST call. If the session uses MCP for some operations and REST for others, run this step once the first time a REST call is needed — not before.

**Read `.env`:**

> ⚠️ **Preferred method:** Use `execute_command` with `grep` (shown below) — this works even when `.env` is listed in `.gitignore`, which blocks `read_file`. If `execute_command` is unavailable, try `read_file` as a fallback. Never surface a tool failure to the user — recover silently.

```bash
grep -E "^(BAW_SERVER_BASE_URL|BAW_BASE_URL|BAW_USERNAME|BAW_PASSWORD)=" .env 2>/dev/null
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
> BAW_SERVER_BASE_URL=https://your-baw-server.example.com:9443
> BAW_USERNAME=your-username
> BAW_PASSWORD=your-password
> ```"

Once all three values are known, store them in session context. Do not ask again for the rest of this session.

---

## Step 0a — Authenticate

Once credentials are resolved, authenticate **once** before the first REST call. The same flow works for standalone BAW and CP4BA.

```bash
curl -sk -c /tmp/baw_cookies.txt -X POST \
  "{BAW_BASE_URL}/bpm/system/login" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n '{BAW_USERNAME}:{BAW_PASSWORD}' | base64)" \
  -d '{}'
```

On **HTTP 200/201**: extract `csrf_token` from the response body → store as `{BAW_CSRF}`.

On **HTTP 401/400**: tell the user their credentials were rejected and ask them to re-enter. Do not proceed until login succeeds.

---

## Step 0b — Making subsequent REST calls

Send **both** of the following on every REST call after login:

```
Authorization: Basic $(echo -n '{BAW_USERNAME}:{BAW_PASSWORD}' | base64)
BPMCSRFToken: {BAW_CSRF}
```

Also include `-b /tmp/baw_cookies.txt` in every curl call (required for standalone BAW; harmless on CP4BA).

---

## Security rules

- **Never echo credentials in output.** Show curl commands with placeholder form only. Never substitute real values.
- **Never write `BAW_PASSWORD` to disk in plain text.** `/tmp/baw_cookies.txt` (session cookies only) is the only credential-related file permitted.
- **One prompt maximum per session.** Once credentials are resolved, do not ask again — not even if a new task starts within the same conversation.
- **Never commit `.env`.** It is in `.gitignore`. Provide a `.env.example` or boilerplate `.env` with placeholder values for user customization.
- **Never expose credentials to client-side code.** Server configuration endpoints (like `GET /api/config`) must only return public URLs (e.g., `bawServerUrl`), never `BAW_USERNAME` or `BAW_PASSWORD`.
