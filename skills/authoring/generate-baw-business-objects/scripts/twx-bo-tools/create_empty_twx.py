#!/usr/bin/env python3
"""
create_empty_twx.py — Python port of Twx.createEmpty()

Reads resources/empty-project.twx (the reference template), rewrites all
project-owned UUIDs to fresh values, substitutes the caller-supplied project
metadata, and writes a new .twx ready for BAW import.

Usage:
    python create_empty_twx.py \
        --name "My Toolkit" \
        --acronym MYTK \
        --out dist/MYTK.twx \
        [--process-app]        # emit a process app instead of a toolkit (default: toolkit)
        [--no-ui-toolkit]      # drop the SYSBPMUI dependency
        [--snapshot 0.0.0.1]   # snapshot name (defaults to 0.0.0.1)

Python 3.9+ required.  No third-party packages needed.
"""

import argparse
import re
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

# ---------------------------------------------------------------------------
# Well-known IBM-owned UUIDs that must NEVER be rewritten.
# These are references to externally-owned content (system toolkits, primitive
# types, the default UI theme, the System participant).
# ---------------------------------------------------------------------------
PRESERVE_TYPED_UUIDS: frozenset[str] = frozenset({
    # System Data
    "2066.1b351583-e5cb-43b7-baee-340a63130ea7",
    "2063.0798815e-0346-4ef4-8946-ab4301c9f340",
    "2064.1080ded6-d153-4654-947c-2d16fce170db",
    # UI Toolkit
    "2066.ec5973da-aebe-40f6-aa02-a77962288f52",
    "2063.83ee2bb2-72b4-4a4d-b8ae-37ecd983c05e",
    "2064.304ac881-16c3-47d2-97d5-6e4c4a893177",
    # Default UI theme (System Data)
    "72.993e03e9-2574-40fc-807c-65b06be378fd",
    # System participant (referenced by every process's System lane)
    "24.6fd38d02-81cf-48ab-bd42-8ff4c0a1628b",
    # System Data primitive types
    "12.db884a3c-c533-44b7-bb2d-47bec8ad4022",  # String
    "12.83ff975e-8dbc-42e5-b738-fa8bc08274a2",  # Boolean
    "12.3fa0d7a0-828a-4d60-99cc-db5ed143fc2d",  # Integer
    "12.536b2aa5-a30f-4eca-87fa-3a28066753ee",  # Decimal
    "12.68474ab0-d56f-47ee-b7e9-510b45a2a8be",  # Date
    "12.20fdb1a2-f6ec-462e-8627-d49859ba42ae",  # Time
})

UI_TOOLKIT_PROJECT_UUID = "2066.ec5973da-aebe-40f6-aa02-a77962288f52"
UI_TOOLKIT_SNAPSHOT_UUID = "2064.304ac881-16c3-47d2-97d5-6e4c4a893177"

BARE_GUID_PAT = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
TYPED_UUID_PAT = r"\d+\." + BARE_GUID_PAT

# Text files that get UUID + literal rewrites applied.
TEXT_PATH_PREFIXES = ("META-INF/", "objects/")


# ---------------------------------------------------------------------------
# UUID helpers
# ---------------------------------------------------------------------------

def mint_guid() -> str:
    """Fresh random UUID v4, lowercase hyphenated."""
    return str(uuid.uuid4())


def escape_xml_attr(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


def escape_xml_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;")


# ---------------------------------------------------------------------------
# Substitution building — mirrors buildSubstitutions() in create-empty.ts
# ---------------------------------------------------------------------------

def _collect_typed_uuids(
    content: str,
    typed_map: dict[str, str],
    bare_map: dict[str, str],
) -> None:
    """
    Find every typed UUID in `content` and, unless it's in PRESERVE_TYPED_UUIDS
    or already mapped, mint a fresh substitution for it (and its bare GUID portion).
    """
    for m in re.finditer(TYPED_UUID_PAT, content):
        old_typed = m.group(0)
        if old_typed in PRESERVE_TYPED_UUIDS or old_typed in typed_map:
            continue
        dot = old_typed.index(".")
        type_code = old_typed[:dot]
        old_guid = old_typed[dot + 1:]
        new_guid = mint_guid()
        typed_map[old_typed] = f"{type_code}.{new_guid}"
        bare_map[old_guid] = new_guid


def _add_bare(bare_map: dict[str, str], old_guid: str) -> None:
    if old_guid not in bare_map:
        bare_map[old_guid] = mint_guid()


def _preseed_identity(
    old_typed: str,
    new_bare: str,
    typed_map: dict[str, str],
    bare_map: dict[str, str],
) -> None:
    """Pin one identity (project or branch) to a caller-supplied bare GUID."""
    dot = old_typed.index(".")
    type_code = old_typed[:dot]
    old_guid = old_typed[dot + 1:]
    typed_map[old_typed] = f"{type_code}.{new_bare}"
    bare_map[old_guid] = new_bare


def _extract_attr(s: str, element: str, attr: str) -> str:
    m = re.search(rf"<{re.escape(element)}\b[^>]*\b{re.escape(attr)}=\"([^\"]*)\"", s)
    if not m:
        raise ValueError(f"Reference package.xml missing <{element} {attr}=\"...\">")
    return m.group(1)


def build_substitutions(
    pkg_xml: str,
    artifact_xmls: list[str],
    *,
    project_name: str,
    short_name: str,
    snapshot_name: str,
    is_toolkit: bool,
    include_ui_toolkit: bool,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """
    Returns (typed_uuids, bare_guids, literals) — three plain-text substitution
    dicts, mirroring buildSubstitutions() in create-empty.ts.
    """
    typed_map: dict[str, str] = {}
    bare_map: dict[str, str] = {}
    literals: dict[str, str] = {}

    # ── 1b. Read the reference's existing project/branch identity ──────────────
    target_block_m = re.search(r"<target>([\s\S]*?)</target>", pkg_xml)
    target_block = target_block_m.group(1) if target_block_m else ""

    # We always mint fresh project + branch UUIDs (no caller-pinning in this
    # simple CLI port; callers that want stable ids can extend this).
    old_project_typed = _extract_attr(target_block, "project", "id")
    old_branch_typed = _extract_attr(target_block, "branch", "id")
    _preseed_identity(old_project_typed, mint_guid(), typed_map, bare_map)
    _preseed_identity(old_branch_typed, mint_guid(), typed_map, bare_map)

    # ── 2. Collect every other typed UUID in package.xml ──────────────────────
    _collect_typed_uuids(pkg_xml, typed_map, bare_map)

    # ── 3. Collect bare versionIds and file paths from package.xml ────────────
    for m in re.finditer(
        rf'<object\b[^/>]*\bversionId="({BARE_GUID_PAT})"', pkg_xml
    ):
        _add_bare(bare_map, m.group(1))
    for m in re.finditer(
        rf'<file\b[^>]*\bpath="({BARE_GUID_PAT})"', pkg_xml
    ):
        _add_bare(bare_map, m.group(1))

    # ── 4. Scan each artifact file for additional internal typed UUIDs ─────────
    for xml in artifact_xmls:
        _collect_typed_uuids(xml, typed_map, bare_map)
        for m in re.finditer(rf"<versionId>({BARE_GUID_PAT})</versionId>", xml):
            _add_bare(bare_map, m.group(1))
        for m in re.finditer(rf"<assetUuid>({BARE_GUID_PAT})</assetUuid>", xml):
            _add_bare(bare_map, m.group(1))

    # ── 5. Project metadata literal substitutions ──────────────────────────────
    ref_name = _extract_attr(target_block, "project", "name")
    ref_short = _extract_attr(target_block, "project", "shortName")
    ref_snapshot = _extract_attr(target_block, "snapshot", "name")
    ref_creation_date = _extract_attr(target_block, "snapshot", "originalCreationDate")

    if project_name != ref_name:
        literals[f'name="{escape_xml_attr(ref_name)}"'] = f'name="{escape_xml_attr(project_name)}"'
    if short_name != ref_short:
        literals[f'shortName="{escape_xml_attr(ref_short)}"'] = f'shortName="{escape_xml_attr(short_name)}"'
        literals[f"http://{ref_short}"] = f"http://{short_name}"
    if snapshot_name != ref_snapshot:
        literals[f'name="{ref_snapshot}"'] = f'name="{escape_xml_attr(snapshot_name)}"'
        literals[f'acronym="{ref_snapshot}"'] = f'acronym="{escape_xml_attr(snapshot_name)}"'

    # Replace the snapshot's originalCreationDate with now().
    now_iso = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    literals[ref_creation_date] = now_iso

    # ── 5b. Toolkit vs process app ────────────────────────────────────────────
    if is_toolkit:
        literals['isToolkit="false"'] = 'isToolkit="true"'
        literals['name="Process App Settings"'] = 'name="Toolkit Settings"'

    return typed_map, bare_map, literals


# ---------------------------------------------------------------------------
# Rewrite engine — mirrors applyRewrites() in uuid-rewrite.ts
# ---------------------------------------------------------------------------

def apply_rewrites(
    entries: dict[str, bytes | str],
    typed_map: dict[str, str],
    bare_map: dict[str, str],
    literals: dict[str, str],
) -> dict[str, bytes | str]:
    """
    Apply substitutions to all entries.  Text entries (META-INF/*, objects/*)
    get full content + path rewrites.  Binary entries only get path renames.
    Returns a new dict with updated paths and contents.
    """
    # Build a single ordered replacement list: longer keys first so typed UUIDs
    # are matched before the bare GUIDs they contain.
    all_replacements: list[tuple[str, str]] = sorted(
        list(typed_map.items()) + list(literals.items()) + list(bare_map.items()),
        key=lambda kv: -len(kv[0]),
    )

    def sub(s: str) -> str:
        for old, new in all_replacements:
            if old != new:
                s = s.replace(old, new)
        return s

    result: dict[str, bytes | str] = {}
    for old_path, content in entries.items():
        new_path = sub(old_path)
        is_text = any(old_path.startswith(p) for p in TEXT_PATH_PREFIXES)
        if is_text:
            text = content if isinstance(content, str) else content.decode("utf-8")
            result[new_path] = sub(text)
        else:
            result[new_path] = content  # binary: pass through unchanged
    return result


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def create_empty_twx(
    template_path: Path,
    out_path: Path,
    project_name: str,
    short_name: str,
    snapshot_name: str = "0.0.0.1",
    is_toolkit: bool = False,
    include_ui_toolkit: bool = True,
) -> None:
    """
    Generate a new empty TWX from the reference template and write it to out_path.
    """
    # ── Load the template zip ─────────────────────────────────────────────────
    with zipfile.ZipFile(template_path, "r") as zin:
        entries: dict[str, bytes | str] = {}
        for info in zin.infolist():
            if not info.is_dir():
                entries[info.filename] = zin.read(info.filename)

    # ── Optionally strip the UI Toolkit dependency ────────────────────────────
    # Must happen before substitution so the scan never sees removed content.
    if not include_ui_toolkit:
        pkg_bytes = entries["META-INF/package.xml"]
        pkg_text = pkg_bytes if isinstance(pkg_bytes, str) else pkg_bytes.decode("utf-8")
        # Remove the <dependency>…</dependency> block that carries the UI Toolkit project id.
        def drop_ui_dep(block: str) -> str:
            return "" if UI_TOOLKIT_PROJECT_UUID in block else block
        new_pkg = re.sub(
            r"[ \t]*<dependency\b[\s\S]*?</dependency>\r?\n",
            lambda m: drop_ui_dep(m.group(0)),
            pkg_text,
        )
        if new_pkg == pkg_text:
            raise RuntimeError("Could not locate the UI Toolkit <dependency> block to remove.")
        entries["META-INF/package.xml"] = new_pkg
        # Drop the bundled toolkit zip.
        toolkit_key = f"toolkits/{UI_TOOLKIT_SNAPSHOT_UUID}.zip"
        entries.pop(toolkit_key, None)

    # ── Extract the texts we need for substitution building ───────────────────
    pkg = entries["META-INF/package.xml"]
    pkg_xml = pkg if isinstance(pkg, str) else pkg.decode("utf-8")

    artifact_xmls: list[str] = []
    for path, content in entries.items():
        if path.startswith("objects/") and path.endswith(".xml"):
            artifact_xmls.append(
                content if isinstance(content, str) else content.decode("utf-8")
            )

    # ── Build substitutions ───────────────────────────────────────────────────
    typed_map, bare_map, literals = build_substitutions(
        pkg_xml,
        artifact_xmls,
        project_name=project_name,
        short_name=short_name,
        snapshot_name=snapshot_name,
        is_toolkit=is_toolkit,
        include_ui_toolkit=include_ui_toolkit,
    )

    # ── Apply rewrites ────────────────────────────────────────────────────────
    rewritten = apply_rewrites(entries, typed_map, bare_map, literals)

    # ── Write output zip ──────────────────────────────────────────────────────
    out_path.parent.mkdir(parents=True, exist_ok=True)
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for path, content in rewritten.items():
            if isinstance(content, str):
                zout.writestr(path, content.encode("utf-8"))
            else:
                zout.writestr(path, content)
    out_path.write_bytes(buf.getvalue())
    print(f"Written: {out_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an empty IBM BAW TWX from the reference template."
    )
    parser.add_argument("--name",     required=True, help='Project display name, e.g. "My App"')
    parser.add_argument("--acronym",  required=True, help="Project short name / acronym, e.g. MYAPP")
    parser.add_argument("--out",      required=True, help="Output .twx path, e.g. dist/MYAPP.twx")
    parser.add_argument("--snapshot", default="0.0.0.1", help="Snapshot name (default: 0.0.0.1)")
    parser.add_argument("--process-app", dest="toolkit", action="store_false", default=True, help="Emit a process app instead of a toolkit (default: toolkit)")
    parser.add_argument("--no-ui-toolkit", action="store_true", help="Drop the SYSBPMUI dependency")
    parser.add_argument(
        "--template",
        default=str(Path(__file__).parent / "empty-project.twx"),
        help="Path to the reference template (default: resources/empty-project.twx)",
    )
    args = parser.parse_args()

    template_path = Path(args.template)
    if not template_path.exists():
        print(f"ERROR: template not found at {template_path}", file=sys.stderr)
        sys.exit(1)

    create_empty_twx(
        template_path=template_path,
        out_path=Path(args.out),
        project_name=args.name,
        short_name=args.acronym,
        snapshot_name=args.snapshot,
        is_toolkit=args.toolkit,
        include_ui_toolkit=not args.no_ui_toolkit,
    )


if __name__ == "__main__":
    main()
