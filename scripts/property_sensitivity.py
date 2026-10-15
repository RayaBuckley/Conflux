"""Retain the property-sensitivity classification of the defence model IRs.

Every holding invariant in ``defence_models.py`` is classified against the
declared mutation alphabet in ``conflux.verification.sensitivity`` (one rule at
a time, guard replaced by ``True``).  The classification is retained next to the
evidence bundle it qualifies, so a claim surface can cite in-repo data instead
of an unretained measurement.

Usage::

    python scripts/property_sensitivity.py
    python scripts/property_sensitivity.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from conflux.verification.defence_models import (
    camel_ir,
    camel_native_property_ir,
    camelot_ir,
    camelot_native_property_ir,
    dual_llm_baseline_ir,
    dual_llm_native_property_ir,
    fides_ir,
    fides_native_property_ir,
    ites_defective_requester_only_ir,
    ites_native_property_ir,
    ites_reference_ir,
    ites_with_read_check_ir,
    pace_ir,
    pace_native_property_ir,
    pact_ir,
    pact_native_property_ir,
    progent_ir,
    progent_native_property_ir,
)
from conflux.verification.sensitivity import classification_document

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "output" / "runs" / "defence-models-v1"

IR_FACTORIES = {
    "dual_llm_pe": dual_llm_baseline_ir,
    "dual_llm_native_property": dual_llm_native_property_ir,
    "camel_pe": camel_ir,
    "camel_native_property": camel_native_property_ir,
    "progent_pe": progent_ir,
    "progent_native_property": progent_native_property_ir,
    "pact_pe": pact_ir,
    "pact_native_property": pact_native_property_ir,
    "ites_pe": ites_reference_ir,
    "ites_native_property": ites_native_property_ir,
    "ites_requester_only": ites_defective_requester_only_ir,
    "ites_with_read_check": ites_with_read_check_ir,
    "camelot_pe": camelot_ir,
    "camelot_native_property": camelot_native_property_ir,
    "fides_pe": fides_ir,
    "fides_native_property": fides_native_property_ir,
    "pace_pe": pace_ir,
    "pace_native_property": pace_native_property_ir,
}


def build() -> dict[str, Any]:
    """Return the classification document for every defence model IR."""
    return classification_document({name: factory() for name, factory in IR_FACTORIES.items()})


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_bundle(output: Path, document: dict[str, Any]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, indent=2, sort_keys=True) + "\n"
    data = payload.encode("utf-8")
    (output / "sensitivity.json").write_bytes(data)
    (output / "SENSITIVITY_CHECKSUMS.sha256").write_text(
        f"{_sha256(data)}  sensitivity.json\n", encoding="utf-8", newline="\n",
    )


def _check(output: Path) -> bool:
    path = output / "sensitivity.json"
    if not path.is_file():
        return False
    regenerated = json.dumps(build(), indent=2, sort_keys=True).encode("utf-8") + b"\n"
    return path.read_bytes() == regenerated


def main() -> int:
    parser = argparse.ArgumentParser(description="Retain the defence-model property-sensitivity classification.")
    parser.add_argument("--check", action="store_true", help="Verify the retained classification matches regeneration.")
    arguments = parser.parse_args()

    if arguments.check:
        if _check(OUTPUT):
            print("Property sensitivity regeneration check passed")
            return 0
        print("Property sensitivity artifact is stale or missing", file=sys.stderr)
        return 1

    _write_bundle(OUTPUT, build())
    print(f"Generated property sensitivity classification: {OUTPUT / 'sensitivity.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
