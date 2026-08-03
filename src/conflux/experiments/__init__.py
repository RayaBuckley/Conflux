"""Reproducible experiment definitions and retained-run metadata."""

from .agentdojo import AgentDojoCell, AgentDojoCellResult, agentdojo_matrix, run_agentdojo_comparison
from .cedar_evidence import (
    CEDAR_EVIDENCE_FILES,
    compare_cedar_preflight_bundle,
    generate_cedar_preflight_bundle,
    verify_cedar_preflight_checksums,
)
from .cedar_preflight import (
    CedarDifferentialCase,
    CedarDifferentialCorpus,
    cedar_differential_preflight,
    load_cedar_bundle,
    load_cedar_corpus,
)
from .coi_evidence import (
    COI_EVIDENCE_ROOT_FILES,
    compare_coi_evidence_bundle,
    generate_coi_evidence_bundle,
    verify_coi_evidence_checksums,
)
from .laptop_smoke import (
    BACKEND_LLAMA_CPP,
    BACKEND_TRANSFORMERS,
    LaptopPlanningSmokePlan,
    LaptopSmokeCell,
    load_laptop_planning_smoke,
    run_laptop_planning_smoke,
    validate_laptop_protocols,
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
    "BACKEND_LLAMA_CPP",
    "BACKEND_TRANSFORMERS",
    "COI_EVIDENCE_ROOT_FILES",
    "AbstractExecutionState",
    "AgentDojoCell",
    "AgentDojoCellResult",
    "CedarDifferentialCase",
    "CedarDifferentialCorpus",
    "CEDAR_EVIDENCE_FILES",
    "CanonicalExecutionOracle",
    "ExperimentCase",
    "ExperimentManifest",
    "ExperimentProtocol",
    "DiagnosticAction",
    "DiagnosticScenario",
    "LocalModelSpec",
    "LaptopPlanningSmokePlan",
    "LaptopSmokeCell",
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
    "cedar_differential_preflight",
    "compare_cedar_preflight_bundle",
    "completion_marker",
    "compare_native_sled_bundle",
    "compare_coi_evidence_bundle",
    "expand_cases",
    "generate_smoke_bundle",
    "generate_native_sled_bundle",
    "generate_coi_evidence_bundle",
    "generate_planning_report",
    "load_manifest",
    "load_laptop_planning_smoke",
    "load_default_planning_diagnostic_suite",
    "load_planning_diagnostic_suite",
    "load_protocol",
    "load_cedar_bundle",
    "load_cedar_corpus",
    "generate_cedar_preflight_bundle",
    "materialise_jobs",
    "plan_resume",
    "planning_matrix",
    "run_native_reproduction",
    "run_laptop_planning_smoke",
    "run_agentdojo_comparison",
    "run_planning_comparison",
    "verify_native_sled_checksums",
    "validate_laptop_protocols",
    "verify_coi_evidence_checksums",
    "verify_cedar_preflight_checksums",
]
