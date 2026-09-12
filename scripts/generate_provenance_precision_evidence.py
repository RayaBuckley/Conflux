"""Generate provenance precision vs utility evidence.

Measures how much utility is lost by conservative may-have-written
provenance and how much authenticated actual-contributor provenance
can recover without broadening the ITES authorisation rule.

Three conditions are compared:

- C0 (requester-only): vulnerable negative control — only the requester
  is in the Principal Context.
- C1 (conservative): all principals who *could* have written the data
  are in the Principal Context (may-have-written overapproximation).
- C2 (authenticated): only principals who *actually* contributed are
  in the Principal Context (under the experiment's trusted provenance
  oracle).

The authorisation rule is identical across all conditions: an action
is permitted only if every principal in the Principal Context is
authorised for that action.  Only the trusted provenance metadata
differs.

Usage::

    python scripts/generate_provenance_precision_evidence.py
    python scripts/generate_provenance_precision_evidence.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

from conflux.domain import (
    DELETE,
    READ,
    SHARE,
    WRITE,
    Permission,
    Principal,
    Provenance,
    ProvenancePrecision,
)
from conflux.verification import (
    enforcement_is_sound,
    measure_overapproximation,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "output" / "runs" / "provenance-precision-v1"

POSSIBLE_AUTHORS = (2, 4, 8, 16)
ACTUAL_CONTRIBUTORS = (1, 2, 4, 8)
HETEROGENEITY_LEVELS = ("low", "medium", "high")
WORKFLOW_DEPTHS = (1, 2, 3)
SEED = 42


def _make_principals(n: int) -> list[Principal]:
    """Create n deterministic principals."""
    return [Principal(id=f"p{i}", name=f"Principal-{i}") for i in range(n)]


def _make_permission_sets(
    principals: list[Principal],
    heterogeneity: str,
    rng: random.Random,
) -> dict[str, frozenset[Permission]]:
    """Assign permission sets to principals based on heterogeneity level."""
    all_perms = frozenset({READ, WRITE, SHARE, DELETE})
    perm_sets: dict[str, frozenset[Permission]] = {}
    for p in principals:
        if heterogeneity == "low":
            perm_sets[p.id] = all_perms
        elif heterogeneity == "medium":
            r = rng.random()
            if r < 0.5:
                perm_sets[p.id] = frozenset({READ, WRITE})
            else:
                perm_sets[p.id] = all_perms
        else:
            r = rng.random()
            if r < 0.33:
                perm_sets[p.id] = frozenset({READ})
            elif r < 0.66:
                perm_sets[p.id] = frozenset({READ, WRITE})
            else:
                perm_sets[p.id] = all_perms
    return perm_sets


def _is_authorised(
    pc_principals: frozenset[Principal],
    perm_sets: dict[str, frozenset[Permission]],
    required: Permission,
) -> bool:
    """ITES intersection rule: all principals in PC must be authorised."""
    return all(required in perm_sets[p.id] for p in pc_principals)


def _generate_task(
    task_id: int,
    n_possible: int,
    k_actual: int,
    heterogeneity: str,
    depth: int,
    rng: random.Random,
) -> dict[str, Any]:
    """Generate one deterministic task fixture.

    Returns a dict with:
    - task_id, parameters
    - possible_authors, actual_contributors
    - requester, required_permission
    - perm_sets (per-principal)
    - ground_truth: securely_achievable | securely_blocked | vulnerable
    """
    all_principals = _make_principals(n_possible)
    perm_sets = _make_permission_sets(all_principals, heterogeneity, rng)
    actual_k = min(k_actual, n_possible)
    actual_contributors = rng.sample(all_principals, actual_k)
    requester = actual_contributors[0]
    possible_authors_set = set(all_principals)
    actual_set = set(actual_contributors)

    required_perms = [WRITE, SHARE, DELETE]
    required = rng.choice(required_perms)

    c0_authorised = _is_authorised(frozenset({requester}), perm_sets, required)
    c1_authorised = _is_authorised(frozenset(possible_authors_set), perm_sets, required)
    c2_authorised = _is_authorised(frozenset(actual_set), perm_sets, required)

    if c2_authorised:
        ground_truth = "securely_achievable"
    elif c0_authorised:
        ground_truth = "vulnerable"
    else:
        ground_truth = "securely_blocked"

    return {
        "task_id": f"task-{task_id:04d}",
        "n_possible": n_possible,
        "k_actual": actual_k,
        "heterogeneity": heterogeneity,
        "depth": depth,
        "requester_id": requester.id,
        "actual_contributor_ids": sorted(p.id for p in actual_contributors),
        "possible_author_ids": sorted(p.id for p in all_principals),
        "required_permission": required.name,
        "perm_sets": {pid: sorted(perm.name for perm in ps) for pid, ps in perm_sets.items()},
        "ground_truth": ground_truth,
        "c0_requester_authorised": c0_authorised,
        "c1_conservative_authorised": c1_authorised,
        "c2_authenticated_authorised": c2_authorised,
    }


def _run_condition(
    task: dict[str, Any],
    condition: str,
) -> dict[str, Any]:
    """Run one condition for one task and return outcome metrics."""
    if condition == "C0":
        pc_ids = {task["requester_id"]}
        precision = ProvenancePrecision.EXACT
    elif condition == "C1":
        pc_ids = set(task["possible_author_ids"])
        precision = ProvenancePrecision.CONSERVATIVE
    elif condition == "C2":
        pc_ids = set(task["actual_contributor_ids"])
        precision = ProvenancePrecision.EXACT
    else:
        raise ValueError(f"Unknown condition: {condition}")

    required = Permission(task["required_permission"])
    perm_sets = {pid: frozenset(Permission(p) for p in perms) for pid, perms in task["perm_sets"].items()}
    pc_principals = frozenset(Principal(id=pid, name=f"Principal-{int(pid[1:])}") for pid in pc_ids)

    authorised = _is_authorised(pc_principals, perm_sets, required)

    actual_set = frozenset(Principal(id=pid, name=f"Principal-{int(pid[1:])}") for pid in task["actual_contributor_ids"])
    security_prov = Provenance(
        principals=pc_principals,
        precision=precision,
        attested=(condition != "C1"),
    )

    overapprox = measure_overapproximation(security_prov, actual_set)
    sound = enforcement_is_sound(security_prov, actual_set) if condition != "C0" else False

    ground_truth = task["ground_truth"]
    if condition == "C0":
        if authorised and ground_truth == "vulnerable":
            outcome = "vulnerable_execution"
        elif authorised:
            outcome = "complete"
        else:
            outcome = "blocked"
    elif condition == "C1":
        outcome = "complete" if authorised else "blocked"
    else:
        outcome = "complete" if authorised else "blocked"

    return {
        "condition": condition,
        "pc_size": len(pc_ids),
        "authorised": authorised,
        "outcome": outcome,
        "overapproximates": overapprox.overapproximates,
        "excess_principals": len(overapprox.excess_principals),
        "is_exact": overapprox.is_exact,
        "enforcement_sound": sound,
    }


def generate() -> dict[str, Any]:
    """Generate the full provenance precision evidence bundle."""
    rng = random.Random(SEED)  # noqa: S311 – deterministic fixture generation, not crypto
    tasks: list[dict[str, Any]] = []
    task_id = 0

    for n_possible in POSSIBLE_AUTHORS:
        for k_actual in ACTUAL_CONTRIBUTORS:
            if k_actual > n_possible:
                continue
            for heterogeneity in HETEROGENEITY_LEVELS:
                for depth in WORKFLOW_DEPTHS:
                    for _rep in range(3):
                        task = _generate_task(task_id, n_possible, k_actual, heterogeneity, depth, rng)
                        tasks.append(task)
                        task_id += 1

    conditions = ("C0", "C1", "C2")
    results: list[dict[str, Any]] = []
    for task in tasks:
        row: dict[str, Any] = {
            "task_id": task["task_id"],
            "n_possible": task["n_possible"],
            "k_actual": task["k_actual"],
            "heterogeneity": task["heterogeneity"],
            "depth": task["depth"],
            "ground_truth": task["ground_truth"],
        }
        for cond in conditions:
            cond_result = _run_condition(task, cond)
            row[f"{cond.lower()}_outcome"] = cond_result["outcome"]
            row[f"{cond.lower()}_pc_size"] = cond_result["pc_size"]
            row[f"{cond.lower()}_authorised"] = cond_result["authorised"]
            row[f"{cond.lower()}_overapproximates"] = cond_result["overapproximates"]
            row[f"{cond.lower()}_excess"] = cond_result["excess_principals"]
            row[f"{cond.lower()}_is_exact"] = cond_result["is_exact"]
            row[f"{cond.lower()}_sound"] = cond_result["enforcement_sound"]
        results.append(row)

    c0_complete = sum(1 for r in results if r["c0_outcome"] == "complete")
    c0_vulnerable = sum(1 for r in results if r["c0_outcome"] == "vulnerable_execution")
    c1_complete = sum(1 for r in results if r["c1_outcome"] == "complete")
    c1_blocked = sum(1 for r in results if r["c1_outcome"] == "blocked")
    c2_complete = sum(1 for r in results if r["c2_outcome"] == "complete")
    c2_blocked = sum(1 for r in results if r["c2_outcome"] == "blocked")

    c1_mean_pc = sum(r["c1_pc_size"] for r in results) / len(results)
    c2_mean_pc = sum(r["c2_pc_size"] for r in results) / len(results)
    c0_mean_pc = sum(r["c0_pc_size"] for r in results) / len(results)

    total = len(results)
    c2_sound_violations = sum(1 for r in results if not r["c2_sound"] and r["c2_authorised"])

    by_n: dict[int, dict[str, float]] = {}
    for n in POSSIBLE_AUTHORS:
        n_rows = [r for r in results if r["n_possible"] == n]
        by_n[n] = {
            "c0_completion": sum(1 for r in n_rows if r["c0_outcome"] == "complete") / len(n_rows),
            "c1_completion": sum(1 for r in n_rows if r["c1_outcome"] == "complete") / len(n_rows),
            "c2_completion": sum(1 for r in n_rows if r["c2_outcome"] == "complete") / len(n_rows),
            "c1_mean_pc": sum(r["c1_pc_size"] for r in n_rows) / len(n_rows),
            "c2_mean_pc": sum(r["c2_pc_size"] for r in n_rows) / len(n_rows),
        }

    by_heterogeneity: dict[str, dict[str, float]] = {}
    for h in HETEROGENEITY_LEVELS:
        h_rows = [r for r in results if r["heterogeneity"] == h]
        by_heterogeneity[h] = {
            "c0_completion": sum(1 for r in h_rows if r["c0_outcome"] == "complete") / len(h_rows),
            "c1_completion": sum(1 for r in h_rows if r["c1_outcome"] == "complete") / len(h_rows),
            "c2_completion": sum(1 for r in h_rows if r["c2_outcome"] == "complete") / len(h_rows),
        }

    return {
        "schema_version": "1",
        "id": "provenance-precision-v1",
        "seed": SEED,
        "conditions": {
            "C0": "requester_only_vulnerable (negative control)",
            "C1": "conservative may-have-written provenance",
            "C2": "authenticated actual-contributor provenance",
        },
        "parameters": {
            "possible_authors": list(POSSIBLE_AUTHORS),
            "actual_contributors": list(ACTUAL_CONTRIBUTORS),
            "heterogeneity_levels": list(HETEROGENEITY_LEVELS),
            "workflow_depths": list(WORKFLOW_DEPTHS),
            "repetitions_per_cell": 3,
        },
        "tasks": tasks,
        "results": results,
        "summary": {
            "total_tasks": total,
            "c0_completion_rate": c0_complete / total,
            "c0_vulnerable_rate": c0_vulnerable / total,
            "c1_completion_rate": c1_complete / total,
            "c1_blocked_rate": c1_blocked / total,
            "c2_completion_rate": c2_complete / total,
            "c2_blocked_rate": c2_blocked / total,
            "utility_recovery": (c2_complete - c1_complete) / total,
            "c0_mean_pc": c0_mean_pc,
            "c1_mean_pc": c1_mean_pc,
            "c2_mean_pc": c2_mean_pc,
            "pc_reduction": c1_mean_pc - c2_mean_pc,
            "c2_sound_violations": c2_sound_violations,
        },
        "by_n_possible_authors": {str(k): v for k, v in by_n.items()},
        "by_heterogeneity": by_heterogeneity,
        "claim_boundary": (
            "Greater authenticated provenance precision can recover legitimate task utility "
            "without changing the authority-confinement rule, under the trusted provenance "
            "assumptions of the experiment."
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
    parser = argparse.ArgumentParser(description="Generate provenance precision vs utility evidence.")
    parser.add_argument("--check", action="store_true", help="Verify retained bundle matches regeneration.")
    arguments = parser.parse_args()

    if arguments.check:
        if _check(OUTPUT):
            print("Provenance precision evidence regeneration check passed")
            return 0
        print("Provenance precision evidence is stale or missing", file=sys.stderr)
        return 1

    bundle = generate()
    _write_bundle(OUTPUT, bundle)
    print(f"Generated provenance precision evidence: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
