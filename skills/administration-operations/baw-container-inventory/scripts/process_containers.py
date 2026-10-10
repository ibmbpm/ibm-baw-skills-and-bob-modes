#!/usr/bin/env python3
"""
process_containers.py

Reads the raw JSON response from GET /ops/std/bpm/containers (one or more
page files) and outputs formatted Markdown tables and/or a count summary.

Usage:
    python3 process_containers.py <file> [<file2> ...] [--mode MODE]

    Where each <file> is a saved API response:
        {"containers": [...], "next": ..., ...}

    Pass all page files as arguments — the script merges them automatically.

Modes:
    list   (default) Two tables (Process Apps, Toolkits) + count summary
    count  Count summary line only — no tables
    pa     Process Apps table + PA count
    tk     Toolkits table + TK count
"""

import json
import sys
import argparse


def load_containers(paths):
    containers = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, list):
            containers.extend(raw)
        elif isinstance(raw, dict) and "containers" in raw:
            containers.extend(raw["containers"])
        else:
            raise ValueError(
                f"{path}: unrecognised format. Expected a containers API response object."
            )
    return containers


def name_for(c):
    name = c.get("container_name") or c.get("container") or "(unknown)"
    if c.get("archived"):
        name = f"{name} (Archived)"
    return name


def acronym_for(c):
    return c.get("container") or ""


def render_table(containers, heading):
    lines = [f"### {heading}", ""]
    lines.append("| Name | Acronym |")
    lines.append("|------|---------|")
    for c in sorted(containers, key=lambda x: (x.get("container_name") or "").lower()):
        lines.append(f"| {name_for(c)} | {acronym_for(c)} |")
    lines.append("")
    return "\n".join(lines)


def render_count_summary(pa_count, tk_count):
    total = pa_count + tk_count
    return f"{pa_count} Process Apps, {tk_count} Toolkits ({total} total)"


def main():
    parser = argparse.ArgumentParser(description="Format BAW container inventory")
    parser.add_argument("inputs", nargs="+", help="Path(s) to JSON response file(s)")
    parser.add_argument(
        "--mode",
        choices=["list", "count", "pa", "tk"],
        default="list",
        help="Output mode (default: list)",
    )
    args = parser.parse_args()

    try:
        containers = load_containers(args.inputs)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    process_apps = [c for c in containers if not c.get("toolkit")]
    toolkits = [c for c in containers if c.get("toolkit")]

    pa_count = len(process_apps)
    tk_count = len(toolkits)

    if args.mode == "count":
        print(render_count_summary(pa_count, tk_count))

    elif args.mode == "pa":
        print(render_table(process_apps, "Process Apps"))
        print(f"**{pa_count} Process Apps**")

    elif args.mode == "tk":
        print(render_table(toolkits, "Toolkits"))
        print(f"**{tk_count} Toolkits**")

    else:  # list (default)
        print(render_table(process_apps, "Process Apps"))
        print(render_table(toolkits, "Toolkits"))
        print(render_count_summary(pa_count, tk_count))


if __name__ == "__main__":
    main()
