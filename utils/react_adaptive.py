"""
Adaptive Reasoning Support (FASE 6)

Implements dynamic strategy switching based on task complexity
and performance metrics.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from utils.react_strategies import ReactStrategy, ReactConfig

logger = logging.getLogger(__name__)


class ComplexityLevel(str, Enum):
    """Estimated complexity level of a task."""
    SIMPLE = "simple"  # Straightforward, clear path
    MODERATE = "moderate"  # Some reasoning required
    COMPLEX = "complex"  # Deep analysis needed
    UNKNOWN = "unknown"  # Complexity not yet determined


@dataclass
class PerformanceMetrics:
    """
    Tracks performance metrics for adaptive strategy selection.

    Attributes:
        iterations_used: Number of iterations consumed
        time_elapsed: Time spent so far (seconds)
        errors_encountered: Number of errors hit
        progress_score: Estimated progress (0.0-1.0)
        confidence_score: Confidence in current approach (0.0-1.0)
    """
    iterations_used: int = 0
    time_elapsed: float = 0.0
    errors_encountered: int = 0
    progress_score: float = 0.0
    confidence_score: float = 1.0

    def is_stuck(self, max_errors: int = 3) -> bool:
        """Check if we appear to be stuck."""
        return (
            self.errors_encountered >= max_errors or
            (self.iterations_used > 5 and self.progress_score < 0.2)
        )

    def is_progressing_well(self) -> bool:
        """Check if making good progress."""
        return (
            self.progress_score > 0.5 and
            self.confidence_score > 0.6 and
            self.errors_encountered == 0
        )


@dataclass
class StrategyTransition:
    """
    Records a strategy change during adaptive reasoning.

    Attributes:
        from_strategy: Previous strategy
        to_strategy: New strategy
        reason: Why the switch occurred
        iteration: At which iteration it happened
        timestamp: When it happened
    """
    from_strategy: ReactStrategy
    to_strategy: ReactStrategy
    reason: str
    iteration: int
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return (
            f"{self.from_strategy.value} → {self.to_strategy.value} "
            f"at iter {self.iteration}: {self.reason}"
        )


@dataclass
class AdaptiveReasoning:
    """
    Manages adaptive strategy selection and switching.

    Starts with a fast strategy and escalates to deeper reasoning
    if needed based on performance metrics.
    """
    task_description: str
    initial_strategy: ReactStrategy = ReactStrategy.FAST
    current_strategy: ReactStrategy = ReactStrategy.FAST
    max_escalations: int = 3  # Maximum times to escalate
    escalation_count: int = 0
    transitions: List[StrategyTransition] = field(default_factory=list)
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    started_at: datetime = field(default_factory=datetime.now)
    complexity_estimate: ComplexityLevel = ComplexityLevel.UNKNOWN

    def __post_init__(self):
        """Initialize current strategy to initial strategy."""
        self.current_strategy = self.initial_strategy

    def estimate_complexity(self, task: str) -> ComplexityLevel:
        """
        Estimate task complexity from description.

        Args:
            task: The task description

        Returns:
            Estimated complexity level
        """
        # Simple heuristic based on task characteristics
        task_lower = task.lower()

        # Keywords that suggest complexity
        complex_keywords = [
            "analyze", "evaluate", "compare", "assess", "research",
            "comprehensive", "detailed", "thorough", "investigate"
        ]

        simple_keywords = [
            "get", "find", "show", "list", "what is", "tell me"
        ]

        complex_count = sum(1 for kw in complex_keywords if kw in task_lower)
        simple_count = sum(1 for kw in simple_keywords if kw in task_lower)

        if complex_count > simple_count:
            return ComplexityLevel.COMPLEX
        elif simple_count > complex_count:
            return ComplexityLevel.SIMPLE
        else:
            return ComplexityLevel.MODERATE

    def get_initial_strategy_for_complexity(
        self,
        complexity: ComplexityLevel
    ) -> ReactStrategy:
        """
        Get recommended initial strategy for complexity level.

        Args:
            complexity: The task complexity

        Returns:
            Recommended starting strategy
        """
        strategy_map = {
            ComplexityLevel.SIMPLE: ReactStrategy.FAST,
            ComplexityLevel.MODERATE: ReactStrategy.BALANCED,
            ComplexityLevel.COMPLEX: ReactStrategy.DEEP,
            ComplexityLevel.UNKNOWN: ReactStrategy.BALANCED
        }

        return strategy_map[complexity]

    def should_escalate(self) -> bool:
        """
        Determine if strategy should be escalated.

        Returns:
            True if escalation recommended
        """
        # Don't escalate if we've hit the limit
        if self.escalation_count >= self.max_escalations:
            logger.debug("Max escalations reached, not escalating")
            return False

        # Escalate if stuck
        if self.metrics.is_stuck():
            logger.info("Performance metrics suggest we're stuck")
            return True

        # Escalate if current strategy is exhausted but task not complete
        if self.current_strategy == ReactStrategy.FAST:
            if self.metrics.iterations_used >= 3 and self.metrics.progress_score < 0.8:
                logger.info("FAST strategy exhausted without completion")
                return True

        elif self.current_strategy == ReactStrategy.BALANCED:
            if self.metrics.iterations_used >= 10 and self.metrics.progress_score < 0.8:
                logger.info("BALANCED strategy exhausted without completion")
                return True

        return False

    def escalate_strategy(self, reason: str) -> ReactStrategy:
        """
        Escalate to a more powerful strategy.

        Args:
            reason: Why escalation is needed

        Returns:
            The new strategy
        """
        # Define escalation path
        escalation_path = {
            ReactStrategy.FAST: ReactStrategy.BALANCED,
            ReactStrategy.BALANCED: ReactStrategy.DEEP,
            ReactStrategy.DEEP: ReactStrategy.TREE_OF_THOUGHT,
            ReactStrategy.TREE_OF_THOUGHT: ReactStrategy.TREE_OF_THOUGHT,  # Max level
            ReactStrategy.COT_EXPLICIT: ReactStrategy.TREE_OF_THOUGHT,
            ReactStrategy.CREATIVE: ReactStrategy.DEEP,  # Escalate to deep reasoning
        }

        old_strategy = self.current_strategy
        new_strategy = escalation_path.get(old_strategy, ReactStrategy.DEEP)

        # Record transition
        transition = StrategyTransition(
            from_strategy=old_strategy,
            to_strategy=new_strategy,
            reason=reason,
            iteration=self.metrics.iterations_used
        )

        self.transitions.append(transition)
        self.current_strategy = new_strategy
        self.escalation_count += 1

        logger.info(f"Strategy escalated: {transition}")

        return new_strategy

    def update_metrics(
        self,
        iterations_used: int,
        time_elapsed: float,
        errors_encountered: int,
        progress_score: float,
        confidence_score: float
    ):
        """
        Update performance metrics.

        Args:
            iterations_used: Total iterations so far
            time_elapsed: Total time elapsed (seconds)
            errors_encountered: Total errors encountered
            progress_score: Estimated progress (0.0-1.0)
            confidence_score: Confidence in approach (0.0-1.0)
        """
        self.metrics.iterations_used = iterations_used
        self.metrics.time_elapsed = time_elapsed
        self.metrics.errors_encountered = errors_encountered
        self.metrics.progress_score = progress_score
        self.metrics.confidence_score = confidence_score

        logger.debug(
            f"Metrics updated: iter={iterations_used}, "
            f"progress={progress_score:.2f}, confidence={confidence_score:.2f}"
        )

        # Check if escalation is needed
        if self.should_escalate():
            self.escalate_strategy("Performance metrics indicate escalation needed")

    def get_current_config(self) -> ReactConfig:
        """
        Get configuration for current strategy.

        Returns:
            ReactConfig for current strategy
        """
        return ReactConfig.from_strategy(self.current_strategy)

    def get_summary(self) -> str:
        """
        Generate a summary of adaptive reasoning session.

        Returns:
            Human-readable summary
        """
        duration = (datetime.now() - self.started_at).total_seconds()

        summary = [
            f"Adaptive Reasoning Summary:",
            f"- Task: {self.task_description}",
            f"- Initial Strategy: {self.initial_strategy.value}",
            f"- Current Strategy: {self.current_strategy.value}",
            f"- Escalations: {self.escalation_count}/{self.max_escalations}",
            f"- Duration: {duration:.1f}s",
            f"- Iterations: {self.metrics.iterations_used}",
            f"- Errors: {self.metrics.errors_encountered}",
            f"- Progress: {self.metrics.progress_score:.2f}",
            f"- Confidence: {self.metrics.confidence_score:.2f}",
            f""
        ]

        if self.transitions:
            summary.append("Strategy Transitions:")
            for t in self.transitions:
                summary.append(f"  - {t}")
        else:
            summary.append("No strategy transitions occurred")

        return "\n".join(summary)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_description": self.task_description,
            "initial_strategy": self.initial_strategy.value,
            "current_strategy": self.current_strategy.value,
            "max_escalations": self.max_escalations,
            "escalation_count": self.escalation_count,
            "transitions": [
                {
                    "from": t.from_strategy.value,
                    "to": t.to_strategy.value,
                    "reason": t.reason,
                    "iteration": t.iteration
                }
                for t in self.transitions
            ],
            "metrics": {
                "iterations_used": self.metrics.iterations_used,
                "time_elapsed": self.metrics.time_elapsed,
                "errors_encountered": self.metrics.errors_encountered,
                "progress_score": self.metrics.progress_score,
                "confidence_score": self.metrics.confidence_score
            },
            "complexity_estimate": self.complexity_estimate.value,
            "started_at": self.started_at.isoformat()
        }


def create_adaptive_session(
    task: str,
    max_escalations: int = 3
) -> AdaptiveReasoning:
    """
    Create an adaptive reasoning session for a task.

    Args:
        task: The task description
        max_escalations: Maximum number of strategy escalations

    Returns:
        Configured AdaptiveReasoning instance
    """
    # Create session
    session = AdaptiveReasoning(
        task_description=task,
        max_escalations=max_escalations
    )

    # Estimate complexity
    complexity = session.estimate_complexity(task)
    session.complexity_estimate = complexity

    # Set initial strategy based on complexity
    initial_strategy = session.get_initial_strategy_for_complexity(complexity)
    session.initial_strategy = initial_strategy
    session.current_strategy = initial_strategy

    logger.info(
        f"Created adaptive session: complexity={complexity.value}, "
        f"initial_strategy={initial_strategy.value}"
    )

    return session
