#!/usr/bin/env python3
"""baw_rest.py - credential-isolating REST client for IBM BAW / CP4BA skills.

Bob (the AI agent) invokes this script with an endpoint. The script reads the
credentials, authenticates, makes the call, and prints only the (scrubbed)
response. Credentials are never printed, so they never enter the AI context.

USAGE
    python3 baw_rest.py --workspace WORKSPACE check
    python3 baw_rest.py --workspace WORKSPACE request GET  /ops/std/bpm/containers
    python3 baw_rest.py --workspace WORKSPACE request POST /ops/std/bpm/containers/install \\
        --upload file=./MyApp.twx
    python3 baw_rest.py --workspace WORKSPACE request GET \\
        /ops/std/bpm/containers/APP/versions/V1/export \\
        --query use_enhanced_filenames=true --output ./MyApp.twx

CONFIGURATION (read by this script only; never printed)
    Read from WORKSPACE/.env, where WORKSPACE is the --workspace argument.
    BAW_BASE_URL      Base URL of your BAW server (no trailing slash)
    BAW_USERNAME      BAW username
    BAW_PASSWORD      BAW password
    BAW_SSL_VERIFY    Set to 'false' for dev/test servers with self-signed certificates
Real environment variables take precedence over the .env file.

EXIT CODES
    0 success (2xx)   1 HTTP error status (response still printed)
    2 configuration / usage error   3 network or authentication failure
"""

from __future__ import annotations

import argparse
import base64
import http.cookiejar
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

REDACTED = "***REDACTED***"
DEFAULT_LOGIN_PATH = "/ops/system/login"
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_CHARS = 200_000
# Headers the caller may never set: they are owned by this script.
_RESERVED_HEADERS = {"authorization", "cookie", "bpmcsrftoken", "host"}
# Response headers that are safe and useful to show.
_SHOWN_HEADERS = ("content-type", "location", "retry-after")

EXIT_OK, EXIT_HTTP, EXIT_CONFIG, EXIT_NETWORK = 0, 1, 2, 3


class ConfigError(Exception):
    """Missing or invalid configuration."""


class AuthError(Exception):
    """Authentication failed."""


# --------------------------------------------------------------------------
# Redaction (same approach as the MCP server's logging/redaction.py)
# --------------------------------------------------------------------------
_secrets: set[str] = set()

_PATTERNS = [
    (re.compile(r"(?i)\b(Bearer|Basic|ZenApiKey)\s+[A-Za-z0-9._~+/=\-]{8,}"),
     r"\1 " + REDACTED),
    (re.compile(
        r'(?i)("(?:csrf_?token|access_?token|refresh_?token|token|password|'
        r'passwd|api_?key|secret|client_?secret|authorization)"\s*:\s*")[^"]*(")'),
     r"\1" + REDACTED + r"\2"),
    (re.compile(r"(?i)\b(LtpaToken2|JSESSIONID|ltpatoken)=[^;\s]+"),
     r"\1=" + REDACTED),
    (re.compile(r"://([^:/\s@]+):([^@/\s]+)@"), r"://\1:" + REDACTED + "@"),
]


def _register(*values: str | None) -> None:
    for value in values:
        if value:
            _secrets.add(value)
            # also the JSON-escaped form, since output is scrubbed after serialization
            _secrets.add(json.dumps(value)[1:-1])


def scrub(text: str) -> str:
    """Remove every known secret value and common secret patterns from text."""
    for secret in sorted(_secrets, key=len, reverse=True):
        text = text.replace(secret, REDACTED)
    for pattern, repl in _PATTERNS:
        text = pattern.sub(repl, text)
    return text


def emit(obj: dict) -> None:
    """Print a JSON object to stdout, scrubbed as one serialized string."""
    print(scrub(json.dumps(obj, indent=2, ensure_ascii=False)))


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
def _is_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    v = value.strip()
    return (not v or (v.startswith("<") and v.endswith(">"))
            or v.lower().startswith(("your-", "your_")))


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, _, val = line.partition("=")
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        values[key.strip()] = val
    return values


def _env_path(workspace: str) -> Path:
    """The only place .env is read from: <workspace>/.env."""
    root = Path(workspace).expanduser()
    if not root.is_dir():
        raise ConfigError(f"workspace directory not found: {workspace}")
    return root.resolve() / ".env"


class Config:
    def __init__(self, base_url: str, username: str, password: str,
                 verify_ssl: bool) -> None:
        self.base_url = base_url
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        _register(password)


def load_config(workspace: str) -> tuple[Config | None, dict]:
    """Return (Config or None, status). Status never contains secret values."""
    path = _env_path(workspace)
    found = path.is_file()
    file_vals = _parse_env_file(path) if found else {}

    def get(name: str) -> str | None:
        return os.environ.get(name) or file_vals.get(name)

    base = get("BAW_BASE_URL")
    user = get("BAW_USERNAME")
    password = get("BAW_PASSWORD")

    missing, placeholders = [], []
    for name, val in (("BAW_BASE_URL", base), ("BAW_USERNAME", user),
                      ("BAW_PASSWORD", password)):
        if val is None or not val.strip():
            missing.append(name)
        elif _is_placeholder(val):
            placeholders.append(name)

    status = {
        "env_file": str(path),
        "env_file_found": found,
        "configured": not missing and not placeholders,
        "missing": missing,
        "placeholders": placeholders,
    }
    if missing or placeholders:
        if not found:
            status["message"] = (f"No .env file found at {path}. Ask the user to create "
                                 f"it in {path.parent} (copy .env.example) and fill in "
                                 "BAW_BASE_URL, BAW_USERNAME and BAW_PASSWORD themselves.")
        return None, status

    base = base.strip().rstrip("/")  # type: ignore[union-attr]
    if not re.match(r"^https?://[^/\s]+", base):
        status.update(configured=False, placeholders=["BAW_BASE_URL"])
        return None, status

    verify_val = (os.environ.get("BAW_SSL_VERIFY") or file_vals.get("BAW_SSL_VERIFY") or "true")
    verify = verify_val.strip().lower() not in ("false", "0", "no")
    cfg = Config(base, user.strip(), password.strip(), verify_ssl=verify)  # type: ignore[union-attr]
    status["base_url"] = base   # a URL is not a secret; needed to confirm target
    status["auth"] = "basic"
    status["ssl_verify"] = verify
    return cfg, status


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------
class _SameHostRedirects(urllib.request.HTTPRedirectHandler):
    """Never follow a redirect to another host (would leak the auth header)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        old = urllib.parse.urlsplit(req.full_url).netloc.lower()
        new = urllib.parse.urlsplit(newurl).netloc.lower()
        if old != new:
            raise urllib.error.URLError("redirect to a different host was blocked")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Response:
    def __init__(self, status: int, headers, body: bytes) -> None:  # noqa: ANN001
        self.status, self.headers, self.body = status, headers, body

    def json(self) -> dict:
        try:
            data = json.loads(self.body.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except (ValueError, UnicodeDecodeError):
            return {}


class BawClient:
    """Holds credentials internally and builds auth headers (MCP 'strategy')."""

    def __init__(self, cfg: Config, login_path: str, timeout: int) -> None:
        self._cfg = cfg
        self._login_path = login_path
        self._timeout = timeout
        self._csrf: str | None = None
        self._bearer: str | None = None
        ctx = ssl.create_default_context()
        if not cfg.verify_ssl:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ctx),
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
            _SameHostRedirects(),
        )

    def _auth_header(self) -> dict[str, str]:
        if self._bearer:
            return {"Authorization": f"Bearer {self._bearer}"}
        encoded = base64.b64encode(
            f"{self._cfg.username}:{self._cfg.password}".encode()).decode()
        _register(encoded)
        return {"Authorization": f"Basic {encoded}"}

    def _send(self, method: str, url: str, headers: dict[str, str],
              data: bytes | None) -> Response:
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with self._opener.open(req, timeout=self._timeout) as resp:
                return Response(resp.status, resp.headers, resp.read())
        except urllib.error.HTTPError as err:
            return Response(err.code, err.headers, err.read())

    # -- Zen bearer fallback (CP4BA with Basic auth disabled at the gateway) --
    def _zen_bearer(self) -> bool:
        """Try to obtain a CP4BA Zen bearer token from the password silently."""
        parts = urllib.parse.urlsplit(self._cfg.base_url)
        host = f"{parts.scheme}://{parts.netloc}"
        body = json.dumps({"username": self._cfg.username,
                           "password": self._cfg.password}).encode()
        resp = self._send("POST", host + "/icp4d-api/v1/authorize",
                          {"Content-Type": "application/json",
                           "Accept": "application/json"}, body)
        token = resp.json().get("token") if resp.status == 200 else None
        if not token:
            basic = base64.b64encode(
                f"{self._cfg.username}:{self._cfg.password}".encode()).decode()
            _register(basic)
            resp = self._send("GET", host + "/v1/preauth/validateAuth",
                              {"Authorization": f"Basic {basic}",
                               "Accept": "application/json"}, None)
            token = resp.json().get("accessToken") if resp.status == 200 else None
        if token:
            self._bearer = token
            _register(token)
            return True
        return False

    @staticmethod
    def _wants_bearer(resp: Response) -> bool:
        return resp.status == 401 and "bearer" in (
            resp.headers.get("WWW-Authenticate") or "").lower()

    def login(self) -> None:
        url = self._cfg.base_url + self._login_path
        for _ in range(2):
            resp = self._send("POST", url, {**self._auth_header(),
                                            "Content-Type": "application/json",
                                            "Accept": "application/json"},
                              json.dumps({"refresh_groups": False}).encode())
            if self._wants_bearer(resp) and not self._bearer and self._zen_bearer():
                continue
            break
        if resp.status in (400, 401, 403):
            raise AuthError(f"credentials were rejected (HTTP {resp.status})")
        if resp.status not in (200, 201):
            hint = ""
            if resp.status == 404:
                hint = " (this usually means BAW_BASE_URL in .env is missing the context root, e.g. /bas or /baw-bawins1)"
            raise AuthError(f"login failed (HTTP {resp.status}){hint}; check the base URL"
                            " and --login-path")
        csrf = resp.json().get("csrf_token")
        if not csrf:
            raise AuthError("login response did not contain a CSRF token")
        self._csrf = csrf
        _register(csrf)

    def request(self, method: str, path: str, headers: dict[str, str],
                data: bytes | None) -> Response:
        if self._csrf is None:
            self.login()
        for _ in range(2):
            hdrs = {**headers, **self._auth_header()}
            if self._csrf:
                hdrs["BPMCSRFToken"] = self._csrf
            resp = self._send(method, self._cfg.base_url + path, hdrs, data)
            if self._wants_bearer(resp) and not self._bearer and self._zen_bearer():
                self.login()
                continue
            break
        return resp


# --------------------------------------------------------------------------
# Request building
# --------------------------------------------------------------------------
def _validate_path(path: str) -> str:
    if (not path.startswith("/") or path.startswith("//") or "://" in path
            or any(c in path for c in "\r\n\\ ")):
        raise ConfigError("PATH must be a server-relative path such as "
                          "/ops/std/bpm/containers (never a full URL)")
    return path


def _parse_header(raw: str) -> tuple[str, str]:
    name, sep, value = raw.partition(":")
    name, value = name.strip(), value.strip()
    if not sep or not name or any(c in raw for c in "\r\n"):
        raise ConfigError(f"invalid --header {raw!r}; use 'Name: value'")
    if name.lower() in _RESERVED_HEADERS:
        raise ConfigError(f"header {name!r} is managed by this script")
    return name, value


def _multipart(fields: dict[str, str], files: list[tuple[str, Path]]
               ) -> tuple[bytes, str]:
    boundary = "----baw" + uuid.uuid4().hex
    out = bytearray()
    for key, val in fields.items():
        out += (f"--{boundary}\r\nContent-Disposition: form-data; "
                f'name="{key}"\r\n\r\n{val}\r\n').encode()
    for key, path in files:
        out += (f"--{boundary}\r\nContent-Disposition: form-data; "
                f'name="{key}"; filename="{path.name}"\r\n'
                "Content-Type: application/octet-stream\r\n\r\n").encode()
        out += path.read_bytes() + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


def _kv(items: list[str], what: str) -> list[tuple[str, str]]:
    pairs = []
    for item in items:
        key, sep, val = item.partition("=")
        if not sep or not key:
            raise ConfigError(f"invalid {what} {item!r}; use key=value")
        pairs.append((key, val))
    return pairs


def _is_textual(content_type: str, body: bytes) -> bool:
    ct = content_type.lower()
    if any(t in ct for t in ("json", "text", "xml", "javascript", "html", "yaml")):
        return True
    if not ct:
        try:
            body.decode("utf-8")
            return True
        except UnicodeDecodeError:
            return False
    return False


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------
def cmd_check(args: argparse.Namespace) -> int:
    _, status = load_config(args.workspace)
    emit(status)
    return EXIT_OK if status["configured"] else EXIT_CONFIG


def _merge_pages(first: dict, second: dict) -> dict:
    for key, val in second.items():
        if isinstance(val, list) and isinstance(first.get(key), list):
            first[key].extend(val)
    return first


def cmd_request(args: argparse.Namespace) -> int:
    cfg, status = load_config(args.workspace)
    if cfg is None:
        emit({"ok": False, "error": "BAW connection is not configured. Ask the user"
              " to edit .env themselves; never ask them to paste credentials in chat.",
              **status})
        return EXIT_CONFIG

    method_upper = args.method.upper()

    base_path = _validate_path(args.path)
    path = base_path
    query = _kv(args.query, "--query")
    if query:
        sep = "&" if "?" in path else "?"
        path += sep + urllib.parse.urlencode(query)

    headers = {"Accept": "application/json"}
    for raw in args.header:
        name, value = _parse_header(raw)
        headers[name] = value

    data: bytes | None = None
    if args.upload or args.form:
        files = []
        for field, fpath in _kv(args.upload, "--upload"):
            p = Path(fpath).expanduser()
            if not p.is_file():
                raise ConfigError(f"upload file not found: {fpath}")
            files.append((field, p))
        data, headers["Content-Type"] = _multipart(dict(_kv(args.form, "--form")),
                                                   files)
    elif args.data_file is not None:
        p = Path(args.data_file).expanduser()
        if not p.is_file():
            raise ConfigError(f"--data-file not found: {args.data_file}")
        data = p.read_bytes()
        headers.setdefault("Content-Type", "application/json")
    elif args.data is not None:
        data = args.data.encode("utf-8")
        headers.setdefault("Content-Type", "application/json")

    out_path = None
    if args.output:
        out_path = Path(args.output).expanduser()
        if out_path.name.lower().startswith(".env"):
            raise ConfigError("refusing to write the response to an .env file")

    client = BawClient(cfg, args.login_path, args.timeout)
    try:
        resp = client.request(method_upper, path, headers, data)
        if args.paginate and 200 <= resp.status < 300:
            try:
                merged = json.loads(resp.body.decode("utf-8"))
            except ValueError:
                merged = None

            if isinstance(merged, dict):
                next_url = merged.get("next")
                page_count = 1
                while next_url and page_count < 1000:
                    next_query = urllib.parse.urlsplit(next_url).query
                    next_path = base_path + ("?" + next_query if next_query else "")
                    
                    next_resp = client.request(method_upper, next_path, headers, data)
                    if not (200 <= next_resp.status < 300):
                        resp = next_resp
                        break
                        
                    try:
                        next_json = json.loads(next_resp.body.decode("utf-8"))
                    except ValueError:
                        next_json = None
                        
                    if not isinstance(next_json, dict):
                        break
                        
                    merged = _merge_pages(merged, next_json)
                    next_url = next_json.get("next")
                    page_count += 1
                
                if isinstance(merged, dict):
                    merged["next"] = None
                    merged.pop("previous", None)
                    resp = Response(resp.status, resp.headers, json.dumps(merged).encode("utf-8"))
    except AuthError as err:
        emit({"ok": False, "error": str(err)})
        return EXIT_NETWORK
    except (urllib.error.URLError, OSError) as err:
        reason = getattr(err, "reason", err)
        hint = ""
        if isinstance(reason, ssl.SSLError):
            hint = " If the server uses a self-signed certificate, add BAW_SSL_VERIFY=false to .env."
        emit({"ok": False, "error": f"network error: {reason}.{hint}"})
        return EXIT_NETWORK

    ctype = resp.headers.get("Content-Type", "") or ""
    envelope: dict = {
        "status": resp.status,
        "ok": 200 <= resp.status < 300,
        "headers": {h: resp.headers[h] for h in _SHOWN_HEADERS if resp.headers.get(h)},
    }
    if out_path is not None and envelope["ok"]:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(resp.body)
        envelope.update(saved_to=str(out_path), bytes=len(resp.body))
    elif _is_textual(ctype, resp.body):
        text = scrub(resp.body.decode("utf-8", errors="replace"))
        truncated = len(text) > args.max_chars
        text = text[: args.max_chars]
        try:
            envelope["body"] = json.loads(text)
        except ValueError:
            envelope["body"] = text
        if truncated:
            envelope["truncated"] = True
    elif resp.body:
        envelope["note"] = (f"binary response ({len(resp.body)} bytes, "
                            f"{ctype or 'unknown type'}); "
                            "re-run with --output <file> to save it")
    emit(envelope)
    return EXIT_OK if envelope["ok"] else EXIT_HTTP


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="baw_rest.py",
        description="Authenticated BAW REST calls without exposing credentials.")
    parser.add_argument("--workspace", required=True, metavar="DIR",
                        help="the user's Bob workspace root; .env is read from DIR/.env")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="report whether a connection is configured "
                   "(never prints credentials)").set_defaults(func=cmd_check)

    req = sub.add_parser("request", help="make one authenticated REST call")
    req.add_argument("method", choices=("GET", "POST", "PUT", "DELETE", "PATCH",
                                        "get", "post", "put", "delete", "patch"))
    req.add_argument("path", help="server-relative path, e.g. /ops/std/bpm/containers")
    req.add_argument("-q", "--query", action="append", default=[], metavar="K=V")
    req.add_argument("--data", help="inline JSON request body")
    req.add_argument("--data-file", help="file containing the request body")
    req.add_argument("--upload", action="append", default=[], metavar="FIELD=FILE",
                     help="multipart file upload (repeatable)")
    req.add_argument("--form", action="append", default=[], metavar="K=V",
                     help="extra multipart text field (repeatable)")
    req.add_argument("-H", "--header", action="append", default=[],
                     metavar="'Name: value'", help="extra non-auth header")
    req.add_argument("-o", "--output", help="save the response body to this file")
    req.add_argument("--login-path", default=DEFAULT_LOGIN_PATH,
                     help=f"CSRF login path (default {DEFAULT_LOGIN_PATH})")
    req.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    req.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS,
                     help="truncate printed text bodies")
    req.add_argument("--paginate", action="store_true",
                     help="follow response 'next' link and merge list properties")
    req.set_defaults(func=cmd_request)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ConfigError as err:
        emit({"ok": False, "error": str(err)})
        return EXIT_CONFIG
    except Exception as err:  # noqa: BLE001 - never leak a traceback with values
        emit({"ok": False, "error": f"unexpected error: {type(err).__name__}"})
        return EXIT_NETWORK


if __name__ == "__main__":
    sys.exit(main())
