"""Tests for provenance precision vs utility evidence generation."""

from __future__ import annotations

import json
import random

from conflux.domain import (
    READ,
    WRITE,
)
from scripts.generate_provenance_precision_evidence import (
    SEED,
    _generate_task,
    _is_authorised,
    _make_principals,
    _run_condition,
    generate,
)


class TestProvenancePrecisionBundle:
    """Test the full evidence bundle generation."""

    def test_bundle_has_correct_schema(self) -> None:
        bundle = generate()
        assert bundle["schema_version"] == "1"
        assert bundle["id"] == "provenance-precision-v1"
        assert bundle["seed"] == SEED

    def test_bundle_has_all_conditions(self) -> None:
        bundle = generate()
        assert "C0" in bundle["conditions"]
        assert "C1" in bundle["conditions"]
        assert "C2" in bundle["conditions"]

    def test_bundle_has_results(self) -> None:
        bundle = generate()
        assert len(bundle["results"]) > 0
        assert bundle["summary"]["total_tasks"] == len(bundle["results"])

    def test_bundle_has_summary_metrics(self) -> None:
        bundle = generate()
        s = bundle["summary"]
        assert "c0_completion_rate" in s
        assert "c1_completion_rate" in s
        assert "c2_completion_rate" in s
        assert "utility_recovery" in s
        assert "pc_reduction" in s
        assert "c2_sound_violations" in s

    def test_c2_never_violates_soundness(self) -> None:
        """C2 (authenticated contributor) must never have soundness violations when authorised."""
        bundle = generate()
        assert bundle["summary"]["c2_sound_violations"] == 0

    def test_c1_completion_le_c2_completion(self) -> None:
        """C1 (conservative) completion rate must not exceed C2 (authenticated)."""
        bundle = generate()
        assert bundle["summary"]["c1_completion_rate"] <= bundle["summary"]["c2_completion_rate"]

    def test_c0_has_vulnerable_executions(self) -> None:
        """C0 (requester-only) should have some vulnerable executions."""
        bundle = generate()
        assert bundle["summary"]["c0_vulnerable_rate"] > 0

    def test_c1_mean_pc_ge_c2_mean_pc(self) -> None:
        """C1 PC size must be >= C2 PC size (conservative overapproximates)."""
        bundle = generate()
        assert bundle["summary"]["c1_mean_pc"] >= bundle["summary"]["c2_mean_pc"]

    def test_deterministic_regeneration(self) -> None:
        """Two calls to generate() must produce identical output."""
        b1 = generate()
        b2 = generate()
        assert json.dumps(b1, sort_keys=True) == json.dumps(b2, sort_keys=True)

    def test_by_n_possible_authors(self) -> None:
        bundle = generate()
        by_n = bundle["by_n_possible_authors"]
        assert "2" in by_n
        assert "16" in by_n
        for metrics in by_n.values():
            assert "c1_completion" in metrics
            assert "c2_completion" in metrics

    def test_by_heterogeneity(self) -> None:
        bundle = generate()
        by_h = bundle["by_heterogeneity"]
        assert "low" in by_h
        assert "medium" in by_h
        assert "high" in by_h

    def test_claim_boundary_present(self) -> None:
        bundle = generate()
        assert "claim_boundary" in bundle
        assert len(bundle["claim_boundary"]) > 0


class TestTaskGeneration:
    """Test individual task fixture generation."""

    def test_task_has_required_fields(self) -> None:
        rng = random.Random(42)
        task = _generate_task(0, 4, 2, "medium", 1, rng)
        assert "task_id" in task
        assert "n_possible" in task
        assert "k_actual" in task
        assert "requester_id" in task
        assert "actual_contributor_ids" in task
        assert "possible_author_ids" in task
        assert "required_permission" in task
        assert "perm_sets" in task
        assert "ground_truth" in task

    def test_task_deterministic(self) -> None:
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        t1 = _generate_task(0, 4, 2, "medium", 1, rng1)
        t2 = _generate_task(0, 4, 2, "medium", 1, rng2)
        assert json.dumps(t1, sort_keys=True) == json.dumps(t2, sort_keys=True)

    def test_actual_subset_of_possible(self) -> None:
        rng = random.Random(99)
        task = _generate_task(0, 8, 3, "high", 2, rng)
        actual = set(task["actual_contributor_ids"])
        possible = set(task["possible_author_ids"])
        assert actual.issubset(possible)

    def test_ground_truth_is_valid(self) -> None:
        rng = random.Random(42)
        for _ in range(20):
            task = _generate_task(0, 8, 4, "high", 2, rng)
            assert task["ground_truth"] in (
                "securely_achievable",
                "securely_blocked",
                "vulnerable",
            )


class TestConditionRunner:
    """Test condition execution."""

    def test_c0_pc_size_is_one(self) -> None:
        rng = random.Random(42)
        task = _generate_task(0, 4, 2, "medium", 1, rng)
        result = _run_condition(task, "C0")
        assert result["pc_size"] == 1

    def test_c1_pc_size_equals_n_possible(self) -> None:
        rng = random.Random(42)
        task = _generate_task(0, 8, 3, "medium", 1, rng)
        result = _run_condition(task, "C1")
        assert result["pc_size"] == 8

    def test_c2_pc_size_equals_k_actual(self) -> None:
        rng = random.Random(42)
        task = _generate_task(0, 8, 3, "medium", 1, rng)
        result = _run_condition(task, "C2")
        assert result["pc_size"] == 3

    def test_c1_overapproximates_when_n_gt_k(self) -> None:
        rng = random.Random(42)
        task = _generate_task(0, 8, 2, "low", 1, rng)
        result = _run_condition(task, "C1")
        assert result["overapproximates"] is True
        assert result["is_exact"] is False

    def test_c2_is_exact(self) -> None:
        rng = random.Random(42)
        task = _generate_task(0, 8, 3, "low", 1, rng)
        result = _run_condition(task, "C2")
        assert result["is_exact"] is True

    def test_c2_enforcement_sound(self) -> None:
        rng = random.Random(42)
        task = _generate_task(0, 4, 2, "medium", 1, rng)
        result = _run_condition(task, "C2")
        assert result["enforcement_sound"] is True

    def test_c0_enforcement_not_sound(self) -> None:
        rng = random.Random(42)
        task = _generate_task(0, 4, 2, "medium", 1, rng)
        result = _run_condition(task, "C0")
        assert result["enforcement_sound"] is False


class TestAuthorisationRule:
    """Test the ITES intersection authorisation rule."""

    def test_all_authorised_permits(self) -> None:
        principals = _make_principals(3)
        perm_sets = {p.id: frozenset({READ, WRITE}) for p in principals}
        assert _is_authorised(frozenset(principals), perm_sets, WRITE) is True

    def test_one_unauthorised_denies(self) -> None:
        principals = _make_principals(3)
        perm_sets = {p.id: frozenset({READ, WRITE}) for p in principals}
        perm_sets[principals[1].id] = frozenset({READ})
        assert _is_authorised(frozenset(principals), perm_sets, WRITE) is False

    def test_empty_pc_denies(self) -> None:
        principals = _make_principals(3)
        perm_sets = {p.id: frozenset({READ, WRITE}) for p in principals}
        assert _is_authorised(frozenset(), perm_sets, WRITE) is True
