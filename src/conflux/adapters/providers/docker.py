"""Fail-closed Docker adapter boundary.

Effectful Docker execution remains experimental and unavailable until its
complete-mediation inventory and provider fixtures are implemented.
"""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import Action
from conflux.ports import ProviderResult


@dataclass(frozen=True, slots=True)
class UnsupportedDockerExecutor:
    reason: str = "docker_execution_not_verified"

    def execute(
        self,
        action: Action,
        *,
        certificate_id: str,
        action_fingerprint: str,
    ) -> ProviderResult:
        _ = action, certificate_id, action_fingerprint
        return ProviderResult(False, error=self.reason)


__all__ = ["UnsupportedDockerExecutor"]
