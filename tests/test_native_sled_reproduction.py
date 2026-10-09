"""Paired native SLED reproduction and independent-oracle tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from conflux.adapters.scenarios import load_schema
from conflux.experiments import ExperimentProtocol, run_native_reproduction

pytestmark = pytest.mark.reproducibility

ROOT = Path(__file__).resolve().parents[1]


def _protocol() -> ExperimentProtocol:
    return ExperimentProtocol(
        id="native-sled-reproduction-v1",
        track="native_sled",
        suite={"id": "legacy-canonical-pairs", "version": "1"},
        source_commit="a" * 40,
        inputs={},
        model=None,
        prompts={},
        seeds=(0,),
        repetitions=1,
        bounds={"max_depth": 4, "max_states": 1000, "max_transitions": 5000, "max_model_calls": 4},
        environment={"python": "3.12", "platform": "test"},
        output_directory="research/output/runs/native-sled-reproduction-v1",
        rerun_command=("conflux", "sled", "reproduce", "--protocol", "protocol.json"),
    )


@pytest.fixture(scope="module")
def reproduction() -> dict[str, object]:
    """Run the paired reproduction once; only the determinism case runs it twice."""
    return run_native_reproduction(_protocol())


def test_native_reproduction_is_deterministic_strict_and_separates_suites() -> None:
    first = run_native_reproduction(_protocol())
    second = run_native_reproduction(_protocol())
    assert first == second
    Draft202012Validator(load_schema("native-sled-result-v2.schema.json")).validate(first)
    assert first["complete"] is True
    pairs = first["pairs"]
    assert isinstance(pairs, list) and len(pairs) == 3
    for pair in pairs:
        assert isinstance(pair, dict)
        results = pair["results"]
        assert isinstance(results, list) and len(results) == 12
        assert {row["suite"] for row in results} == {"legacy_reproduction", "canonical"}


def test_every_defective_monitor_has_a_shortest_witness_and_canonical_is_safe(
    reproduction: dict[str, object],
) -> None:
    controls = reproduction["negative_controls"]
    assert isinstance(controls, list)
    assert {item["defence"] for item in controls} == {
        "no_defence",
        "union_permissions",
        "initiator_only",
        "latest_input_only",
        "no_read_check",
    }
    assert all(item["killed"] and item["canonical_safe"] for item in controls)
    assert all(item["counterexample_length"] == 1 for item in controls)


def test_historical_comparison_is_explicitly_non_comparable(reproduction: dict[str, object]) -> None:
    comparison = reproduction["historical_comparison"]
    assert isinstance(comparison, dict)
    assert comparison == {
        "baseline_id": "archived-paper-sled-approximately-1.5m",
        "historical_trace_claim": 1500000,
        "current_transitions": 60,
        "classification": "enumeration_change",
        "comparable": False,
    }
    assert reproduction["performance"] == {
        "runtime_ms": None,
        "peak_memory_bytes": None,
        "measurement_status": "omitted_from_deterministic_fixture",
    }


def test_installed_fixture_layout_is_resolved_from_an_explicit_root(tmp_path: Path) -> None:
    """The installed wheel ships the fixtures under experiments/, not research/experiments."""
    shutil.copytree(ROOT / "research" / "experiments", tmp_path / "experiments")
    assert run_native_reproduction(_protocol(), tmp_path) == run_native_reproduction(_protocol())


def test_missing_fixtures_are_reported_as_unavailable(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="native_sled_reproduction_fixtures_unavailable"):
        run_native_reproduction(_protocol(), tmp_path)


def test_protocol_requires_native_track_without_model() -> None:
    protocol = _protocol()
    object.__setattr__(protocol, "track", "planning")
    try:
        run_native_reproduction(protocol, Path.cwd())
    except ValueError as error:
        assert str(error) == "native_sled_protocol_required"
    else:
        raise AssertionError("invalid protocol was accepted")
