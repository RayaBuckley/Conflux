"""Offline Cedar differential preflight; never invokes the optional binary."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator, ValidationError

from conflux.adapters.policy import (
    CedarAuthorisationPolicy,
    CedarBinaryIdentity,
    CedarPolicyBundle,
    CedarRequest,
    CedarRunnerResult,
)
from conflux.adapters.scenarios import load_schema
from conflux.domain import (
    ActionArgument,
    ArgumentRole,
    EnvironmentSnapshot,
    Permission,
    PrimitiveAction,
    Principal,
    Provenance,
    ResourceRef,
    canonical_json,
    fingerprint,
)


@dataclass(frozen=True, slots=True)
class CedarDifferentialCase:
    id: str
    principal_ids: tuple[str, ...]
    allowed_principal_ids: frozenset[str]
    argument_allowed_principal_ids: frozenset[str]
    argument_name: str
    argument_role: ArgumentRole
    argument_value: str
    resource_id: str
    resource_present: bool
    explicit_forbid: bool
    expected_reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "principal_ids", tuple(self.principal_ids))
        object.__setattr__(self, "allowed_principal_ids", frozenset(self.allowed_principal_ids))
        object.__setattr__(
            self,
            "argument_allowed_principal_ids",
            frozenset(self.argument_allowed_principal_ids),
        )
        if not self.id or not self.principal_ids or not self.argument_name or not self.argument_value:
            raise ValueError("Cedar differential case identity must be non-empty")
        known = set(self.principal_ids)
        if not self.allowed_principal_ids.issubset(known) or not self.argument_allowed_principal_ids.issubset(known):
            raise ValueError("Cedar case grants refer to an unknown Principal")

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "principal_ids": list(self.principal_ids),
            "allowed_principal_ids": sorted(self.allowed_principal_ids),
            "argument_allowed_principal_ids": sorted(self.argument_allowed_principal_ids),
            "argument_name": self.argument_name,
            "argument_role": self.argument_role.value,
            "argument_value": self.argument_value,
            "resource_id": self.resource_id,
            "resource_present": self.resource_present,
            "explicit_forbid": self.explicit_forbid,
            "expected_reason": self.expected_reason,
        }


@dataclass(frozen=True, slots=True)
class CedarDifferentialCorpus:
    id: str
    cases: tuple[CedarDifferentialCase, ...]
    max_requests: int
    schema_version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "cases", tuple(self.cases))
        if not self.id or not self.cases or self.max_requests < 1:
            raise ValueError("Cedar corpus requires identity, cases, and a positive bound")
        ids = [case.id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("Cedar case IDs must be unique")
        if sum(len(case.principal_ids) for case in self.cases) > self.max_requests:
            raise ValueError("Cedar corpus exceeds its request bound")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "max_requests": self.max_requests,
            "cases": [case.to_dict() for case in self.cases],
        }


class _UnavailableCaptureRunner:
    def __init__(self) -> None:
        self.requests: list[CedarRequest] = []

    def evaluate(self, bundle: CedarPolicyBundle, request: CedarRequest) -> CedarRunnerResult:
        _ = bundle
        self.requests.append(request)
        return CedarRunnerResult(
            False,
            None,
            "preflight_only_binary_not_invoked",
            fingerprint({"request": request.to_dict(), "status": "unavailable"}),
        )


def load_cedar_bundle(path: Path) -> CedarPolicyBundle:
    payload = _load_json(path, "cedar_bundle")
    _validate("cedar-policy-bundle.schema.json", payload, "cedar_bundle")
    binary = cast(dict[str, str], payload["binary"])
    return CedarPolicyBundle(
        bundle_id=str(payload["bundle_id"]),
        schema_json=canonical_json(payload["schema"]),
        policies=str(payload["policies"]),
        entities_json=canonical_json(payload["entities"]),
        binary=CedarBinaryIdentity(binary["version"], binary["commit"], binary["sha256"]),
        supported_features=frozenset(cast(list[str], payload["supported_features"])),
    )


def load_cedar_corpus(path: Path) -> CedarDifferentialCorpus:
    payload = _load_json(path, "cedar_corpus")
    _validate("cedar-differential-corpus.schema.json", payload, "cedar_corpus")
    return CedarDifferentialCorpus(
        id=str(payload["id"]),
        max_requests=cast(int, payload["max_requests"]),
        cases=tuple(
            CedarDifferentialCase(
                id=str(item["id"]),
                principal_ids=tuple(cast(list[str], item["principal_ids"])),
                allowed_principal_ids=frozenset(cast(list[str], item["allowed_principal_ids"])),
                argument_allowed_principal_ids=frozenset(
                    cast(list[str], item["argument_allowed_principal_ids"])
                ),
                argument_name=str(item["argument_name"]),
                argument_role=ArgumentRole(str(item["argument_role"])),
                argument_value=str(item["argument_value"]),
                resource_id=str(item["resource_id"]),
                resource_present=bool(item["resource_present"]),
                explicit_forbid=bool(item["explicit_forbid"]),
                expected_reason=str(item["expected_reason"]),
            )
            for item in cast(list[dict[str, object]], payload["cases"])
        ),
    )


def cedar_differential_preflight(
    bundle: CedarPolicyBundle,
    corpus: CedarDifferentialCorpus,
) -> dict[str, object]:
    results = [_preflight_case(bundle, case) for case in corpus.cases]
    request_count = sum(len(cast(list[object], result["translated_requests"])) for result in results)
    if request_count > corpus.max_requests:
        raise ValueError("Cedar preflight exceeded its request bound")
    payload: dict[str, object] = {
        "schema_version": "1",
        "classification": "evaluation_ready",
        "complete": False,
        "cedar_status": "unavailable",
        "reason": "offline_preflight_does_not_invoke_cedar",
        "bundle_fingerprint": bundle.fingerprint,
        "corpus_fingerprint": fingerprint(corpus.to_dict()),
        "request_count": request_count,
        "max_requests": corpus.max_requests,
        "cases": results,
        "exclusions": [
            "Cedar CLI was not invoked",
            "fixture expectations are not Cedar parity evidence",
            "unavailable cells do not count as policy agreement",
        ],
    }
    _validate("cedar-differential-result.schema.json", payload, "cedar_result")
    return payload


def _preflight_case(bundle: CedarPolicyBundle, case: CedarDifferentialCase) -> dict[str, object]:
    principals = tuple(Principal(item, item.title()) for item in case.principal_ids)
    resource = ResourceRef("fixture", case.resource_id, "document")
    environment = EnvironmentSnapshot(
        id=f"cedar:{case.id}",
        resources=(resource,) if case.resource_present else (),
    )
    argument = ActionArgument.bind(
        name=case.argument_name,
        role=case.argument_role,
        value=case.argument_value,
        provenance=Provenance.from_principals(principals),
    )
    action = PrimitiveAction(
        id=case.id,
        operation="write",
        permission=Permission("write"),
        resource=resource,
        arguments=(argument,),
    )
    runner = _UnavailableCaptureRunner()
    adapter = CedarAuthorisationPolicy(bundle, runner, {"write": "1"}, {"agent_id": "conflux"})
    decisions = [adapter.decide(principal, action, environment) for principal in principals]
    oracle_allowed = (
        case.resource_present
        and not case.explicit_forbid
        and all(principal.id in case.allowed_principal_ids for principal in principals)
        and all(principal.id in case.argument_allowed_principal_ids for principal in principals)
    )
    return {
        "case_id": case.id,
        "oracle_allowed": oracle_allowed,
        "oracle_reason": case.expected_reason,
        "cedar_status": "unavailable",
        "cedar_decision": None,
        "translated_requests": [request.to_dict() for request in runner.requests],
        "translation_denials": [decision.reason for decision in decisions if decision.reason != "preflight_only_binary_not_invoked"],
    }


def _load_json(path: Path, label: str) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label}_load_failed:{type(error).__name__}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{label}_root_must_be_object")
    return cast(dict[str, object], payload)


def _validate(schema_name: str, payload: object, label: str) -> None:
    try:
        Draft202012Validator(load_schema(schema_name)).validate(payload)
    except ValidationError as error:
        location = ".".join(str(item) for item in error.absolute_path) or "<root>"
        raise ValueError(f"{label}_schema_error:{location}:{error.message}") from error


__all__ = [
    "CedarDifferentialCase",
    "CedarDifferentialCorpus",
    "cedar_differential_preflight",
    "load_cedar_bundle",
    "load_cedar_corpus",
]
