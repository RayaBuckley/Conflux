"""Conservative finite abstraction of supported dynamic-plan effects."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import fingerprint
from conflux.planning import (
    ActionTemplateNode,
    ContinuePlanningNode,
    DelegationNode,
    OperationCatalogue,
    Plan,
)

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
from .nuxmv_backend import NuXmvBackend
from .results import FormalVerdict, FormalVerificationResult
from .z3_backend import verify_with_z3


@dataclass(frozen=True, slots=True)
class EffectSummary:
    """Summary of a plan node's authorisation and execution status."""

    node_id: str
    authorised: bool
    executed: bool
    within_capability_envelope: bool = True


@dataclass(frozen=True, slots=True)
class PlanAbstraction:
    """Result of abstracting a dynamic plan into a verification IR or unsupported list."""

    ir: VerificationIR | None
    assumptions: tuple[str, ...]
    unsupported: tuple[str, ...]

    @property
    def supported(self) -> bool:
        """Return True if the plan was fully abstracted without unsupported features."""
        return self.ir is not None and not self.unsupported


def abstract_plan(
    plan: Plan,
    *,
    catalogue: OperationCatalogue,
    effect_summaries: tuple[EffectSummary, ...],
    bound: int,
    unbounded_step: bool = False,
    goal_nodes: tuple[str, ...] = (),
    abort_nodes: tuple[str, ...] = (),
) -> PlanAbstraction:
    """Conservatively abstract a dynamic plan into a serializable verification IR.

    ``unbounded_step`` drops the declared range on the step counter while keeping every
    guard, so an SMT backend can prove the invariants for a symbolic bound. The default
    keeps the range, and therefore keeps every recorded bounded row unchanged.

    ``goal_nodes`` and ``abort_nodes`` name plan nodes as the two ways a run may end well:
    the node that reaches the plan's goal, and a node that stops without the goal but
    without an unauthorised effect. Declaring either adds the ``goal_reached`` and
    ``safe_abort`` state variables and the obligation ``step >= bound -> (goal_reached or
    safe_abort)``, so a run that spends its bound without reaching either endpoint is
    refuted instead of ending on the abstraction's own ``terminated`` assignment. When
    neither is declared the abstraction is identical to the one that omits them, so every
    recorded bounded row stays unchanged.
    """
    if bound < 1:
        raise ValueError("plan verification bound must be positive")
    overlap = sorted(set(goal_nodes) & set(abort_nodes))
    if overlap:
        raise ValueError(f"a plan node cannot be both a goal and an abort: {', '.join(overlap)}")
    declared_nodes = {node.id for current in (plan, *plan.subplans) for node in current.nodes}
    unknown_endpoints = sorted((set(goal_nodes) | set(abort_nodes)) - declared_nodes)
    if unknown_endpoints:
        raise ValueError(f"unknown plan endpoint node: {', '.join(unknown_endpoints)}")
    progress = bool(goal_nodes or abort_nodes)
    summaries = {item.node_id: item for item in effect_summaries}
    unsupported: list[str] = []
    transitions: list[TransitionRule] = []
    step = Expression.variable("step")
    step_guard = Expression.operator(
        ExpressionKind.LESS_EQUAL,
        step,
        Expression.constant(bound - 1),
    )
    step_bound_reached = Expression.operator(
        ExpressionKind.GREATER_EQUAL,
        step,
        Expression.constant(bound - 1),
    )
    all_plans = (plan, *plan.subplans)
    for current in all_plans:
        for node in current.nodes:
            rule_id = f"{current.id}:{node.id}"
            assignments: list[Assignment] = [
                Assignment(
                    "step",
                    Expression.operator(
                        ExpressionKind.ADD,
                        step,
                        Expression.constant(1),
                    ),
                ),
                Assignment(
                    "terminated",
                    step_bound_reached,
                ),
            ]
            if isinstance(node, ActionTemplateNode):
                try:
                    operation = catalogue.resolve(
                        node.template.operation_id,
                        node.template.operation_version,
                    )
                except ValueError:
                    unsupported.append(f"{rule_id}:unknown_operation")
                    continue
                summary = summaries.get(node.id)
                if summary is None:
                    unsupported.append(f"{rule_id}:missing_effect_summary")
                    continue
                assignments.extend(
                    (
                        Assignment(
                            "unauthorised_executed",
                            Expression.constant(summary.executed and not summary.authorised),
                        ),
                        Assignment(
                            "capability_violated",
                            Expression.constant(
                                summary.executed and operation.operation == "execute_code" and not summary.within_capability_envelope,
                            ),
                        ),
                    ),
                )
                if summary.executed and not summary.authorised:
                    assignments.append(
                        Assignment("revocation_received", Expression.constant(True)),
                    )
            elif isinstance(node, ContinuePlanningNode):
                assignments.append(
                    Assignment(
                        "continuation_seen",
                        Expression.constant(True),
                    ),
                )
            elif isinstance(node, DelegationNode):
                assignments.extend(
                    (
                        Assignment("delegation_consumed", Expression.constant(True)),
                        Assignment("delegation_authority_gained", Expression.constant(True)),
                    ),
                )
            if progress:
                if node.id in goal_nodes:
                    node_summary = summaries.get(node.id)
                    reached = node_summary.executed if isinstance(node, ActionTemplateNode) and node_summary else True
                    assignments.append(Assignment("goal_reached", Expression.constant(reached)))
                if node.id in abort_nodes:
                    assignments.append(Assignment("safe_abort", Expression.constant(True)))
            transitions.append(TransitionRule(rule_id, step_guard, tuple(assignments)))
    assumptions: tuple[str, ...] = (
        "every continuation produces only schema-valid patches within the declared node bound",
        "every grounded effect is mediated at action time by the canonical kernel",
        "generated code is abstracted by its declared capability effect summary",
        "arbitrary source-code semantics are not analysed",
        "context_narrowed models continuation patches that drop principals from context",
        "authority_set models monotonic confinement per Progent arXiv:2504.11703",
        "revocation_received models mid-plan revocation blocking downstream effects",
        "terminated models bounded liveness per arXiv:2510.14133",
    )
    if progress:
        assumptions = assumptions + (
            "goal_reached and safe_abort are assigned from the plan's declared endpoint nodes and each action "
            "node's recorded effect summary, not chosen by the model",
        )
    if unsupported:
        return PlanAbstraction(None, assumptions, tuple(sorted(unsupported)))
    endpoint_variables = (
        (
            StateVariable("goal_reached", Sort.BOOLEAN, False),
            StateVariable("safe_abort", Sort.BOOLEAN, False),
        )
        if progress
        else ()
    )
    endpoint_invariants = (
        (
            SafetyInvariant(
                "bounded-progress",
                Expression.operator(
                    ExpressionKind.IMPLIES,
                    Expression.operator(
                        ExpressionKind.GREATER_EQUAL,
                        Expression.variable("step"),
                        Expression.constant(bound),
                    ),
                    Expression.operator(
                        ExpressionKind.OR,
                        Expression.variable("goal_reached"),
                        Expression.variable("safe_abort"),
                    ),
                ),
            ),
            SafetyInvariant(
                "safe-abort-clean",
                Expression.operator(
                    ExpressionKind.IMPLIES,
                    Expression.variable("safe_abort"),
                    Expression.operator(
                        ExpressionKind.NOT,
                        Expression.variable("unauthorised_executed"),
                    ),
                ),
            ),
            SafetyInvariant(
                "goal-reached-clean",
                Expression.operator(
                    ExpressionKind.IMPLIES,
                    Expression.variable("goal_reached"),
                    Expression.operator(
                        ExpressionKind.NOT,
                        Expression.variable("unauthorised_executed"),
                    ),
                ),
            ),
        )
        if progress
        else ()
    )
    ir = VerificationIR(
        f"plan:{plan.id}" + (":progress" if progress else ""),
        (
            StateVariable("step", Sort.INTEGER, 0, 0, None if unbounded_step else bound),
            StateVariable("unauthorised_executed", Sort.BOOLEAN, False),
            StateVariable("capability_violated", Sort.BOOLEAN, False),
            StateVariable("context_narrowed", Sort.BOOLEAN, False),
            StateVariable("continuation_seen", Sort.BOOLEAN, False),
            StateVariable("delegation_consumed", Sort.BOOLEAN, False),
            StateVariable("delegation_authority_gained", Sort.BOOLEAN, False),
            StateVariable("authority_set", Sort.INTEGER, 0, 0, bound),
            StateVariable("revocation_received", Sort.BOOLEAN, False),
            StateVariable("terminated", Sort.BOOLEAN, False),
            *endpoint_variables,
        ),
        tuple(transitions),
        (
            SafetyInvariant(
                "no-unauthorised-execution",
                Expression.operator(
                    ExpressionKind.NOT,
                    Expression.variable("unauthorised_executed"),
                ),
            ),
            SafetyInvariant(
                "capability-envelope-preserved",
                Expression.operator(
                    ExpressionKind.NOT,
                    Expression.variable("capability_violated"),
                ),
            ),
            SafetyInvariant(
                "principal-context-monotonic",
                Expression.operator(
                    ExpressionKind.NOT,
                    Expression.variable("context_narrowed"),
                ),
            ),
            SafetyInvariant(
                "delegation-authority-requires-grant",
                Expression.operator(
                    ExpressionKind.IMPLIES,
                    Expression.variable("delegation_authority_gained"),
                    Expression.variable("delegation_consumed"),
                ),
            ),
            SafetyInvariant(
                "monotonic-confinement",
                Expression.operator(
                    ExpressionKind.NOT,
                    Expression.variable("unauthorised_executed"),
                ),
            ),
            SafetyInvariant(
                "revocation-propagation",
                Expression.operator(
                    ExpressionKind.IMPLIES,
                    Expression.variable("revocation_received"),
                    Expression.operator(
                        ExpressionKind.NOT,
                        Expression.variable("unauthorised_executed"),
                    ),
                ),
            ),
            SafetyInvariant(
                "bounded-liveness",
                Expression.operator(
                    ExpressionKind.IMPLIES,
                    Expression.operator(
                        ExpressionKind.GREATER_EQUAL,
                        Expression.variable("step"),
                        Expression.constant(bound),
                    ),
                    Expression.variable("terminated"),
                ),
            ),
            *endpoint_invariants,
        ),
        bound,
        assumptions,
    )
    return PlanAbstraction(ir, assumptions, ())


def verify_plan(
    plan: Plan,
    *,
    catalogue: OperationCatalogue,
    effect_summaries: tuple[EffectSummary, ...],
    bound: int,
    backend: str = "z3",
) -> FormalVerificationResult:
    """Abstract a plan and verify it with the selected formal backend."""
    abstraction = abstract_plan(
        plan,
        catalogue=catalogue,
        effect_summaries=effect_summaries,
        bound=bound,
    )
    if abstraction.ir is None:
        return FormalVerificationResult(
            FormalVerdict.UNKNOWN,
            f"plan-{backend}",
            fingerprint(plan.to_dict()),
            fingerprint(
                {
                    "plan": plan.fingerprint,
                    "bound": bound,
                    "unsupported": abstraction.unsupported,
                },
            ),
            fingerprint({"backend": backend, "version": "not-invoked"}),
            None,
            bound,
            abstraction.assumptions,
            error=f"unsupported_plan_abstraction:{','.join(abstraction.unsupported)}",
        )
    if backend == "z3":
        return verify_with_z3(abstraction.ir)
    if backend == "nuxmv":
        return NuXmvBackend().verify(abstraction.ir)
    return FormalVerificationResult(
        FormalVerdict.UNKNOWN,
        f"plan-{backend}",
        abstraction.ir.fingerprint,
        fingerprint({"backend": backend, "ir": abstraction.ir.fingerprint}),
        fingerprint({"backend": backend, "version": "unsupported"}),
        None,
        bound,
        abstraction.assumptions,
        error=f"unsupported_verification_backend:{backend}",
    )


__all__ = [
    "EffectSummary",
    "PlanAbstraction",
    "abstract_plan",
    "verify_plan",
]
