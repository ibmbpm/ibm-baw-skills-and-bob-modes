#!/usr/bin/env python3
"""
Package BAW widgets (and optional business objects) into an importable .twx toolkit.

Run this from the BAW project root — it expects:
  - widgets/              — widget folders built by Bob (one subdirectory per widget)
  - toolkit.config.json  — toolkit name, version, bawVersion (copy from assets/toolkit.config.json)
  - templates/BaseTWX/   — BAW base template (copy from assets/templates/BaseTWX/)
  - toolkit_packager/    — TWX build library (already in this scripts/ folder)

Usage:
    python3 scripts/package_baw.py

The script:
  1. Auto-increments the patch version in toolkit.config.json
  2. Auto-discovers every widget subfolder inside widgets/
  3. Builds the TWX and writes it to output/{ToolkitName}_{version}.twx
  4. Prints the output path — import that file into BAW via
     Process Admin Console → Toolkits → Import

No manual widget list to maintain — just drop a widget folder and re-run.
"""

import sys
import logging
import argparse
from pathlib import Path

# The toolkit_packager library must be on the Python path.
# When running from the project root as `python3 scripts/package_baw.py`,
# add scripts/ to sys.path so the import resolves correctly.
sys.path.insert(0, str(Path(__file__).parent))

from toolkit_packager import (
    load_config,
    scan_project,
    TWXBuilder,
    setup_logger,
    get_logger,
)
from toolkit_packager.utils import increment_toolkit_version

# ── Paths (relative to this script's location inside the skill) ──────────────
_SKILL_ROOT = Path(__file__).parent.parent          # src/skills/create-baw-widget/
WIDGETS_DIR = _SKILL_ROOT / "widgets"
OUTPUT_DIR  = _SKILL_ROOT / "output"
CONFIG_FILE = _SKILL_ROOT / "assets" / "toolkit.config.json"

# Setup logging
setup_logger(level=logging.INFO)
logger = get_logger(__name__)


def discover_widget_names(widgets_dir: Path) -> list:
    """Return sorted list of widget names from subdirectories of widgets_dir."""
    if not widgets_dir.exists():
        return []
    return sorted(
        d.name for d in widgets_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )


def main():
    """Package BAW widgets into a TWX toolkit file."""
    try:
        widget_names = discover_widget_names(WIDGETS_DIR)

        logger.info(f"Packaging BAW Toolkit — {len(widget_names)} widget(s) discovered")
        logger.info(f"   Widgets: {', '.join(widget_names) if widget_names else '(none found)'}")
        print("=" * 70)

        if not widget_names:
            logger.error(f"No widget folders found in {WIDGETS_DIR}. Add at least one widget first.")
            return None

        # Step 1 — auto-increment version
        logger.info("Auto-incrementing toolkit version...")
        old_version, new_version = increment_toolkit_version(CONFIG_FILE, increment_type="patch")
        logger.info(f"Version: {old_version} -> {new_version}")

        # Step 2 — load config
        logger.info("Loading toolkit.config.json...")
        config = load_config(CONFIG_FILE)
        logger.info(f"Toolkit: {config.name} v{config.version}")
        logger.info(f"BAW template: {config.baw_version}")

        # Step 3 — validate template exists
        template_dir = _SKILL_ROOT / "assets" / "templates" / "BaseTWX" / config.baw_version
        if not template_dir.exists():
            base = _SKILL_ROOT / "assets" / "templates" / "BaseTWX"
            available = [d.name for d in base.iterdir() if d.is_dir()] if base.exists() else []
            logger.error(f"Template directory not found: {template_dir}")
            if available:
                logger.error(f"   Available versions: {', '.join(available)}")
            logger.error(f"   Update 'bawVersion' in assets/toolkit.config.json to match.")
            return None

        # Step 4 — scan and match widgets
        logger.info(f"Scanning {WIDGETS_DIR}...")
        all_widgets = scan_project(WIDGETS_DIR)
        logger.info(f"Found {len(all_widgets)} widget folder(s)")

        target_widgets = []
        for name in widget_names:
            w = next((x for x in all_widgets if x.name == name), None)
            if w:
                target_widgets.append(w)
                logger.info(f"  + {w.name}")
            else:
                logger.warning(f"  ? Widget '{name}' folder found but could not be loaded — skipping")

        if not target_widgets:
            logger.error("No widgets could be loaded. Check the widgets/ directory structure.")
            return None

        # Step 5 — build TWX
        logger.info(f"Building TWX for {len(target_widgets)} widget(s)...")
        builder = TWXBuilder(config=config, output_dir=OUTPUT_DIR, template_dir=template_dir)
        for w in target_widgets:
            builder.add_widget(w)

        output_path = builder.build()

        # Done
        print("\n" + "=" * 70)
        logger.info(f"TWX created: {output_path}")
        logger.info(f"Size:        {output_path.stat().st_size / 1024:.1f} KB")
        logger.info(f"Widgets:     {', '.join(w.name for w in target_widgets)}")
        logger.info(f"Import via:  BAW Process Admin Console -> Toolkits -> Import")
        print("=" * 70)

        return output_path

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return None
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Package BAW widgets into a .twx toolkit file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/package_baw.py

Prerequisites:
  - widgets/ directory containing at least one widget subfolder
  - toolkit.config.json in assets/
  - templates/BaseTWX/{bawVersion}/ in assets/
        """
    )
    parser.parse_args()

    _discovered = discover_widget_names(WIDGETS_DIR)
    print("\n" + "=" * 70)
    print("BAW Toolkit Packager")
    print(f"Widgets:  {len(_discovered)} discovered")
    print(f"Config:   toolkit.config.json")
    print("=" * 70 + "\n")

    result = main()
    sys.exit(0 if result else 1)

# Made with Bob
