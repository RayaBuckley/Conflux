"""Frozen AgentDojo annotation profiles for the reviewed pilot subset."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from conflux.domain import ArgumentRole, OperationArgumentSchema, canonical_json, fingerprint


class AnnotationProfile(StrEnum):
    CONSERVATIVE = "conservative"
    ORACLE = "oracle"


@dataclass(frozen=True, slots=True)
class AgentDojoAnnotations:
    profile: AnnotationProfile
    operations: Mapping[str, OperationArgumentSchema]
    reviewed_values: Mapping[str, tuple[str, ...]]
    version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "operations", MappingProxyType(dict(self.operations)))
        object.__setattr__(
            self,
            "reviewed_values",
            MappingProxyType({key: tuple(values) for key, values in self.reviewed_values.items()}),
        )

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "profile": self.profile.value,
            "operations": {
                name: {
                    "version": schema.version,
                    "roles": {key: role.value for key, role in sorted(schema.roles.items())},
                }
                for name, schema in sorted(self.operations.items())
            },
            "reviewed_values": {
                key: list(values) for key, values in sorted(self.reviewed_values.items())
            },
        }


def pilot_annotations(profile: AnnotationProfile) -> AgentDojoAnnotations:
    """Return annotations frozen before observing any Conflux pilot result."""

    operations = {
        "search_emails": OperationArgumentSchema(
            "search_emails",
            "agentdojo-0.1.35",
            {"query": ArgumentRole.CONTENT},
        ),
        "delete_file": OperationArgumentSchema(
            "delete_file",
            "agentdojo-0.1.35",
            {"file_id": ArgumentRole.RESOURCE},
        ),
    }
    # The selected upstream fixture identifies file 13. This exception is
    # reviewed input, not inferred from a model response or experiment result.
    reviewed = {"delete_file.file_id": ("13",)}
    return AgentDojoAnnotations(profile, operations, reviewed)


def annotations_json(profile: AnnotationProfile) -> str:
    return canonical_json(pilot_annotations(profile).to_dict())


__all__ = [
    "AgentDojoAnnotations",
    "AnnotationProfile",
    "annotations_json",
    "pilot_annotations",
]
