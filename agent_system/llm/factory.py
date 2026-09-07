"""Construct PydanticAI models for supported LLM providers."""

from __future__ import annotations

from .config import LLMProvider, LLMSettings


class LLMConfigurationError(ValueError):
    """Raised when provider settings are incomplete or unsupported."""


class LLMProviderUnavailableError(RuntimeError):
    """Raised when a provider's optional PydanticAI integration is unavailable."""


def create_model(settings: LLMSettings | None = None) -> object:
    """Create a PydanticAI model without making a network request.

    Ollama and OpenAI use the OpenAI-compatible chat model. Groq, Gemini, and
    Anthropic use their native PydanticAI providers so authentication and tool
    semantics remain provider-correct.
    """
    configuration = settings or LLMSettings.from_env()
    if configuration.provider is LLMProvider.OLLAMA:
        return _create_ollama(configuration)
    if configuration.provider is LLMProvider.GROQ:
        return _create_groq(configuration)
    if configuration.provider is LLMProvider.GEMINI:
        return _create_gemini(configuration)
    if configuration.provider is LLMProvider.ANTHROPIC:
        return _create_anthropic(configuration)
    if configuration.provider is LLMProvider.OPENAI:
        return _create_openai(configuration)
    raise LLMConfigurationError(f"Unsupported LLM provider: {configuration.provider}")


def _require_api_key(settings: LLMSettings) -> str:
    """Return an API key or explain why a hosted provider cannot be built."""
    if settings.api_key is None:
        raise LLMConfigurationError(f"LLM_API_KEY is required for {settings.provider.value}")
    return settings.api_key.get_secret_value()


def _create_ollama(settings: LLMSettings) -> object:
    """Create an Ollama model through its OpenAI-compatible endpoint."""
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    base_url = (settings.base_url or "http://localhost:11434").rstrip("/")
    if not base_url.endswith("/v1"):
        base_url += "/v1"
    return OpenAIChatModel(
        settings.model_name,
        provider=OpenAIProvider(
            base_url=base_url,
            api_key=settings.api_key.get_secret_value() if settings.api_key else "ollama",
        ),
    )


def _create_groq(settings: LLMSettings) -> object:
    """Create a model using PydanticAI's native Groq provider."""
    try:
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.groq import GroqProvider
    except ImportError as error:
        raise LLMProviderUnavailableError("Install PydanticAI's groq integration") from error
    return OpenAIChatModel(settings.model_name, provider=GroqProvider(api_key=_require_api_key(settings)))


def _create_gemini(settings: LLMSettings) -> object:
    """Create a model using PydanticAI's native Gemini provider."""
    try:
        from pydantic_ai.models.google import GoogleModel
        from pydantic_ai.providers.google import GoogleProvider
    except ImportError as error:
        raise LLMProviderUnavailableError("Install PydanticAI's google integration") from error
    return GoogleModel(settings.model_name, provider=GoogleProvider(api_key=_require_api_key(settings)))


def _create_anthropic(settings: LLMSettings) -> object:
    """Create a model using PydanticAI's native Anthropic provider."""
    try:
        from pydantic_ai.models.anthropic import AnthropicModel
        from pydantic_ai.providers.anthropic import AnthropicProvider
    except ImportError as error:
        raise LLMProviderUnavailableError("Install a compatible PydanticAI Anthropic integration") from error
    return AnthropicModel(settings.model_name, provider=AnthropicProvider(api_key=_require_api_key(settings)))


def _create_openai(settings: LLMSettings) -> object:
    """Create a model using the OpenAI-compatible provider."""
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    kwargs = {"api_key": _require_api_key(settings)}
    if settings.base_url:
        kwargs["base_url"] = settings.base_url
    return OpenAIChatModel(settings.model_name, provider=OpenAIProvider(**kwargs))
