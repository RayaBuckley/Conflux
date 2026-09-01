"""Stress-test current SLED on complex environments.

Pushes CombinatorialVerificationSystem beyond the original sweep's
8 actions / 5 data items. Varies principals (5-12), actions (8-16),
data items (8-16), nested input depth, batch size, and model-checking
depth to surface BOUNDED_SAFE transitions, unexpected UNSAFE verdicts,
crash conditions, and non-monotonic behaviour.

Usage:
    python scripts/generate_sled_complex_environments.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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

OUTPUT_DIR = Path("research/output/runs/sled_complex_environments")

ITES_PROPERTIES = (
    NoUnauthorisedAuthorisation(),
    NoForbiddenObservation(),
    PrincipalContextMonotonicity(),
    ProvenancePreserved(),
)

_NAMES = ("alice", "bob", "carol", "dave", "eve", "frank", "grace", "heidi", "ivan", "judy", "karl", "leo")


def _run_config(
    n_principals: int,
    n_actions: int,
    n_data: int,
    max_nested: int,
    max_batch: int,
    depth: int,
) -> dict[str, Any]:
    principals = tuple(Principal(_NAMES[i], _NAMES[i].capitalize()) for i in range(n_principals))
    session = Session("stress-session", frozenset(principals))
    pipeline = DecisionPipeline(
        OwnerAuthorisationPolicy(),
        AllowInternalReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(),
    )
    kernel = TransitionKernel(pipeline)
    resource = ResourceRef(provider="fs", resource_id="file1", resource_type="file")

    actions = tuple(PrimitiveAction(id=f"act_{i}", operation="read", permission=READ, resource=resource) for i in range(n_actions))
    data = tuple(DataItem(id=f"item-{i}", value=f"val-{i}", authors=frozenset({principals[i % n_principals]})) for i in range(n_data))
    env = EnvironmentSnapshot(id=f"env-p{n_principals}-a{n_actions}-d{n_data}", data=data, resources=(resource,))
    system = CombinatorialVerificationSystem.from_environment(
        environment=env,
        primitive_actions=actions,
        kernel=kernel,
        session=session,
        max_batch_size=max_batch,
        max_nested_inputs=max_nested,
        max_model_calls=depth,
    )
    bounds = VerificationBounds(
        max_depth=depth,
        max_states=100_000,
        max_transitions=500_000,
        max_model_calls=depth,
    )
    start = time.perf_counter()
    result = ExplicitStateChecker().verify(system, ITES_PROPERTIES, bounds)  # type: ignore[misc]
    elapsed = time.perf_counter() - start
    return {
        "verdict": result.verdict.value,
        "unique_states": result.unique_states,
        "transitions": result.transitions,
        "duplicates": result.duplicate_states,
        "truncated": result.truncated,
        "runtime_seconds": round(elapsed, 3),
    }


CONFIGS: list[tuple[int, int, int, int, int, int]] = [
    (5, 8, 8, 2, 2, 4),
    (5, 8, 8, 3, 2, 4),
    (5, 8, 8, 3, 3, 6),
    (5, 12, 12, 2, 2, 4),
    (5, 16, 16, 2, 2, 4),
    (8, 8, 8, 2, 2, 4),
    (8, 8, 8, 3, 2, 4),
    (8, 12, 12, 2, 2, 4),
    (8, 16, 16, 2, 2, 4),
    (12, 8, 8, 2, 2, 4),
    (12, 12, 12, 2, 2, 4),
]


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []

    for n_p, n_a, n_d, n_nest, n_batch, depth in CONFIGS:
        config_id = f"p{n_p}-a{n_a}-d{n_d}-nest{n_nest}-batch{n_batch}-depth{depth}"
        entry: dict[str, object] = {
            "config": config_id,
            "principals": n_p,
            "actions": n_a,
            "data_items": n_d,
            "max_nested_inputs": n_nest,
            "max_batch_size": n_batch,
            "depth": depth,
        }
        try:
            r = _run_config(n_p, n_a, n_d, n_nest, n_batch, depth)
            entry.update(r)
        except Exception as e:
            entry["error"] = f"{type(e).__name__}: {e}"

        results.append(entry)
        print(
            f"  {config_id}: verdict={entry.get('verdict', 'ERR')} "
            f"states={entry.get('unique_states', '?')} "
            f"transitions={entry.get('transitions', '?')} "
            f"truncated={entry.get('truncated', '?')} "
            f"runtime={entry.get('runtime_seconds', '?')}s",
        )

    verdicts = [str(r.get("verdict", "error")) for r in results]
    evidence = {
        "generated_at": datetime.now(UTC).isoformat(),
        "module": "conflux.evaluation.combinatorial",
        "total_configs": len(results),
        "safe_count": verdicts.count("safe"),
        "bounded_safe_count": verdicts.count("bounded_safe"),
        "unsafe_count": verdicts.count("unsafe"),
        "unknown_count": verdicts.count("unknown"),
        "error_count": verdicts.count("error"),
        "results": results,
    }
    output_path = OUTPUT_DIR / "evidence.json"
    output_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"\nGenerated complex environment evidence: {output_path}")
    print(f"  Configs: {len(results)}")
    print(
        f"  SAFE: {evidence['safe_count']}, BOUNDED_SAFE: {evidence['bounded_safe_count']}, UNSAFE: {evidence['unsafe_count']}, UNKNOWN: {evidence['unknown_count']}, ERROR: {evidence['error_count']}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
