"""
Reference ITES implementation.
This module exposes the public defence class used by the rest of the project.
It now delegates to the core mediation algorithm, which is where the actual
security semantics live.
"""
from __future__ import annotations

from dataclasses import dataclass

from conflux.ites.mediator import MediatingITES


@dataclass(frozen=True, slots=True)
class ReferenceITES(MediatingITES):
    """
    Default ITES defence.
    This class exists as the stable public entry point for the defence layer.
    The actual algorithm is implemented in `MediatingITES`.
    """
    pass
