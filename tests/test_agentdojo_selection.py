"""The frozen stratified AgentDojo selection stays sound and explains itself."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, cast

import pytest

from conflux.experiments.agentdojo_selection import (
    SuiteFacts,
    build_manifest,
    candidate_pairs,
    protocol_suite_blocks,
    selection_drift,
    selection_pairs,
    validate_manifest,
)

SELECTION = Path(__file__).resolve().parents[1] / "research/experiments/manifests/agentdojo-stratified-selection-v1.json"
MATCHES = "selection matches the installed benchmark"


def _facts() -> SuiteFacts:
    return SuiteFacts(
        suite_id="demo",
        benchmark_version="v1.2.2",
        user_task_ids=("user_task_0", "user_task_1", "user_task_2"),
        default_vectors=("vector_a", "vector_b", "vector_c", "vector_d"),
        candidates={
            "user_task_0": ("vector_a", "vector_b"),
            "user_task_1": ("vector_b", "vector_c"),
            "user_task_2": ("vector_a", "vector_c"),
        },
    )


def _manifest(**overrides: Any) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "facts": [_facts()],
        "per_stratum": 1,
        "excluded_task_ids": {},
        "package_version": "0.1.35",
        "benchmark_pin": "v1.2.2",
        "generated_utc": "2026-10-09T00:00:00Z",
        "command": "python scripts/select_agentdojo_tasks.py",
    }
    kwargs.update(overrides)
    return build_manifest(**kwargs)


@pytest.fixture(name="frozen")
def frozen_fixture() -> dict[str, Any]:
    return cast("dict[str, Any]", json.loads(SELECTION.read_text(encoding="utf-8")))


def test_frozen_selection_is_sound(frozen: dict[str, Any]) -> None:
    assert validate_manifest(frozen) == []


def test_frozen_selection_counts_are_the_measured_ones(frozen: dict[str, Any]) -> None:
    totals = frozen["totals"]
    assert totals["suites"] == 4
    assert totals["default_vectors"] == 39
    assert totals["unreachable_default_vectors"] == 3
    assert totals["strata"] == totals["pairs"] == 36
    assert totals["candidate_pairs"] == 153
    assert frozen["per_stratum"] == 1
    assert frozen["source"]["benchmark_pin"] == "v1.2.2"
    assert frozen["source"]["agentdojo_package"] == "0.1.35"


def test_frozen_selection_pins_the_measured_unreachable_vectors(frozen: dict[str, Any]) -> None:
    suites = frozen["suites"]
    assert suites["slack"]["unreachable_default_vectors"] == ["injection_phishing_1"]
    assert len(suites["workspace"]["unreachable_default_vectors"]) == 2
    assert suites["banking"]["unreachable_default_vectors"] == []
    assert suites["travel"]["unreachable_default_vectors"] == []


def test_frozen_selection_records_each_suites_own_tag(frozen: dict[str, Any]) -> None:
    tags = {suite_id: suite["benchmark_version"] for suite_id, suite in frozen["suites"].items()}
    assert tags == {
        "banking": "v1.2.2",
        "slack": "v1.2.0",
        "travel": "v1.2.0",
        "workspace": "v1.2.2",
    }
    assert protocol_suite_blocks(frozen)["slack"]["version"] == "v1.2.0"


def test_frozen_selection_pairs_are_unique_and_cover_every_stratum(frozen: dict[str, Any]) -> None:
    pairs = selection_pairs(frozen)
    assert len(pairs) == len(set(pairs)) == 36
    for suite_id, suite in frozen["suites"].items():
        chosen = {stratum["vector"] for stratum in suite["strata"]}
        assert chosen == set(suite["injection_vectors"]), suite_id


def test_build_manifest_takes_the_lowest_task_id_per_stratum() -> None:
    manifest = _manifest()
    assert validate_manifest(manifest) == []
    assert selection_pairs(manifest) == [
        ("demo", "user_task_0", "vector_a"),
        ("demo", "user_task_0", "vector_b"),
        ("demo", "user_task_1", "vector_c"),
    ]
    assert manifest["totals"]["selected_tasks"] == 2
    assert manifest["suites"]["demo"]["unreachable_default_vectors"] == ["vector_d"]
    assert manifest["totals"]["unreachable_default_vectors"] == 1


def test_build_manifest_honours_per_stratum() -> None:
    manifest = _manifest(per_stratum=2)
    assert validate_manifest(manifest) == []
    assert len(selection_pairs(manifest)) == 6  # two tasks offer each vector
    assert manifest["totals"]["strata"] == 3
    assert manifest["totals"]["pairs"] == 6


def test_build_manifest_skips_excluded_tasks() -> None:
    manifest = _manifest(excluded_task_ids={"demo": ["user_task_0"]})
    assert validate_manifest(manifest) == []
    assert selection_pairs(manifest) == [
        ("demo", "user_task_2", "vector_a"),
        ("demo", "user_task_1", "vector_b"),
        ("demo", "user_task_1", "vector_c"),
    ]


def test_an_exclusion_that_empties_a_stratum_is_reported() -> None:
    manifest = _manifest(excluded_task_ids={"demo": ["user_task_0", "user_task_1", "user_task_2"]})
    problems = validate_manifest(manifest)
    assert any("no pair chosen for strata ['vector_a'" in problem for problem in problems)


def test_unknown_excluded_tasks_are_refused() -> None:
    with pytest.raises(ValueError, match="excluded tasks unknown to demo"):
        _manifest(excluded_task_ids={"demo": ["user_task_9"]})


def test_a_non_positive_per_stratum_is_refused() -> None:
    with pytest.raises(ValueError, match="per_stratum must be positive"):
        _manifest(per_stratum=0)


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda manifest: manifest["suites"]["demo"]["strata"].pop(), "no pair chosen for strata"),
        (
            lambda manifest: manifest["suites"]["demo"]["strata"][0].__setitem__("task_id", "user_task_1"),
            "does not offer",
        ),
        (
            lambda manifest: manifest["suites"]["demo"]["strata"].append(
                dict(manifest["suites"]["demo"]["strata"][0]),
            ),
            "repeats a (suite, task, vector) pair",
        ),
        (lambda manifest: manifest["totals"].__setitem__("pairs", 99), "totals.pairs is 99"),
        (lambda manifest: manifest.__setitem__("body_digest", "sha256:0"), "body_digest does not match"),
        (
            lambda manifest: manifest["suites"]["demo"].__setitem__("unreachable_default_vectors", []),
            "unreachable_default_vectors is []",
        ),
        (lambda manifest: manifest.pop("protocol_suite_blocks"), "missing key protocol_suite_blocks"),
        (
            lambda manifest: manifest["protocol_suite_blocks"]["demo"].__setitem__("task_ids", ["user_task_9"]),
            "protocol_suite_blocks does not match",
        ),
    ],
)
def test_validation_rejects_a_mutated_manifest(mutate: Any, expected: str) -> None:
    manifest = _manifest()
    mutate(manifest)
    problems = validate_manifest(manifest)
    assert problems, "a mutated manifest must not validate"
    assert any(expected in problem for problem in problems), problems


def test_drift_reports_both_directions() -> None:
    manifest = _manifest()
    assert selection_drift(manifest, copy.deepcopy(manifest)) == [MATCHES]
    changed = copy.deepcopy(manifest)
    changed["suites"]["demo"]["strata"][0]["task_id"] = "user_task_1"
    report = selection_drift(manifest, changed)
    assert any("measured but not frozen" in item for item in report)
    assert any("frozen but not measured" in item for item in report)


def test_candidate_pairs_counts_the_pool() -> None:
    assert candidate_pairs([_facts()]) == 6
