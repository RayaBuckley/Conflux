"""Explicit legacy/reference APIs.

Purpose
Layer: compatibility boundary
Dependencies: canonical domain and ITES contracts.
Public API: legacy translations only; no new security semantics.
Security/data invariants: translations preserve Principal Context and
provenance and cannot broaden permissions.
Related documentation and tests: docs/REFERENCE.md, tests/test_compatibility.py.
"""

from conflux.ites.reference import ReferenceITES

__all__ = ["ReferenceITES"]
