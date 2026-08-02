"""Reproducible experiment definitions and retained-run metadata."""

from .agentdojo import AgentDojoCell, AgentDojoCellResult, agentdojo_matrix, run_agentdojo_comparison
from .coi_evidence import (
    COI_EVIDENCE_ROOT_FILES,
    compare_coi_evidence_bundle,
    generate_coi_evidence_bundle,
    verify_coi_evidence_checksums,
)
from .manifest import ExperimentManifest, load_manifest
from .native_evidence import (
    NATIVE_EVIDENCE_FILES,
    compare_native_sled_bundle,
    generate_native_sled_bundle,
    verify_native_sled_checksums,
)
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
    "COI_EVIDENCE_ROOT_FILES",
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
    "NATIVE_EVIDENCE_FILES",
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
    "compare_native_sled_bundle",
    "compare_coi_evidence_bundle",
    "expand_cases",
    "generate_smoke_bundle",
    "generate_native_sled_bundle",
    "generate_coi_evidence_bundle",
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
    "verify_native_sled_checksums",
    "verify_coi_evidence_checksums",
]
