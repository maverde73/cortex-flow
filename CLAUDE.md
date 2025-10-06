# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **cortex-flow**, an MCP (Model Context Protocol) server designed to implement a distributed multi-agent AI system using LangChain, LangGraph, and FastAPI. The architecture follows a microservices pattern where specialized AI agents run on separate servers and communicate via HTTP using a standardized MCP protocol.

## Project Organization Guidelines

**IMPORTANT**: Keep the project root clean and organized.

### Directory Structure Rules

```
cortex-flow/
├── agents/           # Agent implementations
├── servers/          # FastAPI servers
├── tools/            # Agent tools
├── schemas/          # Pydantic models
├── services/         # Service discovery, health monitoring
├── utils/            # Shared utilities
├── scripts/          # Shell scripts (start_all.sh, stop_all.sh, etc.)
├── tests/            # All test files (test_*.py, *_test.py)
├── docs/             # Documentation (architecture, guides)
├── config.py         # Configuration (allowed in root)
├── requirements.txt  # Dependencies (allowed in root)
├── *.md              # Documentation (allowed in root)
├── docker-compose.yml # Docker config (allowed in root)
└── Dockerfile        # Docker config (allowed in root)
```

### File Placement Rules

**DO:**
- ✅ Place shell scripts in `scripts/` directory
- ✅ Place test files in `tests/` directory
- ✅ Place utility scripts in `scripts/` or `bin/`
- ✅ Place documentation in `docs/` or as `.md` in root
- ✅ Keep config files (`config.py`, `.env`) in root only if necessary

**DON'T:**
- ❌ Place `.sh` scripts in root
- ❌ Place `test_*.py` files in root
- ❌ Place utility/helper scripts in root
- ❌ Create random files in root without purpose

### When Creating New Files

**Scripts:**
```bash
# ❌ DON'T
./new_script.sh

# ✅ DO
./scripts/new_script.sh
```

**Tests:**
```bash
# ❌ DON'T
./test_feature.py

# ✅ DO
./tests/test_feature.py
```

**Utilities:**
```bash
# ❌ DON'T
./helper.py

# ✅ DO
./utils/helper.py
# or
./scripts/helper.py
```

## Key Architecture Principles

### Multi-Agent System Design
- **Distributed Architecture**: Each agent runs as an independent FastAPI server
- **MCP Protocol**: Agents communicate using standardized JSON payloads over HTTP
- **ReAct Pattern**: All agents implement the Reasoning-Action-Observation cycle
- **LangGraph Orchestration**: Each agent's workflow is modeled as a stateful graph
- **Specialization**: Agents have focused roles (Supervisor, Researcher, Analyst, Writer, etc.)

### Architectural Patterns from Documentation
The project follows the architectural blueprint described in "Architettura Backend per Agenti Configurabili.md":
- **Configuration as Code**: All configuration is programmatic using Pydantic BaseSettings
- **Domain-Driven Structure**: Code organized by domain/agent rather than by file type
- **Dependency Injection**: FastAPI's DI system for loose coupling
- **Stateful Workflows**: LangGraph StateGraph with persistent checkpointers (PostgreSQL/Redis)
- **Async I/O**: All I/O operations use `async def` for performance

## Development Setup

### Environment Configuration
1. Copy `.env.example` to `.env` and configure API keys:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY` (note: typo in .env.example as "ANTRHOPIV_API_KEY")
   - `GOOGLE_API_KEY`
   - `GROQ_API_KEY`
   - `OPENROUTER_API_KEY`

2. Install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
pip install -r requirements.txt
```

### Required Dependencies
- `langchain-mcp-adapters`: MCP protocol integration
- `langgraph`: State graph orchestration for agents
- `langchain-openai`: LLM integration
- `python-dotenv`: Environment configuration
- `uvicorn`: ASGI server for FastAPI

## Project Structure (Expected)

Following the recommended pattern from the architectural docs:

```
cortex-flow/
├── agents/                 # Agent definitions (LangGraph graphs)
│   ├── supervisor.py      # Orchestrator agent
│   ├── researcher.py      # Web research specialist
│   ├── analyst.py         # Data analysis specialist
│   └── writer.py          # Report generation specialist
├── servers/               # FastAPI server implementations
│   ├── supervisor_server.py
│   ├── researcher_server.py
│   └── ...
├── tools/                 # Tool implementations
│   ├── web_tools.py      # Direct tools (Tavily, etc.)
│   └── proxy_tools.py    # Cross-server communication tools
├── schemas/              # Pydantic models for MCP protocol
│   └── mcp_protocol.py
├── config.py             # Centralized Pydantic BaseSettings
├── requirements.txt
├── .env.example
└── docs/                 # Architectural documentation
```

## Agent Implementation Guidelines

### LangGraph Agent Structure
Each agent should be implemented as a `StateGraph`:
```python
from langgraph.graph import StateGraph
from typing import TypedDict

class AgentState(TypedDict):
    messages: list  # Message history
    # Additional state fields as needed

# Define nodes (functions that modify state)
def agent_node(state: AgentState) -> dict:
    # Invoke LLM and return state updates
    pass

def tool_node(state: AgentState) -> dict:
    # Execute tools and return observations
    pass

# Build graph
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("action", tool_node)
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("action", "agent")
```

### FastAPI Server Pattern
Each agent server follows this structure:
```python
from fastapi import FastAPI
from pydantic import BaseModel

class MCPRequest(BaseModel):
    task_id: str
    source_agent_id: str
    target_agent_id: str
    task_description: str
    context: dict
    response: str | None = None

app = FastAPI()

@app.post("/invoke")
async def invoke_agent(request: MCPRequest):
    # Extract task and context
    # Invoke local LangGraph agent
    # Return result in response field
    pass
```

### Proxy Tool Pattern
Tools that communicate with other agent servers:
```python
import httpx
from langchain_core.tools import tool

@tool
def research_proxy_tool(query: str) -> str:
    """Delegates to the web research agent."""
    payload = {
        "task_id": generate_id(),
        "source_agent_id": "supervisor",
        "target_agent_id": "researcher",
        "task_description": query,
        "context": {},
        "response": None
    }

    with httpx.Client() as client:
        response = client.post(
            "http://research-server:8000/invoke",
            json=payload,
            timeout=120.0
        )
        result = response.json()
        return result["response"]
```

## Best Practices

### State Management
- **Production**: Use PostgreSQL or Redis for LangGraph checkpointers
- **Never use MemorySaver** in production (ephemeral, lost on pod restart)
- Checkpoint state enables human-in-the-loop workflows

### Async Operations
- All I/O operations must use `async def`
- Use `httpx.AsyncClient` for inter-service communication
- Implement connection pooling for database and HTTP clients

### Error Handling
- Implement retry logic with exponential backoff for cross-server calls
- Use circuit breaker pattern to prevent cascading failures
- Return structured error responses in MCP format

### Security
- Use HTTPS for inter-agent communication in production
- Implement API key or JWT authentication on `/invoke` endpoints
- Never commit `.env` files or expose credentials

### Observability
- Configure **LangSmith** for distributed tracing
- Each cross-server call creates a nested trace
- Monitor latencies at agent boundaries

## Running the System

### Local Development
```bash
# Terminal 1 - Supervisor
uvicorn servers.supervisor_server:app --port 8000

# Terminal 2 - Researcher
uvicorn servers.researcher_server:app --port 8001

# Terminal 3 - Other agents...
```

### Docker Compose (Recommended)
```bash
docker-compose up
```

## Common Workflows

### Adding a New Agent
1. Create agent graph in `agents/{agent_name}.py`
2. Define specialized tools in `tools/`
3. Create FastAPI server in `servers/{agent_name}_server.py`
4. Create proxy tool for supervisor in `tools/proxy_tools.py`
5. Add server configuration to `docker-compose.yml`

### Testing Agent Communication
Use the MCP protocol format directly:
```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-123",
    "source_agent_id": "client",
    "target_agent_id": "supervisor",
    "task_description": "Research latest LangGraph trends",
    "context": {},
    "response": null
  }'
```

## References

The architectural approach is documented in detail in:
- `docs/Architettura Backend per Agenti Configurabili.md` - Full microservices architecture blueprint
- `docs/Guida Agenti ReAct Multi-MCP LangChain.md` - Multi-agent system implementation guide
