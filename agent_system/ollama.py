"""Ollama model configuration and PydanticAI model construction."""

from __future__ import annotations

from os import environ

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr


class OllamaSettings(BaseModel):
    """Validated connection settings for a local Ollama server."""

    model_config = ConfigDict(frozen=True)

    base_url: str = Field(default="http://localhost:11434", min_length=1)
    model_name: str = Field(default="llama3.1:8b", min_length=1)
    api_key: SecretStr = SecretStr("ollama")

    @classmethod
    def from_env(cls) -> "OllamaSettings":
        """Load Ollama settings from `.env` and process environment variables."""
        load_dotenv()
        return cls(
            base_url=environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            model_name=environ.get("OLLAMA_MODEL", "llama3.1:8b"),
            api_key=environ.get("OLLAMA_API_KEY", "ollama"),
        )


def create_ollama_model(settings: OllamaSettings | None = None) -> object:
    """Create a PydanticAI OpenAI model configured for Ollama's local API.

    PydanticAI does not need an Ollama-specific model class because Ollama
    exposes an OpenAI-compatible endpoint. Importing this function is safe;
    network access starts only when an agent executes a model run.
    """
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    configuration = settings or OllamaSettings.from_env()
    base_url = configuration.base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url += "/v1"
    provider = OpenAIProvider(
        base_url=base_url,
        api_key=configuration.api_key.get_secret_value(),
    )
    return OpenAIChatModel(configuration.model_name, provider=provider)
