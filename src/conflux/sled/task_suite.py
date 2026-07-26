"""
SLED task suites.
A task suite is the benchmark-facing unit of evaluation. It groups together a
set of scenarios that should be executed under a common environment or family
of environments.
This is the first step toward benchmark integration:
- the suite defines what should be evaluated,
- the evaluator runs each scenario,
- the defence under test produces reports,
- benchmark logic can later score the outcomes.
The design is intentionally lightweight so it can support AgentDojo-style
benchmarks as well as custom evaluation harnesses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, Iterator, Protocol

from .scenario import Scenario


@dataclass(frozen=True, slots=True)
class BenchmarkExpectation:
    """
    An expectation associated with a benchmark task.
    Attributes
    ----------
    name:
        Short label for the expectation.
    description:
        Human-readable explanation of what should hold in the scenario.
    """
    name: str
    description: str = ""
@dataclass(frozen=True, slots=True)
class BenchmarkTask:
    """
    A single benchmark task.
    Attributes
    ----------
    name:
        Stable identifier for the task.
    scenario:
        The scenario to evaluate.
    expectations:
        High-level expectations used by benchmark logic to score the run.
    """
    name: str
    scenario: Scenario
    expectations: FrozenSet[BenchmarkExpectation] = field(default_factory=frozenset)
class TaskSuite(Protocol):
    """
    Base interface for benchmark task suites.
    """
    name: str

    def tasks(self) -> Iterator[BenchmarkTask]:
        """
        Yield the benchmark tasks in this suite.
        """
        ...
@dataclass(frozen=True, slots=True)
class StaticTaskSuite(TaskSuite):
    """
    Simple in-memory task suite.
    This is the most useful starting point because it lets you define a fixed
    set of benchmark tasks without introducing storage or loading logic yet.
    """
    name: str
    _tasks: tuple[BenchmarkTask, ...]
    def tasks(self) -> Iterator[BenchmarkTask]:
        yield from self._tasks
    @classmethod
    def from_iterable(
        cls,
        name: str,
        tasks: Iterable[BenchmarkTask],
    ) -> "StaticTaskSuite":
        """
        Build a static suite from an iterable of tasks.
        """
        return cls(name=name, _tasks=tuple(tasks))
    def __len__(self) -> int:
        return len(self._tasks)
__all__ = [
    "BenchmarkExpectation",
    "BenchmarkTask",
    "StaticTaskSuite",
    "TaskSuite",
]
