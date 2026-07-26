"""
Owner-based policy implementation.
This is the first concrete policy in the system. It keeps the policy layer
separate from provenance tracking and execution semantics, while providing a
simple, testable authorisation rule.
Rule:
- a request is allowed only when the resource owner appears among the
  contributing principals for that request
"""
from __future__ import annotations

from .base import Policy, PolicyDecision, PolicyRequest


class OwnerPolicy(Policy):
    """
    Policy that grants access only to the resource owner.
    """
    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        owner = request.resource.owner
        if owner is not None and owner in request.principals:
            return PolicyDecision(
                allowed=True,
                reason="resource owner is present in contributing principals",
            )
        return PolicyDecision(
            allowed=False,
            reason="resource owner is not present in contributing principals",
        )
