# Getting Started with MCP

This guide walks you through integrating your first MCP server with Cortex-Flow.

---

## Prerequisites

- Cortex-Flow installed and configured
- An MCP server running (or a Python file with FastMCP implementation)
- Basic understanding of environment variables

---

## Step 1: Enable MCP

Edit your `.env` file:

```bash
MCP_ENABLE=true
```

This is the **master switch** for MCP integration. Without it, all MCP servers are ignored.

---

## Step 2: Choose Your Integration Type

### Option A: Remote MCP Server (HTTP)

For external MCP servers accessible via HTTP.

**Example**: Corporate database server on `http://localhost:8005/mcp`

```bash
# Server type and transport
MCP_SERVER_CORPORATE_TYPE=remote
MCP_SERVER_CORPORATE_TRANSPORT=streamable_http

# Connection details
MCP_SERVER_CORPORATE_URL=http://localhost:8005/mcp
MCP_SERVER_CORPORATE_ENABLED=true
MCP_SERVER_CORPORATE_TIMEOUT=30.0

# Optional: Authentication
MCP_SERVER_CORPORATE_API_KEY=your_api_key_here
```

### Option B: Local MCP Server (Python Module)

For MCP servers in local Python files.

**Example**: Local tools in `my_mcp_server.py`

```bash
# Server type and transport
MCP_SERVER_LOCAL_TYPE=local
MCP_SERVER_LOCAL_TRANSPORT=stdio

# File path
MCP_SERVER_LOCAL_LOCAL_PATH=/home/user/project/my_mcp_server.py
MCP_SERVER_LOCAL_ENABLED=true
```

---

## Step 3: Start the Supervisor

```bash
python -m servers.supervisor_server
```

Watch the logs for successful registration:

```
INFO:utils.mcp_registry:Registering MCP server 'corporate' (type: remote, transport: streamable_http)
INFO:httpx:HTTP Request: POST http://localhost:8005/mcp "HTTP/1.1 200 OK"
INFO:utils.mcp_registry:📋 Found 1 tools from 'corporate'
INFO:utils.mcp_registry:✅ MCP server 'corporate' registered successfully with 1 tools
INFO:utils.mcp_registry:MCP Registry initialized: 1/1 servers healthy, 1 tools available
```

✅ **Success!** Your MCP server is now integrated.

---

## Step 4: Verify Integration

### Method 1: Check Logs

Look for these messages in the supervisor logs:

```bash
grep "MCP" supervisor.log
```

Expected output:
```
INFO:utils.mcp_registry:Registering MCP server 'corporate'
INFO:utils.mcp_registry:📋 Found 1 tools from 'corporate'
INFO:utils.mcp_registry:MCP Registry initialized: 1/1 servers healthy, 1 tools available
```

### Method 2: Run Test Script

```bash
python scripts/test_corporate_prompts.py
```

Expected output:
```
✓ Corporate server: healthy
✓ Tools discovered: 1
✓ Tool: query_database
```

---

## Step 5: Use MCP Tools

MCP tools are automatically available to ReAct agents.

### In ReAct Pattern

The supervisor agent can now use MCP tools:

**User request**: "Query the database for active employees"

**Supervisor reasoning**:
```
THOUGHT: I need to query the corporate database. I see the query_database tool is available.
ACTION: query_database({"table": "employees", "where": {"status": "active"}})
OBSERVATION: [{"id": 1, "name": "John Doe", ...}, ...]
```

### In Workflows

Add MCP tools to workflow templates:

```json
{
  "id": "query_db",
  "agent": "mcp_tool",
  "tool_name": "query_database",
  "instruction": "Query the employees table",
  "params": {
    "query_payload": {
      "table": "employees",
      "select": ["*"],
      "limit": 10
    }
  }
}
```

---

## Common Scenarios

### Scenario 1: Corporate Database (Remote)

```bash
MCP_ENABLE=true

MCP_SERVER_CORPORATE_TYPE=remote
MCP_SERVER_CORPORATE_TRANSPORT=streamable_http
MCP_SERVER_CORPORATE_URL=http://localhost:8005/mcp
MCP_SERVER_CORPORATE_ENABLED=true
MCP_SERVER_CORPORATE_TIMEOUT=30.0
```

### Scenario 2: Internal API with Auth (Remote)

```bash
MCP_ENABLE=true

MCP_SERVER_API_TYPE=remote
MCP_SERVER_API_TRANSPORT=streamable_http
MCP_SERVER_API_URL=https://internal-api.company.com/mcp
MCP_SERVER_API_API_KEY=${INTERNAL_API_KEY}
MCP_SERVER_API_ENABLED=true
MCP_SERVER_API_TIMEOUT=60.0
```

### Scenario 3: Local Python Tools (Local)

```bash
MCP_ENABLE=true

MCP_SERVER_LOCAL_TYPE=local
MCP_SERVER_LOCAL_TRANSPORT=stdio
MCP_SERVER_LOCAL_LOCAL_PATH=/home/user/cortex-flow/tools/my_tools.py
MCP_SERVER_LOCAL_ENABLED=true
```

### Scenario 4: Multiple Servers

```bash
MCP_ENABLE=true

# Corporate database
MCP_SERVER_CORPORATE_TYPE=remote
MCP_SERVER_CORPORATE_TRANSPORT=streamable_http
MCP_SERVER_CORPORATE_URL=http://localhost:8005/mcp
MCP_SERVER_CORPORATE_ENABLED=true

# CRM API
MCP_SERVER_CRM_TYPE=remote
MCP_SERVER_CRM_TRANSPORT=streamable_http
MCP_SERVER_CRM_URL=https://crm-api.company.com/mcp
MCP_SERVER_CRM_API_KEY=${CRM_API_KEY}
MCP_SERVER_CRM_ENABLED=true

# Local utilities
MCP_SERVER_UTILS_TYPE=local
MCP_SERVER_UTILS_TRANSPORT=stdio
MCP_SERVER_UTILS_LOCAL_PATH=/app/utils_server.py
MCP_SERVER_UTILS_ENABLED=true
```

---

## Next Steps

### Add Manual Prompts

If your MCP server doesn't expose prompts via `prompts/list`:

1. Create a markdown file with tool documentation
2. Configure `PROMPTS_FILE` and `PROMPT_TOOL_ASSOCIATION`

See [Manual Prompts](manual-prompts.md) for details.

### Configure Workflows

Use MCP tools in workflow templates:

See [Workflows MCP Integration](../workflows/03_mcp_integration.md) for details.

### Monitor Health

Enable health checks:

```bash
MCP_HEALTH_CHECK_INTERVAL=60.0
```

---

## Troubleshooting

### Server Not Discovered

**Symptoms**:
- No "Registering MCP server" log message
- `MCP Registry initialized: 0/0 servers`

**Check**:
1. `MCP_ENABLE=true` is set
2. Server configuration has required parameters
3. Server name matches pattern: `MCP_SERVER_{NAME}_*`
4. Restart supervisor after `.env` changes

**Debug**:
```bash
grep "MCP_SERVER" .env
```

### Connection Failed

**Symptoms**:
```
ERROR:utils.mcp_registry:Failed to connect to MCP server 'corporate'
ERROR:httpx:HTTP Request: POST http://localhost:8005/mcp "ConnectionError"
```

**Check**:
1. MCP server is running: `curl http://localhost:8005/mcp`
2. URL is correct in `.env`
3. Firewall/network allows connection
4. API key is correct (if required)

**Debug**:
```bash
# Test connection manually
curl -X POST http://localhost:8005/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

### Tools Not Discovered

**Symptoms**:
```
INFO:utils.mcp_registry:📋 Found 0 tools from 'corporate'
```

**Check**:
1. MCP server implements `tools/list` correctly
2. Session initialization succeeded
3. No errors in MCP server logs

**Debug**:
```bash
# Check tool discovery manually
python scripts/test_corporate_prompts.py
```

### See More

Full troubleshooting guide: [Troubleshooting](troubleshooting.md)

---

## Complete Example

Here's a complete `.env` configuration for a remote MCP server with manual prompts:

```bash
# ============================================================================
# MCP INTEGRATION
# ============================================================================

# Enable MCP
MCP_ENABLE=true

# Corporate Database Server
MCP_SERVER_CORPORATE_TYPE=remote
MCP_SERVER_CORPORATE_TRANSPORT=streamable_http
MCP_SERVER_CORPORATE_URL=http://localhost:8005/mcp
MCP_SERVER_CORPORATE_ENABLED=true
MCP_SERVER_CORPORATE_TIMEOUT=30.0

# Manual prompts for database schema
MCP_SERVER_CORPORATE_PROMPTS_FILE=/home/user/project/prompts/database_schema.md
MCP_SERVER_CORPORATE_PROMPT_TOOL_ASSOCIATION=query_database

# Client configuration
MCP_CLIENT_RETRY_ATTEMPTS=3
MCP_CLIENT_TIMEOUT=30.0
MCP_HEALTH_CHECK_INTERVAL=60.0

# ReAct integration
MCP_TOOLS_ENABLE_LOGGING=true
MCP_TOOLS_ENABLE_REFLECTION=false
MCP_TOOLS_TIMEOUT_MULTIPLIER=1.5
```

---

## Learn More

- [**MCP Overview**](README.md) - What is MCP and why use it
- [**Protocol Implementation**](protocol-implementation.md) - Technical details
- [**Configuration Reference**](configuration.md) - All environment variables
- [**Manual Prompts**](manual-prompts.md) - Adding prompts for tools
- [**Troubleshooting**](troubleshooting.md) - Debug common issues

---

**Last Updated**: 2025-10-06
