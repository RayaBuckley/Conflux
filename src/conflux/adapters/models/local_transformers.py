"""Structured adapter for model artifacts already present on the machine."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from importlib.util import find_spec
from typing import Any, Callable, Protocol, cast

from jsonschema import Draft202012Validator, ValidationError

from conflux.domain import canonical_json
from conflux.ports import LocalModelPreflight, LocalModelRequest, LocalModelResponse, LocalModelSpec

from .local_openai import LocalModelFailure


class LocalTextGenerator(Protocol):
    def __call__(self, prompt: str, *, max_new_tokens: int, temperature: float, top_p: float, seed: int) -> str: ...


@dataclass(slots=True)
class TransformersLocalModel:
    spec: LocalModelSpec
    generator: LocalTextGenerator | None = field(default=None, repr=False)
    clock: Callable[[], float] = field(default=time.monotonic, repr=False)

    def __post_init__(self) -> None:
        if self.spec.backend != "transformers":
            raise ValueError("transformers_spec_required")

    def preflight(self) -> LocalModelPreflight:
        available = self.generator is not None or find_spec("transformers") is not None
        return LocalModelPreflight(
            backend=self.spec.backend,
            model_id=self.spec.model_id,
            available=available,
            network_scope="none",
            reason=None if available else "optional_dependency_unavailable:transformers",
        )

    def generate(self, request: LocalModelRequest) -> LocalModelResponse:
        generator = self.generator or self._load_generator()
        prompt = f"{request.system_prompt}\n{request.user_prompt}\nReturn JSON only."
        started = self.clock()
        try:
            content = generator(
                prompt,
                max_new_tokens=self.spec.max_output_tokens,
                temperature=self.spec.temperature,
                top_p=self.spec.top_p,
                seed=self.spec.seed,
            )
            decoded = json.loads(content)
            if not isinstance(decoded, dict):
                raise TypeError("structured_root_not_object")
            Draft202012Validator(dict(request.schema)).validate(decoded)
        except LocalModelFailure:
            raise
        except (TypeError, ValueError, json.JSONDecodeError, ValidationError) as error:
            raise LocalModelFailure("malformed_output", str(error)) from error
        latency = max(0, round((self.clock() - started) * 1000))
        raw_hash = hashlib.sha256(canonical_json(decoded).encode("utf-8")).hexdigest()
        return LocalModelResponse(
            request.request_id,
            self.spec.model_id,
            cast(dict[str, object], decoded),
            None,
            None,
            latency,
            raw_hash,
        )

    def _load_generator(self) -> LocalTextGenerator:
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed  # type: ignore[import-not-found,unused-ignore]
        except ImportError as error:
            raise LocalModelFailure("dependency", "optional_dependency_unavailable:transformers") from error
        tokenizer = AutoTokenizer.from_pretrained(
            self.spec.model_id,
            revision=self.spec.revision,
            local_files_only=True,
            trust_remote_code=False,
        )
        model = AutoModelForCausalLM.from_pretrained(
            self.spec.model_id,
            revision=self.spec.revision,
            local_files_only=True,
            trust_remote_code=False,
            torch_dtype=self.spec.dtype,
            device_map=self.spec.device,
        )

        def generate(prompt: str, *, max_new_tokens: int, temperature: float, top_p: float, seed: int) -> str:
            set_seed(seed)
            encoded = tokenizer(prompt, return_tensors="pt")
            output = cast(Any, model).generate(
                **encoded,
                max_new_tokens=max_new_tokens,
                do_sample=temperature > 0,
                temperature=max(temperature, 1e-8),
                top_p=top_p,
            )
            return cast(str, tokenizer.decode(output[0][encoded["input_ids"].shape[-1] :], skip_special_tokens=True))

        return generate


__all__ = ["LocalTextGenerator", "TransformersLocalModel"]
