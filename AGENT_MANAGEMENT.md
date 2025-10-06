# Agent Management Guide

## Overview

Cortex Flow now supports **dynamic agent management**, allowing you to:
- ✅ Enable/disable agents via configuration
- ✅ Deploy only the agents you need
- ✅ Handle agent failures gracefully
- ✅ Add new agents easily
- ✅ Monitor agent health automatically

## Configuration

### Enabling/Disabling Agents

Edit your `.env` file to control which agents run:

```bash
# Run all agents (default)
ENABLED_AGENTS=researcher,analyst,writer

# Run only researcher and writer
ENABLED_AGENTS=researcher,writer

# Run only researcher
ENABLED_AGENTS=researcher
```

### Retry Configuration

Configure how the system handles temporary agent failures:

```bash
# Number of retry attempts (default: 3)
AGENT_RETRY_ATTEMPTS=3

# Health check interval in seconds (default: 30)
AGENT_HEALTH_CHECK_INTERVAL=30
```

## Local Development

### Start All Configured Agents

```bash
./scripts/start_all.sh
```

This script automatically reads `ENABLED_AGENTS` from `.env` and starts only those agents.

### Start Specific Agents Manually

```bash
# Edit .env
ENABLED_AGENTS=researcher

# Start (only researcher and supervisor will run)
./scripts/start_all.sh
```

### Check Which Agents Are Running

```bash
# View logs
tail -f logs/supervisor.log

# Check health endpoints
curl http://localhost:8000/health  # Supervisor
curl http://localhost:8001/health  # Researcher (if enabled)
curl http://localhost:8003/health  # Analyst (if enabled)
curl http://localhost:8004/health  # Writer (if enabled)
```

## Docker Deployment

### Using Profiles

Docker Compose now supports profiles for flexible deployment:

```bash
# Start all agents
docker-compose --profile=full up

# Start only supervisor + researcher
docker-compose --profile=minimal --profile=research up

# Start supervisor + researcher + writer
docker-compose --profile=minimal --profile=research --profile=writing up

# Start only supervisor (minimal mode)
docker-compose --profile=minimal up
```

### Available Profiles

- `minimal` - Supervisor only (required)
- `research` - Researcher agent
- `analysis` - Analyst agent
- `writing` - Writer agent
- `full` - All agents

### Example: Research-Only Deployment

```bash
# .env file
ENABLED_AGENTS=researcher

# Start containers
docker-compose --profile=minimal --profile=research up
```

## Graceful Degradation

### How It Works

When an agent is unavailable, the system:

1. **Retries** - Attempts to connect multiple times with exponential backoff
2. **Informs** - Returns user-friendly error messages
3. **Continues** - Supervisor can still respond using available agents or its own knowledge

### Example Behavior

```python
# User request: "Create a report on AI trends"

# If all agents are available:
→ Research web for AI trends
→ Analyze the findings
→ Write professional report
→ Return complete report

# If writer is unavailable:
→ Research web for AI trends
→ Analyze the findings
→ ⚠️ "Writer agent is currently unavailable. Here's the analysis: ..."
→ Return analysis without formatted report

# If all specialized agents are down:
→ ⚠️ "Specialized agents are currently unavailable."
→ Supervisor answers based on its own knowledge
→ Suggests trying again later
```

## Adding New Agents

### Step-by-Step Process

#### 1. Create the Agent

```python
# agents/new_agent.py
from langgraph.graph import StateGraph, END
from schemas.agent_state import BaseAgentState

def create_new_agent():
    # Define your agent logic
    workflow = StateGraph(BaseAgentState)
    # ... agent implementation
    return workflow.compile()

_agent = None

async def get_new_agent():
    global _agent
    if _agent is None:
        _agent = create_new_agent()
    return _agent
```

#### 2. Create the Server

```python
# servers/new_agent_server.py
from fastapi import FastAPI
from agents.new_agent import get_new_agent
# ... standard server setup
```

#### 3. Add Configuration

```python
# config.py - add URL property
@property
def new_agent_url(self) -> str:
    return f"http://{self.new_agent_host}:{self.new_agent_port}"
```

```bash
# .env - add configuration
NEW_AGENT_HOST=localhost
NEW_AGENT_PORT=8005
ENABLED_AGENTS=researcher,analyst,writer,new_agent
```

#### 4. Create Proxy Tool

```python
# tools/proxy_tools.py
@tool
async def use_new_agent(task: str) -> str:
    """Delegate to the new agent."""
    return await _call_agent_async(
        agent_url=settings.new_agent_url,
        agent_id="new_agent",
        task_description=task
    )
```

#### 5. Register in Factory

```python
# agents/factory.py
async def get_available_tools():
    # ... existing code ...

    # Add new agent
    if "new_agent" in available_agents:
        tools.append(proxy_tools.use_new_agent)
        tool_descriptions.append(
            "4. **use_new_agent**: Description of what it does"
        )
```

#### 6. Update Registry

```python
# services/registry.py - in initialize_registry_from_config()
agents_config = {
    "researcher": settings.researcher_url,
    "analyst": settings.analyst_url,
    "writer": settings.writer_url,
    "new_agent": settings.new_agent_url,  # Add here
}
```

#### 7. Add to Docker Compose

```yaml
# docker-compose.yml
services:
  new_agent:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: cortex-new-agent
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "8005:8000"
    command: python servers/new_agent_server.py
    networks:
      - cortex-network
    profiles:
      - full
      - custom_profile
```

#### 8. Update Start Script

```bash
# scripts/start_all.sh - add section
if is_enabled "new_agent"; then
    echo "🆕 Starting New Agent (port 8005)..."
    python servers/new_agent_server.py > logs/new_agent.log 2>&1 &
    NEW_AGENT_PID=$!
fi
```

That's it! Your new agent is now integrated into the system.

## Health Monitoring

### Automatic Monitoring

The system automatically monitors agent health every 30 seconds (configurable):

```bash
# Adjust monitoring interval
AGENT_HEALTH_CHECK_INTERVAL=60  # Check every 60 seconds
```

### View Health Status

Check logs to see health status updates:

```bash
tail -f logs/supervisor.log | grep -i health
```

### Manual Health Check

```bash
# Python script
python -c "
import asyncio
from services.registry import get_registry

async def check():
    registry = get_registry()
    available = await registry.get_available_agents()
    print(f'Available agents: {available}')

asyncio.run(check())
"
```

## Troubleshooting

### Agent Shows as Unavailable

1. **Check if enabled**:
   ```bash
   grep ENABLED_AGENTS .env
   ```

2. **Check if running**:
   ```bash
   ps aux | grep "agent_server.py"
   ```

3. **Check logs**:
   ```bash
   tail -f logs/researcher.log
   ```

4. **Restart agent**:
   ```bash
   ./scripts/stop_all.sh
   ./scripts/start_all.sh
   ```

### Retry Exhausted Errors

If you see "Failed after N attempts":

1. **Increase retry attempts**:
   ```bash
   AGENT_RETRY_ATTEMPTS=5
   ```

2. **Check network connectivity**:
   ```bash
   curl http://localhost:8001/health
   ```

3. **Verify agent is healthy**:
   Check agent's own logs for errors

### Supervisor Not Finding Agents

1. **Check registry initialization**:
   Look for "Registered X agents" in supervisor logs

2. **Verify ENABLED_AGENTS matches running agents**

3. **Restart supervisor to re-initialize**:
   ```bash
   pkill -f supervisor_server.py
   python servers/supervisor_server.py
   ```

## Best Practices

### Development

- **Start minimal**: Begin with just researcher for development
- **Enable on-demand**: Add agents as needed for specific tasks
- **Monitor logs**: Keep an eye on `logs/supervisor.log` for health updates

### Production

- **Use Docker profiles**: Deploy only what you need
- **Set appropriate retries**: Balance responsiveness vs resilience
- **Monitor health**: Set up alerting on agent failures
- **Have fallbacks**: Design workflows that degrade gracefully

### Cost Optimization

```bash
# For simple tasks, just researcher might be enough
ENABLED_AGENTS=researcher

# For analysis tasks
ENABLED_AGENTS=researcher,analyst

# For full workflow
ENABLED_AGENTS=researcher,analyst,writer
```

## Examples

### Example 1: Research-Only Setup

```bash
# .env
ENABLED_AGENTS=researcher
```

```bash
# Start
./scripts/start_all.sh

# Test
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"task_description": "What is LangGraph?"}'
```

Result: Supervisor delegates to researcher, returns results directly.

### Example 2: Analysis Without Writing

```bash
# .env
ENABLED_AGENTS=researcher,analyst
```

Result: Can research and analyze, but final formatting will be done by supervisor.

### Example 3: Adding Custom Agent

See "Adding New Agents" section above for complete walkthrough.

## Summary

The dynamic agent management system provides:

- ✅ **Flexibility**: Run only what you need
- ✅ **Resilience**: Graceful degradation when agents fail
- ✅ **Extensibility**: Easy to add new specialized agents
- ✅ **Monitoring**: Automatic health tracking
- ✅ **Cost Efficiency**: Don't run unused services

The supervisor adapts its capabilities based on available agents, ensuring the system always provides the best possible response with available resources.
