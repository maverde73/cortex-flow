# Getting Started with Cortex-Flow

Welcome to Cortex-Flow! This guide will help you set up and run the system in minutes.

---

## Prerequisites

### Required
- **Python** 3.12 or higher
- **pip** (Python package manager)
- At least one **LLM API key**:
  - OpenRouter (recommended) - access to 100+ models
  - OR OpenAI / Anthropic / Google / Groq

### Optional
- **Docker** 20.10+ (for PostgreSQL persistence)
- **docker-compose** 2.0+ (for easy database setup)

---

## Quick Start (5 Minutes)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd cortex-flow

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys (minimum required)
nano .env
```

**Minimum configuration**:
```bash
# LLM Provider (choose one)
OPENROUTER_API_KEY=your_key_here

# OR
OPENAI_API_KEY=your_key_here

# Optional: Web search capability
TAVILY_API_KEY=your_key_here
```

### 3. Start Agents

```bash
# Start all agents at once
./scripts/start_all.sh

# OR start individually in separate terminals:
python -m servers.supervisor_server  # Terminal 1
python -m servers.researcher_server  # Terminal 2
python -m servers.analyst_server     # Terminal 3
python -m servers.writer_server      # Terminal 4
```

### 4. Test the System

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","agent":"supervisor","version":"1.0.0"}
```

✅ **Success!** Cortex-Flow is now running.

---

## Your First Query

### Using cURL

```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-001",
    "source_agent_id": "user",
    "target_agent_id": "supervisor",
    "task_description": "What are the latest trends in AI?",
    "context": {},
    "response": null
  }'
```

### Expected Flow

1. **Supervisor** receives query
2. **Supervisor** delegates to **Researcher**
3. **Researcher** searches web using Tavily
4. **Researcher** returns findings to **Supervisor**
5. **Supervisor** returns final answer

---

## Configuration Options

### LLM Providers

Configure which LLM to use:

```bash
# Default model for all agents
DEFAULT_MODEL=openai/gpt-4o-mini

# Per-agent models (override default)
SUPERVISOR_MODEL=openai/gpt-4o-mini
RESEARCHER_MODEL=anthropic/claude-sonnet-4-20250514
ANALYST_MODEL=openai/gpt-4o
WRITER_MODEL=anthropic/claude-opus-4-20250514
```

### ReAct Strategies

Configure reasoning strategies:

```bash
# Per-agent strategies
SUPERVISOR_REACT_STRATEGY=fast      # Quick coordination
RESEARCHER_REACT_STRATEGY=deep      # Thorough research
ANALYST_REACT_STRATEGY=balanced     # Standard analysis
WRITER_REACT_STRATEGY=creative      # Creative content
```

### Database Persistence (Optional)

By default, agents use in-memory state. For production:

```bash
# Start PostgreSQL
docker-compose -f docker-compose.postgres.yml up -d

# Configure in .env
CHECKPOINT_BACKEND=postgres
POSTGRES_URL=postgresql://cortex:cortex_dev_password@localhost:5432/cortex_flow
```

---

## Common Tasks

### Stopping Agents

```bash
# If using start_all.sh
./scripts/stop_all.sh

# OR manually
pkill -f supervisor_server
pkill -f researcher_server
pkill -f analyst_server
pkill -f writer_server
```

### Checking Logs

```bash
# View supervisor logs
tail -f supervisor.log

# View all agent logs
tail -f *.log
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_fase2_strategies.py -v
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### API Key Not Working

1. Check `.env` file has correct key
2. Ensure no quotes around key value
3. Restart agents after changing `.env`

### Agent Not Responding

1. Check agent is running: `curl http://localhost:8000/health`
2. Check logs for errors: `tail -f supervisor.log`
3. Verify network connectivity between agents

---

## Next Steps

### Learn More
- [**Configuration Guide**](configuration.md) - All environment variables
- [**Quick Start**](quick-start.md) - First workflow tutorial
- [**Architecture**](../architecture/README.md) - How it works

### Add Features
- [**MCP Integration**](../mcp/getting-started.md) - Connect external tools
- [**Workflows**](../workflows/README.md) - Template-based execution
- [**Self-Reflection**](../agents/react-pattern.md) - Quality control

### Deploy to Production
- [**PostgreSQL Setup**](../reference/configuration.md#checkpoint-backend) - Persistent state
- [**Docker Deployment**](../development/README.md) - Containerization
- [**Monitoring**](../reference/api.md) - Health checks and metrics

---

## Getting Help

- **Documentation**: Browse `docs/` folder
- **Examples**: Check `workflows/examples/` for samples
- **Issues**: Report bugs via GitHub Issues
- **Logs**: Always check agent logs first

---

**Last Updated**: 2025-10-06
