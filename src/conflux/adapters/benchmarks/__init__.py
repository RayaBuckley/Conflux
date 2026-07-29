"""Offline benchmark adapters.

Experimental external adapters are intentionally not re-exported.
"""

from .native import NativeBenchmarkResult

__all__ = ["NativeBenchmarkResult"]
