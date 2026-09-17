#!/usr/bin/env python3
"""
Lightweight validator for BAW Business Object import JSON files.

Checks structural rules required by the BAW WebPD BO importer:
  - Valid JSON
  - Required top-level keys (openapi, info, components)
  - openapi version is "3.0.3"
  - components.schemas exists and is non-empty
  - Each schema has type: object and a properties key
  - All $ref values point to schemas that exist in the file
  - No disallowed top-level keys (paths, servers, security, etc.)
  - Schema names are PascalCase
  - Property names are camelCase

Usage:
    python validate_bo_json.py <path-to-bo-import.json>

Exit code 0 = valid, 1 = invalid (errors printed to stdout).
"""

import json
import re
import sys
from pathlib import Path


REQUIRED_TOP_LEVEL = {"openapi", "info", "components"}
DISALLOWED_TOP_LEVEL = {"paths", "servers", "security", "securitySchemes", "tags", "externalDocs"}
VALID_PRIMITIVE_TYPES = {"string", "integer", "number", "boolean", "array"}
PASCAL_RE = re.compile(r'^[A-Z][A-Za-z0-9]*$')
CAMEL_RE = re.compile(r'^[a-z][A-Za-z0-9]*$')


def validate(data: dict) -> list[str]:
    errors = []

    # Top-level required keys
    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"Missing required top-level key: '{key}'")

    # Disallowed keys
    found_disallowed = DISALLOWED_TOP_LEVEL & set(data.keys())
    if found_disallowed:
        errors.append(
            f"Disallowed top-level key(s) found: {sorted(found_disallowed)}. "
            "BAW's BO importer ignores these; remove them to keep the file clean."
        )

    # openapi version
    openapi_ver = data.get("openapi")
    if openapi_ver is not None and openapi_ver != "3.0.3":
        errors.append(
            f"'openapi' must be the string \"3.0.3\", got {json.dumps(openapi_ver)}."
        )

    # info required keys
    info = data.get("info", {})
    if not isinstance(info, dict):
        errors.append("'info' must be an object.")
    else:
        for key in ("title", "version"):
            if key not in info:
                errors.append(f"'info.{key}' is required.")

    # components.schemas
    components = data.get("components", {})
    if not isinstance(components, dict):
        errors.append("'components' must be an object.")
        return errors  # can't continue

    schemas = components.get("schemas")
    if not schemas:
        errors.append("'components.schemas' is missing or empty — no BOs would be imported.")
        return errors

    if not isinstance(schemas, dict):
        errors.append("'components.schemas' must be an object.")
        return errors

    schema_names = set(schemas.keys())

    for schema_name, schema_def in schemas.items():
        prefix = f"Schema '{schema_name}'"

        # PascalCase check
        if not PASCAL_RE.match(schema_name):
            errors.append(
                f"{prefix}: name should be PascalCase (e.g. 'CustomerAddress'). "
                f"Got '{schema_name}'."
            )

        if not isinstance(schema_def, dict):
            errors.append(f"{prefix}: must be an object.")
            continue

        # type: object required
        if schema_def.get("type") != "object":
            errors.append(
                f"{prefix}: 'type' must be \"object\". Got {json.dumps(schema_def.get('type'))}."
            )

        # properties required
        props = schema_def.get("properties")
        if props is None:
            errors.append(f"{prefix}: missing 'properties' key.")
            continue

        if not isinstance(props, dict):
            errors.append(f"{prefix}: 'properties' must be an object.")
            continue

        for prop_name, prop_def in props.items():
            prop_prefix = f"{prefix}.properties.{prop_name}"

            # camelCase check
            if not CAMEL_RE.match(prop_name):
                errors.append(
                    f"{prop_prefix}: property name should be camelCase (e.g. 'totalAmount'). "
                    f"Got '{prop_name}'."
                )

            if not isinstance(prop_def, dict):
                errors.append(f"{prop_prefix}: must be an object.")
                continue

            # $ref handling
            if "$ref" in prop_def:
                ref = prop_def["$ref"]
                expected_prefix = "#/components/schemas/"
                if not ref.startswith(expected_prefix):
                    errors.append(
                        f"{prop_prefix}: '$ref' must start with "
                        f"'#/components/schemas/'. Got '{ref}'."
                    )
                else:
                    ref_name = ref[len(expected_prefix):]
                    if ref_name not in schema_names:
                        errors.append(
                            f"{prop_prefix}: '$ref' points to '{ref_name}', "
                            f"which is not defined in components.schemas."
                        )
                # $ref should be the only key (additional properties are ignored by BAW
                # but signal a misunderstanding of the format)
                extra_keys = set(prop_def.keys()) - {"$ref", "description"}
                if extra_keys:
                    errors.append(
                        f"{prop_prefix}: '$ref' fields should not have additional "
                        f"keywords alongside '$ref' (found: {sorted(extra_keys)}). "
                        "Move descriptions to the referenced schema."
                    )
                continue

            # array handling
            prop_type = prop_def.get("type")
            if prop_type == "array":
                items = prop_def.get("items")
                if not items:
                    errors.append(
                        f"{prop_prefix}: array fields must have an 'items' key."
                    )
                elif isinstance(items, dict) and "$ref" in items:
                    ref = items["$ref"]
                    expected_prefix = "#/components/schemas/"
                    if ref.startswith(expected_prefix):
                        ref_name = ref[len(expected_prefix):]
                        if ref_name not in schema_names:
                            errors.append(
                                f"{prop_prefix}.items: '$ref' points to '{ref_name}', "
                                f"which is not defined in components.schemas."
                            )
                    else:
                        errors.append(
                            f"{prop_prefix}.items: '$ref' must start with "
                            f"'#/components/schemas/'. Got '{ref}'."
                        )
                continue

            # primitive type check
            if prop_type is not None and prop_type not in VALID_PRIMITIVE_TYPES:
                errors.append(
                    f"{prop_prefix}: unsupported type '{prop_type}'. "
                    f"Supported types: {sorted(VALID_PRIMITIVE_TYPES)}."
                )

        # required array consistency
        required = schema_def.get("required", [])
        if not isinstance(required, list):
            errors.append(f"{prefix}: 'required' must be an array of strings.")
        else:
            for req_field in required:
                if req_field not in props:
                    errors.append(
                        f"{prefix}: field '{req_field}' is listed in 'required' "
                        f"but does not exist in 'properties'."
                    )

    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_bo_json.py <path-to-bo-import.json>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: file not found: {path}")
        sys.exit(1)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        sys.exit(1)

    errors = validate(data)

    if not errors:
        schemas = data.get("components", {}).get("schemas", {})
        print(f"✓ Valid BAW BO import file. {len(schemas)} schema(s): {', '.join(schemas.keys())}")
        sys.exit(0)
    else:
        print(f"✗ Found {len(errors)} issue(s):\n")
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
