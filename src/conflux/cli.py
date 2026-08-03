"""Argparse console entry point for supported Conflux workflows."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator, ValidationError

from conflux.adapters.benchmarks.agentdojo_local import PinnedAgentDojoCellExecutor
from conflux.adapters.benchmarks.agentdojo_v1 import (
    load_pinned_suite,
    parse_upstream_log,
    write_translation,
)
from conflux.adapters.models import (
    OpenAICompatibleModel,
    ResolvedLocalModel,
    ScriptedModel,
    SelfHostedOpenAIModel,
    TransformersLocalModel,
    load_resolved_local_model,
    resolve_transformers_snapshot,
    write_resolved_local_model,
)
from conflux.adapters.policy import CedarPolicyBundle
from conflux.adapters.providers import InMemoryExecutor
from conflux.adapters.scenarios import load_scenario, load_schema
from conflux.application import CapabilityReport, ChatRuntime, MediationService
from conflux.application.planning_demo import run_dynamic_planning_demo
from conflux.domain import canonical_json, fingerprint
from conflux.evaluation import (
    DELEGATION_PROPERTIES,
    DelegationMutation,
    DelegationVerificationSystem,
    ExplicitStateChecker,
    ITESVerificationSystem,
    NoForbiddenObservation,
    NoUnauthorisedAuthorisation,
    PrincipalContextMonotonicity,
    ProvenancePreserved,
    RunResult,
    UtilityOutcome,
    VerificationBounds,
    write_plan_result,
    write_plan_trace,
    write_result,
    write_trace,
)
from conflux.experiments import (
    BACKEND_LLAMA_CPP,
    BACKEND_TRANSFORMERS,
    ExperimentProtocol,
    ResolvedRunManifest,
    RunFailure,
    agentdojo_matrix,
    cedar_differential_preflight,
    load_cedar_bundle,
    load_cedar_corpus,
    load_default_planning_diagnostic_suite,
    load_laptop_planning_smoke,
    load_manifest,
    load_protocol,
    planning_matrix,
    run_agentdojo_comparison,
    run_laptop_planning_smoke,
    run_native_reproduction,
    run_planning_comparison,
    validate_laptop_protocols,
)
from conflux.ites import BranchState, MediatingITES, TransitionKernel
from conflux.ports import LocalModelPreflight, LocalModelSpec
from conflux.verification import (
    FormalVerdict,
    NuXmvBackend,
    VerificationIR,
    compare_cone_of_influence,
    verify_with_z3,
)

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_RUNTIME = 3
EXIT_INVALID_EVIDENCE = 4


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="conflux")
    commands = parser.add_subparsers(dest="command", required=True)

    model = commands.add_parser("model", help="resolve operator-owned local model artifacts")
    model_commands = model.add_subparsers(dest="model_command", required=True)
    model_resolve = model_commands.add_parser("resolve")
    resolve_commands = model_resolve.add_subparsers(dest="resolve_command", required=True)
    resolve_transformers = resolve_commands.add_parser("transformers")
    resolve_transformers.add_argument("--model-id", required=True)
    resolve_transformers.add_argument("--revision", required=True)
    resolve_transformers.add_argument("--snapshot", type=Path, required=True)
    resolve_transformers.add_argument("--tokenizer-id")
    resolve_transformers.add_argument("--tokenizer-revision")
    resolve_transformers.add_argument("--prompt-template", default="planning-diagnostic-v1")
    resolve_transformers.add_argument("--runtime-version", required=True)
    resolve_transformers.add_argument("--output", type=Path, required=True)

    demo = commands.add_parser("demo", help="run a deterministic scripted scenario")
    demo.add_argument("--scenario", type=Path, default=Path("examples/basic.yaml"))
    demo.add_argument("--model", choices=("scripted",), default="scripted")
    demo.add_argument("--output", type=Path)
    demo.add_argument("--select-branch")
    demo.add_argument("--max-model-calls", type=int, default=3)
    demo.add_argument("--manifest", type=Path)

    chat = commands.add_parser("chat", help="interactive model loop (M4)")
    chat.add_argument("--scenario", type=Path, required=True)
    chat.add_argument("--endpoint", required=True)
    chat.add_argument("--model", required=True)
    chat.add_argument("--api-key-env", default="OPENAI_API_KEY")
    chat.add_argument("--principal")

    plan = commands.add_parser("plan", help="open-ended dynamic planning")
    plan_commands = plan.add_subparsers(dest="plan_command", required=True)
    plan_demo = plan_commands.add_parser("demo", help="run the scripted recovery plan")
    plan_demo.add_argument("--output", type=Path, default=Path("runs/plan-demo"))
    plan_compare = plan_commands.add_parser("compare", help="preflight or run the four-mode modeled comparison")
    plan_compare.add_argument("--config", type=Path, required=True)
    plan_compare.add_argument("--output", type=Path)
    plan_compare.add_argument("--execute-local", action="store_true")
    plan_pilot = plan_commands.add_parser(
        "pilot",
        help="preflight or run the eight-cell single-backend CPU pilot",
    )
    plan_pilot.add_argument("--model-config", type=Path, required=True)
    plan_pilot.add_argument("--source-commit")
    plan_pilot.add_argument("--output", type=Path, required=True)
    plan_pilot.add_argument("--execute-local", action="store_true")
    laptop_smoke = plan_commands.add_parser(
        "laptop-smoke",
        help="preflight or run the fixed dual-backend laptop matrix",
    )
    laptop_smoke.add_argument("--plan", type=Path, required=True)
    laptop_smoke.add_argument("--transformers-config", type=Path, required=True)
    laptop_smoke.add_argument("--llama-config", type=Path, required=True)
    laptop_smoke.add_argument("--output", type=Path)
    laptop_smoke.add_argument("--execute-local", action="store_true")

    sled = commands.add_parser("sled", help="native bounded verification")
    sled_commands = sled.add_subparsers(dest="sled_command", required=True)
    sled_run = sled_commands.add_parser("run")
    sled_run.add_argument("--suite", type=Path, required=True)
    sled_run.add_argument("--output", type=Path, required=True)
    sled_run.add_argument("--max-depth", type=int, default=8)
    sled_run.add_argument("--max-states", type=int, default=10_000)
    sled_run.add_argument("--max-transitions", type=int, default=50_000)
    sled_run.add_argument("--max-model-calls", type=int, default=8)
    sled_reproduce = sled_commands.add_parser("reproduce", help="run paired legacy/canonical native SLED")
    sled_reproduce.add_argument("--protocol", type=Path, required=True)
    sled_reproduce.add_argument("--output", type=Path)
    sled_delegation = sled_commands.add_parser(
        "delegation", help="verify the disabled scoped-delegation model"
    )
    sled_delegation.add_argument("--output", type=Path, required=True)

    verify = commands.add_parser("verify", help="solver-facing verification (M7)")
    verify.add_argument("--model", type=Path)
    verify.add_argument("--property")
    verify.add_argument("--backend", choices=("z3", "nuxmv"), default="z3")
    verify.add_argument("--reduce", choices=("cone_of_influence",))
    verify.add_argument("--output", type=Path)

    benchmark = commands.add_parser("benchmark", help="external benchmarks")
    benchmark_commands = benchmark.add_subparsers(
        dest="benchmark_command",
        required=True,
    )
    agentdojo = benchmark_commands.add_parser("agentdojo")
    agentdojo.add_argument("--config", type=Path, required=True)
    agentdojo.add_argument("--upstream-log", type=Path)
    agentdojo.add_argument("--output", type=Path)
    agentdojo.add_argument("--execute-local", action="store_true")

    policy = commands.add_parser("policy", help="optional policy-adapter tooling")
    policy_commands = policy.add_subparsers(dest="policy_command", required=True)
    cedar = policy_commands.add_parser("cedar", help="pinned local Cedar adapter")
    cedar_commands = cedar.add_subparsers(dest="cedar_command", required=True)
    cedar_preflight = cedar_commands.add_parser(
        "preflight", help="translate a corpus without invoking Cedar"
    )
    cedar_preflight.add_argument("--bundle", type=Path, required=True)
    cedar_preflight.add_argument("--corpus", type=Path, required=True)
    cedar_preflight.add_argument("--binary", type=Path)
    cedar_preflight.add_argument("--output", type=Path, required=True)

    report = commands.add_parser("report", help="render a result JSON")
    report.add_argument("result", type=Path)
    report.add_argument("--json", action="store_true")

    doctor = commands.add_parser("doctor", help="inspect local capabilities")
    doctor.add_argument("--json", action="store_true")
    doctor.add_argument("--local-model-config", type=Path)
    doctor.add_argument("--cedar-bundle", type=Path)
    doctor.add_argument("--cedar-binary", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        command = str(arguments.command)
        if command == "demo":
            return _demo(arguments)
        if command == "sled":
            return _sled(arguments)
        if command == "report":
            return _report(arguments)
        if command == "doctor":
            return _doctor(arguments)
        if command == "chat":
            return _chat(arguments)
        if command == "plan":
            return _plan(arguments)
        if command == "verify":
            return _verify(arguments)
        if command == "benchmark":
            return _benchmark(arguments)
        if command == "policy":
            return _policy(arguments)
        if command == "model":
            return _model_artifacts(arguments)
        return _unavailable(f"unsupported_command:{command}")
    except ValidationError as error:
        print(f"invalid_evidence:{error.message}", file=sys.stderr)
        return EXIT_INVALID_EVIDENCE
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return EXIT_USAGE
    except (OSError, RuntimeError) as error:
        print(f"runtime_failure:{type(error).__name__}:{error}", file=sys.stderr)
        return EXIT_RUNTIME


def _model_artifacts(arguments: argparse.Namespace) -> int:
    if (
        str(arguments.model_command) != "resolve"
        or str(arguments.resolve_command) != "transformers"
    ):
        return _unavailable("unsupported_model_artifact_command")
    model_id = str(arguments.model_id)
    revision = str(arguments.revision)
    tokenizer_id = str(arguments.tokenizer_id or model_id)
    tokenizer_revision = str(arguments.tokenizer_revision or revision)
    manifest, warnings = resolve_transformers_snapshot(
        cast(Path, arguments.snapshot),
        model_id=model_id,
        revision=revision,
        tokenizer_id=tokenizer_id,
        tokenizer_revision=tokenizer_revision,
    )
    spec = LocalModelSpec(
        backend="transformers",
        model_id=model_id,
        revision=revision,
        weight_manifest_sha256=manifest.fingerprint,
        tokenizer_id=tokenizer_id,
        tokenizer_revision=tokenizer_revision,
        prompt_template_version=str(arguments.prompt_template),
        seed=0,
        temperature=0.0,
        top_p=1.0,
        max_output_tokens=256,
        context_limit=4096,
        device="cpu",
        dtype="float32",
        runtime_version=str(arguments.runtime_version),
    )
    resolved = ResolvedLocalModel(
        spec,
        cast(Path, arguments.snapshot),
        manifest,
        warnings,
    )
    output = cast(Path, arguments.output)
    write_resolved_local_model(resolved, output / "transformers.json")
    (output / "artifact-manifest.json").write_text(
        canonical_json(manifest.to_dict()) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        canonical_json(
            {
                "available": True,
                "configuration": str(output / "transformers.json"),
                "files": len(manifest.files),
                "manifest_sha256": manifest.fingerprint,
                "model_id": model_id,
                "revision": revision,
                "total_size": manifest.total_size,
                "warnings": list(warnings),
            }
        )
    )
    return EXIT_OK


def _demo(arguments: argparse.Namespace) -> int:
    scenario = load_scenario(cast(Path, arguments.scenario))
    manifest = (
        load_manifest(cast(Path, arguments.manifest))
        if arguments.manifest is not None
        else None
    )
    mediator = MediatingITES(TransitionKernel(scenario.pipeline))
    service = MediationService(mediator)
    report = service.evaluate(
        environment=scenario.environment,
        session=scenario.session,
        initial_inputs=scenario.environment.artifacts(),
        model=ScriptedModel((scenario.model,)),
        max_model_calls=int(arguments.max_model_calls),
    )
    authorised = report.authorised_branches
    selected = str(arguments.select_branch) if arguments.select_branch else None
    branch = next((item for item in authorised if item.branch_id == selected), None)
    if selected and branch is None:
        raise ValueError(f"unknown_or_unauthorised_branch:{selected}")
    if branch is None and len(authorised) == 1:
        branch = authorised[0]
    if branch is not None:
        report = service.execute(
            report=report,
            branch=branch,
            executor=InMemoryExecutor(),
            environment=scenario.environment,
            session=scenario.session,
        ).report
        utility = UtilityOutcome(True, "selected_authorised_branch_executed")
    elif authorised:
        utility = UtilityOutcome(False, "branch_selection_required")
    else:
        utility = UtilityOutcome(False, "all_proposals_blocked")
    output = (
        cast(Path | None, arguments.output)
        or (Path(manifest.output_directory) if manifest else None)
        or Path("runs") / report.run_id
    )
    output.mkdir(parents=True, exist_ok=True)
    if manifest is not None:
        manifest.materialise(output)
    trace_path = output / "trace.jsonl"
    trace_hash = write_trace(report, trace_path)
    result = RunResult.from_report(
        report,
        source={"scenario_id": scenario.id, "scenario_path": str(arguments.scenario)},
        manifest=(
            manifest.to_dict()
            if manifest
            else {"scenario": scenario.id, "model": "scripted"}
        ),
        utility=utility,
        trace_path="trace.jsonl",
        trace_sha256=trace_hash,
    )
    result_path = output / "result.json"
    write_result(result, result_path)
    (output / "report.md").write_text(_render_result(result.to_dict()), encoding="utf-8")
    print(canonical_json({"run_id": report.run_id, "output": str(output)}))
    return EXIT_OK


def _sled(arguments: argparse.Namespace) -> int:
    if str(arguments.sled_command) == "reproduce":
        protocol = load_protocol(cast(Path, arguments.protocol))
        reproduction = run_native_reproduction(protocol)
        output = cast(Path | None, arguments.output) or Path(protocol.output_directory)
        output.mkdir(parents=True, exist_ok=True)
        protocol.materialise(output)
        path = output / "result.json"
        path.write_text(canonical_json(reproduction) + "\n", encoding="utf-8", newline="\n")
        print(canonical_json({"complete": reproduction["complete"], "output": str(path)}))
        return EXIT_OK if reproduction["complete"] else EXIT_RUNTIME
    if str(arguments.sled_command) == "delegation":
        return _sled_delegation(cast(Path, arguments.output))
    if str(arguments.sled_command) != "run":
        return _unavailable(f"unsupported_sled_command:{arguments.sled_command}")
    scenario = load_scenario(cast(Path, arguments.suite))
    system = ITESVerificationSystem(
        (BranchState.initial(scenario.environment.artifacts()),),
        scenario.model.proposals,
        TransitionKernel(scenario.pipeline),
        scenario.session,
        scenario.environment,
    )
    bounds = VerificationBounds(
        int(arguments.max_depth),
        int(arguments.max_states),
        int(arguments.max_transitions),
        int(arguments.max_model_calls),
    )
    verification = ExplicitStateChecker().verify(
        system,
        (
            NoUnauthorisedAuthorisation(),
            NoForbiddenObservation(),
            PrincipalContextMonotonicity(),
            ProvenancePreserved(),
        ),
        bounds,
    )
    output = cast(Path, arguments.output)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "verification.json"
    path.write_text(canonical_json(verification.to_dict()) + "\n", encoding="utf-8")
    print(canonical_json({"verdict": verification.verdict.value, "output": str(path)}))
    return EXIT_RUNTIME if verification.verdict.value == "unknown" else EXIT_OK


def _report(arguments: argparse.Namespace) -> int:
    payload = cast(
        dict[str, Any],
        json.loads(cast(Path, arguments.result).read_text(encoding="utf-8")),
    )
    schema = _result_schema(payload)
    Draft202012Validator(load_schema(schema)).validate(payload)
    print(canonical_json(payload) if arguments.json else _render_any_result(payload))
    return EXIT_OK


def _verify(arguments: argparse.Namespace) -> int:
    model_path = cast(Path | None, arguments.model)
    if model_path is None:
        raise ValueError("verification_model_required")
    payload = json.loads(model_path.read_text(encoding="utf-8"))
    ir = VerificationIR.from_dict(payload)
    property_id = str(arguments.property) if arguments.property else None
    invariant_ids = tuple(item.id for item in ir.invariants)
    if property_id is not None:
        selected = tuple(item for item in ir.invariants if item.id == property_id)
        if not selected:
            raise ValueError(f"unknown_verification_property:{property_id}")
        invariant_ids = (property_id,)
    selected_ir = replace(
        ir,
        invariants=tuple(item for item in ir.invariants if item.id in invariant_ids),
    )
    backend = (
        verify_with_z3
        if str(arguments.backend) == "z3"
        else NuXmvBackend().verify
    )
    reduction_name = cast(str | None, arguments.reduce)
    if reduction_name == "cone_of_influence":
        comparison = compare_cone_of_influence(ir, invariant_ids)
        original_result = backend(selected_ir)
        result = backend(comparison.reduction.reduced_ir)
        backend_failure = None
        if FormalVerdict.UNKNOWN in {original_result.verdict, result.verdict}:
            backend_failure = "backend_unavailable_or_failed"
        elif original_result.verdict != result.verdict:
            backend_failure = "backend_verdict_disagreement"
        report: dict[str, object] = {
            "schema_version": "1",
            "comparison": comparison.to_dict(),
            "backend": {
                "original": original_result.to_dict(),
                "reduced": result.to_dict(),
                "equivalent": backend_failure is None,
                "failure": backend_failure,
            },
        }
    else:
        result = backend(selected_ir)
        original_result = None
        comparison = None
        backend_failure = None
        report = result.to_dict()
    output = cast(Path | None, arguments.output)
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
        (output / "formal-verification.json").write_text(
            canonical_json(result.to_dict()) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        if original_result is not None and comparison is not None:
            (output / "formal-verification-original.json").write_text(
                canonical_json(original_result.to_dict()) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            (output / "verification-reduction.json").write_text(
                canonical_json(report) + "\n",
                encoding="utf-8",
                newline="\n",
            )
    print(canonical_json(report))
    failed = (
        result.verdict == FormalVerdict.UNKNOWN
        or backend_failure is not None
        or (comparison is not None and not comparison.equivalent)
    )
    return EXIT_RUNTIME if failed else EXIT_OK


def _render_result(payload: dict[str, Any]) -> str:
    diagnostics = cast(dict[str, object], payload["diagnostics"])
    utility = cast(dict[str, object], payload["utility"])
    return "\n".join(
        (
            f"# Conflux run {payload['run_id']}",
            "",
            f"- Status: {payload['status']}",
            f"- Proposed: {diagnostics.get('proposed', 0)}",
            f"- Authorised: {diagnostics.get('authorised', 0)}",
            f"- Blocked: {diagnostics.get('blocked', 0)}",
            f"- Executed: {diagnostics.get('executed', 0)}",
            f"- Provider failed: {diagnostics.get('provider_failed', 0)}",
            f"- Utility completed: {utility.get('completed', False)}",
            "",
        )
    )


def _doctor(arguments: argparse.Namespace) -> int:
    report = CapabilityReport.discover()
    local_config = cast(Path | None, arguments.local_model_config)
    local = None
    if local_config is not None:
        protocol = load_protocol(local_config)
        if protocol.model is None:
            raise ValueError("local_model_config_requires_model")
        local = _local_model(protocol).preflight()
    payload = report.to_dict()
    if local is not None:
        payload["local_model"] = {
            "backend": local.backend,
            "model_id": local.model_id,
            "available": local.available,
            "network_scope": local.network_scope,
            "reason": local.reason,
        }
    cedar_bundle_path = cast(Path | None, arguments.cedar_bundle)
    cedar_binary_path = cast(Path | None, arguments.cedar_binary)
    if cedar_bundle_path is not None:
        payload["cedar"] = _cedar_identity_preflight(
            load_cedar_bundle(cedar_bundle_path), cedar_binary_path
        )
    if arguments.json:
        print(canonical_json(payload))
    else:
        print(f"Conflux doctor: Python {report.python} on {report.os}")
        print(f"CPU count: {report.cpu_count or 'unknown'}")
        print(f"Container: {report.container or 'unavailable'}")
        print(f"GPU probe: {report.gpu_probe or 'unavailable'}")
        print(f"Schedulers: {', '.join(report.schedulers) or 'unavailable'}")
        if local is not None:
            print(
                f"Local model: {local.model_id} ({local.backend}, {local.network_scope}) - "
                f"{'available' if local.available else local.reason}"
            )
        if "cedar" in payload:
            cedar = cast(dict[str, object], payload["cedar"])
            print(
                f"Cedar: {cedar['expected_version']} - "
                f"{'available' if cedar['available'] else cedar['reason']}"
            )
    return EXIT_OK


def _chat(arguments: argparse.Namespace) -> int:
    scenario = load_scenario(cast(Path, arguments.scenario))
    principal_id = (
        str(arguments.principal)
        if arguments.principal
        else min(scenario.session.participants).id
    )
    human = next(
        (
            principal
            for principal in scenario.session.participants
            if principal.id == principal_id
        ),
        None,
    )
    if human is None:
        raise ValueError(f"unknown_chat_principal:{principal_id}")
    model = OpenAICompatibleModel(
        str(arguments.endpoint),
        str(arguments.model),
        frozenset(resource.key for resource in scenario.environment.resources),
        api_key_env=str(arguments.api_key_env),
    )
    if not model.available():
        return _unavailable(
            f"chat_backend_unavailable:secret_or_httpx:{model.api_key_env}"
        )
    runtime = ChatRuntime(
        scenario.environment,
        scenario.session,
        human,
        MediatingITES(TransitionKernel(scenario.pipeline)),
        model,
        InMemoryExecutor(),
    )
    print("Conflux mediated chat. Type 'exit' to stop.")
    try:
        while True:
            text = input("conflux> ").strip()
            if text.lower() in {"exit", "quit"}:
                return EXIT_OK
            turn = runtime.submit(text)
            print(
                canonical_json(
                    {
                        "run_id": turn.report.run_id,
                        "executed": turn.executed,
                        "reason": turn.reason,
                        "blocked": turn.report.blocked_count,
                    }
                )
            )
    except (EOFError, KeyboardInterrupt):
        print("\nchat_aborted_safely")
        return EXIT_OK


def _plan(arguments: argparse.Namespace) -> int:
    if str(arguments.plan_command) == "pilot":
        return _cpu_pilot(arguments)
    if str(arguments.plan_command) == "laptop-smoke":
        return _laptop_smoke(arguments)
    if str(arguments.plan_command) == "compare":
        protocol = load_protocol(cast(Path, arguments.config))
        scenarios = load_default_planning_diagnostic_suite()
        model = _local_model(protocol)
        matrix = planning_matrix(protocol, scenarios)
        if not bool(arguments.execute_local):
            payload = {
                "schema_version": "1",
                "classification": "evaluation_ready",
                "complete": False,
                "execute_local": False,
                "preflight": _preflight_dict(model.preflight()),
                "bounds": dict(protocol.bounds),
                "matrix": [cell.id for cell in matrix],
                "exclusions": ["local model was not invoked"],
            }
            _emit_preflight(payload, cast(Path | None, arguments.output))
            return EXIT_OK
        comparison = run_planning_comparison(protocol, model, scenarios)
        output = cast(Path | None, arguments.output) or Path(protocol.output_directory)
        _write_protocol_result(protocol, comparison, output)
        print(canonical_json({"complete": comparison["complete"], "output": str(output / "result.json")}))
        return EXIT_OK if comparison["complete"] else EXIT_RUNTIME
    if str(arguments.plan_command) != "demo":
        return _unavailable(f"unsupported_plan_command:{arguments.plan_command}")
    plan_result = run_dynamic_planning_demo()
    output = cast(Path, arguments.output)
    output.mkdir(parents=True, exist_ok=True)
    trace_hash = write_plan_trace(plan_result.state, output / "trace.jsonl")
    write_plan_result(plan_result, output / "result.json")
    print(
        canonical_json(
            {
                "run_id": plan_result.state.run_id,
                "status": plan_result.state.status.value,
                "completed": plan_result.completed,
                "blocked": sum(
                    report.blocked_count for report in plan_result.mediation_reports
                ),
                "executed": sum(
                    report.executed_count for report in plan_result.mediation_reports
                ),
                "trace_sha256": trace_hash,
                "output": str(output),
            }
        )
    )
    return EXIT_OK if plan_result.completed else EXIT_RUNTIME


def _cpu_pilot(arguments: argparse.Namespace) -> int:
    configuration = cast(Path, arguments.model_config)
    resolved = load_resolved_local_model(configuration)
    output = cast(Path, arguments.output)
    source_commit = str(arguments.source_commit or _git_head())
    suite_path = Path("experiments/suites/planning-diagnostic-v1.yaml")
    protocol = ExperimentProtocol(
        id="planning-cpu-pilot-v1",
        track="planning",
        suite={
            "id": "planning-diagnostic-v1",
            "version": "1",
            "case_ids": ["direct-authorised-effect", "blocked-action-recovery"],
        },
        source_commit=source_commit,
        inputs={
            "experiments/suites/planning-diagnostic-v1.yaml": _text_sha256(
                suite_path
            ),
            "local-artifact-manifest": resolved.manifest.fingerprint,
        },
        model=resolved.spec,
        prompts={"planner": "planning-diagnostic-v1"},
        seeds=(0,),
        repetitions=1,
        bounds={"max_model_calls": 4, "max_steps": 3},
        environment={
            "execution": "modeled_actions_only",
            "device": "cpu",
            "runtime": resolved.spec.runtime_version,
        },
        output_directory=str(output),
        rerun_command=(
            "conflux",
            "plan",
            "pilot",
            "--model-config",
            str(configuration),
            "--output",
            str(output),
            "--execute-local",
        ),
    )
    model = TransformersLocalModel(
        resolved.spec,
        snapshot_path=resolved.snapshot_path,
        artifact_manifest=resolved.manifest,
    )
    scenarios = load_default_planning_diagnostic_suite()
    matrix = planning_matrix(protocol, scenarios)
    preflight = model.preflight()
    payload = {
        "schema_version": "1",
        "classification": "evaluation_ready",
        "complete": False,
        "execute_local": bool(arguments.execute_local),
        "preflight": _preflight_dict(preflight),
        "bounds": dict(protocol.bounds),
        "matrix": [cell.id for cell in matrix],
        "model": resolved.spec.to_dict(),
        "resources": {
            "logical_cpus": os.cpu_count(),
            "placement": "cpu",
            "expected_available_memory": "at_least_6_gib",
        },
        "output": str(output),
    }
    if not bool(arguments.execute_local):
        _emit_preflight(payload, output)
        return EXIT_OK
    if not preflight.available:
        return _unavailable(preflight.reason or "local_model_unavailable")
    result = run_planning_comparison(protocol, model, scenarios)
    _write_cpu_pilot_bundle(protocol, result, model.records, output)
    print(
        canonical_json(
            {
                "complete": result["complete"],
                "human_review_required": True,
                "output": str(output / "result.json"),
            }
        )
    )
    return EXIT_OK if result["complete"] else EXIT_RUNTIME


def _laptop_smoke(arguments: argparse.Namespace) -> int:
    plan = load_laptop_planning_smoke(cast(Path, arguments.plan))
    protocols = {
        BACKEND_TRANSFORMERS: load_protocol(
            cast(Path, arguments.transformers_config)
        ),
        BACKEND_LLAMA_CPP: load_protocol(cast(Path, arguments.llama_config)),
    }
    validate_laptop_protocols(plan, protocols)
    models = {backend: _local_model(protocol) for backend, protocol in protocols.items()}
    preflights = {
        backend: _preflight_dict(model.preflight())
        for backend, model in models.items()
    }
    matrix = [cell.id for cell in plan.matrix()]
    if not bool(arguments.execute_local):
        payload = {
            "schema_version": "1",
            "classification": "evaluation_ready",
            "complete": False,
            "execute_local": False,
            "plan_fingerprint": plan.fingerprint,
            "operator_gates": list(plan.operator_gates),
            "stop_after_bundle": plan.stop_after_bundle,
            "bounds": dict(plan.bounds),
            "preflight": preflights,
            "matrix": matrix,
            "exclusions": ["local model runtimes were not invoked"],
        }
        _emit_preflight(payload, cast(Path | None, arguments.output))
        return EXIT_OK
    unavailable = [
        backend
        for backend, preflight in preflights.items()
        if preflight["available"] is not True
    ]
    if unavailable:
        return _unavailable(
            "laptop_smoke_runtime_unavailable:" + ",".join(sorted(unavailable))
        )
    result = run_laptop_planning_smoke(plan, protocols, models)
    output = cast(Path | None, arguments.output) or Path("runs/laptop-planning-smoke-v1")
    output.mkdir(parents=True, exist_ok=True)
    for backend, protocol in protocols.items():
        backend_result = {
            "schema_version": "2",
            "protocol_fingerprint": protocol.fingerprint,
            "complete": result["complete"],
            "model_id": protocol.model.model_id if protocol.model is not None else "missing",
            "task_ids": sorted(plan.scenario_ids),
            "observations": [
                {key: value for key, value in observation.items() if key != "backend_id"}
                for observation in cast(list[dict[str, object]], result["observations"])
                if observation["backend_id"] == backend
            ],
        }
        _write_protocol_result(protocol, backend_result, output / backend)
    (output / "result.json").write_text(
        canonical_json(result) + "\n", encoding="utf-8", newline="\n"
    )
    (output / "raw-results.jsonl").write_text(
        "".join(
            canonical_json({"sequence": index, **observation}) + "\n"
            for index, observation in enumerate(
                cast(list[dict[str, object]], result["observations"])
            )
        ),
        encoding="utf-8",
        newline="\n",
    )
    (output / "manifest.json").write_text(
        canonical_json(
            {
                "schema_version": "1",
                "plan_fingerprint": plan.fingerprint,
                "protocol_fingerprints": {
                    backend: protocol.fingerprint
                    for backend, protocol in protocols.items()
                },
                "source_commits": sorted(
                    {protocol.source_commit for protocol in protocols.values()}
                ),
                "complete": result["complete"],
                "stop_for_human_review": True,
            }
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    content = tuple(
        sorted(path for path in output.rglob("*") if path.is_file())
    )
    (output / "CHECKSUMS.sha256").write_text(
        "".join(
            f"{_text_sha256(path)}  "
            f"{path.relative_to(output).as_posix()}\n"
            for path in content
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(
        canonical_json(
            {
                "complete": result["complete"],
                "cells": len(matrix),
                "stop_for_human_review": True,
                "output": str(output / "result.json"),
            }
        )
    )
    return EXIT_OK if result["complete"] else EXIT_RUNTIME


def _benchmark(arguments: argparse.Namespace) -> int:
    if str(arguments.benchmark_command) != "agentdojo":
        return _unavailable(f"unsupported_benchmark:{arguments.benchmark_command}")
    upstream_log = cast(Path | None, arguments.upstream_log)
    output = cast(Path | None, arguments.output)
    if upstream_log is not None:
        load_manifest(cast(Path, arguments.config))
        translation = parse_upstream_log(upstream_log)
        destination = output or Path("runs") / "agentdojo-translation.json"
        write_translation(translation, destination)
        print(
            canonical_json(
                {
                    "suite_id": translation.suite_id,
                    "user_task_id": translation.user_task_id,
                    "injection_task_id": translation.injection_task_id,
                    "native_security": translation.native_security,
                    "native_utility": translation.native_utility,
                    "output": str(destination),
                }
            )
        )
        return EXIT_OK
    try:
        protocol = load_protocol(cast(Path, arguments.config))
    except ValueError as protocol_error:
        if bool(arguments.execute_local):
            raise protocol_error
        manifest = load_manifest(cast(Path, arguments.config))
        suite_id = manifest.suite.removeprefix("agentdojo-")
        suite = load_pinned_suite(suite_id)
        print(canonical_json(suite.to_dict()))
        return _unavailable(
            "agentdojo_legacy_manifest_has_no_self_hosted_model_protocol:"
            "offline_suite_validation_succeeded"
        )
    model = _local_model(protocol)
    matrix = agentdojo_matrix(protocol)
    if not bool(arguments.execute_local):
        payload = {
            "schema_version": "1",
            "classification": "evaluation_ready",
            "complete": False,
            "execute_local": False,
            "preflight": _preflight_dict(model.preflight()),
            "bounds": dict(protocol.bounds),
            "matrix": [cell.to_dict() for cell in matrix],
            "exclusions": ["AgentDojo and the local model were not invoked"],
        }
        _emit_preflight(payload, output)
        return EXIT_OK
    destination = output or Path(protocol.output_directory)
    comparison = run_agentdojo_comparison(
        protocol,
        model,
        PinnedAgentDojoCellExecutor(destination / "raw-upstream"),
    )
    _write_protocol_result(protocol, comparison, destination)
    print(canonical_json({"complete": comparison["complete"], "output": str(destination / "result.json")}))
    return EXIT_OK if comparison["complete"] else EXIT_RUNTIME


def _local_model(protocol: ExperimentProtocol) -> SelfHostedOpenAIModel | TransformersLocalModel:
    if protocol.model is None:
        raise ValueError("self_hosted_model_protocol_required")
    if protocol.model.backend == "openai_compatible":
        return SelfHostedOpenAIModel(protocol.model)
    if protocol.model.backend == "transformers":
        return TransformersLocalModel(protocol.model)
    raise ValueError(f"unsupported_local_model_backend:{protocol.model.backend}")


def _preflight_dict(preflight: LocalModelPreflight) -> dict[str, object]:
    return {
        "backend": preflight.backend,
        "model_id": preflight.model_id,
        "available": preflight.available,
        "network_scope": preflight.network_scope,
        "reason": preflight.reason,
        "dependency_available": preflight.dependency_available,
        "artifact_available": preflight.artifact_available,
        "identity_verified": preflight.identity_verified,
        "runtime_available": preflight.runtime_available,
        "warnings": list(preflight.warnings),
    }


def _emit_preflight(payload: dict[str, object], output: Path | None) -> None:
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
        path = output / "preflight.json"
        path.write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")
        payload = {**payload, "output": str(path)}
    print(canonical_json(payload))


def _sled_delegation(output: Path) -> int:
    bounds = VerificationBounds(1, 4, 4, 1)
    canonical = ExplicitStateChecker().verify(
        DelegationVerificationSystem(), DELEGATION_PROPERTIES, bounds
    )
    mutants = []
    for mutation in DelegationMutation:
        if mutation is DelegationMutation.CANONICAL:
            continue
        result = ExplicitStateChecker().verify(
            DelegationVerificationSystem(mutation), DELEGATION_PROPERTIES, bounds
        )
        mutants.append(
            {
                "mutation": mutation.value,
                "killed": result.verdict.value == "unsafe"
                and result.counterexample is not None
                and result.counterexample.length == 1,
                "verification": result.to_dict(),
            }
        )
    payload = {
        "schema_version": "1",
        "classification": "bounded_evidence",
        "complete": True,
        "runtime_enabled": False,
        "canonical": canonical.to_dict(),
        "mutants": mutants,
    }
    output.mkdir(parents=True, exist_ok=True)
    path = output / "delegation-verification.json"
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")
    print(canonical_json({"complete": True, "output": str(path)}))
    return EXIT_OK


def _policy(arguments: argparse.Namespace) -> int:
    if (
        str(arguments.policy_command) != "cedar"
        or str(arguments.cedar_command) != "preflight"
    ):
        return _unavailable("unsupported_policy_command")
    bundle = load_cedar_bundle(cast(Path, arguments.bundle))
    corpus = load_cedar_corpus(cast(Path, arguments.corpus))
    result = cedar_differential_preflight(bundle, corpus)
    identity = _cedar_identity_preflight(bundle, cast(Path | None, arguments.binary))
    payload = {**result, "binary_preflight": identity}
    output = cast(Path, arguments.output)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "preflight.json"
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")
    print(canonical_json({"classification": "evaluation_ready", "output": str(path)}))
    return EXIT_OK


def _cedar_identity_preflight(
    bundle: CedarPolicyBundle, binary: Path | None
) -> dict[str, object]:
    expected = bundle.binary
    available = binary is not None and binary.is_file()
    actual_sha256 = None
    matches = False
    if available and binary is not None:
        actual_sha256 = hashlib.sha256(binary.read_bytes()).hexdigest()
        matches = actual_sha256 == expected.sha256
    reason = (
        "binary_not_supplied"
        if binary is None
        else "binary_not_found"
        if not available
        else "identity_match"
        if matches
        else "binary_checksum_mismatch"
    )
    return {
        "available": available and matches,
        "reason": reason,
        "binary_path": str(binary) if binary is not None else None,
        "expected_version": expected.version,
        "expected_commit": expected.commit,
        "expected_sha256": expected.sha256,
        "actual_sha256": actual_sha256,
        "supported_features": sorted(bundle.supported_features),
        "invoked": False,
    }


def _text_sha256(path: Path) -> str:
    content = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head() -> str:
    result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        check=False,
        capture_output=True,
        text=True,
        shell=False,
    )
    commit = result.stdout.strip()
    if result.returncode or not 7 <= len(commit) <= 40:
        raise ValueError("source_commit_required_outside_git_checkout")
    return commit


def _write_cpu_pilot_bundle(
    protocol: ExperimentProtocol,
    result: dict[str, object],
    records: list[dict[str, object]],
    output: Path,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    protocol.materialise(output)
    (output / "result.json").write_text(
        canonical_json(result) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output / "raw-model.jsonl").write_text(
        "".join(canonical_json(record) + "\n" for record in records),
        encoding="utf-8",
        newline="\n",
    )
    observations = cast(list[dict[str, object]], result["observations"])
    statuses: dict[str, int] = {}
    for observation in observations:
        status = cast(str, observation["status"])
        statuses[status] = statuses.get(status, 0) + 1
    table = [
        "# CPU planning pilot v1",
        "",
        "| Measure | Value |",
        "|---|---:|",
        f"| Cells | {len(observations)} |",
        f"| Model calls | {sum(cast(int, item['model_calls']) for item in observations)} |",
        f"| Prompt tokens | {sum(cast(int, item['prompt_tokens'] or 0) for item in observations)} |",
        f"| Output tokens | {sum(cast(int, item['output_tokens'] or 0) for item in observations)} |",
        f"| Latency (ms) | {sum(cast(int, item['latency_ms']) for item in observations)} |",
        "",
        "## Cell outcomes",
        "",
        *(
            f"- `{name}`: {count}"
            for name, count in sorted(statuses.items())
        ),
        "",
        "All effects were modeled in memory. Human review is required before claim promotion.",
        "",
    ]
    (output / "table.md").write_text(
        "\n".join(table),
        encoding="utf-8",
        newline="\n",
    )
    content_names = ("protocol.json", "RERUN.txt", "result.json", "raw-model.jsonl", "table.md")
    checksums = {name: _file_sha256(output / name) for name in content_names}
    failures = tuple(
        RunFailure(
            _planning_failure_category(cast(str, item["status"])),
            cast(str, item["status"]),
            cast(str, item["case_id"]),
        )
        for item in observations
        if cast(str, item["status"]) not in {"complete", "securely_impossible"}
    )
    complete = bool(result["complete"])
    manifest = ResolvedRunManifest(
        run_id=fingerprint(
            {"protocol": protocol.fingerprint, "result": checksums["result.json"]}
        ),
        track="planning",
        protocol_fingerprint=protocol.fingerprint,
        source_commit=protocol.source_commit,
        status="complete" if complete else "incomplete",
        complete=complete,
        exclusions=(
            "human review required before claim promotion",
            "llama.cpp and GPU runtimes were not invoked",
        ),
        failures=failures,
        environment={
            "device": "cpu",
            "execution": "modeled_actions_only",
            "model_id": cast(str, result["model_id"]),
        },
        checksums=checksums,
    )
    (output / "manifest.json").write_text(
        canonical_json(manifest.to_dict()) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    checksum_lines = {
        **checksums,
        "manifest.json": _file_sha256(output / "manifest.json"),
    }
    (output / "CHECKSUMS.sha256").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(checksum_lines.items())),
        encoding="utf-8",
        newline="\n",
    )


def _planning_failure_category(status: str) -> str:
    return {
        "parser_failed": "parser",
        "modeled_program_failed": "parser",
        "model_failed": "model",
        "provider_failed": "tool",
        "bound_reached": "bound",
        "blocked": "policy",
    }.get(status, "unknown")


def _write_protocol_result(
    protocol: ExperimentProtocol,
    result: dict[str, object],
    output: Path,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    protocol.materialise(output)
    (output / "result.json").write_text(canonical_json(result) + "\n", encoding="utf-8", newline="\n")


def _result_schema(payload: dict[str, Any]) -> str:
    if "model_identities" in payload and "observations" in payload:
        return "planning-laptop-smoke-result.schema.json"
    if payload.get("schema_version") != "2":
        return "result.schema.json"
    if "pairs" in payload:
        return "native-sled-result-v2.schema.json"
    if "cells" in payload:
        return "agentdojo-comparison-result-v2.schema.json"
    if "observations" in payload:
        return "planning-comparison-result-v2.schema.json"
    raise ValueError("unknown_version_two_result_kind")


def _render_any_result(payload: dict[str, Any]) -> str:
    if payload.get("schema_version") != "2":
        return _render_result(payload)
    kind = "native SLED" if "pairs" in payload else "AgentDojo" if "cells" in payload else "planning"
    count = len(cast(list[object], payload.get("pairs") or payload.get("cells") or payload.get("observations") or []))
    return "\n".join(
        (
            f"# Conflux {kind} result",
            "",
            f"- Complete: {payload.get('complete', False)}",
            f"- Records: {count}",
            f"- Protocol: {payload.get('protocol_fingerprint', 'unknown')}",
            "",
        )
    )


def _unavailable(reason: str) -> int:
    print(reason, file=sys.stderr)
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
