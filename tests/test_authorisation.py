"""
Tests for provenance-derived authorisation.
These tests define the security rule that will govern the rest of the system:
authorisation must be computed from provenance, not from the ambient execution
context.
"""
from conflux.auth import can_access, effective_authority
from conflux.core import Artifact, Principal, Provenance, Resource


def test_effective_authority_includes_all_contributing_principals():
    alice = Principal("alice", "Alice")
    bob = Principal("bob", "Bob")
    provenance = Provenance.from_principal(alice).merge(
        Provenance.from_principal(bob)
    )
    authority = effective_authority(provenance)
    assert authority == frozenset({alice, bob})
def test_effective_authority_with_single_principal():
    alice = Principal("alice", "Alice")
    provenance = Provenance.from_principal(alice)
    authority = effective_authority(provenance)
    assert authority == frozenset({alice})
def test_can_access_true_for_resource_owner():
    alice = Principal("alice", "Alice")
    resource = Resource("doc-1", "test", "document", "doc-1", owner=alice)
    artifact = Artifact(
        value="document contents",
        provenance=Provenance.from_principal(alice),
    )
    assert can_access(artifact.provenance, resource, "read") is True
def test_can_access_false_when_provenance_lacks_resource_owner():
    alice = Principal("alice", "Alice")
    bob = Principal("bob", "Bob")
    resource = Resource("doc-1", "test", "document", "doc-1", owner=alice)
    artifact = Artifact(
        value="document contents",
        provenance=Provenance.from_principal(bob),
    )
    assert can_access(artifact.provenance, resource, "read") is False
def test_can_access_requires_provenance_coverage_for_derived_data():
    alice = Principal("alice", "Alice")
    bob = Principal("bob", "Bob")
    resource = Resource("doc-1", "test", "document", "doc-1", owner=alice)
    base = Artifact(
        value="secret",
        provenance=Provenance.from_resource(resource),
    )
    derived = Artifact.combine(
        base,
        Artifact(value="public", provenance=Provenance.from_principal(bob)),
        value="secret-public",
        operation="combine",
    )
    assert can_access(derived.provenance, resource, "write") is False
