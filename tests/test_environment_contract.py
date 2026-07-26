"""Tests for provider-neutral immutable environment contracts."""

from __future__ import annotations

import pytest

from conflux.core import Principal
from conflux.domain.environment import DataItem, EnvironmentSnapshot


def test_data_item_separates_scenario_metadata_from_provenance() -> None:
    principal = Principal("p", "Principal")
    item = DataItem(
        id="item-1",
        authors=frozenset({principal}),
        readers=frozenset({principal}),
        label="scenario-label",
        metadata={"scenario": "task-1"},
    )

    assert item.provenance().principals == frozenset({principal})
    assert "scenario" not in item.provenance().tags
    assert item.to_artifact().provenance.operations == frozenset({"environment_input"})


def test_environment_snapshot_is_immutable_and_provider_neutral() -> None:
    item = DataItem("item-1")
    snapshot = EnvironmentSnapshot(frozenset({item}), provider_id="fixture")

    assert snapshot.contains_all({item})
    with pytest.raises(TypeError):
        snapshot.metadata["changed"] = True  # type: ignore[index]
