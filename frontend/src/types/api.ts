/**
 * TypeScript types for Cortex Flow Editor API
 * Matches the Pydantic models in servers/editor_server.py
 */

// ============================================================================
// Projects
// ============================================================================

export interface ProjectInfo {
  name: string;
  version: string;
  description: string;
  active: boolean;
  created_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  template?: string;
}

export interface ProjectUpdate {
  description?: string;
  active?: boolean;
}

// ============================================================================
// Agents & ReAct
// ============================================================================

export interface AgentConfig {
  enabled: boolean;
  host: string;
  port: number;
  model: string | null;
  react_strategy: string;
  temperature: number;
  max_iterations: number;
  enable_reflection: boolean;
  reflection_threshold: number;
  reflection_max_iterations: number;
  enable_hitl: boolean;
  hitl_require_approval_for: string;
  hitl_timeout_seconds: number;
}

export interface AgentsConfig {
  default_model: string;
  web_app_model?: string;  // Optional: model for web app AI features (workflow generation, conversions)
  provider_fallback_order: string;
  agents: {
    [agentName: string]: AgentConfig;
  };
}

export interface ReActConfig {
  max_iterations: number;
  timeout_seconds: number;
  max_consecutive_errors: number;
  enable_verbose_logging: boolean;
  log_thoughts: boolean;
  log_actions: boolean;
  log_observations: boolean;
  allow_delegation: boolean;
  enable_reflection: boolean;
}

// ============================================================================
// Prompts
// ============================================================================

export interface PromptsInfo {
  system: string | null;
  agents: {
    [agentName: string]: string;
  };
  mcp: {
    [serverName: string]: string;
  };
}

export interface PromptContent {
  content: string;
}

// ============================================================================
// Workflows
// ============================================================================

export interface WorkflowInfo {
  name: string;
  description: string;
  version: string;
  agents: string[];
}

export interface WorkflowStep {
  action: string;
  parameters?: Record<string, any>;
}

export interface WorkflowAgent {
  type: string;
  enabled: boolean;
  steps: WorkflowStep[];
}

export interface WorkflowNode {
  id: string;
  agent: string;
  instruction: string;
  depends_on: string[];
  timeout?: number;
  template?: string;
  tool_name?: string;
  parallel_group?: string;
}

export interface ConditionalEdgeCondition {
  field: string;
  operator: string;
  value: any;
  next_node: string;
}

export interface ConditionalEdge {
  from_node: string;
  conditions: ConditionalEdgeCondition[];
  default: string;
}

export interface Workflow {
  name: string;
  description: string;
  version: string;
  // New format (LangGraph)
  nodes?: WorkflowNode[];
  conditional_edges?: ConditionalEdge[];
  parameters?: Record<string, any>;
  trigger_patterns?: string[];
  // Old format (deprecated)
  agents?: {
    [agentName: string]: WorkflowAgent;
  };
  routing?: {
    [key: string]: string;
  };
}

export interface WorkflowValidationRequest {
  workflow: Workflow;
}

export interface WorkflowValidationResponse {
  valid: boolean;
  errors?: string[];
  message?: string;
}

export interface WorkflowPreview {
  workflow_name: string;
  agents: {
    name: string;
    type: string;
    steps_count: number;
    steps: string[];
  }[];
  estimated_steps: number;
  routing: {
    [key: string]: string;
  };
}

// ============================================================================
// MCP
// ============================================================================

export interface MCPServerInfo {
  id: string;
  name: string;
  description: string;
  repository?: string;
}

export interface MCPServerDetails extends MCPServerInfo {
  tools: string[];
  config_schema?: any;
}

export interface MCPRegistry {
  servers: MCPServerInfo[];
}

export interface MCPConfig {
  enabled: boolean;
  client: {
    retry_attempts: number;
    timeout: number;
    health_check_interval: number;
  };
  servers: {
    [serverName: string]: any;
  };
  tools_enable_logging: boolean;
  tools_enable_reflection: boolean;
  tools_timeout_multiplier: number;
}

export interface MCPTestRequest {
  server_config: Record<string, any>;
}

export interface MCPTestResponse {
  server_name: string;
  status: 'success' | 'error' | 'unknown';
  message: string;
  tools: string[];
}

export interface MCPLibrary {
  servers: MCPServerInfo[];
}

// ============================================================================
// AI Generation
// ============================================================================

export interface WorkflowGenerateRequest {
  description: string;
  agent_types?: string[];
  mcp_servers?: string[];
}

export interface WorkflowGenerateResponse {
  workflow: Workflow;
  message: string;
  confidence: number;
}

export interface DslConvertRequest {
  workflow: Record<string, any>;
  format?: string; // "yaml" | "python"
}

export interface DslConvertResponse {
  dsl: string;
  format: string;
}

export interface DslParseRequest {
  dsl: string;
  format?: string; // "yaml" | "python"
}

export interface DslParseResponse {
  workflow: Record<string, any>;
}

export interface NaturalLanguageConvertRequest {
  workflow: Record<string, any>;
  language?: string; // "it" | "en" etc.
}

export interface NaturalLanguageConvertResponse {
  prompt: string;
  language: string;
}

export interface NaturalLanguageParseRequest {
  prompt: string;
  language?: string; // "it" | "en" etc.
}

export interface NaturalLanguageParseResponse {
  workflow: Record<string, any>;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface WorkflowChatRequest {
  workflow: Record<string, any>;
  message: string;
  history: ChatMessage[];
  language?: string; // "it" | "en" etc.
}

export interface WorkflowChatResponse {
  workflow: Record<string, any>;
  explanation: string;
  changes: string[];
}

// ============================================================================
// LLM Configuration
// ============================================================================

export type ProviderType = 'openai' | 'anthropic' | 'google' | 'groq' | 'openrouter';
export type CostTier = 'free' | 'low' | 'medium' | 'high' | 'premium';

export interface ModelInfo {
  provider: ProviderType;
  model_id: string;
  display_name: string;
  context_window: number;
  supports_tools: boolean;
  supports_streaming: boolean;
  cost_tier: CostTier;
  recommended_for: string[];
}

export interface ModelRegistry {
  providers: {
    [provider: string]: ModelInfo[];
  };
}

export interface APIKeyStatus {
  provider: ProviderType;
  configured: boolean;
  valid?: boolean;
  error?: string;
}

export interface APIKeyConfig {
  provider: ProviderType;
  key: string | null;
  masked_key: string | null;
  configured: boolean;
  last_validated: string | null;
}

export interface APIKeyUpdateRequest {
  key: string;
}

export interface APIKeyValidateResponse {
  valid: boolean;
  error?: string;
  model_info?: string;
}

// ============================================================================
// Execution & Testing
// ============================================================================

export interface AgentInvokeRequest {
  agent_name: string;
  task: string;
  project_name?: string;
  stream?: boolean;
}

export interface WorkflowExecuteRequest {
  workflow_name: string;
  user_input: string;
  project_name?: string;
  parameters?: Record<string, any>;
  stream?: boolean;
}

export interface ExecutionStep {
  step_type: 'thought' | 'action' | 'observation' | 'reflection' | 'decision';
  agent?: string;
  node_id?: string;
  iteration: number;
  timestamp: number;
  content: string;
  metadata: Record<string, any>;
}

export interface ExecutionResult {
  status: 'success' | 'error' | 'timeout';
  result?: string;
  error?: string;
  execution_time: number;
  steps: ExecutionStep[];
  metadata: Record<string, any>;
}

export interface AgentHealthResponse {
  agent: string;
  status: 'healthy' | 'unhealthy' | 'error';
  url?: string;
  enabled: boolean;
  error?: string;
  response?: any;
}

// ============================================================================
// API Responses
// ============================================================================

export interface ApiResponse {
  status: 'success' | 'error';
  message: string;
}

export interface HealthCheck {
  status: 'healthy' | 'unhealthy';
  service: string;
  version: string;
  projects_dir: string;
}
