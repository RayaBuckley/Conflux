"""Shared canonical security fixtures."""

from __future__ import annotations

import pytest

from conflux.application import DecisionPipeline
from conflux.domain import DataItem, EnvironmentSnapshot, Principal, ResourceRef, Session
from conflux.policy import (
    ExplicitConsentPolicy,
    InMemoryAuthorisationPolicy,
    PolicyGrant,
    SessionVisibilityPolicy,
    SnapshotReadPolicy,
)


@pytest.fixture
def alice() -> Principal:
    return Principal("alice", "Alice")


@pytest.fixture
def bob() -> Principal:
    return Principal("bob", "Bob")


@pytest.fixture
def mallory() -> Principal:
    return Principal("mallory", "Mallory")


@pytest.fixture
def environment(alice: Principal, bob: Principal) -> EnvironmentSnapshot:
    return EnvironmentSnapshot(
        id="test",
        data=(
            DataItem("alice-doc", "a", frozenset({alice}), frozenset({alice})),
            DataItem("shared-doc", "s", frozenset({bob}), frozenset({alice, bob})),
        ),
        resources=(ResourceRef("test", "out", "document"),),
    )


@pytest.fixture
def session(alice: Principal, bob: Principal) -> Session:
    return Session("session", frozenset({alice, bob}))


@pytest.fixture
def adversarial_session(alice: Principal, mallory: Principal) -> Session:
    return Session("adversarial", frozenset({alice, mallory}))


@pytest.fixture
def adversarial_environment(alice: Principal, mallory: Principal) -> EnvironmentSnapshot:
    return EnvironmentSnapshot(
        id="adversarial",
        data=(
            DataItem("alice-doc", "a", frozenset({alice}), frozenset({alice})),
            DataItem("mallory-doc", "m", frozenset({mallory}), frozenset({mallory})),
        ),
        resources=(ResourceRef("test", "out", "document"),),
    )


@pytest.fixture
def adversarial_pipeline() -> DecisionPipeline:
    return DecisionPipeline(
        InMemoryAuthorisationPolicy(frozenset({PolicyGrant("alice", "write", "out")})),
        SnapshotReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(frozenset({"write", "nested", "message"})),
    )


@pytest.fixture
def pipeline() -> DecisionPipeline:
    return DecisionPipeline(
        InMemoryAuthorisationPolicy(
            frozenset(
                {
                    PolicyGrant("alice", "write", "out"),
                    PolicyGrant("bob", "write", "out"),
                }
            )
        ),
        SnapshotReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(frozenset({"write", "nested", "message"})),
    )
