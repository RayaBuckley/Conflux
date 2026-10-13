"""Tests for the runtime-to-IR conformance boundary statement (limit L3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conflux.domain import WRITE, Principal, Provenance
from conflux.planning import (
    ActionTemplate,
    ActionTemplateNode,
    ArgumentSpec,
    ArgumentType,
    LiteralBinding,
    OperationCatalogue,
    OperationSchema,
    Plan,
    TemplateArgument,
)
from conflux.verification import (
    EffectSummary,
    FormalVerdict,
    PlanAbstraction,
    abstract_plan,
    verify_plan,
)
from conflux.verification.conformance_scope import (
    UNSUPPORTED_CODES,
    UNSUPPORTED_SCOPE,
    unbounded_deployment_row,
)

pytestmark = pytest.mark.security

LEDGER = Path(__file__).resolve().parents[1] / "docs" / "evidence" / "CLAIMS.md"


def _plan_and_catalogue(
    *,
    resolve: bool,
    summarise: bool,
) -> tuple[Plan, OperationCatalogue, tuple[EffectSummary, ...]]:
    principal = Principal("alice", "Alice")
    source = Provenance.from_principal(principal, source="fixture")
    operation = OperationSchema(
        "filesystem.write",
        "1",
        "filesystem",
        "file",
        "write",
        WRITE,
        (
            ArgumentSpec("path", ArgumentType.STRING),
            ArgumentSpec("content", ArgumentType.STRING),
        ),
        "path",
    )
    action = ActionTemplateNode(
        "write",
        ActionTemplate(
            "write",
            operation.id,
            operation.version,
            (
                TemplateArgument("path", LiteralBinding("safe.txt", source)),
                TemplateArgument("content", LiteralBinding("safe", source)),
            ),
        ),
        source,
    )
    plan = Plan("plan-scope", "repair", (action,), source)
    catalogue = OperationCatalogue((operation,)) if resolve else OperationCatalogue(())
    summaries = (EffectSummary("write", True, True),) if summarise else ()
    return plan, catalogue, summaries


def _emitted_codes(abstraction: PlanAbstraction) -> set[str]:
    return {reason.rsplit(":", 1)[1] for reason in abstraction.unsupported}


def test_unknown_operation_is_declared_and_yields_unknown() -> None:
    plan, catalogue, summaries = _plan_and_catalogue(resolve=False, summarise=True)
    abstraction = abstract_plan(plan, catalogue=catalogue, effect_summaries=summaries, bound=4)
    assert not abstraction.supported
    assert _emitted_codes(abstraction) == {"unknown_operation"}
    result = verify_plan(plan, catalogue=catalogue, effect_summaries=summaries, bound=4)
    assert result.verdict is FormalVerdict.UNKNOWN
    assert result.error is not None
    assert result.error.startswith("unsupported_plan_abstraction:")


def test_missing_effect_summary_is_declared_and_yields_unknown() -> None:
    plan, catalogue, summaries = _plan_and_catalogue(resolve=True, summarise=False)
    abstraction = abstract_plan(plan, catalogue=catalogue, effect_summaries=summaries, bound=4)
    assert not abstraction.supported
    assert _emitted_codes(abstraction) == {"missing_effect_summary"}
    result = verify_plan(plan, catalogue=catalogue, effect_summaries=summaries, bound=4)
    assert result.verdict is FormalVerdict.UNKNOWN
    assert result.error is not None
    assert result.error.startswith("unsupported_plan_abstraction:")


def test_unknown_backend_yields_unknown() -> None:
    plan, catalogue, summaries = _plan_and_catalogue(resolve=True, summarise=True)
    result = verify_plan(
        plan,
        catalogue=catalogue,
        effect_summaries=summaries,
        bound=4,
        backend="spacer",
    )
    assert result.verdict is FormalVerdict.UNKNOWN
    assert result.error == "unsupported_verification_backend:spacer"


def test_declared_codes_are_the_codes_the_path_emits() -> None:
    emitted: set[str] = set()
    for resolve, summarise in ((False, True), (True, False)):
        plan, catalogue, summaries = _plan_and_catalogue(resolve=resolve, summarise=summarise)
        emitted |= _emitted_codes(abstract_plan(plan, catalogue=catalogue, effect_summaries=summaries, bound=4))
    emitted.add("unsupported_verification_backend")
    assert emitted == set(UNSUPPORTED_CODES)
    assert len(UNSUPPORTED_SCOPE) == 3


def test_supported_plan_abstraction_declares_nothing_unsupported() -> None:
    plan, catalogue, summaries = _plan_and_catalogue(resolve=True, summarise=True)
    abstraction = abstract_plan(plan, catalogue=catalogue, effect_summaries=summaries, bound=4)
    assert abstraction.supported
    assert abstraction.unsupported == ()


def test_ledger_row_matches_the_scope_statement() -> None:
    declared = unbounded_deployment_row()
    rows = [[cell.strip() for cell in line.split("|")] for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.startswith("|")]
    matching = [cells for cells in rows if len(cells) >= 3 and cells[1] == declared.claim]
    assert len(matching) == 1
    cells = matching[0]
    assert cells[2] == declared.status
    assert cells[-2] == declared.reason
