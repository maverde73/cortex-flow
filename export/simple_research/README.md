# simple_research MCP Server

Simple reusable research workflow - building block for larger workflows

## Overview

This is a standalone MCP (Model Context Protocol) server that executes the `simple_research` workflow.
It includes all necessary dependencies and can run independently.

## Dependencies

### Agents
- researcher
- analyst

### Workflows
- simple_research

### MCP Tools
- None (standalone mode)

## Setup

1. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure LLM Provider**

   Copy `.env.example` to `.env` and configure your preferred LLM provider:
   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and add your API keys.

## Running the Server

### Standard Mode (stdio)
```bash
python server.py
```

### HTTP Mode
```bash
python server.py --transport streamable-http --port 8000
```

### Using Docker
```bash
# Build the image
docker-compose build

# Run the server
docker-compose up
```

## Available Tools

The server exposes the following MCP tools:

### execute_workflow
Execute the main workflow with parameters.

Parameters:
{
  "query": "latest technology trends"
}

### describe_workflow
Get detailed information about the workflow including dependencies and structure.

### list_available_workflows
List all workflows available in this server.

### get_workflow_parameters
Get the required and optional parameters for the main workflow.

### validate_parameters
Validate parameters before executing the workflow.

## Usage Example

### Via MCP Client
```python
from mcp import Client

client = Client()
await client.connect_stdio(["python", "server.py"])

# Execute the workflow
result = await client.call_tool(
    "execute_workflow",
    {
        "query": "latest technology trends"
}
)
print(result)
```

### Via HTTP API
```bash
curl -X POST http://localhost:8000/mcp/tools/execute_workflow \
  -H "Content-Type: application/json" \
  -d '{"query": "latest technology trends"}'
```

## LLM Provider Support

This server supports multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Groq (Mixtral, Llama)
- OpenRouter (Multiple models)
- Ollama (Local models)

The provider is auto-detected based on available API keys, or you can specify one explicitly.

## Logging

Logs are written to the `logs/` directory. Set `LOG_LEVEL` in your `.env` file to control verbosity:
- `DEBUG`: Detailed debugging information
- `INFO`: General information (default)
- `WARNING`: Warnings and errors only
- `ERROR`: Errors only

## License

This exported MCP server is part of the Cortex Flow project.
