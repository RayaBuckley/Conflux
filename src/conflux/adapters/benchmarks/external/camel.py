"""CaMeL external defence adapter.

This module provides a thin integration layer for evaluating CaMeL-style
systems against SLED. The goal is not to reimplement CaMeL internally, but to
wrap an external repository and translate its observable outputs into the
canonical SLED trace model.

The adapter is intentionally conservative:

- it does not assume a particular CaMeL repository layout,
- it does not assume a specific CLI unless configured,
- it treats repository-specific artefacts as opaque,
- and it keeps the trace translation logic separate from execution.

The evaluator can then compare CaMeL against ITES and weaker baselines under a
common environment and reporting pipeline.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from ....evaluation.environment_suite import EnvironmentScenario
from ....evaluation.trace import (
    DecisionOutcome,
    ExecutionTrace,
    TraceContext,
    TraceEvent,
    TraceEventKind,
    TraceKind,
)
from .base import ExternalDefence, ExternalExecutionResult, TraceAdapter
from .runner import extract_execution_time


@dataclass(frozen=True)
class CaMeLConfig:
    """Execution configuration for an external CaMeL repository."""

    repository_root: Path
    entrypoint: Sequence[str] = field(default_factory=tuple)
    working_directory: Path | None = None

    python_executable: str = "python"
    timeout_seconds: int | None = None

    environment_file: str | None = None
    output_file: str | None = None

    extra_args: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


class CaMeLTraceAdapter(TraceAdapter):
    """Convert CaMeL execution artefacts into SLED traces."""

    def convert(
        self,
        result: ExternalExecutionResult,
        *,
        scenario: EnvironmentScenario,
    ) -> Sequence[ExecutionTrace]:
        traces: list[ExecutionTrace] = []

        artefacts = result.artefacts or {}
        raw_traces = _extract_raw_traces(artefacts, result.stdout)

        if not raw_traces:
            trace = _trace_from_artefacts(
                artefacts,
                scenario=scenario,
                defence_name="CaMeL",
                execution_result=result,
            )
            return (trace,)

        for index, raw_trace in enumerate(raw_traces):
            traces.append(
                _trace_from_raw_trace(
                    raw_trace,
                    scenario=scenario,
                    defence_name="CaMeL",
                    execution_result=result,
                    index=index,
                )
            )

        return tuple(traces)


@dataclass
class CaMeLExternalDefence(ExternalDefence):
    """External runner for a CaMeL-style defence repository."""

    name: str = "CaMeL"
    description: str = (
        "External CaMeL-style defence runner wrapped for SLED evaluation."
    )

    config: CaMeLConfig | None = None

    def prepare(self) -> None:
        if self.config is None:
            raise ValueError("CaMeLExternalDefence requires a CaMeLConfig.")

        if not self.config.repository_root.exists():
            raise FileNotFoundError(
                f"Repository root does not exist: {self.config.repository_root}"
            )

    def run(
        self,
        *,
        scenario: EnvironmentScenario,
    ) -> ExternalExecutionResult:
        if self.config is None:
            raise ValueError("CaMeLExternalDefence requires a CaMeLConfig.")

        cmd = self._build_command(scenario)
        cwd = self.config.working_directory or self.config.repository_root

        completed = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=self.config.timeout_seconds,
            check=False,
        )

        artefacts = self._load_artefacts(completed.stdout, completed.stderr)
        return ExternalExecutionResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
            model_name=artefacts.get("model_name"),
            execution_time_seconds=extract_execution_time(artefacts),
            artefacts=artefacts,
            metadata={
                **dict(self.metadata),
                **dict(self.config.metadata),
                "runner": "camel",
                "repository_root": str(self.config.repository_root),
                "scenario_id": scenario.id,
                "scenario_name": scenario.name,
            },
        )

    def trace_adapter(self) -> TraceAdapter:
        return CaMeLTraceAdapter()

    def _build_command(self, scenario: EnvironmentScenario) -> list[str]:
        if self.config is None:
            raise ValueError("CaMeLExternalDefence requires a CaMeLConfig.")

        command = [self.config.python_executable]
        command.extend(str(part) for part in self.config.entrypoint)

        if self.config.environment_file:
            command.extend(["--environment-file", self.config.environment_file])

        if self.config.output_file:
            command.extend(["--output-file", self.config.output_file])

        command.extend(["--scenario-id", scenario.id])
        command.extend(["--scenario-name", scenario.name])

        for principal in scenario.principals:
            command.extend(["--principal", principal])

        for datum in scenario.data_items:
            command.extend(["--datum", datum])

        for tool in scenario.tools:
            command.extend(["--tool", tool])

        command.extend(self.config.extra_args)
        return command

    @staticmethod
    def _load_artefacts(stdout: str, stderr: str) -> dict[str, Any]:
        """Best-effort parse for structured artefacts emitted by the repo."""
        artefacts: dict[str, Any] = {}

        for blob in (stdout, stderr):
            parsed = _try_parse_json_blob(blob)
            if parsed is not None:
                artefacts.update(parsed)

        return artefacts


def make_camel_external_defence(
    repository_root: str | Path,
    *,
    entrypoint: Sequence[str],
    working_directory: str | Path | None = None,
    python_executable: str = "python",
    timeout_seconds: int | None = None,
    environment_file: str | None = None,
    output_file: str | None = None,
    extra_args: Sequence[str] = (),
    metadata: Mapping[str, Any] | None = None,
) -> CaMeLExternalDefence:
    """Convenience constructor for a CaMeL integration."""
    config = CaMeLConfig(
        repository_root=Path(repository_root),
        entrypoint=tuple(entrypoint),
        working_directory=None if working_directory is None else Path(working_directory),
        python_executable=python_executable,
        timeout_seconds=timeout_seconds,
        environment_file=environment_file,
        output_file=output_file,
        extra_args=tuple(extra_args),
        metadata=metadata or {},
    )
    return CaMeLExternalDefence(
        name="CaMeL",
        description="External CaMeL-style defence runner wrapped for SLED evaluation.",
        config=config,
        repository=str(Path(repository_root)),
        working_directory=None if working_directory is None else Path(working_directory),
        metadata=metadata or {},
    )


def _extract_raw_traces(
    artefacts: Mapping[str, Any],
    stdout: str,
) -> list[Any]:
    """Extract raw trace objects from structured output."""
    if "traces" in artefacts and isinstance(artefacts["traces"], list):
        return list(artefacts["traces"])

    if "trace" in artefacts:
        value = artefacts["trace"]
        return value if isinstance(value, list) else [value]

    parsed = _try_parse_json_blob(stdout)
    if parsed is None:
        return []

    if "traces" in parsed and isinstance(parsed["traces"], list):
        return list(parsed["traces"])

    if "trace" in parsed:
        value = parsed["trace"]
        return value if isinstance(value, list) else [value]

    return []


def _trace_from_artefacts(
    artefacts: Mapping[str, Any],
    *,
    scenario: EnvironmentScenario,
    defence_name: str,
    execution_result: ExternalExecutionResult,
) -> ExecutionTrace:
    """Create a fallback trace from structured artefacts."""
    context = TraceContext(
        initiator=_first_text(artefacts, "initiator", "principal", "requester", "user"),
        latest_principal=_first_text(artefacts, "latest_principal", "principal"),
        principal_history=tuple(_string_list(artefacts, "principal_history", "influencing_principals")),
        influencing_principals=frozenset(_string_list(artefacts, "influencing_principals", "principals")),
        plan_id=_first_text(artefacts, "plan_id", "execution_id", "trace_id"),
        capability_ids=frozenset(_string_list(artefacts, "capability_ids", "tokens")),
        labels=frozenset(_string_list(artefacts, "labels", "tags")),
        metadata=dict(artefacts),
    )

    return ExecutionTrace(
        trace_id=_first_text(artefacts, "trace_id", "id") or f"{scenario.id}:{defence_name}:0",
        kind=TraceKind.REAL,
        context=context,
        events=(),
        task_name=scenario.name,
        environment_name=scenario.name,
        defence_name=defence_name,
        complete=not bool(artefacts.get("incomplete", False)),
        blocked=bool(artefacts.get("blocked", False)),
        violation=bool(artefacts.get("violation", False)),
        max_depth_reached=bool(artefacts.get("max_depth_reached", False)),
        labels=frozenset(_string_list(artefacts, "labels", "tags")),
        metadata={
            **dict(artefacts),
            "exit_code": execution_result.exit_code,
            "stdout": execution_result.stdout,
            "stderr": execution_result.stderr,
        },
    )


def _trace_from_raw_trace(
    raw_trace: Any,
    *,
    scenario: EnvironmentScenario,
    defence_name: str,
    execution_result: ExternalExecutionResult,
    index: int,
) -> ExecutionTrace:
    """Convert one raw trace object into a canonical SLED trace."""
    if isinstance(raw_trace, ExecutionTrace):
        return raw_trace

    if isinstance(raw_trace, Mapping):
        artefacts = dict(raw_trace)
    else:
        artefacts = {
            key: getattr(raw_trace, key, None)
            for key in (
                "trace_id",
                "id",
                "kind",
                "task_name",
                "environment_name",
                "defence_name",
                "complete",
                "blocked",
                "violation",
                "max_depth_reached",
                "labels",
                "tags",
                "metadata",
                "context",
                "events",
            )
            if getattr(raw_trace, key, None) is not None
        }

    events = _coerce_events(artefacts.get("events", ()))
    context_data = artefacts.get("context")
    context = _coerce_context(context_data, artefacts)

    kind_value = artefacts.get("kind", TraceKind.REAL.value)
    if isinstance(kind_value, TraceKind):
        kind = kind_value
    else:
        try:
            kind = TraceKind(str(kind_value))
        except Exception:
            kind = TraceKind.REAL

    return ExecutionTrace(
        trace_id=str(
            artefacts.get("trace_id")
            or artefacts.get("id")
            or f"{scenario.id}:{defence_name}:{index}"
        ),
        kind=kind,
        context=context,
        events=events,
        task_name=artefacts.get("task_name") or scenario.name,
        environment_name=artefacts.get("environment_name") or scenario.name,
        defence_name=artefacts.get("defence_name") or defence_name,
        complete=bool(artefacts.get("complete", True)),
        blocked=bool(artefacts.get("blocked", False)),
        violation=bool(artefacts.get("violation", False)),
        max_depth_reached=bool(artefacts.get("max_depth_reached", False)),
        labels=frozenset(_string_list(artefacts, "labels", "tags")),
        metadata={
            **dict(artefacts.get("metadata", {}) or {}),
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
            "exit_code": execution_result.exit_code,
        },
    )


def _coerce_context(context_data: Any, artefacts: Mapping[str, Any]) -> TraceContext:
    """Best-effort conversion of arbitrary context data."""
    if isinstance(context_data, TraceContext):
        return context_data

    if isinstance(context_data, Mapping):
        return TraceContext(
            initiator=_first_text(context_data, "initiator", "principal", "requester", "user"),
            latest_principal=_first_text(context_data, "latest_principal", "principal"),
            principal_history=tuple(_string_list(context_data, "principal_history", "influencing_principals")),
            influencing_principals=frozenset(_string_list(context_data, "influencing_principals", "principals")),
            plan_id=_first_text(context_data, "plan_id", "execution_id"),
            capability_ids=frozenset(_string_list(context_data, "capability_ids", "tokens")),
            labels=frozenset(_string_list(context_data, "labels", "tags")),
            metadata=dict(context_data),
        )

    if context_data is not None:
        return TraceContext(
            initiator=getattr(context_data, "initiator", None),
            latest_principal=getattr(context_data, "latest_principal", None),
            principal_history=tuple(getattr(context_data, "principal_history", ()) or ()),
            influencing_principals=frozenset(getattr(context_data, "influencing_principals", ()) or ()),
            plan_id=getattr(context_data, "plan_id", None),
            capability_ids=frozenset(getattr(context_data, "capability_ids", ()) or ()),
            labels=frozenset(getattr(context_data, "labels", ()) or ()),
            metadata=getattr(context_data, "metadata", {}) or {},
        )

    return TraceContext(
        initiator=_first_text(artefacts, "initiator", "principal", "requester", "user"),
        latest_principal=_first_text(artefacts, "latest_principal", "principal"),
        principal_history=tuple(_string_list(artefacts, "principal_history", "influencing_principals")),
        influencing_principals=frozenset(_string_list(artefacts, "influencing_principals", "principals")),
        plan_id=_first_text(artefacts, "plan_id", "execution_id"),
        capability_ids=frozenset(_string_list(artefacts, "capability_ids", "tokens")),
        labels=frozenset(_string_list(artefacts, "labels", "tags")),
        metadata=dict(artefacts),
    )


def _coerce_events(events: Any) -> tuple[TraceEvent, ...]:
    """Best-effort conversion of event-like objects to trace events."""
    if not events:
        return ()

    coerced: list[TraceEvent] = []
    for index, event in enumerate(events):
        if isinstance(event, TraceEvent):
            coerced.append(event)
            continue

        if isinstance(event, Mapping):
            raw = event
        else:
            raw = {
                key: getattr(event, key, None)
                for key in (
                    "id",
                    "event_id",
                    "kind",
                    "principal",
                    "subject",
                    "action",
                    "resource",
                    "input_text",
                    "output_text",
                    "decision",
                    "plan_step",
                    "capability",
                    "nested_trace_id",
                    "blocked",
                    "incomplete",
                    "error",
                    "labels",
                    "metadata",
                )
                if getattr(event, key, None) is not None
            }

        kind_value = raw.get("kind", TraceEventKind.OTHER)
        if isinstance(kind_value, TraceEventKind):
            kind = kind_value
        else:
            try:
                kind = TraceEventKind(str(kind_value))
            except Exception:
                kind = TraceEventKind.OTHER

        decision_value = raw.get("decision", DecisionOutcome.UNKNOWN)
        if isinstance(decision_value, DecisionOutcome):
            decision = decision_value
        else:
            try:
                decision = DecisionOutcome(str(decision_value))
            except Exception:
                decision = DecisionOutcome.UNKNOWN

        coerced.append(
            TraceEvent(
                id=str(raw.get("id") or raw.get("event_id") or f"event_{index}"),
                kind=kind,
                principal=raw.get("principal"),
                subject=raw.get("subject"),
                action=raw.get("action"),
                resource=raw.get("resource"),
                input_text=raw.get("input_text"),
                output_text=raw.get("output_text"),
                decision=decision,
                nested_trace_id=raw.get("nested_trace_id"),
                blocked=bool(raw.get("blocked", False)),
                incomplete=bool(raw.get("incomplete", False)),
                error=raw.get("error"),
                labels=frozenset(_string_list(raw, "labels", "tags")),
                metadata=dict(raw.get("metadata", {}) or {}),
            )
        )
    return tuple(coerced)


def _try_parse_json_blob(blob: str) -> dict[str, Any] | None:
    """Parse a JSON blob from stdout/stderr when possible."""
    text = blob.strip()
    if not text:
        return None

    try:
        data = json.loads(text)
    except Exception:
        return None

    return data if isinstance(data, dict) else None


def _first_text(obj: Any, *keys: str) -> str | None:
    """Return the first non-empty string from the given keys."""
    for key in keys:
        value = _extract(obj, key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _string_list(obj: Any, *keys: str) -> list[str]:
    """Return a list of strings from the first available key."""
    for key in keys:
        value = _extract(obj, key)
        if value is None:
            continue
        if isinstance(value, (list, tuple, set, frozenset)):
            return [str(item) for item in value if item is not None and str(item).strip()]
        return [str(value)]
    return []


def _extract(obj: Any, key: str) -> Any:
    """Extract a field from either a mapping or an attribute-bearing object."""
    if isinstance(obj, Mapping):
        return obj.get(key)
    return getattr(obj, key, None)
