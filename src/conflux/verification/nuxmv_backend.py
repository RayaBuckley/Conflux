"""Optional nuXmv IC3 adapter for the supported Boolean IR subset."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol

from conflux.domain import fingerprint

from .ir import Expression, ExpressionKind, Sort, StateVariable, VerificationIR
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
            version = subprocess.run(
                (binary, "-h"),
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
            )
            process = subprocess.run(
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
        result = subprocess.run(
            ("wsl", "-d", _WSL_DISTRIBUTION, "--", "bash", "-ic", "which nuXmv"),
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
            smv_file.write_text(model_path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
            linux_model = f"/tmp/{wsl_dir.name}/model.smv"
            wsl_prefix: tuple[str, ...] = ("wsl", "-d", _WSL_DISTRIBUTION, "--", "bash", "-ic")
            try:
                version = subprocess.run(
                    (*wsl_prefix, f"{binary} -h"),
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=False,
                )
                process = subprocess.run(
                    (*wsl_prefix, f"{binary} -int {linux_model}"),
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


_NUXMV_PATH_ENV = "CONFLUX_NUXMV_PATH"


def configured_binary(default: str = "nuXmv") -> str:
    """Return the binary named by ``CONFLUX_NUXMV_PATH``, or ``default`` when it is unset.

    The environment is read on every call, so an export in the shell that runs the
    verification is enough.  An empty or blank value is unset, not a path.
    """
    override = os.environ.get(_NUXMV_PATH_ENV, "").strip()
    return override or default


def default_runner(binary: str) -> NuXmvRunner:
    """Return the runner to use for ``binary`` on this host.

    A binary that ``PATH`` resolves is used directly.  It is the one a verification
    record names, it needs no shell, and on a Windows host with WSL installed it is
    still the faster of the two.  WSL is the fallback for a nuXmv that exists only
    inside a distribution, and it is probed only when no local binary is found.
    """
    if shutil.which(binary) is not None:
        return SubprocessNuXmvRunner()
    if _wsl_available():
        return WslNuXmvRunner()
    return SubprocessNuXmvRunner()


@dataclass(frozen=True, slots=True)
class NuXmvBackend:
    """Optional nuXmv IC3 backend for the supported finite-domain IR subset."""

    binary: str | None = None
    runner: NuXmvRunner | None = None
    availability: Callable[[str], bool] = field(
        default=lambda binary: shutil.which(binary) is not None or _wsl_available(),
        repr=False,
        compare=False,
    )

    def resolved_binary(self) -> str:
        """Return the binary to run: the constructor value, the environment, or ``nuXmv``."""
        return self.binary or configured_binary()

    def selected_runner(self) -> NuXmvRunner:
        """Return the runner this backend uses: the given one, or the host default."""
        return self.runner if self.runner is not None else default_runner(self.resolved_binary())

    def verify(self, ir: VerificationIR, *, smt: bool = False) -> FormalVerificationResult:
        """Verify IR invariants with nuXmv, returning a formal result.

        ``smt=False`` keeps the recorded behaviour: BDD IC3 over a finite-domain model.
        ``smt=True`` renders unbounded integer variables as infinite-precision integers and
        checks the invariants on the SMT route (``go_msat`` then ``msat_check_invar_bmc``),
        which answers for a symbolic bound rather than one recorded bound. A model the SMT
        route cannot settle is UNKNOWN, never safe.
        """
        backend = "nuxmv-msat" if smt else "nuxmv-ic3"
        if not ir.invariants:
            return self._unknown(ir, "no_safety_invariants", backend)
        binary = self.resolved_binary()
        if not self.availability(binary):
            return self._unknown(ir, "optional_binary_unavailable:nuXmv", backend)
        try:
            model = _smv(ir, unbounded=smt)
        except ValueError as error:
            return self._unknown(ir, f"unsupported_ir:{error}", backend)
        commands = (
            "go_msat\nmsat_check_invar_bmc\nquit\n"
            if smt
            else "go\nbuild_boolean_model\ncheck_invar_ic3\nquit\n"
        )
        with TemporaryDirectory(prefix="conflux-nuxmv-") as temporary:
            path = Path(temporary) / "model.smv"
            path.write_text(model, encoding="utf-8", newline="\n")
            outcome = self.selected_runner().run(binary, path, commands)
        solver_hash = fingerprint({"backend": backend, "version": outcome.version})
        query_hash = fingerprint(commands)
        model_hash = fingerprint(model)
        output = f"{outcome.stdout}\n{outcome.stderr}"
        if outcome.exit_code != 0:
            return FormalVerificationResult(
                FormalVerdict.UNKNOWN,
                backend,
                ir.fingerprint,
                query_hash,
                solver_hash,
                model_hash,
                ir.bound,
                ir.assumptions,
                error=f"nuxmv_failed:{outcome.exit_code}:{fingerprint(output)}",
            )
        # An incomplete induction prints "cannot prove the invariant X is true or false", which
        # contains the substring " is true"; drop those lines before counting settled invariants.
        settled = "\n".join(line for line in output.splitlines() if "cannot prove" not in line)
        false_count = settled.count(" is false")
        true_count = settled.count(" is true")
        incomplete = false_count == 0 and "cannot prove" in output
        if false_count:
            return FormalVerificationResult(
                FormalVerdict.UNSAFE,
                backend,
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
                backend,
                ir.fingerprint,
                query_hash,
                solver_hash,
                model_hash,
                ir.bound,
                ir.assumptions,
            )
        if incomplete:
            return FormalVerificationResult(
                FormalVerdict.UNKNOWN,
                backend,
                ir.fingerprint,
                query_hash,
                solver_hash,
                model_hash,
                ir.bound,
                ir.assumptions,
                error=f"nuxmv_incomplete:{fingerprint(output)}",
            )
        return FormalVerificationResult(
            FormalVerdict.UNKNOWN,
            backend,
            ir.fingerprint,
            query_hash,
            solver_hash,
            model_hash,
            ir.bound,
            ir.assumptions,
            error=f"nuxmv_unrecognised_output:{fingerprint(output)}",
        )

    def _unknown(
        self,
        ir: VerificationIR,
        error: str,
        backend: str = "nuxmv-ic3",
    ) -> FormalVerificationResult:
        return FormalVerificationResult(
            FormalVerdict.UNKNOWN,
            backend,
            ir.fingerprint,
            fingerprint({"ir": ir.fingerprint, "ir_bound": ir.bound}),
            fingerprint({"backend": "nuXmv", "version": "unavailable"}),
            None,
            ir.bound,
            ir.assumptions,
            error=error,
        )


def _domain(variable: StateVariable, *, unbounded: bool = False) -> str:
    """Return the SMV type of a state variable, or fail closed on an unsupported sort.

    With ``unbounded`` the SMT route is being rendered, so an integer variable without a declared
    maximum becomes an infinite-precision integer instead of failing closed. The guards in the
    model, not the type, then keep the run finite.
    """
    if variable.sort == Sort.BOOLEAN:
        return "boolean"
    if variable.sort == Sort.INTEGER:
        if variable.minimum is None or variable.maximum is None:
            if unbounded:
                return "integer"
            raise ValueError(f"integer state variable {variable.name} requires a bounded domain")
        return f"{variable.minimum}..{variable.maximum}"
    raise ValueError(f"nuXmv subset does not support sort {variable.sort.value}")


def _initial(variable: StateVariable) -> str:
    """Return the SMV initial condition for a state variable."""
    if variable.sort == Sort.BOOLEAN:
        return variable.name if variable.initial is True else f"!{variable.name}"
    if variable.sort == Sort.INTEGER:
        if not isinstance(variable.initial, int) or isinstance(variable.initial, bool):
            raise ValueError(f"integer state variable {variable.name} requires an integer initial value")
        return f"{variable.name} = {variable.initial}"
    raise ValueError(f"nuXmv subset does not support sort {variable.sort.value}")


def _smv(ir: VerificationIR, *, unbounded: bool = False) -> str:
    variables = "\n".join(f"  {variable.name} : {_domain(variable, unbounded=unbounded)};" for variable in ir.variables)
    initial = " & ".join(_initial(variable) for variable in ir.variables)
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
        if isinstance(expression.value, bool):
            return "TRUE" if expression.value else "FALSE"
        if isinstance(expression.value, int):
            return str(expression.value)
        raise ValueError("nuXmv subset supports Boolean and integer constants only")
    if expression.kind == ExpressionKind.VARIABLE:
        if not isinstance(expression.value, str):
            raise TypeError(f"expected str variable name, got {type(expression.value).__name__}")
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
    if expression.kind == ExpressionKind.IMPLIES:
        return f"({values[0]} -> {values[1]})"
    if expression.kind == ExpressionKind.LESS_EQUAL:
        return f"({values[0]} <= {values[1]})"
    if expression.kind == ExpressionKind.GREATER_EQUAL:
        return f"({values[0]} >= {values[1]})"
    if expression.kind == ExpressionKind.LESS_THAN:
        return f"({values[0]} < {values[1]})"
    if expression.kind == ExpressionKind.GREATER_THAN:
        return f"({values[0]} > {values[1]})"
    if expression.kind == ExpressionKind.ADD:
        return f"({values[0]} + {values[1]})"
    raise ValueError(f"nuXmv subset does not support {expression.kind.value}")


__all__ = [
    "NuXmvBackend",
    "NuXmvOutcome",
    "NuXmvRunner",
    "SubprocessNuXmvRunner",
    "WslNuXmvRunner",
    "configured_binary",
    "default_runner",
]
