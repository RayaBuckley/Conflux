"""Validate every checked-in Conflux JSON Schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def main() -> int:
    errors: list[str] = []
    identifiers: set[str] = set()
    for path in sorted(SCHEMAS.glob("*.schema.json")):
        try:
            schema = cast(
                dict[str, object],
                json.loads(path.read_text(encoding="utf-8")),
            )
            Draft202012Validator.check_schema(schema)
            identifier = str(schema.get("$id", ""))
            if not identifier:
                errors.append(f"{path.name}: missing $id")
            elif identifier in identifiers:
                errors.append(f"{path.name}: duplicate $id {identifier}")
            identifiers.add(identifier)
        except (json.JSONDecodeError, TypeError) as error:
            errors.append(f"{path.name}: {error}")
    if not identifiers:
        errors.append("no JSON Schemas found")
    if errors:
        print("Schema validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"Validated {len(identifiers)} JSON Schemas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
