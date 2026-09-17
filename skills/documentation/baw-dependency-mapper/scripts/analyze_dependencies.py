#!/usr/bin/env python3
"""
analyze_dependencies.py — BAW TWX Dependency Mapper
Analyses a BAW .twx export and maps all usages of a specified variable or
Business Object type across processes, services, coaches, and BO definitions.

Usage:
    python analyze_dependencies.py <path-to.twx> <TargetName> \
        [--threshold N] [--output-dir DIR]

Requirements: Python 3.6+ standard library only.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import zipfile
from collections import defaultdict, deque
from datetime import datetime, timezone
from functools import lru_cache
from xml.etree import ElementTree as ET


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_ns(tag: str) -> str:
    """Remove XML namespace from a tag string."""
    return tag.split("}")[-1] if "}" in tag else tag


@lru_cache(maxsize=256)
def _make_pattern(target: str) -> re.Pattern:
    """Compile and cache a whole-word, case-insensitive pattern for target."""
    return re.compile(r"\b" + re.escape(target) + r"\b", re.IGNORECASE)


def _text_contains(text: str, target: str) -> bool:
    """Case-insensitive whole-word search for target inside text."""
    if not text:
        return False
    return bool(_make_pattern(target).search(text))


def _collect_xml_files(twx_path: str):
    """
    Return list of (zip_path, parsed_ElementTree) for every XML file inside
    the TWX. Reads all entries while the ZipFile is open to avoid the
    generator-leaks-handle problem.
    """
    results = []
    with zipfile.ZipFile(twx_path, "r") as zf:
        for entry in zf.namelist():
            if not entry.endswith(".xml"):
                continue
            try:
                with zf.open(entry) as fh:
                    content = fh.read()
                tree = ET.ElementTree(ET.fromstring(content))
                results.append((entry, tree))
            except ET.ParseError:
                # Skip unparseable files silently
                continue
    return results


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

class DependencyAnalyser:
    def __init__(self, twx_path: str, target: str, threshold: int = 3):
        self.twx_path = twx_path
        # Accept both qualified (tw.local.Foo) and bare (Foo) names
        bare = target.split(".")[-1]
        self.target = bare
        self.target_qualified = target
        self.threshold = threshold

        # Results
        self.declarations:      list = []   # {artefact, type, file, detail}
        self.reads:             list = []
        self.writes:            list = []
        self.service_inputs:    list = []
        self.service_outputs:   list = []
        self.coach_bindings:    list = []

        # BO type graph for circular detection: {type_name: [referenced_type_names]}
        self.bo_graph: dict = defaultdict(list)
        # All BO definitions: {name: [field_names]}
        self.bo_defs: dict = {}

        # Per-artefact variable tracking for advanced checks
        # {artefact_name: {"vars": {var_name: {"type", "file", "atype"}},
        #                  "reads": set(), "writes": set()}}
        self._artefact_vars: dict = defaultdict(lambda: {
            "vars": {}, "reads": set(), "writes": set(), "file": ""
        })
        # Service activity tracking for missing-output-mapping detection
        # {artefact_name: {activity_name: {"has_input_for_target": bool,
        #                                   "has_output_for_target": bool, "file": str}}}
        self._service_activities: dict = defaultdict(dict)

        # Flow graph for read-before-write detection
        # {process_name: {"nodes": {node_id: node_name},
        #                 "edges": [(from_id, to_id)],
        #                 "writes": {node_id},   # activities that write target
        #                 "reads":  {node_id},   # activities that read target
        #                 "file": str,
        #                 "has_parallel": bool,  # parallel gateways present (lower confidence)
        #                 "has_loop": bool}}      # back-edges detected (lower confidence)
        self._flow_graphs: dict = defaultdict(lambda: {
            "nodes": {}, "edges": [], "writes": set(), "reads": set(),
            "file": "", "has_parallel": False, "has_loop": False,
        })
        # Current process/service being visited, tracked for flow-graph population
        self._current_process: str = ""

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self):
        for zip_path, tree in _collect_xml_files(self.twx_path):
            root = tree.getroot()
            if _strip_ns(root.tag) == "teamworks":
                # Real BAW TWX: artefacts are children of <teamworks>, data in <jsonData> JSON
                self._analyse_teamworks(root, zip_path)
        # Second pass: resolve any raw itemSubjectRef strings left in declaration details
        # (can happen when a variable is parsed before its twClass definition)
        self._resolve_pending_type_refs()

    def _resolve_pending_type_refs(self):
        """Replace raw itemSubjectRef strings in declaration details with resolved BO names."""
        id_map = getattr(self, "_tw_class_id_to_name", {})
        if not id_map:
            return
        for record in self.declarations:
            detail = record.get("detail", "")
            # Match pattern: var 'X' : itm.12.<uuid> or var 'X' : /12.<uuid>
            m = re.search(r"var '([^']+)' : ((itm\.|/)?(\d+\.[0-9a-f\-]+))", detail)
            if m:
                raw_ref = m.group(2)          # full matched ref string, e.g. "itm.12.uuid"
                bo_name = self._resolve_bo_name(raw_ref)
                if bo_name:
                    record["detail"] = detail.replace(raw_ref, bo_name)
                    # Also fix _artefact_vars
                    var_name = m.group(1)
                    artefact = record["artefact"]
                    if var_name in self._artefact_vars.get(artefact, {}).get("vars", {}):
                        self._artefact_vars[artefact]["vars"][var_name]["type"] = bo_name

    # ------------------------------------------------------------------
    # Real BAW TWX format: <teamworks> root, JSON in <jsonData>
    # ------------------------------------------------------------------

    def _analyse_teamworks(self, root: ET.Element, zip_path: str):
        """
        Parse a real BAW TWX object file whose root element is <teamworks>.
        Each child element represents one artefact: <bpd>, <process>, <twClass>, etc.
        Artefact data is stored as JSON inside a <jsonData> child element.
        BO field definitions are in <definition><property> XML children.
        """
        for child in root:
            tag = _strip_ns(child.tag)
            name = child.get("name") or ""

            if tag == "twClass":
                self._parse_tw_class(child, name, zip_path)

            elif tag == "bpd":
                self._parse_bpd_json(child, name, zip_path)

            elif tag == "process":
                # Services and CSHS are both <process> elements; processType distinguishes them
                # 10=CSHS, 12=ServiceFlow/General, 13=Deployment (skip)
                ptype_elem = child.find("processType")
                ptype = (ptype_elem.text or "").strip() if ptype_elem is not None else ""
                if ptype == "13":
                    continue  # deployment service flow — skip
                atype = "coach" if ptype == "10" else "service"
                self._parse_process_json(child, name, atype, zip_path)

    def _get_jsondata(self, elem: ET.Element):
        """Return parsed jsonData dict from an artefact element, or None."""
        for child in elem:
            if _strip_ns(child.tag) == "jsonData" and child.text:
                try:
                    return json.loads(child.text)
                except (json.JSONDecodeError, ValueError):
                    return None
        return None

    def _parse_tw_class(self, elem: ET.Element, name: str, zip_path: str):
        """Parse a <twClass> Business Object definition."""
        fields = []
        type_refs = []
        _PRIMITIVES_LOWER = {p.lower() for p in (
            "String", "Integer", "Decimal", "Boolean", "Date", "Time", "DateTime",
            "ANY", "string", "integer", "boolean", "number", "decimal",
        )}

        # classId is used for cross-referencing with itemSubjectRef in variables
        class_id_elem = elem.find("classId")
        class_id = (class_id_elem.text or "").strip() if class_id_elem is not None else ""

        for def_elem in elem.iter():
            if _strip_ns(def_elem.tag) != "definition":
                continue
            for prop in def_elem:
                if _strip_ns(prop.tag) != "property":
                    continue
                fname, ftype_id = "", ""
                for sub in prop:
                    stag = _strip_ns(sub.tag)
                    if stag == "name":
                        fname = (sub.text or "").strip()
                    elif stag == "classRef":
                        ftype_id = (sub.text or "").strip()
                if fname:
                    fields.append({"name": fname, "type": ftype_id})
                    # Check if the classRef points to a non-primitive BO (contains a UUID)
                    if ftype_id and not any(p in ftype_id.lower() for p in _PRIMITIVES_LOWER):
                        type_refs.append(ftype_id)

        self.bo_defs[name] = fields
        # Also store by class_id for variable → BO name resolution
        if class_id:
            self.bo_defs[f"_id:{class_id}"] = fields
            self._tw_class_id_to_name = getattr(self, "_tw_class_id_to_name", {})
            self._tw_class_id_to_name[class_id] = name
            # Also index by last segment of the id (e.g. "12.bac3e1d1-...")
            short = class_id.split(".")[-1] if "." in class_id else class_id
            self._tw_class_id_to_name[short] = name

        # Build BO type graph for circular detection using other twClass names we've seen
        for ref_id in type_refs:
            # ref_id examples: "/12.023fa9af-..." or "01f32839-.../12.db884a3c-..."
            short_ref = ref_id.split(".")[-1] if "." in ref_id else ref_id
            if short_ref:
                self.bo_graph[name].append(f"_ref:{short_ref}")

        if name.lower() == self.target.lower():
            self.declarations.append({
                "artefact": name,
                "type": "business-object",
                "file": zip_path,
                "detail": f"BO definition with {len(fields)} field(s): "
                          + ", ".join(f["name"] for f in fields[:8])
                          + ("…" if len(fields) > 8 else ""),
            })

    def _resolve_bo_name(self, item_subject_ref: str) -> str:
        """
        Resolve an itemSubjectRef like 'itm.12.bac3e1d1-a533-422b-b17e-5d8b24622dac'
        or '/12.023fa9af-...' to a BO type name using the class-id index.
        Returns empty string if not found.
        """
        id_map = getattr(self, "_tw_class_id_to_name", {})
        # Try last segment after the last dot
        parts = item_subject_ref.replace("itm.", "").lstrip("/").split(".")
        # Try "12.uuid" form
        if len(parts) >= 2:
            key = ".".join(parts[-2:])
            if key in id_map:
                return id_map[key]
        # Try uuid only
        if parts:
            key = parts[-1]
            if key in id_map:
                return id_map[key]
        return ""

    def _iter_flow_elements(self, jd: dict):
        """
        Yield all flowElement dicts from a jsonData structure regardless of nesting.
        Handles both top-level rootElement[].flowElement[] and nested
        extensionElements.userTaskImplementation[].flowElement[] (CSHS).
        """
        def _walk(obj):
            if isinstance(obj, dict):
                if "flowElement" in obj:
                    for fe in obj["flowElement"]:
                        yield fe
                for v in obj.values():
                    yield from _walk(v)
            elif isinstance(obj, list):
                for item in obj:
                    yield from _walk(item)
        yield from _walk(jd)

    def _parse_process_json(self, elem: ET.Element, name: str,
                            atype: str, zip_path: str):
        """Parse a <process> service flow or CSHS from its jsonData."""
        jd = self._get_jsondata(elem)
        if not jd:
            return

        self._current_process = name
        fg = self._flow_graphs[name]
        if not fg["file"]:
            fg["file"] = zip_path

        for fe in self._iter_flow_elements(jd):
            dtype = fe.get("declaredType", "")
            fe_name = fe.get("name", "") or ""
            fe_id = fe.get("id", "") or fe_name

            # Variable declarations (dataObject)
            if dtype == "dataObject":
                item_ref = fe.get("itemSubjectRef", "")
                bo_name = self._resolve_bo_name(item_ref)
                var_name = fe_name
                is_target_name = _text_contains(var_name, self.target)
                is_target_type = bo_name and _text_contains(bo_name, self.target)
                if is_target_name or is_target_type:
                    self.declarations.append({
                        "artefact": name,
                        "type": atype,
                        "file": zip_path,
                        "detail": f"var '{var_name}' : {bo_name or item_ref} [declared]",
                    })
                    rec = self._artefact_vars[name]
                    if not rec["file"]:
                        rec["file"] = zip_path
                    rec["vars"][var_name] = {"type": bo_name, "atype": atype, "file": zip_path}

            # Script tasks — scan for reads/writes
            elif dtype == "scriptTask":
                script_content = ""
                sc = fe.get("script")
                if isinstance(sc, dict):
                    parts = sc.get("content", [])
                    script_content = " ".join(str(p) for p in parts if p)
                if script_content and _text_contains(script_content, self.target):
                    self._classify_script_usage(script_content, name, atype, zip_path, "script")
                if script_content:
                    self._track_script_vars(script_content, name)
                    self._record_flow_access(script_content, fe_id, "script")
                fg["nodes"][fe_id] = fe_name

            # Sequence flows
            elif dtype == "sequenceFlow":
                src = fe.get("sourceRef", "")
                tgt = fe.get("targetRef", "")
                if src and tgt:
                    fg["edges"].append((src, tgt))

            # Parallel gateways
            elif "parallelGateway" in dtype or (dtype == "gateway" and "parallel" in fe_name.lower()):
                fg["has_parallel"] = True
                fg["nodes"][fe_id] = fe_name

            # Other tasks / events — register in flow graph
            elif dtype in ("userTask", "serviceTask", "subProcess", "callActivity",
                           "com.ibm.bpmsdk.model.bpmn20.ibmext.TFormTask"):
                fg["nodes"][fe_id] = fe_name

            # Coach bindings inside formDefinition (CSHS coach tasks)
            if "formDefinition" in fe:
                self._parse_coach_bindings_json(fe["formDefinition"], name, zip_path)

        # Service I/O parameters (ioSpecification)
        io = jd.get("ioSpecification") or {}
        if not io:
            # Check inside rootElement[0]
            for re_item in jd.get("rootElement", []):
                if "ioSpecification" in re_item:
                    io = re_item["ioSpecification"]
                    break
        self._parse_io_specification(io, name, atype, zip_path)

    def _parse_bpd_json(self, elem: ET.Element, name: str, zip_path: str):
        """Parse a <bpd> (heritage process) from its jsonData."""
        jd = self._get_jsondata(elem)
        if not jd:
            return
        # BPD uses same JSON structure as service flows
        self._parse_process_json(elem, name, "process", zip_path)

    def _parse_coach_bindings_json(self, form_def: dict, artefact: str, zip_path: str):
        """Recursively find binding values in a formDefinition/coachDefinition structure."""
        if not isinstance(form_def, dict):
            return
        for key, val in form_def.items():
            if key == "binding" and isinstance(val, str):
                if _text_contains(val, self.target):
                    self.coach_bindings.append({
                        "artefact": artefact,
                        "type": "coach",
                        "file": zip_path,
                        "detail": f"UI control bound to '{val}'",
                    })
            elif isinstance(val, dict):
                self._parse_coach_bindings_json(val, artefact, zip_path)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        self._parse_coach_bindings_json(item, artefact, zip_path)

    def _parse_io_specification(self, io: dict, artefact: str, atype: str, zip_path: str):
        """Parse ioSpecification to find service input/output parameters typed as the target BO."""
        if not io:
            return
        id_map = getattr(self, "_tw_class_id_to_name", {})

        for direction, result_list in (("dataInput", self.service_inputs),
                                       ("dataOutput", self.service_outputs)):
            for param in io.get(direction, []):
                item_ref = param.get("itemSubjectRef", "")
                bo_name = self._resolve_bo_name(item_ref)
                param_name = param.get("name", "")
                is_target_name = _text_contains(param_name, self.target)
                is_target_type = bo_name and _text_contains(bo_name, self.target)
                if is_target_name or is_target_type:
                    result_list.append({
                        "artefact": artefact,
                        "type": atype,
                        "file": zip_path,
                        "detail": f"[{direction}] '{param_name}' : {bo_name or item_ref}",
                    })

    # ------------------------------------------------------------------
    # Script usage classification
    # ------------------------------------------------------------------

    def _classify_script_usage(self, text: str, artefact: str, atype: str,
                                zip_path: str, tag: str):
        record = {
            "artefact": artefact or "unknown",
            "type": atype or "other",
            "file": zip_path,
            "detail": f"[{tag}] contains reference to '{self.target}'",
        }
        # Heuristic: assignment → write; otherwise → read
        assign_pattern = re.compile(
            r"\b" + re.escape(self.target) + r"\b\s*[\.\[].*?=(?!=)",
            re.IGNORECASE,
        )
        if assign_pattern.search(text):
            self.writes.append(record)
        else:
            self.reads.append(record)

    def _track_script_vars(self, text: str, artefact: str):
        """
        Scan script text for any tw.local.X or bare X references and mark
        the variable as read or written in the containing artefact.
        Uses same heuristic as _classify_script_usage.
        """
        if not artefact or not text:
            return
        rec = self._artefact_vars[artefact]
        assign_pat = re.compile(
            r"\b(tw\.local\.(\w+)|(\w+))\s*[\.\[].*?=(?!=)", re.IGNORECASE
        )
        read_pat = re.compile(r"\btw\.local\.(\w+)\b", re.IGNORECASE)
        for m in assign_pat.finditer(text):
            name = m.group(2) or m.group(3) or ""
            if name:
                rec["writes"].add(name.lower())
        for m in read_pat.finditer(text):
            name = m.group(1)
            if name:
                rec["reads"].add(name.lower())

    def _record_flow_access(self, text: str, activity_name: str, tag: str):
        """
        Record whether the current activity reads or writes the target,
        keyed by activity name, into the active process flow graph.
        Called from the script/expression/condition scan path.
        """
        if not self._current_process or not activity_name or not text:
            return
        fg = self._flow_graphs[self._current_process]
        # Find the node_id whose display name matches activity_name
        node_id = next(
            (nid for nid, nname in fg["nodes"].items() if nname == activity_name),
            activity_name,  # fall back to name as id if not yet registered
        )
        assign_pat = re.compile(
            r"\b" + re.escape(self.target) + r"\b\s*[\.\[].*?=(?!=)",
            re.IGNORECASE,
        )
        if assign_pat.search(text):
            fg["writes"].add(node_id)
        elif _text_contains(text, self.target):
            fg["reads"].add(node_id)

    # ------------------------------------------------------------------
    # New issue detectors
    # ------------------------------------------------------------------

    def find_orphaned_variables(self) -> list:
        """
        Return variables that are declared in a process/service but never
        appear in any read or write script within that same artefact.
        Only checks variables whose name or type matches the target.
        """
        orphans = []
        for artefact, rec in self._artefact_vars.items():
            for var_name, var_info in rec["vars"].items():
                is_target = (
                    _text_contains(var_name, self.target)
                    or _text_contains(var_info.get("type", ""), self.target)
                )
                if not is_target:
                    continue
                key = var_name.lower()
                if key not in rec["reads"] and key not in rec["writes"]:
                    orphans.append({
                        "artefact": artefact,
                        "type": var_info.get("atype", "other"),
                        "file": var_info.get("file", ""),
                        "variable": var_name,
                        "var_type": var_info.get("type", ""),
                        "detail": (
                            f"'{var_name}' : {var_info.get('type', '?')} is declared "
                            f"but never read or written within '{artefact}'"
                        ),
                    })
        return orphans

    def find_write_only_variables(self) -> list:
        """
        Variables of the target type that are written but never read by any
        coach, service output, or script read — likely dead data.
        """
        write_artefacts = {r["artefact"] for r in self.writes}
        read_artefacts = (
            {r["artefact"] for r in self.reads}
            | {r["artefact"] for r in self.service_outputs}
            | {r["artefact"] for r in self.coach_bindings}
        )
        write_only = write_artefacts - read_artefacts
        results = []
        for artefact in sorted(write_only):
            # Find the file from writes list
            file_ = next(
                (r["file"] for r in self.writes if r["artefact"] == artefact), ""
            )
            results.append({
                "artefact": artefact,
                "file": file_,
                "detail": (
                    f"'{self.target}' is written in '{artefact}' but never "
                    f"read or consumed downstream"
                ),
            })
        return results

    def find_missing_output_mappings(self) -> list:
        """
        Service activities that receive the target BO as input but have no
        output mapping for it. Mutations inside the service are silently discarded.
        """
        results = []
        for artefact, activities in self._service_activities.items():
            for act_name, flags in activities.items():
                if flags["has_input_for_target"] and not flags["has_output_for_target"]:
                    results.append({
                        "artefact": artefact,
                        "activity": act_name,
                        "file": flags.get("file", ""),
                        "detail": (
                            f"Activity '{act_name}' in '{artefact}' maps "
                            f"'{self.target}' as input but has no output mapping — "
                            f"any mutations inside the service are discarded"
                        ),
                    })
        return results

    def find_unused_bo_types(self) -> list:
        """
        BO definitions present in the process app that share no name match
        with any declared variable type or service parameter. Scoped to the
        target: only reports if the target BO itself is unreferenced.
        """
        if self.target.lower() not in (k.lower() for k in self.bo_defs):
            return []  # Target BO not defined in this app
        declared_types = set()
        for rec in self.declarations:
            # Extract type from detail string
            m = re.search(r":\s*(\w+)", rec.get("detail", ""))
            if m:
                declared_types.add(m.group(1).lower())
        # If no variable ever uses this BO as its type, it's unused
        if self.target.lower() not in declared_types:
            bo_fields = self.bo_defs.get(self.target, [])
            return [{
                "bo": self.target,
                "fields": [f["name"] for f in bo_fields],
                "detail": (
                    f"BO '{self.target}' is defined in the process app but no "
                    f"process variable or service parameter uses it as a type"
                ),
            }]
        return []

    def find_stale_coach_bindings(self) -> list:
        """
        Coach bindings that reference a field path on the target BO where
        the field name does not exist in the BO definition.
        e.g., binding='claim.nonExistentField' but ClaimRequest has no nonExistentField.
        """
        if self.target.lower() not in (k.lower() for k in self.bo_defs):
            return []  # Can't check without the definition
        bo_field_names = {
            f["name"].lower()
            for f in self.bo_defs.get(self.target, [])
        }
        if not bo_field_names:
            return []

        results = []
        for rec in self.coach_bindings:
            binding_val = re.sub(r".*?'(.*?)'.*", r"\1", rec["detail"])
            # Extract field after the target name: e.g. claim.fieldName
            m = re.search(
                r"\b" + re.escape(self.target) + r"\b\.(\w+)", binding_val, re.IGNORECASE
            )
            if not m:
                # Also check tw.local.varName.fieldName pattern
                m = re.search(r"\.(\w+)\s*$", binding_val)
            if m:
                field = m.group(1).lower()
                if field and field not in bo_field_names:
                    results.append({
                        "artefact": rec["artefact"],
                        "type": "coach",
                        "file": rec["file"],
                        "field": m.group(1),
                        "detail": (
                            f"Coach '{rec['artefact']}' binds to field "
                            f"'{m.group(1)}' which does not exist in "
                            f"'{self.target}' definition"
                        ),
                    })
        return results

    def find_read_before_write(self) -> list:
        """
        Detect activities that read the target variable before any activity
        that writes it has been reached in the process flow.

        Strategy:
        1. For each process flow graph, BFS from the start node.
        2. Track the set of 'write-reached' nodes accumulated along each path.
        3. At each node that reads the target, check whether any write node
           has been visited on any path leading to it. If not, flag it.

        Confidence is lowered (candidate) when the flow contains parallel
        gateways or back-edges (loops), because ordering becomes ambiguous.
        """
        results = []
        for process, fg in self._flow_graphs.items():
            nodes  = fg["nodes"]
            edges  = fg["edges"]
            reads  = fg["reads"]
            writes = fg["writes"]
            file_  = fg["file"]

            if not reads and not writes:
                continue  # Target not referenced in this process at all

            # Build adjacency list
            adj: dict = defaultdict(list)
            all_node_ids: set = set(nodes.keys())
            for src, tgt in edges:
                adj[src].append(tgt)
                all_node_ids.add(src)
                all_node_ids.add(tgt)

            # Detect back-edges (loops) with DFS
            visited_dfs: set = set()
            stack_dfs:   set = set()
            has_loop = False

            def _dfs_loop(node: str):
                nonlocal has_loop
                if node in stack_dfs:
                    has_loop = True
                    return
                if node in visited_dfs:
                    return
                visited_dfs.add(node)
                stack_dfs.add(node)
                for nb in adj.get(node, []):
                    _dfs_loop(nb)
                stack_dfs.discard(node)

            for n in list(all_node_ids):
                _dfs_loop(n)

            fg["has_loop"] = has_loop
            is_ambiguous = fg["has_parallel"] or has_loop

            # Find start nodes: nodes with no incoming edges
            targets_of_edge = {tgt for _, tgt in edges}
            start_nodes = [n for n in all_node_ids if n not in targets_of_edge]
            if not start_nodes:
                # Fully cyclic or no edges — skip, can't determine order
                continue

            # BFS tracking write-reached set per path (state = (node, frozenset of writes seen))
            # To keep complexity tractable, use a per-node "writes_seen_on_any_path" set.
            # This is a sound over-approximation: if a write can precede a read on ANY path,
            # we don't flag it. We only flag reads that have NO preceding write on ANY path.
            writes_reachable_before: dict = defaultdict(set)  # {node_id: {write_nodes_reachable_before}}
            visited_bfs: set = set()
            queue: deque = deque()

            for sn in start_nodes:
                queue.append((sn, frozenset()))
                visited_bfs.add((sn, frozenset()))

            while queue:
                node, writes_so_far = queue.popleft()
                writes_reachable_before[node] |= writes_so_far

                new_writes = writes_so_far | (writes & {node})
                for nb in adj.get(node, []):
                    state = (nb, new_writes)
                    if state not in visited_bfs:
                        visited_bfs.add(state)
                        queue.append(state)

            # Flag read nodes where no write was reachable before them on any path
            for read_node in reads:
                preceding_writes = writes_reachable_before.get(read_node, set())
                if not (preceding_writes & writes):
                    node_name = nodes.get(read_node, read_node)
                    confidence = "candidate" if is_ambiguous else "likely"
                    results.append({
                        "process": process,
                        "activity": node_name,
                        "node_id": read_node,
                        "file": file_,
                        "is_ambiguous": is_ambiguous,
                        "detail": (
                            f"Activity '{node_name}' in '{process}' reads "
                            f"'{self.target}' before any write to it has been "
                            f"reached on this flow path "
                            f"({'candidate — parallel/loop flow present' if is_ambiguous else 'likely'})"
                        ),
                    })

        return results

    # ------------------------------------------------------------------
    # Circular reference detection (DFS on BO graph)
    # ------------------------------------------------------------------

    def find_cycles(self) -> list:
        """Return list of cycles as ordered name lists."""
        # Resolve _ref: placeholders to actual BO names before cycle detection
        id_map = getattr(self, "_tw_class_id_to_name", {})
        if id_map:
            resolved: dict = defaultdict(list)
            for bo_name, refs in self.bo_graph.items():
                for ref in refs:
                    if ref.startswith("_ref:"):
                        short = ref[5:]
                        target_name = id_map.get(short, "")
                        if target_name and target_name != bo_name:
                            resolved[bo_name].append(target_name)
                    else:
                        resolved[bo_name].append(ref)
            self.bo_graph = resolved

        visited = set()
        path = []
        cycles = []

        def dfs(node):
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            for neighbour in self.bo_graph.get(node, []):
                dfs(neighbour)
            path.pop()

        for bo in list(self.bo_graph.keys()):
            dfs(bo)

        # Deduplicate (cycles that are rotations of each other)
        seen = set()
        unique = []
        for c in cycles:
            key = tuple(sorted(c))
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    # ------------------------------------------------------------------
    # Over-coupling detection
    # ------------------------------------------------------------------

    def find_over_coupling(self) -> list:
        """
        Group write usages by target BO. Flag groups exceeding threshold.
        Returns list of {bo, count, services}.
        """
        writers_by_bo = defaultdict(set)
        for w in self.writes:
            writers_by_bo[self.target].add(w["artefact"])

        results = []
        for bo, writers in writers_by_bo.items():
            if len(writers) > self.threshold:
                results.append({
                    "bo": bo,
                    "count": len(writers),
                    "services": sorted(writers),
                })
        return results

    # ------------------------------------------------------------------
    # Redundant service call candidates
    # ------------------------------------------------------------------

    def find_redundant_service_candidates(self) -> list:
        """
        Flag pairs of services that both appear in service_inputs for the same
        BO and are in the same process artefact. These are candidates only.
        """
        by_process = defaultdict(list)
        for rec in self.service_inputs:
            by_process[rec["artefact"]].append(rec)

        candidates = []
        for process, recs in by_process.items():
            if len(recs) > 1:
                services = sorted({r["artefact"] for r in recs})
                candidates.append({
                    "process": process,
                    "services": services,
                    "note": "Multiple services in the same process consume this BO as input. "
                            "Verify whether each call is distinct or duplicated.",
                })
        return candidates

    # ------------------------------------------------------------------
    # Impact assessment
    # ------------------------------------------------------------------

    def impact_assessment(self) -> dict:
        write_count = len(self.writes)
        coach_count = len(self.coach_bindings)
        total_consumers = (len(self.reads) + write_count + len(self.service_inputs)
                           + len(self.service_outputs) + coach_count)

        if write_count == 0 and coach_count == 0:
            risk = "Low"
        elif write_count <= self.threshold and coach_count <= 2:
            risk = "Medium"
        else:
            risk = "High"

        changes = {
            "add_field": {
                "risk": "Low",
                "must_update": [],
                "safe": [r["artefact"] for r in self.reads + self.service_inputs
                         + self.service_outputs + self.coach_bindings],
                "note": "Adding a new field is backward-compatible. Existing consumers are unaffected.",
            },
            "remove_field": {
                "risk": risk,
                "must_update": ([r["artefact"] for r in self.writes]
                                + [r["artefact"] for r in self.coach_bindings]),
                "safe": [r["artefact"] for r in self.reads if "field" not in r["detail"]],
                "note": "Removing a field breaks any service or coach that writes to or binds the field.",
            },
            "rename_field": {
                "risk": risk,
                "must_update": ([r["artefact"] for r in self.reads + self.writes]
                                + [r["artefact"] for r in self.coach_bindings]),
                "safe": [],
                "note": "Renaming a field requires updating all read, write, and coach-binding references.",
            },
            "delete_bo": {
                "risk": "High" if total_consumers > 0 else "Low",
                "must_update": sorted({r["artefact"] for r in
                                       self.reads + self.writes + self.declarations
                                       + self.service_inputs + self.service_outputs
                                       + self.coach_bindings}),
                "safe": [],
                "note": f"Deleting the BO affects all {total_consumers} consumer(s) found.",
            },
            "change_field_type": {
                "risk": "Medium" if total_consumers < 5 else "High",
                "must_update": sorted({r["artefact"] for r in self.writes
                                       + self.service_inputs + self.service_outputs}),
                "safe": [r["artefact"] for r in self.reads],
                "note": "Type changes affect serialization and mapping in every service that passes the field.",
            },
        }
        return changes


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _dedup(records: list) -> list:
    seen = set()
    out = []
    for r in records:
        key = (r["artefact"], r["type"], r["detail"])
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def generate_markdown(target: str, analyser: DependencyAnalyser,
                      cycles: list, over_coupling: list,
                      redundant: list, orphans: list, write_only: list,
                      missing_outputs: list, unused_bos: list,
                      stale_bindings: list, read_before_write: list) -> str:
    impact = analyser.impact_assessment()
    lines = [
        f"# Dependency Report: `{target}`",
        f"",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}  ",
        f"**Source:** `{analyser.twx_path}`  ",
        f"**Over-coupling threshold:** {analyser.threshold} writers",
        f"",
    ]

    # Summary
    total = (len(analyser.declarations) + len(analyser.reads) + len(analyser.writes)
             + len(analyser.service_inputs) + len(analyser.service_outputs)
             + len(analyser.coach_bindings))
    issues = (len(cycles) + len(over_coupling) + len(redundant)
              + len(orphans) + len(write_only) + len(missing_outputs)
              + len(unused_bos) + len(stale_bindings) + len(read_before_write))
    lines += [
        "## Summary",
        "",
        f"`{target}` was found in **{total}** location(s) across the process application: "
        f"{len(analyser.declarations)} declaration(s), {len(analyser.reads)} read(s), "
        f"{len(analyser.writes)} write(s), "
        f"{len(analyser.service_inputs)+len(analyser.service_outputs)} service binding(s), "
        f"{len(analyser.coach_bindings)} coach binding(s). "
        f"**{issues}** issue(s) detected.",
        "",
    ]

    # Dependency graph (Mermaid)
    # Collect all unique nodes; cap at 20 to keep the diagram readable.
    _GRAPH_CAP = 20
    all_graph_records = (
        [(r, "decl")    for r in _dedup(analyser.declarations)]
        + [(r, "read")  for r in _dedup(analyser.reads)]
        + [(r, "write") for r in _dedup(analyser.writes)]
        + [(r, "sin")   for r in _dedup(analyser.service_inputs)]
        + [(r, "sout")  for r in _dedup(analyser.service_outputs)]
        + [(r, "coach") for r in _dedup(analyser.coach_bindings)]
    )
    trimmed = len(all_graph_records) > _GRAPH_CAP
    if trimmed:
        shown = all_graph_records[:_GRAPH_CAP]
        omitted = len(all_graph_records) - _GRAPH_CAP
    else:
        shown = all_graph_records
        omitted = 0

    def _nid(name: str) -> str:
        """Return a unique, Mermaid-safe node ID: sanitised name + 6-char hash."""
        safe = re.sub(r"\W", "_", name)[:30]
        suffix = hashlib.md5(name.encode()).hexdigest()[:6]
        return f"{safe}_{suffix}"

    def _node_decl(nid: str, label: str, atype: str) -> str:
        """Return the Mermaid node declaration using the correct shape for atype."""
        if atype == "business-object":
            return f'    {nid}(("{label}\\n[{atype}]"))'   # circle
        if atype == "coach":
            return f'    {nid}{{"{label}\\n[{atype}]"}}'   # diamond
        if atype == "service":
            return f'    {nid}>"{label}\\n[{atype}]"]'     # flag/asymmetric
        # process, other → rectangle
        return f'    {nid}["{label}\\n[{atype}]"]'

    lines += ["## Dependency graph", "", "```mermaid", "flowchart LR"]
    lines.append(f'    target["{target}"]')
    # Track which node IDs have already had their shape/label declaration emitted
    # so we only emit a node definition once (the first relationship wins for shape).
    _emitted_nodes: set = set()

    for r, rel in shown:
        nid = _nid(r["artefact"])
        label = r["artefact"].replace('"', "'")
        atype = r.get("type", "other")
        already = nid in _emitted_nodes
        _emitted_nodes.add(nid)

        if rel == "decl":
            if not already:
                lines.append(_node_decl(nid, label, atype))
            lines.append(f'    {nid} -->|declares| target')
        elif rel == "read":
            if not already:
                lines.append(_node_decl(nid, label, atype))
            lines.append(f'    {nid} -->|reads| target')
        elif rel == "write":
            if not already:
                lines.append(_node_decl(nid, label, atype))
            lines.append(f'    target -->|written by| {nid}')
        elif rel == "sin":
            if not already:
                lines.append(f'    {nid}>"{label}\\n[{atype}]"]')
            lines.append(f'    target -->|input to| {nid}')
        elif rel == "sout":
            if not already:
                lines.append(f'    {nid}>"{label}\\n[{atype}]"]')
            lines.append(f'    {nid} -->|outputs| target')
        elif rel == "coach":
            if not already:
                lines.append(f'    {nid}{{"{label}\\n[{atype}]"}}')
            lines.append(f'    {nid} -.->|binds| target')
    if trimmed:
        lines.append(f'    note["... and {omitted} more node(s) omitted for readability"]')
    lines += ["```", ""]
    if trimmed:
        lines += [
            f"> **Note:** The diagram shows the first {_GRAPH_CAP} of "
            f"{len(all_graph_records)} nodes. See the tables below for the full list.",
            "",
        ]

    def _table(records, header="Artefact | Type | File | Detail"):
        cols = header.split(" | ")
        out = ["| " + " | ".join(cols) + " |",
               "| " + " | ".join(["---"] * len(cols)) + " |"]
        for r in _dedup(records):
            fname = os.path.basename(r.get("file", ""))
            out.append(f"| `{r['artefact']}` | {r['type']} | `{fname}` | {r['detail']} |")
        return out

    for section, records in [
        ("## Declarations", analyser.declarations),
        ("## Read usages", analyser.reads),
        ("## Write usages", analyser.writes),
        ("## Service input bindings", analyser.service_inputs),
        ("## Service output bindings", analyser.service_outputs),
        ("## Coach bindings", analyser.coach_bindings),
    ]:
        lines.append(section)
        lines.append("")
        if records:
            lines += _table(records)
        else:
            lines.append("_None found._")
        lines.append("")

    # Issues
    lines += ["## Issues detected", ""]
    any_issues = any([cycles, over_coupling, redundant, orphans,
                      write_only, missing_outputs, unused_bos, stale_bindings,
                      read_before_write])
    if not any_issues:
        lines.append("_No issues detected._")
    else:
        for cycle in cycles:
            path_str = " → ".join(cycle)
            lines.append(f"⚠️ **Circular BO reference:** `{path_str}`  ")
            lines.append("  Each type in this chain directly or transitively references the next, "
                         "which can cause serialization and deep-copy failures at runtime.")
            lines.append("")
        for oc in over_coupling:
            svc_list = ", ".join(f"`{s}`" for s in oc["services"])
            lines.append(f"⚠️ **Over-coupling:** `{oc['bo']}` is written by {oc['count']} services "
                         f"({svc_list}). Consider splitting responsibilities or introducing a "
                         f"dedicated update service.")
            lines.append("")
        for rc in redundant:
            svc_list = ", ".join(f"`{s}`" for s in rc["services"])
            lines.append(f"🔍 **Redundant call candidate:** In `{rc['process']}`, the services "
                         f"{svc_list} all consume `{target}` as input. {rc['note']}")
            lines.append("")
        for o in orphans:
            lines.append(f"🔍 **Orphaned variable:** {o['detail']}")
            lines.append("")
        for w in write_only:
            lines.append(f"⚠️ **Write-only variable:** {w['detail']}")
            lines.append("")
        for mo in missing_outputs:
            lines.append(f"⚠️ **Missing output mapping:** {mo['detail']}")
            lines.append("")
        for ub in unused_bos:
            lines.append(f"⚠️ **Unused BO type:** {ub['detail']}")
            lines.append("")
        for sb in stale_bindings:
            lines.append(f"⚠️ **Stale coach binding:** {sb['detail']}")
            lines.append("")
        for rb in read_before_write:
            icon = "🔍" if rb["is_ambiguous"] else "⚠️"
            lines.append(f"{icon} **Read before write:** {rb['detail']}")
            lines.append("")
    lines.append("")

    # Impact assessment
    lines += ["## Impact assessment", ""]
    risk_icons = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
    for change, details in impact.items():
        icon = risk_icons.get(details["risk"], "⚪")
        lines.append(f"### {icon} {change.replace('_', ' ').title()} — {details['risk']} risk")
        lines.append("")
        lines.append(details["note"])
        if details["must_update"]:
            lines.append("")
            lines.append("**Must update:** " + ", ".join(f"`{a}`" for a in sorted(set(details["must_update"]))))
        if details["safe"]:
            lines.append("**Safe (unaffected):** " + ", ".join(f"`{a}`" for a in sorted(set(details["safe"][:8]))))
        lines.append("")

    return "\n".join(lines)


def generate_json(target: str, analyser: DependencyAnalyser,
                  cycles: list, over_coupling: list, redundant: list,
                  orphans: list, write_only: list, missing_outputs: list,
                  unused_bos: list, stale_bindings: list,
                  read_before_write: list) -> dict:
    return {
        "target": target,
        "twx": analyser.twx_path,
        "generated": datetime.now(timezone.utc).isoformat(),
        "declarations": _dedup(analyser.declarations),
        "reads": _dedup(analyser.reads),
        "writes": _dedup(analyser.writes),
        "service_inputs": _dedup(analyser.service_inputs),
        "service_outputs": _dedup(analyser.service_outputs),
        "coach_bindings": _dedup(analyser.coach_bindings),
        "issues": {
            "circular_references": cycles,
            "over_coupling": over_coupling,
            "redundant_service_candidates": redundant,
            "orphaned_variables": orphans,
            "write_only_variables": write_only,
            "missing_output_mappings": missing_outputs,
            "unused_bo_types": unused_bos,
            "stale_coach_bindings": stale_bindings,
            "read_before_write": read_before_write,
        },
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def list_bos(twx_path: str) -> list:
    """Return a sorted list of all Business Object (twClass) names in a TWX."""
    names = []
    with zipfile.ZipFile(twx_path, "r") as zf:
        for entry in zf.namelist():
            if not entry.startswith("objects/") or not entry.endswith(".xml"):
                continue
            try:
                with zf.open(entry) as fh:
                    content = fh.read(600).decode("utf-8", errors="ignore")
                if "<twClass " not in content:
                    continue
                import re as _re
                m = _re.search(r'<twClass[^>]+name="([^"]+)"', content)
                if m:
                    names.append(m.group(1))
            except Exception:
                continue
    return sorted(names)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a BAW TWX export for variable/BO dependencies."
    )
    parser.add_argument("twx", help="Path to the .twx file")
    parser.add_argument(
        "target", nargs="?", default=None,
        help="Variable or BO name to analyze (omit when using --list-bos)",
    )
    parser.add_argument(
        "--list-bos", action="store_true",
        help="List all Business Object names defined in the TWX and exit",
    )
    parser.add_argument(
        "--threshold", type=int, default=3,
        help="Over-coupling threshold: flag when more than N distinct services write to the BO (default: 3)",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Directory to write the reports into (default: '<twxname>.twx - reports' subfolder next to the TWX file)",
    )
    args = parser.parse_args()

    # Resolve default output dir relative to the TWX file, not the working directory
    if args.output_dir is None:
        twx_abs = os.path.abspath(args.twx)
        twx_dir = os.path.dirname(twx_abs)
        twx_basename = os.path.basename(twx_abs)
        args.output_dir = os.path.join(twx_dir, f"{twx_basename} - reports")

    if not os.path.isfile(args.twx):
        print(f"ERROR: File not found: {args.twx}", file=sys.stderr)
        sys.exit(1)

    if not zipfile.is_zipfile(args.twx):
        print(f"ERROR: '{args.twx}' is not a valid ZIP/TWX archive.", file=sys.stderr)
        sys.exit(1)

    if args.list_bos:
        for name in list_bos(args.twx):
            print(name)
        sys.exit(0)

    if not args.target:
        parser.error("target is required unless --list-bos is specified")

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Analyzing '{args.target}' in {args.twx} …")
    analyser = DependencyAnalyser(args.twx, args.target, args.threshold)
    analyser.run()

    cycles          = analyser.find_cycles()
    over_coupling   = analyser.find_over_coupling()
    redundant       = analyser.find_redundant_service_candidates()
    orphans         = analyser.find_orphaned_variables()
    write_only      = analyser.find_write_only_variables()
    missing_outputs = analyser.find_missing_output_mappings()
    unused_bos      = analyser.find_unused_bo_types()
    stale_bindings    = analyser.find_stale_coach_bindings()
    read_before_write = analyser.find_read_before_write()

    safe_name = re.sub(r"[^\w\-]", "_", args.target)
    md_path   = os.path.join(args.output_dir, f"{safe_name}-dependency-report.md")
    json_path = os.path.join(args.output_dir, f"{safe_name}-dependency-report.json")

    md_content = generate_markdown(
        args.target, analyser,
        cycles, over_coupling, redundant,
        orphans, write_only, missing_outputs, unused_bos, stale_bindings,
        read_before_write,
    )
    json_content = generate_json(
        args.target, analyser,
        cycles, over_coupling, redundant,
        orphans, write_only, missing_outputs, unused_bos, stale_bindings,
        read_before_write,
    )

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_content, f, indent=2, default=str)

    total = (len(analyser.declarations) + len(analyser.reads) + len(analyser.writes)
             + len(analyser.service_inputs) + len(analyser.service_outputs)
             + len(analyser.coach_bindings))
    issues = (len(cycles) + len(over_coupling) + len(redundant)
              + len(orphans) + len(write_only) + len(missing_outputs)
              + len(unused_bos) + len(stale_bindings) + len(read_before_write))

    print(f"Done. {total} location(s) found, {issues} issue(s).")
    print(f"  Markdown report : {md_path}")
    print(f"  JSON report     : {json_path}")


if __name__ == "__main__":
    main()
