"""Canonical domain invariants."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from conflux.domain import (
    Artifact,
    DataItem,
    EnvironmentSnapshot,
    NoOpAction,
    Principal,
    PrincipalContext,
    ProposalBatch,
    ProposalMode,
    Provenance,
    ProvenancePrecision,
    canonical_json,
)


def test_principal_is_identity_only(alice: Principal) -> None:
    assert alice.id == "alice"
    assert not hasattr(alice, "permissions")


def test_domain_values_are_immutable(alice: Principal) -> None:
    with pytest.raises(FrozenInstanceError):
        alice.name = "Mallory"  # type: ignore[misc]


def test_unknown_provenance_produces_non_authority_context() -> None:
    provenance = Provenance.unknown()
    assert provenance.context.unknown
    assert not provenance.context.is_authority_bearing


def test_empty_principal_context_is_not_authority_bearing() -> None:
    assert not PrincipalContext().is_authority_bearing


def test_provenance_merge_never_drops_principals(alice: Principal, bob: Principal) -> None:
    left = Provenance.from_principal(alice)
    right = Provenance.from_principal(bob)
    merged = left.merge(right)
    assert merged.principals == frozenset({alice, bob})


def test_unknown_precision_dominates_merge(alice: Principal) -> None:
    merged = Provenance.from_principal(alice).merge(Provenance.unknown())
    assert merged.precision is ProvenancePrecision.UNKNOWN
    assert merged.context.unknown


def test_derivation_preserves_provenance(alice: Principal) -> None:
    source = Artifact("source", "a", Provenance.from_principal(alice))
    derived = source.derive(artifact_id="derived", value="A", activity="upper")
    assert alice in derived.provenance.principals
    assert derived.provenance.activities == ("upper",)


def test_combination_is_monotone(alice: Principal, bob: Principal) -> None:
    one = Artifact("one", 1, Provenance.from_principal(alice))
    two = Artifact("two", 2, Provenance.from_principal(bob))
    combined = Artifact.combine(one, two, artifact_id="sum", value=3, activity="add")
    assert combined.provenance.principals == frozenset({alice, bob})


def test_artifact_fingerprint_is_deterministic(alice: Principal) -> None:
    first = Artifact("x", {"b": 2, "a": 1}, Provenance.from_principal(alice))
    second = Artifact("x", {"a": 1, "b": 2}, Provenance.from_principal(alice))
    assert first.fingerprint == second.fingerprint


def test_authors_and_readers_are_separate(alice: Principal, bob: Principal) -> None:
    item = DataItem("doc", "secret", frozenset({alice}), frozenset({bob}))
    artifact = item.to_artifact()
    assert alice in artifact.provenance.principals
    assert bob not in artifact.provenance.principals
    assert bob in item.readers


def test_environment_rejects_duplicate_data_ids() -> None:
    first = DataItem("same", 1)
    second = DataItem("same", 2)
    with pytest.raises(ValueError, match="unique"):
        EnvironmentSnapshot("duplicate", (first, second))


def test_canonical_json_orders_mappings() -> None:
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'


def test_proposal_batch_is_immutable_and_serialisable() -> None:
    action = NoOpAction("noop")
    batch = ProposalBatch.ordered_plan(action)
    assert batch.mode is ProposalMode.ORDERED_PLAN
    assert batch.to_dict()["proposals"] == [
        {
            "id": "noop",
            "kind": "no_op",
            "visibility": "internal",
            "input_ids": [],
            "label": "no-op",
        }
    ]
    assert batch.fingerprint == ProposalBatch.ordered_plan(action).fingerprint
    with pytest.raises(ValueError, match="at least one"):
        ProposalBatch(ProposalMode.ORDERED_PLAN, ())
