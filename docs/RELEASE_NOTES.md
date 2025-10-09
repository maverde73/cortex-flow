# Release Notes

## v1.1 - Python Library Integration System (2025-10-09)

### 🎉 Major Features

#### Custom Python Libraries in Workflows
- **Library System** - Integrate any Python functionality into workflows
- **Decorator-based** - Simple `@library_tool` decorator to expose functions
- **Type Validation** - Automatic parameter validation with Pydantic
- **Security Controls** - Capability-based access control and sandboxing
- **Built-in Libraries** - REST API and Filesystem libraries included

#### New Components
- `libraries/` package with base classes and decorators
- Registry system for dynamic library discovery
- Executor module for workflow integration
- Security capabilities system
- Variable substitution from workflow state

#### Built-in Libraries
- **REST API Library** - HTTP GET, POST, PUT, DELETE operations
- **Filesystem Library** - Read/write files, JSON operations, directory management

### 📚 New Documentation
- [Libraries Overview](libraries/README.md)
- [Creating Libraries Guide](libraries/creating-libraries.md)
- [Using Libraries in Workflows](libraries/using-in-workflows.md)
- [Security & Capabilities](libraries/security.md)
- [Built-in Libraries Reference](libraries/built-in-libraries.md)
- [API Reference](libraries/api-reference.md)

### 🔧 Workflow Enhancements
- New `library` agent type for workflow nodes
- Support for `library_name`, `function_name`, and `function_params` in nodes
- Automatic variable substitution in library parameters
- Full integration with LangGraph compiler

### 🔒 Security Features
- Capability-based access control (filesystem, network, etc.)
- Path validation for filesystem operations
- Allowlist/blocklist for libraries
- Configurable timeouts and resource limits
- Sandboxing support for critical operations

### 📝 Example Usage

```json
{
  "nodes": [{
    "id": "fetch_data",
    "agent": "library",
    "library_name": "rest_api",
    "function_name": "http_get",
    "function_params": {
      "url": "https://api.example.com/data",
      "headers": {"Authorization": "Bearer {api_token}"}
    }
  }]
}
```

### 🎯 Benefits
- ✅ **Extensibility** - Add any Python functionality without modifying core
- ✅ **Reusability** - Libraries can be shared across workflows
- ✅ **Security** - Fine-grained access control
- ✅ **Performance** - Async support and lazy loading
- ✅ **Standardization** - Uniform interface for all libraries

---

## v1.0 - Multi-Project Configuration System (2025-10-06)

### 🎉 Major Features

#### Multi-Project JSON Configuration
- **Complete migration** from `.env`-based to JSON-based configuration
- **Multi-project support** - Multiple isolated project environments
- **Secrets separation** - API keys in `.env`, configuration in JSON
- **Type safety** - Pydantic validation on all configurations
- **Backward compatibility** - Legacy code continues to work

#### New Configuration System
- `config/` package with models, loader, and secrets management
- `projects/{name}/` directories for isolated configurations
- Project management CLI (`scripts/project.py`)
- Environment variable substitution in JSON (`${VAR}` syntax)

#### Configuration Files
- `project.json` - Core project settings
- `agents.json` - Agent configuration (models, ports, strategies)
- `mcp.json` - MCP server configuration
- `react.json` - ReAct pattern configuration
- `workflows/` - Workflow templates

### 📚 New Documentation
- [Multi-Project Configuration](reference/multi-project-config.md)
- Complete migration guide and API reference
- CLI usage examples and best practices

### 🔄 Backward Compatibility
- `config_legacy.py` provides compatibility layer
- All existing code works with deprecation warnings
- Gradual migration path for developers

### 🎯 Migration Benefits
- ✅ Clean `.env` - 250+ → 83 lines (secrets only)
- ✅ Version control - JSON configs can be committed
- ✅ Type safety - Pydantic validation
- ✅ Multi-environment - dev/staging/prod projects
- ✅ Easy management - CLI tools for project operations

---

## v0.2.0 - Dynamic Agent Management System

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
