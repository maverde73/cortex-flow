/**
 * API Client for Cortex Flow Editor
 * Provides typed axios methods for all backend endpoints
 */

import axios from 'axios';
import type { AxiosInstance } from 'axios';
import type {
  ProjectInfo,
  ProjectCreate,
  ProjectUpdate,
  AgentsConfig,
  ReActConfig,
  PromptsInfo,
  PromptContent,
  WorkflowInfo,
  Workflow,
  WorkflowValidationRequest,
  WorkflowValidationResponse,
  WorkflowPreview,
  DslConvertRequest,
  DslConvertResponse,
  DslParseRequest,
  DslParseResponse,
  NaturalLanguageConvertRequest,
  NaturalLanguageConvertResponse,
  NaturalLanguageParseRequest,
  NaturalLanguageParseResponse,
  WorkflowChatRequest,
  WorkflowChatResponse,
  MCPRegistry,
  MCPServerDetails,
  MCPConfig,
  MCPTestRequest,
  MCPTestResponse,
  MCPLibrary,
  WorkflowGenerateRequest,
  WorkflowGenerateResponse,
  ModelRegistry,
  APIKeyStatus,
  APIKeyConfig,
  APIKeyValidateResponse,
  ApiResponse,
  HealthCheck,
  ProcessInfo,
  ProcessLogsResponse,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002';

class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // ============================================================================
  // Root & Health
  // ============================================================================

  async health(): Promise<HealthCheck> {
    const { data } = await this.client.get<HealthCheck>('/health');
    return data;
  }

  // ============================================================================
  // Projects
  // ============================================================================

  async listProjects(): Promise<ProjectInfo[]> {
    const { data } = await this.client.get<ProjectInfo[]>('/api/projects');
    return data;
  }

  async getProject(name: string): Promise<ProjectInfo> {
    const { data } = await this.client.get<ProjectInfo>(`/api/projects/${name}`);
    return data;
  }

  async createProject(project: ProjectCreate): Promise<ProjectInfo> {
    const { data } = await this.client.post<ProjectInfo>('/api/projects', project);
    return data;
  }

  async updateProject(name: string, update: ProjectUpdate): Promise<ProjectInfo> {
    const { data } = await this.client.put<ProjectInfo>(`/api/projects/${name}`, update);
    return data;
  }

  async deleteProject(name: string): Promise<void> {
    await this.client.delete(`/api/projects/${name}`);
  }

  async activateProject(name: string): Promise<ProjectInfo> {
    const { data } = await this.client.post<ProjectInfo>(`/api/projects/${name}/activate`);
    return data;
  }

  // ============================================================================
  // Agents & ReAct
  // ============================================================================

  async getAgentsConfig(projectName: string): Promise<AgentsConfig> {
    const { data } = await this.client.get<AgentsConfig>(`/api/projects/${projectName}/agents`);
    return data;
  }

  async updateAgentsConfig(projectName: string, config: AgentsConfig): Promise<ApiResponse> {
    const { data } = await this.client.put<ApiResponse>(
      `/api/projects/${projectName}/agents`,
      { config }
    );
    return data;
  }

  async getReActConfig(projectName: string): Promise<ReActConfig> {
    const { data } = await this.client.get<ReActConfig>(`/api/projects/${projectName}/react`);
    return data;
  }

  async updateReActConfig(projectName: string, config: ReActConfig): Promise<ApiResponse> {
    const { data } = await this.client.put<ApiResponse>(
      `/api/projects/${projectName}/react`,
      { config }
    );
    return data;
  }

  // ============================================================================
  // Prompts
  // ============================================================================

  async listPrompts(projectName: string): Promise<PromptsInfo> {
    const { data } = await this.client.get<PromptsInfo>(`/api/projects/${projectName}/prompts`);
    return data;
  }

  async getSystemPrompt(projectName: string): Promise<PromptContent> {
    const { data } = await this.client.get<PromptContent>(
      `/api/projects/${projectName}/prompts/system`
    );
    return data;
  }

  async updateSystemPrompt(projectName: string, content: string): Promise<ApiResponse> {
    const { data } = await this.client.put<ApiResponse>(
      `/api/projects/${projectName}/prompts/system`,
      { content }
    );
    return data;
  }

  async getAgentPrompt(projectName: string, agentName: string): Promise<PromptContent> {
    const { data } = await this.client.get<PromptContent>(
      `/api/projects/${projectName}/prompts/agents/${agentName}`
    );
    return data;
  }

  async updateAgentPrompt(
    projectName: string,
    agentName: string,
    content: string
  ): Promise<ApiResponse> {
    const { data } = await this.client.put<ApiResponse>(
      `/api/projects/${projectName}/prompts/agents/${agentName}`,
      { content }
    );
    return data;
  }

  async getMCPPrompt(projectName: string, serverName: string): Promise<PromptContent> {
    const { data } = await this.client.get<PromptContent>(
      `/api/projects/${projectName}/prompts/mcp/${serverName}`
    );
    return data;
  }

  async updateMCPPrompt(
    projectName: string,
    serverName: string,
    content: string
  ): Promise<ApiResponse> {
    const { data } = await this.client.put<ApiResponse>(
      `/api/projects/${projectName}/prompts/mcp/${serverName}`,
      { content }
    );
    return data;
  }

  // ============================================================================
  // Workflows
  // ============================================================================

  async listWorkflows(projectName: string): Promise<WorkflowInfo[]> {
    const { data } = await this.client.get<WorkflowInfo[]>(
      `/api/projects/${projectName}/workflows`
    );
    return data;
  }

  async getWorkflow(projectName: string, workflowName: string): Promise<Workflow> {
    const { data } = await this.client.get<Workflow>(
      `/api/projects/${projectName}/workflows/${workflowName}`
    );
    return data;
  }

  async createWorkflow(
    projectName: string,
    workflowName: string,
    workflow: Workflow
  ): Promise<ApiResponse> {
    const { data } = await this.client.post<ApiResponse>(
      `/api/projects/${projectName}/workflows/${workflowName}`,
      { workflow }
    );
    return data;
  }

  async updateWorkflow(
    projectName: string,
    workflowName: string,
    workflow: Workflow
  ): Promise<ApiResponse> {
    const { data } = await this.client.put<ApiResponse>(
      `/api/projects/${projectName}/workflows/${workflowName}`,
      { workflow }
    );
    return data;
  }

  async deleteWorkflow(projectName: string, workflowName: string): Promise<void> {
    await this.client.delete(`/api/projects/${projectName}/workflows/${workflowName}`);
  }

  async validateWorkflow(
    projectName: string,
    request: WorkflowValidationRequest
  ): Promise<WorkflowValidationResponse> {
    const { data } = await this.client.post<WorkflowValidationResponse>(
      `/api/projects/${projectName}/workflows/validate`,
      request
    );
    return data;
  }

  async previewWorkflow(projectName: string, workflowName: string): Promise<WorkflowPreview> {
    const { data } = await this.client.post<WorkflowPreview>(
      `/api/projects/${projectName}/workflows/${workflowName}/preview`
    );
    return data;
  }

  async convertWorkflowToDsl(request: DslConvertRequest): Promise<DslConvertResponse> {
    const { data } = await this.client.post<DslConvertResponse>(
      '/api/workflows/convert-to-dsl',
      request
    );
    return data;
  }

  async parseDslToWorkflow(request: DslParseRequest): Promise<DslParseResponse> {
    const { data } = await this.client.post<DslParseResponse>(
      '/api/workflows/parse-dsl',
      request
    );
    return data;
  }

  async convertWorkflowToNaturalLanguage(
    request: NaturalLanguageConvertRequest
  ): Promise<NaturalLanguageConvertResponse> {
    const { data } = await this.client.post<NaturalLanguageConvertResponse>(
      '/api/workflows/to-natural-language',
      request
    );
    return data;
  }

  async parseNaturalLanguageToWorkflow(
    request: NaturalLanguageParseRequest
  ): Promise<NaturalLanguageParseResponse> {
    const { data} = await this.client.post<NaturalLanguageParseResponse>(
      '/api/workflows/from-natural-language',
      request
    );
    return data;
  }

  async chatModifyWorkflow(
    request: WorkflowChatRequest
  ): Promise<WorkflowChatResponse> {
    const { data } = await this.client.post<WorkflowChatResponse>(
      '/api/workflows/chat-modify',
      request
    );
    return data;
  }

  // ============================================================================
  // MCP
  // ============================================================================

  async browseMCPRegistry(): Promise<MCPRegistry> {
    const { data } = await this.client.get<MCPRegistry>('/api/mcp/registry');
    return data;
  }

  async getMCPServerDetails(serverId: string): Promise<MCPServerDetails> {
    const { data } = await this.client.get<MCPServerDetails>(`/api/mcp/registry/${serverId}`);
    return data;
  }

  async getMCPConfig(projectName: string): Promise<MCPConfig> {
    const { data } = await this.client.get<MCPConfig>(`/api/projects/${projectName}/mcp`);
    return data;
  }

  async updateMCPConfig(projectName: string, config: MCPConfig): Promise<ApiResponse> {
    const { data } = await this.client.put<ApiResponse>(
      `/api/projects/${projectName}/mcp`,
      { config }
    );
    return data;
  }

  async testMCPConnection(
    projectName: string,
    serverName: string,
    request: MCPTestRequest
  ): Promise<MCPTestResponse> {
    const { data } = await this.client.post<MCPTestResponse>(
      `/api/projects/${projectName}/mcp/test/${serverName}`,
      request
    );
    return data;
  }

  async listMCPLibrary(): Promise<MCPLibrary> {
    const { data } = await this.client.get<MCPLibrary>('/api/mcp/library');
    return data;
  }

  async addToMCPLibrary(serverId: string, config: any): Promise<ApiResponse> {
    const { data } = await this.client.post<ApiResponse>(
      `/api/mcp/library?server_id=${serverId}`,
      { config }
    );
    return data;
  }

  async removeFromMCPLibrary(serverId: string): Promise<void> {
    await this.client.delete(`/api/mcp/library/${serverId}`);
  }

  // ============================================================================
  // AI Generation
  // ============================================================================

  async generateWorkflow(request: WorkflowGenerateRequest): Promise<WorkflowGenerateResponse> {
    const { data } = await this.client.post<WorkflowGenerateResponse>(
      '/api/workflows/generate',
      request
    );
    return data;
  }

  // ============================================================================
  // LLM Configuration
  // ============================================================================

  async getModelRegistry(): Promise<ModelRegistry> {
    const { data } = await this.client.get<ModelRegistry>('/api/llm/registry');
    return data;
  }

  async getAPIKeyStatus(): Promise<APIKeyStatus[]> {
    const { data } = await this.client.get<APIKeyStatus[]>('/api/llm/api-keys/status');
    return data;
  }

  async getAPIKeys(): Promise<APIKeyConfig[]> {
    const { data } = await this.client.get<APIKeyConfig[]>('/api/llm/api-keys');
    return data;
  }

  async updateAPIKey(provider: string, key: string): Promise<ApiResponse> {
    const { data } = await this.client.put<ApiResponse>(
      `/api/llm/api-keys/${provider}`,
      { key }
    );
    return data;
  }

  async validateAPIKey(provider: string): Promise<APIKeyValidateResponse> {
    const { data } = await this.client.post<APIKeyValidateResponse>(
      `/api/llm/api-keys/validate/${provider}`
    );
    return data;
  }

  // ============================================================================
  // Execution & Testing
  // ============================================================================

  async invokeAgent(request: AgentInvokeRequest): Promise<ExecutionResult> {
    const { data } = await this.client.post<ExecutionResult>('/api/agents/invoke', request);
    return data;
  }

  async executeWorkflow(request: WorkflowExecuteRequest): Promise<ExecutionResult> {
    const { data } = await this.client.post<ExecutionResult>('/api/workflows/execute', request);
    return data;
  }

  async checkAgentHealth(agentName: string, projectName: string = 'default'): Promise<AgentHealthResponse> {
    const { data } = await this.client.get<AgentHealthResponse>(
      `/api/agents/${agentName}/health`,
      { params: { project_name: projectName } }
    );
    return data;
  }

  // ============================================================================
  // Process Management
  // ============================================================================

  async getProcessesStatus(): Promise<ProcessInfo[]> {
    const { data } = await this.client.get<ProcessInfo[]>('/api/processes/status');
    return data;
  }

  async getProcessStatus(processName: string): Promise<ProcessInfo> {
    const { data } = await this.client.get<ProcessInfo>(`/api/processes/${processName}/status`);
    return data;
  }

  async startProcess(processName: string): Promise<ProcessInfo> {
    const { data } = await this.client.post<ProcessInfo>('/api/processes/start', { name: processName });
    return data;
  }

  async stopProcess(processName: string): Promise<ProcessInfo> {
    const { data } = await this.client.post<ProcessInfo>(`/api/processes/${processName}/stop`);
    return data;
  }

  async restartProcess(processName: string): Promise<ProcessInfo> {
    const { data } = await this.client.post<ProcessInfo>(`/api/processes/${processName}/restart`);
    return data;
  }

  async startAllProcesses(): Promise<ProcessInfo[]> {
    const { data } = await this.client.post<ProcessInfo[]>('/api/processes/start-all');
    return data;
  }

  async stopAllProcesses(): Promise<ProcessInfo[]> {
    const { data } = await this.client.post<ProcessInfo[]>('/api/processes/stop-all');
    return data;
  }

  async getProcessLogs(processName: string, lines: number = 50): Promise<ProcessLogsResponse> {
    const { data } = await this.client.get<ProcessLogsResponse>(
      `/api/processes/${processName}/logs`,
      { params: { lines } }
    );
    return data;
  }
}

// Export singleton instance
export const api = new ApiClient(API_BASE_URL);
export default api;
