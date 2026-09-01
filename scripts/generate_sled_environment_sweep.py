"""Generate multi-environment SLED sweep evidence.

Runs native SLED across varied environment snapshots with different
principal counts, action space sizes, and policy configurations to
surface scaling bugs and verdict changes.

Usage:
    python scripts/generate_sled_environment_sweep.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
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
    OwnerAuthorisationPolicy,
    SessionVisibilityPolicy,
)

OUTPUT_DIR = Path("research/output/runs/sled_environment_sweep")

ITES_PROPERTIES = (
    NoUnauthorisedAuthorisation(),
    NoForbiddenObservation(),
    PrincipalContextMonotonicity(),
    ProvenancePreserved(),
)

PRINCIPAL_COUNTS = (1, 2, 3, 5, 8)
ACTION_COUNTS = (1, 3, 8)
DATA_ITEM_COUNTS = (1, 3, 5)
BOUNDS = VerificationBounds(
    max_depth=6,
    max_states=5_000,
    max_transitions=25_000,
    max_model_calls=6,
)


def _make_principals(n: int) -> tuple[Principal, ...]:
    names = ("alice", "bob", "carol", "dave", "eve", "frank", "grace", "heidi")
    return tuple(Principal(names[i], names[i].capitalize()) for i in range(n))


def _make_actions(n: int, resource: ResourceRef) -> tuple[PrimitiveAction, ...]:
    return tuple(
        PrimitiveAction(
            id=f"action-{i}",
            operation="read",
            permission=READ,
            resource=resource,
        )
        for i in range(n)
    )


def _make_data_items(n: int, principals: tuple[Principal, ...]) -> tuple[DataItem, ...]:
    owner = principals[0]
    return tuple(DataItem(id=f"item-{i}", value=f"data-{i}", authors=frozenset({owner})) for i in range(n))


def _make_resource() -> ResourceRef:
    return ResourceRef(provider="fs", resource_id="file1", resource_type="file")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []

    for n_principals in PRINCIPAL_COUNTS:
        principals = _make_principals(n_principals)
        session = Session("sweep-session", frozenset(principals))
        pipeline = DecisionPipeline(
            OwnerAuthorisationPolicy(),
            AllowInternalReadPolicy(),
            SessionVisibilityPolicy(),
            ExplicitConsentPolicy(),
        )
        kernel = TransitionKernel(pipeline)
        resource = _make_resource()

        for n_actions in ACTION_COUNTS:
            actions = _make_actions(n_actions, resource)

            for n_data in DATA_ITEM_COUNTS:
                data = _make_data_items(n_data, principals)
                env = EnvironmentSnapshot(
                    id=f"env-p{n_principals}-a{n_actions}-d{n_data}",
                    data=data,
                    resources=(resource,),
                )
                system = CombinatorialVerificationSystem.from_environment(
                    environment=env,
                    primitive_actions=actions,
                    kernel=kernel,
                    session=session,
                    max_batch_size=2,
                    max_nested_inputs=2,
                    max_model_calls=4,
                )
                result = ExplicitStateChecker().verify(system, ITES_PROPERTIES, BOUNDS)  # type: ignore[misc]
                results.append(
                    {
                        "principals": n_principals,
                        "actions": n_actions,
                        "data_items": n_data,
                        "verdict": result.verdict.value,
                        "unique_states": result.unique_states,
                        "transitions": result.transitions,
                        "truncated": result.truncated,
                        "counterexample_length": result.counterexample.length if result.counterexample else 0,
                    },
                )

    verdicts = [r["verdict"] for r in results]
    evidence = {
        "generated_at": datetime.now(UTC).isoformat(),
        "module": "conflux.evaluation.combinatorial",
        "total_runs": len(results),
        "principal_counts": list(PRINCIPAL_COUNTS),
        "action_counts": list(ACTION_COUNTS),
        "data_item_counts": list(DATA_ITEM_COUNTS),
        "safe_count": verdicts.count("safe"),
        "bounded_safe_count": verdicts.count("bounded_safe"),
        "unsafe_count": verdicts.count("unsafe"),
        "unknown_count": verdicts.count("unknown"),
        "results": results,
    }
    output_path = OUTPUT_DIR / "evidence.json"
    output_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"Generated SLED environment sweep evidence: {output_path}")
    print(f"  Total runs: {len(results)}")
    print(
        f"  SAFE: {evidence['safe_count']}, BOUNDED_SAFE: {evidence['bounded_safe_count']}, UNSAFE: {evidence['unsafe_count']}, UNKNOWN: {evidence['unknown_count']}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
