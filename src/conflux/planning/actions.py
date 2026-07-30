"""Authenticated operation definitions and provenance-preserving grounding."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping, TypeAlias

from conflux.domain import (
    ActionVisibility,
    Artifact,
    Permission,
    PrimitiveAction,
    Provenance,
    ResourceRef,
    fingerprint,
    normalise_permission,
    provenance_union,
)


class ArgumentType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


@dataclass(frozen=True, slots=True)
class ArgumentSpec:
    name: str
    value_type: ArgumentType
    required: bool = True

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("argument name must be non-empty")

    def validate(self, value: object) -> None:
        valid = {
            ArgumentType.STRING: isinstance(value, str),
            ArgumentType.INTEGER: isinstance(value, int) and not isinstance(value, bool),
            ArgumentType.NUMBER: isinstance(value, (int, float)) and not isinstance(value, bool),
            ArgumentType.BOOLEAN: isinstance(value, bool),
            ArgumentType.OBJECT: isinstance(value, Mapping),
            ArgumentType.ARRAY: isinstance(value, (list, tuple)),
        }[self.value_type]
        if not valid:
            raise ValueError(f"argument {self.name!r} must be {self.value_type.value}")

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "type": self.value_type.value,
            "required": self.required,
        }


@dataclass(frozen=True, slots=True)
class OperationSchema:
    """Trusted operation metadata; planner text cannot create one."""

    id: str
    version: str
    provider: str
    resource_type: str
    operation: str
    permission: Permission
    arguments: tuple[ArgumentSpec, ...] = ()
    resource_argument: str | None = None

    def __post_init__(self) -> None:
        if not all((self.id, self.version, self.provider, self.resource_type, self.operation)):
            raise ValueError(
                "operation identity, version, provider, resource type, and operation are required"
            )
        object.__setattr__(self, "permission", normalise_permission(self.permission))
        object.__setattr__(self, "arguments", tuple(self.arguments))
        names = [argument.name for argument in self.arguments]
        if len(names) != len(set(names)):
            raise ValueError("operation argument names must be unique")
        if self.resource_argument is not None and self.resource_argument not in names:
            raise ValueError("resource_argument must name a declared argument")

    @property
    def key(self) -> tuple[str, str]:
        return (self.id, self.version)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "version": self.version,
            "provider": self.provider,
            "resource_type": self.resource_type,
            "operation": self.operation,
            "permission": self.permission.name,
            "arguments": [item.to_dict() for item in self.arguments],
            "resource_argument": self.resource_argument,
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


@dataclass(frozen=True, slots=True)
class OperationCatalogue:
    operations: tuple[OperationSchema, ...]
    identity: str = "catalogue"
    version: str = "1"
    _by_key: Mapping[tuple[str, str], OperationSchema] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        operations = tuple(self.operations)
        by_key = {operation.key: operation for operation in operations}
        if len(by_key) != len(operations):
            raise ValueError("operation catalogue contains duplicate identities")
        if not self.identity or not self.version:
            raise ValueError("catalogue identity and version must be non-empty")
        object.__setattr__(self, "operations", operations)
        object.__setattr__(self, "_by_key", MappingProxyType(by_key))

    def resolve(self, operation_id: str, version: str) -> OperationSchema:
        try:
            return self._by_key[(operation_id, version)]
        except KeyError as error:
            raise ValueError(f"unknown operation schema: {operation_id}@{version}") from error

    def to_dict(self) -> dict[str, object]:
        return {
            "identity": self.identity,
            "version": self.version,
            "operations": [
                item.to_dict() for item in sorted(self.operations, key=lambda item: item.key)
            ],
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


@dataclass(frozen=True, slots=True)
class LiteralBinding:
    value: object
    provenance: Provenance
    kind: str = field(default="literal", init=False)

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "value": self.value,
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ArtifactBinding:
    artifact_id: str
    kind: str = field(default="artifact", init=False)

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("artifact binding requires an artifact id")

    def to_dict(self) -> dict[str, object]:
        return {"kind": self.kind, "artifact_id": self.artifact_id}


@dataclass(frozen=True, slots=True)
class NodeOutputBinding:
    node_id: str
    output_name: str
    kind: str = field(default="node_output", init=False)

    def __post_init__(self) -> None:
        if not self.node_id or not self.output_name:
            raise ValueError("node-output binding requires node and output names")

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "node_id": self.node_id,
            "output_name": self.output_name,
        }


Binding: TypeAlias = LiteralBinding | ArtifactBinding | NodeOutputBinding


@dataclass(frozen=True, slots=True)
class TemplateArgument:
    name: str
    binding: Binding

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("template argument name must be non-empty")

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "binding": self.binding.to_dict()}


@dataclass(frozen=True, slots=True)
class ActionTemplate:
    id: str
    operation_id: str
    operation_version: str
    arguments: tuple[TemplateArgument, ...]
    visibility: ActionVisibility = ActionVisibility.INTERNAL

    def __post_init__(self) -> None:
        if not self.id or not self.operation_id or not self.operation_version:
            raise ValueError("template and operation identities must be non-empty")
        object.__setattr__(self, "arguments", tuple(self.arguments))
        names = [argument.name for argument in self.arguments]
        if len(names) != len(set(names)):
            raise ValueError("template argument names must be unique")

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "operation_id": self.operation_id,
            "operation_version": self.operation_version,
            "arguments": [item.to_dict() for item in self.arguments],
            "visibility": self.visibility.value,
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


@dataclass(frozen=True, slots=True)
class GroundArgument:
    name: str
    value: object
    provenance: Provenance

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "value": self.value,
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class GroundAction:
    id: str
    schema: OperationSchema
    arguments: tuple[GroundArgument, ...]
    provenance: Provenance
    visibility: ActionVisibility = ActionVisibility.INTERNAL

    def __post_init__(self) -> None:
        object.__setattr__(self, "arguments", tuple(self.arguments))

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "operation": self.schema.to_dict(),
            "arguments": [item.to_dict() for item in self.arguments],
            "provenance": self.provenance.to_dict(),
            "visibility": self.visibility.value,
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())

    def to_action(self) -> PrimitiveAction:
        resource: ResourceRef | None = None
        inputs: list[Artifact[Any]] = []
        for argument in self.arguments:
            if argument.name == self.schema.resource_argument:
                resource = ResourceRef(
                    self.schema.provider,
                    str(argument.value),
                    self.schema.resource_type,
                )
                continue
            inputs.append(
                Artifact(
                    id=f"ground:{self.id}:{argument.name}:{fingerprint(argument.value)[:16]}",
                    value=argument.value,
                    provenance=argument.provenance,
                    label=argument.name,
                )
            )
        return PrimitiveAction(
            id=self.id,
            operation=self.schema.operation,
            permission=self.schema.permission,
            resource=resource,
            inputs=tuple(inputs),
            visibility=self.visibility,
        )


@dataclass(frozen=True, slots=True)
class BindingEnvironment:
    artifacts: Mapping[str, Artifact[Any]]
    node_outputs: Mapping[tuple[str, str], Artifact[Any]]


def resolve_binding(binding: Binding, environment: BindingEnvironment) -> Artifact[Any]:
    if isinstance(binding, LiteralBinding):
        return Artifact(
            id=f"literal:{fingerprint(binding.to_dict())[:24]}",
            value=binding.value,
            provenance=binding.provenance,
        )
    if isinstance(binding, ArtifactBinding):
        try:
            return environment.artifacts[binding.artifact_id]
        except KeyError as error:
            raise ValueError(f"unknown artifact binding: {binding.artifact_id}") from error
    try:
        return environment.node_outputs[(binding.node_id, binding.output_name)]
    except KeyError as error:
        raise ValueError(
            f"unknown node-output binding: {binding.node_id}.{binding.output_name}"
        ) from error


def ground_action(
    template: ActionTemplate,
    *,
    catalogue: OperationCatalogue,
    environment: BindingEnvironment,
    invocation_provenance: Provenance,
    control_provenance: Provenance,
    branch_provenance: Provenance | None = None,
) -> GroundAction:
    schema = catalogue.resolve(template.operation_id, template.operation_version)
    specifications = {item.name: item for item in schema.arguments}
    supplied = {item.name for item in template.arguments}
    unknown = supplied - specifications.keys()
    if unknown:
        raise ValueError(f"unknown operation arguments: {sorted(unknown)}")
    missing = {
        name for name, item in specifications.items() if item.required and name not in supplied
    }
    if missing:
        raise ValueError(f"missing operation arguments: {sorted(missing)}")
    resolved: list[GroundArgument] = []
    for argument in template.arguments:
        artifact = resolve_binding(argument.binding, environment)
        specifications[argument.name].validate(artifact.value)
        resolved.append(GroundArgument(argument.name, artifact.value, artifact.provenance))
    sources = [invocation_provenance, control_provenance]
    if branch_provenance is not None:
        sources.append(branch_provenance)
    sources.extend(item.provenance for item in resolved)
    provenance = provenance_union(*sources).with_activity(f"ground:{template.id}")
    return GroundAction(template.id, schema, tuple(resolved), provenance, template.visibility)


__all__ = [
    "ActionTemplate",
    "ArgumentSpec",
    "ArgumentType",
    "ArtifactBinding",
    "Binding",
    "BindingEnvironment",
    "GroundAction",
    "GroundArgument",
    "LiteralBinding",
    "NodeOutputBinding",
    "OperationCatalogue",
    "OperationSchema",
    "TemplateArgument",
    "ground_action",
    "resolve_binding",
]
