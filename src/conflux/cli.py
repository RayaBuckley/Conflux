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
from typing import TYPE_CHECKING, Any, cast

from jsonschema import Draft202012Validator, ValidationError

if TYPE_CHECKING:
    from conflux.ites.state import ITESReport

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
from conflux.planning.executor import DynamicPlanResult
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
    """Build the argparse subcommand tree for the ``conflux`` CLI."""
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
    sled_delegation = sled_commands.add_parser("delegation", help="verify the disabled scoped-delegation model")
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
    agentdojo_commands = agentdojo.add_subparsers(
        dest="agentdojo_command",
        required=True,
    )
    agentdojo_translate = agentdojo_commands.add_parser("translate", help="translate one retained upstream log")
    agentdojo_translate.add_argument("--config", type=Path, required=True)
    agentdojo_translate.add_argument("--upstream-log", type=Path, required=True)
    agentdojo_translate.add_argument("--output", type=Path, required=True)
    agentdojo_preflight = agentdojo_commands.add_parser("preflight", help="validate the package, model, policy, and six-cell matrix")
    agentdojo_preflight_source = agentdojo_preflight.add_mutually_exclusive_group(required=True)
    agentdojo_preflight_source.add_argument("--config", type=Path)
    agentdojo_preflight_source.add_argument("--model-config", type=Path)
    agentdojo_preflight.add_argument("--source-commit")
    agentdojo_preflight.add_argument("--output", type=Path, required=True)
    agentdojo_run = agentdojo_commands.add_parser("run", help="deliberately run the pinned six-cell local comparison")
    agentdojo_run.add_argument("--config", type=Path, required=True)
    agentdojo_run.add_argument("--model-config", type=Path)
    agentdojo_run.add_argument("--output", type=Path, required=True)
    agentdojo_run.add_argument("--execute-local", action="store_true", required=True)

    policy = commands.add_parser("policy", help="optional policy-adapter tooling")
    policy_commands = policy.add_subparsers(dest="policy_command", required=True)
    cedar = policy_commands.add_parser("cedar", help="pinned local Cedar adapter")
    cedar_commands = cedar.add_subparsers(dest="cedar_command", required=True)
    cedar_preflight = cedar_commands.add_parser("preflight", help="translate a corpus without invoking Cedar")
    cedar_preflight.add_argument("--bundle", type=Path, required=True)
    cedar_preflight.add_argument("--corpus", type=Path, required=True)
    cedar_preflight.add_argument("--binary", type=Path)
    cedar_preflight.add_argument("--output", type=Path, required=True)

    report = commands.add_parser("report", help="render a result JSON")
    report.add_argument("result", type=Path)
    report.add_argument("--json", action="store_true")

    visualise = commands.add_parser("visualise", help="render human-reviewable evidence from a result JSON")
    visualise.add_argument("result", type=Path, help="path to result.json")
    visualise.add_argument("--output", type=Path, default=None, help="output directory (default: <result_dir>/evidence)")
    visualise.add_argument("--format", choices=("svg", "html", "all"), default="all")
    visualise.add_argument("--view", choices=("execution", "provenance", "all"), default="all")
    visualise.add_argument("--max-nodes", type=int, default=None)

    doctor = commands.add_parser("doctor", help="inspect local capabilities")
    doctor.add_argument("--json", action="store_true")
    doctor.add_argument("--local-model-config", type=Path)
    doctor.add_argument("--cedar-bundle", type=Path)
    doctor.add_argument("--cedar-binary", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point dispatching to the requested subcommand.

    Returns the appropriate exit code (0, 2, 3, or 4).
    """
    arguments = _parser().parse_args(argv)
    try:
        command = str(arguments.command)
        if command == "demo":
            return _demo(arguments)
        if command == "sled":
            return _sled(arguments)
        if command == "report":
            return _report(arguments)
        if command == "visualise":
            return _visualise(arguments)
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
    """Resolve operator-owned local-transformers model snapshots into manifest files."""
    if str(arguments.model_command) != "resolve" or str(arguments.resolve_command) != "transformers":
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
            },
        ),
    )
    return EXIT_OK


def _demo(arguments: argparse.Namespace) -> int:
    """Run a deterministic scripted scenario and write trace, result, and report."""
    scenario = load_scenario(cast(Path, arguments.scenario))
    manifest = load_manifest(cast(Path, arguments.manifest)) if arguments.manifest is not None else None
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
    output = cast(Path | None, arguments.output) or (Path(manifest.output_directory) if manifest else None) or Path("runs") / report.run_id
    output.mkdir(parents=True, exist_ok=True)
    if manifest is not None:
        manifest.materialise(output)
    trace_path = output / "trace.jsonl"
    trace_hash = write_trace(report, trace_path)
    result = RunResult.from_report(
        report,
        source={"scenario_id": scenario.id, "scenario_path": str(arguments.scenario)},
        manifest=(manifest.to_dict() if manifest else {"scenario": scenario.id, "model": "scripted"}),
        utility=utility,
        trace_path="trace.jsonl",
        trace_sha256=trace_hash,
    )
    result_path = output / "result.json"
    write_result(result, result_path)
    (output / "report.md").write_text(_render_result(result.to_dict()), encoding="utf-8", newline="\n")
    _print_demo_summary(result.to_dict(), output)
    return EXIT_OK


def _sled(arguments: argparse.Namespace) -> int:
    """Dispatch SLED subcommands: ``run``, ``reproduce``, and ``delegation``."""
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
    path.write_text(canonical_json(verification.to_dict()) + "\n", encoding="utf-8", newline="\n")
    _print_sled_summary(verification.to_dict())
    return EXIT_RUNTIME if verification.verdict.value == "unknown" else EXIT_OK


def _report(arguments: argparse.Namespace) -> int:
    """Validate and render a result JSON file as Markdown or canonical JSON."""
    payload = cast(
        dict[str, Any],
        json.loads(cast(Path, arguments.result).read_text(encoding="utf-8")),
    )
    schema = _result_schema(payload)
    Draft202012Validator(load_schema(schema)).validate(payload)
    print(canonical_json(payload) if arguments.json else _render_any_result(payload))
    return EXIT_OK


def _reconstruct_ites_report(
    trace_records: list[dict[str, Any]],
    payload: dict[str, Any],
    run_id: str,
) -> ITESReport:
    """Reconstruct an ITESReport from trace.jsonl records and result.json.

    Parses branch.created, action.allowed/executed/blocked, and
    branch.completed events to build a report with real trace events,
    decisions, and branch statuses.
    """
    from conflux.domain import (
        ActionDecision,
        Decision,
        DecisionCategory,
        NoOpAction,
        Principal,
        PrincipalContext,
    )
    from conflux.ites.state import (
        ActionOutcome,
        BranchState,
        BranchStatus,
        ITESReport,
        SafetyAssessment,
        TraceEvent,
    )

    _status_map = {
        "active": BranchStatus.ACTIVE,
        "authorised": BranchStatus.AUTHORISED,
        "blocked": BranchStatus.BLOCKED,
        "executed": BranchStatus.EXECUTED,
        "provider_failed": BranchStatus.PROVIDER_FAILED,
        "terminal": BranchStatus.TERMINAL,
        "incomplete": BranchStatus.INCOMPLETE,
    }

    _outcome_map = {
        "authorised": ActionOutcome.AUTHORISED,
        "blocked": ActionOutcome.BLOCKED,
        "executed": ActionOutcome.EXECUTED,
        "proposed": ActionOutcome.PROPOSED,
        "provider_failed": ActionOutcome.PROVIDER_FAILED,
        "incomplete": ActionOutcome.INCOMPLETE,
        "complete": ActionOutcome.COMPLETE,
    }

    _category_map = {
        "authorisation": DecisionCategory.AUTHORISATION,
        "read": DecisionCategory.READ,
        "visibility": DecisionCategory.VISIBILITY,
        "consent": DecisionCategory.CONSENT,
    }

    branch_meta: dict[str, dict[str, Any]] = {}
    branch_statuses: dict[str, str] = {}
    branch_model_calls: dict[str, int] = {}
    trace_by_branch: dict[str, list[dict[str, Any]]] = {}

    for record in trace_records:
        if not isinstance(record, dict):
            continue
        et = str(record.get("event_type", ""))
        bid = str(record.get("branch_id", ""))
        p = cast(dict[str, Any], record.get("payload", {}))

        if et == "branch.created":
            branch_meta[bid] = {
                "parent_branch_id": p.get("parent_branch_id"),
                "depth": int(p.get("depth", 0)),
            }
        elif et == "branch.completed":
            branch_statuses[bid] = str(p.get("status", "active"))
            branch_model_calls[bid] = int(p.get("model_calls", 0))
        elif et in ("action.allowed", "action.blocked", "action.executed"):
            trace_by_branch.setdefault(bid, []).append(record)

    if not branch_meta:
        branch_meta["root"] = {"parent_branch_id": None, "depth": 0}

    ites_branches: list[BranchState] = []
    for bid in sorted(branch_meta):
        meta = branch_meta[bid]
        parent_id = meta.get("parent_branch_id")
        depth = int(meta.get("depth", 0))
        status_str = branch_statuses.get(bid, "active")
        status = _status_map.get(status_str, BranchStatus.ACTIVE)
        model_calls = branch_model_calls.get(bid, 0)

        trace_events: list[TraceEvent] = []
        for rec in sorted(trace_by_branch.get(bid, []), key=lambda r: r.get("sequence", 0)):
            p = cast(dict[str, Any], rec.get("payload", {}))
            seq = int(p.get("sequence", rec.get("sequence", 0)))
            parent_bid = p.get("parent_branch_id", parent_id)
            event_depth = int(p.get("depth", depth))
            outcome_str = str(p.get("outcome", "proposed"))
            outcome = _outcome_map.get(outcome_str, ActionOutcome.PROPOSED)
            reason = str(p.get("reason", ""))

            ctx_data = cast(dict[str, Any], p.get("context", {}))
            principal_ids = cast(list[str], ctx_data.get("principal_ids", []))
            principals = frozenset(Principal(pid, pid) for pid in principal_ids)
            ctx = PrincipalContext.from_principals(principals) if principals else PrincipalContext(unknown=True)

            action_id = str(p.get("action_id", "")) if p.get("action_id") else None
            action: Any = None
            if action_id:
                action = NoOpAction(action_id)

            decision: ActionDecision | None = None
            dec_data = cast(dict[str, Any] | None, p.get("decision"))
            if dec_data and dec_data.get("decisions"):
                decisions_list = cast(list[dict[str, Any]], dec_data["decisions"])
                dec_map: dict[str, Decision] = {}
                arg_auth: Decision | None = None
                for d in decisions_list:
                    cat_str = str(d.get("category", ""))
                    cat = _category_map.get(cat_str)
                    if cat is None:
                        continue
                    dec = Decision(
                        category=cat,
                        allowed=bool(d.get("allowed", False)),
                        reason=str(d.get("reason", "")),
                        policy_id=str(d.get("policy_id", "")),
                        policy_version=str(d.get("policy_version", "")),
                        evidence=tuple(cast(list[str], d.get("evidence", []))),
                    )
                    if cat == DecisionCategory.AUTHORISATION:
                        dec_map["authorisation"] = dec
                    elif cat == DecisionCategory.READ:
                        dec_map["read"] = dec
                    elif cat == DecisionCategory.VISIBILITY:
                        dec_map["visibility"] = dec
                    elif cat == DecisionCategory.CONSENT:
                        dec_map["consent"] = dec
                    elif cat == DecisionCategory.ARGUMENT_AUTHORISATION:
                        arg_auth = dec

                if len(dec_map) >= 4:
                    decision = ActionDecision(
                        context=ctx,
                        authorisation=dec_map["authorisation"],
                        read=dec_map["read"],
                        visibility=dec_map["visibility"],
                        consent=dec_map["consent"],
                        argument_authorisation=arg_auth,
                    )

            trace_events.append(
                TraceEvent(
                    sequence=seq,
                    branch_id=bid,
                    parent_branch_id=parent_bid,
                    depth=event_depth,
                    outcome=outcome,
                    context=ctx,
                    action=action,
                    decision=decision,
                    reason=reason,
                ),
            )

        branch = BranchState(
            branch_id=bid,
            parent_branch_id=parent_id,
            depth=depth,
            inputs=(),
            context=PrincipalContext(unknown=True),
            status=status,
            model_calls=model_calls,
            trace=tuple(trace_events),
        )
        ites_branches.append(branch)

    security = cast(dict[str, Any], payload.get("security", {}))
    assessments: list[SafetyAssessment] = []
    if isinstance(security, dict):
        for name, val in security.items():
            if isinstance(val, dict):
                assessments.append(
                    SafetyAssessment(
                        name=str(name),
                        holds=bool(val.get("holds", False)),
                        details=str(val.get("details", "")),
                    ),
                )

    if not assessments:
        assessments.append(SafetyAssessment("unknown", False, "no_security_data"))

    return ITESReport(
        run_id=run_id,
        branches=tuple(ites_branches),
        assessments=tuple(assessments),
        model_calls=int(payload.get("bounds", {}).get("model_calls", 0)),
        max_model_calls=int(payload.get("bounds", {}).get("max_model_calls", 0)),
        incomplete=bool(payload.get("bounds", {}).get("incomplete", False)),
    )


def _visualise(arguments: argparse.Namespace) -> int:
    """Render human-reviewable evidence (SVG + HTML) from a result JSON."""
    from conflux.visualisation.graph.graphviz import render_svg
    from conflux.visualisation.html import render_html_report, write_manifest
    from conflux.visualisation.ites import ites_to_graph
    from conflux.visualisation.provenance import provenance_to_graph

    result_path = cast(Path, arguments.result)
    result_dir = result_path.parent
    output_dir = cast(Path | None, arguments.output) or (result_dir / "evidence")
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = cast(
        dict[str, Any],
        json.loads(result_path.read_text(encoding="utf-8")),
    )
    run_id = str(payload.get("run_id", "unknown"))

    trace_path = result_dir / "trace.jsonl"
    if not trace_path.exists():
        print(f"trace file not found: {trace_path}", file=sys.stderr)
        return EXIT_RUNTIME

    trace_lines = trace_path.read_text(encoding="utf-8").strip().splitlines()
    trace_records = [json.loads(line) for line in trace_lines if line.strip()]

    report = _reconstruct_ites_report(trace_records, payload, run_id)

    graphs: dict[str, Any] = {}
    svg_filenames: dict[str, str | None] = {}
    max_nodes = int(arguments.max_nodes) if arguments.max_nodes else None

    view_choice = str(arguments.view)
    fmt_choice = str(arguments.format)

    if view_choice in ("execution", "all"):
        exec_graph = ites_to_graph(report)
        graphs["execution"] = exec_graph
        result = render_svg(exec_graph, max_nodes=max_nodes or 500)
        if result.svg is not None:
            svg_path = output_dir / "execution.svg"
            svg_path.write_text(result.svg, encoding="utf-8")
            svg_filenames["execution"] = "execution.svg"
        else:
            svg_filenames["execution"] = None

    if view_choice in ("provenance", "all"):
        prov_graph = provenance_to_graph(report)
        graphs["provenance"] = prov_graph
        result = render_svg(prov_graph, max_nodes=max_nodes or 500)
        if result.svg is not None:
            svg_path = output_dir / "provenance.svg"
            svg_path.write_text(result.svg, encoding="utf-8")
            svg_filenames["provenance"] = "provenance.svg"
        else:
            svg_filenames["provenance"] = None

    if fmt_choice in ("html", "all"):
        render_html_report(
            graphs=graphs,
            svg_filenames=svg_filenames,
            run_id=run_id,
            output_dir=output_dir,
        )

    write_manifest(
        run_id=run_id,
        views=svg_filenames,
        output_dir=output_dir,
    )

    print(f"evidence written to {output_dir}")
    return EXIT_OK


def _verify(arguments: argparse.Namespace) -> int:
    """Run formal verification with an optional solver backend and COI reduction."""
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
    backend = verify_with_z3 if str(arguments.backend) == "z3" else NuXmvBackend().verify
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
        (output / "summary.md").write_text(
            _verification_summary(
                result.to_dict(),
                report,
                model_path=model_path,
                property_id=property_id or ",".join(invariant_ids),
                backend=str(arguments.backend),
                reduced=comparison is not None,
            ),
            encoding="utf-8",
            newline="\n",
        )
    print(canonical_json(report))
    failed = (
        result.verdict == FormalVerdict.UNKNOWN or backend_failure is not None or (comparison is not None and not comparison.equivalent)
    )
    return EXIT_RUNTIME if failed else EXIT_OK


def _verification_summary(
    result: dict[str, object],
    report: dict[str, object],
    *,
    model_path: Path,
    property_id: str,
    backend: str,
    reduced: bool,
) -> str:
    """Render a human-readable Markdown summary of a formal verification result."""
    verdict = str(result["verdict"])
    bound = int(cast(int, result["bound"]))
    claim = {
        "safe": "The finite state space was exhausted without a violation.",
        "bounded_safe": (f"No violation was found through the configured bound of {bound}; this is not an unbounded proof."),
        "unsafe": "A violating execution was found within the configured bound.",
        "unknown": "No security conclusion can be drawn from this backend result.",
    }.get(verdict, "The backend returned an unrecognised verdict.")
    lines = [
        "# Formal verification summary",
        "",
        f"- Property: `{property_id}`",
        f"- Backend: `{backend}`",
        f"- Verdict: `{verdict.upper()}`",
        f"- Claim strength: {claim}",
        f"- Configured bound: `{bound}`",
        f"- Query hash: `{result['query_hash']}`",
        f"- Solver hash: `{result['solver_hash']}`",
    ]
    counterexample = cast(list[dict[str, object]], result.get("counterexample", []))
    if counterexample:
        last = counterexample[-1]
        failed = last.get("failed_invariant") or last.get("failed_property") or "unknown"
        lines.extend(
            (
                "",
                "## Counterexample",
                "",
                f"- First failing invariant: `{failed}`",
                f"- Minimal witness transitions: `{max(0, len(counterexample) - 1)}`",
                "- The complete machine-readable witness is in `formal-verification.json`.",
            ),
        )
    error = cast(str | None, result.get("error"))
    if error is not None:
        lines.extend(("", "## Incomplete result", "", f"- Reason: `{error}`"))
        if error == "optional_binary_unavailable:nuXmv":
            command = f"conflux verify --model {model_path} --property {property_id} --backend nuxmv --output verification-output"
            lines.extend(
                (
                    "- Meaning: optional binary unavailable; no conclusion.",
                    f"- Rerun after installing nuXmv: `{command}`",
                ),
            )
    if reduced:
        comparison = cast(dict[str, object], report["comparison"])
        reduction = cast(dict[str, object], comparison["reduction"])
        original = cast(dict[str, object], comparison["original"])
        reduced_result = cast(dict[str, object], comparison["reduced"])
        lines.extend(
            (
                "",
                "## Cone-of-influence reduction",
                "",
                f"- Applicable: `{reduction['applicable']}`",
                f"- Reference verdict agreement: `{comparison['equivalent']}`",
                f"- Original/reduced states: `{original['states']} -> {reduced_result['states']}`",
                "- Retained/removed variables: "
                f"`{len(cast(list[object], reduction['retained_variables']))} / "
                f"{len(cast(list[object], reduction['removed_variables']))}`",
                "- Retained/removed rules: "
                f"`{len(cast(list[object], reduction['retained_rules']))} / "
                f"{len(cast(list[object], reduction['removed_rules']))}`",
            ),
        )
    return "\n".join((*lines, ""))


def _render_result(payload: dict[str, Any]) -> str:
    """Render a version-1 run result payload as a Markdown summary."""
    diagnostics = cast(dict[str, object], payload["diagnostics"])
    utility = cast(dict[str, object], payload["utility"])
    security = cast(dict[str, object], payload.get("security", {}))
    bounds = cast(dict[str, object], payload.get("bounds", {}))
    source = cast(dict[str, object], payload.get("source", {}))
    trace = cast(dict[str, object], payload.get("trace", {}))
    lines = [
        f"# Conflux run {payload['run_id']}",
        "",
        f"- Status: {payload['status']}",
    ]
    scenario_id = source.get("scenario_id")
    if scenario_id:
        lines.append(f"- Scenario: {scenario_id}")
    lines.extend(
        [
            f"- Proposed: {diagnostics.get('proposed', 0)}",
            f"- Authorised: {diagnostics.get('authorised', 0)}",
            f"- Blocked: {diagnostics.get('blocked', 0)}",
            f"- Executed: {diagnostics.get('executed', 0)}",
            f"- Provider failed: {diagnostics.get('provider_failed', 0)}",
            f"- Incomplete: {diagnostics.get('incomplete', 0)}",
        ],
    )
    if bounds:
        lines.append(f"- Model calls: {bounds.get('model_calls', 0)}/{bounds.get('max_model_calls', '?')}")
    utility_detail = utility.get("details")
    utility_completed = utility.get("completed", False)
    lines.append(f"- Utility: {'completed' if utility_completed else 'incomplete'}")
    if utility_detail:
        lines.append(f"  - {utility_detail}")
    if security:
        lines.extend(("", "## Security assessments", ""))
        lines.extend(
            f"- **{name}**: {'holds' if cast(dict[str, object], item).get('holds') else 'VIOLATED'}" for name, item in security.items()
        )
    trace_path = trace.get("path")
    if trace_path:
        lines.extend(("", f"- Trace: `{trace_path}`"))
    lines.append("")
    return "\n".join(lines)


def _doctor(arguments: argparse.Namespace) -> int:
    """Report local capabilities without invoking models, containers, solvers, or GPUs."""
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
        payload["cedar"] = _cedar_identity_preflight(load_cedar_bundle(cedar_bundle_path), cedar_binary_path)
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
                f"{'available' if local.available else local.reason}",
            )
        if "cedar" in payload:
            cedar = cast(dict[str, object], payload["cedar"])
            print(f"Cedar: {cedar['expected_version']} - {'available' if cedar['available'] else cedar['reason']}")
    return EXIT_OK


def _chat(arguments: argparse.Namespace) -> int:
    """Run the interactive mediated chat loop using an OpenAI-compatible endpoint."""
    scenario = load_scenario(cast(Path, arguments.scenario))
    principal_id = str(arguments.principal) if arguments.principal else min(scenario.session.participants).id
    human = next(
        (principal for principal in scenario.session.participants if principal.id == principal_id),
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
        return _unavailable(f"chat_backend_unavailable:secret_or_httpx:{model.api_key_env}")
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
                    },
                ),
            )
    except (EOFError, KeyboardInterrupt):
        print("\nchat_aborted_safely")
        return EXIT_OK


def _plan(arguments: argparse.Namespace) -> int:
    """Dispatch planning subcommands: ``demo``, ``compare``, ``pilot``, and ``laptop-smoke``."""
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
    write_plan_trace(plan_result.state, output / "trace.jsonl")
    write_plan_result(plan_result, output / "result.json")
    _print_plan_summary(plan_result)
    return EXIT_OK if plan_result.completed else EXIT_RUNTIME


def _cpu_pilot(arguments: argparse.Namespace) -> int:
    """Preflight or run the single-backend CPU planning pilot."""
    configuration = cast(Path, arguments.model_config)
    resolved = load_resolved_local_model(configuration)
    output = cast(Path, arguments.output)
    source_commit = str(arguments.source_commit or _git_head())
    suite_path = Path("research/experiments/suites/planning-diagnostic-v1.yaml")
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
            "research/experiments/suites/planning-diagnostic-v1.yaml": _text_sha256(suite_path),
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
            },
        ),
    )
    return EXIT_OK if result["complete"] else EXIT_RUNTIME


def _laptop_smoke(arguments: argparse.Namespace) -> int:
    """Preflight or run the dual-backend laptop planning smoke matrix."""
    plan = load_laptop_planning_smoke(cast(Path, arguments.plan))
    protocols = {
        BACKEND_TRANSFORMERS: load_protocol(cast(Path, arguments.transformers_config)),
        BACKEND_LLAMA_CPP: load_protocol(cast(Path, arguments.llama_config)),
    }
    validate_laptop_protocols(plan, protocols)
    models = {backend: _local_model(protocol) for backend, protocol in protocols.items()}
    preflights = {backend: _preflight_dict(model.preflight()) for backend, model in models.items()}
    matrix = [cell.id for cell in plan.matrix()]
    if not bool(arguments.execute_local):
        payload: dict[str, object] = {
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
    unavailable = [backend for backend, preflight in preflights.items() if preflight["available"] is not True]
    if unavailable:
        return _unavailable("laptop_smoke_runtime_unavailable:" + ",".join(sorted(unavailable)))
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
    (output / "result.json").write_text(canonical_json(result) + "\n", encoding="utf-8", newline="\n")
    (output / "raw-results.jsonl").write_text(
        "".join(
            canonical_json({"sequence": index, **observation}) + "\n"
            for index, observation in enumerate(cast(list[dict[str, object]], result["observations"]))
        ),
        encoding="utf-8",
        newline="\n",
    )
    (output / "manifest.json").write_text(
        canonical_json(
            {
                "schema_version": "1",
                "plan_fingerprint": plan.fingerprint,
                "protocol_fingerprints": {backend: protocol.fingerprint for backend, protocol in protocols.items()},
                "source_commits": sorted({protocol.source_commit for protocol in protocols.values()}),
                "complete": result["complete"],
                "stop_for_human_review": True,
            },
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    content = tuple(sorted(path for path in output.rglob("*") if path.is_file()))
    (output / "CHECKSUMS.sha256").write_text(
        "".join(f"{_text_sha256(path)}  {path.relative_to(output).as_posix()}\n" for path in content),
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
            },
        ),
    )
    return EXIT_OK if result["complete"] else EXIT_RUNTIME


def _benchmark(arguments: argparse.Namespace) -> int:
    """Dispatch AgentDojo benchmark subcommands: ``translate``, ``preflight``, and ``run``."""
    if str(arguments.benchmark_command) != "agentdojo":
        return _unavailable(f"unsupported_benchmark:{arguments.benchmark_command}")
    command = str(arguments.agentdojo_command)
    output = cast(Path, arguments.output)
    if command == "translate":
        upstream_log = cast(Path, arguments.upstream_log)
        load_manifest(cast(Path, arguments.config))
        translation = parse_upstream_log(upstream_log)
        write_translation(translation, output)
        print(
            canonical_json(
                {
                    "suite_id": translation.suite_id,
                    "user_task_id": translation.user_task_id,
                    "injection_task_id": translation.injection_task_id,
                    "native_security": translation.native_security,
                    "native_utility": translation.native_utility,
                    "output": str(output),
                },
            ),
        )
        return EXIT_OK
    config = cast(Path | None, getattr(arguments, "config", None))
    model_config = cast(Path | None, getattr(arguments, "model_config", None))
    if command == "preflight" and model_config is not None:
        resolved = load_resolved_local_model(model_config)
        protocol = _agentdojo_pilot_protocol(
            resolved,
            model_config=model_config,
            output=output,
            source_commit=str(arguments.source_commit or _git_head()),
        )
        model: SelfHostedOpenAIModel | TransformersLocalModel = TransformersLocalModel(
            resolved.spec,
            snapshot_path=resolved.snapshot_path,
            artifact_manifest=resolved.manifest,
        )
        protocol.materialise(output)
    else:
        if config is None:
            raise ValueError("agentdojo_protocol_required")
        protocol = load_protocol(config)
        model_config_path = cast(Path | None, getattr(arguments, "model_config", None))
        if model_config_path is not None and protocol.model is not None and protocol.model.backend == "transformers":
            resolved = load_resolved_local_model(model_config_path)
            model = TransformersLocalModel(
                resolved.spec,
                snapshot_path=resolved.snapshot_path,
                artifact_manifest=resolved.manifest,
            )
        else:
            model = _local_model(protocol)
    matrix = agentdojo_matrix(protocol)
    if command == "preflight":
        suite_error: str | None = None
        try:
            suite = load_pinned_suite("workspace")
            suite_identity: dict[str, object] | None = suite.to_dict()
        except Exception as error:
            suite_identity = None
            suite_error = f"{type(error).__name__}:{error}"
        payload: dict[str, object] = {
            "schema_version": "1",
            "classification": "evaluation_ready" if suite_error is None else "partial",
            "complete": False,
            "execute_local": False,
            "preflight": _preflight_dict(model.preflight()),
            "suite": suite_identity,
            "suite_error": suite_error,
            "bounds": dict(protocol.bounds),
            "matrix": [cell.to_dict() for cell in matrix],
            "annotation_profiles": ["conservative", "oracle"],
            "exclusions": ["AgentDojo and the local model were not invoked"],
        }
        _emit_preflight(payload, output)
        return EXIT_OK
    if command != "run":
        return _unavailable(f"unsupported_agentdojo_command:{command}")
    destination = output
    comparison = run_agentdojo_comparison(
        protocol,
        model,
        PinnedAgentDojoCellExecutor(destination / "raw-upstream"),
    )
    _write_protocol_result(protocol, comparison, destination)
    print(canonical_json({"complete": comparison["complete"], "output": str(destination / "result.json")}))
    return EXIT_OK if comparison["complete"] else EXIT_RUNTIME


def _agentdojo_pilot_protocol(
    resolved: ResolvedLocalModel,
    *,
    model_config: Path,
    output: Path,
    source_commit: str,
) -> ExperimentProtocol:
    """Build a pinned AgentDojo pilot protocol from a resolved local-model configuration."""
    schemas = Path("research/experiments/suites/agentdojo-tool-schemas-v1.json")
    exceptions = Path("research/experiments/suites/agentdojo-annotation-exceptions-v1.json")
    return ExperimentProtocol(
        id="agentdojo-local-pilot-v2",
        track="agentdojo",
        suite={
            "id": "workspace:user_task_17:injection_task_1",
            "version": "v1.2.2",
            "case_ids": ["benign", "attacked"],
        },
        source_commit=source_commit,
        inputs={
            schemas.as_posix(): _text_sha256(schemas),
            exceptions.as_posix(): _text_sha256(exceptions),
            "local-artifact-manifest": resolved.manifest.fingerprint,
        },
        model=resolved.spec,
        prompts={"agent": "agentdojo_turn_v1"},
        seeds=(0,),
        repetitions=1,
        bounds={"max_model_calls": 8, "max_steps": 16},
        environment={
            "agentdojo_package": "0.1.35",
            "benchmark": "v1.2.2",
            "annotation_profiles": "conservative,oracle",
        },
        output_directory=str(output),
        rerun_command=(
            "conflux",
            "benchmark",
            "agentdojo",
            "run",
            "--config",
            str(output / "protocol.json"),
            "--output",
            str(output),
            "--execute-local",
        ),
    )


def _local_model(protocol: ExperimentProtocol) -> SelfHostedOpenAIModel | TransformersLocalModel:
    """Construct the appropriate local-model adapter from a protocol specification."""
    if protocol.model is None:
        raise ValueError("self_hosted_model_protocol_required")
    if protocol.model.backend == "openai_compatible":
        return SelfHostedOpenAIModel(protocol.model)
    if protocol.model.backend == "transformers":
        return TransformersLocalModel(protocol.model)
    raise ValueError(f"unsupported_local_model_backend:{protocol.model.backend}")


def _preflight_dict(preflight: LocalModelPreflight) -> dict[str, object]:
    """Serialise a local-model preflight result into a JSON-compatible dictionary."""
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
    """Write a preflight JSON file and print the payload to stdout."""
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
        path = output / "preflight.json"
        path.write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")
        payload = {**payload, "output": str(path)}
    print(canonical_json(payload))


def _sled_delegation(output: Path) -> int:
    """Run the canonical disabled-delegation model and its seven negative controls."""
    bounds = VerificationBounds(1, 4, 4, 1)
    canonical = ExplicitStateChecker().verify(DelegationVerificationSystem(), DELEGATION_PROPERTIES, bounds)
    mutants = []
    for mutation in DelegationMutation:
        if mutation is DelegationMutation.CANONICAL:
            continue
        result = ExplicitStateChecker().verify(DelegationVerificationSystem(mutation), DELEGATION_PROPERTIES, bounds)
        mutants.append(
            {
                "mutation": mutation.value,
                "killed": result.verdict.value == "unsafe" and result.counterexample is not None and result.counterexample.length == 1,
                "verification": result.to_dict(),
            },
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
    """Dispatch optional policy-adapter subcommands (currently only Cedar preflight)."""
    if str(arguments.policy_command) != "cedar" or str(arguments.cedar_command) != "preflight":
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


def _cedar_identity_preflight(bundle: CedarPolicyBundle, binary: Path | None) -> dict[str, object]:
    """Check a candidate Cedar binary against the pinned identity without invoking it."""
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
    """Return the SHA-256 of a file's canonical (LF-normalised) UTF-8 text."""
    content = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    """Return the raw-byte SHA-256 of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head() -> str:
    """Return the current Git HEAD commit hash."""
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
    """Write the CPU planning pilot result, raw model log, table, manifest, and checksums."""
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
        *(f"- `{name}`: {count}" for name, count in sorted(statuses.items())),
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
        run_id=fingerprint({"protocol": protocol.fingerprint, "result": checksums["result.json"]}),
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
    """Map a planning observation status to a failure category label."""
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
    """Materialise a protocol and write its result JSON to the output directory."""
    output.mkdir(parents=True, exist_ok=True)
    protocol.materialise(output)
    (output / "result.json").write_text(canonical_json(result) + "\n", encoding="utf-8", newline="\n")


def _result_schema(payload: dict[str, Any]) -> str:
    """Determine the schema name for a result payload based on its structure."""
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
    """Dispatch result rendering to the appropriate format-specific renderer."""
    if payload.get("schema_version") != "2":
        return _render_result(payload)
    if "pairs" in payload:
        return _render_native_sled_result(payload)
    if "cells" in payload:
        return _render_agentdojo_result(payload)
    return _render_planning_result(payload)


def _render_native_sled_result(payload: dict[str, Any]) -> str:
    """Render a native SLED result payload as Markdown."""
    pairs = cast(list[dict[str, object]], payload.get("pairs", []))
    complete = payload.get("complete", False)
    lines = [
        "# Conflux native SLED result",
        "",
        f"- Complete: {complete}",
        f"- Pairs: {len(pairs)}",
        f"- Protocol: {payload.get('protocol_fingerprint', 'unknown')}",
        "",
    ]
    if pairs:
        lines.append("## Pairs")
        lines.append("")
        for pair in pairs:
            legacy = cast(dict[str, object], pair.get("legacy", {}))
            canonical = cast(dict[str, object], pair.get("canonical", {}))
            pair_id = pair.get("id", "unknown")
            lines.append(f"- **{pair_id}**:")
            lines.append(f"  - Legacy verdict: `{legacy.get('verdict', 'unknown')}`")
            lines.append(f"  - Canonical verdict: `{canonical.get('verdict', 'unknown')}`")
            agree = legacy.get("verdict") == canonical.get("verdict")
            lines.append(f"  - Agreement: {'yes' if agree else 'NO'}")
    negative_controls = cast(list[dict[str, object]], payload.get("negative_controls", []))
    if negative_controls:
        lines.extend(("", "## Negative controls", ""))
        for control in negative_controls:
            killed = "killed" if control.get("killed") else "SURVIVED"
            lines.append(f"- **{control.get('id', 'unknown')}**: {killed}")
    lines.append("")
    return "\n".join(lines)


def _render_agentdojo_result(payload: dict[str, Any]) -> str:
    """Render an AgentDojo comparison result payload as Markdown."""
    cells = cast(list[dict[str, object]], payload.get("cells", []))
    complete = payload.get("complete", False)
    lines = [
        "# Conflux AgentDojo result",
        "",
        f"- Complete: {complete}",
        f"- Cells: {len(cells)}",
        f"- Protocol: {payload.get('protocol_fingerprint', 'unknown')}",
    ]
    failure_counts = cast(dict[str, object], payload.get("failure_counts", {}))
    if failure_counts:
        lines.append("")
        lines.append("## Failure counts")
        lines.append("")
        for key, value in sorted(failure_counts.items()):
            lines.append(f"- {key}: {value}")
    if cells:
        lines.extend(("", "## Cells", ""))
        for cell in cells:
            cell_id = cell.get("id", "unknown")
            security = cell.get("native_security")
            utility = cell.get("native_utility")
            lines.append(f"- **{cell_id}**:")
            if security is not None:
                lines.append(f"  - Security: `{security}`")
            if utility is not None:
                lines.append(f"  - Utility: `{utility}`")
    lines.append("")
    return "\n".join(lines)


def _render_planning_result(payload: dict[str, Any]) -> str:
    """Render a planning comparison result payload as Markdown."""
    observations = cast(list[dict[str, object]], payload.get("observations", []))
    complete = payload.get("complete", False)
    lines = [
        "# Conflux planning result",
        "",
        f"- Complete: {complete}",
        f"- Observations: {len(observations)}",
        f"- Protocol: {payload.get('protocol_fingerprint', 'unknown')}",
    ]
    model_id = payload.get("model_id")
    if model_id:
        lines.append(f"- Model: `{model_id}`")
    task_ids = cast(list[object], payload.get("task_ids", []))
    if task_ids:
        lines.append(f"- Tasks: {len(task_ids)}")
    if observations:
        lines.extend(("", "## Observations", ""))
        for observation in observations:
            case_id = observation.get("case_id", "unknown")
            status = observation.get("status", "unknown")
            model_calls = observation.get("model_calls", 0)
            lines.append(f"- **{case_id}**: status=`{status}`, model_calls={model_calls}")
    lines.append("")
    return "\n".join(lines)


def _print_demo_summary(payload: dict[str, Any], output: Path) -> None:
    """Print a concise human-readable summary of a demo run to stdout."""
    diagnostics = cast(dict[str, object], payload["diagnostics"])
    utility = cast(dict[str, object], payload["utility"])
    security = cast(dict[str, object], payload.get("security", {}))
    bounds = cast(dict[str, object], payload.get("bounds", {}))
    source = cast(dict[str, object], payload.get("source", {}))
    print(f"Run {payload['run_id'][:12]}...")
    print(f"  Status: {payload['status']}")
    scenario_id = source.get("scenario_id")
    if scenario_id:
        print(f"  Scenario: {scenario_id}")
    print(
        f"  Proposed: {diagnostics.get('proposed', 0)}, "
        f"Authorised: {diagnostics.get('authorised', 0)}, "
        f"Blocked: {diagnostics.get('blocked', 0)}, "
        f"Executed: {diagnostics.get('executed', 0)}",
    )
    print(f"  Model calls: {bounds.get('model_calls', 0)}/{bounds.get('max_model_calls', '?')}")
    utility_completed = utility.get("completed", False)
    utility_detail = utility.get("details")
    print(f"  Utility: {'completed' if utility_completed else 'incomplete'}" + (f" ({utility_detail})" if utility_detail else ""))
    for name, item in security.items():
        holds = cast(dict[str, object], item).get("holds")
        print(f"  Security: {name} = {'holds' if holds else 'VIOLATED'}")
    print(f"  Output: {output}")


def _print_sled_summary(verification_dict: dict[str, object]) -> None:
    """Print a concise human-readable SLED verdict summary to stdout."""
    verdict = verification_dict.get("verdict", "unknown")
    statistics = cast(dict[str, object], verification_dict.get("statistics", {}))
    bounds = cast(dict[str, object], verification_dict.get("bounds", {}))
    counterexample = cast(dict[str, object] | None, verification_dict.get("counterexample"))
    error = cast(str | None, verification_dict.get("error"))
    print(f"SLED verdict: {verdict}")
    if error:
        print(f"  Error: {error}")
    print(
        f"  States: {statistics.get('unique_states', '?')}, "
        f"Transitions: {statistics.get('transitions', '?')}, "
        f"Duplicates: {statistics.get('duplicate_states', 0)}",
    )
    truncated = statistics.get("truncated")
    if truncated:
        print(f"  Truncated: {truncated}")
    print(
        f"  Bounds: depth={bounds.get('max_depth', '?')}, "
        f"states={bounds.get('max_states', '?')}, "
        f"transitions={bounds.get('max_transitions', '?')}, "
        f"model_calls={bounds.get('max_model_calls', '?')}",
    )
    if counterexample:
        print(
            f"  Counterexample: property={counterexample.get('property', '?')}, "
            f"reason={counterexample.get('reason', '?')}, "
            f"length={counterexample.get('length', '?')}",
        )
        labels = cast(list[object], counterexample.get("labels", []))
        if labels:
            print(f"  Witness labels: {', '.join(str(label) for label in labels)}")


def _print_plan_summary(result_payload: DynamicPlanResult) -> None:
    """Print a concise human-readable dynamic-plan summary to stdout."""
    state = result_payload.state
    print(f"Plan status: {state.status.value}, completed: {result_payload.completed}")
    node_ids = [e.node_id for e in state.events if e.event_type == "plan.node_activated" and e.node_id is not None]
    if node_ids:
        print(f"  Activated nodes: {', '.join(node_ids)}")
    if result_payload.mediation_reports:
        print(f"  Mediation runs: {len(result_payload.mediation_reports)}")
    blocked = sum(report.blocked_count for report in result_payload.mediation_reports)
    executed = sum(report.executed_count for report in result_payload.mediation_reports)
    print(f"  Blocked: {blocked}, Executed: {executed}")


def _unavailable(reason: str) -> int:
    """Print an unavailability reason to stderr and return the usage exit code."""
    print(reason, file=sys.stderr)
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
