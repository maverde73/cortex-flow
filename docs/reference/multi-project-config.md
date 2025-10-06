# Multi-Project Configuration System

**Status**: ✅ Production Ready
**Since**: Version 1.0
**Date**: 2025-10-06

---

## Overview

Cortex-Flow uses a **JSON-based multi-project configuration system** that separates secrets from configuration, enables type-safe validation, and supports multiple isolated project environments.

### Key Features

- ✅ **Secrets Separation** - API keys in `.env`, configuration in JSON
- ✅ **Multi-Project Support** - Multiple isolated configurations
- ✅ **Type Safety** - Pydantic validation on all configs
- ✅ **Environment Variables** - `${VAR}` substitution in JSON
- ✅ **Version Control** - Config files can be safely committed
- ✅ **CLI Management** - Command-line tools for project management
- ✅ **Backward Compatible** - Legacy code continues to work

---

## Architecture

### Directory Structure

```
cortex-flow/
├── .env                        # Secrets only (never commit)
├── .env.example               # Template for secrets
│
├── config/                    # Configuration package
│   ├── __init__.py           # Public API
│   ├── models.py             # Pydantic validation models
│   ├── loader.py             # JSON loader with env substitution
│   └── secrets.py            # Secrets management
│
├── projects/                  # Multi-project configurations
│   ├── default/              # Default project
│   │   ├── project.json      # Core settings
│   │   ├── agents.json       # Agent configuration
│   │   ├── mcp.json          # MCP servers
│   │   ├── react.json        # ReAct pattern
│   │   └── workflows/        # Workflow templates
│   │
│   ├── staging/              # Staging environment
│   └── production/           # Production environment
│
└── scripts/
    └── project.py            # Project management CLI
```

### Configuration Layers

1. **Secrets Layer** (`.env`)
   - API keys
   - Database URLs
   - Sensitive credentials
   - Never in JSON files

2. **Project Layer** (`projects/{name}/*.json`)
   - All non-sensitive configuration
   - Agent settings
   - MCP servers
   - ReAct behavior
   - Workflows

3. **Runtime Layer**
   - Environment variable substitution
   - Pydantic validation
   - Type checking

---

## Configuration Files

### `.env` - Secrets Only

Contains ONLY sensitive data:

```bash
# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-v1-...

# Tool API Keys
TAVILY_API_KEY=tvly-...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...

# Database URLs
POSTGRES_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379

# LangSmith (Observability)
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=cortex-flow
LANGSMITH_TRACING=true

# Active Project
ACTIVE_PROJECT=default
```

**Important**: Never commit `.env` to version control!

### `project.json` - Core Settings

Project metadata and backend configuration:

```json
{
  "name": "default",
  "version": "1.0.0",
  "description": "Default Cortex-Flow project",
  "active": true,
  "created_at": "2025-10-06T00:00:00",
  "settings": {
    "checkpoint_backend": "postgres",
    "postgres_url": "${POSTGRES_URL}",
    "redis_url": "${REDIS_URL:-redis://localhost:6379}",
    "http_timeout": 120.0,
    "http_max_connections": 100,
    "http_max_keepalive_connections": 20
  }
}
```

**Settings:**
- `checkpoint_backend`: State persistence (`memory`, `postgres`, `redis`)
- `postgres_url`: PostgreSQL connection (supports env vars)
- `redis_url`: Redis connection (supports env vars)
- HTTP client configuration

### `agents.json` - Agent Configuration

Per-agent settings and models:

```json
{
  "default_model": "openai/gpt-4o-mini",
  "provider_fallback_order": "openai,anthropic,google,groq,openrouter",
  "agents": {
    "supervisor": {
      "enabled": true,
      "host": "localhost",
      "port": 8000,
      "model": "openai/gpt-4o-mini",
      "react_strategy": "fast",
      "temperature": 0.7,
      "max_iterations": 10,
      "enable_reflection": false,
      "reflection_threshold": 0.6,
      "reflection_max_iterations": 1,
      "enable_hitl": false,
      "hitl_require_approval_for": "",
      "hitl_timeout_seconds": 180.0
    },
    "researcher": {
      "enabled": true,
      "host": "localhost",
      "port": 8001,
      "model": "openai/gpt-4o-mini",
      "react_strategy": "deep",
      "temperature": 0.7,
      "max_iterations": 10,
      "enable_reflection": false,
      "reflection_threshold": 0.7,
      "reflection_max_iterations": 2,
      "enable_hitl": false,
      "hitl_require_approval_for": "",
      "hitl_timeout_seconds": 300.0
    },
    "analyst": {
      "enabled": true,
      "host": "localhost",
      "port": 8003,
      "model": "openai/gpt-4o-mini",
      "react_strategy": "balanced"
    },
    "writer": {
      "enabled": true,
      "host": "localhost",
      "port": 8004,
      "model": "openai/gpt-4o-mini",
      "react_strategy": "creative",
      "enable_reflection": true,
      "reflection_threshold": 0.8
    }
  }
}
```

**Per-Agent Settings:**
- `enabled`: Enable/disable agent
- `host`/`port`: Server binding
- `model`: LLM model (format: `provider/model`)
- `react_strategy`: Reasoning strategy (`fast`, `balanced`, `deep`, `creative`)
- `temperature`: LLM temperature
- `max_iterations`: Max ReAct cycles
- Reflection settings (enable, threshold, max iterations)
- HITL settings (enable, approval patterns, timeout)

### `mcp.json` - MCP Server Configuration

Model Context Protocol server configuration:

```json
{
  "enabled": true,
  "client": {
    "retry_attempts": 3,
    "timeout": 30.0,
    "health_check_interval": 60.0
  },
  "servers": {
    "corporate": {
      "type": "remote",
      "transport": "streamable_http",
      "url": "http://localhost:8005/mcp",
      "api_key": null,
      "local_path": null,
      "enabled": true,
      "timeout": 30.0,
      "prompts_file": "/path/to/prompts.md",
      "prompt_tool_association": "query_database"
    },
    "local_tools": {
      "type": "local",
      "transport": "stdio",
      "local_path": "/path/to/mcp_server.py",
      "enabled": true
    }
  },
  "tools_enable_logging": true,
  "tools_enable_reflection": false,
  "tools_timeout_multiplier": 1.5
}
```

**Server Types:**
- `remote`: External HTTP MCP server
- `local`: Local Python MCP implementation

**Transports:**
- `streamable_http`: Modern HTTP streaming (recommended)
- `sse`: Server-Sent Events (legacy)
- `stdio`: Standard I/O (local only)

### `react.json` - ReAct Pattern Configuration

ReAct reasoning and logging configuration:

```json
{
  "execution": {
    "timeout_seconds": 120.0,
    "enable_early_stopping": true,
    "max_consecutive_errors": 3
  },
  "logging": {
    "enable_verbose": true,
    "log_thoughts": true,
    "log_actions": true,
    "log_observations": true
  },
  "reflection": {
    "enabled": false,
    "quality_threshold": 0.7,
    "max_iterations": 2
  },
  "hitl": {
    "enabled": false,
    "timeout_seconds": 300.0,
    "timeout_action": "reject"
  },
  "advanced_modes": {
    "cot_enabled": false,
    "cot_min_steps": 2,
    "tot_enabled": false,
    "tot_max_branches": 5,
    "adaptive_enabled": false,
    "adaptive_max_escalations": 3
  }
}
```

---

## Usage

### Loading Configuration

**New Code (Recommended):**

```python
from config import load_config

# Load active project (from ACTIVE_PROJECT env var)
config = load_config()

# Load specific project
config = load_config(project_name="production")

# Access configuration
print(f"Project: {config.name}")
print(f"Checkpoint: {config.project.settings.checkpoint_backend}")
print(f"Default model: {config.agents.default_model}")

# Get agent config
researcher = config.get_agent_config("researcher")
print(f"Researcher model: {researcher.model}")
print(f"Researcher port: {researcher.port}")

# Get enabled agents
enabled = config.get_enabled_agents()
print(f"Enabled agents: {enabled}")

# Get MCP servers
if config.mcp.enabled:
    servers = config.get_enabled_mcp_servers()
    for name, server in servers.items():
        print(f"MCP: {name} at {server.url}")
```

**Legacy Code (Still Works):**

```python
from config_legacy import settings

# Old code continues to work with deprecation warnings
print(settings.researcher_port)
print(settings.default_model)
print(settings.checkpoint_backend)
```

### Environment Variable Substitution

JSON files support environment variable substitution:

```json
{
  "settings": {
    "postgres_url": "${POSTGRES_URL}",
    "redis_url": "${REDIS_URL:-redis://localhost:6379}",
    "api_key": "${API_KEY}"
  }
}
```

**Syntax:**
- `${VAR}` - Required variable (error if not set)
- `${VAR:-default}` - Optional with default value

---

## Project Management CLI

### List Projects

```bash
python scripts/project.py list
```

Output:
```
Available projects:
* default
  staging
  production

Active project: default
```

### Create Project

```bash
# Create from default template
python scripts/project.py create my_project

# Create from specific template
python scripts/project.py copy staging my_project
```

### Show Project Configuration

```bash
# Show active project
python scripts/project.py show

# Show specific project
python scripts/project.py show production
```

Output:
```
Project: production
Version: 1.0.0
Description: Production environment

Agents:
  supervisor: enabled (localhost:8000)
  researcher: enabled (localhost:8001)
  analyst: enabled (localhost:8003)
  writer: enabled (localhost:8004)

MCP:
  Enabled: True
  Servers: corporate, internal_tools

Workflows:
  sentiment_routing
  competitive_analysis
  report_generation
```

### Validate Project

```bash
python scripts/project.py validate
```

Output:
```
Validating project: default

✓ Project structure is valid
```

### Activate Project

```bash
python scripts/project.py activate production
```

This updates `.env` file with:
```bash
ACTIVE_PROJECT=production
```

---

## Creating a New Project

### Step 1: Create Project

```bash
python scripts/project.py create production
```

### Step 2: Edit Configuration

```bash
# Edit project settings
vim projects/production/project.json

# Edit agent configuration
vim projects/production/agents.json

# Edit MCP servers
vim projects/production/mcp.json

# Edit ReAct behavior
vim projects/production/react.json
```

### Step 3: Add Workflows

```bash
# Copy workflow templates
cp projects/default/workflows/*.json projects/production/workflows/

# Or create new ones
vim projects/production/workflows/custom_workflow.json
```

### Step 4: Activate

```bash
python scripts/project.py activate production
```

### Step 5: Test

```bash
# Validate configuration
python scripts/project.py validate production

# Start servers
./scripts/start_all.sh
```

---

## Migration from .env

### Before (Old System)

`.env` with 250+ lines:
```bash
SUPERVISOR_HOST=localhost
SUPERVISOR_PORT=8000
DEFAULT_MODEL=openai/gpt-4o-mini
RESEARCHER_MODEL=openai/gpt-4o
REACT_TIMEOUT_SECONDS=120.0
# ... 200+ more lines
```

### After (New System)

`.env` with 83 lines (secrets only):
```bash
OPENAI_API_KEY=sk-...
POSTGRES_URL=postgresql://...
LANGSMITH_API_KEY=lsv2_pt_...
ACTIVE_PROJECT=default
```

Configuration in JSON:
```
projects/default/
├── project.json    # Settings
├── agents.json     # Agents
├── mcp.json       # MCP
└── react.json     # ReAct
```

---

## Best Practices

### 1. Secrets Management

**DO:**
- ✅ Keep secrets in `.env`
- ✅ Use `.env.example` as template
- ✅ Add `.env` to `.gitignore`
- ✅ Use environment variable substitution in JSON

**DON'T:**
- ❌ Never commit `.env` to version control
- ❌ Don't put API keys in JSON files
- ❌ Don't share `.env` files in chat/email

### 2. Project Organization

**DO:**
- ✅ Create separate projects for environments (dev, staging, prod)
- ✅ Use descriptive project names
- ✅ Document project purpose in description field
- ✅ Keep workflows in project directories

**DON'T:**
- ❌ Don't modify `default` project for production
- ❌ Don't mix environment configs
- ❌ Don't share database URLs across environments

### 3. Configuration Changes

**DO:**
- ✅ Validate after changes: `python scripts/project.py validate`
- ✅ Test in development first
- ✅ Commit JSON config changes to git
- ✅ Document significant changes

**DON'T:**
- ❌ Don't change production config without testing
- ❌ Don't skip validation
- ❌ Don't commit `.env` files

### 4. Version Control

**DO:**
- ✅ Commit `projects/` directory
- ✅ Commit `.env.example`
- ✅ Use meaningful commit messages for config changes
- ✅ Review config changes in PRs

**DON'T:**
- ❌ Don't commit `.env`
- ❌ Don't commit sensitive data
- ❌ Don't bypass config validation

---

## Troubleshooting

### Configuration Not Loading

**Problem**: `ConfigurationError: Project directory not found`

**Solution**:
```bash
# Check available projects
python scripts/project.py list

# Validate project structure
python scripts/project.py validate

# Check ACTIVE_PROJECT in .env
cat .env | grep ACTIVE_PROJECT
```

### Environment Variable Not Substituted

**Problem**: `${VAR}` appears literally in config

**Solution**:
```bash
# Check variable is in .env
cat .env | grep VAR

# Check syntax (must be ${VAR} or ${VAR:-default})
# Reload secrets
python -c "from config import reload_secrets; reload_secrets()"
```

### Validation Errors

**Problem**: Pydantic validation fails

**Solution**:
```bash
# Check JSON syntax
python -m json.tool projects/default/project.json

# Validate specific project
python scripts/project.py validate default

# Check error message for specific field
```

### Deprecation Warnings

**Problem**: `DeprecationWarning: The 'config.py' module is deprecated`

**Solution**: Migrate to new config system:
```python
# Old
from config import settings
print(settings.researcher_port)

# New
from config import load_config
config = load_config()
print(config.get_agent_config("researcher").port)
```

---

## API Reference

### `load_config()`

Load project configuration.

```python
from config import load_config

# Load active project
config = load_config()

# Load specific project
config = load_config(project_name="production")

# Force reload
config = load_config(force_reload=True)
```

### `ProjectConfiguration`

Main configuration object.

**Properties:**
- `name: str` - Project name
- `is_active: bool` - Whether project is active
- `project: ProjectModel` - Project settings
- `agents: AgentsModel` - Agent configuration
- `mcp: MCPModel` - MCP configuration
- `react: ReactModel` - ReAct configuration

**Methods:**
- `get_agent_config(name: str) -> AgentConfig` - Get agent configuration
- `get_enabled_agents() -> List[str]` - Get enabled agent names
- `get_mcp_server(name: str) -> MCPServerConfig` - Get MCP server config
- `get_enabled_mcp_servers() -> Dict[str, MCPServerConfig]` - Get enabled servers

### `ProjectLoader`

Configuration loader class.

```python
from config import ProjectLoader

# Create loader
loader = ProjectLoader("production")

# Load configuration
config = loader.load()

# List workflows
workflows = loader.list_workflows()

# Load specific workflow
workflow = loader.load_workflow("sentiment_routing")

# List all projects
projects = ProjectLoader.list_projects()
```

---

## Related Documentation

- [Environment Variables Reference](environment-variables.md)
- [MCP Configuration](../mcp/configuration.md)
- [Agent Management](../agents/agent-management.md)
- [Workflows](../workflows/README.md)

---

**Last Updated**: 2025-10-06
**Version**: 1.0
