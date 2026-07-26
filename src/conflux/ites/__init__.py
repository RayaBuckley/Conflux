"""
ITES: the defence layer.

Layer: canonical security boundary. This package owns the domain-facing ITES
contract and exports compatibility/reference implementations explicitly.

See ``docs/ARCHITECTURE.md``, ``docs/REFERENCE.md``, and ``docs/AUDIT.md``.

ITES is the reference defence that takes:
- an environment,
- an LLM model, and
- an initial set of inputs,

and produces security guarantees about what was or was not allowed to happen.

This package intentionally sits at the top level because ITES is the core
contribution of the project, not just an implementation detail of execution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, FrozenSet, Protocol, TypeAlias

from conflux.core import Artifact
from conflux.core.actions import Proposal

Declare: TypeAlias = Callable[[Any], None]
LLMCall: TypeAlias = Callable[[FrozenSet[Artifact[Any]]], FrozenSet[Proposal]]


class EnvironmentLike(Protocol):
    """
    Minimal interface for an evaluation environment.

    A concrete SLED environment will provide the objects, relations and
    metadata that ITES evaluates against.
    """

    ...


@dataclass(frozen=True, slots=True)
class Guarantee:
    """
    A statement that ITES claims to enforce or preserve.

    Attributes
    ----------
    name:
        Short identifier for the guarantee.
    holds:
        Whether the guarantee was satisfied in a given run.
    details:
        Human-readable explanation suitable for debugging and reporting.
    """

    name: str
    holds: bool
    details: str = ""


@dataclass(frozen=True, slots=True)
class ITESReport:
    """
    Result of running the defence.

    Attributes
    ----------
    guarantees:
        The set of guarantees assessed during the run.
    declared_actions:
        Actions that were permitted to be declared.
    blocked_actions:
        Actions that were rejected by the defence.
    """

    guarantees: FrozenSet[Guarantee] = field(default_factory=frozenset)
    declared_actions: FrozenSet[Any] = field(default_factory=frozenset)
    blocked_actions: FrozenSet[Any] = field(default_factory=frozenset)


class ITES(ABC):
    """
    Base class for ITES defences.

    Concrete implementations should evaluate an environment, mediate LLM calls,
    and return a report describing the guarantees achieved.
    """

    @abstractmethod
    def run(
        self,
        environment: EnvironmentLike,
        initial_inputs: FrozenSet[Artifact[Any]],
        llm_call: LLMCall,
        declare: Declare,
    ) -> ITESReport:
        """
        Execute the defence.

        Implementations should be deterministic for a fixed environment,
        initial input set and LLM model.
        """
        raise NotImplementedError


from .mediator import MediatingITES  # noqa: E402

ReferenceITES: Any = None
try:
    from .reference import ReferenceITES as _ReferenceITES
    ReferenceITES = _ReferenceITES
except ImportError:  # pragma: no cover
    pass

__all__ = [
    "Declare",
    "EnvironmentLike",
    "Guarantee",
    "ITES",
    "ITESReport",
    "LLMCall",
    "MediatingITES",
    "Proposal",
    "ReferenceITES",
]
