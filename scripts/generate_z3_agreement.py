"""Generate Z3 checker agreement evidence for COI fixtures.

Runs Z3 BMC on the two original COI fixtures and their reduced
counterparts, retaining a deterministic JSON evidence bundle.

``all_agree`` compares verdict classes, so the bounded model checker's
``bounded_safe`` agrees with the reference interpreter's ``safe`` while the raw
strings are kept per fixture and summarised separately in
``raw_verdict_agreement``.  With no solver installed nothing is measured and
``all_agree`` is ``null``: an unmeasured flag must never claim agreement.

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
from conflux.verification.results import FormalVerdict
from conflux.verification.z3_backend import verify_with_z3

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "output" / "runs" / "z3-agreement-v1"
SUITES = ROOT / "research" / "experiments" / "suites" / "sled-coi-v1"


SAFE_FAMILY = frozenset({"safe", "bounded_safe"})
"""Verdicts that mean "no violation found within the stated bounds".

The reference interpreter reports ``safe`` and the bounded model checker reports
``bounded_safe``: same class, different scope of guarantee. The raw strings are
retained in every fixture so the two are never conflated in the artefact itself.
"""


def verdict_class(verdict: str) -> str:
    """Map a verdict onto its class for cross-backend comparison."""
    return "safe" if verdict in SAFE_FAMILY else verdict


def _verify(ir: VerificationIR) -> dict[str, Any]:
    result = verify_with_z3(ir)
    counterexample = result.counterexample or ()
    return {
        "verdict": result.verdict.value,
        "measured": result.verdict is not FormalVerdict.UNKNOWN,
        "counterexample": bool(counterexample),
        "counterexample_length": len(counterexample),
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
    measured = [f for f in fixtures if f["z3_original"]["measured"] and f["z3_reduced"]["measured"]]
    agree = [
        f
        for f in measured
        if verdict_class(f["z3_original"]["verdict"])
        == verdict_class(f["z3_reduced"]["verdict"])
        == verdict_class(f["reference_verdict"])
    ]
    raw_agree = [
        f
        for f in measured
        if f["z3_original"]["verdict"] == f["z3_reduced"]["verdict"] == f["reference_verdict"]
    ]
    return {
        "schema_version": "1",
        "id": "z3-agreement-v1",
        "fixtures": fixtures,
        "summary": {
            "total_fixtures": len(fixtures),
            "z3_measured": len(measured),
            "all_agree": (len(agree) == len(measured)) if measured else None,
            "raw_verdict_agreement": (len(raw_agree) == len(measured)) if measured else None,
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
