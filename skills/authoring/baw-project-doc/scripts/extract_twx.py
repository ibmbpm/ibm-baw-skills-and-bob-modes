#!/usr/bin/env python3
"""
extract_twx.py  —  part of the baw-project-doc skill.

Extracts and parses a BAW TWX export file offline (no server required).
Produces a structured JSON summary of all artifacts: processes (BPDs and
service flows), business objects, coach views, REST/SOAP/web-service
definitions, environment variables, and managed assets.

Supports both TWX layout variants:
  - Modern flat layout: objects/<prefix>.<uuid>.xml  (type determined by XML root tag)
  - Legacy subfolder layout: objects/process/*.xml, objects/service/*.xml, etc.

Usage:
    python extract_twx.py <path/to/app.twx> [--out-dir <dir>]

Output:
    Writes <AppName>.artifacts.json to the output directory (stdout: JSON path).

Stdlib only — no pip dependencies.
"""

import json
import os
import re
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# processType integer -> human-readable service type
# ---------------------------------------------------------------------------
_PROCESS_TYPE_MAP = {
    "0":  "BPD",
    "1":  "Integration Service",
    "2":  "Ajax Service",
    "3":  "General System Service",
    "4":  "Heritage Human Service",
    "5":  "Decision Service",
    "6":  "External Implementation",
    "7":  "Event Sub-Process",
    "8":  "Case Activity",
    "9":  "Case Activity",
    "10": "Client-Side Human Service",
    "11": "Client-Side Human Service",
    "12": "Service Flow (Ajax)",
    "13": "Service Flow",
    "14": "REST Service Flow",
    "15": "External Service",
}

# BPMN declaredType -> readable step type
_STEP_TYPE_MAP = {
    "startEvent":               "Start Event",
    "endEvent":                 "End Event",
    "userTask":                 "Human Task",
    "serviceTask":              "Service Task",
    "scriptTask":               "Script Task",
    "callActivity":             "Sub-Process / Call Activity",
    "subProcess":               "Embedded Sub-Process",
    "exclusiveGateway":         "Exclusive Gateway",
    "inclusiveGateway":         "Inclusive Gateway",
    "parallelGateway":          "Parallel Gateway",
    "eventBasedGateway":        "Event-Based Gateway",
    "intermediateCatchEvent":   "Intermediate Catch Event",
    "intermediateThrowEvent":   "Intermediate Throw Event",
    "boundaryEvent":            "Boundary Event",
    "receiveTask":              "Receive Task",
    "sendTask":                 "Send Task",
    "manualTask":               "Manual Task",
    "businessRuleTask":         "Business Rule Task",
    "sequenceFlow":             "Sequence Flow",
    "dataObject":               "Data Object",
    "dataObjectReference":      "Data Object Reference",
    "textAnnotation":           "Annotation",
    "association":              "Association",
}

# interactionPattern integer -> string
_INTERACTION_MAP = {
    "1": "REQUEST_RESPONSE_SYNC",
    "2": "REQUEST_ONLY",
    "3": "FIRE_AND_FORGET",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tag(element) -> str:
    t = element.tag
    return t.split("}")[-1] if "}" in t else t


def _child_text(element, *tags) -> str:
    """Return stripped text of the first matching child tag name."""
    for t in tags:
        child = element.find(t)
        if child is not None and child.text:
            return child.text.strip()
    return ""


def _is_null(element, tag: str) -> bool:
    child = element.find(tag)
    if child is None:
        return True
    return child.get("isNull", "false").lower() == "true"


def _parse_json_data(element) -> dict:
    """Extract and parse the <jsonData> child of an artifact element."""
    jd_el = element.find("jsonData")
    if jd_el is None or not jd_el.text or jd_el.get("isNull", "false").lower() == "true":
        return {}
    try:
        return json.loads(jd_el.text)
    except (json.JSONDecodeError, ValueError):
        return {}


# ---------------------------------------------------------------------------
# META-INF / package.xml  (authoritative source for app metadata)
# ---------------------------------------------------------------------------

def _parse_package_xml(tmp_path: Path) -> dict:
    """
    Read META-INF/package.xml for app name, acronym, snapshot label,
    branch name, and toolkit dependencies.
    Falls back to MANIFEST.MF for legacy TWX exports.
    """
    result = {
        "appName": "",
        "acronym": "",
        "snapshotName": "",
        "branchName": "",
        "isToolkit": False,
        "buildVersion": "",
        "dependencies": [],
        "objectIndex": {},   # id -> {name, type}
    }

    pkg_path = tmp_path / "META-INF" / "package.xml"
    if pkg_path.exists():
        try:
            root = ET.parse(pkg_path).getroot()
        except ET.ParseError:
            pass
        else:
            build_ver = root.get("buildVersion", "")
            if build_ver:
                result["buildVersion"] = build_ver

            # Walk top-level sections: <target>, <dependencies>, <objects>
            # IMPORTANT: iterate section-by-section so toolkit <project> elements
            # inside <dependencies> are not mistaken for the app's own identity.
            for section in root:
                section_tag = _tag(section)

                if section_tag == "target":
                    # App identity — only direct children of <target>
                    for el in section:
                        local = _tag(el)
                        if local == "project":
                            result["appName"]   = el.get("name", result["appName"])
                            result["acronym"]   = el.get("shortName", "")
                            result["isToolkit"] = el.get("isToolkit", "false").lower() == "true"
                        elif local == "branch":
                            result["branchName"] = el.get("name", "")
                        elif local == "snapshot":
                            result["snapshotName"] = el.get("name", "")

                elif section_tag == "dependencies":
                    for dep in section:
                        if _tag(dep) != "dependency":
                            continue
                        dep_proj = dep_snap = dep_branch = ""
                        for child in dep:
                            ct = _tag(child)
                            if ct == "project":
                                dep_proj = child.get("name", "")
                            elif ct == "snapshot":
                                dep_snap = child.get("name", "")
                            elif ct == "branch":
                                dep_branch = child.get("name", "")
                        if dep_proj:
                            result["dependencies"].append({
                                "name": dep_proj,
                                "snapshot": dep_snap,
                                "branch": dep_branch,
                            })

                elif section_tag == "objects":
                    for obj in section:
                        if _tag(obj) != "object":
                            continue
                        oid   = obj.get("id", "")
                        otype = obj.get("type", "")
                        oname = obj.get("name", "")
                        if oid:
                            result["objectIndex"][oid] = {"name": oname, "type": otype}
        return result

    # Fallback: MANIFEST.MF
    manifest_path = tmp_path / "META-INF" / "MANIFEST.MF"
    if manifest_path.exists():
        for line in manifest_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if ":" in line:
                key, _, val = line.partition(":")
                key, val = key.strip(), val.strip()
                if key == "ProcessApp-Name":
                    result["appName"] = val
                elif key == "Snapshot-Name":
                    result["snapshotName"] = val

    return result


# ---------------------------------------------------------------------------
# Helpers for jsonData-based process/service parsing
# ---------------------------------------------------------------------------

def _extract_lanes(root_elem: dict) -> list:
    lanes = []
    for lane_set in root_elem.get("laneSet", []):
        for lane in lane_set.get("lane", []):
            lane_name = lane.get("name", "")
            other = lane.get("otherAttributes", {})
            is_system = other.get(
                "{http://www.ibm.com/xmlns/prod/bpm/bpmn/ext/process/wle}isSystemLane", "false"
            ).lower() == "true"
            if lane_name:
                lanes.append({
                    "name": lane_name,
                    "isSystem": is_system,
                    "nodeRefs": lane.get("flowNodeRef", []),
                })
    return lanes


def _build_node_to_lane(lanes: list) -> dict:
    """Map each node id -> lane name for step annotation."""
    mapping = {}
    for lane in lanes:
        for ref in lane.get("nodeRefs", []):
            mapping[ref] = lane["name"]
    return mapping


def _extract_flow_elements(root_elem: dict, node_to_lane: dict) -> tuple:
    """
    Returns (steps, gateways, sequence_flows, boundary_events, timers).
    steps         — all tasks / events (not sequence flows)
    gateways      — exclusive/parallel/inclusive gateways
    sequence_flows — edges with source, target, optional condition name
    boundary_events — timer/error/escalation boundaries
    timers        — timer entries extracted from boundary events
    """
    steps = []
    gateways = []
    sequence_flows = []
    boundary_events = []

    for fe in root_elem.get("flowElement", []):
        dtype = fe.get("declaredType", "")
        fid   = fe.get("id", "")
        fname = fe.get("name", "") or ""
        lane  = node_to_lane.get(fid, "")

        if dtype == "sequenceFlow":
            sequence_flows.append({
                "id":       fid,
                "name":     fname,
                "source":   fe.get("sourceRef", ""),
                "target":   fe.get("targetRef", ""),
            })
        elif "Gateway" in dtype:
            gateways.append({
                "id":       fid,
                "name":     fname,
                "type":     _STEP_TYPE_MAP.get(dtype, dtype),
                "outgoing": fe.get("outgoing", []),
            })
            steps.append({
                "id":          fid,
                "name":        fname,
                "type":        _STEP_TYPE_MAP.get(dtype, dtype),
                "lane":        lane,
                "description": _extract_documentation(fe),
                "scriptFormat": fe.get("scriptFormat", ""),
                "outgoing":    fe.get("outgoing", []),
                "incoming":    fe.get("incoming", []),
            })
        elif dtype == "boundaryEvent":
            bev = {
                "id":             fid,
                "name":           fname,
                "attachedTo":     fe.get("attachedToRef", fe.get("cancelActivity", True) and fe.get("attachedToRef", "")),
                "isInterrupting": not fe.get("cancelActivity", True) is False,
                "eventDefs":      [
                    ed.get("declaredType", "") if isinstance(ed, dict) else (
                        _tag(ed) if hasattr(ed, "tag") else str(ed)
                    )
                    for ed in fe.get("eventDefinition", [])
                ],
            }
            boundary_events.append(bev)
            steps.append({
                "id":          fid,
                "name":        fname,
                "type":        "Boundary Event",
                "lane":        lane,
                "description": _extract_documentation(fe),
                "scriptFormat": "",
                "outgoing":    fe.get("outgoing", []),
                "incoming":    [],
            })
        else:
            steps.append({
                "id":          fid,
                "name":        fname,
                "type":        _STEP_TYPE_MAP.get(dtype, dtype),
                "lane":        lane,
                "description": _extract_documentation(fe),
                "scriptFormat": fe.get("scriptFormat", ""),
                "outgoing":    fe.get("outgoing", []),
                "incoming":    fe.get("incoming", []),
            })

    # Derive timers: boundary events that reference a timer
    timers = []
    for bev in boundary_events:
        if any("timer" in d.lower() for d in bev.get("eventDefs", [])):
            timers.append({
                "name":       bev["name"],
                "attachedTo": bev["attachedTo"],
                "interrupting": bev["isInterrupting"],
            })

    return steps, gateways, sequence_flows, boundary_events, timers


def _extract_documentation(fe: dict) -> str:
    import re as _re
    for doc in fe.get("documentation", []):
        if isinstance(doc, dict):
            t = doc.get("text", "") or doc.get("content", "")
            if isinstance(t, list):
                # content is sometimes a list of HTML strings — flatten and strip tags
                t = " ".join(str(s) for s in t if s)
            if t and isinstance(t, str):
                # Strip HTML tags for plain text
                t = _re.sub(r"<[^>]+>", " ", t)
                t = _re.sub(r"\s+", " ", t).strip()
                return t
        elif isinstance(doc, str) and doc.strip():
            return doc.strip()
    return ""


def _extract_variables(root_elem: dict, io_spec: dict) -> list:
    """
    Extract process/service variables from:
      1. root_elem['property']  (BPD private variables)
      2. io_spec['dataInput'] / io_spec['dataOutput']  (interface parameters)
      3. root_elem['dataObject']  (data objects, older BPD format)
    """
    variables = []
    seen = set()

    def _resolve_type(item_ref: str) -> str:
        """Strip the 'itm.NN.' prefix to get a readable type hint."""
        if not item_ref:
            return ""
        # Format: itm.<num>.<uuid> — strip prefix to surface the UUID for now
        m = re.match(r"^itm\.\d+\.", item_ref)
        return item_ref[m.end():] if m else item_ref

    # dataInput → input parameters
    for di in io_spec.get("dataInput", []):
        var_id   = di.get("id", "")
        var_name = di.get("name", "")
        if not var_name or var_id in seen:
            continue
        seen.add(var_id)
        variables.append({
            "name":        var_name,
            "type":        _resolve_type(di.get("itemSubjectRef", "")),
            "isList":      di.get("isCollection", False),
            "isInput":     True,
            "isOutput":    False,
            "description": "",
        })

    # dataOutput → output parameters
    for do_ in io_spec.get("dataOutput", []):
        var_id   = do_.get("id", "")
        var_name = do_.get("name", "")
        if not var_name or var_id in seen:
            continue
        seen.add(var_id)
        variables.append({
            "name":        var_name,
            "type":        _resolve_type(do_.get("itemSubjectRef", "")),
            "isList":      do_.get("isCollection", False),
            "isInput":     False,
            "isOutput":    True,
            "description": "",
        })

    # property list (BPD private variables, heritage format)
    for prop in root_elem.get("property", []):
        if not isinstance(prop, dict):
            continue
        var_name = prop.get("name", "")
        var_id   = prop.get("id", var_name)
        if not var_name or var_id in seen:
            continue
        seen.add(var_id)
        variables.append({
            "name":        var_name,
            "type":        prop.get("itemSubjectRef", prop.get("type", "")),
            "isList":      prop.get("isCollection", False),
            "isInput":     prop.get("isInput", False),
            "isOutput":    prop.get("isOutput", False),
            "description": prop.get("documentation", ""),
        })

    # dataObject list (older BPD format)
    for do_ in root_elem.get("dataObject", []):
        if not isinstance(do_, dict):
            continue
        var_name = do_.get("name", "")
        var_id   = do_.get("id", var_name)
        if not var_name or var_id in seen:
            continue
        seen.add(var_id)
        variables.append({
            "name":        var_name,
            "type":        _resolve_type(do_.get("itemSubjectRef", "")),
            "isList":      do_.get("isCollection", False),
            "isInput":     False,
            "isOutput":    False,
            "description": "",
        })

    return variables


def _extract_endpoints_from_json(root_elem: dict) -> list:
    """
    Walk the entire flowElement list looking for integration references:
    REST URLs, WSDL references, SQL data sources embedded in extension attributes.
    """
    endpoints = []

    def _walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                kl = k.lower()
                if isinstance(v, str) and v.strip():
                    if kl in ("url", "endpoint", "wsdllocation", "datasource",
                               "resturl", "httpurl", "serviceurl", "targetnamespace"):
                        endpoints.append({"kind": k, "value": v.strip()})
                    elif kl == "implementation" and (v.startswith("http") or v.startswith("/")):
                        endpoints.append({"kind": "implementation", "value": v.strip()})
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(root_elem)
    return endpoints


# ---------------------------------------------------------------------------
# Artifact parsers
# ---------------------------------------------------------------------------

def _parse_process_xml(art_el: ET.Element, object_index: dict) -> dict:
    """
    Parse a <process>, <service>, or legacy <bpd> artifact element.
    Both BPDs and service flows use the same <process> root tag in modern TWX;
    processType distinguishes them.  Legacy <bpd> elements always represent BPDs
    and use <type> instead of <processType>.
    """
    name        = art_el.get("name", "")
    art_id      = art_el.get("id", "")
    is_legacy_bpd = _tag(art_el) == "bpd"
    # <bpd> (legacy) is always a BPD — its <type> child is an internal field, not processType.
    # <process> (modern) uses <processType> to distinguish BPDs from service flows.
    proc_type_n = "" if is_legacy_bpd else _child_text(art_el, "processType")
    description = _child_text(art_el, "description")
    is_ajax     = _child_text(art_el, "isAjaxExposed").lower() == "true"
    is_secured  = _child_text(art_el, "isSecured").lower() == "true"

    service_type = _PROCESS_TYPE_MAP.get(proc_type_n, f"Service Flow (type {proc_type_n})")

    jd = _parse_json_data(art_el)
    root_elems = jd.get("rootElement", [])
    root_elem  = root_elems[0] if root_elems else {}

    # If jsonData is present prefer name from there (more reliable)
    if root_elem.get("name"):
        name = root_elem["name"]
    if not description and root_elem.get("documentation"):
        for doc in root_elem["documentation"]:
            if isinstance(doc, dict) and doc.get("text"):
                description = doc["text"].strip()
                break

    io_spec = root_elem.get("ioSpecification", {})
    lanes   = _extract_lanes(root_elem)
    n2l     = _build_node_to_lane(lanes)
    steps, gateways, seq_flows, boundary_events, timers = _extract_flow_elements(root_elem, n2l)
    variables  = _extract_variables(root_elem, io_spec)
    endpoints  = _extract_endpoints_from_json(root_elem)

    # Determine if this is a BPD or a service flow.
    # Legacy <bpd> tag is always a BPD.  For <process>, check executionMode and processType.
    exec_mode = root_elem.get("otherAttributes", {}).get(
        "{http://www.ibm.com/xmlns/prod/bpm/bpmn/ext/process}executionMode", "")

    is_bpd = is_legacy_bpd or proc_type_n == "0" or (
        exec_mode == "" and proc_type_n not in _PROCESS_TYPE_MAP
    )
    if is_legacy_bpd:
        service_type = "BPD"
        exec_mode = exec_mode or "longRunning"

    return {
        "id":            art_id,
        "name":          name,
        "serviceType":   service_type,
        "isBPD":         is_bpd,
        "executionMode": exec_mode or ("bpd" if is_bpd else "microflow"),
        "description":   description,
        "isAjaxExposed": is_ajax,
        "isSecured":     is_secured,
        "lanes":         lanes,
        "steps":         [s for s in steps if s["type"] != "Sequence Flow"],
        "sequenceFlows": seq_flows,
        "gateways":      gateways,
        "timers":        timers,
        "boundaryEvents": boundary_events,
        "variables":     variables,
        "endpoints":     endpoints,
    }


def _parse_rest_service_xml(art_el: ET.Element, object_index: dict) -> dict:
    """Parse a <restService> artifact — a REST API exposure definition."""
    name        = art_el.get("name", "")
    description = _child_text(art_el, "description")
    jd          = _parse_json_data(art_el)

    # Resolve operation → implementation name
    ops = []
    for op in jd.get("operations", []):
        impl_id = op.get("implementation", "")
        impl_info = object_index.get(impl_id, {})
        pattern_raw = op.get("interactionPattern", "1")
        ops.append({
            "name":               op.get("name", ""),
            "interactionPattern": _INTERACTION_MAP.get(str(pattern_raw), pattern_raw),
            "implementationId":   impl_id,
            "implementationName": impl_info.get("name", impl_id),
        })

    # Parse openAPI URL template (extract base URL)
    open_api_url = jd.get("openAPIDefinitionURLTemplate", "")
    # Sanitise snapshot placeholder tokens for readability
    clean_url = re.sub(r"\{SNAPSHOT_START:[^}]*:SNAPSHOT_END\}", "{SNAPSHOT}", open_api_url)
    clean_url = re.sub(r"\{NAME_START:([^}]*):NAME_END\}", r"\1", clean_url)

    return {
        "name":        name,
        "description": description,
        "operations":  ops,
        "openAPIURL":  clean_url,
    }


def _parse_web_service_xml(art_el: ET.Element, object_index: dict) -> dict:
    """Parse a <webService> or <soapService> artifact."""
    name        = art_el.get("name", "")
    description = _child_text(art_el, "description")
    wsdl_url    = _child_text(art_el, "wsdlUrl", "wsdlLocation", "wsdl")
    jd          = _parse_json_data(art_el)

    operations = []
    for op in jd.get("operations", jd.get("portTypeOperation", [])):
        if isinstance(op, dict):
            operations.append({
                "name":         op.get("name", ""),
                "soapAction":   op.get("soapAction", ""),
                "inputMessage": op.get("inputMessage", ""),
                "outputMessage": op.get("outputMessage", ""),
            })

    return {
        "name":        name,
        "description": description,
        "wsdlUrl":     wsdl_url or jd.get("wsdlUrl", ""),
        "operations":  operations,
    }


def _parse_business_object_xml(art_el: ET.Element) -> list:
    """
    Parse a <businessObject> or <businessObjectType> artifact.
    One file can define multiple BO types.
    """
    objects = []
    jd = _parse_json_data(art_el)

    # Modern format: jsonData contains type definitions
    if jd:
        for bo in jd.get("businessObjectType", jd.get("objectType", [])):
            if not isinstance(bo, dict):
                continue
            fields = []
            for f in bo.get("parameter", bo.get("field", bo.get("property", []))):
                if not isinstance(f, dict):
                    continue
                fields.append({
                    "name":        f.get("name", ""),
                    "type":        f.get("type", f.get("itemSubjectRef", "")),
                    "isList":      f.get("isCollection", f.get("isList", False)),
                    "isRequired":  f.get("required", f.get("isRequired", False)),
                    "description": f.get("documentation", f.get("description", "")),
                })
            objects.append({
                "name":        bo.get("name", art_el.get("name", "")),
                "description": bo.get("description", bo.get("documentation", "")),
                "parent":      bo.get("parentType", ""),
                "fields":      fields,
            })
        if objects:
            return objects

    # Fallback: parse XML children directly (legacy layout)
    name    = art_el.get("name", "")
    desc    = art_el.get("description", "")
    parent  = art_el.get("parentType", "")
    fields  = []
    for child in art_el:
        ct = _tag(child)
        if ct in ("parameter", "field", "property"):
            fields.append({
                "name":        child.get("name", ""),
                "type":        child.get("type", child.get("itemSubjectRef", "")),
                "isList":      child.get("isCollection", child.get("isList", "false")).lower() == "true",
                "isRequired":  child.get("required", child.get("isRequired", "false")).lower() == "true",
                "description": child.get("description", child.get("documentation", "")),
            })
        elif ct == "businessObjectType":
            # Nested BO definition
            n = child.get("name", "")
            if n:
                sub_fields = []
                for gf in child:
                    gt = _tag(gf)
                    if gt in ("parameter", "field", "property"):
                        sub_fields.append({
                            "name":        gf.get("name", ""),
                            "type":        gf.get("type", gf.get("itemSubjectRef", "")),
                            "isList":      gf.get("isCollection", gf.get("isList", "false")).lower() == "true",
                            "isRequired":  gf.get("required", gf.get("isRequired", "false")).lower() == "true",
                            "description": gf.get("description", ""),
                        })
                objects.append({"name": n, "description": child.get("description", ""),
                                 "parent": child.get("parentType", ""), "fields": sub_fields})

    if name:
        objects.append({"name": name, "description": desc, "parent": parent, "fields": fields})

    return objects


def _parse_coach_view_xml(art_el: ET.Element) -> dict:
    """Parse a <coachView> artifact."""
    name = art_el.get("name", "")
    jd   = _parse_json_data(art_el)

    config_options = []
    event_handlers = []
    bound_types    = []

    if jd:
        for opt in jd.get("configOption", jd.get("option", [])):
            if isinstance(opt, dict):
                config_options.append({
                    "name": opt.get("name", ""),
                    "type": opt.get("type", ""),
                    "description": opt.get("description", opt.get("documentation", "")),
                })
        for eh in jd.get("eventHandler", jd.get("event", [])):
            if isinstance(eh, dict):
                event_handlers.append(eh.get("event", eh.get("name", "")))
            elif isinstance(eh, str):
                event_handlers.append(eh)
        for bnd in jd.get("binding", jd.get("boundType", [])):
            if isinstance(bnd, dict):
                bound_types.append(bnd.get("type", bnd.get("name", "")))
    else:
        # Legacy XML fallback
        for el in art_el.iter():
            lt = _tag(el)
            if lt == "configOption":
                config_options.append({"name": el.get("name", ""), "type": el.get("type", ""), "description": ""})
            elif lt == "eventHandler":
                event_handlers.append(el.get("event", el.get("name", "")))

    return {
        "name":          name,
        "description":   _child_text(art_el, "description"),
        "configOptions": config_options,
        "eventHandlers": event_handlers,
        "boundTypes":    bound_types,
    }


def _parse_env_vars_xml(art_el: ET.Element) -> list:
    """Parse an <environmentVariableSet> artifact."""
    jd   = _parse_json_data(art_el)
    vars_ = []

    if jd:
        for ev in jd.get("variable", jd.get("environmentVariable", [])):
            if isinstance(ev, dict):
                vars_.append({
                    "name":         ev.get("name", ""),
                    "type":         ev.get("type", "String"),
                    "defaultValue": ev.get("default", ev.get("value", "")),
                    "description":  ev.get("description", ""),
                })
    else:
        for child in art_el.iter():
            if _tag(child) in ("variable", "environmentVariable"):
                vars_.append({
                    "name":         child.get("name", ""),
                    "type":         child.get("type", "String"),
                    "defaultValue": child.get("default", child.get("value", "")),
                    "description":  child.get("description", ""),
                })

    return vars_


# ---------------------------------------------------------------------------
# Dispatcher — route an XML file to the right parser
# ---------------------------------------------------------------------------

# Map XML root-child tag -> bucket key
_TAG_BUCKET = {
    "process":              "processes",
    "bpd":                  "processes",   # legacy tag used by older BAW exports
    "restService":          "restServices",
    "webService":           "webServices",
    "soapService":          "webServices",
    "businessObject":       "businessObjects",
    "businessObjectType":   "businessObjects",
    "coachView":            "coachViews",
    "environmentVariableSet": "environmentVariableSets",
}

# Tags we explicitly ignore (no documentation value)
_IGNORED_TAGS = {
    "managedAsset", "projectDefaults", "template",
    "participantGroup", "exposedItemsReference",
}


def _dispatch_xml_file(xml_path: Path, object_index: dict) -> tuple:
    """
    Parse one objects/*.xml file.
    Returns (bucket_key, [parsed_artifacts]) or (None, skipped_note).
    """
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as exc:
        return None, f"{xml_path.name}: XML parse error — {exc}"

    root = tree.getroot()
    # The <teamworks> root wraps the artifact element
    art_list = list(root)
    if not art_list:
        return None, f"{xml_path.name}: empty <teamworks> element"

    art_el  = art_list[0]
    art_tag = _tag(art_el)

    if art_tag in _IGNORED_TAGS:
        return None, None  # silently skip

    bucket = _TAG_BUCKET.get(art_tag)

    if bucket == "processes":
        # For legacy <bpd> elements: skip embedded sub-BPDs (parentBpdId is set).
        # These are internal sub-processes already captured inside their parent's jsonData.
        if art_tag == "bpd":
            parent_bpd = art_el.find("parentBpdId")
            if parent_bpd is not None and parent_bpd.get("isNull", "false").lower() != "true" and parent_bpd.text and parent_bpd.text.strip():
                return None, None  # silently skip embedded sub-BPD
        parsed = _parse_process_xml(art_el, object_index)
        return bucket, [parsed]

    elif bucket == "restServices":
        parsed = _parse_rest_service_xml(art_el, object_index)
        return bucket, [parsed]

    elif bucket == "webServices":
        parsed = _parse_web_service_xml(art_el, object_index)
        return bucket, [parsed]

    elif bucket == "businessObjects":
        parsed_list = _parse_business_object_xml(art_el)
        return bucket, parsed_list

    elif bucket == "coachViews":
        parsed = _parse_coach_view_xml(art_el)
        return bucket, [parsed]

    elif bucket == "environmentVariableSets":
        evars = _parse_env_vars_xml(art_el)
        return bucket, [{"name": art_el.get("name", ""), "variables": evars}]

    else:
        # Unknown tag — record in skipped with the tag name so future runs can add support
        return None, f"{xml_path.name}: unrecognised artifact tag <{art_tag}> — skipped"


# ---------------------------------------------------------------------------
# Legacy subfolder layout support
# ---------------------------------------------------------------------------

_LEGACY_FOLDER_BUCKET = {
    "process":                "processes",
    "service":                "processes",
    "human-service":          "processes",
    "heritage-human-service": "processes",
    "business-object":        "businessObjects",
    "coach-view":             "coachViews",
}


def _collect_xml_files(objects_dir: Path, object_index: dict) -> list:
    """
    Return list of (xml_path, effective_object_index) covering both layouts.
    Modern: objects/<prefix>.<uuid>.xml  (flat)
    Legacy: objects/<folder>/<name>.xml  (subfolders)
    """
    files = []
    for entry in sorted(objects_dir.iterdir()):
        if entry.is_file() and entry.suffix == ".xml":
            # Modern flat layout
            files.append(entry)
        elif entry.is_dir() and entry.name in _LEGACY_FOLDER_BUCKET:
            # Legacy subfolder layout
            for xml_file in sorted(entry.glob("*.xml")):
                files.append(xml_file)
    return files


# ---------------------------------------------------------------------------
# Main extraction logic
# ---------------------------------------------------------------------------

def extract_twx(twx_path: Path, out_dir: Path) -> Path:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        with zipfile.ZipFile(twx_path, "r") as zf:
            zf.extractall(tmp_path)

        meta = _parse_package_xml(tmp_path)
        app_name = meta["appName"] or twx_path.stem

        artifacts = {
            "appName":              app_name,
            "acronym":              meta["acronym"],
            "snapshotName":         meta["snapshotName"],
            "branchName":           meta["branchName"],
            "isToolkit":            meta["isToolkit"],
            "buildVersion":         meta["buildVersion"],
            "sourceFile":           twx_path.name,
            "toolkitDependencies":  meta["dependencies"],
            "processes":            [],   # BPDs
            "serviceFlows":         [],   # microflows / service flows
            "restServices":         [],   # REST API exposure definitions
            "webServices":          [],   # SOAP/web service definitions
            "businessObjects":      [],
            "coachViews":           [],
            "environmentVariables": [],
            "skipped":              [],
        }

        objects_dir = tmp_path / "objects"
        if not objects_dir.exists():
            artifacts["skipped"].append("No objects/ directory found in TWX.")
            _write_output(artifacts, app_name, out_dir)
            return _write_output(artifacts, app_name, out_dir)

        xml_files = _collect_xml_files(objects_dir, meta["objectIndex"])

        for xml_path in xml_files:
            bucket, result = _dispatch_xml_file(xml_path, meta["objectIndex"])
            if bucket is None:
                if result:  # non-None means a skip note
                    artifacts["skipped"].append(result)
                continue
            for item in result:
                if item is None:
                    continue
                # Route processes: BPD vs service flow
                if bucket == "processes":
                    if item.get("isBPD"):
                        artifacts["processes"].append(item)
                    else:
                        artifacts["serviceFlows"].append(item)
                elif bucket == "environmentVariableSets":
                    artifacts["environmentVariables"].extend(
                        item.get("variables", [])
                    )
                else:
                    artifacts[bucket].append(item)

    return _write_output(artifacts, app_name, out_dir)


def _write_output(artifacts: dict, app_name: str, out_dir: Path) -> Path:
    safe_name = re.sub(r"[^\w\-]", "_", app_name)
    out_path  = out_dir / f"{safe_name}.artifacts.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifacts, indent=2), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv):
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("twx_file",  help="Path to the .twx export file")
    parser.add_argument("--out-dir", default=".", help="Output directory (default: current directory)")
    opts = parser.parse_args(argv[1:])

    twx_path = Path(opts.twx_file)
    if not twx_path.is_file():
        print(f"ERROR: file not found: {twx_path}", file=sys.stderr)
        return 1
    if twx_path.suffix.lower() != ".twx":
        print(f"WARNING: expected a .twx file, got: {twx_path.name}", file=sys.stderr)

    out_dir = Path(opts.out_dir)

    try:
        out_path = extract_twx(twx_path, out_dir)
    except (zipfile.BadZipFile, Exception) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"saved": str(out_path)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
