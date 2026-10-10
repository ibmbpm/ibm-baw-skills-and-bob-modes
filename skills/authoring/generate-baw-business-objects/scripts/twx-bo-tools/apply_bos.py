#!/usr/bin/env python3
"""
apply_bos.py — add or overwrite Business Objects in an existing TWX file.

Reads one or more .bo.json descriptor files, applies them to a copy of the
source TWX, and writes the result to a new TWX with a caller-supplied snapshot
version.  The source TWX is never modified.

Follows the same logic as BusinessObjectCollection.createComplex /
createSelection / addProperty in src/twx/business-object.ts, and the
snapshot-stamping in Twx.createSnapshot / Twx.applySnapshotMetadata.

────────────────────────────────────────────────────────────────────────────────
INPUT FILE FORMAT  (<Name>.bo.json)
────────────────────────────────────────────────────────────────────────────────
The filename stem (everything before ".bo.json") IS the BO name.

COMPLEX BO — a record with typed properties:

  {
    "kind": "complex",
    "description": "Optional.",          // omit or null to leave unset
    "properties": [
      { "name": "id",     "type": "String" },
      { "name": "amount", "type": "Decimal" },
      { "name": "status", "type": "OrderStatus" },    // local BO name
      { "name": "tags",   "type": "String", "array": true },
      { "name": "score",  "type": "Integer", "required": true },
      { "name": "notes",  "type": "String",  "hidden": true,
        "description": "Internal note." }
    ]
  }

SELECTION BO — an enum:

  {
    "kind": "selection",
    "description": "Optional.",
    "options": [
      { "value": "NEW",      "display": "New" },
      { "value": "COMPLETE", "display": "Complete" }
    ]
  }

Accepted "type" values for complex BO properties:
  Primitives  : String  Integer  Boolean  Decimal  Date  Time
                (always resolve to System Data; never confused with a local BO)
  Local BO    : the name of another BO defined in this project
                (either already in the TWX or added by another input file)

BEHAVIOUR:
  • A BO whose name matches an existing twClass in the TWX is REPLACED entirely.
  • A BO whose name is new is ADDED.
  • All other objects in the TWX are left byte-identical to the source.
  • The output snapshot gets a fresh snapshot UUID and the name you supply.

────────────────────────────────────────────────────────────────────────────────
USAGE
────────────────────────────────────────────────────────────────────────────────
  python apply_bos.py \\
      --source  path/to/source.twx          \\
      --version 1.2.3.4                     \\
      --out     path/to/output.twx          \\
      Customer.bo.json Order.bo.json OrderStatus.bo.json

  # All .bo.json files in a directory:
  python apply_bos.py --source src.twx --version 2.0.0.1 --out out.twx bos/*.bo.json

Python 3.9+ required.  No third-party packages needed.
"""

import argparse
import json
import re
import sys
import time
import uuid
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET


# ---------------------------------------------------------------------------
# System Data primitive UUIDs (src/twx/uuid.ts)
# ---------------------------------------------------------------------------
PRIMITIVE_TYPE_UUIDS: dict[str, str] = {
    "String":  "12.db884a3c-c533-44b7-bb2d-47bec8ad4022",
    "Boolean": "12.83ff975e-8dbc-42e5-b738-fa8bc08274a2",
    "Integer": "12.3fa0d7a0-828a-4d60-99cc-db5ed143fc2d",
    "Decimal": "12.536b2aa5-a30f-4eca-87fa-3a28066753ee",
    "Date":    "12.68474ab0-d56f-47ee-b7e9-510b45a2a8be",
    "Time":    "12.20fdb1a2-f6ec-462e-8627-d49859ba42ae",
}
PRIMITIVES = set(PRIMITIVE_TYPE_UUIDS)


# ---------------------------------------------------------------------------
# XML / string helpers
# ---------------------------------------------------------------------------

def _esc_attr(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")

def _esc_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _mint() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# BO spec validation
# ---------------------------------------------------------------------------

def _load_bo_spec(path: Path) -> dict:
    """Load and validate a .bo.json file.  Returns the parsed dict."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise SystemExit(f"ERROR: cannot read {path}: {e}")
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(f"ERROR: {path} is not valid JSON: {e}")
    if not isinstance(spec, dict):
        raise SystemExit(f"ERROR: {path}: expected a JSON object at top level")
    kind = spec.get("kind")
    if kind not in ("complex", "selection"):
        raise SystemExit(
            f'ERROR: {path}: "kind" must be "complex" or "selection" (got {kind!r})'
        )
    if kind == "complex":
        props = spec.get("properties", [])
        if not isinstance(props, list):
            raise SystemExit(f'ERROR: {path}: "properties" must be an array')
        for i, p in enumerate(props):
            if not isinstance(p, dict):
                raise SystemExit(f'ERROR: {path}: properties[{i}] must be an object')
            if not p.get("name"):
                raise SystemExit(f'ERROR: {path}: properties[{i}] missing "name"')
            if not p.get("type"):
                raise SystemExit(f'ERROR: {path}: properties[{i}] missing "type"')
            
            # Normalize list notations (Type[] or isList/array flags)
            ptype = p["type"]
            if ptype.endswith("[]"):
                p["type"] = ptype[:-2]
                p["array"] = True
            elif p.get("isList"):
                p["array"] = True
    else:  # selection
        opts = spec.get("options")
        if not isinstance(opts, list) or len(opts) == 0:
            raise SystemExit(f'ERROR: {path}: "options" must be a non-empty array')
        for i, o in enumerate(opts):
            if not isinstance(o, dict) or "value" not in o or "display" not in o:
                raise SystemExit(
                    f'ERROR: {path}: options[{i}] must have "value" and "display"'
                )
    return spec


# ---------------------------------------------------------------------------
# Package.xml helpers (regex-based, no DOM — keeps untouched XML byte-exact)
# ---------------------------------------------------------------------------

def _read_project_namespace(pkg_xml: str) -> str:
    """
    Read the <namespace> from the projectDefaults artifact, falling back to
    http://<shortName>.  Mirrors BusinessObjectCollection.projectNamespace().
    """
    # Find projectDefaults object id
    m = re.search(r'<object\b[^>]*\btype="projectDefaults"[^>]*\bid="([^"]+)"', pkg_xml)
    if not m:
        m = re.search(r'<object\b[^>]*\bid="([^"]+)"[^>]*\btype="projectDefaults"', pkg_xml)
    pd_id = m.group(1) if m else None

    if pd_id:
        return pd_id  # caller resolves against artifact XML — see _resolve_namespace

    # Fallback: derive from shortName
    sn = re.search(r'<project\b[^>]*\bshortName="([^"]+)"', pkg_xml)
    return f"http://{sn.group(1)}" if sn else "http://UNKNOWN"


def _resolve_namespace(pkg_xml: str, artifact_xml_map: dict[str, str]) -> str:
    """
    Read the <namespace> text from the projectDefaults artifact.
    Falls back to http://<shortName>.
    Mirrors BusinessObjectCollection.projectNamespace().
    """
    m_id = re.search(r'<object\b[^>]*\btype="projectDefaults"[^>]*\bid="([^"]+)"', pkg_xml)
    if not m_id:
        m_id = re.search(r'<object\b[^>]*\bid="([^"]+)"[^>]*\btype="projectDefaults"', pkg_xml)
    if m_id:
        pd_path = f"objects/{m_id.group(1)}.xml"
        pd_xml = artifact_xml_map.get(pd_path, "")
        ns_m = re.search(r'<namespace>([^<]+)</namespace>', pd_xml)
        if ns_m and ns_m.group(1).strip():
            return ns_m.group(1).strip()

    # Fallback: http://<shortName>
    sn = re.search(r'<project\b[^>]*\bshortName="([^"]+)"', pkg_xml)
    return f"http://{sn.group(1)}" if sn else "http://UNKNOWN"


def _read_twsys_dep_guid(pkg_xml: str) -> str:
    """
    Extract the bare depGuid for System Data (TWSYS).
    Mirrors BusinessObjectCollection.systemDataDepGuid().
    """
    # Find <dependency id="2069.<guid>"> that contains <project shortName="TWSYS">
    for dep_m in re.finditer(r'<dependency\b([^>]*)>([\s\S]*?)</dependency>', pkg_xml):
        attrs, body = dep_m.group(1), dep_m.group(2)
        if 'shortName="TWSYS"' not in body:
            continue
        id_m = re.search(r'\bid="2069\.([^"]+)"', attrs)
        if id_m:
            return id_m.group(1)
    raise SystemExit("ERROR: package.xml has no System Data (TWSYS) dependency")


def _all_twclass_ids(pkg_xml: str) -> list[tuple[str, str]]:
    """Return [(id, name), …] for all twClass objects in package.xml order."""
    out = []
    for m in re.finditer(r'<object\b([^>]+)>', pkg_xml):
        attrs = m.group(1)
        if 'type="twClass"' not in attrs:
            continue
        id_m  = re.search(r'\bid="([^"]+)"',   attrs)
        nm_m  = re.search(r'\bname="([^"]+)"',  attrs)
        if id_m:
            out.append((id_m.group(1), nm_m.group(1) if nm_m else ""))
    return out


def _remove_object_entry(pkg_xml: str, obj_id: str) -> str:
    """Remove a single <object …/> or <object …></object> line from package.xml."""
    # Self-closing or open/close — always on its own line(s) in BAW output.
    # Match the whole tag (attrs contain the id) and its surrounding whitespace line.
    escaped = re.escape(obj_id)
    pkg_xml = re.sub(
        rf'[ \t]*<object\b[^>]*\bid="{escaped}"[^>]*/>\r?\n?',
        '',
        pkg_xml,
    )
    pkg_xml = re.sub(
        rf'[ \t]*<object\b[^>]*\bid="{escaped}"[^>]*>.*?</object>\r?\n?',
        '',
        pkg_xml,
        flags=re.DOTALL,
    )
    return pkg_xml


def _insert_object_entry(pkg_xml: str, entry_line: str) -> str:
    """Append a new <object …/> entry just before </objects>.

    Uses a regex so that any leading whitespace already in front of </objects>
    (e.g. from a previous insert) is normalised back to 4 spaces, keeping all
    entries consistently indented at 8 spaces regardless of call order.
    """
    return re.sub(
        r'[ \t]*</objects>',
        f'        {entry_line}\r\n    </objects>',
        pkg_xml,
    )


def _update_snapshot(pkg_xml: str, version: str) -> str:
    """
    Replace the target snapshot's id, name, acronym and originalCreationDate.
    Mirrors Twx.applySnapshotMetadata().
    """
    new_snap_id = f"2064.{_mint()}"
    now_iso = _now_iso()

    def replace_snap(m: re.Match) -> str:
        tag = m.group(0)
        tag = re.sub(r'\bid="[^"]*"', f'id="{new_snap_id}"', tag)
        tag = re.sub(r'\bname="[^"]*"', f'name="{_esc_attr(version)}"', tag)
        tag = re.sub(r'\bacronym="[^"]*"', f'acronym="{_esc_attr(version)}"', tag)
        tag = re.sub(r'\boriginalCreationDate="[^"]*"',
                     f'originalCreationDate="{now_iso}"', tag)
        return tag

    # Only the <target> block's snapshot — not a dependency snapshot.
    # Strategy: replace inside <target>…</target> only.
    def replace_target(tm: re.Match) -> str:
        inner = tm.group(0)
        inner = re.sub(r'<snapshot\b[^>]*/>', replace_snap, inner)
        inner = re.sub(r'<snapshot\b[^>]*>.*?</snapshot>', replace_snap, inner, flags=re.DOTALL)
        return inner

    return re.sub(r'<target>[\s\S]*?</target>', replace_target, pkg_xml)


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


# ---------------------------------------------------------------------------
# classRef encoding
# Mirrors BusinessObjectCollection._typeArgToClassRef()
# ---------------------------------------------------------------------------

def _class_ref(type_name: str, twsys_dep_guid: str, bo_id_map: dict[str, str]) -> str:
    """
    Encode a property type as a <classRef> value.

    Primitives  → "<twsys_dep_guid>/12.<primitiveUuid>"
    Local BO    → "/12.<boUuid>"
    """
    if type_name in PRIMITIVES:
        typed = PRIMITIVE_TYPE_UUIDS[type_name]
        return f"{twsys_dep_guid}/{typed}"
    bo_id = bo_id_map.get(type_name)
    if bo_id is None:
        raise SystemExit(
            f'ERROR: property type "{type_name}" is neither a primitive nor a '
            f'known local BO. Known BOs: {sorted(bo_id_map)}'
        )
    return f"/{bo_id}"


# ---------------------------------------------------------------------------
# JSON-data mirror builders
# Mirrors buildComplexJsonData / buildSelectionJsonData in business-object.ts
# ---------------------------------------------------------------------------

def _complex_json_data(
    bo_id: str,
    bo_name: str,
    description: Optional[str],
    properties: list[dict],
    twsys_dep_guid: str,
    bo_id_map: dict[str, str],
    project_namespace: str,
) -> str:
    elements = []
    for p in properties:
        ptype   = p["type"]
        pname   = p["name"]
        is_array = bool(p.get("array"))
        is_req   = bool(p.get("required"))
        is_hide  = bool(p.get("hidden"))
        pdesc    = p.get("description")

        # Build namespacedName + refid for this type
        if ptype in PRIMITIVES:
            typed_uuid = PRIMITIVE_TYPE_UUIDS[ptype]
            ns_name    = f"{{http://lombardi.ibm.com/schema/}}{ptype}"
            refid      = typed_uuid
        else:
            local_id = bo_id_map.get(ptype)
            if local_id is None:
                raise SystemExit(f'ERROR: type "{ptype}" not found')
            # The local namespace for local BOs uses the project namespace.
            ns_name = f"{{{project_namespace}}}{ptype}"
            refid   = local_id

        elem: dict = {
            "annotation": {
                "documentation": [{"content": [pdesc]}] if pdesc else [{}],
                "appinfo": [{
                    "propertyName":   [pname],
                    "propertyRequired": [is_req],
                    "propertyHidden":   [is_hide],
                    "advancedParameterProperties": [{}],
                }],
            },
            "name": pname,
        }
        if is_array:
            elem["maxOccurs"] = "unbounded"
        elem["type"] = ns_name
        elem["otherAttributes"] = {"{http://www.ibm.com/bpmsdk}refid": refid}
        elements.append(elem)

    doc = [{"content": [description]}] if description else [{}]
    payload = {
        "attributeFormDefault": "unqualified",
        "elementFormDefault":   "unqualified",
        "targetNamespace":      project_namespace,
        "complexType": [{
            "annotation": {
                "documentation": doc,
                "appinfo": [{
                    "shared": [False],
                    "advancedProperties": [{}],
                    "shadow": [False],
                    "allowAdditionalProperties": [False],
                }],
            },
            "sequence": {"element": elements},
            "name": bo_name,
        }],
        "id": f"_{bo_id}",
    }
    return json.dumps(payload, separators=(',', ':'))


def _selection_json_data(
    bo_id: str,
    bo_name: str,
    description: Optional[str],
    options: list[dict],
    project_namespace: str,
) -> str:
    enumeration = [
        {"annotation": {"appinfo": [{"displayName": [o["display"]]}]}, "value": o["value"]}
        for o in options
    ]
    doc = [{"content": [description]}] if description else [{}]
    payload = {
        "simpleType": [{
            "annotation": {
                "documentation": doc,
                "appinfo": [{"advancedProperties": [{}]}],
            },
            "name": bo_name,
            "restriction": {
                "annotation": {"appinfo": [{"simpleBaseType": ["Selection"]}]},
                "enumeration": enumeration,
                "base": "{http://www.w3.org/2001/XMLSchema}string",
            },
        }],
        "attributeFormDefault": "unqualified",
        "elementFormDefault":   "unqualified",
        "targetNamespace":      project_namespace,
        "id": f"_{bo_id}",
    }
    return json.dumps(payload, separators=(',', ':'))


# ---------------------------------------------------------------------------
# Artifact XML renderers
# Mirrors renderInitialComplexTwClass / renderInitialSelectionTwClass
# ---------------------------------------------------------------------------

def _render_complex_xml(
    bo_id: str,
    bo_name: str,
    version_id: str,
    description: Optional[str],
    properties: list[dict],
    twsys_dep_guid: str,
    bo_id_map: dict[str, str],
    project_namespace: str,
) -> str:
    guid_portion = bo_id[bo_id.index('.') + 1:]
    desc_tag = (
        f'        <description isNull="true" />'
        if description is None
        else f'        <description>{_esc_text(description)}</description>'
    )
    json_data = _complex_json_data(
        bo_id, bo_name, description, properties,
        twsys_dep_guid, bo_id_map, project_namespace
    )

    # Build property XML blocks
    prop_lines = []
    for p in properties:
        pname   = p["name"]
        ptype   = p["type"]
        is_arr  = str(bool(p.get("array"))).lower()
        is_req  = str(bool(p.get("required"))).lower()
        is_hide = str(bool(p.get("hidden"))).lower()
        pdesc   = p.get("description")
        cref    = _class_ref(ptype, twsys_dep_guid, bo_id_map)
        desc_line = (
            f'                <description isNull="true" />'
            if pdesc is None
            else f'                <description>{_esc_text(pdesc)}</description>'
        )
        prop_lines.append(
            f'            <property>\r\n'
            f'                <name>{_esc_text(pname)}</name>\r\n'
            f'{desc_line}\r\n'
            f'                <classRef>{_esc_text(cref)}</classRef>\r\n'
            f'                <arrayProperty>{is_arr}</arrayProperty>\r\n'
            f'                <propertyDefault isNull="true" />\r\n'
            f'                <propertyRequired>{is_req}</propertyRequired>\r\n'
            f'                <propertyHidden>{is_hide}</propertyHidden>\r\n'
            f'                <annotation type="com.lombardisoftware.core.xml.XMLFieldAnnotation" version="2.0">\r\n'
            f'                    <exclude isNull="true" />\r\n'
            f'                    <nodeType isNull="true" />\r\n'
            f'                    <name isNull="true" />\r\n'
            f'                    <namespace isNull="true" />\r\n'
            f'                    <typeName isNull="true" />\r\n'
            f'                    <typeNamespace isNull="true" />\r\n'
            f'                    <minOccurs isNull="true" />\r\n'
            f'                    <maxOccurs isNull="true" />\r\n'
            f'                    <nillable isNull="true" />\r\n'
            f'                    <order isNull="true" />\r\n'
            f'                    <wrapArray isNull="true" />\r\n'
            f'                    <arrayTypeName isNull="true" />\r\n'
            f'                    <arrayTypeAnonymous isNull="true" />\r\n'
            f'                    <arrayItemName isNull="true" />\r\n'
            f'                    <arrayItemWildcard isNull="true" />\r\n'
            f'                    <wildcard isNull="true" />\r\n'
            f'                    <wildcardVariety isNull="true" />\r\n'
            f'                    <wildcardMode isNull="true" />\r\n'
            f'                    <wildcardNamespace isNull="true" />\r\n'
            f'                    <parentModelGroupCompositor isNull="true" />\r\n'
            f'                    <timeZone isNull="true" />\r\n'
            f'                </annotation>\r\n'
            f'            </property>'
        )
    props_xml = '\r\n'.join(prop_lines)
    if props_xml:
        props_xml = f'\r\n{props_xml}\r\n            '

    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\r\n'
        f'<teamworks>\r\n'
        f'    <twClass id="{bo_id}" name="{_esc_attr(bo_name)}">\r\n'
        f'        <lastModified>{int(time.time() * 1000)}</lastModified>\r\n'
        f'        <lastModifiedBy isNull="true" />\r\n'
        f'        <tenantId isNull="true" />\r\n'
        f'        <classId>{bo_id}</classId>\r\n'
        f'        <type>1</type>\r\n'
        f'        <isSystem>false</isSystem>\r\n'
        f'        <shared>false</shared>\r\n'
        f'        <isShadow>false</isShadow>\r\n'
        f'        <globalLifetime>false</globalLifetime>\r\n'
        f'        <internalName isNull="true" />\r\n'
        f'        <extensionType isNull="true" />\r\n'
        f'        <saveServiceRef isNull="true" />\r\n'
        f'        <bpmn2Data isNull="true" />\r\n'
        f'        <externalId>itm.{bo_id}</externalId>\r\n'
        f'        <dependencySummary isNull="true" />\r\n'
        f'        <jsonData>{_esc_text(json_data)}</jsonData>\r\n'
        f'        <dataName isNull="true" />\r\n'
        f'        <allowAdditionalProperties>false</allowAdditionalProperties>\r\n'
        f'{desc_tag}\r\n'
        f'        <guid>guid:{guid_portion}</guid>\r\n'
        f'        <versionId>{version_id}</versionId>\r\n'
        f'        <definition>{props_xml}<validator>\r\n'
        f'                <className isNull="true" />\r\n'
        f'                <errorMessage isNull="true" />\r\n'
        f'                <webWidgetJavaClass isNull="true" />\r\n'
        f'                <externalType isNull="true" />\r\n'
        f'                <configData>\r\n'
        f'                    <schema>\r\n'
        f'                        <simpleType name="{_esc_attr(bo_name)}">\r\n'
        f'                            <restriction base="String" />\r\n'
        f'                        </simpleType>\r\n'
        f'                    </schema>\r\n'
        f'                </configData>\r\n'
        f'            </validator>\r\n'
        f'            <annotation type="com.lombardisoftware.core.xml.XMLTypeAnnotation" version="2.0">\r\n'
        f'                <exclude isNull="true" />\r\n'
        f'                <anonymous isNull="true" />\r\n'
        f'                <local isNull="true" />\r\n'
        f'                <name isNull="true" />\r\n'
        f'                <namespace isNull="true" />\r\n'
        f'                <elementName isNull="true" />\r\n'
        f'                <elementNamespace isNull="true" />\r\n'
        f'                <protoTypeName isNull="true" />\r\n'
        f'                <baseTypeName isNull="true" />\r\n'
        f'                <specialType isNull="true" />\r\n'
        f'                <contentTypeVariety isNull="true" />\r\n'
        f'                <xscRef isNull="true" />\r\n'
        f'            </annotation>\r\n'
        f'        </definition>\r\n'
        f'    </twClass>\r\n'
        f'</teamworks>\r\n'
    )


def _render_selection_xml(
    bo_id: str,
    bo_name: str,
    version_id: str,
    description: Optional[str],
    options: list[dict],
    project_namespace: str,
) -> str:
    guid_portion = bo_id[bo_id.index('.') + 1:]
    desc_tag = (
        f'        <description isNull="true" />'
        if description is None
        else f'        <description>{_esc_text(description)}</description>'
    )
    json_data = _selection_json_data(bo_id, bo_name, description, options, project_namespace)
    options_xml = '\r\n'.join(
        f'                            <option value="{_esc_attr(o["value"])}" display="{_esc_attr(o["display"])}" />'
        for o in options
    )

    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\r\n'
        f'<teamworks>\r\n'
        f'    <twClass id="{bo_id}" name="{_esc_attr(bo_name)}">\r\n'
        f'        <lastModified>{int(time.time() * 1000)}</lastModified>\r\n'
        f'        <lastModifiedBy isNull="true" />\r\n'
        f'        <tenantId isNull="true" />\r\n'
        f'        <classId>{bo_id}</classId>\r\n'
        f'        <type>0</type>\r\n'
        f'        <isSystem>false</isSystem>\r\n'
        f'        <shared>false</shared>\r\n'
        f'        <isShadow>false</isShadow>\r\n'
        f'        <globalLifetime>false</globalLifetime>\r\n'
        f'        <internalName isNull="true" />\r\n'
        f'        <extensionType isNull="true" />\r\n'
        f'        <saveServiceRef isNull="true" />\r\n'
        f'        <bpmn2Data isNull="true" />\r\n'
        f'        <externalId>itm.{bo_id}</externalId>\r\n'
        f'        <dependencySummary isNull="true" />\r\n'
        f'        <jsonData>{_esc_text(json_data)}</jsonData>\r\n'
        f'        <dataName isNull="true" />\r\n'
        f'        <allowAdditionalProperties>false</allowAdditionalProperties>\r\n'
        f'{desc_tag}\r\n'
        f'        <guid>guid:{guid_portion}</guid>\r\n'
        f'        <versionId>{version_id}</versionId>\r\n'
        f'        <definition>\r\n'
        f'            <validator>\r\n'
        f'                <className isNull="true" />\r\n'
        f'                <errorMessage isNull="true" />\r\n'
        f'                <webWidgetJavaClass isNull="true" />\r\n'
        f'                <externalType isNull="true" />\r\n'
        f'                <configData>\r\n'
        f'                    <schema>\r\n'
        f'                        <simpleType name="{_esc_attr(bo_name)}">\r\n'
        f'                            <restriction base="Selection">\r\n'
        f'{options_xml}\r\n'
        f'                            </restriction>\r\n'
        f'                        </simpleType>\r\n'
        f'                    </schema>\r\n'
        f'                </configData>\r\n'
        f'            </validator>\r\n'
        f'            <annotation type="com.lombardisoftware.core.xml.XMLTypeAnnotation" version="2.0">\r\n'
        f'                <exclude isNull="true" />\r\n'
        f'                <anonymous isNull="true" />\r\n'
        f'                <local isNull="true" />\r\n'
        f'                <name isNull="true" />\r\n'
        f'                <namespace isNull="true" />\r\n'
        f'                <elementName isNull="true" />\r\n'
        f'                <elementNamespace isNull="true" />\r\n'
        f'                <protoTypeName isNull="true" />\r\n'
        f'                <baseTypeName isNull="true" />\r\n'
        f'                <specialType isNull="true" />\r\n'
        f'                <contentTypeVariety isNull="true" />\r\n'
        f'                <xscRef isNull="true" />\r\n'
        f'            </annotation>\r\n'
        f'        </definition>\r\n'
        f'    </twClass>\r\n'
        f'</teamworks>\r\n'
    )


# ---------------------------------------------------------------------------
# Main apply logic
# ---------------------------------------------------------------------------

def apply_bos(
    source_twx: Path,
    bo_files: list[Path],
    out_twx: Path,
    version: str,
) -> None:
    # ── 1. Load source TWX ──────────────────────────────────────────────────
    try:
        zin = zipfile.ZipFile(source_twx, 'r')
    except (zipfile.BadZipFile, OSError) as e:
        raise SystemExit(f"ERROR: cannot open {source_twx}: {e}")

    entries: dict[str, bytes] = {}
    for info in zin.infolist():
        if not info.is_dir():
            entries[info.filename] = zin.read(info.filename)
    zin.close()

    pkg_xml = entries['META-INF/package.xml'].decode('utf-8')

    # ── 2. Load all artifact XMLs (text paths only) ─────────────────────────
    artifact_xml_map: dict[str, str] = {}
    for path, raw in entries.items():
        if path.startswith('objects/') and path.endswith('.xml'):
            artifact_xml_map[path] = raw.decode('utf-8')

    # ── 3. Resolve project namespace + System Data dep guid ─────────────────
    project_namespace = _resolve_namespace(pkg_xml, artifact_xml_map)
    twsys_dep_guid    = _read_twsys_dep_guid(pkg_xml)

    # ── 4. Build bo_id_map: name → typed UUID (from existing TWX first) ─────
    # This is the symbol table — covers existing BOs AND the ones we're adding,
    # so cross-BO property references resolve regardless of input file order.
    existing: dict[str, str] = {}  # name → id
    for obj_id, obj_name in _all_twclass_ids(pkg_xml):
        existing[obj_name] = obj_id

    # Load specs; assign IDs: reuse existing UUID for same-name (overwrite),
    # mint fresh for new BOs.
    specs: list[tuple[str, str, dict]] = []  # (name, id, spec)
    for bo_path in bo_files:
        spec = _load_bo_spec(bo_path)
        bo_name = bo_path.stem  # filename without .bo.json
        if bo_path.suffix == '.json' and bo_name.endswith('.bo'):
            bo_name = bo_name[:-3]  # handle double-suffix if passed as .bo.json
        bo_id = existing.get(bo_name) or f"12.{_mint()}"
        existing[bo_name] = bo_id  # register immediately for forward refs
        specs.append((bo_name, bo_id, spec))

    # The full symbol table (existing + new) for classRef resolution
    bo_id_map: dict[str, str] = dict(existing)

    # ── 5. Apply each BO ────────────────────────────────────────────────────
    modified_pkg = pkg_xml

    for bo_name, bo_id, spec in specs:
        version_id  = _mint()
        artifact_path = f'objects/{bo_id}.xml'
        is_overwrite  = artifact_path in entries  # True if replacing existing

        # Remove old package.xml entry and artifact (if overwriting)
        if is_overwrite:
            modified_pkg = _remove_object_entry(modified_pkg, bo_id)
            # artifact bytes replaced below

        # Build new artifact XML
        if spec['kind'] == 'complex':
            xml_bytes = _render_complex_xml(
                bo_id, bo_name, version_id,
                spec.get('description'),
                spec.get('properties', []),
                twsys_dep_guid, bo_id_map, project_namespace,
            ).encode('utf-8')
            action = 'overwrite' if is_overwrite else 'add'
        else:  # selection
            xml_bytes = _render_selection_xml(
                bo_id, bo_name, version_id,
                spec.get('description'),
                spec['options'],
                project_namespace,
            ).encode('utf-8')
            action = 'overwrite' if is_overwrite else 'add'

        entries[artifact_path] = xml_bytes

        # Add new package.xml <object> entry
        entry_line = f'<object id="{bo_id}" versionId="{version_id}" name="{_esc_attr(bo_name)}" type="twClass"/>'
        modified_pkg = _insert_object_entry(modified_pkg, entry_line)

        print(f'  [{action}] {bo_name}  ({bo_id})')

    # ── 6. Stamp new snapshot metadata ──────────────────────────────────────
    modified_pkg = _update_snapshot(modified_pkg, version)
    entries['META-INF/package.xml'] = modified_pkg.encode('utf-8')

    # ── 7. Write output TWX ─────────────────────────────────────────────────
    out_twx.parent.mkdir(parents=True, exist_ok=True)
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zout:
        for path, raw in entries.items():
            zout.writestr(path, raw)
    out_twx.write_bytes(buf.getvalue())
    print(f'\nWritten: {out_twx}')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Add or overwrite Business Objects in a BAW TWX file.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split('USAGE')[1] if 'USAGE' in __doc__ else '',
    )
    parser.add_argument('--source',  required=True, metavar='TWX',
                        help='Source .twx file (read-only; never modified)')
    parser.add_argument('--version', required=True,
                        help='Snapshot version name for the output TWX, e.g. 1.2.3.4')
    parser.add_argument('--out',     required=True, metavar='TWX',
                        help='Output .twx path')
    parser.add_argument('bo_files',  nargs='+', metavar='FILE.bo.json',
                        help='One or more .bo.json descriptor files')
    args = parser.parse_args()

    source  = Path(args.source)
    out     = Path(args.out)
    bo_paths = [Path(f) for f in args.bo_files]

    if not source.exists():
        raise SystemExit(f'ERROR: source TWX not found: {source}')
    if source.resolve() == out.resolve():
        raise SystemExit('ERROR: --out must differ from --source')

    # Normalise .bo.json vs just .json suffixes (folders are expanded to all .bo.json / .json files within them)
    resolved: list[Path] = []
    for p in bo_paths:
        if not p.exists():
            raise SystemExit(f'ERROR: BO file or directory not found: {p}')
        if p.is_dir():
            dir_files = list(p.glob('*.bo.json'))
            if not dir_files:
                dir_files = list(p.glob('*.json'))
            if not dir_files:
                raise SystemExit(f'ERROR: No .bo.json or .json files found in directory: {p}')
            resolved.extend(sorted(dir_files))
        else:
            resolved.append(p)

    print(f'Source : {source}')
    print(f'Output : {out}  (snapshot "{args.version}")')
    print(f'BOs    : {len(resolved)} file(s)\n')

    apply_bos(source, resolved, out, args.version)


if __name__ == '__main__':
    main()
