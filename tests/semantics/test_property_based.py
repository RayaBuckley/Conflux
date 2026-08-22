"""Hypothesis-based property tests for domain algebraic laws (SEM-001, SEM-002, SEM-003)."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from conflux.application import DecisionPipeline
from conflux.domain import (
    Artifact,
    EnvironmentSnapshot,
    PrimitiveAction,
    Principal,
    PrincipalContext,
    ProposalBatch,
    Provenance,
    ProvenancePrecision,
    ResourceRef,
    Session,
)
from conflux.ites import BranchState, TransitionKernel
from conflux.policy import ExplicitConsentPolicy, InMemoryAuthorisationPolicy, PolicyGrant, SessionVisibilityPolicy, SnapshotReadPolicy

from .strategies import artifacts, primitive_actions, principal_contexts, provenances

pytestmark = pytest.mark.slow

_PERMIT_ALL = InMemoryAuthorisationPolicy(
    frozenset(
        {
            PolicyGrant(p.id, "write", "out")
            for p in [
                Principal("alice", "Alice"),
                Principal("bob", "Bob"),
                Principal("carol", "Carol"),
                Principal("dave", "Dave"),
                Principal("eve", "Eve"),
                Principal("frank", "Frank"),
                Principal("grace", "Grace"),
                Principal("heidi", "Heidi"),
                Principal("ivan", "Ivan"),
                Principal("judy", "Judy"),
                Principal("mallory", "Mallory"),
                Principal("oscar", "Oscar"),
                Principal("peggy", "Peggy"),
                Principal("sybil", "Sybil"),
                Principal("trent", "Trent"),
                Principal("victor", "Victor"),
                Principal("walter", "Walter"),
            ]
        }
    )
)


class TestPrincipalContextMerge:
    """SEM-001: PrincipalContext.merge forms a join semilattice."""

    @given(a=principal_contexts(), b=principal_contexts())
    @settings(max_examples=200, deadline=None)
    def test_merge_commutative(self, a: PrincipalContext, b: PrincipalContext) -> None:
        assert a.merge(b) == b.merge(a)

    @given(a=principal_contexts(), b=principal_contexts(), c=principal_contexts())
    @settings(max_examples=200, deadline=None)
    def test_merge_associative(self, a: PrincipalContext, b: PrincipalContext, c: PrincipalContext) -> None:
        assert a.merge(b).merge(c) == a.merge(b.merge(c))

    @given(a=principal_contexts())
    @settings(max_examples=200, deadline=None)
    def test_merge_idempotent(self, a: PrincipalContext) -> None:
        assert a.merge(a) == a

    @given(a=principal_contexts(), b=principal_contexts())
    @settings(max_examples=200, deadline=None)
    def test_merge_monotone_principals(self, a: PrincipalContext, b: PrincipalContext) -> None:
        result = a.merge(b)
        assert a.principals.issubset(result.principals)
        assert b.principals.issubset(result.principals)

    @given(a=principal_contexts(), b=st.just(PrincipalContext(unknown=True)))
    @settings(max_examples=200, deadline=None)
    def test_unknown_absorbing(self, a: PrincipalContext, b: PrincipalContext) -> None:
        assert a.merge(b).unknown
        assert b.merge(a).unknown


class TestIsAuthorityBearing:
    """SEM-002: is_authority_bearing guard."""

    @given(ctx=principal_contexts())
    @settings(max_examples=200, deadline=None)
    def test_authority_bearing_iff_nonempty_and_known(self, ctx: PrincipalContext) -> None:
        expected = bool(ctx.principals) and not ctx.unknown
        assert ctx.is_authority_bearing == expected


class TestProvenanceMerge:
    """SEM-003: Provenance.merge forms a commutative monoid."""

    @given(a=provenances(), b=provenances())
    @settings(max_examples=200, deadline=None)
    def test_merge_commutative(self, a: Provenance, b: Provenance) -> None:
        assert a.merge(b) == b.merge(a)

    @given(a=provenances(), b=provenances(), c=provenances())
    @settings(max_examples=200, deadline=None)
    def test_merge_associative(self, a: Provenance, b: Provenance, c: Provenance) -> None:
        assert a.merge(b).merge(c) == a.merge(b.merge(c))

    @given(a=provenances())
    @settings(max_examples=200, deadline=None)
    def test_merge_idempotent(self, a: Provenance) -> None:
        assert a.merge(a) == a

    @given(a=provenances(), b=provenances())
    @settings(max_examples=200, deadline=None)
    def test_merge_preserves_all_principals(self, a: Provenance, b: Provenance) -> None:
        result = a.merge(b)
        assert a.principals.issubset(result.principals)
        assert b.principals.issubset(result.principals)

    @given(a=provenances(), b=provenances())
    @settings(max_examples=200, deadline=None)
    def test_precision_not_more_precise_than_inputs(self, a: Provenance, b: Provenance) -> None:
        result = a.merge(b)
        assert result.precision.value >= min(a.precision.value, b.precision.value)

    @given(a=provenances(), b=provenances())
    @settings(max_examples=200, deadline=None)
    def test_attestation_conjunction(self, a: Provenance, b: Provenance) -> None:
        result = a.merge(b)
        if a.attested and b.attested:
            assert result.attested
        else:
            assert not result.attested

    @given(a=provenances(), b=st.just(Provenance(precision=ProvenancePrecision.UNKNOWN, attested=False)))
    @settings(max_examples=200, deadline=None)
    def test_unknown_provenance_dominates_precision(self, a: Provenance, b: Provenance) -> None:
        result = a.merge(b)
        assert result.precision == ProvenancePrecision.UNKNOWN


class TestKernelInvariants:
    """SEM-008, SEM-012: Kernel transition invariants."""

    @given(art=artifacts(), action=primitive_actions())
    @settings(max_examples=100, deadline=None)
    def test_context_monotone_through_kernel(self, art: Artifact[object], action: PrimitiveAction) -> None:
        parent = BranchState.initial((art,))
        consent_ids = {action.id}
        for inp in action.inputs:
            consent_ids.add(inp.id)
        pipeline = _permitting_pipeline(consent_ids)
        kernel = TransitionKernel(pipeline)
        env = EnvironmentSnapshot("e", resources=(ResourceRef("test", "out", "document"),))
        session = Session("s", parent.context.principals)

        children = kernel.expand_batch(
            parent=parent,
            batch=ProposalBatch.alternatives(action),
            session=session,
            environment=env,
            model_calls=1,
        )
        for child in children:
            if child.status.value == "authorised" and action.inputs:
                assert child.context.principals.issubset(
                    parent.context.principals | {p for a in action.inputs for p in a.provenance.principals}
                )

    @given(art=artifacts(), action=primitive_actions())
    @settings(max_examples=100, deadline=None)
    def test_certificate_branch_id_matches(self, art: Artifact[object], action: PrimitiveAction) -> None:
        parent = BranchState.initial((art,))
        consent_ids = {action.id}
        for inp in action.inputs:
            consent_ids.add(inp.id)
        pipeline = _permitting_pipeline(consent_ids)
        kernel = TransitionKernel(pipeline)
        env = EnvironmentSnapshot("e", resources=(ResourceRef("test", "out", "document"),))
        session = Session("s", parent.context.principals)

        children = kernel.expand_batch(
            parent=parent,
            batch=ProposalBatch.alternatives(action),
            session=session,
            environment=env,
            model_calls=1,
        )
        for child in children:
            if child.certificate is not None:
                assert child.certificate.branch_id == child.branch_id


def _permitting_pipeline(consent_ids: set[str]) -> DecisionPipeline:
    return DecisionPipeline(
        _PERMIT_ALL,
        SnapshotReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(frozenset(consent_ids)),
    )
