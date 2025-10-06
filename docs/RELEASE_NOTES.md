# Release Notes - v0.2.0

## Dynamic Agent Management System

### Overview

This release introduces a comprehensive **dynamic agent management system** that transforms Cortex Flow from a static multi-agent setup into a flexible, resilient, and production-ready platform.

### 🎉 New Features

#### 1. Service Discovery & Registry

**New Files:**
- `services/registry.py` - Central agent registry with health tracking
- `services/health_monitor.py` - Continuous background monitoring

**What it does:**
- Automatically discovers and registers available agents
- Tracks agent health status in real-time
- Provides API for querying agent availability
- Supports async operations throughout

**Example:**
```python
from services.registry import get_registry

registry = get_registry()
available = await registry.get_available_agents()
# Returns: ['researcher', 'writer'] (if analyst is down)
```

#### 2. Dynamic Tool Loading

**Modified Files:**
- `agents/supervisor.py` - Now loads tools dynamically
- `agents/factory.py` - New factory for creating supervisor with available tools

**What it does:**
- Supervisor only binds tools for agents that are actually running
- System prompt updates dynamically based on available agents
- Graceful degradation when agents are offline

**Before:**
```python
# Fixed tools - crash if agent unavailable
tools = [research_web, analyze_data, write_content]
```

**After:**
```python
# Dynamic tools - adapts to available agents
tools, prompt = await get_available_tools()
# If only researcher available: tools = [research_web]
```

#### 3. Configurable Agent Enablement

**Modified Files:**
- `config.py` - New `enabled_agents` configuration
- `.env.example` - Documented new variables

**What it does:**
- Control which agents run via configuration
- Parse comma-separated agent list
- Helper methods to check agent status

**Configuration:**
```bash
# .env
ENABLED_AGENTS=researcher,writer  # Disable analyst
AGENT_RETRY_ATTEMPTS=3
AGENT_HEALTH_CHECK_INTERVAL=30
```

#### 4. Enhanced Error Handling

**Modified Files:**
- `tools/proxy_tools.py` - Comprehensive retry and error handling

**What it does:**
- Retry with exponential backoff (1s, 2s, 4s, ...)
- User-friendly error messages with emojis
- Different strategies for different error types
- Detailed logging for debugging

**Error Messages:**
```
⚠️ The Researcher agent is currently unavailable (connection refused).

💡 Please ensure the researcher service is running and try again.
```

#### 5. Docker Compose Profiles

**Modified Files:**
- `docker-compose.yml` - Added profiles for flexible deployment

**What it does:**
- Deploy only the agents you need
- Reduce resource usage in development
- Cost optimization for production

**Available Profiles:**
- `minimal` - Supervisor only
- `research` - Adds researcher
- `analysis` - Adds analyst
- `writing` - Adds writer
- `full` - All agents

**Usage:**
```bash
# Development: Just supervisor + researcher
docker-compose --profile=minimal --profile=research up

# Production: Everything
docker-compose --profile=full up
```

#### 6. Smart Startup Script

**Modified Files:**
- `scripts/start_all.sh` - Reads configuration and starts only enabled agents

**What it does:**
- Reads `ENABLED_AGENTS` from `.env`
- Starts only configured agents
- Health checks only enabled agents
- Saves PIDs correctly

**Output:**
```
📋 Enabled agents: researcher,writer
📡 Starting Researcher Agent (port 8001)...
✍️  Starting Writer Agent (port 8004)...
🎯 Starting Supervisor Agent (port 8000)...
✅ All agents are running!
```

### 📊 System Improvements

#### Health Monitoring

- **Automatic**: Checks every 30 seconds (configurable)
- **Resilient**: Tracks consecutive failures before marking unhealthy
- **Logged**: All status changes logged for monitoring

#### Retry Logic

- **Exponential Backoff**: 1s → 2s → 4s between retries
- **Configurable**: Set `AGENT_RETRY_ATTEMPTS` in .env
- **Smart**: Different strategies for different error types
  - Connection refused → Retry
  - Timeout → Retry
  - 5xx errors → Retry
  - 4xx errors → Fail immediately (client error)

#### Graceful Degradation

The supervisor now handles missing agents intelligently:

```
User: "Create a report on AI"

All agents available:
✅ Research → Analyze → Write → Complete report

Writer unavailable:
✅ Research → Analyze → ⚠️ "Writer unavailable, here's the analysis..."

All unavailable:
✅ "Agents unavailable. Based on my knowledge: ..."
```

### 🔧 Breaking Changes

#### Supervisor Initialization

**Before:**
```python
from agents.supervisor import get_supervisor_agent

agent = get_supervisor_agent()  # Sync
```

**After:**
```python
from agents.supervisor import get_supervisor_agent

agent = await get_supervisor_agent()  # Now async!
```

**Why:** Dynamic tool loading requires checking registry, which is async.

**Migration:** Add `await` to all `get_supervisor_agent()` calls.

### 📚 New Documentation

1. **AGENT_MANAGEMENT.md** - Complete guide to agent management
   - Configuration
   - Deployment options
   - Adding new agents
   - Troubleshooting

2. **Updated README.md** - New features section and examples

3. **Updated EXAMPLES.md** - Docker profile examples

### 🚀 Upgrade Guide

#### From v0.1.0 to v0.2.0

1. **Update .env file:**
   ```bash
   cp .env.example .env.new
   # Copy your API keys from old .env
   # Add new variables:
   ENABLED_AGENTS=researcher,analyst,writer
   AGENT_RETRY_ATTEMPTS=3
   AGENT_HEALTH_CHECK_INTERVAL=30
   mv .env.new .env
   ```

2. **Update code (if using supervisor directly):**
   ```python
   # Change this:
   agent = get_supervisor_agent()

   # To this:
   agent = await get_supervisor_agent()
   ```

3. **Restart system:**
   ```bash
   ./scripts/stop_all.sh
   ./scripts/start_all.sh
   ```

### 📈 Performance Impact

- **Startup**: ~2s longer (registry initialization)
- **First Request**: ~200ms longer (dynamic tool loading)
- **Subsequent Requests**: No impact
- **Failed Agent Calls**: 3-7s retry period before failure

### 🐛 Bug Fixes

- Fixed race condition in agent initialization
- Fixed supervisor crash when all agents down
- Fixed PID file management in start script
- Fixed health check timeout handling

### 🔒 Security

- No new security changes
- Existing security practices maintained
- Recommend adding authentication for production

### 📦 Dependencies

No new external dependencies - all features use existing packages.

### 🎯 Future Enhancements

Planned for v0.3.0:

- [ ] Agent auto-restart on failure
- [ ] Circuit breaker implementation
- [ ] Metrics and monitoring endpoints
- [ ] Agent load balancing (multiple instances)
- [ ] Dynamic agent registration via API
- [ ] WebSocket support for real-time updates

### 👥 Contributors

- Implementation by Claude Code Assistant
- Based on architectural design from project docs

### 📞 Support

- Issues: GitHub Issues
- Documentation: See AGENT_MANAGEMENT.md
- Examples: See EXAMPLES.md

---

**Full Changelog**: v0.1.0...v0.2.0
