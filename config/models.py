"""
Pydantic models for JSON-based project configuration.

Each project has multiple configuration files:
- project.json: Core project settings
- agents.json: Per-agent configuration
- mcp.json: MCP server configuration
- react.json: ReAct pattern configuration
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# PROJECT CONFIGURATION MODELS
# ============================================================================

class ProjectSettings(BaseModel):
    """Core project settings"""
    checkpoint_backend: str = Field(default="memory", description="State backend: memory, postgres, redis")
    postgres_url: Optional[str] = Field(default=None, description="PostgreSQL connection string")
    redis_url: Optional[str] = Field(default=None, description="Redis connection string")
    http_timeout: float = Field(default=120.0, description="HTTP timeout in seconds")
    http_max_connections: int = Field(default=100, description="Max HTTP connections")
    http_max_keepalive_connections: int = Field(default=20, description="Max keepalive connections")


class ProjectModel(BaseModel):
    """Main project configuration"""
    name: str = Field(..., description="Project name (unique identifier)")
    version: str = Field(default="1.0.0", description="Project version")
    description: str = Field(default="", description="Project description")
    active: bool = Field(default=True, description="Whether project is active")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    settings: ProjectSettings = Field(default_factory=ProjectSettings, description="Project settings")


# ============================================================================
# AGENT CONFIGURATION MODELS
# ============================================================================

class ReActStrategy(str, Enum):
    """ReAct reasoning strategies"""
    FAST = "fast"
    BALANCED = "balanced"
    DEEP = "deep"
    CREATIVE = "creative"


class AgentConfig(BaseModel):
    """Configuration for a single agent"""
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    host: str = Field(default="localhost", description="Agent server host")
    port: int = Field(..., description="Agent server port")
    model: Optional[str] = Field(default=None, description="LLM model (e.g., 'openai/gpt-4o-mini')")
    react_strategy: ReActStrategy = Field(default=ReActStrategy.BALANCED, description="ReAct strategy")
    temperature: float = Field(default=0.7, description="LLM temperature")
    max_iterations: int = Field(default=10, description="Max ReAct iterations")

    # Reflection settings
    enable_reflection: bool = Field(default=False, description="Enable self-reflection")
    reflection_threshold: float = Field(default=0.7, description="Quality threshold for reflection")
    reflection_max_iterations: int = Field(default=2, description="Max refinement iterations")

    # HITL settings
    enable_hitl: bool = Field(default=False, description="Enable Human-in-the-Loop")
    hitl_require_approval_for: str = Field(default="", description="Tool patterns requiring approval")
    hitl_timeout_seconds: float = Field(default=300.0, description="HITL approval timeout")


class AgentsModel(BaseModel):
    """Configuration for all agents"""
    default_model: str = Field(default="openai/gpt-4o-mini", description="Default LLM model")
    provider_fallback_order: str = Field(
        default="openai,anthropic,google,groq,openrouter",
        description="Provider fallback order"
    )
    agents: Dict[str, AgentConfig] = Field(..., description="Per-agent configuration")


# ============================================================================
# MCP CONFIGURATION MODELS
# ============================================================================

class MCPServerType(str, Enum):
    """MCP server types"""
    REMOTE = "remote"
    LOCAL = "local"


class MCPTransportType(str, Enum):
    """MCP transport types"""
    STREAMABLE_HTTP = "streamable_http"
    SSE = "sse"
    STDIO = "stdio"


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server"""
    type: MCPServerType = Field(..., description="Server type")
    transport: MCPTransportType = Field(..., description="Transport type")
    url: Optional[str] = Field(default=None, description="Server URL (for remote)")
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    local_path: Optional[str] = Field(default=None, description="Local Python file path (for local)")
    enabled: bool = Field(default=True, description="Whether server is enabled")
    timeout: float = Field(default=30.0, description="Request timeout")
    prompts_file: Optional[str] = Field(default=None, description="Path to manual prompts file")
    prompt_tool_association: Optional[str] = Field(default=None, description="Tool to associate prompt with")

    # Auto-testing and health monitoring
    test_results: Optional[Dict[str, Any]] = Field(default=None, description="Cached test results from last auto-test")
    last_tested: Optional[str] = Field(default=None, description="ISO 8601 timestamp of last test execution")
    status: Optional[str] = Field(default="untested", description="Server health status: healthy|unhealthy|untested")


class MCPClientConfig(BaseModel):
    """MCP client configuration"""
    retry_attempts: int = Field(default=3, description="Max retry attempts")
    timeout: float = Field(default=30.0, description="Default timeout")
    health_check_interval: float = Field(default=60.0, description="Health check interval in seconds")


class MCPModel(BaseModel):
    """MCP integration configuration"""
    enabled: bool = Field(default=False, description="Enable MCP integration")
    client: MCPClientConfig = Field(default_factory=MCPClientConfig, description="Client configuration")
    servers: Dict[str, MCPServerConfig] = Field(default_factory=dict, description="MCP servers")
    tools_enable_logging: bool = Field(default=True, description="Log MCP tool calls")
    tools_enable_reflection: bool = Field(default=False, description="Apply reflection to MCP results")
    tools_timeout_multiplier: float = Field(default=1.5, description="Timeout multiplier for MCP tools")


# ============================================================================
# REACT CONFIGURATION MODELS
# ============================================================================

class ReactExecutionConfig(BaseModel):
    """ReAct execution control"""
    timeout_seconds: float = Field(default=120.0, description="Max execution time")
    enable_early_stopping: bool = Field(default=True, description="Enable early stopping")
    max_consecutive_errors: int = Field(default=3, description="Max consecutive errors")


class ReactLoggingConfig(BaseModel):
    """ReAct logging configuration"""
    enable_verbose: bool = Field(default=True, description="Enable verbose logging")
    log_thoughts: bool = Field(default=True, description="Log reasoning thoughts")
    log_actions: bool = Field(default=True, description="Log tool actions")
    log_observations: bool = Field(default=True, description="Log tool observations")


class ReactReflectionConfig(BaseModel):
    """ReAct self-reflection configuration"""
    enabled: bool = Field(default=False, description="Enable reflection globally")
    quality_threshold: float = Field(default=0.7, description="Min quality score")
    max_iterations: int = Field(default=2, description="Max refinement iterations")


class ReactHITLConfig(BaseModel):
    """ReAct Human-in-the-Loop configuration"""
    enabled: bool = Field(default=False, description="Enable HITL globally")
    timeout_seconds: float = Field(default=300.0, description="Approval timeout")
    timeout_action: str = Field(default="reject", description="Action on timeout: reject|approve")


class ReactAdvancedModesConfig(BaseModel):
    """Advanced reasoning modes configuration"""
    cot_enabled: bool = Field(default=False, description="Chain-of-Thought explicit reasoning")
    cot_min_steps: int = Field(default=2, description="Min CoT reasoning steps")
    tot_enabled: bool = Field(default=False, description="Tree-of-Thought branching")
    tot_max_branches: int = Field(default=5, description="Max ToT branches")
    adaptive_enabled: bool = Field(default=False, description="Adaptive reasoning")
    adaptive_max_escalations: int = Field(default=3, description="Max strategy escalations")


class ReactModel(BaseModel):
    """ReAct pattern configuration"""
    execution: ReactExecutionConfig = Field(default_factory=ReactExecutionConfig)
    logging: ReactLoggingConfig = Field(default_factory=ReactLoggingConfig)
    reflection: ReactReflectionConfig = Field(default_factory=ReactReflectionConfig)
    hitl: ReactHITLConfig = Field(default_factory=ReactHITLConfig)
    advanced_modes: ReactAdvancedModesConfig = Field(default_factory=ReactAdvancedModesConfig)


# ============================================================================
# WORKFLOW CONFIGURATION MODELS
# ============================================================================

class WorkflowNode(BaseModel):
    """Workflow node configuration"""
    id: str = Field(..., description="Node ID")
    agent: str = Field(..., description="Agent to execute node")
    instruction: str = Field(..., description="Node instruction")
    depends_on: List[str] = Field(default_factory=list, description="Dependencies")
    parallel_group: Optional[str] = Field(default=None, description="Parallel execution group")
    timeout: Optional[int] = Field(default=None, description="Node timeout")
    template: Optional[str] = Field(default=None, description="Output template")
    use_mcp_prompt: bool = Field(default=False, description="Use MCP prompt for instruction")


class WorkflowConditionalEdge(BaseModel):
    """Workflow conditional edge"""
    source: str = Field(..., description="Source node")
    condition: str = Field(..., description="Condition expression")
    target: str = Field(..., description="Target node")


class WorkflowTemplate(BaseModel):
    """Workflow template configuration"""
    name: str = Field(..., description="Workflow name")
    version: str = Field(default="1.0", description="Workflow version")
    description: str = Field(default="", description="Workflow description")
    trigger_patterns: List[str] = Field(default_factory=list, description="Trigger patterns")
    nodes: List[WorkflowNode] = Field(..., description="Workflow nodes")
    conditional_edges: List[WorkflowConditionalEdge] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Default parameters")


# ============================================================================
# COMPLETE PROJECT CONFIGURATION
# ============================================================================

class ProjectConfiguration:
    """
    Complete configuration for a project.

    Loads and validates all configuration files for a project:
    - project.json
    - agents.json
    - mcp.json
    - react.json
    """

    def __init__(
        self,
        project: ProjectModel,
        agents: AgentsModel,
        mcp: MCPModel,
        react: ReactModel
    ):
        self.project = project
        self.agents = agents
        self.mcp = mcp
        self.react = react

    @property
    def name(self) -> str:
        """Project name"""
        return self.project.name

    @property
    def is_active(self) -> bool:
        """Whether project is active"""
        return self.project.active

    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get configuration for specific agent"""
        return self.agents.agents.get(agent_name)

    def get_enabled_agents(self) -> List[str]:
        """Get list of enabled agent names"""
        return [
            name for name, config in self.agents.agents.items()
            if config.enabled
        ]

    def get_mcp_server(self, server_name: str) -> Optional[MCPServerConfig]:
        """Get configuration for specific MCP server"""
        return self.mcp.servers.get(server_name)

    def get_enabled_mcp_servers(self) -> Dict[str, MCPServerConfig]:
        """Get all enabled MCP servers"""
        return {
            name: config
            for name, config in self.mcp.servers.items()
            if config.enabled
        }
