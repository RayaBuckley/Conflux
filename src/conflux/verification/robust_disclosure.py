"""Robust disclosure verification (Zdancewic & Myers connection).

Robust declassification asks whether an attacker can manipulate what or
when trusted code declassifies.  Applied to Conflux, this becomes:

    An unauthorised influencing principal cannot cause a disclosure
    transition to fire.

This module models disclosure as IR transitions with influence guards
and verifies the robustness property using the existing reference
checker.  A safe model blocks disclosure when an unauthorised principal
has influence; a defective model allows attacker-controlled disclosure.

SEM-RD-1: Robust disclosure is a safety property checkable on individual
traces: no reachable state has an executed disclosure transition caused
by an unauthorised influencer.

SEM-RD-2: A defective disclosure rule where attacker influence can
trigger disclosure must produce an UNSAFE verdict with a minimal
counterexample.

Connection to classical literature: Zdancewic & Myers, Robust
Declassification (2001); Askarov & Myers, Attacker Control and Impact.
"""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import fingerprint

from .ir import (
    Assignment,
    Expression,
    ExpressionKind,
    SafetyInvariant,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
)
from .reduction import reference_safety_check
from .results import FormalVerdict

ROBUST_DISCLOSURE_SCHEMA_VERSION = "1"


def _const(value: bool | int) -> Expression:
    return Expression.constant(value)


def _var(name: str) -> Expression:
    return Expression.variable(name)


def _not(expr: Expression) -> Expression:
    return Expression.operator(ExpressionKind.NOT, expr)


def _and(*exprs: Expression) -> Expression:
    return Expression.operator(ExpressionKind.AND, *exprs)


def _or(*exprs: Expression) -> Expression:
    return Expression.operator(ExpressionKind.OR, *exprs)


@dataclass(frozen=True, slots=True)
class RobustDisclosureResult:
    """Outcome of a robust-disclosure verification check.

    Attributes:
        model_id: identifier of the IR model checked.
        verdict: SAFE, BOUNDED_SAFE, UNSAFE, or UNKNOWN.
        robust: whether the disclosure is robust (no attacker-controlled
            disclosure is reachable).
        counterexample: shortest violation trace, if any.
    """

    model_id: str
    verdict: FormalVerdict
    robust: bool
    counterexample: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        """Serialise this robust disclosure result to a JSON-compatible dictionary."""
        return {
            "schema_version": ROBUST_DISCLOSURE_SCHEMA_VERSION,
            "model_id": self.model_id,
            "verdict": self.verdict.value,
            "robust": self.robust,
            "counterexample": list(self.counterexample),
        }


def robust_disclosure_ir() -> VerificationIR:
    """A safe disclosure model where attacker influence blocks disclosure.

    The model has three steps:
    1. The agent may consume attacker-controlled data.
    2. A trusted principal may request disclosure of a secret.
    3. The disclosure transition fires only when the requester is
       authorised AND no unauthorised influencer is in context.

    Variables:
        consumed_attacker: whether attacker data entered the context.
        disclosure_requested: whether a trusted principal requested
            disclosure.
        disclosed: whether the secret was disclosed.
        unauthorised_disclosure: whether disclosure occurred while an
            unauthorised influencer was in context.
        requester_authorised: whether the requester is authorised (True).
        attacker_authorised: whether the attacker is authorised (False).

    The robust disclosure invariant: no unauthorised disclosure occurs.

    This model should be SAFE.
    """
    return VerificationIR(
        id="robust-disclosure",
        variables=(
            StateVariable("consumed_attacker", Sort.BOOLEAN, False),
            StateVariable("disclosure_requested", Sort.BOOLEAN, False),
            StateVariable("disclosed", Sort.BOOLEAN, False),
            StateVariable("unauthorised_disclosure", Sort.BOOLEAN, False),
            StateVariable("requester_authorised", Sort.BOOLEAN, True),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
        ),
        transitions=(
            TransitionRule(
                "consume-attacker-data",
                _const(True),
                (Assignment("consumed_attacker", _const(True)),),
            ),
            TransitionRule(
                "request-disclosure",
                _const(True),
                (Assignment("disclosure_requested", _const(True)),),
            ),
            TransitionRule(
                "robust-disclosure-grants",
                _and(
                    _var("disclosure_requested"),
                    _var("requester_authorised"),
                    _not(_var("consumed_attacker")),
                ),
                (
                    Assignment("disclosed", _const(True)),
                    Assignment("unauthorised_disclosure", _const(False)),
                ),
            ),
            TransitionRule(
                "robust-disclosure-blocks-attacker",
                _and(
                    _var("disclosure_requested"),
                    _var("consumed_attacker"),
                    _not(_var("attacker_authorised")),
                ),
                (
                    Assignment("disclosed", _const(False)),
                    Assignment("unauthorised_disclosure", _const(False)),
                ),
            ),
        ),
        invariants=(
            SafetyInvariant(
                "no-unauthorised-disclosure",
                _not(_var("unauthorised_disclosure")),
                "Robust disclosure: no secret is disclosed when an unauthorised influencer is in the Principal Context",
            ),
        ),
        bound=5,
        assumptions=(
            "robust disclosure model: disclosure requires authorised requester",
            "disclosure is blocked when attacker is in context",
            "connects to Zdancewic & Myers robust declassification",
        ),
    )


def defective_disclosure_ir() -> VerificationIR:
    """A defective disclosure model where attacker influence can trigger disclosure.

    This model has the same structure as the robust model, but the
    disclosure transition does not check for attacker influence.  When
    the agent has consumed attacker data and disclosure is requested,
    the disclosure fires regardless of the attacker's authorisation.

    This creates a robust-disclosure violation: an attacker who
    influences the agent can cause a disclosure that the trusted
    requester intended, but which should not have occurred under
    attacker influence.

    This model should be UNSAFE.
    """
    return VerificationIR(
        id="defective-disclosure",
        variables=(
            StateVariable("consumed_attacker", Sort.BOOLEAN, False),
            StateVariable("disclosure_requested", Sort.BOOLEAN, False),
            StateVariable("disclosed", Sort.BOOLEAN, False),
            StateVariable("unauthorised_disclosure", Sort.BOOLEAN, False),
            StateVariable("requester_authorised", Sort.BOOLEAN, True),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
        ),
        transitions=(
            TransitionRule(
                "consume-attacker-data",
                _const(True),
                (Assignment("consumed_attacker", _const(True)),),
            ),
            TransitionRule(
                "request-disclosure",
                _const(True),
                (Assignment("disclosure_requested", _const(True)),),
            ),
            TransitionRule(
                "defective-disclosure-grants",
                _and(
                    _var("disclosure_requested"),
                    _var("requester_authorised"),
                ),
                (
                    Assignment("disclosed", _const(True)),
                    Assignment(
                        "unauthorised_disclosure",
                        _and(
                            _var("consumed_attacker"),
                            _not(_var("attacker_authorised")),
                        ),
                    ),
                ),
            ),
        ),
        invariants=(
            SafetyInvariant(
                "no-unauthorised-disclosure",
                _not(_var("unauthorised_disclosure")),
                "Robust disclosure: no secret is disclosed when an unauthorised influencer is in the Principal Context",
            ),
        ),
        bound=5,
        assumptions=(
            "defective disclosure model: disclosure ignores attacker influence",
            "the requester is authorised but disclosure should not occur when an unauthorised influencer is in context",
        ),
    )


def verify_robust_disclosure(ir: VerificationIR) -> RobustDisclosureResult:
    """Check the robust disclosure property on a verification IR.

    Returns a RobustDisclosureResult with the verdict and
    counterexample (if any).
    """
    ref = reference_safety_check(ir)
    return RobustDisclosureResult(
        model_id=ir.id,
        verdict=ref.verdict,
        robust=ref.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE),
        counterexample=ref.counterexample,
    )


def run_robust_disclosure_experiment() -> dict[str, object]:
    """Run the full robust-disclosure experiment.

    Checks both the robust (safe) and defective (unsafe) models and
    returns a JSON-compatible summary.
    """
    robust_ir = robust_disclosure_ir()
    defective_ir = defective_disclosure_ir()

    robust_result = verify_robust_disclosure(robust_ir)
    defective_result = verify_robust_disclosure(defective_ir)

    return {
        "schema_version": ROBUST_DISCLOSURE_SCHEMA_VERSION,
        "robust_model": robust_result.to_dict(),
        "defective_model": defective_result.to_dict(),
        "summary": {
            "robust_is_safe": robust_result.robust,
            "defective_is_unsafe": defective_result.verdict == FormalVerdict.UNSAFE,
            "defective_has_counterexample": len(defective_result.counterexample) > 0,
        },
        "fingerprint": fingerprint(
            {
                "robust_verdict": robust_result.verdict.value,
                "defective_verdict": defective_result.verdict.value,
            }
        ),
    }


__all__ = [
    "ROBUST_DISCLOSURE_SCHEMA_VERSION",
    "RobustDisclosureResult",
    "defective_disclosure_ir",
    "robust_disclosure_ir",
    "run_robust_disclosure_experiment",
    "verify_robust_disclosure",
]
