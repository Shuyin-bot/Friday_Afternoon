"""Provider-neutral LLM configuration."""

from __future__ import annotations

from enum import Enum
from os import environ

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr


class LLMProvider(str, Enum):
    """LLM providers supported by the model factory."""

    OLLAMA = "ollama"
    GROQ = "groq"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class LLMSettings(BaseModel):
    """Validated model and credential settings shared by all agents."""

    model_config = ConfigDict(frozen=True)

    provider: LLMProvider = LLMProvider.OLLAMA
    model_name: str = Field(default="llama3.1:8b", min_length=1)
    api_key: SecretStr | None = None
    base_url: str | None = None

    @classmethod
    def from_env(cls) -> "LLMSettings":
        """Load provider-neutral settings and provider-specific API keys from `.env`."""
        load_dotenv()
        provider = LLMProvider(environ.get("LLM_PROVIDER", "ollama").lower())
        legacy_prefix = "OLLAMA_" if provider is LLMProvider.OLLAMA else ""
        api_key = environ.get("LLM_API_KEY") or environ.get(f"{provider.value.upper()}_API_KEY")
        if provider is LLMProvider.OLLAMA and api_key is None:
            api_key = "ollama"
        base_url = environ.get("LLM_BASE_URL")
        if base_url is None and legacy_prefix:
            base_url = environ.get("OLLAMA_BASE_URL")
        model_name = environ.get("LLM_MODEL") or environ.get(f"{provider.value.upper()}_MODEL")
        if model_name is None and legacy_prefix:
            model_name = environ.get("OLLAMA_MODEL")
        defaults = {
            LLMProvider.OLLAMA: "llama3.1:8b",
            LLMProvider.GROQ: "llama-3.1-8b-instant",
            LLMProvider.GEMINI: "gemini-2.0-flash",
            LLMProvider.ANTHROPIC: "claude-3-5-haiku-latest",
            LLMProvider.OPENAI: "gpt-4o-mini",
        }
        return cls(
            provider=provider,
            model_name=model_name or defaults[provider],
            api_key=api_key,
            base_url=base_url,
        )
