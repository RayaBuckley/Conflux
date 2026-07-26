"""
SLED attack model.

Attacks represent adversarial modifications to a benchmark scenario. They are
used by SLED to evaluate how effectively a defence (e.g. ITES) prevents
undesired behaviour.

An attack is deliberately modelled independently of any particular benchmark or
LLM. This allows the same attack to be reused across multiple environments
(AWS, Google Workspace, GitHub, AgentDojo, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

from .scenario import Scenario


@dataclass(frozen=True, slots=True)
class AttackMetadata:
    """
    Descriptive information about an attack.

    Attributes
    ----------
    name:
        Stable identifier for the attack.

    description:
        Human-readable explanation.

    category:
        High-level attack class (e.g. "prompt_injection",
        "indirect_prompt_injection", "tool_output", "data_poisoning").
    """

    name: str
    description: str
    category: str


class Attack(ABC):
    """
    Base class for benchmark attacks.

    An attack transforms a benign scenario into an adversarial one. The original
    scenario must never be modified in place.
    """

    @property
    @abstractmethod
    def metadata(self) -> AttackMetadata:
        """
        Metadata describing the attack.
        """
        raise NotImplementedError

    @abstractmethod
    def apply(self, scenario: Scenario) -> Scenario:
        """
        Produce a new scenario containing the attack.
        """
        raise NotImplementedError


class AttackFactory(Protocol):
    """
    Protocol for constructing attacks.

    Useful when benchmark suites need to instantiate attacks dynamically.
    """

    def __call__(self) -> Attack:
        ...
