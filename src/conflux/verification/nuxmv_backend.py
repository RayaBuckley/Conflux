"""Optional nuXmv IC3 adapter for the supported Boolean IR subset."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Protocol

from conflux.domain import fingerprint

from .ir import Expression, ExpressionKind, Sort, VerificationIR
from .results import FormalVerdict, FormalVerificationResult


@dataclass(frozen=True, slots=True)
class NuXmvOutcome:
    """Captured stdout, stderr, and version from a nuXmv invocation."""

    exit_code: int
    stdout: str
    stderr: str
    version: str


class NuXmvRunner(Protocol):
    """Protocol for executing a nuXmv binary on a model file."""

    def run(
        self,
        binary: str,
        model_path: Path,
        commands: str,
    ) -> NuXmvOutcome:
        """Execute the nuXmv binary on the model file with the given commands."""
        ...


@dataclass(frozen=True, slots=True)
class SubprocessNuXmvRunner:
    """Runs nuXmv as a local subprocess with a configurable timeout."""

    timeout_seconds: float = 120.0

    def run(
        self,
        binary: str,
        model_path: Path,
        commands: str,
    ) -> NuXmvOutcome:
        """Execute the nuXmv binary on the model file with the given commands."""
        try:
            version = subprocess.run(  # noqa: S603
                (binary, "-h"),
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
            )
            process = subprocess.run(  # noqa: S603
                (binary, "-int", str(model_path)),
                input=commands,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            return NuXmvOutcome(
                1,
                "",
                f"{type(error).__name__}: {error}",
                "unavailable",
            )
        version_text = (version.stdout or version.stderr).splitlines()
        return NuXmvOutcome(
            process.returncode,
            process.stdout,
            process.stderr,
            version_text[0] if version_text else "unknown",
        )


_WSL_DISTRIBUTION = "Ubuntu"
_WSL_TMP = Path(f"//wsl.localhost/{_WSL_DISTRIBUTION}/tmp")


def _wsl_available() -> bool:
    try:
        result = subprocess.run(  # noqa: S603
            ("wsl", "-d", _WSL_DISTRIBUTION, "--", "which", "nuXmv"),
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        return False


@dataclass(frozen=True, slots=True)
class WslNuXmvRunner:
    """Runs nuXmv inside WSL, bridging the Windows/Linux file-system boundary."""

    timeout_seconds: float = 120.0

    def run(
        self,
        binary: str,
        model_path: Path,
        commands: str,
    ) -> NuXmvOutcome:
        """Execute nuXmv under WSL using a temporary shared model file."""
        wsl_dir = _WSL_TMP / f"conflux-nuxmv-{os.getpid()}-{id(model_path)}"
        wsl_dir.mkdir(parents=True, exist_ok=True)
        smv_file = wsl_dir / "model.smv"
        try:
            smv_file.write_text(model_path.read_text(encoding="utf-8"), encoding="utf-8")
            linux_model = f"/tmp/{wsl_dir.name}/model.smv"
            wsl_prefix: tuple[str, ...] = ("wsl", "-d", _WSL_DISTRIBUTION, "--")
            try:
                version = subprocess.run(  # noqa: S603
                    (*wsl_prefix, binary, "-h"),
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=False,
                )
                process = subprocess.run(  # noqa: S603
                    (*wsl_prefix, binary, "-int", linux_model),
                    input=commands,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    shell=False,
                )
            except (OSError, subprocess.SubprocessError) as error:
                return NuXmvOutcome(
                    1,
                    "",
                    f"{type(error).__name__}: {error}",
                    "unavailable",
                )
            version_text = (version.stdout or version.stderr).splitlines()
            return NuXmvOutcome(
                process.returncode,
                process.stdout,
                process.stderr,
                version_text[0] if version_text else "unknown",
            )
        finally:
            try:
                smv_file.unlink(missing_ok=True)
                wsl_dir.rmdir()
            except OSError:
                pass


@dataclass(frozen=True, slots=True)
class NuXmvBackend:
    """Optional nuXmv IC3 backend for the supported Boolean IR subset."""

    binary: str = "nuXmv"
    runner: NuXmvRunner = field(default_factory=lambda: WslNuXmvRunner() if _wsl_available() else SubprocessNuXmvRunner())
    availability: Callable[[str], bool] = field(
        default=lambda binary: shutil.which(binary) is not None or _wsl_available(),
        repr=False,
        compare=False,
    )

    def verify(self, ir: VerificationIR) -> FormalVerificationResult:
        """Verify Boolean IR invariants using nuXmv IC3, returning a formal result."""
        unsupported = tuple(variable.name for variable in ir.variables if variable.sort != Sort.BOOLEAN)
        if unsupported:
            return self._unknown(
                ir,
                f"unsupported_integer_variables:{','.join(unsupported)}",
            )
        if not ir.invariants:
            return self._unknown(ir, "no_safety_invariants")
        if not self.availability(self.binary):
            return self._unknown(ir, "optional_binary_unavailable:nuXmv")
        try:
            model = _smv(ir)
        except ValueError as error:
            return self._unknown(ir, f"unsupported_ir:{error}")
        commands = "go\ncheck_invar_ic3\nquit\n"
        with TemporaryDirectory(prefix="conflux-nuxmv-") as temporary:
            path = Path(temporary) / "model.smv"
            path.write_text(model, encoding="utf-8", newline="\n")
            outcome = self.runner.run(self.binary, path, commands)
        solver_hash = fingerprint({"backend": "nuXmv-ic3", "version": outcome.version})
        query_hash = fingerprint(commands)
        model_hash = fingerprint(model)
        output = f"{outcome.stdout}\n{outcome.stderr}"
        if outcome.exit_code != 0:
            return FormalVerificationResult(
                FormalVerdict.UNKNOWN,
                "nuxmv-ic3",
                ir.fingerprint,
                query_hash,
                solver_hash,
                model_hash,
                ir.bound,
                ir.assumptions,
                error=f"nuxmv_failed:{outcome.exit_code}:{fingerprint(output)}",
            )
        false_count = output.count(" is false")
        true_count = output.count(" is true")
        if false_count:
            return FormalVerificationResult(
                FormalVerdict.UNSAFE,
                "nuxmv-ic3",
                ir.fingerprint,
                query_hash,
                solver_hash,
                model_hash,
                ir.bound,
                ir.assumptions,
                (
                    {
                        "output_sha256": fingerprint(output),
                        "failed_invariants": false_count,
                    },
                ),
            )
        if true_count >= len(ir.invariants):
            return FormalVerificationResult(
                FormalVerdict.SAFE,
                "nuxmv-ic3",
                ir.fingerprint,
                query_hash,
                solver_hash,
                model_hash,
                ir.bound,
                ir.assumptions,
            )
        return FormalVerificationResult(
            FormalVerdict.UNKNOWN,
            "nuxmv-ic3",
            ir.fingerprint,
            query_hash,
            solver_hash,
            model_hash,
            ir.bound,
            ir.assumptions,
            error=f"nuxmv_unrecognised_output:{fingerprint(output)}",
        )

    def _unknown(self, ir: VerificationIR, error: str) -> FormalVerificationResult:
        return FormalVerificationResult(
            FormalVerdict.UNKNOWN,
            "nuxmv-ic3",
            ir.fingerprint,
            fingerprint({"ir": ir.fingerprint, "command": "check_invar_ic3"}),
            fingerprint({"backend": "nuXmv", "version": "unavailable"}),
            None,
            ir.bound,
            ir.assumptions,
            error=error,
        )


def _smv(ir: VerificationIR) -> str:
    variables = "\n".join(f"  {variable.name} : boolean;" for variable in ir.variables)
    initial = " & ".join((variable.name if variable.initial is True else f"!{variable.name}") for variable in ir.variables)
    transition_terms: list[str] = []
    for rule in sorted(ir.transitions, key=lambda item: item.id):
        assignments = {item.variable: item.expression for item in rule.assignments}
        updates = " & ".join(
            f"next({variable.name}) = {_render(assignments.get(variable.name, Expression.variable(variable.name)))}"
            for variable in ir.variables
        )
        transition_terms.append(f"({_render(rule.guard)} & {updates})")
    stutter = " & ".join(f"next({variable.name}) = {variable.name}" for variable in ir.variables)
    transition = " | ".join((*transition_terms, f"({stutter})"))
    invariants = "\n".join(
        f"INVARSPEC NAME {item.id} := {_render(item.expression)};" for item in sorted(ir.invariants, key=lambda item: item.id)
    )
    return f"MODULE main\nVAR\n{variables}\nINIT {initial};\nTRANS {transition};\n{invariants}\n"


def _render(expression: Expression) -> str:
    if expression.kind == ExpressionKind.CONSTANT:
        if not isinstance(expression.value, bool):
            raise ValueError("nuXmv subset supports Boolean constants only")
        return "TRUE" if expression.value else "FALSE"
    if expression.kind == ExpressionKind.VARIABLE:
        assert isinstance(expression.value, str)
        return expression.value
    values = tuple(_render(argument) for argument in expression.arguments)
    if expression.kind == ExpressionKind.NOT:
        return f"!({values[0]})"
    if expression.kind == ExpressionKind.AND:
        return "(" + " & ".join(values) + ")"
    if expression.kind == ExpressionKind.OR:
        return "(" + " | ".join(values) + ")"
    if expression.kind == ExpressionKind.EQUAL:
        return f"({values[0]} = {values[1]})"
    raise ValueError(f"nuXmv subset does not support {expression.kind.value}")


__all__ = [
    "NuXmvBackend",
    "NuXmvOutcome",
    "NuXmvRunner",
    "SubprocessNuXmvRunner",
    "WslNuXmvRunner",
]
