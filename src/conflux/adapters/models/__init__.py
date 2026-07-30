"""Model adapters."""

from .huggingface import HuggingFaceCausalModel
from .openai_compatible import (
    ModelOutputError,
    ModelProviderError,
    OpenAICompatibleModel,
)
from .scripted import ScriptedModel

__all__ = [
    "HuggingFaceCausalModel",
    "ModelOutputError",
    "ModelProviderError",
    "OpenAICompatibleModel",
    "ScriptedModel",
]
