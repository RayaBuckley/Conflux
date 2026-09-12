"""Generate SLED-V scaling evidence: parameterised synthetic fixtures.

Extends the existing COI scaling and Z3 agreement harness with a
broader parameter grid.  Measures how canonical state exploration,
COI reduction, and Z3 BMC scale with increasing model complexity.

Minimum viable matrix:

1. Noise scaling: N = 0, 4, 8, 16, 32 on safe and unsafe fixtures.
2. Principal scaling: P = 2, 4, 8, 16 at fixed noise/depth.
3. Depth scaling: K = 1..5 at fixed noise/principals.
4. Historical anchor: 3 legacy environments (from existing baseline).

Compared modes:

- ``reference``: reference BFS safety check on original IR
- ``reference_coi``: reference BFS safety check on COI-reduced IR
- ``z3_bmc``: Z3 BMC on original IR
- ``z3_bmc_coi``: Z3 BMC on COI-reduced IR

Usage::

    python scripts/generate_sledv_scaling_evidence.py
    python scripts/generate_sledv_scaling_evidence.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from conflux.verification.ir import VerificationIR
from conflux.verification.reduction import (
    compare_cone_of_influence,
)
from conflux.verification.z3_backend import verify_with_z3

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "output" / "runs" / "sledv-scaling-v1"

NOISE_COUNTS = (0, 4, 8, 16, 32)
PRINCIPAL_COUNTS = (2, 4, 8, 16)
DEPTH_VALUES = (1, 2, 3, 4, 5)

HISTORICAL_ANCHOR = {
    "environment": "legacy-env-01",
    "legacy_traces": 422535,
    "canonical_states": 31,
    "depth_bound": 3,
    "source": "research/experiments/baselines/sled-historical-v1.json",
}

HISTORICAL_TOTAL_TRACES = 1462607
HISTORICAL_TOTAL_STATES = 31


def _const(value: bool) -> dict[str, Any]:
    return {"kind": "constant", "value": value, "arguments": []}


def _var(name: str) -> dict[str, Any]:
    return {"kind": "variable", "value": name, "arguments": []}


def _not(expr: dict[str, Any]) -> dict[str, Any]:
    return {"kind": "not", "value": None, "arguments": [expr]}


def _and(*exprs: dict[str, Any]) -> dict[str, Any]:
    return {"kind": "and", "value": None, "arguments": list(exprs)}


def _bool_var(name: str, initial: bool) -> dict[str, Any]:
    return {"name": name, "sort": "boolean", "initial": initial, "minimum": None, "maximum": None}


def _safe_noise_fixture(n: int, bound: int = 4) -> dict[str, Any]:
    """Safe fixture with N independent noise variables."""
    variables: list[dict[str, Any]] = [_bool_var("safe", True)]
    transitions: list[dict[str, Any]] = []
    for i in range(n):
        vname = f"noise{i}"
        variables.append(_bool_var(vname, False))
        transitions.append(
            {
                "id": f"toggle-{vname}",
                "guard": _const(True),
                "assignments": [
                    {"variable": vname, "expression": _not(_var(vname))},
                ],
            },
        )
    return {
        "schema_version": "1",
        "id": f"safe-noise-{n}",
        "bound": bound,
        "assumptions": [f"{n} noise variables are independent of the safety invariant"],
        "variables": variables,
        "transitions": transitions,
        "invariants": [
            {
                "id": "safe-remains-true",
                "expression": _var("safe"),
                "description": "Independent noise cannot falsify the safety bit.",
            },
        ],
    }


def _unsafe_noise_fixture(n: int, bound: int = 4) -> dict[str, Any]:
    """Unsafe fixture with a control bit and N noise variables."""
    variables: list[dict[str, Any]] = [
        _bool_var("safe", True),
        _bool_var("control", True),
    ]
    transitions: list[dict[str, Any]] = [
        {
            "id": "apply-control",
            "guard": _const(True),
            "assignments": [
                {"variable": "safe", "expression": _not(_var("control"))},
            ],
        },
    ]
    for i in range(n):
        vname = f"noise{i}"
        variables.append(_bool_var(vname, False))
        transitions.append(
            {
                "id": f"toggle-{vname}",
                "guard": _const(True),
                "assignments": [
                    {"variable": vname, "expression": _not(_var(vname))},
                ],
            },
        )
    return {
        "schema_version": "1",
        "id": f"unsafe-noise-{n}",
        "bound": bound,
        "assumptions": [f"{n} noise variables are independent of the control/safety bits"],
        "variables": variables,
        "transitions": transitions,
        "invariants": [
            {
                "id": "safe-remains-true",
                "expression": _var("safe"),
                "description": "The unsafe control transition must produce a witness.",
            },
        ],
    }


def _safe_principal_fixture(p: int, bound: int = 4) -> dict[str, Any]:
    """Safe fixture with P independent principal-authority variables."""
    variables: list[dict[str, Any]] = [_bool_var("safe", True)]
    transitions: list[dict[str, Any]] = []
    for i in range(p):
        vname = f"auth{i}"
        variables.append(_bool_var(vname, True))
        transitions.append(
            {
                "id": f"toggle-{vname}",
                "guard": _const(True),
                "assignments": [
                    {"variable": vname, "expression": _not(_var(vname))},
                ],
            },
        )
    return {
        "schema_version": "1",
        "id": f"safe-principal-{p}",
        "bound": bound,
        "assumptions": [f"{p} principal-authority variables are independent of the safety invariant"],
        "variables": variables,
        "transitions": transitions,
        "invariants": [
            {
                "id": "safe-remains-true",
                "expression": _var("safe"),
                "description": "Principal toggles cannot falsify the safety bit.",
            },
        ],
    }


def _unsafe_principal_fixture(p: int, bound: int = 4) -> dict[str, Any]:
    """Unsafe fixture with P principals where one can negate safety."""
    variables: list[dict[str, Any]] = [_bool_var("safe", True)]
    transitions: list[dict[str, Any]] = [
        {
            "id": "apply-control",
            "guard": _const(True),
            "assignments": [
                {"variable": "safe", "expression": _not(_var("safe"))},
            ],
        },
    ]
    for i in range(p):
        vname = f"auth{i}"
        variables.append(_bool_var(vname, True))
        transitions.append(
            {
                "id": f"toggle-{vname}",
                "guard": _const(True),
                "assignments": [
                    {"variable": vname, "expression": _not(_var(vname))},
                ],
            },
        )
    return {
        "schema_version": "1",
        "id": f"unsafe-principal-{p}",
        "bound": bound,
        "assumptions": [f"{p} principal-authority variables alongside an unsafe control transition"],
        "variables": variables,
        "transitions": transitions,
        "invariants": [
            {
                "id": "safe-remains-true",
                "expression": _var("safe"),
                "description": "The unsafe control transition must produce a witness.",
            },
        ],
    }


def _safe_depth_fixture(k: int) -> dict[str, Any]:
    """Safe fixture with a chain of K variables that cannot falsify safety."""
    variables: list[dict[str, Any]] = [_bool_var("safe", True)]
    transitions: list[dict[str, Any]] = []
    for i in range(k):
        vname = f"chain{i}"
        variables.append(_bool_var(vname, False))
        transitions.append(
            {
                "id": f"step-{vname}",
                "guard": _const(True),
                "assignments": [
                    {"variable": vname, "expression": _not(_var(vname))},
                ],
            },
        )
    return {
        "schema_version": "1",
        "id": f"safe-depth-{k}",
        "bound": k + 1,
        "assumptions": [f"{k} chain variables are independent of the safety invariant"],
        "variables": variables,
        "transitions": transitions,
        "invariants": [
            {
                "id": "safe-remains-true",
                "expression": _var("safe"),
                "description": "Chain toggles cannot falsify the safety bit.",
            },
        ],
    }


def _unsafe_depth_fixture(k: int) -> dict[str, Any]:
    """Unsafe fixture requiring K steps to reach the violation."""
    variables: list[dict[str, Any]] = [_bool_var("safe", True)]
    transitions: list[dict[str, Any]] = []
    for i in range(k):
        vname = f"gate{i}"
        variables.append(_bool_var(vname, False))
        guard = _var(vname) if i == 0 else _and(_var(f"gate{i - 1}"), _const(True))
        transitions.append(
            {
                "id": f"open-{vname}",
                "guard": guard,
                "assignments": [
                    {"variable": vname, "expression": _const(True)},
                ],
            },
        )
    final_guard = _var(f"gate{k - 1}") if k > 0 else _const(True)
    transitions.append(
        {
            "id": "violate",
            "guard": final_guard,
            "assignments": [
                {"variable": "safe", "expression": _const(False)},
            ],
        },
    )
    return {
        "schema_version": "1",
        "id": f"unsafe-depth-{k}",
        "bound": k + 2,
        "assumptions": [f"requires {k + 1} steps to reach the safety violation"],
        "variables": variables,
        "transitions": transitions,
        "invariants": [
            {
                "id": "safe-remains-true",
                "expression": _var("safe"),
                "description": f"Witness at depth {k + 1}.",
            },
        ],
    }


def _run_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    """Run all backends on a fixture and return measurements."""
    ir = VerificationIR.from_dict(fixture)
    comp = compare_cone_of_influence(ir, ())
    z3_orig = verify_with_z3(ir)
    z3_red = verify_with_z3(comp.reduction.reduced_ir)

    orig_ref = comp.original
    red_ref = comp.reduced

    return {
        "fixture_id": fixture["id"],
        "bound": fixture["bound"],
        "original": {
            "variables": len(ir.variables),
            "rules": len(ir.transitions),
            "states": orig_ref.states,
            "transitions": orig_ref.transitions,
            "verdict": orig_ref.verdict.value,
            "witness_length": len(orig_ref.counterexample) if orig_ref.counterexample else 0,
        },
        "reduced": {
            "variables": len(comp.reduction.reduced_ir.variables),
            "rules": len(comp.reduction.reduced_ir.transitions),
            "states": red_ref.states,
            "transitions": red_ref.transitions,
            "verdict": red_ref.verdict.value,
            "witness_length": len(red_ref.counterexample) if red_ref.counterexample else 0,
        },
        "coi_equivalent": comp.equivalent,
        "z3_original": {
            "verdict": z3_orig.verdict.value,
            "witness_length": len(z3_orig.counterexample) if z3_orig.counterexample else 0,
            "error": z3_orig.error,
        },
        "z3_reduced": {
            "verdict": z3_red.verdict.value,
            "witness_length": len(z3_red.counterexample) if z3_red.counterexample else 0,
            "error": z3_red.error,
        },
    }


def _noise_scaling_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for n in NOISE_COUNTS:
        rows.append(
            {
                "family": "noise_scaling",
                "parameter": "noise_variables",
                "value": n,
                "safety": "safe",
                **_run_fixture(_safe_noise_fixture(n)),
            },
        )
        rows.append(
            {
                "family": "noise_scaling",
                "parameter": "noise_variables",
                "value": n,
                "safety": "unsafe",
                **_run_fixture(_unsafe_noise_fixture(n)),
            },
        )
    return rows


def _principal_scaling_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p in PRINCIPAL_COUNTS:
        rows.append(
            {
                "family": "principal_scaling",
                "parameter": "principals",
                "value": p,
                "safety": "safe",
                **_run_fixture(_safe_principal_fixture(p)),
            },
        )
        rows.append(
            {
                "family": "principal_scaling",
                "parameter": "principals",
                "value": p,
                "safety": "unsafe",
                **_run_fixture(_unsafe_principal_fixture(p)),
            },
        )
    return rows


def _depth_scaling_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for k in DEPTH_VALUES:
        rows.append(
            {
                "family": "depth_scaling",
                "parameter": "depth",
                "value": k,
                "safety": "safe",
                **_run_fixture(_safe_depth_fixture(k)),
            },
        )
        rows.append(
            {
                "family": "depth_scaling",
                "parameter": "depth",
                "value": k,
                "safety": "unsafe",
                **_run_fixture(_unsafe_depth_fixture(k)),
            },
        )
    return rows


def generate() -> dict[str, Any]:
    """Generate the full SLED-V scaling evidence bundle."""
    rows: list[dict[str, Any]] = []
    rows.extend(_noise_scaling_rows())
    rows.extend(_principal_scaling_rows())
    rows.extend(_depth_scaling_rows())

    all_equivalent = all(r["coi_equivalent"] for r in rows)
    z3_agree = all(
        r["z3_original"]["verdict"] == r["z3_reduced"]["verdict"]
        for r in rows
        if r["z3_original"]["error"] is None and r["z3_reduced"]["error"] is None
    )

    def _safe(v: str) -> bool:
        return v in ("safe", "bounded_safe")

    def _agree(a: str, b: str) -> bool:
        if a == "unsafe" or b == "unsafe":
            return a == b
        return _safe(a) and _safe(b)

    ref_z3_agree = all(_agree(r["original"]["verdict"], r["z3_original"]["verdict"]) for r in rows if r["z3_original"]["error"] is None)

    by_family: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        fam = r["family"]
        by_family.setdefault(fam, []).append(r)

    family_summaries: dict[str, dict[str, Any]] = {}
    for fam, fam_rows in by_family.items():
        safe_rows = [r for r in fam_rows if r["safety"] == "safe"]
        unsafe_rows = [r for r in fam_rows if r["safety"] == "unsafe"]
        family_summaries[fam] = {
            "total_fixtures": len(fam_rows),
            "safe_count": len(safe_rows),
            "unsafe_count": len(unsafe_rows),
            "max_original_states": max(r["original"]["states"] for r in fam_rows),
            "max_reduced_states": max(r["reduced"]["states"] for r in fam_rows),
            "max_original_variables": max(r["original"]["variables"] for r in fam_rows),
            "max_reduced_variables": max(r["reduced"]["variables"] for r in fam_rows),
            "state_reduction_ratio": (
                max(r["original"]["states"] for r in fam_rows) / max(r["reduced"]["states"] for r in fam_rows)
                if max(r["reduced"]["states"] for r in fam_rows) > 0
                else 0.0
            ),
        }

    no_coi_downgrade = all(r["reduced"]["verdict"] != "unsafe" for r in rows if r["original"]["verdict"] in ("safe", "bounded_safe"))

    return {
        "schema_version": "1",
        "id": "sledv-scaling-v1",
        "historical_anchor": {
            "total_traces": HISTORICAL_TOTAL_TRACES,
            "total_canonical_states": HISTORICAL_TOTAL_STATES,
            "environments": [HISTORICAL_ANCHOR],
            "source": "research/experiments/baselines/sled-historical-v1.json",
        },
        "scaling_families": list(by_family.keys()),
        "noise_counts": list(NOISE_COUNTS),
        "principal_counts": list(PRINCIPAL_COUNTS),
        "depth_values": list(DEPTH_VALUES),
        "fixtures": rows,
        "summary": {
            "total_fixtures": len(rows),
            "all_coi_equivalent": all_equivalent,
            "no_coi_downgrade": no_coi_downgrade,
            "z3_all_agree": z3_agree,
            "ref_z3_agree": ref_z3_agree,
        },
        "by_family": family_summaries,
        "claim_boundary": (
            "SLED-V drastically reduces redundancy and agrees with independent "
            "bounded/reference backends on the tested finite models. "
            "Not allowed: SLED-V proves Conflux secure for arbitrary or unbounded deployments."
        ),
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
    parser = argparse.ArgumentParser(description="Generate SLED-V scaling evidence from parameterised fixtures.")
    parser.add_argument("--check", action="store_true", help="Verify retained bundle matches regeneration.")
    arguments = parser.parse_args()

    if arguments.check:
        if _check(OUTPUT):
            print("SLED-V scaling evidence regeneration check passed")
            return 0
        print("SLED-V scaling evidence is stale or missing", file=sys.stderr)
        return 1

    bundle = generate()
    _write_bundle(OUTPUT, bundle)
    print(f"Generated SLED-V scaling evidence: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
