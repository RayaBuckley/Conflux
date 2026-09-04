"""Generate SLED deep-exploration convergence evidence.

Runs the planning system and combinatorial system (with permissive policies)
at very large depths to find convergence points where the state space is
exhausted (truncated=False).

Usage:
    python scripts/generate_sled_deep_exploration.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path

from conflux.application import DecisionPipeline
from conflux.domain import (
    READ,
    DataItem,
    EnvironmentSnapshot,
    PrimitiveAction,
    Principal,
    ResourceRef,
    Session,
)
from conflux.evaluation.combinatorial import CombinatorialVerificationSystem
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
from conflux.evaluation.properties import (
    NoForbiddenObservation,
    NoUnauthorisedAuthorisation,
    PrincipalContextMonotonicity,
    ProvenancePreserved,
)
from conflux.ites import TransitionKernel
from conflux.policy import (
    AllowInternalReadPolicy,
    ExplicitConsentPolicy,
    InMemoryAuthorisationPolicy,
    PolicyGrant,
    SessionVisibilityPolicy,
)

OUTPUT_DIR = Path("research/output/runs/sled_deep_exploration")

PLANNING_PROPERTIES = (
    NoUnauthorisedPlanningEffect(),
    PlanningContextMonotonicity(),
    CodeCapabilityPreserved(),
)

ITES_PROPERTIES = (
    NoUnauthorisedAuthorisation(),
    NoForbiddenObservation(),
    PrincipalContextMonotonicity(),
    ProvenancePreserved(),
)

DEPTHS = (16, 24, 32, 48, 64, 96, 128)

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

_PRINCIPALS = (
    Principal("alice", "Alice"),
    Principal("bob", "Bob"),
    Principal("carol", "Carol"),
)
_RESOURCE = ResourceRef(provider="fs", resource_id="file1", resource_type="file")
_ACTIONS = tuple(PrimitiveAction(id=f"act_{i}", operation="read", permission=READ, resource=_RESOURCE) for i in range(4))
_DATA = tuple(
    DataItem(
        id=f"item-{i}",
        value=f"data-{i}",
        authors=frozenset({_PRINCIPALS[i % 3]}),
        readers=frozenset(_PRINCIPALS),
    )
    for i in range(5)
)
_ENV = EnvironmentSnapshot(id="deep-exploration", data=_DATA, resources=(_RESOURCE,))


def _all_action_ids() -> frozenset[str]:
    artifacts = _ENV.artifacts()
    nested_ids: set[str] = set()
    for r in range(1, min(3, len(artifacts)) + 1):
        for combo in combinations(artifacts, r):
            nested_ids.add(f"nested-{r}-{'-'.join(a.id for a in combo)}")
    return frozenset(a.id for a in _ACTIONS) | frozenset(nested_ids)


def _combinatorial_system(depth: int) -> CombinatorialVerificationSystem:
    grants = frozenset(PolicyGrant(p.id, "read", _RESOURCE.resource_id) for p in _PRINCIPALS)
    pipeline = DecisionPipeline(
        InMemoryAuthorisationPolicy(grants),
        AllowInternalReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(_all_action_ids()),
    )
    kernel = TransitionKernel(pipeline)
    session = Session("deep-exploration", frozenset(_PRINCIPALS))
    return CombinatorialVerificationSystem.from_environment(
        environment=_ENV,
        primitive_actions=_ACTIONS,
        kernel=kernel,
        session=session,
        max_batch_size=2,
        max_nested_inputs=3,
        max_model_calls=depth,
    )


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []

    for depth in DEPTHS:
        bounds = VerificationBounds(
            max_depth=depth,
            max_states=5_000_000,
            max_transitions=10_000_000,
            max_model_calls=depth,
        )

        planning_system = WorstCasePlanningSystem(
            initial_context=frozenset({"alice", "bob"}),
            patches=_PLANNING_PATCHES,
            max_plan_nodes=depth + 2,
            max_continuation_depth=depth + 2,
            max_planner_calls=depth + 2,
            max_effects=depth + 2,
        )
        start = time.perf_counter()
        planning_result = ExplicitStateChecker().verify(planning_system, PLANNING_PROPERTIES, bounds)
        elapsed = time.perf_counter() - start
        results.append(
            {
                "system": "planning",
                "depth": depth,
                "verdict": planning_result.verdict.value,
                "unique_states": planning_result.unique_states,
                "duplicate_states": planning_result.duplicate_states,
                "transitions_explored": planning_result.transitions,
                "truncated": planning_result.truncated,
                "counterexample_length": planning_result.counterexample.length if planning_result.counterexample else 0,
                "runtime_seconds": round(elapsed, 3),
            },
        )
        print(
            f"  planning depth={depth}: verdict={planning_result.verdict.value} "
            f"states={planning_result.unique_states} "
            f"transitions={planning_result.transitions} "
            f"truncated={planning_result.truncated} "
            f"runtime={elapsed:.3f}s",
        )

        combo_system = _combinatorial_system(depth)
        combo_bounds = VerificationBounds(
            max_depth=depth,
            max_states=50_000,
            max_transitions=200_000,
            max_model_calls=depth,
        )
        start = time.perf_counter()
        combo_result = ExplicitStateChecker().verify(combo_system, ITES_PROPERTIES, combo_bounds)  # type: ignore[misc]
        elapsed = time.perf_counter() - start
        results.append(
            {
                "system": "combinatorial",
                "depth": depth,
                "verdict": combo_result.verdict.value,
                "unique_states": combo_result.unique_states,
                "duplicate_states": combo_result.duplicate_states,
                "transitions_explored": combo_result.transitions,
                "truncated": combo_result.truncated,
                "counterexample_length": combo_result.counterexample.length if combo_result.counterexample else 0,
                "runtime_seconds": round(elapsed, 3),
            },
        )
        print(
            f"  combinatorial depth={depth}: verdict={combo_result.verdict.value} "
            f"states={combo_result.unique_states} "
            f"transitions={combo_result.transitions} "
            f"truncated={combo_result.truncated} "
            f"runtime={elapsed:.3f}s",
        )

    planning_convergence = next(
        (r for r in results if r["system"] == "planning" and not r["truncated"]),
        None,
    )
    combinatorial_convergence = next(
        (r for r in results if r["system"] == "combinatorial" and not r["truncated"]),
        None,
    )
    evidence = {
        "generated_at": datetime.now(UTC).isoformat(),
        "module": "conflux.evaluation.model_checking",
        "depths": list(DEPTHS),
        "total_runs": len(results),
        "planning_convergence_depth": planning_convergence["depth"] if planning_convergence else None,
        "combinatorial_convergence_depth": combinatorial_convergence["depth"] if combinatorial_convergence else None,
        "results": results,
    }
    output_path = OUTPUT_DIR / "evidence.json"
    output_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"\nGenerated SLED deep exploration evidence: {output_path}")
    print(f"  Total runs: {len(results)}")
    print(
        f"  Planning convergence: {planning_convergence['depth'] if planning_convergence else 'not converged'}",
    )
    print(
        f"  Combinatorial convergence: {combinatorial_convergence['depth'] if combinatorial_convergence else 'not converged'}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
