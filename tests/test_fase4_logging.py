"""
Unit tests for FASE 4: Structured ReAct Logging

Tests ReactLogger, event tracking, and history retrieval.
"""

import pytest
import time
from utils.react_logger import (
    ReactLogger,
    ReactEvent,
    ReactEventType,
    create_react_logger
)


class TestReactEventType:
    """Test ReactEventType enum."""

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_event_types_exist(self):
        """Test that all expected event types exist."""
        assert ReactEventType.THOUGHT == "thought"
        assert ReactEventType.ACTION == "action"
        assert ReactEventType.OBSERVATION == "observation"
        assert ReactEventType.REFLECTION == "reflection"
        assert ReactEventType.REFINEMENT == "refinement"
        assert ReactEventType.COMPLETION == "completion"
        assert ReactEventType.ERROR == "error"


class TestReactEvent:
    """Test ReactEvent dataclass."""

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_event_creation(self):
        """Test creating a ReAct event."""
        event = ReactEvent(
            event_type=ReactEventType.THOUGHT,
            iteration=1,
            timestamp=time.time(),
            thought="This is a test thought"
        )
        assert event.event_type == ReactEventType.THOUGHT
        assert event.iteration == 1
        assert event.thought == "This is a test thought"

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = ReactEvent(
            event_type=ReactEventType.ACTION,
            iteration=2,
            timestamp=time.time(),
            action_name="test_tool",
            action_input={"param": "value"}
        )
        event_dict = event.to_dict()
        assert "event_type" in event_dict
        assert "iteration" in event_dict
        assert "action_name" in event_dict
        assert event_dict["action_name"] == "test_tool"

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_event_to_json(self):
        """Test converting event to JSON."""
        event = ReactEvent(
            event_type=ReactEventType.OBSERVATION,
            iteration=3,
            timestamp=time.time(),
            observation="Test observation"
        )
        json_str = event.to_json()
        assert "observation" in json_str
        assert "Test observation" in json_str

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_event_to_human_readable(self):
        """Test converting event to human-readable string."""
        event = ReactEvent(
            event_type=ReactEventType.THOUGHT,
            iteration=1,
            timestamp=time.time(),
            thought="Test thought"
        )
        readable = event.to_human_readable()
        assert "Iteration 1" in readable
        assert "THOUGHT" in readable
        assert "Test thought" in readable


class TestReactLogger:
    """Test ReactLogger class."""

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_logger_creation(self):
        """Test creating a ReactLogger."""
        logger = ReactLogger(agent_name="test_agent", task_id="test-001")
        assert logger.agent_name == "test_agent"
        assert logger.task_id == "test-001"
        assert len(logger.events) == 0

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_log_thought(self):
        """Test logging a thought."""
        logger = ReactLogger(agent_name="test_agent", task_id="test-001")
        event = logger.log_thought(iteration=1, thought="Test thought")
        assert len(logger.events) == 1
        assert event.event_type == ReactEventType.THOUGHT
        assert event.thought == "Test thought"

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_log_action(self):
        """Test logging an action."""
        logger = ReactLogger(agent_name="test_agent", task_id="test-001")
        event = logger.log_action(
            iteration=1,
            action_name="search",
            action_input={"query": "test"}
        )
        assert len(logger.events) == 1
        assert event.event_type == ReactEventType.ACTION
        assert event.action_name == "search"
        assert event.action_input == {"query": "test"}

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_log_observation(self):
        """Test logging an observation."""
        logger = ReactLogger(agent_name="test_agent", task_id="test-001")
        event = logger.log_observation(
            iteration=1,
            observation="Test result",
            duration_ms=150.5
        )
        assert len(logger.events) == 1
        assert event.event_type == ReactEventType.OBSERVATION
        assert event.observation == "Test result"
        assert event.duration_ms == 150.5

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_log_reflection(self):
        """Test logging a reflection."""
        logger = ReactLogger(agent_name="test_agent", task_id="test-001")
        event = logger.log_reflection(
            iteration=1,
            quality_score=0.75,
            decision="refine",
            reasoning="Needs improvement",
            suggestions=["Add more detail"]
        )
        assert len(logger.events) == 1
        assert event.event_type == ReactEventType.REFLECTION
        assert event.reflection_score == 0.75
        assert event.reflection_decision == "refine"

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_log_completion(self):
        """Test logging completion."""
        logger = ReactLogger(agent_name="test_agent", task_id="test-001")
        event = logger.log_completion(
            total_iterations=3,
            success=True,
            final_answer="Test answer"
        )
        assert len(logger.events) == 1
        assert event.event_type == ReactEventType.COMPLETION
        assert event.duration_ms is not None
        assert event.duration_ms > 0

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_log_error(self):
        """Test logging an error."""
        logger = ReactLogger(agent_name="test_agent", task_id="test-001")
        event = logger.log_error(
            iteration=2,
            error_message="Test error",
            error_count=1
        )
        assert len(logger.events) == 1
        assert event.event_type == ReactEventType.ERROR
        assert event.error_message == "Test error"

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_get_history(self):
        """Test getting execution history."""
        logger = ReactLogger(agent_name="test_agent", task_id="test-001")
        logger.log_thought(iteration=1, thought="Thought 1")
        logger.log_action(iteration=1, action_name="action_1")
        logger.log_observation(iteration=1, observation="Obs 1")

        history = logger.get_history()
        assert len(history) == 3
        assert all(isinstance(event, dict) for event in history)

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_get_history_json(self):
        """Test getting history as JSON."""
        logger = ReactLogger(agent_name="test_agent", task_id="test-001")
        logger.log_thought(iteration=1, thought="Test")
        json_str = logger.get_history_json()
        assert isinstance(json_str, str)
        assert "test_agent" not in json_str  # Agent name not in individual events
        assert "thought" in json_str

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_get_summary(self):
        """Test getting execution summary."""
        logger = ReactLogger(agent_name="test_agent", task_id="test-001")
        logger.log_thought(iteration=1, thought="T1")
        logger.log_action(iteration=1, action_name="A1")
        logger.log_observation(iteration=1, observation="O1")
        logger.log_completion(total_iterations=1, success=True)

        summary = logger.get_summary()
        assert summary["agent_name"] == "test_agent"
        assert summary["task_id"] == "test-001"
        assert summary["total_events"] == 4
        assert "event_counts" in summary
        assert summary["event_counts"]["thought"] == 1
        assert summary["event_counts"]["action"] == 1
        assert summary["event_counts"]["observation"] == 1
        assert summary["event_counts"]["completion"] == 1


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_create_react_logger(self):
        """Test create_react_logger convenience function."""
        logger = create_react_logger(agent_name="writer", task_id="task-123")
        assert isinstance(logger, ReactLogger)
        assert logger.agent_name == "writer"
        assert logger.task_id == "task-123"


class TestReactLoggerIntegration:
    """Integration tests for ReactLogger."""

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_complete_react_cycle(self):
        """Test logging a complete ReAct cycle."""
        logger = ReactLogger(agent_name="test_agent", task_id="test-cycle")

        # Iteration 1
        logger.log_thought(iteration=1, thought="I need to search for information")
        logger.log_action(iteration=1, action_name="search", action_input={"query": "test"})
        logger.log_observation(iteration=1, observation="Found 10 results", duration_ms=250)

        # Iteration 2
        logger.log_thought(iteration=2, thought="I have enough information")
        logger.log_completion(total_iterations=2, success=True)

        assert len(logger.events) == 5
        summary = logger.get_summary()
        assert summary["total_events"] == 5
        assert summary["event_counts"]["thought"] == 2
        assert summary["event_counts"]["action"] == 1
        assert summary["event_counts"]["observation"] == 1
        assert summary["event_counts"]["completion"] == 1

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_reflection_cycle(self):
        """Test logging with reflection."""
        logger = ReactLogger(agent_name="writer", task_id="reflect-test")

        logger.log_thought(iteration=1, thought="Writing response")
        logger.log_reflection(
            iteration=1,
            quality_score=0.65,
            decision="refine",
            suggestions=["Add more examples"]
        )
        logger.log_thought(iteration=2, thought="Refining response")
        logger.log_reflection(
            iteration=2,
            quality_score=0.85,
            decision="accept"
        )
        logger.log_completion(total_iterations=2, success=True)

        summary = logger.get_summary()
        assert summary["event_counts"]["reflection"] == 2
        assert summary["event_counts"]["thought"] == 2


class TestReactHistoryMetadata:
    """Test react_history metadata compatibility."""

    @pytest.mark.unit
    @pytest.mark.fase4
    def test_history_format_compatible(self):
        """Test that history format is compatible with existing react_history."""
        logger = ReactLogger(agent_name="test", task_id="compat-test")
        logger.log_action(
            iteration=1,
            action_name="tool_execution",
            metadata={"tool": "search"}
        )
        logger.log_observation(iteration=1, observation="Result")

        history = logger.get_history()

        # Check compatibility with existing format
        for event in history:
            assert "iteration" in event
            assert "timestamp" in event
            assert "event_type" in event
