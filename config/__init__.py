"""
Configuration package for Cortex-Flow.

Multi-project JSON-based configuration system with:
- Pydantic models for validation
- Environment variable substitution
- Secrets management (API keys from .env)
- Project isolation and management

Usage:
    from config import load_config

    # Load active project (from ACTIVE_PROJECT env var)
    config = load_config()

    # Access configuration
    project_name = config.name
    enabled_agents = config.get_enabled_agents()
    mcp_servers = config.get_enabled_mcp_servers()

    # Get specific agent config
    supervisor_config = config.get_agent_config("supervisor")
"""

from config.loader import (
    load_config,
    reload_config,
    get_config,
    ProjectLoader,
    ConfigurationError,
    validate_project_structure
)

from config.secrets import (
    get_secrets,
    reload_secrets,
    get_api_key,
    get_database_url,
    setup_langsmith,
    validate_secrets,
    get_active_project,
    set_active_project,
    Secrets
)

from config.models import (
    # Project
    ProjectSettings,
    ProjectModel,
    ProjectConfiguration,

    # Agents
    ReActStrategy,
    AgentConfig,
    AgentsModel,

    # MCP
    MCPServerType,
    MCPTransportType,
    MCPServerConfig,
    MCPClientConfig,
    MCPModel,

    # ReAct
    ReactExecutionConfig,
    ReactLoggingConfig,
    ReactReflectionConfig,
    ReactHITLConfig,
    ReactAdvancedModesConfig,
    ReactModel,

    # Workflows
    WorkflowNode,
    WorkflowConditionalEdge,
    WorkflowTemplate
)

__all__ = [
    # Loader
    "load_config",
    "reload_config",
    "get_config",
    "ProjectLoader",
    "ConfigurationError",
    "validate_project_structure",

    # Secrets
    "get_secrets",
    "reload_secrets",
    "get_api_key",
    "get_database_url",
    "setup_langsmith",
    "validate_secrets",
    "get_active_project",
    "set_active_project",
    "Secrets",

    # Models - Project
    "ProjectSettings",
    "ProjectModel",
    "ProjectConfiguration",

    # Models - Agents
    "ReActStrategy",
    "AgentConfig",
    "AgentsModel",

    # Models - MCP
    "MCPServerType",
    "MCPTransportType",
    "MCPServerConfig",
    "MCPClientConfig",
    "MCPModel",

    # Models - ReAct
    "ReactExecutionConfig",
    "ReactLoggingConfig",
    "ReactReflectionConfig",
    "ReactHITLConfig",
    "ReactAdvancedModesConfig",
    "ReactModel",

    # Models - Workflows
    "WorkflowNode",
    "WorkflowConditionalEdge",
    "WorkflowTemplate",
]
