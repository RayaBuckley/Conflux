"""Targeted tests for fail-closed paths in modules omitted from the coverage gate."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from conflux.domain import Permission, PrimitiveAction, Provenance, ResourceRef
from conflux.ports import ProviderResult
from conflux.verification.ir import Sort, StateVariable, VerificationIR
from conflux.verification.results import FormalVerdict

pytestmark = pytest.mark.integration


def _trivial_ir() -> VerificationIR:
    return VerificationIR(
        id="test",
        bound=1,
        assumptions=(),
        variables=(StateVariable("safe", Sort.BOOLEAN, True, None, None),),
        transitions=(),
        invariants=(),
    )


def test_z3_backend_unavailable_returns_unknown() -> None:
    """Z3 backend returns UNKNOWN when z3-solver is not installed."""
    if "z3" in sys.modules:
        del sys.modules["z3"]
    with patch.dict(sys.modules, {"z3": None}):
        from conflux.verification.z3_backend import verify_with_z3

        result = verify_with_z3(_trivial_ir())
        assert result.verdict is FormalVerdict.UNKNOWN


def test_nuxmv_backend_unavailable_returns_unknown() -> None:
    """nuXmv backend returns UNKNOWN when the binary is not on PATH."""
    from conflux.verification.nuxmv_backend import NuXmvBackend

    backend = NuXmvBackend()
    with patch("conflux.verification.nuxmv_backend.shutil.which", return_value=None):
        result = backend.verify(_trivial_ir())
        assert result.verdict is FormalVerdict.UNKNOWN


def test_openai_compatible_model_unavailable_fails_closed() -> None:
    """OpenAI-compatible model adapter fails closed when httpx is unavailable."""
    if "httpx" in sys.modules:
        original = sys.modules["httpx"]
    else:
        original = None
    try:
        sys.modules["httpx"] = None
        if "conflux.adapters.models.openai_compatible" in sys.modules:
            del sys.modules["conflux.adapters.models.openai_compatible"]
        from conflux.adapters.models.openai_compatible import OpenAICompatibleModel

        model = OpenAICompatibleModel(
            endpoint="http://127.0.0.1:1/v1",
            model="test",
            allowed_resources=frozenset({("test", "out", "document")}),
            api_key_env="MISSING_KEY",
        )
        assert not model.available()
    finally:
        if original is not None:
            sys.modules["httpx"] = original
        elif "httpx" in sys.modules:
            del sys.modules["httpx"]


def test_code_sandbox_executor_fails_closed_without_docker() -> None:
    """Docker code sandbox executor fails closed when Docker is unavailable."""
    from conflux.adapters.providers.code_sandbox import DockerCodeSandboxExecutor

    executor = DockerCodeSandboxExecutor(
        root=Path("."),
        runtime_provenance=Provenance.unknown(),
    )
    action = PrimitiveAction(
        "test",
        "run",
        Permission("execute"),
        ResourceRef("test", "sandbox", "container"),
        (),
    )
    result = executor.execute(action, certificate_id="cert", action_fingerprint="fp")
    assert isinstance(result, ProviderResult)
    assert not result.success
    assert result.error
