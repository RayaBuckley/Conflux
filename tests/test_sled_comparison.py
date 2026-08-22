"""Reproducible comparison of trace and state exploration."""

from __future__ import annotations

import pytest

from conflux.experiments.sled_comparison import comparison

pytestmark = pytest.mark.reproducibility


def test_state_exploration_deduplicates_equivalent_continuations() -> None:
    first = comparison(6)
    second = comparison(6)
    assert first == second
    traces = first["trace_enumeration"]
    states = first["state_exploration"]
    assert isinstance(traces, dict) and isinstance(states, dict)
    assert states["unique_states"] < traces["state_visits"]
    assert states["duplicate_states"] > 0
