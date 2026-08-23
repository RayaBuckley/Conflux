"""Dual-backend laptop planning smoke contracts without model downloads."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from conflux.domain import fingerprint
from conflux.experiments import (
    BACKEND_LLAMA_CPP,
    BACKEND_TRANSFORMERS,
    ExperimentProtocol,
    LocalModelSpec,
    load_laptop_planning_smoke,
    run_laptop_planning_smoke,
    validate_laptop_protocols,
)
from conflux.ports import LocalModelPreflight, LocalModelRequest, LocalModelResponse
from scripts.prepare_laptop_smoke import main as prepare_laptop_smoke

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "experiments/manifests/planning-laptop-smoke-v1.json"


def _protocols() -> dict[str, ExperimentProtocol]:
    plan = load_laptop_planning_smoke(PLAN_PATH)
    specifications = {
        BACKEND_TRANSFORMERS: LocalModelSpec(
            backend="transformers",
            model_id=plan.source_model_id,
            revision=plan.source_revision,
            weight_manifest_sha256="a" * 64,
            tokenizer_id=plan.tokenizer_id,
            tokenizer_revision=plan.tokenizer_revision,
            prompt_template_version=plan.prompt_template_version,
            seed=plan.seed,
            temperature=0.0,
            top_p=1.0,
            max_output_tokens=128,
            context_limit=2048,
            device="cpu",
            dtype="float32",
            runtime_version="transformers-test",
        ),
        BACKEND_LLAMA_CPP: LocalModelSpec(
            backend="openai_compatible",
            model_id=plan.generated_llama_model_id,
            revision=plan.source_revision,
            weight_manifest_sha256="b" * 64,
            tokenizer_id=plan.tokenizer_id,
            tokenizer_revision=plan.tokenizer_revision,
            prompt_template_version=plan.prompt_template_version,
            seed=plan.seed,
            temperature=0.0,
            top_p=1.0,
            max_output_tokens=128,
            context_limit=2048,
            device="cpu",
            dtype="Q8_0",
            runtime_version="llama.cpp-b9637-test",
            endpoint="http://127.0.0.1:8080/v1",
        ),
    }
    return {
        backend: ExperimentProtocol(
            id=f"laptop-{backend}",
            track="planning",
            suite={
                "id": "planning-diagnostic-v1",
                "version": "1",
                "case_ids": list(plan.scenario_ids),
            },
            source_commit="a" * 40,
            inputs={},
            model=spec,
            prompts={"planner": plan.prompt_template_version},
            seeds=(plan.seed,),
            repetitions=plan.repetitions,
            bounds=dict(plan.bounds),
            environment={"execution": "modeled"},
            output_directory=f"output/runs/{backend}",
            rerun_command=("conflux", "plan", "compare", "--execute-local"),
        )
        for backend, spec in specifications.items()
    }


@dataclass
class _Model:
    model_id: str
    backend: str

    def preflight(self) -> LocalModelPreflight:
        return LocalModelPreflight(self.backend, self.model_id, True, "none", None)

    def generate(self, request: LocalModelRequest) -> LocalModelResponse:
        prompt = json.loads(request.user_prompt)
        actions = prompt["actions"]
        attempted = set(prompt["attempted"])
        available = [action for action in actions if action["id"] not in attempted]
        selected = available or actions
        if request.schema_name == "modeled_program_v1":
            payload: dict[str, object] = {
                "schema_version": "1",
                "id": request.request_id,
                "max_steps": 4,
                "effects": [
                    {
                        "id": f"effect-{index}",
                        "action_id": action["id"],
                        "dependencies": [] if index == 0 else [f"effect-{index - 1}"],
                        "declared_reads": action["declared_reads"],
                        "declared_writes": action["declared_writes"],
                    }
                    for index, action in enumerate(selected)
                ],
            }
        else:
            payload = {"action_ids": [action["id"] for action in selected]}
        return LocalModelResponse(
            request.request_id,
            self.model_id,
            payload,
            10,
            3,
            1,
            fingerprint(payload),
        )


def test_laptop_smoke_plan_has_exactly_sixteen_distinct_cells() -> None:
    plan = load_laptop_planning_smoke(PLAN_PATH)
    assert len(plan.matrix()) == 16
    assert len({cell.id for cell in plan.matrix()}) == 16
    assert plan.stop_after_bundle


def test_protocol_pair_requires_matching_source_prompt_seed_and_loopback() -> None:
    plan = load_laptop_planning_smoke(PLAN_PATH)
    protocols = _protocols()
    validate_laptop_protocols(plan, protocols)

    llama_model = protocols[BACKEND_LLAMA_CPP].model
    assert llama_model is not None
    bad_llama = replace(
        protocols[BACKEND_LLAMA_CPP],
        model=replace(llama_model, endpoint="http://10.0.0.2:8080/v1"),
    )
    with pytest.raises(ValueError, match="must_be_loopback"):
        validate_laptop_protocols(
            plan,
            {**protocols, BACKEND_LLAMA_CPP: bad_llama},
        )
    with pytest.raises(ValueError, match="backend_pair_required"):
        validate_laptop_protocols(plan, {BACKEND_TRANSFORMERS: protocols[BACKEND_TRANSFORMERS]})


def test_fake_dual_backend_run_retains_distinct_identities_and_all_cells() -> None:
    plan = load_laptop_planning_smoke(PLAN_PATH)
    protocols = _protocols()
    models = {
        backend: _Model(protocol.model.model_id, protocol.model.backend)
        for backend, protocol in protocols.items()
        if protocol.model is not None
    }
    result = run_laptop_planning_smoke(plan, protocols, models)
    observations = result["observations"]
    identities = result["model_identities"]
    assert isinstance(observations, list) and len(observations) == 16
    assert isinstance(identities, dict)
    assert identities[BACKEND_TRANSFORMERS]["model_id"] != identities[BACKEND_LLAMA_CPP]["model_id"]
    assert {item["backend_id"] for item in observations} == set(plan.backends)
    assert all(item["security_violations"] == 0 for item in observations)


def test_operator_preparation_hashes_local_artifacts_without_invoking_them(
    tmp_path: Path,
) -> None:
    weights = tmp_path / "weights.manifest"
    binary = tmp_path / "llama-server"
    gguf = tmp_path / "model.gguf"
    weights.write_text("local cache files", encoding="utf-8")
    binary.write_bytes(b"pinned llama binary")
    gguf.write_bytes(b"converted Q8_0 weights")
    output = tmp_path / "protocols"
    assert (
        prepare_laptop_smoke(
            [
                "--plan",
                str(PLAN_PATH),
                "--transformers-weight-manifest",
                str(weights),
                "--transformers-runtime-version",
                "4.test",
                "--llama-binary",
                str(binary),
                "--gguf",
                str(gguf),
                "--conversion-command",
                "convert_hf_to_gguf.py --outtype q8_0 LOCAL OUTPUT",
                "--source-commit",
                "a" * 40,
                "--output",
                str(output),
                "--licence-reviewed",
            ],
        )
        == 0
    )
    transformer = json.loads((output / "transformers.json").read_text())
    llama = json.loads((output / "llama_cpp_q8_0.json").read_text())
    assert transformer["model"]["weight_manifest_sha256"] != "0" * 64
    assert llama["model"]["weight_manifest_sha256"] != "0" * 64
    assert llama["environment"]["conversion_command"].startswith("convert_hf_to_gguf.py")
