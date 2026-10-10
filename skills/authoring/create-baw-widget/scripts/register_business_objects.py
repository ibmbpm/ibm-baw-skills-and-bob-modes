#!/usr/bin/env python3
"""
Register business object JSON files with stable BAW class IDs before packaging.

Run this from the BAW project root whenever you add or modify business object
JSON files under widgets/*/widget/*.json or business-objects/generated/.

The script is idempotent — running it multiple times will reuse existing class IDs
and only register new files. Class IDs are written to:
  toolkit_packager/baw_custom_types.json

Business objects must follow the required format (packaging will fail otherwise):
  {
    "type": "BusinessObjectName",   <-- MUST be "type", NOT "name"
    "description": "...",
    "properties": [
      { "name": "...", "type": "String|Integer|Decimal|Boolean|Date",
        "required": true|false, "description": "..." }
    ]
  }

Usage:
    python3 scripts/register_business_objects.py
"""

import sys
import logging
from pathlib import Path

# Add scripts/ to path so toolkit_packager resolves when running from project root.
sys.path.insert(0, str(Path(__file__).parent))

from toolkit_packager import (
    scan_business_objects,
    get_processing_order,
    get_or_create_class_id,
    load_custom_types_registry,
    save_custom_types_registry,
    setup_logger,
    get_logger,
)

# ── Paths (relative to this script's location inside the skill) ──────────────
_SKILL_ROOT           = Path(__file__).parent.parent   # src/skills/create-baw-widget/
PROJECT_ROOT          = _SKILL_ROOT
BUSINESS_OBJECTS_DIR  = _SKILL_ROOT / "widgets"
REGISTRY_PATH         = _SKILL_ROOT / "scripts" / "toolkit_packager" / "baw_custom_types.json"

setup_logger(level=logging.INFO)
logger = get_logger(__name__)


def main():
    """Scan and register all business objects with stable BAW class IDs."""
    try:
        logger.info("=" * 70)
        logger.info("📦 Business Object Registration")
        logger.info("=" * 70)

        logger.info(f"🔍 Scanning: {BUSINESS_OBJECTS_DIR}")
        business_objects = scan_business_objects(PROJECT_ROOT)

        if not business_objects:
            logger.info("ℹ️  No business objects found — nothing to register.")
            logger.info("   Place .json files in business-objects/generated/ or widgets/*/widget/")
            return

        logger.info(f"✓ Found {len(business_objects)} business object(s)")

        logger.info("\n📊 Resolving dependency order...")
        ordered_bos = get_processing_order(business_objects)

        logger.info(f"\n📄 Loading registry: {REGISTRY_PATH}")
        registry = load_custom_types_registry(REGISTRY_PATH)
        existing_count = len(registry.get("custom_types", {}))
        logger.info(f"✓ {existing_count} type(s) already registered")

        logger.info("\n🔨 Registering...")
        new_count = 0
        already_count = 0

        for bo in ordered_bos:
            context = bo.path.parent.name
            class_id = get_or_create_class_id(REGISTRY_PATH, bo.name, bo.description, context)

            if bo.name not in registry.get("custom_types", {}):
                new_count += 1
                logger.info(f"  ✓ NEW  {bo.name}  classId={class_id}  context={context}")
            else:
                already_count += 1
                logger.info(f"  ↻ KEEP {bo.name}  classId={class_id}")

        final = load_custom_types_registry(REGISTRY_PATH)
        final_count = len(final.get("custom_types", {}))

        logger.info("\n" + "=" * 70)
        logger.info(f"✅ Done — {new_count} new, {already_count} unchanged, {final_count} total")
        logger.info(f"   Registry: {REGISTRY_PATH}")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"❌ Registration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
