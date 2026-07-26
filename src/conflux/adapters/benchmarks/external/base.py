"""Base interfaces for evaluating external defence implementations.

Unlike the native SLED defences, external defences are complete agent systems
implemented in their own repositories. This module defines the common interface
used to execute those systems and translate their outputs into SLED traces.

The overall architecture is:

    EnvironmentScenario
            │
            ▼
    ExternalDefenceRunner
            │
            ▼
    Real model execution
            │
            ▼
    External execution artefacts
            │
            ▼
    TraceAdapter
            │
            ▼
    ExecutionTrace
            │
            ▼
    Existing SLED pipeline

This keeps the evaluator independent from any particular defence repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

from ....evaluation.environment_suite import EnvironmentScenario
from ....evaluation.trace import ExecutionTrace


@dataclass(frozen=True)
class ExternalExecutionResult:
    """Raw output produced by an external defence implementation."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0

    model_name: str | None = None

    execution_time_seconds: float | None = None

    artefacts: Mapping[str, Any] = field(default_factory=dict)

    metadata: Mapping[str, Any] = field(default_factory=dict)


@runtime_checkable
class TraceAdapter(Protocol):
    """Converts external execution artefacts into SLED traces."""

    def convert(
        self,
        result: ExternalExecutionResult,
        *,
        scenario: EnvironmentScenario,
    ) -> Sequence[ExecutionTrace]:
        ...


@runtime_checkable
class ExternalDefenceRunner(Protocol):
    """Interface implemented by each external defence integration."""

    name: str
    description: str

    repository: str | None

    def prepare(self) -> None:
        """Prepare the repository for execution."""

    def run(
        self,
        *,
        scenario: EnvironmentScenario,
    ) -> ExternalExecutionResult:
        """Execute the defence implementation."""

    def trace_adapter(self) -> TraceAdapter:
        """Return the adapter used to convert outputs into SLED traces."""


@dataclass
class ExternalDefence:
    """Reference implementation of an external defence."""

    name: str

    description: str

    repository: str | None = None

    working_directory: Path | None = None

    metadata: Mapping[str, Any] = field(default_factory=dict)

    def prepare(self) -> None:
        """Prepare the implementation for execution.

        Default implementation does nothing.
        """
        return

    def run(
        self,
        *,
        scenario: EnvironmentScenario,
    ) -> ExternalExecutionResult:
        raise NotImplementedError

    def trace_adapter(self) -> TraceAdapter:
        raise NotImplementedError
