"""AgentDojo tool translation preserves provenance and certificate binding."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.adapters.benchmarks.agentdojo_local import AgentDojoActionMediator
from conflux.domain import Action
from conflux.ports import ProviderResult


@dataclass
class _Executor:
    calls: list[tuple[str, str]]

    def execute(self, action: Action, *, certificate_id: str, action_fingerprint: str) -> ProviderResult:
        self.calls.append((certificate_id, action_fingerprint))
        return ProviderResult(True, outcome=f"result:{action.id}")


def test_attacked_search_adds_injection_provenance_and_blocks_delete() -> None:
    executor = _Executor([])
    mediator = AgentDojoActionMediator(attacked=True, defence="ites")
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
    assert mediator.mediate("search_emails", {}, executor).success
    assert mediator.mediate("delete_file", {"file_id": "13"}, executor).success
    assert len(executor.calls) == 2
    unknown = mediator.mediate("run_shell", {"command": "whoami"}, executor)
    assert not unknown.success and unknown.error == "unsupported_tool"
    assert len(executor.calls) == 2


def test_benign_results_do_not_manufacture_injection_principal() -> None:
    mediator = AgentDojoActionMediator(attacked=False, defence="ites")
    assert mediator.mediate("search_emails", {}, _Executor([])).success
    assert {principal.id for principal in mediator.environment.data[-1].authors} == {"agentdojo:user"}
