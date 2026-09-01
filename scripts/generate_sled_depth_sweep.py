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
            patches=(),
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
