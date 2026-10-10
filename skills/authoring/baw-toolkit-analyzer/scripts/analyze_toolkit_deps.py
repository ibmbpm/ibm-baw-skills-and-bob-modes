#!/usr/bin/env python3
"""
analyze_toolkit_deps.py — BAW Toolkit Dependency Analyzer

Analyses a BAW TWX export and produces a report of toolkit dependencies
(direct, transitive), snapshot tracking, and issue detection.

Real TWX structure (confirmed from BAW 8.6.12):
  META-INF/package.xml        — master manifest; lists <dependencies> and <objects>
  objects/<id>.xml            — individual artifact XML files (wrapped in <teamworks>)
  toolkits/<snapshot-id>.zip  — each declared dependency is embedded as a nested zip

Usage:
  python analyze_toolkit_deps.py <path-to-file.twx> [options]

Options:
  --list-toolkits             List all toolkits declared in the TWX and exit.
  --mode full|where-used|what-uses
                              Analysis mode. Default: full.
  --toolkit <name>            Toolkit name (required for where-used / what-uses).
  --output-dir <dir>          Override the default output directory.

Output (written to <output-dir>/):
  toolkit-dependency-report.json
  toolkit-dependency-report.md
"""

import argparse
import io
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# package.xml parsing helpers
# ---------------------------------------------------------------------------

def _strip_ns(tag: str) -> str:
    """Return the local name without any XML namespace prefix."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _parse_package_xml(zf: zipfile.ZipFile) -> ET.Element:
    """Read and parse META-INF/package.xml from an open ZipFile."""
    with zf.open("META-INF/package.xml") as f:
        return ET.fromstring(f.read())


def _extract_target_info(pkg_root: ET.Element) -> dict:
    """
    Return {name, short_name, is_toolkit, snapshot_name, snapshot_acronym}
    from the <target> element of package.xml.
    """
    target = pkg_root.find("target")
    if target is None:
        return {"name": "Unknown", "short_name": "", "is_toolkit": False,
                "snapshot_name": "", "snapshot_acronym": ""}

    project = target.find("project")
    snapshot = target.find("snapshot")

    name = project.attrib.get("name", "") if project is not None else ""
    short_name = project.attrib.get("shortName", "") if project is not None else ""
    is_toolkit = (project.attrib.get("isToolkit", "false").lower() == "true"
                  if project is not None else False)
    snap_name = snapshot.attrib.get("name", "Tip") if snapshot is not None else "Tip"
    snap_acronym = snapshot.attrib.get("acronym", snap_name) if snapshot is not None else snap_name

    return {
        "name": name,
        "short_name": short_name,
        "is_toolkit": is_toolkit,
        "snapshot_name": snap_name,
        "snapshot_acronym": snap_acronym,
    }


def _extract_direct_deps(pkg_root: ET.Element) -> list:
    """
    Parse <dependencies><dependency> elements from package.xml.

    Each <dependency> contains:
      <project name="..." shortName="..." isToolkit="true|false" />
      <branch name="..." />
      <snapshot name="..." acronym="..." originalCreationDate="..." />

    Returns a list of dicts:
      {name, short_name, branch, snapshot_name, snapshot_id, rank, is_managed}
    """
    deps = []
    deps_elem = pkg_root.find("dependencies")
    if deps_elem is None:
        return deps

    for dep in deps_elem.findall("dependency"):
        project = dep.find("project")
        branch = dep.find("branch")
        snapshot = dep.find("snapshot")

        if project is None:
            continue

        name = project.attrib.get("name", "")
        short_name = project.attrib.get("shortName", "")
        is_system = project.attrib.get("isSystem", "false").lower() == "true"
        branch_name = branch.attrib.get("name", "") if branch is not None else ""
        snap_name = snapshot.attrib.get("name", "") if snapshot is not None else ""
        snap_id = snapshot.attrib.get("id", "").replace("2064.", "") if snapshot is not None else ""
        snap_date = snapshot.attrib.get("originalCreationDate", "") if snapshot is not None else ""
        rank = int(dep.attrib.get("rank", 0))
        dep_id = dep.attrib.get("id", "").replace("2069.", "")

        deps.append({
            "name": name,
            "short_name": short_name,
            "branch": branch_name,
            "snapshot_name": snap_name,
            "snapshot_id": snap_id,
            "snapshot_date": snap_date,
            "rank": rank,
            "is_system": is_system,
            "dep_id": dep_id,
        })

    return deps


# ---------------------------------------------------------------------------
# Artifact XML scanning for toolkit references
# ---------------------------------------------------------------------------

def _scan_objects_for_toolkit_refs(zf: zipfile.ZipFile, direct_deps: list) -> tuple:
    """
    Scan all objects/*.xml files in a ZipFile for references to toolkit items.

    Detection strategies:
    1. Index all exported artifacts (UUIDs, names, types) from embedded toolkit ZIPs
       in toolkits/<snapshot-id>.zip.
    2. Match dependency IDs (<dependency id="2069.UUID">) and artifact UUIDs (classRefs,
       coach views, services, variable types, participants, etc.) in app objects.
    3. Script/JSON references matching '<shortName>.' prefix.
    4. Dangling classRefs — classRef values whose leading dep-UUID does not match any
       declared dependency (indicates a removed toolkit still referenced by an artifact).

    Returns ({toolkit_key: [(artifact_name, artifact_type, snippet), ...]},
             [(artifact_name, artifact_type, dep_uuid), ...])  <- dangling refs
    """
    refs = defaultdict(list)
    dangling = []  # (art_name, art_type, dep_uuid_prefix)

    # 1. Build index from embedded toolkits and direct dependency metadata
    dep_id_to_key = {}
    obj_to_tk = {}  # uuid -> (tk_key, target_art_name, target_art_type)
    short_names = []
    known_dep_ids = set()  # all dep_id UUIDs from declared dependencies
    known_view_uuids = set()  # all coachView UUIDs found in embedded toolkit ZIPs

    for dep in direct_deps:
        tk_key = dep.get("short_name") or dep.get("name")
        if not tk_key:
            continue
        short_names.append(tk_key)

        # Track dependency ID if available
        dep_id = dep.get("dep_id", "").replace("2069.", "")
        if dep_id:
            dep_id_to_key[dep_id] = tk_key
            known_dep_ids.add(dep_id)

        snap_id = dep.get("snapshot_id", "").replace("2064.", "")
        tk_zip_name = f"toolkits/2064.{snap_id}.zip"
        if tk_zip_name in zf.namelist():
            try:
                tk_bytes = zf.read(tk_zip_name)
                with zipfile.ZipFile(io.BytesIO(tk_bytes)) as tk_zf:
                    for oname in tk_zf.namelist():
                        if oname.startswith("objects/") and oname.endswith(".xml"):
                            obj_id = oname.replace("objects/", "").replace(".xml", "")
                            uuid_part = obj_id.split(".", 1)[-1]
                            try:
                                oraw = tk_zf.read(oname)
                                oroot = ET.fromstring(oraw)
                                for child in oroot:
                                    target_name = child.attrib.get("name", "")
                                    target_type = _strip_ns(child.tag)
                                    obj_to_tk[uuid_part] = (tk_key, target_name, target_type)
                                    # Track all coach view UUIDs for viewUUID resolution
                                    if target_type == "coachView":
                                        known_view_uuids.add(uuid_part)
                                    break
                            except Exception:
                                pass
            except Exception:
                pass

    patterns = {sn: re.compile(re.escape(sn) + r"\.", re.IGNORECASE)
                for sn in short_names if sn}

    uuid_pattern = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
    # classRef format: <dep-uuid>/<type-prefix>.<artifact-uuid>
    classref_pattern = re.compile(
        r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
        r"/\d+\.[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    )
    # viewUUID in CSHS jsonData: "viewUUID":"<type-prefix>.<uuid>"
    view_uuid_pattern = re.compile(
        r'"viewUUID"\s*:\s*"(?:\d+\.)?([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"'
    )

    for entry in zf.namelist():
        if not entry.startswith("objects/") or not entry.endswith(".xml"):
            continue
        try:
            with zf.open(entry) as f:
                raw = f.read().decode("utf-8", errors="replace")
        except Exception:
            continue

        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            continue

        # Human-friendly mapping for artifact type tags
        TYPE_LABELS = {
            "coachView": "Coach View",
            "twClass": "Business Object / Variable Type",
            "process": "Service Flow / Process",
            "participant": "Participant",
            "uiTheme": "Theme",
            "managedAsset": "Managed File / Asset",
            "projectDefaults": "Process App Settings",
            "environmentVariableSet": "Environment Variables",
            "bpd": "Business Process (BPD)",
        }

        # Identify the artifact's name and type from the first child of <teamworks>
        art_name = ""
        art_type = "Artifact"
        for child in root:
            art_name = child.attrib.get("name", "")
            raw_tag = _strip_ns(child.tag)
            
            # Refine process type if it's a process element
            if raw_tag == "process":
                pt = child.find("processType")
                pt_val = pt.text if pt is not None else ""
                if pt_val == "10" or child.find("coachflow") is not None:
                    art_type = "Client-Side Human Service"
                elif pt_val == "12":
                    art_type = "Service Flow"
                elif pt_val == "13":
                    art_type = "Deployment Service Flow"
                elif pt_val == "1":
                    art_type = "General System Service"
                else:
                    art_type = "Service Flow / Process"
            else:
                art_type = TYPE_LABELS.get(raw_tag, raw_tag)
            break

        seen_for_file = set()
        seen_dangling = set()

        # Strategy 4: Dangling classRefs (dep UUID not in any declared dependency)
        for m in classref_pattern.finditer(raw):
            dep_uuid = m.group(1)
            if dep_uuid not in known_dep_ids and dep_uuid not in seen_dangling:
                seen_dangling.add(dep_uuid)
                dangling.append((art_name, art_type, dep_uuid))

        # Strategy 5: Unresolved viewUUID in CSHS JSON (coach view from removed toolkit)
        for m in view_uuid_pattern.finditer(raw):
            view_uuid = m.group(1)
            if view_uuid not in known_view_uuids and view_uuid not in seen_dangling:
                seen_dangling.add(view_uuid)
                dangling.append((art_name, art_type, f"unresolved coach view ({view_uuid[:8]}…)"))

        # Strategy 1: Match toolkit artifact UUIDs
        found_uuids = set(uuid_pattern.findall(raw))
        for uid in found_uuids:
            if uid in obj_to_tk:
                tk_key, target_name, target_type = obj_to_tk[uid]
                friendly_type = TYPE_LABELS.get(target_type, target_type)
                item_display = target_name if target_name else f"Unnamed {friendly_type}"
                snippet = f"{friendly_type}: `{item_display}`"
                ref_key = (tk_key, art_name, art_type, snippet)
                if ref_key not in seen_for_file:
                    seen_for_file.add(ref_key)
                    refs[tk_key].append((art_name, art_type, snippet))

        # Strategy 2: Match short_name prefix in scripts/JSON
        for sn, pattern in patterns.items():
            m = pattern.search(raw)
            if m:
                start = max(0, m.start() - 20)
                end = min(len(raw), m.end() + 40)
                match_text = raw[start:end].replace("\n", " ").strip()
                snippet = f"Script Reference: `{match_text}`"
                ref_key = (sn, art_name, art_type, snippet)
                if ref_key not in seen_for_file:
                    seen_for_file.add(ref_key)
                    refs[sn].append((art_name, art_type, snippet))

    return refs, dangling


# ---------------------------------------------------------------------------
# Transitive dependency resolution (from embedded toolkit zips)
# ---------------------------------------------------------------------------

def _load_embedded_toolkit_deps(twx_path: str, direct_deps: list) -> dict:
    """
    For each embedded toolkit zip in toolkits/, open it and extract its own
    direct dependencies.  Returns {toolkit_short_name: [list of dep dicts]}.

    The toolkit zips are named toolkits/<snapshot-id>.zip where snapshot-id
    matches the snapshot id from the <snapshot id="2064.<uuid>"> element.
    We match on the uuid portion (after "2064.").
    """
    transitive = {}
    with zipfile.ZipFile(twx_path, "r") as outer:
        # Build a map of snapshot_id -> toolkit name for matching
        snap_id_to_dep = {d["snapshot_id"]: d for d in direct_deps if d["snapshot_id"]}

        for entry in outer.namelist():
            if not entry.startswith("toolkits/") or not entry.endswith(".zip"):
                continue
            # Entry is like toolkits/2064.<uuid>.zip
            zip_name = Path(entry).name  # e.g. "2064.abc123.zip"
            # Extract uuid portion
            parts = zip_name.replace(".zip", "").split(".", 1)
            snap_uuid = parts[1] if len(parts) == 2 else ""

            dep_info = snap_id_to_dep.get(snap_uuid)
            if dep_info is None:
                continue  # skip unknown toolkits

            try:
                tk_bytes = outer.read(entry)
                with zipfile.ZipFile(io.BytesIO(tk_bytes)) as inner:
                    pkg_root = _parse_package_xml(inner)
                    inner_deps = _extract_direct_deps(pkg_root)
                    if inner_deps:
                        transitive[dep_info["short_name"] or dep_info["name"]] = inner_deps
            except Exception:
                pass  # unreadable toolkit zip — skip silently

    return transitive


# ---------------------------------------------------------------------------
# Issue detection
# ---------------------------------------------------------------------------

def _find_circular(direct_deps: list, transitive: dict) -> list:
    """
    Detect circular toolkit dependencies using DFS over the full graph.
    Returns list of cycle paths (each a list of short names / names).
    """
    # Build graph: {node_key: [list of dep short_names]}
    graph = defaultdict(list)
    app_key = "__APP__"
    for d in direct_deps:
        k = d["short_name"] or d["name"]
        graph[app_key].append(k)
    for parent, deps in transitive.items():
        for d in deps:
            k = d["short_name"] or d["name"]
            graph[parent].append(k)

    cycles = []
    visited = set()
    rec_stack = []

    def dfs(node):
        visited.add(node)
        rec_stack.append(node)
        for neighbour in graph.get(node, []):
            if neighbour not in visited:
                dfs(neighbour)
            elif neighbour in rec_stack:
                idx = rec_stack.index(neighbour)
                cycle = rec_stack[idx:] + [neighbour]
                if cycle not in cycles:
                    cycles.append(cycle)
        rec_stack.pop()

    for node in list(graph.keys()):
        if node not in visited:
            dfs(node)

    # Strip the internal __APP__ sentinel from reported paths
    cleaned = []
    for cycle in cycles:
        c = [n for n in cycle if n != "__APP__"]
        if c and c not in cleaned:
            cleaned.append(c)
    return cleaned


def _find_conflicts(direct_deps: list, transitive: dict) -> list:
    """
    Find cases where the same toolkit name is required at two different
    snapshots across direct deps and transitive deps.
    """
    all_deps = direct_deps[:]
    for sub_deps in transitive.values():
        all_deps.extend(sub_deps)

    by_name = defaultdict(set)
    for d in all_deps:
        key = d["short_name"] or d["name"]
        if key and d["snapshot_name"]:
            by_name[key].add(d["snapshot_name"])

    conflicts = []
    for name, snapshots in by_name.items():
        if len(snapshots) > 1:
            conflicts.append({"toolkit": name, "snapshots": sorted(snapshots)})
    return conflicts


def _find_unused(direct_deps: list, artifact_refs: dict) -> list:
    """Return deps whose short_name (or name) has no artifact references."""
    unused = []
    for dep in direct_deps:
        key = dep["short_name"] or dep["name"]
        if not artifact_refs.get(key):
            unused.append(dep)
    return unused


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _make_mermaid(app_name: str, direct_deps: list, transitive: dict,
                  max_nodes: int = 25) -> str:
    lines = ["graph TD"]
    app_id = re.sub(r"[^A-Za-z0-9]", "_", app_name)
    lines.append(f'  {app_id}["{app_name}"]')
    shown = 0
    total = len(direct_deps)
    for dep in direct_deps:
        if shown >= max_nodes:
            break
        tk_key = dep["short_name"] or dep["name"]
        tk_id = re.sub(r"[^A-Za-z0-9]", "_", tk_key)
        snap = dep["snapshot_name"] or "Tip"
        lines.append(f'  {app_id} -->|direct| {tk_id}["{tk_key}\\n({snap})"]')
        shown += 1
        # Add transitive children
        for sub in transitive.get(tk_key, []):
            if shown >= max_nodes:
                break
            sub_key = sub["short_name"] or sub["name"]
            sub_id = re.sub(r"[^A-Za-z0-9]", "_", sub_key)
            sub_snap = sub["snapshot_name"] or "Tip"
            lines.append(
                f'  {tk_id} -->|via {tk_key}| {sub_id}["{sub_key}\\n({sub_snap})"]'
            )
            shown += 1

    total_shown = shown
    if total > total_shown:
        lines.append(f"  %% {total - total_shown} node(s) omitted (limit {max_nodes})")
    return "\n".join(lines)


def _build_report(twx_path, mode, toolkit_filter, target_info, direct_deps,
                  transitive, artifact_refs, dangling_refs=None):
    cycles = _find_circular(direct_deps, transitive)
    conflicts = _find_conflicts(direct_deps, transitive)
    unused = _find_unused(direct_deps, artifact_refs)
    dangling_refs = dangling_refs or []

    issues = {
        "circular": cycles,
        "conflicts": conflicts,
        "possibly_unused": [d["short_name"] or d["name"] for d in unused],
        "dangling_refs": [
            {"artifact": a, "artifact_type": t, "dep_uuid": u}
            for a, t, u in dangling_refs
        ],
    }

    mermaid = _make_mermaid(
        target_info["name"], direct_deps, transitive
    )

    # where-used / what-uses
    where_used = []
    what_uses = []
    if mode == "where-used" and toolkit_filter:
        tl = toolkit_filter.lower()
        for dep in direct_deps:
            # Match against both full name AND short name so the user can pass either
            if dep["name"].lower() == tl or dep["short_name"].lower() == tl:
                where_used.append({
                    "type": "declared_dependency",
                    "detail": f"snapshot={dep['snapshot_name']}, branch={dep['branch']}",
                })
        for sn, uses in artifact_refs.items():
            if sn.lower() == tl:
                for art_name, art_type, snippet in uses:
                    where_used.append({
                        "type": "artifact_reference",
                        "artifact": art_name,
                        "artifact_type": art_type,
                        "detail": snippet,
                    })
    elif mode == "what-uses":
        tl = toolkit_filter.lower() if toolkit_filter else ""
        what_uses = [
            d for d in direct_deps
            if not tl or d["name"].lower() == tl or d["short_name"].lower() == tl
        ]

    report = {
        "process_app": target_info,
        "analysis_mode": mode,
        "toolkit_filter": toolkit_filter,
        "direct_dependencies": direct_deps,
        "transitive_dependencies": {k: v for k, v in transitive.items()},
        "dependency_counts": {
            "direct": len(direct_deps),
            "transitive_resolved": sum(len(v) for v in transitive.values()),
        },
        "issues": issues,
        "artifact_toolkit_refs": {k: len(v) for k, v in artifact_refs.items()},
        "where_used": where_used,
        "what_uses": what_uses,
        "mermaid_diagram": mermaid,
    }

    # Build markdown
    app = target_info
    issue_count = len(cycles) + len(conflicts) + len(unused) + len(dangling_refs)
    md = []
    md.append("# BAW Toolkit Dependency & Usage Report\n\n")
    md.append(f"| Property | Details |\n")
    md.append(f"|---|---|\n")
    md.append(f"| **Process Application** | {app['name']} (`{app['short_name']}`) |\n")
    md.append(f"| **Snapshot** | `{app['snapshot_name']}` |\n")
    md.append(f"| **TWX Archive** | `{Path(twx_path).name}` |\n")
    md.append(f"| **Analysis Mode** | `{mode}` |\n\n")

    # 1. Summary
    md.append("## 1. Executive Summary\n\n")
    md.append(
        f"**{app['name']}** has **{len(direct_deps)} direct toolkit dependencies** and **{sum(len(v) for v in transitive.values())} resolved transitive dependencies**.\n\n"
    )
    if issue_count == 0:
        md.append("✅ **No dependency conflicts or issues were detected.** All dependencies are healthy.\n\n")
    else:
        md.append(f"⚠️ **{issue_count} issue(s) detected:**\n")
        if dangling_refs:
            seen_arts = {}
            for art_name, art_type, detail in dangling_refs:
                seen_arts.setdefault(art_name or art_type, detail)
            for art, detail in seen_arts.items():
                md.append(f"- **Dangling Reference (removed toolkit):** `{art}` contains a reference that cannot be resolved to any declared dependency ({detail}).\n")
        if conflicts:
            for c in conflicts:
                snaps = ", ".join(f"`{s}`" for s in c["snapshots"])
                md.append(f"- **Snapshot Conflict:** `{c['toolkit']}` is referenced at multiple conflicting versions: {snaps}.\n")
        if cycles:
            for cycle in cycles:
                md.append(f"- **Circular Dependency:** " + " → ".join(f"`{x}`" for x in cycle) + "\n")
        if unused:
            unused_list = ", ".join(f"`{u['short_name'] or u['name']}`" for u in unused)
            md.append(f"- **Unused (no references found):** {unused_list} have no direct artifact references. Verify in Process Designer before removing.\n")
        md.append("\n")

    # 2. Direct Dependencies Status
    md.append("## 2. Direct Dependencies Overview\n\n")
    md.append("| Toolkit Name | Acronym | Referenced Snapshot | Usage Status | Issues / Notes |\n")
    md.append("|---|:---:|:---:|:---:|---|\n")
    for dep in direct_deps:
        k = dep["short_name"] or dep["name"]
        issue_flags = []
        if any(c["toolkit"] == k for c in conflicts):
            issue_flags.append("⚠️ **Snapshot Conflict**")
        if dep in unused:
            usage_str = "🔍 *No direct refs*"
            issue_flags.append("Unused (no refs found — verify before removing)")
        else:
            usage_str = "✅ **In Use**"
        
        notes = ", ".join(issue_flags) if issue_flags else "Healthy"
        md.append(f"| **{dep['name']}** | `{dep['short_name']}` | `{dep['snapshot_name']}` | {usage_str} | {notes} |\n")
    md.append("\n")

    # 3. Artifact Usage Breakdown
    if mode == "full":
        md.append("## 3. Toolkit Usage Breakdown (Where Used in Process App)\n\n")
        has_usage = False
        for dep in direct_deps:
            k = dep["short_name"] or dep["name"]
            uses = artifact_refs.get(k, [])
            if uses:
                has_usage = True
                md.append(f"### 📦 {dep['name']} (`{dep['short_name']}`)\n\n")
                
                by_artifact = defaultdict(list)
                for art_name, art_type, snippet in uses:
                    display_name = art_name if art_name else "(unnamed artifact)"
                    by_artifact[(display_name, art_type)].append(snippet)
                
                md.append("| Where Used (Process App Item) | What It Uses from Toolkit |\n")
                md.append("|---|---|\n")
                for (art_name, art_type), snippets in by_artifact.items():
                    # If artifact name is same as type or generic filename, format neatly
                    if art_name == art_type:
                        location = f"**{art_name}**"
                    elif art_name.endswith(".zip"):
                        location = f"**Theme Asset** (`{art_name}`)"
                    else:
                        location = f"**{art_name}** <br><sub>Type: {art_type}</sub>"
                    
                    clean_snippets = "<br>".join(f"• {s}" for s in sorted(set(snippets)))
                    md.append(f"| {location} | {clean_snippets} |\n")
                md.append("\n")
        if not has_usage:
            md.append("*No direct artifact references detected for any declared toolkit.*\n\n")

    # 4. Dependency Graph
    md.append("## 4. Visual Dependency Graph\n\n```mermaid\n")
    md.append(mermaid)
    md.append("\n```\n\n")

    # 5. Transitive Dependencies
    if transitive:
        md.append("## 5. Transitive Dependencies (Resolved from Toolkit Zips)\n\n")
        md.append("| Provided By (Direct Toolkit) | Included Transitive Toolkit | Snapshot |\n")
        md.append("|---|---|:---:|\n")
        for parent, sub_deps in transitive.items():
            for sub in sub_deps:
                md.append(f"| `{parent}` | **{sub['name']}** (`{sub['short_name'] or '-'}`) | `{sub['snapshot_name']}` |\n")
        md.append("\n")

    # 6. Actionable Recommendations
    md.append("## 6. Recommendations & Action Items\n\n")
    if issue_count == 0:
        md.append("1. **Pre-deployment Check:** No changes required. The process application's toolkit dependencies are aligned and healthy.\n")
    else:
        rec_idx = 1
        if dangling_refs:
            seen_arts = list(dict.fromkeys(a for a, _, _ in dangling_refs))
            arts_str = ", ".join(f"`{a}`" for a in seen_arts)
            md.append(f"{rec_idx}. **Remove dangling toolkit references:** {arts_str} contain references to a toolkit that is no longer declared as a dependency. Open each artifact in Process Designer, locate and remove or reassign the reference, then re-export the TWX.\n")
            rec_idx += 1
        if conflicts:
            for c in conflicts:
                md.append(f"{rec_idx}. **Align `{c['toolkit']}` Snapshot:** Resolve conflicting versions ({', '.join(f'`{s}`' for s in c['snapshots'])}) by updating either the process application or child toolkits to target the latest unified snapshot.\n")
                rec_idx += 1
        if unused:
            unused_names = ", ".join(f"`{u['name']}`" for u in unused)
            md.append(f"{rec_idx}. **Remove Unused Toolkits (no references found):** No artifact in this process app references {unused_names}. Verify in Process Designer, then remove the dependency to reduce archive size and avoid transitive dependency bloat.\n")
            rec_idx += 1
    md.append("\n")

    # where-used / what-uses sections
    if mode == "where-used" and toolkit_filter:
        md.append(f"## Where Used: `{toolkit_filter}`\n\n")
        if not where_used:
            md.append(f"No references to `{toolkit_filter}` found in this TWX.\n\n")
        else:
            for r in where_used:
                if r["type"] == "declared_dependency":
                    md.append(f"- **Declared dependency** — {r['detail']}\n")
                else:
                    md.append(
                        f"- **Artifact reference** in `{r['artifact']}` "
                        f"({r.get('artifact_type', '')}) — `{r['detail']}`\n"
                    )
            md.append("\n")

    if mode == "what-uses":
        md.append("## What This App Uses\n\n")
        if not what_uses:
            md.append("No toolkit dependencies found.\n\n")
        else:
            for dep in what_uses:
                md.append(
                    f"- `{dep['short_name'] or dep['name']}` — "
                    f"snapshot: `{dep['snapshot_name']}`\n"
                )
            md.append("\n")

    return report, "".join(md)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _default_output_dir(twx_path: str) -> str:
    return twx_path + " - reports"


def _write_outputs(output_dir: str, report: dict, md: str):
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "toolkit-dependency-report.json")
    md_path = os.path.join(output_dir, "toolkit-dependency-report.md")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    return json_path, md_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="BAW Toolkit Dependency Analyzer")
    parser.add_argument("twx_path", help="Path to the .twx file")
    parser.add_argument("--list-toolkits", action="store_true",
                        help="List all toolkits declared in the TWX and exit")
    parser.add_argument("--mode", choices=["full", "where-used", "what-uses"],
                        default="full", help="Analysis mode (default: full)")
    parser.add_argument("--toolkit", default="",
                        help="Toolkit name/short-name for where-used / what-uses")
    parser.add_argument("--output-dir", default="",
                        help="Override the default output directory")
    args = parser.parse_args()

    if not os.path.isfile(args.twx_path):
        print(f"ERROR: File not found: {args.twx_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with zipfile.ZipFile(args.twx_path, "r") as zf:
            pkg_root = _parse_package_xml(zf)
            target_info = _extract_target_info(pkg_root)
            direct_deps = _extract_direct_deps(pkg_root)

            if args.list_toolkits:
                if direct_deps:
                    for d in direct_deps:
                        print(f"{d['name']} ({d['short_name']})  snapshot: {d['snapshot_name']}")
                else:
                    print("No toolkit dependencies found in this TWX.")
                sys.exit(0)

            artifact_refs, dangling_refs = _scan_objects_for_toolkit_refs(zf, direct_deps)

    except zipfile.BadZipFile:
        print(f"ERROR: Not a valid ZIP/TWX file: {args.twx_path}", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"ERROR: Missing expected file in TWX archive: {e}", file=sys.stderr)
        sys.exit(1)

    # Load transitive deps from embedded toolkit zips (outside the with block
    # is fine — we re-open to read the nested zips)
    transitive = _load_embedded_toolkit_deps(args.twx_path, direct_deps)

    report, md = _build_report(
        twx_path=args.twx_path,
        mode=args.mode,
        toolkit_filter=args.toolkit,
        target_info=target_info,
        direct_deps=direct_deps,
        transitive=transitive,
        artifact_refs=artifact_refs,
        dangling_refs=dangling_refs,
    )

    output_dir = args.output_dir or _default_output_dir(args.twx_path)
    json_path, md_path = _write_outputs(output_dir, report, md)

    print(f"Report written to:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")


if __name__ == "__main__":
    main()
