"""
AWS policy adapter.

This module provides a minimal adapter from an AWS IAM-style policy document
into the project's internal policy abstraction.

The goal is not to fully reimplement IAM. The goal is to provide a realistic,
maintainable bridge that can be extended over time while keeping the rest of the
codebase independent of AWS-specific details.

Supported subset:
- Allow / Deny statements
- Action matching
- Resource matching
- Optional principal matching
- Simple string-based conditions

This is intentionally conservative and should be treated as a foundation for
future AWS integration work, not a complete IAM evaluator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable

from .adapters import PolicyAdapter, PolicyAdapterResult, PolicyContext, request_from_context
from .base import Policy, PolicyDecision, PolicyRequest


def _as_frozenset(value: str | Iterable[str] | None) -> FrozenSet[str]:
    """
    Normalise a scalar or iterable into a frozenset of strings.
    """
    if value is None:
        return frozenset()
    if isinstance(value, str):
        return frozenset({value})
    return frozenset(value)


def _matches(pattern: str, value: str) -> bool:
    """
    Very small wildcard matcher.

    Supported forms:
    - exact match
    - "*" wildcard
    - prefix/suffix wildcard using a single "*"
    """
    if pattern == "*":
        return True
    if "*" not in pattern:
        return pattern == value

    prefix, suffix = pattern.split("*", 1)
    return value.startswith(prefix) and value.endswith(suffix)


@dataclass(frozen=True, slots=True)
class AWSCondition:
    """
    Simplified AWS-style condition.

    Attributes
    ----------
    key:
        Condition key, for example "principal_id" or "resource_type".

    operator:
        Comparison operator. Supported values are "StringEquals" and
        "StringLike".

    value:
        Expected condition value.
    """

    key: str
    operator: str
    value: str

    def matches(self, context: PolicyRequest) -> bool:
        """
        Evaluate the condition against an internal policy request.
        """
        actual = _condition_value(context, self.key)

        if self.operator == "StringEquals":
            return actual == self.value
        if self.operator == "StringLike":
            return _matches(self.value, actual)

        raise ValueError(f"unsupported AWS condition operator: {self.operator}")


@dataclass(frozen=True, slots=True)
class AWSStatement:
    """
    A minimal IAM-style statement.

    Attributes
    ----------
    effect:
        Either "Allow" or "Deny".

    actions:
        Set of matching action names.

    resources:
        Set of matching resource identifiers or patterns.

    principals:
        Optional set of matching principal identifiers or patterns. When empty,
        the statement applies to any principal.

    conditions:
        Optional conditions that must all match.
    """

    effect: str
    actions: FrozenSet[str] = field(default_factory=frozenset)
    resources: FrozenSet[str] = field(default_factory=frozenset)
    principals: FrozenSet[str] = field(default_factory=frozenset)
    conditions: FrozenSet[AWSCondition] = field(default_factory=frozenset)

    def applies_to(self, request: PolicyRequest) -> bool:
        """
        Check whether this statement applies to the supplied request.
        """
        if self.actions and request.permission not in self.actions and "*" not in self.actions:
            return False

        if self.resources and not any(
            _matches(pattern, request.resource.id) for pattern in self.resources
        ):
            return False

        if self.principals:
            request_principal_ids = {principal.id for principal in request.principals}
            if not any(
                _matches(pattern, principal_id)
                for pattern in self.principals
                for principal_id in request_principal_ids
            ):
                return False

        return all(condition.matches(request) for condition in self.conditions)


@dataclass(frozen=True, slots=True)
class AWSPolicyDocument:
    """
    Simplified AWS policy document.

    This is a convenient in-memory representation of a policy that can be
    translated into an internal policy object.
    """

    statements: FrozenSet[AWSStatement] = field(default_factory=frozenset)


@dataclass(frozen=True, slots=True)
class AWSIAMPolicy(Policy):
    """
    Internal policy produced by the AWS adapter.

    Evaluation follows a deny-overrides model:
    - if any matching Deny statement applies, the request is denied;
    - otherwise, if any matching Allow statement applies, the request is allowed;
    - otherwise, the request is denied.
    """

    document: AWSPolicyDocument
    name_value: str = "aws_iam_policy"

    @property
    def name(self) -> str:
        return self.name_value

    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        matching: list[AWSStatement] = [
            statement for statement in self.document.statements if statement.applies_to(request)
        ]

        for statement in matching:
            if statement.effect.lower() == "deny":
                return PolicyDecision(
                    allowed=False,
                    reason="request denied by matching AWS deny statement",
                )

        for statement in matching:
            if statement.effect.lower() == "allow":
                return PolicyDecision(
                    allowed=True,
                    reason="request allowed by matching AWS allow statement",
                )

        return PolicyDecision(
            allowed=False,
            reason="request denied because no AWS statement matched",
        )


@dataclass(frozen=True, slots=True)
class AWSIAMAdapter(PolicyAdapter):
    """
    Adapter for AWS IAM-style policy documents.
    """

    policy_document: AWSPolicyDocument
    provider_name_value: str = "aws_iam"
    notes: str = ""

    @property
    def provider_name(self) -> str:
        return self.provider_name_value

    def adapt(self, context: PolicyContext) -> PolicyAdapterResult:
        """
        Translate the supplied context into the internal policy model.

        The current adapter is intentionally simple: it attaches a single
        AWSIAMPolicy to the context without mutating the request representation.
        """
        _ = context
        return PolicyAdapterResult(
            policy=AWSIAMPolicy(document=self.policy_document),
            source=self.provider_name,
            notes=self.notes,
        )


def _condition_value(context: PolicyRequest, key: str) -> str:
    """
    Extract a comparison value from a policy request.

    Supported keys:
    - principal_id
    - principal_name
    - resource_id
    - resource_type
    - permission
    """
    if key == "permission":
        return context.permission
    if key == "resource_id":
        return context.resource.id
    if key == "resource_type":
        return context.resource.resource_type

    if key == "principal_id":
        return next((principal.id for principal in context.principals), "")
    if key == "principal_name":
        return next((principal.name for principal in context.principals), "")

    raise ValueError(f"unsupported AWS condition key: {key}")


def build_request_from_context(context: PolicyContext) -> PolicyRequest:
    """
    Convert adapter context to the internal request type.

    This is a convenience wrapper around the shared helper in adapters.py.
    """
    return request_from_context(context)


__all__ = [
    "AWSCondition",
    "AWSIAMAdapter",
    "AWSIAMPolicy",
    "AWSStatement",
    "AWSPolicyDocument",
    "build_request_from_context",
]
