"""Verification IR models of contemporary agent defence patterns.

Each factory returns a :class:`VerificationIR` that represents a small
finite abstraction intended for hypothesis generation and verifier
testing.  The models are **not** implementation-conformance evidence for
the cited external systems.  They are designed for comparative
verification against the Conflux PE property:

    Executed(a) -> forall p in Influencers(a): ACSAllows(p, a)

A candidate abstraction can satisfy its own intended property while
admitting a PE counterexample because it does not track per-principal
provenance.  External defence model fidelity is tracked in
``docs/evidence/defence-model-fidelity.json``.
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
    """Dual-LLM candidate abstraction: privileged planner + quarantined data processor.

    This is a small finite abstraction inspired by the Dual-LLM pattern, not
    an implementation-conformance model of any published system.  The
    abstraction separates control flow (privileged planner) from data
    processing (quarantined processor).  The planner decides which tool
    to call and with what arguments; the processor handles untrusted data
    but cannot directly invoke tools.

    The key security property (Q) is that the quarantined processor never
    directly executes effects — only the privileged planner can.

    **PE vulnerability (in the candidate abstraction):** The Dual-LLM
    abstraction does not track which principals influenced the planner's
    decision.  If the planner consumes data from principal ``attacker`` and decides to execute an action, the action is
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
            "Dual-LLM candidate abstraction: privileged planner + quarantined processor",
            "planner tracks data consumption but not per-principal provenance",
            "attacker_authorised is False (attacker lacks permission for the action)",
        ),
    )


def dual_llm_native_property_ir() -> VerificationIR:
    """Dual-LLM candidate abstraction: its own intended property Q.

    This model encodes the Dual-LLM abstraction's own security guarantee:
    the quarantined processor never directly performs effects.  Only the
    privileged planner can execute actions.  This property Q is satisfied
    by the model.

    Variables:
        processor_executed: the quarantined processor directly executed an effect
        planner_executed: the privileged planner executed an effect
        processor_gate: the defence is active (starts True; no rule clears it)

    Q invariant: ``not processor_executed`` — holds, and is falsifiable by a
    single-rule mutation of ``processor-executes``.
    """
    return VerificationIR(
        "dual-llm-native-property",
        (
            StateVariable("processor_executed", Sort.BOOLEAN, False),
            StateVariable("planner_executed", Sort.BOOLEAN, False),
            StateVariable("processor_gate", Sort.BOOLEAN, True),
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
            TransitionRule(
                "processor-executes",
                _not(_var("processor_gate")),
                (Assignment("processor_executed", _const(True)),),
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
            "Dual-LLM candidate abstraction native property: processor never executes",
            "the planner can execute; the processor only receives data",
            "processor_gate starts True and no rule clears it: holds by construction",
        ),
    )


def ites_reference_ir() -> VerificationIR:
    """ITES reference: blocks execution when an influencer lacks permission.

    This model encodes the ITES rule: if the planner consumed attacker data
    and the attacker is not authorised, the action is blocked.  The PE
    invariant holds, and each holding invariant is falsifiable by a
    single-rule guard mutation (the block and allow guards partition the
    state space, and each property has one rule that records it).

    Variables:
        planner_consumed_attacker: planner read attacker-controlled data
        action_executed: an effect was executed
        action_blocked: ITES blocked the action
        pe_violation: PE violation recorded (executed after consuming unauthorised data)
        attacker_authorised: attacker has permission (False)
        maximality_violation: over-blocking recorded (blocked without unauthorised influence)

    Transition rules:
        1. ``planner-consumes-attacker-data``: planner reads attacker data
        2. ``ites-blocks-unauthorised``: block when consumed and the attacker is unauthorised
        3. ``ites-allows-authorised``: allow when not blocked and no unauthorised influence
        4. ``authorisation-granted``: the attacker gains permission for this action
        5. ``pe-violation-recorded``: executed after consuming unauthorised data
        6. ``maximality-violation-recorded``: blocked without unauthorised influence
    """
    return VerificationIR(
        "ites-reference",
        (
            StateVariable("planner_consumed_attacker", Sort.BOOLEAN, False),
            StateVariable("action_executed", Sort.BOOLEAN, False),
            StateVariable("action_blocked", Sort.BOOLEAN, False),
            StateVariable("pe_violation", Sort.BOOLEAN, False),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
            StateVariable("maximality_violation", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "planner-consumes-attacker-data",
                _not(_var("action_executed")),
                (Assignment("planner_consumed_attacker", _const(True)),),
            ),
            TransitionRule(
                "ites-blocks-unauthorised",
                _and(
                    _not(_var("action_executed")),
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
                _and(
                    _not(_var("action_blocked")),
                    _or(
                        _not(_var("planner_consumed_attacker")),
                        _var("attacker_authorised"),
                    ),
                ),
                (Assignment("action_executed", _const(True)),),
            ),
            TransitionRule(
                "authorisation-granted",
                _var("planner_consumed_attacker"),
                (Assignment("attacker_authorised", _const(True)),),
            ),
            TransitionRule(
                "pe-violation-recorded",
                _and(
                    _var("action_executed"),
                    _var("planner_consumed_attacker"),
                    _not(_var("attacker_authorised")),
                ),
                (Assignment("pe_violation", _const(True)),),
            ),
            TransitionRule(
                "maximality-violation-recorded",
                _and(_var("action_blocked"), _not(_var("planner_consumed_attacker"))),
                (Assignment("maximality_violation", _const(True)),),
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
            SafetyInvariant(
                "no-maximality-violation",
                _not(_var("maximality_violation")),
                "no over-blocking: nothing is blocked without unauthorised influence",
            ),
        ),
        6,
        (
            "ITES reference: principal-intersection rule",
            "attacker_authorised is False; ITES blocks after consuming attacker data",
            "block and allow guards partition the state space; each property has a recording rule",
        ),
    )


def ites_native_property_ir() -> VerificationIR:
    """ITES candidate abstraction: its own property Q (no over-blocking).

    ITES claims to block exactly the actions an unauthorised influencer
    contributed to.  This model carries that family-specific guarantee:
    nothing is blocked without unauthorised influence.  The comparative PE
    property stays on :func:`ites_reference_ir`; this factory is the native
    property surface that every other defence family already has.

    Q invariant: ``not maximality_violation`` — holds, and is falsifiable
    by a single-rule mutation of the block guard.
    """
    return VerificationIR(
        "ites-native-property",
        (
            StateVariable("planner_consumed_attacker", Sort.BOOLEAN, False),
            StateVariable("action_executed", Sort.BOOLEAN, False),
            StateVariable("action_blocked", Sort.BOOLEAN, False),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
            StateVariable("maximality_violation", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "planner-consumes-attacker-data",
                _not(_var("action_executed")),
                (Assignment("planner_consumed_attacker", _const(True)),),
            ),
            TransitionRule(
                "ites-blocks-unauthorised",
                _and(
                    _not(_var("action_executed")),
                    _var("planner_consumed_attacker"),
                    _not(_var("attacker_authorised")),
                ),
                (Assignment("action_blocked", _const(True)),),
            ),
            TransitionRule(
                "ites-allows-authorised",
                _and(
                    _not(_var("action_blocked")),
                    _or(
                        _not(_var("planner_consumed_attacker")),
                        _var("attacker_authorised"),
                    ),
                ),
                (Assignment("action_executed", _const(True)),),
            ),
            TransitionRule(
                "authorisation-granted",
                _var("planner_consumed_attacker"),
                (Assignment("attacker_authorised", _const(True)),),
            ),
            TransitionRule(
                "maximality-violation-recorded",
                _and(_var("action_blocked"), _not(_var("planner_consumed_attacker"))),
                (Assignment("maximality_violation", _const(True)),),
            ),
        ),
        (
            SafetyInvariant(
                "no-maximality-violation",
                _not(_var("maximality_violation")),
                "Q: ITES never blocks an action that no unauthorised principal influenced",
            ),
        ),
        5,
        ("ITES candidate abstraction native property: no over-blocking",),
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
    """CaMeL candidate abstraction: capability flow with data/control separation.

    This is a small finite abstraction inspired by CaMeL, not an
    implementation-conformance model of the published system.  CaMeL
    separates a trusted planner (control flow) from a quarantined data
    processor.  Capabilities are granted to the planner but data flow is
    restricted.  The key property Q is that data-controlled actions cannot
    directly execute — they must go through the planner's capability checks.

    **PE vulnerability (in the candidate abstraction):** The CaMeL
    abstraction's capability checks authorise based on the planner's
    capabilities, not on the provenance of data consumed by the planner.
    If the planner consumes attacker-controlled data
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
            "CaMeL candidate abstraction: capability flow with data/control separation",
            "capability_granted is True; attacker_authorised is False",
            "planner checks capabilities but not per-principal provenance",
        ),
    )


def camel_native_property_ir() -> VerificationIR:
    """CaMeL candidate abstraction: its own property Q (data-flow cannot cause effects).

    Only the planner (with capabilities) can execute; the quarantined data
    processor cannot.  This property Q is satisfied by the abstraction.

    Variables:
        processor_executed: the quarantined processor directly executed an effect
        planner_executed: the privileged planner executed an effect
        processor_gate: the defence is active (starts True; no rule clears it)

    Q invariant: ``not processor_executed`` — holds, and is falsifiable by a
    single-rule mutation of ``processor-executes``.
    """
    return VerificationIR(
        "camel-native-property",
        (
            StateVariable("processor_executed", Sort.BOOLEAN, False),
            StateVariable("planner_executed", Sort.BOOLEAN, False),
            StateVariable("processor_gate", Sort.BOOLEAN, True),
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
            TransitionRule(
                "processor-executes",
                _not(_var("processor_gate")),
                (Assignment("processor_executed", _const(True)),),
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
            "CaMeL candidate abstraction native property: processor never executes",
            "the planner can execute via capabilities; the processor only receives data",
            "processor_gate starts True and no rule clears it: holds by construction",
        ),
    )


def progent_ir() -> VerificationIR:
    """Progent candidate abstraction: parameter-sensitive tool policy.

    This is a small finite abstraction inspired by Progent, not an
    implementation-conformance model of the published system.  Progent
    applies symbolic policies to tool calls, checking arguments against
    policy rules.  The key property Q is that all tool calls satisfy the
    policy.  However, the policy checks arguments, not the provenance of
    the data that influenced the planner's decision to call the tool.

    **PE vulnerability (in the candidate abstraction):** If the planner
    consumed attacker-controlled data and decides to call a tool with
    arguments that satisfy the policy, the action executes even though
    the attacker influenced the decision and lacks authorisation.

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
            "Progent candidate abstraction: parameter-sensitive tool policy",
            "policy_satisfied is True; attacker_authorised is False",
            "policy checks arguments but not planner provenance",
        ),
    )


def progent_native_property_ir() -> VerificationIR:
    """Progent candidate abstraction: its own property Q (all calls satisfy policy).

    Variables:
        policy_violation: a call violated the parameter-sensitive policy
        policy_gate: the defence is active (starts True; no rule clears it)

    Q invariant: ``not policy_violation`` — holds, and is falsifiable by a
    single-rule mutation of ``policy-violated-call``.
    """
    return VerificationIR(
        "progent-native-property",
        (
            StateVariable("policy_violation", Sort.BOOLEAN, False),
            StateVariable("policy_gate", Sort.BOOLEAN, True),
        ),
        (
            TransitionRule(
                "policy-checked-call",
                _const(True),
                (Assignment("policy_violation", _const(False)),),
            ),
            TransitionRule(
                "policy-violated-call",
                _not(_var("policy_gate")),
                (Assignment("policy_violation", _const(True)),),
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
        (
            "Progent candidate abstraction native property: all calls satisfy policy",
            "policy_gate starts True and no rule clears it: holds by construction",
        ),
    )


def pact_ir() -> VerificationIR:
    """PACT candidate abstraction: argument-level provenance tracking.

    This is a small finite abstraction inspired by PACT, not an
    implementation-conformance model of the published system.  PACT
    tracks provenance at the argument level, not just the execution
    level.  The key property Q is that argument provenance is preserved
    across steps.  However, PACT does not derive action authority from
    the intersection of all influencing principals' permissions.

    **PE vulnerability (in the candidate abstraction):** The PACT
    abstraction may track that the attacker influenced a specific
    argument, but it does not block the action based on the attacker's
    lack of ACS permission.  The action executes because the requester

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
            "PACT candidate abstraction: argument-level provenance without authority intersection",
            "requester_authorised is True; attacker_authorised is False",
            "tracks arg provenance but does not block based on influencer authority",
        ),
    )


def pact_native_property_ir() -> VerificationIR:
    """PACT candidate abstraction: its own property Q (argument provenance preserved).

    Variables:
        arg_provenance_tracked: argument provenance is tracked (True, unchanged)
        provenance_lost: argument provenance was lost
        provenance_gate: the defence is active (starts True; no rule clears it)

    Q invariant: ``not provenance_lost`` — holds, and is falsifiable by a
    single-rule mutation of ``provenance-dropped``.
    """
    return VerificationIR(
        "pact-native-property",
        (
            StateVariable("arg_provenance_tracked", Sort.BOOLEAN, True),
            StateVariable("provenance_lost", Sort.BOOLEAN, False),
            StateVariable("provenance_gate", Sort.BOOLEAN, True),
        ),
        (
            TransitionRule(
                "cross-step-provenance",
                _const(True),
                (Assignment("provenance_lost", _const(False)),),
            ),
            TransitionRule(
                "provenance-dropped",
                _not(_var("provenance_gate")),
                (Assignment("provenance_lost", _const(True)),),
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
        (
            "PACT candidate abstraction native property: argument provenance preserved",
            "provenance_gate starts True and no rule clears it: holds by construction",
        ),
    )


def ites_with_read_check_ir() -> VerificationIR:
    """ITES with an additional read-check on nested execution inputs.

    This is an ablation model inspired by the original prototype's
    ``auth_read`` function, which checked that all influencers could
    read the inputs to a nested LLM call before allowing it.

    The model uses set-typed variables to represent the principal context
    (``pc``) and the set of principals who can read the nested execution
    inputs (``input_readers``).  The nested-execution transition is
    guarded by ``SUBSET(pc, input_readers)`` — all influencers must be
    able to read the inputs.

    This model is PE-safe (the read check is stricter than ITES alone)
    but may deny actions that ITES would allow, reducing utility.

    Variables:
        pc: principal context (set of principal IDs).
        input_readers: principals who can read the nested inputs.
        action_executed: whether the action was executed.
        pe_violation: whether a PE violation occurred.
        attacker_authorised: whether the attacker has permission (False).
    """
    return VerificationIR(
        "ites-with-read-check",
        (
            StateVariable("pc", Sort.SET, frozenset()),
            StateVariable("input_readers", Sort.SET, frozenset({"alice"})),
            StateVariable("action_executed", Sort.BOOLEAN, False),
            StateVariable("pe_violation", Sort.BOOLEAN, False),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "consume-attacker-data",
                _const(True),
                (
                    Assignment(
                        "pc",
                        Expression.operator(
                            ExpressionKind.UNION,
                            _var("pc"),
                            Expression.constant("mallory"),
                        ),
                    ),
                ),
            ),
            TransitionRule(
                "ites-read-check-blocks",
                _and(
                    Expression.operator(
                        ExpressionKind.IN,
                        Expression.constant("mallory"),
                        _var("pc"),
                    ),
                    _not(_var("attacker_authorised")),
                ),
                (
                    Assignment("action_executed", _const(False)),
                    Assignment("pe_violation", _const(False)),
                ),
            ),
            TransitionRule(
                "ites-read-check-allows",
                _and(
                    _not(
                        Expression.operator(
                            ExpressionKind.IN,
                            Expression.constant("mallory"),
                            _var("pc"),
                        ),
                    ),
                    Expression.operator(
                        ExpressionKind.SUBSET,
                        _var("pc"),
                        _var("input_readers"),
                    ),
                ),
                (Assignment("action_executed", _const(True)),),
            ),
        ),
        (
            SafetyInvariant(
                "no-pe-violation",
                _not(_var("pe_violation")),
                "PE: no action executed when an influencing principal lacks authorisation",
            ),
        ),
        5,
        (
            "ITES with read-check ablation: auth_read on nested inputs",
            "pc starts empty; input_readers = {alice}; attacker_authorised = False",
            "nested execution requires SUBSET(pc, input_readers)",
        ),
    )


def camelot_ir() -> VerificationIR:
    """CaMeLoT candidate abstraction: plan pre-check with history facts.

    This is a small finite abstraction inspired by CaMeLoT
    (arXiv:2609.18674), not an implementation-conformance model of the
    published system.  CaMeLoT parses the plan into a finite state machine
    whose states carry the tool, the argument provenance and history facts,
    checks CTL policy formulas with nuXmv before any tool runs, and feeds a
    failing trace back to the planner as repair feedback.

    The finite model collapses the plan trace to one pre-check gate and one
    history fact: whether the decision to execute was influenced by an
    untrusted source.  CaMeLoT's temporal formulas are **not** modelled here:
    the expression language has no temporal operator, so only the safety half
    of its representative policy is represented, and that half is the subject
    of ``camelot_native_property_ir``.  The liveness obligation the paper adds
    (a ticket must eventually resolve, so a suppression attack is caught) has
    no analogue in a safety invariant and is deliberately out of scope.

    **PE vulnerability (in the candidate abstraction):** CaMeLoT has no
    principal at all.  Trust is positional - the user prompt is trusted by
    position - and is assigned per tool, never per value, so the plan policy
    can be satisfied while the principal that actually influenced the decision
    lacks authority for it.

    Variables:
        plan_prechecked: the plan passed the CTL pre-check.
        history_influenced: a history fact records untrusted influence.
        action_executed: an effect was executed.
        ticket_resolved: the ticket flow reached resolution.
        pe_violation: PE violation occurred.
        attacker_authorised: attacker has permission (False).
    """
    return VerificationIR(
        "camelot-baseline",
        (
            StateVariable("plan_prechecked", Sort.BOOLEAN, False),
            StateVariable("history_influenced", Sort.BOOLEAN, False),
            StateVariable("action_executed", Sort.BOOLEAN, False),
            StateVariable("ticket_resolved", Sort.BOOLEAN, False),
            StateVariable("pe_violation", Sort.BOOLEAN, False),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "plan-precheck-accepts",
                _const(True),
                (Assignment("plan_prechecked", _const(True)),),
            ),
            TransitionRule(
                "history-records-untrusted-influence",
                _const(True),
                (Assignment("history_influenced", _const(True)),),
            ),
            TransitionRule(
                "prechecked-plan-executes",
                _var("plan_prechecked"),
                (
                    Assignment("action_executed", _const(True)),
                    Assignment(
                        "pe_violation",
                        _and(
                            _var("action_executed"),
                            _var("history_influenced"),
                            _not(_var("attacker_authorised")),
                        ),
                    ),
                ),
            ),
            TransitionRule(
                "ticket-flow-resolves",
                _var("action_executed"),
                (Assignment("ticket_resolved", _const(True)),),
            ),
        ),
        (
            SafetyInvariant(
                "no-pe-violation",
                _not(_var("pe_violation")),
                "PE: no action executed when an influencing principal lacks authorisation",
            ),
        ),
        5,
        (
            "CaMeLoT candidate abstraction: plan pre-check with history facts",
            "plan_prechecked gates execution; history facts record untrusted influence",
            "CaMeLoT trust is positional and per tool, so the plan policy holds while PE fails",
            "the CTL formulas and their liveness half are not modelled in this finite IR",
        ),
    )


def camelot_native_property_ir() -> VerificationIR:
    """CaMeLoT candidate abstraction: its own property Q (policy holds on the trace).

    The safety half of CaMeLoT's representative policy: a direct message is
    sent only when the recipient is trusted.  The plan pre-check is the gate
    that enforces it; the ticket flow is modelled because the paper's liveness
    obligation returns repair feedback through it, but no liveness property is
    checked (a ``SafetyInvariant`` cannot express ``AF``).

    Variables:
        recipient_trusted: the policy marked the recipient trusted.
        send_called: a direct-message call was made.
        precheck_gate: the plan pre-check is active (starts True; no rule clears it).
        ticket_created: the ticket flow created a ticket.
        ticket_resolved: the ticket flow resolved it.

    Q invariant: ``not send_called or recipient_trusted`` - holds, and is
    falsifiable by a single-rule mutation of ``send-direct-message``.
    """
    return VerificationIR(
        "camelot-native-property",
        (
            StateVariable("recipient_trusted", Sort.BOOLEAN, False),
            StateVariable("send_called", Sort.BOOLEAN, False),
            StateVariable("precheck_gate", Sort.BOOLEAN, True),
            StateVariable("ticket_created", Sort.BOOLEAN, False),
            StateVariable("ticket_resolved", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "precheck-labels-recipient-trusted",
                _const(True),
                (Assignment("recipient_trusted", _const(True)),),
            ),
            TransitionRule(
                "send-direct-message",
                _and(_var("precheck_gate"), _var("recipient_trusted")),
                (Assignment("send_called", _const(True)),),
            ),
            TransitionRule(
                "ticket-create",
                _const(True),
                (Assignment("ticket_created", _const(True)),),
            ),
            TransitionRule(
                "ticket-resolve",
                _var("ticket_created"),
                (Assignment("ticket_resolved", _const(True)),),
            ),
        ),
        (
            SafetyInvariant(
                "no-untrusted-recipient",
                _or(_not(_var("send_called")), _var("recipient_trusted")),
                "Q: a direct message is sent only to a policy-trusted recipient",
            ),
        ),
        4,
        (
            "CaMeLoT candidate abstraction native property: policy holds on the trace",
            "the pre-check gates the call; the policy labels the recipient trusted",
            "the liveness half (a ticket eventually resolves) is not modelled",
        ),
    )


def fides_ir() -> VerificationIR:
    """Fides candidate abstraction: planner information-flow control.

    This is a small finite abstraction inspired by Fides
    (arXiv:2505.23643), not an implementation-conformance model of the
    published system.  Fides labels data with a confidentiality (reader
    scope) and an integrity (source trust) label that travel with the data
    and join when values combine; policy P-T allows a dangerous call only
    from a trusted context and P-F releases data only to permitted readers.

    The finite model collapses both labels to booleans: one integrity label
    for the value that drives the call and one for the planner context.  The
    reader scope is not modelled here.

    **PE vulnerability (in the candidate abstraction):** a label is only as
    honest as the party that wrote it.  A lying tool can label
    attacker-controlled data trusted (the note names this), and the resulting
    call satisfies P-T while the principal that supplied the data still lacks
    authority for it.

    Variables:
        source_label_trusted: integrity label written by the tool that supplied the value.
        context_label_trusted: integrity label of the planner context.
        value_trusted: the joined label of the value driving the call.
        action_executed: an effect was executed.
        pe_violation: PE violation occurred.
        attacker_authorised: attacker has permission (False).
    """
    return VerificationIR(
        "fides-baseline",
        (
            StateVariable("source_label_trusted", Sort.BOOLEAN, False),
            StateVariable("context_label_trusted", Sort.BOOLEAN, True),
            StateVariable("value_trusted", Sort.BOOLEAN, False),
            StateVariable("action_executed", Sort.BOOLEAN, False),
            StateVariable("pe_violation", Sort.BOOLEAN, False),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "lying-tool-labels-source-trusted",
                _const(True),
                (Assignment("source_label_trusted", _const(True)),),
            ),
            TransitionRule(
                "join-integrity-labels",
                _var("source_label_trusted"),
                (
                    Assignment(
                        "value_trusted",
                        _and(_var("source_label_trusted"), _var("context_label_trusted")),
                    ),
                ),
            ),
            TransitionRule(
                "trusted-action-call",
                _and(_var("context_label_trusted"), _var("value_trusted")),
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
        5,
        (
            "Fides candidate abstraction: planner information-flow control",
            "labels are booleans; the reader scope is not modelled in the PE model",
            "a lying tool can relabel attacker data trusted, so P-T holds while PE fails",
        ),
    )


def fides_native_property_ir() -> VerificationIR:
    """Fides candidate abstraction: its own properties Q (P-T and P-F).

    Policy P-T: a dangerous call runs only from a trusted context with a
    trusted value.  Policy P-F: no value is released to a reader outside the
    permitted scope, modelled with a bounded reader set and a membership test
    (``ExpressionKind.IN``), the same set encoding ``ites_with_read_check_ir``
    uses.

    Variables:
        context_trusted: the planner context's integrity label.
        value_trusted: the value's integrity label.
        readers: the readership the value is released to.
        released_readers: the readership the value was released to.
        trusted_call_made: a dangerous call ran.
        released: the value was released.

    P-F is stated over the label captured at release (``released_readers``),
    not over the current ``readers``: a value that left under a permitted
    readership does not become a violation because a later join widens the
    label it was copied from.

    Q invariants: ``not trusted_call_made or (context_trusted and
    value_trusted)`` (P-T) and ``not released or "mallory" not in
    released_readers`` (P-F).
    """
    return VerificationIR(
        "fides-native-property",
        (
            StateVariable("context_trusted", Sort.BOOLEAN, True),
            StateVariable("value_trusted", Sort.BOOLEAN, False),
            StateVariable("readers", Sort.SET, frozenset({"alice"})),
            StateVariable("released_readers", Sort.SET, frozenset()),
            StateVariable("trusted_call_made", Sort.BOOLEAN, False),
            StateVariable("released", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "trusted-context-labels-value",
                _var("context_trusted"),
                (Assignment("value_trusted", _const(True)),),
            ),
            TransitionRule(
                "untrusted-reader-joins-scope",
                _const(True),
                (
                    Assignment(
                        "readers",
                        Expression.operator(
                            ExpressionKind.UNION,
                            _var("readers"),
                            Expression.constant("mallory"),
                        ),
                    ),
                ),
            ),
            TransitionRule(
                "trusted-action-call",
                _and(_var("context_trusted"), _var("value_trusted")),
                (Assignment("trusted_call_made", _const(True)),),
            ),
            TransitionRule(
                "permitted-flow-release",
                _and(
                    _not(
                        Expression.operator(
                            ExpressionKind.IN,
                            Expression.constant("mallory"),
                            _var("readers"),
                        ),
                    ),
                    _var("value_trusted"),
                ),
                (
                    Assignment("released", _const(True)),
                    Assignment("released_readers", _var("readers")),
                ),
            ),
        ),
        (
            SafetyInvariant(
                "no-untrusted-action",
                _or(
                    _not(_var("trusted_call_made")),
                    _and(_var("context_trusted"), _var("value_trusted")),
                ),
                "Q (P-T): a dangerous call runs only from a trusted context and value",
            ),
            SafetyInvariant(
                "no-flow-to-untrusted-reader",
                _or(
                    _not(_var("released")),
                    _not(
                        Expression.operator(
                            ExpressionKind.IN,
                            Expression.constant("mallory"),
                            _var("released_readers"),
                        ),
                    ),
                ),
                "Q (P-F): a value is not released to a reader outside the permitted scope",
            ),
        ),
        4,
        (
            "Fides candidate abstraction native property: P-T and P-F",
            "the reader scope is a bounded set; membership is an IN test",
            "the join takes the lower integrity label; a lying tool can raise it",
        ),
    )


def pace_ir() -> VerificationIR:
    """PACE candidate abstraction: provenance-aware capability enforcement.

    This is a small finite abstraction inspired by PACE (arXiv:2610.01349),
    not an implementation-conformance model of it.  PACE freezes a tool call
    at the last boundary, wires it into an episode graph, and verifies a path
    chain (cut every flow edge from a protected value to the unsafe terminal)
    and an effect chain of nine obligations before dispatch.  This IR keeps
    only the compile step and a cut-then-dispatch step: the episode graph,
    the nine obligations, the two certificates and the recomputing verifier
    are not modelled.

    The abstraction's PE vulnerability is the one the expansion survey
    records: authority is compiled from the authenticated request channel
    alone and is never summed over the principals that influenced the
    decision, and the untrusted frontier is a single bucket.  The
    represented-path property Q can therefore hold while an influencing
    principal's separate authority is never required.

    ``Sort`` has no enum member, so provenance here is a boolean; that is
    what the finite model does and does not capture.

    Variables:
        request_authenticated: the request channel is authenticated (True).
        capability_compiled: a capability was compiled from the request.
        untrusted_influence: attacker-influenced content entered the episode.
        cut_installed: the flow cut was installed.
        dispatched: the call was dispatched.
        attacker_authorised: attacker has permission (False).
        pe_violation: PE violation occurred.

    **PE vulnerability:** ``dispatch-past-cut`` runs once the capability is
    compiled and the cut is installed, even when attacker-influenced content
    entered the episode and the attacker is not authorised, so
    ``no-pe-violation`` has a reachable counterexample.
    """
    return VerificationIR(
        "pace-baseline",
        (
            StateVariable("request_authenticated", Sort.BOOLEAN, True),
            StateVariable("capability_compiled", Sort.BOOLEAN, False),
            StateVariable("untrusted_influence", Sort.BOOLEAN, False),
            StateVariable("cut_installed", Sort.BOOLEAN, False),
            StateVariable("dispatched", Sort.BOOLEAN, False),
            StateVariable("attacker_authorised", Sort.BOOLEAN, False),
            StateVariable("pe_violation", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "compile-capability-from-request",
                _var("request_authenticated"),
                (Assignment("capability_compiled", _const(True)),),
            ),
            TransitionRule(
                "untrusted-influence-enters-episode",
                _const(True),
                (Assignment("untrusted_influence", _const(True)),),
            ),
            TransitionRule(
                "install-cut",
                _var("capability_compiled"),
                (Assignment("cut_installed", _const(True)),),
            ),
            TransitionRule(
                "dispatch-past-cut",
                _and(_var("capability_compiled"), _var("cut_installed")),
                (
                    Assignment("dispatched", _const(True)),
                    Assignment(
                        "pe_violation",
                        _and(
                            _var("dispatched"),
                            _and(
                                _var("untrusted_influence"),
                                _not(_var("attacker_authorised")),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        (
            SafetyInvariant(
                "no-pe-violation",
                _not(_var("pe_violation")),
                "PE: no effect is executed without the authority of every influencing principal",
            ),
        ),
        5,
        (
            "PACE candidate abstraction: capability compiled from the authenticated request, cut then dispatch",
            "the episode graph, the nine effect obligations, the certificates and the recomputing verifier are not modelled",
            "trust levels are booleans because the IR has no enum sort",
        ),
    )


def pace_native_property_ir() -> VerificationIR:
    """PACE candidate abstraction: its own path-chain property Q.

    Q (the represented-path half of PACE-C): no call is dispatched while a
    represented flow edge from a protected value to the unsafe terminal is
    uncut.  The survey states the property as "no represented path from a
    protected value to an unsafe terminal"; this abstraction states it over a
    *bounded enumerated* cut set - the two edges ``e1`` and ``e2`` the
    abstraction represents - instead of an open hypergraph.  Bounding the
    graph and enumerating the cut set is the abstraction decision that makes
    this candidate verifiable in the finite IR; the effect chain, the
    certificates and the recomputing verifier are not modelled, and the
    delegation-attenuation obligation is not represented at all.

    ``Sort`` has no enum member, so the cut set is a bounded ``Sort.SET``
    whose membership is an ``IN`` test - the same encoding
    ``ites_with_read_check_ir`` uses.  Each represented edge is added by its
    own rule, so the cut is data the model can be mutated away from rather
    than a guard that always holds.

    Variables:
        graph_built: the episode graph was built at the last boundary.
        cut_edges: the represented flow edges that have been cut (set).
        dispatched: the call was dispatched.
        effect_verified: the effect atoms were verified.

    Q invariant: ``not dispatched or ("e1" in cut_edges and "e2" in
    cut_edges)``.
    """
    return VerificationIR(
        "pace-native-property",
        (
            StateVariable("graph_built", Sort.BOOLEAN, False),
            StateVariable("cut_edges", Sort.SET, frozenset()),
            StateVariable("dispatched", Sort.BOOLEAN, False),
            StateVariable("effect_verified", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "freeze-and-build-graph",
                _not(_var("graph_built")),
                (Assignment("graph_built", _const(True)),),
            ),
            TransitionRule(
                "install-cut-edge-e1",
                _var("graph_built"),
                (
                    Assignment(
                        "cut_edges",
                        Expression.operator(
                            ExpressionKind.UNION,
                            _var("cut_edges"),
                            Expression.constant("e1"),
                        ),
                    ),
                ),
            ),
            TransitionRule(
                "install-cut-edge-e2",
                _var("graph_built"),
                (
                    Assignment(
                        "cut_edges",
                        Expression.operator(
                            ExpressionKind.UNION,
                            _var("cut_edges"),
                            Expression.constant("e2"),
                        ),
                    ),
                ),
            ),
            TransitionRule(
                "dispatch-past-cut",
                _and(
                    _var("graph_built"),
                    _and(
                        Expression.operator(
                            ExpressionKind.IN,
                            Expression.constant("e1"),
                            _var("cut_edges"),
                        ),
                        Expression.operator(
                            ExpressionKind.IN,
                            Expression.constant("e2"),
                            _var("cut_edges"),
                        ),
                    ),
                ),
                (Assignment("dispatched", _const(True)),),
            ),
            TransitionRule(
                "verify-effect-atoms",
                _var("dispatched"),
                (Assignment("effect_verified", _const(True)),),
            ),
        ),
        (
            SafetyInvariant(
                "no-uncut-flow-to-unsafe-terminal",
                _or(
                    _not(_var("dispatched")),
                    _and(
                        Expression.operator(
                            ExpressionKind.IN,
                            Expression.constant("e1"),
                            _var("cut_edges"),
                        ),
                        Expression.operator(
                            ExpressionKind.IN,
                            Expression.constant("e2"),
                            _var("cut_edges"),
                        ),
                    ),
                ),
                "Q: no call is dispatched while a represented flow edge to the unsafe terminal is uncut",
            ),
        ),
        5,
        (
            "PACE candidate abstraction native property: the path chain over a bounded enumerated cut set",
            "the graph is bounded to the two represented edges; the effect chain and the certificates are not modelled",
            "the cut set is a bounded set; membership is an IN test",
        ),
    )


__all__ = [
    "camel_ir",
    "camel_native_property_ir",
    "camelot_ir",
    "camelot_native_property_ir",
    "dual_llm_baseline_ir",
    "dual_llm_native_property_ir",
    "fides_ir",
    "fides_native_property_ir",
    "ites_defective_requester_only_ir",
    "ites_native_property_ir",
    "ites_reference_ir",
    "ites_with_read_check_ir",
    "pace_ir",
    "pace_native_property_ir",
    "pact_ir",
    "pact_native_property_ir",
    "progent_ir",
    "progent_native_property_ir",
]
