"""
Agent Factory

Dynamically creates agents with tools based on service registry.
Ensures only available agents are included in tool binding.
"""

import logging
from typing import List
from langchain_core.tools import BaseTool

from services.registry import get_registry
from config import settings

logger = logging.getLogger(__name__)


async def get_available_tools() -> tuple[List[BaseTool], str]:
    """
    Get list of proxy tools for currently available agents and MCP tools.

    Returns:
        Tuple of (tools list, updated system prompt)
    """
    registry = get_registry()
    available_agents = await registry.get_available_agents()

    tools = []
    tool_descriptions = []

    # Import tools dynamically based on availability
    from tools import proxy_tools

    # Researcher tool
    if "researcher" in available_agents:
        tools.append(proxy_tools.research_web)
        tool_descriptions.append(
            "1. **research_web**: Web Researcher - finds up-to-date information from the internet"
        )

    # Analyst tool
    if "analyst" in available_agents:
        tools.append(proxy_tools.analyze_data)
        tool_descriptions.append(
            "2. **analyze_data**: Analyst - analyzes and synthesizes information, extracts insights"
        )

    # Writer tool
    if "writer" in available_agents:
        tools.append(proxy_tools.write_content)
        tool_descriptions.append(
            "3. **write_content**: Writer - creates professional, well-structured written content"
        )

    # Log available core tools
    logger.info(
        f"Loaded {len(tools)} core agent tools: {available_agents}"
    )

    # Add MCP tools if MCP integration is enabled
    if settings.mcp_enable:
        try:
            from utils.mcp_client import get_mcp_langchain_tools

            mcp_tools = await get_mcp_langchain_tools()

            if mcp_tools:
                # Add MCP tools to the list
                tools.extend(mcp_tools)

                # Add MCP tools to descriptions
                tool_descriptions.append("\n**MCP TOOLS (External):**")
                for idx, mcp_tool in enumerate(mcp_tools, start=len(tool_descriptions)):
                    tool_descriptions.append(
                        f"{idx}. **{mcp_tool.name}**: {mcp_tool.description}"
                    )

                logger.info(
                    f"Loaded {len(mcp_tools)} MCP tools from external servers"
                )
        except Exception as e:
            logger.error(f"Error loading MCP tools: {e}")
            # Continue without MCP tools

    # Generate dynamic system prompt section
    if tool_descriptions:
        tools_section = "AVAILABLE AGENTS (via tools):\n" + "\n".join(tool_descriptions)
    else:
        tools_section = "⚠️ WARNING: No specialized agents are currently available.\nYou can still respond to queries based on your own knowledge, but cannot delegate tasks."

    logger.info(f"Total tools available: {len(tools)}")

    return tools, tools_section


def create_dynamic_supervisor_prompt(tools_section: str) -> str:
    """
    Create supervisor system prompt with dynamic tools list.

    Args:
        tools_section: String describing available tools

    Returns:
        Complete system prompt
    """
    return f"""You are the Supervisor Agent, orchestrating a team of specialized AI agents.

YOUR ROLE:
You coordinate multiple specialized agents to solve complex tasks that require different types of expertise.

{tools_section}

WORKFLOW STRATEGY:
1. **Understand** the user's request completely
2. **Plan** the sequence of steps needed
3. **Delegate** each step to the appropriate specialist agent (if available)
4. **Synthesize** results from multiple agents if needed
5. **Deliver** a comprehensive final response

BEST PRACTICES:
- Break complex tasks into clear, focused subtasks
- Delegate to specialists when they are available
- If an agent is unavailable, inform the user or use your own knowledge as fallback
- Pass context between agents when needed (e.g., research results to analyst)
- For reports: Research → Analyze → Write (if all agents available)
- For quick questions: May only need one agent or direct response
- Always provide clear, specific instructions to each agent

HANDLING UNAVAILABLE AGENTS:
- If a needed agent is unavailable, inform the user
- Provide the best answer you can with available resources
- Suggest trying again later if the task specifically requires that agent

EXAMPLE WORKFLOWS:

**Simple Query** (researcher available):
User: "What is LangGraph?"
→ research_web("What is LangGraph framework")
→ Return the research results directly

**Report Generation** (all agents available):
User: "Create a report on AI agent trends"
→ research_web("latest trends in AI agent frameworks 2025")
→ analyze_data(research_results)
→ write_content("Write a professional report on AI agent trends based on this analysis: {{analysis}}")
→ Return the final report

**Graceful Degradation** (some agents unavailable):
User: "Create a report on AI trends"
If writer is unavailable:
→ research_web("AI trends")
→ analyze_data(results)
→ "I've gathered and analyzed the information, but the Writer agent is currently unavailable. Here's the analysis: ..."

Think step by step and use the appropriate tools to accomplish the task efficiently."""
