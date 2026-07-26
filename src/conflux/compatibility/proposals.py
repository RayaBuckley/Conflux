"""Translation of legacy proposal shapes into canonical actions.

Purpose
Layer: compatibility boundary
Dependencies: canonical actions and artifacts.
Public API: ``coerce_legacy_proposal`` only.
Security/data invariants: conversion never authorises an action; ITES still
performs all visibility, consent, and Principal Context checks.
Related documentation and tests: docs/REFERENCE.md, tests/test_ites.py.
"""

from __future__ import annotations

from typing import Any, FrozenSet

from conflux.core import Artifact, Provenance
from conflux.core.actions import Action, ActionVisibility, NestedExecutionAction, PrimitiveAction
from conflux.core.permissions import Permission
from conflux.core.principals import Principal


def _materialise_inputs(inputs: FrozenSet[Any]) -> FrozenSet[Artifact[Any]]:
    """Wrap legacy raw inputs without granting authority."""
    materialised: set[Artifact[Any]] = set()
    for item in inputs:
        if isinstance(item, Artifact):
            materialised.add(item)
        else:
            provenance = Provenance.from_principals(getattr(item, "authors", frozenset()))
            materialised.add(Artifact(value=item, provenance=provenance))
    return frozenset(materialised)


def coerce_legacy_proposal(
    proposal: Any,
    current_inputs: FrozenSet[Artifact[Any]],
    influencers: FrozenSet[Principal],
) -> Action[Any] | None:
    """Translate old ``action``/``inputs`` objects without defining semantics."""
    if isinstance(proposal, Action):
        return proposal
    if hasattr(proposal, "action"):
        action_name = str(getattr(proposal, "action"))
        return PrimitiveAction(
            permission=Permission(action_name),
            resource=getattr(proposal, "resource", None),
            provider_operation=action_name,
            inputs=current_inputs,
            decision_principals=influencers,
            visibility=getattr(proposal, "visibility", ActionVisibility.INTERNAL),
        )
    if hasattr(proposal, "inputs"):
        nested_inputs = _materialise_inputs(frozenset(getattr(proposal, "inputs")))
        return NestedExecutionAction(
            nested_inputs=nested_inputs,
            inputs=nested_inputs,
            decision_principals=influencers,
            visibility=getattr(proposal, "visibility", ActionVisibility.INTERNAL),
        )
    return None


__all__ = ["coerce_legacy_proposal"]
