"""Generate COI scaling evidence: parameterized noise-variable fixtures.

Creates safe-noise-N and unsafe-control-N fixtures for N = 0, 1, 2, 4, 8, 16,
runs COI reduction and Z3 BMC on each, and retains a deterministic JSON
evidence bundle at ``research/output/runs/coi-scaling-v1/``.

Usage::

    python scripts/generate_coi_scaling.py
    python scripts/generate_coi_scaling.py --check
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
OUTPUT = ROOT / "research" / "output" / "runs" / "coi-scaling-v1"

NOISE_COUNTS = (0, 1, 2, 4, 8, 16)


def _safe_noise_fixture(n: int) -> dict[str, Any]:
    """A safe fixture with N independent boolean noise variables."""
    variables: list[dict[str, Any]] = [{"name": "safe", "sort": "boolean", "initial": True, "minimum": None, "maximum": None}]
    transitions: list[dict[str, Any]] = []
    for i in range(n):
        variables.append({"name": f"noise{i}", "sort": "boolean", "initial": False, "minimum": None, "maximum": None})
        transitions.append(
            {
                "id": f"toggle-noise{i}",
                "guard": {"kind": "constant", "value": True, "arguments": []},
                "assignments": [
                    {
                        "variable": f"noise{i}",
                        "expression": {
                            "kind": "not",
                            "value": None,
                            "arguments": [{"kind": "variable", "value": f"noise{i}", "arguments": []}],
                        },
                    },
                ],
            },
        )
    return {
        "schema_version": "1",
        "id": f"safe-noise-{n}",
        "bound": n + 1 if n > 0 else 4,
        "assumptions": [f"{n} noise variables are independent of the safety invariant"],
        "variables": variables,
        "transitions": transitions,
        "invariants": [
            {
                "id": "safe-remains-true",
                "expression": {"kind": "variable", "value": "safe", "arguments": []},
                "description": "Independent noise cannot falsify the safety bit.",
            },
        ],
    }


def _unsafe_control_fixture(n: int) -> dict[str, Any]:
    """An unsafe fixture with a control bit and N noise variables."""
    variables: list[dict[str, Any]] = [
        {"name": "safe", "sort": "boolean", "initial": True, "minimum": None, "maximum": None},
        {"name": "control", "sort": "boolean", "initial": True, "minimum": None, "maximum": None},
    ]
    transitions: list[dict[str, Any]] = [
        {
            "id": "apply-control",
            "guard": {"kind": "constant", "value": True, "arguments": []},
            "assignments": [
                {
                    "variable": "safe",
                    "expression": {
                        "kind": "not",
                        "value": None,
                        "arguments": [{"kind": "variable", "value": "control", "arguments": []}],
                    },
                },
            ],
        },
    ]
    for i in range(n):
        variables.append({"name": f"noise{i}", "sort": "boolean", "initial": False, "minimum": None, "maximum": None})
        transitions.append(
            {
                "id": f"toggle-noise{i}",
                "guard": {"kind": "constant", "value": True, "arguments": []},
                "assignments": [
                    {
                        "variable": f"noise{i}",
                        "expression": {
                            "kind": "not",
                            "value": None,
                            "arguments": [{"kind": "variable", "value": f"noise{i}", "arguments": []}],
                        },
                    },
                ],
            },
        )
    return {
        "schema_version": "1",
        "id": f"unsafe-control-{n}",
        "bound": n + 2 if n > 0 else 4,
        "assumptions": [f"{n} noise variables are independent of the control/safety bits"],
        "variables": variables,
        "transitions": transitions,
        "invariants": [
            {
                "id": "safe-remains-true",
                "expression": {"kind": "variable", "value": "safe", "arguments": []},
                "description": "The unsafe control transition must produce a witness.",
            },
        ],
    }


def _run_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    """Run COI reduction and Z3 on a fixture and return measurements."""
    ir = VerificationIR.from_dict(fixture)
    comp = compare_cone_of_influence(ir, ())
    z3_orig = verify_with_z3(ir)
    z3_red = verify_with_z3(comp.reduction.reduced_ir)
    orig_metrics = {
        "variables": len(ir.variables),
        "rules": len(ir.transitions),
        "states": comp.original.states,
    }
    red_metrics = {
        "variables": len(comp.reduction.reduced_ir.variables),
        "rules": len(comp.reduction.reduced_ir.transitions),
        "states": comp.reduced.states,
    }
    return {
        "fixture_id": fixture["id"],
        "noise_variables": fixture.get("bound", 4) - 2 if "control" in fixture["id"] else fixture.get("bound", 4) - 1,
        "original": orig_metrics,
        "reduced": red_metrics,
        "reference": {
            "original_verdict": comp.original.verdict.value,
            "reduced_verdict": comp.reduced.verdict.value,
            "equivalent": comp.equivalent,
        },
        "z3": {
            "original_verdict": z3_orig.verdict.value,
            "reduced_verdict": z3_red.verdict.value,
        },
        "witness_length": len(comp.reduced.counterexample) if comp.reduced.counterexample else 0,
    }


def generate() -> dict[str, Any]:
    """Generate the full scaling evidence bundle."""
    rows: list[dict[str, Any]] = []
    for n in NOISE_COUNTS:
        safe_fixture = _safe_noise_fixture(n)
        rows.append(_run_fixture(safe_fixture))
    for n in NOISE_COUNTS:
        unsafe_fixture = _unsafe_control_fixture(n)
        rows.append(_run_fixture(unsafe_fixture))
    return {
        "schema_version": "1",
        "id": "coi-scaling-v1",
        "noise_counts": list(NOISE_COUNTS),
        "fixtures": rows,
        "summary": {
            "total_fixtures": len(rows),
            "all_equivalent": all(r["reference"]["equivalent"] for r in rows),
            "z3_all_agree": all(r["z3"]["original_verdict"] == r["z3"]["reduced_verdict"] for r in rows),
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
    parser = argparse.ArgumentParser(description="Generate COI scaling evidence from parameterized fixtures.")
    parser.add_argument("--check", action="store_true", help="Verify retained bundle matches regeneration.")
    arguments = parser.parse_args()

    if arguments.check:
        if _check(OUTPUT):
            print("COI scaling evidence regeneration check passed")
            return 0
        print("COI scaling evidence is stale or missing", file=sys.stderr)
        return 1

    bundle = generate()
    _write_bundle(OUTPUT, bundle)
    print(f"Generated COI scaling evidence: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
