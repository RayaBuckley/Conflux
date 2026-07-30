"""Conservative plan abstraction and UNKNOWN-condition tests."""

from __future__ import annotations

from conflux.domain import WRITE, Principal, Provenance
from conflux.planning import (
    ActionTemplate,
    ActionTemplateNode,
    ArgumentSpec,
    ArgumentType,
    ContinuePlanningNode,
    LiteralBinding,
    OperationCatalogue,
    OperationSchema,
    Plan,
    TemplateArgument,
)
from conflux.verification import (
    EffectSummary,
    FormalVerdict,
    abstract_plan,
    initial_state,
    successors,
    verify_plan,
)


def fixture() -> tuple[Plan, OperationCatalogue]:
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
    continuation = ContinuePlanningNode(
        "continue",
        (),
        "manual",
        source,
        ("write",),
    )
    return (
        Plan("verified-plan", "repair", (action, continuation), source),
        OperationCatalogue((operation,)),
    )


def test_supported_plan_abstraction_is_serialisable_and_models_continuation() -> None:
    plan, catalogue = fixture()
    abstraction = abstract_plan(
        plan,
        catalogue=catalogue,
        effect_summaries=(EffectSummary("write", True, True),),
        bound=4,
    )
    assert abstraction.supported
    assert abstraction.ir is not None
    assert "arbitrary source-code semantics are not analysed" in abstraction.assumptions
    transition_ids = {rule.id for rule in abstraction.ir.transitions}
    assert transition_ids == {"verified-plan:continue", "verified-plan:write"}
    state = initial_state(abstraction.ir)
    targets = dict(successors(abstraction.ir, state))
    assert targets["verified-plan:write"]["unauthorised_executed"] is False
    assert targets["verified-plan:continue"]["continuation_seen"] is True


def test_missing_summary_and_unknown_backend_return_unknown() -> None:
    plan, catalogue = fixture()
    missing = verify_plan(
        plan,
        catalogue=catalogue,
        effect_summaries=(),
        bound=4,
    )
    assert missing.verdict == FormalVerdict.UNKNOWN
    assert "missing_effect_summary" in (missing.error or "")

    unsupported = verify_plan(
        plan,
        catalogue=catalogue,
        effect_summaries=(EffectSummary("write", True, True),),
        bound=4,
        backend="unsupported",
    )
    assert unsupported.verdict == FormalVerdict.UNKNOWN
    assert unsupported.error == "unsupported_verification_backend:unsupported"


def test_unsafe_effect_summary_is_visible_to_formal_invariant() -> None:
    plan, catalogue = fixture()
    abstraction = abstract_plan(
        plan,
        catalogue=catalogue,
        effect_summaries=(EffectSummary("write", False, True),),
        bound=4,
    )
    assert abstraction.ir is not None
    state = initial_state(abstraction.ir)
    target = dict(successors(abstraction.ir, state))["verified-plan:write"]
    assert target["unauthorised_executed"] is True
