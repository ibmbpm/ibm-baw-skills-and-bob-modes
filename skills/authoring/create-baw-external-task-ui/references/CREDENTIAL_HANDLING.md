# Business Automation Workflow Credential Handling

**Credentials must never enter your context.** Do not read `.env` or ask for credentials, and do not build `Authorization` headers, `curl` commands, or Base64 strings yourself. All authenticated REST calls go through the bundled script, `scripts/baw_rest.py` in this skill's folder. The script reads `<workspace>/.env`, logs in, handles the CSRF token, makes the call, and prints only a scrubbed response.

Skip this file for any operation you execute through MCP. MCP manages authentication internally.

---

## How to run the script

Every command has the form:

```bash
python3 <skill_dir>/scripts/baw_rest.py --workspace <workspace> <command> ...
```

- `<skill_dir>` is the folder that contains this skill's `SKILL.md`.
- `<workspace>` is the absolute path of the folder the user has open in Bob (the workspace root). The script reads only `<workspace>/.env`. It does not search parent folders. Always pass it, and use the same value for every call.
- In the examples below, `baw_rest.py` stands for the full `python3 <skill_dir>/scripts/baw_rest.py --workspace <workspace>` prefix.

---

## Step 0 — Check the connection (once per session)

```bash
python3 <skill_dir>/scripts/baw_rest.py --workspace <workspace> check
```

The output is JSON and never contains secrets. Example: `{"configured": true, "base_url": "https://baw.example.com:9443", "auth": "basic", ...}`.

| Result | What to do |
|---|---|
| `"configured": true` | Continue. If the task changes data (install, delete, import), confirm `base_url` with the user first. |
| `"configured": false` | `missing` or `placeholders` lists variable **names** only. If `"env_file_found": false` (exit code 2), the output also has a `message` and the `env_file` path that was checked. Tell the user to create or edit `.env` in `<workspace>` (copy `.env.example`), fill those names in themselves, then re-run `check`. |

If the script does not exist at `<skill_dir>/scripts/baw_rest.py`, tell the user the skill installation is incomplete. Do not fall back to reading `.env` or writing `curl`.

---

## Step 1 — Make calls

```bash
baw_rest.py request GET /ops/std/bpm/containers --paginate
baw_rest.py request GET /ops/std/bpm/containers/APP/versions -q filter=active
baw_rest.py request POST /ops/std/bpm/containers/APP/versions/V1/activate
baw_rest.py request POST /bpm/processes --data '{"processAppId":"..."}'
baw_rest.py request POST /ops/std/bpm/containers/install \
    --upload file=./MyApp.twx --form inactive=false
baw_rest.py request GET /ops/std/bpm/containers/APP/versions/V1/export \
    -q use_enhanced_filenames=true -o ./MyApp.twx
```

- `PATH` is always **server-relative** (it starts with `/`). The script prepends the configured base URL, so a full URL is rejected by design.
- The script logs in once per invocation (`POST /ops/system/login`), sends the CSRF token (`BPMCSRFToken`), and falls back to a Zen Bearer token silently if a Cloud Pak for Business Automation gateway requires it. You do none of this.
- Use `-q key=value` for query parameters, `--data '<json>'` or `--data-file <file>` for JSON bodies, `--upload field=file` for multipart uploads, and `-o <file>` to save a binary response such as a `.twx`. Binary responses without `-o` are not printed.
- Use `--paginate` to automatically follow the response `"next"` link and merge list properties in-memory (highly recommended for list-retrieval).
- Confirm with the user before any state-changing call (`POST`, `PUT`, `DELETE`, `PATCH`), as the skill instructs.
- Use `--login-path /bpm/system/login` for the Process Server login used by `/bpm/...` endpoints on some servers.
- Add `-H 'Name: value'` for extra non-auth headers. `Authorization`, `Cookie`, and `BPMCSRFToken` are managed by the script and cannot be set.

### Reading the result

Output is one JSON object: `{"status": 200, "ok": true, "body": {...}}`, or `{"status": ..., "saved_to": "...", "bytes": ...}` when `-o` is used. Exit codes: `0` success, `1` HTTP error status (the body is still printed), `2` configuration or usage error, `3` network or authentication failure.

| Result | Meaning and action |
|---|---|
| `error: credentials were rejected` (exit 3) | Wrong username or password in `.env`. Tell the user to correct `.env` themselves. Do not retry in a loop. |
| `status: 400` with `CWTBG0651E` | CSRF problem. Re-run the same command (the script logs in fresh each time). |
| `status: 401/403` | Account lacks permission (on-premises: needs the `tw_admins` group). Report it. |
| `status: 404` or `login failed (HTTP 404)` | Wrong base URL or missing context root. In Cloud Pak for Business Automation environments, `BAW_BASE_URL` MUST include the context root path (for example, `/bas` or `/baw-bawins1`, e.g., `https://cpd.example.com/bas`). Tell the user to update `.env` to include the context root. |
| `network error ... self-signed` (exit 3) | The server uses a self-signed certificate. Tell the user to add `BAW_SSL_VERIFY=false` to `.env` (dev/test only). |
| `error: BAW connection is not configured` (exit 2) | Go back to Step 0. |

---

## Rules

- **Never read `.env`** by any means: `read_file`, `cat`, `grep`, `head`, `source`, `printenv`, `env`, or an editor tool. `.bobignore` blocks some of these, but this rule applies regardless. To find out whether `.env` is present, run `check`.
- **Never print, log, or write credentials**, and never put them in a file you create, a command line, or generated code. Generated applications read their own configuration from `.env` at run time (see `.env.example`).
- Do not ask the user for credentials in chat. If anything is missing, tell them which variable **names** to fill in, in `.env`.
- Do not try to bypass the script, for example by extracting values from `scripts/baw_rest.py`'s process, shell history, or environment. If the script cannot do something you need, say so and ask the user.
- **Do not chat about system internals.** Keep script names (like `baw_rest.py`), server URLs, endpoints, and your inner monologue (such as choosing a REST path or verifying connection checks) completely hidden from your natural language responses. Present results cleanly as parsed Markdown tables or business-level text. Only mention endpoints or script files if an error occurs and you are helping the user troubleshoot.
- Never commit `.env`. It is in `.gitignore` and `.bobignore`.
