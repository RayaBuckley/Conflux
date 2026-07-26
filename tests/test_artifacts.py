"""
Tests for information artefacts.
These tests verify that artefacts remain immutable and that provenance is
propagated correctly when new derived artefacts are created.
"""
from conflux.core import Artifact, Principal, Provenance, Resource


def test_artifact_stores_value_and_provenance():
    alice = Principal("alice", "Alice")
    provenance = Provenance.from_principal(alice)
    artifact = Artifact(value="hello", provenance=provenance)
    assert artifact.value == "hello"
    assert artifact.provenance == provenance
def test_map_preserves_provenance_and_adds_operation():
    alice = Principal("alice", "Alice")
    provenance = Provenance.from_principal(alice)
    artifact = Artifact(value="hello", provenance=provenance)
    derived = artifact.map(value="HELLO", operation="uppercase")
    assert derived.value == "HELLO"
    assert derived.provenance.principals == frozenset({alice})
    assert derived.provenance.operations == frozenset({"uppercase"})
def test_combine_merges_provenance():
    alice = Principal("alice", "Alice")
    owner = Principal("owner", "Owner")
    resource = Resource("doc-1", "test", "document", "doc-1", owner=owner)
    left = Artifact(value="hello", provenance=Provenance.from_principal(alice))
    right = Artifact(value="world", provenance=Provenance.from_resource(resource))
    combined = Artifact.combine(left, right, value="hello world", operation="concat")
    assert combined.value == "hello world"
    assert combined.provenance.principals == frozenset({alice})
    assert combined.provenance.resources == frozenset({resource})
    assert combined.provenance.operations == frozenset({"concat"})
def test_map_is_immutable():
    alice = Principal("alice", "Alice")
    artifact = Artifact(
        value="hello",
        provenance=Provenance.from_principal(alice),
    )
    derived = artifact.map(value="HELLO", operation="uppercase")
    assert artifact.value == "hello"
    assert artifact.provenance.operations == frozenset()
    assert derived.provenance.operations == frozenset({"uppercase"})
def test_combine_is_immutable():
    alice = Principal("alice", "Alice")
    bob = Principal("bob", "Bob")
    left = Artifact(value="a", provenance=Provenance.from_principal(alice))
    right = Artifact(value="b", provenance=Provenance.from_principal(bob))
    combined = Artifact.combine(left, right, value="ab", operation="concat")
    assert left.provenance.principals == frozenset({alice})
    assert right.provenance.principals == frozenset({bob})
    assert combined.provenance.principals == frozenset({alice, bob})
