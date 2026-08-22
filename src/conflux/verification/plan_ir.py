"""Conservative finite abstraction of supported dynamic-plan effects."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import fingerprint
from conflux.planning import (
    ActionTemplateNode,
    ContinuePlanningNode,
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
) -> PlanAbstraction:
    """Conservatively abstract a dynamic plan into a serializable verification IR."""
    if bound < 1:
        raise ValueError("plan verification bound must be positive")
    summaries = {item.node_id: item for item in effect_summaries}
    unsupported: list[str] = []
    transitions: list[TransitionRule] = []
    step = Expression.variable("step")
    step_guard = Expression.operator(
        ExpressionKind.LESS_EQUAL,
        step,
        Expression.constant(bound - 1),
    )
    all_plans = (plan, *plan.subplans)
    for current in all_plans:
        for node in current.nodes:
            rule_id = f"{current.id}:{node.id}"
            assignments = [
                Assignment(
                    "step",
                    Expression.operator(
                        ExpressionKind.ADD,
                        step,
                        Expression.constant(1),
                    ),
                )
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
                                summary.executed and operation.operation == "execute_code" and not summary.within_capability_envelope
                            ),
                        ),
                    )
                )
            elif isinstance(node, ContinuePlanningNode):
                assignments.append(
                    Assignment(
                        "continuation_seen",
                        Expression.constant(True),
                    )
                )
            transitions.append(TransitionRule(rule_id, step_guard, tuple(assignments)))
    assumptions = (
        "every continuation produces only schema-valid patches within the declared node bound",
        "every grounded effect is mediated at action time by the canonical kernel",
        "generated code is abstracted by its declared capability effect summary",
        "arbitrary source-code semantics are not analysed",
    )
    if unsupported:
        return PlanAbstraction(None, assumptions, tuple(sorted(unsupported)))
    ir = VerificationIR(
        f"plan:{plan.id}",
        (
            StateVariable("step", Sort.INTEGER, 0, 0, bound),
            StateVariable("unauthorised_executed", Sort.BOOLEAN, False),
            StateVariable("capability_violated", Sort.BOOLEAN, False),
            StateVariable("context_narrowed", Sort.BOOLEAN, False),
            StateVariable("continuation_seen", Sort.BOOLEAN, False),
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
                }
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
