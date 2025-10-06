"""
Analyst Agent

Specializes in analyzing and synthesizing information from multiple sources.
"""

import time
import logging
from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from schemas.agent_state import AnalystState
from utils.llm_factory import get_llm
from config_legacy import settings

logger = logging.getLogger(__name__)


ANALYST_SYSTEM_PROMPT = """You are a Data Analysis Specialist agent.

Your role is to analyze, synthesize, and extract insights from raw information.

CAPABILITIES:
- Identify patterns and trends in data
- Filter relevant from irrelevant information
- Extract key points and insights
- Organize information logically
- Detect contradictions or gaps

INSTRUCTIONS:
1. Review all provided information carefully
2. Identify the most important points
3. Look for patterns, trends, and connections
4. Organize findings in a structured way
5. Highlight any gaps or areas needing more research

Be analytical, objective, and thorough. Focus on actionable insights."""


def create_analyst_agent():
    """Creates the Analyst agent graph."""

    # Initialize the LLM using the factory (FASE 2: now returns tuple with ReactConfig)
    llm, react_config = get_llm(agent="analyst")

    logger.info(f"Analyst initialized with {react_config}")

    # Analyst typically doesn't need tools - just analyzes provided data
    # But we can add tools if needed later
    tools = []

    def call_model(state: AnalystState) -> dict:
        """Agent node: invokes the LLM for analysis."""
        messages = state["messages"]

        # Initialize ReAct metadata on first run
        if "iteration_count" not in state or state.get("iteration_count") is None:
            state.setdefault("iteration_count", 0)
            state.setdefault("error_count", 0)
            state.setdefault("start_time", time.time())
            state.setdefault("react_history", [])
            state.setdefault("should_stop", False)
            state.setdefault("early_stop_reason", None)

        if len(messages) == 1 and isinstance(messages[0], HumanMessage):
            messages = [SystemMessage(content=ANALYST_SYSTEM_PROMPT)] + list(messages)

        response = llm.invoke(messages)

        # Increment iteration counter
        new_iteration = state.get("iteration_count", 0) + 1

        # Log thought if verbose logging enabled
        if settings.react_log_thoughts and settings.react_enable_verbose_logging:
            thought = getattr(response, "content", "")
            logger.info(f"[Analyst ReAct Iteration {new_iteration}] Analysis: {thought[:200]}...")

        return {
            "messages": [response],
            "iteration_count": new_iteration
        }

    def should_continue(state: AnalystState) -> Literal["end"]:
        """
        Analyst typically completes in one pass, but we add timeout/iteration checks.
        """
        # Check manual stop flag
        if state.get("should_stop", False):
            reason = state.get("early_stop_reason", "Manual stop triggered")
            logger.warning(f"[Analyst ReAct] Stopping early: {reason}")
            return "end"

        # Check timeout (FASE 2: use strategy timeout)
        start_time = state.get("start_time", time.time())
        elapsed = time.time() - start_time
        if elapsed > react_config.timeout_seconds:
            logger.warning(f"[Analyst ReAct] Timeout exceeded: {elapsed:.1f}s")
            state["early_stop_reason"] = f"Timeout after {elapsed:.1f}s"
            return "end"

        # Check max iterations (FASE 2: use strategy max_iterations)
        iteration_count = state.get("iteration_count", 0)
        if iteration_count >= react_config.max_iterations:
            logger.warning(f"[Analyst ReAct] Max iterations reached: {iteration_count}")
            state["early_stop_reason"] = f"Max iterations ({react_config.max_iterations}) reached"
            return "end"

        if settings.react_enable_verbose_logging:
            logger.info(f"[Analyst ReAct] Completed after {iteration_count} iteration(s)")

        return "end"

    # Create simple graph (analyst doesn't use tools typically)
    workflow = StateGraph(AnalystState)
    workflow.add_node("agent", call_model)
    workflow.set_entry_point("agent")

    # Add conditional edge for safety checks
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"end": END}
    )

    return workflow.compile()


_analyst_agent = None

def get_analyst_agent():
    """Get or create the analyst agent instance."""
    global _analyst_agent
    if _analyst_agent is None:
        _analyst_agent = create_analyst_agent()
    return _analyst_agent
