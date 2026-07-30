"""Provider adapters; effectful experimental adapters fail closed."""

from .base import RecordingExecutor, StaticEnvironmentProvider
from .code_sandbox import DockerCodeSandboxExecutor
from .docker import UnsupportedDockerExecutor
from .filesystem import FilesystemSnapshotProvider
from .runtime import ConfinedFilesystemExecutor, InMemoryExecutor

__all__ = [
    "ConfinedFilesystemExecutor",
    "DockerCodeSandboxExecutor",
    "FilesystemSnapshotProvider",
    "InMemoryExecutor",
    "RecordingExecutor",
    "StaticEnvironmentProvider",
    "UnsupportedDockerExecutor",
]
