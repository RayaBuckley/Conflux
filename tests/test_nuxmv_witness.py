"""Tests for the witness length a nuXmv refutation now carries.

nuXmv's IC3 prints one execution sequence per refuted invariant. The length recorded here is the
number of states in that sequence. The sample text below is the format nuXmv 2.2.0 actually
printed on 2026-10-13, captured in writing/probe/nuxmv_ic3_trace_probe.out in the investigation
store (trailing whitespace trimmed; only the two marker lines matter to the parser).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conflux.verification import (
    Expression,
    ExpressionKind,
    FormalVerdict,
    SafetyInvariant,
    Sort,
    StateVariable,
    VerificationIR,
)
from conflux.verification.nuxmv_backend import NuXmvBackend, NuXmvOutcome, _witness_lengths

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
    variable = StateVariable("safe", Sort.BOOLEAN, True)
    invariant = SafetyInvariant(
        "safe-remains-true",
        Expression(ExpressionKind.VARIABLE, "safe"),
        "safe stays true",
    )
    return VerificationIR("witness-fixture", (variable,), (), (invariant,), 4)


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
