"""Part B classification evidence: retained counters for the archived prototype."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.reproducibility

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "research" / "output" / "runs" / "native-sled-partb-classification-v1"
HISTORICAL_TOTAL_TRACES = 1462607
HISTORICAL_INCOMPLETE = 218907


def _load_generator() -> Any:
    """Load the generator module without importing the scripts directory as a package."""
    path = ROOT / "scripts" / "generate_partb_classification_evidence.py"
    spec = importlib.util.spec_from_file_location("generate_partb_classification_evidence", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bundle() -> dict[str, Any]:
    """Return the retained classification evidence bundle."""
    data: dict[str, Any] = json.loads((BUNDLE / "result.json").read_text(encoding="utf-8"))
    return data


def test_bundle_reproduces_historical_totals_and_invariants(bundle: dict[str, Any]) -> None:
    totals = bundle["totals"]
    assert totals["traces_match"]
    assert totals["total_traces"] == HISTORICAL_TOTAL_TRACES
    assert totals["historical_incomplete"] == HISTORICAL_INCOMPLETE
    for environment in bundle["environments"]:
        historical = environment["historical_row"]
        assert historical["traces_match"]
        assert historical["blocked_pe_tasks_match"]
        assert environment["invariant"]["constant_across_seeds"]
        assert historical["invariant_in_observed_set"]
        assert environment["primary_run"]["status"] == "COMPLETE"


def test_primary_seed_run_is_reproducible_from_the_bundle(bundle: dict[str, Any]) -> None:
    module = _load_generator()
    lines = module.archived_lines()
    for environment in bundle["environments"]:
        source = module.build_source(environment["block"], lines)
        assert source == (BUNDLE / environment["source_file"]).read_text(encoding="utf-8")
    reproduced = {
        item["env_id"]: item["historical_row"]["historical_incomplete_observed"] for item in bundle["environments"]
    }
    assert reproduced == {"env1": True, "env2": False, "env3": True}
    environment = next(item for item in bundle["environments"] if item["env_id"] == "env3")
    source = module.build_source(environment["block"], lines)
    live = module.run_environment(environment["block"], environment["primary_seed"], source)
    assert live["status"] == "COMPLETE"
    assert live["total"] == environment["primary_run"]["total"]
    assert live["incomplete"] == environment["primary_run"]["incomplete"]
    assert live["counts"] == environment["primary_run"]["counts"]


def test_bundle_records_order_dependence_without_timing_fields(bundle: dict[str, Any]) -> None:
    variable = [item for item in bundle["environments"] if item["seed_sensitivity"]["distinct_signatures"] > 1]
    assert variable, "the archived classifier is order dependent; the bundle must record more than one signature"
    assert any(item["historical_row"]["exact_tuple_observed"] is False for item in bundle["environments"])
    protocol = json.loads((BUNDLE / "protocol.json").read_text(encoding="utf-8"))
    assert "hash order" in protocol["determinism"]
    assert protocol["negated_claims"]
    retained = (BUNDLE / "result.json").read_text(encoding="utf-8") + (BUNDLE / "protocol.json").read_text(encoding="utf-8")
    assert "wall_seconds" not in retained
    assert "elapsed" not in retained
