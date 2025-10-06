# MCP Configuration Reference

Complete reference for all MCP-related environment variables in Cortex-Flow.

---

## Master Switch

### MCP_ENABLE

**Type**: Boolean
**Default**: `false`
**Required**: Yes (to use MCP)

Enable or disable MCP integration globally.

```bash
MCP_ENABLE=true
```

When `false`, all MCP servers are ignored and no MCP tools are registered.

---

## Server Configuration Pattern

Each MCP server is configured using this pattern:

```bash
MCP_SERVER_{NAME}_{PARAMETER}={VALUE}
```

Where:
- `{NAME}` is your server identifier (e.g., `CORPORATE`, `LOCAL_TOOLS`)
- `{PARAMETER}` is the configuration parameter

### Example: Corporate Server

```bash
MCP_SERVER_CORPORATE_TYPE=remote
MCP_SERVER_CORPORATE_TRANSPORT=streamable_http
MCP_SERVER_CORPORATE_URL=http://localhost:8005/mcp
MCP_SERVER_CORPORATE_API_KEY=secret123
MCP_SERVER_CORPORATE_ENABLED=true
MCP_SERVER_CORPORATE_TIMEOUT=30.0
MCP_SERVER_CORPORATE_PROMPTS_FILE=/path/to/PROMPT.md
MCP_SERVER_CORPORATE_PROMPT_TOOL_ASSOCIATION=query_database
```

---

## Server Parameters

### TYPE (Required)

**Values**: `remote` | `local`
**Default**: `remote`

Defines whether the MCP server is remote (HTTP-based) or local (Python module).

```bash
MCP_SERVER_MYSERVER_TYPE=remote
```

**Use Cases**:
- `remote`: External MCP servers (APIs, services)
- `local`: Python files in the project

---

### TRANSPORT (Required)

**Values**: `streamable_http` | `sse` | `stdio`
**Default**: `streamable_http`

Defines the transport protocol for communication.

```bash
MCP_SERVER_MYSERVER_TRANSPORT=streamable_http
```

**Transport Types**:

| Transport | Type | Use Case | Status |
|-----------|------|----------|--------|
| `streamable_http` | Remote | Modern HTTP streaming | ✅ Recommended |
| `sse` | Remote | Server-Sent Events (legacy) | ✅ Supported |
| `stdio` | Local | Standard I/O | ✅ Supported |

---

### URL (Required for Remote)

**Type**: String (URL)
**Default**: None

Full URL to the remote MCP server endpoint.

```bash
MCP_SERVER_MYSERVER_URL=http://localhost:8005/mcp
```

**Examples**:
```bash
# Local development
MCP_SERVER_DEV_URL=http://localhost:8001/mcp

# Production
MCP_SERVER_PROD_URL=https://api.example.com/mcp

# Internal service
MCP_SERVER_INTERNAL_URL=http://mcp-server.svc.cluster.local:8000
```

---

### LOCAL_PATH (Required for Local)

**Type**: String (File Path)
**Default**: None

Absolute path to the Python file containing the MCP server implementation.

```bash
MCP_SERVER_MYSERVER_LOCAL_PATH=/home/user/project/mcp_server.py
```

**Requirements**:
- File must exist
- File must be a valid Python module
- File must contain FastMCP server implementation

---

### API_KEY (Optional)

**Type**: String
**Default**: None

Bearer token for authentication with remote MCP servers.

```bash
MCP_SERVER_MYSERVER_API_KEY=your_secret_api_key_here
```

**Usage**: Added as `Authorization: Bearer {API_KEY}` header in all requests.

---

### ENABLED (Optional)

**Type**: Boolean
**Default**: `true`

Enable or disable a specific MCP server without removing its configuration.

```bash
MCP_SERVER_MYSERVER_ENABLED=false
```

**Use Cases**:
- Temporarily disable a server
- Testing with subset of servers
- Conditional environments (dev vs prod)

---

### TIMEOUT (Optional)

**Type**: Float (seconds)
**Default**: `30.0`

Timeout for HTTP requests to the MCP server.

```bash
MCP_SERVER_MYSERVER_TIMEOUT=60.0
```

**Recommendations**:
- Fast tools: `10.0` - `30.0` seconds
- Database queries: `30.0` - `60.0` seconds
- Heavy computations: `60.0` - `300.0` seconds

---

### PROMPTS_FILE (Optional)

**Type**: String (File Path)
**Default**: None

Path to a markdown/text file containing manual prompt documentation.

```bash
MCP_SERVER_MYSERVER_PROMPTS_FILE=/path/to/PROMPT.md
```

**Use Case**: For servers that don't expose prompts via `prompts/list`.

See [Manual Prompts](manual-prompts.md) for details.

---

### PROMPT_TOOL_ASSOCIATION (Optional)

**Type**: String (Tool Name)
**Default**: None

Associate the manual prompt with a specific tool.

```bash
MCP_SERVER_MYSERVER_PROMPT_TOOL_ASSOCIATION=query_database
```

**Behavior**: The prompt content is injected into the tool's description.

See [Manual Prompts](manual-prompts.md) for details.

---

## Client Configuration

### MCP_CLIENT_RETRY_ATTEMPTS

**Type**: Integer
**Default**: `3`

Number of retry attempts for failed MCP tool calls.

```bash
MCP_CLIENT_RETRY_ATTEMPTS=3
```

**Retry Strategy**: Exponential backoff with jitter.

---

### MCP_CLIENT_TIMEOUT

**Type**: Float (seconds)
**Default**: `30.0`

Global timeout for MCP client operations.

```bash
MCP_CLIENT_TIMEOUT=30.0
```

**Note**: Per-server `TIMEOUT` overrides this value.

---

### MCP_HEALTH_CHECK_INTERVAL

**Type**: Float (seconds)
**Default**: `60.0`

Interval for periodic health checks of MCP servers.

```bash
MCP_HEALTH_CHECK_INTERVAL=60.0
```

**Behavior**:
- Healthy servers: monitored every N seconds
- Failed servers: marked as unhealthy
- Logged for observability

---

## ReAct Integration

### MCP_TOOLS_ENABLE_LOGGING

**Type**: Boolean
**Default**: `true`

Enable detailed logging of MCP tool calls in ReAct reasoning cycle.

```bash
MCP_TOOLS_ENABLE_LOGGING=true
```

**Log Output**:
```
INFO:agents.supervisor:🔧 Calling MCP tool: query_database
INFO:agents.supervisor:📊 MCP tool result: {...}
```

---

### MCP_TOOLS_ENABLE_REFLECTION

**Type**: Boolean
**Default**: `false`

Apply ReAct reflection mechanism to MCP tool results.

```bash
MCP_TOOLS_ENABLE_REFLECTION=true
```

**Behavior**: After MCP tool execution, agent reflects on result quality.

See [ReAct Controls](../agents/react-controls.md) for details.

---

### MCP_TOOLS_TIMEOUT_MULTIPLIER

**Type**: Float
**Default**: `1.5`

Multiply agent timeout for MCP tool calls.

```bash
MCP_TOOLS_TIMEOUT_MULTIPLIER=2.0
```

**Example**: If agent timeout is `120s` and multiplier is `1.5`, MCP tools get `180s`.

---

## Supervisor as MCP Server

### SUPERVISOR_MCP_ENABLE

**Type**: Boolean
**Default**: `false`

Expose the Supervisor agent as an MCP server for external clients.

```bash
SUPERVISOR_MCP_ENABLE=true
```

---

### SUPERVISOR_MCP_PATH

**Type**: String (URL Path)
**Default**: `/mcp`

Endpoint path for MCP protocol on the Supervisor server.

```bash
SUPERVISOR_MCP_PATH=/mcp
```

**Full URL**: `http://localhost:8000/mcp`

---

### SUPERVISOR_MCP_TRANSPORT

**Type**: String
**Default**: `streamable_http`

Transport type for Supervisor MCP server.

```bash
SUPERVISOR_MCP_TRANSPORT=streamable_http
```

---

## Complete Example

### Development Environment

```bash
# Master switch
MCP_ENABLE=true

# Corporate database server
MCP_SERVER_CORPORATE_TYPE=remote
MCP_SERVER_CORPORATE_TRANSPORT=streamable_http
MCP_SERVER_CORPORATE_URL=http://localhost:8005/mcp
MCP_SERVER_CORPORATE_ENABLED=true
MCP_SERVER_CORPORATE_TIMEOUT=30.0
MCP_SERVER_CORPORATE_PROMPTS_FILE=/home/user/project/prompts/database.md
MCP_SERVER_CORPORATE_PROMPT_TOOL_ASSOCIATION=query_database

# Local tools server
MCP_SERVER_LOCAL_TYPE=local
MCP_SERVER_LOCAL_TRANSPORT=stdio
MCP_SERVER_LOCAL_LOCAL_PATH=/home/user/project/local_tools.py
MCP_SERVER_LOCAL_ENABLED=true

# Client config
MCP_CLIENT_RETRY_ATTEMPTS=3
MCP_CLIENT_TIMEOUT=30.0
MCP_HEALTH_CHECK_INTERVAL=60.0

# ReAct integration
MCP_TOOLS_ENABLE_LOGGING=true
MCP_TOOLS_ENABLE_REFLECTION=false
MCP_TOOLS_TIMEOUT_MULTIPLIER=1.5

# Supervisor as MCP server
SUPERVISOR_MCP_ENABLE=true
SUPERVISOR_MCP_PATH=/mcp
SUPERVISOR_MCP_TRANSPORT=streamable_http
```

### Production Environment

```bash
# Master switch
MCP_ENABLE=true

# Production API
MCP_SERVER_PROD_API_TYPE=remote
MCP_SERVER_PROD_API_TRANSPORT=streamable_http
MCP_SERVER_PROD_API_URL=https://api.example.com/mcp
MCP_SERVER_PROD_API_API_KEY=${PROD_API_KEY}
MCP_SERVER_PROD_API_ENABLED=true
MCP_SERVER_PROD_API_TIMEOUT=60.0

# Internal database
MCP_SERVER_DB_TYPE=remote
MCP_SERVER_DB_TRANSPORT=streamable_http
MCP_SERVER_DB_URL=http://db-mcp.svc.cluster.local:8000/mcp
MCP_SERVER_DB_ENABLED=true
MCP_SERVER_DB_TIMEOUT=30.0
MCP_SERVER_DB_PROMPTS_FILE=/app/prompts/database_schema.md
MCP_SERVER_DB_PROMPT_TOOL_ASSOCIATION=query_database

# Client config (higher retries for production)
MCP_CLIENT_RETRY_ATTEMPTS=5
MCP_CLIENT_TIMEOUT=60.0
MCP_HEALTH_CHECK_INTERVAL=30.0

# ReAct integration
MCP_TOOLS_ENABLE_LOGGING=true
MCP_TOOLS_ENABLE_REFLECTION=false
MCP_TOOLS_TIMEOUT_MULTIPLIER=2.0
```

---

## Validation Rules

### Required Combinations

**For Remote Servers**:
```bash
MCP_SERVER_X_TYPE=remote
MCP_SERVER_X_TRANSPORT=streamable_http|sse
MCP_SERVER_X_URL=http://...      # REQUIRED
```

**For Local Servers**:
```bash
MCP_SERVER_X_TYPE=local
MCP_SERVER_X_TRANSPORT=stdio
MCP_SERVER_X_LOCAL_PATH=/path... # REQUIRED
```

### Invalid Configurations

❌ Remote server without URL:
```bash
MCP_SERVER_X_TYPE=remote
# Missing MCP_SERVER_X_URL
```

❌ Local server with URL:
```bash
MCP_SERVER_X_TYPE=local
MCP_SERVER_X_URL=http://...  # Ignored for local servers
```

❌ STDIO transport for remote:
```bash
MCP_SERVER_X_TYPE=remote
MCP_SERVER_X_TRANSPORT=stdio  # Only for local
```

---

## Naming Conventions

### Server Names

Use UPPERCASE with underscores:

✅ Good:
```bash
MCP_SERVER_CORPORATE_...
MCP_SERVER_LOCAL_TOOLS_...
MCP_SERVER_PROD_API_V2_...
```

❌ Bad:
```bash
MCP_SERVER_corporate_...        # Lowercase
MCP_SERVER_MY-SERVER_...        # Hyphens
MCP_SERVER_MyServer_...         # CamelCase
```

### Tool Names

Use lowercase with underscores (defined by MCP server):

```
query_database
create_ticket
send_email
```

---

## Troubleshooting

### Configuration Not Loaded

**Check**:
1. `.env` file exists in project root
2. Variable names match pattern exactly: `MCP_SERVER_{NAME}_{PARAM}`
3. No typos in parameter names
4. Restart supervisor after `.env` changes

**Debug**:
```python
from config import settings
print(settings.mcp_servers)
```

### Server Not Registered

**Check**:
1. `MCP_ENABLE=true`
2. Server `ENABLED=true`
3. Required parameters provided (URL for remote, LOCAL_PATH for local)
4. No errors in supervisor logs

**Debug**:
```bash
grep "MCP server" supervisor.log
```

---

## Next Steps

- [**Getting Started**](getting-started.md) - Setup your first MCP server
- [**Manual Prompts**](manual-prompts.md) - Configure prompts for tools
- [**Troubleshooting**](troubleshooting.md) - Debug common issues

---

**Related Files**:
- `config.py:348-395` - Configuration parsing implementation
- `.env.example:259-351` - Configuration examples
- `utils/mcp_registry.py` - Server registration logic

**Last Updated**: 2025-10-06
