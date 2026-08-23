"""Portable, non-invasive runtime capability discovery."""

from __future__ import annotations

import os
import platform
import shutil
import sys
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CapabilityReport:
    """Snapshot of runtime capabilities: OS, Python, CPU, container, GPU, schedulers, and optional backends."""

    schema_version: str
    os: str
    python: str
    cpu_count: int | None
    container: str | None
    gpu_probe: str | None
    schedulers: tuple[str, ...]
    optional_backends: dict[str, bool]

    @classmethod
    def discover(cls) -> CapabilityReport:
        """Probe the host environment and return a populated capability report."""
        container = next(
            (name for name in ("docker", "podman") if shutil.which(name)),
            None,
        )
        gpu_probe = next(
            (name for name in ("nvidia-smi", "rocm-smi") if shutil.which(name)),
            None,
        )
        schedulers = tuple(name for name in ("sinfo", "squeue", "sbatch", "qsub") if shutil.which(name))
        return cls(
            schema_version="1",
            os=platform.platform(),
            python=sys.version.split()[0],
            cpu_count=os.cpu_count(),
            container=container,
            gpu_probe=gpu_probe,
            schedulers=schedulers,
            optional_backends={
                "openai_compatible": _available("httpx"),
                "hugging_face": _available("transformers"),
                "z3": _available("z3"),
                "nuxmv": shutil.which("nuXmv") is not None,
                "agentdojo": _available("agentdojo"),
            },
        )

    def to_dict(self) -> dict[str, object]:
        """Serialise the report to a plain dictionary."""
        return {
            "schema_version": self.schema_version,
            "os": self.os,
            "python": self.python,
            "cpu_count": self.cpu_count,
            "container": self.container,
            "gpu_probe": self.gpu_probe,
            "schedulers": list(self.schedulers),
            "optional_backends": self.optional_backends,
        }


def _available(module: str) -> bool:
    from importlib.util import find_spec

    return find_spec(module) is not None


__all__ = ["CapabilityReport"]
