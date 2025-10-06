#!/usr/bin/env python3
"""
Simple test script to verify the Cortex Flow system is working.

This script tests:
1. Individual agent servers are responding
2. MCP protocol is working correctly
3. Supervisor can orchestrate other agents
"""

import asyncio
import httpx
from schemas.mcp_protocol import MCPRequest, MCPResponse
from datetime import datetime


async def test_health_check(port: int, name: str) -> bool:
    """Test health endpoint of an agent."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:{port}/health", timeout=5.0)
            if response.status_code == 200:
                print(f"✅ {name} health check passed")
                return True
            else:
                print(f"❌ {name} health check failed (status {response.status_code})")
                return False
    except Exception as e:
        print(f"❌ {name} health check failed: {e}")
        return False


async def test_agent_invocation(
    port: int,
    agent_id: str,
    task: str,
    name: str
) -> bool:
    """Test invoking an agent directly."""
    try:
        request = MCPRequest(
            source_agent_id="test",
            target_agent_id=agent_id,
            task_description=task
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:{port}/invoke",
                json=request.model_dump(mode='json'),
                timeout=30.0
            )

            if response.status_code == 200:
                mcp_response = MCPResponse(**response.json())
                if mcp_response.status == "success":
                    print(f"✅ {name} invocation successful")
                    print(f"   Result preview: {mcp_response.result[:100]}...")
                    return True
                else:
                    print(f"❌ {name} returned error: {mcp_response.error_message}")
                    return False
            else:
                print(f"❌ {name} invocation failed (status {response.status_code})")
                return False

    except Exception as e:
        print(f"❌ {name} invocation failed: {e}")
        return False


async def test_supervisor_orchestration():
    """Test supervisor coordinating multiple agents."""
    print("\n🎯 Testing Supervisor Orchestration")
    print("=" * 60)

    task = """Find recent information about LangGraph and create a brief summary."""

    request = MCPRequest(
        source_agent_id="test",
        target_agent_id="supervisor",
        task_description=task
    )

    try:
        async with httpx.AsyncClient() as client:
            print(f"📤 Sending request to supervisor...")
            print(f"   Task: {task}")

            response = await client.post(
                "http://localhost:8000/invoke",
                json=request.model_dump(mode='json'),
                timeout=120.0  # Longer timeout for orchestration
            )

            if response.status_code == 200:
                mcp_response = MCPResponse(**response.json())

                if mcp_response.status == "success":
                    print(f"\n✅ Supervisor orchestration successful!")
                    print(f"\n📊 Metadata:")
                    print(f"   Messages exchanged: {mcp_response.metadata.get('message_count')}")
                    print(f"   Agents used: {mcp_response.metadata.get('agents_used')}")
                    print(f"\n📝 Final Result:")
                    print("-" * 60)
                    print(mcp_response.result)
                    print("-" * 60)
                    return True
                else:
                    print(f"❌ Supervisor returned error: {mcp_response.error_message}")
                    return False
            else:
                print(f"❌ Supervisor request failed (status {response.status_code})")
                return False

    except Exception as e:
        print(f"❌ Supervisor orchestration failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧪 Cortex Flow System Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Test 1: Health checks
    print("📋 Phase 1: Health Checks")
    print("-" * 60)
    results = []
    results.append(await test_health_check(8001, "Researcher"))
    results.append(await test_health_check(8003, "Analyst"))
    results.append(await test_health_check(8004, "Writer"))
    results.append(await test_health_check(8000, "Supervisor"))

    if not all(results):
        print("\n❌ Health checks failed. Make sure all agents are running.")
        print("   Run: ./start_all.sh")
        return False

    # Test 2: Individual agent invocations (optional, can be skipped if no API keys)
    print("\n📋 Phase 2: Individual Agent Tests")
    print("-" * 60)
    print("⏭️  Skipping (requires API keys and takes time)")

    # Test 3: Full orchestration
    success = await test_supervisor_orchestration()

    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
