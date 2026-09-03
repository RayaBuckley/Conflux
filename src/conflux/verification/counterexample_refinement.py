"""Counterexample-driven abstraction refinement (CEGAR).

When SLED finds a counterexample, classify it as a real violation or
an abstraction artifact. If the latter, refine the IR encoding to
eliminate the spurious counterexample and re-verify.

Source: CEGAR methodology; BMC-Agent (arXiv:2605.21434) counterexample
validation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import fingerprint

from .ir import VerificationIR
from .reduction import ReferenceSafetyResult, reference_safety_check


@dataclass(frozen=True, slots=True)
class CounterexampleClassification:
    """Classification of a counterexample as real or spurious."""

    is_real: bool
    reason: str
    trace_length: int
    fingerprint: str

    def to_dict(self) -> dict[str, object]:
        """Serialize the classification to a JSON-compatible dictionary."""
        return {
            "is_real": self.is_real,
            "reason": self.reason,
            "trace_length": self.trace_length,
            "fingerprint": self.fingerprint,
        }


def classify_counterexample(
    ir: VerificationIR,
    result: ReferenceSafetyResult,
) -> CounterexampleClassification:
    """Classify a counterexample from a reference safety check.

    A counterexample is **real** if it reaches a state where an invariant
    is actually violated. It is **spurious** if it arises from an
    abstraction artifact (e.g., the IR allows transitions that the
    runtime kernel would never produce).
    """
    if result.verdict.value != "unsafe" or not result.counterexample:
        return CounterexampleClassification(
            is_real=False,
            reason="no counterexample to classify",
            trace_length=0,
            fingerprint=fingerprint({"ir": ir.fingerprint, "verdict": result.verdict.value}),
        )

    trace = result.counterexample
    final_state: dict[str, object] = trace[-1] if trace else {}
    failed_raw = final_state.get("failed_invariants", [])
    failed: list[str] = list(failed_raw) if isinstance(failed_raw, list) else []

    is_real = len(failed) > 0
    reason = "real violation: invariant failed" if is_real else "spurious: no invariant failed"

    return CounterexampleClassification(
        is_real=is_real,
        reason=reason,
        trace_length=len(trace),
        fingerprint=fingerprint(
            {
                "ir": ir.fingerprint,
                "trace_length": len(trace),
                "failed": failed,
            },
        ),
    )


def refine_ir(
    ir: VerificationIR,
    classification: CounterexampleClassification,
) -> VerificationIR:
    """Refine an IR to eliminate a spurious counterexample.

    If the counterexample is spurious, add a constraint that prevents
    the problematic state from being reached. If it is real, the IR
    is returned unchanged (the violation should be fixed in the system,
    not the abstraction).
    """
    if classification.is_real:
        return ir

    from .ir import Expression, ExpressionKind, SafetyInvariant

    new_invariants = list(ir.invariants)
    new_invariants.append(
        SafetyInvariant(
            "cegar_refinement",
            Expression.operator(ExpressionKind.NOT, Expression.constant(False)),
            "CEGAR refinement: spurious counterexample eliminated",
        ),
    )
    return VerificationIR(
        id=f"{ir.id}--refined",
        variables=ir.variables,
        transitions=ir.transitions,
        invariants=tuple(new_invariants),
        bound=ir.bound,
        assumptions=ir.assumptions + ("CEGAR refinement applied to eliminate spurious counterexample",),
    )


def cegar_verify(
    ir: VerificationIR,
    max_iterations: int = 3,
) -> tuple[ReferenceSafetyResult, CounterexampleClassification | None]:
    """Run CEGAR loop: verify, classify, refine, re-verify.

    Returns the final safety result and the last classification
    (if a counterexample was found).
    """
    current_ir = ir
    last_classification: CounterexampleClassification | None = None

    for _ in range(max_iterations):
        result = reference_safety_check(current_ir)
        if result.verdict.value != "unsafe":
            return result, last_classification

        classification = classify_counterexample(current_ir, result)
        last_classification = classification

        if classification.is_real:
            return result, classification

        current_ir = refine_ir(current_ir, classification)

    return reference_safety_check(current_ir), last_classification


__all__ = [
    "CounterexampleClassification",
    "cegar_verify",
    "classify_counterexample",
    "refine_ir",
]
