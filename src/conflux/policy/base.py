"""
Policy abstractions.
This module defines the minimal interface for policy evaluation. Concrete
implementations can later model enterprise authorisation systems such as AWS
IAM, Google Cloud IAM, or Microsoft Entra without changing the rest of the
project.
The goal is to keep policy evaluation separate from provenance propagation and
execution semantics.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import FrozenSet

from conflux.core import Principal, Resource


@dataclass(frozen=True, slots=True)
class PolicyRequest:
    """
    Input to a policy evaluation.
    Attributes
    ----------
    principals:
        The principals contributing authority to the request.
    resource:
        The protected resource being accessed.
    permission:
        The requested action, expressed as a simple string for now.
    """
    principals: FrozenSet[Principal]
    resource: Resource
    permission: str
@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """
    Result of evaluating a policy request.
    """
    allowed: bool
    reason: str = ""
class Policy(ABC):
    """
    Base class for policy engines.
    """
    @abstractmethod
    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        """
        Evaluate whether a request is allowed.
        """
        raise NotImplementedError
