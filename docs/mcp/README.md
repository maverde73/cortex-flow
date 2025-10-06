# MCP Integration Overview

**Model Context Protocol (MCP)** integration allows Cortex-Flow to connect to external tools and services via a standardized protocol.

---

## What is MCP?

The **Model Context Protocol** is a universal interface that enables AI agents to:
- **Discover tools** from remote and local servers
- **Execute tools** with validated input schemas
- **Access prompts** for tool usage guidance
- **Maintain sessions** across multiple operations

### Why Use MCP?

- **Unified Interface**: One protocol to connect to any tool provider
- **Dynamic Discovery**: Tools are discovered at runtime, no code changes needed
- **Type Safety**: JSON Schema validation for inputs and outputs
- **Stateful Sessions**: Persistent sessions for complex operations
- **Distributed Architecture**: Tools can run anywhere (local, cloud, on-premise)

---

## Features

Cortex-Flow's MCP integration supports:

✅ **Remote MCP Servers** (HTTP-based)
- Streamable HTTP transport (recommended)
- SSE (Server-Sent Events) transport
- Full MCP 2025-03-26 protocol

✅ **Local MCP Servers** (Python modules)
- Direct Python imports
- STDIO transport
- FastMCP integration

✅ **Manual Prompts Configuration**
- Load prompts from external files
- Associate prompts with tools
- Inject prompts into LangChain tool descriptions

✅ **Tool Discovery & Execution**
- Automatic tool discovery at startup
- JSON Schema validation
- Session management
- Retry logic with exponential backoff

✅ **ReAct Integration**
- MCP tools available in ReAct reasoning cycle
- Detailed logging of MCP tool calls
- Optional reflection on MCP results

✅ **Workflow Integration**
- Use MCP tools in workflow templates
- Auto-populate prompts with `use_mcp_prompt`
- Conditional routing based on MCP results

---

## Quick Start

### 1. Enable MCP

In your `.env` file:

```bash
MCP_ENABLE=true
```

### 2. Configure an MCP Server

Add a remote MCP server:

```bash
# Server configuration
MCP_SERVER_CORPORATE_TYPE=remote
MCP_SERVER_CORPORATE_TRANSPORT=streamable_http
MCP_SERVER_CORPORATE_URL=http://localhost:8005/mcp
MCP_SERVER_CORPORATE_ENABLED=true
MCP_SERVER_CORPORATE_TIMEOUT=30.0

# Optional: Manual prompts
MCP_SERVER_CORPORATE_PROMPTS_FILE=/path/to/PROMPT.md
MCP_SERVER_CORPORATE_PROMPT_TOOL_ASSOCIATION=query_database
```

### 3. Start the Supervisor

```bash
python -m servers.supervisor_server
```

The supervisor will:
1. Connect to configured MCP servers
2. Initialize MCP sessions
3. Discover available tools
4. Register tools in the MCP registry
5. Make tools available to ReAct agents

### 4. Verify Integration

Check the logs for:

```
INFO:utils.mcp_registry:Registering MCP server 'corporate' (type: remote, transport: streamable_http)
INFO:utils.mcp_registry:📋 Found 1 tools from 'corporate'
INFO:utils.mcp_registry:MCP Registry initialized: 1/1 servers healthy, 1 tools available
```

---

## Documentation

### Getting Started
- [**Getting Started with MCP**](getting-started.md) - Step-by-step setup guide
- [**Configuration Reference**](configuration.md) - All MCP environment variables

### Technical Details
- [**Protocol Implementation**](protocol-implementation.md) - MCP protocol specifics
- [**Manual Prompts**](manual-prompts.md) - Configuring prompts for servers without prompts/list
- [**Testing Guide**](testing.md) - Test MCP integration

### Troubleshooting
- [**Common Issues**](troubleshooting.md) - Debugging MCP problems

---

## Architecture

### MCP Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Supervisor Agent                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              MCP Tool Registry                        │  │
│  │  • Tool Discovery                                     │  │
│  │  • Session Management                                 │  │
│  │  • Health Checks                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│              │                                               │
│              ▼                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         LangChain MCP Tool Adapters                   │  │
│  │  • Schema Validation                                  │  │
│  │  • Prompt Injection                                   │  │
│  │  • Error Handling                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Remote     │ │   Remote     │ │    Local     │
│ MCP Server 1 │ │ MCP Server 2 │ │ MCP Server 3 │
│              │ │              │ │              │
│ (HTTP)       │ │ (SSE)        │ │ (STDIO)      │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Data Flow

1. **Startup**: Supervisor discovers tools from all configured MCP servers
2. **Tool Selection**: ReAct agent selects an MCP tool based on task
3. **Execution**: Supervisor calls MCP server via HTTP/STDIO
4. **Response**: MCP server returns result in JSON-RPC format
5. **Observation**: ReAct agent observes result and continues reasoning

---

## Use Cases

### 1. Database Query APIs
Connect to corporate databases via MCP servers:
- Server exposes `query_database` tool
- Manual prompt provides full database schema
- ReAct agents generate zero-hallucination queries

### 2. Internal Tools
Expose internal APIs as MCP tools:
- CRM systems (create tickets, search customers)
- Document management (search, upload, version)
- Workflow automation (trigger builds, deploy)

### 3. AI Models
Access specialized AI models:
- Image generation (DALL-E, Stable Diffusion)
- Speech synthesis (TTS models)
- Computer vision (OCR, object detection)

### 4. External Services
Integrate with cloud services:
- Cloud storage (S3, GCS, Azure)
- Email/SMS gateways
- Payment processors

---

## Next Steps

1. [**Getting Started**](getting-started.md) - Configure your first MCP server
2. [**Protocol Implementation**](protocol-implementation.md) - Understand MCP protocol details
3. [**Manual Prompts**](manual-prompts.md) - Add prompts for tools without prompts/list
4. [**Testing**](testing.md) - Test your MCP integration

---

**Related Documentation**:
- [Workflows MCP Integration](../workflows/03_mcp_integration.md) - Using MCP tools in workflows
- [Agent Management](../agents/agent-management.md) - Health checks and retries
- [Configuration Reference](../reference/configuration.md) - All config options

---

**Last Updated**: 2025-10-06
