"""Pinned-container code sandbox with fail-closed capability enforcement."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Mapping, Protocol

from conflux.domain import Artifact, PrimitiveAction, Provenance, canonical_json, fingerprint
from conflux.domain import action_fingerprint as fingerprint_action
from conflux.planning.code_execution import (
    CapabilityEnvelope,
    CodeExecutionRequest,
    CodeExecutionResult,
    CodeOutput,
)
from conflux.ports import ProviderResult


@dataclass(frozen=True, slots=True)
class CommandOutcome:
    exit_code: int | None
    stdout: bytes = b""
    stderr: bytes = b""
    outputs: Mapping[str, bytes] = field(default_factory=dict)
    timed_out: bool = False
    output_limited: bool = False
    error: str | None = None


class CommandRunner(Protocol):
    def run(
        self,
        command: tuple[str, ...],
        *,
        workspace: Path,
        timeout_seconds: float,
        output_bytes: int,
    ) -> CommandOutcome: ...


@dataclass(frozen=True, slots=True)
class SubprocessCommandRunner:
    """Run an already-tokenised command and bound retained process output."""

    poll_seconds: float = 0.01

    def run(
        self,
        command: tuple[str, ...],
        *,
        workspace: Path,
        timeout_seconds: float,
        output_bytes: int,
    ) -> CommandOutcome:
        stdout_path = workspace / ".stdout"
        stderr_path = workspace / ".stderr"
        started = time.monotonic()
        try:
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                process = subprocess.Popen(  # noqa: S603 - authenticated argv, never a shell
                    command,
                    cwd=workspace,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=stderr,
                    shell=False,
                )
                timed_out = False
                output_limited = False
                while process.poll() is None:
                    if time.monotonic() - started >= timeout_seconds:
                        timed_out = True
                        process.kill()
                        break
                    if _file_size(stdout_path) + _file_size(stderr_path) > output_bytes:
                        output_limited = True
                        process.kill()
                        break
                    time.sleep(self.poll_seconds)
                exit_code = process.wait(timeout=5)
        except (OSError, subprocess.SubprocessError) as error:
            return CommandOutcome(None, error=f"{type(error).__name__}: {error}")
        stdout_data = _bounded_read(stdout_path, output_bytes)
        stderr_data = _bounded_read(stderr_path, max(0, output_bytes - len(stdout_data)))
        outputs, output_error = _capture_outputs(workspace / "outputs", output_bytes)
        return CommandOutcome(
            exit_code,
            stdout_data,
            stderr_data,
            outputs,
            timed_out,
            output_limited,
            output_error,
        )


@dataclass(frozen=True, slots=True)
class DockerCodeSandboxExecutor:
    """Execute a canonical `execute_code` action in one pinned container."""

    root: Path
    runtime_provenance: Provenance
    docker_binary: str = "docker"
    runner: CommandRunner = SubprocessCommandRunner()
    availability: Callable[[str], bool] = field(
        default=lambda binary: shutil.which(binary) is not None,
        repr=False,
        compare=False,
    )

    def execute(
        self,
        action: object,
        *,
        certificate_id: str,
        action_fingerprint: str,
    ) -> ProviderResult:
        if (
            not isinstance(action, PrimitiveAction)
            or not certificate_id
            or action_fingerprint != fingerprint_action(action)
        ):
            return ProviderResult(False, error="certificate_action_mismatch")
        if action.operation != "execute_code":
            return ProviderResult(False, error="unsupported_code_action")
        if action.resource is None or action.resource.provider != "code-sandbox":
            return ProviderResult(False, error="unsupported_code_resource")
        try:
            request = self._request(action)
            self._validate_enforcement(request.envelope)
            workspace_root = self._workspace_root(request.envelope.workspace)
        except (TypeError, ValueError, OSError) as error:
            return ProviderResult(
                False,
                error=f"code_request_rejected:{type(error).__name__}:{error}",
            )
        if not self.availability(self.docker_binary):
            return ProviderResult(False, error="sandbox_unavailable:docker")
        workspace_root.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="conflux-code-", dir=workspace_root) as temporary:
            workspace = Path(temporary)
            (workspace / "outputs").mkdir()
            (workspace / "source.py").write_text(
                request.source.value,
                encoding="utf-8",
                newline="\n",
            )
            inputs = {
                item.id: {
                    "value": item.value,
                    "fingerprint": item.fingerprint,
                }
                for item in request.inputs
            }
            (workspace / "inputs.json").write_text(
                canonical_json(inputs) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            command = _docker_command(
                self.docker_binary,
                workspace,
                request.envelope,
            )
            outcome = self.runner.run(
                command,
                workspace=workspace,
                timeout_seconds=request.envelope.timeout_seconds,
                output_bytes=request.envelope.output_bytes,
            )
            result = _result(request, command, outcome)
        if not result.success:
            return ProviderResult(False, outcome=result, error=result.failure_category)
        return ProviderResult(True, outcome=result)

    def _request(self, action: PrimitiveAction) -> CodeExecutionRequest:
        arguments = {artifact.label: artifact for artifact in action.inputs}
        if set(arguments) != {"source", "inputs", "output_contract", "envelope"}:
            raise ValueError("execute_code arguments do not match the authenticated schema")
        source = arguments["source"]
        if not isinstance(source.value, str):
            raise TypeError("execute_code source must be text")
        input_bundle = arguments["inputs"]
        if not isinstance(input_bundle.value, list):
            raise TypeError("execute_code inputs must be a JSON array")
        output_contract = arguments["output_contract"].value
        if not isinstance(output_contract, Mapping):
            raise TypeError("execute_code output contract must be an object")
        envelope = CapabilityEnvelope.from_dict(arguments["envelope"].value)
        if action.resource is None or action.resource.resource_id != envelope.workspace:
            raise ValueError("code workspace resource does not match the envelope")
        inputs = tuple(
            Artifact(
                f"{input_bundle.id}:{index}",
                value,
                input_bundle.provenance,
            )
            for index, value in enumerate(input_bundle.value)
        )
        return CodeExecutionRequest(
            action.id,
            Artifact(source.id, source.value, source.provenance, source.label),
            inputs,
            dict(output_contract),
            envelope,
            self.runtime_provenance,
        )

    def _validate_enforcement(self, envelope: CapabilityEnvelope) -> None:
        if envelope.network_allowlist:
            raise ValueError("network allowlists are unsupported; network must remain denied")
        if envelope.credential_capabilities:
            raise ValueError("credential capabilities are unsupported")
        if set(envelope.read_paths) - {"source.py", "inputs.json"}:
            raise ValueError("unsupported read path")
        if set(envelope.write_paths) != {"outputs"}:
            raise ValueError("only the outputs directory is writable")

    def _workspace_root(self, relative: str) -> Path:
        root = self.root.resolve(strict=True)
        target = root.joinpath(*Path(relative).parts)
        if target.is_symlink():
            raise ValueError("sandbox workspace cannot be a symlink")
        resolved = target.resolve(strict=False)
        if not resolved.is_relative_to(root):
            raise ValueError("sandbox workspace escapes configured root")
        return resolved


def _docker_command(
    binary: str,
    workspace: Path,
    envelope: CapabilityEnvelope,
) -> tuple[str, ...]:
    source = (workspace / "source.py").resolve()
    inputs = (workspace / "inputs.json").resolve()
    outputs = (workspace / "outputs").resolve()
    return (
        binary,
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        str(envelope.process_limit),
        "--memory",
        str(envelope.memory_bytes),
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=16777216",
        "--mount",
        f"type=bind,src={source},dst=/workspace/source.py,readonly",
        "--mount",
        f"type=bind,src={inputs},dst=/workspace/inputs.json,readonly",
        "--mount",
        f"type=bind,src={outputs},dst=/workspace/outputs",
        "--workdir",
        "/workspace",
        "--entrypoint",
        "python",
        envelope.runtime_image,
        "-I",
        "-S",
        "source.py",
    )


def _result(
    request: CodeExecutionRequest,
    command: tuple[str, ...],
    outcome: CommandOutcome,
) -> CodeExecutionResult:
    category: str | None = None
    if outcome.error is not None:
        category = f"sandbox_error:{outcome.error}"
    elif outcome.timed_out:
        category = "sandbox_timeout"
    elif outcome.output_limited:
        category = "sandbox_output_bound"
    elif outcome.exit_code != 0:
        category = "code_nonzero_exit"
    outputs = tuple(
        CodeOutput(
            path,
            hashlib.sha256(content).hexdigest(),
            len(content),
            Artifact(
                f"code-output:{request.id}:{path}",
                content,
                request.output_provenance,
                path,
            ),
        )
        for path, content in sorted(outcome.outputs.items())
    )
    return CodeExecutionResult(
        category is None,
        request.fingerprint,
        request.envelope.runtime_image,
        request.envelope.fingerprint,
        fingerprint(command),
        outcome.exit_code,
        hashlib.sha256(outcome.stdout).hexdigest(),
        hashlib.sha256(outcome.stderr).hexdigest(),
        outputs,
        ("source.py", "inputs.json"),
        tuple(item.path for item in outputs),
        category,
    )


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _bounded_read(path: Path, limit: int) -> bytes:
    with path.open("rb") as stream:
        return stream.read(limit)


def _capture_outputs(root: Path, limit: int) -> tuple[dict[str, bytes], str | None]:
    outputs: dict[str, bytes] = {}
    total = 0
    try:
        for path in sorted(root.rglob("*")):
            if path.is_symlink():
                return {}, "sandbox_output_symlink"
            if not path.is_file():
                continue
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(root.resolve(strict=True)):
                return {}, "sandbox_output_escape"
            content = path.read_bytes()
            total += len(content)
            if total > limit:
                return {}, "sandbox_output_bound"
            outputs[path.relative_to(root).as_posix()] = content
    except OSError as error:
        return {}, f"sandbox_output_error:{type(error).__name__}"
    return outputs, None


__all__ = [
    "CommandOutcome",
    "CommandRunner",
    "DockerCodeSandboxExecutor",
    "SubprocessCommandRunner",
]
