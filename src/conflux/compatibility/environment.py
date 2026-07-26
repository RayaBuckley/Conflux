"""Deprecated SLED environment aliases for staged adapter migration.

Purpose
Layer: compatibility boundary
Dependencies: staged ``conflux.evaluation.environment`` implementation only.
Public API: Data and Environment aliases for callers not yet migrated.
Security/data invariants: no new semantics; migration preserves existing
Principal and provenance behavior.
Related documentation and tests: docs/EVALUATION.md, docs/AUDIT.md.
"""

from conflux.domain.environment import DataItem, EnvironmentSnapshot
from conflux.evaluation.environment import Data, Environment


def data_item_from_legacy(item: Data) -> DataItem:
    """Translate one legacy SLED input without copying scenario tags to provenance."""
    item_id = str(item.metadata.get("id", item.metadata.get("path", item.tag or "data")))
    return DataItem(
        id=item_id,
        authors=item.authors,
        readers=item.readers,
        label=item.tag,
        confidential=item.confidential,
        metadata=item.metadata,
    )


def snapshot_from_legacy(environment: Environment) -> EnvironmentSnapshot:
    """Translate a legacy SLED environment into the provider-neutral contract."""
    return EnvironmentSnapshot(
        data=frozenset(data_item_from_legacy(item) for item in environment.data),
        provider_id=environment.name,
        metadata=environment.metadata,
    )

__all__ = ["Data", "Environment", "data_item_from_legacy", "snapshot_from_legacy"]
