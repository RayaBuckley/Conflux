"""Structured adapter for model artifacts already present on the machine."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Callable, Protocol, cast

from jsonschema import Draft202012Validator, ValidationError

from conflux.domain import canonical_json
from conflux.ports import LocalModelPreflight, LocalModelRequest, LocalModelResponse, LocalModelSpec

from .artifacts import LocalArtifactManifest, verify_transformers_snapshot
from .local_openai import LocalModelFailure


class LocalTextGenerator(Protocol):
    def __call__(self, prompt: str, *, max_new_tokens: int, temperature: float, top_p: float, seed: int) -> str: ...


@dataclass(slots=True)
class TransformersLocalModel:
    spec: LocalModelSpec
    generator: LocalTextGenerator | None = field(default=None, repr=False)
    clock: Callable[[], float] = field(default=time.monotonic, repr=False)
    snapshot_path: Path | None = None
    artifact_manifest: LocalArtifactManifest | None = None

    def __post_init__(self) -> None:
        if self.spec.backend != "transformers":
            raise ValueError("transformers_spec_required")

    def preflight(self) -> LocalModelPreflight:
        dependency = self.generator is not None or find_spec("transformers") is not None
        artifact = self.generator is not None or (
            self.snapshot_path is not None and self.artifact_manifest is not None
        )
        identity = False
        warnings: tuple[str, ...] = ()
        reason = None
        if dependency and artifact and self.generator is None:
            try:
                assert self.snapshot_path is not None
                assert self.artifact_manifest is not None
                warnings = verify_transformers_snapshot(
                    self.snapshot_path,
                    self.artifact_manifest,
                )
                identity = (
                    self.artifact_manifest.fingerprint
                    == self.spec.weight_manifest_sha256
                )
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
        if self.snapshot_path is None or self.artifact_manifest is None:
            raise LocalModelFailure("artifact", "artifact_resolution_required")
        try:
            verify_transformers_snapshot(self.snapshot_path, self.artifact_manifest)
        except (OSError, ValueError) as error:
            raise LocalModelFailure("artifact", str(error)) from error
        source = str(self.snapshot_path)
        tokenizer = AutoTokenizer.from_pretrained(
            source,
            local_files_only=True,
            trust_remote_code=False,
        )
        model = AutoModelForCausalLM.from_pretrained(
            source,
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
