"""Property-scoped cone-of-influence reduction for the verification IR."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace

from conflux.domain import fingerprint

from .interpreter import evaluate, initial_state, successors
from .ir import Expression, ExpressionKind, Scalar, VerificationIR
from .results import FormalVerdict

REDUCTION_SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class WitnessLiftingEvidence:
    """Evidence that a reduced-model witness can be lifted to the original."""

    strategy: str
    rule_ids_preserved: bool
    projected_variables: tuple[str, ...]
    validated: bool | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize this witness-lifting evidence to a JSON-compatible dictionary."""
        return {
            "strategy": self.strategy,
            "rule_ids_preserved": self.rule_ids_preserved,
            "projected_variables": list(self.projected_variables),
            "validated": self.validated,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class VerificationReduction:
    """A cone-of-influence reduction of a verification IR."""

    original_fingerprint: str
    reduced_fingerprint: str
    reduced_ir: VerificationIR
    invariant_ids: tuple[str, ...]
    retained_variables: tuple[str, ...]
    removed_variables: tuple[str, ...]
    retained_rules: tuple[str, ...]
    removed_rules: tuple[str, ...]
    assumptions: tuple[str, ...]
    applicable: bool
    reason: str | None
    witness_lifting: WitnessLiftingEvidence
    schema_version: str = REDUCTION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        """Serialize this reduction to a JSON-compatible dictionary."""
        return {
            "schema_version": self.schema_version,
            "original_fingerprint": self.original_fingerprint,
            "reduced_fingerprint": self.reduced_fingerprint,
            "invariant_ids": list(self.invariant_ids),
            "retained_variables": list(self.retained_variables),
            "removed_variables": list(self.removed_variables),
            "retained_rules": list(self.retained_rules),
            "removed_rules": list(self.removed_rules),
            "assumptions": list(self.assumptions),
            "applicable": self.applicable,
            "reason": self.reason,
            "witness_lifting": self.witness_lifting.to_dict(),
            "reduced_ir": self.reduced_ir.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReferenceSafetyResult:
    """The outcome of a reference breadth-first bounded safety check."""

    verdict: FormalVerdict
    states: int
    transitions: int
    duplicate_states: int
    counterexample: tuple[dict[str, object], ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Serialize this reference safety result to a JSON-compatible dictionary."""
        return {
            "verdict": self.verdict.value,
            "states": self.states,
            "transitions": self.transitions,
            "duplicate_states": self.duplicate_states,
            "counterexample": list(self.counterexample),
        }


@dataclass(frozen=True, slots=True)
class ReductionComparison:
    """Comparison of original and reduced reference safety checks with witness lifting."""

    reduction: VerificationReduction
    original: ReferenceSafetyResult
    reduced: ReferenceSafetyResult
    equivalent: bool
    failure: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize this reduction comparison to a JSON-compatible dictionary."""
        return {
            "schema_version": REDUCTION_SCHEMA_VERSION,
            "reduction": self.reduction.to_dict(),
            "original": self.original.to_dict(),
            "reduced": self.reduced.to_dict(),
            "equivalent": self.equivalent,
            "failure": self.failure,
        }


def expression_variables(expression: Expression) -> frozenset[str]:
    """Return every state variable read by an expression."""

    direct = {expression.value} if expression.kind == ExpressionKind.VARIABLE and isinstance(expression.value, str) else set()
    for argument in expression.arguments:
        direct.update(expression_variables(argument))
    return frozenset(direct)


def reduce_cone_of_influence(
    ir: VerificationIR,
    invariant_ids: tuple[str, ...],
) -> VerificationReduction:
    """Project *ir* onto the dependency closure of selected safety properties."""

    selected_ids = invariant_ids or tuple(item.id for item in ir.invariants)
    if len(selected_ids) != len(set(selected_ids)):
        raise ValueError("selected invariant IDs must be unique")
    by_id = {item.id: item for item in ir.invariants}
    unknown = sorted(set(selected_ids) - set(by_id))
    if unknown:
        raise ValueError(f"unknown verification invariants: {unknown}")
    selected = tuple(by_id[identifier] for identifier in selected_ids)
    relevant: set[str] = set()
    for invariant in selected:
        relevant.update(expression_variables(invariant.expression))
    assumptions = (
        "selected properties are state safety invariants",
        "transition assignments are simultaneous",
        "omitted rules stutter on every retained variable",
        "rule identifiers are stable witness labels",
    )
    if not selected:
        return _unchanged(ir, selected_ids, assumptions, "no_invariants_selected")
    if not relevant:
        return _unchanged(
            ir,
            selected_ids,
            assumptions,
            "selected_invariants_have_no_state_variables",
        )

    changed = True
    while changed:
        changed = False
        for rule in ir.transitions:
            relevant_assignments = tuple(assignment for assignment in rule.assignments if assignment.variable in relevant)
            if not relevant_assignments:
                continue
            dependencies = set(expression_variables(rule.guard))
            for assignment in relevant_assignments:
                dependencies.update(expression_variables(assignment.expression))
            before = len(relevant)
            relevant.update(dependencies)
            changed = changed or len(relevant) != before

    retained_variables = tuple(variable for variable in ir.variables if variable.name in relevant)
    retained_rules = tuple(
        replace(
            rule,
            assignments=tuple(assignment for assignment in rule.assignments if assignment.variable in relevant),
        )
        for rule in ir.transitions
        if any(assignment.variable in relevant for assignment in rule.assignments)
    )
    removed_variable_names = tuple(sorted({item.name for item in ir.variables} - relevant))
    retained_rule_ids = tuple(sorted(rule.id for rule in retained_rules))
    removed_rule_ids = tuple(sorted({item.id for item in ir.transitions} - set(retained_rule_ids)))
    if not removed_variable_names and not removed_rule_ids and len(selected) == len(ir.invariants):
        return _unchanged(ir, selected_ids, assumptions, "cone_is_already_complete")
    reduced = replace(
        ir,
        id=f"{ir.id}--coi--{fingerprint(selected_ids)[:12]}",
        variables=retained_variables,
        transitions=retained_rules,
        invariants=selected,
    )
    retained_variable_names = tuple(sorted(relevant))
    return VerificationReduction(
        ir.fingerprint,
        reduced.fingerprint,
        reduced,
        selected_ids,
        retained_variable_names,
        removed_variable_names,
        retained_rule_ids,
        removed_rule_ids,
        assumptions,
        True,
        None,
        WitnessLiftingEvidence(
            "preserved_rule_sequence_with_original_state_replay",
            True,
            retained_variable_names,
        ),
    )


def compare_cone_of_influence(
    ir: VerificationIR,
    invariant_ids: tuple[str, ...],
) -> ReductionComparison:
    """Check original/reduced reference verdicts and lift a reduced witness."""

    reduction = reduce_cone_of_influence(ir, invariant_ids)
    selected_original = replace(
        ir,
        invariants=tuple(item for item in ir.invariants if item.id in reduction.invariant_ids),
    )
    original = reference_safety_check(selected_original)
    reduced = reference_safety_check(reduction.reduced_ir)
    failure: str | None = None
    lifted: bool | None = None
    lift_reason: str | None = None
    if original.verdict != reduced.verdict:
        failure = "reference_verdict_disagreement"
    elif reduced.verdict == FormalVerdict.UNSAFE:
        lifted = _lift_counterexample(
            selected_original,
            reduction.reduced_ir,
            reduced.counterexample,
        )
        if not lifted:
            failure = "counterexample_not_liftable"
            lift_reason = failure
    reduction = replace(
        reduction,
        witness_lifting=replace(
            reduction.witness_lifting,
            validated=lifted,
            reason=lift_reason,
        ),
    )
    return ReductionComparison(
        reduction,
        original,
        reduced,
        failure is None,
        failure,
    )


def reference_safety_check(ir: VerificationIR) -> ReferenceSafetyResult:
    """Explore the bounded IR breadth-first and retain a shortest violation."""

    start = initial_state(ir)
    start_key = _state_key(start)
    queue: deque[tuple[dict[str, Scalar], int]] = deque(((start, 0),))
    visited = {start_key}
    predecessor: dict[
        tuple[tuple[str, Scalar], ...],
        tuple[tuple[tuple[str, Scalar], ...], str] | None,
    ] = {start_key: None}
    states = {start_key: start}
    transition_count = 0
    duplicate_count = 0
    truncated = False
    while queue:
        state, depth = queue.popleft()
        state_key = _state_key(state)
        failed = tuple(invariant.id for invariant in ir.invariants if evaluate(invariant.expression, state) is not True)
        if failed:
            return ReferenceSafetyResult(
                FormalVerdict.UNSAFE,
                len(visited),
                transition_count,
                duplicate_count,
                _counterexample(state_key, states, predecessor, failed),
            )
        for rule_id, target in successors(ir, state):
            transition_count += 1
            target_key = _state_key(target)
            if target_key in visited:
                duplicate_count += 1
                continue
            if depth >= ir.bound:
                truncated = True
                continue
            visited.add(target_key)
            states[target_key] = target
            predecessor[target_key] = (state_key, rule_id)
            queue.append((target, depth + 1))
    return ReferenceSafetyResult(
        FormalVerdict.BOUNDED_SAFE if truncated else FormalVerdict.SAFE,
        len(visited),
        transition_count,
        duplicate_count,
    )


def _unchanged(
    ir: VerificationIR,
    invariant_ids: tuple[str, ...],
    assumptions: tuple[str, ...],
    reason: str,
) -> VerificationReduction:
    variables = tuple(sorted(item.name for item in ir.variables))
    rules = tuple(sorted(item.id for item in ir.transitions))
    return VerificationReduction(
        ir.fingerprint,
        ir.fingerprint,
        ir,
        invariant_ids,
        variables,
        (),
        rules,
        (),
        assumptions,
        False,
        reason,
        WitnessLiftingEvidence(
            "unchanged_model",
            True,
            variables,
            validated=None,
            reason=reason,
        ),
    )


def _state_key(state: dict[str, Scalar]) -> tuple[tuple[str, Scalar], ...]:
    return tuple(sorted(state.items()))


def _counterexample(
    target: tuple[tuple[str, Scalar], ...],
    states: dict[tuple[tuple[str, Scalar], ...], dict[str, Scalar]],
    predecessor: dict[
        tuple[tuple[str, Scalar], ...],
        tuple[tuple[tuple[str, Scalar], ...], str] | None,
    ],
    failed: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    path: list[tuple[tuple[tuple[str, Scalar], ...], str | None]] = []
    cursor = target
    while True:
        previous = predecessor[cursor]
        path.append((cursor, None if previous is None else previous[1]))
        if previous is None:
            break
        cursor = previous[0]
    path.reverse()
    return tuple(
        {
            "step": index,
            "rule_id": None if index == 0 else rule_id,
            "state": dict(states[key]),
            "failed_invariants": list(failed) if index == len(path) - 1 else [],
        }
        for index, (key, rule_id) in enumerate(path)
    )


def _lift_counterexample(
    original: VerificationIR,
    reduced: VerificationIR,
    witness: tuple[dict[str, object], ...],
) -> bool:
    state = initial_state(original)
    reduced_names = {item.name for item in reduced.variables}
    if not witness or {name: value for name, value in state.items() if name in reduced_names} != witness[0].get("state"):
        return False
    for step in witness[1:]:
        rule_id = step.get("rule_id")
        candidates = [target for current_rule_id, target in successors(original, state) if current_rule_id == rule_id]
        if len(candidates) != 1:
            return False
        state = candidates[0]
        projection = {name: value for name, value in state.items() if name in reduced_names}
        if projection != step.get("state"):
            return False
    return any(evaluate(item.expression, state) is not True for item in original.invariants)


__all__ = [
    "REDUCTION_SCHEMA_VERSION",
    "ReductionComparison",
    "ReferenceSafetyResult",
    "VerificationReduction",
    "WitnessLiftingEvidence",
    "compare_cone_of_influence",
    "expression_variables",
    "reduce_cone_of_influence",
    "reference_safety_check",
]
