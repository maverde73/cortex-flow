"""
Model Registry

Central registry of supported LLM models with metadata.
Provides validation and information about available models per provider.
"""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass


ProviderType = Literal["openai", "anthropic", "google", "groq", "openrouter"]


@dataclass
class ModelInfo:
    """Information about a specific LLM model."""

    provider: ProviderType
    model_id: str
    display_name: str
    context_window: int
    supports_tools: bool = True
    supports_streaming: bool = True
    cost_tier: Literal["free", "low", "medium", "high", "premium"] = "medium"
    recommended_for: List[str] = None

    def __post_init__(self):
        if self.recommended_for is None:
            self.recommended_for = []

    @property
    def full_name(self) -> str:
        """Returns provider/model format."""
        return f"{self.provider}/{self.model_id}"


# ============================================================================
# OpenAI Models
# ============================================================================

OPENAI_MODELS = {
    "gpt-4o": ModelInfo(
        provider="openai",
        model_id="gpt-4o",
        display_name="GPT-4o (Omni)",
        context_window=128000,
        cost_tier="high",
        recommended_for=["general", "reasoning", "analysis", "coding"]
    ),
    "gpt-4o-mini": ModelInfo(
        provider="openai",
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        context_window=128000,
        cost_tier="low",
        recommended_for=["general", "fast", "economical"]
    ),
    "gpt-4-turbo": ModelInfo(
        provider="openai",
        model_id="gpt-4-turbo",
        display_name="GPT-4 Turbo",
        context_window=128000,
        cost_tier="high",
        recommended_for=["general", "analysis", "writing"]
    ),
    "o1": ModelInfo(
        provider="openai",
        model_id="o1",
        display_name="O1",
        context_window=200000,
        supports_tools=False,  # O1 doesn't support tools yet
        cost_tier="premium",
        recommended_for=["reasoning", "complex_analysis", "research"]
    ),
    "o1-mini": ModelInfo(
        provider="openai",
        model_id="o1-mini",
        display_name="O1 Mini",
        context_window=128000,
        supports_tools=False,
        cost_tier="high",
        recommended_for=["reasoning", "fast"]
    ),
    "o3-mini": ModelInfo(
        provider="openai",
        model_id="o3-mini",
        display_name="O3 Mini",
        context_window=128000,
        supports_tools=False,
        cost_tier="high",
        recommended_for=["reasoning", "fast"]
    ),
}


# ============================================================================
# Anthropic Models
# ============================================================================

ANTHROPIC_MODELS = {
    "claude-opus-4": ModelInfo(
        provider="anthropic",
        model_id="claude-opus-4-20250514",
        display_name="Claude Opus 4",
        context_window=200000,
        cost_tier="premium",
        recommended_for=["writing", "creative", "complex_reasoning", "research"]
    ),
    "claude-opus-4-20250514": ModelInfo(
        provider="anthropic",
        model_id="claude-opus-4-20250514",
        display_name="Claude Opus 4",
        context_window=200000,
        cost_tier="premium",
        recommended_for=["writing", "creative", "complex_reasoning", "research"]
    ),
    "claude-sonnet-4": ModelInfo(
        provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4",
        context_window=200000,
        cost_tier="high",
        recommended_for=["general", "reasoning", "analysis", "coding"]
    ),
    "claude-sonnet-4-20250514": ModelInfo(
        provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4",
        context_window=200000,
        cost_tier="high",
        recommended_for=["general", "reasoning", "analysis", "coding"]
    ),
    "claude-3-5-sonnet-20241022": ModelInfo(
        provider="anthropic",
        model_id="claude-3-5-sonnet-20241022",
        display_name="Claude 3.5 Sonnet",
        context_window=200000,
        cost_tier="medium",
        recommended_for=["general", "fast", "reasoning"]
    ),
    "claude-3-5-haiku-20241022": ModelInfo(
        provider="anthropic",
        model_id="claude-3-5-haiku-20241022",
        display_name="Claude 3.5 Haiku",
        context_window=200000,
        cost_tier="low",
        recommended_for=["fast", "economical"]
    ),
}


# ============================================================================
# Google Models
# ============================================================================

GOOGLE_MODELS = {
    "gemini-2.0-flash-exp": ModelInfo(
        provider="google",
        model_id="gemini-2.0-flash-exp",
        display_name="Gemini 2.0 Flash (Experimental)",
        context_window=1000000,
        cost_tier="low",
        recommended_for=["fast", "long_context"]
    ),
    "gemini-1.5-pro": ModelInfo(
        provider="google",
        model_id="gemini-1.5-pro",
        display_name="Gemini 1.5 Pro",
        context_window=2000000,
        cost_tier="medium",
        recommended_for=["long_context", "analysis", "research"]
    ),
    "gemini-1.5-flash": ModelInfo(
        provider="google",
        model_id="gemini-1.5-flash",
        display_name="Gemini 1.5 Flash",
        context_window=1000000,
        cost_tier="low",
        recommended_for=["fast", "economical", "long_context"]
    ),
}


# ============================================================================
# Groq Models (Fast inference)
# ============================================================================

GROQ_MODELS = {
    "llama-3.3-70b-versatile": ModelInfo(
        provider="groq",
        model_id="llama-3.3-70b-versatile",
        display_name="Llama 3.3 70B",
        context_window=128000,
        cost_tier="low",
        recommended_for=["fast", "general"]
    ),
    "mixtral-8x7b-32768": ModelInfo(
        provider="groq",
        model_id="mixtral-8x7b-32768",
        display_name="Mixtral 8x7B",
        context_window=32768,
        cost_tier="low",
        recommended_for=["fast", "economical"]
    ),
}


# ============================================================================
# OpenRouter Models (Meta-provider - access to all models)
# ============================================================================

OPENROUTER_MODELS = {
    # OpenAI via OpenRouter
    "openai/gpt-4o": ModelInfo(
        provider="openrouter",
        model_id="openai/gpt-4o",
        display_name="GPT-4o (via OpenRouter)",
        context_window=128000,
        cost_tier="high",
        recommended_for=["general", "reasoning"]
    ),
    "openai/o1": ModelInfo(
        provider="openrouter",
        model_id="openai/o1",
        display_name="O1 (via OpenRouter)",
        context_window=200000,
        supports_tools=False,
        cost_tier="premium",
        recommended_for=["reasoning", "complex_analysis"]
    ),

    # Anthropic via OpenRouter
    "anthropic/claude-opus-4": ModelInfo(
        provider="openrouter",
        model_id="anthropic/claude-opus-4",
        display_name="Claude Opus 4 (via OpenRouter)",
        context_window=200000,
        cost_tier="premium",
        recommended_for=["writing", "creative"]
    ),
    "anthropic/claude-sonnet-4": ModelInfo(
        provider="openrouter",
        model_id="anthropic/claude-sonnet-4",
        display_name="Claude Sonnet 4 (via OpenRouter)",
        context_window=200000,
        cost_tier="high",
        recommended_for=["general", "reasoning"]
    ),
    "anthropic/claude-3.5-sonnet": ModelInfo(
        provider="openrouter",
        model_id="anthropic/claude-3.5-sonnet",
        display_name="Claude 3.5 Sonnet (via OpenRouter)",
        context_window=200000,
        cost_tier="medium",
        recommended_for=["general", "fast"]
    ),

    # Google via OpenRouter
    "google/gemini-2.0-flash-exp": ModelInfo(
        provider="openrouter",
        model_id="google/gemini-2.0-flash-exp",
        display_name="Gemini 2.0 Flash (via OpenRouter)",
        context_window=1000000,
        cost_tier="low",
        recommended_for=["fast", "long_context"]
    ),

    # Meta Llama via OpenRouter
    "meta-llama/llama-3.3-70b-instruct": ModelInfo(
        provider="openrouter",
        model_id="meta-llama/llama-3.3-70b-instruct",
        display_name="Llama 3.3 70B (via OpenRouter)",
        context_window=128000,
        cost_tier="low",
        recommended_for=["fast", "economical"]
    ),

    # DeepSeek via OpenRouter
    "deepseek/deepseek-chat": ModelInfo(
        provider="openrouter",
        model_id="deepseek/deepseek-chat",
        display_name="DeepSeek Chat (via OpenRouter)",
        context_window=64000,
        cost_tier="low",
        recommended_for=["coding", "economical"]
    ),
}


# ============================================================================
# Registry Class
# ============================================================================

class ModelRegistry:
    """Central registry for all supported models."""

    def __init__(self):
        self._models: Dict[str, ModelInfo] = {}
        self._register_all_models()

    def _register_all_models(self):
        """Register all models from all providers."""
        for models_dict in [OPENAI_MODELS, ANTHROPIC_MODELS, GOOGLE_MODELS, GROQ_MODELS, OPENROUTER_MODELS]:
            self._models.update(models_dict)

    def get_model(self, model_identifier: str) -> Optional[ModelInfo]:
        """
        Get model info by identifier.

        Args:
            model_identifier: Can be:
                - Short form: "gpt-4o"
                - Full form: "openai/gpt-4o"

        Returns:
            ModelInfo if found, None otherwise
        """
        # Try exact match first
        if model_identifier in self._models:
            return self._models[model_identifier]

        # Try with provider prefix
        if "/" in model_identifier:
            provider, model_id = model_identifier.split("/", 1)
            # Try direct lookup
            if model_id in self._models:
                return self._models[model_id]

        return None

    def parse_model_string(self, model_string: str) -> tuple[ProviderType, str]:
        """
        Parse a model string in format 'provider/model' or 'model'.

        Args:
            model_string: e.g., "openai/gpt-4o" or "gpt-4o"

        Returns:
            Tuple of (provider, model_id)

        Raises:
            ValueError: If model string is invalid or model not found
        """
        if "/" in model_string:
            parts = model_string.split("/", 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid model string format: {model_string}")

            provider, model_id = parts

            # Validate provider
            if provider not in ["openai", "anthropic", "google", "groq", "openrouter"]:
                raise ValueError(f"Unknown provider: {provider}")

            return provider, model_id
        else:
            # Try to find model in registry and infer provider
            model_info = self.get_model(model_string)
            if model_info:
                return model_info.provider, model_info.model_id

            raise ValueError(f"Model not found in registry: {model_string}")

    def validate_model(self, model_string: str) -> bool:
        """
        Validate that a model string is supported.

        Args:
            model_string: Model identifier

        Returns:
            True if valid, False otherwise
        """
        try:
            self.parse_model_string(model_string)
            return True
        except ValueError:
            return False

    def list_models(self, provider: Optional[ProviderType] = None) -> List[ModelInfo]:
        """
        List all models, optionally filtered by provider.

        Args:
            provider: Optional provider to filter by

        Returns:
            List of ModelInfo objects
        """
        models = list(self._models.values())

        if provider:
            models = [m for m in models if m.provider == provider]

        return models

    def get_recommended_models(self, task: str) -> List[ModelInfo]:
        """
        Get models recommended for a specific task.

        Args:
            task: Task name (e.g., "writing", "reasoning", "fast")

        Returns:
            List of recommended models
        """
        return [
            m for m in self._models.values()
            if task in m.recommended_for
        ]


# Global registry instance
_registry = ModelRegistry()


def get_registry() -> ModelRegistry:
    """Get the global model registry instance."""
    return _registry
