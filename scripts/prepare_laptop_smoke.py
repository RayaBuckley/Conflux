"""Create resolved laptop-smoke protocols from operator-owned local artifacts."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path
from typing import Sequence

from conflux.domain import canonical_json
from conflux.experiments import (
    BACKEND_LLAMA_CPP,
    BACKEND_TRANSFORMERS,
    ExperimentProtocol,
    LaptopPlanningSmokePlan,
    LocalModelSpec,
    load_laptop_planning_smoke,
    validate_laptop_protocols,
)

ROOT = Path(__file__).resolve().parents[1]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve protocols only; never download, convert, or invoke a model.")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--transformers-weight-manifest", type=Path, required=True)
    parser.add_argument("--transformers-runtime-version", required=True)
    parser.add_argument("--llama-binary", type=Path, required=True)
    parser.add_argument("--gguf", type=Path, required=True)
    parser.add_argument("--llama-endpoint", default="http://127.0.0.1:8080/v1")
    parser.add_argument("--conversion-command", required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--licence-reviewed", action="store_true")
    arguments = parser.parse_args(argv)
    if not arguments.licence_reviewed:
        parser.error("--licence-reviewed is required before resolving live protocols")
    artifact_paths = (
        arguments.transformers_weight_manifest,
        arguments.llama_binary,
        arguments.gguf,
    )
    missing = [str(path) for path in artifact_paths if not path.is_file()]
    if missing:
        parser.error("local artifact missing: " + ", ".join(missing))
    plan = load_laptop_planning_smoke(arguments.plan)
    source_commit = str(arguments.source_commit or _head_commit())
    transformer_hash = _sha256(arguments.transformers_weight_manifest)
    binary_hash = _sha256(arguments.llama_binary)
    gguf_hash = _sha256(arguments.gguf)
    transformers = LocalModelSpec(
        backend="transformers",
        model_id=plan.source_model_id,
        revision=plan.source_revision,
        weight_manifest_sha256=transformer_hash,
        tokenizer_id=plan.tokenizer_id,
        tokenizer_revision=plan.tokenizer_revision,
        prompt_template_version=plan.prompt_template_version,
        seed=plan.seed,
        temperature=0.0,
        top_p=1.0,
        max_output_tokens=256,
        context_limit=4096,
        device="cpu",
        dtype="float32",
        runtime_version=str(arguments.transformers_runtime_version),
    )
    llama = LocalModelSpec(
        backend="openai_compatible",
        model_id=plan.generated_llama_model_id,
        revision=plan.source_revision,
        weight_manifest_sha256=gguf_hash,
        tokenizer_id=plan.tokenizer_id,
        tokenizer_revision=plan.tokenizer_revision,
        prompt_template_version=plan.prompt_template_version,
        seed=plan.seed,
        temperature=0.0,
        top_p=1.0,
        max_output_tokens=256,
        context_limit=4096,
        device="cpu",
        dtype=plan.quantization,
        runtime_version=f"llama.cpp-{plan.llama_cpp_release}:{binary_hash}",
        endpoint=str(arguments.llama_endpoint),
    )
    protocols = {
        BACKEND_TRANSFORMERS: _protocol(
            plan,
            source_commit,
            BACKEND_TRANSFORMERS,
            transformers,
            {
                "transformers_weight_manifest_sha256": transformer_hash,
                "licence_reviewed": "true",
            },
        ),
        BACKEND_LLAMA_CPP: _protocol(
            plan,
            source_commit,
            BACKEND_LLAMA_CPP,
            llama,
            {
                "llama_binary_sha256": binary_hash,
                "gguf_sha256": gguf_hash,
                "conversion_command": str(arguments.conversion_command),
                "quantization": plan.quantization,
                "licence_reviewed": "true",
            },
        ),
    }
    validate_laptop_protocols(plan, protocols)
    arguments.output.mkdir(parents=True, exist_ok=True)
    for backend, protocol in protocols.items():
        path = arguments.output / f"{backend}.json"
        path.write_text(
            canonical_json(protocol.to_dict()) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(f"Resolved two local protocols in {arguments.output}")
    return 0


def _protocol(
    plan: LaptopPlanningSmokePlan,
    source_commit: str,
    backend: str,
    model: LocalModelSpec,
    environment: dict[str, object],
) -> ExperimentProtocol:
    return ExperimentProtocol(
        id=f"planning-laptop-smoke-v1-{backend}",
        track="planning",
        suite={
            "id": "planning-diagnostic-v1",
            "version": "1",
            "case_ids": list(plan.scenario_ids),
        },
        source_commit=source_commit,
        inputs={
            "experiments/manifests/planning-laptop-smoke-v1.json": _sha256(ROOT / "experiments/manifests/planning-laptop-smoke-v1.json")
        },
        model=model,
        prompts={"planner": plan.prompt_template_version},
        seeds=(plan.seed,),
        repetitions=plan.repetitions,
        bounds=dict(plan.bounds),
        environment={"execution": "modeled_actions_only", **environment},
        output_directory=f"output/runs/laptop-planning-smoke-v1/{backend}",
        rerun_command=(
            "conflux",
            "plan",
            "laptop-smoke",
            "--execute-local",
        ),
    )


def _head_commit() -> str:
    result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
