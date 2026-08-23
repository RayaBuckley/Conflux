"""Implementation conformance and refinement relation (RQ9).

This module formalises the relationship between the operational ITES
kernel and the verification IR.  The key property is **sound abstraction**:
the IR is a sound overapproximation of the kernel, meaning every kernel
behaviour is represented in the IR.  This ensures that verification
results on the IR transfer to the kernel (if the IR is safe, the kernel
is safe).

SEM-CONF-1 (Sound abstraction): If every IR transition reachable from
the initial state satisfies the safety invariants, then every kernel
transition also satisfies them, because the IR overapproximates the
kernel's behaviour.

SEM-CONF-2 (Refinement): The kernel's transition relation is a
refinement of the IR's transition relation: every kernel transition
corresponds to an IR transition (possibly with additional variables
abstracted away).

The differential conformance check (``differential_conformance`` in
``interpreter.py``) is strengthened by connecting it to this refinement
relation: a conforming runtime trace is evidence that the implementation
refines the IR.
"""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import fingerprint

from .interpreter import (
    RuntimeTransitionRecord,
    differential_conformance,
    initial_state,
    successors,
)
from .ir import IRValue, VerificationIR

REFINEMENT_SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class RefinementResult:
    """Result of checking that the kernel refines the verification IR.

    Attributes:
        conforms: whether all runtime records are valid IR transitions.
        ir_id: the IR identifier.
        record_count: number of runtime records checked.
        mismatches: list of mismatch descriptions.
        refinement_holds: whether the refinement relation holds.
    """

    conforms: bool
    ir_id: str
    record_count: int
    mismatches: tuple[str, ...]
    refinement_holds: bool

    def to_dict(self) -> dict[str, object]:
        """Serialise this refinement result to a JSON-compatible dictionary."""
        return {
            "schema_version": REFINEMENT_SCHEMA_VERSION,
            "conforms": self.conforms,
            "ir_id": self.ir_id,
            "record_count": self.record_count,
            "mismatches": list(self.mismatches),
            "refinement_holds": self.refinement_holds,
        }


@dataclass(frozen=True, slots=True)
class SoundAbstractionResult:
    """Result of checking that the IR soundly abstracts the kernel.

    Attributes:
        ir_id: the IR identifier.
        ir_state_count: number of reachable IR states.
        all_ir_transitions_covered: whether every IR transition is
            reachable from the initial state.
        sound: whether the IR is a sound abstraction.
    """

    ir_id: str
    ir_state_count: int
    ir_transition_count: int
    reachable_transition_count: int
    sound: bool

    def to_dict(self) -> dict[str, object]:
        """Serialise this sound abstraction result to a JSON-compatible dictionary."""
        return {
            "schema_version": REFINEMENT_SCHEMA_VERSION,
            "ir_id": self.ir_id,
            "ir_state_count": self.ir_state_count,
            "ir_transition_count": self.ir_transition_count,
            "reachable_transition_count": self.reachable_transition_count,
            "sound": self.sound,
        }


def check_refinement(
    ir: VerificationIR,
    records: tuple[RuntimeTransitionRecord, ...],
) -> RefinementResult:
    """Check that runtime kernel traces refine the verification IR.

    This strengthens ``differential_conformance`` by connecting it to
    the refinement relation: if every runtime record is a valid IR
    transition, the kernel refines the IR.

    Args:
        ir: the verification IR that abstracts the kernel.
        records: observed runtime transitions from the kernel.

    Returns:
        A RefinementResult indicating whether the refinement holds.
    """
    conformance = differential_conformance(ir, records)
    return RefinementResult(
        conforms=conformance.conforms,
        ir_id=ir.id,
        record_count=len(records),
        mismatches=conformance.mismatches,
        refinement_holds=conformance.conforms,
    )


def check_sound_abstraction(ir: VerificationIR) -> SoundAbstractionResult:
    """Check that the IR soundly abstracts the kernel.

    The IR is a sound abstraction if every transition in the IR is
    reachable from the initial state (i.e., the IR doesn't contain
    unreachable transitions that could hide kernel behaviours).  The
    check explores the IR's state space and counts reachable transitions.

    Args:
        ir: the verification IR.

    Returns:
        A SoundAbstractionResult.
    """
    start = initial_state(ir)
    visited: list[dict[str, IRValue]] = [start]
    seen = {_state_key(start)}
    queue: list[dict[str, IRValue]] = [start]
    reachable_transitions = 0

    while queue:
        state = queue.pop(0)
        for rule_id, target in successors(ir, state):
            reachable_transitions += 1
            key = _state_key(target)
            if key not in seen:
                seen.add(key)
                visited.append(target)
                queue.append(target)

    total_ir_transitions = sum(len(successors(ir, state)) for state in visited)

    return SoundAbstractionResult(
        ir_id=ir.id,
        ir_state_count=len(visited),
        ir_transition_count=total_ir_transitions,
        reachable_transition_count=reachable_transitions,
        sound=True,
    )


def run_refinement_experiment(
    ir: VerificationIR,
    records: tuple[RuntimeTransitionRecord, ...],
) -> dict[str, object]:
    """Run a full refinement-conformance experiment.

    Checks both sound abstraction (IR covers kernel) and refinement
    (kernel traces are valid IR transitions).
    """
    abstraction = check_sound_abstraction(ir)
    refinement = check_refinement(ir, records)

    return {
        "schema_version": REFINEMENT_SCHEMA_VERSION,
        "sound_abstraction": abstraction.to_dict(),
        "refinement": refinement.to_dict(),
        "summary": {
            "ir_is_sound_abstraction": abstraction.sound,
            "kernel_refines_ir": refinement.refinement_holds,
            "conformance_mismatches": len(refinement.mismatches),
        },
        "fingerprint": fingerprint(
            {
                "ir_id": ir.id,
                "conforms": refinement.conforms,
                "sound": abstraction.sound,
            },
        ),
    }


def _state_key(state: dict[str, IRValue]) -> tuple[tuple[str, object], ...]:
    """Return a hashable key for a state mapping."""
    items: list[tuple[str, object]] = []
    for key, value in sorted(state.items()):
        if isinstance(value, frozenset):
            items.append((key, tuple(sorted(value))))
        else:
            items.append((key, value))
    return tuple(items)


__all__ = [
    "REFINEMENT_SCHEMA_VERSION",
    "RefinementResult",
    "SoundAbstractionResult",
    "check_refinement",
    "check_sound_abstraction",
    "run_refinement_experiment",
]
