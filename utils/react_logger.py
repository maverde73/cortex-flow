"""
ReAct Structured Logger (FASE 4)

Provides structured logging for ReAct pattern execution:
- Thought/Action/Observation logging
- JSON and human-readable output
- Performance metrics
- History tracking
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class ReactEventType(str, Enum):
    """Types of ReAct events."""
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    REFLECTION = "reflection"
    REFINEMENT = "refinement"
    COMPLETION = "completion"
    ERROR = "error"
    TIMEOUT = "timeout"
    MAX_ITERATIONS = "max_iterations"


@dataclass
class ReactEvent:
    """Structured ReAct event."""
    event_type: ReactEventType
    iteration: int
    timestamp: float
    duration_ms: Optional[float] = None

    # Event-specific data
    thought: Optional[str] = None
    action_name: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    reflection_score: Optional[float] = None
    reflection_decision: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        data = asdict(self)
        # Remove None values for cleaner JSON
        return {k: v for k, v in data.items() if v is not None}

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def to_human_readable(self) -> str:
        """Convert to human-readable string."""
        lines = []
        lines.append(f"[Iteration {self.iteration}] {self.event_type.value.upper()}")

        if self.thought:
            lines.append(f"  Thought: {self.thought[:100]}...")

        if self.action_name:
            lines.append(f"  Action: {self.action_name}")
            if self.action_input:
                lines.append(f"  Input: {str(self.action_input)[:100]}...")

        if self.observation:
            lines.append(f"  Observation: {self.observation[:100]}...")

        if self.reflection_score is not None:
            lines.append(f"  Quality Score: {self.reflection_score:.2f}")
            if self.reflection_decision:
                lines.append(f"  Decision: {self.reflection_decision}")

        if self.error_message:
            lines.append(f"  Error: {self.error_message}")

        if self.duration_ms:
            lines.append(f"  Duration: {self.duration_ms:.0f}ms")

        return "\n".join(lines)


class ReactLogger:
    """
    Structured logger for ReAct pattern execution.

    Provides both JSON-structured logging and human-readable output.
    Tracks complete execution history with performance metrics.
    """

    def __init__(self, agent_name: str, task_id: str):
        """
        Initialize ReAct logger.

        Args:
            agent_name: Name of the agent (e.g., "researcher", "writer")
            task_id: Unique task identifier
        """
        self.agent_name = agent_name
        self.task_id = task_id
        self.events: List[ReactEvent] = []
        self.start_time = time.time()
        self.logger = logging.getLogger(f"react.{agent_name}")

    def log_thought(
        self,
        iteration: int,
        thought: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReactEvent:
        """
        Log agent thought/reasoning.

        Args:
            iteration: Current iteration number
            thought: Agent's reasoning text
            metadata: Additional metadata

        Returns:
            Created ReactEvent
        """
        event = ReactEvent(
            event_type=ReactEventType.THOUGHT,
            iteration=iteration,
            timestamp=time.time(),
            thought=thought,
            metadata=metadata
        )

        self.events.append(event)

        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info(f"[{self.agent_name} Iteration {iteration}] Thought: {thought[:200]}...")

        return event

    def log_action(
        self,
        iteration: int,
        action_name: str,
        action_input: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReactEvent:
        """
        Log agent action/tool call.

        Args:
            iteration: Current iteration number
            action_name: Name of action/tool being executed
            action_input: Input parameters for action
            metadata: Additional metadata

        Returns:
            Created ReactEvent
        """
        event = ReactEvent(
            event_type=ReactEventType.ACTION,
            iteration=iteration,
            timestamp=time.time(),
            action_name=action_name,
            action_input=action_input,
            metadata=metadata
        )

        self.events.append(event)

        if self.logger.isEnabledFor(logging.INFO):
            input_str = str(action_input)[:100] if action_input else "none"
            self.logger.info(
                f"[{self.agent_name} Iteration {iteration}] Action: {action_name} "
                f"with input: {input_str}..."
            )

        return event

    def log_observation(
        self,
        iteration: int,
        observation: str,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReactEvent:
        """
        Log observation from action/tool.

        Args:
            iteration: Current iteration number
            observation: Observation/result text
            duration_ms: Action duration in milliseconds
            metadata: Additional metadata

        Returns:
            Created ReactEvent
        """
        event = ReactEvent(
            event_type=ReactEventType.OBSERVATION,
            iteration=iteration,
            timestamp=time.time(),
            observation=observation,
            duration_ms=duration_ms,
            metadata=metadata
        )

        self.events.append(event)

        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info(
                f"[{self.agent_name} Iteration {iteration}] Observation: {observation[:200]}..."
            )

        return event

    def log_reflection(
        self,
        iteration: int,
        quality_score: float,
        decision: str,
        reasoning: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReactEvent:
        """
        Log reflection/quality assessment.

        Args:
            iteration: Current iteration number
            quality_score: Quality score (0.0-1.0)
            decision: Reflection decision (accept/refine/insufficient)
            reasoning: Reasoning for decision
            suggestions: Improvement suggestions
            metadata: Additional metadata

        Returns:
            Created ReactEvent
        """
        event_metadata = metadata or {}
        if reasoning:
            event_metadata["reasoning"] = reasoning
        if suggestions:
            event_metadata["suggestions"] = suggestions

        event = ReactEvent(
            event_type=ReactEventType.REFLECTION,
            iteration=iteration,
            timestamp=time.time(),
            reflection_score=quality_score,
            reflection_decision=decision,
            metadata=event_metadata
        )

        self.events.append(event)

        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info(
                f"[{self.agent_name} Reflection {iteration}] "
                f"Score: {quality_score:.2f}, Decision: {decision}"
            )

        return event

    def log_refinement(
        self,
        iteration: int,
        refinement_count: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReactEvent:
        """
        Log response refinement.

        Args:
            iteration: Current iteration number
            refinement_count: Number of refinements performed
            metadata: Additional metadata

        Returns:
            Created ReactEvent
        """
        event = ReactEvent(
            event_type=ReactEventType.REFINEMENT,
            iteration=iteration,
            timestamp=time.time(),
            metadata={**(metadata or {}), "refinement_count": refinement_count}
        )

        self.events.append(event)

        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info(
                f"[{self.agent_name} Refinement {refinement_count}] "
                f"Improving response based on feedback"
            )

        return event

    def log_completion(
        self,
        total_iterations: int,
        success: bool = True,
        final_answer: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReactEvent:
        """
        Log execution completion.

        Args:
            total_iterations: Total number of iterations
            success: Whether execution was successful
            final_answer: Final answer/response
            metadata: Additional metadata

        Returns:
            Created ReactEvent
        """
        duration_ms = (time.time() - self.start_time) * 1000

        event_metadata = metadata or {}
        event_metadata["success"] = success
        event_metadata["total_iterations"] = total_iterations
        if final_answer:
            event_metadata["final_answer_preview"] = final_answer[:200]

        event = ReactEvent(
            event_type=ReactEventType.COMPLETION,
            iteration=total_iterations,
            timestamp=time.time(),
            duration_ms=duration_ms,
            metadata=event_metadata
        )

        self.events.append(event)

        if self.logger.isEnabledFor(logging.INFO):
            status = "successfully" if success else "with errors"
            self.logger.info(
                f"[{self.agent_name} ReAct] Completed {status} after {total_iterations} "
                f"iteration(s) in {duration_ms:.0f}ms"
            )

        return event

    def log_error(
        self,
        iteration: int,
        error_message: str,
        error_count: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReactEvent:
        """
        Log error during execution.

        Args:
            iteration: Current iteration number
            error_message: Error message
            error_count: Consecutive error count
            metadata: Additional metadata

        Returns:
            Created ReactEvent
        """
        event = ReactEvent(
            event_type=ReactEventType.ERROR,
            iteration=iteration,
            timestamp=time.time(),
            error_message=error_message,
            metadata={**(metadata or {}), "error_count": error_count}
        )

        self.events.append(event)

        if self.logger.isEnabledFor(logging.ERROR):
            self.logger.error(
                f"[{self.agent_name} Iteration {iteration}] Error #{error_count}: {error_message}"
            )

        return event

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get complete execution history as list of dictionaries.

        Returns:
            List of event dictionaries
        """
        return [event.to_dict() for event in self.events]

    def get_history_json(self, indent: int = 2) -> str:
        """
        Get execution history as JSON string.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string
        """
        return json.dumps(self.get_history(), indent=indent)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get execution summary with metrics.

        Returns:
            Summary dictionary with metrics
        """
        total_duration = (time.time() - self.start_time) * 1000

        event_counts = {}
        for event in self.events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        return {
            "agent_name": self.agent_name,
            "task_id": self.task_id,
            "total_duration_ms": total_duration,
            "total_events": len(self.events),
            "event_counts": event_counts,
            "start_time": self.start_time,
            "end_time": time.time()
        }

    def print_human_readable(self):
        """Print human-readable execution history."""
        print("=" * 80)
        print(f"ReAct Execution History - {self.agent_name.upper()}")
        print(f"Task ID: {self.task_id}")
        print("=" * 80)

        for event in self.events:
            print(event.to_human_readable())
            print("-" * 80)

        summary = self.get_summary()
        print(f"\nTotal Duration: {summary['total_duration_ms']:.0f}ms")
        print(f"Total Events: {summary['total_events']}")
        print(f"Event Distribution: {summary['event_counts']}")
        print("=" * 80)


# Convenience functions

def create_react_logger(agent_name: str, task_id: str) -> ReactLogger:
    """Create a new ReactLogger instance."""
    return ReactLogger(agent_name, task_id)
