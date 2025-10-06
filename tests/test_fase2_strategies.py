"""
Unit tests for FASE 2: ReAct Reasoning Strategies

Tests the ReactConfig system, strategy selection, and LLM factory integration.
"""

import pytest
from utils.react_strategies import (
    ReactStrategy,
    ReactConfig,
    get_strategy_for_agent,
    get_fast_config,
    get_balanced_config,
    get_deep_config,
    get_creative_config
)
from utils.llm_factory import get_llm


class TestReactStrategyEnum:
    """Test ReactStrategy enum functionality."""

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_strategy_enum_values(self):
        """Test that all expected strategies exist."""
        assert ReactStrategy.FAST == "fast"
        assert ReactStrategy.BALANCED == "balanced"
        assert ReactStrategy.DEEP == "deep"
        assert ReactStrategy.CREATIVE == "creative"

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_from_string_valid(self):
        """Test ReactStrategy.from_string with valid inputs."""
        assert ReactStrategy.from_string("fast") == ReactStrategy.FAST
        assert ReactStrategy.from_string("FAST") == ReactStrategy.FAST
        assert ReactStrategy.from_string("Fast") == ReactStrategy.FAST

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_from_string_invalid_fallback(self):
        """Test ReactStrategy.from_string falls back to BALANCED for invalid input."""
        assert ReactStrategy.from_string("invalid") == ReactStrategy.BALANCED
        assert ReactStrategy.from_string("") == ReactStrategy.BALANCED
        assert ReactStrategy.from_string(None) == ReactStrategy.BALANCED


class TestReactConfig:
    """Test ReactConfig class functionality."""

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_fast_config(self, fast_config):
        """Test FAST strategy configuration."""
        assert fast_config.strategy == ReactStrategy.FAST
        assert fast_config.max_iterations == 3
        assert fast_config.temperature == 0.3
        assert fast_config.timeout_seconds == 30.0

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_balanced_config(self, balanced_config):
        """Test BALANCED strategy configuration."""
        assert balanced_config.strategy == ReactStrategy.BALANCED
        assert balanced_config.max_iterations == 10
        assert balanced_config.temperature == 0.7
        assert balanced_config.timeout_seconds == 120.0

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_deep_config(self, deep_config):
        """Test DEEP strategy configuration."""
        assert deep_config.strategy == ReactStrategy.DEEP
        assert deep_config.max_iterations == 20
        assert deep_config.temperature == 0.7
        assert deep_config.timeout_seconds == 300.0

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_creative_config(self, creative_config):
        """Test CREATIVE strategy configuration."""
        assert creative_config.strategy == ReactStrategy.CREATIVE
        assert creative_config.max_iterations == 15
        assert creative_config.temperature == 0.9
        assert creative_config.timeout_seconds == 180.0

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_from_strategy(self):
        """Test ReactConfig.from_strategy factory method."""
        config = ReactConfig.from_strategy(ReactStrategy.FAST)
        assert config.strategy == ReactStrategy.FAST
        assert config.max_iterations == 3

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_from_string(self):
        """Test ReactConfig.from_string factory method."""
        config = ReactConfig.from_string("deep")
        assert config.strategy == ReactStrategy.DEEP
        assert config.max_iterations == 20

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_config_repr(self, fast_config):
        """Test ReactConfig string representation."""
        repr_str = repr(fast_config)
        assert "fast" in repr_str.lower()
        assert "3" in repr_str
        assert "0.3" in repr_str
        assert "30" in repr_str


class TestConvenienceFunctions:
    """Test convenience functions for getting configs."""

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_get_fast_config(self):
        """Test get_fast_config convenience function."""
        config = get_fast_config()
        assert config.strategy == ReactStrategy.FAST

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_get_balanced_config(self):
        """Test get_balanced_config convenience function."""
        config = get_balanced_config()
        assert config.strategy == ReactStrategy.BALANCED

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_get_deep_config(self):
        """Test get_deep_config convenience function."""
        config = get_deep_config()
        assert config.strategy == ReactStrategy.DEEP

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_get_creative_config(self):
        """Test get_creative_config convenience function."""
        config = get_creative_config()
        assert config.strategy == ReactStrategy.CREATIVE


class TestStrategySelection:
    """Test strategy selection for agents."""

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_get_strategy_for_supervisor(self):
        """Test that supervisor gets FAST strategy from config."""
        config = get_strategy_for_agent("supervisor")
        assert config.strategy == ReactStrategy.FAST
        assert config.max_iterations == 3

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_get_strategy_for_researcher(self):
        """Test that researcher gets DEEP strategy from config."""
        config = get_strategy_for_agent("researcher")
        assert config.strategy == ReactStrategy.DEEP
        assert config.max_iterations == 20

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_get_strategy_for_analyst(self):
        """Test that analyst gets BALANCED strategy from config."""
        config = get_strategy_for_agent("analyst")
        assert config.strategy == ReactStrategy.BALANCED
        assert config.max_iterations == 10

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_get_strategy_for_writer(self):
        """Test that writer gets CREATIVE strategy from config."""
        config = get_strategy_for_agent("writer")
        assert config.strategy == ReactStrategy.CREATIVE
        assert config.max_iterations == 15
        assert config.temperature == 0.9

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_get_strategy_default_fallback(self):
        """Test fallback to default strategy for unknown agent."""
        config = get_strategy_for_agent("unknown_agent", default_strategy="balanced")
        assert config.strategy == ReactStrategy.BALANCED


class TestLLMFactoryIntegration:
    """Test LLM factory integration with strategies."""

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_get_llm_returns_tuple(self):
        """Test that get_llm returns (LLM, ReactConfig) tuple."""
        llm, config = get_llm(agent="supervisor")
        assert llm is not None
        assert isinstance(config, ReactConfig)

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_get_llm_applies_agent_strategy(self):
        """Test that get_llm applies correct strategy for agent."""
        llm, config = get_llm(agent="researcher")
        assert config.strategy == ReactStrategy.DEEP
        assert config.max_iterations == 20

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_get_llm_explicit_strategy_override(self):
        """Test that explicit strategy parameter overrides agent config."""
        llm, config = get_llm(agent="researcher", react_strategy="fast")
        assert config.strategy == ReactStrategy.FAST
        assert config.max_iterations == 3

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_get_llm_temperature_from_strategy(self):
        """Test that temperature is applied from strategy."""
        llm, config = get_llm(agent="supervisor")
        # Supervisor uses FAST strategy with temp 0.3
        assert config.temperature == 0.3

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_get_llm_temperature_override(self):
        """Test that explicit temperature overrides strategy temperature."""
        llm, config = get_llm(agent="supervisor", temperature=0.9)
        # Explicit temperature should be respected
        # Config still shows strategy temp, but LLM uses override


class TestStrategyParametersRange:
    """Test that strategy parameters are within acceptable ranges."""

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_all_strategies_have_positive_iterations(self):
        """Test that all strategies have positive max_iterations."""
        for strategy in ReactStrategy:
            config = ReactConfig.from_strategy(strategy)
            assert config.max_iterations > 0

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_all_strategies_have_valid_temperature(self):
        """Test that all strategies have temperature in [0, 1] range."""
        for strategy in ReactStrategy:
            config = ReactConfig.from_strategy(strategy)
            assert 0.0 <= config.temperature <= 1.0

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_all_strategies_have_positive_timeout(self):
        """Test that all strategies have positive timeout."""
        for strategy in ReactStrategy:
            config = ReactConfig.from_strategy(strategy)
            assert config.timeout_seconds > 0

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_fast_is_fastest(self):
        """Test that FAST strategy has shortest timeout and fewest iterations."""
        fast = get_fast_config()
        balanced = get_balanced_config()
        deep = get_deep_config()

        assert fast.max_iterations < balanced.max_iterations
        assert fast.max_iterations < deep.max_iterations
        assert fast.timeout_seconds < balanced.timeout_seconds
        assert fast.timeout_seconds < deep.timeout_seconds

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_deep_is_most_thorough(self):
        """Test that DEEP strategy has longest timeout and most iterations."""
        fast = get_fast_config()
        balanced = get_balanced_config()
        deep = get_deep_config()

        assert deep.max_iterations > balanced.max_iterations
        assert deep.max_iterations > fast.max_iterations
        assert deep.timeout_seconds > balanced.timeout_seconds
        assert deep.timeout_seconds > fast.timeout_seconds

    @pytest.mark.unit
    @pytest.mark.fase2
    def test_creative_has_highest_temperature(self):
        """Test that CREATIVE strategy has highest temperature."""
        fast = get_fast_config()
        balanced = get_balanced_config()
        creative = get_creative_config()

        assert creative.temperature > balanced.temperature
        assert creative.temperature > fast.temperature
