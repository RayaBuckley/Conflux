"""
Tests for the policy layer.
These tests lock in the first concrete policy rule: access is granted only when
the resource owner is among the contributing principals.
"""
from conflux.core import Principal, Resource
from conflux.policy import PolicyRequest
from conflux.policy.owner_policy import OwnerPolicy


def test_owner_policy_allows_when_owner_is_present():
    alice = Principal("alice", "Alice")
    resource = Resource("doc-1", "test", "document", "doc-1", owner=alice)
    request = PolicyRequest(
        principals=frozenset({alice}),
        resource=resource,
        permission="read",
    )
    decision = OwnerPolicy().evaluate(request)
    assert decision.allowed is True
    assert "resource owner" in decision.reason
def test_owner_policy_denies_when_owner_is_missing():
    alice = Principal("alice", "Alice")
    bob = Principal("bob", "Bob")
    resource = Resource("doc-1", "test", "document", "doc-1", owner=alice)
    request = PolicyRequest(
        principals=frozenset({bob}),
        resource=resource,
        permission="read",
    )
    decision = OwnerPolicy().evaluate(request)
    assert decision.allowed is False
    assert "not present" in decision.reason
def test_owner_policy_denies_empty_principal_set():
    alice = Principal("alice", "Alice")
    resource = Resource("doc-1", "test", "document", "doc-1", owner=alice)
    request = PolicyRequest(
        principals=frozenset(),
        resource=resource,
        permission="write",
    )
    decision = OwnerPolicy().evaluate(request)
    assert decision.allowed is False
