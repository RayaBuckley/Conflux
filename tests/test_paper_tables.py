"""Tests for paper tables aggregation."""

from __future__ import annotations

import json

from scripts.generate_paper_tables import generate


class TestPaperTables:
    """Test aggregated paper tables generation."""

    def test_bundle_has_correct_schema(self) -> None:
        bundle = generate()
        assert bundle["schema_version"] == "1"
        assert bundle["id"] == "paper-tables-v1"

    def test_has_tables(self) -> None:
        bundle = generate()
        assert len(bundle["tables"]) >= 3

    def test_has_evidence_index(self) -> None:
        bundle = generate()
        assert len(bundle["evidence_index"]) >= 5

    def test_has_evidence_sources(self) -> None:
        bundle = generate()
        assert "sledv_scaling" in bundle["evidence_sources"]
        assert "mutation_benchmark" in bundle["evidence_sources"]
        assert "provenance_precision" in bundle["evidence_sources"]

    def test_table_ids_are_unique(self) -> None:
        bundle = generate()
        ids = [t["table_id"] for t in bundle["tables"]]
        assert len(ids) == len(set(ids))

    def test_deterministic_regeneration(self) -> None:
        b1 = generate()
        b2 = generate()
        assert json.dumps(b1, sort_keys=True) == json.dumps(b2, sort_keys=True)

    def test_experiments_pending_listed(self) -> None:
        bundle = generate()
        pending = bundle["summary"]["experiments_pending"]
        assert "agentdojo_live" in pending
