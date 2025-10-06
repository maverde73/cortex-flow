# MCP Troubleshooting Guide

Common issues and solutions for MCP integration in Cortex-Flow.

---

## Configuration Issues

### Server Not Registered

**Symptoms**:
- No "Registering MCP server" in logs
- `MCP Registry initialized: 0/0 servers`

**Possible Causes**:

#### 1. MCP Not Enabled

**Check**: `.env` has `MCP_ENABLE=true`

```bash
grep "MCP_ENABLE" .env
```

**Fix**:
```bash
MCP_ENABLE=true
```

#### 2. Invalid Server Configuration

**Check**: Server has required parameters

For remote servers:
```bash
MCP_SERVER_X_TYPE=remote
MCP_SERVER_X_URL=http://...    # REQUIRED
```

For local servers:
```bash
MCP_SERVER_X_TYPE=local
MCP_SERVER_X_LOCAL_PATH=/...   # REQUIRED
```

**Fix**: Add missing required parameter

#### 3. Server Disabled

**Check**: Server `ENABLED` parameter

```bash
grep "MCP_SERVER_.*_ENABLED" .env
```

**Fix**:
```bash
MCP_SERVER_MYSERVER_ENABLED=true
```

#### 4. Supervisor Not Restarted

**Problem**: `.env` changes require restart

**Fix**:
```bash
# Stop supervisor
pkill -f supervisor_server

# Restart
python -m servers.supervisor_server
```

---

## Connection Issues

### Connection Refused

**Symptoms**:
```
ERROR:utils.mcp_registry:Failed to connect to MCP server 'corporate'
ERROR:httpx:ConnectionRefusedError
```

**Possible Causes**:

#### 1. Server Not Running

**Check**: Is the MCP server running?

```bash
# For remote servers
curl http://localhost:8005/mcp

# Check process
ps aux | grep mcp
```

**Fix**: Start the MCP server

```bash
# Example: FastMCP server
python my_mcp_server.py
```

#### 2. Wrong URL

**Check**: URL in `.env` matches actual server

```bash
grep "MCP_SERVER_.*_URL" .env
```

**Fix**: Correct the URL
```bash
MCP_SERVER_CORPORATE_URL=http://localhost:8005/mcp
```

#### 3. Firewall/Network Block

**Check**: Can you reach the server?

```bash
# Test connectivity
curl -v http://localhost:8005/mcp

# Check firewall
sudo iptables -L | grep 8005
```

**Fix**: Allow connection through firewall

---

### HTTP 401 Unauthorized

**Symptoms**:
```
ERROR:httpx:HTTP Request: POST http://localhost:8005/mcp "HTTP/1.1 401 Unauthorized"
```

**Possible Causes**:

#### API Key Missing or Wrong

**Check**: API key configured correctly

```bash
grep "MCP_SERVER_.*_API_KEY" .env
```

**Fix**: Add or correct API key
```bash
MCP_SERVER_CORPORATE_API_KEY=your_correct_api_key
```

---

### HTTP 400 Bad Request (During Operations)

**Symptoms**:
```
ERROR:utils.mcp_registry:HTTP Request: POST http://localhost:8005/mcp "HTTP/1.1 400 Bad Request"
```

**Note**: A `400` during **health check** is normal. A `400` during **operations** is an error.

**Possible Causes**:

#### 1. Missing Session Initialization

**Problem**: Calling `tools/list` or `tools/call` without initializing session

**Check**: Logs show initialization sequence

```bash
grep "initialize" supervisor.log
```

**Expected**:
```
HTTP Request: POST http://localhost:8005/mcp "HTTP/1.1 200 OK"    # initialize
HTTP Request: POST http://localhost:8005/mcp "HTTP/1.1 202 Accepted"  # notifications/initialized
```

**Fix**: Already implemented in `utils/mcp_registry.py:438-473`. If this fails, check MCP server logs.

#### 2. Invalid JSON-RPC Request

**Problem**: Malformed request payload

**Check**: Enable verbose HTTP logging

```python
import logging
logging.getLogger("httpx").setLevel(logging.DEBUG)
```

**Fix**: Report issue with logs

---

### HTTP 500 Internal Server Error

**Symptoms**:
```
ERROR:httpx:HTTP Request: POST http://localhost:8005/mcp "HTTP/1.1 500 Internal Server Error"
```

**Possible Causes**:

#### MCP Server Error

**Check**: MCP server logs for errors

```bash
# Check MCP server logs
tail -f mcp_server.log
```

**Fix**: Fix error in MCP server implementation

---

## Discovery Issues

### No Tools Discovered

**Symptoms**:
```
INFO:utils.mcp_registry:📋 Found 0 tools from 'corporate'
```

**Possible Causes**:

#### 1. MCP Server Has No Tools

**Check**: MCP server implements tools

```bash
# Test tools/list manually
curl -X POST http://localhost:8005/mcp \
  -H "Content-Type: application/json" \
  -H "mcp-session-id: test-123" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

**Fix**: Implement tools in MCP server

#### 2. Session Not Initialized

**Check**: Session initialization succeeded

```bash
grep "mcp-session-id" supervisor.log
```

**Fix**: Check MCP server session handling

#### 3. SSE Parsing Failed

**Check**: Response format is SSE

```bash
# Check response format
curl -v http://localhost:8005/mcp
```

Expected:
```
Content-Type: text/event-stream

event: message
data: {...json...}
```

**Fix**: Ensure MCP server returns SSE format

---

### No Prompts Discovered

**Symptoms**:
```
INFO:utils.mcp_registry:📋 Found 0 prompts from 'corporate'
```

**Possible Causes**:

#### 1. Server Doesn't Expose Prompts

**Problem**: MCP server doesn't implement `prompts/list`

**Solution**: Use manual prompts configuration

See [Manual Prompts](manual-prompts.md) for details.

#### 2. Manual Prompt File Not Found

**Check**: Prompt file exists

```bash
ls -la /path/to/PROMPT.md
```

**Fix**: Create prompt file or correct path

```bash
MCP_SERVER_CORPORATE_PROMPTS_FILE=/correct/path/to/PROMPT.md
```

#### 3. Wrong File Path

**Check**: Path is absolute, not relative

❌ Wrong:
```bash
MCP_SERVER_CORPORATE_PROMPTS_FILE=./prompts/PROMPT.md
```

✅ Correct:
```bash
MCP_SERVER_CORPORATE_PROMPTS_FILE=/home/user/project/prompts/PROMPT.md
```

---

## Execution Issues

### Tool Call Failed

**Symptoms**:
```
ERROR:utils.mcp_client:Tool call failed: query_database
```

**Possible Causes**:

#### 1. Invalid Arguments

**Check**: Arguments match tool input schema

**Example**: Tool expects:
```json
{
  "query_payload": {
    "table": "employees",
    "select": ["*"]
  }
}
```

But received:
```json
{
  "table": "employees"  // Wrong: missing query_payload wrapper
}
```

**Fix**: Validate arguments against tool schema

#### 2. Session Expired

**Problem**: Session ID no longer valid

**Check**: Session timeout in MCP server

**Fix**: Increase timeout or implement session refresh

#### 3. MCP Server Error

**Check**: MCP server logs for execution errors

**Fix**: Debug MCP server tool implementation

---

### Tool Call Timeout

**Symptoms**:
```
ERROR:utils.mcp_client:Tool call timeout after 30.0 seconds
```

**Possible Causes**:

#### 1. Timeout Too Short

**Check**: Timeout configuration

```bash
grep "TIMEOUT" .env | grep MCP_SERVER
```

**Fix**: Increase timeout
```bash
MCP_SERVER_CORPORATE_TIMEOUT=60.0
```

#### 2. Slow MCP Server

**Problem**: Tool takes longer than expected

**Fix**: Optimize tool implementation or increase timeout

---

## Prompt Issues

### Prompt Not Injected

**Symptoms**: LangChain tool description doesn't include prompt

**Check**: Run test script

```bash
python scripts/test_langchain_tool_prompts.py
```

**Possible Causes**:

#### 1. Prompt Not Associated

**Check**: `PROMPT_TOOL_ASSOCIATION` configured

```bash
grep "PROMPT_TOOL_ASSOCIATION" .env
```

**Fix**: Add association
```bash
MCP_SERVER_CORPORATE_PROMPT_TOOL_ASSOCIATION=query_database
```

#### 2. Tool Name Mismatch

**Problem**: Association uses wrong tool name

**Check**: Actual tool name from discovery

```bash
grep "Found.*tools" supervisor.log
```

**Fix**: Use exact tool name
```bash
MCP_SERVER_CORPORATE_PROMPT_TOOL_ASSOCIATION=query_database  # Exact match
```

#### 3. Prompt File Empty

**Check**: File has content

```bash
wc -l /path/to/PROMPT.md
```

**Fix**: Add content to prompt file

---

## Performance Issues

### Slow Tool Discovery

**Symptoms**: Supervisor startup takes > 30 seconds

**Possible Causes**:

#### 1. Many MCP Servers

**Problem**: Each server requires HTTP round-trips

**Fix**: Disable unused servers
```bash
MCP_SERVER_UNUSED_ENABLED=false
```

#### 2. High Timeout

**Problem**: Timeout is too high for unavailable servers

**Fix**: Reduce timeout for dev environments
```bash
MCP_SERVER_CORPORATE_TIMEOUT=10.0
```

---

### Slow Tool Execution

**Symptoms**: MCP tool calls take > 5 seconds

**Possible Causes**:

#### 1. Network Latency

**Problem**: Remote MCP server is far away

**Fix**: Deploy MCP server closer or use local cache

#### 2. Heavy Computation

**Problem**: Tool performs slow operations

**Fix**: Optimize tool implementation or use async processing

---

## Debugging Techniques

### Enable Verbose Logging

```python
# In supervisor_server.py
import logging

# MCP registry logs
logging.getLogger("utils.mcp_registry").setLevel(logging.DEBUG)

# HTTP request logs
logging.getLogger("httpx").setLevel(logging.DEBUG)

# MCP client logs
logging.getLogger("utils.mcp_client").setLevel(logging.DEBUG)
```

### Test MCP Server Manually

```bash
# 1. Initialize session
curl -v -X POST http://localhost:8005/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 0,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "1.0"}
    }
  }'

# 2. Extract mcp-session-id from response headers

# 3. Send initialized notification
curl -X POST http://localhost:8005/mcp \
  -H "Content-Type: application/json" \
  -H "mcp-session-id: <session-id>" \
  -d '{"jsonrpc": "2.0", "method": "notifications/initialized"}'

# 4. List tools
curl -X POST http://localhost:8005/mcp \
  -H "Content-Type: application/json" \
  -H "mcp-session-id: <session-id>" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# 5. Call tool
curl -X POST http://localhost:8005/mcp \
  -H "Content-Type: application/json" \
  -H "mcp-session-id: <session-id>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "query_database",
      "arguments": {...}
    }
  }'
```

### Test MCP Integration

```bash
# Test server health and tool discovery
python scripts/test_corporate_prompts.py

# Test prompt injection
python scripts/test_langchain_tool_prompts.py
```

### Check Configuration Parsing

```python
# In Python REPL
from config import settings
print(settings.mcp_enable)
print(settings.mcp_servers)
```

---

## Common Error Messages

### "Remote MCP server 'X' requires 'url'"

**Cause**: Missing `URL` parameter for remote server

**Fix**: Add URL
```bash
MCP_SERVER_X_URL=http://localhost:8005/mcp
```

### "Local MCP server 'X' requires 'local_path'"

**Cause**: Missing `LOCAL_PATH` parameter for local server

**Fix**: Add local path
```bash
MCP_SERVER_X_LOCAL_PATH=/path/to/server.py
```

### "MCP server 'X' is not healthy"

**Cause**: Server failed health check

**Fix**: Check server is running and accessible

### "Failed to parse SSE response"

**Cause**: Response not in SSE format

**Fix**: Ensure MCP server returns `Content-Type: text/event-stream`

### "Tool 'X' not found in registry"

**Cause**: Tool not discovered or wrong name

**Fix**: Check tool discovery logs, verify tool name

---

## Getting Help

If you're still stuck:

1. **Check Logs**: Look for errors in supervisor logs
2. **Test Manually**: Use curl to test MCP server directly
3. **Run Tests**: Use provided test scripts
4. **Review Docs**: Check [Configuration Reference](configuration.md)
5. **Report Issue**: Provide logs and configuration (redact secrets!)

---

## Useful Commands

```bash
# Check MCP configuration
grep "MCP" .env | grep -v "^#"

# Check supervisor logs
grep -E "(MCP|ERROR)" supervisor.log | tail -20

# Test MCP server connectivity
curl -v http://localhost:8005/mcp

# Restart supervisor
pkill -f supervisor_server && python -m servers.supervisor_server

# Run MCP tests
python scripts/test_corporate_prompts.py
python scripts/test_langchain_tool_prompts.py
```

---

## Next Steps

- [**Getting Started**](getting-started.md) - Setup guide
- [**Configuration Reference**](configuration.md) - All parameters
- [**Protocol Implementation**](protocol-implementation.md) - Technical details

---

**Last Updated**: 2025-10-06
