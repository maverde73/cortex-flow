#!/usr/bin/env python3
"""
Test diretto del tool MCP json_query_sse tramite supervisor API
"""
import requests
import json

def test_mcp_tool():
    """Test direct MCP tool call via supervisor"""

    print("🧪 Testing MCP tool json_query_sse via supervisor API...")
    print()

    # Prepare request
    payload = {
        "task_id": "test-mcp-1",
        "source_agent_id": "user",
        "target_agent_id": "supervisor",
        "task_description": "Usa il tool json_query_sse per interrogare il database. Esegui questa query JSON: {\"table\": \"employees\", \"select\": [\"first_name\", \"last_name\", \"position\"], \"limit\": 5}",
        "context": {},
        "response": None
    }

    print("📤 Sending request to supervisor...")
    print(f"   Task: {payload['task_description'][:80]}...")
    print()

    try:
        response = requests.post(
            "http://localhost:8000/invoke",
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            print()
            print("📊 Response:")
            print(json.dumps(result, indent=2)[:1000])
            print()

            if "response" in result and result["response"]:
                print("💡 Agent Response:")
                print(result["response"][:500])
        else:
            print(f"❌ HTTP {response.status_code}")
            print(response.text[:500])

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mcp_tool()
