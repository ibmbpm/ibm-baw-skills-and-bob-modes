#!/usr/bin/env python3
"""
generate_baw_bpmn.py - Deterministic BPMN 2.0 generator for IBM Business
Automation Workflow (BAW) import.

Reads a process JSON config (see references/PROCESS_JSON_SCHEMA.md) and emits
BPMN 2.0 XML in the exact dialect IBM BAW itself uses when exporting a process,
plus a .zip archive ready for the BAW import wizards (both Workflow Center
"Import Process App" and Process Designer "File > Import" expect a .zip).

Design principles:
- Only emits BPMN constructs that IBM documents as supported by the BAW BPMN
  import mapping. Anything else is rejected at validation time instead of
  being silently dropped by BAW at import time.
- All XML ids are uuid5-derived from the config ids, so regenerating the same
  config always produces the same XML, and every sourceRef/targetRef is
  guaranteed to match a real element id.
- No BPMN DI (diagram) section is generated: BAW ignores incoming layout and
  auto-arranges the diagram, so DI is pure risk with zero benefit.
- Standard library only. No pip installs needed.

Outputs, all in the output file's directory (use one directory per process):
    <name>.bpmn            the process, in BAW's own export dialect
    <name>.xsd             business object schema (only when businessObjects defined)
    <name>.zip             the import archive (.bpmn + .xsd)
    README.md              Mermaid diagram + process documentation

Usage:
    python generate_baw_bpmn.py <config.json> <output.bpmn> [--validate-only] [--no-zip] [--no-readme]

Exit codes: 0 = success, 1 = validation errors (nothing written), 2 = bad invocation.
"""

import json
import re
import sys
import uuid
import zipfile
from pathlib import Path
from urllib.parse import quote
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

# Fixed namespace so uuid5 ids are stable across runs and machines.
ID_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
XMI_NS = "http://www.omg.org/XMI"
XSD_NS = "http://www.w3.org/2001/XMLSchema"

EXPORTER = "generate-baw-bpmn"
EXPORTER_VERSION = "1.0.0"

# Element types accepted by this generator. Every entry maps 1:1 to a row in
# IBM's "Mapping BPMN 2.0 constructs to workflow objects after import" table.
TASK_TYPES = {"userTask", "serviceTask", "scriptTask", "manualTask", "businessRuleTask", "task"}
GATEWAY_TYPES = {"exclusiveGateway", "inclusiveGateway", "parallelGateway"}
EVENT_TYPES = {"startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent", "boundaryEvent"}
CONTAINER_TYPES = {"subProcess"}
ANNOTATION_TYPES = {"textAnnotation"}  # imported as a Note; takes no flows
ALL_TYPES = TASK_TYPES | GATEWAY_TYPES | EVENT_TYPES | CONTAINER_TYPES | ANNOTATION_TYPES

# Friendly business-object field types -> XSD builtins (BAW's BO primitive set).
# Raw XSD builtin names are accepted too.
FIELD_TYPE_MAP = {
    "String": "string", "Integer": "integer", "Decimal": "decimal",
    "Boolean": "boolean", "Date": "date", "Time": "time", "DateTime": "dateTime",
}
XSD_BUILTINS = set(FIELD_TYPE_MAP.values()) | {"anyType"}

# eventDefinition values allowed per event type (per the IBM mapping table).
EVENT_DEFINITIONS = {
    "startEvent": {None, "message", "timer", "error"},
    "endEvent": {None, "message", "error", "terminate"},
    "intermediateCatchEvent": {"message", "timer"},
    "intermediateThrowEvent": {"message"},
    "boundaryEvent": {"message", "timer", "error"},
}


def stable_id(process_name: str, config_id: str) -> str:
    """Deterministic bpmnid for a config id. Same config in, same XML out."""
    return "bpmnid-" + str(uuid.uuid5(ID_NAMESPACE, f"{process_name}/{config_id}"))


class ConfigError(Exception):
    pass


def load_config(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Config is not valid JSON: {e}")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(config: dict) -> tuple:
    """Return (errors, warnings). Errors block generation; warnings don't."""
    errors, warnings = [], []

    process = config.get("process")
    if not isinstance(process, dict) or not process.get("name"):
        errors.append("Config must have a 'process' object with at least a 'name'.")
        return errors, warnings

    name = process["name"]
    if re.search(r'[<>&"\\/:*?|]', name):
        errors.append(f"Process name {name!r} contains characters BAW rejects in artifact names.")

    _validate_flow_graph(config, "process", errors, warnings, top_level=True)

    bo_names = _validate_business_objects(config.get("businessObjects", []), errors)

    used_bo = set()
    for var in config.get("variables", []):
        if not var.get("name"):
            errors.append("Every entry in 'variables' needs a 'name'.")
            continue
        vtype = var.get("type", "xsd:anyType")
        if vtype in bo_names:
            used_bo.add(vtype)
        elif not (vtype.startswith("xsd:") and vtype[4:] in XSD_BUILTINS):
            errors.append(
                f"variable '{var['name']}' has type '{vtype}', which is neither a defined "
                f"business object nor a supported simple type (xsd:{'/xsd:'.join(sorted(XSD_BUILTINS))})."
            )
    for unused in sorted(bo_names - used_bo - {f.get("type") for bo in config.get("businessObjects", []) for f in bo.get("fields", [])}):
        warnings.append(f"business object '{unused}' is defined but no variable or field uses it.")

    return errors, warnings


def _validate_business_objects(business_objects, errors) -> set:
    """Validate the businessObjects section; return the set of defined names."""
    names = set()
    for bo in business_objects:
        name = bo.get("name")
        if not name or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            errors.append(f"business object name {name!r} must be a simple identifier "
                          f"(letters/digits/underscore, no spaces) - it becomes an XSD type name.")
            continue
        if name in names:
            errors.append(f"duplicate business object '{name}'.")
        names.add(name)
    for bo in business_objects:
        for field in bo.get("fields", []):
            fname = field.get("name")
            if not fname or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", fname):
                errors.append(f"business object '{bo.get('name')}': field name {fname!r} must be a "
                              f"simple identifier.")
            ftype = field.get("type", "String")
            if ftype not in FIELD_TYPE_MAP and ftype not in XSD_BUILTINS and ftype not in names:
                errors.append(
                    f"business object '{bo.get('name')}': field '{fname}' has type '{ftype}', which is "
                    f"neither a primitive ({', '.join(sorted(FIELD_TYPE_MAP))}) nor another defined "
                    f"business object."
                )
    return names


def _validate_flow_graph(scope: dict, scope_label: str, errors, warnings, top_level: bool):
    """Validate elements+flows of a scope (the whole config, or a subProcess)."""
    elements = scope.get("elements") or []
    flows = scope.get("flows") or []

    if not elements:
        errors.append(f"{scope_label}: no 'elements' defined.")
        return

    ids = {}
    for el in elements:
        el_id, el_type = el.get("id"), el.get("type")
        if not el_id:
            errors.append(f"{scope_label}: element missing 'id': {el}")
            continue
        if el_id in ids:
            errors.append(f"{scope_label}: duplicate element id '{el_id}'.")
        ids[el_id] = el
        if el_type not in ALL_TYPES:
            errors.append(
                f"{scope_label}: element '{el_id}' has type '{el_type}', which the BAW import "
                f"mapping does not support. Allowed: {', '.join(sorted(ALL_TYPES))}."
            )
            continue
        if el_type == "textAnnotation":
            if not el.get("text"):
                warnings.append(f"{scope_label}: textAnnotation '{el_id}' has no 'text'.")
            continue
        if not el.get("name"):
            warnings.append(f"{scope_label}: element '{el_id}' has no name; BAW will show an unnamed node.")

        ev_def = el.get("eventDefinition")
        if el_type in EVENT_DEFINITIONS:
            allowed = EVENT_DEFINITIONS[el_type]
            if ev_def not in allowed:
                allowed_str = ", ".join(sorted(str(a) for a in allowed))
                errors.append(
                    f"{scope_label}: '{el_id}' ({el_type}) has eventDefinition '{ev_def}'; allowed: {allowed_str}."
                )
        elif ev_def:
            errors.append(f"{scope_label}: '{el_id}' ({el_type}) cannot carry an eventDefinition.")

        if el_type == "boundaryEvent":
            attached = el.get("attachedToRef")
            if not attached:
                errors.append(f"{scope_label}: boundaryEvent '{el_id}' needs 'attachedToRef'.")
        if el_type == "subProcess":
            _validate_flow_graph(el, f"subProcess '{el_id}'", errors, warnings, top_level=False)

    # boundary attachedToRef must resolve to a task/subProcess in the same scope
    for el in elements:
        if el.get("type") == "boundaryEvent" and el.get("attachedToRef"):
            target = ids.get(el["attachedToRef"])
            if target is None:
                errors.append(f"{scope_label}: boundaryEvent '{el['id']}' attachedToRef "
                              f"'{el['attachedToRef']}' does not match any element id.")
            elif target.get("type") not in TASK_TYPES | CONTAINER_TYPES:
                errors.append(f"{scope_label}: boundaryEvent '{el['id']}' must attach to a task "
                              f"or subProcess, not a {target.get('type')}.")

    # start/end rules (IBM: only a single none start event is honored)
    starts = [e for e in elements if e.get("type") == "startEvent"]
    none_starts = [e for e in starts if not e.get("eventDefinition")]
    ends = [e for e in elements if e.get("type") == "endEvent"]
    if len(none_starts) != 1:
        errors.append(f"{scope_label}: need exactly one plain (none) startEvent; found {len(none_starts)}. "
                      f"(BAW honors only a single none start event per process or subprocess.)")
    if not ends:
        errors.append(f"{scope_label}: at least one endEvent is required.")

    # flows
    incoming, outgoing = {}, {}
    seen_flow_ids = set()
    for fl in flows:
        fl_id = fl.get("id")
        if not fl_id:
            errors.append(f"{scope_label}: flow missing 'id': {fl}")
            continue
        if fl_id in seen_flow_ids or fl_id in ids:
            errors.append(f"{scope_label}: duplicate id '{fl_id}'.")
        seen_flow_ids.add(fl_id)
        src, tgt = fl.get("sourceRef"), fl.get("targetRef")
        for ref, label in ((src, "sourceRef"), (tgt, "targetRef")):
            if ref not in ids:
                errors.append(f"{scope_label}: flow '{fl_id}' {label} '{ref}' does not match any element id.")
            elif ids[ref].get("type") in ANNOTATION_TYPES:
                errors.append(f"{scope_label}: flow '{fl_id}' connects to textAnnotation '{ref}'; "
                              f"annotations are free-standing notes and take no sequence flows.")
        if src in ids and tgt in ids:
            outgoing.setdefault(src, []).append(fl)
            incoming.setdefault(tgt, []).append(fl)
        if fl.get("condition") and src in ids and ids[src].get("type") not in GATEWAY_TYPES:
            warnings.append(f"{scope_label}: flow '{fl_id}' has a condition but its source is not a "
                            f"gateway; BAW only evaluates conditions on gateway outputs.")

    # per-node degree rules
    for el_id, el in ids.items():
        el_type = el.get("type")
        n_in = len(incoming.get(el_id, []))
        n_out = len(outgoing.get(el_id, []))
        if el_type == "startEvent" and n_in:
            errors.append(f"{scope_label}: startEvent '{el_id}' cannot have incoming flows.")
        if el_type == "endEvent" and n_out:
            errors.append(f"{scope_label}: endEvent '{el_id}' cannot have outgoing flows.")
        if el_type == "boundaryEvent":
            if n_in:
                errors.append(f"{scope_label}: boundaryEvent '{el_id}' cannot have incoming flows.")
            if not n_out:
                errors.append(f"{scope_label}: boundaryEvent '{el_id}' needs an outgoing flow (its exception path).")
            continue
        if el_type in TASK_TYPES | CONTAINER_TYPES | GATEWAY_TYPES:
            if not n_in:
                errors.append(f"{scope_label}: '{el_id}' ({el_type}) has no incoming flow.")
            if not n_out:
                errors.append(f"{scope_label}: '{el_id}' ({el_type}) has no outgoing flow.")
        if el_type in GATEWAY_TYPES and n_out < 2 and n_in < 2:
            warnings.append(f"{scope_label}: gateway '{el_id}' neither forks (2+ out) nor joins (2+ in); "
                            f"a gateway with one path in and one out is doing nothing.")
        if el_type in ("exclusiveGateway", "inclusiveGateway") and n_out >= 2:
            outs = outgoing.get(el_id, [])
            defaults = [f for f in outs if f.get("isDefault")]
            if len(defaults) > 1:
                errors.append(f"{scope_label}: gateway '{el_id}' has more than one default flow.")
            unconditioned = [f for f in outs if not f.get("condition") and not f.get("isDefault")]
            if unconditioned and not defaults:
                warnings.append(f"{scope_label}: gateway '{el_id}' has unconditioned non-default branches "
                                f"({', '.join(f['id'] for f in unconditioned)}); mark one branch isDefault "
                                f"or add conditions so the logic survives import review.")

    # reachability (boundary events are entered via their attached task, not a flow)
    start_ids = [e["id"] for e in none_starts if e.get("id")]
    if start_ids and not errors:
        reachable = set()
        stack = list(start_ids)
        while stack:
            node = stack.pop()
            if node in reachable:
                continue
            reachable.add(node)
            for fl in outgoing.get(node, []):
                stack.append(fl["targetRef"])
            # a reachable task makes its boundary events reachable
            for el in elements:
                if el.get("type") == "boundaryEvent" and el.get("attachedToRef") == node:
                    stack.append(el["id"])
        unreachable = [i for i in ids if i not in reachable
                       and ids[i].get("type") not in ANNOTATION_TYPES]
        if unreachable:
            errors.append(f"{scope_label}: unreachable from start: {', '.join(sorted(unreachable))}.")

    # variable references must point at real task ids (top level only)
    if top_level:
        for var in scope.get("variables", []):
            for key in ("inputTo", "outputFrom"):
                for task_ref in var.get(key, []):
                    if task_ref not in ids:
                        errors.append(f"variable '{var.get('name')}' {key} references unknown element '{task_ref}'.")


# ---------------------------------------------------------------------------
# XML generation
# ---------------------------------------------------------------------------

def ns_segment(text: str) -> str:
    """Percent-encode a namespace path segment. BAW's own exports put raw spaces
    in namespace URIs, but strict parsers (including Python's expat) reject
    xmlns values that aren't valid URIs - encoding keeps both sides happy."""
    return quote(text, safe="")


def bo_namespace(app: str) -> str:
    """Namespace for the business-object XSD (referenced by bpmn:import)."""
    return f"http://{ns_segment(app)}/BusinessObjects"


def build_xsd(config: dict) -> str:
    """Build the sidecar XSD defining complex business objects.

    One complexType per business object, dependency-ordered (referenced types
    first), fields as elements with minOccurs from 'required' and
    maxOccurs="unbounded" for lists. The default xmlns is the XSD namespace, so
    builtin types are bare ("string") and cross-references use the tns prefix -
    the same shape Blueworks Live exports and BAW imports.
    """
    business_objects = config["businessObjects"]
    app = config["process"].get("processApp", "Imported Processes")
    by_name = {bo["name"]: bo for bo in business_objects}

    # Topological order: referenced business objects before their referencers.
    ordered, seen = [], set()

    def visit(name, trail):
        if name in seen or name in trail:  # cycles emitted in first-seen order
            return
        for field in by_name[name].get("fields", []):
            ftype = field.get("type", "String")
            if ftype in by_name:
                visit(ftype, trail | {name})
        seen.add(name)
        ordered.append(name)

    for bo in business_objects:
        visit(bo["name"], set())

    schema = Element("schema")
    schema.set("xmlns", XSD_NS)
    schema.set("xmlns:tns", bo_namespace(app))
    schema.set("targetNamespace", bo_namespace(app))
    schema.set("elementFormDefault", "qualified")
    schema.set("attributeFormDefault", "unqualified")

    for name in ordered:
        bo = by_name[name]
        ct = SubElement(schema, "complexType")
        ct.set("name", name)
        if bo.get("description"):
            ann = SubElement(ct, "annotation")
            SubElement(ann, "documentation").text = bo["description"]
        seq = SubElement(ct, "sequence")
        for field in bo.get("fields", []):
            ftype = field.get("type", "String")
            elem = SubElement(seq, "element")
            elem.set("name", field["name"])
            if ftype in by_name:
                elem.set("type", f"tns:{ftype}")
            else:
                elem.set("type", FIELD_TYPE_MAP.get(ftype, ftype))
            elem.set("minOccurs", "1" if field.get("required") else "0")
            if field.get("list"):
                elem.set("maxOccurs", "unbounded")

    rough = tostring(schema, encoding="unicode")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")
    return "\n".join(line for line in pretty.splitlines() if line.strip()) + "\n"

def build_xml(config: dict, xsd_filename: str = None) -> str:
    process_cfg = config["process"]
    proc_name = process_cfg["name"]
    app = process_cfg.get("processApp", "Imported Processes")
    snapshot = process_cfg.get("snapshot", "Main")
    target_ns = f"http://{ns_segment(app)}/{ns_segment(snapshot)}/{ns_segment(proc_name)}"
    bo_names = {bo["name"] for bo in config.get("businessObjects", [])}

    definitions = Element("bpmn:definitions")
    definitions.set("xmi:version", "2.0")
    definitions.set("xmlns:xmi", XMI_NS)
    definitions.set("xmlns:bpmn", BPMN_NS)
    definitions.set("xmlns:xsd", XSD_NS)
    # BAW's own exports bind a prefix to the targetNamespace and use it to
    # qualify attachedToRef (a QName, unlike the plain-IDREF sourceRef/targetRef).
    definitions.set("xmlns:tns", target_ns)
    if bo_names:
        definitions.set("xmlns:bo", bo_namespace(app))
    definitions.set("exporter", EXPORTER)
    definitions.set("exporterVersion", EXPORTER_VERSION)
    definitions.set("id", stable_id(proc_name, "definitions"))
    definitions.set("targetNamespace", target_ns)

    # Imports must precede all other definitions children (BPMN 2.0 schema order).
    # Complex business objects live in a sibling XSD, Blueworks-Live style; the
    # importer materializes them as BAW business objects.
    if bo_names:
        imp = SubElement(definitions, "bpmn:import")
        imp.set("namespace", bo_namespace(app))
        imp.set("location", xsd_filename or "InputOutput.xsd")
        imp.set("importType", XSD_NS)

    # itemDefinitions for declared variables (imported as business objects /
    # private variables per the IBM mapping)
    item_ids = {}
    for var in config.get("variables", []):
        item_id = stable_id(proc_name, f"item/{var['name']}")
        item_ids[var["name"]] = item_id
        item = SubElement(definitions, "bpmn:itemDefinition")
        item.set("id", item_id)
        vtype = var.get("type", "xsd:anyType")
        item.set("structureRef", f"bo:{vtype}" if vtype in bo_names else vtype)

    process = SubElement(definitions, "bpmn:process")
    process.set("id", stable_id(proc_name, "process"))
    process.set("name", proc_name)
    process.set("isClosed", "false")
    process.set("processType", "None")
    if process_cfg.get("description"):
        doc = SubElement(process, "bpmn:documentation")
        doc.text = process_cfg["description"]

    # Emit laneSet when roles are defined — BAW infers swim-lane assignment from
    # the <performer> elements on tasks (added in _emit_scope) and falls back to
    # <laneSet>/<lane>/<flowNodeRef> membership.  Both are emitted so the import
    # works correctly whether BAW reads performer semantics or lane XML.
    roles = config.get("roles", [])
    if roles:
        _emit_laneset(process, proc_name, config.get("elements", []), roles)

    _emit_scope(process, proc_name, config.get("elements", []), config.get("flows", []),
                config.get("variables", []), item_ids, roles)

    rough = tostring(definitions, encoding="unicode")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")
    # drop blank lines minidom likes to add
    return "\n".join(line for line in pretty.splitlines() if line.strip()) + "\n"


def _emit_laneset(parent: Element, proc_name: str, elements: list, roles: list):
    """Emit a laneSet grouping elements by their assigned role.

    BAW reads lane membership from two sources on import:
      1. <performer> child elements on tasks (semantic — preferred by BAW).
      2. <laneSet>/<lane>/<flowNodeRef> membership (visual fallback).
    Both are emitted so the import is robust regardless of BAW version behaviour.
    Elements with no role land in an implicit default lane (BAW creates one).
    """
    roles_by_id = {r["id"]: r for r in roles}
    # Build role_id -> [element_ids] map for all flow nodes (tasks, gateways, events).
    lane_members: dict[str, list] = {r["id"]: [] for r in roles}
    unassigned = []
    for el in elements:
        if el.get("type") in ANNOTATION_TYPES:
            continue
        role_id = el.get("role")
        if role_id and role_id in lane_members:
            lane_members[role_id].append(el["id"])
        else:
            unassigned.append(el["id"])

    # Only emit the laneSet if at least one role has members.
    if not any(lane_members.values()):
        return

    laneset = SubElement(parent, "bpmn:laneSet")
    laneset.set("id", stable_id(proc_name, "laneSet"))
    for role in roles:
        members = lane_members.get(role["id"], [])
        lane = SubElement(laneset, "bpmn:lane")
        lane.set("id", stable_id(proc_name, f"lane/{role['id']}"))
        lane.set("name", role["name"])
        for eid in members:
            SubElement(lane, "bpmn:flowNodeRef").text = stable_id(proc_name, eid)
    # Unassigned elements go in a catch-all lane so no flowNodeRef is orphaned.
    if unassigned:
        lane = SubElement(laneset, "bpmn:lane")
        lane.set("id", stable_id(proc_name, "lane/unassigned"))
        lane.set("name", "Unassigned")
        for eid in unassigned:
            SubElement(lane, "bpmn:flowNodeRef").text = stable_id(proc_name, eid)


def _emit_scope(parent: Element, proc_name: str, elements, flows, variables, item_ids,
                roles: list = None):
    """Emit elements + flows into a process or subProcess element."""
    roles_by_id = {r["id"]: r for r in (roles or [])}
    el_by_id = {el["id"]: el for el in elements}

    for el in elements:
        el_type = el["type"]
        xml_el = SubElement(parent, f"bpmn:{el_type}")
        xml_el.set("id", stable_id(proc_name, el["id"]))
        if el_type == "textAnnotation":
            xml_el.set("textFormat", "text/plain")
            SubElement(xml_el, "bpmn:text").text = el.get("text", "")
            continue
        if el.get("name"):
            xml_el.set("name", el["name"])
        if el_type == "boundaryEvent":
            # attachedToRef is a QName in BAW exports: prefix it with tns
            xml_el.set("attachedToRef", "tns:" + stable_id(proc_name, el["attachedToRef"]))
            if not el.get("interrupting", True):
                xml_el.set("cancelActivity", "false")
        if el_type in GATEWAY_TYPES:
            xml_el.set("gatewayDirection", "Unspecified")
            default_flow = next((f for f in flows if f.get("sourceRef") == el["id"] and f.get("isDefault")), None)
            if default_flow:
                xml_el.set("default", stable_id(proc_name, default_flow["id"]))
        if el.get("documentation"):
            doc = SubElement(xml_el, "bpmn:documentation")
            doc.text = el["documentation"]
        if el.get("eventDefinition"):
            SubElement(xml_el, f"bpmn:{el['eventDefinition']}EventDefinition").set(
                "id", stable_id(proc_name, f"{el['id']}/eventdef"))
        if el.get("script") and el_type == "scriptTask":
            script = SubElement(xml_el, "bpmn:script")
            script.text = el["script"]
        # Emit <performer> on tasks that have a role — BAW uses this as the
        # primary signal for lane assignment and team/role binding on import.
        if el_type in TASK_TYPES and el.get("role") and el["role"] in roles_by_id:
            perf = SubElement(xml_el, "bpmn:performer")
            perf.set("id", stable_id(proc_name, f"{el['id']}/performer"))
            perf.set("name", roles_by_id[el["role"]]["name"])
        if el_type in TASK_TYPES and variables:
            _emit_io_spec(xml_el, proc_name, el["id"], variables, item_ids)
        if el_type == "subProcess":
            _emit_scope(xml_el, proc_name, el.get("elements", []), el.get("flows", []), [], item_ids)

    for fl in flows:
        flow_el = SubElement(parent, "bpmn:sequenceFlow")
        flow_el.set("id", stable_id(proc_name, fl["id"]))
        target = el_by_id.get(fl["targetRef"], {})
        # BAW's own exports name every flow; default to its "To <target>" style
        flow_el.set("name", fl.get("name") or f"To {target.get('name', fl['targetRef'])}")
        flow_el.set("sourceRef", stable_id(proc_name, fl["sourceRef"]))
        flow_el.set("targetRef", stable_id(proc_name, fl["targetRef"]))
        if fl.get("condition"):
            cond = SubElement(flow_el, "bpmn:conditionExpression")
            cond.set("id", stable_id(proc_name, f"{fl['id']}/condition"))
            cond.text = fl["condition"]


def _emit_io_spec(task_el: Element, proc_name: str, task_id: str, variables, item_ids):
    inputs = [v for v in variables if task_id in v.get("inputTo", [])]
    outputs = [v for v in variables if task_id in v.get("outputFrom", [])]
    if not inputs and not outputs:
        return
    io_spec = SubElement(task_el, "bpmn:ioSpecification")
    io_spec.set("id", stable_id(proc_name, f"{task_id}/iospec"))
    input_ids, output_ids = [], []
    for var in inputs:
        din_id = stable_id(proc_name, f"{task_id}/in/{var['name']}")
        din = SubElement(io_spec, "bpmn:dataInput")
        din.set("id", din_id)
        din.set("name", var["name"])
        din.set("itemSubjectRef", item_ids[var["name"]])
        input_ids.append(din_id)
    for var in outputs:
        dout_id = stable_id(proc_name, f"{task_id}/out/{var['name']}")
        dout = SubElement(io_spec, "bpmn:dataOutput")
        dout.set("id", dout_id)
        dout.set("name", var["name"])
        dout.set("itemSubjectRef", item_ids[var["name"]])
        output_ids.append(dout_id)
    inset = SubElement(io_spec, "bpmn:inputSet")
    inset.set("id", stable_id(proc_name, f"{task_id}/inputset"))
    for din_id in input_ids:
        SubElement(inset, "bpmn:dataInputRefs").text = din_id
    outset = SubElement(io_spec, "bpmn:outputSet")
    outset.set("id", stable_id(proc_name, f"{task_id}/outputset"))
    for dout_id in output_ids:
        SubElement(outset, "bpmn:dataOutputRefs").text = dout_id


# ---------------------------------------------------------------------------
# README + Mermaid generation (blueprint-parser conventions)
# ---------------------------------------------------------------------------

_MERMAID_RESERVED = {"end", "start", "graph", "subgraph", "direction", "click",
                     "style", "classdef", "class", "linkstyle", "flowchart"}


def _mid(config_id: str) -> str:
    """Config id -> mermaid-safe node id (reserved words would break the diagram)."""
    safe = re.sub(r"[^A-Za-z0-9_]", "_", config_id)
    return f"n_{safe}" if safe.lower() in _MERMAID_RESERVED else safe


def _mlabel(text: str) -> str:
    return '"' + (text or "").replace('"', "'") + '"'


def _mermaid_node(el: dict) -> str:
    """Render one element in the blueprint-parser shape vocabulary:
    ([events]) [tasks] {gateways} [[service tasks]]."""
    nid, name = _mid(el["id"]), el.get("name", el["id"])
    t = el["type"]
    if t in ("startEvent", "endEvent", "boundaryEvent", "intermediateCatchEvent", "intermediateThrowEvent"):
        return f"    {nid}([{_mlabel(name)}])"
    if t in GATEWAY_TYPES:
        return f"    {nid}{{{_mlabel(name)}}}"
    if t in ("serviceTask", "businessRuleTask"):
        return f"    {nid}[[{_mlabel(name)}]]"
    return f"    {nid}[{_mlabel(name)}]"


def _mermaid_scope(lines, elements, flows):
    for el in elements:
        if el["type"] in ANNOTATION_TYPES:
            continue
        if el["type"] == "subProcess":
            lines.append(f"    subgraph {_mid(el['id'])}[{_mlabel(el.get('name', el['id']))}]")
            _mermaid_scope(lines, el.get("elements", []), el.get("flows", []))
            lines.append("    end")
        else:
            lines.append(_mermaid_node(el))
    for el in elements:
        if el.get("type") == "boundaryEvent":
            lines.append(f"    {_mid(el['attachedToRef'])} -.-> {_mid(el['id'])}")
    for fl in flows:
        label = fl.get("name", "")
        if fl.get("isDefault"):
            label = (label + " (default)").strip()
        arrow = f"-->|{_mlabel(label)}|" if label else "-->"
        lines.append(f"    {_mid(fl['sourceRef'])} {arrow} {_mid(fl['targetRef'])}")


def _role_name(element: dict, roles_by_id: dict) -> str:
    """Resolve the 'Performed by' label for an element.

    Priority:
      1. Named role via element's 'role' field → look up in roles_by_id
      2. Inferred from element type (serviceTask/scriptTask/businessRuleTask → System)
      3. Fallback: "User/team (assign in Process Designer)"
    """
    role_id = element.get("role")
    if role_id and role_id in roles_by_id:
        return roles_by_id[role_id]["name"]
    el_type = element.get("type", "")
    if el_type in ("serviceTask", "businessRuleTask", "scriptTask"):
        return "System"
    return "User/team (assign in Process Designer)"


def build_readme(config: dict, bpmn_name: str, xsd_name: str, zip_name: str) -> str:
    """One README.md per generated process: a Mermaid flowchart in the blueprint
    parser's style plus the documentation that mode captures (steps and owners,
    decision logic, data touched, exception paths, import guidance)."""
    p = config["process"]
    elements = config.get("elements", [])
    flows = config.get("flows", [])
    variables = config.get("variables", [])
    bos = config.get("businessObjects", [])
    roles = config.get("roles", [])
    roles_by_id = {r["id"]: r for r in roles}
    el_by_id = {e["id"]: e for e in elements}

    def walk(els):
        for e in els:
            yield e
            if e.get("type") == "subProcess":
                yield from walk(e.get("elements", []))

    all_els = list(walk(elements))
    service_tasks = [e for e in all_els if e.get("type") in ("serviceTask", "businessRuleTask")]
    boundary_events = [e for e in all_els if e.get("type") == "boundaryEvent"]
    gateways = [e for e in elements if e.get("type") in GATEWAY_TYPES]
    notes = [e for e in all_els if e.get("type") in ANNOTATION_TYPES]

    md = [f"# {p['name']}", ""]
    if p.get("description"):
        md += [p["description"], ""]
    md += [f"Generated by the generate-baw-bpmn skill. Import **`{zip_name}`** into IBM BAW "
           f"(Workflow Center > Import Process App, or Process Designer > File > Import).", ""]

    md += ["## Process diagram", "", "```mermaid", "flowchart TD"]
    lines = []
    _mermaid_scope(lines, elements, flows)
    md += lines + ["```", ""]

    # Roles table — equivalent to swimlane overview, rendered from the roles section
    if roles:
        md += ["## Roles", "",
               "| Role | Type | Steps |",
               "|---|---|---|"]
        for role in roles:
            role_steps = [e.get("name", e["id"]) for e in all_els
                          if e.get("role") == role["id"] and e["type"] in
                          ("userTask", "serviceTask", "businessRuleTask", "scriptTask",
                           "manualTask", "task", "subProcess")]
            rtype = role.get("type", "human").capitalize()
            md.append(f"| {role['name']} | {rtype} | {', '.join(role_steps) or '—'} |")
        md += ["",
               "> Assign teams to each human step in Process Designer after import.", ""]

    md += ["## Steps", "", "| Step | Type | Performed by | Notes |", "|---|---|---|---|"]
    kind = {"userTask": "Human step", "serviceTask": "Automated (service flow)",
            "businessRuleTask": "Decision (service flow)", "scriptTask": "Script (JavaScript)",
            "manualTask": "Manual (offline)", "task": "Activity", "subProcess": "Subprocess"}
    for e in all_els:
        if e["type"] in kind:
            who = _role_name(e, roles_by_id)
            md.append(f"| {e.get('name', e['id'])} | {kind[e['type']]} | {who} | {e.get('documentation', '')} |")
    md.append("")

    if gateways:
        md += ["## Decision logic", ""]
        for gw in gateways:
            md.append(f"- **{gw.get('name', gw['id'])}** ({gw['type']}):")
            for fl in flows:
                if fl.get("sourceRef") == gw["id"]:
                    target = el_by_id.get(fl["targetRef"], {}).get("name", fl["targetRef"])
                    cond = f" — `{fl['condition']}`" if fl.get("condition") else ""
                    dflt = " *(default path)*" if fl.get("isDefault") else ""
                    md.append(f"  - {fl.get('name') or 'to ' + target} -> {target}{cond}{dflt}")
        md += ["", "Conditions are starting points; finalize them in Process Designer after import.", ""]

    if service_tasks:
        md += ["## Service flows BAW generates on import", ""]
        for st in service_tasks:
            md.append(f"- **{st.get('name', st['id'])}**" + (f" — {st['documentation']}" if st.get("documentation") else ""))
        md.append("")

    if boundary_events:
        md += ["## Exception and escalation paths", ""]
        for be in boundary_events:
            attached = el_by_id.get(be.get("attachedToRef"), {}).get("name", be.get("attachedToRef"))
            interrupting = "interrupting" if be.get("interrupting", True) else "non-interrupting"
            md.append(f"- **{be.get('name', be['id'])}** — {be.get('eventDefinition')} event on *{attached}* ({interrupting})."
                      + (f" {be['documentation']}" if be.get("documentation") else ""))
        md.append("")

    if variables or bos:
        md += ["## Data", ""]
    if variables:
        md += ["| Variable | Type | Produced by | Used by |", "|---|---|---|---|"]
        for v in variables:
            produced = ", ".join(el_by_id.get(i, {}).get("name", i) for i in v.get("outputFrom", [])) or "-"
            used = ", ".join(el_by_id.get(i, {}).get("name", i) for i in v.get("inputTo", [])) or "-"
            md.append(f"| {v['name']} | {v.get('type', 'xsd:anyType')} | {produced} | {used} |")
        md.append("")
    if bos:
        md += [f"Business objects (defined in `{xsd_name}`, imported as BAW business objects):", ""]
        for bo in bos:
            fields = ", ".join(f"{f['name']}: {f.get('type', 'String')}{'[]' if f.get('list') else ''}"
                               for f in bo.get("fields", []))
            md.append(f"- **{bo['name']}**" + (f" — {bo['description']}" if bo.get("description") else "") + f" ({fields})")
        md.append("")

    if notes:
        md += ["## Notes", ""] + [f"- {n.get('text', '')}" for n in notes] + [""]

    md += ["## Files", "",
           f"- `{bpmn_name}` — BPMN 2.0 XML in BAW's export dialect."]
    if xsd_name:
        md.append(f"- `{xsd_name}` — business object schema (must stay in the zip).")
    md += [f"- `{zip_name}` — the archive to import.",
           "",
           "## After importing", "",
           "1. Complete each generated service flow's implementation.",
           "2. Finalize gateway conditions against real variables.",
           "3. Customize the generated coaches for human steps and assign teams.",
           "4. Set timer durations on any timer events, initialize variables, adjust layout, and run BAW validation.",
           ""]
    return "\n".join(md)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    opts = {a for a in argv[1:] if a.startswith("--")}
    if len(args) < 1 or (len(args) < 2 and "--validate-only" not in opts):
        print(__doc__)
        return 2

    config_path = Path(args[0])
    try:
        config = load_config(config_path)
    except (ConfigError, OSError) as e:
        print(f"ERROR: {e}")
        return 1

    errors, warnings = validate(config)
    for w in warnings:
        print(f"WARNING: {w}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        print(f"\n{len(errors)} error(s). Nothing was generated - fix the config and rerun.")
        return 1
    print("Config is valid.")
    if "--validate-only" in opts:
        return 0

    output_path = Path(args[1])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    xsd_path = None
    if config.get("businessObjects"):
        xsd_path = output_path.with_suffix(".xsd")
        xsd_text = build_xsd(config)
        minidom.parseString(xsd_text.encode("utf-8"))
        xsd_path.write_text(xsd_text, encoding="utf-8")
        print(f"Wrote {xsd_path} ({len(config['businessObjects'])} business object(s))")

    xml_text = build_xml(config, xsd_filename=xsd_path.name if xsd_path else None)

    # Round-trip parse as a final well-formedness gate before writing.
    minidom.parseString(xml_text.encode("utf-8"))

    output_path.write_text(xml_text, encoding="utf-8")
    print(f"Wrote {output_path}")

    if "--no-zip" not in opts:
        zip_path = output_path.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(output_path, arcname=output_path.name)
            if xsd_path:
                zf.write(xsd_path, arcname=xsd_path.name)
        print(f"Wrote {zip_path} (import this archive into BAW)")

    if "--no-readme" not in opts:
        readme_path = output_path.parent / "README.md"
        readme_path.write_text(
            build_readme(config, output_path.name,
                         xsd_path.name if xsd_path else "",
                         output_path.with_suffix(".zip").name),
            encoding="utf-8")
        print(f"Wrote {readme_path} (Mermaid diagram + process documentation)")

    n_elements = len(config.get("elements", []))
    n_flows = len(config.get("flows", []))
    n_service = sum(1 for e in config.get("elements", []) if e.get("type") == "serviceTask")
    print(f"Process '{config['process']['name']}': {n_elements} elements, {n_flows} flows.")
    if n_service:
        print(f"{n_service} serviceTask(s) -> BAW will generate one service flow per serviceTask on import, "
              f"named after the task.")
    if config.get("businessObjects"):
        print(f"Business objects ({', '.join(bo['name'] for bo in config['businessObjects'])}) are defined "
              f"in the sidecar .xsd; keep it in the zip so BAW imports them as business objects.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
