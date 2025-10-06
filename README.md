# Cortex Flow

A distributed multi-agent AI system implementing the Model Context Protocol (MCP) for scalable, specialized agent collaboration.

## Overview

Cortex Flow is a microservices-based AI agent ecosystem where multiple specialized agents run on independent servers and communicate via HTTP using a standardized MCP protocol. Built with LangChain, LangGraph, and FastAPI, it enables complex workflows through agent orchestration and specialization.

### Key Features

- 🤖 **Multi-Agent Architecture**: Specialized agents (Supervisor, Researcher, Analyst, Writer) working in coordination
- 🔄 **ReAct Pattern**: Transparent reasoning with Thought→Action→Observation cycles
- 📊 **LangGraph Orchestration**: Stateful workflow graphs with persistent checkpointing
- 🌐 **Distributed Communication**: HTTP-based MCP protocol for inter-agent messaging
- ⚡ **Async Performance**: Non-blocking I/O throughout the stack
- 🔍 **Full Observability**: LangSmith integration for distributed tracing

### Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────┐
│   Supervisor    │ ◄─── Orchestrates workflow
│   Agent Server  │
└────────┬────────┘
         │ MCP Protocol (HTTP)
    ┌────┴─────────┬──────────┬─────────┐
    ▼              ▼          ▼         ▼
┌─────────┐  ┌─────────┐ ┌────────┐ ┌────────┐
│Research │  │ Reddit  │ │Analyst │ │Writer  │
│ Agent   │  │ Agent   │ │ Agent  │ │ Agent  │
└─────────┘  └─────────┘ └────────┘ └────────┘
```

## Project Implementation Checklist

### Phase 1: Foundation Setup

- [ ] **Environment Configuration**
  - [ ] Create virtual environment (`python -m venv .venv`)
  - [ ] Copy `.env.example` to `.env`
  - [ ] Configure API keys in `.env`:
    - [ ] `OPENAI_API_KEY`
    - [ ] `ANTHROPIC_API_KEY`
    - [ ] `GOOGLE_API_KEY` (optional)
    - [ ] `GROQ_API_KEY` (optional)
    - [ ] `OPENROUTER_API_KEY` (optional)
  - [ ] Install dependencies (`pip install -r requirements.txt`)

- [ ] **Project Structure**
  - [ ] Create `agents/` directory for LangGraph agent definitions
  - [ ] Create `servers/` directory for FastAPI server implementations
  - [ ] Create `tools/` directory for tool implementations
  - [ ] Create `schemas/` directory for Pydantic models
  - [ ] Create `config.py` for centralized configuration

### Phase 2: Core Infrastructure

- [ ] **MCP Protocol Definition**
  - [ ] Define `MCPRequest` Pydantic model in `schemas/mcp_protocol.py`
  - [ ] Define `MCPResponse` Pydantic model
  - [ ] Add validation logic for protocol fields
  - [ ] Document protocol specification

- [ ] **Configuration Management**
  - [ ] Create `Settings` class using Pydantic `BaseSettings` in `config.py`
  - [ ] Add environment variable loading
  - [ ] Configure LLM provider settings
  - [ ] Add database/Redis connection settings
  - [ ] Configure LangSmith tracing settings

- [ ] **State Management**
  - [ ] Set up PostgreSQL or Redis for production checkpointing
  - [ ] Create checkpoint configuration
  - [ ] Implement state schema base class
  - [ ] Test state persistence and recovery

### Phase 3: Agent Implementation

- [ ] **Base Agent Components**
  - [ ] Create base agent state TypedDict
  - [ ] Implement base agent node (LLM invocation)
  - [ ] Implement base tool execution node
  - [ ] Create conditional edge logic (should_continue)
  - [ ] Add END node routing

- [ ] **Web Researcher Agent**
  - [ ] Define `ResearcherState` in `agents/researcher.py`
  - [ ] Implement Tavily web search tool in `tools/web_tools.py`
  - [ ] Build LangGraph StateGraph for researcher
  - [ ] Add specialized research prompt
  - [ ] Create FastAPI server in `servers/researcher_server.py`
  - [ ] Implement `/invoke` endpoint
  - [ ] Test standalone researcher functionality

- [ ] **Reddit Agent**
  - [ ] Define `RedditState` in `agents/reddit.py`
  - [ ] Implement Reddit API tool in `tools/social_tools.py`
  - [ ] Build LangGraph StateGraph
  - [ ] Add Reddit-specific prompt engineering
  - [ ] Create FastAPI server in `servers/reddit_server.py`
  - [ ] Implement `/invoke` endpoint
  - [ ] Test Reddit data retrieval

- [ ] **Analyst Agent**
  - [ ] Define `AnalystState` in `agents/analyst.py`
  - [ ] Implement data synthesis tools
  - [ ] Build LangGraph StateGraph with analysis logic
  - [ ] Add analytical prompt with structured output
  - [ ] Create FastAPI server in `servers/analyst_server.py`
  - [ ] Implement `/invoke` endpoint
  - [ ] Test analysis capabilities

- [ ] **Writer Agent**
  - [ ] Define `WriterState` in `agents/writer.py`
  - [ ] Build LangGraph StateGraph for content generation
  - [ ] Add writing style prompt templates
  - [ ] Create FastAPI server in `servers/writer_server.py`
  - [ ] Implement `/invoke` endpoint
  - [ ] Test report generation

### Phase 4: Orchestration Layer

- [ ] **Proxy Tools**
  - [ ] Implement `web_research_proxy_tool` in `tools/proxy_tools.py`
  - [ ] Implement `reddit_proxy_tool`
  - [ ] Implement `analyst_proxy_tool`
  - [ ] Implement `writer_proxy_tool`
  - [ ] Add error handling and retry logic
  - [ ] Add timeout configuration
  - [ ] Implement circuit breaker pattern

- [ ] **Supervisor Agent**
  - [ ] Define `SupervisorState` in `agents/supervisor.py`
  - [ ] Attach all proxy tools to supervisor
  - [ ] Build orchestration LangGraph StateGraph
  - [ ] Add planning and delegation prompt
  - [ ] Implement multi-step workflow logic
  - [ ] Create FastAPI server in `servers/supervisor_server.py`
  - [ ] Implement `/invoke` endpoint
  - [ ] Test end-to-end workflow

### Phase 5: Integration & Communication

- [ ] **HTTP Client Configuration**
  - [ ] Implement shared `httpx.AsyncClient` instance
  - [ ] Configure connection pooling
  - [ ] Add timeout settings
  - [ ] Implement request/response logging

- [ ] **Service Discovery**
  - [ ] Define server URLs in configuration
  - [ ] Implement environment-based endpoint resolution
  - [ ] Add health check endpoints to all servers
  - [ ] Create service registry (optional for advanced setup)

- [ ] **Error Handling**
  - [ ] Implement retry logic with exponential backoff
  - [ ] Add circuit breaker for failing services
  - [ ] Create standardized error response format
  - [ ] Add fallback strategies for agent failures

### Phase 6: Deployment & Operations

- [ ] **Containerization**
  - [ ] Create `Dockerfile` for each agent server
  - [ ] Use multi-stage builds for optimization
  - [ ] Create `docker-compose.yml` for local orchestration
  - [ ] Configure container networking
  - [ ] Add volume mounts for development

- [ ] **Observability**
  - [ ] Configure LangSmith API key
  - [ ] Enable tracing in all agents
  - [ ] Implement structured logging
  - [ ] Add performance metrics collection
  - [ ] Create debugging dashboard

- [ ] **Security**
  - [ ] Implement API key authentication for `/invoke` endpoints
  - [ ] Add HTTPS support for production
  - [ ] Configure CORS policies
  - [ ] Implement rate limiting
  - [ ] Add input validation and sanitization
  - [ ] Set up secrets management (HashiCorp Vault)

### Phase 7: Testing & Validation

- [ ] **Unit Tests**
  - [ ] Test individual agent graph execution
  - [ ] Test tool implementations
  - [ ] Test MCP protocol serialization/deserialization
  - [ ] Test state persistence and recovery

- [ ] **Integration Tests**
  - [ ] Test agent-to-agent communication
  - [ ] Test full workflow execution
  - [ ] Test error scenarios and recovery
  - [ ] Test concurrent request handling

- [ ] **Performance Tests**
  - [ ] Benchmark individual agent latency
  - [ ] Benchmark end-to-end workflow latency
  - [ ] Test system under load
  - [ ] Identify and optimize bottlenecks

### Phase 8: Documentation & Refinement

- [ ] **Technical Documentation**
  - [ ] Document MCP protocol specification
  - [ ] Create API documentation (OpenAPI/Swagger)
  - [ ] Document agent roles and capabilities
  - [ ] Create architecture diagrams
  - [ ] Write deployment guide

- [ ] **Developer Documentation**
  - [ ] Create "Adding a New Agent" guide
  - [ ] Document configuration options
  - [ ] Create troubleshooting guide
  - [ ] Add code examples and tutorials

- [ ] **Production Readiness**
  - [ ] Implement monitoring and alerting
  - [ ] Create runbooks for common operations
  - [ ] Set up CI/CD pipeline
  - [ ] Configure production environment
  - [ ] Perform security audit

## Quick Start

### Option 1: Local Development

```bash
# 1. Setup environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure API keys
cp .env.example .env
# Edit .env and add at minimum: OPENAI_API_KEY

# 3. Start all agents
./scripts/start_all.sh

# 4. Test the system
python tests/test_system.py

# Or test manually with curl:
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "demo-001",
    "source_agent_id": "client",
    "target_agent_id": "supervisor",
    "task_description": "What is LangGraph?",
    "context": {}
  }'

# 5. Stop all agents
./scripts/stop_all.sh
```

### Option 2: Docker Compose

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and add your API keys

# 2a. Start all services (full profile)
docker-compose --profile=full up --build

# 2b. Or start only specific agents
docker-compose --profile=minimal --profile=research up  # Supervisor + Researcher only

# 3. Test the system (in another terminal)
python tests/test_system.py

# 4. Stop all services
docker-compose down
```

### Option 3: Selective Agent Deployment

Start only the agents you need:

```bash
# Edit .env to enable only specific agents
ENABLED_AGENTS=researcher,writer  # Disable analyst

# Start configured agents
./scripts/start_all.sh
```

### Accessing the System

- **Supervisor API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

Individual agents (if needed):
- Researcher: http://localhost:8001
- Analyst: http://localhost:8003
- Writer: http://localhost:8004

## Technology Stack

- **Framework**: FastAPI (async web framework)
- **Agent Engine**: LangGraph (stateful agent orchestration)
- **LLM Integration**: LangChain
- **Service Discovery**: Custom registry with health monitoring
- **State Persistence**: PostgreSQL or Redis
- **HTTP Client**: httpx (async)
- **Observability**: LangSmith
- **Containerization**: Docker & Docker Compose
- **Configuration**: Pydantic BaseSettings

## New Features 🆕

### Dynamic Agent Management

- **Configurable Agents**: Enable/disable agents via `.env` configuration
- **Service Discovery**: Automatic registration and health monitoring
- **Graceful Degradation**: System adapts when agents are unavailable
- **Docker Profiles**: Deploy only the agents you need
- **Retry Logic**: Automatic retry with exponential backoff
- **Health Monitoring**: Continuous background health checks

**See [AGENT_MANAGEMENT.md](AGENT_MANAGEMENT.md) for complete guide**

### Key Capabilities

```bash
# Run only researcher and writer
ENABLED_AGENTS=researcher,writer

# System automatically:
✅ Registers available agents
✅ Updates supervisor tools dynamically
✅ Handles agent failures gracefully
✅ Retries with exponential backoff
✅ Provides user-friendly error messages
```

## Project Status

🚧 **Under Development** - This project is currently in the planning/implementation phase. Follow the checklist above to track progress.

## Contributing

When implementing features:

1. Follow the architectural patterns in `docs/` directory
2. Maintain async operations throughout
3. Use Pydantic for all data validation
4. Implement proper error handling and logging
5. Add tests for new functionality
6. Update this checklist as items are completed

## Documentation

📚 **Complete documentation is available in the [`docs/`](docs/) directory**

### Quick Links

- **[Getting Started](docs/getting-started/README.md)** - Setup and first workflow
- **[Architecture Overview](docs/architecture/README.md)** - System design and patterns
- **[Agents Guide](docs/agents/README.md)** - ReAct agents and strategies
- **[MCP Integration](docs/mcp/README.md)** - External tool integration
- **[Workflows](docs/workflows/README.md)** - Template-based execution
- **[Development Guide](docs/development/README.md)** - Contributing and testing
- **[Configuration Reference](docs/reference/README.md)** - All settings and APIs

### External Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Model Context Protocol](https://spec.modelcontextprotocol.io/)

## License

[Add license information]

## Support

[Add support/contact information]
