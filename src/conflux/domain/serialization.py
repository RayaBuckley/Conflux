"""Deterministic JSON conversion and fingerprints for security values."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence, Set
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any


def canonical_value(value: Any) -> Any:
    """Return a recursively JSON-compatible value with deterministic ordering."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Enum):
        return canonical_value(value.value)
    if hasattr(value, "to_dict"):
        return canonical_value(value.to_dict())
    if is_dataclass(value) and not isinstance(value, type):
        return canonical_value(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): canonical_value(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, Set):
        converted = [canonical_value(item) for item in value]
        return sorted(converted, key=lambda item: json.dumps(item, sort_keys=True))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [canonical_value(item) for item in value]
    return {"type": f"{type(value).__module__}.{type(value).__qualname__}", "value": str(value)}


def canonical_json(value: Any) -> str:
    """Serialise a value to deterministic, compact JSON."""
    return json.dumps(canonical_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint(value: Any) -> str:
    """Return the lowercase SHA-256 hex digest of the canonical JSON."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


__all__ = ["canonical_json", "canonical_value", "fingerprint"]
