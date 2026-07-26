"""
Authorisation.
This package is responsible for determining whether protected actions are
permitted based on provenance and policy.
The core package models *what* information exists and where it came from.
The auth package determines *whether* an action may proceed.
Initially, authorisation is intentionally simple. More sophisticated policy
evaluation (e.g. AWS IAM, Google Cloud IAM, Microsoft Entra PIM) will be added
later without changing the external API.
"""
from .authorisation import can_access, effective_authority

__all__ = [
    "can_access",
    "effective_authority",
]
