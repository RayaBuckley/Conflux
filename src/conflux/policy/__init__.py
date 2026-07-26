"""
Policy abstractions.
This package defines the interfaces and concrete policy models used to decide
whether a provenance-derived request should be permitted.
Policy evaluation is intentionally separated from provenance tracking and
execution semantics so the architecture stays modular and testable.
"""
from .base import Policy, PolicyDecision, PolicyRequest

__all__ = [
    "Policy",
    "PolicyDecision",
    "PolicyRequest",
]
