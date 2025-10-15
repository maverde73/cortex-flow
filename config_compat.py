"""
Backward compatibility layer for legacy config.py usage.

This module provides a Settings-like interface that reads from the new
JSON-based configuration system, allowing gradual migration of existing code.

DEPRECATED: New code should use `from config import load_config` instead.
"""

import warnings
from typing import Optional

from config import load_config, get_secrets


class CompatSettings:
    """
    Compatibility wrapper that mimics the old Settings class interface
    but reads from the new JSON configuration system.
    """

    def __init__(self):
        # Load new configuration
        self._config = load_config()
        self._secrets = get_secrets()

        # Show deprecation warning
        warnings.warn(
            "Using config.settings is deprecated. "
            "Please migrate to: from config import load_config",
            DeprecationWarning,
            stacklevel=2
        )

    # ============================================================================
    # LLM API Keys (from secrets)
    # ============================================================================

    @property
    def openai_api_key(self) -> Optional[str]:
        return self._secrets.openai_api_key

    @property
    def anthropic_api_key(self) -> Optional[str]:
        return self._secrets.anthropic_api_key

    @property
    def google_api_key(self) -> Optional[str]:
        return self._secrets.google_api_key

    @property
    def groq_api_key(self) -> Optional[str]:
        return self._secrets.groq_api_key

    @property
    def openrouter_api_key(self) -> Optional[str]:
        return self._secrets.openrouter_api_key

    # ============================================================================
    # LangSmith (from secrets)
    # ============================================================================

    @property
    def langsmith_api_key(self) -> Optional[str]:
        return self._secrets.langsmith_api_key

    @property
    def langsmith_project(self) -> str:
        return self._secrets.langsmith_project

    @property
    def langsmith_tracing(self) -> bool:
        return self._secrets.langsmith_tracing

    # ============================================================================
    # Server Configuration (from agents.json)
    # ============================================================================

    @property
    def supervisor_host(self) -> str:
        agent = self._config.get_agent_config("supervisor")
        return agent.host if agent else "localhost"

    @property
    def supervisor_port(self) -> int:
        agent = self._config.get_agent_config("supervisor")
        return agent.port if agent else 8000

    @property
    def researcher_host(self) -> str:
        agent = self._config.get_agent_config("researcher")
        return agent.host if agent else "localhost"

    @property
    def researcher_port(self) -> int:
        agent = self._config.get_agent_config("researcher")
        return agent.port if agent else 8001

    @property
    def reddit_host(self) -> str:
        agent = self._config.get_agent_config("reddit")
        return agent.host if agent else "localhost"

    @property
    def reddit_port(self) -> int:
        agent = self._config.get_agent_config("reddit")
        return agent.port if agent else 8002

    @property
    def analyst_host(self) -> str:
        agent = self._config.get_agent_config("analyst")
        return agent.host if agent else "localhost"

    @property
    def analyst_port(self) -> int:
        agent = self._config.get_agent_config("analyst")
        return agent.port if agent else 8003

    @property
    def writer_host(self) -> str:
        agent = self._config.get_agent_config("writer")
        return agent.host if agent else "localhost"

    @property
    def writer_port(self) -> int:
        agent = self._config.get_agent_config("writer")
        return agent.port if agent else 8004

    # ============================================================================
    # HTTP Client Configuration (from project.json)
    # ============================================================================

    @property
    def http_timeout(self) -> float:
        return self._config.project.settings.http_timeout

    @property
    def http_max_connections(self) -> int:
        return self._config.project.settings.http_max_connections

    @property
    def http_max_keepalive_connections(self) -> int:
        return self._config.project.settings.http_max_keepalive_connections

    # ============================================================================
    # State Management (from project.json)
    # ============================================================================

    @property
    def checkpoint_backend(self) -> str:
        return self._config.project.settings.checkpoint_backend

    @property
    def postgres_url(self) -> Optional[str]:
        return self._secrets.postgres_url

    @property
    def redis_url(self) -> Optional[str]:
        return self._secrets.redis_url

    # ============================================================================
    # Agent Configuration (from agents.json)
    # ============================================================================

    @property
    def default_model(self) -> str:
        return self._config.agents.default_model

    @property
    def temperature(self) -> float:
        # Use supervisor as default
        agent = self._config.get_agent_config("supervisor")
        return agent.temperature if agent else 0.7

    @property
    def max_iterations(self) -> int:
        # Use supervisor as default
        agent = self._config.get_agent_config("supervisor")
        return agent.max_iterations if agent else 10

    @property
    def researcher_model(self) -> Optional[str]:
        agent = self._config.get_agent_config("researcher")
        return agent.model if agent else None

    @property
    def analyst_model(self) -> Optional[str]:
        agent = self._config.get_agent_config("analyst")
        return agent.model if agent else None

    @property
    def writer_model(self) -> Optional[str]:
        agent = self._config.get_agent_config("writer")
        return agent.model if agent else None

    @property
    def supervisor_model(self) -> Optional[str]:
        agent = self._config.get_agent_config("supervisor")
        return agent.model if agent else None

    @property
    def provider_fallback_order(self) -> str:
        return self._config.agents.provider_fallback_order

    # ============================================================================
    # ReAct Configuration (from react.json)
    # ============================================================================

    @property
    def react_timeout_seconds(self) -> float:
        return self._config.react.execution.timeout_seconds

    @property
    def react_enable_early_stopping(self) -> bool:
        return self._config.react.execution.enable_early_stopping

    @property
    def react_max_consecutive_errors(self) -> int:
        return self._config.react.execution.max_consecutive_errors

    @property
    def react_enable_verbose_logging(self) -> bool:
        return self._config.react.logging.enable_verbose

    @property
    def react_log_thoughts(self) -> bool:
        return self._config.react.logging.log_thoughts

    @property
    def react_log_actions(self) -> bool:
        return self._config.react.logging.log_actions

    @property
    def react_log_observations(self) -> bool:
        return self._config.react.logging.log_observations

    # ReAct Strategies (from agents.json)
    @property
    def supervisor_react_strategy(self) -> str:
        agent = self._config.get_agent_config("supervisor")
        return agent.react_strategy.value if agent else "fast"

    @property
    def researcher_react_strategy(self) -> str:
        agent = self._config.get_agent_config("researcher")
        return agent.react_strategy.value if agent else "deep"

    @property
    def analyst_react_strategy(self) -> str:
        agent = self._config.get_agent_config("analyst")
        return agent.react_strategy.value if agent else "balanced"

    @property
    def writer_react_strategy(self) -> str:
        agent = self._config.get_agent_config("writer")
        return agent.react_strategy.value if agent else "creative"

    # ReAct Reflection (from react.json + agents.json)
    @property
    def react_enable_reflection(self) -> bool:
        return self._config.react.reflection.enabled

    @property
    def react_reflection_quality_threshold(self) -> float:
        return self._config.react.reflection.quality_threshold

    @property
    def react_reflection_max_iterations(self) -> int:
        return self._config.react.reflection.max_iterations

    @property
    def researcher_enable_reflection(self) -> bool:
        agent = self._config.get_agent_config("researcher")
        return agent.enable_reflection if agent else False

    @property
    def analyst_enable_reflection(self) -> bool:
        agent = self._config.get_agent_config("analyst")
        return agent.enable_reflection if agent else False

    @property
    def writer_enable_reflection(self) -> bool:
        agent = self._config.get_agent_config("writer")
        return agent.enable_reflection if agent else False

    @property
    def supervisor_enable_reflection(self) -> bool:
        agent = self._config.get_agent_config("supervisor")
        return agent.enable_reflection if agent else False

    # Tool Configuration (from secrets)
    @property
    def tavily_api_key(self) -> Optional[str]:
        return self._secrets.tavily_api_key

    @property
    def reddit_client_id(self) -> Optional[str]:
        return self._secrets.reddit_client_id

    @property
    def reddit_client_secret(self) -> Optional[str]:
        return self._secrets.reddit_client_secret

    # Agent Management
    @property
    def enabled_agents(self) -> str:
        # Get enabled agents and join with comma
        agents = self._config.get_enabled_agents()
        # Filter out supervisor
        agents = [a for a in agents if a != "supervisor"]
        return ",".join(agents)

    # MCP Configuration (from mcp.json)
    @property
    def mcp_enable(self) -> bool:
        return self._config.mcp.enabled

    @property
    def mcp_client_retry_attempts(self) -> int:
        return self._config.mcp.client.retry_attempts

    @property
    def mcp_client_timeout(self) -> float:
        return self._config.mcp.client.timeout

    @property
    def mcp_health_check_interval(self) -> float:
        return self._config.mcp.client.health_check_interval

    @property
    def mcp_tools_enable_logging(self) -> bool:
        return self._config.mcp.tools_enable_logging

    @property
    def mcp_tools_enable_reflection(self) -> bool:
        return self._config.mcp.tools_enable_reflection

    @property
    def mcp_tools_timeout_multiplier(self) -> float:
        return self._config.mcp.tools_timeout_multiplier

    # Supervisor MCP Configuration
    @property
    def supervisor_mcp_enable(self) -> bool:
        # Supervisor MCP is enabled if overall MCP is enabled
        return self._config.mcp.enabled

    @property
    def supervisor_mcp_path(self) -> str:
        return "/mcp"

    @property
    def supervisor_mcp_transport(self) -> str:
        return "streamable_http"

    # Agent Health Monitoring
    @property
    def agent_health_check_interval(self) -> float:
        # Use same interval as MCP health check
        return self._config.mcp.client.health_check_interval

    # Agent retry configuration
    @property
    def agent_retry_attempts(self) -> int:
        return 3

    @property
    def agent_retry_delay(self) -> float:
        return 1.0

    # URL properties
    @property
    def supervisor_url(self) -> str:
        return f"http://{self.supervisor_host}:{self.supervisor_port}"

    @property
    def researcher_url(self) -> str:
        return f"http://{self.researcher_host}:{self.researcher_port}"

    @property
    def reddit_url(self) -> str:
        return f"http://{self.reddit_host}:{self.reddit_port}"

    @property
    def analyst_url(self) -> str:
        return f"http://{self.analyst_host}:{self.analyst_port}"

    @property
    def writer_url(self) -> str:
        return f"http://{self.writer_host}:{self.writer_port}"

    # Helper methods
    def get_enabled_agents(self) -> list[str]:
        return self._config.get_enabled_agents()

    def is_agent_enabled(self, agent_id: str) -> bool:
        return agent_id in self.get_enabled_agents()

    def parse_mcp_servers(self) -> dict:
        return {
            name: {
                "type": server.type.value,
                "transport": server.transport.value,
                "url": server.url,
                "enabled": server.enabled,
            }
            for name, server in self._config.mcp.servers.items()
        }

    # MCP Servers - required by initialize_mcp_registry_from_config()
    @property
    def mcp_servers(self) -> dict:
        """Return MCP servers configuration with all fields for registry initialization."""
        return {
            name: {
                "type": server.type.value,
                "transport": server.transport.value,
                "url": server.url,
                "api_key": server.api_key,
                "local_path": server.local_path,
                "enabled": server.enabled,
                "timeout": server.timeout,
                "prompts_file": server.prompts_file,
                "prompt_tool_association": server.prompt_tool_association
            }
            for name, server in self._config.mcp.servers.items()
        }

    # ============================================================================
    # Workflow Configuration (Python workflow support)
    # ============================================================================

    @property
    def workflow_enable(self) -> bool:
        """Enable workflow system (JSON + Python templates)."""
        return True  # Always enabled

    @property
    def workflow_auto_classify(self) -> bool:
        """Auto-match workflows based on user input patterns."""
        return True  # Enable auto-classification

    @property
    def workflow_mode(self) -> str:
        """Workflow execution mode: 'auto', 'manual', or 'hybrid'."""
        return "auto"  # Auto-select workflows

    @property
    def workflow_engine_mode(self) -> str:
        """Workflow engine: 'langgraph' or 'sequential'."""
        return "langgraph"  # Use LangGraph for execution

    @property
    def workflow_templates_dir(self) -> Optional[str]:
        """Directory containing workflow templates (JSON + Python)."""
        return None  # Use default: workflows/templates

    @property
    def workflow_fallback_to_react(self) -> bool:
        """Fallback to ReAct mode if workflow fails."""
        return False  # Don't fallback by default, return error


# Create global instance for backward compatibility
settings = CompatSettings()
