"""Backward-compatible Ollama names for the provider-neutral LLM layer."""

from __future__ import annotations

from os import environ
from typing import Literal

from dotenv import load_dotenv
from pydantic import SecretStr

from .llm.config import LLMProvider, LLMSettings
from .llm.factory import create_model


class OllamaSettings(LLMSettings):
    """Compatibility settings model for callers that explicitly choose Ollama."""

    provider: Literal[LLMProvider.OLLAMA] = LLMProvider.OLLAMA
    base_url: str = "http://localhost:11434"
    api_key: SecretStr = SecretStr("ollama")

    @classmethod
    def from_env(cls) -> "OllamaSettings":
        """Load only legacy Ollama variables for backward-compatible callers."""
        load_dotenv()
        return cls(
            base_url=environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            model_name=environ.get("OLLAMA_MODEL", "llama3.1:8b"),
            api_key=environ.get("OLLAMA_API_KEY", "ollama"),
        )


def create_ollama_model(settings: OllamaSettings | None = None) -> object:
    """Create an Ollama model through the generalized model factory."""
    return create_model(settings)
