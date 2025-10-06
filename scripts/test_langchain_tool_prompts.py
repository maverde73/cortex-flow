#!/usr/bin/env python3
"""
Test MCP Prompts Injection in LangChain Tools

Tests that prompts are correctly injected into LangChain tool descriptions.

Usage:
    python scripts/test_langchain_tool_prompts.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.mcp_registry import get_mcp_registry, initialize_mcp_registry_from_config
from utils.mcp_client import get_mcp_langchain_tools
from config import settings


async def test_langchain_prompt_injection():
    """Test that MCP prompts are injected into LangChain tools"""

    print("=" * 80)
    print("LANGCHAIN TOOL PROMPT INJECTION TEST")
    print("=" * 80)
    print()

    # Check if MCP is enabled
    if not settings.mcp_enable:
        print("❌ MCP_ENABLE is False. Set MCP_ENABLE=true in .env")
        return False

    print("✓ MCP enabled")
    print()

    # Initialize registry
    print("🔍 Initializing MCP registry...")
    await initialize_mcp_registry_from_config()
    print()

    # Get LangChain tools
    print("Test 1: LangChain Tools Creation")
    print("-" * 80)

    tools = await get_mcp_langchain_tools()

    if not tools:
        print("❌ No LangChain tools created")
        return False

    print(f"✓ Created {len(tools)} LangChain tool(s)")
    print()

    # Find query_database tool
    query_tool = None
    for tool in tools:
        if tool.name == "query_database":
            query_tool = tool
            break

    if not query_tool:
        print("❌ query_database tool not found")
        return False

    print("✓ Found query_database tool")
    print()

    # Test 2: Check prompt injection
    print("Test 2: Prompt Injection Verification")
    print("-" * 80)

    description = query_tool.description

    print(f"Tool Description Length: {len(description)} chars")
    print()

    # Check for prompt markers
    has_usage_guide = "Usage Guide" in description or "## Usage Guide" in description
    has_schema_info = "schema" in description.lower() or "tabelle" in description.lower()
    has_json_api = "json" in description.lower()
    has_examples = "example" in description.lower() or "esempi" in description.lower()
    has_rules = "regole" in description.lower() or "rule" in description.lower()

    print("Prompt Injection Markers:")
    print(f"  {'✓' if has_usage_guide else '✗'} Usage Guide section")
    print(f"  {'✓' if has_schema_info else '✗'} Database schema information")
    print(f"  {'✓' if has_json_api else '✗'} JSON API format")
    print(f"  {'✓' if has_examples else '✗'} Examples")
    print(f"  {'✓' if has_rules else '✗'} Rules/Guidelines")
    print()

    if not (has_usage_guide or (has_schema_info and has_json_api)):
        print("❌ Prompt not properly injected")
        print()
        print("Tool Description Preview:")
        print("-" * 80)
        print(description[:500])
        print()
        return False

    print("✓ Prompt successfully injected into tool description")
    print()

    # Test 3: Show description preview
    print("Test 3: Description Preview")
    print("-" * 80)

    # Show first 1000 chars
    preview_length = 1000
    preview = description[:preview_length]
    print(preview)

    if len(description) > preview_length:
        remaining = len(description) - preview_length
        print(f"\n... ({remaining} more characters)")

    print()

    # Test 4: Check tool schema
    print("Test 4: Tool Input Schema")
    print("-" * 80)

    if hasattr(query_tool, 'args_schema') and query_tool.args_schema:
        schema = query_tool.args_schema
        print(f"✓ Tool has input schema: {schema.__name__}")

        # Show schema fields
        if hasattr(schema, '__fields__'):
            print("\nSchema Fields:")
            for field_name, field_info in schema.__fields__.items():
                print(f"  - {field_name}: {field_info.annotation}")
        print()
    else:
        print("⚠️  No input schema defined")
        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✓ LangChain tools created: {len(tools)}")
    print(f"✓ query_database tool found: YES")
    print(f"✓ Description length: {len(description)} chars")
    print(f"✓ Prompt injected: YES")
    print()

    # Show what a ReAct agent would see
    print("=" * 80)
    print("WHAT A REACT AGENT SEES")
    print("=" * 80)
    print()
    print(f"Tool Name: {query_tool.name}")
    print()
    print("Tool Description (first 2000 chars):")
    print("-" * 80)
    print(description[:2000])
    if len(description) > 2000:
        print(f"\n... ({len(description) - 2000} more characters with schema, examples, rules)")
    print()

    print("✅ ALL TESTS PASSED")
    print()
    print("The ReAct agent will see the full 18K+ character prompt when deciding to use this tool!")
    print()

    return True


async def main():
    """Main test runner"""
    try:
        success = await test_langchain_prompt_injection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
