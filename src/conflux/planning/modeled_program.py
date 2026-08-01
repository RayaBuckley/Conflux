"""Inert graph of declared effects; this module has no execution boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True, slots=True)
class ModeledEffect:
    id: str
    action_id: str
    dependencies: tuple[str, ...]
    declared_reads: tuple[str, ...]
    declared_writes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.id or not self.action_id:
            raise ValueError("modeled_effect_identity_required")
        object.__setattr__(self, "dependencies", tuple(self.dependencies))
        object.__setattr__(self, "declared_reads", tuple(self.declared_reads))
        object.__setattr__(self, "declared_writes", tuple(self.declared_writes))
        if any(
            len(set(items)) != len(items)
            for items in (self.dependencies, self.declared_reads, self.declared_writes)
        ):
            raise ValueError(f"modeled_effect_duplicate_reference:{self.id}")

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "action_id": self.action_id,
            "dependencies": list(self.dependencies),
            "declared_reads": list(self.declared_reads),
            "declared_writes": list(self.declared_writes),
        }


@dataclass(frozen=True, slots=True)
class ModeledProgram:
    id: str
    max_steps: int
    effects: tuple[ModeledEffect, ...]
    schema_version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "effects", tuple(self.effects))
        if self.schema_version != "1" or not self.id or self.max_steps < 1 or not self.effects:
            raise ValueError("modeled_program_header_invalid")
        if len(self.effects) > self.max_steps:
            raise ValueError("modeled_program_step_bound_exceeded")
        identifiers = [effect.id for effect in self.effects]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("modeled_program_duplicate_effect")
        known: set[str] = set()
        for effect in self.effects:
            if not set(effect.dependencies).issubset(known):
                raise ValueError(f"modeled_program_forward_or_unknown_dependency:{effect.id}")
            known.add(effect.id)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "max_steps": self.max_steps,
            "effects": [effect.to_dict() for effect in self.effects],
        }

    @property
    def action_ids(self) -> tuple[str, ...]:
        return tuple(effect.action_id for effect in self.effects)


def parse_modeled_program(value: object) -> ModeledProgram:
    if not isinstance(value, dict) or set(value) != {"schema_version", "id", "max_steps", "effects"}:
        raise ValueError("modeled_program_schema_error:root")
    payload = cast(dict[str, object], value)
    if payload["schema_version"] != "1" or not isinstance(payload["id"], str):
        raise ValueError("modeled_program_schema_error:header")
    max_steps = payload["max_steps"]
    effects = payload["effects"]
    if not isinstance(max_steps, int) or isinstance(max_steps, bool) or not isinstance(effects, list):
        raise ValueError("modeled_program_schema_error:bounds_or_effects")
    parsed_effects = []
    for value in effects:
        if not isinstance(value, dict) or set(value) != {
            "id",
            "action_id",
            "dependencies",
            "declared_reads",
            "declared_writes",
        }:
            raise ValueError("modeled_program_schema_error:effect")
        item = cast(dict[str, object], value)
        if not isinstance(item["id"], str) or not isinstance(item["action_id"], str):
            raise ValueError("modeled_program_schema_error:effect_identity")
        sequences = (item["dependencies"], item["declared_reads"], item["declared_writes"])
        if any(not isinstance(sequence, list) or any(not isinstance(entry, str) for entry in sequence) for sequence in sequences):
            raise ValueError("modeled_program_schema_error:effect_references")
        parsed_effects.append(
            ModeledEffect(
                item["id"],
                item["action_id"],
                tuple(cast(list[str], item["dependencies"])),
                tuple(cast(list[str], item["declared_reads"])),
                tuple(cast(list[str], item["declared_writes"])),
            )
        )
    return ModeledProgram(
        payload["id"],
        max_steps,
        tuple(parsed_effects),
    )


__all__ = ["ModeledEffect", "ModeledProgram", "parse_modeled_program"]
