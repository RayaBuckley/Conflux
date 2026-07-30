"""Hard-security plan selection and authenticated outcome contracts."""

from __future__ import annotations

from conflux.domain import Principal, Provenance
from conflux.planning import (
    CandidateSecurity,
    Plan,
    PlanCandidate,
    TerminalNode,
    TerminalOutcome,
    select_plan,
)


def plan(identifier: str) -> Plan:
    principal = Principal("alice", "Alice")
    provenance = Provenance.from_principal(principal, source="fixture")
    return Plan(
        identifier,
        "repair",
        (
            TerminalNode(
                "done",
                TerminalOutcome.SUCCEEDED,
                "done",
                provenance,
            ),
        ),
        provenance,
    )


def candidate(
    identifier: str,
    *,
    security: CandidateSecurity = CandidateSecurity.SAFE,
    utility: float = 1.0,
    authority: frozenset[str] = frozenset({"write:safe"}),
    sensitive: int = 0,
    cost: float = 1.0,
    irreversible: int = 0,
) -> PlanCandidate:
    return PlanCandidate(
        plan(identifier),
        security,
        utility,
        authority,
        sensitive,
        cost,
        irreversible,
    )


def test_unsafe_and_unknown_candidates_never_satisfy_hard_constraint() -> None:
    selection = select_plan(
        (
            candidate(
                "unknown-high-utility",
                security=CandidateSecurity.UNKNOWN,
                utility=100.0,
            ),
            candidate(
                "unsafe-high-utility",
                security=CandidateSecurity.UNSAFE,
                utility=100.0,
            ),
            candidate("safe", utility=0.1),
        )
    )
    assert selection.selected is not None
    assert selection.selected.plan.id == "safe"
    assert selection.excluded == (
        ("unknown-high-utility", "hard_security_constraint:unknown"),
        ("unsafe-high-utility", "hard_security_constraint:unsafe"),
    )


def test_selection_minimises_authority_after_security_and_utility() -> None:
    selection = select_plan(
        (
            candidate(
                "broad",
                utility=2.0,
                authority=frozenset({"read:a", "read:b"}),
            ),
            candidate(
                "narrow",
                utility=2.0,
                authority=frozenset({"read:a"}),
            ),
            candidate(
                "bounded",
                security=CandidateSecurity.BOUNDED_SAFE,
                utility=100.0,
                authority=frozenset(),
            ),
        ),
        include_ablation=True,
    )
    assert selection.selected is not None
    assert selection.selected.plan.id == "narrow"
    assert selection.ranked_plan_ids == ("narrow", "broad", "bounded")
    assert len(selection.ablation) == 5
    assert selection.to_dict() == selection.to_dict()


def test_tie_breaking_uses_stable_plan_fingerprint() -> None:
    first = candidate("a")
    second = candidate("b")
    forward = select_plan((first, second))
    reverse = select_plan((second, first))
    assert forward.ranked_plan_ids == reverse.ranked_plan_ids
    assert forward.selected is not None and reverse.selected is not None
    assert forward.selected.plan.fingerprint == reverse.selected.plan.fingerprint


def test_no_eligible_candidate_returns_explicit_empty_selection() -> None:
    selection = select_plan(
        (candidate("unknown", security=CandidateSecurity.UNKNOWN),)
    )
    assert selection.selected is None
    assert selection.ranked_plan_ids == ()
