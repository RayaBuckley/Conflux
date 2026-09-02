"""Structured adapter for model artifacts already present on the machine."""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Protocol, cast

from jsonschema import Draft202012Validator, ValidationError

from conflux.domain import canonical_json
from conflux.ports import LocalModelPreflight, LocalModelRequest, LocalModelResponse, LocalModelSpec

from .artifacts import LocalArtifactManifest, verify_transformers_snapshot
from .local_openai import LocalModelFailure

_FENCE_RE = re.compile(
    r"^\s*```(?:json)?\s*\n(.*?)\n```\s*$",
    re.DOTALL,
)


def _strip_markdown_fences(text: str) -> str:
    stripped = _FENCE_RE.sub(r"\1", text)
    return stripped.strip() if stripped != text.strip() else text.strip()


def _extract_first_json(text: str) -> dict[str, object]:
    cleaned = _strip_markdown_fences(text)
    start = cleaned.find("{")
    if start == -1:
        raise ValueError("no_json_object_found")
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(cleaned, start)
    if not isinstance(obj, dict):
        raise TypeError("structured_root_not_object")
    return obj


class LocalTextGenerator(Protocol):
    """Callable protocol for local text generation."""

    def __call__(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_new_tokens: int,
        temperature: float,
        top_p: float,
        seed: int,
    ) -> str | LocalTextGeneration: ...


@dataclass(frozen=True, slots=True)
class LocalTextGeneration:
    """Result of a local text generation call."""

    content: str
    prompt_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(slots=True)
class TransformersLocalModel:
    """Adapter for a locally resolved transformers model."""

    spec: LocalModelSpec
    generator: LocalTextGenerator | None = field(default=None, repr=False)
    clock: Callable[[], float] = field(default=time.monotonic, repr=False)
    snapshot_path: Path | None = None
    artifact_manifest: LocalArtifactManifest | None = None
    records: list[dict[str, object]] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if self.spec.backend != "transformers":
            raise ValueError("transformers_spec_required")

    def preflight(self) -> LocalModelPreflight:
        """Return availability, dependency, and artifact-identity metadata."""
        dependency = self.generator is not None or find_spec("transformers") is not None
        artifact = self.generator is not None or (self.snapshot_path is not None and self.artifact_manifest is not None)
        identity = False
        warnings: tuple[str, ...] = ()
        reason = None
        if dependency and artifact and self.generator is None:
            try:
                if self.snapshot_path is None:
                    raise ValueError("snapshot_path must be resolved before preflight")
                if self.artifact_manifest is None:
                    raise ValueError("artifact_manifest must be resolved before preflight")
                warnings = verify_transformers_snapshot(
                    self.snapshot_path,
                    self.artifact_manifest,
                )
                identity = self.artifact_manifest.fingerprint == self.spec.weight_manifest_sha256
                if not identity:
                    reason = "artifact_identity_mismatch"
            except (OSError, ValueError) as error:
                reason = f"artifact_invalid:{error}"
        elif not dependency:
            reason = "optional_dependency_unavailable:transformers"
        elif not artifact:
            reason = "artifact_resolution_required"
        else:
            identity = True
        available = dependency and artifact and identity
        return LocalModelPreflight(
            backend=self.spec.backend,
            model_id=self.spec.model_id,
            available=available,
            network_scope="none",
            reason=reason,
            dependency_available=dependency,
            artifact_available=artifact,
            identity_verified=identity,
            runtime_available=dependency,
            warnings=warnings,
        )

    def generate(self, request: LocalModelRequest) -> LocalModelResponse:
        """Generate structured output from the local model and validate it."""
        if self.generator is None:
            self.generator = self._load_generator()
        generator = self.generator
        schema_hint = json.dumps(dict(request.schema), indent=None, separators=(",", ":"))
        user_content = f"{request.user_prompt}\nReturn JSON matching this schema: {schema_hint}"
        started = self.clock()
        try:
            generated = generator(
                request.system_prompt,
                user_content,
                max_new_tokens=self.spec.max_output_tokens,
                temperature=self.spec.temperature,
                top_p=self.spec.top_p,
                seed=self.spec.seed,
            )
            generation = generated if isinstance(generated, LocalTextGeneration) else LocalTextGeneration(generated)
            content = generation.content
            if not content or not content.strip():
                raise LocalModelFailure("empty_output", "content=empty")
            self.records.append(
                {
                    "request_id": request.request_id,
                    "content": content,
                    "raw_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    "prompt_tokens": generation.prompt_tokens,
                    "output_tokens": generation.output_tokens,
                },
            )
            try:
                decoded = _extract_first_json(content)
            except (json.JSONDecodeError, ValueError) as parse_error:
                raise LocalModelFailure(
                    "malformed_output",
                    str(parse_error),
                ) from parse_error
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
            decoded,
            generation.prompt_tokens,
            generation.output_tokens,
            latency,
            raw_hash,
        )

    def _load_generator(self) -> LocalTextGenerator:
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
        except ImportError as error:
            raise LocalModelFailure("dependency", "optional_dependency_unavailable:transformers") from error
        if self.snapshot_path is None or self.artifact_manifest is None:
            raise LocalModelFailure("artifact", "artifact_resolution_required")
        try:
            verify_transformers_snapshot(self.snapshot_path, self.artifact_manifest)
        except (OSError, ValueError) as error:
            raise LocalModelFailure("artifact", str(error)) from error
        source = str(self.snapshot_path)
        tokenizer = AutoTokenizer.from_pretrained(  # type: ignore[no-untyped-call]
            source,
            local_files_only=True,
            trust_remote_code=False,
        )
        nf4 = self.spec.dtype == "nf4"
        if nf4:
            try:
                from transformers import BitsAndBytesConfig as _BnBConfig
            except ImportError as error:
                raise LocalModelFailure("dependency", "optional_dependency_unavailable:transformers") from error
            import torch

            quantization_config = _BnBConfig(  # type: ignore[no-untyped-call]
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
            model = AutoModelForCausalLM.from_pretrained(
                source,
                local_files_only=True,
                trust_remote_code=False,
                quantization_config=quantization_config,
                device_map=self.spec.device,
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                source,
                local_files_only=True,
                trust_remote_code=False,
                torch_dtype=self.spec.dtype,
                device_map=self.spec.device,
            )
        try:
            target_device = next(cast(Any, model).parameters(), None)
            device = str(target_device.device) if target_device is not None else self.spec.device
        except AttributeError:
            device = self.spec.device

        def generate(
            system_prompt: str,
            user_prompt: str,
            *,
            max_new_tokens: int,
            temperature: float,
            top_p: float,
            seed: int,
        ) -> LocalTextGeneration:
            """Generate text from the model and return content with token counts."""
            set_seed(seed)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            formatted = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            encoded = tokenizer(formatted, return_tensors="pt")
            if nf4:
                encoded = encoded.to(device)
            output = cast(Any, model).generate(
                **encoded,
                max_new_tokens=max_new_tokens,
                do_sample=temperature > 0,
                temperature=max(temperature, 1e-8),
                top_p=top_p,
            )
            prompt_count = int(encoded["input_ids"].shape[-1])
            content = cast(
                str,
                tokenizer.decode(
                    output[0][prompt_count:],
                    skip_special_tokens=True,
                ),
            )
            return LocalTextGeneration(
                content,
                prompt_count,
                int(output[0].shape[-1]) - prompt_count,
            )

        return generate


__all__ = ["LocalTextGeneration", "LocalTextGenerator", "TransformersLocalModel"]
