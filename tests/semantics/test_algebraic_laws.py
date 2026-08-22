"""Algebraic law tests for domain merge operations (SEM-001, SEM-003)."""

from __future__ import annotations

import pytest

from conflux.domain import Principal, PrincipalContext, Provenance, ProvenancePrecision

pytestmark = pytest.mark.security

alice = Principal("alice", "Alice")
bob = Principal("bob", "Bob")
carol = Principal("carol", "Carol")


def _ctx(*principals: Principal, unknown: bool = False) -> PrincipalContext:
    return PrincipalContext(frozenset(principals), unknown=unknown)


def _prov(*principals: Principal, precision: ProvenancePrecision = ProvenancePrecision.EXACT, attested: bool = True) -> Provenance:
    return Provenance(
        principals=frozenset(principals),
        precision=precision,
        attested=attested,
    )


class TestPrincipalContextMergeSemilattice:
    """SEM-001: PrincipalContext.merge forms a join semilattice."""

    def test_merge_commutative(self) -> None:
        a = _ctx(alice)
        b = _ctx(bob)
        assert a.merge(b) == b.merge(a)

    def test_merge_commutative_with_unknown(self) -> None:
        a = _ctx(alice)
        b = _ctx(unknown=True)
        assert a.merge(b) == b.merge(a)

    def test_merge_associative(self) -> None:
        a = _ctx(alice)
        b = _ctx(bob)
        c = _ctx(carol)
        assert a.merge(b).merge(c) == a.merge(b.merge(c))

    def test_merge_associative_mixed(self) -> None:
        a = _ctx(alice)
        b = _ctx(unknown=True)
        c = _ctx(carol)
        assert a.merge(b).merge(c) == a.merge(b.merge(c))

    def test_merge_idempotent(self) -> None:
        a = _ctx(alice, bob)
        assert a.merge(a) == a

    def test_merge_idempotent_unknown(self) -> None:
        a = _ctx(unknown=True)
        assert a.merge(a) == a

    def test_merge_monotone_principals(self) -> None:
        a = _ctx(alice)
        b = _ctx(bob)
        result = a.merge(b)
        assert a.principals.issubset(result.principals)
        assert b.principals.issubset(result.principals)

    def test_merge_monotone_unknown(self) -> None:
        a = _ctx(alice)
        b = _ctx(unknown=True)
        result = a.merge(b)
        assert result.unknown

    def test_unknown_absorbing(self) -> None:
        a = _ctx(alice)
        b = _ctx(unknown=True)
        assert a.merge(b).unknown
        assert b.merge(a).unknown

    def test_empty_merge_empty(self) -> None:
        a = _ctx()
        b = _ctx()
        assert a.merge(b) == _ctx()

    def test_unknown_merge_unknown(self) -> None:
        a = _ctx(unknown=True)
        b = _ctx(unknown=True)
        assert a.merge(b) == _ctx(unknown=True)

    def test_merge_preserves_all_principals(self) -> None:
        a = _ctx(alice)
        b = _ctx(bob, carol)
        result = a.merge(b)
        assert result.principals == frozenset({alice, bob, carol})


class TestIsAuthorityBearing:
    """SEM-002: is_authority_bearing guard."""

    def test_empty_context_not_authority_bearing(self) -> None:
        assert not _ctx().is_authority_bearing

    def test_unknown_context_not_authority_bearing(self) -> None:
        assert not _ctx(unknown=True).is_authority_bearing

    def test_non_empty_known_is_authority_bearing(self) -> None:
        assert _ctx(alice).is_authority_bearing

    def test_non_empty_unknown_not_authority_bearing(self) -> None:
        assert not _ctx(alice, unknown=True).is_authority_bearing

    def test_from_principals_empty_is_unknown(self) -> None:
        ctx = PrincipalContext.from_principals(frozenset())
        assert not ctx.is_authority_bearing
        assert ctx.unknown

    def test_from_principals_non_empty_is_known(self) -> None:
        ctx = PrincipalContext.from_principals(frozenset({alice}))
        assert ctx.is_authority_bearing
        assert not ctx.unknown


class TestProvenanceMergeMonoid:
    """SEM-003: Provenance.merge forms a commutative monoid."""

    def test_merge_commutative(self) -> None:
        a = _prov(alice)
        b = _prov(bob)
        assert a.merge(b) == b.merge(a)

    def test_merge_commutative_precision(self) -> None:
        a = _prov(alice, precision=ProvenancePrecision.EXACT)
        b = _prov(bob, precision=ProvenancePrecision.CONSERVATIVE)
        assert a.merge(b) == b.merge(a)

    def test_merge_associative(self) -> None:
        a = _prov(alice)
        b = _prov(bob)
        c = _prov(carol)
        assert a.merge(b).merge(c) == a.merge(b.merge(c))

    def test_merge_associative_mixed_precision(self) -> None:
        a = _prov(alice, precision=ProvenancePrecision.EXACT)
        b = _prov(bob, precision=ProvenancePrecision.CONSERVATIVE)
        c = _prov(carol, precision=ProvenancePrecision.UNKNOWN, attested=False)
        assert a.merge(b).merge(c) == a.merge(b.merge(c))

    def test_merge_idempotent(self) -> None:
        a = _prov(alice, bob)
        assert a.merge(a) == a

    def test_unknown_merge_dominates_precision(self) -> None:
        a = _prov(alice, precision=ProvenancePrecision.EXACT)
        b = _prov(precision=ProvenancePrecision.UNKNOWN, attested=False)
        result = a.merge(b)
        assert result.precision == ProvenancePrecision.UNKNOWN

    def test_conservative_merge_exact_yields_conservative(self) -> None:
        a = _prov(alice, precision=ProvenancePrecision.EXACT)
        b = _prov(bob, precision=ProvenancePrecision.CONSERVATIVE)
        result = a.merge(b)
        assert result.precision == ProvenancePrecision.CONSERVATIVE

    def test_merge_preserves_all_principals(self) -> None:
        a = _prov(alice)
        b = _prov(bob, carol)
        result = a.merge(b)
        assert result.principals == frozenset({alice, bob, carol})

    def test_merge_attestation_conjunction(self) -> None:
        a = _prov(alice, attested=True)
        b = _prov(bob, attested=False)
        result = a.merge(b)
        assert not result.attested

    def test_merge_both_attested_stays_attested(self) -> None:
        a = _prov(alice, attested=True)
        b = _prov(bob, attested=True)
        result = a.merge(b)
        assert result.attested

    def test_unknown_provenance_is_unknown(self) -> None:
        p = Provenance.unknown()
        assert p.is_unknown
        assert not p.attested
        assert p.precision == ProvenancePrecision.UNKNOWN

    def test_empty_principals_is_unknown(self) -> None:
        p = _prov()
        assert p.is_unknown

    def test_context_from_provenance_carries_unknown(self) -> None:
        p = Provenance.unknown()
        ctx = p.context
        assert ctx.unknown
        assert not ctx.is_authority_bearing

    def test_context_from_attested_provenance(self) -> None:
        p = _prov(alice, attested=True)
        ctx = p.context
        assert not ctx.unknown
        assert ctx.is_authority_bearing
        assert alice in ctx.principals
