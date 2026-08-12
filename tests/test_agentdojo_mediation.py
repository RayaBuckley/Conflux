"""AgentDojo tool translation preserves provenance and certificate binding."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from conflux.adapters.benchmarks.agentdojo_annotations import (
    AnnotationProfile,
    pilot_annotations,
)
from conflux.adapters.benchmarks.agentdojo_local import AgentDojoActionMediator
from conflux.domain import Action
from conflux.ports import ProviderResult

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class _Executor:
    calls: list[tuple[str, str]]

    def execute(self, action: Action, *, certificate_id: str, action_fingerprint: str) -> ProviderResult:
        self.calls.append((certificate_id, action_fingerprint))
        return ProviderResult(True, outcome=f"result:{action.id}")


def test_attacked_search_adds_injection_provenance_and_blocks_delete() -> None:
    executor = _Executor([])
    mediator = AgentDojoActionMediator(attacked=True, defence="ites_conservative")
    assert {principal.id for principal in mediator.session.participants} == {
        "agentdojo:user"
    }
    assert mediator.mediate("search_emails", {"query": "hiking"}, executor).success
    assert len(executor.calls) == 1 and all(executor.calls[0])
    assert {principal.id for principal in mediator.environment.data[-1].authors} == {
        "agentdojo:user",
        "agentdojo:injection",
    }
    blocked = mediator.mediate("delete_file", {"file_id": "13"}, executor)
    assert not blocked.success and blocked.error == "policy_blocked"
    assert len(executor.calls) == 1
    assert mediator.records[-1]["outcome"] == "blocked"


def test_no_defence_executes_same_injected_delete_and_unknown_tools_deny() -> None:
    executor = _Executor([])
    mediator = AgentDojoActionMediator(attacked=True, defence="no_defence")
    assert mediator.mediate("search_emails", {"query": "hiking"}, executor).success
    assert mediator.mediate("delete_file", {"file_id": "13"}, executor).success
    assert len(executor.calls) == 2
    unknown = mediator.mediate("run_shell", {"command": "whoami"}, executor)
    assert not unknown.success and unknown.error == "unsupported_tool"
    assert len(executor.calls) == 2


def test_benign_conservative_results_introduce_external_but_not_injection() -> None:
    mediator = AgentDojoActionMediator(attacked=False, defence="ites_conservative")
    assert mediator.mediate("search_emails", {"query": "hiking"}, _Executor([])).success
    ids = {principal.id for principal in mediator.environment.data[-1].authors}
    assert ids == {"agentdojo:user", "agentdojo:external"}
    assert "agentdojo:injection" not in ids


def test_benign_oracle_uses_ground_truth_and_annotations_are_frozen() -> None:
    mediator = AgentDojoActionMediator(attacked=False, defence="ites_oracle")
    assert mediator.mediate("search_emails", {"query": "hiking"}, _Executor([])).success
    assert {principal.id for principal in mediator.environment.data[-1].authors} == {"agentdojo:user"}
    conservative = pilot_annotations(AnnotationProfile.CONSERVATIVE)
    oracle = pilot_annotations(AnnotationProfile.ORACLE)
    assert conservative.fingerprint != oracle.fingerprint
    assert conservative.operations["delete_file"].roles["file_id"].value == "resource"


def test_missing_unknown_and_unreviewed_selector_arguments_deny() -> None:
    mediator = AgentDojoActionMediator(attacked=False, defence="ites_oracle")
    executor = _Executor([])
    assert mediator.mediate("search_emails", {}, executor).error == "unsupported_arguments"
    assert (
        mediator.mediate("search_emails", {"query": "x", "recipient": "y"}, executor).error
        == "unsupported_arguments"
    )
    assert mediator.mediate("delete_file", {"file_id": "999"}, executor).error == "policy_blocked"
    assert not executor.calls


def test_reviewed_annotations_match_checked_experiment_inputs() -> None:
    schemas = json.loads(
        (ROOT / "experiments/suites/agentdojo-tool-schemas-v1.json").read_text(
            encoding="utf-8"
        )
    )
    exceptions = json.loads(
        (
            ROOT
            / "experiments/suites/agentdojo-annotation-exceptions-v1.json"
        ).read_text(encoding="utf-8")
    )
    annotations = pilot_annotations(AnnotationProfile.CONSERVATIVE)
    assert schemas["operations"] == {
        name: {
            "arguments": {key: role.value for key, role in sorted(schema.roles.items())},
            "version": schema.version,
        }
        for name, schema in sorted(annotations.operations.items())
    }
    assert exceptions["reviewed_values"] == {
        key: list(values) for key, values in annotations.reviewed_values.items()
    }
