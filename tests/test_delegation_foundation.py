"""Disabled-runtime scoped delegation values, state, and SLED gates."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from conflux.application import DecisionPipeline
from conflux.domain import (
    ArgumentRole,
    AtomicDelegationStore,
    DelegationAction,
    DelegationArgumentConstraint,
    DelegationArgumentFact,
    DelegationConsumption,
    DelegationRequest,
    DelegationStoreSnapshot,
    DisclosureLevel,
    Principal,
    PrincipalContext,
    Provenance,
    ResourceRef,
    ScopedDelegationGrant,
    Session,
    action_to_dict,
    delegation_grant_from_dict,
    delegation_request_from_dict,
    fingerprint,
)
from conflux.evaluation import (
    DELEGATION_PROPERTIES,
    DelegationEventType,
    DelegationMutation,
    DelegationVerificationSystem,
    ExplicitStateChecker,
    VerificationVerdict,
    consumption_record,
    issuance_record,
    revocation_record,
)
from conflux.policy import SessionAudienceVisibilityPolicy

ROOT = Path(__file__).resolve().parents[1]
CERTIFICATE_ID = sha256(b"issuance-certificate").hexdigest()
NONCE = sha256(b"one-use-nonce").hexdigest()
USE_CERTIFICATE_ID = sha256(b"use-certificate").hexdigest()


def _grant(alice: Principal, bob: Principal) -> ScopedDelegationGrant:
    constraint = DelegationArgumentConstraint(
        "destination",
        ArgumentRole.DESTINATION,
        fingerprint("archive"),
    )
    request = DelegationRequest(
        alice,
        bob,
        "write",
        "1",
        ResourceRef("test", "out", "document"),
        (constraint,),
        "2026-08-03T00:00:00Z",
        "revoke-1",
        Provenance.from_principal(alice, source="authenticated-issuance"),
    )
    return ScopedDelegationGrant(
        request,
        "2026-08-02T00:00:00Z",
        CERTIFICATE_ID,
        NONCE,
    )


def _consume(
    store: DelegationStoreSnapshot | AtomicDelegationStore,
    grant: ScopedDelegationGrant,
    bob: Principal,
    *,
    idempotency_key: str = "use-1",
    used_at: str = "2026-08-02T12:00:00Z",
    beneficiary: Principal | None = None,
    resource: ResourceRef | None = None,
    argument: DelegationArgumentFact | None = None,
) -> DelegationConsumption:
    return store.consume(
        grant_id=grant.id,
        idempotency_key=idempotency_key,
        beneficiary=beneficiary or bob,
        operation_id="write",
        operation_version="1",
        resource=resource or grant.request.resource,
        arguments=(
            argument
            or DelegationArgumentFact(
                "destination",
                ArgumentRole.DESTINATION,
                fingerprint("archive"),
            ),
        ),
        used_at=used_at,
        context=PrincipalContext(frozenset({bob})),
        decision_certificate_id=USE_CERTIFICATE_ID,
    )


def test_grant_is_immutable_round_trips_and_validates(
    alice: Principal,
    bob: Principal,
) -> None:
    grant = _grant(alice, bob)
    assert delegation_request_from_dict(
        grant.request.to_dict(), principals={"alice": alice, "bob": bob}
    ) == grant.request
    assert delegation_grant_from_dict(
        grant.to_dict(), principals={"alice": alice, "bob": bob}
    ) == grant
    schema = json.loads((ROOT / "schemas" / "delegation-grant.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(grant.to_dict())
    with pytest.raises(FrozenInstanceError):
        grant.issued_at = "later"  # type: ignore[misc]


def test_canonical_delegation_action_has_no_free_form_scope(
    alice: Principal,
    bob: Principal,
) -> None:
    action = DelegationAction("delegate", _grant(alice, bob).request)
    serialized = action_to_dict(action)
    assert "scope" not in serialized
    assert action.request is not None
    assert serialized["request_fingerprint"] == action.request.fingerprint
    with pytest.raises(TypeError, match="trusted DelegationRequest"):
        DelegationAction("legacy", "write:*")  # type: ignore[arg-type]


def test_typed_delegation_request_remains_runtime_disabled(
    pipeline: DecisionPipeline,
    environment: object,
    session: object,
    alice: Principal,
    bob: Principal,
) -> None:
    from conflux.domain import EnvironmentSnapshot, Session

    assert isinstance(environment, EnvironmentSnapshot)
    assert isinstance(session, Session)
    decision = pipeline.decide(
        session=session,
        action=DelegationAction("delegate", _grant(alice, bob).request),
        context=PrincipalContext(frozenset({alice})),
        environment=environment,
    )
    assert not decision.allowed
    assert decision.authorisation.reason == "delegation_unsupported"


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("uses", "one use"),
        ("redelegation", "redelegation"),
        ("expiry", "before expiry"),
    ],
)
def test_unsafe_grant_shapes_are_rejected(
    case: str,
    message: str,
    alice: Principal,
    bob: Principal,
) -> None:
    grant = _grant(alice, bob)
    if case == "expiry":
        with pytest.raises(ValueError, match=message):
            replace(grant, request=replace(grant.request, expires_at="2026-08-01T00:00:00Z"))
    elif case == "uses":
        with pytest.raises(ValueError, match=message):
            replace(grant.request, remaining_use_count=2)
    else:
        with pytest.raises(ValueError, match=message):
            replace(grant.request, redelegable=True)


def test_exact_use_is_bound_and_single_use(
    alice: Principal,
    bob: Principal,
) -> None:
    grant = _grant(alice, bob)
    initial = DelegationStoreSnapshot().add(grant)
    first = _consume(initial, grant, bob)
    assert first.record.allowed
    assert first.record.certificate_binding is not None
    assert len(first.record.certificate_binding) == 64
    repeat = _consume(first.snapshot, grant, bob, idempotency_key="use-2")
    assert not repeat.record.allowed
    assert repeat.record.reason == "delegation_exhausted"


def test_idempotent_retry_returns_the_same_record(
    alice: Principal,
    bob: Principal,
) -> None:
    grant = _grant(alice, bob)
    first = _consume(DelegationStoreSnapshot((grant,)), grant, bob)
    retried = _consume(first.snapshot, grant, bob)
    assert retried.snapshot is first.snapshot
    assert retried.record is first.record
    assert retried.idempotent_retry


def test_delegation_lifecycle_records_are_attributed_and_projectable(
    alice: Principal,
    bob: Principal,
    session: Session,
) -> None:
    grant = _grant(alice, bob)
    context = PrincipalContext(frozenset({alice, bob}))
    issued = issuance_record(grant, context)
    first = _consume(DelegationStoreSnapshot((grant,)), grant, bob)
    used = consumption_record(grant, first, context, sequence=1)
    retry = consumption_record(
        grant,
        _consume(first.snapshot, grant, bob),
        context,
        sequence=2,
    )
    revoked_snapshot = first.snapshot.revoke(grant.request.revocation_id)
    revoked = revocation_record(
        grant,
        revoked_snapshot,
        context,
        sequence=3,
        revoked_at="2026-08-02T13:00:00Z",
    )
    assert [item.event_type for item in (issued, used, retry, revoked)] == [
        DelegationEventType.ISSUED,
        DelegationEventType.USED,
        DelegationEventType.IDEMPOTENT_RETRY,
        DelegationEventType.REVOKED,
    ]
    validator = Draft202012Validator(
        json.loads((ROOT / "schemas" / "delegation-trace.schema.json").read_text(encoding="utf-8"))
    )
    for record in (issued, used, retry, revoked):
        validator.validate(record.to_dict())
        assert record.attribution.conservative_influence.principals == frozenset({alice, bob})
    visibility = SessionAudienceVisibilityPolicy().decide(
        session,
        alice,
        issued.event_class,
        None,
        context,
    )
    full = issued.project(visibility)
    assert full is not None
    redacted = used.project(replace(visibility, level=DisclosureLevel.REDACTED))
    assert redacted is not None
    serialized = json.dumps(redacted)
    assert grant.request.revocation_id not in serialized
    assert grant.one_use_nonce not in serialized


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("beneficiary", "wrong_beneficiary"),
        ("resource", "resource_out_of_scope"),
        ("argument", "arguments_out_of_scope"),
        ("expired", "delegation_expired"),
        ("ordering", "delegation_issued_after_influence"),
        ("revoked", "delegation_revoked"),
    ],
)
def test_scope_expiry_revocation_and_ordering_fail_closed(
    case: str,
    expected: str,
    alice: Principal,
    bob: Principal,
) -> None:
    grant = _grant(alice, bob)
    store = DelegationStoreSnapshot((grant,))
    if case == "beneficiary":
        result = _consume(store, grant, bob, beneficiary=alice)
    elif case == "resource":
        result = _consume(store, grant, bob, resource=ResourceRef("test", "other", "document"))
    elif case == "argument":
        result = _consume(
            store,
            grant,
            bob,
            argument=DelegationArgumentFact(
                "destination", ArgumentRole.DESTINATION, fingerprint("elsewhere")
            ),
        )
    elif case == "expired":
        result = _consume(store, grant, bob, used_at="2026-08-03T00:00:00Z")
    elif case == "ordering":
        result = _consume(store, grant, bob, used_at="2026-08-01T00:00:00Z")
    else:
        store = store.revoke("revoke-1")
        result = _consume(store, grant, bob)
    assert not result.record.allowed
    assert result.record.reason == expected


def test_atomic_store_allows_only_one_concurrent_use(
    alice: Principal,
    bob: Principal,
) -> None:
    grant = _grant(alice, bob)
    store = AtomicDelegationStore(DelegationStoreSnapshot((grant,)))

    def consume(index: int) -> bool:
        return _consume(store, grant, bob, idempotency_key=f"use-{index}").record.allowed

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = tuple(executor.map(consume, range(4)))
    assert sum(results) == 1
    assert len(store.snapshot.uses) == 1


@pytest.mark.parametrize(
    "mutation",
    [
        DelegationMutation.WIDENED_SCOPE,
        DelegationMutation.WRONG_BENEFICIARY,
        DelegationMutation.REUSE,
        DelegationMutation.EXPIRY_BYPASS,
        DelegationMutation.REVOCATION_BYPASS,
        DelegationMutation.REDELEGATION,
        DelegationMutation.POST_INFLUENCE_ISSUANCE,
    ],
)
def test_sled_kills_every_delegation_mutant_with_minimal_witness(
    mutation: DelegationMutation,
) -> None:
    result = ExplicitStateChecker().verify(
        DelegationVerificationSystem(mutation),
        DELEGATION_PROPERTIES,
    )
    assert result.verdict is VerificationVerdict.UNSAFE
    assert result.counterexample is not None
    assert result.counterexample.length == 1


def test_canonical_delegation_model_is_safe_but_runtime_remains_disabled() -> None:
    result = ExplicitStateChecker().verify(
        DelegationVerificationSystem(),
        DELEGATION_PROPERTIES,
    )
    assert result.verdict is VerificationVerdict.SAFE
