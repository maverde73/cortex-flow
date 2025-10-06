"""
Web Researcher Agent

Specializes in finding up-to-date information from the internet.
Uses the ReAct pattern with LangGraph for transparent reasoning.
Includes self-reflection capability for research quality (FASE 3).
"""

import time
import logging
from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from schemas.agent_state import ResearcherState
from tools.web_tools import tavily_search
from utils.llm_factory import get_llm
from utils.react_reflection import (
    reflect_on_response,
    create_refinement_prompt,
    get_reflection_config,
    ReflectionDecision
)
from config_legacy import settings

logger = logging.getLogger(__name__)


# System prompt for the researcher agent
RESEARCHER_SYSTEM_PROMPT = """You are a Web Research Specialist agent.

Your role is to find accurate, up-to-date information from the internet.

CAPABILITIES:
- Search the web using advanced search tools
- Identify reliable sources
- Extract relevant information
- Summarize findings clearly

INSTRUCTIONS:
1. Analyze the research request carefully
2. Formulate effective search queries
3. Use the tavily_search tool to find information
4. Synthesize the results into a clear, concise summary
5. Include source URLs for verification

Be thorough but concise. Focus on factual, recent information."""


def create_researcher_agent():
    """
    Creates the Web Researcher agent graph with self-reflection (FASE 3).

    Returns:
        Compiled LangGraph agent
    """

    # Initialize the LLM using the factory (FASE 2: now returns tuple with ReactConfig)
    llm, react_config = get_llm(agent="researcher")

    # Get reflection configuration (FASE 3)
    reflection_config = get_reflection_config("researcher")

    logger.info(f"Researcher initialized with {react_config}")
    if reflection_config.enabled:
        logger.info(f"Researcher reflection enabled: threshold={reflection_config.quality_threshold}, max_iter={reflection_config.max_refinement_iterations}")

    # Bind tools to the LLM
    tools = [tavily_search]
    llm_with_tools = llm.bind_tools(tools)

    # Define the agent node
    def call_model(state: ResearcherState) -> dict:
        """
        Agent node: invokes the LLM to decide next action.

        Returns state update with the LLM's response (thought + action).
        """
        messages = state["messages"]

        # Initialize ReAct metadata on first run
        if "iteration_count" not in state or state.get("iteration_count") is None:
            state.setdefault("iteration_count", 0)
            state.setdefault("error_count", 0)
            state.setdefault("start_time", time.time())
            state.setdefault("react_history", [])
            state.setdefault("should_stop", False)
            state.setdefault("early_stop_reason", None)
            state.setdefault("refinement_count", 0)  # FASE 3: track refinements

        # Add system prompt if this is the first message
        if len(messages) == 1 and isinstance(messages[0], HumanMessage):
            messages = [SystemMessage(content=RESEARCHER_SYSTEM_PROMPT)] + list(messages)

        response = llm_with_tools.invoke(messages)

        # Increment iteration counter
        new_iteration = state.get("iteration_count", 0) + 1

        # Log thought if verbose logging enabled
        if settings.react_log_thoughts and settings.react_enable_verbose_logging:
            thought = getattr(response, "content", "")
            logger.info(f"[ReAct Iteration {new_iteration}] Thought: {thought[:200]}...")

        return {
            "messages": [response],
            "iteration_count": new_iteration
        }

    # Define conditional edge logic
    def should_continue(state: ResearcherState) -> Literal["tools", "end"]:
        """
        Determines whether to continue with tool execution or end.

        Checks multiple conditions:
        - Timeout exceeded
        - Max iterations reached
        - Max consecutive errors reached
        - Manual stop flag
        - Tool calls present (normal ReAct flow)
        """
        messages = state["messages"]
        last_message = messages[-1]

        # Check 1: Manual stop flag
        if state.get("should_stop", False):
            reason = state.get("early_stop_reason", "Manual stop triggered")
            logger.warning(f"[ReAct] Stopping early: {reason}")
            return "end"

        # Check 2: Timeout exceeded (FASE 2: use strategy timeout)
        start_time = state.get("start_time", time.time())
        elapsed = time.time() - start_time
        agent_react_config = get_llm(agent="researcher")[1]  # Get ReactConfig from factory
        if elapsed > agent_react_config.timeout_seconds:
            logger.warning(
                f"[ReAct] Timeout exceeded: {elapsed:.1f}s > {agent_react_config.timeout_seconds}s"
            )
            # Optionally set early_stop_reason in state for logging
            state["early_stop_reason"] = f"Timeout after {elapsed:.1f}s"
            return "end"

        # Check 3: Max iterations reached (FASE 2: use strategy max_iterations)
        iteration_count = state.get("iteration_count", 0)
        if iteration_count >= react_config.max_iterations:
            logger.warning(
                f"[ReAct] Max iterations reached: {iteration_count} >= {react_config.max_iterations}"
            )
            state["early_stop_reason"] = f"Max iterations ({react_config.max_iterations}) reached"
            return "end"

        # Check 4: Max consecutive errors
        error_count = state.get("error_count", 0)
        if error_count >= settings.react_max_consecutive_errors:
            logger.error(
                f"[ReAct] Max consecutive errors reached: {error_count} >= {settings.react_max_consecutive_errors}"
            )
            state["early_stop_reason"] = f"Too many consecutive errors ({error_count})"
            return "end"

        # Check 5: Normal ReAct flow - check for tool calls
        if hasattr(last_message, "tool_calls") and getattr(last_message, "tool_calls", None):
            # Log action if enabled
            if settings.react_log_actions and settings.react_enable_verbose_logging:
                tool_calls = last_message.tool_calls
                for tc in tool_calls:
                    logger.info(
                        f"[ReAct Iteration {iteration_count}] Action: {tc.get('name', 'unknown')} "
                        f"with input: {str(tc.get('args', {}))[:100]}..."
                    )
            return "tools"

        # No tool calls and no stop conditions = final answer reached
        if settings.react_enable_verbose_logging:
            logger.info(f"[ReAct] Completed successfully after {iteration_count} iterations")

        return "end"

    # Wrapper for tool execution with error tracking
    async def execute_tools(state: ResearcherState) -> dict:
        """
        Execute tools and track errors/observations.
        """
        tool_node = ToolNode(tools)

        try:
            # Execute the tool - use ainvoke for async tools
            result = await tool_node.ainvoke(state)

            # Reset error count on successful execution
            new_error_count = 0

            # Log observation if enabled
            if settings.react_log_observations and settings.react_enable_verbose_logging:
                # Get the last tool message (observation)
                messages = result.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    observation = getattr(last_msg, "content", "")
                    iteration = state.get("iteration_count", 0)
                    logger.info(
                        f"[ReAct Iteration {iteration}] Observation: {observation[:200]}..."
                    )

            # Update react_history if logging enabled
            if settings.react_enable_verbose_logging:
                history_entry = {
                    "iteration": state.get("iteration_count", 0),
                    "timestamp": time.time(),
                    "action": "tool_execution",
                    "observation": str(messages[-1].content) if messages else ""
                }
                new_history = state.get("react_history", []) + [history_entry]
                result["react_history"] = new_history

            result["error_count"] = new_error_count
            return result

        except Exception as e:
            # Increment error count
            new_error_count = state.get("error_count", 0) + 1
            logger.error(
                f"[ReAct] Tool execution error (#{new_error_count}): {str(e)}"
            )

            # Create error message to add to state
            from langchain_core.messages import AIMessage
            error_msg = AIMessage(
                content=f"Tool execution failed: {str(e)}. Error count: {new_error_count}"
            )

            return {
                "messages": [error_msg],
                "error_count": new_error_count
            }

    # FASE 3: Reflection functions (optional, disabled by default)
    async def reflect(state: ResearcherState) -> dict:
        """Reflection node: evaluates research quality."""
        messages = state["messages"]
        original_query = messages[0].content if messages else ""
        current_response = messages[-1].content if messages else ""
        refinement_count = state.get("refinement_count", 0)

        reflection_result = await reflect_on_response(
            query=original_query,
            response=current_response,
            agent_name="researcher",
            llm=llm,
            iteration=refinement_count,
            config=reflection_config
        )

        react_history = state.get("react_history", [])
        react_history.append({
            "iteration": state.get("iteration_count", 0),
            "timestamp": time.time(),
            "action": "reflection",
            "decision": reflection_result.decision.value,
            "quality_score": reflection_result.quality_score,
            "reasoning": reflection_result.reasoning
        })

        return {
            "react_history": react_history,
            "reflection_decision": reflection_result.decision.value,
            "reflection_score": reflection_result.quality_score,
            "reflection_suggestions": reflection_result.suggestions
        }

    # Create the graph
    workflow = StateGraph(ResearcherState)

    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", execute_tools)
    if reflection_config.enabled:
        workflow.add_node("reflect", reflect)  # FASE 3: optional reflection node

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    # Note: Reflection for researcher would require more complex logic
    # For now, keep simple flow: agent <-> tools -> end
    # Reflection can be added in future iteration
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )

    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")

    # Compile the graph
    return workflow.compile()


# Lazy initialization - create agent when needed
_researcher_agent = None

def get_researcher_agent():
    """Get or create the researcher agent instance."""
    global _researcher_agent
    if _researcher_agent is None:
        _researcher_agent = create_researcher_agent()
    return _researcher_agent
