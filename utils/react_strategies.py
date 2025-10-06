"""
ReAct Reasoning Strategies

Defines different reasoning strategies for agents with corresponding parameters.
Each strategy optimizes for different use cases:
- FAST: Quick responses, minimal iterations
- BALANCED: Standard tasks, moderate reasoning
- DEEP: Complex research, extended reasoning
- CREATIVE: Content generation, high temperature
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ReactStrategy(str, Enum):
    """Enumeration of available ReAct reasoning strategies."""

    # FASE 2: Basic strategies
    FAST = "fast"
    BALANCED = "balanced"
    DEEP = "deep"
    CREATIVE = "creative"

    # FASE 6: Advanced reasoning modes
    COT_EXPLICIT = "cot_explicit"  # Chain-of-Thought with explicit step logging
    TREE_OF_THOUGHT = "tree_of_thought"  # Explore multiple reasoning paths
    ADAPTIVE = "adaptive"  # Dynamic strategy switching based on performance

    @classmethod
    def from_string(cls, value: str) -> "ReactStrategy":
        """
        Convert string to ReactStrategy enum, with fallback to BALANCED.

        Args:
            value: String representation of strategy

        Returns:
            ReactStrategy enum value
        """
        try:
            return cls(value.lower())
        except (ValueError, AttributeError):
            logger.warning(
                f"Invalid strategy '{value}', falling back to BALANCED"
            )
            return cls.BALANCED


@dataclass
class ReactConfig:
    """
    Configuration parameters for a ReAct reasoning strategy.

    Attributes:
        strategy: The strategy type
        max_iterations: Maximum number of ReAct cycles
        temperature: LLM temperature (0.0-1.0)
        timeout_seconds: Maximum execution time
        description: Human-readable strategy description
    """

    strategy: ReactStrategy
    max_iterations: int
    temperature: float
    timeout_seconds: float
    description: str

    @classmethod
    def from_strategy(cls, strategy: ReactStrategy) -> "ReactConfig":
        """
        Create ReactConfig from strategy enum.

        Args:
            strategy: ReactStrategy enum value

        Returns:
            ReactConfig with parameters for the strategy
        """
        configs = {
            # FASE 2: Basic strategies
            ReactStrategy.FAST: cls(
                strategy=ReactStrategy.FAST,
                max_iterations=3,
                temperature=0.3,
                timeout_seconds=30.0,
                description="Quick responses for simple queries (3 iter, low temp, 30s timeout)"
            ),
            ReactStrategy.BALANCED: cls(
                strategy=ReactStrategy.BALANCED,
                max_iterations=10,
                temperature=0.7,
                timeout_seconds=120.0,
                description="Standard reasoning for most tasks (10 iter, balanced temp, 2min timeout)"
            ),
            ReactStrategy.DEEP: cls(
                strategy=ReactStrategy.DEEP,
                max_iterations=20,
                temperature=0.7,
                timeout_seconds=300.0,
                description="Deep reasoning for complex research (20 iter, balanced temp, 5min timeout)"
            ),
            ReactStrategy.CREATIVE: cls(
                strategy=ReactStrategy.CREATIVE,
                max_iterations=15,
                temperature=0.9,
                timeout_seconds=180.0,
                description="Creative generation for content writing (15 iter, high temp, 3min timeout)"
            ),

            # FASE 6: Advanced reasoning modes
            ReactStrategy.COT_EXPLICIT: cls(
                strategy=ReactStrategy.COT_EXPLICIT,
                max_iterations=15,
                temperature=0.5,
                timeout_seconds=240.0,
                description="Chain-of-Thought: Explicit step-by-step reasoning with checkpoints (15 iter, 4min timeout)"
            ),
            ReactStrategy.TREE_OF_THOUGHT: cls(
                strategy=ReactStrategy.TREE_OF_THOUGHT,
                max_iterations=25,
                temperature=0.6,
                timeout_seconds=360.0,
                description="Tree-of-Thought: Explore multiple reasoning paths and select best (25 iter, 6min timeout)"
            ),
            ReactStrategy.ADAPTIVE: cls(
                strategy=ReactStrategy.ADAPTIVE,
                max_iterations=30,  # Higher ceiling for adaptive escalation
                temperature=0.7,
                timeout_seconds=300.0,
                description="Adaptive: Dynamic strategy switching based on task complexity (up to 30 iter, 5min timeout)"
            ),
        }

        return configs[strategy]

    @classmethod
    def from_string(cls, strategy_str: str) -> "ReactConfig":
        """
        Create ReactConfig from strategy string.

        Args:
            strategy_str: String name of strategy

        Returns:
            ReactConfig with parameters for the strategy
        """
        strategy = ReactStrategy.from_string(strategy_str)
        return cls.from_strategy(strategy)

    def __repr__(self) -> str:
        """String representation for logging."""
        return (
            f"ReactConfig(strategy={self.strategy.value}, "
            f"max_iter={self.max_iterations}, temp={self.temperature}, "
            f"timeout={self.timeout_seconds}s)"
        )


def get_strategy_for_agent(
    agent_name: str,
    task_name: Optional[str] = None,
    default_strategy: str = "balanced"
) -> ReactConfig:
    """
    Get ReAct strategy configuration for an agent.

    Priority order:
    1. Task-specific strategy (e.g., RESEARCHER_DEEP_ANALYSIS_REACT_STRATEGY)
    2. Agent-specific strategy (e.g., RESEARCHER_REACT_STRATEGY)
    3. Default strategy parameter
    4. Fallback to BALANCED

    Args:
        agent_name: Name of the agent (e.g., "researcher")
        task_name: Optional specific task (e.g., "deep_analysis")
        default_strategy: Default if no config found

    Returns:
        ReactConfig for the agent/task
    """
    from config_legacy import settings

    # Priority 1: Task-specific strategy
    if task_name:
        task_strategy_key = f"{agent_name}_{task_name}_react_strategy"
        task_strategy = getattr(settings, task_strategy_key, None)
        if task_strategy:
            logger.info(
                f"Using task-specific strategy for {agent_name}.{task_name}: {task_strategy}"
            )
            return ReactConfig.from_string(task_strategy)

    # Priority 2: Agent-specific strategy
    agent_strategy_key = f"{agent_name}_react_strategy"
    agent_strategy = getattr(settings, agent_strategy_key, None)
    if agent_strategy:
        logger.info(
            f"Using agent-specific strategy for {agent_name}: {agent_strategy}"
        )
        return ReactConfig.from_string(agent_strategy)

    # Priority 3: Default strategy
    logger.info(
        f"Using default strategy for {agent_name}: {default_strategy}"
    )
    return ReactConfig.from_string(default_strategy)


# Convenience functions for common patterns

def get_fast_config() -> ReactConfig:
    """Get FAST strategy config."""
    return ReactConfig.from_strategy(ReactStrategy.FAST)


def get_balanced_config() -> ReactConfig:
    """Get BALANCED strategy config."""
    return ReactConfig.from_strategy(ReactStrategy.BALANCED)


def get_deep_config() -> ReactConfig:
    """Get DEEP strategy config."""
    return ReactConfig.from_strategy(ReactStrategy.DEEP)


def get_creative_config() -> ReactConfig:
    """Get CREATIVE strategy config."""
    return ReactConfig.from_strategy(ReactStrategy.CREATIVE)


# FASE 6: Advanced reasoning mode helpers

def get_cot_explicit_config() -> ReactConfig:
    """Get COT_EXPLICIT strategy config."""
    return ReactConfig.from_strategy(ReactStrategy.COT_EXPLICIT)


def get_tree_of_thought_config() -> ReactConfig:
    """Get TREE_OF_THOUGHT strategy config."""
    return ReactConfig.from_strategy(ReactStrategy.TREE_OF_THOUGHT)


def get_adaptive_config() -> ReactConfig:
    """Get ADAPTIVE strategy config."""
    return ReactConfig.from_strategy(ReactStrategy.ADAPTIVE)
