"""Deterministic offline readiness and security-mutation evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

from conflux.adapters.scenarios import load_schema
from conflux.domain import canonical_json, fingerprint
from conflux.evaluation import (
    DELEGATION_PROPERTIES,
    CompleteAttribution,
    DelegationMutation,
    DelegationVerificationSystem,
    DisclosureMutation,
    DisclosureVerificationSystem,
    ExplicitStateChecker,
    NoHiddenDecisionLeakage,
    NoUnauthorisedSelector,
    SafeRedaction,
    VerificationBounds,
)

from .agentdojo import AgentDojoCell
from .laptop_smoke import load_laptop_planning_smoke
from .planning_comparison import PlanningMode
from .planning_runner import load_default_planning_diagnostic_suite

_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_OUTPUT = Path("runs/direction-readiness-v1")
DIRECTION_EVIDENCE_FILES = frozenset(
    {
        "CHECKSUMS.sha256",
        "RERUN.txt",
        "agentdojo-preflight.json",
        "laptop-planning-preflight.json",
        "manifest.json",
        "planning-preflight.json",
        "security-mutations.json",
        "table.md",
    },
)
DISCLOSURE_PROPERTIES = (
    NoUnauthorisedSelector(),
    NoHiddenDecisionLeakage(),
    CompleteAttribution(),
    SafeRedaction(),
)


def generate_direction_evidence_bundle(source_commit: str, output: Path, *, repo_root: Path | None = None) -> None:
    """Generate the offline direction-readiness and security-mutation evidence bundle."""
    root = repo_root or _ROOT
    laptop_plan = root / "experiments/manifests/planning-laptop-smoke-v1.json"
    planning_suite = root / "experiments/suites/planning-diagnostic-v1.yaml"
    planning_source = root / "src/conflux/experiments/planning_runner.py"
    agentdojo_manifest = root / "experiments/manifests/agentdojo-smoke.yaml"
    output.mkdir(parents=True, exist_ok=True)
    laptop = _laptop_preflight(laptop_plan, planning_source)
    planning = _planning_preflight(planning_source)
    agentdojo = _agentdojo_preflight()
    mutations = _security_mutations()
    payloads = {
        "laptop-planning-preflight.json": laptop,
        "planning-preflight.json": planning,
        "agentdojo-preflight.json": agentdojo,
        "security-mutations.json": mutations,
    }
    for name, payload in payloads.items():
        _write_json(output / name, payload)
    manifest = {
        "schema_version": "1",
        "id": "direction-readiness-v1",
        "source_commit": source_commit,
        "classification": {
            "laptop_planning": "evaluation_ready",
            "planning": "evaluation_ready",
            "agentdojo": "evaluation_ready",
            "security_mutations": "bounded_evidence",
        },
        "offline": True,
        "optional_runtimes_invoked": [],
        "inputs": {
            "laptop_plan_sha256": _file_sha256(laptop_plan),
            "planning_suite_sha256": _file_sha256(planning_suite),
            "planning_prompt_source_sha256": _file_sha256(planning_source),
            "agentdojo_manifest_sha256": _file_sha256(agentdojo_manifest),
        },
        "outputs": {name: fingerprint(payload) for name, payload in payloads.items()},
        "rerun_command": [
            "python",
            "scripts/generate_direction_evidence.py",
            CANONICAL_OUTPUT.as_posix(),
            "--source-commit",
            source_commit,
        ],
    }
    _validate("direction-readiness-manifest.schema.json", manifest)
    _write_json(output / "manifest.json", manifest)
    (output / "RERUN.txt").write_text(
        " ".join(cast(list[str], manifest["rerun_command"])) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output / "table.md").write_text(
        _table(laptop, planning, agentdojo, mutations),
        encoding="utf-8",
        newline="\n",
    )
    _write_checksums(output)


def compare_direction_evidence_bundle(retained: Path, regenerated: Path) -> tuple[str, ...]:
    """Return file names that are missing or differ between two direction evidence bundles."""
    names = {path.name for path in retained.iterdir() if path.is_file()} | {path.name for path in regenerated.iterdir() if path.is_file()}
    return tuple(
        name
        for name in sorted(names)
        if not (retained / name).is_file()
        or not (regenerated / name).is_file()
        or _canonical_bytes(retained / name) != _canonical_bytes(regenerated / name)
    )


def _laptop_preflight(laptop_plan: Path, planning_source: Path) -> dict[str, object]:
    plan = load_laptop_planning_smoke(laptop_plan)
    models = {
        "transformers": {
            "backend": "transformers",
            "model_id": plan.source_model_id,
            "revision": plan.source_revision,
            "tokenizer_id": plan.tokenizer_id,
            "tokenizer_revision": plan.tokenizer_revision,
            "weight_manifest_sha256": None,
            "status": "unavailable",
            "reason": "operator_has_not_acquired_or_verified_local_weights",
        },
        "llama_cpp_q8_0": {
            "backend": "openai_compatible",
            "model_id": plan.generated_llama_model_id,
            "source_revision": plan.source_revision,
            "tokenizer_id": plan.tokenizer_id,
            "tokenizer_revision": plan.tokenizer_revision,
            "runtime_release": plan.llama_cpp_release,
            "quantization": plan.quantization,
            "endpoint_scope": "loopback_only",
            "binary_sha256": None,
            "gguf_sha256": None,
            "status": "unavailable",
            "reason": "operator_has_not_built_or_verified_llama_cpp_and_gguf",
        },
    }
    payload = {
        "schema_version": "1",
        "id": plan.id,
        "classification": "evaluation_ready",
        "complete": False,
        "models": models,
        "prompt": {
            "template_version": plan.prompt_template_version,
            "source": "conflux.experiments.planning_runner._planning_request",
            "source_sha256": _file_sha256(planning_source),
        },
        "seeds": [plan.seed],
        "repetitions": plan.repetitions,
        "bounds": dict(plan.bounds),
        "matrix": [{"cell_id": cell.id, "status": "unavailable"} for cell in plan.matrix()],
        "expected_resources": {
            "transformers": ["local_model_cache", "laptop_cpu_or_gpu"],
            "llama_cpp_q8_0": ["pinned_local_binary", "local_gguf", "loopback_endpoint"],
        },
        "operator_gates": list(plan.operator_gates),
        "exclusions": [
            "models and runtimes were not acquired or invoked",
            "unavailable cells are not efficacy evidence",
        ],
    }
    _validate("direction-readiness-result.schema.json", payload)
    return payload


def _planning_preflight(planning_source: Path) -> dict[str, object]:
    scenarios = load_default_planning_diagnostic_suite()
    cells = [f"{scenario.id}:{mode.value}:r0:s0" for scenario in scenarios for mode in PlanningMode]
    payload = {
        "schema_version": "1",
        "id": "planning-diagnostic-v1",
        "classification": "evaluation_ready",
        "complete": False,
        "model": {
            "status": "unavailable",
            "identity": None,
            "reason": "operator_must_supply_one_immutable_self_hosted_model_spec",
        },
        "prompt": {
            "template_version": "planning-diagnostic-v1",
            "source": "conflux.experiments.planning_runner._planning_request",
            "source_sha256": _file_sha256(planning_source),
        },
        "seeds": [0],
        "repetitions": 1,
        "bounds": {"max_model_calls": 12, "max_plan_nodes": 64},
        "matrix": [{"cell_id": cell, "status": "unavailable"} for cell in cells],
        "expected_resources": ["self_hosted_model", "local_or_private_model_runtime"],
        "exclusions": [
            "no model identity was selected",
            "no modeled planning cell was executed",
        ],
    }
    _validate("direction-readiness-result.schema.json", payload)
    return payload


def _agentdojo_preflight() -> dict[str, object]:
    cells = tuple(AgentDojoCell(attacked, defence, 0, 0) for attacked in (False, True) for defence in ("no_defence", "ites"))
    payload = {
        "schema_version": "1",
        "id": "agentdojo-v0.1.35-smoke",
        "classification": "evaluation_ready",
        "complete": False,
        "suite": {
            "release": "0.1.35",
            "commit": "a75aba7631d3ca5fb7ab938965c97ead2f9ff84b",
            "suite_version": "v1.2.2",
        },
        "model": {
            "status": "unavailable",
            "identity": None,
            "reason": "operator_must_supply_one_immutable_self_hosted_model_spec",
        },
        "prompt": {
            "owner": "pinned_agentdojo_suite",
            "identity": "resolved_and_hashed_by_live_runner",
        },
        "seeds": [0],
        "repetitions": 1,
        "bounds": {"max_model_calls": 8},
        "matrix": [{**cell.to_dict(), "status": "unavailable"} for cell in cells],
        "expected_resources": ["agentdojo_0.1.35", "self_hosted_model"],
        "exclusions": [
            "AgentDojo was not installed or invoked",
            "no model identity was selected",
        ],
    }
    _validate("direction-readiness-result.schema.json", payload)
    return payload


def _security_mutations() -> dict[str, object]:
    bounds = VerificationBounds(1, 4, 4, 1)
    disclosure_canonical = ExplicitStateChecker().verify(DisclosureVerificationSystem(), DISCLOSURE_PROPERTIES, bounds)
    delegation_canonical = ExplicitStateChecker().verify(DelegationVerificationSystem(), DELEGATION_PROPERTIES, bounds)
    disclosure = [
        _mutation_result(
            mutation.value,
            ExplicitStateChecker().verify(DisclosureVerificationSystem(mutation), DISCLOSURE_PROPERTIES, bounds),
        )
        for mutation in DisclosureMutation
        if mutation is not DisclosureMutation.CANONICAL
    ]
    delegation = [
        _mutation_result(
            mutation.value,
            ExplicitStateChecker().verify(DelegationVerificationSystem(mutation), DELEGATION_PROPERTIES, bounds),
        )
        for mutation in DelegationMutation
        if mutation is not DelegationMutation.CANONICAL
    ]
    payload = {
        "schema_version": "1",
        "classification": "bounded_evidence",
        "complete": True,
        "runtime_delegation_enabled": False,
        "bounds": {
            "max_depth": 1,
            "max_states": 4,
            "max_transitions": 4,
            "max_model_calls": 1,
        },
        "canonical": {
            "disclosure": disclosure_canonical.to_dict(),
            "delegation": delegation_canonical.to_dict(),
        },
        "mutants": {"disclosure": disclosure, "delegation": delegation},
    }
    _validate("security-mutation-result.schema.json", payload)
    return payload


def _mutation_result(mutation: str, result: Any) -> dict[str, object]:
    verification = result.to_dict()
    counterexample = verification["counterexample"]
    return {
        "mutation": mutation,
        "killed": verification["verdict"] == "unsafe" and counterexample is not None and counterexample["length"] == 1,
        "verification": verification,
    }


def _table(
    laptop: dict[str, object],
    planning: dict[str, object],
    agentdojo: dict[str, object],
    mutations: dict[str, object],
) -> str:
    mutant_groups = cast(dict[str, list[dict[str, object]]], mutations["mutants"])
    killed = sum(item["killed"] is True for group in mutant_groups.values() for item in group)
    total = sum(len(group) for group in mutant_groups.values())
    return "\n".join(
        (
            "# Fourth-year direction evidence v1",
            "",
            "| Track | Classification | Cells | Execution |",
            "|---|---|---:|---|",
            f"| Laptop planning | evaluation_ready | {len(cast(list[object], laptop['matrix']))} | unavailable |",
            f"| Full planning | evaluation_ready | {len(cast(list[object], planning['matrix']))} | unavailable |",
            f"| AgentDojo | evaluation_ready | {len(cast(list[object], agentdojo['matrix']))} | unavailable |",
            f"| Security mutants | bounded_evidence | {total} ({killed} killed) | native SLED |",
            "",
            "Unavailable cells were not executed and are not empirical efficacy results.",
            "",
        ),
    )


def _validate(schema: str, payload: object) -> None:
    Draft202012Validator(load_schema(schema)).validate(payload)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")


def _write_checksums(output: Path) -> None:
    paths = sorted(path for path in output.iterdir() if path.is_file() and path.name != "CHECKSUMS.sha256")
    (output / "CHECKSUMS.sha256").write_text(
        "".join(f"{_file_sha256(path)}  {path.name}\n" for path in paths),
        encoding="utf-8",
        newline="\n",
    )


def _file_sha256(path: Path) -> str:
    content = path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _canonical_bytes(path: Path) -> bytes:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")


__all__ = [
    "DIRECTION_EVIDENCE_FILES",
    "compare_direction_evidence_bundle",
    "generate_direction_evidence_bundle",
]
