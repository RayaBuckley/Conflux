"""Endorsement / trusted-transform verification models.

Endorsement is the integrity-side counterpart to declassification:
untrusted information is deliberately accepted as sufficiently
trustworthy.  In Conflux, endorsement would allow provenance to be
*reduced* under explicit authority conditions — the only exception to
monotonic provenance accumulation.

This module models endorsement as verification IR transitions to
formalise the soundness conditions and test them against defective
controls.  It does not change the ITES kernel or runtime security
semantics (per plan Decision 2).

SEM-END-1 (Endorsement soundness): An endorsement transition is sound
only when:
  (a) the endorser is authorised to endorse;
  (b) the endorsed information meets a trust threshold; and
  (c) the endorsement is auditable.

SEM-END-2 (Nonmalleability): An attacker cannot exploit endorsement to
remove their own influence from the Principal Context.  A defective
endorsement that allows attacker-controlled removal must produce an
UNSAFE verdict.

Connection to classical literature: Cecchetti, Myers & Arden,
Nonmalleable Information Flow (2017); Askarov & Myers, Attacker Control
and Impact.
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

ENDORSEMENT_SCHEMA_VERSION = "1"


def _const(value: bool | int | str) -> Expression:
    return Expression.constant(value)


def _var(name: str) -> Expression:
    return Expression.variable(name)


def _not(expr: Expression) -> Expression:
    return Expression.operator(ExpressionKind.NOT, expr)


def _and(*exprs: Expression) -> Expression:
    return Expression.operator(ExpressionKind.AND, *exprs)


@dataclass(frozen=True, slots=True)
class EndorsementResult:
    """Outcome of an endorsement verification check.

    Attributes:
        model_id: identifier of the IR model checked.
        verdict: SAFE, BOUNDED_SAFE, UNSAFE, or UNKNOWN.
        sound: whether the endorsement is sound.
        counterexample: shortest violation trace, if any.
    """

    model_id: str
    verdict: FormalVerdict
    sound: bool
    counterexample: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        """Serialise this endorsement result to a JSON-compatible dictionary."""
        return {
            "schema_version": ENDORSEMENT_SCHEMA_VERSION,
            "model_id": self.model_id,
            "verdict": self.verdict.value,
            "sound": self.sound,
            "counterexample": list(self.counterexample),
        }


def sound_endorsement_ir() -> VerificationIR:
    """A sound endorsement model with authorised endorser and trust threshold.

    The model has three steps:
    1. The agent consumes attacker-controlled data (PC grows).
    2. An authorised endorser verifies the data and endorses it,
       reducing the PC back to the requester only.  This transition
       requires endorser_authorised=True.
    3. The agent executes an action under the reduced context.

    The endorsement invariant: the PC never contains the attacker after
    endorsement, and endorsement only occurs when the endorser is
    authorised.

    This model should be SAFE.
    """
    return VerificationIR(
        id="sound-endorsement",
        variables=(
            StateVariable("consumed_attacker", Sort.BOOLEAN, False),
            StateVariable("endorsed", Sort.BOOLEAN, False),
            StateVariable("endorser_authorised", Sort.BOOLEAN, True),
            StateVariable("attacker_in_pc", Sort.BOOLEAN, False),
            StateVariable("action_executed", Sort.BOOLEAN, False),
            StateVariable("pe_violation", Sort.BOOLEAN, False),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
        ),
        transitions=(
            TransitionRule(
                "consume-attacker-data",
                _const(True),
                (
                    Assignment("consumed_attacker", _const(True)),
                    Assignment("attacker_in_pc", _const(True)),
                ),
            ),
            TransitionRule(
                "endorser-removes-attacker",
                _and(
                    _var("consumed_attacker"),
                    _var("endorser_authorised"),
                ),
                (
                    Assignment("endorsed", _const(True)),
                    Assignment("attacker_in_pc", _const(False)),
                ),
            ),
            TransitionRule(
                "execute-after-endorsement",
                _and(
                    _var("endorsed"),
                    _not(_var("attacker_in_pc")),
                ),
                (
                    Assignment("action_executed", _const(True)),
                    Assignment("pe_violation", _const(False)),
                ),
            ),
        ),
        invariants=(
            SafetyInvariant(
                "no-pe-violation",
                _not(_var("pe_violation")),
                "PE: no action executed with an unauthorised influencer",
            ),
            SafetyInvariant(
                "endorsement-requires-authorised-endorser",
                _not(
                    _and(
                        _var("endorsed"),
                        _not(_var("endorser_authorised")),
                    )
                ),
                "Endorsement requires an authorised endorser",
            ),
        ),
        bound=5,
        assumptions=(
            "sound endorsement: endorser is authorised, trust threshold met",
            "endorsement removes attacker from PC",
            "connects to Cecchetti et al. nonmalleable IFC",
        ),
    )


def defective_endorsement_ir() -> VerificationIR:
    """A defective endorsement model where attacker can exploit endorsement.

    The endorsement transition fires regardless of endorser authority.
    An attacker who influences the agent can trigger endorsement to
    remove their own influence from the PC, then execute actions that
    would otherwise be blocked.

    This violates nonmalleability: the attacker controls the endorsement
    to escape their own contamination.

    This model should be UNSAFE.
    """
    return VerificationIR(
        id="defective-endorsement",
        variables=(
            StateVariable("consumed_attacker", Sort.BOOLEAN, False),
            StateVariable("endorsed", Sort.BOOLEAN, False),
            StateVariable("endorser_authorised", Sort.BOOLEAN, True),
            StateVariable("attacker_in_pc", Sort.BOOLEAN, False),
            StateVariable("action_executed", Sort.BOOLEAN, False),
            StateVariable("pe_violation", Sort.BOOLEAN, False),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
        ),
        transitions=(
            TransitionRule(
                "consume-attacker-data",
                _const(True),
                (
                    Assignment("consumed_attacker", _const(True)),
                    Assignment("attacker_in_pc", _const(True)),
                ),
            ),
            TransitionRule(
                "defective-endorsement-removes-attacker",
                _var("consumed_attacker"),
                (
                    Assignment("endorsed", _const(True)),
                    Assignment("attacker_in_pc", _const(False)),
                    Assignment(
                        "pe_violation",
                        _and(
                            _var("action_executed"),
                            _var("consumed_attacker"),
                            _not(_var("attacker_authorised")),
                        ),
                    ),
                ),
            ),
            TransitionRule(
                "execute-after-defective-endorsement",
                _and(
                    _var("endorsed"),
                    _not(_var("attacker_in_pc")),
                ),
                (
                    Assignment("action_executed", _const(True)),
                    Assignment(
                        "pe_violation",
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
                "no-pe-violation",
                _not(_var("pe_violation")),
                "PE: no action executed with an unauthorised influencer",
            ),
            SafetyInvariant(
                "endorsement-requires-authorised-endorser",
                _not(
                    _and(
                        _var("endorsed"),
                        _not(_var("endorser_authorised")),
                    )
                ),
                "Endorsement requires an authorised endorser",
            ),
        ),
        bound=5,
        assumptions=(
            "defective endorsement: endorsement fires without endorser authority",
            "attacker can exploit endorsement to remove their own influence",
        ),
    )


def verify_endorsement(ir: VerificationIR) -> EndorsementResult:
    """Check the endorsement soundness property on a verification IR."""
    ref = reference_safety_check(ir)
    return EndorsementResult(
        model_id=ir.id,
        verdict=ref.verdict,
        sound=ref.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE),
        counterexample=ref.counterexample,
    )


def run_endorsement_experiment() -> dict[str, object]:
    """Run the full endorsement experiment with safe and defective models."""
    safe_ir = sound_endorsement_ir()
    defective_ir = defective_endorsement_ir()

    safe_result = verify_endorsement(safe_ir)
    defective_result = verify_endorsement(defective_ir)

    return {
        "schema_version": ENDORSEMENT_SCHEMA_VERSION,
        "safe_model": safe_result.to_dict(),
        "defective_model": defective_result.to_dict(),
        "summary": {
            "safe_is_sound": safe_result.sound,
            "defective_is_unsafe": defective_result.verdict == FormalVerdict.UNSAFE,
            "defective_has_counterexample": len(defective_result.counterexample) > 0,
        },
        "fingerprint": fingerprint(
            {
                "safe_verdict": safe_result.verdict.value,
                "defective_verdict": defective_result.verdict.value,
            }
        ),
    }


__all__ = [
    "ENDORSEMENT_SCHEMA_VERSION",
    "EndorsementResult",
    "defective_endorsement_ir",
    "run_endorsement_experiment",
    "sound_endorsement_ir",
    "verify_endorsement",
]
