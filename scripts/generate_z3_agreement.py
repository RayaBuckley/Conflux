"""Generate Z3 checker agreement evidence for COI fixtures.

Runs Z3 BMC on the two original COI fixtures and their reduced
counterparts, retaining a deterministic JSON evidence bundle.

Usage::

    python scripts/generate_z3_agreement.py
    python scripts/generate_z3_agreement.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from conflux.verification.ir import VerificationIR
from conflux.verification.reduction import compare_cone_of_influence
from conflux.verification.z3_backend import verify_with_z3

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "output" / "runs" / "z3-agreement-v1"
SUITES = ROOT / "research" / "experiments" / "suites" / "sled-coi-v1"


def _verify(ir: VerificationIR) -> dict[str, Any]:
    result = verify_with_z3(ir)
    return {
        "verdict": result.verdict.value,
        "counterexample": result.counterexample is not None,
        "counterexample_length": len(result.counterexample) if result.counterexample else 0,
    }


def generate() -> dict[str, Any]:
    """Generate Z3 agreement evidence for all COI fixtures."""
    fixtures: list[dict[str, Any]] = []
    for fixture_path in sorted(SUITES.glob("*.json")):
        ir = VerificationIR.from_dict(json.loads(fixture_path.read_text()))
        comp = compare_cone_of_influence(ir, ())
        fixtures.append(
            {
                "fixture_id": ir.id,
                "reference_verdict": comp.original.verdict.value,
                "reduced_verdict": comp.reduced.verdict.value,
                "equivalent": comp.equivalent,
                "z3_original": _verify(ir),
                "z3_reduced": _verify(comp.reduction.reduced_ir),
            },
        )
    return {
        "schema_version": "1",
        "id": "z3-agreement-v1",
        "fixtures": fixtures,
        "summary": {
            "total_fixtures": len(fixtures),
            "all_agree": all(
                f["z3_original"]["verdict"] == f["z3_reduced"]["verdict"] and f["z3_original"]["verdict"] == f["reference_verdict"]
                for f in fixtures
            ),
        },
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_bundle(output: Path, bundle: dict[str, Any]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(bundle, indent=2, sort_keys=True) + "\n"
    data = payload.encode("utf-8")
    (output / "result.json").write_bytes(data)
    (output / "CHECKSUMS.sha256").write_text(f"{_sha256(data)}  result.json\n", encoding="utf-8", newline="\n")


def _check(output: Path) -> bool:
    result_path = output / "result.json"
    if not result_path.is_file():
        return False
    retained = result_path.read_bytes()
    regenerated = json.dumps(generate(), indent=2, sort_keys=True).encode("utf-8") + b"\n"
    return retained == regenerated


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Z3 checker agreement evidence for COI fixtures.")
    parser.add_argument("--check", action="store_true", help="Verify retained bundle matches regeneration.")
    arguments = parser.parse_args()

    if arguments.check:
        if _check(OUTPUT):
            print("Z3 agreement evidence regeneration check passed")
            return 0
        print("Z3 agreement evidence is stale or missing", file=sys.stderr)
        return 1

    bundle = generate()
    _write_bundle(OUTPUT, bundle)
    print(f"Generated Z3 agreement evidence: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
