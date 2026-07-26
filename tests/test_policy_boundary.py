"""Tests for application-owned collective authorisation."""

from __future__ import annotations

from conflux.application import AuthorisationService
from conflux.core import Principal
from conflux.core.actions import PrimitiveAction
from conflux.core.permissions import Permission
from conflux.domain import PrincipalContext


def test_authorisation_service_requires_every_principal() -> None:
    allowed = Principal("allowed", "Allowed", permissions=frozenset({Permission("read")}))
    denied = Principal("denied", "Denied")
    action = PrimitiveAction(permission=Permission("read"), provider_operation="read")

    decision = AuthorisationService().decide(action, PrincipalContext(frozenset({allowed, denied})))

    assert decision.allowed is False
    assert decision.category.value == "authorisation"
