"""Declared fail-closed subset of AWS-style policy statements."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

SUPPORTED_KEYS = frozenset({"Effect", "Action", "Resource"})


@dataclass(frozen=True, slots=True)
class AWSSubsetDecision:
    """Outcome of evaluating an AWS-style policy statement."""

    allowed: bool
    reason: str


def evaluate_statement(
    statement: Mapping[str, Any],
    *,
    action: str,
    resource: str,
) -> AWSSubsetDecision:
    """Evaluate an AWS-style statement against an action and resource."""
    unsupported = set(statement) - SUPPORTED_KEYS
    if unsupported:
        return AWSSubsetDecision(False, f"unsupported_fields:{','.join(sorted(unsupported))}")
    if not all(key in statement for key in SUPPORTED_KEYS):
        return AWSSubsetDecision(False, "incomplete_statement")
    if statement["Effect"] not in {"Allow", "Deny"}:
        return AWSSubsetDecision(False, "unsupported_effect")
    actions = statement["Action"]
    resources = statement["Resource"]
    action_values = {actions} if isinstance(actions, str) else set(actions)
    resource_values = {resources} if isinstance(resources, str) else set(resources)
    if statement["Effect"] == "Deny" and action in action_values and resource in resource_values:
        return AWSSubsetDecision(False, "explicit_deny")
    allowed = statement["Effect"] == "Allow" and action in action_values and resource in resource_values
    return AWSSubsetDecision(allowed, "explicit_allow" if allowed else "no_matching_allow")


__all__ = ["SUPPORTED_KEYS", "AWSSubsetDecision", "evaluate_statement"]
