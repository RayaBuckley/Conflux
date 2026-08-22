"""Provider adapter contracts and safe in-memory executor."""

from __future__ import annotations

from dataclasses import dataclass, field

from conflux.domain import Action, EnvironmentSnapshot
from conflux.domain import action_fingerprint as fingerprint_action
from conflux.ports import ProviderResult


@dataclass(frozen=True, slots=True)
class StaticEnvironmentProvider:
    """Provider that always returns the same fixed environment snapshot."""

    environment: EnvironmentSnapshot

    def snapshot(self) -> EnvironmentSnapshot:
        """Return the static environment snapshot."""
        return self.environment


@dataclass(slots=True)
class RecordingExecutor:
    """Test/sandbox executor that rejects certificate substitution."""

    executed: list[str] = field(default_factory=list)

    def execute(
        self,
        action: Action,
        *,
        certificate_id: str,
        action_fingerprint: str,
    ) -> ProviderResult:
        """Execute the action, rejecting any certificate-action mismatch."""
        if not certificate_id or action_fingerprint != fingerprint_action(action):
            return ProviderResult(False, error="certificate_action_mismatch")
        self.executed.append(action.id)
        return ProviderResult(True, outcome=action.id)


__all__ = ["RecordingExecutor", "StaticEnvironmentProvider"]
