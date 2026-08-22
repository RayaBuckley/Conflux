"""Versioned schema, trace, and result evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator

from conflux.application import DecisionPipeline
from conflux.domain import Artifact, EnvironmentSnapshot, NoOpAction, ProposalBatch, Session
from conflux.evaluation import (
    RunResult,
    UtilityOutcome,
    VerificationBounds,
    VerificationResult,
    VerificationVerdict,
    trace_records,
    write_result,
    write_trace,
)
from conflux.ites import MediatingITES, TransitionKernel

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"

pytestmark = pytest.mark.integration


class NoOpModel:
    def propose(self, inputs: tuple[Artifact[Any], ...]) -> ProposalBatch:
        _ = inputs
        return ProposalBatch.alternatives(NoOpAction("noop"))


def _schema(name: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads((SCHEMAS / name).read_text(encoding="utf-8")),
    )


def test_checked_in_schemas_are_valid() -> None:
    for path in SCHEMAS.glob("*.schema.json"):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))


def test_proposal_and_verification_records_validate() -> None:
    Draft202012Validator(_schema("proposal-batch-v2.schema.json")).validate(ProposalBatch.alternatives(NoOpAction("noop")).to_dict())
    result: VerificationResult[object, object] = VerificationResult(
        VerificationVerdict.SAFE,
        1,
        0,
        0,
        False,
        VerificationBounds(),
    )
    Draft202012Validator(_schema("verification-result.schema.json")).validate(result.to_dict())


def test_golden_trace_event_validates() -> None:
    event = json.loads((ROOT / "tests" / "fixtures" / "traces" / "minimal-event.json").read_text(encoding="utf-8"))
    Draft202012Validator(_schema("trace-event.schema.json")).validate(event)


def test_trace_and_result_writers_are_deterministic(
    tmp_path: Path,
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
) -> None:
    item = environment.data_item("shared-doc")
    assert item is not None
    report = MediatingITES(TransitionKernel(pipeline)).run(
        environment=environment,
        session=session,
        initial_inputs=(item.to_artifact(),),
        model=NoOpModel(),
    )
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    first_hash = write_trace(report, first)
    second_hash = write_trace(report, second)
    assert first_hash == second_hash
    assert first.read_bytes() == second.read_bytes()
    validator = Draft202012Validator(_schema("trace-event-v3.schema.json"))
    records = trace_records(report)
    for record in records:
        validator.validate(record)
    event_types = [str(record["event_type"]) for record in records]
    assert event_types[0] == "run.started"
    assert event_types[-1] == "run.completed"
    assert "branch.created" in event_types
    assert event_types.count("policy.action_decided") == 1
    assert event_types.count("policy.read_decided") == 1
    assert event_types.count("policy.visibility_decided") == 1
    assert event_types.count("policy.consent_decided") == 1

    result = RunResult.from_report(
        report,
        source={"commit": "test"},
        manifest={"id": "fixture"},
        utility=UtilityOutcome(True, "noop"),
        trace_sha256=first_hash,
    )
    result_path = tmp_path / "result.json"
    write_result(result, result_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    Draft202012Validator(_schema("result.schema.json")).validate(payload)
