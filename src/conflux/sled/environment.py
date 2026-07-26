"""
SLED environment model.

SLED is the evaluation layer used to construct scenarios and measure whether a
defence such as ITES behaves safely.

This module defines the data structures that describe the environment seen by
the defence:
- Data items with authors and readers
- Primitive actions proposed by the model
- Nested LLM execution requests
- The overall environment container
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, FrozenSet, Iterable, Mapping

from conflux.core import Artifact, Principal, Provenance
from conflux.core.actions import (
    ActionVisibility,
    MessageUserAction,
    NestedExecutionAction,
    NoOpAction,
    PrimitiveAction,
    RequestConsentAction,
    StopAction,
)
from conflux.core.actions import (
    Proposal as ActionProposal,
)
from conflux.core.permissions import Permission, normalise_permission

# Backwards-compatible aliases for older imports.
Proposal = ActionProposal
LLMExecutionAction = NestedExecutionAction


@dataclass(frozen=True, slots=True)
class Data:
    """
    A piece of environment data.

    Attributes
    ----------
    authors:
        Principals who contributed to or authored the data.
    readers:
        Principals who are permitted to read the data.
    tag:
        Optional human-readable label used by evaluation scenarios.
    confidential:
        Whether the data should be treated as confidential by default.
    metadata:
        Opaque evaluation metadata for adapters and benchmark harnesses.
    """

    authors: FrozenSet[Principal] = field(default_factory=frozenset)
    readers: FrozenSet[Principal] = field(default_factory=frozenset)
    tag: str | None = None
    confidential: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict, compare=False, hash=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "authors", frozenset(self.authors))
        object.__setattr__(self, "readers", frozenset(self.readers))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def provenance(self) -> Provenance:
        """
        Return the provenance associated with this data item.
        """
        prov = Provenance.from_principals(self.authors)
        if self.tag is not None:
            prov = prov.with_tag(self.tag)
        if self.confidential:
            prov = prov.with_tag("confidential")
        return prov

    def to_artifact(self) -> Artifact["Data"]:
        """
        Convert this data item into an artifact for ITES execution.
        """
        return Artifact(
            value=self,
            provenance=self.provenance().with_operation("sled_input"),
            label=self.tag,
            confidential=self.confidential,
        )

    def can_read(self, principal: Principal) -> bool:
        """
        Return True if the principal may read this item.
        """
        return principal in self.readers

    def is_readable_by(self, principals: Iterable[Principal]) -> bool:
        """
        Return True if every supplied principal may read this item.
        """
        principal_set = frozenset(principals)
        return all(principal in self.readers for principal in principal_set)

    def with_metadata(self, **updates: Any) -> "Data":
        """
        Return a copy with updated metadata.
        """
        merged = dict(self.metadata)
        merged.update(updates)
        return replace(self, metadata=merged)

    @property
    def key(self) -> tuple[frozenset[str], frozenset[str], bool]:
        """
        Stable equivalence key used by representative-environment reduction.
        """
        return (
            frozenset(principal.id for principal in self.authors),
            frozenset(principal.id for principal in self.readers),
            self.confidential,
        )

    @property
    def label(self) -> str:
        """
        Human-readable label for the item.
        """
        return self.tag or "data"

    def __repr__(self) -> str:
        return (
            "Data("
            f"authors={tuple(sorted(principal.name for principal in self.authors))!r}, "
            f"readers={tuple(sorted(principal.name for principal in self.readers))!r}, "
            f"tag={self.tag!r}, "
            f"confidential={self.confidential!r}, "
            f"metadata={dict(self.metadata)!r})"
        )


@dataclass(frozen=True, slots=True)
class Environment:
    """
    The complete evaluation environment.

    SLED uses the environment to expose the data available to the defence and
    to derive convenience sets used during evaluation.
    """

    data: FrozenSet[Data] = field(default_factory=frozenset)
    name: str = "environment"
    metadata: Mapping[str, Any] = field(default_factory=dict, compare=False, hash=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", frozenset(self.data))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def total_principals(self) -> FrozenSet[Principal]:
        """
        Return all principals that appear anywhere in the environment.
        """
        principals: set[Principal] = set()
        for item in self.data:
            principals.update(item.authors)
            principals.update(item.readers)
        return frozenset(principals)

    @property
    def total_actions(self) -> FrozenSet[Permission]:
        """
        Return the atomic permissions represented by the environment.

        This is a conservative convenience view; provider-specific adapters can
        supply richer action vocabularies separately.
        """
        actions: set[Permission] = set()
        for item in self.data:
            for principal in item.authors | item.readers:
                actions.update(principal.permissions)
        return frozenset(actions)

    @property
    def tags(self) -> FrozenSet[str]:
        """
        Return all non-empty data tags in the environment.
        """
        return frozenset(item.tag for item in self.data if item.tag is not None)

    def authors_for(self, inputs: Iterable[Data]) -> FrozenSet[Principal]:
        """
        Return the union of authors for a collection of data items.
        """
        authors: set[Principal] = set()
        for item in inputs:
            authors.update(item.authors)
        return frozenset(authors)

    def readers_for(self, inputs: Iterable[Data]) -> FrozenSet[Principal]:
        """
        Return the union of readers for a collection of data items.
        """
        readers: set[Principal] = set()
        for item in inputs:
            readers.update(item.readers)
        return frozenset(readers)

    def readable_by(self, principal: Principal, inputs: Iterable[Data]) -> bool:
        """
        Check whether a principal may read all supplied inputs.
        """
        return all(principal in item.readers for item in inputs)

    def readable_by_all(self, principals: Iterable[Principal], inputs: Iterable[Data]) -> bool:
        """
        Check whether all supplied principals may read all supplied inputs.
        """
        principal_set = frozenset(principals)
        return all(self.readable_by(principal, inputs) for principal in principal_set)

    def contains_all(self, inputs: Iterable[Data]) -> bool:
        """
        Check whether every input is present in the environment.
        """
        env_items = set(self.data)
        return all(item in env_items for item in inputs)

    def as_artifacts(self) -> FrozenSet[Artifact[Data]]:
        """
        Materialise the environment as provenance-bearing artifacts.
        """
        return frozenset(item.to_artifact() for item in self.data)

    def representative_groups(self) -> dict[tuple[frozenset[str], frozenset[str], bool], FrozenSet[Data]]:
        """
        Group data items by permission-structure equivalence.

        This is used by the exhaustive evaluator to compress the search space.
        """
        groups: dict[tuple[frozenset[str], frozenset[str], bool], set[Data]] = {}
        for item in self.data:
            groups.setdefault(item.key, set()).add(item)
        return {key: frozenset(items) for key, items in groups.items()}

    def representative_environment(self) -> "Environment":
        """
        Return a compressed environment with one representative per equivalence class.
        """
        representatives: set[Data] = set()
        for items in self.representative_groups().values():
            representative = min(
                items,
                key=lambda item: (
                    item.tag is None,
                    item.tag or "",
                    len(item.authors),
                    len(item.readers),
                ),
            )
            representatives.add(representative)
        return Environment(
            data=frozenset(representatives),
            name=f"{self.name}:representative",
            metadata=dict(self.metadata),
        )

    def with_metadata(self, **updates: Any) -> "Environment":
        """
        Return a copy with updated metadata.
        """
        merged = dict(self.metadata)
        merged.update(updates)
        return Environment(data=self.data, name=self.name, metadata=merged)


def authors_for(inputs: Iterable[Data]) -> FrozenSet[Principal]:
    """
    Convenience helper for extracting the union of authors from inputs.
    """
    authors: set[Principal] = set()
    for item in inputs:
        authors.update(item.authors)
    return frozenset(authors)


def readers_for(inputs: Iterable[Data]) -> FrozenSet[Principal]:
    """
    Convenience helper for extracting the union of readers from inputs.
    """
    readers: set[Principal] = set()
    for item in inputs:
        readers.update(item.readers)
    return frozenset(readers)


def contains_all(environment: Environment, inputs: Iterable[Data]) -> bool:
    """
    Convenience helper for checking environment membership.
    """
    return environment.contains_all(inputs)


def make_primitive_action(
    operation: str,
    *,
    permission: str | Permission | None = None,
    resource: Any | None = None,
    visibility: ActionVisibility | None = None,
) -> PrimitiveAction:
    """
    Create a primitive action suitable for benchmark scenarios.

    This is a convenience helper for environment adapters that still need to
    manufacture action proposals directly.
    """
    perm = normalise_permission(permission or operation)
    kwargs: dict[str, Any] = {
        "permission": perm,
        "provider_operation": operation,
    }
    if resource is not None:
        kwargs["resource"] = resource
    if visibility is not None:
        kwargs["visibility"] = visibility
    return PrimitiveAction(**kwargs)


def make_nested_execution_action(
    inputs: Iterable[Data],
    *,
    visibility: ActionVisibility | None = None,
) -> NestedExecutionAction:
    """
    Create a nested execution action from raw environment data.
    """
    artifacts = frozenset(item.to_artifact() for item in inputs)
    kwargs: dict[str, Any] = {
        "nested_inputs": artifacts,
        "inputs": artifacts,
    }
    if visibility is not None:
        kwargs["visibility"] = visibility
    return NestedExecutionAction(**kwargs)


def make_message_action(
    message: str,
    *,
    inputs: Iterable[Data] = (),
    visibility: ActionVisibility | None = None,
) -> MessageUserAction:
    """
    Create a user-visible message action.
    """
    artifacts = frozenset(item.to_artifact() for item in inputs)
    kwargs: dict[str, Any] = {
        "message": message,
        "inputs": artifacts,
    }
    if visibility is not None:
        kwargs["visibility"] = visibility
    return MessageUserAction(**kwargs)


def make_request_consent_action(
    reason: str,
    *,
    inputs: Iterable[Data] = (),
    visibility: ActionVisibility | None = None,
) -> RequestConsentAction:
    """
    Create a consent request action.
    """
    artifacts = frozenset(item.to_artifact() for item in inputs)
    kwargs: dict[str, Any] = {
        "reason": reason,
        "inputs": artifacts,
    }
    if visibility is not None:
        kwargs["visibility"] = visibility
    return RequestConsentAction(**kwargs)


def make_stop_action(
    reason: str,
    *,
    inputs: Iterable[Data] = (),
    visibility: ActionVisibility | None = None,
) -> StopAction:
    """
    Create a stop action.
    """
    artifacts = frozenset(item.to_artifact() for item in inputs)
    kwargs: dict[str, Any] = {
        "reason": reason,
        "inputs": artifacts,
    }
    if visibility is not None:
        kwargs["visibility"] = visibility
    return StopAction(**kwargs)


def make_noop_action(
    label: str = "noop",
    *,
    inputs: Iterable[Data] = (),
    visibility: ActionVisibility | None = None,
) -> NoOpAction:
    """
    Create a no-op action.
    """
    artifacts = frozenset(item.to_artifact() for item in inputs)
    kwargs: dict[str, Any] = {
        "label": label,
        "inputs": artifacts,
    }
    if visibility is not None:
        kwargs["visibility"] = visibility
    return NoOpAction(**kwargs)


__all__ = [
    "Data",
    "Environment",
    "LLMExecutionAction",
    "Proposal",
    "authors_for",
    "contains_all",
    "make_message_action",
    "make_nested_execution_action",
    "make_noop_action",
    "make_primitive_action",
    "make_request_consent_action",
    "make_stop_action",
    "readers_for",
]
