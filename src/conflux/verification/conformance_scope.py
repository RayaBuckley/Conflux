"""The supported subset of the runtime-to-IR conformance path (limit L3).

A formal verdict for a dynamic plan passes two translation steps:

1. ``plan_ir.abstract_plan`` translates the plan into the finite delegation IR
   and returns ``PlanAbstraction.unsupported`` naming every plan feature it
   could not model.
2. ``plan_ir.verify_plan`` dispatches the abstracted IR to a backend.

Outside that subset the path answers ``FormalVerdict.UNKNOWN``; it never answers
safely for a feature it cannot model.  This module states the boundary as data,
so a reader can check it without reading the two implementations, and so a new
unsupported feature cannot be added without declaring it here.

The runtime side of the comparison is ``interpreter.differential_conformance``.
That check is boolean: a runtime record that is not a transition of the
abstracted IR is a mismatch, not an UNKNOWN.  The two outcomes are recorded
separately rather than left to the reader.

The ledger row for unbounded deployment stays ``Not claimed``
(``docs/evidence/CLAIMS.md``).  ``unbounded_deployment_row`` carries that row so
the code and the ledger share one source.
"""

from __future__ import annotations

from dataclasses import dataclass

from .plan_ir import (
    UNSUPPORTED_MISSING_EFFECT_SUMMARY,
    UNSUPPORTED_PLAN_ABSTRACTION,
    UNSUPPORTED_UNKNOWN_OPERATION,
    UNSUPPORTED_VERIFICATION_BACKEND,
)


@dataclass(frozen=True, slots=True)
class ScopeEntry:
    """One boundary entry: a feature outside the supported subset and its outcome."""

    feature: str
    code: str
    where: str
    outcome: str
    detail: str


UNSUPPORTED_SCOPE: tuple[ScopeEntry, ...] = (
    ScopeEntry(
        feature="a plan node whose operation id and version the catalogue cannot resolve",
        code=UNSUPPORTED_UNKNOWN_OPERATION,
        where="plan_ir.abstract_plan",
        outcome="UNKNOWN",
        detail=(
            "the abstraction records '<rule id>:unknown_operation' and returns no IR, so verify_plan"
            " reports " + UNSUPPORTED_PLAN_ABSTRACTION
        ),
    ),
    ScopeEntry(
        feature="a plan node with no recorded effect summary",
        code=UNSUPPORTED_MISSING_EFFECT_SUMMARY,
        where="plan_ir.abstract_plan",
        outcome="UNKNOWN",
        detail=(
            "the abstraction records '<rule id>:missing_effect_summary' and returns no IR, so verify_plan"
            " reports " + UNSUPPORTED_PLAN_ABSTRACTION
        ),
    ),
    ScopeEntry(
        feature="a backend the dispatcher does not know",
        code=UNSUPPORTED_VERIFICATION_BACKEND,
        where="plan_ir.verify_plan",
        outcome="UNKNOWN",
        detail=("the IR is abstracted, then the dispatcher returns UNKNOWN with '" + UNSUPPORTED_VERIFICATION_BACKEND + ":<name>'"),
    ),
)

MISMATCH_SCOPE: tuple[ScopeEntry, ...] = (
    ScopeEntry(
        feature="a runtime transition record that is not a transition of the abstracted IR",
        code="differential_conformance",
        where="interpreter.differential_conformance",
        outcome="mismatch",
        detail="the check is boolean: a record outside the IR is a mismatch, not an UNKNOWN",
    ),
)

UNSUPPORTED_CODES: frozenset[str] = frozenset(entry.code for entry in UNSUPPORTED_SCOPE)
UNSUPPORTED_ERROR_PREFIXES: tuple[str, ...] = (
    UNSUPPORTED_PLAN_ABSTRACTION,
    UNSUPPORTED_VERIFICATION_BACKEND,
)


@dataclass(frozen=True, slots=True)
class LedgerRow:
    """A claim, its recorded status, and the reason recorded beside it."""

    claim: str
    status: str
    reason: str


def unbounded_deployment_row() -> LedgerRow:
    """Return the unbounded-deployment ledger row that this boundary supports."""
    return LedgerRow(
        claim="Conflux is secure for unbounded deployments",
        status="Not claimed",
        reason="finite bounds and abstractions do not prove unbounded deployments",
    )


__all__ = [
    "MISMATCH_SCOPE",
    "UNSUPPORTED_CODES",
    "UNSUPPORTED_ERROR_PREFIXES",
    "UNSUPPORTED_SCOPE",
    "LedgerRow",
    "ScopeEntry",
    "unbounded_deployment_row",
]
