# Architecture Overview

Cortex-Flow implements a **distributed multi-agent AI system** using modern architectural patterns and technologies.

---

## Key Architectural Principles

### 1. Microservices Architecture
- **Independent Agents**: Each agent runs as a separate FastAPI server
- **Loose Coupling**: Agents communicate via HTTP using standardized MCP protocol
- **Scalability**: Each agent can be scaled independently
- **Fault Isolation**: Failures in one agent don't affect others

### 2. ReAct Pattern
- **Reasoning-Action-Observation Cycle**: LLM-driven iterative problem solving
- **Tool Integration**: Agents use tools to interact with external systems
- **State Management**: LangGraph maintains execution state
- **Checkpointing**: PostgreSQL for production-grade persistence

### 3. Configuration as Code
- **Pydantic BaseSettings**: Type-safe configuration management
- **Environment Variables**: All configuration via `.env`
- **No GUI**: Fully programmable configuration
- **GitOps Ready**: Configuration stored in version control

---

## System Components

### Multi-Agent System

```
┌─────────────────────────────────────────────────────────┐
│                 User / External Client                   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │   Supervisor Agent     │  Port 8000
            │  (Orchestrator)        │  Strategy: FAST
            └────────┬───────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Researcher   │ │   Analyst    │ │   Writer     │
│ Port 8001    │ │  Port 8003   │ │  Port 8004   │
│ Strategy:    │ │  Strategy:   │ │  Strategy:   │
│ DEEP         │ │  BALANCED    │ │  CREATIVE    │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Agent Specializations

| Agent | Role | Strategy | Tools | Reflection |
|-------|------|----------|-------|------------|
| **Supervisor** | Orchestrator | FAST (3 iter, 30s) | Agent delegation | No |
| **Researcher** | Web research | DEEP (20 iter, 300s) | Tavily Search | Optional |
| **Analyst** | Data analysis | BALANCED (10 iter, 120s) | Analysis tools | Optional |
| **Writer** | Content creation | CREATIVE (15 iter, 180s) | Writing tools | **Yes** (0.8 threshold) |

---

## Technology Stack

### Core Framework
- **LangGraph 0.6.8**: State graph orchestration
- **LangChain Core 0.3.78**: LLM integration and tools
- **FastAPI**: High-performance async API framework
- **Pydantic**: Data validation and settings management

### LLM Providers
- **OpenRouter** (Recommended): Access to 100+ models
- **OpenAI**: GPT-4, GPT-4o, GPT-3.5
- **Anthropic**: Claude Sonnet, Opus
- **Google**: Gemini models
- **Groq**: Fast inference

### Infrastructure
- **PostgreSQL 16**: Production state persistence
- **Redis** (Optional): Caching and pub/sub
- **Docker**: Containerization
- **Docker Compose**: Local development orchestration

---

## Execution Flow

### 1. Request Processing

```
User Query
    ↓
Supervisor receives request
    ↓
Supervisor analyzes task
    ↓
Supervisor creates execution plan
```

### 2. Task Delegation

```
Supervisor delegates to:
    ├─ Researcher (for information gathering)
    ├─ Analyst (for data analysis)
    └─ Writer (for content generation)

Each agent:
    1. Receives task via HTTP POST
    2. Executes ReAct cycle
    3. Returns result to Supervisor
```

### 3. Result Synthesis

```
Supervisor collects results
    ↓
Supervisor synthesizes final answer
    ↓
Returns to user
```

---

## Data Flow

### Request/Response Protocol

Each agent communicates using a standardized MCP-like protocol:

```json
{
  "task_id": "unique-id",
  "source_agent_id": "supervisor",
  "target_agent_id": "researcher",
  "task_description": "Search for information about X",
  "context": {
    "previous_results": {},
    "constraints": {}
  },
  "response": null
}
```

### State Management

LangGraph maintains execution state with:
- **Memory**: Development only, ephemeral
- **PostgreSQL**: Production, persistent across restarts
- **Redis** (Future): Distributed caching

---

## Architectural Patterns

### 1. Domain-Driven Structure

Each agent is organized by domain:

```
agents/
├── supervisor.py      # Orchestration domain
├── researcher.py      # Research domain
├── analyst.py         # Analysis domain
└── writer.py          # Writing domain

servers/
├── supervisor_server.py
├── researcher_server.py
├── analyst_server.py
└── writer_server.py
```

### 2. Dependency Injection

FastAPI's DI system for loose coupling:

```python
from fastapi import Depends
from typing import Annotated

async def get_llm():
    return create_llm_from_config()

@app.post("/invoke")
async def invoke(
    request: MCPRequest,
    llm: Annotated[ChatOpenAI, Depends(get_llm)]
):
    # LLM is injected, not hardcoded
    pass
```

### 3. Repository Pattern

Separation of data access logic:

```python
class AgentRepository:
    """Abstract data access"""
    async def save_state(self, task_id: str, state: dict)
    async def load_state(self, task_id: str) -> dict

class PostgresAgentRepository(AgentRepository):
    """Concrete PostgreSQL implementation"""
    pass
```

---

## Scalability Considerations

### Horizontal Scaling
- Each agent can run multiple instances behind a load balancer
- Stateless execution (state in PostgreSQL)
- Session affinity not required

### Vertical Scaling
- Async I/O prevents thread blocking
- Connection pooling for database and HTTP
- Configurable worker processes

### Performance Optimization
- Connection pooling (max 20 per agent)
- HTTP keep-alive between agents
- LLM response caching (optional)
- Tool result caching (optional)

---

## Security Architecture

### Authentication
- API keys for agent-to-agent communication
- JWT tokens for external clients
- OAuth2 for user authentication (optional)

### Data Security
- Secrets in environment variables (never in code)
- PostgreSQL credentials encrypted
- HTTPS for inter-agent communication (production)

### Network Security
- Internal network for agent communication
- API gateway for external access
- Rate limiting per agent
- CORS configuration

---

## Resilience Patterns

### 1. Retry Logic
- Exponential backoff for failed HTTP calls
- Configurable max retry attempts (default: 3)
- Idempotent operations for safety

### 2. Circuit Breaker
- Monitor agent health
- Fail fast when agent is down
- Auto-recovery after timeout

### 3. Timeout Control
- Per-agent timeout configuration
- Per-strategy timeout (FAST: 30s, DEEP: 300s)
- Graceful timeout handling

### 4. Error Isolation
- Agent failures don't cascade
- Supervisor handles partial results
- Detailed error logging

---

## Documentation

### Detailed Guides
- [**Backend Design**](backend-design.md) - Microservices architecture blueprint
- [**Multi-Agent System**](multi-agent-system.md) - ReAct pattern and coordination
- [**Project Structure**](project-structure.md) - File organization and modules
- [**Implementation Summary**](implementation-summary.md) - Current state and features

### Related Documentation
- [Agents Overview](../agents/README.md) - Agent implementation details
- [MCP Integration](../mcp/README.md) - External tool integration
- [Workflows](../workflows/README.md) - Template-based execution

---

## Architecture Evolution

### Phase 1: Foundation ✅
- Multi-agent architecture
- ReAct pattern
- Basic orchestration
- Memory-based state

### Phase 2: Production Ready ✅
- PostgreSQL persistence
- ReAct strategies
- Self-reflection
- Structured logging

### Phase 3: Advanced Features (In Progress)
- Human-in-the-Loop (85% complete)
- MCP server integration
- Workflow templates
- Visual diagrams

### Phase 4: Future
- Advanced reasoning modes (CoT, ToT, Adaptive)
- Metrics and optimization
- Auto-tuning
- Multi-modal support

---

**Last Updated**: 2025-10-06
