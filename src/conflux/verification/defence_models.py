"""Verification IR models of contemporary agent defence patterns.

Each factory returns a :class:`VerificationIR` that faithfully encodes the
defence's transition semantics for a small finite instance.  The models are
designed for comparative verification against the Conflux PE property:

    Executed(a) -> forall p in Influencers(a): ACSAllows(p, a)

A defence can satisfy its own intended property while violating PE because
it does not track per-principal provenance.
"""

from __future__ import annotations

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


def _not(expression: Expression) -> Expression:
    return Expression.operator(ExpressionKind.NOT, expression)


def _and(*expressions: Expression) -> Expression:
    return Expression.operator(ExpressionKind.AND, *expressions)


def _or(*expressions: Expression) -> Expression:
    return Expression.operator(ExpressionKind.OR, *expressions)


def _equal(left: Expression, right: Expression) -> Expression:
    return Expression.operator(ExpressionKind.EQUAL, left, right)


def _const(value: bool | int) -> Expression:
    return Expression.constant(value)


def _var(name: str) -> Expression:
    return Expression.variable(name)


def dual_llm_baseline_ir() -> VerificationIR:
    """Dual-LLM baseline: privileged planner + quarantined data processor.

    The Dual-LLM pattern separates control flow (privileged planner) from
    data processing (quarantined processor).  The planner decides which tool
    to call and with what arguments; the processor handles untrusted data
    but cannot directly invoke tools.

    The key security property (Q) is that the quarantined processor never
    directly executes effects — only the privileged planner can.

    **PE vulnerability:** The Dual-LLM model does not track which principals
    influenced the planner's decision.  If the planner consumes data from
    principal ``attacker`` and decides to execute an action, the action is
    performed even though ``attacker`` lacks authorisation.  The model
    satisfies Q (processor never executes directly) but violates PE.

    Variables:
        planner_consumed_attacker: planner read attacker-controlled data
        processor_has_data: quarantined processor received data
        action_executed: an effect was executed
        pe_violation: an action was executed without all influencers authorised
        attacker_authorised: attacker has permission for the action

    The model has two transition rules:
        1. ``planner-acts``: planner consumes attacker data and executes
        2. ``processor-handles``: processor receives data (no execution)

    PE invariant: ``not pe_violation`` — should be UNSAFE because the
    planner can execute after consuming unauthorised attacker data.
    """
    return VerificationIR(
        "dual-llm-baseline",
        (
            StateVariable("planner_consumed_attacker", Sort.BOOLEAN, False),
            StateVariable("processor_has_data", Sort.BOOLEAN, False),
            StateVariable("action_executed", Sort.BOOLEAN, False),
            StateVariable("pe_violation", Sort.BOOLEAN, False),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "planner-consumes-attacker-data",
                _const(True),
                (
                    Assignment("planner_consumed_attacker", _const(True)),
                    Assignment("processor_has_data", _const(True)),
                ),
            ),
            TransitionRule(
                "planner-executes-after-consumption",
                _var("planner_consumed_attacker"),
                (
                    Assignment("action_executed", _const(True)),
                    Assignment(
                        "pe_violation",
                        _and(
                            _var("action_executed"),
                            _not(_var("attacker_authorised")),
                        ),
                    ),
                ),
            ),
        ),
        (
            SafetyInvariant(
                "no-pe-violation",
                _not(_var("pe_violation")),
                "PE: no action executed when an influencing principal lacks authorisation",
            ),
        ),
        4,
        (
            "dual-llm baseline: privileged planner + quarantined processor",
            "planner tracks data consumption but not per-principal provenance",
            "attacker_authorised is False (attacker lacks permission for the action)",
        ),
    )


def dual_llm_native_property_ir() -> VerificationIR:
    """Dual-LLM with its own intended property Q: processor never executes.

    This model encodes the Dual-LLM's own security guarantee: the quarantined
    processor never directly performs effects.  Only the privileged planner
    can execute actions.  This property Q is satisfied by the model.

    Variables:
        processor_executed: the quarantined processor directly executed an effect
        planner_executed: the privileged planner executed an effect

    Q invariant: ``not processor_executed`` — should be SAFE.
    """
    return VerificationIR(
        "dual-llm-native-property",
        (
            StateVariable("processor_executed", Sort.BOOLEAN, False),
            StateVariable("planner_executed", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "planner-acts",
                _const(True),
                (Assignment("planner_executed", _const(True)),),
            ),
            TransitionRule(
                "processor-receives-data",
                _const(True),
                (),
            ),
        ),
        (
            SafetyInvariant(
                "processor-never-executes",
                _not(_var("processor_executed")),
                "Q: the quarantined processor never directly executes effects",
            ),
        ),
        3,
        (
            "dual-llm native property: processor never executes",
            "the planner can execute; the processor only receives data",
        ),
    )


def ites_reference_ir() -> VerificationIR:
    """ITES reference: blocks execution when an influencer lacks permission.

    This model encodes the ITES rule: if the planner consumed attacker data
    and the attacker is not authorised, the action is blocked.  The PE
    invariant should hold (SAFE).

    Variables:
        planner_consumed_attacker: planner read attacker-controlled data
        action_executed: an effect was executed
        action_blocked: ITES blocked the action
        pe_violation: PE violation occurred
        attacker_authorised: attacker has permission (False)

    Transition rules:
        1. ``planner-consumes``: planner reads attacker data
        2. ``ites-blocks``: ITES blocks execution because attacker is unauthorised
        3. ``ites-allows``: ITES allows execution when no unauthorised influence
    """
    return VerificationIR(
        "ites-reference",
        (
            StateVariable("planner_consumed_attacker", Sort.BOOLEAN, False),
            StateVariable("action_executed", Sort.BOOLEAN, False),
            StateVariable("action_blocked", Sort.BOOLEAN, False),
            StateVariable("pe_violation", Sort.BOOLEAN, False),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "planner-consumes-attacker-data",
                _const(True),
                (Assignment("planner_consumed_attacker", _const(True)),),
            ),
            TransitionRule(
                "ites-blocks-unauthorised",
                _and(
                    _var("planner_consumed_attacker"),
                    _not(_var("attacker_authorised")),
                ),
                (
                    Assignment("action_blocked", _const(True)),
                    Assignment("action_executed", _const(False)),
                ),
            ),
            TransitionRule(
                "ites-allows-authorised",
                _not(_var("planner_consumed_attacker")),
                (Assignment("action_executed", _const(True)),),
            ),
        ),
        (
            SafetyInvariant(
                "no-pe-violation",
                _not(_var("pe_violation")),
                "PE: ITES blocks execution when an influencing principal lacks authorisation",
            ),
            SafetyInvariant(
                "blocked-not-executed",
                _not(_and(_var("action_blocked"), _var("action_executed"))),
                "a blocked action is never executed",
            ),
        ),
        4,
        (
            "ITES reference: principal-intersection rule",
            "attacker_authorised is False; ITES blocks after consuming attacker data",
        ),
    )


def ites_defective_requester_only_ir() -> VerificationIR:
    """Defective controller: checks only the requester, not all influencers.

    This model encodes a REQUESTER_ONLY negative control: it authorises
    actions based solely on the initiating user, ignoring the attacker's
    influence.  The PE invariant should be UNSAFE.

    Variables:
        planner_consumed_attacker: planner read attacker-controlled data
        requester_authorised: the initiating user has permission (True)
        action_executed: an effect was executed
        pe_violation: PE violation occurred
        attacker_authorised: attacker has permission (False)
    """
    return VerificationIR(
        "ites-defective-requester-only",
        (
            StateVariable("planner_consumed_attacker", Sort.BOOLEAN, False),
            StateVariable("requester_authorised", Sort.BOOLEAN, True),
            StateVariable("action_executed", Sort.BOOLEAN, False),
            StateVariable("pe_violation", Sort.BOOLEAN, False),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "planner-consumes-attacker-data",
                _const(True),
                (Assignment("planner_consumed_attacker", _const(True)),),
            ),
            TransitionRule(
                "requester-only-allows",
                _var("requester_authorised"),
                (
                    Assignment("action_executed", _const(True)),
                    Assignment(
                        "pe_violation",
                        _and(
                            _var("action_executed"),
                            _var("planner_consumed_attacker"),
                            _not(_var("attacker_authorised")),
                        ),
                    ),
                ),
            ),
        ),
        (
            SafetyInvariant(
                "no-pe-violation",
                _not(_var("pe_violation")),
                "PE: requester-only check must prevent unauthorised execution",
            ),
        ),
        4,
        (
            "defective controller: checks only requester, ignores influencer provenance",
            "requester_authorised is True; attacker_authorised is False",
        ),
    )


def camel_ir() -> VerificationIR:
    """CaMeL-style defence: capability flow with data/control separation.

    CaMeL separates a trusted planner (control flow) from a quarantined
    data processor.  Capabilities are granted to the planner but data
    flow is restricted.  The key property Q is that data-controlled
    actions cannot directly execute — they must go through the planner's
    capability checks.

    **PE vulnerability:** CaMeL's capability checks authorise based on
    the planner's capabilities, not on the provenance of data consumed
    by the planner.  If the planner consumes attacker-controlled data
    and decides to execute, the action is performed even though the
    attacker lacks authorisation.

    Variables:
        planner_consumed_attacker: planner read attacker data.
        capability_granted: a tool capability is granted to the planner.
        action_executed: an effect was executed.
        pe_violation: PE violation occurred.
        attacker_authorised: attacker has permission (False).
    """
    return VerificationIR(
        "camel-baseline",
        (
            StateVariable("planner_consumed_attacker", Sort.BOOLEAN, False),
            StateVariable("capability_granted", Sort.BOOLEAN, True),
            StateVariable("action_executed", Sort.BOOLEAN, False),
            StateVariable("pe_violation", Sort.BOOLEAN, False),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "planner-consumes-attacker-data",
                _const(True),
                (Assignment("planner_consumed_attacker", _const(True)),),
            ),
            TransitionRule(
                "capability-checked-execute",
                _var("capability_granted"),
                (
                    Assignment("action_executed", _const(True)),
                    Assignment(
                        "pe_violation",
                        _and(
                            _var("action_executed"),
                            _var("planner_consumed_attacker"),
                            _not(_var("attacker_authorised")),
                        ),
                    ),
                ),
            ),
        ),
        (
            SafetyInvariant(
                "no-pe-violation",
                _not(_var("pe_violation")),
                "PE: no action executed when an influencing principal lacks authorisation",
            ),
        ),
        4,
        (
            "CaMeL: capability flow with data/control separation",
            "capability_granted is True; attacker_authorised is False",
            "planner checks capabilities but not per-principal provenance",
        ),
    )


def camel_native_property_ir() -> VerificationIR:
    """CaMeL's own property Q: data-flow cannot directly cause effects.

    Only the planner (with capabilities) can execute; the quarantined
    data processor cannot.  This property Q is satisfied.
    """
    return VerificationIR(
        "camel-native-property",
        (
            StateVariable("processor_executed", Sort.BOOLEAN, False),
            StateVariable("planner_executed", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "planner-acts",
                _const(True),
                (Assignment("planner_executed", _const(True)),),
            ),
            TransitionRule(
                "processor-receives-data",
                _const(True),
                (),
            ),
        ),
        (
            SafetyInvariant(
                "processor-never-executes",
                _not(_var("processor_executed")),
                "Q: the quarantined data processor never directly executes effects",
            ),
        ),
        3,
        (
            "CaMeL native property: processor never executes",
            "the planner can execute via capabilities; the processor only receives data",
        ),
    )


def progent_ir() -> VerificationIR:
    """Progent-like defence: parameter-sensitive tool policy.

    Progent applies symbolic policies to tool calls, checking arguments
    against policy rules.  The key property Q is that all tool calls
    satisfy the policy.  However, the policy checks arguments, not the
    provenance of the data that influenced the planner's decision to
    call the tool.

    **PE vulnerability:** If the planner consumed attacker-controlled
    data and decides to call a tool with arguments that satisfy the
    policy, the action executes even though the attacker influenced the
    decision and lacks authorisation.

    Variables:
        planner_consumed_attacker: planner read attacker data.
        policy_satisfied: tool arguments pass the policy check (True).
        action_executed: an effect was executed.
        pe_violation: PE violation occurred.
        attacker_authorised: attacker has permission (False).
    """
    return VerificationIR(
        "progent-baseline",
        (
            StateVariable("planner_consumed_attacker", Sort.BOOLEAN, False),
            StateVariable("policy_satisfied", Sort.BOOLEAN, True),
            StateVariable("action_executed", Sort.BOOLEAN, False),
            StateVariable("pe_violation", Sort.BOOLEAN, False),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "planner-consumes-attacker-data",
                _const(True),
                (Assignment("planner_consumed_attacker", _const(True)),),
            ),
            TransitionRule(
                "policy-checked-execute",
                _var("policy_satisfied"),
                (
                    Assignment("action_executed", _const(True)),
                    Assignment(
                        "pe_violation",
                        _and(
                            _var("planner_consumed_attacker"),
                            _not(_var("attacker_authorised")),
                        ),
                    ),
                ),
            ),
        ),
        (
            SafetyInvariant(
                "no-pe-violation",
                _not(_var("pe_violation")),
                "PE: no action executed when an influencing principal lacks authorisation",
            ),
        ),
        4,
        (
            "Progent: parameter-sensitive tool policy",
            "policy_satisfied is True; attacker_authorised is False",
            "policy checks arguments but not planner provenance",
        ),
    )


def progent_native_property_ir() -> VerificationIR:
    """Progent's own property Q: all tool calls satisfy the policy."""
    return VerificationIR(
        "progent-native-property",
        (StateVariable("policy_violation", Sort.BOOLEAN, False),),
        (
            TransitionRule(
                "policy-checked-call",
                _const(True),
                (Assignment("policy_violation", _const(False)),),
            ),
        ),
        (
            SafetyInvariant(
                "no-policy-violation",
                _not(_var("policy_violation")),
                "Q: all tool calls satisfy the parameter-sensitive policy",
            ),
        ),
        2,
        ("Progent native property: all calls satisfy policy",),
    )


def pact_ir() -> VerificationIR:
    """PACT-like defence: argument-level provenance tracking.

    PACT tracks provenance at the argument level, not just the execution
    level.  The key property Q is that argument provenance is preserved
    across steps.  However, PACT does not derive action authority from
    the intersection of all influencing principals' permissions.

    **PE vulnerability:** PACT may track that the attacker influenced a
    specific argument, but it does not block the action based on the
    attacker's lack of ACS permission.  The action executes because the
    requester is authorised, even though the attacker also influenced it.

    Variables:
        requester_authorised: the requester has permission (True).
        attacker_influenced_arg: attacker data reached a tool argument.
        action_executed: an effect was executed.
        pe_violation: PE violation occurred.
        attacker_authorised: attacker has permission (False).
    """
    return VerificationIR(
        "pact-baseline",
        (
            StateVariable("attacker_influenced_arg", Sort.BOOLEAN, False),
            StateVariable("requester_authorised", Sort.BOOLEAN, True),
            StateVariable("action_executed", Sort.BOOLEAN, False),
            StateVariable("pe_violation", Sort.BOOLEAN, False),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "attacker-data-reaches-argument",
                _const(True),
                (Assignment("attacker_influenced_arg", _const(True)),),
            ),
            TransitionRule(
                "execute-with-arg-provenance",
                _var("requester_authorised"),
                (
                    Assignment("action_executed", _const(True)),
                    Assignment(
                        "pe_violation",
                        _and(
                            _var("attacker_influenced_arg"),
                            _not(_var("attacker_authorised")),
                        ),
                    ),
                ),
            ),
        ),
        (
            SafetyInvariant(
                "no-pe-violation",
                _not(_var("pe_violation")),
                "PE: no action executed when an influencing principal lacks authorisation",
            ),
        ),
        4,
        (
            "PACT: argument-level provenance without authority intersection",
            "requester_authorised is True; attacker_authorised is False",
            "tracks arg provenance but does not block based on influencer authority",
        ),
    )


def pact_native_property_ir() -> VerificationIR:
    """PACT's own property Q: argument provenance is preserved."""
    return VerificationIR(
        "pact-native-property",
        (
            StateVariable("arg_provenance_tracked", Sort.BOOLEAN, True),
            StateVariable("provenance_lost", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "cross-step-provenance",
                _const(True),
                (Assignment("provenance_lost", _const(False)),),
            ),
        ),
        (
            SafetyInvariant(
                "provenance-preserved",
                _not(_var("provenance_lost")),
                "Q: argument-level provenance is preserved across steps",
            ),
        ),
        2,
        ("PACT native property: argument provenance preserved",),
    )


__all__ = [
    "camel_ir",
    "camel_native_property_ir",
    "dual_llm_baseline_ir",
    "dual_llm_native_property_ir",
    "ites_defective_requester_only_ir",
    "ites_reference_ir",
    "pact_ir",
    "pact_native_property_ir",
    "progent_ir",
    "progent_native_property_ir",
]
