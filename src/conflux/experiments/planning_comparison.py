"""Strict aggregation for the report's four-way planning comparison."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator

from conflux.adapters.scenarios import load_schema
from conflux.domain import canonical_json


class PlanningMode(StrEnum):
    REACTIVE = "reactive"
    STATIC = "static"
    DYNAMIC = "dynamic"
    DYNAMIC_CODE = "dynamic_code"


@dataclass(frozen=True, slots=True)
class PlanningObservation:
    task_id: str
    mode: PlanningMode
    security_passed: bool
    utility_completed: bool
    status: str
    calls: int
    tokens: int
    latency_ms: int
    replans: int
    plan_nodes: int
    sensitive_reads: int
    max_context_size: int

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "PlanningObservation":
        Draft202012Validator(load_schema("planning-observation.schema.json")).validate(value)
        return cls(
            task_id=cast(str, value["task_id"]),
            mode=PlanningMode(cast(str, value["mode"])),
            security_passed=cast(bool, value["security_passed"]),
            utility_completed=cast(bool, value["utility_completed"]),
            status=cast(str, value["status"]),
            calls=cast(int, value["calls"]),
            tokens=cast(int, value["tokens"]),
            latency_ms=cast(int, value["latency_ms"]),
            replans=cast(int, value["replans"]),
            plan_nodes=cast(int, value["plan_nodes"]),
            sensitive_reads=cast(int, value["sensitive_reads"]),
            max_context_size=cast(int, value["max_context_size"]),
        )


def aggregate_planning_comparison(
    observations: tuple[PlanningObservation, ...],
) -> dict[str, object]:
    if not observations:
        raise ValueError("planning comparison requires observations")
    grouped: dict[PlanningMode, list[PlanningObservation]] = defaultdict(list)
    for observation in observations:
        grouped[observation.mode].append(observation)
    missing = set(PlanningMode) - set(grouped)
    if missing:
        raise ValueError(f"planning comparison missing modes:{','.join(sorted(missing))}")
    task_sets = {mode: {item.task_id for item in items} for mode, items in grouped.items()}
    if len({frozenset(tasks) for tasks in task_sets.values()}) != 1:
        raise ValueError("planning comparison modes must use identical task IDs")
    modes: dict[str, object] = {}
    for mode in PlanningMode:
        items = sorted(grouped[mode], key=lambda item: item.task_id)
        modes[mode.value] = {
            "runs": len(items),
            "security_passed": sum(item.security_passed for item in items),
            "utility_completed": sum(item.utility_completed for item in items),
            "incomplete": sum(item.status != "complete" for item in items),
            "calls": sum(item.calls for item in items),
            "tokens": sum(item.tokens for item in items),
            "latency_ms": sum(item.latency_ms for item in items),
            "replans": sum(item.replans for item in items),
            "plan_nodes": sum(item.plan_nodes for item in items),
            "sensitive_reads": sum(item.sensitive_reads for item in items),
            "max_context_size": max(item.max_context_size for item in items),
            "statuses": [
                {"task_id": item.task_id, "status": item.status} for item in items
            ],
        }
    result: dict[str, object] = {
        "schema_version": "1",
        "task_ids": sorted(next(iter(task_sets.values()))),
        "modes": modes,
    }
    Draft202012Validator(load_schema("planning-comparison-result.schema.json")).validate(result)
    return result


def generate_planning_report(input_directory: Path, output: Path) -> dict[str, object]:
    observations: list[PlanningObservation] = []
    for path in sorted(input_directory.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"planning observation root must be object:{path}")
        observations.append(PlanningObservation.from_dict(cast(dict[str, object], value)))
    result = aggregate_planning_comparison(tuple(observations))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical_json(result) + "\n", encoding="utf-8", newline="\n")
    return result


__all__ = [
    "PlanningMode",
    "PlanningObservation",
    "aggregate_planning_comparison",
    "generate_planning_report",
]
