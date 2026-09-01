"""Generate SLED depth-bound sweep evidence.

Runs native SLED across a matrix of increased bounds to surface
verdict changes and state-space growth patterns.

Usage:
    python scripts/generate_sled_depth_sweep.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from conflux.evaluation.delegation_verification import (
    DELEGATION_PROPERTIES,
    DelegationMutation,
    DelegationVerificationSystem,
)
from conflux.evaluation.model_checking import (
    ExplicitStateChecker,
    VerificationBounds,
)
from conflux.evaluation.planning import (
    AbstractEffect,
    AbstractPatchKind,
    AbstractPlanPatch,
    CodeCapabilityPreserved,
    NoUnauthorisedPlanningEffect,
    PlanningContextMonotonicity,
    WorstCasePlanningSystem,
)

OUTPUT_DIR = Path("research/output/runs/sled_depth_sweep")

PLANNING_PROPERTIES = (
    NoUnauthorisedPlanningEffect(),
    PlanningContextMonotonicity(),
    CodeCapabilityPreserved(),
)

_PLANNING_PATCHES: tuple[AbstractPlanPatch, ...] = (
    AbstractPlanPatch(
        id="auth_effect",
        kind=AbstractPatchKind.APPEND_EFFECT,
        control_principals=frozenset({"alice"}),
        effect=AbstractEffect(
            id="write_file",
            permission="write",
            resource="file",
            influencing_principals=frozenset({"alice"}),
            authorised=True,
        ),
    ),
    AbstractPlanPatch(
        id="unauth_effect",
        kind=AbstractPatchKind.APPEND_EFFECT,
        control_principals=frozenset({"bob"}),
        effect=AbstractEffect(
            id="unauth_write",
            permission="write",
            resource="file",
            influencing_principals=frozenset({"bob"}),
            authorised=False,
        ),
    ),
    AbstractPlanPatch(
        id="code_in_cap",
        kind=AbstractPatchKind.APPEND_CODE_EFFECT,
        control_principals=frozenset({"alice"}),
        effect=AbstractEffect(
            id="safe_code",
            permission="execute_code",
            resource="sandbox",
            influencing_principals=frozenset({"alice"}),
            authorised=True,
            code_effect=True,
            within_capability_envelope=True,
        ),
    ),
    AbstractPlanPatch(
        id="code_outside_cap",
        kind=AbstractPatchKind.APPEND_CODE_EFFECT,
        control_principals=frozenset({"carol"}),
        effect=AbstractEffect(
            id="unsafe_code",
            permission="execute_code",
            resource="sandbox",
            influencing_principals=frozenset({"carol"}),
            authorised=True,
            code_effect=True,
            within_capability_envelope=False,
        ),
    ),
    AbstractPlanPatch(
        id="terminate",
        kind=AbstractPatchKind.TERMINATE,
        control_principals=frozenset(),
    ),
)

BOUND_CONFIGS = [
    VerificationBounds(max_depth=8, max_states=10_000, max_transitions=50_000, max_model_calls=8),
    VerificationBounds(max_depth=12, max_states=50_000, max_transitions=250_000, max_model_calls=12),
    VerificationBounds(max_depth=16, max_states=100_000, max_transitions=500_000, max_model_calls=16),
    VerificationBounds(max_depth=24, max_states=500_000, max_transitions=1_000_000, max_model_calls=16),
]


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []

    for bound_idx, bounds in enumerate(BOUND_CONFIGS):
        for mutation in DelegationMutation:
            system = DelegationVerificationSystem(mutation)
            result = ExplicitStateChecker().verify(system, DELEGATION_PROPERTIES, bounds)
            results.append(
                {
                    "system": "delegation",
                    "variant": mutation.value,
                    "bound_config": bound_idx,
                    "max_depth": bounds.max_depth,
                    "max_states": bounds.max_states,
                    "verdict": result.verdict.value,
                    "unique_states": result.unique_states,
                    "duplicate_states": result.duplicate_states,
                    "transitions_explored": result.transitions,
                    "truncated": result.truncated,
                    "counterexample_length": result.counterexample.length if result.counterexample else 0,
                },
            )

        planning_system: WorstCasePlanningSystem = WorstCasePlanningSystem(
            initial_context=frozenset({"alice", "bob"}),
            patches=_PLANNING_PATCHES,
            max_plan_nodes=4 + bound_idx * 4,
            max_continuation_depth=2 + bound_idx * 2,
            max_planner_calls=2 + bound_idx * 2,
            max_effects=2 + bound_idx * 2,
        )
        planning_result = ExplicitStateChecker().verify(planning_system, PLANNING_PROPERTIES, bounds)
        results.append(
            {
                "system": "planning",
                "variant": "worst_case",
                "bound_config": bound_idx,
                "max_depth": bounds.max_depth,
                "max_states": bounds.max_states,
                "verdict": planning_result.verdict.value,
                "unique_states": planning_result.unique_states,
                "duplicate_states": planning_result.duplicate_states,
                "transitions_explored": planning_result.transitions,
                "truncated": planning_result.truncated,
                "counterexample_length": planning_result.counterexample.length if planning_result.counterexample else 0,
            },
        )

    evidence = {
        "generated_at": datetime.now(UTC).isoformat(),
        "module": "conflux.evaluation.model_checking",
        "bound_configs": len(BOUND_CONFIGS),
        "total_runs": len(results),
        "results": results,
    }
    output_path = OUTPUT_DIR / "evidence.json"
    output_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"Generated SLED depth sweep evidence: {output_path}")
    print(f"  Bound configs: {len(BOUND_CONFIGS)}")
    print(f"  Total runs: {len(results)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
