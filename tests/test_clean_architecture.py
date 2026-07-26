"""Contract tests for the clean-slate domain and application boundaries."""

from __future__ import annotations

from conflux.application import MediationService
from conflux.core import Artifact, Principal, Provenance
from conflux.domain import Decision, DecisionCategory, Intent, PrincipalContext, ResourceRef
from conflux.evaluation import TraceRecord
from conflux.ites import MediatingITES


def test_domain_values_are_explicit_and_immutable() -> None:
    principal = Principal("p", "Principal")
    context = PrincipalContext(frozenset({principal}))
    resource = ResourceRef("memory", "r1", "document")
    intent = Intent("read", resource, context)

    assert intent.context.contains(principal)
    assert hash(resource)
    assert Decision(DecisionCategory.AUTHORISATION, True, "policy").allowed


def test_application_mediation_facade_delegates_canonical_ites() -> None:
    principal = Principal("p", "Principal")
    artifact = Artifact("input", Provenance.from_principal(principal))
    declared: list[object] = []

    report = MediationService(MediatingITES()).run(
        environment=object(),
        initial_inputs=frozenset({artifact}),
        llm_call=lambda _inputs: frozenset(),
        declare=declared.append,
    )

    assert report.guarantees
    assert declared == []


def test_trace_records_are_versioned_and_detached() -> None:
    record = TraceRecord("decision", "run-1", 0, {"allowed": True})
    exported = record.to_dict()

    exported["payload"]["allowed"] = False
    assert record.payload["allowed"] is True
    assert record.schema_version == "1"
