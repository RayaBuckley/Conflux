"""
SLED: the evaluation environment.

SLED provides the environment and harness used to evaluate defences such as
ITES. It is responsible for constructing scenarios, exposing inputs, and
measuring outcomes so that defence guarantees can be assessed against a known
testbed.

ITES is the defence under test.
SLED is the evaluation engine.
"""

from __future__ import annotations

from conflux.core.actions import PrimitiveAction

from .environment import Data, Environment, LLMExecutionAction, Proposal
from .evaluator import Evaluator
from .scenario import Scenario
from .task_suite import (
    BenchmarkExpectation,
    BenchmarkTask,
    StaticTaskSuite,
    TaskSuite,
)

__all__ = [
    "BenchmarkExpectation",
    "BenchmarkTask",
    "Data",
    "Environment",
    "Evaluator",
    "LLMExecutionAction",
    "PrimitiveAction",
    "Proposal",
    "Scenario",
    "StaticTaskSuite",
    "TaskSuite",
]
