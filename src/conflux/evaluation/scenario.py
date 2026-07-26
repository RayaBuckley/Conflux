"""
SLED scenarios.
A scenario represents a single evaluation instance for a defence. It bundles
together the environment, the initial information available to the defence, and
configuration describing how the evaluation should proceed.
Scenarios are immutable so that evaluations are deterministic and repeatable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet

from .environment import Data, Environment


@dataclass(frozen=True, slots=True)
class Scenario:
    """
    A single evaluation scenario.
    Attributes
    ----------
    name:
        Human-readable identifier.
    environment:
        The environment in which the defence executes.
    initial_inputs:
        Data initially supplied to the defence.
    max_llm_calls:
        Upper bound on the number of LLM executions permitted during the
        evaluation.
    """
    name: str
    environment: Environment
    initial_inputs: FrozenSet[Data]
    max_llm_calls: int = 3
__all__ = [
    "Scenario",
]
