from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from conflux.experiments import (
    PlanningMode,
    PlanningObservation,
    aggregate_planning_comparison,
    generate_planning_report,
)


def _observation(mode: PlanningMode, task_id: str = "task") -> PlanningObservation:
    return PlanningObservation(
        task_id,
        mode,
        security_passed=mode != PlanningMode.REACTIVE,
        utility_completed=True,
        status="complete" if mode != PlanningMode.DYNAMIC_CODE else "bound_reached",
        calls=2,
        tokens=20,
        latency_ms=10,
        replans=1,
        plan_nodes=3,
        sensitive_reads=1,
        max_context_size=2,
    )


def test_aggregate_separates_security_utility_and_incomplete_runs() -> None:
    result = aggregate_planning_comparison(tuple(_observation(mode) for mode in PlanningMode))
    modes = cast(dict[str, dict[str, object]], result["modes"])
    reactive = modes["reactive"]
    dynamic_code = modes["dynamic_code"]
    assert reactive["security_passed"] == 0
    assert reactive["utility_completed"] == 1
    assert dynamic_code["incomplete"] == 1


def test_aggregate_requires_all_modes_and_identical_tasks() -> None:
    with pytest.raises(ValueError, match="missing modes"):
        aggregate_planning_comparison((_observation(PlanningMode.REACTIVE),))
    observations = tuple(
        _observation(mode, "different" if mode == PlanningMode.STATIC else "task")
        for mode in PlanningMode
    )
    with pytest.raises(ValueError, match="identical task IDs"):
        aggregate_planning_comparison(observations)


def test_report_generation_reads_strict_observations(tmp_path: Path) -> None:
    source = tmp_path / "raw"
    source.mkdir()
    for mode in PlanningMode:
        observation = _observation(mode)
        payload = {
            "task_id": observation.task_id,
            "mode": observation.mode.value,
            "security_passed": observation.security_passed,
            "utility_completed": observation.utility_completed,
            "status": observation.status,
            "calls": observation.calls,
            "tokens": observation.tokens,
            "latency_ms": observation.latency_ms,
            "replans": observation.replans,
            "plan_nodes": observation.plan_nodes,
            "sensitive_reads": observation.sensitive_reads,
            "max_context_size": observation.max_context_size,
        }
        (source / f"{mode.value}.json").write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "result.json"
    result = generate_planning_report(source, output)
    assert json.loads(output.read_text()) == result
