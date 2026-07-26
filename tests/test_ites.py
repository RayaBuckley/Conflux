"""
Tests for the ITES defence layer.

These tests exercise the mediator-backed ITES implementation and verify the
observable behaviour of the defence. The internal implementation may evolve,
but these behavioural guarantees should remain stable.
"""

from __future__ import annotations

from conflux.core import Artifact, Principal, Provenance
from conflux.core.actions import NestedExecutionAction, PrimitiveAction
from conflux.core.permissions import Permission
from conflux.ites import Guarantee
from conflux.ites.reference import ReferenceITES
from conflux.sled.environment import Data


def _initial_inputs() -> tuple[Principal, frozenset[Artifact[Data]]]:
    alice = Principal("alice", "Alice", permissions=frozenset({Permission("approve")}))

    seed = Data(
        authors=frozenset({alice}),
        readers=frozenset({alice}),
        tag="seed",
    )

    artifacts = frozenset(
        {
            Artifact(
                value=seed,
                provenance=Provenance.from_principal(alice),
            )
        }
    )

    return alice, artifacts


def test_reference_ites_declares_authorised_primitive_proposals() -> None:
    _, initial_inputs = _initial_inputs()

    llm_inputs: list[frozenset[Artifact[object]]] = []
    declared: list[object] = []

    def llm_call(
        inputs: frozenset[Artifact[object]],
    ) -> frozenset[object]:
        llm_inputs.append(inputs)
        return frozenset(
            {
                PrimitiveAction(
                    permission="approve",
                    provider_operation="approve",
                    inputs=inputs,
                ),
            }
        )

    def declare(item: object) -> None:
        declared.append(item)

    report = ReferenceITES().run(
        environment=object(),
        initial_inputs=initial_inputs,
        llm_call=llm_call,
        declare=declare,
    )

    assert len(llm_inputs) == 1
    assert llm_inputs[0] == initial_inputs

    assert len(declared) == 1
    assert report.declared_actions == frozenset(declared)
    assert report.blocked_actions == frozenset()

    guarantee_names = {g.name for g in report.guarantees}

    assert {
        "bounded_llm_calls",
        "nested_inputs_readable",
        "primitive_actions_authorised",
    } <= guarantee_names


def test_reference_ites_blocks_unreadable_nested_execution() -> None:
    alice = Principal("alice", "Alice")
    bob = Principal("bob", "Bob")

    readable = Data(
        authors=frozenset({alice}),
        readers=frozenset({alice}),
        tag="readable",
    )

    unreadable = Data(
        authors=frozenset({bob}),
        readers=frozenset({bob}),
        tag="unreadable",
    )

    initial_inputs = frozenset(
        {
            Artifact(
                value=readable,
                provenance=Provenance.from_principal(alice),
            )
        }
    )

    declared: list[object] = []

    def llm_call(
        inputs: frozenset[Artifact[object]],
    ) -> frozenset[object]:
        _ = inputs
        return frozenset(
            {
                    NestedExecutionAction(
                        nested_inputs=frozenset({readable.to_artifact()}),
                        inputs=inputs,
                    ),
                    NestedExecutionAction(
                        nested_inputs=frozenset({unreadable.to_artifact()}),
                        inputs=inputs,
                    ),
            }
        )

    def declare(item: object) -> None:
        declared.append(item)

    report = ReferenceITES().run(
        environment=object(),
        initial_inputs=initial_inputs,
        llm_call=llm_call,
        declare=declare,
    )

    assert any(
        action.nested_inputs
        and next(iter(action.nested_inputs)).value.tag == "readable"
        for action in report.declared_actions
    )
    assert any(
        action.nested_inputs
        and next(iter(action.nested_inputs)).value.tag == "unreadable"
        for action in report.blocked_actions
    )

    nested_guarantee = next(
        g
        for g in report.guarantees
        if g.name == "nested_inputs_readable"
    )

    assert nested_guarantee.holds is False


def test_reference_ites_respects_llm_budget() -> None:
    _, initial_inputs = _initial_inputs()

    calls = 0

    def llm_call(
        inputs: frozenset[Artifact[object]],
    ) -> frozenset[object]:
        nonlocal calls
        _ = inputs
        calls += 1

        return frozenset(
            {
                PrimitiveAction(
                    permission=f"action-{calls}",
                    provider_operation=f"action-{calls}",
                    inputs=inputs,
                ),
            }
        )

    report = ReferenceITES(max_llm_calls=1).run(
        environment=object(),
        initial_inputs=initial_inputs,
        llm_call=llm_call,
        declare=lambda _: None,
    )

    assert calls == 1

    budget = next(
        g
        for g in report.guarantees
        if g.name == "bounded_llm_calls"
    )

    assert budget.holds is True


def test_reference_ites_is_deterministic() -> None:
    _, initial_inputs = _initial_inputs()

    def llm_call(
        inputs: frozenset[Artifact[object]],
    ) -> frozenset[object]:
        _ = inputs
        return frozenset(
            {
                PrimitiveAction(
                    permission="approve",
                    provider_operation="approve",
                    inputs=inputs,
                ),
            }
        )

    report_one = ReferenceITES().run(
        environment=object(),
        initial_inputs=initial_inputs,
        llm_call=llm_call,
        declare=lambda _: None,
    )

    report_two = ReferenceITES().run(
        environment=object(),
        initial_inputs=initial_inputs,
        llm_call=llm_call,
        declare=lambda _: None,
    )

    assert report_one == report_two


def test_report_contains_guarantees() -> None:
    _, initial_inputs = _initial_inputs()

    report = ReferenceITES().run(
        environment=object(),
        initial_inputs=initial_inputs,
        llm_call=lambda _: frozenset(),
        declare=lambda _: None,
    )

    assert all(isinstance(g, Guarantee) for g in report.guarantees)
    assert {g.name for g in report.guarantees} == {
        "bounded_llm_calls",
        "nested_inputs_readable",
        "primitive_actions_authorised",
        "visibility_respected",
        "consent_respected",
    }
