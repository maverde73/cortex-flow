#!/usr/bin/env python3
import requests

# Step 1: Initialize
response = requests.post(
    "http://localhost:8005/mcp",
    json={
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    },
    headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
)

print(f"Initialize response status: {response.status_code}")
print(f"Initialize response headers: {dict(response.headers)}")
print(f"Initialize response text: {response.text}\n")

session_id = response.headers.get("mcp-session-id")
print(f"Session ID: {session_id}\n")

# Step 2: Send initialized notification (required after initialize)
if session_id:
    response = requests.post(
        "http://localhost:8005/mcp",
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": session_id
        }
    )
    print(f"Initialized notification sent: {response.status_code}\n")

# Step 3: List tools (try without params)
if session_id:
    response = requests.post(
        "http://localhost:8005/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": session_id
        }
    )

    print(f"Tools/list (no params) response status: {response.status_code}")
    print(f"Tools/list (no params) response text: {response.text}")
