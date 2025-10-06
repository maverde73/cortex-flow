"""
Provider Configuration

Provider-specific LLM configurations and factory functions.
Handles initialization of different LLM providers (OpenAI, Anthropic, Google, Groq, OpenRouter).
"""

import logging
from typing import Optional
from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


def create_openai_llm(
    model: str,
    temperature: float = 0.7,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseChatModel:
    """
    Create an OpenAI LLM instance.

    Args:
        model: Model ID (e.g., "gpt-4o", "gpt-4o-mini")
        temperature: Temperature for generation
        api_key: Optional API key (will use env var if not provided)
        **kwargs: Additional arguments passed to ChatOpenAI

    Returns:
        ChatOpenAI instance
    """
    from langchain_openai import ChatOpenAI

    logger.debug(f"Creating OpenAI LLM: {model}")

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        **kwargs
    )


def create_anthropic_llm(
    model: str,
    temperature: float = 0.7,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseChatModel:
    """
    Create an Anthropic LLM instance.

    Args:
        model: Model ID (e.g., "claude-sonnet-4-20250514")
        temperature: Temperature for generation
        api_key: Optional API key (will use env var if not provided)
        **kwargs: Additional arguments passed to ChatAnthropic

    Returns:
        ChatAnthropic instance
    """
    from langchain_anthropic import ChatAnthropic

    logger.debug(f"Creating Anthropic LLM: {model}")

    return ChatAnthropic(
        model=model,
        temperature=temperature,
        api_key=api_key,
        **kwargs
    )


def create_google_llm(
    model: str,
    temperature: float = 0.7,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseChatModel:
    """
    Create a Google LLM instance.

    Args:
        model: Model ID (e.g., "gemini-1.5-pro", "gemini-2.0-flash-exp")
        temperature: Temperature for generation
        api_key: Optional API key (will use env var if not provided)
        **kwargs: Additional arguments passed to ChatGoogleGenerativeAI

    Returns:
        ChatGoogleGenerativeAI instance
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise ImportError(
            "langchain-google-genai is not installed. "
            "Install it with: pip install langchain-google-genai"
        )

    logger.debug(f"Creating Google LLM: {model}")

    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=api_key,
        **kwargs
    )


def create_groq_llm(
    model: str,
    temperature: float = 0.7,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseChatModel:
    """
    Create a Groq LLM instance.

    Args:
        model: Model ID (e.g., "llama-3.3-70b-versatile")
        temperature: Temperature for generation
        api_key: Optional API key (will use env var if not provided)
        **kwargs: Additional arguments passed to ChatGroq

    Returns:
        ChatGroq instance
    """
    try:
        from langchain_groq import ChatGroq
    except ImportError:
        raise ImportError(
            "langchain-groq is not installed. "
            "Install it with: pip install langchain-groq"
        )

    logger.debug(f"Creating Groq LLM: {model}")

    return ChatGroq(
        model=model,
        temperature=temperature,
        api_key=api_key,
        **kwargs
    )


def create_openrouter_llm(
    model: str,
    temperature: float = 0.7,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseChatModel:
    """
    Create an OpenRouter LLM instance.

    OpenRouter uses the OpenAI-compatible API, so we use ChatOpenAI
    with a custom base_url.

    Args:
        model: Model ID in OpenRouter format (e.g., "anthropic/claude-sonnet-4")
        temperature: Temperature for generation
        api_key: Optional API key (will use env var if not provided)
        **kwargs: Additional arguments passed to ChatOpenAI

    Returns:
        ChatOpenAI instance configured for OpenRouter
    """
    from langchain_openai import ChatOpenAI

    logger.debug(f"Creating OpenRouter LLM: {model}")

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/cortex-flow",  # Optional
            "X-Title": "Cortex Flow",  # Optional
        },
        **kwargs
    )


def get_provider_factory(provider: str):
    """
    Get the factory function for a specific provider.

    Args:
        provider: Provider name ("openai", "anthropic", "google", "groq", "openrouter")

    Returns:
        Factory function for creating LLM instances

    Raises:
        ValueError: If provider is not supported
    """
    factories = {
        "openai": create_openai_llm,
        "anthropic": create_anthropic_llm,
        "google": create_google_llm,
        "groq": create_groq_llm,
        "openrouter": create_openrouter_llm,
    }

    if provider not in factories:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported providers: {', '.join(factories.keys())}"
        )

    return factories[provider]


def create_llm_for_provider(
    provider: str,
    model: str,
    temperature: float = 0.7,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseChatModel:
    """
    Create an LLM instance for a specific provider.

    Args:
        provider: Provider name
        model: Model ID
        temperature: Temperature for generation
        api_key: Optional API key
        **kwargs: Additional arguments

    Returns:
        LLM instance

    Raises:
        ValueError: If provider is not supported
        ImportError: If required package is not installed
    """
    factory = get_provider_factory(provider)
    return factory(model, temperature, api_key, **kwargs)
