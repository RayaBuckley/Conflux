"""Offline direction evidence remains deterministic and claim-limited."""

from __future__ import annotations

import json
from pathlib import Path

from conflux.experiments import (
    compare_direction_evidence_bundle,
    generate_direction_evidence_bundle,
)


def test_direction_bundle_separates_readiness_from_bounded_evidence(
    tmp_path: Path,
) -> None:
    output = tmp_path / "direction"
    generate_direction_evidence_bundle("abcdef0", output)
    for name, cells in (
        ("laptop-planning-preflight.json", 16),
        ("planning-preflight.json", 32),
        ("agentdojo-preflight.json", 4),
    ):
        payload = json.loads((output / name).read_text(encoding="utf-8"))
        assert payload["classification"] == "evaluation_ready"
        assert payload["complete"] is False
        assert len(payload["matrix"]) == cells
        assert all(cell["status"] == "unavailable" for cell in payload["matrix"])
    mutations = json.loads(
        (output / "security-mutations.json").read_text(encoding="utf-8")
    )
    assert mutations["classification"] == "bounded_evidence"
    assert mutations["canonical"]["disclosure"]["verdict"] == "safe"
    assert mutations["canonical"]["delegation"]["verdict"] == "safe"
    assert all(
        item["killed"]
        for group in mutations["mutants"].values()
        for item in group
    )
    assert all(
        item["verification"]["counterexample"]["length"] == 1
        for group in mutations["mutants"].values()
        for item in group
    )


def test_direction_bundle_regenerates_byte_identically(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate_direction_evidence_bundle("abcdef0", first)
    generate_direction_evidence_bundle("abcdef0", second)
    assert compare_direction_evidence_bundle(first, second) == ()
