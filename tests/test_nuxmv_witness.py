"""Tests for the witness length a nuXmv refutation carries, and for the settled CEGAR verdict.

nuXmv's IC3 prints one execution sequence per refuted invariant. The length recorded here is the
number of states in that sequence. The sample text below is the format nuXmv 2.2.0 actually
printed on 2026-10-13, captured in writing/probe/nuxmv_ic3_trace_probe.out in the investigation
store (trailing whitespace trimmed; only the two marker lines matter to the parser).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conflux.verification import (
    Assignment,
    Expression,
    ExpressionKind,
    FormalVerdict,
    SafetyInvariant,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
)
from conflux.verification.nuxmv_backend import (
    NuXmvBackend,
    NuXmvOutcome,
    _predabs_verdict,
    _witness_lengths,
)

pytestmark = pytest.mark.security

REFUTATION = """nuXmv > nuXmv > nuXmv > -- invariant safe  is false
-- as demonstrated by the following execution sequence
Trace Description: IC3 counterexample
Trace Type: Counterexample
  -> State: 1.1 <-
    control = TRUE
    safe = TRUE
  -> State: 1.2 <-
    safe = FALSE
nuXmv >
"""


class _StubRunner:
    """A runner that returns fixed text instead of executing nuXmv."""

    def __init__(self, stdout: str) -> None:
        self.stdout = stdout
        self.commands: list[str] = []

    def run(self, binary: str, model_path: Path, commands: str) -> NuXmvOutcome:
        self.commands.append(commands)
        return NuXmvOutcome(0, self.stdout, "", "*** This is nuXmv 2.2.0 (stub)")


def _ir() -> VerificationIR:
    """A one-rule model; the runner is a stub, so the rule only has to make the IR renderable."""
    variable = StateVariable("safe", Sort.BOOLEAN, True)
    invariant = SafetyInvariant(
        "safe-remains-true",
        Expression(ExpressionKind.VARIABLE, "safe"),
        "safe stays true",
    )
    drop_safe = TransitionRule(
        "drop-safe",
        Expression(ExpressionKind.VARIABLE, "safe"),
        (Assignment("safe", Expression.constant(False)),),
    )
    return VerificationIR("witness-fixture", (variable,), (drop_safe,), (invariant,), 4)


def test_witness_lengths_counts_the_states_of_one_sequence() -> None:
    assert _witness_lengths(REFUTATION) == (2,)


def test_witness_lengths_counts_each_sequence_separately() -> None:
    second = REFUTATION.replace("1.1", "2.1").replace("1.2", "2.2") + "  -> State: 2.3 <-\n"
    assert _witness_lengths(REFUTATION + second) == (2, 3)


def test_witness_lengths_is_empty_when_no_sequence_is_printed() -> None:
    assert _witness_lengths("-- invariant safe  is false\nnuXmv >\n") == ()


def test_unsafe_result_records_the_witness_lengths() -> None:
    backend = NuXmvBackend(binary="nuXmv", runner=_StubRunner(REFUTATION), availability=lambda _binary: True)
    result = backend.verify(_ir())
    assert result.verdict is FormalVerdict.UNSAFE
    assert result.counterexample[0]["witness_lengths"] == [2]
    assert result.counterexample[0]["failed_invariants"] == 1


def test_safe_result_carries_no_trace_and_no_length() -> None:
    ir = _ir()
    stdout = "\n".join(f"-- invariant {invariant.id}  is true" for invariant in ir.invariants)
    backend = NuXmvBackend(binary="nuXmv", runner=_StubRunner(stdout), availability=lambda _binary: True)
    result = backend.verify(ir)
    assert result.verdict is FormalVerdict.SAFE
    assert result.counterexample == ()


# --- predicate-abstraction CEGAR: only the settled verdict counts (2026-10-17) ---
#
# The samples are the filtered transcript the O2b diagnostic recorded on 2026-10-17
# (writing/proofs/notes/2026-10-17-o2b-predabs-diagnostic.json); the marker lines are what the
# parser reads.

PREDABS_REFINEMENT = """nuXmv > nuXmv > nuXmv > -- invariant !maximality_violation  is false
Trace Description: AG alpha Counterexample
Trace Type: Counterexample
  -> State: 1.1 <-
    maximality_violation = FALSE
  -> State: 1.2 <-
    maximality_violation = TRUE
-- invariant !maximality_violation  is true
nuXmv >
"""

PREDABS_REFUTATION = """nuXmv > nuXmv > nuXmv > -- invariant !pe_violation  is false
Trace Description: IC3 counterexample
Trace Type: Counterexample
  -> State: 1.1 <-
    pe_violation = FALSE
  -> State: 1.2 <-
    pe_violation = TRUE
nuXmv >
"""

def test_predabs_verdict_reads_the_settled_line_after_a_spurious_counterexample() -> None:
    assert _predabs_verdict(PREDABS_REFINEMENT) == "true"


def test_predabs_verdict_reads_a_settled_refutation() -> None:
    assert _predabs_verdict(PREDABS_REFUTATION) == "false"


def test_predabs_verdict_is_empty_without_a_verdict_line() -> None:
    assert _predabs_verdict("nuXmv >\n") is None


def test_predabs_route_is_safe_when_the_settled_line_is_true() -> None:
    """Regression for 2026-10-17: a spurious leading ``is false`` made this route report unsafe."""
    backend = NuXmvBackend(binary="nuXmv", runner=_StubRunner(PREDABS_REFINEMENT), availability=lambda _binary: True)
    result = backend.verify(_ir(), predabs=True)
    assert result.verdict is FormalVerdict.SAFE
    assert result.backend == "nuxmv-predabs"


def test_predabs_route_is_unsafe_for_a_settled_refutation() -> None:
    backend = NuXmvBackend(binary="nuXmv", runner=_StubRunner(PREDABS_REFUTATION), availability=lambda _binary: True)
    result = backend.verify(_ir(), predabs=True)
    assert result.verdict is FormalVerdict.UNSAFE
    assert result.backend == "nuxmv-predabs"
