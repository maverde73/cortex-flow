"""
MCP Server Tester Utility

Provides comprehensive testing capabilities for MCP servers including:
- Connection and capabilities testing
- Resources discovery and reading
- Tools listing and execution
- Prompts listing and retrieval
- Completions testing
- Session management for stateful servers
"""

import asyncio
import httpx
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class MCPTestResult:
    """Result from an MCP test operation."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MCPServerTester:
    """
    Comprehensive tester for MCP servers.

    Supports testing all MCP protocol capabilities:
    - Initialize/Session management
    - Resources (list, read, templates)
    - Tools (list, call with structured output)
    - Prompts (list, get)
    - Completions
    - Logging and notifications
    """

    def __init__(self, server_config: Dict[str, Any], timeout: float = 30.0):
        """
        Initialize MCP server tester.

        Args:
            server_config: Server configuration dict with url, transport, api_key, etc.
            timeout: Timeout in seconds for HTTP requests
        """
        self.config = server_config
        self.timeout = timeout
        self.session_id: Optional[str] = None
        self.capabilities: Dict[str, Any] = {}
        self.server_info: Dict[str, Any] = {}

        # Transport configuration
        self.url = server_config.get("url", "")
        self.transport = server_config.get("transport", "streamable_http")
        self.api_key = server_config.get("api_key")

    def _get_headers(self, include_session: bool = True) -> Dict[str, str]:
        """Build HTTP headers for MCP requests."""
        headers = {}

        # Streamable HTTP requires specific Accept header
        if self.transport == "streamable_http":
            headers["Accept"] = "application/json, text/event-stream"

        # Bearer token authentication
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Session ID for stateful servers
        if include_session and self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        return headers

    def _parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Parse MCP response (supports both JSON and SSE formats).

        Args:
            response: HTTP response from MCP server

        Returns:
            Parsed response data
        """
        content_type = response.headers.get("content-type", "")

        if "text/event-stream" in content_type:
            # Parse SSE format: "event: message\ndata: {...}"
            text = response.text
            for line in text.split('\n'):
                if line.startswith('data: '):
                    json_str = line[6:]  # Remove 'data: ' prefix
                    return json.loads(json_str)
            # No data line found
            return {}
        else:
            # Standard JSON response
            return response.json()

    async def test_connection(self) -> MCPTestResult:
        """
        Test connection and initialize session.

        Returns:
            MCPTestResult with server info and capabilities
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._get_headers(include_session=False)

                # Send initialize request (required by MCP protocol)
                init_payload = {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "cortex-flow-tester",
                            "version": "1.0"
                        }
                    }
                }

                response = await client.post(
                    self.url,
                    json=init_payload,
                    headers=headers
                )
                response.raise_for_status()

                # Extract session ID from headers
                if "mcp-session-id" in response.headers:
                    self.session_id = response.headers["mcp-session-id"]
                    logger.debug(f"Initialized session: {self.session_id}")

                # Parse response
                data = self._parse_response(response)

                if "result" in data:
                    result = data["result"]
                    self.server_info = result.get("serverInfo", {})
                    self.capabilities = result.get("capabilities", {})

                    # Send initialized notification
                    if self.session_id:
                        headers["Mcp-Session-Id"] = self.session_id
                        await client.post(
                            self.url,
                            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                            headers=headers
                        )

                    return MCPTestResult(
                        success=True,
                        data={
                            "serverInfo": self.server_info,
                            "capabilities": self.capabilities,
                            "sessionId": self.session_id,
                            "protocolVersion": result.get("protocolVersion")
                        },
                        metadata={
                            "transport": self.transport,
                            "stateful": bool(self.session_id)
                        }
                    )
                else:
                    error_msg = data.get("error", {}).get("message", "Unknown error")
                    return MCPTestResult(
                        success=False,
                        error=f"Initialize failed: {error_msg}"
                    )

        except httpx.ConnectError as e:
            return MCPTestResult(
                success=False,
                error=f"Connection refused: {str(e)}"
            )
        except httpx.TimeoutException:
            return MCPTestResult(
                success=False,
                error="Connection timeout"
            )
        except Exception as e:
            logger.error(f"Connection test error: {e}", exc_info=True)
            return MCPTestResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )

    async def list_resources(self) -> MCPTestResult:
        """
        List available resources from the MCP server.

        Returns:
            MCPTestResult with list of resources
        """
        return await self._send_request(
            method="resources/list",
            request_id=10
        )

    async def read_resource(self, uri: str) -> MCPTestResult:
        """
        Read a specific resource.

        Args:
            uri: Resource URI to read

        Returns:
            MCPTestResult with resource contents
        """
        return await self._send_request(
            method="resources/read",
            params={"uri": uri},
            request_id=11
        )

    async def list_resource_templates(self) -> MCPTestResult:
        """
        List resource templates.

        Returns:
            MCPTestResult with list of resource templates
        """
        return await self._send_request(
            method="resources/templates/list",
            request_id=12
        )

    async def list_tools(self) -> MCPTestResult:
        """
        List available tools from the MCP server.

        Returns:
            MCPTestResult with list of tools
        """
        return await self._send_request(
            method="tools/list",
            request_id=20
        )

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPTestResult:
        """
        Call a tool with specific arguments.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as dict

        Returns:
            MCPTestResult with tool execution result (content + structured output)
        """
        return await self._send_request(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            },
            request_id=21
        )

    async def list_prompts(self) -> MCPTestResult:
        """
        List available prompts from the MCP server.

        Returns:
            MCPTestResult with list of prompts
        """
        return await self._send_request(
            method="prompts/list",
            request_id=30
        )

    async def get_prompt(self, prompt_name: str, arguments: Optional[Dict[str, str]] = None) -> MCPTestResult:
        """
        Get a specific prompt with arguments.

        Args:
            prompt_name: Name of the prompt to get
            arguments: Prompt arguments (optional)

        Returns:
            MCPTestResult with prompt messages
        """
        params = {"name": prompt_name}
        if arguments:
            params["arguments"] = arguments

        return await self._send_request(
            method="prompts/get",
            params=params,
            request_id=31
        )

    async def get_completions(
        self,
        ref: Dict[str, Any],
        argument: Dict[str, str]
    ) -> MCPTestResult:
        """
        Get argument completions.

        Args:
            ref: Reference to resource/prompt (e.g., {"type": "ref/resource", "uri": "..."})
            argument: Argument to complete (e.g., {"name": "path", "value": "/home/"})

        Returns:
            MCPTestResult with completion suggestions
        """
        return await self._send_request(
            method="completion/complete",
            params={
                "ref": ref,
                "argument": argument
            },
            request_id=40
        )

    async def reset_session(self) -> MCPTestResult:
        """
        Reset the current session (re-initialize).

        Returns:
            MCPTestResult from new connection test
        """
        self.session_id = None
        self.capabilities = {}
        self.server_info = {}

        return await self.test_connection()

    async def _send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        request_id: int = 1
    ) -> MCPTestResult:
        """
        Send a generic MCP JSON-RPC request.

        Args:
            method: MCP method name (e.g., "tools/list")
            params: Method parameters (optional)
            request_id: JSON-RPC request ID

        Returns:
            MCPTestResult with response data
        """
        try:
            # Ensure session is initialized
            if not self.session_id and self.transport == "streamable_http":
                conn_result = await self.test_connection()
                if not conn_result.success:
                    return conn_result

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._get_headers()

                # Build JSON-RPC request
                payload: Dict[str, Any] = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": method
                }

                if params:
                    payload["params"] = params

                logger.debug(f"Sending MCP request: {method}")
                response = await client.post(
                    self.url,
                    json=payload,
                    headers=headers
                )

                # Update session ID if changed
                if "mcp-session-id" in response.headers:
                    self.session_id = response.headers["mcp-session-id"]

                response.raise_for_status()

                # Parse response
                data = self._parse_response(response)

                if "result" in data:
                    return MCPTestResult(
                        success=True,
                        data=data["result"],
                        metadata={
                            "method": method,
                            "sessionId": self.session_id
                        }
                    )
                elif "error" in data:
                    error = data["error"]
                    return MCPTestResult(
                        success=False,
                        error=f"{error.get('message', 'Unknown error')} (code: {error.get('code', -1)})",
                        data=error
                    )
                else:
                    return MCPTestResult(
                        success=False,
                        error="Invalid response format",
                        data=data
                    )

        except httpx.HTTPStatusError as e:
            return MCPTestResult(
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            )
        except Exception as e:
            logger.error(f"Request error ({method}): {e}", exc_info=True)
            return MCPTestResult(
                success=False,
                error=f"Request failed: {str(e)}"
            )
