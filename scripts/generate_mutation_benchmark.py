"""Generate expanded security mutation benchmark evidence.

Aggregates mutants from four families into a single deterministic
evidence bundle:

- **Disclosure** (4 mutants): native SLED explicit-state checking
- **Delegation** (7 mutants): native SLED explicit-state checking
- **Delegation IR** (10 mutants): reference BFS + Z3 BMC + COI-reduced Z3 BMC
- **Synthesis** (5 defective strategies): Z3 BMC on synthesised IR

Total: 26 mutants across 4 families, exceeding the SaTML target of
≥20 mutants across ≥4 families.

Usage::

    python scripts/generate_mutation_benchmark.py
    python scripts/generate_mutation_benchmark.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from conflux.evaluation import (
    DELEGATION_PROPERTIES,
    DelegationMutation,
    DelegationVerificationSystem,
    DisclosureMutation,
    DisclosureVerificationSystem,
    ExplicitStateChecker,
    VerificationBounds,
)
from conflux.verification.delegation_ir import (
    DelegationIRMutation,
    all_delegation_ir_variants,
)
from conflux.verification.reduction import (
    compare_cone_of_influence,
    reference_safety_check,
)
from conflux.verification.synthesis import (
    ControllerStrategy,
    default_instance,
    evaluate_strategy,
)
from conflux.verification.z3_backend import verify_with_z3

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "output" / "runs" / "mutation-benchmark-v1"

BOUNDS = VerificationBounds(1, 4, 4, 1)
DISCLOSURE_PROPERTIES = ()  # populated below to avoid circular import


def _native_mutation_result(mutation: str, result: Any) -> dict[str, Any]:
    verification = result.to_dict()
    counterexample = verification["counterexample"]
    return {
        "mutation": mutation,
        "killed": verification["verdict"] == "unsafe" and counterexample is not None and counterexample["length"] == 1,
        "verdict": verification["verdict"],
        "witness_length": counterexample["length"] if counterexample else 0,
    }


def _ir_mutation_result(mutation: str, ir: Any) -> dict[str, Any]:
    ref = reference_safety_check(ir)
    z3_orig = verify_with_z3(ir)
    comp = compare_cone_of_influence(ir, ())
    z3_red = verify_with_z3(comp.reduction.reduced_ir)

    def _safe(v: str) -> bool:
        return v in ("safe", "bounded_safe")

    def _agree(a: str, b: str) -> bool:
        if a == "unsafe" or b == "unsafe":
            return a == b
        return _safe(a) and _safe(b)

    return {
        "mutation": mutation,
        "killed": ref.verdict.value == "unsafe",
        "reference": {
            "verdict": ref.verdict.value,
            "states": ref.states,
            "witness_length": len(ref.counterexample) if ref.counterexample else 0,
        },
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
        "coi_equivalent": comp.equivalent,
        "backends_agree": _agree(ref.verdict.value, z3_orig.verdict.value) if z3_orig.error is None else None,
        "original_variables": len(ir.variables),
        "reduced_variables": len(comp.reduction.reduced_ir.variables),
    }


def _synthesis_mutation_result(strategy: ControllerStrategy) -> dict[str, Any]:
    instance = default_instance()
    result = evaluate_strategy(instance, strategy)
    return {
        "mutation": strategy.value,
        "killed": result.verdict == "unsafe",
        "verdict": result.verdict,
        "witness_length": len(result.counterexample) if result.counterexample else 0,
        "decisions": len(result.synthesised_decisions),
        "ites_decisions": len(result.ites_decisions),
        "equivalent_to_ites": result.equivalent,
    }


def _disclosure_mutants() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    from conflux.evaluation import (
        CompleteAttribution,
        NoHiddenDecisionLeakage,
        NoUnauthorisedSelector,
        SafeRedaction,
    )

    props = (
        NoUnauthorisedSelector(),
        NoHiddenDecisionLeakage(),
        CompleteAttribution(),
        SafeRedaction(),
    )
    canonical = ExplicitStateChecker().verify(DisclosureVerificationSystem(), props, BOUNDS)
    mutants: list[dict[str, Any]] = []
    for m in DisclosureMutation:
        if m is DisclosureMutation.CANONICAL:
            continue
        result = ExplicitStateChecker().verify(DisclosureVerificationSystem(m), props, BOUNDS)
        mutants.append(_native_mutation_result(m.value, result))
    return canonical.to_dict(), mutants


def _delegation_mutants() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    canonical = ExplicitStateChecker().verify(DelegationVerificationSystem(), DELEGATION_PROPERTIES, BOUNDS)
    mutants: list[dict[str, Any]] = []
    for m in DelegationMutation:
        if m is DelegationMutation.CANONICAL:
            continue
        result = ExplicitStateChecker().verify(DelegationVerificationSystem(m), DELEGATION_PROPERTIES, BOUNDS)
        mutants.append(_native_mutation_result(m.value, result))
    return canonical.to_dict(), mutants


def _delegation_ir_mutants() -> list[dict[str, Any]]:
    variants = all_delegation_ir_variants()
    mutants: list[dict[str, Any]] = []
    for v in variants:
        if v.mutation is DelegationIRMutation.CANONICAL:
            continue
        mutants.append(_ir_mutation_result(v.mutation.value, v.ir))
    return mutants


def _synthesis_mutants() -> list[dict[str, Any]]:
    mutants: list[dict[str, Any]] = []
    for s in ControllerStrategy:
        if s in (ControllerStrategy.ITES_INTERSECTION, ControllerStrategy.READ_CHECK_ENABLED):
            continue
        mutants.append(_synthesis_mutation_result(s))
    return mutants


def generate() -> dict[str, Any]:
    """Generate the full mutation benchmark evidence bundle."""
    disclosure_canonical, disclosure_mutants = _disclosure_mutants()
    delegation_canonical, delegation_mutants = _delegation_mutants()
    delegation_ir_mutants = _delegation_ir_mutants()
    synthesis_mutants = _synthesis_mutants()

    all_mutants = disclosure_mutants + delegation_mutants + delegation_ir_mutants + synthesis_mutants
    killed = sum(1 for m in all_mutants if m["killed"])

    families = {
        "disclosure": {
            "count": len(disclosure_mutants),
            "killed": sum(1 for m in disclosure_mutants if m["killed"]),
            "backend": "native_sled",
        },
        "delegation": {
            "count": len(delegation_mutants),
            "killed": sum(1 for m in delegation_mutants if m["killed"]),
            "backend": "native_sled",
        },
        "delegation_ir": {
            "count": len(delegation_ir_mutants),
            "killed": sum(1 for m in delegation_ir_mutants if m["killed"]),
            "backend": "reference_bfs+z3_bmc+coi_z3_bmc",
        },
        "synthesis": {
            "count": len(synthesis_mutants),
            "killed": sum(1 for m in synthesis_mutants if m["killed"]),
            "backend": "synthesis_ir+z3_bmc",
        },
    }

    return {
        "schema_version": "1",
        "id": "mutation-benchmark-v1",
        "classification": "bounded_evidence",
        "complete": True,
        "runtime_delegation_enabled": False,
        "bounds": {
            "max_depth": 1,
            "max_states": 4,
            "max_transitions": 4,
            "max_model_calls": 1,
        },
        "canonical": {
            "disclosure": disclosure_canonical,
            "delegation": delegation_canonical,
        },
        "mutants": {
            "disclosure": disclosure_mutants,
            "delegation": delegation_mutants,
            "delegation_ir": delegation_ir_mutants,
            "synthesis": synthesis_mutants,
        },
        "summary": {
            "total_mutants": len(all_mutants),
            "total_killed": killed,
            "kill_rate": killed / len(all_mutants) if all_mutants else 0.0,
            "families": families,
            "family_count": len(families),
        },
        "claim_boundary": (
            "All seeded security mutants are killed by at least one "
            "verification backend within the tested bound. "
            "Not allowed: this proves all possible mutants are detectable."
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
    parser = argparse.ArgumentParser(description="Generate expanded security mutation benchmark evidence.")
    parser.add_argument("--check", action="store_true", help="Verify retained bundle matches regeneration.")
    arguments = parser.parse_args()

    if arguments.check:
        if _check(OUTPUT):
            print("Mutation benchmark evidence regeneration check passed")
            return 0
        print("Mutation benchmark evidence is stale or missing", file=sys.stderr)
        return 1

    bundle = generate()
    _write_bundle(OUTPUT, bundle)
    print(f"Generated mutation benchmark evidence: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
