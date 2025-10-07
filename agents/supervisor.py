"""
Supervisor Agent

Orchestrates the multi-agent workflow by delegating tasks to specialized agents.
This is the entry point for all user requests.

The supervisor now dynamically loads tools based on available agents from the registry.
Supports conversation memory via checkpointer (MemorySaver or PostgreSQL).
"""

import time
from typing import Literal, Optional
import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from schemas.agent_state import SupervisorState
from utils.llm_factory import get_llm
from config_legacy import settings

logger = logging.getLogger(__name__)


# Dynamic prompt - will be populated by factory
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

BEST PRACTICES:
- Break complex tasks into clear, focused subtasks
- Delegate to specialists rather than doing everything yourself
- Pass context between agents when needed (e.g., research results to analyst)
- For reports: Research → Analyze → Write
- For quick questions: May only need one agent
- Always provide clear, specific instructions to each agent

EXAMPLE WORKFLOWS:

**Simple Query**:
User: "What is LangGraph?"
→ research_web("What is LangGraph framework")
→ Return the research results directly

**Report Generation**:
User: "Create a report on AI agent trends"
→ research_web("latest trends in AI agent frameworks 2025")
→ analyze_data(research_results)
→ write_content("Write a professional report on AI agent trends based on this analysis: {analysis}")
→ Return the final report

**Multi-Source Analysis**:
User: "Compare LangGraph vs CrewAI"
→ research_web("LangGraph framework features and use cases")
→ research_web("CrewAI framework features and use cases")
→ analyze_data(combined_research)
→ write_content("Write a comparison report: {analysis}")

Think step by step and use the appropriate tools to accomplish the task efficiently."""


def get_checkpointer() -> Optional[any]:
    """
    Get configured checkpointer for conversation memory.

    Returns:
        Checkpointer instance (MemorySaver, PostgresSaver, etc.) or None

    Supports:
    - memory: In-memory checkpointing (development/testing)
    - postgres: PostgreSQL persistence (production)
    - None: Disabled (stateless mode)
    """
    enable_memory = getattr(settings, 'enable_conversation_memory', True)

    if not enable_memory:
        logger.info("Conversation memory disabled - supervisor will be stateless")
        return None

    checkpointer_type = getattr(settings, 'checkpointer_type', 'memory')

    if checkpointer_type == 'memory':
        logger.info("Using MemorySaver for conversation memory")
        return MemorySaver()

    elif checkpointer_type == 'postgres':
        try:
            from langgraph.checkpoint.postgres import PostgresSaver

            postgres_url = getattr(settings, 'postgres_checkpoint_url', None)
            if not postgres_url:
                logger.warning(
                    "PostgreSQL checkpointer requested but POSTGRES_CHECKPOINT_URL not set. "
                    "Falling back to MemorySaver"
                )
                return MemorySaver()

            logger.info(f"Using PostgresSaver for conversation memory: {postgres_url}")
            return PostgresSaver.from_conn_string(postgres_url)

        except ImportError:
            logger.error(
                "PostgreSQL checkpointer requested but langgraph postgres extras not installed. "
                "Install with: pip install langgraph[postgres]. "
                "Falling back to MemorySaver"
            )
            return MemorySaver()
        except Exception as e:
            logger.error(f"Error initializing PostgreSQL checkpointer: {e}. Falling back to MemorySaver")
            return MemorySaver()

    else:
        logger.warning(f"Unknown checkpointer type: {checkpointer_type}. Using MemorySaver")
        return MemorySaver()


async def create_supervisor_agent_dynamic():
    """
    Creates the Supervisor agent graph with dynamic tool loading.

    Tools are loaded based on currently available agents from the registry.
    This allows graceful degradation when agents are offline.
    """
    from agents.factory import get_available_tools, create_dynamic_supervisor_prompt

    # Get tools and prompt section based on available agents
    tools, tools_section = await get_available_tools()
    dynamic_prompt = create_dynamic_supervisor_prompt(tools_section)

    logger.info(f"Creating supervisor with {len(tools)} available tools")

    # Initialize the LLM using the factory (FASE 2: now returns tuple with ReactConfig)
    llm, react_config = get_llm(agent="supervisor")

    logger.info(f"Supervisor initialized with {react_config}")

    # Bind dynamically loaded tools
    if tools:
        llm_with_tools = llm.bind_tools(tools)
    else:
        llm_with_tools = llm
        logger.warning("No tools available - supervisor running without delegation capabilities")

    def call_model(state: SupervisorState) -> dict:
        """Agent node: invokes the LLM to plan and delegate."""
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
        """Determines whether to continue delegating or finish."""
        messages = state["messages"]
        last_message = messages[-1]

        # Check 1: Manual stop flag
        if state.get("should_stop", False):
            reason = state.get("early_stop_reason", "Manual stop triggered")
            logger.warning(f"[Supervisor ReAct] Stopping early: {reason}")
            return "end"

        # Check 2: Timeout exceeded (FASE 2: use strategy timeout)
        start_time = state.get("start_time", time.time())
        elapsed = time.time() - start_time
        if elapsed > react_config.timeout_seconds:
            logger.warning(f"[Supervisor ReAct] Timeout exceeded: {elapsed:.1f}s")
            state["early_stop_reason"] = f"Timeout after {elapsed:.1f}s"
            return "end"

        # Check 3: Max iterations reached (FASE 2: use strategy max_iterations)
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

    # Wrapper for tool execution with error tracking
    async def execute_tools(state: SupervisorState) -> dict:
        """Execute tools (delegate to other agents) and track errors/observations."""
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

    # Build the graph
    workflow = StateGraph(SupervisorState)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", execute_tools)

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )

    workflow.add_edge("tools", "agent")

    # Get checkpointer for conversation memory
    checkpointer = get_checkpointer()

    if checkpointer:
        logger.info("Compiling supervisor with conversation memory enabled")
        return workflow.compile(checkpointer=checkpointer)
    else:
        logger.info("Compiling supervisor in stateless mode (no conversation memory)")
        return workflow.compile()


_supervisor_agent = None

async def get_supervisor_agent():
    """
    Get or create the supervisor agent instance.

    Note: This is now async to support dynamic tool loading from registry.
    """
    global _supervisor_agent
    if _supervisor_agent is None:
        logger.info("Initializing supervisor agent with dynamic tools...")
        _supervisor_agent = await create_supervisor_agent_dynamic()
    return _supervisor_agent


def reset_supervisor_agent():
    """
    Reset the supervisor agent instance.

    Call this to force recreation of the supervisor with updated tool availability.
    Useful when agents come online/offline.
    """
    global _supervisor_agent
    _supervisor_agent = None
    logger.info("Supervisor agent reset - will recreate on next get_supervisor_agent()")
