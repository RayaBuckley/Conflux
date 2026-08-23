"""Operator-gated dual-backend laptop planning smoke protocol."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import cast
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, ValidationError

from conflux.adapters.scenarios import load_schema
from conflux.domain import fingerprint
from conflux.experiments.planning_comparison import PlanningMode
from conflux.ports import LocalModelPort, LocalModelSpec

from .planning_runner import (
    DiagnosticScenario,
    load_default_planning_diagnostic_suite,
    run_planning_comparison,
)
from .protocol import ExperimentProtocol

BACKEND_TRANSFORMERS = "transformers"
BACKEND_LLAMA_CPP = "llama_cpp_q8_0"


@dataclass(frozen=True, slots=True)
class LaptopSmokeCell:
    """A single cell in the laptop planning smoke matrix."""

    backend: str
    scenario_id: str
    mode: PlanningMode
    repetition: int
    seed: int

    @property
    def id(self) -> str:
        """Return the deterministic identifier for this laptop smoke cell."""
        return f"{self.backend}:{self.scenario_id}:{self.mode.value}:r{self.repetition}:s{self.seed}"


@dataclass(frozen=True, slots=True)
class LaptopPlanningSmokePlan:
    """Immutable specification for a dual-backend laptop planning smoke run."""

    id: str
    source_model_id: str
    source_revision: str
    generated_llama_model_id: str
    tokenizer_id: str
    tokenizer_revision: str
    prompt_template_version: str
    seed: int
    repetitions: int
    scenario_ids: tuple[str, ...]
    modes: tuple[PlanningMode, ...]
    backends: tuple[str, ...]
    llama_cpp_release: str
    quantization: str
    bounds: Mapping[str, int]
    operator_gates: tuple[str, ...]
    stop_after_bundle: bool
    schema_version: str = "1"

    def __post_init__(self) -> None:
        """Freeze mutable fields and validate the plan against its schema."""
        object.__setattr__(self, "scenario_ids", tuple(self.scenario_ids))
        object.__setattr__(self, "modes", tuple(self.modes))
        object.__setattr__(self, "backends", tuple(self.backends))
        object.__setattr__(self, "bounds", MappingProxyType(dict(self.bounds)))
        object.__setattr__(self, "operator_gates", tuple(self.operator_gates))
        Draft202012Validator(load_schema("planning-laptop-smoke.schema.json")).validate(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        """Serialize this laptop planning smoke plan to a JSON-compatible dictionary."""
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "source_model_id": self.source_model_id,
            "source_revision": self.source_revision,
            "generated_llama_model_id": self.generated_llama_model_id,
            "tokenizer_id": self.tokenizer_id,
            "tokenizer_revision": self.tokenizer_revision,
            "prompt_template_version": self.prompt_template_version,
            "seed": self.seed,
            "repetitions": self.repetitions,
            "scenario_ids": list(self.scenario_ids),
            "modes": [mode.value for mode in self.modes],
            "backends": list(self.backends),
            "llama_cpp_release": self.llama_cpp_release,
            "quantization": self.quantization,
            "bounds": dict(self.bounds),
            "operator_gates": list(self.operator_gates),
            "stop_after_bundle": self.stop_after_bundle,
        }

    @property
    def fingerprint(self) -> str:
        """Return a content-based fingerprint of this plan."""
        return fingerprint(self.to_dict())

    def matrix(self) -> tuple[LaptopSmokeCell, ...]:
        """Expand this plan into its full cross-product of laptop smoke cells."""
        return tuple(
            LaptopSmokeCell(backend, scenario, mode, repetition, self.seed)
            for backend in self.backends
            for scenario in self.scenario_ids
            for mode in self.modes
            for repetition in range(self.repetitions)
        )


def load_laptop_planning_smoke(path: Path) -> LaptopPlanningSmokePlan:
    """Load and validate a laptop planning smoke plan from a JSON file."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator(load_schema("planning-laptop-smoke.schema.json")).validate(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as error:
        raise ValueError(f"laptop_smoke_plan_invalid:{type(error).__name__}") from error
    value = cast(dict[str, object], payload)
    return LaptopPlanningSmokePlan(
        id=cast(str, value["id"]),
        source_model_id=cast(str, value["source_model_id"]),
        source_revision=cast(str, value["source_revision"]),
        generated_llama_model_id=cast(str, value["generated_llama_model_id"]),
        tokenizer_id=cast(str, value["tokenizer_id"]),
        tokenizer_revision=cast(str, value["tokenizer_revision"]),
        prompt_template_version=cast(str, value["prompt_template_version"]),
        seed=cast(int, value["seed"]),
        repetitions=cast(int, value["repetitions"]),
        scenario_ids=tuple(cast(list[str], value["scenario_ids"])),
        modes=tuple(PlanningMode(item) for item in cast(list[str], value["modes"])),
        backends=tuple(cast(list[str], value["backends"])),
        llama_cpp_release=cast(str, value["llama_cpp_release"]),
        quantization=cast(str, value["quantization"]),
        bounds=cast(dict[str, int], value["bounds"]),
        operator_gates=tuple(cast(list[str], value["operator_gates"])),
        stop_after_bundle=cast(bool, value["stop_after_bundle"]),
    )


def validate_laptop_protocols(
    plan: LaptopPlanningSmokePlan,
    protocols: Mapping[str, ExperimentProtocol],
) -> None:
    """Validate that two backend protocols are consistent with the smoke plan."""
    if set(protocols) != set(plan.backends):
        raise ValueError("laptop_smoke_backend_pair_required")
    transformers = _model(protocols[BACKEND_TRANSFORMERS])
    llama = _model(protocols[BACKEND_LLAMA_CPP])
    for backend, protocol in protocols.items():
        model = _model(protocol)
        if protocol.track != "planning":
            raise ValueError(f"laptop_smoke_track_invalid:{backend}")
        configured_cases = cast(list[str], protocol.suite.get("case_ids", []))
        if tuple(configured_cases) != plan.scenario_ids:
            raise ValueError(f"laptop_smoke_scenarios_mismatch:{backend}")
        if protocol.seeds != (plan.seed,) or protocol.repetitions != plan.repetitions:
            raise ValueError(f"laptop_smoke_sampling_matrix_mismatch:{backend}")
        if dict(protocol.bounds) != dict(plan.bounds):
            raise ValueError(f"laptop_smoke_bounds_mismatch:{backend}")
        if protocol.prompts.get("planner") != plan.prompt_template_version:
            raise ValueError(f"laptop_smoke_prompt_mismatch:{backend}")
        if model.revision != plan.source_revision:
            raise ValueError(f"laptop_smoke_revision_mismatch:{backend}")
        if model.tokenizer_id != plan.tokenizer_id or model.tokenizer_revision != plan.tokenizer_revision:
            raise ValueError(f"laptop_smoke_tokenizer_mismatch:{backend}")
    if transformers.backend != "transformers" or transformers.model_id != plan.source_model_id:
        raise ValueError("laptop_smoke_transformers_identity_mismatch")
    if llama.backend != "openai_compatible" or llama.model_id != plan.generated_llama_model_id:
        raise ValueError("laptop_smoke_llama_identity_mismatch")
    if plan.llama_cpp_release not in llama.runtime_version:
        raise ValueError("laptop_smoke_llama_release_mismatch")
    endpoint = urlparse(llama.endpoint or "")
    if endpoint.hostname not in {"localhost", "127.0.0.1", "::1"} or llama.allow_private_remote:
        raise ValueError("laptop_smoke_llama_must_be_loopback")
    if _sampling(transformers) != _sampling(llama):
        raise ValueError("laptop_smoke_decoding_mismatch")


def run_laptop_planning_smoke(
    plan: LaptopPlanningSmokePlan,
    protocols: Mapping[str, ExperimentProtocol],
    models: Mapping[str, LocalModelPort],
    scenarios: tuple[DiagnosticScenario, ...] | None = None,
) -> dict[str, object]:
    """Execute both laptop backends and return the validated smoke result."""
    validate_laptop_protocols(plan, protocols)
    if set(models) != set(plan.backends):
        raise ValueError("laptop_smoke_model_pair_required")
    selected = scenarios or load_default_planning_diagnostic_suite()
    results = {backend: run_planning_comparison(protocols[backend], models[backend], selected) for backend in plan.backends}
    observations = [
        {"backend_id": backend, **observation}
        for backend in plan.backends
        for observation in cast(list[dict[str, object]], results[backend]["observations"])
    ]
    if len(observations) != len(plan.matrix()):
        raise ValueError("laptop_smoke_matrix_incomplete")
    result: dict[str, object] = {
        "schema_version": "1",
        "plan_fingerprint": plan.fingerprint,
        "complete": all(bool(result["complete"]) for result in results.values()),
        "model_identities": {backend: _model(protocols[backend]).to_dict() for backend in plan.backends},
        "observations": observations,
    }
    Draft202012Validator(load_schema("planning-laptop-smoke-result.schema.json")).validate(result)
    return result


def _sampling(model: LocalModelSpec) -> tuple[int, float, float, int, int, str]:
    return (
        model.seed,
        model.temperature,
        model.top_p,
        model.max_output_tokens,
        model.context_limit,
        model.prompt_template_version,
    )


def _model(protocol: ExperimentProtocol) -> LocalModelSpec:
    if protocol.model is None:
        raise ValueError("laptop_smoke_model_required")
    return protocol.model


__all__ = [
    "BACKEND_LLAMA_CPP",
    "BACKEND_TRANSFORMERS",
    "LaptopPlanningSmokePlan",
    "LaptopSmokeCell",
    "load_laptop_planning_smoke",
    "run_laptop_planning_smoke",
    "validate_laptop_protocols",
]
