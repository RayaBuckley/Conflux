"""SLED must find a one-step witness for each seeded monitor defect."""

from __future__ import annotations

from conflux.application import DecisionPipeline
from conflux.domain import (
    Artifact,
    DataItem,
    EnvironmentSnapshot,
    NestedExecutionAction,
    Permission,
    PrimitiveAction,
    Principal,
    ProposalBatch,
    Provenance,
    ResourceRef,
    Session,
)
from conflux.evaluation import (
    ExplicitStateChecker,
    VerificationVerdict,
)
from conflux.ites import BranchState, TransitionKernel
from conflux.policy import (
    ExplicitConsentPolicy,
    InMemoryAuthorisationPolicy,
    PolicyGrant,
    SessionVisibilityPolicy,
    SnapshotReadPolicy,
)

from .mutants import (
    BatchSystem,
    CertificateReplayKernel,
    ConsentGrantsAuthority,
    ContextResetOnDeny,
    EmptyContextAllow,
    ExecutedInvariantOnly,
    NestedInputsInfluenceContext,
    NoAuthorAsReader,
    NoAuthorityWithoutContext,
    NoCertificateReplay,
    NoConsentOverride,
    NoMixedContextUnion,
    NoSiblingLeakage,
    PermissionUnion,
    ProvenanceAsReadPolicy,
    SiblingLeakKernel,
    StaleContextKernel,
    VisibilityImpliesRead,
    with_read_policy,
)


def _pipeline(
    *,
    grants: frozenset[PolicyGrant],
    consent: frozenset[str],
) -> DecisionPipeline:
    return DecisionPipeline(
        InMemoryAuthorisationPolicy(grants),
        SnapshotReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(consent),
    )


def _action(action_id: str, inputs: tuple[Artifact[object], ...] = ()) -> PrimitiveAction:
    return PrimitiveAction(
        action_id,
        "write",
        Permission("write"),
        ResourceRef("test", "out", "document"),
        inputs,
    )


def _assert_minimal(system: BatchSystem, property_: object) -> None:
    result = ExplicitStateChecker().verify(system, (property_,))  # type: ignore[arg-type]
    assert result.verdict is VerificationVerdict.UNSAFE
    assert result.counterexample is not None
    assert result.counterexample.length == 1


def test_empty_context_allow_mutant() -> None:
    alice = Principal("alice", "Alice")
    environment = EnvironmentSnapshot(
        "e",
        resources=(ResourceRef("test", "out", "document"),),
    )
    pipeline = _pipeline(
        grants=frozenset({PolicyGrant("alice", "write", "out")}),
        consent=frozenset({"write"}),
    )
    system = BatchSystem(
        BranchState.initial(()),
        ProposalBatch.alternatives(_action("write")),
        TransitionKernel(EmptyContextAllow(pipeline, alice)),
        Session("s", frozenset({alice})),
        environment,
    )
    _assert_minimal(system, NoAuthorityWithoutContext())


def test_permission_union_mutant() -> None:
    alice, bob = Principal("alice", "Alice"), Principal("bob", "Bob")
    source = Artifact(
        "mixed",
        "x",
        Provenance(frozenset({alice, bob})),
    )
    environment = EnvironmentSnapshot(
        "e",
        resources=(ResourceRef("test", "out", "document"),),
    )
    pipeline = _pipeline(
        grants=frozenset({PolicyGrant("alice", "write", "out")}),
        consent=frozenset({"write"}),
    )
    system = BatchSystem(
        BranchState.initial((source,)),
        ProposalBatch.alternatives(_action("write")),
        TransitionKernel(PermissionUnion(pipeline)),
        Session("s", frozenset({alice, bob})),
        environment,
    )
    _assert_minimal(system, NoMixedContextUnion())


def test_provenance_as_acl_mutant() -> None:
    alice, bob = Principal("alice", "Alice"), Principal("bob", "Bob")
    item = DataItem("doc", "secret", frozenset({alice}), frozenset({bob}))
    environment = EnvironmentSnapshot(
        "e",
        data=(item,),
        resources=(ResourceRef("test", "out", "document"),),
    )
    pipeline = _pipeline(
        grants=frozenset({PolicyGrant("alice", "write", "out")}),
        consent=frozenset({"write"}),
    )
    pipeline = with_read_policy(pipeline, ProvenanceAsReadPolicy())
    system = BatchSystem(
        BranchState.initial((item.to_artifact(),)),
        ProposalBatch.alternatives(_action("write", (item.to_artifact(),))),
        TransitionKernel(pipeline),
        Session("s", frozenset({alice, bob})),
        environment,
    )
    _assert_minimal(system, NoAuthorAsReader(frozenset({bob})))


def test_stale_context_mutant() -> None:
    alice, bob = Principal("alice", "Alice"), Principal("bob", "Bob")
    initial = Artifact("initial", "a", Provenance.from_principal(alice))
    nested = Artifact("nested", "b", Provenance.from_principal(bob))
    pipeline = _pipeline(grants=frozenset(), consent=frozenset({"nested"}))
    system = BatchSystem(
        BranchState.initial((initial,)),
        ProposalBatch.alternatives(NestedExecutionAction("nested", (nested,))),
        StaleContextKernel(TransitionKernel(pipeline)),
        Session("s", frozenset({alice, bob})),
        EnvironmentSnapshot("e"),
    )
    _assert_minimal(system, NestedInputsInfluenceContext())


def test_sibling_leak_mutant() -> None:
    alice, bob = Principal("alice", "Alice"), Principal("bob", "Bob")
    initial = Artifact("initial", "a", Provenance.from_principal(alice))
    nested = Artifact("nested", "b", Provenance.from_principal(bob))
    pipeline = _pipeline(
        grants=frozenset(
            {
                PolicyGrant("alice", "write", "out"),
                PolicyGrant("bob", "write", "out"),
            }
        ),
        consent=frozenset({"nested", "write"}),
    )
    environment = EnvironmentSnapshot(
        "e",
        resources=(ResourceRef("test", "out", "document"),),
    )
    system = BatchSystem(
        BranchState.initial((initial,)),
        ProposalBatch.alternatives(
            NestedExecutionAction("nested", (nested,)),
            _action("write"),
        ),
        SiblingLeakKernel(TransitionKernel(pipeline)),
        Session("s", frozenset({alice, bob})),
        environment,
    )
    _assert_minimal(system, NoSiblingLeakage())


def test_rejected_proposal_misclassification_mutant() -> None:
    alice = Principal("alice", "Alice")
    pipeline = _pipeline(grants=frozenset(), consent=frozenset({"write"}))
    system = BatchSystem(
        BranchState.initial((Artifact("input", "x", Provenance.from_principal(alice)),)),
        ProposalBatch.alternatives(_action("write")),
        TransitionKernel(pipeline),
        Session("s", frozenset({alice})),
        EnvironmentSnapshot(
            "e",
            resources=(ResourceRef("test", "out", "document"),),
        ),
    )
    _assert_minimal(system, ExecutedInvariantOnly())


def test_consent_grants_authority_mutant() -> None:
    alice = Principal("alice", "Alice")
    source = Artifact("input", "x", Provenance.from_principal(alice))
    pipeline = _pipeline(grants=frozenset(), consent=frozenset({"write"}))
    system = BatchSystem(
        BranchState.initial((source,)),
        ProposalBatch.alternatives(_action("write")),
        TransitionKernel(ConsentGrantsAuthority(pipeline)),
        Session("s", frozenset({alice})),
        EnvironmentSnapshot(
            "e",
            resources=(ResourceRef("test", "out", "document"),),
        ),
    )
    _assert_minimal(system, NoConsentOverride())


def test_visibility_implies_read_mutant() -> None:
    alice, bob = Principal("alice", "Alice"), Principal("bob", "Bob")
    item = DataItem("doc", "secret", frozenset({alice}), frozenset({bob}))
    environment = EnvironmentSnapshot(
        "e",
        data=(item,),
        resources=(ResourceRef("test", "out", "document"),),
    )
    pipeline = _pipeline(
        grants=frozenset({PolicyGrant("alice", "write", "out")}),
        consent=frozenset({"write"}),
    )
    pipeline = with_read_policy(pipeline, VisibilityImpliesRead())
    source = Artifact("input", "x", Provenance.from_principal(alice))
    system = BatchSystem(
        BranchState.initial((source,)),
        ProposalBatch.alternatives(_action("write", (item.to_artifact(),))),
        TransitionKernel(pipeline),
        Session("s", frozenset({alice})),
        environment,
    )
    _assert_minimal(system, NoAuthorAsReader(frozenset({bob})))


def test_certificate_replay_mutant() -> None:
    alice, bob = Principal("alice", "Alice"), Principal("bob", "Bob")
    initial = Artifact("initial", "a", Provenance.from_principal(alice))
    pipeline = _pipeline(
        grants=frozenset(
            {
                PolicyGrant("alice", "write", "out"),
                PolicyGrant("bob", "write", "out"),
            }
        ),
        consent=frozenset({"write-a", "write-b"}),
    )
    environment = EnvironmentSnapshot(
        "e",
        resources=(ResourceRef("test", "out", "document"),),
    )
    system = BatchSystem(
        BranchState.initial((initial,)),
        ProposalBatch.alternatives(
            _action("write-a"),
            _action("write-b"),
        ),
        CertificateReplayKernel(TransitionKernel(pipeline)),
        Session("s", frozenset({alice, bob})),
        environment,
    )
    _assert_minimal(system, NoCertificateReplay())


def test_context_reset_on_deny_mutant() -> None:
    alice, bob = Principal("alice", "Alice"), Principal("bob", "Bob")
    initial = Artifact("initial", "a", Provenance.from_principal(alice))
    nested = Artifact("nested", "b", Provenance.from_principal(bob))
    pipeline = _pipeline(grants=frozenset(), consent=frozenset({"nested"}))
    system = BatchSystem(
        BranchState.initial((initial,)),
        ProposalBatch.alternatives(NestedExecutionAction("nested", (nested,))),
        ContextResetOnDeny(TransitionKernel(pipeline)),
        Session("s", frozenset({alice, bob})),
        EnvironmentSnapshot("e"),
    )
    _assert_minimal(system, NestedInputsInfluenceContext())
