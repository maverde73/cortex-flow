"""
Proxy Tools for cross-server agent communication.

These tools allow the supervisor agent to delegate tasks to specialized agents
running on different servers via HTTP using the MCP protocol.
"""

import httpx
import asyncio
import logging
from langchain_core.tools import tool
from typing import Optional
from uuid import uuid4

from schemas.mcp_protocol import MCPRequest, MCPResponse
from config import settings

logger = logging.getLogger(__name__)


async def _call_agent_async(
    agent_url: str,
    agent_id: str,
    task_description: str,
    context: dict = None,
    retry_attempts: Optional[int] = None
) -> str:
    """
    Internal helper function to make async HTTP calls to agent servers with retry logic.

    Args:
        agent_url: Full URL of the agent server (e.g., http://localhost:8001)
        agent_id: Identifier of the target agent
        task_description: The task to be performed
        context: Additional context for the task
        retry_attempts: Number of retry attempts (defaults to settings value)

    Returns:
        The agent's response or user-friendly error message
    """
    if retry_attempts is None:
        retry_attempts = settings.agent_retry_attempts

    request = MCPRequest(
        task_id=str(uuid4()),
        source_agent_id="supervisor",
        target_agent_id=agent_id,
        task_description=task_description,
        context=context or {}
    )

    last_error = None

    for attempt in range(retry_attempts):
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
                logger.debug(
                    f"Calling {agent_id} (attempt {attempt + 1}/{retry_attempts})"
                )

                response = await client.post(
                    f"{agent_url}/invoke",
                    json=request.model_dump(mode='json'),
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()

                mcp_response = MCPResponse(**response.json())

                if mcp_response.status == "success":
                    logger.info(f"Successfully called {agent_id}")
                    return mcp_response.result or "No result returned"
                else:
                    error_msg = f"❌ {agent_id.capitalize()} agent returned an error: {mcp_response.error_message}"
                    logger.warning(error_msg)
                    return error_msg

        except httpx.ConnectError as e:
            last_error = e
            error_msg = f"⚠️ The {agent_id.capitalize()} agent is currently unavailable (connection refused)."

            if attempt < retry_attempts - 1:
                # Exponential backoff: 1s, 2s, 4s, ...
                wait_time = 2 ** attempt
                logger.debug(
                    f"{agent_id} unavailable, retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"{agent_id} unavailable after {retry_attempts} attempts")
                return (
                    f"{error_msg}\n\n"
                    f"💡 Please ensure the {agent_id} service is running and try again. "
                    f"If the problem persists, check the service logs."
                )

        except httpx.TimeoutException:
            last_error = "timeout"
            error_msg = f"⏱️ Request to {agent_id.capitalize()} agent timed out after {settings.http_timeout}s."

            if attempt < retry_attempts - 1:
                logger.debug(f"{agent_id} timeout, retrying...")
                await asyncio.sleep(1)
            else:
                logger.error(f"{agent_id} timeout after {retry_attempts} attempts")
                return (
                    f"{error_msg}\n\n"
                    f"💡 The agent may be processing a complex task. "
                    f"Try again or simplify your request."
                )

        except httpx.HTTPStatusError as e:
            last_error = e
            status_code = e.response.status_code

            error_msg = f"❌ {agent_id.capitalize()} agent returned HTTP {status_code}"

            if status_code >= 500:
                if attempt < retry_attempts - 1:
                    logger.debug(f"{agent_id} server error, retrying...")
                    await asyncio.sleep(1)
                    continue
                else:
                    return (
                        f"{error_msg}\n\n"
                        f"💡 The agent is experiencing server issues. "
                        f"Please try again later."
                    )
            else:
                # Client errors (4xx) - don't retry
                return (
                    f"{error_msg}\n\n"
                    f"💡 There may be an issue with the request format. "
                    f"Check the logs for more details."
                )

        except Exception as e:
            last_error = e
            logger.error(f"Unexpected error calling {agent_id}: {e}")
            return (
                f"❌ Unexpected error communicating with {agent_id.capitalize()} agent: {str(e)}\n\n"
                f"💡 This is likely a system issue. Check the logs for more information."
            )

    # Should not reach here, but handle gracefully
    return (
        f"❌ Failed to communicate with {agent_id.capitalize()} agent after {retry_attempts} attempts.\n\n"
        f"Last error: {str(last_error)}"
    )


@tool
async def research_web(query: str) -> str:
    """
    Delegate a web research task to the specialized Web Researcher agent.

    Use this tool when you need to find up-to-date information from the internet,
    such as news, articles, blog posts, or any recent developments.

    Args:
        query: The research query or topic to search for

    Returns:
        Research results with sources and summaries
    """
    return await _call_agent_async(
        agent_url=settings.researcher_url,
        agent_id="researcher",
        task_description=query
    )


@tool
async def analyze_data(data: str) -> str:
    """
    Delegate data analysis to the specialized Analyst agent.

    Use this tool when you have gathered information that needs to be:
    - Analyzed for patterns and trends
    - Synthesized into key insights
    - Organized and structured
    - Evaluated for relevance

    Args:
        data: The raw data or information to be analyzed

    Returns:
        Structured analysis with key findings and insights
    """
    task = f"Analyze the following information and extract key insights:\n\n{data}"

    return await _call_agent_async(
        agent_url=settings.analyst_url,
        agent_id="analyst",
        task_description=task
    )


@tool
async def write_content(instructions: str) -> str:
    """
    Delegate content writing to the specialized Writer agent.

    Use this tool when you need to create well-structured written content such as:
    - Reports
    - Articles
    - Summaries
    - Documentation

    Args:
        instructions: Instructions for what to write, including content and style preferences

    Returns:
        Professional, well-structured written content
    """
    return await _call_agent_async(
        agent_url=settings.writer_url,
        agent_id="writer",
        task_description=instructions
    )


# Additional proxy tools can be added here for other specialized agents
# For example:
# - reddit_search_proxy
# - database_query_proxy
# - code_analysis_proxy
# etc.
