"""Strict versioned YAML scenario loading for deterministic runs."""

from __future__ import annotations

import json
import sysconfig
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import Any, cast

import yaml
from jsonschema import Draft202012Validator, ValidationError
from yaml import YAMLError

from conflux.application import DecisionPipeline
from conflux.domain import (
    Action,
    ActionVisibility,
    Artifact,
    DataItem,
    DelegationAction,
    EnvironmentSnapshot,
    MessageAction,
    NestedExecutionAction,
    NoOpAction,
    Permission,
    PrimitiveAction,
    Principal,
    ProposalBatch,
    ProposalMode,
    ResourceRef,
    Session,
    StopAction,
)
from conflux.policy import (
    ExplicitConsentPolicy,
    InMemoryAuthorisationPolicy,
    PolicyGrant,
    SessionVisibilityPolicy,
    SnapshotReadPolicy,
)

ROOT = Path(__file__).resolve().parents[3]
REPOSITORY_SCHEMAS = ROOT / "schemas"
INSTALLED_SCHEMAS = Path(sysconfig.get_path("data")) / "share" / "conflux" / "schemas"


@dataclass(frozen=True, slots=True)
class LoadedScenario:
    """A fully resolved scenario ready for execution: environment, session, pipeline, and model proposals."""

    id: str
    environment: EnvironmentSnapshot
    session: Session
    pipeline: DecisionPipeline
    model: ProposalBatch
    schema_version: str = "1"


def load_schema(name: str) -> dict[str, Any]:
    """Load a JSON schema by name from the repository or installed package."""
    installed = _installed_schema_path(name)
    schema_path = next(
        (
            path
            for path in (
                REPOSITORY_SCHEMAS / name,
                INSTALLED_SCHEMAS / name,
                installed,
            )
            if path is not None and path.is_file()
        ),
        None,
    )
    if schema_path is None:
        raise ValueError(f"schema_unavailable:{name}")
    return cast(
        dict[str, Any],
        json.loads(schema_path.read_text(encoding="utf-8")),
    )


def _installed_schema_path(name: str) -> Path | None:
    try:
        package = distribution("conflux")
    except PackageNotFoundError:
        return None
    for entry in package.files or ():
        if entry.as_posix().endswith(f"share/conflux/schemas/{name}"):
            return Path(str(package.locate_file(entry)))
    return None


def _resolved_scenario_schema() -> dict[str, Any]:
    scenario = load_schema("scenario.schema.json")
    proposal = load_schema("proposal-batch.schema.json")
    properties = cast(dict[str, Any], scenario["properties"])
    resources = cast(dict[str, Any], properties["resources"])
    resources["items"] = proposal["$defs"]["resource"]
    properties["model"] = proposal
    return scenario


def load_scenario(path: Path) -> LoadedScenario:
    """Parse and validate a YAML scenario file into a fully resolved ``LoadedScenario``."""
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, YAMLError) as error:
        raise ValueError(f"scenario_load_failed:{type(error).__name__}") from error
    if not isinstance(payload, dict):
        raise ValueError("scenario_root_must_be_mapping")
    try:
        Draft202012Validator(_resolved_scenario_schema()).validate(payload)
    except ValidationError as error:
        location = ".".join(str(item) for item in error.absolute_path) or "<root>"
        raise ValueError(f"scenario_schema_error:{location}:{error.message}") from error
    return _parse_scenario(cast(dict[str, Any], payload))


def _parse_scenario(payload: dict[str, Any]) -> LoadedScenario:
    principals = tuple(Principal(str(item["id"]), str(item["name"]), str(item["kind"])) for item in payload["principals"])
    by_id = {principal.id: principal for principal in principals}
    if len(by_id) != len(principals):
        raise ValueError("duplicate_principal_id")

    def resolve_principals(identifiers: list[str]) -> frozenset[Principal]:
        """Resolve a list of principal identifiers to ``Principal`` objects."""
        try:
            return frozenset(by_id[identifier] for identifier in identifiers)
        except KeyError as error:
            raise ValueError(f"unknown_principal:{error.args[0]}") from error

    data = tuple(
        DataItem(
            id=str(item["id"]),
            value=item["value"],
            authors=resolve_principals(item["authors"]),
            readers=resolve_principals(item["readers"]),
            label=cast(str | None, item.get("label")),
            confidential=bool(item.get("confidential", False)),
        )
        for item in payload["data"]
    )
    resources = tuple(_resource(item) for item in payload["resources"])
    environment = EnvironmentSnapshot(
        id=str(payload["id"]),
        data=data,
        resources=resources,
    )
    grants = frozenset(
        PolicyGrant(
            principal_id=str(item["principal_id"]),
            permission=str(item["permission"]),
            resource_id=cast(str | None, item["resource_id"]),
        )
        for item in payload["grants"]
    )
    unknown_grants = sorted(grant.principal_id for grant in grants if grant.principal_id not in by_id)
    if unknown_grants:
        raise ValueError(f"unknown_grant_principal:{unknown_grants[0]}")
    pipeline = DecisionPipeline(
        InMemoryAuthorisationPolicy(grants),
        SnapshotReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(frozenset(str(item) for item in payload["consent"])),
    )
    batch = _proposal_batch(payload["model"], environment)
    return LoadedScenario(
        id=str(payload["id"]),
        environment=environment,
        session=Session(f"{payload['id']}:session", frozenset(principals)),
        pipeline=pipeline,
        model=batch,
    )


def _resource(payload: dict[str, Any]) -> ResourceRef:
    return ResourceRef(
        provider=str(payload["provider"]),
        resource_id=str(payload["resource_id"]),
        resource_type=str(payload["resource_type"]),
        attributes=cast(dict[str, Any], payload["attributes"]),
    )


def _proposal_batch(payload: dict[str, Any], environment: EnvironmentSnapshot) -> ProposalBatch:
    return parse_proposal_batch(payload, environment.artifacts())


def parse_proposal_batch(
    payload: dict[str, Any],
    inputs: tuple[Artifact[Any], ...],
) -> ProposalBatch:
    """Validate a proposal-batch payload and resolve it against available inputs."""
    try:
        Draft202012Validator(load_schema("proposal-batch.schema.json")).validate(payload)
    except ValidationError as error:
        location = ".".join(str(item) for item in error.absolute_path) or "<root>"
        raise ValueError(f"proposal_schema_error:{location}:{error.message}") from error
    by_id = {item.id: item for item in inputs}
    if len(by_id) != len(inputs):
        raise ValueError("duplicate_input_id")
    actions = tuple(_action(item, by_id) for item in payload["proposals"])
    return ProposalBatch(ProposalMode(str(payload["mode"])), actions)


def _action(payload: dict[str, Any], by_id: dict[str, Artifact[Any]]) -> Action:
    try:
        inputs = tuple(by_id[str(identifier)] for identifier in payload["input_ids"])
    except KeyError as error:
        raise ValueError(f"unknown_input:{error.args[0]}") from error
    identifier = str(payload["id"])
    visibility = ActionVisibility(str(payload["visibility"]))
    kind = str(payload["kind"])
    if kind == "primitive":
        resource_payload = payload["resource"]
        return PrimitiveAction(
            identifier,
            str(payload["operation"]),
            Permission(str(payload["permission"])),
            _resource(resource_payload) if resource_payload is not None else None,
            inputs,
            visibility,
        )
    if kind == "nested":
        return NestedExecutionAction(identifier, inputs, visibility)
    if kind == "message":
        return MessageAction(identifier, str(payload["message"]), inputs, visibility)
    if kind == "delegation":
        # Historical v1 scenarios can contain free-form delegation text. It is
        # deliberately discarded rather than promoted into a trusted grant.
        return DelegationAction(identifier, None, inputs, visibility)
    if kind == "stop":
        return StopAction(identifier, str(payload["reason"]), inputs, visibility)
    if kind == "no_op":
        return NoOpAction(identifier, str(payload["label"]), inputs, visibility)
    raise ValueError(f"unsupported_action_kind:{kind}")


__all__ = [
    "LoadedScenario",
    "load_scenario",
    "load_schema",
    "parse_proposal_batch",
]
