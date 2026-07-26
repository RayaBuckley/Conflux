"""Application facade for the canonical ITES mediation workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, FrozenSet

from conflux.core import Artifact
from conflux.ites import ITES, Declare, ITESReport, LLMCall


@dataclass(frozen=True, slots=True)
class MediationService:
    """Run ITES through an application-owned use-case boundary."""

    defence: ITES

    def run(
        self,
        environment: Any,
        initial_inputs: FrozenSet[Artifact[Any]],
        llm_call: LLMCall,
        declare: Declare,
    ) -> ITESReport:
        """Mediate model proposals and return the canonical immutable report."""
        return self.defence.run(environment, initial_inputs, llm_call, declare)


__all__ = ["MediationService"]
