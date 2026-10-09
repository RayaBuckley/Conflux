"""Tests for paper tables aggregation."""

from __future__ import annotations

import json
from typing import Any

import pytest

from scripts.generate_paper_tables import generate


@pytest.fixture(scope="module")
def bundle() -> dict[str, Any]:
    """Build the aggregated tables bundle once; two generations are only for the determinism check."""
    return generate()


class TestPaperTables:
    """Test aggregated paper tables generation."""

    def test_bundle_has_correct_schema(self, bundle: dict[str, Any]) -> None:
        assert bundle["schema_version"] == "1"
        assert bundle["id"] == "paper-tables-v1"

    def test_has_tables(self, bundle: dict[str, Any]) -> None:
        assert len(bundle["tables"]) >= 3

    def test_has_evidence_index(self, bundle: dict[str, Any]) -> None:
        assert len(bundle["evidence_index"]) >= 5

    def test_has_evidence_sources(self, bundle: dict[str, Any]) -> None:
        assert "sledv_scaling" in bundle["evidence_sources"]
        assert "mutation_benchmark" in bundle["evidence_sources"]
        assert "provenance_precision" in bundle["evidence_sources"]

    def test_table_ids_are_unique(self, bundle: dict[str, Any]) -> None:
        ids = [t["table_id"] for t in bundle["tables"]]
        assert len(ids) == len(set(ids))

    def test_deterministic_regeneration(self) -> None:
        b1 = generate()
        b2 = generate()
        assert json.dumps(b1, sort_keys=True) == json.dumps(b2, sort_keys=True)

    def test_experiments_pending_listed(self, bundle: dict[str, Any]) -> None:
        pending = bundle["summary"]["experiments_pending"]
        assert "agentdojo_live" in pending
