"""Tests for mutation benchmark evidence generation."""

from __future__ import annotations

import json
from typing import Any

import pytest

from scripts.generate_mutation_benchmark import (
    _delegation_ir_mutants,
    _delegation_mutants,
    _disclosure_mutants,
    _synthesis_mutants,
    generate,
)


@pytest.fixture(scope="module")
def bundle() -> dict[str, Any]:
    """Build the mutation benchmark bundle once; two generations are only for the determinism check."""
    return generate()


class TestMutationBenchmarkBundle:
    """Test the full evidence bundle generation."""

    def test_bundle_has_correct_schema(self, bundle: dict[str, Any]) -> None:
        assert bundle["schema_version"] == "1"
        assert bundle["id"] == "mutation-benchmark-v1"

    def test_bundle_has_all_families(self, bundle: dict[str, Any]) -> None:
        mutants = bundle["mutants"]
        assert "disclosure" in mutants
        assert "delegation" in mutants
        assert "delegation_ir" in mutants
        assert "synthesis" in mutants

    def test_total_mutants_meets_target(self, bundle: dict[str, Any]) -> None:
        """Must have >=20 mutants across >=4 families."""
        assert bundle["summary"]["total_mutants"] >= 20
        assert bundle["summary"]["family_count"] >= 4

    def test_all_mutants_killed(self, bundle: dict[str, Any]) -> None:
        """Every mutant must be killed by at least one backend."""
        assert bundle["summary"]["total_killed"] == bundle["summary"]["total_mutants"]
        assert bundle["summary"]["kill_rate"] == 1.0

    def test_deterministic_regeneration(self) -> None:
        b1 = generate()
        b2 = generate()
        assert json.dumps(b1, sort_keys=True) == json.dumps(b2, sort_keys=True)

    def test_claim_boundary_present(self, bundle: dict[str, Any]) -> None:
        assert "claim_boundary" in bundle
        assert "bound" in bundle["claim_boundary"].lower()

    def test_canonical_results_present(self, bundle: dict[str, Any]) -> None:
        assert "disclosure" in bundle["canonical"]
        assert "delegation" in bundle["canonical"]

    def test_family_summaries(self, bundle: dict[str, Any]) -> None:
        families = bundle["summary"]["families"]
        for metrics in families.values():
            assert metrics["count"] > 0
            assert metrics["killed"] == metrics["count"]
            assert metrics["backend"]


class TestDisclosureMutants:
    """Test disclosure mutant family."""

    def test_disclosure_count(self) -> None:
        _canonical, mutants = _disclosure_mutants()
        assert len(mutants) == 4

    def test_all_killed(self) -> None:
        _canonical, mutants = _disclosure_mutants()
        assert all(m["killed"] for m in mutants)

    def test_witness_length_is_one(self) -> None:
        """Native SLED mutants must be killed in 1 step."""
        _canonical, mutants = _disclosure_mutants()
        for m in mutants:
            assert m["witness_length"] == 1


class TestDelegationMutants:
    """Test delegation mutant family."""

    def test_delegation_count(self) -> None:
        _canonical, mutants = _delegation_mutants()
        assert len(mutants) == 7

    def test_all_killed(self) -> None:
        _canonical, mutants = _delegation_mutants()
        assert all(m["killed"] for m in mutants)


class TestDelegationIRMutants:
    """Test delegation IR mutant family."""

    def test_delegation_ir_count(self) -> None:
        mutants = _delegation_ir_mutants()
        assert len(mutants) == 10

    def test_all_killed(self) -> None:
        mutants = _delegation_ir_mutants()
        assert all(m["killed"] for m in mutants)

    def test_have_z3_results(self) -> None:
        mutants = _delegation_ir_mutants()
        for m in mutants:
            assert "z3_original" in m
            assert "z3_reduced" in m

    def test_have_coi_results(self) -> None:
        mutants = _delegation_ir_mutants()
        for m in mutants:
            assert "coi_equivalent" in m
            assert "original_variables" in m
            assert "reduced_variables" in m


class TestSynthesisMutants:
    """Test synthesis mutant family."""

    def test_synthesis_count(self) -> None:
        mutants = _synthesis_mutants()
        assert len(mutants) == 5

    def test_all_killed(self) -> None:
        mutants = _synthesis_mutants()
        assert all(m["killed"] for m in mutants)

    def test_have_verdict_and_witness(self) -> None:
        mutants = _synthesis_mutants()
        for m in mutants:
            assert m["verdict"] == "unsafe"
            assert m["witness_length"] > 0
