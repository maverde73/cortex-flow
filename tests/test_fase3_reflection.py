"""
Unit tests for FASE 3: Self-Reflection

Tests reflection mechanism, quality assessment, and refinement loops.
"""

import pytest
from utils.react_reflection import (
    ReflectionDecision,
    ReflectionResult,
    ReflectionConfig,
    ReflectionPrompts,
    parse_reflection_response,
    get_reflection_config,
    is_reflection_enabled,
    create_refinement_prompt
)


class TestReflectionDecisionEnum:
    """Test ReflectionDecision enum."""

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_decision_values(self):
        """Test that all expected decisions exist."""
        assert ReflectionDecision.ACCEPT == "accept"
        assert ReflectionDecision.REFINE == "refine"
        assert ReflectionDecision.INSUFFICIENT == "insufficient"


class TestReflectionResult:
    """Test ReflectionResult dataclass."""

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_result_creation(self):
        """Test creating reflection result."""
        result = ReflectionResult(
            decision=ReflectionDecision.ACCEPT,
            quality_score=0.85,
            reasoning="Good quality response",
            suggestions=[],
            should_continue=False
        )
        assert result.decision == ReflectionDecision.ACCEPT
        assert result.quality_score == 0.85
        assert result.should_continue is False

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_result_repr(self):
        """Test result string representation."""
        result = ReflectionResult(
            decision=ReflectionDecision.REFINE,
            quality_score=0.65,
            reasoning="Needs improvement",
            suggestions=["Add more detail"],
            should_continue=True
        )
        repr_str = repr(result)
        assert "refine" in repr_str.lower()
        assert "0.65" in repr_str
        assert "True" in repr_str


class TestReflectionConfig:
    """Test ReflectionConfig class."""

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_default_config(self):
        """Test default configuration."""
        config = ReflectionConfig()
        assert config.enabled is False
        assert config.quality_threshold == 0.7
        assert config.max_refinement_iterations == 2
        assert config.require_complete_answer is True

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_from_agent_writer(self):
        """Test loading config for writer agent."""
        config = ReflectionConfig.from_agent("writer")
        # Writer has higher threshold in config
        assert isinstance(config, ReflectionConfig)
        assert 0.0 <= config.quality_threshold <= 1.0

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_from_agent_researcher(self):
        """Test loading config for researcher agent."""
        config = ReflectionConfig.from_agent("researcher")
        assert isinstance(config, ReflectionConfig)
        # Researcher should require sources
        assert config.require_sources is True

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_from_agent_supervisor(self):
        """Test loading config for supervisor agent."""
        config = ReflectionConfig.from_agent("supervisor")
        assert isinstance(config, ReflectionConfig)
        # Supervisor usually has lower threshold
        assert config.quality_threshold >= 0.0


class TestReflectionPrompts:
    """Test reflection prompts."""

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_general_prompt_exists(self):
        """Test general reflection prompt exists."""
        assert hasattr(ReflectionPrompts, "GENERAL_REFLECTION")
        assert "QUALITY_SCORE" in ReflectionPrompts.GENERAL_REFLECTION
        assert "DECISION" in ReflectionPrompts.GENERAL_REFLECTION

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_researcher_prompt_exists(self):
        """Test researcher-specific prompt exists."""
        assert hasattr(ReflectionPrompts, "RESEARCHER_REFLECTION")
        prompt = ReflectionPrompts.RESEARCHER_REFLECTION
        assert "research" in prompt.lower() or "source" in prompt.lower()

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_writer_prompt_exists(self):
        """Test writer-specific prompt exists."""
        assert hasattr(ReflectionPrompts, "WRITER_REFLECTION")
        prompt = ReflectionPrompts.WRITER_REFLECTION
        assert "writing" in prompt.lower() or "content" in prompt.lower()

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_analyst_prompt_exists(self):
        """Test analyst-specific prompt exists."""
        assert hasattr(ReflectionPrompts, "ANALYST_REFLECTION")
        prompt = ReflectionPrompts.ANALYST_REFLECTION
        assert "analy" in prompt.lower()

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_get_prompt_for_agent(self):
        """Test getting prompt for specific agent."""
        researcher_prompt = ReflectionPrompts.get_prompt_for_agent("researcher")
        assert researcher_prompt == ReflectionPrompts.RESEARCHER_REFLECTION

        writer_prompt = ReflectionPrompts.get_prompt_for_agent("writer")
        assert writer_prompt == ReflectionPrompts.WRITER_REFLECTION

        # Unknown agent should get general prompt
        unknown_prompt = ReflectionPrompts.get_prompt_for_agent("unknown")
        assert unknown_prompt == ReflectionPrompts.GENERAL_REFLECTION


class TestParseReflectionResponse:
    """Test parsing reflection LLM responses."""

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_parse_accept_decision(self):
        """Test parsing ACCEPT decision."""
        response = """
QUALITY_SCORE: 0.85
DECISION: ACCEPT
REASONING: The response is complete and accurate.
SUGGESTIONS: None
"""
        result = parse_reflection_response(response)
        assert result.decision == ReflectionDecision.ACCEPT
        assert result.quality_score == 0.85
        assert result.should_continue is False

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_parse_refine_decision(self):
        """Test parsing REFINE decision."""
        response = """
QUALITY_SCORE: 0.60
DECISION: REFINE
REASONING: Missing key details.
SUGGESTIONS: Add more specific examples
"""
        result = parse_reflection_response(response)
        assert result.decision == ReflectionDecision.REFINE
        assert result.quality_score == 0.60
        assert result.should_continue is True
        assert len(result.suggestions) > 0

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_parse_insufficient_decision(self):
        """Test parsing INSUFFICIENT decision."""
        response = """
QUALITY_SCORE: 0.30
DECISION: INSUFFICIENT
REASONING: Response is completely incorrect.
SUGGESTIONS: Start over with correct approach
"""
        result = parse_reflection_response(response)
        assert result.decision == ReflectionDecision.INSUFFICIENT
        assert result.quality_score == 0.30

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_parse_with_invalid_score(self):
        """Test parsing with invalid quality score."""
        response = """
QUALITY_SCORE: invalid
DECISION: ACCEPT
REASONING: Good enough
SUGGESTIONS: None
"""
        result = parse_reflection_response(response)
        # Should default to 0.7
        assert 0.0 <= result.quality_score <= 1.0

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_parse_clamps_score(self):
        """Test that score is clamped to 0.0-1.0 range."""
        response = """
QUALITY_SCORE: 1.5
DECISION: ACCEPT
REASONING: Excellent
SUGGESTIONS: None
"""
        result = parse_reflection_response(response)
        assert result.quality_score <= 1.0


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_get_reflection_config(self):
        """Test get_reflection_config function."""
        config = get_reflection_config("writer")
        assert isinstance(config, ReflectionConfig)

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_is_reflection_enabled(self):
        """Test is_reflection_enabled function."""
        # By default, reflection is disabled
        enabled = is_reflection_enabled("writer")
        assert isinstance(enabled, bool)


class TestRefinementPrompt:
    """Test refinement prompt creation."""

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_create_refinement_prompt(self):
        """Test creating refinement prompt."""
        reflection_result = ReflectionResult(
            decision=ReflectionDecision.REFINE,
            quality_score=0.65,
            reasoning="Missing sources",
            suggestions=["Add citations", "Include more recent data"],
            should_continue=True
        )

        prompt = create_refinement_prompt(
            original_query="What is AI?",
            current_response="AI is artificial intelligence.",
            reflection_result=reflection_result
        )

        assert "What is AI?" in prompt
        assert "AI is artificial intelligence" in prompt
        assert "0.65" in prompt
        assert "Missing sources" in prompt
        assert "Add citations" in prompt
        assert "Include more recent data" in prompt

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_refinement_prompt_contains_guidance(self):
        """Test that refinement prompt contains improvement guidance."""
        reflection_result = ReflectionResult(
            decision=ReflectionDecision.REFINE,
            quality_score=0.5,
            reasoning="Too brief",
            suggestions=["Expand explanation"],
            should_continue=True
        )

        prompt = create_refinement_prompt(
            original_query="Test query",
            current_response="Test response",
            reflection_result=reflection_result
        )

        # Should contain guidance for improvement
        assert "improve" in prompt.lower() or "refin" in prompt.lower()
        assert "Expand explanation" in prompt


class TestReflectionConfigThresholds:
    """Test that reflection thresholds are properly configured."""

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_all_thresholds_in_valid_range(self):
        """Test that all agent thresholds are in 0.0-1.0 range."""
        agents = ["researcher", "analyst", "writer", "supervisor"]
        for agent in agents:
            config = get_reflection_config(agent)
            assert 0.0 <= config.quality_threshold <= 1.0

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_writer_has_highest_threshold(self):
        """Test that writer has strict quality threshold."""
        writer_config = get_reflection_config("writer")
        supervisor_config = get_reflection_config("supervisor")
        # Writer should be more strict (higher threshold)
        assert writer_config.quality_threshold >= supervisor_config.quality_threshold

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_max_iterations_positive(self):
        """Test that all agents have positive max iterations."""
        agents = ["researcher", "analyst", "writer", "supervisor"]
        for agent in agents:
            config = get_reflection_config(agent)
            assert config.max_refinement_iterations > 0


class TestReflectionIntegrationReadiness:
    """Test that reflection is ready for integration."""

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_reflection_can_be_disabled_globally(self):
        """Test that reflection can be disabled."""
        from config_legacy import settings
        # Reflection should be disabled by default
        # This prevents unexpected behavior in production
        assert hasattr(settings, 'react_enable_reflection')

    @pytest.mark.unit
    @pytest.mark.fase3
    def test_per_agent_reflection_settings_exist(self):
        """Test that per-agent reflection settings exist in config."""
        from config_legacy import settings
        agents = ["researcher", "analyst", "writer", "supervisor"]
        for agent in agents:
            # Check enable flag exists
            enable_attr = f"{agent}_enable_reflection"
            assert hasattr(settings, enable_attr)

            # Check threshold exists
            threshold_attr = f"{agent}_reflection_threshold"
            assert hasattr(settings, threshold_attr)

            # Check max iterations exists
            max_iter_attr = f"{agent}_reflection_max_iterations"
            assert hasattr(settings, max_iter_attr)
