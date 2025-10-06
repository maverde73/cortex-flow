"""
MCP Client for External Server Communication

Provides client functionality to call MCP tools on remote and local servers.
Supports all MCP transport protocols and integrates with LangChain tools.
"""

import asyncio
import httpx
import logging
from typing import Any, Dict, Optional, Callable
from langchain_core.tools import tool as langchain_tool, StructuredTool
from pydantic import BaseModel, Field, create_model

from utils.mcp_registry import (
    get_mcp_registry,
    MCPTool,
    MCPServerConfig,
    MCPServerType,
    MCPTransportType
)

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for calling MCP tools on remote and local servers.

    Handles protocol-specific communication (Streamable HTTP, SSE, STDIO)
    and provides retry logic, error handling, and session management.
    """

    def __init__(self, retry_attempts: int = 3, timeout: float = 30.0):
        """
        Initialize MCP client.

        Args:
            retry_attempts: Number of retry attempts for failed requests
            timeout: Default timeout in seconds
        """
        self.retry_attempts = retry_attempts
        self.timeout = timeout
        self._registry = get_mcp_registry()

        # Session tracking for remote servers
        self._sessions: Dict[str, str] = {}  # server_name -> session_id

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_name: Optional[str] = None
    ) -> Any:
        """
        Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            server_name: Optional server name (if not provided, will lookup)

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool or server not found
            RuntimeError: If tool execution fails
        """
        # Get tool metadata
        tool = await self._registry.get_tool(tool_name)

        if tool is None:
            raise ValueError(f"MCP tool '{tool_name}' not found")

        # Get server config
        server = await self._registry.get_server_config(
            server_name or tool.server_name
        )

        if server is None:
            raise ValueError(f"MCP server not found for tool '{tool_name}'")

        if server.status != "healthy":
            raise RuntimeError(
                f"MCP server '{server.name}' is not healthy (status: {server.status})"
            )

        # Call tool based on server type
        if server.server_type == MCPServerType.REMOTE:
            return await self._call_remote_tool(server, tool_name, arguments)
        else:
            return await self._call_local_tool(server, tool_name, arguments)

    async def _call_remote_tool(
        self,
        server: MCPServerConfig,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Call tool on remote MCP server via HTTP."""
        last_error = None

        for attempt in range(self.retry_attempts):
            try:
                headers = server.headers.copy()

                # Streamable HTTP requires specific Accept header
                if server.transport == MCPTransportType.STREAMABLE_HTTP:
                    headers["Accept"] = "application/json, text/event-stream"

                if server.api_key:
                    headers["Authorization"] = f"Bearer {server.api_key}"

                async with httpx.AsyncClient(timeout=server.timeout) as client:
                    # For Streamable HTTP, initialize session if we don't have one
                    if (server.transport == MCPTransportType.STREAMABLE_HTTP and
                        server.name not in self._sessions):
                        # Send initialize request
                        init_payload = {
                            "jsonrpc": "2.0",
                            "id": 0,
                            "method": "initialize",
                            "params": {
                                "protocolVersion": "2025-03-26",
                                "capabilities": {},
                                "clientInfo": {
                                    "name": "cortex-flow-supervisor",
                                    "version": "1.0"
                                }
                            }
                        }

                        init_response = await client.post(
                            server.url,
                            json=init_payload,
                            headers=headers
                        )

                        if "mcp-session-id" in init_response.headers:
                            session_id = init_response.headers["mcp-session-id"]
                            self._sessions[server.name] = session_id
                            headers["mcp-session-id"] = session_id

                            # Send initialized notification
                            await client.post(
                                server.url,
                                json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                                headers=headers
                            )
                            logger.debug(f"Initialized MCP session for '{server.name}': {session_id}")

                    # Add session ID if we have one
                    if server.name in self._sessions:
                        headers["mcp-session-id"] = self._sessions[server.name]

                    logger.debug(
                        f"Calling MCP tool '{tool_name}' on '{server.name}' "
                        f"(attempt {attempt + 1}/{self.retry_attempts})"
                    )

                    # MCP protocol: send tools/call request
                    request_payload = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": arguments
                        }
                    }

                    response = await client.post(
                        server.url,
                        json=request_payload,
                        headers=headers
                    )

                    # Update session ID from response if present
                    if "mcp-session-id" in response.headers:
                        self._sessions[server.name] = response.headers["mcp-session-id"]

                    response.raise_for_status()

                    # For Streamable HTTP, response might be SSE format
                    if response.headers.get("content-type") == "text/event-stream":
                        # Parse SSE format: "event: message\ndata: {...}"
                        import json as json_module
                        text = response.text
                        # Extract JSON from SSE data line
                        for line in text.split('\n'):
                            if line.startswith('data: '):
                                json_str = line[6:]  # Remove 'data: ' prefix
                                data = json_module.loads(json_str)
                                break
                        else:
                            data = {}
                    else:
                        data = response.json()

                    # Parse MCP response
                    if "result" in data:
                        result = data["result"]

                        # MCP tools/call returns content array
                        if "content" in result and isinstance(result["content"], list):
                            # Concatenate text content
                            text_content = []
                            for content_item in result["content"]:
                                if content_item.get("type") == "text":
                                    text_content.append(content_item.get("text", ""))

                            return "\n".join(text_content) if text_content else result

                        return result

                    elif "error" in data:
                        error = data["error"]
                        error_msg = f"MCP error: {error.get('message', 'Unknown error')}"
                        logger.error(error_msg)
                        raise RuntimeError(error_msg)

                    else:
                        logger.warning(f"Unexpected MCP response format: {data}")
                        return data

            except httpx.ConnectError as e:
                last_error = e
                error_msg = f"MCP server '{server.name}' connection refused"

                if attempt < self.retry_attempts - 1:
                    wait_time = 2 ** attempt
                    logger.debug(f"{error_msg}, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"{error_msg} after {self.retry_attempts} attempts")
                    raise RuntimeError(error_msg) from e

            except httpx.TimeoutException as e:
                last_error = e
                error_msg = f"MCP server '{server.name}' timeout"

                if attempt < self.retry_attempts - 1:
                    logger.debug(f"{error_msg}, retrying...")
                    await asyncio.sleep(1)
                else:
                    logger.error(f"{error_msg} after {self.retry_attempts} attempts")
                    raise RuntimeError(error_msg) from e

            except httpx.HTTPStatusError as e:
                last_error = e
                status_code = e.response.status_code

                if status_code >= 500 and attempt < self.retry_attempts - 1:
                    logger.debug(f"MCP server error (HTTP {status_code}), retrying...")
                    await asyncio.sleep(1)
                    continue
                else:
                    error_msg = f"MCP server returned HTTP {status_code}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg) from e

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error calling MCP tool '{tool_name}': {e}")
                raise RuntimeError(f"MCP tool call failed: {str(e)}") from e

        # Should not reach here
        raise RuntimeError(
            f"Failed to call MCP tool '{tool_name}' after {self.retry_attempts} attempts: "
            f"{str(last_error)}"
        )

    async def _call_local_tool(
        self,
        server: MCPServerConfig,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Call tool on local MCP server module."""
        try:
            # Get the loaded module
            registry = get_mcp_registry()
            module = registry._loaded_modules.get(server.name)

            if module is None:
                raise RuntimeError(f"Local MCP module '{server.name}' not loaded")

            # Get FastMCP instance
            mcp_instance = None
            if hasattr(module, 'mcp'):
                mcp_instance = module.mcp
            elif hasattr(module, 'app'):
                mcp_instance = module.app

            if mcp_instance is None:
                raise RuntimeError(f"No MCP instance found in module '{server.name}'")

            # Get the tool function
            if hasattr(mcp_instance, '_tools') and tool_name in mcp_instance._tools:
                tool_obj = mcp_instance._tools[tool_name]

                # Call the tool function
                # FastMCP tools are typically async
                if asyncio.iscoroutinefunction(tool_obj):
                    result = await tool_obj(**arguments)
                else:
                    result = tool_obj(**arguments)

                return result

            else:
                raise ValueError(f"Tool '{tool_name}' not found in local server '{server.name}'")

        except Exception as e:
            logger.error(f"Error calling local MCP tool '{tool_name}': {e}")
            raise RuntimeError(f"Local MCP tool call failed: {str(e)}") from e


async def _get_tool_prompt(mcp_tool: MCPTool) -> Optional[str]:
    """
    Get the MCP prompt associated with a tool, if available.

    Args:
        mcp_tool: MCP tool metadata

    Returns:
        Prompt text or None if no prompt is associated
    """
    try:
        registry = get_mcp_registry()

        # Check if tool has associated_prompt
        if mcp_tool.associated_prompt:
            prompt = await registry.get_prompt(mcp_tool.associated_prompt)
            if prompt and prompt.description:
                return prompt.description

        # Fallback: Try to find prompt with same name as tool
        prompt = await registry.get_prompt(mcp_tool.name)
        if prompt and prompt.description:
            return prompt.description

        # No prompt found
        return None

    except Exception as e:
        logger.debug(f"Error retrieving prompt for tool '{mcp_tool.name}': {e}")
        return None


def create_langchain_tool_from_mcp(mcp_tool: MCPTool, client: MCPClient) -> StructuredTool:
    """
    Convert an MCP tool to a LangChain StructuredTool.

    This allows MCP tools to be used seamlessly with LangChain agents
    and integrated into the ReAct pattern.

    The tool description will be enhanced with MCP prompt guidance if available.

    Args:
        mcp_tool: MCP tool metadata
        client: MCP client for executing the tool

    Returns:
        LangChain StructuredTool ready to use
    """
    # Create Pydantic model from input schema
    input_schema = mcp_tool.input_schema

    # Extract properties and required fields
    properties = input_schema.get("properties", {})
    required = input_schema.get("required", [])

    # Build field definitions for Pydantic model
    field_definitions = {}
    for field_name, field_info in properties.items():
        field_type = _json_schema_type_to_python(field_info.get("type", "string"))
        field_description = field_info.get("description", "")
        is_required = field_name in required

        if is_required:
            field_definitions[field_name] = (
                field_type,
                Field(..., description=field_description)
            )
        else:
            field_definitions[field_name] = (
                Optional[field_type],
                Field(None, description=field_description)
            )

    # Create dynamic Pydantic model for input validation
    InputModel = create_model(
        f"{mcp_tool.name.capitalize()}Input",
        **field_definitions
    )

    # Create the tool function
    async def tool_func(**kwargs) -> str:
        """Dynamically created tool function for MCP tool."""
        try:
            result = await client.call_tool(
                tool_name=mcp_tool.name,
                arguments=kwargs,
                server_name=mcp_tool.server_name
            )

            # Convert result to string for LangChain
            if isinstance(result, str):
                return result
            else:
                return str(result)

        except Exception as e:
            logger.error(f"Error executing MCP tool '{mcp_tool.name}': {e}")
            return f"❌ Error executing MCP tool: {str(e)}"

    # Create StructuredTool
    langchain_tool = StructuredTool(
        name=mcp_tool.name,
        description=mcp_tool.description,
        func=tool_func,
        coroutine=tool_func,  # Support async
        args_schema=InputModel
    )

    return langchain_tool


def _json_schema_type_to_python(json_type: str) -> type:
    """Convert JSON Schema type to Python type."""
    type_mapping = {
        "string": str,
        "number": float,
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None)
    }

    return type_mapping.get(json_type, str)


async def get_mcp_langchain_tools() -> list:
    """
    Get all available MCP tools as LangChain tools.

    This function is called by the agent factory to integrate MCP tools
    into the supervisor's tool set.

    Tool descriptions will be enhanced with MCP prompts if available.

    Returns:
        List of LangChain StructuredTool objects
    """
    registry = get_mcp_registry()
    client = MCPClient()

    # Get all available MCP tools
    mcp_tools = await registry.get_available_tools()

    # Convert to LangChain tools with prompt enhancement
    langchain_tools = []

    for mcp_tool in mcp_tools:
        try:
            # Get associated prompt if available
            prompt_text = await _get_tool_prompt(mcp_tool)

            # Enhance tool description with prompt
            if prompt_text:
                original_description = mcp_tool.description
                mcp_tool.description = f"{original_description}\n\n## Usage Guide\n{prompt_text}"
                logger.debug(f"Enhanced '{mcp_tool.name}' description with MCP prompt")

            lc_tool = create_langchain_tool_from_mcp(mcp_tool, client)
            langchain_tools.append(lc_tool)
            logger.debug(f"Created LangChain tool for MCP tool '{mcp_tool.name}'")
        except Exception as e:
            logger.error(
                f"Error converting MCP tool '{mcp_tool.name}' to LangChain tool: {e}"
            )

    logger.info(f"Loaded {len(langchain_tools)} MCP tools as LangChain tools")

    return langchain_tools
