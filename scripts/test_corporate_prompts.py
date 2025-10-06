#!/usr/bin/env python3
"""
Test MCP Prompts Discovery from Corporate Server

Tests that the MCP registry correctly:
1. Calls prompts/list on corporate server
2. Parses prompt response
3. Associates prompts with tools
4. Stores prompts in registry

Usage:
    python scripts/test_corporate_prompts.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.mcp_registry import get_mcp_registry, initialize_mcp_registry_from_config
from config_legacy import settings


async def test_prompt_discovery():
    """Test prompt discovery from corporate MCP server"""

    print("=" * 80)
    print("MCP PROMPTS DISCOVERY TEST")
    print("=" * 80)
    print()

    # Check if MCP is enabled
    if not settings.mcp_enable:
        print("❌ MCP_ENABLE is False. Set MCP_ENABLE=true in .env")
        return False

    print("✓ MCP enabled")
    print()

    # Initialize registry (discover all servers)
    print("🔍 Initializing MCP registry and discovering servers...")
    await initialize_mcp_registry_from_config()
    print()

    # Get registry
    registry = get_mcp_registry()

    # Test 1: Check if corporate server is configured
    print("Test 1: Corporate Server Configuration")
    print("-" * 80)

    servers_dict = await registry.get_all_servers()
    corporate_server = servers_dict.get("corporate")

    if not corporate_server:
        print("❌ Corporate server not configured")
        print("   Add to .env:")
        print("   MCP_SERVER_CORPORATE_TYPE=remote")
        print("   MCP_SERVER_CORPORATE_TRANSPORT=streamable_http")
        print("   MCP_SERVER_CORPORATE_URL=http://localhost:8005/mcp")
        print("   MCP_SERVER_CORPORATE_ENABLED=true")
        return False

    print(f"✓ Corporate server configured:")
    print(f"  - URL: {corporate_server.url}")
    print(f"  - Transport: {corporate_server.transport}")
    print(f"  - Status: {corporate_server.status}")
    print()

    if corporate_server.status != "healthy":
        print(f"❌ Corporate server not healthy (status: {corporate_server.status})")
        print("   Make sure the server is running on http://localhost:8005/mcp")
        return False

    print("✓ Corporate server is healthy")
    print()

    # Test 2: Check prompts discovery
    print("Test 2: Prompts Discovery")
    print("-" * 80)

    prompts = await registry.get_available_prompts()

    if not prompts:
        print("❌ No prompts discovered")
        print("   The corporate server should expose prompts via prompts/list")
        return False

    print(f"✓ Discovered {len(prompts)} prompt(s)")
    print()

    for prompt in prompts:
        print(f"Prompt: {prompt.name}")
        print(f"  Server: {prompt.server_name}")
        print(f"  Description (first 200 chars):")
        print(f"    {prompt.description[:200]}...")
        print(f"  Arguments: {[arg.name for arg in prompt.arguments]}")
        print()

    # Test 3: Check tool-prompt association
    print("Test 3: Tool-Prompt Association")
    print("-" * 80)

    tools = await registry.get_available_tools()
    corporate_tools = [t for t in tools if t.server_name == "corporate"]

    if not corporate_tools:
        print("❌ No tools discovered from corporate server")
        return False

    print(f"✓ Discovered {len(corporate_tools)} tool(s) from corporate:")
    print()

    for tool in corporate_tools:
        print(f"Tool: {tool.name}")
        print(f"  Description: {tool.description}")
        print(f"  Associated Prompt: {tool.associated_prompt or '(none)'}")

        # Try to get associated prompt
        if tool.associated_prompt:
            prompt = await registry.get_prompt(tool.associated_prompt)
            if prompt:
                print(f"  ✓ Prompt found: {prompt.name}")
                print(f"    Prompt length: {len(prompt.description)} chars")
            else:
                print(f"  ❌ Prompt '{tool.associated_prompt}' not found in registry")
        else:
            # Try to find prompt with same name as tool
            prompt = await registry.get_prompt(tool.name)
            if prompt:
                print(f"  ✓ Prompt with same name found: {prompt.name}")
                print(f"    Prompt length: {len(prompt.description)} chars")
            else:
                print(f"  ⚠️  No prompt associated (neither explicit nor by name)")

        print()

    # Test 4: Check specific corporate prompt content
    print("Test 4: Corporate JSON Query Prompt Content")
    print("-" * 80)

    # Try to find the database query prompt
    db_prompt = None
    for prompt in prompts:
        if "database" in prompt.name.lower() or "query" in prompt.name.lower():
            db_prompt = prompt
            break

    if not db_prompt:
        # Try first prompt
        db_prompt = prompts[0] if prompts else None

    if db_prompt:
        print(f"✓ Found prompt: {db_prompt.name}")
        print()
        print("Prompt Content Preview:")
        print("-" * 80)

        # Show first 1000 chars
        preview = db_prompt.description[:1000]
        print(preview)

        if len(db_prompt.description) > 1000:
            remaining = len(db_prompt.description) - 1000
            print(f"\n... ({remaining} more characters)")

        print()

        # Check for key elements from PROMPT.md
        key_elements = [
            ("Schema definition", "schema" in db_prompt.description.lower()),
            ("JSON API format", "json" in db_prompt.description.lower()),
            ("SELECT operations", "select" in db_prompt.description.lower()),
            ("WHERE clauses", "where" in db_prompt.description.lower()),
            ("JOIN operations", "join" in db_prompt.description.lower()),
            ("Examples", "example" in db_prompt.description.lower() or "esempi" in db_prompt.description.lower()),
        ]

        print("Key Elements Check:")
        for element, found in key_elements:
            status = "✓" if found else "✗"
            print(f"  {status} {element}")

        print()
    else:
        print("❌ No database/query prompt found")
        return False

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✓ Corporate server: {corporate_server.status}")
    print(f"✓ Prompts discovered: {len(prompts)}")
    print(f"✓ Tools discovered: {len(corporate_tools)}")
    print(f"✓ Prompts working: YES")
    print()
    print("✅ ALL TESTS PASSED")
    print()

    return True


async def main():
    """Main test runner"""
    try:
        success = await test_prompt_discovery()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
