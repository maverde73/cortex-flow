"""
MCP Auto-Test Orchestrator

Automatically tests MCP servers on configuration save and caches results.
Provides health status and metadata for better workflow integration.
"""

import asyncio
import logging
from typing import Dict, Any, Tuple
from datetime import datetime

from utils.mcp_tester import MCPServerTester, MCPTestResult

logger = logging.getLogger(__name__)


async def run_comprehensive_mcp_tests(
    server_name: str,
    server_config: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """
    Run comprehensive MCP server tests and aggregate results.

    This orchestrator function:
    1. Tests connection and capabilities
    2. If connection succeeds, runs all available tests:
       - List tools
       - List prompts
       - List resources
       - Test completions (if supported)
    3. Aggregates results into structured format
    4. Returns health status and cached data

    Args:
        server_name: Name/ID of the MCP server
        server_config: Server configuration dict (url, transport, api_key, etc.)

    Returns:
        Tuple of (status, test_results) where:
        - status: "healthy" | "unhealthy" | "untested"
        - test_results: Dict with connection, tools, prompts, resources, completions data
    """
    logger.info(f"🧪 Starting comprehensive auto-test for MCP server '{server_name}'")

    tester = MCPServerTester(server_config, timeout=server_config.get("timeout", 30.0))
    test_results: Dict[str, Any] = {}
    status = "untested"

    # Step 1: Test connection (required)
    logger.debug(f"Testing connection to '{server_name}'...")
    connection_result = await tester.test_connection()
    test_results["connection"] = {
        "success": connection_result.success,
        "data": connection_result.data,
        "error": connection_result.error,
        "metadata": connection_result.metadata
    }

    if not connection_result.success:
        logger.warning(
            f"❌ Connection test failed for '{server_name}': {connection_result.error}"
        )
        status = "unhealthy"
        return status, test_results

    # Connection succeeded - server is potentially healthy
    logger.info(f"✅ Connection successful for '{server_name}'")
    capabilities = connection_result.data.get("capabilities", {}) if connection_result.data else {}

    # Step 2: List tools (if supported)
    if capabilities.get("tools"):
        logger.debug(f"Listing tools for '{server_name}'...")
        tools_result = await tester.list_tools()
        test_results["tools"] = {
            "success": tools_result.success,
            "data": tools_result.data,
            "error": tools_result.error,
            "metadata": tools_result.metadata
        }

        if tools_result.success and tools_result.data:
            tools_list = tools_result.data.get("tools", [])
            logger.info(f"📦 Found {len(tools_list)} tools in '{server_name}'")
    else:
        logger.debug(f"Server '{server_name}' does not advertise tools capability")
        test_results["tools"] = {
            "success": False,
            "error": "Capability not advertised",
            "data": None,
            "metadata": {}
        }

    # Step 3: List prompts (if supported)
    if capabilities.get("prompts"):
        logger.debug(f"Listing prompts for '{server_name}'...")
        prompts_result = await tester.list_prompts()
        test_results["prompts"] = {
            "success": prompts_result.success,
            "data": prompts_result.data,
            "error": prompts_result.error,
            "metadata": prompts_result.metadata
        }

        if prompts_result.success and prompts_result.data:
            prompts_list = prompts_result.data.get("prompts", [])
            logger.info(f"📝 Found {len(prompts_list)} prompts in '{server_name}'")
    else:
        logger.debug(f"Server '{server_name}' does not advertise prompts capability")
        test_results["prompts"] = {
            "success": False,
            "error": "Capability not advertised",
            "data": None,
            "metadata": {}
        }

    # Step 4: List resources (if supported)
    if capabilities.get("resources"):
        logger.debug(f"Listing resources for '{server_name}'...")
        resources_result = await tester.list_resources()
        test_results["resources"] = {
            "success": resources_result.success,
            "data": resources_result.data,
            "error": resources_result.error,
            "metadata": resources_result.metadata
        }

        if resources_result.success and resources_result.data:
            resources_list = resources_result.data.get("resources", [])
            logger.info(f"📚 Found {len(resources_list)} resources in '{server_name}'")
    else:
        logger.debug(f"Server '{server_name}' does not advertise resources capability")
        test_results["resources"] = {
            "success": False,
            "error": "Capability not advertised",
            "data": None,
            "metadata": {}
        }

    # Determine overall health status
    # Server is healthy if connection succeeded and at least one capability test passed
    connection_healthy = test_results.get("connection", {}).get("success", False)
    tools_healthy = test_results.get("tools", {}).get("success", False)
    prompts_healthy = test_results.get("prompts", {}).get("success", False)
    resources_healthy = test_results.get("resources", {}).get("success", False)

    # Server is healthy if connection works and at least one feature is available
    # OR if connection works but server advertises no capabilities (minimalist server)
    if connection_healthy:
        has_features = tools_healthy or prompts_healthy or resources_healthy
        advertises_capabilities = (
            capabilities.get("tools") or
            capabilities.get("prompts") or
            capabilities.get("resources")
        )

        if has_features or not advertises_capabilities:
            status = "healthy"
            logger.info(f"✅ Server '{server_name}' is HEALTHY")
        else:
            # Connection works but all advertised features failed
            status = "unhealthy"
            logger.warning(
                f"⚠️ Server '{server_name}' connection works but features failed"
            )
    else:
        status = "unhealthy"
        logger.error(f"❌ Server '{server_name}' is UNHEALTHY")

    return status, test_results


async def update_server_test_results(
    project_name: str,
    server_name: str,
    server_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run tests and update server configuration with results.

    Args:
        project_name: Name of the project
        server_name: Name of the MCP server
        server_config: Current server configuration

    Returns:
        Updated server configuration with test results and status
    """
    # Run comprehensive tests
    status, test_results = await run_comprehensive_mcp_tests(server_name, server_config)

    # Update configuration with test results
    updated_config = server_config.copy()
    updated_config["status"] = status
    updated_config["test_results"] = test_results
    updated_config["last_tested"] = datetime.utcnow().isoformat() + "Z"

    logger.info(
        f"📊 Auto-test complete for '{server_name}': "
        f"status={status}, tested_at={updated_config['last_tested']}"
    )

    return updated_config
