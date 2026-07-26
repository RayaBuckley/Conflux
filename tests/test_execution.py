"""
Tests for the execution layer.
These tests lock in the invariant that execution produces new artefacts rather
than mutating existing ones, and that provenance is carried forward through
operations.
"""
from __future__ import annotations

from dataclasses import dataclass

from conflux.core import Artifact, Principal, Provenance
from conflux.execution.operations import Operation


@dataclass(frozen=True, slots=True)
class UppercaseOperation(Operation[str, str]):
    def run(self, artifact: Artifact[str]) -> Artifact[str]:
        return Artifact(
            value=artifact.value.upper(),
            provenance=artifact.provenance.with_operation(self.name),
        )
def test_operation_produces_new_artifact():
    alice = Principal("alice", "Alice")
    artifact = Artifact(
        value="hello",
        provenance=Provenance.from_principal(alice),
    )
    op = UppercaseOperation(name="uppercase")
    result = op.run(artifact)
    assert result.value == "HELLO"
    assert result.provenance.principals == frozenset({alice})
    assert result.provenance.operations == frozenset({"uppercase"})
def test_operation_does_not_mutate_input_artifact():
    alice = Principal("alice", "Alice")
    artifact = Artifact(
        value="hello",
        provenance=Provenance.from_principal(alice),
    )
    op = UppercaseOperation(name="uppercase")
    result = op.run(artifact)
    assert artifact.value == "hello"
    assert artifact.provenance.operations == frozenset()
    assert result is not artifact
def test_operation_name_is_preserved():
    op = UppercaseOperation(name="uppercase")
    assert op.name == "uppercase"
