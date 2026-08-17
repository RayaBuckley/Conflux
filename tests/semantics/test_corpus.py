"""Decision-complete corpus shared by direct policy and kernel conformance."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from conflux.application import DecisionPipeline
from conflux.domain import (
    Action,
    Artifact,
    DelegationAction,
    EnvironmentSnapshot,
    MessageAction,
    Permission,
    PrimitiveAction,
    Principal,
    PrincipalContext,
    ProposalBatch,
    Provenance,
    ResourceRef,
    Session,
)
from conflux.ites import BranchState, TransitionKernel


@dataclass(frozen=True, slots=True)
class SemanticCase:
    name: str
    context: PrincipalContext
    action: Action
    expected: bool
    reason: str | None = None


def _write(action_id: str, inputs: tuple[Artifact[object], ...] = ()) -> PrimitiveAction:
    return PrimitiveAction(
        action_id,
        "write",
        Permission("write"),
        ResourceRef("test", "out", "document"),
        inputs,
    )


def _cases(
    environment: EnvironmentSnapshot,
    alice: Principal,
    bob: Principal,
) -> tuple[SemanticCase, ...]:
    alice_doc = environment.data_item("alice-doc")
    shared_doc = environment.data_item("shared-doc")
    assert alice_doc is not None and shared_doc is not None
    mallory = Principal("mallory", "Mallory")
    return (
        SemanticCase(
            "empty_context",
            PrincipalContext(),
            _write("write"),
            False,
            "empty_principal_context",
        ),
        SemanticCase(
            "unknown_context",
            PrincipalContext(unknown=True),
            _write("write"),
            False,
            "unknown_principal_context",
        ),
        SemanticCase(
            "one_authorised_principal",
            PrincipalContext(frozenset({alice})),
            _write("write"),
            True,
        ),
        SemanticCase(
            "mixed_authorised_principals",
            PrincipalContext(frozenset({alice, bob})),
            _write("write", (shared_doc.to_artifact(),)),
            True,
        ),
        SemanticCase(
            "reader_not_author",
            PrincipalContext(frozenset({alice})),
            _write("write", (shared_doc.to_artifact(),)),
            True,
        ),
        SemanticCase(
            "author_not_reader",
            PrincipalContext(frozenset({bob})),
            _write("write", (alice_doc.to_artifact(),)),
            False,
            "read_denied",
        ),
        SemanticCase(
            "visibility_denied",
            PrincipalContext(frozenset({mallory})),
            MessageAction("message", "hello"),
            False,
            "principal_not_visible",
        ),
        SemanticCase(
            "delegation_unsupported",
            PrincipalContext(frozenset({alice})),
            DelegationAction("delegation"),
            False,
            "delegation_unsupported",
        ),
        SemanticCase(
            "mixed_authorised_and_unauthorised",
            PrincipalContext(frozenset({alice, mallory})),
            _write("write"),
            False,
            "principal_denied",
        ),
        SemanticCase(
            "unauthorised_single_principal",
            PrincipalContext(frozenset({mallory})),
            _write("write"),
            False,
            "principal_denied",
        ),
        SemanticCase(
            "mixed_context_with_both_grants_no_inputs",
            PrincipalContext(frozenset({alice, bob})),
            _write("write"),
            True,
        ),
        SemanticCase(
            "mixed_context_read_blocked",
            PrincipalContext(frozenset({alice, bob})),
            _write("write", (alice_doc.to_artifact(),)),
            False,
            "read_denied",
        ),
    )


@pytest.mark.parametrize("case_index", range(12))
def test_direct_decision_and_kernel_conform(
    case_index: int,
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
    alice: Principal,
    bob: Principal,
) -> None:
    case = _cases(environment, alice, bob)[case_index]
    direct = pipeline.decide(
        session=session,
        action=case.action,
        context=case.context,
        environment=environment,
    )
    source = Artifact("source", "x", Provenance(case.context.principals))
    parent = BranchState.initial((source,))
    if case.context.unknown:
        parent = BranchState.initial((Artifact("source", "x", Provenance.unknown()),))
    branch = TransitionKernel(pipeline).expand_batch(
        parent=parent,
        batch=ProposalBatch.alternatives(case.action),
        session=session,
        environment=environment,
        model_calls=1,
    )[0]
    assert branch.decision is not None
    assert direct.allowed is case.expected
    assert branch.decision.allowed is case.expected
    if case.reason is not None:
        assert case.reason in {decision.reason for decision in direct.decisions}
