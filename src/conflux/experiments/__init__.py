"""Reproducible experiment definitions and retained-run metadata."""

from .agentdojo import AgentDojoCell, AgentDojoCellResult, agentdojo_matrix, run_agentdojo_comparison
from .manifest import ExperimentManifest, load_manifest
from .native_sled import AbstractExecutionState, CanonicalExecutionOracle, run_native_reproduction
from .planning_comparison import (
    PlanningMode,
    PlanningObservation,
    aggregate_planning_comparison,
    generate_planning_report,
)
from .planning_runner import (
    DiagnosticAction,
    DiagnosticScenario,
    ModeledWorld,
    PlanningCell,
    load_default_planning_diagnostic_suite,
    load_planning_diagnostic_suite,
    planning_matrix,
    run_planning_comparison,
)
from .protocol import (
    ExperimentProtocol,
    LocalModelSpec,
    ResolvedRunManifest,
    RunFailure,
    load_protocol,
)
from .resume import (
    ExperimentCase,
    ResumePlan,
    completion_marker,
    expand_cases,
    materialise_jobs,
    plan_resume,
)
from .smoke import BUNDLE_FILES, generate_smoke_bundle

__all__ = [
    "BUNDLE_FILES",
    "AbstractExecutionState",
    "AgentDojoCell",
    "AgentDojoCellResult",
    "CanonicalExecutionOracle",
    "ExperimentCase",
    "ExperimentManifest",
    "ExperimentProtocol",
    "DiagnosticAction",
    "DiagnosticScenario",
    "LocalModelSpec",
    "ModeledWorld",
    "PlanningMode",
    "PlanningObservation",
    "PlanningCell",
    "ResumePlan",
    "ResolvedRunManifest",
    "RunFailure",
    "aggregate_planning_comparison",
    "agentdojo_matrix",
    "completion_marker",
    "expand_cases",
    "generate_smoke_bundle",
    "generate_planning_report",
    "load_manifest",
    "load_default_planning_diagnostic_suite",
    "load_planning_diagnostic_suite",
    "load_protocol",
    "materialise_jobs",
    "plan_resume",
    "planning_matrix",
    "run_native_reproduction",
    "run_agentdojo_comparison",
    "run_planning_comparison",
]
