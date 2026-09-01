"""Tests for extended plan IR invariants: delegation, monotonic confinement, revocation, liveness."""

from __future__ import annotations

import pytest

from conflux.domain import WRITE, Principal, Provenance
from conflux.planning import (
    ActionTemplate,
    ActionTemplateNode,
    ArgumentSpec,
    ArgumentType,
    DelegationNode,
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

pytestmark = pytest.mark.security


def _fixture_with_delegation() -> tuple[Plan, OperationCatalogue]:
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
    delegation = DelegationNode("delegate", "scope-text", source, ())
    return (
        Plan("plan-with-delegation", "repair", (action, delegation), source),
        OperationCatalogue((operation,)),
    )


def test_delegation_node_produces_ir_transitions() -> None:
    plan, catalogue = _fixture_with_delegation()
    abstraction = abstract_plan(
        plan,
        catalogue=catalogue,
        effect_summaries=(EffectSummary("write", True, True),),
        bound=4,
    )
    assert abstraction.supported
    assert abstraction.ir is not None
    transition_ids = {rule.id for rule in abstraction.ir.transitions}
    assert "plan-with-delegation:delegate" in transition_ids


def test_delegation_node_sets_authority_gained() -> None:
    plan, catalogue = _fixture_with_delegation()
    abstraction = abstract_plan(
        plan,
        catalogue=catalogue,
        effect_summaries=(EffectSummary("write", True, True),),
        bound=4,
    )
    assert abstraction.ir is not None
    state = initial_state(abstraction.ir)
    targets = dict(successors(abstraction.ir, state))
    delegate_target = targets["plan-with-delegation:delegate"]
    assert delegate_target["delegation_consumed"] is True
    assert delegate_target["delegation_authority_gained"] is True


def test_delegation_authority_invariant_exists() -> None:
    plan, catalogue = _fixture_with_delegation()
    abstraction = abstract_plan(
        plan,
        catalogue=catalogue,
        effect_summaries=(EffectSummary("write", True, True),),
        bound=4,
    )
    assert abstraction.ir is not None
    inv_ids = {inv.id for inv in abstraction.ir.invariants}
    assert "delegation-authority-requires-grant" in inv_ids


def test_revocation_propagation_invariant_exists() -> None:
    principal = Principal("alice", "Alice")
    source = Provenance.from_principal(principal, source="fixture")
    operation = OperationSchema(
        "filesystem.write",
        "1",
        "filesystem",
        "file",
        "write",
        WRITE,
        (ArgumentSpec("path", ArgumentType.STRING),),
        "path",
    )
    action = ActionTemplateNode(
        "write",
        ActionTemplate("write", operation.id, operation.version, (TemplateArgument("path", LiteralBinding("safe.txt", source)),)),
        source,
    )
    plan = Plan("plan-revocation", "repair", (action,), source)
    catalogue = OperationCatalogue((operation,))
    abstraction = abstract_plan(
        plan,
        catalogue=catalogue,
        effect_summaries=(EffectSummary("write", False, True),),
        bound=4,
    )
    assert abstraction.ir is not None
    inv_ids = {inv.id for inv in abstraction.ir.invariants}
    assert "revocation-propagation" in inv_ids


def test_bounded_liveness_invariant_exists() -> None:
    plan, catalogue = _fixture_with_delegation()
    abstraction = abstract_plan(
        plan,
        catalogue=catalogue,
        effect_summaries=(EffectSummary("write", True, True),),
        bound=4,
    )
    assert abstraction.ir is not None
    inv_ids = {inv.id for inv in abstraction.ir.invariants}
    assert "bounded-liveness" in inv_ids


def test_new_state_variables_exist() -> None:
    plan, catalogue = _fixture_with_delegation()
    abstraction = abstract_plan(
        plan,
        catalogue=catalogue,
        effect_summaries=(EffectSummary("write", True, True),),
        bound=4,
    )
    assert abstraction.ir is not None
    var_names = {v.name for v in abstraction.ir.variables}
    assert "delegation_consumed" in var_names
    assert "delegation_authority_gained" in var_names
    assert "authority_set" in var_names
    assert "revocation_received" in var_names
    assert "terminated" in var_names


def test_existing_plan_verification_still_works() -> None:
    principal = Principal("alice", "Alice")
    source = Provenance.from_principal(principal, source="fixture")
    operation = OperationSchema(
        "filesystem.write",
        "1",
        "filesystem",
        "file",
        "write",
        WRITE,
        (ArgumentSpec("path", ArgumentType.STRING), ArgumentSpec("content", ArgumentType.STRING)),
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
    plan = Plan("verified-plan", "repair", (action,), source)
    catalogue = OperationCatalogue((operation,))
    result = verify_plan(
        plan,
        catalogue=catalogue,
        effect_summaries=(EffectSummary("write", True, True),),
        bound=4,
    )
    assert result.verdict in (FormalVerdict.BOUNDED_SAFE, FormalVerdict.SAFE)
