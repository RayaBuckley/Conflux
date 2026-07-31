"""Argparse console entry point for supported Conflux workflows."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator, ValidationError

from conflux.adapters.benchmarks.agentdojo_v1 import (
    load_pinned_suite,
    parse_upstream_log,
    write_translation,
)
from conflux.adapters.models import OpenAICompatibleModel, ScriptedModel
from conflux.adapters.providers import InMemoryExecutor
from conflux.adapters.scenarios import load_scenario, load_schema
from conflux.application import CapabilityReport, ChatRuntime, MediationService
from conflux.application.planning_demo import run_dynamic_planning_demo
from conflux.domain import canonical_json
from conflux.evaluation import (
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
from conflux.experiments import load_manifest
from conflux.ites import BranchState, MediatingITES, TransitionKernel
from conflux.verification import NuXmvBackend, VerificationIR, verify_with_z3

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_RUNTIME = 3
EXIT_INVALID_EVIDENCE = 4


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="conflux")
    commands = parser.add_subparsers(dest="command", required=True)

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

    sled = commands.add_parser("sled", help="native bounded verification")
    sled_commands = sled.add_subparsers(dest="sled_command", required=True)
    sled_run = sled_commands.add_parser("run")
    sled_run.add_argument("--suite", type=Path, required=True)
    sled_run.add_argument("--output", type=Path, required=True)
    sled_run.add_argument("--max-depth", type=int, default=8)
    sled_run.add_argument("--max-states", type=int, default=10_000)
    sled_run.add_argument("--max-transitions", type=int, default=50_000)
    sled_run.add_argument("--max-model-calls", type=int, default=8)

    verify = commands.add_parser("verify", help="solver-facing verification (M7)")
    verify.add_argument("--model", type=Path)
    verify.add_argument("--property")
    verify.add_argument("--backend", choices=("z3", "nuxmv"), default="z3")
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

    report = commands.add_parser("report", help="render a result JSON")
    report.add_argument("result", type=Path)
    report.add_argument("--json", action="store_true")

    doctor = commands.add_parser("doctor", help="inspect local capabilities")
    doctor.add_argument("--json", action="store_true")
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
    result = ExplicitStateChecker().verify(
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
    path.write_text(canonical_json(result.to_dict()) + "\n", encoding="utf-8")
    print(canonical_json({"verdict": result.verdict.value, "output": str(path)}))
    return EXIT_RUNTIME if result.verdict.value == "unknown" else EXIT_OK


def _report(arguments: argparse.Namespace) -> int:
    payload = cast(
        dict[str, Any],
        json.loads(cast(Path, arguments.result).read_text(encoding="utf-8")),
    )
    Draft202012Validator(load_schema("result.schema.json")).validate(payload)
    print(canonical_json(payload) if arguments.json else _render_result(payload))
    return EXIT_OK


def _verify(arguments: argparse.Namespace) -> int:
    model_path = cast(Path | None, arguments.model)
    if model_path is None:
        raise ValueError("verification_model_required")
    payload = json.loads(model_path.read_text(encoding="utf-8"))
    ir = VerificationIR.from_dict(payload)
    property_id = str(arguments.property) if arguments.property else None
    if property_id is not None:
        selected = tuple(item for item in ir.invariants if item.id == property_id)
        if not selected:
            raise ValueError(f"unknown_verification_property:{property_id}")
        ir = replace(ir, invariants=selected)
    result = (
        verify_with_z3(ir)
        if str(arguments.backend) == "z3"
        else NuXmvBackend().verify(ir)
    )
    output = cast(Path | None, arguments.output)
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
        (output / "formal-verification.json").write_text(
            canonical_json(result.to_dict()) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(canonical_json(result.to_dict()))
    return EXIT_RUNTIME if result.verdict.value == "unknown" else EXIT_OK


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
    if arguments.json:
        print(canonical_json(report.to_dict()))
    else:
        print(f"Conflux doctor: Python {report.python} on {report.os}")
        print(f"CPU count: {report.cpu_count or 'unknown'}")
        print(f"Container: {report.container or 'unavailable'}")
        print(f"GPU probe: {report.gpu_probe or 'unavailable'}")
        print(f"Schedulers: {', '.join(report.schedulers) or 'unavailable'}")
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
    if str(arguments.plan_command) != "demo":
        return _unavailable(f"unsupported_plan_command:{arguments.plan_command}")
    result = run_dynamic_planning_demo()
    output = cast(Path, arguments.output)
    output.mkdir(parents=True, exist_ok=True)
    trace_hash = write_plan_trace(result.state, output / "trace.jsonl")
    write_plan_result(result, output / "result.json")
    print(
        canonical_json(
            {
                "run_id": result.state.run_id,
                "status": result.state.status.value,
                "completed": result.completed,
                "blocked": sum(
                    report.blocked_count for report in result.mediation_reports
                ),
                "executed": sum(
                    report.executed_count for report in result.mediation_reports
                ),
                "trace_sha256": trace_hash,
                "output": str(output),
            }
        )
    )
    return EXIT_OK if result.completed else EXIT_RUNTIME


def _benchmark(arguments: argparse.Namespace) -> int:
    if str(arguments.benchmark_command) != "agentdojo":
        return _unavailable(f"unsupported_benchmark:{arguments.benchmark_command}")
    manifest = load_manifest(cast(Path, arguments.config))
    upstream_log = cast(Path | None, arguments.upstream_log)
    output = cast(Path | None, arguments.output)
    if upstream_log is not None:
        result = parse_upstream_log(upstream_log)
        destination = output or Path("runs") / "agentdojo-translation.json"
        write_translation(result, destination)
        print(
            canonical_json(
                {
                    "suite_id": result.suite_id,
                    "user_task_id": result.user_task_id,
                    "injection_task_id": result.injection_task_id,
                    "native_security": result.native_security,
                    "native_utility": result.native_utility,
                    "output": str(destination),
                }
            )
        )
        return EXIT_OK
    suite_id = manifest.suite.removeprefix("agentdojo-")
    suite = load_pinned_suite(suite_id)
    print(canonical_json(suite.to_dict()))
    return _unavailable(
        "agentdojo_live_comparison_requires_explicit_model_runner:"
        "offline_translation_and_suite_validation_succeeded"
    )


def _unavailable(reason: str) -> int:
    print(reason, file=sys.stderr)
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
