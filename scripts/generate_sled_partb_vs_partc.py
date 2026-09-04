"""Compare Part B trace enumeration vs Part C state exploration on complex environments.

Uses the ported ReproductionEvaluator from generate_partb_reproduction.py
to run counter-based trace enumeration (Part B style) on new environments
beyond the original three. Simultaneously runs the current canonical-state
BFS (Part C style) on equivalent environments via CombinatorialVerificationSystem.

Comparison metrics: trace count, unique states, compression ratio, verdict
agreement, runtime.

Usage:
    python scripts/generate_sled_partb_vs_partc.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any

from generate_partb_reproduction import (
    Data,
    Environment,
    MyDefence,
    ReproductionEvaluator,
    User,
)

from conflux.application import DecisionPipeline
from conflux.domain import (
    READ,
    DataItem,
    EnvironmentSnapshot,
    Principal,
    ResourceRef,
    Session,
)
from conflux.domain import (
    PrimitiveAction as DomainPrimitiveAction,
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
    InMemoryAuthorisationPolicy,
    PolicyGrant,
    SessionVisibilityPolicy,
)

OUTPUT_DIR = Path("research/output/runs/sled_partb_vs_partc")

ITES_PROPERTIES = (
    NoUnauthorisedAuthorisation(),
    NoForbiddenObservation(),
    PrincipalContextMonotonicity(),
    ProvenancePreserved(),
)

MAX_TRACE_CAP = 2_000_000


def _make_partb_env(n_principals: int, n_actions: int, n_data: int) -> tuple[Environment, set[Data]]:
    """Create a Part B environment with the given complexity."""
    names = ("alice", "bob", "carol", "dave", "eve", "frank", "grace", "heidi", "ivan", "judy", "karl", "leo")
    action_names = tuple(f"action_{i}" for i in range(n_actions))

    users: list[User] = []
    for i in range(n_principals):
        perms = frozenset({action_names[i % n_actions], action_names[(i + 1) % n_actions]}) if n_actions > 0 else frozenset()
        users.append(User(perms, names[i]))

    data_items: list[Data] = []
    for i in range(n_data):
        author = users[i % n_principals]
        readers = frozenset({users[i % n_principals], users[(i + 1) % n_principals]})
        data_items.append(Data(frozenset({author}), readers, f"data_{i}"))

    env = Environment(frozenset(data_items))
    initial = {data_items[0]} if data_items else set()
    return env, initial


def _run_partb(env: Environment, initial: set[Data]) -> dict[str, Any]:
    """Run Part B trace enumeration and return metrics."""
    start = time.perf_counter()
    evaluator = ReproductionEvaluator(MyDefence, env, initial)
    elapsed = time.perf_counter() - start
    result: dict[str, Any] = dict(evaluator.result())
    result["runtime_seconds"] = round(elapsed, 3)
    return result


def _run_partc(n_principals: int, n_actions: int, n_data: int) -> dict[str, Any]:
    """Run Part C state exploration on an equivalent environment."""
    names = ("alice", "bob", "carol", "dave", "eve", "frank", "grace", "heidi", "ivan", "judy", "karl", "leo")
    principals = tuple(Principal(names[i], names[i].capitalize()) for i in range(n_principals))
    session = Session("cmp-session", frozenset(principals))
    resource = ResourceRef(provider="fs", resource_id="file1", resource_type="file")
    grants = frozenset(PolicyGrant(principals[i].id, "read", resource.resource_id) for i in range(n_principals))

    actions: tuple[DomainPrimitiveAction, ...] = tuple(
        DomainPrimitiveAction(
            id=f"action_{i}",
            operation="read",
            permission=READ,
            resource=resource,
        )
        for i in range(n_actions)
    )

    data_items = tuple(
        DataItem(
            id=f"item-{i}",
            value=f"data-{i}",
            authors=frozenset({principals[i % n_principals]}),
            readers=frozenset(principals),
        )
        for i in range(n_data)
    )
    env_snapshot = EnvironmentSnapshot(
        id=f"cmp-p{n_principals}-a{n_actions}-d{n_data}",
        data=data_items,
        resources=(resource,),
    )

    artifacts = env_snapshot.artifacts()
    nested_ids: set[str] = set()
    for r in range(1, min(3, len(artifacts)) + 1):
        for combo in combinations(artifacts, r):
            nested_ids.add(f"nested-{r}-{'-'.join(a.id for a in combo)}")
    all_action_ids = frozenset(a.id for a in actions) | frozenset(nested_ids)

    pipeline = DecisionPipeline(
        InMemoryAuthorisationPolicy(grants),
        AllowInternalReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(all_action_ids),
    )
    kernel = TransitionKernel(pipeline)
    system = CombinatorialVerificationSystem.from_environment(
        environment=env_snapshot,
        primitive_actions=actions,
        kernel=kernel,
        session=session,
        max_batch_size=2,
        max_nested_inputs=3,
        max_model_calls=3,
    )
    bounds = VerificationBounds(
        max_depth=6,
        max_states=50_000,
        max_transitions=250_000,
        max_model_calls=6,
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


PARTB_CONFIGS = [
    (2, 3, 3),
    (3, 4, 4),
    (3, 5, 5),
    (4, 4, 4),
    (5, 4, 4),
]

PARTC_ONLY_CONFIGS = [
    (3, 8, 8),
    (5, 8, 8),
    (5, 8, 12),
    (5, 12, 12),
    (8, 8, 8),
    (8, 12, 12),
    (8, 16, 16),
    (12, 8, 8),
    (12, 12, 12),
]


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []

    for n_principals, n_actions, n_data in PARTB_CONFIGS:
        config_id = f"p{n_principals}-a{n_actions}-d{n_data}"
        entry: dict[str, object] = {
            "config": config_id,
            "principals": n_principals,
            "actions": n_actions,
            "data_items": n_data,
        }

        env_b, initial_b = _make_partb_env(n_principals, n_actions, n_data)
        try:
            partb = _run_partb(env_b, initial_b)
            entry["partb_traces"] = partb["total_traces"]
            entry["partb_states"] = partb["unique_canonical_states"]
            entry["partb_incomplete"] = partb["incomplete_traces"]
            entry["partb_runtime"] = partb["runtime_seconds"]
            if partb["total_traces"] > 0:
                entry["compression_ratio"] = round(partb["total_traces"] / max(partb["unique_canonical_states"], 1), 1)
            else:
                entry["compression_ratio"] = 0
        except Exception as e:
            entry["partb_error"] = f"{type(e).__name__}: {e}"

        try:
            partc = _run_partc(n_principals, n_actions, n_data)
            entry["partc_verdict"] = partc["verdict"]
            entry["partc_states"] = partc["unique_states"]
            entry["partc_transitions"] = partc["transitions"]
            entry["partc_truncated"] = partc["truncated"]
            entry["partc_runtime"] = partc["runtime_seconds"]
        except Exception as e:
            entry["partc_error"] = f"{type(e).__name__}: {e}"

        if "partb_states" in entry and "partc_states" in entry:
            entry["state_count_agree"] = entry["partb_states"] == entry["partc_states"]

        results.append(entry)
        print(
            f"  {config_id}: partB={entry.get('partb_traces', 'ERR')} traces, partC={entry.get('partc_verdict', 'ERR')} ({entry.get('partc_states', '?')} states)",
        )

    for n_principals, n_actions, n_data in PARTC_ONLY_CONFIGS:
        config_id = f"p{n_principals}-a{n_actions}-d{n_data}"
        entry = {
            "config": config_id,
            "principals": n_principals,
            "actions": n_actions,
            "data_items": n_data,
            "partb_skipped": "trace_count_too_large",
        }

        try:
            partc = _run_partc(n_principals, n_actions, n_data)
            entry["partc_verdict"] = partc["verdict"]
            entry["partc_states"] = partc["unique_states"]
            entry["partc_transitions"] = partc["transitions"]
            entry["partc_truncated"] = partc["truncated"]
            entry["partc_runtime"] = partc["runtime_seconds"]
        except Exception as e:
            entry["partc_error"] = f"{type(e).__name__}: {e}"

        results.append(entry)
        print(
            f"  {config_id}: partB=skipped, partC={entry.get('partc_verdict', 'ERR')} ({entry.get('partc_states', '?')} states)",
        )

    evidence = {
        "generated_at": datetime.now(UTC).isoformat(),
        "module": "partb_vs_partc_comparison",
        "total_configs": len(results),
        "results": results,
    }
    output_path = OUTPUT_DIR / "evidence.json"
    output_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"\nGenerated Part B vs Part C comparison evidence: {output_path}")
    print(f"  Configs: {len(results)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
