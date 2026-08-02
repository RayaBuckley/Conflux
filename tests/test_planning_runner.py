"""Four planning modes use identical tasks and action-time ITES mediation."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from conflux.domain import canonical_json, fingerprint
from conflux.experiments import ExperimentProtocol, LocalModelSpec, load_planning_diagnostic_suite, run_planning_comparison
from conflux.ports import LocalModelPreflight, LocalModelRequest, LocalModelResponse

ROOT = Path(__file__).resolve().parents[1]


def _protocol() -> ExperimentProtocol:
    return ExperimentProtocol(
        id="planning-local-v1",
        track="planning",
        suite={"id": "planning-diagnostic-v1", "version": "1"},
        source_commit="a" * 40,
        inputs={},
        model=LocalModelSpec(
            "transformers",
            "local/test",
            "revision",
            "b" * 64,
            "local/test",
            "revision",
            "1",
            0,
            0.0,
            1.0,
            128,
            2048,
            "cpu",
            "float32",
            "test",
        ),
        prompts={"planner": "1"},
        seeds=(0,),
        repetitions=1,
        bounds={"max_model_calls": 4, "max_steps": 4},
        environment={"kind": "modeled"},
        output_directory="runs/planning-local-v1",
        rerun_command=("conflux", "plan", "compare", "--execute-local"),
    )


@dataclass
class _Model:
    def preflight(self) -> LocalModelPreflight:
        return LocalModelPreflight("transformers", "local/test", True, "none", None)

    def generate(self, request: LocalModelRequest) -> LocalModelResponse:
        user = request.user_prompt
        actions = _actions_for(user)
        if request.schema_name == "modeled_program_v1":
            payload: dict[str, object] = {
                "schema_version": "1",
                "id": request.request_id,
                "max_steps": 4,
                "effects": [
                    {
                        "id": f"effect-{index}",
                        "action_id": action["id"],
                        "dependencies": [] if index == 0 else [f"effect-{index - 1}"],
                        "declared_reads": action["declared_reads"],
                        "declared_writes": action["declared_writes"],
                    }
                    for index, action in enumerate(actions)
                ],
            }
        else:
            payload = {"action_ids": [action["id"] for action in actions]}
        return LocalModelResponse(request.request_id, "local/test", payload, 10, 3, 1, fingerprint(payload))


def _actions_for(user_prompt: str) -> list[dict[str, object]]:
    value = json.loads(user_prompt)
    actions = value["actions"]
    attempted = set(value["attempted"])
    available = [action for action in actions if action["id"] not in attempted]
    return available or actions


def test_suite_has_exactly_eight_distinct_diagnostics() -> None:
    scenarios = load_planning_diagnostic_suite(ROOT / "experiments" / "suites" / "planning-diagnostic-v1.yaml")
    assert len(scenarios) == 8
    assert len({scenario.id for scenario in scenarios}) == 8
    assert all(scenario.distinguishes for scenario in scenarios)


def test_runner_covers_four_modes_and_reports_security_separately() -> None:
    result = run_planning_comparison(_protocol(), _Model())
    observations = result["observations"]
    assert isinstance(observations, list) and len(observations) == 32
    assert {item["mode"] for item in observations} == {"reactive", "static", "dynamic", "dynamic_code"}
    assert all(item["security_violations"] == 0 for item in observations)
    assert all("modeled_effects" in item for item in observations)
    assert result["task_ids"] == sorted({item["task_id"] for item in observations})
    assert canonical_json(result) == canonical_json(run_planning_comparison(_protocol(), _Model()))


def test_protocol_can_select_the_two_laptop_smoke_scenarios() -> None:
    protocol = _protocol()
    protocol = replace(
        protocol,
        suite={
            "id": "planning-diagnostic-v1",
            "version": "1",
            "case_ids": [
                "direct-authorised-effect",
                "blocked-action-recovery",
            ],
        },
    )
    result = run_planning_comparison(protocol, _Model())
    observations = result["observations"]
    assert isinstance(observations, list) and len(observations) == 8
    assert result["task_ids"] == [
        "blocked-action-recovery",
        "direct-authorised-effect",
    ]


def test_dynamic_modes_replan_after_block_or_provider_failure() -> None:
    result = run_planning_comparison(_protocol(), _Model())
    observations = result["observations"]
    assert isinstance(observations, list)
    selected = [
        item
        for item in observations
        if item["task_id"] in {"blocked-action-recovery", "provider-failure-recovery"}
        and item["mode"] in {"dynamic", "dynamic_code", "reactive"}
    ]
    assert selected and all(item["replans"] >= 1 for item in selected)
    assert any(item["utility_completed"] for item in selected)


def test_mixed_and_revoked_authority_are_blocked_at_action_time() -> None:
    result = run_planning_comparison(_protocol(), _Model())
    observations = result["observations"]
    assert isinstance(observations, list)
    selected = [
        item
        for item in observations
        if item["task_id"] in {"mixed-principal-input", "action-time-revocation"}
    ]
    assert all(item["legitimate_blocks"] >= 1 for item in selected)
    assert all(item["security_violations"] == 0 for item in selected)
