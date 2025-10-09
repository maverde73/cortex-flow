# research_and_report MCP Server

Composable workflow: Executes multi-source research then generates a report

## Overview

This is a standalone MCP (Model Context Protocol) server that executes the `research_and_report` workflow.
It includes all necessary dependencies and can run independently.

## Dependencies

### Agents
- analyst
- researcher
- writer

### Workflows
- research_and_report
- report_generation
- multi_source_research

### MCP Tools
- query_database

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
  "topic": "Artificial Intelligence trends 2024",
  "table_name": "research_data",
  "report_type": "executive_summary",
  "format": "markdown"
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
        "topic": "Artificial Intelligence trends 2024",
        "table_name": "research_data",
        "report_type": "executive_summary",
        "format": "markdown"
}
)
print(result)
```

### Via HTTP API
```bash
# Default port is 8000, change MCP_PORT in .env if needed
curl -X POST http://localhost:8000/mcp/tools/execute_workflow \
  -H "Content-Type: application/json" \
  -d '{"topic": "Artificial Intelligence trends 2024", "table_name": "research_data", "report_type": "executive_summary", "format": "markdown"}'
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
