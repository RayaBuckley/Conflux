"""Deprecated SLED environment aliases for staged adapter migration.

Purpose
Layer: compatibility boundary
Dependencies: legacy ``conflux.sled.environment`` only.
Public API: Data and Environment aliases for callers not yet migrated.
Security/data invariants: no new semantics; migration preserves existing
Principal and provenance behavior.
Related documentation and tests: docs/EVALUATION.md, docs/AUDIT.md.
"""

from conflux.sled.environment import Data, Environment

__all__ = ["Data", "Environment"]
