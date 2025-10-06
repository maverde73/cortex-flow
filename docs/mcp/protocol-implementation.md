# MCP Protocol Implementation

This document describes the complete implementation of the **Model Context Protocol (MCP) 2025-03-26** in Cortex-Flow.

---

## Protocol Overview

MCP is a **stateful JSON-RPC 2.0 protocol** for tool discovery and execution. It requires:
1. **Session initialization** before any operations
2. **Session ID management** across all requests
3. **SSE response parsing** for Streamable HTTP transport
4. **JSON Schema validation** for tool inputs

---

## Implementation Details

### 1. Session Lifecycle

#### Health Check (Optional)
```http
GET /mcp HTTP/1.1
Host: localhost:8005
```

**Response**:
```
HTTP/1.1 400 Bad Request
mcp-session-id: <uuid>
```

> **Note**: A `400` response with `mcp-session-id` header indicates the server is alive. This is expected behavior.

#### Initialize Session
```http
POST /mcp HTTP/1.1
Content-Type: application/json

{
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
```

**Response**:
```
HTTP/1.1 200 OK
mcp-session-id: <session-id>
Content-Type: text/event-stream

event: message
data: {"jsonrpc":"2.0","id":0,"result":{...}}
```

**Extract session ID from header** - this must be included in all subsequent requests.

#### Send Initialized Notification
```http
POST /mcp HTTP/1.1
Content-Type: application/json
mcp-session-id: <session-id>

{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

**Response**:
```
HTTP/1.1 202 Accepted
```

---

### 2. Tool Discovery

Once the session is initialized, request the list of available tools:

```http
POST /mcp HTTP/1.1
Content-Type: application/json
mcp-session-id: <session-id>

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

**Response** (SSE format):
```
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: message
data: {
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "query_database",
        "description": "Execute a database query using the JSON API",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query_payload": {
              "type": "object"
            }
          },
          "required": ["query_payload"]
        }
      }
    ]
  }
}
```

### 3. Tool Execution

Execute a discovered tool:

```http
POST /mcp HTTP/1.1
Content-Type: application/json
mcp-session-id: <session-id>

{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "query_database",
    "arguments": {
      "query_payload": {
        "table": "employees",
        "select": ["id", "first_name", "last_name"],
        "limit": 10
      }
    }
  }
}
```

**Response** (SSE format):
```
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: message
data: {
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"id\":1,\"first_name\":\"John\",\"last_name\":\"Doe\"}...]"
      }
    ],
    "isError": false
  }
}
```

---

## Code Implementation

### MCPToolRegistry (utils/mcp_registry.py)

The `MCPToolRegistry` class manages MCP server connections and tool discovery.

#### Session Initialization (lines 438-473)

```python
async def _discover_remote_tools(self, server: MCPServerConfig) -> List[MCPTool]:
    """Discover tools from a remote MCP server"""

    async with httpx.AsyncClient(timeout=server.timeout) as client:
        headers = {"Content-Type": "application/json"}

        # Add API key if configured
        if server.api_key:
            headers["Authorization"] = f"Bearer {server.api_key}"

        # For Streamable HTTP, first initialize the MCP session
        session_id = None
        if server.transport == MCPTransportType.STREAMABLE_HTTP:
            # 1. Initialize
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

            # 2. Extract session ID
            if "mcp-session-id" in init_response.headers:
                session_id = init_response.headers["mcp-session-id"]
                headers["mcp-session-id"] = session_id

                # 3. Send initialized notification
                await client.post(
                    server.url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized"
                    },
                    headers=headers
                )
```

#### SSE Response Parsing (lines 471-493)

```python
# Request tools/list
tools_payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
}

response = await client.post(
    server.url,
    json=tools_payload,
    headers=headers
)

# Parse SSE format: "event: message\ndata: {...json...}"
response_text = response.text
if "event: message" in response_text:
    # Extract JSON from SSE format
    lines = response_text.strip().split('\n')
    for line in lines:
        if line.startswith('data: '):
            data_json = line[6:]  # Remove "data: " prefix
            result = json.loads(data_json)

            # Extract tools from result
            if "result" in result and "tools" in result["result"]:
                tools_data = result["result"]["tools"]
                # Convert to MCPTool objects
                ...
```

### MCPClient (utils/mcp_client.py)

The `MCPClient` class executes MCP tools with session management.

#### Tool Execution with Session (lines 115-151)

```python
async def call_tool(
    self,
    server_name: str,
    tool_name: str,
    arguments: dict
) -> dict:
    """Execute an MCP tool"""

    # Get server config
    server = await registry.get_server(server_name)

    # Initialize session if needed
    session_id = None
    if server.transport == MCPTransportType.STREAMABLE_HTTP:
        session_id = await self._initialize_session(server)

    # Prepare headers
    headers = {"Content-Type": "application/json"}
    if session_id:
        headers["mcp-session-id"] = session_id
    if server.api_key:
        headers["Authorization"] = f"Bearer {server.api_key}"

    # Call tool
    payload = {
        "jsonrpc": "2.0",
        "id": random.randint(1, 1000000),
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }

    async with httpx.AsyncClient(timeout=server.timeout) as client:
        response = await client.post(
            server.url,
            json=payload,
            headers=headers
        )

        # Parse SSE response
        result = self._parse_sse_response(response.text)

        return result
```

---

## Issues Fixed During Implementation

### 1. Missing Initialize Sequence ❌ → ✅

**Problem**: Direct `tools/list` call without initialization

**Error**: `HTTP 400 "Invalid request parameters"`

**Root Cause**: MCP protocol requires proper handshake before any operations

**Fix**: Added complete initialization sequence in `utils/mcp_registry.py:438-473`

### 2. SSE Response Parsing ❌ → ✅

**Problem**: Responses in `text/event-stream` format not parsed

**Format**:
```
event: message
data: {...json...}
```

**Fix**: Added SSE parsing in both `mcp_registry.py:471-493` and `mcp_client.py:156-167`

### 3. Asyncio Lock Deadlock ❌ → ✅

**Problem**: `register_server()` acquired lock, then called `_discover_tools()` which tried to acquire same lock → deadlock

**Error**: Supervisor hung after "📋 Found 1 tools from 'corporate'"

**Root Cause**: Python's `asyncio.Lock` is **not reentrant** - the same coroutine cannot acquire a lock it already holds

**Fix**: Removed nested lock acquisition in `_discover_tools()` (line 410)

---

## Testing

### Test 1: Tool Discovery

**Script**: `scripts/test_corporate_prompts.py`

```bash
python scripts/test_corporate_prompts.py
```

**Expected Output**:
```
✓ Corporate server: healthy
✓ Prompts discovered: 1
✓ Tools discovered: 1
✓ Tool: query_database
```

### Test 2: Session Management

**Verify session initialization in logs**:

```bash
python -m servers.supervisor_server
```

**Expected Log Output**:
```
INFO:utils.mcp_registry:Registering MCP server 'corporate' (type: remote, transport: streamable_http)
INFO:httpx:HTTP Request: POST http://localhost:8005/mcp "HTTP/1.1 200 OK"        # initialize
INFO:httpx:HTTP Request: POST http://localhost:8005/mcp "HTTP/1.1 202 Accepted" # notifications/initialized
INFO:httpx:HTTP Request: POST http://localhost:8005/mcp "HTTP/1.1 200 OK"        # tools/list
INFO:utils.mcp_registry:📋 Found 1 tools from 'corporate'
INFO:utils.mcp_registry:MCP Registry initialized: 1/1 servers healthy, 1 tools available
```

---

## Configuration

### Environment Variables

```bash
# Enable MCP
MCP_ENABLE=true

# Server Configuration
MCP_SERVER_CORPORATE_TYPE=remote
MCP_SERVER_CORPORATE_TRANSPORT=streamable_http
MCP_SERVER_CORPORATE_URL=http://localhost:8005/mcp
MCP_SERVER_CORPORATE_API_KEY=secret123  # Optional
MCP_SERVER_CORPORATE_ENABLED=true
MCP_SERVER_CORPORATE_TIMEOUT=30.0

# Client Configuration
MCP_CLIENT_RETRY_ATTEMPTS=3
MCP_CLIENT_TIMEOUT=30.0
MCP_HEALTH_CHECK_INTERVAL=60.0
```

---

## Key Learnings

1. **MCP Protocol is Stateful**: Must initialize session before any operations
2. **FastMCP Uses SSE Format**: Even for Streamable HTTP transport
3. **Asyncio Locks Are Not Reentrant**: Careful with nested `async with lock`
4. **Session Management Critical**: Session ID must persist across requests
5. **Health Check Returns 400**: A `400` with `mcp-session-id` indicates server is alive

---

## Next Steps

- [**Manual Prompts Configuration**](manual-prompts.md) - Add prompts for tools without prompts/list
- [**Testing Guide**](testing.md) - Complete MCP testing workflow
- [**Troubleshooting**](troubleshooting.md) - Debug common issues

---

**Related Files**:
- `utils/mcp_registry.py` - MCP server registry implementation
- `utils/mcp_client.py` - MCP tool execution client
- `config.py` - MCP configuration parsing
- `.env` - MCP server configuration

**Last Updated**: 2025-10-06
