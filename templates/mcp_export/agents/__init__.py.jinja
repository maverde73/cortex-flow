"""
Lite Agent Implementations for Standalone MCP Export

These are lightweight versions of the full agents that can run
independently with just an LLM client.
"""

from .base_agent import BaseLiteAgent
from .researcher_lite import ResearcherLiteAgent
from .analyst_lite import AnalystLiteAgent
from .writer_lite import WriterLiteAgent

# Agent registry
AGENT_REGISTRY = {
    "researcher": ResearcherLiteAgent,
    "analyst": AnalystLiteAgent,
    "writer": WriterLiteAgent,
}


def get_agent(agent_type: str) -> BaseLiteAgent:
    """
    Factory function to get an agent instance by type.

    Args:
        agent_type: Type of agent (researcher, analyst, writer)

    Returns:
        Agent instance

    Raises:
        ValueError: If agent type is not supported
    """
    if agent_type not in AGENT_REGISTRY:
        raise ValueError(f"Unknown agent type: {agent_type}. Supported types: {list(AGENT_REGISTRY.keys())}")

    agent_class = AGENT_REGISTRY[agent_type]
    return agent_class()


__all__ = [
    "BaseLiteAgent",
    "ResearcherLiteAgent",
    "AnalystLiteAgent",
    "WriterLiteAgent",
    "get_agent",
]