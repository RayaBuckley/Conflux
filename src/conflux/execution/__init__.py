"""
Execution engine.
The execution package is responsible for modelling how artefacts are transformed
through computation while preserving provenance.
Unlike traditional execution engines that operate on raw values, every
operation in this system consumes and produces `Artifact` objects. This ensures
that provenance is propagated throughout execution and is available for
authorisation decisions.
Initially, this package will contain a simple execution model. More advanced
execution graphs and scheduling mechanisms may be introduced later without
changing the core interfaces.
"""
from .operations import Operation

__all__ = [
    "Operation",
]
