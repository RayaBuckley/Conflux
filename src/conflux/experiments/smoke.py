"""Generate the small, deterministic, current-code M3 evidence bundle."""

from __future__ import annotations

import hashlib
from pathlib import Path

from conflux.adapters.models import ScriptedModel
from conflux.adapters.providers import InMemoryExecutor
from conflux.adapters.scenarios import load_scenario
from conflux.application import MediationService
from conflux.domain import Action, canonical_json, fingerprint
from conflux.evaluation import (
    DeterministicClock,
    ExplicitStateChecker,
    ITESVerificationSystem,
    RunResult,
    RunStatus,
    UtilityOutcome,
    VerificationResult,
    trace_records,
    write_result,
)
from conflux.evaluation.defences import ForbiddenAuthorisation, NoDefence
from conflux.ites import BranchState, ITESReport, MediatingITES, TransitionKernel

from .manifest import ExperimentManifest

_ROOT = Path(__file__).resolve().parents[3]
BUNDLE_FILES = (
    "RERUN.txt",
    "counterexample.json",
    "manifest.json",
    "raw.jsonl",
    "result.json",
    "table.md",
)


def generate_smoke_bundle(
    manifest: ExperimentManifest,
    output: Path,
    *,
    repo_root: Path | None = None,
) -> tuple[Path, ...]:
    root = repo_root or _ROOT
    output.mkdir(parents=True, exist_ok=True)
    manifest.materialise(output)
    authorised = _run(root / "examples" / "basic.yaml", execute=True)
    blocked_path = root / "experiments" / "suites" / "canonical" / "env-01-confidential-handoff.yaml"
    blocked = _run(blocked_path, execute=False)
    negative = _negative_control(blocked_path)

    records = list(trace_records(authorised)) + list(trace_records(blocked))
    clock = DeterministicClock()
    normalised = tuple(
        replace_record(record, sequence=index, timestamp=clock.at(index))
        for index, record in enumerate(records)
    )
    raw_content = "".join(canonical_json(record) + "\n" for record in normalised)
    raw_path = output / "raw.jsonl"
    raw_path.write_text(raw_content, encoding="utf-8", newline="\n")
    raw_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()

    counterexample_path = output / "counterexample.json"
    counterexample_path.write_text(
        canonical_json(negative.to_dict()) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    result = RunResult(
        run_id=fingerprint(
            {
                "manifest": manifest.fingerprint,
                "authorised": authorised.run_id,
                "blocked": blocked.run_id,
                "negative": negative.to_dict(),
            }
        ),
        status=RunStatus.COMPLETED,
        source={
            "source_commit": manifest.source_commit,
            "cases": [
                "examples/basic.yaml",
                "canonical-env-01-confidential-handoff",
            ],
        },
        manifest_hash=manifest.fingerprint,
        security={
            "authorised_task_executed": authorised.executed_count == 1,
            "attack_blocked": blocked.blocked_count >= 1,
            "negative_control_counterexample": negative.verdict.value == "unsafe",
        },
        utility=UtilityOutcome(True, "scripted_smoke_completed"),
        bounds=dict(manifest.bounds),
        diagnostics={
            "proposed": authorised.proposed_count + blocked.proposed_count,
            "authorised": authorised.authorised_count + blocked.authorised_count,
            "blocked": authorised.blocked_count + blocked.blocked_count,
            "executed": authorised.executed_count + blocked.executed_count,
            "provider_failed": (
                authorised.provider_failed_count + blocked.provider_failed_count
            ),
            "incomplete": authorised.incomplete_count + blocked.incomplete_count,
            "negative_counterexample_length": (
                negative.counterexample.length if negative.counterexample else None
            ),
        },
        trace_path="raw.jsonl",
        trace_sha256=raw_hash,
    )
    write_result(result, output / "result.json")
    (output / "table.md").write_text(
        _table(result),
        encoding="utf-8",
        newline="\n",
    )
    _write_checksums(output)
    return tuple(output / name for name in (*BUNDLE_FILES, "checksums.sha256"))


def replace_record(
    record: dict[str, object],
    *,
    sequence: int,
    timestamp: str,
) -> dict[str, object]:
    result = dict(record)
    result["sequence"] = sequence
    result["timestamp"] = timestamp
    return result


def _run(path: Path, *, execute: bool) -> ITESReport:
    scenario = load_scenario(path)
    mediator = MediatingITES(TransitionKernel(scenario.pipeline))
    report = mediator.run(
        environment=scenario.environment,
        session=scenario.session,
        initial_inputs=scenario.environment.artifacts(),
        model=ScriptedModel((scenario.model,)),
    )
    if execute:
        if len(report.authorised_branches) != 1:
            raise RuntimeError("smoke_authorised_case_did_not_yield_one_branch")
        report = MediationService(mediator).execute(
            report=report,
            branch=report.authorised_branches[0],
            executor=InMemoryExecutor(),
            environment=scenario.environment,
            session=scenario.session,
        ).report
    return report


def _negative_control(
    path: Path,
) -> VerificationResult[BranchState, Action]:
    scenario = load_scenario(path)
    action = scenario.model.proposals[0]
    return ExplicitStateChecker().verify(
        ITESVerificationSystem(
            (BranchState.initial(scenario.environment.artifacts()),),
            (action,),
            TransitionKernel(NoDefence()),
            scenario.session,
            scenario.environment,
        ),
        (ForbiddenAuthorisation(action.id),),
    )


def _table(result: RunResult) -> str:
    diagnostics = result.diagnostics
    return "\n".join(
        (
            "# M3 scripted smoke result",
            "",
            "| Measure | Value |",
            "|---|---:|",
            f"| Proposed actions | {diagnostics['proposed']} |",
            f"| Authorised actions | {diagnostics['authorised']} |",
            f"| Blocked actions | {diagnostics['blocked']} |",
            f"| Executed actions | {diagnostics['executed']} |",
            f"| Provider failures | {diagnostics['provider_failed']} |",
            f"| Negative-control counterexample length | {diagnostics['negative_counterexample_length']} |",
            "",
            "Generated from `result.json`; no values are hand-entered.",
            "",
        )
    )


def _write_checksums(output: Path) -> None:
    lines = (
        f"{_canonical_file_sha256(output / name)}  {name}"
        for name in BUNDLE_FILES
    )
    (output / "checksums.sha256").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _canonical_file_sha256(path: Path) -> str:
    content = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


__all__ = ["BUNDLE_FILES", "generate_smoke_bundle", "replace_record"]
