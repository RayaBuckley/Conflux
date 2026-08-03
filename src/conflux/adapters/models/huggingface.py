"""One optional local causal-model path with strict proposal parsing."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol, cast

from conflux.adapters.scenarios import parse_proposal_batch
from conflux.domain import Artifact, PrimitiveAction, ProposalBatch, canonical_json

from .openai_compatible import ModelOutputError

DEFAULT_MODEL_ID = "HuggingFaceTB/SmolLM2-360M-Instruct"
DEFAULT_REVISION = "c38281e01d0c0b0c36eac2f5bcb5b51fa2e803fc"


class TextGenerator(Protocol):
    def __call__(
        self,
        prompt: str,
        *,
        max_new_tokens: int,
        do_sample: bool,
    ) -> list[dict[str, object]]: ...


@dataclass(slots=True)
class HuggingFaceCausalModel:
    allowed_resources: frozenset[tuple[str, str, str]]
    model_id: str = DEFAULT_MODEL_ID
    revision: str = DEFAULT_REVISION
    device: str = "cpu"
    dtype: str = "auto"
    max_new_tokens: int = 512
    generator: TextGenerator | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self.allowed_resources = frozenset(self.allowed_resources)
        if not self.model_id or not self.revision or self.max_new_tokens < 1:
            raise ValueError("invalid local-model configuration")

    def metadata(self) -> dict[str, object]:
        return {
            "adapter": "huggingface-causal",
            "model_id": self.model_id,
            "revision": self.revision,
            "device": self.device,
            "dtype": self.dtype,
            "max_new_tokens": self.max_new_tokens,
        }

    def propose(self, inputs: tuple[Artifact[Any], ...]) -> ProposalBatch:
        generator = self.generator or self._load_generator()
        prompt = (
            "Return only one JSON object matching Conflux proposal-batch schema version 1.\n"
            + canonical_json(
                {
                    "artifacts": [
                        {"id": item.id, "value": item.value}
                        for item in inputs
                    ]
                }
            )
        )
        try:
            outputs = generator(
                prompt,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
            )
            generated = outputs[0]["generated_text"]
            if not isinstance(generated, str):
                raise TypeError("generated_text must be a string")
            proposal = json.loads(generated.removeprefix(prompt).strip())
            if not isinstance(proposal, dict):
                raise TypeError("proposal root must be an object")
            batch = parse_proposal_batch(cast(dict[str, Any], proposal), inputs)
            for action in batch.proposals:
                if (
                    isinstance(action, PrimitiveAction)
                    and action.resource is not None
                    and action.resource.key not in self.allowed_resources
                ):
                    raise ValueError(f"unknown_resource:{action.resource.key}")
            return batch
        except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ModelOutputError(f"malformed_local_model_output:{error}") from error

    def _load_generator(self) -> TextGenerator:
        try:
            from transformers import pipeline  # type: ignore[import-not-found,unused-ignore]
        except ImportError as error:
            raise RuntimeError(
                "optional_dependency_unavailable:transformers"
            ) from error
        return cast(
            TextGenerator,
            pipeline(
                "text-generation",
                model=self.model_id,
                revision=self.revision,
                device_map=self.device,
                model_kwargs={"torch_dtype": self.dtype},
            ),
        )


__all__ = [
    "DEFAULT_MODEL_ID",
    "DEFAULT_REVISION",
    "HuggingFaceCausalModel",
    "TextGenerator",
]
