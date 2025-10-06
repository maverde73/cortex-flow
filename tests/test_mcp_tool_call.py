#!/usr/bin/env python3
"""
Test calling MCP tool through Supervisor's LangChain integration
"""
import asyncio
from utils.mcp_client import get_mcp_langchain_tools

async def test_mcp_tool():
    print("🔍 Getting MCP LangChain tools...")
    tools = await get_mcp_langchain_tools()

    print(f"\n📋 Found {len(tools)} MCP tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")

    if tools:
        tool = tools[0]
        print(f"\n🧪 Testing tool: {tool.name}")
        print(f"Description: {tool.description}")
        print(f"Args schema: {tool.args_schema.schema() if hasattr(tool, 'args_schema') else 'N/A'}")

        # Test calling the tool with a simple query
        print("\n📞 Calling MCP tool with test query...")
        try:
            # The query_database tool expects a query_payload
            result = await tool.ainvoke({
                "query_payload": {
                    "table": "users",
                    "method": "select",
                    "columns": ["id", "name", "email"],
                    "limit": 5
                }
            })
            print(f"\n✅ Tool call successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"\n❌ Tool call failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_tool())
