# Reference Documentation

Complete reference for Cortex-Flow configuration, APIs, and command-line tools.

---

## Configuration Reference

### Environment Variables

All configuration in Cortex-Flow is done via environment variables in `.env`.

#### LLM Configuration

```bash
# API Keys (at least one required)
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GOOGLE_API_KEY=your_key
GROQ_API_KEY=your_key
OPENROUTER_API_KEY=your_key  # Recommended

# Default model for all agents
DEFAULT_MODEL=openai/gpt-4o-mini

# Per-agent models (optional)
SUPERVISOR_MODEL=openai/gpt-4o-mini
RESEARCHER_MODEL=anthropic/claude-sonnet-4-20250514
ANALYST_MODEL=openai/gpt-4o
WRITER_MODEL=anthropic/claude-opus-4-20250514

# LLM parameters
TEMPERATURE=0.7
MAX_ITERATIONS=10
```

#### Server Configuration

```bash
# Supervisor
SUPERVISOR_HOST=localhost
SUPERVISOR_PORT=8000

# Researcher
RESEARCHER_HOST=localhost
RESEARCHER_PORT=8001

# Analyst
ANALYST_HOST=localhost
ANALYST_PORT=8003

# Writer
WRITER_HOST=localhost
WRITER_PORT=8004

# HTTP client
HTTP_TIMEOUT=120.0
HTTP_MAX_CONNECTIONS=100
HTTP_MAX_KEEPALIVE_CONNECTIONS=20
```

#### ReAct Configuration

```bash
# Execution control
REACT_TIMEOUT_SECONDS=120.0
REACT_ENABLE_EARLY_STOPPING=true
REACT_MAX_CONSECUTIVE_ERRORS=3

# Logging
REACT_ENABLE_VERBOSE_LOGGING=true
REACT_LOG_THOUGHTS=true
REACT_LOG_ACTIONS=true
REACT_LOG_OBSERVATIONS=true

# Strategies (per-agent)
SUPERVISOR_REACT_STRATEGY=fast
RESEARCHER_REACT_STRATEGY=deep
ANALYST_REACT_STRATEGY=balanced
WRITER_REACT_STRATEGY=creative

# Self-reflection
REACT_ENABLE_REFLECTION=false
REACT_REFLECTION_QUALITY_THRESHOLD=0.7
REACT_REFLECTION_MAX_ITERATIONS=2

# Per-agent reflection
WRITER_ENABLE_REFLECTION=true
WRITER_REFLECTION_THRESHOLD=0.8
WRITER_REFLECTION_MAX_ITERATIONS=3

# Human-in-the-Loop
REACT_ENABLE_HITL=false
REACT_HITL_TIMEOUT_SECONDS=300.0
REACT_HITL_TIMEOUT_ACTION=reject  # or approve

# Per-agent HITL
WRITER_ENABLE_HITL=false
WRITER_HITL_REQUIRE_APPROVAL_FOR=publish_*,send_*,delete_*
WRITER_HITL_TIMEOUT_SECONDS=600.0
```

#### State Management

```bash
# Backend type
CHECKPOINT_BACKEND=memory  # or postgres, redis

# PostgreSQL
POSTGRES_URL=postgresql://user:password@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0
```

#### MCP Integration

```bash
# Master switch
MCP_ENABLE=false

# Client configuration
MCP_CLIENT_RETRY_ATTEMPTS=3
MCP_CLIENT_TIMEOUT=30.0
MCP_HEALTH_CHECK_INTERVAL=60.0

# ReAct integration
MCP_TOOLS_ENABLE_LOGGING=true
MCP_TOOLS_ENABLE_REFLECTION=false
MCP_TOOLS_TIMEOUT_MULTIPLIER=1.5

# Server configuration pattern
MCP_SERVER_{NAME}_TYPE=remote|local
MCP_SERVER_{NAME}_TRANSPORT=streamable_http|sse|stdio
MCP_SERVER_{NAME}_URL=http://...
MCP_SERVER_{NAME}_API_KEY=secret
MCP_SERVER_{NAME}_ENABLED=true
MCP_SERVER_{NAME}_TIMEOUT=30.0
MCP_SERVER_{NAME}_PROMPTS_FILE=/path/to/prompt.md
MCP_SERVER_{NAME}_PROMPT_TOOL_ASSOCIATION=tool_name
```

#### Workflow Configuration

```bash
# Workflow mode
WORKFLOW_ENABLE=false
WORKFLOW_MODE=hybrid  # react, template, hybrid
WORKFLOW_TEMPLATES_DIR=workflows/templates
WORKFLOW_AUTO_CLASSIFY=true
WORKFLOW_FALLBACK_TO_REACT=true
WORKFLOW_PARALLEL_MAX_WORKERS=5
```

#### Tool Configuration

```bash
# External tools
TAVILY_API_KEY=your_key
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret

# Agent management
ENABLED_AGENTS=researcher,analyst,writer
AGENT_RETRY_ATTEMPTS=3
AGENT_HEALTH_CHECK_INTERVAL=30.0
```

#### Observability

```bash
# LangSmith
LANGSMITH_API_KEY=your_key
LANGSMITH_PROJECT=cortex-flow
LANGSMITH_TRACING=false
```

---

## REST API Reference

### Supervisor Agent

**Base URL**: `http://localhost:8000`

#### POST /invoke

Execute a task with the supervisor agent.

**Request**:
```json
{
  "task_id": "unique-id",
  "source_agent_id": "user",
  "target_agent_id": "supervisor",
  "task_description": "Your task here",
  "context": {},
  "response": null
}
```

**Response**:
```json
{
  "task_id": "unique-id",
  "source_agent_id": "user",
  "target_agent_id": "supervisor",
  "task_description": "Your task here",
  "context": {...},
  "response": "Agent's response here"
}
```

#### GET /health

Check agent health.

**Response**:
```json
{
  "status": "healthy",
  "agent": "supervisor",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

#### GET /react_history/{task_id}

Get ReAct execution history for a task.

**Response**:
```json
{
  "task_id": "unique-id",
  "agent_name": "supervisor",
  "events": [
    {
      "event_type": "thought",
      "iteration": 1,
      "timestamp": "2025-10-06T10:00:00Z",
      "content": "..."
    }
  ],
  "summary": {
    "total_duration_ms": 5000,
    "total_events": 10,
    "event_counts": {...}
  }
}
```

### Other Agents

All agents (researcher, analyst, writer) expose the same endpoints:

- **Researcher**: `http://localhost:8001`
- **Analyst**: `http://localhost:8003`
- **Writer**: `http://localhost:8004`

---

## Command-Line Tools

### Agent Management

```bash
# Start all agents
./scripts/start_all.sh

# Stop all agents
./scripts/stop_all.sh

# Health check all agents
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_fase2_strategies.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run by marker
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m fase2
```

### MCP Testing

```bash
# Test MCP server discovery
python scripts/test_corporate_prompts.py

# Test LangChain tool integration
python scripts/test_langchain_tool_prompts.py
```

### Database Management

```bash
# Start PostgreSQL
docker-compose -f docker-compose.postgres.yml up -d

# Stop PostgreSQL
docker-compose -f docker-compose.postgres.yml down

# Connect to PostgreSQL
psql postgresql://cortex:cortex_dev_password@localhost:5432/cortex_flow
```

---

## Data Models

### MCPRequest (Agent Communication)

```python
class MCPRequest(BaseModel):
    task_id: str
    source_agent_id: str
    target_agent_id: str
    task_description: str
    context: dict
    response: Optional[str] = None
```

### ReActStrategy

```python
class ReActStrategy(str, Enum):
    FAST = "fast"        # 3 iter, 30s, temp 0.3
    BALANCED = "balanced"  # 10 iter, 120s, temp 0.7
    DEEP = "deep"        # 20 iter, 300s, temp 0.7
    CREATIVE = "creative"  # 15 iter, 180s, temp 0.9
```

### ReflectionResult

```python
class ReflectionResult(BaseModel):
    quality_score: float  # 0.0-1.0
    decision: ReflectionDecision  # ACCEPT, REFINE, INSUFFICIENT
    reasoning: str
    suggestions: List[str]
```

### MCPServerConfig

```python
class MCPServerConfig(BaseModel):
    name: str
    server_type: MCPServerType  # remote, local
    transport: MCPTransportType  # streamable_http, sse, stdio
    url: Optional[str]
    api_key: Optional[str]
    local_path: Optional[str]
    enabled: bool = True
    timeout: float = 30.0
    prompts_file: Optional[str]
    prompt_tool_association: Optional[str]
```

---

## Performance Benchmarks

### Latency by Strategy

| Strategy | Avg Latency | P95 Latency | P99 Latency |
|----------|-------------|-------------|-------------|
| FAST | 3-10s | 15s | 30s |
| BALANCED | 10-30s | 60s | 120s |
| DEEP | 30-120s | 180s | 300s |
| CREATIVE | 15-60s | 120s | 180s |

### Resource Usage

| Component | CPU (idle) | CPU (active) | Memory |
|-----------|------------|--------------|--------|
| Supervisor | 1% | 10-20% | 100MB |
| Researcher | 1% | 15-30% | 150MB |
| Analyst | 1% | 10-20% | 120MB |
| Writer | 1% | 20-40% | 180MB |
| PostgreSQL | 1% | 5-10% | 50MB |

---

## Error Codes

### HTTP Status Codes

- `200 OK`: Success
- `400 Bad Request`: Invalid request payload
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Agent execution error
- `503 Service Unavailable`: Agent not ready

### Agent Error Codes

- `TIMEOUT`: Execution exceeded timeout
- `MAX_ITERATIONS`: Reached iteration limit
- `TOOL_ERROR`: Tool execution failed
- `VALIDATION_ERROR`: Input validation failed
- `CONNECTION_ERROR`: Failed to connect to downstream agent

---

## Related Documentation

- [**Environment Variables**](environment-variables.md) - Complete variable reference
- [**Configuration API**](configuration.md) - config.py and Pydantic settings
- [**REST API**](api.md) - Detailed API documentation
- [**CLI Tools**](cli.md) - Command-line utilities

---

**Last Updated**: 2025-10-06
