"""
Tests for provenance tracking.
These tests verify the core security properties of the provenance model.
"""
from conflux.core import (
    Principal,
    Provenance,
    Resource,
)


def test_merge_combines_principals():
    alice = Principal("alice", "Alice")
    bob = Principal("bob", "Bob")
    p1 = Provenance.from_principal(alice)
    p2 = Provenance.from_principal(bob)
    merged = p1.merge(p2)
    assert merged.principals == frozenset({alice, bob})
def test_merge_combines_resources():
    owner = Principal("owner", "Owner")
    file_a = Resource("file_a", "test", "file", "file_a", owner=owner)
    file_b = Resource("file_b", "test", "file", "file_b", owner=owner)
    p1 = Provenance.from_resource(file_a)
    p2 = Provenance.from_resource(file_b)
    merged = p1.merge(p2)
    assert merged.resources == frozenset({file_a, file_b})
def test_merge_preserves_existing_information():
    alice = Principal("alice", "Alice")
    owner = Principal("owner", "Owner")
    resource = Resource("document", "test", "document", "document", owner=owner)
    p1 = Provenance.from_principal(alice)
    p2 = Provenance.from_resource(resource)
    merged = p1.merge(p2)
    assert alice in merged.principals
    assert resource in merged.resources
def test_with_operation_adds_operation():
    provenance = Provenance()
    updated = provenance.with_operation("summarise")
    assert updated.operations == frozenset({"summarise"})
def test_merge_is_immutable():
    alice = Principal("alice", "Alice")
    bob = Principal("bob", "Bob")
    p1 = Provenance.from_principal(alice)
    p2 = Provenance.from_principal(bob)
    merged = p1.merge(p2)
    assert p1.principals == frozenset({alice})
    assert p2.principals == frozenset({bob})
    assert merged.principals == frozenset({alice, bob})
