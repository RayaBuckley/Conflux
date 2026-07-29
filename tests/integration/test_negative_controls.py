"""Negative controls must fail where canonical ITES remains safe."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pytest

from conflux.application import DecisionPipeline
from conflux.domain import (
    Action,
    DataItem,
    EnvironmentSnapshot,
    Permission,
    PrimitiveAction,
    Principal,
    ResourceRef,
    Session,
)
from conflux.evaluation import (
    ExplicitStateChecker,
    ITESVerificationSystem,
    VerificationResult,
)
from conflux.evaluation.defences import (
    CanonicalITES,
    ForbiddenAuthorisation,
    InitiatorOnly,
    LatestInputOnly,
    NoDefence,
    NoReadCheck,
    UnionPermissions,
)
from conflux.ites import BranchState, TransitionKernel
from conflux.ites.kernel import DecisionEngine
from conflux.policy import (
    ExplicitConsentPolicy,
    InMemoryAuthorisationPolicy,
    PolicyGrant,
    SessionVisibilityPolicy,
    SnapshotReadPolicy,
)


@dataclass(frozen=True, slots=True)
class ControlCase:
    action: Action
    initial: BranchState
    environment: EnvironmentSnapshot
    session: Session
    pipeline: DecisionPipeline


def _case(*, all_granted: bool, cross_readable: bool) -> ControlCase:
    alice = Principal("alice", "Alice")
    bob = Principal("bob", "Bob")
    readers = frozenset({alice, bob}) if cross_readable else frozenset({alice})
    environment = EnvironmentSnapshot(
        "negative-control",
        (
            DataItem("bob-request", "attack", frozenset({bob}), readers),
            DataItem(
                "alice-data",
                "secret",
                frozenset({alice}),
                frozenset({alice, bob}) if cross_readable else frozenset({alice}),
            ),
        ),
        (ResourceRef("memory", "out", "document"),),
    )
    inputs = environment.artifacts()
    action = PrimitiveAction(
        "forbidden-write",
        "write",
        Permission("write"),
        environment.resources[0],
        inputs,
    )
    grants = {PolicyGrant("alice", "write", "out")}
    if all_granted:
        grants.add(PolicyGrant("bob", "write", "out"))
    pipeline = DecisionPipeline(
        InMemoryAuthorisationPolicy(frozenset(grants)),
        SnapshotReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(frozenset({"forbidden-write"})),
    )
    return ControlCase(
        action,
        BranchState.initial(inputs),
        environment,
        Session("negative-control", frozenset({alice, bob})),
        pipeline,
    )


def _verify(
    case: ControlCase,
    engine: DecisionEngine,
) -> VerificationResult[BranchState, Action]:
    system = ITESVerificationSystem(
        (case.initial,),
        (case.action,),
        TransitionKernel(engine),
        case.session,
        case.environment,
    )
    return ExplicitStateChecker().verify(
        system,
        (ForbiddenAuthorisation("forbidden-write"),),
    )


@pytest.mark.parametrize(
    "factory",
    (
        lambda pipeline: NoDefence(),
        UnionPermissions,
        InitiatorOnly,
        LatestInputOnly,
    ),
)
def test_authority_negative_controls_have_minimal_counterexamples(
    factory: Callable[[DecisionPipeline], DecisionEngine],
) -> None:
    case = _case(all_granted=False, cross_readable=True)
    control = factory(case.pipeline)
    result = _verify(case, control)
    assert result.verdict.value == "unsafe"
    assert result.counterexample is not None
    assert result.counterexample.length == 1
    canonical = _verify(case, CanonicalITES(case.pipeline))
    assert canonical.verdict.value == "safe"


def test_no_read_check_has_counterexample_but_canonical_ites_does_not() -> None:
    case = _case(all_granted=True, cross_readable=False)
    result = _verify(case, NoReadCheck(case.pipeline))
    assert result.verdict.value == "unsafe"
    assert result.counterexample is not None
    assert result.counterexample.length == 1
    canonical = _verify(case, CanonicalITES(case.pipeline))
    assert canonical.verdict.value == "safe"
