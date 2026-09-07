"""Backward-compatible Ollama names for the provider-neutral LLM layer."""

from __future__ import annotations

from typing import Literal

from pydantic import SecretStr

from .llm.config import LLMProvider, LLMSettings
from .llm.factory import create_model


class OllamaSettings(LLMSettings):
    """Compatibility settings model for callers that explicitly choose Ollama."""

    provider: Literal[LLMProvider.OLLAMA] = LLMProvider.OLLAMA
    base_url: str = "http://localhost:11434"
    api_key: SecretStr = SecretStr("ollama")


def create_ollama_model(settings: OllamaSettings | None = None) -> object:
    """Create an Ollama model through the generalized model factory."""
    return create_model(settings)
