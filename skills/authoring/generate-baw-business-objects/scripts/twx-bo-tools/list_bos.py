#!/usr/bin/env python3
"""
list_bos.py — discover and print all Business Objects in a TWX file.

Follows the same logic as BusinessObjectCollection in src/twx/business-object.ts:

  1. Open the TWX zip and read META-INF/package.xml.
  2. Find every <object type="twClass"> entry — each is a BO.
  3. For each one, open its objects/<id>.xml artifact file.
  4. Read <type>: 1 = complex, 0 = simple/selection.
  5. Complex: walk <definition><property>* to read name, classRef, array, required, hidden.
     Resolve classRef against the primitive-UUID table and the project's own BO names.
  6. Simple/selection: walk <definition><validator><configData><schema><simpleType>
     <restriction> to read baseType and <option> entries.

Usage:
    python list_bos.py path/to/app.twx
    python list_bos.py path/to/app.twx --json
"""

import argparse
import json
import re
import sys
import zipfile
from dataclasses import dataclass, field
from typing import Optional
from xml.etree import ElementTree as ET


# ---------------------------------------------------------------------------
# System Data primitive UUID → friendly name  (src/twx/uuid.ts PRIMITIVE_UUIDS)
# ---------------------------------------------------------------------------
PRIMITIVE_UUIDS: dict[str, str] = {
    "12.db884a3c-c533-44b7-bb2d-47bec8ad4022": "String",
    "12.83ff975e-8dbc-42e5-b738-fa8bc08274a2": "Boolean",
    "12.3fa0d7a0-828a-4d60-99cc-db5ed143fc2d": "Integer",
    "12.536b2aa5-a30f-4eca-87fa-3a28066753ee": "Decimal",
    "12.68474ab0-d56f-47ee-b7e9-510b45a2a8be": "Date",
    "12.20fdb1a2-f6ec-462e-8627-d49859ba42ae": "Time",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class BoProperty:
    name: str
    type: Optional[str]      # resolved friendly name, or None if unresolvable
    class_ref: str           # raw <classRef> value
    array: bool
    required: bool
    hidden: bool
    description: Optional[str]


@dataclass
class SelectionOption:
    value: str
    display: str


@dataclass
class BusinessObject:
    id: str
    name: str
    kind: str                # 'complex' | 'selection' | 'simple'
    description: Optional[str]
    properties: list[BoProperty] = field(default_factory=list)   # complex only
    base_type: Optional[str] = None                               # simple only
    options: list[SelectionOption] = field(default_factory=list)  # selection only


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

def _text(el: Optional[ET.Element], tag: str) -> Optional[str]:
    """Return stripped text content of the first child with the given tag, or None."""
    if el is None:
        return None
    child = el.find(tag)
    if child is None:
        return None
    if child.get("isNull") == "true":
        return None
    return (child.text or "").strip() or None


def _parse(xml_bytes: bytes) -> ET.Element:
    return ET.fromstring(xml_bytes)


# ---------------------------------------------------------------------------
# classRef resolution
# ---------------------------------------------------------------------------

def _resolve_class_ref(class_ref: str, bo_by_id: dict[str, str]) -> Optional[str]:
    """
    Resolve a raw <classRef> to a friendly type name.

    classRef formats:
      - Local BO:   /12.<guid>          (leading slash, no scope prefix)
      - Primitive:  <depGuid>/12.<guid> (System Data dep GUID + slash + typed UUID)

    Returns the friendly name (e.g. 'String', 'Customer') or None if unresolvable.
    """
    # Strip leading slash to get the typed UUID for local BOs, or split on the
    # first slash for cross-toolkit (primitive) refs.
    slash = class_ref.find("/")
    if slash == -1:
        # Malformed — no slash at all; try direct lookup.
        typed_uuid = class_ref
    elif slash == 0:
        # Local BO: /12.<guid>
        typed_uuid = class_ref[1:]
    else:
        # Cross-toolkit: <depGuid>/12.<guid>
        typed_uuid = class_ref[slash + 1:]

    # Primitive?
    if typed_uuid in PRIMITIVE_UUIDS:
        return PRIMITIVE_UUIDS[typed_uuid]

    # Local BO?
    if typed_uuid in bo_by_id:
        return bo_by_id[typed_uuid]

    return None


# ---------------------------------------------------------------------------
# Core parser
# ---------------------------------------------------------------------------

def list_business_objects(twx_path: str) -> list[BusinessObject]:
    """
    Open a TWX file and return all BusinessObject records found inside it.
    Follows the same discovery path as BusinessObjectCollection.findTwClassEntries().
    """
    with zipfile.ZipFile(twx_path, "r") as zf:
        # ── 1. Read package.xml ───────────────────────────────────────────────
        pkg_bytes = zf.read("META-INF/package.xml")
        pkg_root = _parse(pkg_bytes)

        # Strip the namespace prefix from the root element so .find() works simply.
        # package.xml uses xmlns:p="..." on the root; strip it from the root tag only.
        # Child elements have no namespace prefix, so ET finds them fine.

        # ── 2. Find all <object type="twClass"> entries ───────────────────────
        objects_el = pkg_root.find("objects")
        if objects_el is None:
            return []

        twclass_entries: list[tuple[str, str]] = []  # (id, name)
        for obj in objects_el.findall("object"):
            if obj.get("type") == "twClass":
                oid = obj.get("id", "")
                oname = obj.get("name", "")
                if oid:
                    twclass_entries.append((oid, oname))

        if not twclass_entries:
            return []

        # ── 3. Load artifact XML for each twClass ─────────────────────────────
        # Build a map id → raw ET.Element (<twClass> root) for all available BOs.
        # Also build id → name for classRef resolution.
        raw_elements: dict[str, ET.Element] = {}
        bo_by_id: dict[str, str] = {}  # typed UUID → BO name

        for oid, oname in twclass_entries:
            artifact_path = f"objects/{oid}.xml"
            try:
                artifact_bytes = zf.read(artifact_path)
            except KeyError:
                continue  # artifact file missing — skip
            doc_root = _parse(artifact_bytes)
            tw_class = doc_root.find("twClass")
            if tw_class is None:
                continue
            raw_elements[oid] = tw_class
            bo_by_id[oid] = oname

        # ── 4. Parse each BO ──────────────────────────────────────────────────
        results: list[BusinessObject] = []
        for oid, oname in twclass_entries:
            tw_class = raw_elements.get(oid)
            if tw_class is None:
                continue

            bo_type = (tw_class.findtext("type") or "").strip()
            desc_el = tw_class.find("description")
            description: Optional[str] = None
            if desc_el is not None and desc_el.get("isNull") != "true":
                description = (desc_el.text or "").strip() or None

            if bo_type == "1":
                # ── Complex BO ────────────────────────────────────────────────
                properties = _parse_complex_properties(tw_class, bo_by_id)
                results.append(BusinessObject(
                    id=oid,
                    name=oname,
                    kind="complex",
                    description=description,
                    properties=properties,
                ))

            else:
                # ── Simple BO (type="0") ──────────────────────────────────────
                # Path: <definition><validator><configData><schema><simpleType><restriction>
                restriction = _find_restriction(tw_class)
                if restriction is None:
                    results.append(BusinessObject(
                        id=oid,
                        name=oname,
                        kind="simple",
                        description=description,
                        base_type=None,
                    ))
                    continue

                base_type = restriction.get("base")
                if base_type == "Selection":
                    options = [
                        SelectionOption(
                            value=opt.get("value", ""),
                            display=opt.get("display", ""),
                        )
                        for opt in restriction.findall("option")
                    ]
                    results.append(BusinessObject(
                        id=oid,
                        name=oname,
                        kind="selection",
                        description=description,
                        base_type=base_type,
                        options=options,
                    ))
                else:
                    # Length-restricted string or other simple type.
                    results.append(BusinessObject(
                        id=oid,
                        name=oname,
                        kind="simple",
                        description=description,
                        base_type=base_type,
                    ))

        return results


def _parse_complex_properties(
    tw_class: ET.Element,
    bo_by_id: dict[str, str],
) -> list[BoProperty]:
    """
    Parse <definition><property>* from a complex twClass element.
    Mirrors ComplexBusinessObject.properties + Property accessors.
    """
    definition = tw_class.find("definition")
    if definition is None:
        return []

    props: list[BoProperty] = []
    for prop_el in definition.findall("property"):
        name = (prop_el.findtext("name") or "").strip()
        if not name:
            continue

        class_ref = (prop_el.findtext("classRef") or "").strip()
        array = (prop_el.findtext("arrayProperty") or "false").strip() == "true"
        required = (prop_el.findtext("propertyRequired") or "false").strip() == "true"
        hidden = (prop_el.findtext("propertyHidden") or "false").strip() == "true"

        desc_el = prop_el.find("description")
        prop_desc: Optional[str] = None
        if desc_el is not None and desc_el.get("isNull") != "true":
            prop_desc = (desc_el.text or "").strip() or None

        resolved = _resolve_class_ref(class_ref, bo_by_id)

        props.append(BoProperty(
            name=name,
            type=resolved,
            class_ref=class_ref,
            array=array,
            required=required,
            hidden=hidden,
            description=prop_desc,
        ))

    return props


def _find_restriction(tw_class: ET.Element) -> Optional[ET.Element]:
    """
    Navigate the path:
      <definition><validator><configData><schema><simpleType><restriction>
    Mirrors SimpleBusinessObject.restrictionElement().
    """
    definition = tw_class.find("definition")
    if definition is None:
        return None
    validator = definition.find("validator")
    if validator is None:
        return None
    config_data = validator.find("configData")
    if config_data is None:
        return None
    schema = config_data.find("schema")
    if schema is None:
        return None
    simple_type = schema.find("simpleType")
    if simple_type is None:
        return None
    return simple_type.find("restriction")


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def _print_human(bos: list[BusinessObject]) -> None:
    if not bos:
        print("No Business Objects found.")
        return

    print(f"Found {len(bos)} Business Object(s):\n")
    for bo in bos:
        kind_label = {"complex": "Complex", "selection": "Selection", "simple": "Simple"}.get(bo.kind, bo.kind)
        print(f"  [{kind_label}] {bo.name}  ({bo.id})")
        if bo.description:
            print(f"    Description: {bo.description}")

        if bo.kind == "complex":
            if bo.properties:
                for p in bo.properties:
                    type_label = p.type or f"? ({p.class_ref})"
                    flags = []
                    if p.array:
                        flags.append("array")
                    if p.required:
                        flags.append("required")
                    if p.hidden:
                        flags.append("hidden")
                    flag_str = f"  [{', '.join(flags)}]" if flags else ""
                    print(f"    • {p.name}: {type_label}{flag_str}")
                    if p.description:
                        print(f"        \"{p.description}\"")
            else:
                print("    (no properties)")

        elif bo.kind == "selection":
            for opt in bo.options:
                print(f"    • {opt.value!r} = {opt.display!r}")

        elif bo.kind == "simple":
            print(f"    Base type: {bo.base_type or '(unknown)'}")

        print()


def _to_dict(bo: BusinessObject) -> dict:
    d: dict = {"id": bo.id, "name": bo.name, "kind": bo.kind}
    if bo.description:
        d["description"] = bo.description
    if bo.kind == "complex":
        d["properties"] = [
            {
                "name": p.name,
                "type": p.type,
                "classRef": p.class_ref,
                **({} if not p.array else {"array": True}),
                **({} if not p.required else {"required": True}),
                **({} if not p.hidden else {"hidden": True}),
                **({} if p.description is None else {"description": p.description}),
            }
            for p in bo.properties
        ]
    elif bo.kind == "selection":
        d["baseType"] = bo.base_type
        d["options"] = [{"value": o.value, "display": o.display} for o in bo.options]
    elif bo.kind == "simple":
        d["baseType"] = bo.base_type
    return d


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="List all Business Objects in a BAW TWX file."
    )
    parser.add_argument("twx", help="Path to the .twx file")
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON instead of human-readable text"
    )
    args = parser.parse_args()

    try:
        bos = list_business_objects(args.twx)
    except (zipfile.BadZipFile, KeyError) as e:
        print(f"ERROR: could not read TWX: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps([_to_dict(bo) for bo in bos], indent=2))
    else:
        _print_human(bos)


if __name__ == "__main__":
    main()
