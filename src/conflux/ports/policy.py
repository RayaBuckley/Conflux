"""Independent fail-closed policy boundaries."""

from __future__ import annotations

from typing import Any, Protocol

from conflux.domain import (
    Action,
    Artifact,
    Decision,
    EnvironmentSnapshot,
    Principal,
    PrincipalContext,
    Session,
)


class AuthorisationPort(Protocol):
    @property
    def policy_id(self) -> str: ...

    @property
    def policy_version(self) -> str: ...

    def decide(
        self,
        principal: Principal,
        action: Action,
        environment: EnvironmentSnapshot,
    ) -> Decision: ...


class ReadPolicyPort(Protocol):
    @property
    def policy_id(self) -> str: ...

    @property
    def policy_version(self) -> str: ...

    def decide(
        self,
        principal: Principal,
        artifact: Artifact[Any],
        environment: EnvironmentSnapshot,
    ) -> Decision: ...


class VisibilityPolicyPort(Protocol):
    @property
    def policy_id(self) -> str: ...

    @property
    def policy_version(self) -> str: ...

    def decide(self, session: Session, action: Action, context: PrincipalContext) -> Decision: ...


class ConsentPolicyPort(Protocol):
    @property
    def policy_id(self) -> str: ...

    @property
    def policy_version(self) -> str: ...

    def decide(self, session: Session, action: Action, context: PrincipalContext) -> Decision: ...


__all__ = [
    "AuthorisationPort",
    "ConsentPolicyPort",
    "ReadPolicyPort",
    "VisibilityPolicyPort",
]
