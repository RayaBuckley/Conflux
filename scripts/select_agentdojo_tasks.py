"""Freeze or check the stratified AgentDojo task selection.

Reads the installed benchmark: for every (suite, injection vector) stratum it records the
lowest user-task id that offers the vector, skipping tasks the retained pilots already ran.
The benchmark package is required here; the gate validates the frozen manifest without it.

Usage:
    python scripts/select_agentdojo_tasks.py                 # rewrite the manifest
    python scripts/select_agentdojo_tasks.py --check         # drift check, writes nothing
    python scripts/select_agentdojo_tasks.py --per-stratum 2 # two pairs per stratum
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from conflux.adapters.benchmarks.agentdojo_v1 import BENCHMARK_VERSION, PACKAGE_VERSION
from conflux.experiments.agentdojo_selection import (
    SuiteFacts,
    build_manifest,
    selection_drift,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SELECTION = Path("research/experiments/manifests/agentdojo-stratified-selection-v1.json")
SUITE_IDS = ("banking", "slack", "travel", "workspace")

# Pairs the retained pilots already executed (the workspace expanded cell and the nf4 cell); a
# breadth sweep must not count them twice.
PILOT_TASK_IDS: dict[str, tuple[str, ...]] = {
    "workspace": ("user_task_14", "user_task_16", "user_task_17", "user_task_22", "user_task_39"),
}


def measure_suite(suite_id: str) -> SuiteFacts:
    """Read one suite's task and vector shape through the pinned benchmark package."""
    from agentdojo.attacks.base_attacks import BaseAttack
    from agentdojo.task_suite.load_suites import get_suite

    upstream = get_suite(BENCHMARK_VERSION, suite_id)
    defaults = tuple(sorted(upstream.get_injection_vector_defaults()))
    attack = BaseAttack.__new__(BaseAttack)  # only get_injection_candidates runs, never the pipeline
    attack.task_suite = upstream
    attack.canary_injections = {vector: f"<CANARY---{vector}--->" for vector in defaults}
    candidates: dict[str, tuple[str, ...]] = {}
    for task_id, task in sorted(upstream.user_tasks.items()):
        try:
            candidates[task_id] = tuple(sorted(attack.get_injection_candidates(task)))
        except ValueError:
            candidates[task_id] = ()
    return SuiteFacts(
        suite_id=suite_id,
        benchmark_version="v" + ".".join(str(part) for part in upstream.benchmark_version),
        user_task_ids=tuple(sorted(upstream.user_tasks)),
        default_vectors=defaults,
        candidates=candidates,
    )


def build(args: argparse.Namespace) -> dict[str, object]:
    """Measure every suite and return the manifest a run of this script would freeze."""
    return build_manifest(
        facts=[measure_suite(suite_id) for suite_id in SUITE_IDS],
        per_stratum=args.per_stratum,
        excluded_task_ids=PILOT_TASK_IDS,
        package_version=PACKAGE_VERSION,
        benchmark_pin=BENCHMARK_VERSION,
        generated_utc=args.generated_utc,
        command=f"python scripts/select_agentdojo_tasks.py --per-stratum {args.per_stratum}",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", default=str(DEFAULT_SELECTION), help="manifest to write or check")
    parser.add_argument("--per-stratum", type=int, default=1, help="pairs to take per stratum")
    parser.add_argument("--check", action="store_true", help="compare with the installed benchmark, write nothing")
    parser.add_argument("--generated-utc", default="", help="timestamp to record (defaults to now)")
    args = parser.parse_args(argv)
    args.generated_utc = args.generated_utc or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    selection = Path(args.selection)
    if not selection.is_absolute():
        selection = ROOT / selection
    measured = build(args)
    problems = validate_manifest(measured)
    if problems:
        print("measured manifest is not sound:")
        print("\n".join(f"- {problem}" for problem in problems))
        return 1
    if args.check:
        if not selection.exists():
            print(f"{selection} does not exist; run without --check to freeze a selection")
            return 1
        frozen = json.loads(selection.read_text(encoding="utf-8"))
        frozen_problems = validate_manifest(frozen)
        if frozen_problems:
            print(f"{selection} is not sound:")
            print("\n".join(f"- {problem}" for problem in frozen_problems))
            return 1
        report = selection_drift(frozen, measured)
        if report != ["selection matches the installed benchmark"]:
            print("\n".join(report))
            return 1
        print(report[0])
        return 0
    selection.parent.mkdir(parents=True, exist_ok=True)
    selection.write_text(json.dumps(measured, indent=2) + "\n", encoding="utf-8")
    totals = measured["totals"]
    print(f"wrote {selection} ({selection.stat().st_size} bytes)")
    print(f"totals: {json.dumps(totals, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
