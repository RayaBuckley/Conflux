"""
Policy adapters.
This module provides the bridge between external policy systems and the
project's internal policy model.
The purpose of an adapter is to translate a provider-specific representation
such as AWS IAM, Google Cloud IAM, or Microsoft Entra into the common
`PolicyRequest` / `PolicyDecision` abstraction used by the rest of the codebase.
Keeping this layer separate prevents provider-specific logic from leaking into
the core authorisation and ITES layers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, FrozenSet, Protocol

from conflux.core import Principal, Resource

from .base import Policy, PolicyDecision, PolicyRequest


@dataclass(frozen=True, slots=True)
class PolicyContext:
    """
    Context supplied to a policy adapter.
    Attributes
    ----------
    principals:
        Principals currently relevant to the request.
    resource:
        The protected resource being accessed.
    permission:
        The requested action.
    attributes:
        Optional key-value context used by provider-specific policies.
    """
    principals: FrozenSet[Principal]
    resource: Resource
    permission: str
    attributes: dict[str, Any] = field(default_factory=dict)
@dataclass(frozen=True, slots=True)
class PolicyAdapterResult:
    """
    Result of adapting an external policy representation.
    Attributes
    ----------
    policy:
        The internal policy object produced by the adapter.
    source:
        A short label identifying the originating policy system.
    notes:
        Human-readable notes about the translation.
    """
    policy: Policy
    source: str
    notes: str = ""
class PolicyAdapter(ABC):
    """
    Base class for provider-specific policy adapters.
    """
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Name of the external policy system handled by this adapter.
        """
        raise NotImplementedError
    @abstractmethod
    def adapt(self, context: PolicyContext) -> PolicyAdapterResult:
        """
        Translate provider-specific policy information into an internal policy.
        """
        raise NotImplementedError
class PolicyTranslator(Protocol):
    """
    Protocol for objects that can translate policy contexts.
    This is useful when a caller wants a simple callable-style adapter rather
    than a full class hierarchy.
    """
    def __call__(self, context: PolicyContext) -> PolicyAdapterResult:
        ...
@dataclass(frozen=True, slots=True)
class StaticPolicyAdapter(PolicyAdapter):
    """
    Adapter that always returns the same policy.
    This is useful for tests and for bootstrap integration work where a provider
    parser has not yet been implemented.
    """
    provider_name_value: str
    policy: Policy
    notes: str = ""
    @property
    def provider_name(self) -> str:
        return self.provider_name_value
    def adapt(self, context: PolicyContext) -> PolicyAdapterResult:
        _ = context
        return PolicyAdapterResult(
            policy=self.policy,
            source=self.provider_name,
            notes=self.notes,
        )
@dataclass(frozen=True, slots=True)
class AllowAllPolicy(Policy):
    """
    Minimal policy used for bootstrap and tests.
    This policy grants every request. It is intentionally simple and should only
    be used where the caller wants to verify the adapter pipeline itself rather
    than provider semantics.
    """
    name_value: str = "allow_all"
    @property
    def name(self) -> str:
        return self.name_value
    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        _ = request
        return PolicyDecision(
            allowed=True,
            reason="request permitted by allow-all policy",
        )
@dataclass(frozen=True, slots=True)
class DenyAllPolicy(Policy):
    """
    Minimal policy used for bootstrap and tests.
    This policy denies every request. It is useful when verifying that the
    plumbing reaches the policy layer but should not be treated as a real
    security model.
    """
    name_value: str = "deny_all"
    @property
    def name(self) -> str:
        return self.name_value
    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        _ = request
        return PolicyDecision(
            allowed=False,
            reason="request denied by deny-all policy",
        )
def request_from_context(context: PolicyContext) -> PolicyRequest:
    """
    Convert an adapter context into the internal request format.
    """
    return PolicyRequest(
        principals=context.principals,
        resource=context.resource,
        permission=context.permission,
    )
