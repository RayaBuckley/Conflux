"""Property-sensitivity classification for verification IRs.

A holding invariant is evidence only if something can break it.  This module
classifies every invariant of an IR against a declared mutation alphabet, so a
verdict of ``safe`` can be reported together with how the property was
exercised.

Declared mutation alphabet (the only mutations used here): for one transition
rule at a time, replace that rule's guard with the constant ``True``.  No
assignment is edited, no rule is added or removed, and the bound is unchanged.
Every class below is relative to this alphabet.

Classes for an invariant that holds at baseline:

``checked``
    Some guard mutation of a rule whose guard is satisfied by at least one
    reachable state of the unmodified IR falsifies the invariant.
``checked_by_construction``
    Guard mutations falsify it, but only rules whose guard is unsatisfied in
    every reachable state of the unmodified IR - the mutation creates the
    reachability, so the reference model holds the property by construction.
``violated_at_baseline``
    Some reachable state of the unmodified IR already fails it (the verdict is
    then ``unsafe``, and this module reports the class for completeness).

The falsifiers are reported individually with the guard-satisfiability flag, so
the class can be audited without re-running the classification.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, replace
from typing import Any

from .interpreter import evaluate, initial_state, successors
from .ir import Expression, IRValue, VerificationIR

CLASS_CHECKED = "checked"
CLASS_CHECKED_BY_CONSTRUCTION = "checked_by_construction"
CLASS_VIOLATED_AT_BASELINE = "violated_at_baseline"


def _state_key(state: dict[str, IRValue]) -> tuple[tuple[str, IRValue], ...]:
    return tuple(sorted(state.items()))


def reachable_states(ir: VerificationIR) -> tuple[dict[str, IRValue], ...]:
    """Every state reachable within the IR's bound, in discovery order."""
    start = initial_state(ir)
    seen = {_state_key(start)}
    pending: list[tuple[dict[str, IRValue], int]] = [(start, 0)]
    states: list[dict[str, IRValue]] = [start]
    while pending:
        state, depth = pending.pop()
        if depth >= ir.bound:
            continue
        for _rule_id, target in successors(ir, state):
            key = _state_key(target)
            if key in seen:
                continue
            seen.add(key)
            states.append(target)
            pending.append((target, depth + 1))
    return tuple(states)


def guard_mutations(ir: VerificationIR) -> Iterator[tuple[str, VerificationIR]]:
    """Yield ``(rule_id, mutated_ir)`` with that one rule's guard replaced by True."""
    for rule in ir.transitions:
        mutated = replace(
            ir,
            transitions=tuple(
                replace(other, guard=Expression.constant(True)) if other.id == rule.id else other
                for other in ir.transitions
            ),
        )
        yield rule.id, mutated


@dataclass(frozen=True, slots=True)
class MutationFalsifier:
    """One guard mutation that falsifies an invariant."""

    rule_id: str
    guard_satisfiable_at_reachable_state: bool

    def to_dict(self) -> dict[str, Any]:
        """Serialize this falsifier to a JSON-compatible dictionary."""
        return {
            "rule_id": self.rule_id,
            "guard_satisfiable_at_reachable_state": self.guard_satisfiable_at_reachable_state,
        }


@dataclass(frozen=True, slots=True)
class InvariantSensitivity:
    """The exercise class of one invariant under the declared mutation alphabet."""

    invariant_id: str
    exercise_class: str
    falsifiers: tuple[MutationFalsifier, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize this classification to a JSON-compatible dictionary."""
        return {
            "invariant_id": self.invariant_id,
            "exercise_class": self.exercise_class,
            "falsifiers": [falsifier.to_dict() for falsifier in self.falsifiers],
        }


def _falsified(ir: VerificationIR, expression: Expression) -> bool:
    return any(evaluate(expression, state) is not True for state in reachable_states(ir))


def classify_invariant(ir: VerificationIR, invariant_id: str) -> InvariantSensitivity:
    """Classify one invariant of ``ir`` under the declared mutation alphabet."""
    invariant = next(item for item in ir.invariants if item.id == invariant_id)
    if _falsified(ir, invariant.expression):
        return InvariantSensitivity(invariant_id, CLASS_VIOLATED_AT_BASELINE, ())
    baseline = reachable_states(ir)
    guards_satisfied = {
        rule.id: any(evaluate(rule.guard, state) is True for state in baseline) for rule in ir.transitions
    }
    falsifiers = tuple(
        MutationFalsifier(rule_id, guards_satisfied[rule_id])
        for rule_id, mutated in guard_mutations(ir)
        if _falsified(mutated, invariant.expression)
    )
    exercise_class = (
        CLASS_CHECKED
        if any(falsifier.guard_satisfiable_at_reachable_state for falsifier in falsifiers)
        else CLASS_CHECKED_BY_CONSTRUCTION
    )
    return InvariantSensitivity(invariant_id, exercise_class, falsifiers)


def classify_ir(ir: VerificationIR) -> tuple[InvariantSensitivity, ...]:
    """Classify every invariant of ``ir`` under the declared mutation alphabet."""
    return tuple(classify_invariant(ir, invariant.id) for invariant in ir.invariants)


def classification_document(named_irs: dict[str, VerificationIR]) -> dict[str, Any]:
    """Build the JSON-ready classification document for named IRs."""
    return {
        "schema_version": "1",
        "mutation_alphabet": "replace_one_rule_guard_with_true",
        "irs": {
            name: {
                "ir_id": ir.id,
                "bound": ir.bound,
                "reachable_states": len(reachable_states(ir)),
                "invariants": [item.to_dict() for item in classify_ir(ir)],
            }
            for name, ir in sorted(named_irs.items())
        },
    }
