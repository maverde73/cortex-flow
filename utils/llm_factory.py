"""
LLM Factory

Intelligent LLM selection and creation with multi-level configuration support.

Priority order for model selection:
1. {AGENT}_{TASK}_MODEL (e.g., RESEARCHER_DEEP_ANALYSIS_MODEL)
2. {AGENT}_MODEL (e.g., RESEARCHER_MODEL)
3. DEFAULT_MODEL
4. Fallback using PROVIDER_FALLBACK_ORDER

Format: provider/model (e.g., "openai/gpt-4o", "anthropic/claude-sonnet-4")

FASE 2: Now also supports ReAct strategy configuration.
Returns tuple: (LLM, ReactConfig) for integrated reasoning control.
"""

import logging
import os
from typing import Optional, Dict, Tuple
from langchain_core.language_models import BaseChatModel

from utils.model_registry import get_registry
from utils.provider_config import create_llm_for_provider
from utils.react_strategies import ReactConfig, get_strategy_for_agent

logger = logging.getLogger(__name__)


# Cache for LLM instances to avoid recreating them
_llm_cache: Dict[str, BaseChatModel] = {}


def get_llm(
    agent: Optional[str] = None,
    task: Optional[str] = None,
    temperature: Optional[float] = None,
    use_cache: bool = True,
    react_strategy: Optional[str] = None,
    **kwargs
) -> Tuple[BaseChatModel, ReactConfig]:
    """
    Get an LLM instance with intelligent model selection and ReAct strategy.

    Selection priority for MODEL:
    1. {AGENT}_{TASK}_MODEL env var (e.g., RESEARCHER_DEEP_ANALYSIS_MODEL)
    2. {AGENT}_MODEL env var (e.g., RESEARCHER_MODEL)
    3. DEFAULT_MODEL env var
    4. Fallback chain using PROVIDER_FALLBACK_ORDER

    Selection priority for STRATEGY:
    1. react_strategy parameter (explicit override)
    2. {AGENT}_{TASK}_REACT_STRATEGY env var
    3. {AGENT}_REACT_STRATEGY env var
    4. "balanced" default

    Args:
        agent: Agent name (e.g., "researcher", "analyst", "writer", "supervisor")
        task: Optional task name for task-specific model selection
        temperature: Temperature override (if None, uses strategy default)
        use_cache: Whether to use cached LLM instances (default: True)
        react_strategy: Explicit strategy override ("fast", "balanced", "deep", "creative")
        **kwargs: Additional arguments passed to the LLM constructor

    Returns:
        Tuple of (LLM instance, ReactConfig) configured for the agent/task

    Raises:
        ValueError: If no valid model configuration is found
        ImportError: If required provider package is not installed

    Examples:
        >>> # Use agent-specific model and strategy
        >>> llm, config = get_llm(agent="researcher")
        >>> # Returns researcher model + deep strategy

        >>> # Override strategy
        >>> llm, config = get_llm(agent="researcher", react_strategy="fast")
        >>> # Returns researcher model + fast strategy

        >>> # Task-specific configuration
        >>> llm, config = get_llm(agent="researcher", task="deep_analysis")
        >>> # Uses task-specific model and strategy if configured
    """
    from config_legacy import settings

    # FASE 2: Get ReAct strategy configuration
    if react_strategy:
        # Explicit override provided
        react_config = ReactConfig.from_string(react_strategy)
        logger.info(f"Using explicit ReAct strategy: {react_strategy}")
    else:
        # Load from configuration (agent/task specific)
        react_config = get_strategy_for_agent(
            agent_name=agent if agent else "default",
            task_name=task
        )

    # Determine temperature
    # Priority: explicit parameter > strategy default > settings default
    if temperature is None:
        temperature = react_config.temperature
        logger.debug(f"Using temperature from strategy: {temperature}")

    # Step 1: Try {AGENT}_{TASK}_MODEL
    model_string = None
    if agent and task:
        env_var = f"{agent.upper()}_{task.upper()}_MODEL"
        model_string = os.getenv(env_var)
        if model_string:
            logger.info(f"Using task-specific model from {env_var}: {model_string}")

    # Step 2: Try {AGENT}_MODEL
    if not model_string and agent:
        env_var = f"{agent.upper()}_MODEL"
        model_string = os.getenv(env_var)
        if model_string:
            logger.info(f"Using agent-specific model from {env_var}: {model_string}")

    # Step 3: Try DEFAULT_MODEL
    if not model_string:
        model_string = settings.default_model
        if model_string:
            logger.info(f"Using default model: {model_string}")

    # Step 4: Fallback chain
    if not model_string:
        model_string = _get_fallback_model()
        if model_string:
            logger.warning(f"Using fallback model: {model_string}")

    # If still no model, raise error
    if not model_string:
        raise ValueError(
            "No LLM model configured. Please set DEFAULT_MODEL or provider-specific models in .env"
        )

    # Check cache if enabled
    cache_key = f"{model_string}:{temperature}"
    if use_cache and cache_key in _llm_cache:
        logger.debug(f"Returning cached LLM for {cache_key}")
        return _llm_cache[cache_key], react_config

    # Parse and create LLM
    try:
        llm = _create_llm_from_string(model_string, temperature, **kwargs)

        # Cache the instance
        if use_cache:
            _llm_cache[cache_key] = llm

        logger.info(f"Created LLM with {react_config}")
        return llm, react_config

    except Exception as e:
        logger.error(f"Failed to create LLM for {model_string}: {e}")

        # Try fallback if not already using it
        if model_string != _get_fallback_model():
            logger.warning("Attempting fallback model...")
            fallback_model = _get_fallback_model()
            if fallback_model:
                llm = _create_llm_from_string(fallback_model, temperature, **kwargs)
                return llm, react_config

        raise


def _create_llm_from_string(
    model_string: str,
    temperature: float,
    **kwargs
) -> BaseChatModel:
    """
    Create an LLM instance from a model string.

    Args:
        model_string: Model in format "provider/model" or just "model"
        temperature: Temperature for generation
        **kwargs: Additional arguments

    Returns:
        LLM instance

    Raises:
        ValueError: If model string is invalid
        ImportError: If required package is not installed
    """
    from config_legacy import settings

    # Get registry
    registry = get_registry()

    # Parse the model string
    try:
        provider, model_id = registry.parse_model_string(model_string)
    except ValueError as e:
        logger.error(f"Invalid model string: {model_string} - {e}")
        raise

    # Get API key for provider
    api_key = _get_api_key_for_provider(provider)
    if not api_key:
        raise ValueError(
            f"No API key configured for provider: {provider}. "
            f"Please set {provider.upper()}_API_KEY in .env"
        )

    # Get model info for validation
    model_info = registry.get_model(model_id)
    if model_info and not model_info.supports_tools and "tools" in kwargs:
        logger.warning(
            f"Model {model_id} does not support tools. "
            f"Tool calling may fail or be ignored."
        )

    # Create LLM using provider factory
    logger.info(f"Creating {provider} LLM: {model_id} (temp={temperature})")

    return create_llm_for_provider(
        provider=provider,
        model=model_id,
        temperature=temperature,
        api_key=api_key,
        **kwargs
    )


def _get_api_key_for_provider(provider: str) -> Optional[str]:
    """
    Get API key for a specific provider from settings.

    Args:
        provider: Provider name

    Returns:
        API key if configured, None otherwise
    """
    from config_legacy import settings

    key_mapping = {
        "openai": settings.openai_api_key,
        "anthropic": settings.anthropic_api_key,
        "google": settings.google_api_key,
        "groq": settings.groq_api_key,
        "openrouter": settings.openrouter_api_key,
    }

    return key_mapping.get(provider)


def _get_fallback_model() -> Optional[str]:
    """
    Get fallback model based on provider availability.

    Tries providers in order specified by PROVIDER_FALLBACK_ORDER,
    or uses default order if not specified.

    Returns:
        Model string if a provider is available, None otherwise
    """
    from config_legacy import settings

    # Get fallback order from settings
    fallback_order_str = getattr(settings, "provider_fallback_order", None)

    if fallback_order_str:
        fallback_order = [p.strip() for p in fallback_order_str.split(",")]
    else:
        # Default fallback order
        fallback_order = ["openai", "anthropic", "google", "groq", "openrouter"]

    # Default models for each provider
    default_models = {
        "openai": "openai/gpt-4o-mini",
        "anthropic": "anthropic/claude-3-5-sonnet-20241022",
        "google": "google/gemini-1.5-flash",
        "groq": "groq/llama-3.3-70b-versatile",
        "openrouter": "openrouter/anthropic/claude-3.5-sonnet",
    }

    # Try each provider in fallback order
    for provider in fallback_order:
        api_key = _get_api_key_for_provider(provider)
        if api_key:
            logger.info(f"Found API key for fallback provider: {provider}")
            return default_models.get(provider)

    logger.error("No API keys found for any provider")
    return None


def clear_llm_cache():
    """
    Clear the LLM instance cache.

    Useful when you want to force recreation of LLM instances,
    for example after changing configuration.
    """
    global _llm_cache
    _llm_cache.clear()
    logger.info("LLM cache cleared")


def list_available_providers() -> Dict[str, bool]:
    """
    Check which providers have API keys configured.

    Returns:
        Dictionary mapping provider names to availability (True/False)
    """
    providers = ["openai", "anthropic", "google", "groq", "openrouter"]

    return {
        provider: _get_api_key_for_provider(provider) is not None
        for provider in providers
    }


def validate_model_config(agent: Optional[str] = None, task: Optional[str] = None) -> bool:
    """
    Validate that model configuration is valid for an agent/task.

    Args:
        agent: Agent name
        task: Optional task name

    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        # Try to get LLM (without creating it)
        # This will validate the configuration
        from config_legacy import settings

        model_string = None

        # Check task-specific
        if agent and task:
            env_var = f"{agent.upper()}_{task.upper()}_MODEL"
            model_string = os.getenv(env_var)

        # Check agent-specific
        if not model_string and agent:
            env_var = f"{agent.upper()}_MODEL"
            model_string = os.getenv(env_var)

        # Check default
        if not model_string:
            model_string = settings.default_model

        # Check fallback
        if not model_string:
            model_string = _get_fallback_model()

        if not model_string:
            return False

        # Validate format
        registry = get_registry()
        provider, model_id = registry.parse_model_string(model_string)

        # Check API key exists
        api_key = _get_api_key_for_provider(provider)

        return api_key is not None

    except Exception as e:
        logger.error(f"Model config validation failed: {e}")
        return False
