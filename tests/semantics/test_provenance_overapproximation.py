"""Tests for provenance overapproximation and precision metrics (SEM-017, SEM-018)."""

from __future__ import annotations

import pytest

from conflux.domain import Principal, Provenance
from conflux.verification import (
    enforcement_is_sound,
    measure_authority_loss,
    measure_exposure,
    measure_overapproximation,
)

pytestmark = pytest.mark.security

alice = Principal("alice", "Alice")
bob = Principal("bob", "Bob")
mallory = Principal("mallory", "Mallory")


class TestOverapproximationSoundness:
    """SEM-017: enforcement based on security provenance is sound."""

    def test_exact_provenance_is_sound(self) -> None:
        sec_prov = Provenance.from_principals({alice, bob})
        actual = frozenset({alice, bob})
        assert enforcement_is_sound(sec_prov, actual)

    def test_overapproximation_is_sound(self) -> None:
        sec_prov = Provenance.from_principals({alice, bob, mallory})
        actual = frozenset({alice})
        assert enforcement_is_sound(sec_prov, actual)

    def test_underapproximation_is_unsound(self) -> None:
        sec_prov = Provenance.from_principals({alice})
        actual = frozenset({alice, mallory})
        assert not enforcement_is_sound(sec_prov, actual)

    def test_empty_security_provenance_with_actual_is_unsound(self) -> None:
        sec_prov = Provenance.unknown()
        actual = frozenset({alice})
        assert not enforcement_is_sound(sec_prov, actual)

    def test_empty_actual_with_nonempty_security_is_sound(self) -> None:
        sec_prov = Provenance.from_principals({alice})
        actual: frozenset[Principal] = frozenset()
        assert enforcement_is_sound(sec_prov, actual)


class TestMeasureOverapproximation:
    """Measuring the overapproximation relationship."""

    def test_exact_provenance_has_no_excess(self) -> None:
        sec_prov = Provenance.from_principals({alice, bob})
        result = measure_overapproximation(sec_prov, frozenset({alice, bob}))
        assert result.overapproximates
        assert result.is_exact
        assert len(result.excess_principals) == 0

    def test_overapproximation_has_excess(self) -> None:
        sec_prov = Provenance.from_principals({alice, bob, mallory})
        result = measure_overapproximation(sec_prov, frozenset({alice}))
        assert result.overapproximates
        assert not result.is_exact
        assert mallory in result.excess_principals
        assert bob in result.excess_principals

    def test_underapproximation_is_not_overapproximation(self) -> None:
        sec_prov = Provenance.from_principals({alice})
        result = measure_overapproximation(sec_prov, frozenset({alice, mallory}))
        assert not result.overapproximates
        assert not result.is_exact

    def test_result_round_trips(self) -> None:
        sec_prov = Provenance.from_principals({alice, bob})
        result = measure_overapproximation(sec_prov, frozenset({alice}))
        d = result.to_dict()
        assert d["overapproximates"] is True
        assert d["is_exact"] is False
        assert "bob" in d["excess_principal_ids"]


class TestAuthorityLoss:
    """SEM-018: precision metric for authority loss."""

    def test_no_loss_when_no_overlap(self) -> None:
        result = measure_authority_loss(
            denied_actions=frozenset({"delete"}),
            would_allow_actions=frozenset({"write"}),
        )
        assert len(result.authority_loss) == 0
        assert result.loss_ratio == 0.0

    def test_full_loss_when_complete_overlap(self) -> None:
        result = measure_authority_loss(
            denied_actions=frozenset({"write", "delete"}),
            would_allow_actions=frozenset({"write", "delete"}),
        )
        assert result.authority_loss == frozenset({"write", "delete"})
        assert result.loss_ratio == 1.0

    def test_partial_loss(self) -> None:
        result = measure_authority_loss(
            denied_actions=frozenset({"write", "delete", "share"}),
            would_allow_actions=frozenset({"write", "delete"}),
        )
        assert result.authority_loss == frozenset({"write", "delete"})
        assert 0.0 < result.loss_ratio < 1.0

    def test_empty_sets_give_zero_loss(self) -> None:
        result = measure_authority_loss(
            denied_actions=frozenset(),
            would_allow_actions=frozenset(),
        )
        assert len(result.authority_loss) == 0
        assert result.loss_ratio == 0.0

    def test_result_round_trips(self) -> None:
        result = measure_authority_loss(
            denied_actions=frozenset({"write"}),
            would_allow_actions=frozenset({"write"}),
        )
        d = result.to_dict()
        assert d["authority_loss"] == ["write"]
        assert d["loss_ratio"] == 1.0


class TestExposureMeasure:
    """Exposure is an empirical measure, not a security guarantee."""

    def test_basic_exposure(self) -> None:
        result = measure_exposure({"alice": 100, "mallory": 50})
        assert result.total_tokens == 150
        assert result.principal_count == 2

    def test_empty_exposure(self) -> None:
        result = measure_exposure({})
        assert result.total_tokens == 0
        assert result.principal_count == 0

    def test_result_round_trips(self) -> None:
        result = measure_exposure({"alice": 10})
        d = result.to_dict()
        assert d["total_tokens"] == 10
        assert d["principal_count"] == 1
