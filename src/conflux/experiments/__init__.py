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
from .direction_evidence import (
    DIRECTION_EVIDENCE_FILES,
    compare_direction_evidence_bundle,
    generate_direction_evidence_bundle,
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
    "BACKEND_LLAMA_CPP",
    "BACKEND_TRANSFORMERS",
    "BUNDLE_FILES",
    "CEDAR_EVIDENCE_FILES",
    "COI_EVIDENCE_ROOT_FILES",
    "DIRECTION_EVIDENCE_FILES",
    "NATIVE_EVIDENCE_FILES",
    "AbstractExecutionState",
    "AgentDojoCell",
    "AgentDojoCellResult",
    "CanonicalExecutionOracle",
    "CedarDifferentialCase",
    "CedarDifferentialCorpus",
    "DiagnosticAction",
    "DiagnosticScenario",
    "ExperimentCase",
    "ExperimentManifest",
    "ExperimentProtocol",
    "LaptopPlanningSmokePlan",
    "LaptopSmokeCell",
    "LocalModelSpec",
    "ModeledWorld",
    "PlanningCell",
    "PlanningMode",
    "PlanningObservation",
    "ResolvedRunManifest",
    "ResumePlan",
    "RunFailure",
    "agentdojo_matrix",
    "aggregate_planning_comparison",
    "cedar_differential_preflight",
    "compare_cedar_preflight_bundle",
    "compare_coi_evidence_bundle",
    "compare_direction_evidence_bundle",
    "compare_native_sled_bundle",
    "completion_marker",
    "expand_cases",
    "generate_cedar_preflight_bundle",
    "generate_coi_evidence_bundle",
    "generate_direction_evidence_bundle",
    "generate_native_sled_bundle",
    "generate_planning_report",
    "generate_smoke_bundle",
    "load_cedar_bundle",
    "load_cedar_corpus",
    "load_default_planning_diagnostic_suite",
    "load_laptop_planning_smoke",
    "load_manifest",
    "load_planning_diagnostic_suite",
    "load_protocol",
    "materialise_jobs",
    "plan_resume",
    "planning_matrix",
    "run_agentdojo_comparison",
    "run_laptop_planning_smoke",
    "run_native_reproduction",
    "run_planning_comparison",
    "validate_laptop_protocols",
    "verify_cedar_preflight_checksums",
    "verify_coi_evidence_checksums",
    "verify_native_sled_checksums",
]
