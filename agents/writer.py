"""
Writer Agent

Specializes in creating well-structured, professional written content.
Includes self-reflection capability for quality improvement (FASE 3).
Includes structured ReAct logging (FASE 4).
"""

import time
import logging
from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from schemas.agent_state import WriterState
from utils.llm_factory import get_llm
from utils.react_reflection import (
    reflect_on_response,
    create_refinement_prompt,
    get_reflection_config,
    ReflectionDecision
)
from utils.react_logger import create_react_logger, ReactLogger
from config import settings

logger = logging.getLogger(__name__)


WRITER_SYSTEM_PROMPT = """You are a Professional Writing Specialist agent.

Your role is to create clear, well-structured, and engaging written content.

CAPABILITIES:
- Write reports, articles, and summaries
- Structure content logically with clear sections
- Maintain consistent tone and style
- Use proper formatting (markdown)
- Ensure clarity and readability

INSTRUCTIONS:
1. Understand the writing task and target audience
2. Organize information into logical sections
3. Use clear headings and structure
4. Write concisely but comprehensively
5. Include relevant details and citations when available

STYLE GUIDELINES:
- Use markdown formatting for structure
- Start with an executive summary for reports
- Use bullet points for lists
- Include clear section headers
- End with key takeaways or conclusions

Be professional, clear, and engaging."""


def create_writer_agent():
    """Creates the Writer agent graph with self-reflection (FASE 3)."""

    # Initialize the LLM using the factory (FASE 2: now returns tuple with ReactConfig)
    # Note: temperature can be overridden, but strategy's temperature will be used if not specified
    llm, react_config = get_llm(agent="writer")

    # Get reflection configuration (FASE 3)
    reflection_config = get_reflection_config("writer")

    logger.info(f"Writer initialized with {react_config}")
    if reflection_config.enabled:
        logger.info(f"Writer reflection enabled: threshold={reflection_config.quality_threshold}, max_iter={reflection_config.max_refinement_iterations}")

    def call_model(state: WriterState) -> dict:
        """Agent node: invokes the LLM for writing."""
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

        if len(messages) == 1 and isinstance(messages[0], HumanMessage):
            messages = [SystemMessage(content=WRITER_SYSTEM_PROMPT)] + list(messages)

        response = llm.invoke(messages)

        # Increment iteration counter
        new_iteration = state.get("iteration_count", 0) + 1

        # Log thought if verbose logging enabled
        if settings.react_log_thoughts and settings.react_enable_verbose_logging:
            thought = getattr(response, "content", "")
            logger.info(f"[Writer ReAct Iteration {new_iteration}] Writing: {thought[:200]}...")

        return {
            "messages": [response],
            "iteration_count": new_iteration
        }

    async def reflect(state: WriterState) -> dict:
        """Reflection node: evaluates response quality and decides if refinement needed."""
        messages = state["messages"]

        # Get original query and current response
        original_query = messages[0].content if messages else ""
        current_response = messages[-1].content if messages else ""

        # Get refinement iteration count
        refinement_count = state.get("refinement_count", 0)

        # Perform reflection
        reflection_result = await reflect_on_response(
            query=original_query,
            response=current_response,
            agent_name="writer",
            llm=llm,
            iteration=refinement_count,
            config=reflection_config
        )

        # Store reflection result in state
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

    async def refine(state: WriterState) -> dict:
        """Refinement node: improves response based on reflection feedback."""
        messages = state["messages"]

        # Get original query and current response
        original_query = messages[0].content if messages else ""
        current_response = messages[-1].content if messages else ""

        # Get reflection feedback from state
        suggestions = state.get("reflection_suggestions", [])
        quality_score = state.get("reflection_score", 0.0)

        # Create mock reflection result for refinement prompt
        from utils.react_reflection import ReflectionResult
        reflection_result = ReflectionResult(
            decision=ReflectionDecision.REFINE,
            quality_score=quality_score,
            reasoning=state.get("react_history", [])[-1].get("reasoning", "Needs improvement"),
            suggestions=suggestions,
            should_continue=True
        )

        # Create refinement prompt
        refinement_prompt = create_refinement_prompt(
            original_query=original_query,
            current_response=current_response,
            reflection_result=reflection_result
        )

        # Add system message and refinement request
        refinement_messages = [
            SystemMessage(content=WRITER_SYSTEM_PROMPT),
            HumanMessage(content=refinement_prompt)
        ]

        # Get refined response
        refined_response = llm.invoke(refinement_messages)

        # Increment counters
        new_iteration = state.get("iteration_count", 0) + 1
        new_refinement_count = state.get("refinement_count", 0) + 1

        if settings.react_enable_verbose_logging:
            logger.info(f"[Writer Refinement {new_refinement_count}] Improving response based on feedback")

        return {
            "messages": [refined_response],
            "iteration_count": new_iteration,
            "refinement_count": new_refinement_count
        }

    def should_continue(state: WriterState) -> Literal["reflect", "end"]:
        """Decide if should reflect on response or end."""
        # Check manual stop
        if state.get("should_stop", False):
            reason = state.get("early_stop_reason", "Manual stop triggered")
            logger.warning(f"[Writer ReAct] Stopping early: {reason}")
            return "end"

        # Check timeout (FASE 2: use strategy timeout)
        start_time = state.get("start_time", time.time())
        elapsed = time.time() - start_time
        if elapsed > react_config.timeout_seconds:
            logger.warning(f"[Writer ReAct] Timeout exceeded: {elapsed:.1f}s")
            state["early_stop_reason"] = f"Timeout after {elapsed:.1f}s"
            return "end"

        # Check max iterations (FASE 2: use strategy max_iterations)
        iteration_count = state.get("iteration_count", 0)
        if iteration_count >= react_config.max_iterations:
            logger.warning(f"[Writer ReAct] Max iterations reached: {iteration_count}")
            state["early_stop_reason"] = f"Max iterations ({react_config.max_iterations}) reached"
            return "end"

        # FASE 3: If reflection enabled, go to reflection
        if reflection_config.enabled:
            return "reflect"

        if settings.react_enable_verbose_logging:
            logger.info(f"[Writer ReAct] Completed after {iteration_count} iteration(s)")

        return "end"

    def should_refine(state: WriterState) -> Literal["refine", "end"]:
        """Decide if should refine response based on reflection."""
        decision = state.get("reflection_decision", "accept")

        if decision == "refine":
            refinement_count = state.get("refinement_count", 0)
            if refinement_count < reflection_config.max_refinement_iterations:
                return "refine"
            else:
                logger.info(f"[Writer Reflection] Max refinements ({reflection_config.max_refinement_iterations}) reached, accepting response")
                return "end"

        # ACCEPT or INSUFFICIENT - end execution
        if settings.react_enable_verbose_logging:
            score = state.get("reflection_score", 0.0)
            iteration_count = state.get("iteration_count", 0)
            logger.info(f"[Writer ReAct] Completed after {iteration_count} iteration(s), quality score: {score:.2f}")

        return "end"

    workflow = StateGraph(WriterState)
    workflow.add_node("agent", call_model)
    workflow.add_node("reflect", reflect)  # FASE 3: reflection node
    workflow.add_node("refine", refine)    # FASE 3: refinement node

    workflow.set_entry_point("agent")

    # Edges from agent: check if should reflect or end
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "reflect": "reflect",
            "end": END
        }
    )

    # Edges from reflection: check if should refine or end
    workflow.add_conditional_edges(
        "reflect",
        should_refine,
        {
            "refine": "refine",
            "end": END
        }
    )

    # Edge from refinement: go back to reflection for re-evaluation
    workflow.add_edge("refine", "reflect")

    return workflow.compile()


_writer_agent = None

def get_writer_agent():
    """Get or create the writer agent instance."""
    global _writer_agent
    if _writer_agent is None:
        _writer_agent = create_writer_agent()
    return _writer_agent
