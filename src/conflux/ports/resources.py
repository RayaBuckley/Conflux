"""Authorised effect execution boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from conflux.domain import Action


@dataclass(frozen=True, slots=True)
class ProviderResult:
    success: bool
    outcome: object | None = None
    error: str | None = None


class ExecutorPort(Protocol):
    def execute(
        self,
        action: Action,
        *,
        certificate_id: str,
        action_fingerprint: str,
    ) -> ProviderResult:
        """Execute one action already bound to an authorising certificate."""
        ...


__all__ = ["ExecutorPort", "ProviderResult"]
