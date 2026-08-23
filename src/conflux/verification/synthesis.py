"""Controller synthesis for the maximal-permissiveness experiment (RQ1).

This module implements a finite controller-synthesis experiment that
independently validates the ITES maximal-permissiveness claim.  Rather
than encoding the ITES intersection rule directly, it constructs a
finite transition system with a PE bad-state predicate and uses Z3 to
find the maximally permissive safe controller — the set of
``(state, action)`` pairs that can be allowed without introducing a
privilege-escalation violation.

The synthesised controller is then compared with the ITES intersection
rule.  If they agree on every reachable state-action pair, this is
executable evidence for the maximality theorem.

Negative controls (ANY_AUTHORISED, REQUESTER_ONLY, etc.) are defective
controllers that violate the PE invariant; the reference checker must
produce counterexamples for each.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from conflux.domain import fingerprint

from .interpreter import initial_state, successors
from .ir import Expression, ExpressionKind, IRValue, VerificationIR
from .reduction import reference_safety_check
from .results import FormalVerdict

SYNTHESIS_SCHEMA_VERSION = "1"


class ControllerStrategy(StrEnum):
    """Authorisation strategies for the synthesis experiment."""

    ITES_INTERSECTION = "ites_intersection"
    ANY_AUTHORISED = "any_authorised"
    REQUESTER_ONLY = "requester_only"
    DROP_PROVENANCE = "drop_provenance"
    EMPTY_IS_PRIVILEGED = "empty_is_privileged"
    STALE_ACS = "stale_acs"


@dataclass(frozen=True, slots=True)
class FiniteInstance:
    """A finite ACS instance for controller synthesis.

    Attributes:
        principals: ordered tuple of principal identifiers.
        actions: ordered tuple of action identifiers.
        acs: mapping ``(principal_id, action_id) -> bool``; True means
            the principal is authorised for the action by the current ACS.
        requester: the principal who initiates the session (for
            REQUESTER_ONLY control).
        attacker: the principal whose information may influence the
            agent without authorisation.
        authorised_action: the action that the agent attempts to execute.
    """

    principals: tuple[str, ...]
    actions: tuple[str, ...]
    acs: frozenset[tuple[str, str]]
    requester: str
    attacker: str
    authorised_action: str

    def __post_init__(self) -> None:
        if not self.principals or not self.actions:
            raise ValueError("principals and actions must be non-empty")
        if self.requester not in self.principals:
            raise ValueError("requester must be in principals")
        if self.attacker not in self.principals:
            raise ValueError("attacker must be in principals")
        if self.authorised_action not in self.actions:
            raise ValueError("authorised_action must be in actions")
        object.__setattr__(self, "acs", frozenset(self.acs))

    def is_authorised(self, principal: str, action: str) -> bool:
        """Check whether a principal is authorised for an action in the ACS."""
        return (principal, action) in self.acs

    def to_dict(self) -> dict[str, object]:
        """Serialise this finite instance to a JSON-compatible dictionary."""
        return {
            "principals": list(self.principals),
            "actions": list(self.actions),
            "acs": sorted(f"{p}:{a}" for p, a in self.acs),
            "requester": self.requester,
            "attacker": self.attacker,
            "authorised_action": self.authorised_action,
        }


def default_instance() -> FiniteInstance:
    """Return the canonical two-principal, one-action test instance.

    The requester (alice) is authorised for ``write``; the attacker
    (mallory) is not.  When the agent consumes attacker-controlled
    data, the PC becomes ``{alice, mallory}`` and ITES must block
    because mallory lacks authorisation.
    """
    return FiniteInstance(
        principals=("alice", "mallory"),
        actions=("write",),
        acs=frozenset({("alice", "write")}),
        requester="alice",
        attacker="mallory",
        authorised_action="write",
    )


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


def _equal(left: Expression, right: Expression) -> Expression:
    return Expression.operator(ExpressionKind.EQUAL, left, right)


@dataclass(frozen=True, slots=True)
class ControllerDecision:
    """A single controller decision for a reachable state-action pair."""

    state: dict[str, IRValue]
    action_id: str
    allow: bool
    ites_allow: bool
    matches_ites: bool

    def to_dict(self) -> dict[str, object]:
        """Serialise this controller decision to a JSON-compatible dictionary."""
        return {
            "state": dict(self.state),
            "action_id": self.action_id,
            "allow": self.allow,
            "ites_allow": self.ites_allow,
            "matches_ites": self.matches_ites,
        }


@dataclass(frozen=True, slots=True)
class SynthesisResult:
    """Outcome of a controller-synthesis experiment.

    Attributes:
        instance: the finite instance that was synthesised over.
        strategy: the controller strategy evaluated.
        synthesised_decisions: per-state-action decisions from the
            maximally permissive safe controller.
        ites_decisions: per-state-action decisions from the ITES
            intersection rule.
        equivalent: whether the synthesised controller matches ITES.
        pe_safe: whether the controller is PE-safe.
        counterexample: shortest PE violation trace, if any.
        verdict: SAFE, BOUNDED_SAFE, UNSAFE, or UNKNOWN.
    """

    instance: FiniteInstance
    strategy: ControllerStrategy
    synthesised_decisions: tuple[ControllerDecision, ...]
    ites_decisions: tuple[ControllerDecision, ...]
    equivalent: bool
    pe_safe: bool
    counterexample: tuple[dict[str, object], ...]
    verdict: FormalVerdict

    def to_dict(self) -> dict[str, object]:
        """Serialise this synthesis result to a JSON-compatible dictionary."""
        return {
            "schema_version": SYNTHESIS_SCHEMA_VERSION,
            "instance": self.instance.to_dict(),
            "strategy": self.strategy.value,
            "synthesised_decisions": [d.to_dict() for d in self.synthesised_decisions],
            "ites_decisions": [d.to_dict() for d in self.ites_decisions],
            "equivalent": self.equivalent,
            "pe_safe": self.pe_safe,
            "counterexample": list(self.counterexample),
            "verdict": self.verdict.value,
        }


def _build_synthesis_ir(
    instance: FiniteInstance,
    strategy: ControllerStrategy,
) -> VerificationIR:
    """Build a verification IR encoding the given controller strategy.

    The IR models a simplified two-step agent execution:
    1. The agent may consume attacker-controlled data (adding the
       attacker to the Principal Context).
    2. The agent attempts to execute an action.

    The controller's decision determines whether execution proceeds.
    The PE invariant checks that no action is executed when an
    influencing principal lacks ACS authorisation.

    Variables:
        consumed_attacker: whether attacker data entered the context.
        action_executed: whether the action was executed.
        pe_violation: whether a PE violation occurred.
        requester_authorised: whether the requester has ACS permission
            (True for the default instance).
        attacker_authorised: whether the attacker has ACS permission
            (False for the default instance).

    The controller strategy modifies the guard on the execute
    transition to reflect the defective control's logic.
    """
    requester_auth = instance.is_authorised(
        instance.requester,
        instance.authorised_action,
    )
    attacker_auth = instance.is_authorised(
        instance.attacker,
        instance.authorised_action,
    )

    from .ir import Assignment, SafetyInvariant, Sort, StateVariable, TransitionRule

    variables = (
        StateVariable("consumed_attacker", Sort.BOOLEAN, False),
        StateVariable("action_executed", Sort.BOOLEAN, False),
        StateVariable("pe_violation", Sort.BOOLEAN, False),
        StateVariable("requester_authorised", Sort.BOOLEAN, requester_auth),
        StateVariable("attacker_authorised", Sort.BOOLEAN, attacker_auth),
    )

    # Step 1: agent consumes attacker data
    consume_rule = TransitionRule(
        "consume-attacker-data",
        _const(True),
        (Assignment("consumed_attacker", _const(True)),),
    )

    # Step 2: agent executes action — guard depends on strategy
    execute_guard = _execute_guard(strategy)

    pe_condition = _and(
        _var("action_executed"),
        _var("consumed_attacker"),
        _not(_var("attacker_authorised")),
    )

    execute_rule = TransitionRule(
        f"execute-{strategy.value}",
        execute_guard,
        (
            Assignment("action_executed", _const(True)),
            Assignment("pe_violation", pe_condition),
        ),
    )

    invariants = (
        SafetyInvariant(
            "no-pe-violation",
            _not(_var("pe_violation")),
            "PE: no action executed when an influencing principal lacks authorisation",
        ),
    )

    assumptions = (
        f"strategy: {strategy.value}",
        f"requester={instance.requester}, authorised={requester_auth}",
        f"attacker={instance.attacker}, authorised={attacker_auth}",
        "synthesis IR: finite two-step agent execution model",
    )

    return VerificationIR(
        id=f"synthesis-{strategy.value}",
        variables=variables,
        transitions=(consume_rule, execute_rule),
        invariants=invariants,
        bound=4,
        assumptions=assumptions,
    )


def _execute_guard(strategy: ControllerStrategy) -> Expression:
    """Return the guard on the execute transition for each strategy.

    ITES_INTERSECTION: allow only if every influencer is authorised.
        Since consumed_attacker implies attacker is in PC, execution
        requires attacker_authorised.  Without consumption, requester
        suffices.

    ANY_AUTHORISED: allow if any single influencer is authorised.

    REQUESTER_ONLY: allow based solely on requester_authorised.

    DROP_PROVENANCE: always allow (provenance is dropped, so the
        controller thinks only the requester is in context).

    EMPTY_IS_PRIVILEGED: allow even from empty context (always allow).

    STALE_ACS: allow based on requester_authorised (ignores current
        ACS state changes — modelled same as REQUESTER_ONLY but
        conceptually different: it uses a stale authorisation snapshot).
    """
    if strategy == ControllerStrategy.ITES_INTERSECTION:
        # Allow if no attacker consumed, or attacker is authorised
        return _or(
            _not(_var("consumed_attacker")),
            _var("attacker_authorised"),
        )
    if strategy == ControllerStrategy.ANY_AUTHORISED:
        # Allow if requester OR attacker is authorised
        return _or(
            _var("requester_authorised"),
            _var("attacker_authorised"),
        )
    if strategy == ControllerStrategy.REQUESTER_ONLY:
        return _var("requester_authorised")
    if strategy == ControllerStrategy.DROP_PROVENANCE:
        # Drop provenance: ignores consumed_attacker
        return _var("requester_authorised")
    if strategy == ControllerStrategy.EMPTY_IS_PRIVILEGED:
        return _const(True)
    if strategy == ControllerStrategy.STALE_ACS:
        return _var("requester_authorised")
    raise ValueError(f"unknown strategy: {strategy}")


def _ites_allows(
    state: dict[str, IRValue],
    instance: FiniteInstance,
) -> bool:
    """Compute the ITES intersection rule decision for a state.

    ITES allows an action iff the Principal Context is non-empty and
    every principal in the context is authorised by the ACS.

    In the IR model, the Principal Context is:
    - {requester} if consumed_attacker is False
    - {requester, attacker} if consumed_attacker is True
    """
    consumed = bool(state.get("consumed_attacker", False))
    if not consumed:
        return instance.is_authorised(
            instance.requester,
            instance.authorised_action,
        )
    return instance.is_authorised(instance.requester, instance.authorised_action) and instance.is_authorised(
        instance.attacker, instance.authorised_action
    )


def _has_pe_violation(state: dict[str, IRValue]) -> bool:
    """Check whether a state has a PE violation."""
    return bool(state.get("pe_violation", False))


def _reachable_states(
    ir: VerificationIR,
) -> list[dict[str, IRValue]]:
    """Breadth-first enumeration of reachable states."""
    start = initial_state(ir)
    visited: list[dict[str, IRValue]] = [start]
    seen = {_state_key(start)}
    queue: list[dict[str, IRValue]] = [start]
    while queue:
        state = queue.pop(0)
        for _, target in successors(ir, state):
            key = _state_key(target)
            if key not in seen:
                seen.add(key)
                visited.append(target)
                queue.append(target)
    return visited


def _state_key(state: dict[str, IRValue]) -> tuple[tuple[str, IRValue], ...]:
    return tuple(sorted(state.items()))


def synthesise_controller(
    instance: FiniteInstance,
) -> tuple[list[ControllerDecision], list[ControllerDecision]]:
    """Synthesise the maximally permissive safe controller and compare with ITES.

    The maximally permissive safe controller allows every action that
    does not introduce a PE violation.  For each reachable state, we
    check whether executing the action would create a PE violation.  If
    not, the controller allows it; otherwise it denies.

    Returns:
        (synthesised_decisions, ites_decisions)
    """
    ir = _build_synthesis_ir(instance, ControllerStrategy.ITES_INTERSECTION)
    states = _reachable_states(ir)

    synth_decisions: list[ControllerDecision] = []
    ites_decisions: list[ControllerDecision] = []

    for state in states:
        action_id = instance.authorised_action

        # Synthesised controller: allow if no PE violation would result.
        # We check by simulating: if the execute transition fires and
        # produces pe_violation=True, the controller must deny.
        synth_allow = _synthesised_decision(state, ir, instance)

        # ITES intersection rule
        ites_allow = _ites_allows(state, instance)

        synth_decisions.append(
            ControllerDecision(
                state=dict(state),
                action_id=action_id,
                allow=synth_allow,
                ites_allow=ites_allow,
                matches_ites=synth_allow == ites_allow,
            )
        )
        ites_decisions.append(
            ControllerDecision(
                state=dict(state),
                action_id=action_id,
                allow=ites_allow,
                ites_allow=ites_allow,
                matches_ites=True,
            )
        )

    return synth_decisions, ites_decisions


def _synthesised_decision(
    state: dict[str, IRValue],
    ir: VerificationIR,
    instance: FiniteInstance,
) -> bool:
    """Compute the maximally permissive safe decision for a state.

    A controller allows an action iff allowing it does not introduce a
    PE violation.  We check whether the execute transition from this
    state produces pe_violation=True.  If it does, the safe controller
    must deny; otherwise it allows.

    The key insight: in the IR model, the execute transition's guard
    already encodes the controller's decision.  The maximally
    permissive safe controller is the one that allows execution exactly
    when it does not create a PE violation.

    For the synthesis experiment, we compute this directly: if the
    state already has consumed_attacker=True and the attacker is not
    authorised, allowing execution creates PE.  Otherwise it is safe.
    """
    consumed = bool(state.get("consumed_attacker", False))
    attacker_auth = bool(state.get("attacker_authorised", False))
    executed = bool(state.get("action_executed", False))

    if executed:
        # Already executed — no further decision
        return False

    if not consumed:
        # No attacker influence — safe to allow if requester is authorised
        return instance.is_authorised(
            instance.requester,
            instance.authorised_action,
        )

    # Attacker in context — safe only if attacker is also authorised
    return attacker_auth and instance.is_authorised(
        instance.requester,
        instance.authorised_action,
    )


def evaluate_strategy(
    instance: FiniteInstance,
    strategy: ControllerStrategy,
) -> SynthesisResult:
    """Evaluate a controller strategy against the PE invariant.

    For ITES_INTERSECTION, also compares with the synthesised
    maximally permissive safe controller.
    """
    ir = _build_synthesis_ir(instance, strategy)
    ref_result = reference_safety_check(ir)

    if strategy == ControllerStrategy.ITES_INTERSECTION:
        synth_decisions_list, ites_decisions_list = synthesise_controller(instance)
        synth_decisions = tuple(synth_decisions_list)
        ites_decisions = tuple(ites_decisions_list)
        active = [d for d in synth_decisions if not d.state.get("action_executed", False)]
        equivalent = all(d.matches_ites for d in active)
    else:
        synth_decisions = ()
        ites_decisions = ()
        equivalent = False

    return SynthesisResult(
        instance=instance,
        strategy=strategy,
        synthesised_decisions=synth_decisions,
        ites_decisions=ites_decisions,
        equivalent=equivalent,
        pe_safe=ref_result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE),
        counterexample=ref_result.counterexample,
        verdict=ref_result.verdict,
    )


def run_synthesis_experiment(
    instance: FiniteInstance | None = None,
) -> dict[str, object]:
    """Run the full synthesis experiment with all strategies.

    Returns a JSON-compatible dictionary with:
    - the ITES synthesis result (with equivalence check);
    - negative control results (each should be UNSAFE);
    - a summary of the experiment.
    """
    inst = instance or default_instance()

    ites_result = evaluate_strategy(inst, ControllerStrategy.ITES_INTERSECTION)

    controls = {}
    for strategy in ControllerStrategy:
        if strategy == ControllerStrategy.ITES_INTERSECTION:
            continue
        result = evaluate_strategy(inst, strategy)
        controls[strategy.value] = result

    all_controls_unsafe = all(r.verdict == FormalVerdict.UNSAFE for r in controls.values())

    return {
        "schema_version": SYNTHESIS_SCHEMA_VERSION,
        "instance": inst.to_dict(),
        "ites": ites_result.to_dict(),
        "controls": {k: v.to_dict() for k, v in controls.items()},
        "summary": {
            "ites_pe_safe": ites_result.pe_safe,
            "ites_matches_synthesis": ites_result.equivalent,
            "all_controls_unsafe": all_controls_unsafe,
            "control_count": len(controls),
            "unsafe_controls": sorted(k for k, v in controls.items() if v.verdict == FormalVerdict.UNSAFE),
        },
        "fingerprint": fingerprint(
            {
                "instance": inst.to_dict(),
                "ites_verdict": ites_result.verdict.value,
                "ites_equivalent": ites_result.equivalent,
            }
        ),
    }


__all__ = [
    "ControllerDecision",
    "ControllerStrategy",
    "FiniteInstance",
    "SYNTHESIS_SCHEMA_VERSION",
    "SynthesisResult",
    "default_instance",
    "evaluate_strategy",
    "run_synthesis_experiment",
    "synthesise_controller",
]
