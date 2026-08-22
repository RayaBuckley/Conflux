"""Pinned AgentDojo comparison matrix over one self-hosted model."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Protocol

from jsonschema import Draft202012Validator

from conflux.adapters.scenarios import load_schema
from conflux.experiments.protocol import ExperimentProtocol
from conflux.ports import LocalModelPort

FAILURE_CATEGORIES = ("setup", "model", "parser", "policy", "security", "tool", "utility", "bound", "adapter", "unknown")


@dataclass(frozen=True, slots=True)
class AgentDojoCell:
    """A single cell in the AgentDojo comparison matrix."""

    attacked: bool
    defence: str
    repetition: int
    seed: int
    suite_id: str = "workspace"
    user_task_id: str = "user_task_17"
    injection_task_id: str = "injection_task_1"
    attack_id: str = "important_instructions"

    @property
    def id(self) -> str:
        """Return the deterministic identifier for this cell."""
        attack = "attacked" if self.attacked else "benign"
        return f"{self.suite_id}:{self.user_task_id}:{attack}:{self.defence}:r{self.repetition}:s{self.seed}"

    def to_dict(self) -> dict[str, object]:
        """Serialize this cell to a JSON-compatible dictionary."""
        return {
            "case_id": self.id,
            "attacked": self.attacked,
            "defence": self.defence,
            "repetition": self.repetition,
            "seed": self.seed,
            "suite_id": self.suite_id,
            "user_task_id": self.user_task_id,
            "injection_task_id": self.injection_task_id if self.attacked else None,
            "attack_id": self.attack_id if self.attacked else None,
        }


@dataclass(frozen=True, slots=True)
class AgentDojoCellResult:
    """Result of executing a single AgentDojo comparison cell."""

    cell: AgentDojoCell
    status: str
    native_utility: bool | None
    native_security: bool | None
    raw_log: str | None
    raw_sha256: str | None
    augmentation: tuple[Mapping[str, object], ...]
    failures: tuple[str, ...]
    model_calls: int
    prompt_tokens: int | None
    output_tokens: int | None
    latency_ms: int

    def __post_init__(self) -> None:
        """Freeze augmentations and validate failure categories."""
        object.__setattr__(self, "augmentation", tuple(MappingProxyType(dict(item)) for item in self.augmentation))
        unknown = set(self.failures) - set(FAILURE_CATEGORIES)
        if unknown:
            raise ValueError(f"unknown_agentdojo_failure:{sorted(unknown)[0]}")

    def to_dict(self) -> dict[str, object]:
        """Serialize this cell result to a JSON-compatible dictionary."""
        return {
            "case_id": self.cell.id,
            "attacked": self.cell.attacked,
            "defence": self.cell.defence,
            "repetition": self.cell.repetition,
            "seed": self.cell.seed,
            "status": self.status,
            "native_utility": self.native_utility,
            "native_security": self.native_security,
            "raw_log": self.raw_log,
            "raw_sha256": self.raw_sha256,
            "augmentation": [dict(item) for item in self.augmentation],
            "failures": list(self.failures),
            "model_calls": self.model_calls,
            "prompt_tokens": self.prompt_tokens,
            "output_tokens": self.output_tokens,
            "latency_ms": self.latency_ms,
        }


class AgentDojoCellExecutor(Protocol):
    """Protocol for executing an AgentDojo cell against a local model."""

    def execute(self, cell: AgentDojoCell, model: LocalModelPort, max_model_calls: int) -> AgentDojoCellResult:
        """Execute an AgentDojo cell and return the captured result."""
        ...


def agentdojo_matrix(protocol: ExperimentProtocol) -> tuple[AgentDojoCell, ...]:
    """Expand an AgentDojo protocol into its full cross-product of cells."""
    if protocol.track != "agentdojo" or protocol.model is None:
        raise ValueError("agentdojo_protocol_with_model_required")
    return tuple(
        AgentDojoCell(attacked, defence, repetition, seed)
        for attacked in (False, True)
        for defence in ("no_defence", "ites_conservative", "ites_oracle")
        for repetition in range(protocol.repetitions)
        for seed in protocol.seeds
    )


def run_agentdojo_comparison(
    protocol: ExperimentProtocol,
    model: LocalModelPort,
    executor: AgentDojoCellExecutor,
) -> dict[str, object]:
    """Execute every AgentDojo cell and return the validated comparison payload."""
    cells = agentdojo_matrix(protocol)
    preflight = model.preflight()
    if not preflight.available or preflight.model_id != protocol.model.model_id:  # type: ignore[union-attr]
        raise ValueError(preflight.reason or "local_model_identity_mismatch")
    max_calls = protocol.bounds.get("max_model_calls", 8)
    if not isinstance(max_calls, int) or isinstance(max_calls, bool) or max_calls < 1:
        raise ValueError("invalid_agentdojo_model_call_bound")
    results = tuple(executor.execute(cell, model, max_calls) for cell in cells)
    counts = {category: 0 for category in FAILURE_CATEGORIES}
    for result in results:
        for failure in result.failures:
            counts[failure] += 1
    payload: dict[str, object] = {
        "schema_version": "2",
        "protocol_fingerprint": protocol.fingerprint,
        "complete": all(result.status == "complete" for result in results),
        "model_id": protocol.model.model_id,  # type: ignore[union-attr]
        "cells": [result.to_dict() for result in results],
        "failure_counts": counts,
    }
    Draft202012Validator(load_schema("agentdojo-comparison-result-v2.schema.json")).validate(payload)
    return payload


__all__ = [
    "AgentDojoCell",
    "AgentDojoCellExecutor",
    "AgentDojoCellResult",
    "agentdojo_matrix",
    "run_agentdojo_comparison",
]
