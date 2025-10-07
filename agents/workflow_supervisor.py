"""
Workflow-Enabled Supervisor

Enhanced supervisor with dual-mode execution:
- ReAct Mode: Autonomous decision-making (original behavior)
- Workflow Mode: Template-based predefined workflows
- Hybrid Mode: Auto-detect template or use ReAct

Integrates with WorkflowEngine for template execution.
"""

import time
import logging
from typing import Literal, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from schemas.agent_state import SupervisorState
from utils.llm_factory import get_llm
from config_legacy import settings
from workflows.registry import get_workflow_registry
from workflows.engine import WorkflowEngine

logger = logging.getLogger(__name__)


# System prompt (same as original supervisor)
SUPERVISOR_SYSTEM_PROMPT_BASE = """You are the Supervisor Agent, orchestrating a team of specialized AI agents.

YOUR ROLE:
You coordinate multiple specialized agents to solve complex tasks that require different types of expertise.

AVAILABLE AGENTS (via tools):
1. **research_web**: Web Researcher - finds up-to-date information from the internet
2. **analyze_data**: Analyst - analyzes and synthesizes information, extracts insights
3. **write_content**: Writer - creates professional, well-structured written content

WORKFLOW STRATEGY:
1. **Understand** the user's request completely
2. **Plan** the sequence of steps needed
3. **Delegate** each step to the appropriate specialist agent
4. **Synthesize** results from multiple agents if needed
5. **Deliver** a comprehensive final response

Think step by step and use the appropriate tools to accomplish the task efficiently."""


async def create_workflow_supervisor():
    """
    Create workflow-enabled supervisor with dual-mode execution.

    Returns:
        Compiled LangGraph with workflow support
    """
    from agents.factory import get_available_tools, create_dynamic_supervisor_prompt

    # Get tools and prompt
    tools, tools_section = await get_available_tools()
    dynamic_prompt = create_dynamic_supervisor_prompt(tools_section)

    # Initialize LLM
    llm, react_config = get_llm(agent="supervisor")

    # Initialize workflow components
    workflow_registry = get_workflow_registry(settings.workflow_templates_dir)

    # Initialize engine with LangGraph mode (default)
    # Can be overridden with WORKFLOW_ENGINE_MODE=custom in config
    engine_mode = getattr(settings, 'workflow_engine_mode', 'langgraph')
    workflow_engine = WorkflowEngine(mode=engine_mode)

    # Load templates
    if settings.workflow_enable:
        template_count = workflow_registry.load_templates()
        logger.info(
            f"Workflow system enabled: {template_count} templates loaded, "
            f"mode={settings.workflow_mode}, engine={engine_mode}"
        )

    # Bind tools
    llm_with_tools = llm.bind_tools(tools) if tools else llm

    # =====================================================================
    # WORKFLOW MODE NODES
    # =====================================================================

    async def workflow_executor(state: SupervisorState) -> Dict[str, Any]:
        """
        Execute workflow template.

        Args:
            state: Current state with workflow_template specified

        Returns:
            State update with workflow results
        """
        template_name = state.get("workflow_template")
        if not template_name:
            logger.error("workflow_executor called without template_name")
            return {"messages": [AIMessage(content="Error: No workflow template specified")]}

        template = workflow_registry.get(template_name)
        if not template:
            logger.error(f"Template '{template_name}' not found")
            return {"messages": [AIMessage(content=f"Error: Template '{template_name}' not found")]}

        # Get user input
        user_message = state["messages"][0]
        user_input = user_message.content if hasattr(user_message, "content") else str(user_message)

        # Get parameters
        params = state.get("workflow_params", {})

        logger.info(
            f"🎯 Executing workflow template '{template_name}' "
            f"with params: {params}"
        )

        try:
            # Execute workflow
            result = await workflow_engine.execute_workflow(
                template=template,
                user_input=user_input,
                params=params
            )

            if result.success:
                logger.info(
                    f"✅ Workflow '{template_name}' completed successfully "
                    f"in {result.total_execution_time:.2f}s"
                )

                # Return final output as AI message
                return {
                    "messages": [AIMessage(content=result.final_output)],
                    "workflow_history": result.execution_log,
                    "workflow_name": template_name
                }
            else:
                logger.error(f"❌ Workflow '{template_name}' failed: {result.error}")

                if settings.workflow_fallback_to_react:
                    logger.info("Falling back to ReAct mode...")
                    # Clear workflow template to trigger ReAct
                    return {
                        "workflow_template": None,
                        "messages": []  # Will be reprocessed in ReAct mode
                    }
                else:
                    return {
                        "messages": [AIMessage(
                            content=f"Workflow execution failed: {result.error}"
                        )]
                    }

        except Exception as e:
            logger.error(f"Workflow execution error: {e}", exc_info=True)

            if settings.workflow_fallback_to_react:
                logger.info("Falling back to ReAct mode...")
                return {
                    "workflow_template": None,
                    "messages": []
                }
            else:
                return {
                    "messages": [AIMessage(
                        content=f"Workflow execution error: {str(e)}"
                    )]
                }

    # =====================================================================
    # REACT MODE NODES (original supervisor logic)
    # =====================================================================

    def call_model(state: SupervisorState) -> dict:
        """Agent node: invokes the LLM to plan and delegate (ReAct mode)"""
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
            messages = [SystemMessage(content=dynamic_prompt)] + list(messages)

        response = llm_with_tools.invoke(messages)

        # Increment iteration counter
        new_iteration = state.get("iteration_count", 0) + 1

        # Log thought if verbose logging enabled
        if settings.react_log_thoughts and settings.react_enable_verbose_logging:
            thought = getattr(response, "content", "")
            logger.info(f"[Supervisor ReAct Iteration {new_iteration}] Planning: {thought[:200]}...")

        return {
            "messages": [response],
            "iteration_count": new_iteration
        }

    def should_continue(state: SupervisorState) -> Literal["tools", "end"]:
        """Determines whether to continue delegating or finish (ReAct mode)"""
        messages = state["messages"]
        last_message = messages[-1]

        # Check 1: Manual stop flag
        if state.get("should_stop", False):
            reason = state.get("early_stop_reason", "Manual stop triggered")
            logger.warning(f"[Supervisor ReAct] Stopping early: {reason}")
            return "end"

        # Check 2: Timeout exceeded
        start_time = state.get("start_time", time.time())
        elapsed = time.time() - start_time
        if elapsed > react_config.timeout_seconds:
            logger.warning(f"[Supervisor ReAct] Timeout exceeded: {elapsed:.1f}s")
            state["early_stop_reason"] = f"Timeout after {elapsed:.1f}s"
            return "end"

        # Check 3: Max iterations reached
        iteration_count = state.get("iteration_count", 0)
        if iteration_count >= react_config.max_iterations:
            logger.warning(f"[Supervisor ReAct] Max iterations reached: {iteration_count}")
            state["early_stop_reason"] = f"Max iterations ({react_config.max_iterations}) reached"
            return "end"

        # Check 4: Max consecutive errors
        error_count = state.get("error_count", 0)
        if error_count >= settings.react_max_consecutive_errors:
            logger.error(f"[Supervisor ReAct] Max consecutive errors reached: {error_count}")
            state["early_stop_reason"] = f"Too many consecutive errors ({error_count})"
            return "end"

        # Check 5: Normal ReAct flow - check for tool calls
        if hasattr(last_message, "tool_calls") and getattr(last_message, "tool_calls", None):
            # Log action if enabled
            if settings.react_log_actions and settings.react_enable_verbose_logging:
                tool_calls = last_message.tool_calls
                for tc in tool_calls:
                    tool_name = tc.get('name', 'unknown')
                    # Check if this is an MCP tool
                    is_mcp_tool = not any(
                        agent_tool in tool_name
                        for agent_tool in ['research_web', 'analyze_data', 'write_content']
                    )
                    tool_type = "MCP Tool" if is_mcp_tool and settings.mcp_enable else "Agent Tool"

                    if settings.mcp_tools_enable_logging or not is_mcp_tool:
                        logger.info(
                            f"[Supervisor ReAct Iteration {iteration_count}] "
                            f"Delegating to {tool_type}: {tool_name}"
                        )
            return "tools"

        # No tool calls and no stop conditions = final answer reached
        if settings.react_enable_verbose_logging:
            logger.info(f"[Supervisor ReAct] Completed successfully after {iteration_count} iterations")

        return "end"

    async def execute_tools(state: SupervisorState) -> dict:
        """Execute tools (delegate to other agents) and track errors (ReAct mode)"""
        tool_node = ToolNode(tools)

        try:
            # Execute the tool (delegation) - use ainvoke for async tools
            result = await tool_node.ainvoke(state)

            # Reset error count on successful execution
            new_error_count = 0

            # Log observation if enabled
            if settings.react_log_observations and settings.react_enable_verbose_logging:
                messages = result.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    observation = getattr(last_msg, "content", "")
                    iteration = state.get("iteration_count", 0)
                    logger.info(
                        f"[Supervisor ReAct Iteration {iteration}] Received: {observation[:200]}..."
                    )

            # Update react_history if logging enabled
            if settings.react_enable_verbose_logging:
                messages = result.get("messages", [])
                history_entry = {
                    "iteration": state.get("iteration_count", 0),
                    "timestamp": time.time(),
                    "action": "agent_delegation",
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
                f"[Supervisor ReAct] Agent delegation error (#{new_error_count}): {str(e)}"
            )

            # Create error message to add to state
            error_msg = AIMessage(
                content=f"Agent delegation failed: {str(e)}. Error count: {new_error_count}"
            )

            return {
                "messages": [error_msg],
                "error_count": new_error_count
            }

    # =====================================================================
    # ROUTING NODE
    # =====================================================================

    async def route_execution(state: SupervisorState) -> Literal["workflow_mode", "react_mode"]:
        """
        Decide execution mode: workflow or ReAct.

        Priority:
        1. Explicit workflow_template → workflow mode
        2. Auto-classify (if enabled) → workflow mode if matched
        3. Fallback → ReAct mode
        """
        # Check if workflow explicitly specified
        if state.get("workflow_template"):
            logger.info(f"Using explicit workflow: {state['workflow_template']}")
            return "workflow_mode"

        # Check workflow mode setting
        mode = state.get("workflow_mode", settings.workflow_mode)

        if mode == "template":
            # Always use template (must be specified)
            if not state.get("workflow_template"):
                logger.warning("Template mode but no template specified, falling back to ReAct")
                return "react_mode"
            return "workflow_mode"

        elif mode == "react":
            # Always use ReAct
            return "react_mode"

        elif mode == "hybrid" or mode == "auto":
            # Auto-detect template from user input
            if settings.workflow_auto_classify and settings.workflow_enable:
                user_message = state["messages"][0]
                user_input = user_message.content if hasattr(user_message, "content") else str(user_message)

                template = await workflow_registry.match_template(user_input)
                if template:
                    logger.info(f"Auto-matched workflow: {template.name}")
                    state["workflow_template"] = template.name
                    return "workflow_mode"

            # No template matched, use ReAct
            logger.info("No workflow matched, using ReAct mode")
            return "react_mode"

        else:
            logger.warning(f"Unknown workflow mode: {mode}, using ReAct")
            return "react_mode"

    # =====================================================================
    # BUILD GRAPH
    # =====================================================================

    workflow = StateGraph(SupervisorState)

    # Add nodes
    workflow.add_node("router", lambda s: s)  # Pass-through for routing
    workflow.add_node("workflow_executor", workflow_executor)
    workflow.add_node("react_agent", call_model)
    workflow.add_node("tools", execute_tools)

    # Set entry point
    workflow.set_entry_point("router")

    # Routing from entry
    workflow.add_conditional_edges(
        "router",
        route_execution,
        {
            "workflow_mode": "workflow_executor",
            "react_mode": "react_agent"
        }
    )

    # Workflow mode ends after execution
    workflow.add_edge("workflow_executor", END)

    # ReAct mode flow (same as original)
    workflow.add_conditional_edges(
        "react_agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    workflow.add_edge("tools", "react_agent")

    return workflow.compile()


# Singleton instance
_workflow_supervisor = None


async def get_workflow_supervisor():
    """Get or create workflow supervisor instance"""
    global _workflow_supervisor
    if _workflow_supervisor is None:
        logger.info("Initializing workflow-enabled supervisor...")
        _workflow_supervisor = await create_workflow_supervisor()
    return _workflow_supervisor


def reset_workflow_supervisor():
    """Reset supervisor instance"""
    global _workflow_supervisor
    _workflow_supervisor = None
    logger.info("Workflow supervisor reset")
