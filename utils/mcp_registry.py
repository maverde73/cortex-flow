"""
MCP Server Registry and Tool Discovery

Manages external and local MCP servers, providing dynamic tool discovery
and integration with the Cortex Flow agent system.

Supports all MCP transport protocols:
- Streamable HTTP (recommended for production)
- SSE (Server-Sent Events)
- STDIO (local processes)
"""

import asyncio
import httpx
import logging
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import importlib.util
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class MCPTransportType(str, Enum):
    """Supported MCP transport protocols."""
    STREAMABLE_HTTP = "streamable_http"  # HTTP with streaming support (recommended)
    SSE = "sse"  # Server-Sent Events
    STDIO = "stdio"  # Standard I/O (local process)


class MCPServerType(str, Enum):
    """Type of MCP server integration."""
    REMOTE = "remote"  # External MCP server via HTTP
    LOCAL = "local"  # Local Python module with FastMCP


@dataclass
class MCPServerConfig:
    """
    Configuration for an MCP server.

    Examples:
        # Remote server with Streamable HTTP
        MCPServerConfig(
            name="corporate",
            server_type=MCPServerType.REMOTE,
            transport=MCPTransportType.STREAMABLE_HTTP,
            url="http://localhost:8001/mcp",
            api_key="secret123"
        )

        # Local server from Python file
        MCPServerConfig(
            name="local_tools",
            server_type=MCPServerType.LOCAL,
            transport=MCPTransportType.STDIO,
            local_path="/path/to/mcp_server.py"
        )
    """
    name: str
    server_type: MCPServerType
    transport: MCPTransportType

    # Remote server configuration
    url: Optional[str] = None
    api_key: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)

    # Local server configuration
    local_path: Optional[str] = None
    module_name: Optional[str] = None

    # Common settings
    enabled: bool = True
    timeout: float = 30.0
    health_check_interval: int = 60

    # Manual prompts configuration
    prompts_file: Optional[str] = None  # Path to markdown file with prompts
    prompt_tool_association: Optional[str] = None  # Tool name to associate with the prompt

    # Metadata
    status: str = "unknown"  # unknown, healthy, unhealthy, disabled
    last_check: Optional[datetime] = None
    tool_count: int = 0

    def __post_init__(self):
        """Validate configuration."""
        if self.server_type == MCPServerType.REMOTE:
            if not self.url:
                raise ValueError(f"Remote MCP server '{self.name}' requires 'url'")
            if self.transport not in [MCPTransportType.STREAMABLE_HTTP, MCPTransportType.SSE]:
                raise ValueError(
                    f"Remote servers only support streamable_http or sse transport, "
                    f"got: {self.transport}"
                )

        elif self.server_type == MCPServerType.LOCAL:
            if not self.local_path:
                raise ValueError(f"Local MCP server '{self.name}' requires 'local_path'")
            if not Path(self.local_path).exists():
                logger.warning(f"Local path does not exist: {self.local_path}")


@dataclass
class MCPPromptArgument:
    """
    Argument specification for an MCP prompt.
    """
    name: str
    description: str
    required: bool = True


@dataclass
class MCPPrompt:
    """
    MCP prompt metadata.

    Represents a prompt template exposed by an MCP server.
    Prompts provide guidance on how to use MCP tools effectively.
    """
    name: str
    description: str
    arguments: List[MCPPromptArgument]
    server_name: str  # Which MCP server provides this prompt

    # Optional metadata
    content: Optional[str] = None  # Full prompt text/template


@dataclass
class MCPTool:
    """
    MCP tool metadata.

    Represents a tool exposed by an MCP server.
    """
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str  # Which MCP server provides this tool

    # Optional metadata
    examples: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    associated_prompt: Optional[str] = None  # Name of associated MCP prompt


class MCPToolRegistry:
    """
    Central registry for MCP servers and their tools.

    Manages both remote and local MCP servers, performs tool discovery,
    and provides integration with LangChain tools for the agent system.
    """

    def __init__(self, health_check_timeout: float = 5.0):
        """
        Initialize MCP tool registry.

        Args:
            health_check_timeout: Timeout for health checks in seconds
        """
        self._servers: Dict[str, MCPServerConfig] = {}
        self._tools: Dict[str, MCPTool] = {}  # tool_name -> MCPTool
        self._prompts: Dict[str, MCPPrompt] = {}  # prompt_name -> MCPPrompt
        self._health_check_timeout = health_check_timeout
        self._lock = asyncio.Lock()

        # Cache for loaded local modules
        self._loaded_modules: Dict[str, Any] = {}

    async def register_server(self, config: MCPServerConfig) -> bool:
        """
        Register an MCP server.

        Args:
            config: MCP server configuration

        Returns:
            True if registration successful
        """
        async with self._lock:
            if not config.enabled:
                logger.info(f"MCP server '{config.name}' is disabled, skipping registration")
                config.status = "disabled"
                self._servers[config.name] = config
                return False

            logger.info(
                f"Registering MCP server '{config.name}' "
                f"(type: {config.server_type.value}, transport: {config.transport.value})"
            )

            # Perform initial health check and tool discovery
            is_healthy = await self._check_server_health(config)

            if is_healthy:
                config.status = "healthy"
                await self._discover_tools(config)
                await self._discover_prompts(config)  # Discover prompts after tools
                logger.info(
                    f"✅ MCP server '{config.name}' registered successfully "
                    f"with {config.tool_count} tools"
                )
            else:
                config.status = "unhealthy"
                logger.warning(f"⚠️ MCP server '{config.name}' is unhealthy")

            self._servers[config.name] = config
            return is_healthy

    async def unregister_server(self, server_name: str):
        """Remove an MCP server and its tools/prompts."""
        async with self._lock:
            if server_name in self._servers:
                # Remove all tools from this server
                tools_to_remove = [
                    tool_name for tool_name, tool in self._tools.items()
                    if tool.server_name == server_name
                ]

                for tool_name in tools_to_remove:
                    del self._tools[tool_name]

                # Remove all prompts from this server
                prompts_to_remove = [
                    prompt_name for prompt_name, prompt in self._prompts.items()
                    if prompt.server_name == server_name
                ]

                for prompt_name in prompts_to_remove:
                    del self._prompts[prompt_name]

                del self._servers[server_name]
                logger.info(
                    f"Unregistered MCP server '{server_name}' "
                    f"({len(tools_to_remove)} tools, {len(prompts_to_remove)} prompts)"
                )

    async def get_available_tools(self) -> List[MCPTool]:
        """
        Get all tools from healthy MCP servers.

        Returns:
            List of available MCP tools
        """
        async with self._lock:
            return [
                tool for tool in self._tools.values()
                if tool.server_name in self._servers
                and self._servers[tool.server_name].status == "healthy"
            ]

    async def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Get a specific tool by name."""
        async with self._lock:
            return self._tools.get(tool_name)

    async def get_prompt(self, prompt_name: str) -> Optional[MCPPrompt]:
        """Get a specific prompt by name."""
        async with self._lock:
            return self._prompts.get(prompt_name)

    async def get_available_prompts(self) -> List[MCPPrompt]:
        """
        Get all prompts from healthy MCP servers.

        Returns:
            List of available MCP prompts
        """
        async with self._lock:
            return [
                prompt for prompt in self._prompts.values()
                if prompt.server_name in self._servers
                and self._servers[prompt.server_name].status == "healthy"
            ]

    async def get_server_config(self, server_name: str) -> Optional[MCPServerConfig]:
        """Get configuration for a specific server."""
        async with self._lock:
            return self._servers.get(server_name)

    async def get_all_servers(self) -> Dict[str, MCPServerConfig]:
        """Get all registered servers."""
        async with self._lock:
            return self._servers.copy()

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health checks on all registered servers.

        Returns:
            Dictionary mapping server_name to health status
        """
        results = {}

        async with self._lock:
            servers_to_check = list(self._servers.values())

        # Check all servers concurrently
        tasks = [
            self._check_and_update_server(server)
            for server in servers_to_check
            if server.enabled
        ]

        health_results = await asyncio.gather(*tasks, return_exceptions=True)

        for server, is_healthy in zip(servers_to_check, health_results):
            if isinstance(is_healthy, Exception):
                logger.error(f"Error checking MCP server {server.name}: {is_healthy}")
                results[server.name] = False
            else:
                results[server.name] = is_healthy

        return results

    async def _check_and_update_server(self, server: MCPServerConfig) -> bool:
        """Check server health and update its status."""
        is_healthy = await self._check_server_health(server)

        async with self._lock:
            if server.name in self._servers:
                if is_healthy:
                    self._servers[server.name].status = "healthy"
                    # Refresh tools if needed
                    await self._discover_tools(server)
                else:
                    self._servers[server.name].status = "unhealthy"

                self._servers[server.name].last_check = datetime.now()

        return is_healthy

    async def _check_server_health(self, server: MCPServerConfig) -> bool:
        """
        Perform health check on an MCP server.

        Args:
            server: MCP server configuration

        Returns:
            True if server is healthy
        """
        try:
            if server.server_type == MCPServerType.REMOTE:
                return await self._check_remote_server_health(server)
            else:
                return await self._check_local_server_health(server)
        except Exception as e:
            logger.error(f"Error checking MCP server '{server.name}': {e}")
            return False

    async def _check_remote_server_health(self, server: MCPServerConfig) -> bool:
        """Check health of remote MCP server via HTTP."""
        try:
            headers = server.headers.copy()

            # Streamable HTTP requires specific Accept header
            if server.transport == MCPTransportType.STREAMABLE_HTTP:
                headers["Accept"] = "application/json, text/event-stream"

            if server.api_key:
                headers["Authorization"] = f"Bearer {server.api_key}"

            async with httpx.AsyncClient(timeout=self._health_check_timeout) as client:
                # Try to get server info/health
                # MCP servers typically respond to GET on their base endpoint
                response = await client.get(server.url, headers=headers)

                # For Streamable HTTP, 400 with session ID in headers means server is alive
                if response.status_code == 200:
                    logger.debug(f"MCP server '{server.name}' is healthy")
                    return True
                elif (response.status_code == 400 and
                      server.transport == MCPTransportType.STREAMABLE_HTTP and
                      "mcp-session-id" in response.headers):
                    # Streamable HTTP server responded with session - it's alive
                    logger.debug(f"MCP server '{server.name}' is healthy (Streamable HTTP)")
                    return True
                else:
                    logger.warning(
                        f"MCP server '{server.name}' returned status {response.status_code}"
                    )
                    return False

        except httpx.ConnectError:
            logger.debug(f"MCP server '{server.name}' connection refused")
            return False
        except httpx.TimeoutException:
            logger.debug(f"MCP server '{server.name}' health check timed out")
            return False
        except Exception as e:
            logger.error(f"Error checking remote MCP server '{server.name}': {e}")
            return False

    async def _check_local_server_health(self, server: MCPServerConfig) -> bool:
        """Check health of local MCP server."""
        try:
            # Check if file exists
            if not Path(server.local_path).exists():
                logger.error(f"Local MCP server file not found: {server.local_path}")
                return False

            # Try to load the module
            module = await self._load_local_module(server)

            if module is None:
                return False

            # Check if it has the expected MCP structure
            if hasattr(module, 'mcp') or hasattr(module, 'app'):
                logger.debug(f"Local MCP server '{server.name}' loaded successfully")
                return True
            else:
                logger.warning(
                    f"Local module '{server.local_path}' doesn't have 'mcp' or 'app' attribute"
                )
                return False

        except Exception as e:
            logger.error(f"Error checking local MCP server '{server.name}': {e}")
            return False

    async def _load_local_module(self, server: MCPServerConfig) -> Optional[Any]:
        """Load a local Python module."""
        try:
            # Check cache first
            if server.name in self._loaded_modules:
                return self._loaded_modules[server.name]

            # Load module dynamically
            module_name = server.module_name or f"mcp_server_{server.name}"
            spec = importlib.util.spec_from_file_location(module_name, server.local_path)

            if spec is None or spec.loader is None:
                logger.error(f"Cannot load module from {server.local_path}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Cache the loaded module
            self._loaded_modules[server.name] = module

            logger.info(f"Loaded local MCP module: {module_name}")
            return module

        except Exception as e:
            logger.error(f"Error loading local module '{server.local_path}': {e}")
            return None

    async def _discover_tools(self, server: MCPServerConfig):
        """
        Discover tools from an MCP server.

        This method queries the MCP server for available tools and registers them.
        NOTE: This method expects to be called while holding self._lock
        """
        try:
            if server.server_type == MCPServerType.REMOTE:
                tools = await self._discover_remote_tools(server)
            else:
                tools = await self._discover_local_tools(server)

            # Register discovered tools (lock is already held by caller)
            for tool in tools:
                tool.server_name = server.name
                self._tools[tool.name] = tool

            server.tool_count = len(tools)
            logger.info(
                f"Discovered {len(tools)} tools from MCP server '{server.name}'"
            )

        except Exception as e:
            logger.error(f"Error discovering tools from '{server.name}': {e}")

    async def _discover_remote_tools(self, server: MCPServerConfig) -> List[MCPTool]:
        """Discover tools from remote MCP server via HTTP."""
        tools = []

        try:
            headers = server.headers.copy()

            # Streamable HTTP requires specific Accept header
            if server.transport == MCPTransportType.STREAMABLE_HTTP:
                headers["Accept"] = "application/json, text/event-stream"

            if server.api_key:
                headers["Authorization"] = f"Bearer {server.api_key}"

            async with httpx.AsyncClient(timeout=server.timeout) as client:
                # For Streamable HTTP, first initialize the MCP session
                session_id = None
                if server.transport == MCPTransportType.STREAMABLE_HTTP:
                    # Send initialize request first (required by MCP protocol)
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
                        headers["mcp-session-id"] = session_id
                        logger.debug(f"Initialized MCP session for '{server.name}': {session_id}")

                        # Send initialized notification (required by MCP protocol after initialize)
                        await client.post(
                            server.url,
                            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                            headers=headers
                        )
                        logger.debug(f"Sent initialized notification to '{server.name}'")

                # MCP protocol: send tools/list request
                request_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list"
                }

                response = await client.post(
                    server.url,
                    json=request_payload,
                    headers=headers
                )

                if response.status_code == 200:
                    logger.info(f"✅ MCP server '{server.name}' returned 200 OK")
                    logger.debug(f"Response headers: {dict(response.headers)}")

                    # For Streamable HTTP, response might be SSE format
                    content_type = response.headers.get("content-type", "")
                    logger.debug(f"Response content-type: {content_type}")

                    try:
                        if "text/event-stream" in content_type:
                            # Parse SSE format: "event: message\ndata: {...}"
                            logger.debug("Parsing SSE format response")
                            import json as json_module

                            text = response.text
                            logger.debug(f"Response text (first 500 chars): {text[:500]}")
                            logger.debug(f"Response text (last 500 chars): {text[-500:]}")

                            # Extract JSON from SSE data line
                            data = None
                            for line in text.split('\n'):
                                logger.debug(f"SSE line: {line[:100] if len(line) > 100 else line}")
                                if line.startswith('data: '):
                                    json_str = line[6:]  # Remove 'data: ' prefix
                                    logger.debug(f"Found data line, parsing JSON: {json_str[:200]}")
                                    data = json_module.loads(json_str)
                                    logger.info("✅ Successfully parsed SSE data")
                                    break

                            if data is None:
                                logger.warning("⚠️ No 'data:' line found in SSE response, using empty dict")
                                data = {}
                        else:
                            logger.debug("Parsing JSON response")
                            data = response.json()
                            logger.debug(f"Parsed JSON data: {data}")

                    except Exception as e:
                        logger.error(f"❌ Error parsing response: {e}", exc_info=True)
                        logger.error(f"Response text: {response.text[:1000]}")
                        data = {}

                    # Parse MCP tools/list response
                    logger.debug(f"Checking for tools in response data: {data.keys() if isinstance(data, dict) else type(data)}")
                    if "result" in data and "tools" in data["result"]:
                        tools_list = data["result"]["tools"]
                        logger.info(f"📋 Found {len(tools_list)} tools from '{server.name}'")

                        for tool_data in tools_list:
                            tool = MCPTool(
                                name=tool_data.get("name", ""),
                                description=tool_data.get("description", ""),
                                input_schema=tool_data.get("inputSchema", {}),
                                server_name=server.name
                            )
                            tools.append(tool)
                            logger.debug(f"  - {tool.name}: {tool.description[:80] if len(tool.description) > 80 else tool.description}")
                    else:
                        logger.warning(f"⚠️ Response missing 'result.tools': {data}")
                else:
                    logger.warning(
                        f"Failed to discover tools from '{server.name}': "
                        f"HTTP {response.status_code}"
                    )

        except Exception as e:
            logger.error(f"Error discovering remote tools from '{server.name}': {e}")

        return tools

    async def _discover_local_tools(self, server: MCPServerConfig) -> List[MCPTool]:
        """Discover tools from local MCP server module."""
        tools = []

        try:
            module = await self._load_local_module(server)

            if module is None:
                return tools

            # Try to get FastMCP instance
            mcp_instance = None
            if hasattr(module, 'mcp'):
                mcp_instance = module.mcp
            elif hasattr(module, 'app'):
                # Some servers export 'app' instead
                mcp_instance = module.app

            if mcp_instance is None:
                logger.warning(f"No MCP instance found in module '{server.local_path}'")
                return tools

            # Extract tools from FastMCP instance
            # FastMCP stores tools in _tools attribute
            if hasattr(mcp_instance, '_tools'):
                for tool_name, tool_obj in mcp_instance._tools.items():
                    # Extract tool metadata
                    tool = MCPTool(
                        name=tool_name,
                        description=getattr(tool_obj, 'description', ''),
                        input_schema=getattr(tool_obj, 'input_schema', {}),
                        server_name=server.name
                    )
                    tools.append(tool)
            elif hasattr(mcp_instance, 'list_tools'):
                # Alternative: use list_tools method if available
                tool_list = mcp_instance.list_tools()
                for tool_data in tool_list:
                    tool = MCPTool(
                        name=tool_data.get("name", ""),
                        description=tool_data.get("description", ""),
                        input_schema=tool_data.get("inputSchema", {}),
                        server_name=server.name
                    )
                    tools.append(tool)

        except Exception as e:
            logger.error(f"Error discovering local tools from '{server.name}': {e}")

        return tools

    async def _discover_prompts(self, server: MCPServerConfig):
        """
        Discover prompts from an MCP server.

        This method queries the MCP server for available prompts and registers them.
        If server.prompts_file is specified, loads prompts from that file instead.
        NOTE: This method expects to be called while holding self._lock
        """
        try:
            prompts = []

            # Check if manual prompts file is specified
            if server.prompts_file:
                prompts = await self._load_prompts_from_file(server)
            elif server.server_type == MCPServerType.REMOTE:
                prompts = await self._discover_remote_prompts(server)
            else:
                prompts = await self._discover_local_prompts(server)

            # Register discovered prompts (lock is already held by caller)
            for prompt in prompts:
                prompt.server_name = server.name
                self._prompts[prompt.name] = prompt

                # Associate with tool if specified
                if server.prompt_tool_association:
                    tool = self._tools.get(server.prompt_tool_association)
                    if tool:
                        tool.associated_prompt = prompt.name
                        logger.info(
                            f"Associated prompt '{prompt.name}' with tool '{tool.name}'"
                        )

            if len(prompts) > 0:
                logger.info(
                    f"Discovered {len(prompts)} prompts from MCP server '{server.name}'"
                )

        except Exception as e:
            logger.error(f"Error discovering prompts from '{server.name}': {e}")

    async def _discover_remote_prompts(self, server: MCPServerConfig) -> List[MCPPrompt]:
        """Discover prompts from remote MCP server via HTTP."""
        prompts = []

        try:
            headers = server.headers.copy()

            # Streamable HTTP requires specific Accept header
            if server.transport == MCPTransportType.STREAMABLE_HTTP:
                headers["Accept"] = "application/json, text/event-stream"

            if server.api_key:
                headers["Authorization"] = f"Bearer {server.api_key}"

            async with httpx.AsyncClient(timeout=server.timeout) as client:
                # For Streamable HTTP, first initialize the MCP session
                session_id = None
                if server.transport == MCPTransportType.STREAMABLE_HTTP:
                    # Send initialize request first (required by MCP protocol)
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
                        headers["mcp-session-id"] = session_id
                        logger.debug(f"Initialized MCP session for prompts/list '{server.name}': {session_id}")

                        # Send initialized notification (required by MCP protocol after initialize)
                        await client.post(
                            server.url,
                            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                            headers=headers
                        )

                # MCP protocol: send prompts/list request
                request_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "prompts/list"
                }

                response = await client.post(
                    server.url,
                    json=request_payload,
                    headers=headers
                )

                if response.status_code == 200:
                    logger.info(f"✅ MCP server '{server.name}' responded 200 OK to prompts/list")

                    # Parse response (could be SSE or JSON)
                    content_type = response.headers.get("content-type", "")
                    logger.debug(f"Response content-type: {content_type}")

                    try:
                        if "text/event-stream" in content_type:
                            # Parse SSE format
                            import json as json_module
                            text = response.text
                            data = None
                            for line in text.split('\n'):
                                if line.startswith('data: '):
                                    json_str = line[6:]
                                    data = json_module.loads(json_str)
                                    break

                            if data is None:
                                logger.debug("No prompts/list data in SSE response")
                                data = {}
                        else:
                            data = response.json()

                    except Exception as e:
                        logger.error(f"Error parsing prompts/list response: {e}")
                        data = {}

                    # Parse MCP prompts/list response
                    logger.debug(f"Parsed data keys: {list(data.keys())}")
                    if "result" in data:
                        logger.debug(f"Result keys: {list(data['result'].keys())}")

                    if "result" in data and "prompts" in data["result"]:
                        prompts_list = data["result"]["prompts"]
                        logger.info(f"📋 Found {len(prompts_list)} prompts from '{server.name}'")

                        for prompt_data in prompts_list:
                            # Parse arguments
                            arguments = []
                            for arg_data in prompt_data.get("arguments", []):
                                arg = MCPPromptArgument(
                                    name=arg_data.get("name", ""),
                                    description=arg_data.get("description", ""),
                                    required=arg_data.get("required", True)
                                )
                                arguments.append(arg)

                            prompt = MCPPrompt(
                                name=prompt_data.get("name", ""),
                                description=prompt_data.get("description", ""),
                                arguments=arguments,
                                server_name=server.name
                            )
                            prompts.append(prompt)
                            logger.debug(f"  - {prompt.name}: {prompt.description[:80]}")
                    else:
                        logger.debug(f"No prompts available from '{server.name}'")
                else:
                    logger.debug(
                        f"MCP server '{server.name}' returned {response.status_code} for prompts/list"
                    )

        except Exception as e:
            logger.debug(f"Error discovering remote prompts from '{server.name}': {e}")

        return prompts

    async def _discover_local_prompts(self, server: MCPServerConfig) -> List[MCPPrompt]:
        """Discover prompts from local MCP server module."""
        prompts = []

        try:
            module = await self._load_local_module(server)

            if module is None:
                return prompts

            # Try to get FastMCP instance
            mcp_instance = None
            if hasattr(module, 'mcp'):
                mcp_instance = module.mcp
            elif hasattr(module, 'app'):
                mcp_instance = module.app

            if mcp_instance is None:
                return prompts

            # Extract prompts from FastMCP instance
            if hasattr(mcp_instance, '_prompts'):
                for prompt_name, prompt_obj in mcp_instance._prompts.items():
                    # Extract prompt metadata
                    prompt = MCPPrompt(
                        name=prompt_name,
                        description=getattr(prompt_obj, 'description', ''),
                        arguments=[],  # Local prompts may not have argument metadata
                        server_name=server.name
                    )
                    prompts.append(prompt)
            elif hasattr(mcp_instance, 'list_prompts'):
                # Alternative: use list_prompts method if available
                prompt_list = mcp_instance.list_prompts()
                for prompt_data in prompt_list:
                    arguments = []
                    for arg_data in prompt_data.get("arguments", []):
                        arg = MCPPromptArgument(
                            name=arg_data.get("name", ""),
                            description=arg_data.get("description", ""),
                            required=arg_data.get("required", True)
                        )
                        arguments.append(arg)

                    prompt = MCPPrompt(
                        name=prompt_data.get("name", ""),
                        description=prompt_data.get("description", ""),
                        arguments=arguments,
                        server_name=server.name
                    )
                    prompts.append(prompt)

        except Exception as e:
            logger.debug(f"Error discovering local prompts from '{server.name}': {e}")

        return prompts

    async def _load_prompts_from_file(self, server: MCPServerConfig) -> List[MCPPrompt]:
        """
        Load prompts from a file (markdown, text, etc.).

        This allows manually configuring prompts for MCP servers that don't expose
        prompts via prompts/list.

        Args:
            server: Server configuration with prompts_file set

        Returns:
            List of MCPPrompt objects loaded from file
        """
        prompts = []

        try:
            if not server.prompts_file:
                return prompts

            prompt_file = Path(server.prompts_file)

            if not prompt_file.exists():
                logger.warning(
                    f"Prompts file not found for server '{server.name}': {server.prompts_file}"
                )
                return prompts

            # Read file content
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_content = f.read()

            # Create a single prompt from file content
            # Use filename (without extension) as prompt name
            prompt_name = prompt_file.stem

            prompt = MCPPrompt(
                name=prompt_name,
                description=prompt_content,
                arguments=[],  # No arguments for manual prompts
                server_name=server.name
            )

            prompts.append(prompt)

            logger.info(
                f"📄 Loaded prompt '{prompt_name}' from file for server '{server.name}' "
                f"({len(prompt_content)} chars)"
            )

        except Exception as e:
            logger.error(f"Error loading prompts from file for '{server.name}': {e}")

        return prompts


# Global MCP tool registry instance
_global_mcp_registry: Optional[MCPToolRegistry] = None


def get_mcp_registry() -> MCPToolRegistry:
    """Get or create the global MCP tool registry instance."""
    global _global_mcp_registry
    if _global_mcp_registry is None:
        _global_mcp_registry = MCPToolRegistry()
    return _global_mcp_registry


async def initialize_mcp_registry_from_config():
    """
    Initialize MCP registry from configuration.

    This should be called at application startup to register
    all configured MCP servers.
    """
    from config import settings

    registry = get_mcp_registry()

    # Parse MCP server configurations from settings
    # Format: MCP_SERVER_{NAME}_TYPE, MCP_SERVER_{NAME}_URL, etc.
    mcp_servers = getattr(settings, 'mcp_servers', {})

    for server_name, server_config in mcp_servers.items():
        try:
            config = MCPServerConfig(
                name=server_name,
                server_type=MCPServerType(server_config.get('type', 'remote')),
                transport=MCPTransportType(server_config.get('transport', 'streamable_http')),
                url=server_config.get('url'),
                api_key=server_config.get('api_key'),
                local_path=server_config.get('local_path'),
                enabled=server_config.get('enabled', True),
                timeout=server_config.get('timeout', 30.0),
                prompts_file=server_config.get('prompts_file'),
                prompt_tool_association=server_config.get('prompt_tool_association')
            )

            await registry.register_server(config)

        except Exception as e:
            logger.error(f"Error registering MCP server '{server_name}': {e}")

    # Log summary
    all_servers = await registry.get_all_servers()
    healthy_count = sum(1 for s in all_servers.values() if s.status == "healthy")
    total_tools = sum(s.tool_count for s in all_servers.values() if s.status == "healthy")

    logger.info(
        f"MCP Registry initialized: {healthy_count}/{len(all_servers)} servers healthy, "
        f"{total_tools} tools available"
    )
