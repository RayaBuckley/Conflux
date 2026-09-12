"""Tests for SLED-V scaling evidence generation."""

from __future__ import annotations

import json

from scripts.generate_sledv_scaling_evidence import (
    HISTORICAL_TOTAL_STATES,
    HISTORICAL_TOTAL_TRACES,
    _run_fixture,
    _safe_depth_fixture,
    _safe_noise_fixture,
    _safe_principal_fixture,
    _unsafe_depth_fixture,
    _unsafe_noise_fixture,
    _unsafe_principal_fixture,
    generate,
)


class TestSledvScalingBundle:
    """Test the full evidence bundle generation."""

    def test_bundle_has_correct_schema(self) -> None:
        bundle = generate()
        assert bundle["schema_version"] == "1"
        assert bundle["id"] == "sledv-scaling-v1"

    def test_bundle_has_historical_anchor(self) -> None:
        bundle = generate()
        anchor = bundle["historical_anchor"]
        assert anchor["total_traces"] == HISTORICAL_TOTAL_TRACES
        assert anchor["total_canonical_states"] == HISTORICAL_TOTAL_STATES

    def test_bundle_has_all_scaling_families(self) -> None:
        bundle = generate()
        families = bundle["scaling_families"]
        assert "noise_scaling" in families
        assert "principal_scaling" in families
        assert "depth_scaling" in families

    def test_bundle_has_results(self) -> None:
        bundle = generate()
        assert len(bundle["fixtures"]) > 0
        assert bundle["summary"]["total_fixtures"] == len(bundle["fixtures"])

    def test_no_coi_verdict_downgrade(self) -> None:
        """COI reduction must never turn a safe verdict into unsafe."""
        bundle = generate()
        for r in bundle["fixtures"]:
            if r["original"]["verdict"] in ("safe", "bounded_safe"):
                assert r["reduced"]["verdict"] != "unsafe", f"{r['fixture_id']}: safe→unsafe downgrade"

    def test_z3_all_agree(self) -> None:
        """Z3 on original and reduced IR must agree where both succeed."""
        bundle = generate()
        assert bundle["summary"]["z3_all_agree"] is True

    def test_ref_z3_agree(self) -> None:
        """Reference and Z3 verdicts must agree where Z3 is available."""
        bundle = generate()
        assert bundle["summary"]["ref_z3_agree"] is True

    def test_deterministic_regeneration(self) -> None:
        b1 = generate()
        b2 = generate()
        assert json.dumps(b1, sort_keys=True) == json.dumps(b2, sort_keys=True)

    def test_by_family_summaries(self) -> None:
        bundle = generate()
        by_fam = bundle["by_family"]
        for metrics in by_fam.values():
            assert metrics["total_fixtures"] > 0
            assert metrics["max_original_states"] > 0
            assert metrics["max_reduced_states"] > 0

    def test_claim_boundary_present(self) -> None:
        bundle = generate()
        assert "claim_boundary" in bundle
        assert "bounded" in bundle["claim_boundary"].lower()


class TestFixtureBuilders:
    """Test individual fixture construction."""

    def test_safe_noise_fixture_has_n_noise_vars(self) -> None:
        f = _safe_noise_fixture(4)
        noise_vars = [v for v in f["variables"] if v["name"].startswith("noise")]
        assert len(noise_vars) == 4

    def test_unsafe_noise_fixture_has_control(self) -> None:
        f = _unsafe_noise_fixture(4)
        var_names = [v["name"] for v in f["variables"]]
        assert "control" in var_names

    def test_safe_principal_fixture_has_p_auth_vars(self) -> None:
        f = _safe_principal_fixture(8)
        auth_vars = [v for v in f["variables"] if v["name"].startswith("auth")]
        assert len(auth_vars) == 8

    def test_unsafe_principal_fixture_has_violate_transition(self) -> None:
        f = _unsafe_principal_fixture(4)
        rule_ids = [t["id"] for t in f["transitions"]]
        assert "apply-control" in rule_ids

    def test_safe_depth_fixture_chain_length(self) -> None:
        f = _safe_depth_fixture(3)
        chain_vars = [v for v in f["variables"] if v["name"].startswith("chain")]
        assert len(chain_vars) == 3

    def test_unsafe_depth_fixture_requires_k_plus_1_steps(self) -> None:
        f = _unsafe_depth_fixture(3)
        assert f["bound"] == 5  # k+2

    def test_all_fixtures_have_required_keys(self) -> None:
        from collections.abc import Callable

        builders: list[tuple[Callable[[int], dict[str, object]], int]] = [
            (_safe_noise_fixture, 4),
            (_unsafe_noise_fixture, 4),
            (_safe_principal_fixture, 4),
            (_unsafe_principal_fixture, 4),
            (_safe_depth_fixture, 3),
            (_unsafe_depth_fixture, 3),
        ]
        for builder, arg in builders:
            f = builder(arg)
            assert "schema_version" in f
            assert "id" in f
            assert "bound" in f
            assert "variables" in f
            assert "transitions" in f
            assert "invariants" in f


class TestRunFixture:
    """Test running a fixture through backends."""

    def test_safe_fixture_returns_safe_verdict(self) -> None:
        result = _run_fixture(_safe_noise_fixture(0))
        assert result["original"]["verdict"] in ("safe", "bounded_safe")

    def test_unsafe_fixture_returns_unsafe_verdict(self) -> None:
        result = _run_fixture(_unsafe_noise_fixture(0))
        assert result["original"]["verdict"] == "unsafe"

    def test_unsafe_fixture_has_witness(self) -> None:
        result = _run_fixture(_unsafe_noise_fixture(0))
        assert result["original"]["witness_length"] > 0

    def test_coi_reduces_variables(self) -> None:
        result = _run_fixture(_safe_noise_fixture(8))
        assert result["reduced"]["variables"] < result["original"]["variables"]

    def test_coi_preserves_verdict(self) -> None:
        result = _run_fixture(_unsafe_noise_fixture(4))
        assert result["original"]["verdict"] == result["reduced"]["verdict"]
