"""
Centralized configuration management using Pydantic BaseSettings.
All configuration is loaded from environment variables or .env file.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os
import re


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Configuration is type-safe and validated at startup.
    Missing required fields will raise an error.
    """

    # LLM API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    # LangSmith Configuration (for observability)
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "cortex-flow"
    langsmith_tracing: bool = False

    # Server Configuration
    supervisor_host: str = "localhost"
    supervisor_port: int = 8000

    researcher_host: str = "localhost"
    researcher_port: int = 8001

    reddit_host: str = "localhost"
    reddit_port: int = 8002

    analyst_host: str = "localhost"
    analyst_port: int = 8003

    writer_host: str = "localhost"
    writer_port: int = 8004

    # HTTP Client Configuration
    http_timeout: float = 120.0
    http_max_connections: int = 100
    http_max_keepalive_connections: int = 20

    # State Management (for LangGraph checkpointing)
    # Options: "memory" (dev only), "postgres", "redis"
    checkpoint_backend: str = "memory"
    postgres_url: Optional[str] = None
    redis_url: Optional[str] = None

    # Agent Configuration
    default_model: str = "openai/gpt-4o-mini"
    temperature: float = 0.7
    max_iterations: int = 10

    # Per-Agent LLM Configuration (Optional - overrides DEFAULT_MODEL)
    researcher_model: Optional[str] = None
    analyst_model: Optional[str] = None
    writer_model: Optional[str] = None
    supervisor_model: Optional[str] = None

    # Provider Fallback Order (comma-separated list)
    # Used when no model is explicitly configured
    provider_fallback_order: str = "openai,anthropic,google,groq,openrouter"

    # ============================================================================
    # REACT PATTERN CONFIGURATION
    # ============================================================================

    # Execution Control
    react_timeout_seconds: float = 120.0  # Max time for complete agent execution
    react_enable_early_stopping: bool = True  # Stop early if satisfactory answer reached
    react_max_consecutive_errors: int = 3  # Max consecutive tool errors before abort

    # Logging and Observability
    react_enable_verbose_logging: bool = True  # Detailed ReAct cycle logging
    react_log_thoughts: bool = True  # Log LLM reasoning explicitly
    react_log_actions: bool = True  # Log tool executions
    react_log_observations: bool = True  # Log tool results

    # ReAct Reasoning Strategies (FASE 2)
    # Per-agent strategies: fast, balanced, deep, creative
    supervisor_react_strategy: str = "fast"  # Quick coordination
    researcher_react_strategy: str = "deep"  # Deep research
    analyst_react_strategy: str = "balanced"  # Standard analysis
    writer_react_strategy: str = "creative"  # Creative content

    # Task-specific strategy overrides (optional)
    # Format: {agent}_{task}_react_strategy
    # Examples below - uncomment and configure as needed
    # researcher_quick_search_react_strategy: Optional[str] = None
    # researcher_deep_analysis_react_strategy: Optional[str] = None
    # writer_creative_react_strategy: Optional[str] = None
    # writer_technical_react_strategy: Optional[str] = None

    # ============================================================================
    # REACT SELF-REFLECTION (FASE 3)
    # ============================================================================

    # Global reflection settings
    react_enable_reflection: bool = False  # Master switch for reflection feature
    react_reflection_quality_threshold: float = 0.7  # Accept responses with score >= threshold
    react_reflection_max_iterations: int = 2  # Max refinement attempts

    # Per-Agent Reflection Configuration
    # Enable/disable reflection for specific agents
    researcher_enable_reflection: bool = False
    analyst_enable_reflection: bool = False
    writer_enable_reflection: bool = False
    supervisor_enable_reflection: bool = False  # Usually disabled for supervisor

    # Per-Agent Quality Thresholds (0.0-1.0)
    # Higher threshold = more strict, more refinements
    researcher_reflection_threshold: float = 0.7
    analyst_reflection_threshold: float = 0.75
    writer_reflection_threshold: float = 0.8  # Higher for content quality
    supervisor_reflection_threshold: float = 0.6  # Lower for quick decisions

    # Per-Agent Max Refinement Iterations
    researcher_reflection_max_iterations: int = 2
    analyst_reflection_max_iterations: int = 2
    writer_reflection_max_iterations: int = 3  # Allow more refinements for writing
    supervisor_reflection_max_iterations: int = 1  # Minimal for supervisor

    # ============================================================================
    # REACT HUMAN-IN-THE-LOOP (FASE 5)
    # ============================================================================

    # Global HITL settings
    react_enable_hitl: bool = False  # Master switch for Human-in-the-Loop
    react_hitl_timeout_seconds: float = 300.0  # Approval timeout (5 minutes)
    react_hitl_timeout_action: str = "reject"  # Action on timeout: reject or approve

    # Per-Agent HITL Configuration
    supervisor_enable_hitl: bool = False
    researcher_enable_hitl: bool = False
    analyst_enable_hitl: bool = False
    writer_enable_hitl: bool = False

    # Per-Agent Approval Requirements (comma-separated tool names)
    # Supports wildcards: "send_*" matches "send_email", "send_sms", etc.
    supervisor_hitl_require_approval_for: str = ""
    researcher_hitl_require_approval_for: str = ""
    analyst_hitl_require_approval_for: str = ""
    writer_hitl_require_approval_for: str = "publish_*,send_*,delete_*"

    # Per-Agent Timeout Settings
    supervisor_hitl_timeout_seconds: float = 180.0  # 3 min for supervisor
    researcher_hitl_timeout_seconds: float = 300.0  # 5 min for researcher
    analyst_hitl_timeout_seconds: float = 300.0  # 5 min for analyst
    writer_hitl_timeout_seconds: float = 600.0  # 10 min for writer (content review)

    # ============================================================================
    # ADVANCED REASONING MODES (FASE 6)
    # ============================================================================

    # Chain-of-Thought (CoT) Configuration
    react_cot_enabled: bool = False  # Enable explicit chain-of-thought reasoning
    react_cot_min_steps: int = 2  # Minimum reasoning steps required
    react_cot_log_steps: bool = True  # Log each reasoning step
    react_cot_require_confidence: bool = True  # Require confidence scores

    # Tree-of-Thought (ToT) Configuration
    react_tot_enabled: bool = False  # Enable tree-of-thought branching
    react_tot_max_branches: int = 5  # Maximum branches to explore
    react_tot_max_depth: int = 4  # Maximum depth to explore
    react_tot_evaluation_threshold: float = 0.6  # Minimum score to consider branch

    # Adaptive Reasoning Configuration
    react_adaptive_enabled: bool = False  # Enable adaptive strategy switching
    react_adaptive_max_escalations: int = 3  # Maximum strategy escalations
    react_adaptive_escalation_threshold: float = 0.3  # Progress threshold for escalation
    react_adaptive_complexity_detection: bool = True  # Auto-detect task complexity

    # Per-Agent Advanced Mode Preferences
    # Which advanced mode to use when enabled for each agent
    # Options: "cot_explicit", "tree_of_thought", "adaptive", "none"
    supervisor_advanced_mode: str = "none"  # Supervisor uses basic strategies
    researcher_advanced_mode: str = "cot_explicit"  # Researcher benefits from CoT
    analyst_advanced_mode: str = "tree_of_thought"  # Analyst explores alternatives
    writer_advanced_mode: str = "adaptive"  # Writer adapts to content complexity

    # Tool Configuration
    tavily_api_key: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None

    # Agent Management
    enabled_agents: str = "researcher,analyst,writer"  # Comma-separated list
    agent_retry_attempts: int = 3
    agent_health_check_interval: float = 30.0  # seconds

    # ============================================================================
    # MCP SERVERS INTEGRATION
    # ============================================================================

    # Enable MCP server integration
    mcp_enable: bool = False  # Master switch for MCP integration

    # MCP Server Configuration Format:
    # Define servers using prefix: MCP_SERVER_{NAME}_*
    # Example in .env:
    #   MCP_SERVER_CORPORATE_TYPE=remote
    #   MCP_SERVER_CORPORATE_TRANSPORT=streamable_http
    #   MCP_SERVER_CORPORATE_URL=http://localhost:8001/mcp
    #   MCP_SERVER_CORPORATE_API_KEY=secret123
    #   MCP_SERVER_CORPORATE_ENABLED=true

    # This will be populated dynamically from environment variables
    # at runtime by parsing all MCP_SERVER_* variables
    mcp_servers: dict = {}

    # MCP Client Configuration
    mcp_client_retry_attempts: int = 3
    mcp_client_timeout: float = 30.0
    mcp_health_check_interval: float = 60.0  # seconds

    # MCP Tools in ReAct Pattern
    # Controls how MCP tools are integrated into the ReAct reasoning cycle
    mcp_tools_enable_logging: bool = True  # Log MCP tool calls in ReAct
    mcp_tools_enable_reflection: bool = False  # Apply reflection to MCP tool results
    mcp_tools_timeout_multiplier: float = 1.5  # Multiply agent timeout for MCP tools

    # Supervisor as MCP Server
    supervisor_mcp_enable: bool = False  # Expose supervisor as MCP server
    supervisor_mcp_path: str = "/mcp"  # Endpoint path for MCP
    supervisor_mcp_transport: str = "streamable_http"  # Transport type

    # ========================================================================
    # WORKFLOW SYSTEM
    # ========================================================================

    # Workflow Mode Configuration
    workflow_enable: bool = False
    workflow_mode: str = "hybrid"  # "react", "template", "hybrid"
    workflow_templates_dir: Optional[str] = None  # Default: workflows/templates
    workflow_auto_classify: bool = True  # Auto-match templates from user input
    workflow_fallback_to_react: bool = True  # Use ReAct if workflow fails
    workflow_parallel_max_workers: int = 5  # Max parallel node execution

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra env vars (for MCP_SERVER_* pattern)

    @property
    def supervisor_url(self) -> str:
        """Full URL for supervisor agent server."""
        return f"http://{self.supervisor_host}:{self.supervisor_port}"

    @property
    def researcher_url(self) -> str:
        """Full URL for researcher agent server."""
        return f"http://{self.researcher_host}:{self.researcher_port}"

    @property
    def reddit_url(self) -> str:
        """Full URL for reddit agent server."""
        return f"http://{self.reddit_host}:{self.reddit_port}"

    @property
    def analyst_url(self) -> str:
        """Full URL for analyst agent server."""
        return f"http://{self.analyst_host}:{self.analyst_port}"

    @property
    def writer_url(self) -> str:
        """Full URL for writer agent server."""
        return f"http://{self.writer_host}:{self.writer_port}"

    def get_enabled_agents(self) -> list[str]:
        """
        Parse and return list of enabled agents.

        Returns:
            List of agent IDs that should be enabled
        """
        if not self.enabled_agents:
            return []

        # Parse comma-separated string
        agents = [
            agent.strip().lower()
            for agent in self.enabled_agents.split(",")
            if agent.strip()
        ]

        return agents

    def parse_mcp_servers(self) -> dict:
        """
        Parse MCP server configurations from environment variables.

        Looks for variables with pattern: MCP_SERVER_{NAME}_{PARAM}
        and builds a dictionary of server configurations.

        Returns:
            Dictionary mapping server_name to server config dict
        """
        servers = {}

        # Pattern to match MCP_SERVER_* variables
        pattern = re.compile(r'^mcp_server_([a-z_]+)_([a-z_]+)$', re.IGNORECASE)

        # Get all model fields and their values (includes those loaded from .env)
        model_dump = self.model_dump()

        for key, value in model_dump.items():
            match = pattern.match(key)
            if match:
                server_name = match.group(1).lower()
                param_name = match.group(2).lower()

                if server_name not in servers:
                    servers[server_name] = {}

                # Value is already converted by Pydantic
                servers[server_name][param_name] = value

        return servers

    def is_agent_enabled(self, agent_id: str) -> bool:
        """
        Check if a specific agent is enabled.

        Args:
            agent_id: The agent ID to check

        Returns:
            True if agent is in the enabled list
        """
        return agent_id.lower() in self.get_enabled_agents()


# Global settings instance
settings = Settings()

# Parse MCP servers from environment variables if MCP is enabled
if settings.mcp_enable:
    # Load .env manually to get MCP_SERVER_* variables
    from dotenv import dotenv_values
    env_vars = dotenv_values(".env")

    # Parse MCP servers from loaded env vars
    servers = {}
    import re

    # Known parameter names (must match last part of env var)
    known_params = {
        'TYPE', 'TRANSPORT', 'URL', 'API_KEY', 'LOCAL_PATH', 'ENABLED', 'TIMEOUT',
        'PROMPTS_FILE', 'PROMPT_TOOL_ASSOCIATION'
    }

    for key, value in env_vars.items():
        if not key.startswith('MCP_SERVER_'):
            continue

        # Remove MCP_SERVER_ prefix
        rest = key[11:]  # len('MCP_SERVER_') = 11

        # Find last known parameter
        param_name = None
        server_name = None

        for known_param in known_params:
            if rest.endswith(f'_{known_param}'):
                param_name = known_param.lower()
                server_name = rest[:-(len(known_param) + 1)].lower()  # Remove _PARAM
                break

        if not server_name or not param_name:
            continue  # Skip unknown parameters

        if server_name not in servers:
            servers[server_name] = {}

        # Convert boolean strings
        if value and value.lower() in ('true', 'false'):
            value = value.lower() == 'true'
        # Convert numeric strings
        elif value and value.replace('.', '').replace('-', '').isdigit():
            value = float(value) if '.' in value else int(value)

        servers[server_name][param_name] = value

    settings.mcp_servers = servers

# Enable LangSmith tracing if configured
if settings.langsmith_api_key and settings.langsmith_tracing:
    import os
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
