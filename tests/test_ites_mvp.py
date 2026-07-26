from __future__ import annotations

from conflux.core import Principal, Provenance
from conflux.core.permissions import Permission
from conflux.research.mvp import (
    MVPExplorer,
    MVPNested,
    MVPPrimitive,
    MVPStatus,
    artifact,
)


def _principals() -> tuple[Principal, Principal]:
    alice = Principal(
        "alice",
        "Alice",
        permissions=frozenset({Permission("read"), Permission("write")}),
    )
    bob = Principal("bob", "Bob", permissions=frozenset({Permission("read")}))
    return alice, bob


def test_mvp_blocks_mixed_context_primitive() -> None:
    alice, bob = _principals()
    seed = artifact("seed", alice, label="seed")
    mixed = artifact("mixed", bob, label="mixed")

    def model(_inputs):
        return (MVPPrimitive(Permission("write"), operation="write"),)

    report = MVPExplorer(model, max_calls=2).run(object(), frozenset({seed, mixed}))

    assert report.privilege_escalation is False
    assert len(report.blocked) == 1
    assert report.blocked[0].reason == "principal_lacks_permission"
    assert report.blocked[0].influencers == frozenset({alice, bob})


def test_mvp_nested_execution_accumulates_provenance() -> None:
    alice, bob = _principals()
    seed = artifact("seed", alice, label="seed")
    nested = artifact("nested", alice, label="nested")
    calls: list[frozenset] = []

    def model(inputs):
        calls.append(inputs)
        if len(calls) == 1:
            return (MVPNested(frozenset({nested})),)
        return (MVPPrimitive(Permission("write"), operation="write"),)

    report = MVPExplorer(model, max_calls=3).run(object(), frozenset({seed}))

    assert len(calls) == 2
    assert report.declared[0].reason == "nested_inputs_readable"
    assert report.declared[-1].influencers == frozenset({alice})
    assert report.terminal_states[-1].status is MVPStatus.TERMINAL
    assert bob not in report.terminal_states[-1].influencers


def test_mvp_sibling_branches_share_parent_and_do_not_mutate_each_other() -> None:
    alice, _ = _principals()
    seed = artifact("seed", alice, label="seed")

    def model(_inputs):
        return (
            MVPPrimitive(Permission("read"), operation="read-a"),
            MVPPrimitive(Permission("read"), operation="read-b"),
        )

    report = MVPExplorer(model, max_calls=1).run(object(), frozenset({seed}))

    assert report.calls_used == 1
    assert report.branch_count == 2
    assert {state.branch_id for state in report.terminal_states} == {"root.1", "root.2"}
    assert all(len(state.trace) == 1 for state in report.terminal_states)
    assert all(state.inputs == frozenset({seed}) for state in report.terminal_states)


def test_mvp_budget_is_shared_across_nested_branches_and_marks_incomplete() -> None:
    alice, _ = _principals()
    seed = artifact("seed", alice, label="seed")
    nested = artifact("nested", alice, label="nested")

    def model(_inputs):
        return (MVPNested(frozenset({nested})),)

    report = MVPExplorer(model, max_calls=2).run(object(), frozenset({seed}))

    assert report.calls_used == 2
    assert report.incomplete is True
    assert any(state.status is MVPStatus.INCOMPLETE for state in report.terminal_states)


def test_mvp_report_is_serialisable_and_deterministic() -> None:
    alice, _ = _principals()
    seed = artifact("seed", alice, label="seed")

    def model(_inputs):
        return (
            MVPPrimitive(Permission("read"), operation="z"),
            MVPPrimitive(Permission("read"), operation="a"),
        )

    first = MVPExplorer(model, max_calls=1).run(object(), frozenset({seed})).to_dict()
    second = MVPExplorer(model, max_calls=1).run(object(), frozenset({seed})).to_dict()

    assert first == second
    assert [item["proposal"]["operation"] for item in first["declared"]] == ["a", "z"]


def test_mvp_artifact_helper_has_single_principal_provenance() -> None:
    alice, _ = _principals()
    item = artifact("value", alice)

    assert item.provenance == Provenance.from_principal(alice)
